/**
 * API Override - ACTIVE
 * Redirects all API calls from production to localhost
 */
(function() {
    'use strict';
    
    const PRODUCTION_HOST = 'https://ingredientiq.ai';
    const LOCAL_HOST = 'http://localhost:8000';
    
    console.log('[API Override] ACTIVE - Redirecting API calls to localhost');
    
    // Override XMLHttpRequest.open (axios uses this)
    const originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        if (typeof url === 'string' && url.startsWith(PRODUCTION_HOST)) {
            url = url.replace(PRODUCTION_HOST, LOCAL_HOST);
            console.log('[API Override] Redirected to:', url);
        }
        return originalXHROpen.call(this, method, url, async !== false, user, password);
    };
    
    // Override fetch
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        if (typeof url === 'string' && url.startsWith(PRODUCTION_HOST)) {
            url = url.replace(PRODUCTION_HOST, LOCAL_HOST);
            console.log('[API Override] Fetch redirected to:', url);
        }
        return originalFetch.call(this, url, options);
    };
    
    console.log('[API Override] Ready - Login: admin@ingredientiq.ai / IQ@dmin2026!');
})();
