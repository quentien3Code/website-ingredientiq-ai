# Build Folder Serving Guide

## Overview
The Django backend is now configured to serve the React build folder at the `/ai-ingredients` basename.

## Configuration

### URL Configuration
The build folder is served through the following URL patterns in `foodanalysis/urls.py`:

```python
# Serve the React app at root URL
path('', serve_react_app),

# Serve the React app at /ai-ingredients/ base
path('ai-ingredients/', serve_react_app, name='ai-ingredients'),

# Serve static assets (CSS, JS, images) from the build folder
path('ai-ingredients/<path:path>', serve, {
    'document_root': os.path.join(settings.BASE_DIR, 'build')
}),
```

**Note**: The root path (`''`) is placed after the admin and API routes to ensure they take precedence over the React app.

### How It Works

1. **Main Route (`/ai-ingredients/`)**: 
   - Serves the `index.html` file from the build folder
   - Handles React Router client-side routing
   - Returns the main React app

2. **Static Assets (`/ai-ingredients/<path>`)**: 
   - Serves CSS, JS, images, and other static files
   - Uses Django's built-in `serve` view
   - Serves files directly from the build folder

## File Structure

```
foodapp_backend/
├── build/                    # React build folder
│   ├── index.html           # Main React app
│   ├── static/              # Static assets
│   │   ├── css/            # CSS files
│   │   ├── js/             # JavaScript files
│   │   └── media/          # Images and other media
│   ├── manifest.json        # PWA manifest
│   └── robots.txt          # SEO robots file
└── foodanalysis/
    └── urls.py             # URL configuration
```

## Accessing the App

- **Main App (Root)**: `http://your-domain.com/`
- **Main App (Base)**: `http://your-domain.com/ai-ingredients/`
- **Static Assets**: `http://your-domain.com/ai-ingredients/static/css/main.css`
- **Images**: `http://your-domain.com/ai-ingredients/static/media/logo.png`

## React Router Support

The configuration supports React Router's client-side routing:
- **Root routes** (`/`, `/dashboard`, `/profile`) will serve the React app
- **Base routes** (`/ai-ingredients/`, `/ai-ingredients/dashboard`) will serve the React app
- React Router will handle the routing on the client side
- Static assets are served directly without going through React Router

## Production Considerations

For production deployment, consider:

1. **Static File Serving**: Use a web server like Nginx to serve static files directly
2. **Caching**: Set appropriate cache headers for static assets
3. **Compression**: Enable gzip compression for better performance
4. **CDN**: Consider using a CDN for static assets

## Development

To update the build:
1. Run `npm run build` in your React project
2. Copy the build folder to `foodapp_backend/build/`
3. The Django server will automatically serve the updated files

## Error Handling

If the build folder is not found, the server will return a 404 error with the message:
"Build folder not found. Please run npm run build first."
