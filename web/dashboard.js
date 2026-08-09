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
      // Not "a validated combination", which is what this read until 2026-08-09
      // and which was false on every plate the app has ever served: nothing in
      // the library can ship as validated (docs/methodology.md), and the
      // provenance line below says so explicitly.
      : `A combination of real components for this plate.`;

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

    renderProvenance(data);

    const relaxationNote = document.getElementById("obPlanRelaxationNote");
    relaxationNote.textContent = data.relaxation_applied.length ? data.disclosure : "";
  }

  // docs/methodology.md, "dev_mode versus validated": a plate solved with the
  // eligibility filter suspended must say so on the artifact, because what
  // leaves this page is a screenshot and a boolean in a payload does not
  // survive that. Written here rather than sent as prose from the API for the
  // same reason every other label on this page is: `dev_mode` is snake_case,
  // it must never reach a visible text node, and the API's job is the number.
  //
  // The first draft of this function rendered the token itself, and
  // tests/test_web_no_identifiers.py failed on `dashboard_after_plan` with
  // ('dev_mode', 'Built with dev_mode') -- confirmed red before this copy was
  // written, which is the order this repo keeps having to relearn.
  function renderProvenance(data) {
    const el = document.getElementById("obPlanProvenance");
    if (!data.dev_mode) {
      el.textContent = "";
      return;
    }
    const est = data.estimate;
    // Rounded to whole percent: a band this wide does not support a decimal,
    // and "99.97%" would be the false precision this project exists to avoid.
    const share =
      est && est.unverified_energy_fraction > 0
        ? `About ${Math.round(est.unverified_energy_fraction * 100)}% of this plate's energy `
          + `rests on figures nobody has checked against a primary source yet. `
        : "";
    el.textContent =
      `Not validated. ${share}` +
      `The nutrition data behind these dishes is unconfirmed, so treat the numbers as ` +
      `an illustration of the method rather than dietary advice.`;
  }

  // ---------------------------------------------------------------- decline copy
  //
  // The decline used to render two server-written strings: `violations[]` (the
  // prose `Violation.describe` produces) and `disclosure` (a join of the same
  // prose). Both interpolate `Violation.macro` raw, so a reader was shown
  // "sodium_mg is 1546.0mg, above its ceiling of 1400.0mg" -- twice, in two
  // places. `docs/audit_log.md` finding 31.
  //
  // The fix is here rather than in the planner for the reason D11 gives: the
  // server sends stable tokens and numbers, the client writes the sentence.
  // `ViolationOut` already carried macro/kind/bound_source/reach/relaxability/
  // locked_by; D9 adds `actual` and `bound`, so nothing below needs to parse a
  // number back out of English. `core/planner/validator.py` still writes
  // `text` and `disclosure` and they are still correct -- they are simply not
  // what this page renders.
  //
  // Every key `Violation.macro` can carry is mapped, not only the ones a
  // decline happens to produce today. A macro missing from here would fall
  // through to a raw identifier, which is the whole defect.
  const MACRO_COPY = {
    energy_kcal: { name: "Calories", unit: " kcal", digits: 0 },
    protein_g: { name: "Protein", unit: "g", digits: 1 },
    fat_g: { name: "Fat", unit: "g", digits: 1 },
    carb_g: { name: "Carbohydrate", unit: "g", digits: 1 },
    fibre_g: { name: "Fibre", unit: "g", digits: 1 },
    sodium_mg: { name: "Sodium", unit: "mg", digits: 0 },
    iron_mg: { name: "Iron", unit: "mg", digits: 1 },
    calcium_mg: { name: "Calcium", unit: "mg", digits: 0 },
    b12_ug: { name: "Vitamin B12", unit: "µg", digits: 1 },
    // Not in MACRO_KEYS and deliberately not a macro -- see core/foods/
    // quality.py. It reaches a decline like any other bound, so it needs copy.
    quality_protein_g: { name: "High-quality protein", unit: "g", digits: 1 },
  };

  // Which rule set the bound. Only `meal_share` is the ordinary case, so only
  // the other two say anything: a reader who is over a limit deserves to know
  // when the limit came from the rest of their day rather than from this plate.
  const BOUND_SOURCE_CLAUSE = {
    meal_share: "",
    day_remaining: " — what's left of your day's allowance after your other meals",
    absurdity_guard: " — more than one plate should take of a whole day's allowance",
  };

  // Why the limit did not move. "locked" is the one this screen exists to show:
  // the system deliberately refused to trade something away, and saying so is
  // more useful than any number on the page.
  const RELAXABILITY_NOTE = {
    relaxable: "",
    relaxed_to_limit: " We had already stretched this as far as it goes.",
    hard_capped: " This is a hard limit that never widens.",
    never_relaxed: " This isn't a limit we trade away.",
    locked: "", // handled with locked_by, which names the condition
  };

  // TemplateSlot names, for the "we couldn't even fill the plate" case.
  // humanise() is an acceptable fallback here by this file's own doctrine: a
  // slot is structural, not a trust claim, and "Curd course" is honest.
  const SLOT_LABELS = {
    base: "a base",
    tiffin: "a tiffin item",
    rice: "a rice course",
    curry: "a curry",
    kuzhambu: "a kuzhambu",
    sambar: "a sambar",
    dal: "a dal",
    sabzi: "a sabzi",
    poriyal: "a vegetable side",
    vegetable: "a vegetable side",
    chutney: "a chutney",
    curd_course: "a curd course",
    accompaniment: "an accompaniment",
    protein: "a protein dish",
    bread: "a bread",
  };

  const fmt = (n, digits) =>
    Number(n).toLocaleString(undefined, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });

  /** One violation as a sentence a person can read. Never returns a token. */
  function violationSentence(v) {
    if (v.kind === "no_candidates") {
      const slots = (v.blocking_slots || []).map(
        (s) => SLOT_LABELS[s] || humanise(s).toLowerCase()
      );
      if (!slots.length) {
        return "We couldn't assemble a complete plate from the recipes available for this meal.";
      }
      const list =
        slots.length === 1
          ? slots[0]
          : slots.slice(0, -1).join(", ") + " and " + slots[slots.length - 1];
      return `This meal needs ${list}, and the library has nothing that fits your profile.`;
    }

    // An unmapped macro must not fall through to its key. humanise() would give
    // "Sodium mg" -- readable, but the unit is then wrong in the sentence, so
    // the number is dropped rather than stated against a unit we can't name.
    const copy = MACRO_COPY[v.macro];
    if (!copy) {
      return "One of this plate's nutritional limits couldn't be met.";
    }

    const actual = `${fmt(v.actual, copy.digits)}${copy.unit}`;
    const bound = `${fmt(v.bound, copy.digits)}${copy.unit}`;
    const source = BOUND_SOURCE_CLAUSE[v.bound_source] || "";

    let sentence;
    if (v.kind === "below_floor") {
      sentence = `${copy.name} reaches only ${actual}, short of the ${bound} this plate needs${source}.`;
    } else if (v.kind === "above_ceiling") {
      sentence = `${copy.name} comes to ${actual}, over the ${bound} limit${source}.`;
    } else {
      sentence = `${copy.name} is ${actual} against a limit of ${bound}${source}.`;
    }

    const flags = (v.locked_by || []).map((f) => FLAG_LABELS[f] || humanise(f));
    if (flags.length) {
      // The most important sentence on the screen: the system did not fail to
      // fix this, it declined to.
      sentence +=
        ` We didn't loosen this one, because you told us about ${flags
          .join(" and ")
          .toLowerCase()}.`;
    } else {
      sentence += RELAXABILITY_NOTE[v.relaxability] || "";
    }
    return sentence;
  }

  /** The closing paragraph. Composed here; the server's `disclosure` is not
   *  rendered, because it is a join of the same prose the list above shows and
   *  it carries the same raw macro key. */
  function declineDisclosure(details) {
    const locked = details.some((v) => (v.locked_by || []).length);
    if (locked) {
      return (
        "We stopped rather than relax a limit tied to a condition you disclosed. " +
        "This system is not a substitute for clinical nutrition guidance — please " +
        "take these targets to your doctor or dietitian."
      );
    }
    const unreachable = details.some((v) => v.reach === "unreachable");
    if (unreachable) {
      return (
        "No combination this library can build meets that limit, so changing the " +
        "portions wouldn't help — the recipes themselves are the constraint."
      );
    }
    return (
      "Each limit above is reachable on its own; there's no combination that " +
      "meets all of them at once for this meal."
    );
  }

  // The wording is static UI copy and fine to hardcode; WHICH of them shows is
  // not. D9 asks the screen to "offer only suggestions that can change the
  // outcome", and three unconditional strings cannot do that: telling someone
  // whose decline has nothing to do with a disclosed condition to review their
  // conditions sends them to a settings page that will change nothing, and a
  // screen that pads its advice teaches a reader to skip all of it.
  //
  // Each `applies` reads only tokens the payload actually carries. The first is
  // unconditional and must stay that way -- it is what guarantees the list is
  // never empty, which would be a worse screen than a slightly loose suggestion.
  const DECLINE_PATHS = [
    {
      // Reworded 2026-08-09: this used to end "...to fit the same locked
      // limits", which was written when it only ever appeared beside a locked
      // bound. It is the unconditional suggestion, so its wording has to hold
      // for every decline — including the common one where nothing is locked.
      text: "Try a different plate above — a different template draws on different recipes, so the same limits may fit.",
      // Every `reach` value is scoped to the template that was solved, including
      // "unreachable": it means no combination *of this template* works, so
      // another template genuinely can. Always offered, and always true.
      applies: () => true,
    },
    {
      text: "If your disclosed conditions have changed, update your profile and we'll recompute from scratch.",
      // Only when a disclosed condition actually held a bound out of the ladder.
      // Otherwise the profile's conditions had no bearing on this decline and
      // this is busywork dressed as a remedy.
      applies: (details) => details.some((v) => (v.locked_by || []).length > 0),
    },
    {
      text: "Check back as the recipe library grows — a plate that's infeasible today may not be next week.",
      // Only when the catalogue is the binding constraint: no legal assignment
      // reaches the bound ("unreachable"), or the template could not be filled
      // at all ("empty_pool"). For a plate that misses only in combination, more
      // recipes is a guess, and `docs/audit_log.md` finding 24 is precisely
      // about the harm of offering an action against a cause nobody established.
      applies: (details) =>
        details.some((v) => v.reach === "unreachable" || v.reach === "empty_pool"),
    },
  ];

  /** The decline's provenance line, counterpart to renderProvenance().
   *
   *  There is no plate here, so there is no "% of this plate's energy" to
   *  quote -- but the refusal itself was computed from the same unchecked
   *  figures, and a reader deciding whether to trust a "no" is owed that as
   *  much as one deciding whether to trust a "yes".
   */
  function renderDeclineProvenance(data) {
    const el = document.getElementById("obDeclineProvenance");
    if (!data.dev_mode) {
      el.textContent = "";
      return;
    }
    el.textContent =
      "Not validated. The limits above were computed from nutrition data nobody " +
      "has checked against a primary source yet, so treat this as an " +
      "illustration of the method rather than dietary advice.";
  }

  function renderPlanDecline(data, plate) {
    planDeclineEl.hidden = false;
    const label = plateLabel(plate);

    document.getElementById("obDeclineEyebrow").textContent = `Your plate · ${label}`;
    document.getElementById("obDeclineLede").textContent =
      "This library can't build you a plate yet — here's exactly why.";

    // `violation_detail`, not `violations`: the latter is server prose with the
    // raw macro key in it. If an older API sends only the prose, say something
    // true and vague rather than render an identifier -- a decline that reads
    // thinly is a worse screen, but a decline that says "sodium_mg" is the bug.
    const details = data.violation_detail || [];
    const sentences = details.length
      ? details.map(violationSentence)
      : ["We couldn't meet this plate's nutritional targets for your profile."];

    const list = document.getElementById("obDeclineViolations");
    list.innerHTML = "";
    for (const sentence of sentences) {
      const row = document.createElement("div");
      row.className = "ob-callout-item";
      // textContent, not innerHTML: these strings are composed here from server
      // values, and one of them is a number formatted by toLocaleString.
      const dot = document.createElement("span");
      dot.className = "dot";
      const body = document.createElement("span");
      body.textContent = sentence;
      row.appendChild(dot);
      row.appendChild(body);
      list.appendChild(row);
    }

    const paths = document.getElementById("obDeclinePaths");
    paths.innerHTML = "";
    // Numbered after filtering, not before: a list reading 1, 3 tells the reader
    // something was withheld and invites them to wonder what.
    DECLINE_PATHS.filter((p) => p.applies(details)).forEach((p, i) => {
      const row = document.createElement("div");
      row.className = "ob-path-item";
      row.innerHTML = `<span class="ob-path-num">${i + 1}</span><span class="ob-path-text">${p.text}</span>`;
      paths.appendChild(row);
    });

    document.getElementById("obDeclineDisclosure").textContent =
      declineDisclosure(details);
    renderDeclineProvenance(data);
  }

  init();
})();
