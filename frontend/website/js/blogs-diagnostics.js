(function () {
  'use strict';

  // Only run on the SPA blogs list route.
  // Note: /blog/<slug>/ is server-rendered and should not be affected.
  var path = (window.location && window.location.pathname) || '';
  if (!(path === '/blogs' || path.indexOf('/blogs/') === 0)) {
    return;
  }

  // Allow an emergency runtime opt-out (defaults to enabled).
  // Example: localStorage.setItem('blogs_diagnostics', '0')
  try {
    if (window.__DISABLE_BLOGS_DIAGNOSTICS__ === true) return;
    if (window.localStorage && window.localStorage.getItem('blogs_diagnostics') === '0') return;
  } catch (e) {
    // ignore
  }

  var diagId = (function () {
    try {
      return 'blogs_' + String(Date.now()) + '_' + Math.random().toString(16).slice(2);
    } catch (e) {
      return 'blogs_' + String(Date.now());
    }
  })();

  var hasLoggedFirstFailure = false;
  var hasRenderedFallback = false;

  function safeConsoleError() {
    try {
      // eslint-disable-next-line no-console
      console.error.apply(console, arguments);
    } catch (e) {
      // ignore
    }
  }

  function safeConsoleInfo() {
    try {
      // eslint-disable-next-line no-console
      console.info.apply(console, arguments);
    } catch (e) {
      // ignore
    }
  }

  function normalizeUrl(input) {
    try {
      if (input && typeof input === 'object' && input.url) {
        return new URL(input.url, window.location.origin);
      }
      if (typeof input === 'string') {
        return new URL(input, window.location.origin);
      }
    } catch (e) {
      // ignore
    }
    return null;
  }

  function isBlogsListApi(urlObj) {
    if (!urlObj) return false;
    // Match both absolute and relative forms.
    return urlObj.pathname === '/web/blogs/' || urlObj.pathname === '/web/blogs';
  }

  function ensureFallbackUI(reason) {
    if (hasRenderedFallback) return;
    hasRenderedFallback = true;

    try {
      var root = document.getElementById('root');
      if (!root) return;

      var overlay = document.createElement('div');
      overlay.setAttribute('data-blogs-fallback', '1');
      overlay.style.cssText = [
        'position:relative',
        'margin:24px auto',
        'max-width:900px',
        'padding:16px',
        'border:1px solid rgba(0,0,0,0.12)',
        'border-radius:12px',
        'background:#fff',
        'font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif'
      ].join(';');

      var title = document.createElement('h2');
      title.textContent = 'Unable to load posts. Try again.';
      title.style.cssText = 'margin:0 0 8px 0;font-size:20px;line-height:1.2;';

      var msg = document.createElement('p');
      msg.textContent = 'The blog list depends on the API endpoint /web/blogs/. Please refresh, and if it persists check your network/DNS and server logs.';
      msg.style.cssText = 'margin:0 0 10px 0;color:rgba(0,0,0,0.75)';

      var hint = document.createElement('p');
      hint.textContent = 'Diagnostic ID: ' + diagId;
      hint.style.cssText = 'margin:0 0 10px 0;color:rgba(0,0,0,0.6);font-size:12px;';

      var detail = document.createElement('pre');
      detail.textContent = reason ? String(reason) : '';
      detail.style.cssText = 'margin:0;padding:10px;border-radius:8px;background:rgba(0,0,0,0.04);white-space:pre-wrap;word-break:break-word;color:rgba(0,0,0,0.7)';

      overlay.appendChild(title);
      overlay.appendChild(msg);
      overlay.appendChild(hint);
      if (reason) overlay.appendChild(detail);

      // Prefer replacing the root contents to avoid a blank page.
      root.innerHTML = '';
      root.appendChild(overlay);
    } catch (e) {
      // ignore
    }
  }

  function logFirstFailure(payload) {
    if (hasLoggedFirstFailure) return;
    hasLoggedFirstFailure = true;

    var enriched = payload || {};
    try {
      enriched.diagId = diagId;
      enriched.ts = new Date().toISOString();
    } catch (e) {
      // ignore
    }

    safeConsoleError('[blogs] first load failure', enriched);

    var reason = '';
    try {
      reason = JSON.stringify(enriched, null, 2);
    } catch (e) {
      reason = String(enriched);
    }
    ensureFallbackUI(reason);
  }

  // --- Error boundary surrogate: capture render/runtime errors on /blogs.
  window.addEventListener('error', function (evt) {
    try {
      logFirstFailure({
        kind: 'window_error',
        message: evt && evt.message,
        filename: evt && evt.filename,
        lineno: evt && evt.lineno,
        colno: evt && evt.colno
      });
    } catch (e) {
      // ignore
    }
  });

  window.addEventListener('unhandledrejection', function (evt) {
    try {
      var reason = evt && evt.reason;
      logFirstFailure({
        kind: 'unhandledrejection',
        message: reason && (reason.message || String(reason))
      });
    } catch (e) {
      // ignore
    }
  });

  // If React fails to mount or crashes during initial render, the page can remain blank.
  // As a safety net, show a fallback if #root stays empty shortly after load.
  try {
    window.setTimeout(function () {
      if (hasRenderedFallback) return;
      var root = document.getElementById('root');
      if (!root) return;
      if (root.childNodes && root.childNodes.length > 0) return;
      logFirstFailure({
        kind: 'root_empty_timeout',
        message: 'Root did not render any content within timeout'
      });
    }, 4000);
  } catch (e) {
    // ignore
  }

  // --- Network failure logging (fetch + XHR)
  function instrumentFetch() {
    if (!window.fetch) return;
    var originalFetch = window.fetch;

    window.fetch = function (input, init) {
      var urlObj = normalizeUrl(input);
      var isTarget = isBlogsListApi(urlObj);

      return originalFetch.call(this, input, init).then(
        function (res) {
          if (isTarget && res && res.ok === false) {
            logFirstFailure({
              kind: 'fetch',
              url: urlObj ? urlObj.toString() : String(input),
              host: urlObj ? urlObj.host : null,
              status: res.status,
              statusText: res.statusText
            });
          }
          return res;
        },
        function (err) {
          if (isTarget) {
            logFirstFailure({
              kind: 'fetch_exception',
              url: urlObj ? urlObj.toString() : String(input),
              host: urlObj ? urlObj.host : null,
              message: err && (err.message || String(err))
            });
          }
          throw err;
        }
      );
    };
  }

  function instrumentXHR() {
    if (!window.XMLHttpRequest || !window.XMLHttpRequest.prototype) return;

    var originalOpen = window.XMLHttpRequest.prototype.open;
    var originalSend = window.XMLHttpRequest.prototype.send;

    window.XMLHttpRequest.prototype.open = function (method, url) {
      try {
        this.__blogsDiagUrl = url;
      } catch (e) {
        // ignore
      }
      return originalOpen.apply(this, arguments);
    };

    window.XMLHttpRequest.prototype.send = function () {
      var xhr = this;

      function onDone() {
        try {
          var urlObj = normalizeUrl(xhr.__blogsDiagUrl);
          if (!isBlogsListApi(urlObj)) return;

          // If status is 0, it usually means network error/blocked/cors/dns.
          if (xhr.status === 0 || xhr.status >= 400) {
            logFirstFailure({
              kind: 'xhr',
              url: urlObj ? urlObj.toString() : String(xhr.__blogsDiagUrl || ''),
              host: urlObj ? urlObj.host : null,
              status: xhr.status
            });
          }
        } catch (e) {
          // ignore
        }
      }

      try {
        xhr.addEventListener('loadend', onDone);
      } catch (e) {
        // ignore
      }

      return originalSend.apply(this, arguments);
    };
  }

  safeConsoleInfo('[blogs] diagnostics enabled', { diagId: diagId });
  instrumentFetch();
  instrumentXHR();
})();
