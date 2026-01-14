"""foodanalysis URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
import panel,Website

from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, FileResponse
import os
from django.views.generic import TemplateView
from pathlib import Path

# Health endpoints (deployment gating + diagnostics)
from .health import healthz, readyz

# SEO: Sitemaps
from django.contrib.sitemaps.views import sitemap
from Website.sitemaps import sitemaps

# SEO: RSS/Atom Feeds
from Website.feeds import LatestBlogsFeed, LatestBlogsAtomFeed, CategoryFeed, TagFeed

# SEO: Dynamic robots.txt, llms.txt, etc.
from Website.seo_views import robots_txt, llms_txt, humans_txt, security_txt, blog_detail_view

# =============================================================================
# Frontend Asset Paths Configuration
# =============================================================================
# Organized structure: frontend/website/ and frontend/admin/

WEBSITE_BUILD_PATH = os.path.join(settings.BASE_DIR, 'frontend', 'website')
ADMIN_BUILD_PATH = os.path.join(settings.BASE_DIR, 'frontend', 'admin')


def _safe_resolve_under_root(root_dir: str, rel_path: str) -> str:
    root = Path(root_dir).resolve()
    candidate = (root / rel_path).resolve()
    # Prevent path traversal (e.g. ../) from escaping the root.
    if candidate != root and root not in candidate.parents:
        raise FileNotFoundError("Invalid path")
    return str(candidate)


def serve_website_image(request, path):
    """Serve images from frontend/website/images with a safe fallback.

    Avoids noisy 404s for missing content-referenced images by serving a known
    placeholder instead.
    """
    images_root = os.path.join(WEBSITE_BUILD_PATH, 'images')
    fallback_name = '404-error-img.png'

    try:
        resolved = _safe_resolve_under_root(images_root, path)
        if os.path.isfile(resolved):
            return serve(request, path, document_root=images_root)
    except Exception:
        # Treat any traversal / resolution issue as missing.
        pass

    # Fallback (if present). If it's missing for any reason, return 404.
    try:
        resolved_fallback = _safe_resolve_under_root(images_root, fallback_name)
        if os.path.isfile(resolved_fallback):
            return serve(request, fallback_name, document_root=images_root)
    except Exception:
        pass

    return HttpResponse('Not Found', status=404)


def serve_react_app(request, path=None):
    """Serve the React app's index.html for all routes"""
    # Never serve the SPA shell for sensitive paths (e.g. scanners probing for /.env).
    # This avoids misleading 200s and ensures upstream protection even if middleware order changes.
    try:
        req_path = (getattr(request, 'path', '') or '').lower()
        if req_path.startswith('/.env') or '/.' in req_path:
            return HttpResponse('Not Found', status=404)
    except Exception:
        pass

    candidate_paths = [
        os.path.join(WEBSITE_BUILD_PATH, 'index.html'),
        os.path.join(settings.BASE_DIR, 'index.html'),
    ]

    for build_path in candidate_paths:
        if os.path.exists(build_path):
            with open(build_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Optional diagnostics injection (disabled by default).
            # This avoids shipping debug scripts in production unless explicitly enabled.
            if getattr(settings, 'ENABLE_BLOGS_DIAGNOSTICS', False):
                diag_tag = '<script defer="defer" src="/js/blogs-diagnostics.js"></script>'
                if diag_tag not in content:
                    main_tag = '<script defer="defer" src="/static/js/main.'
                    idx = content.find(main_tag)
                    if idx != -1:
                        content = content[:idx] + diag_tag + "\n" + content[idx:]
                    else:
                        # Fallback: append before closing head.
                        content = content.replace('</head>', diag_tag + "\n</head>")
            return HttpResponse(content, content_type='text/html')

    return HttpResponse('Build folder not found. Please run npm run build first.', status=404)

def serve_react_admin_panel(request, path=None):
    """Serve the React admin panel's index.html for all routes"""
    candidate_paths = [
        os.path.join(ADMIN_BUILD_PATH, 'index.html'),
        os.path.join(ADMIN_BUILD_PATH, 'build', 'index.html'),
    ]

    for build_path in candidate_paths:
        if os.path.exists(build_path):
            with open(build_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HttpResponse(content, content_type='text/html')

    return HttpResponse('Build folder not found. Please run npm run build first.', status=404)

def serve_build_static(request, path):
    """Serve static files from the React build folder"""
    # The path comes as 'css/main.48ab48a6.css' or 'js/main.832bbcc1.js'
    # We need to construct the full path to build/static/
    file_path = os.path.join(WEBSITE_BUILD_PATH, 'static', path)
    
    if os.path.exists(file_path):
        # Determine content type based on file extension
        if path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif path.endswith('.svg'):
            content_type = 'image/svg+xml'
        else:
            content_type = 'application/octet-stream'
        
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    else:
        return HttpResponse(f'File not found: {file_path}', status=404)

def serve_admin_static(request, path):
    """Serve static files from the React admin panel build folder"""
    # The path comes as 'css/main.48ab48a6.css' or 'js/main.832bbcc1.js'
    # We need to construct the full path to admin panel static/
    file_path = os.path.join(ADMIN_BUILD_PATH, 'static', path)
    
    if os.path.exists(file_path):
        # Some older admin builds hard-code absolute API origins like
        # https://ingredientiq.ai/master, which breaks when the site is served
        # from https://www.ingredientiq.ai due to CSP/CORS. Rewrite those to
        # same-origin relative paths at serve time.
        if path.endswith('.js'):
            try:
                with open(file_path, 'rb') as f:
                    raw = f.read()
                text = raw.decode('utf-8', errors='ignore')
                rewritten = text
                rewritten = rewritten.replace('https://ingredientiq.ai/master', '/master')
                rewritten = rewritten.replace('https://ingredientiq.ai/web', '/web')
                rewritten = rewritten.replace('https://ingredientiq.ai/foodapp', '/foodapp')
                if rewritten != text:
                    return HttpResponse(rewritten, content_type='application/javascript; charset=utf-8')
            except Exception:
                # Fall back to raw file serving on any failure.
                pass

        # Determine content type based on file extension
        if path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif path.endswith('.svg'):
            content_type = 'image/svg+xml'
        else:
            content_type = 'application/octet-stream'

        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    else:
        return HttpResponse(f'File not found: {file_path}', status=404)

def serve_logo(request, filename):
    """Serve logo files from the React build folder"""
    file_path = os.path.join(WEBSITE_BUILD_PATH, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='image/png')
    else:
        return HttpResponse('Logo not found', status=404)

urlpatterns = [
    # Liveness + readiness (recommended for Railway healthcheck: /readyz)
    path('healthz', healthz, name='healthz'),
    path('healthz/', healthz),
    path('readyz', readyz, name='readyz'),
    path('readyz/', readyz),

    # Back-compat: previous Railway healthcheck path
    path('api/health/', healthz, name='health-check'),
    
    # ==========================================================================
    # SEO & DISCOVERY ROUTES (Dynamic, Django-generated)
    # ==========================================================================
    # Sitemap - XML sitemap index with all content types
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # RSS/Atom Feeds
    path('blog/feed/rss/', LatestBlogsFeed(), name='blog-feed-rss'),
    path('blog/feed/atom/', LatestBlogsAtomFeed(), name='blog-feed-atom'),
    path('blog/feed/', LatestBlogsFeed(), name='blog-feed'),  # Default to RSS
    path('blog/category/<slug:slug>/feed/', CategoryFeed(), name='category-feed'),
    path('blog/tag/<slug:slug>/feed/', TagFeed(), name='tag-feed'),
    
    # Dynamic SEO files (robots.txt, llms.txt, etc.)
    path('robots.txt', robots_txt, name='robots-txt'),
    path('llms.txt', llms_txt, name='llms-txt'),
    path('humans.txt', humans_txt, name='humans-txt'),
    path('.well-known/security.txt', security_txt, name='security-txt'),
    
    # CKEditor 5 URLs (for rich text editor)
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    
    # ==========================================================================
    # CORE APPLICATION ROUTES
    # ==========================================================================
    # Media files - must come before catch-all routes
    path('media/<path:path>', lambda request, path: serve(request, path, document_root=settings.MEDIA_ROOT), name='media'),
    
    path('launch',TemplateView.as_view(template_name='ingredient-iq-revised.html'),name='landing'),
    path('admin/', admin.site.urls),  # Django admin at /admin/
    # foodinfo removed - mobile app terminated
    path('accounts/', include('allauth.urls')),
    path('master/',include('panel.urls')),
    path('web/',include('Website.urls')),
    path('firebase-messaging-sw.js', lambda request: serve(request, 'firebase-messaging-sw.js', document_root=settings.STATIC_ROOT)),
    
    # Django admin static files - HIGH PRIORITY (must come before main app static files)
    path('admin/static/<path:path>', serve_admin_static, name='admin-static'),
    path('admin/assets/<path:path>', serve_admin_static, name='admin-assets'),
    path('admin/css/<path:path>', serve_admin_static, name='admin-css'),
    path('admin/js/<path:path>', serve_admin_static, name='admin-js'),
    path('admin/images/<path:path>', serve_admin_static, name='admin-images'),
    path('admin/manifest.json', lambda request: serve(request, 'manifest.json', document_root=ADMIN_BUILD_PATH)),
    
    # Serve static files from build folder - HIGH PRIORITY
    # Handle all static file requests from React build (uses new frontend paths with fallback)
    path('static/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'static'))),
    path('assets/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'static'))),
    path('css/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'css'))),
    path('js/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'js'))),
    path('images/<path:path>', serve_website_image, name='website-images'),
    path('manifest.json', lambda request: serve(request, 'manifest.json', document_root=WEBSITE_BUILD_PATH)),
    path('logo192.png', lambda request: serve_logo(request, 'logo192.png')),
    path('logo512.png', lambda request: serve_logo(request, 'logo512.png')),
    
    # Serve React build static files with correct paths
    path('static/css/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'static', 'css'))),
    path('static/js/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'static', 'js'))),
    path('static/media/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'static', 'media'))),
    
    # Control panel static files - HIGH PRIORITY (must come before main app static files)
    path('control-panel/static/<path:path>', serve_admin_static, name='control-panel-static'),
    path('control-panel/assets/<path:path>', serve_admin_static, name='control-panel-assets'),
    path('control-panel/css/<path:path>', serve_admin_static, name='control-panel-css'),
    path('control-panel/js/<path:path>', serve_admin_static, name='control-panel-js'),
    path('control-panel/images/<path:path>', serve_admin_static, name='control-panel-images'),
    path('control-panel/manifest.json', lambda request: serve(request, 'manifest.json', document_root=ADMIN_BUILD_PATH)),
    
    # React admin panel - moved to /adminpanel/ to avoid conflict with Django admin
    path('control-panel/', serve_react_admin_panel, name='react-admin-panel'),
    path('control-panel/<path:path>', serve_react_admin_panel, name='react-admin-panel-catch-all'),
    
    # ==========================================================================
    # PUBLIC BLOG ROUTES (Server-side rendered for SEO)
    # ==========================================================================
    # Blog detail page - serves full HTML with meta tags for SEO/social sharing
    # This MUST come before the React catch-all to ensure proper rendering
    path('blog/<slug:slug>/', blog_detail_view, name='blog-detail-public'),
    
    # Serve the main React app at root (catch-all for React routing)
    path('', serve_react_app, name='react-app'),
    # Catch-all route for React app sub-routes (must be last)
    path('<path:path>', serve_react_app, name='react-app-catch-all'),
]

# Serve media files in development (uploaded files like profile pictures, images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
