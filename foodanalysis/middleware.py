"""
Custom middleware for handling CORS, security headers, caching, and SEO optimization
"""
from django.utils.deprecation import MiddlewareMixin
import os


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
            links.append('<https://www.ingredientiq.ai/>; rel="canonical"')
        
        # Preconnect hints via Link header (in addition to HTML)
        links.extend([
            '<https://fonts.googleapis.com>; rel="preconnect"',
            '<https://fonts.gstatic.com>; rel="preconnect"; crossorigin',
            '<https://cdnjs.cloudflare.com>; rel="dns-prefetch"',
        ])
        
        if links:
            response['Link'] = ', '.join(links)
        
        return response

