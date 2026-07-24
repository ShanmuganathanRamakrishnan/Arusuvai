// web/dashboard.js — the auth-gated dashboard: saved profile + POST /api/plan.
//
// This file computes NOTHING nutritional, same constraint as onboarding.js.
// The plate-picker and the plan success/decline rendering below are moved
// here verbatim from what was previously onboarding.html's step 6 — this
// increment relocates where POST /api/plan is called from (behind an
// authenticated session, against a persisted profile) without touching what
// core.planner returns or how a decline is described (CLAUDE.md: don't touch
// the plan-call/decline logic).

(() => {
  "use strict";

  const API_BASE = ArusuvaiAuth.API_BASE;

  function fmtKcal(n) {
    return Math.round(n).toLocaleString("en-IN");
  }
  function fmtG(n) {
    return Math.round(n * 10) / 10;
  }

  const PLATE_LABELS = {
    "south_indian:breakfast": "South Indian breakfast",
    "south_indian:lunch": "South Indian lunch",
    "north_indian:lunch": "North Indian lunch",
    "north_indian:dinner": "North Indian dinner",
  };

  const gateLoadingEl = document.getElementById("dashGateLoading");
  const noProfileEl = document.getElementById("dashNoProfile");
  const mainEl = document.getElementById("dashMain");

  const authBar = document.getElementById("obAuthBar");
  const authBarText = document.getElementById("obAuthBarText");
  const authBarLogout = document.getElementById("obAuthBarLogout");

  authBarLogout.addEventListener("click", async () => {
    await ArusuvaiAuth.logout();
    window.location.href = "onboarding.html";
  });

  let profile = null; // the saved profile this page renders and plans against

  function renderProfileLine(p) {
    const flags = p.clinical_flags.length ? p.clinical_flags.join(", ") : "none disclosed";
    document.getElementById("dashProfileLine").textContent =
      `${p.age_years}y ${p.sex} · ${fmtG(p.weight_kg)} kg · ${fmtG(p.height_cm)} cm · ` +
      `${p.activity} activity · goal: ${p.goal} · diet: ${p.diet} · clinical flags: ${flags}`;
  }

  // ------------------------------------------------------------------
  // Auth gate: unauthenticated visitors are redirected to onboarding.html
  // (this project's real signup/login entry point — see its top auth bar
  // and its ?next=dashboard handling), not shown a dashboard shell first.
  // ------------------------------------------------------------------

  async function init() {
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

    authBar.hidden = false;
    authBarText.textContent = `Signed in as ${user.email}`;
    authBarLogout.hidden = false;

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
    renderProfileLine(profile);
  }

  // ------------------------------------------------------------------
  // Plate picker + POST /api/plan — unchanged logic from the old onboarding
  // step 6, just re-homed here and sourcing the profile from the saved
  // record instead of a freshly-collected form.
  // ------------------------------------------------------------------

  const generateBtn = document.getElementById("dashGenerate");
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
      renderPlanSuccess(data, plate);
    } else {
      renderPlanDecline(data);
    }
  }

  function renderPlanSuccess(data, plate) {
    planSuccessEl.hidden = false;

    const wrap = document.getElementById("obPlanMeals");
    const label = PLATE_LABELS[`${plate.region}:${plate.meal_slot}`] || `${plate.region} · ${plate.meal_slot}`;

    const list = document.createElement("ul");
    list.className = "ob-plan-components";
    for (const c of data.components) {
      const li = document.createElement("li");
      li.innerHTML =
        `<span>${c.recipe_name} <span class="cat">${c.category}</span></span>` +
        `<span class="count">${c.unit_count} × ${c.unit_name}</span>`;
      list.appendChild(li);
    }

    const est = data.estimate;
    const stat = document.createElement("div");
    stat.className = "stat";
    stat.textContent = est
      ? `≈ ${fmtKcal(est.energy_kcal)} kcal · ${fmtG(est.protein_g)}g protein · ${fmtG(est.carb_g)}g carb · ` +
        `${fmtG(est.fat_g)}g fat · ${fmtG(est.fibre_g)}g fibre · ${fmtKcal(est.sodium_mg)}mg sodium`
      : "";

    wrap.innerHTML = `<div class="meal">${label}</div>`;
    wrap.appendChild(list);
    wrap.appendChild(stat);

    const relaxationNote = document.getElementById("obPlanRelaxationNote");
    relaxationNote.textContent = data.relaxation_applied.length ? data.disclosure : "";
  }

  function renderPlanDecline(data) {
    planDeclineEl.hidden = false;

    // Same three drafted, not-finalized copy options as before this
    // increment (see git history for onboarding.js's old renderPlanDecline)
    // — still ships with A, still flagged for review, unchanged by moving
    // this function to dashboard.js.
    //   A) "This library can't build you a plate yet — here's exactly why."
    //   B) "No plate today. The engine looked, and here's precisely what's missing."
    //   C) "We don't have a match for you right now — and we're not going to fake one."
    document.getElementById("obDeclineLede").textContent =
      "This library can't build you a plate yet — here's exactly why.";

    const list = document.getElementById("obDeclineViolations");
    list.innerHTML = "";
    for (const v of data.violations) {
      const li = document.createElement("li");
      li.textContent = v;
      list.appendChild(li);
    }

    document.getElementById("obDeclineDisclosure").textContent = data.disclosure || "";
  }

  init();
})();
