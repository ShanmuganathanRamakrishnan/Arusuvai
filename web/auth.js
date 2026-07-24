// web/auth.js — shared account/session calls + the auth-modal wiring, used
// by both onboarding.html and dashboard.html.
//
// This file computes nothing nutritional (same constraint onboarding.js
// states for itself). It only does two things: call the five /api/auth/*
// and /api/profile endpoints with `credentials: "include"` (required for the
// signed session cookie to survive a cross-port fetch between the static
// page and the API — see api/main.py's CORS comment), and wire the auth
// modal markup that already existed, decoratively, on index.html
// (DESIGN_SYSTEM.md's "Auth modal" row) to those real calls instead of a
// no-op paint() toggle.

(() => {
  "use strict";

  const API_BASE = "http://localhost:8000";

  async function apiFetch(path, options) {
    const res = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return res;
  }

  const ArusuvaiAuth = {
    API_BASE,

    // null on 401 (not signed in) rather than throwing -- "am I signed in"
    // is an expected, common outcome, not an error.
    async me() {
      const res = await apiFetch("/api/auth/me");
      if (res.status === 401) return null;
      if (!res.ok) throw new Error(`GET /api/auth/me failed (HTTP ${res.status})`);
      return res.json();
    },

    // null on 404 (signed in, nothing saved yet) -- also an expected outcome.
    async getProfile() {
      const res = await apiFetch("/api/profile");
      if (res.status === 404) return null;
      if (res.status === 401) return null;
      if (!res.ok) throw new Error(`GET /api/profile failed (HTTP ${res.status})`);
      return res.json();
    },

    async saveProfile(profile) {
      const res = await apiFetch("/api/profile", { method: "PUT", body: JSON.stringify(profile) });
      if (!res.ok) throw await _apiError(res);
      return res.json();
    },

    async signup(email, password, profile) {
      const res = await apiFetch("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify(profile ? { email, password, profile } : { email, password }),
      });
      if (!res.ok) throw await _apiError(res);
      return res.json();
    },

    async login(email, password) {
      const res = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw await _apiError(res);
      return res.json();
    },

    async logout() {
      await apiFetch("/api/auth/logout", { method: "POST" });
    },

    // Wires up the auth-modal markup copied from index.html: same IDs
    // (authOverlay, authTitle, ...), same signin/signup toggle, but a real
    // submit handler in place of index.html's decorative `onsubmit="return
    // false"`. `opts.getProfile()` (optional) supplies a profile to attach
    // to a signup call in progress -- used by onboarding's step-6 hinge, not
    // by dashboard's cold-entry gate, which has nothing to attach yet.
    initAuthModal(opts) {
      const overlay = document.getElementById("authOverlay");
      if (!overlay) return { open: () => {} };

      const titleEl = document.getElementById("authTitle");
      const subEl = document.getElementById("authSub");
      const ctaEl = document.getElementById("authCta");
      const switchLabel = document.getElementById("authSwitchLabel");
      const switchBtn = document.getElementById("authSwitch");
      const closeBtn = document.getElementById("authClose");
      const formEl = overlay.querySelector("form.fields");
      const emailEl = document.getElementById("authEmail");
      const passwordEl = document.getElementById("authPassword");
      const errorEl = document.getElementById("authError");

      let mode = opts.initialMode || "signin";

      const paint = () => {
        const signup = mode === "signup";
        titleEl.textContent = signup ? "Create your account" : "Welcome back";
        subEl.textContent = signup
          ? "Save this profile and see your plan."
          : "Sign in to pick up your plan where you left off.";
        ctaEl.textContent = signup ? "Create account" : "Sign in";
        switchLabel.textContent = signup ? "Already have an account?" : "New to Arusuvai?";
        switchBtn.textContent = signup ? "Sign in" : "Create an account";
        errorEl.hidden = true;
        errorEl.textContent = "";
      };

      const open = (m) => {
        mode = m || mode;
        paint();
        overlay.hidden = false;
        emailEl.focus();
      };
      const close = () => {
        overlay.hidden = true;
      };

      switchBtn.addEventListener("click", () => {
        mode = mode === "signup" ? "signin" : "signup";
        paint();
      });
      closeBtn.addEventListener("click", close);
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) close();
      });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !overlay.hidden) close();
      });

      formEl.addEventListener("submit", async (e) => {
        e.preventDefault();
        errorEl.hidden = true;
        const email = emailEl.value.trim();
        const password = passwordEl.value;
        ctaEl.disabled = true;
        try {
          const profile = mode === "signup" && opts.getProfile ? opts.getProfile() : undefined;
          const data =
            mode === "signup"
              ? await ArusuvaiAuth.signup(email, password, profile)
              : await ArusuvaiAuth.login(email, password);
          close();
          if (opts.onAuthed) await opts.onAuthed(data);
        } catch (err) {
          errorEl.hidden = false;
          errorEl.textContent = err.message || "Something went wrong.";
        } finally {
          ctaEl.disabled = false;
        }
      });

      return { open, close };
    },
  };

  async function _apiError(res) {
    const body = await res.json().catch(() => null);
    const detail = body && body.detail ? body.detail : `HTTP ${res.status}`;
    return new Error(detail);
  }

  window.ArusuvaiAuth = ArusuvaiAuth;
})();
