/* Arusuvai landing — behaviour ported from the DCLogic component in
   Arusuvai Landing.dc.html to plain vanilla JS (no runtime, no build step).
   Everything here is presentation only; no nutrition quantity a user relies
   on is determined in this layer (see the calculator note below and CLAUDE.md). */
(function () {
  'use strict';

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------- kolam breathing background ---------------- */
  // Woven pulli-and-line dot grid. Two families of sinusoidal lines thread
  // around dots placed at the loop centres, matching the design's buildKolam().
  function buildKolam() {
    var W = 1200, H = 1400, g = 118, amp = g * 0.46, per = g * 2;
    var lines = [], dots = [], i = 0;
    var f = function (n) { return Math.round(n * 100) / 100; };
    for (var row = 0; row * g <= H + g; row++) {
      var y0 = row * g, ph = row % 2 ? Math.PI : 0, d = '';
      for (var x = 0; x <= W; x += 12) {
        var y = y0 + amp * Math.sin((x / per) * 2 * Math.PI + ph);
        d += (x === 0 ? 'M' : 'L') + f(x) + ' ' + f(y) + ' ';
      }
      lines.push({ d: d.trim(), i: i++ });
    }
    for (var col = 0; col * g <= W + g; col++) {
      var x0 = col * g, ph2 = col % 2 ? Math.PI : 0, d2 = '';
      for (var yy = 0; yy <= H; yy += 12) {
        var xx = x0 + amp * Math.sin((yy / per) * 2 * Math.PI + ph2);
        d2 += (yy === 0 ? 'M' : 'L') + f(xx) + ' ' + f(yy) + ' ';
      }
      lines.push({ d: d2.trim(), i: i++ });
    }
    for (var r = 0; r * g <= H + g; r++)
      for (var c = 0; c * g <= W + g; c++)
        dots.push([c * g - g / 2, r * g - g / 2]);
    return { lines: lines, dots: dots };
  }

  function renderKolam() {
    var host = document.getElementById('kolam');
    if (!host) return null;
    var k = buildKolam();
    var svgNS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 1200 1400');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');
    var dotStr = '';
    k.dots.forEach(function (p) { dotStr += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="4.6" fill="#B98416"></circle>'; });
    var pathEls = [];
    var lineStr = '';
    k.lines.forEach(function (l) {
      lineStr += '<path d="' + l.d + '" fill="none" stroke="#3A5A40" stroke-width="1.5" stroke-linecap="round" pathLength="1" style="stroke-dasharray:1;stroke-dashoffset:1"></path>';
    });
    svg.innerHTML = dotStr + lineStr;
    host.appendChild(svg);
    pathEls = Array.prototype.slice.call(svg.querySelectorAll('path'));

    if (reduce) {
      host.style.opacity = '0.16';
      pathEls.forEach(function (p) { p.style.strokeDashoffset = '0'; });
      return null;
    }

    // Breathing envelope over an 11s cycle: draw in -> hold -> unravel -> rest.
    var cycle = 11000, startT = performance.now();
    var smooth = function (t) { return t * t * (3 - 2 * t); };
    var envelope = function (t) {
      if (t < 0.42) return smooth(t / 0.42);
      if (t < 0.55) return 1;
      if (t < 0.9) return smooth(1 - (t - 0.55) / 0.35);
      return 0;
    };
    function frame(now) {
      var t = ((now - startT) % cycle) / cycle;
      var lp = envelope(t);
      host.style.opacity = (Math.round((0.03 + 0.15 * lp) * 100) / 100).toString();
      for (var j = 0; j < pathEls.length; j++) {
        var prog = Math.min(1, Math.max(0, lp * 1.4 - j * 0.012));
        pathEls[j].style.strokeDashoffset = (Math.round((1 - prog) * 1000) / 1000).toString();
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    return null;
  }

  /* ---------------- morphing headline ---------------- */
  // Cycles the word for "taste" across South Indian scripts, resolving on Tamil.
  function startMorph() {
    var seq = [
      { t: 'அறுசுவை', f: "'Noto Serif Tamil', serif", lang: 'Tamil' },
      { t: 'రుచి', f: "'Noto Serif Telugu', serif", lang: 'Telugu' },
      { t: 'ರುಚಿ', f: "'Noto Serif Kannada', serif", lang: 'Kannada' },
      { t: 'രുചി', f: "'Noto Serif Malayalam', serif", lang: 'Malayalam' }
    ];
    var wordEl = document.getElementById('morphWord');
    var langEl = document.getElementById('morphLang');
    if (!wordEl || !langEl) return;
    var idx = 0;
    var apply = function () {
      var cur = seq[idx];
      wordEl.textContent = cur.t;
      wordEl.style.fontFamily = cur.f;
      langEl.textContent = cur.lang;
    };
    apply();
    if (reduce) {
      setInterval(function () { idx = (idx + 1) % seq.length; apply(); }, 2500);
      return;
    }
    setInterval(function () {
      wordEl.style.opacity = '0';
      langEl.style.opacity = '0';
      setTimeout(function () {
        idx = (idx + 1) % seq.length;
        apply();
        wordEl.style.opacity = '1';
        langEl.style.opacity = '1';
      }, 520);
    }, 2500);
  }

  /* ---------------- sticky header blur on scroll ---------------- */
  function startHeader() {
    var header = document.getElementById('siteHeader');
    if (!header) return;
    var raf = null;
    var onScroll = function () {
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = null;
        var el = document.scrollingElement || document.documentElement;
        header.classList.toggle('scrolled', el.scrollTop > 6);
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------------- protein calculator (illustrative demo) ---------------- */
  // NOT the product's target engine — a public g/kg rule of thumb (Morton et
  // al.) shown to convey character. Real targets live in the Python backend.
  function startCalc() {
    var dock = document.getElementById('calcDock');
    var toggle = document.getElementById('calcToggle');
    var wIn = document.getElementById('calcWeight');
    var dIn = document.getElementById('calcDays');
    var targetEl = document.getElementById('calcTarget');
    var factorEl = document.getElementById('calcFactor');
    if (!dock || !toggle || !wIn || !dIn) return;

    toggle.addEventListener('click', function () {
      var open = dock.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    var recompute = function () {
      var w = Math.max(0, Math.min(250, parseInt(wIn.value, 10) || 0));
      var d = Math.max(0, Math.min(7, parseInt(dIn.value, 10) || 0));
      var factor = d <= 1 ? 1.2 : d <= 3 ? 1.4 : d <= 5 ? 1.6 : 1.8;
      targetEl.textContent = w > 0 ? String(Math.round(w * factor)) : '—';
      factorEl.textContent = factor.toFixed(1);
    };
    wIn.addEventListener('input', recompute);
    dIn.addEventListener('input', recompute);
    recompute();
  }

  /* ---------------- six-food bloom on scroll into view ---------------- */
  function startBloom() {
    var grid = document.getElementById('bloomGrid');
    if (!grid) return;
    if (reduce || !('IntersectionObserver' in window)) { grid.classList.add('in'); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { grid.classList.add('in'); io.disconnect(); }
      });
    }, { threshold: 0.35 });
    io.observe(grid);
  }

  /* ---------------- FAQ accordion ---------------- */
  function startFaq() {
    var list = document.getElementById('faqList');
    if (!list) return;
    list.addEventListener('click', function (e) {
      var btn = e.target.closest('.faq-q');
      if (!btn) return;
      var item = btn.parentNode;
      var open = item.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  /* ---------------- auth modal — real, wired to /api/auth/* via auth.js ---------------- */
  //
  // Was decorative (paint()-only, onsubmit="return false", no backend call).
  // Now uses the same ArusuvaiAuth.initAuthModal() that onboarding.html and
  // dashboard.html use (web/auth.js), so there is one signup/login/session
  // implementation, not three. The landing page collects no profile, so a
  // signup here never attaches one -- the "correct sequence" below is what
  // decides where a signed-in visitor lands.
  function startAuth() {
    var overlay = document.getElementById('authOverlay');
    if (!overlay || !window.ArusuvaiAuth) return;

    var openSignin = document.getElementById('btnSignin');
    var openSignup = document.getElementById('btnSignup');
    var dashboardBtn = document.getElementById('btnDashboard');
    var logoutBtn = document.getElementById('btnLogout');
    var emailLabel = document.getElementById('navUserEmail');

    function renderSignedIn(user) {
      openSignin.hidden = !!user;
      openSignup.hidden = !!user;
      dashboardBtn.hidden = !user;
      logoutBtn.hidden = !user;
      emailLabel.hidden = !user;
      emailLabel.textContent = user ? user.email : '';
    }

    // Correct sequence, not "always go to the same place":
    //   - a fresh signup has no profile yet -> onboarding.html (the five
    //     steps that don't need an account, then the save hinge that already
    //     has one).
    //   - a returning sign-in with a saved profile -> dashboard.html, skip
    //     onboarding entirely.
    //   - a returning sign-in with NO saved profile (account exists,
    //     onboarding was never finished) -> onboarding.html, same as a fresh
    //     signup, rather than a dashboard that has nothing to show.
    var modal = window.ArusuvaiAuth.initAuthModal({
      onAuthed: function (data) {
        window.location.href = data.profile ? 'dashboard.html' : 'onboarding.html';
      },
    });

    if (openSignin) openSignin.addEventListener('click', function () { modal.open('signin'); });
    if (openSignup) openSignup.addEventListener('click', function () { modal.open('signup'); });
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function () {
        window.ArusuvaiAuth.logout().then(function () { renderSignedIn(null); });
      });
    }

    window.ArusuvaiAuth.me().then(renderSignedIn).catch(function () { renderSignedIn(null); });
  }

  /* ---------------- early-access form (demo, no backend) ---------------- */
  function startEarly() {
    var form = document.getElementById('earlyForm');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button');
      if (btn) { btn.textContent = 'On the list ✓'; btn.disabled = true; }
    });
  }

  function init() {
    renderKolam();
    startMorph();
    startHeader();
    startCalc();
    startBloom();
    startFaq();
    startAuth();
    startEarly();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
