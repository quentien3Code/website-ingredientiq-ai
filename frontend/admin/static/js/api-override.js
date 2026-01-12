/**
 * API Host Normalizer
 *
 * The admin bundle was built with absolute API URLs like https://ingredientiq.ai/...
 * When you're testing on the Railway domain (or any other hostname), those requests
 * can fail and show up as "Network Error".
 *
 * This script rewrites those absolute URLs to the current origin so API calls stay
 * on the same host that served the page.
 */
(function () {
    'use strict';

    const REWRITE_FROM_HOSTS = [
        'https://ingredientiq.ai',
        'https://www.ingredientiq.ai',
    ];

    const TARGET_ORIGIN = window.location.origin;

    function rewriteUrl(url) {
        if (typeof url !== 'string') return url;
        for (const from of REWRITE_FROM_HOSTS) {
            if (url.startsWith(from)) {
                return TARGET_ORIGIN + url.slice(from.length);
            }
        }
        return url;
    }

    // Override XMLHttpRequest.open (axios uses this)
    const originalXHROpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, async, user, password) {
        return originalXHROpen.call(this, method, rewriteUrl(url), async !== false, user, password);
    };

    // Override fetch
    const originalFetch = window.fetch;
    window.fetch = function (url, options) {
        return originalFetch.call(this, rewriteUrl(url), options);
    };
})();
