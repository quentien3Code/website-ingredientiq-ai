"""
Custom middleware for handling CORS, security headers, caching, and SEO optimization
"""
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponseNotFound
import os
import json
import socket
import logging
from urllib.parse import urlparse, parse_qsl, urlencode


_admin_debug_logger = logging.getLogger('foodanalysis.admin_debug')


def _admin_debug_enabled() -> bool:
    return os.getenv('ADMIN_DEBUG', '').strip().lower() in ('1', 'true', 'yes', 'y', 'on')


def _truncate(value: str, max_len: int = 200) -> str:
    if not value:
        return ''
    value = str(value)
    return value if len(value) <= max_len else value[:max_len] + '…'


_SENSITIVE_QUERY_KEYS = (
    'token', 'preview', 'key', 'secret', 'signature', 'sig', 'csrf', 'session', 'auth', 'password', 'pass', 'code'
)


def _scrub_full_path(full_path: str) -> str:
    """Remove token-like query parameters from a URL path for safe logging."""
    if not full_path:
        return ''
    try:
        parsed = urlparse(str(full_path))
        if not parsed.query:
            return parsed.path or str(full_path)

        scrubbed = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            k = (key or '').strip().lower()
            if not k:
                continue
            if k == 'next':
                scrubbed.append((key, 'REDACTED'))
                continue
            if any(s in k for s in _SENSITIVE_QUERY_KEYS):
                scrubbed.append((key, 'REDACTED'))
            else:
                scrubbed.append((key, value))

        query = urlencode(scrubbed, doseq=True)
        return f"{parsed.path}?{query}" if query else (parsed.path or str(full_path))
    except Exception:
        return _truncate(str(full_path))


class AdminDebugMiddleware(MiddlewareMixin):
    """Temporary, safe diagnostics for Django admin instability.

    Enabled via env var ADMIN_DEBUG=1.
    Logs only admin requests and never logs cookie/token values.
    """

    def process_response(self, request, response):
        if not _admin_debug_enabled():
            return response

        path = getattr(request, 'path', '') or ''
        if not path.startswith('/admin/'):
            return response

        status = getattr(response, 'status_code', None)
        method = getattr(request, 'method', None)
        location = response.get('Location', '') if hasattr(response, 'get') else ''
        has_location_header = bool(location)

        location_is_absolute = False
        location_scheme = None
        location_host = None
        location_path = None
        if isinstance(location, str) and location:
            try:
                parsed = urlparse(location)
                if parsed.scheme and parsed.netloc:
                    location_is_absolute = True
                    location_scheme = parsed.scheme
                    location_host = parsed.netloc
                    location_path = parsed.path
                else:
                    # Relative redirects (common for Django admin)
                    location_path = location
            except Exception:
                # Never fail logging due to unexpected Location values.
                pass

        is_redirect_to_login = (
            status in (301, 302, 303, 307, 308)
            and isinstance(location, str)
            and '/admin/login' in location
        )

        should_log = (
            method == 'POST'
            or (isinstance(status, int) and status >= 400)
            or is_redirect_to_login
        )

        if not should_log:
            return response

        user = getattr(request, 'user', None)
        is_authenticated = bool(getattr(user, 'is_authenticated', False))

        payload = {
            'event': (
                'admin_redirect_to_login' if is_redirect_to_login else
                'admin_403' if status == 403 else
                'admin_response'
            ),
            'method': method,
            'path': path,
            'full_path': _truncate(_scrub_full_path(getattr(request, 'get_full_path', lambda: path)())),
            'status_code': status,
            'is_secure': bool(getattr(request, 'is_secure', lambda: False)()),
            'host': _truncate(getattr(request, 'get_host', lambda: '')()),
            'has_any_cookie': bool(getattr(request, 'COOKIES', None)),
            'has_session_cookie': settings.SESSION_COOKIE_NAME in request.COOKIES,
            'has_csrf_cookie': settings.CSRF_COOKIE_NAME in request.COOKIES,
            'user_authenticated': is_authenticated,
            'user_id': getattr(user, 'pk', None) if is_authenticated else None,
            'pid': os.getpid(),
            'hostname': socket.gethostname(),
            'has_location_header': has_location_header,
            'location': _truncate(location),
            'location_is_absolute': location_is_absolute,
            'location_scheme': _truncate(location_scheme or ''),
            'location_host': _truncate(location_host or ''),
            'location_path': _truncate(location_path or ''),
        }

        try:
            _admin_debug_logger.info(json.dumps(payload, separators=(',', ':'), sort_keys=True))
        except Exception:
            # Never break responses due to logging.
            pass

        return response


class SensitivePathBlockMiddleware(MiddlewareMixin):
    """Block access to dotfiles and common secret/config filenames.

    This is an upstream safety rail for scanners probing for `/.env`, `/.git/config`, etc.
    It returns a 404 and does not disclose whether such files exist.

    NOTE: We explicitly allow `/.well-known/` which is used for standards-based files.
    """

    _PREFIX_BLOCKLIST = (
        '/.env',
        '/.git',
        '/.hg',
        '/.svn',
        '/.ssh',
        '/.aws',
        '/.docker',
        '/.kube',
        '/.npmrc',
        '/.pypirc',
        '/.netrc',
        '/.htaccess',
        '/.htpasswd',
        '/.DS_Store',
    )

    _EXACT_BLOCKLIST = (
        '/env',
        '/dotenv',
    )

    def process_request(self, request):
        try:
            path = getattr(request, 'path', '') or ''
        except Exception:
            return None

        # Allow standards-based files.
        if path.startswith('/.well-known/'):
            return None

        lower = path.lower()

        if lower in self._EXACT_BLOCKLIST:
            resp = HttpResponseNotFound('Not Found')
            resp['Cache-Control'] = 'no-store'
            return resp

        for prefix in self._PREFIX_BLOCKLIST:
            if lower.startswith(prefix):
                resp = HttpResponseNotFound('Not Found')
                resp['Cache-Control'] = 'no-store'
                return resp

        # Block any path segment starting with a dot (e.g. /foo/.env, /bar/.git/config)
        # while preserving '/.well-known/'.
        if '/.' in lower:
            resp = HttpResponseNotFound('Not Found')
            resp['Cache-Control'] = 'no-store'
            return resp

        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add comprehensive security headers for modern web security
    """
    
    def process_response(self, request, response):
        # =================================================================
        # Cross-Origin Policies
        # =================================================================
        response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        response['Cross-Origin-Embedder-Policy'] = 'unsafe-none'
        response['Cross-Origin-Resource-Policy'] = 'cross-origin'
        
        # =================================================================
        # Basic Security Headers
        # =================================================================
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # =================================================================
        # HSTS (HTTP Strict Transport Security) - Forces HTTPS
        # =================================================================
        # Only enable in production (when not DEBUG)
        if not os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes'):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # =================================================================
        # Permissions Policy (formerly Feature Policy)
        # =================================================================
        response['Permissions-Policy'] = (
            'camera=(self), '
            'microphone=(), '
            'geolocation=(self), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )
        
        # =================================================================
        # Content Security Policy (CSP)
        # =================================================================
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://www.googletagmanager.com https://www.google-analytics.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://www.ingredientiq.ai https://*.ingredientiq.ai https://www.google-analytics.com https://fonts.googleapis.com https://fonts.gstatic.com",
            "frame-src 'self' https://www.youtube.com https://youtube.com",
            "media-src 'self' https: blob:",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'self'",
            "upgrade-insecure-requests"
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # =================================================================
        # Cache Control for HTML pages (don't cache dynamic content)
        # =================================================================
        if response.get('Content-Type', '').startswith('text/html'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class StaticFileMIMEMiddleware(MiddlewareMixin):
    """
    Middleware to ensure proper MIME types and caching for static files
    """
    
    # File extensions that should be cached for a long time (immutable assets)
    LONG_CACHE_EXTENSIONS = {'.js', '.css', '.woff', '.woff2', '.ttf', '.eot', '.otf'}
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico', '.avif'}
    
    def process_response(self, request, response):
        path = request.path.lower()
        
        # Check if this is a static file request
        is_static = (
            path.startswith('/static/') or 
            path.startswith('/control-panel/static/') or
            path.startswith('/images/') or
            path.startswith('/css/') or
            path.startswith('/js/')
        )
        
        if is_static or any(path.endswith(ext) for ext in self.LONG_CACHE_EXTENSIONS | self.IMAGE_EXTENSIONS):
            # =================================================================
            # Set proper MIME types
            # =================================================================
            if path.endswith('.js'):
                response['Content-Type'] = 'application/javascript; charset=utf-8'
            elif path.endswith('.css'):
                response['Content-Type'] = 'text/css; charset=utf-8'
            elif path.endswith('.png'):
                response['Content-Type'] = 'image/png'
            elif path.endswith('.jpg') or path.endswith('.jpeg'):
                response['Content-Type'] = 'image/jpeg'
            elif path.endswith('.gif'):
                response['Content-Type'] = 'image/gif'
            elif path.endswith('.webp'):
                response['Content-Type'] = 'image/webp'
            elif path.endswith('.avif'):
                response['Content-Type'] = 'image/avif'
            elif path.endswith('.svg'):
                response['Content-Type'] = 'image/svg+xml'
            elif path.endswith('.ico'):
                response['Content-Type'] = 'image/x-icon'
            elif path.endswith('.woff2'):
                response['Content-Type'] = 'font/woff2'
            elif path.endswith('.woff'):
                response['Content-Type'] = 'font/woff'
            elif path.endswith('.ttf'):
                response['Content-Type'] = 'font/ttf'
            elif path.endswith('.eot'):
                response['Content-Type'] = 'application/vnd.ms-fontobject'
            elif path.endswith('.json'):
                response['Content-Type'] = 'application/json; charset=utf-8'
            elif path.endswith('.xml'):
                response['Content-Type'] = 'application/xml; charset=utf-8'
            elif path.endswith('.txt'):
                response['Content-Type'] = 'text/plain; charset=utf-8'
            elif path.endswith('.pdf'):
                response['Content-Type'] = 'application/pdf'
            
            # =================================================================
            # Cache Control for Static Assets
            # =================================================================
            # Files with hash in filename (like main.75def15d.js) are immutable
            if any(ext in path for ext in ['.chunk.', '.min.']):
                # Chunked/minified files - cache for 1 year, immutable
                response['Cache-Control'] = 'public, max-age=31536000, immutable'
            elif any(path.endswith(ext) for ext in self.LONG_CACHE_EXTENSIONS):
                # CSS/JS/Fonts - cache for 1 year
                response['Cache-Control'] = 'public, max-age=31536000, immutable'
            elif any(path.endswith(ext) for ext in self.IMAGE_EXTENSIONS):
                # Images - cache for 1 month
                response['Cache-Control'] = 'public, max-age=2592000'
            else:
                # Other static files - cache for 1 week
                response['Cache-Control'] = 'public, max-age=604800'
        
        return response


class SEOHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add SEO-related headers for discoverability
    """
    
    def process_response(self, request, response):
        # Only add to HTML responses
        if not response.get('Content-Type', '').startswith('text/html'):
            return response
        
        # =================================================================
        # Link headers for SEO/discoverability
        # =================================================================
        links = []
        
        # Canonical URL
        if request.path == '/':
            try:
                canonical_origin = getattr(settings, 'CANONICAL_ORIGIN', '') or ''
                parsed = urlparse(canonical_origin)
                if parsed.scheme and parsed.netloc:
                    canonical_root = f"{parsed.scheme}://{parsed.netloc}/"
                    links.append(f'<{canonical_root}>; rel="canonical"')
            except Exception:
                # Never fail response processing due to malformed SITE_URL
                pass
        
        # Preconnect hints via Link header (in addition to HTML)
        links.extend([
            '<https://fonts.googleapis.com>; rel="preconnect"',
            '<https://fonts.gstatic.com>; rel="preconnect"; crossorigin',
            '<https://cdnjs.cloudflare.com>; rel="dns-prefetch"',
        ])
        
        if links:
            response['Link'] = ', '.join(links)
        
        return response

