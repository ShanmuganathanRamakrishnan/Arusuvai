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
  const DIET_LABELS = {
    non_vegetarian: "Non-vegetarian",
    eggetarian: "Eggetarian",
    vegetarian: "Vegetarian",
    vegan: "Vegan",
    jain: "Jain",
  };
  const GOAL_LABELS = {
    lose_fat: "Fat loss",
    maintain: "Maintain",
    gain_muscle: "Muscle gain",
  };
  // ClinicalFlag's values are snake_case enum members and were rendered raw,
  // so a user who disclosed kidney disease saw the tag "chronic_kidney_disease"
  // on their own dashboard. Diet and goal already had a label map; the flags
  // were simply missed. Same treatment, same reason.
  const FLAG_LABELS = {
    hypertension: "Hypertension",
    chronic_kidney_disease: "Chronic kidney disease",
    diabetes: "Diabetes",
  };
  // Last-resort readability for an enum member added to core/schemas after
  // this file was written: "some_new_flag" -> "Some new flag". Not a licence
  // to skip the map above -- it cannot produce a real display name, only stop
  // an identifier reaching the screen looking like an identifier.
  //
  // WHICH FIELDS MAY FALL THROUGH TO THIS, AND WHICH MAY NOT.
  // Eligible: diet, goal, clinical flag, region, meal slot. Every one of these
  // is a value the USER chose and can already read back; prettifying an
  // unrecognised one restates their own input in worse words, and restating it
  // wrongly is a cosmetic failure.
  // Not eligible: anything that states how much to TRUST a number -- evidence
  // grade, verification status, claim strength. There, humanise() is actively
  // harmful: "Some new grade" is typographically indistinguishable from
  // "Primary measurement", so an unrecognised value would render as a
  // confident-looking claim this code cannot actually vouch for. Those fall
  // through to an explicitly cautious label instead (onboarding.js's
  // GRADE_LABELS -> "Ungraded"), never to prettified prose.
  const humanise = (v) => {
    const s = String(v).replace(/_/g, " ");
    return s.charAt(0).toUpperCase() + s.slice(1);
  };

  // ------------------------------------------------------------------
  // Kolam background — same grid as onboarding.js's renderKolam(),
  // duplicated per-page rather than shared (see web/app.js).
  // ------------------------------------------------------------------

  function renderKolam() {
    const host = document.getElementById("kolam");
    if (!host) return;
    const W = 1200, H = 1400, g = 128, amp = g * 0.44, per = g * 2;
    const f = (n) => Math.round(n * 100) / 100;
    let dotStr = "";
    let lineStr = "";
    for (let r = 0; r * g <= H + g; r++) {
      const y0 = r * g, ph = r % 2 ? Math.PI : 0;
      let d = "";
      for (let x = 0; x <= W; x += 14) {
        const y = y0 + amp * Math.sin((x / per) * 2 * Math.PI + ph);
        d += (x === 0 ? "M" : "L") + f(x) + " " + f(y) + " ";
      }
      lineStr += `<path d="${d.trim()}" fill="none" stroke="#3A5A40" stroke-width="1.4"></path>`;
    }
    for (let c = 0; c * g <= W + g; c++) {
      const x0 = c * g, ph = c % 2 ? Math.PI : 0;
      let d = "";
      for (let y = 0; y <= H; y += 14) {
        const x = x0 + amp * Math.sin((y / per) * 2 * Math.PI + ph);
        d += (y === 0 ? "M" : "L") + f(x) + " " + f(y) + " ";
      }
      lineStr += `<path d="${d.trim()}" fill="none" stroke="#3A5A40" stroke-width="1.4"></path>`;
    }
    for (let r = 0; r * g <= H + g; r++) {
      for (let c = 0; c * g <= W + g; c++) {
        dotStr += `<circle cx="${c * g - g / 2}" cy="${r * g - g / 2}" r="4.4" fill="#B98416"></circle>`;
      }
    }
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 1200 1400");
    svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
    svg.innerHTML = dotStr + lineStr;
    host.appendChild(svg);
  }

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

  // Tag row: only diet and goal come from the saved profile -- ProfileIn/Out
  // carries no region preference (region_pref is collected on onboarding's
  // diet step but not part of the schema; only the plate picker below picks
  // a region, per plate). Fabricating a third "region" tag here from
  // something the profile doesn't actually store would be exactly the kind
  // of unverified claim CLAUDE.md's process rule forbids.
  function renderProfileTags(p) {
    const wrap = document.getElementById("dashProfileTags");
    wrap.innerHTML =
      `<span class="tag">${DIET_LABELS[p.diet] || humanise(p.diet)}</span>` +
      `<span class="tag">${GOAL_LABELS[p.goal] || humanise(p.goal)}</span>`;
    if (p.clinical_flags.length) {
      const flags = p.clinical_flags.map((f) => FLAG_LABELS[f] || humanise(f)).join(", ");
      wrap.innerHTML += `<span class="tag">${flags}</span>`;
    }
  }

  // ------------------------------------------------------------------
  // Auth gate: unauthenticated visitors are redirected to onboarding.html
  // (this project's real signup/login entry point — see its step 6 and its
  // ?next=dashboard handling), not shown a dashboard shell first.
  // ------------------------------------------------------------------

  async function init() {
    renderKolam();

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
    renderProfileTags(profile);
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
      renderPlanSuccess(data, plate);
    } else {
      renderPlanDecline(data, plate);
    }
  }

  function plateLabel(plate) {
    // Both halves go through humanise(): a region or meal slot added to
    // core/schemas after this map was written would otherwise reach the
    // eyebrow as "south_indian · breakfast".
    return (
      PLATE_LABELS[`${plate.region}:${plate.meal_slot}`] ||
      `${humanise(plate.region)} · ${humanise(plate.meal_slot).toLowerCase()}`
    );
  }

  function renderPlanSuccess(data, plate) {
    planSuccessEl.hidden = false;
    const label = plateLabel(plate);

    document.getElementById("obSuccessEyebrow").textContent = `Your plate · ${label}`;

    const est = data.estimate;
    document.getElementById("obSuccessSentence").innerHTML = est
      ? `${DIET_LABELS[profile.diet] || humanise(profile.diet)} components tuned to your ${(GOAL_LABELS[profile.goal] || humanise(profile.goal)).toLowerCase()} target — about ` +
        `<span class="accent">${fmtKcal(est.energy_kcal)} kcal</span> with <span class="accent">${fmtG(est.protein_g)} g protein</span>.`
      : `A validated combination of real components for this plate.`;

    const wrap = document.getElementById("obPlanMeals");
    wrap.innerHTML = `<div class="meal">${label}</div>`;
    const list = document.createElement("ul");
    list.className = "ob-plan-components";
    for (const c of data.components) {
      const li = document.createElement("li");
      li.innerHTML =
        `<span>${c.recipe_name} <span class="cat">${c.category}</span></span>` +
        `<span class="count">${c.unit_count} × ${c.unit_name}</span>`;
      list.appendChild(li);
    }
    wrap.appendChild(list);
    if (est) {
      const stat = document.createElement("div");
      stat.className = "stat";
      stat.textContent =
        `≈ ${fmtKcal(est.energy_kcal)} kcal · ${fmtG(est.protein_g)}g protein · ${fmtG(est.carb_g)}g carb · ` +
        `${fmtG(est.fat_g)}g fat · ${fmtG(est.fibre_g)}g fibre · ${fmtKcal(est.sodium_mg)}mg sodium`;
      wrap.appendChild(stat);
    }

    const totalEl = document.getElementById("obPlanTotal");
    totalEl.innerHTML = est
      ? `<strong>This plate</strong><span class="num">≈ ${fmtKcal(est.energy_kcal)} kcal · ${fmtG(est.protein_g)}g protein · ` +
        `${fmtG(est.carb_g)}g carb · ${fmtG(est.fat_g)}g fat</span>`
      : "";

    const relaxationNote = document.getElementById("obPlanRelaxationNote");
    relaxationNote.textContent = data.relaxation_applied.length ? data.disclosure : "";
  }

  // Generic guidance, not a claim about this profile's numbers -- static UI
  // copy, unlike everything else on this page, is fine to hardcode.
  const DECLINE_PATHS = [
    "Try a different plate above — more (region, meal) combinations means more room to fit the same locked limits.",
    "If your disclosed conditions have changed, update your profile and we'll recompute from scratch.",
    "Check back as the recipe library grows — a plate that's infeasible today may not be next week.",
  ];

  function renderPlanDecline(data, plate) {
    planDeclineEl.hidden = false;
    const label = plateLabel(plate);

    document.getElementById("obDeclineEyebrow").textContent = `Your plate · ${label}`;
    document.getElementById("obDeclineLede").textContent =
      "This library can't build you a plate yet — here's exactly why.";

    const list = document.getElementById("obDeclineViolations");
    list.innerHTML = "";
    for (const v of data.violations) {
      const row = document.createElement("div");
      row.className = "ob-callout-item";
      row.innerHTML = `<span class="dot"></span><span>${v}</span>`;
      list.appendChild(row);
    }

    const paths = document.getElementById("obDeclinePaths");
    paths.innerHTML = "";
    DECLINE_PATHS.forEach((text, i) => {
      const row = document.createElement("div");
      row.className = "ob-path-item";
      row.innerHTML = `<span class="ob-path-num">${i + 1}</span><span class="ob-path-text">${text}</span>`;
      paths.appendChild(row);
    });

    document.getElementById("obDeclineDisclosure").textContent = data.disclosure || "";
  }

  init();
})();
