"""
Custom middleware for handling CORS and security headers
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers including Cross-Origin-Opener-Policy
    """
    
    def process_response(self, request, response):
        # Add Cross-Origin-Opener-Policy header
        response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        
        # Add Cross-Origin-Embedder-Policy header
        response['Cross-Origin-Embedder-Policy'] = 'unsafe-none'
        
        # Add other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class StaticFileMIMEMiddleware(MiddlewareMixin):
    """
    Middleware to ensure proper MIME types for static files
    """
    
    def process_response(self, request, response):
        # Check if this is a static file request
        if request.path.startswith('/static/') or request.path.startswith('/control-panel/static/'):
            # Set proper MIME types based on file extension
            if request.path.endswith('.js'):
                response['Content-Type'] = 'application/javascript'
            elif request.path.endswith('.css'):
                response['Content-Type'] = 'text/css'
            elif request.path.endswith('.png'):
                response['Content-Type'] = 'image/png'
            elif request.path.endswith('.jpg') or request.path.endswith('.jpeg'):
                response['Content-Type'] = 'image/jpeg'
            elif request.path.endswith('.svg'):
                response['Content-Type'] = 'image/svg+xml'
            elif request.path.endswith('.woff2'):
                response['Content-Type'] = 'font/woff2'
            elif request.path.endswith('.woff'):
                response['Content-Type'] = 'font/woff'
            elif request.path.endswith('.ttf'):
                response['Content-Type'] = 'font/ttf'
        
        return response
