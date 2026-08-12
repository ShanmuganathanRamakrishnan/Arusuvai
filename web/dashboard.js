// web/dashboard.js — the auth-gated dashboard: saved profile + POST /api/plan.
//
// Visually reworked 2026-07-25 porting the Claude Design canvas
// "Arusuvai Dashboard.dc.html". The canvas mocks a full day of three meals
// (breakfast/lunch/dinner) with a demo "Plan outcome" switcher toggling
// between fabricated success/decline states -- neither ported as-is:
// core.planner.plan.plan_meal solves one (region, meal_slot) plate per call,
// not a day, and there is no real "north_indian breakfast" or
// "south_indian dinner" template yet (see CLAUDE.md's build-status table),
// so a fabricated three-meal day would overclaim what the real engine does
// today. The outcome switcher was a prototyping affordance, not a feature --
// this page's success/decline state is whichever POST /api/plan actually
// returns. Only the visual language (kolam background, tag pills, the
// serif headline+sentence pattern, the "why we stopped" callout) was ported.
//
// This file computes NOTHING nutritional, same constraint as onboarding.js.
// The plate-picker and the plan success/decline rendering are unchanged in
// substance from before this rework -- every number is a field off the real
// POST /api/plan response.
//
// Split 2026-08-12 (D14) into five files, structure only, zero behavior
// change: copy/label tables moved to dashboard-copy.js, the success-view
// renderer to dashboard-success.js, the decline-view renderer to
// dashboard-decline.js, and the shared kolam background to kolam.js. What
// remains here is the state/API module -- talks to the server, holds page
// state, and hands data to the view modules. It never touches the DOM
// directly except for the gate/loading elements this file itself owns.

(() => {
  "use strict";

  const API_BASE = ArusuvaiAuth.API_BASE;

  const gateLoadingEl = document.getElementById("dashGateLoading");
  const noProfileEl = document.getElementById("dashNoProfile");
  const mainEl = document.getElementById("dashMain");

  // Shared header (web/header.js), "authenticated" state. `current` drops
  // the Dashboard self-link; this page is it.
  ArusuvaiHeader.init({
    state: "authenticated",
    current: "dashboard",
    onLogout: async () => {
      await ArusuvaiAuth.logout();
      window.location.href = "onboarding.html";
    },
  });

  let profile = null; // the saved profile this page renders and plans against

  // ------------------------------------------------------------------
  // Auth gate: unauthenticated visitors are redirected to onboarding.html
  // (this project's real signup/login entry point — see its step 6 and its
  // ?next=dashboard handling), not shown a dashboard shell first.
  // ------------------------------------------------------------------

  async function init() {
    ArusuvaiKolam.render();

    let user;
    try {
      user = await ArusuvaiAuth.me();
    } catch {
      user = null;
    }

    if (!user) {
      window.location.href = "onboarding.html?next=dashboard";
      return;
    }

    ArusuvaiHeader.render("authenticated", user);

    try {
      profile = await ArusuvaiAuth.getProfile();
    } catch {
      profile = null;
    }

    gateLoadingEl.hidden = true;
    if (!profile) {
      noProfileEl.hidden = false;
      return;
    }

    mainEl.hidden = false;
    ArusuvaiDashboardSuccess.renderProfileTags(profile);
  }

  // ------------------------------------------------------------------
  // Plate picker + POST /api/plan
  // ------------------------------------------------------------------

  const generateBtn = document.getElementById("dashGenerate");
  const regenerateBtn = document.getElementById("dashRegenerate");
  const tryAnotherBtn = document.getElementById("dashTryAnother");
  const endpointLabel = document.getElementById("dashEndpointLabel");
  const planLoadingEl = document.getElementById("obPlanLoading");
  const planNetworkErrorEl = document.getElementById("obPlanNetworkError");
  const planSuccessEl = document.getElementById("obPlanSuccess");
  const planDeclineEl = document.getElementById("obPlanDecline");

  function collectPlate() {
    const raw = document.querySelector('input[name="plate"]:checked').value;
    const [region, meal_slot] = raw.split(":");
    return { region, meal_slot };
  }

  generateBtn.addEventListener("click", fetchPlan);
  regenerateBtn.addEventListener("click", fetchPlan);
  tryAnotherBtn.addEventListener("click", () => {
    planDeclineEl.hidden = true;
    document.getElementById("obPlatePicker").scrollIntoView({ behavior: "smooth", block: "center" });
  });

  async function fetchPlan() {
    endpointLabel.textContent = `Calling ${API_BASE}/api/plan`;
    planLoadingEl.hidden = false;
    planNetworkErrorEl.hidden = true;
    planSuccessEl.hidden = true;
    planDeclineEl.hidden = true;

    const plate = collectPlate();
    const body = Object.assign(
      {
        weight_kg: profile.weight_kg,
        height_cm: profile.height_cm,
        age_years: profile.age_years,
        sex: profile.sex,
        activity: profile.activity,
        goal: profile.goal,
        diet: profile.diet,
        clinical_flags: profile.clinical_flags,
      },
      plate
    );

    let data;
    try {
      const res = await fetch(`${API_BASE}/api/plan`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.status === 422) {
        const errBody = await res.json().catch(() => null);
        const detail = errBody && errBody.detail
          ? (Array.isArray(errBody.detail) ? errBody.detail.map((d) => d.msg || JSON.stringify(d)).join("; ") : errBody.detail)
          : "Invalid input.";
        throw new Error(`The API rejected this profile: ${detail}`);
      }
      if (!res.ok) throw new Error(`The API returned an unexpected error (HTTP ${res.status}).`);
      data = await res.json();
    } catch (err) {
      const message = err instanceof TypeError
        ? `Couldn't reach the plan API at ${API_BASE}. Is it running? Start it with: uvicorn api.main:app --reload`
        : err.message;
      planLoadingEl.hidden = true;
      planNetworkErrorEl.hidden = false;
      planNetworkErrorEl.textContent = message;
      return;
    }

    planLoadingEl.hidden = true;
    if (data.passed) {
      ArusuvaiDashboardSuccess.render(data, plate, profile);
    } else {
      ArusuvaiDashboardDecline.render(data, plate);
    }
  }

  init();
})();
