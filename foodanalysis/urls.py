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

# Import standalone health check (isolated, no dependencies)
from .health import health

# =============================================================================
# Frontend Asset Paths Configuration
# =============================================================================
# Organized structure: frontend/website/ and frontend/admin/

WEBSITE_BUILD_PATH = os.path.join(settings.BASE_DIR, 'frontend', 'website')
ADMIN_BUILD_PATH = os.path.join(settings.BASE_DIR, 'frontend', 'admin')


def serve_react_app(request, path=None):
    """Serve the React app's index.html for all routes"""
    build_path = os.path.join(WEBSITE_BUILD_PATH, 'index.html')
    try:
        with open(build_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
        return HttpResponse('Build folder not found. Please run npm run build first.', status=404)

def serve_react_admin_panel(request, path=None):
    """Serve the React admin panel's index.html for all routes"""
    build_path = os.path.join(ADMIN_BUILD_PATH, 'index.html')
    try:
        with open(build_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/html')
    except FileNotFoundError:
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

def health_check(request):
    """Health check endpoint for Railway deployment - always returns 200"""
    return HttpResponse('OK', status=200)

urlpatterns = [
    # Health check for Railway - simple endpoint, no database dependency
    path('api/health/', health_check, name='health-check'),
    
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
    path('images/<path:path>', lambda request, path: serve(request, path, document_root=os.path.join(WEBSITE_BUILD_PATH, 'images'))),
    path('manifest.json', lambda request: serve(request, 'manifest.json', document_root=WEBSITE_BUILD_PATH)),
    path('robots.txt', lambda request: serve(request, 'robots.txt', document_root=WEBSITE_BUILD_PATH)),
    path('logo192.png', lambda request: serve_logo(request, 'logo192.png')),
    path('logo512.png', lambda request: serve_logo(request, 'logo512.png')),
    
    # SEO & Discovery Files (NEW)
    path('sitemap.xml', lambda request: serve(request, 'sitemap.xml', document_root=WEBSITE_BUILD_PATH)),
    path('llms.txt', lambda request: serve(request, 'llms.txt', document_root=WEBSITE_BUILD_PATH)),
    path('humans.txt', lambda request: serve(request, 'humans.txt', document_root=WEBSITE_BUILD_PATH)),
    path('.well-known/security.txt', lambda request: serve(request, 'security.txt', document_root=os.path.join(WEBSITE_BUILD_PATH, '.well-known'))),
    
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
    
    # Serve the main React app at root (catch-all for React routing)
    path('', serve_react_app, name='react-app'),
    # Catch-all route for React app sub-routes (must be last)
    path('<path:path>', serve_react_app, name='react-app-catch-all'),
]
