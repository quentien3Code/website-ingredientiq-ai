/**
 * API Host Normalizer (website)
 *
 * The website bundle includes absolute API URLs like https://ingredientiq.ai/web/...
 * When you're browsing via the Railway domain (or any other hostname), those calls can
 * fail and surface as "Network Error".
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

  const originalXHROpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, async, user, password) {
    return originalXHROpen.call(this, method, rewriteUrl(url), async !== false, user, password);
  };

  const originalFetch = window.fetch;
  window.fetch = function (url, options) {
    return originalFetch.call(this, rewriteUrl(url), options);
  };
})();
