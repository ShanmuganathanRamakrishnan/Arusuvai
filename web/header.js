// web/header.js — the one site header, in three explicit states.
//
// Why this file exists
// --------------------
//
// The three routes each hand-rolled their own header markup, and the result
// was three different navs that nobody had decided on:
//
//   index.html      How it works · Get your targets · Sign in · Sign up
//   onboarding.html (nothing at all)
//   dashboard.html  Edit profile · Signed in as <email> · Log out
//
// The onboarding case is the one that gives it away as drift rather than
// design: a signed-in user midway through the wizard had no way to reach Log
// out, or anything else, because that page's auth bar only appeared when a
// session existed and the page had no other nav to fall back on. Three
// hand-written navs cannot disagree if there is only one.
//
// The three states, and why each contains what it does
// ----------------------------------------------------
//
//   "anonymous"      How it works · Get your targets · Sign in · Sign up.
//                    A visitor with no session. This is the marketing nav.
//
//   "onboarding"     Logo, plus "Signed in as <email>" and Log out when a
//                    session exists — and nothing else, ever.
//
//                    The omission is deliberate, not an oversight to fix
//                    later. The wizard is a six-step flow holding unsaved
//                    profile state in memory; every nav link is a way to
//                    lose a half-filled form to a stray click, and none of
//                    them lead anywhere the flow doesn't already reach (step
//                    6 IS the sign-in point, so an anonymous visitor needs no
//                    "Sign in" link). Log out is the single exception,
//                    because being signed into an account with no visible way
//                    out is worse than the escape-hatch risk it introduces.
//
//   "authenticated"  Dashboard · Edit profile · <email> · Log out.
//                    A signed-in visitor on a page that is not the wizard.
//                    The self-link is dropped via `current`, so the dashboard
//                    does not offer a link to itself.
//
// The brand stays in each page's static HTML rather than being rendered here.
// Two reasons: it must not depend on JavaScript, and
// tests/test_web_wizard_layout.py measures the brand's left edge against the
// content container with JS disabled — the check that catches a route setting
// its own width. A JS-rendered brand would make that route unmeasurable.

(() => {
  "use strict";

  const STATES = ["anonymous", "onboarding", "authenticated"];

  let opts = {};

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function markup(state, user, current) {
    if (state === "onboarding") {
      if (!user) return "";
      return (
        `<span class="hdr-email" id="hdrUserEmail">Signed in as ${esc(user.email)}</span>` +
        `<button type="button" class="btn btn-link" id="hdrLogout">Log out</button>`
      );
    }
    if (state === "authenticated") {
      const dash =
        current === "dashboard"
          ? ""
          : `<a href="dashboard.html" class="btn btn-link" id="hdrDashboard">Dashboard</a>`;
      return (
        dash +
        `<a href="onboarding.html" class="btn btn-link" id="hdrEditProfile">Edit profile</a>` +
        `<span class="hdr-email" id="hdrUserEmail">${esc(user ? user.email : "")}</span>` +
        `<button type="button" class="btn btn-link" id="hdrLogout">Log out</button>`
      );
    }
    // anonymous
    const how =
      current === "landing"
        ? `<a href="#how" class="hide-sm" id="hdrHow">How it works</a>`
        : `<a href="index.html#how" class="hide-sm" id="hdrHow">How it works</a>`;
    return (
      how +
      `<a href="onboarding.html" class="hide-sm" id="hdrTargets">Get your targets</a>` +
      `<button type="button" class="btn btn-link" id="hdrSignin">Sign in</button>` +
      `<button type="button" class="btn btn-primary" id="hdrSignup">Sign up</button>`
    );
  }

  const ArusuvaiHeader = {
    // init() records the handlers once; render() may then be called as often
    // as the session changes. Listeners are re-bound on every render because
    // rendering replaces the nodes -- binding once outside would leave the
    // second render's buttons dead.
    init(o) {
      opts = o || {};
      this.render(opts.state, opts.user || null);
    },

    render(state, user) {
      if (STATES.indexOf(state) === -1) {
        throw new Error(`unknown header state "${state}" (expected one of ${STATES.join(", ")})`);
      }
      const host = document.getElementById("appNav");
      if (!host) return;
      const header = document.getElementById("siteHeader");
      if (header) header.dataset.headerState = state;
      host.innerHTML = markup(state, user, opts.current);

      const bind = (id, fn) => {
        const el = document.getElementById(id);
        if (el && fn) el.addEventListener("click", fn);
      };
      bind("hdrSignin", opts.onSignin);
      bind("hdrSignup", opts.onSignup);
      bind("hdrLogout", opts.onLogout);
    },
  };

  window.ArusuvaiHeader = ArusuvaiHeader;
})();
