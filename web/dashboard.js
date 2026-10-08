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

    // N11: choices kept from earlier visits. `null` means they could not be
    // loaded -- not "none saved" -- so the page says so instead of quietly
    // showing the suggested plate as if nothing had been kept.
    try {
      saved = {};
      for (const c of await ArusuvaiAuth.getChoices()) {
        saved[`${c.region}:${c.meal_slot}`] = { picks: c.picks, leave_empty: c.leave_empty };
      }
    } catch {
      saved = null;
    }

    mainEl.hidden = false;
    ArusuvaiDashboardSuccess.renderProfileTags(profile);
  }

  // ------------------------------------------------------------------
  // Plate picker + POST /api/plan
  // ------------------------------------------------------------------

  const generateBtn = document.getElementById("dashGenerate");
  const resetPicksBtn = document.getElementById("dashResetPicks");
  const rememberBtn = document.getElementById("dashRememberChoices");
  const forgetBtn = document.getElementById("dashForgetChoices");
  const savedNoteEl = document.getElementById("dashSavedNote");
  const swapNoteEl = document.getElementById("obPlanSwapNote");
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

  // N8: dishes the user swapped in, for this visit only (owner 2026-09-29:
  // saving favourites is a later task). Held here, not in storage, so a
  // reload starts from the suggested plate.
  let picks = [];
  // N10: courses the user removed a dish from, as slot names, for this visit
  // only. Sent with every plan so the course stays empty; dropping the dish's
  // pick alone was measured to bring the course back in 67 of 155 flows
  // (docs/audit_log.md 2026-09-30).
  let leaveEmpty = [];
  // N11 (owner 2026-10-02): choices the user asked to keep, per meal, as the
  // server holds them: {"south_indian:breakfast": {picks, leave_empty}}.
  // A new plan for a meal starts from them. They are asked of the planner
  // afresh each time and never forced: after a profile edit they stop
  // fitting 20% of the time (docs/audit_log.md 2026-10-02).
  let saved = {};
  // The last plate shown, so a swap that finds no plate can leave it on
  // screen and say so, instead of replacing it with a decline page.
  let shown = null;

  generateBtn.addEventListener("click", () => {
    const plate = collectPlate();
    const kept = saved && saved[plateKey(plate)];
    picks = kept ? kept.picks.slice() : [];
    leaveEmpty = kept ? kept.leave_empty.slice() : [];
    shown = null;
    fetchPlan({
      plate,
      fromSaved: Boolean(kept),
      note: saved === null
        ? "Your saved choices couldn't be loaded, so this is the suggested plate."
        : "",
    });
  });

  function plateKey(plate) {
    return `${plate.region}:${plate.meal_slot}`;
  }

  function sameChoices(a, b) {
    const norm = (xs) => JSON.stringify(xs.slice().sort());
    return norm(a.picks) === norm(b.picks) && norm(a.leave_empty) === norm(b.leave_empty);
  }

  // What the remember/forget controls say depends only on the plate on
  // screen and what is saved for its meal. With saved choices unknown
  // (could not be loaded) neither is offered: either could overwrite them.
  function renderSavedControls(message = "") {
    const kept = saved && shown && saved[plateKey(shown.plate)];
    const current = { picks, leave_empty: leaveEmpty };
    const hasChoices = picks.length > 0 || leaveEmpty.length > 0;
    rememberBtn.hidden = !(saved && shown && hasChoices && !(kept && sameChoices(kept, current)));
    forgetBtn.hidden = !kept;
    savedNoteEl.textContent = message ||
      (kept && sameChoices(kept, current) ? "This plate uses your saved choices for this meal." : "");
  }

  async function storeChoices(choices, done) {
    try {
      await ArusuvaiAuth.saveChoices(Object.assign({}, shown.plate, choices));
    } catch {
      renderSavedControls("Couldn't reach the server, so nothing was saved or forgotten.");
      return;
    }
    const key = plateKey(shown.plate);
    if (choices.picks.length || choices.leave_empty.length) saved[key] = choices;
    else delete saved[key];
    renderSavedControls(done);
  }

  rememberBtn.addEventListener("click", () =>
    storeChoices(
      { picks: picks.slice(), leave_empty: leaveEmpty.slice() },
      "Saved. This meal will start from these choices next time."
    )
  );
  forgetBtn.addEventListener("click", () =>
    storeChoices(
      { picks: [], leave_empty: [] },
      "Forgotten. This meal will start from the suggested plate next time."
    )
  );
  resetPicksBtn.addEventListener("click", () => {
    picks = [];
    leaveEmpty = [];
    fetchPlan({ plate: shown && shown.plate });
  });

  // A swap replaces whatever was picked for that slot and keeps the other
  // slots' picks. Counts for every dish come back from the server.
  // Choosing a dish for a course also ends that course's removal: asking for
  // a dish in a course and for the course to be empty is a decline.
  function onSwap(recipeId, recipeName, slotOptions, slot) {
    const inSlot = new Set(slotOptions.map((o) => o.recipe_id));
    const previous = { picks, leaveEmpty };
    picks = picks.filter((r) => !inSlot.has(r)).concat([recipeId]);
    leaveEmpty = leaveEmpty.filter((s) => s !== slot);
    // The plate the menu belongs to, not whatever the picker reads now.
    fetchPlan({ previous, tried: recipeName, plate: shown.plate });
  }

  // A removal empties the dish's course and drops any pick in it, for the
  // same reason in reverse. The other courses' picks and removals stay.
  function onRemove(slot, recipeName) {
    const slotOptions = (shown.data.swap_options.find((s) => s.slot === slot) || {}).options || [];
    const inSlot = new Set(slotOptions.map((o) => o.recipe_id));
    const previous = { picks, leaveEmpty };
    picks = picks.filter((r) => !inSlot.has(r));
    leaveEmpty = leaveEmpty.filter((s) => s !== slot).concat([slot]);
    fetchPlan({ previous, tried: recipeName, removing: true, plate: shown.plate });
  }
  tryAnotherBtn.addEventListener("click", () => {
    planDeclineEl.hidden = true;
    document.getElementById("obPlatePicker").scrollIntoView({ behavior: "smooth", block: "center" });
  });

  async function fetchPlan({
    previous = null, tried = null, removing = false, plate = null, fromSaved = false, note = "",
  } = {}) {
    endpointLabel.textContent = `Calling ${API_BASE}/api/plan`;
    swapNoteEl.textContent = "";
    savedNoteEl.textContent = "";
    planLoadingEl.hidden = false;
    planNetworkErrorEl.hidden = true;
    planSuccessEl.hidden = true;
    planDeclineEl.hidden = true;

    plate = plate || collectPlate();
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
        picks,
        leave_empty: leaveEmpty,
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
      shown = { data, plate };
      resetPicksBtn.hidden = picks.length === 0 && leaveEmpty.length === 0;
      ArusuvaiDashboardSuccess.render(data, plate, profile, onSwap, onRemove);
      renderSavedControls(note);
    } else if (fromSaved) {
      // The saved choices don't fit this meal's limits today -- usually a
      // profile edit since they were saved. Nothing is loosened to fit them
      // and they are not deleted (the user may change back): show the
      // suggested plate and say so.
      picks = [];
      leaveEmpty = [];
      fetchPlan({
        plate,
        note: "Your saved choices for this meal don't fit its limits today, so this is " +
          "the suggested plate. They are still saved.",
      });
    } else if (previous && shown) {
      // A swap or a removal found no valid plate. Not a decline of the meal:
      // the plate on screen is still valid, so keep it, undo the change, and
      // say which dish it was, by the name the page showed, never the id.
      // Nothing is loosened to make a choice fit (owner 2026-09-29).
      picks = previous.picks;
      leaveEmpty = previous.leaveEmpty;
      resetPicksBtn.hidden = picks.length === 0 && leaveEmpty.length === 0;
      ArusuvaiDashboardSuccess.render(shown.data, shown.plate, profile, onSwap, onRemove);
      renderSavedControls();
      swapNoteEl.textContent = removing
        ? `${tried || "That dish"} couldn't be removed: no plate without it stays within ` +
          `this meal's limits, so your plate is unchanged.`
        : `${tried || "That dish"} couldn't be fitted into a plate that stays within ` +
          `this meal's limits, so your plate is unchanged.`;
    } else {
      ArusuvaiDashboardDecline.render(data, plate);
    }
  }

  init();
})();
