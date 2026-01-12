/**
 * API Host Normalizer (website)
 *
 * Rewrites absolute API URLs (https://ingredientiq.ai, https://www.ingredientiq.ai)
 * to the current origin so navigation/API calls work on the Railway domain too.
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
