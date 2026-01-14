(function () {
  function isAppRoute() {
    try {
      var path = (window.location && window.location.pathname) || "";
      return path === "/app" || path.indexOf("/app/") === 0;
    } catch (e) {
      return false;
    }
  }

  function replacePricingSection() {
    var pricing = document.querySelector("section.pricing");
    if (!pricing) return;

    pricing.innerHTML =
      '<div class="container">' +
      '  <div class="section-title text-center mxw-565 mx-auto">' +
      '    <h2 class="text-center">Plans</h2>' +
      '    <p class="text-center">Four simple plans: Free, Premium, Family/Team, and Enterprise.</p>' +
      '  </div>' +
      '  <div class="table-responive">' +
      '    <table class="pricing-table">' +
      '      <thead>' +
      '        <tr>' +
      '          <th>Feature</th>' +
      '          <th>Free</th>' +
      '          <th>Premium</th>' +
      '          <th>Family/Team</th>' +
      '          <th>Enterprise</th>' +
      '        </tr>' +
      '      </thead>' +
      '      <tbody>' +
      '        <tr>' +
      '          <td class="plan-name">Plan</td>' +
      '          <td class="price">$0</td>' +
      '          <td class="price">&mdash;</td>' +
      '          <td class="price">&mdash;</td>' +
      '          <td class="price">&mdash;</td>' +
      '        </tr>' +
      '        <tr>' +
      '          <td>Barcode Scanning</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '        </tr>' +
      '        <tr>' +
      '          <td>Personalized preferences</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '        </tr>' +
      '        <tr>' +
      '          <td>Advanced insights</td>' +
      '          <td class="cross">\u2717</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '        </tr>' +
      '        <tr>' +
      '          <td>Team management</td>' +
      '          <td class="cross">\u2717</td>' +
      '          <td class="cross">\u2717</td>' +
      '          <td class="check">\u2713</td>' +
      '          <td class="check">\u2713</td>' +
      '        </tr>' +
      '        <tr>' +
      '          <td>Custom integrations</td>' +
      '          <td class="cross">\u2717</td>' +
      '          <td class="cross">\u2717</td>' +
      '          <td class="cross">\u2717</td>' +
      '          <td class="check">\u2713</td>' +
      '        </tr>' +
      '        <tr>' +
      '          <td></td>' +
      '          <td><a href="#" class="btn btn-dark rounded-5">Get Free</a></td>' +
      '          <td><a href="#" class="btn btn-accent">Contact Us</a></td>' +
      '          <td><a href="#" class="btn btn-accent">Contact Us</a></td>' +
      '          <td><a href="#" class="btn btn-accent">Contact Us</a></td>' +
      '        </tr>' +
      '      </tbody>' +
      '    </table>' +
      '  </div>' +
      '</div>';
  }

  function init() {
    if (!isAppRoute()) return;

    // Wait for the SPA to render the section.
    var attempts = 0;
    var timer = window.setInterval(function () {
      attempts += 1;
      if (document.querySelector("section.pricing")) {
        window.clearInterval(timer);
        replacePricingSection();
      } else if (attempts > 50) {
        window.clearInterval(timer);
      }
    }, 100);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
