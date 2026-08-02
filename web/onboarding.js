// web/onboarding.js — the six-step onboarding wizard, ported from
// "Arusuvai Onboarding.dc.html" (the Claude Design canvas) to a
// self-contained page with no proprietary runtime, the same deviation
// documented for web/index.html and web/README.md.
//
// The design canvas's own Component.compute() computes BMR/TDEE/macros in
// the browser -- useful for a visual mockup, but it duplicates
// core.nutrition.targets in JS and violates this project's central
// invariant (CLAUDE.md: nutrition is never computed outside core/). This
// file borrows the canvas's layout and interaction language only; every
// number rendered below is a property read off a real API response
// (POST /api/targets, POST /api/auth/*, GET /api/science) -- there is no
// arithmetic on a gram value anywhere in this file. Steps 1-5 need no
// account: they collect the profile in browser memory and call
// /api/targets. Step 6 is the account/save hinge -- this replaces the
// canvas's client-side auth tab UI with real signup/login calls, persists
// the profile against the resulting user_id (POST /api/profile), and hands
// off to dashboard.html, which is where POST /api/plan lives. See auth.js
// for the signup/login/session calls this file uses without the shared
// modal (step 6 supersedes it on this page).

(() => {
  "use strict";

  // Dev-only: uvicorn's default port. api/main.py's CORS list assumes this
  // page is served from :3000 or :8000 (a different port than the API), per
  // its own comment. Change both together if you run the API elsewhere.
  const API_BASE = "http://localhost:8000";
  const TOTAL_STEPS = 6;

  const form = document.getElementById("obForm");
  const backBtn = document.getElementById("obBack");
  const nextBtn = document.getElementById("obNext");
  const nextLabel = document.getElementById("obNextLabel");
  const endpointLabel = document.getElementById("obEndpointLabel");
  const wizardEl = document.getElementById("obWizard");
  const progressSegs = Array.from(document.querySelectorAll(".ob-progress2-seg"));

  let currentStep = 1;
  let targetsLoaded = false;
  let scienceCache = null;

  // ------------------------------------------------------------------
  // Kolam background — same woven pulli-and-line grid as index.html's
  // app.js (buildKolam/renderKolam), duplicated here rather than shared,
  // consistent with this project's existing per-page duplication of small
  // presentation helpers (see web/app.js).
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

  // ------------------------------------------------------------------
  // Formatting — display only. Nothing below performs a nutritional
  // computation, only rounds a value the API already computed.
  // ------------------------------------------------------------------

  function fmtKcal(n) {
    return Math.round(n).toLocaleString("en-IN");
  }

  // ONE rounding policy for displayed macro masses: nearest whole gram.
  //
  // This is a correctness-of-presentation fix, not a style preference. The
  // page states energy as an interval — "±14%, so roughly 1,905-2,533 kcal" —
  // and then reported macros as "120.9 g protein · 67.8 g fat · 281.3 g carb".
  // A tenth of a gram is four significant figures under a two-significant-
  // figure interval: the displayed precision asserted an accuracy the data
  // explicitly says it does not have, which is the exact false-precision
  // failure this project exists to avoid. Full precision is retained in the
  // API response and in core/; only the display rounds.
  function fmtGrams(n) {
    return Math.round(n);
  }

  // Ratios (protein g/kg, DIAAS) are NOT masses and are meaningless at whole
  // numbers — 1.6 g/kg rounds to 2, a 25% error. They keep one decimal.
  function fmtRatio(n) {
    return Math.round(n * 10) / 10;
  }

  function fmtPct(fraction) {
    return `${Math.round(fraction * 100)}%`;
  }

  // ------------------------------------------------------------------
  // Step navigation
  // ------------------------------------------------------------------

  // Primary-CTA labels, applied consistently: a step that produces something
  // meaningful names what it produces; every other step says Continue. Step 5
  // used to say "Looks right", which acknowledges rather than acts — it named
  // a judgement about the previous screen instead of the next destination.
  // Step 6 has no action-bar CTA at all; its primary lives in the panel, so
  // the screen has one primary rather than two dark-green filled buttons with
  // no stated difference between them.
  const NEXT_LABELS = {
    1: "Continue",
    2: "Continue",
    3: "Continue",
    4: "See my targets",
    5: "Use these targets",
  };

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function showStep(n) {
    currentStep = n;
    // A debugging and test hook only. It used to drive the per-step width
    // (--step-w / --fields-w); no CSS reads it for geometry any more, which is
    // the point — see "THE WIZARD LAYOUT CONTRACT" in styles.css.
    if (wizardEl) wizardEl.dataset.step = String(n);
    document.querySelectorAll(".ob-step").forEach((el) => {
      el.hidden = Number(el.dataset.step) !== n;
    });
    progressSegs.forEach((seg) => {
      const s = Number(seg.dataset.step);
      seg.classList.toggle("is-current", s === n);
      seg.classList.toggle("is-done", s < n);
    });
    updateNav();
    window.scrollTo({ top: 0, behavior: prefersReducedMotion.matches ? "auto" : "smooth" });
  }

  function updateNav() {
    // Back is available from step 2 onward, INCLUDING the final step. It used
    // to be hidden on step 6, which made the account step a one-way door: a
    // user who wanted to correct a target had no way back to step 5.
    backBtn.hidden = currentStep === 1;
    nextBtn.hidden = currentStep === TOTAL_STEPS;

    nextLabel.textContent = NEXT_LABELS[currentStep] || "Continue";
    nextBtn.disabled = currentStep === 5 && !targetsLoaded;

    endpointLabel.textContent = currentStep === 5 ? `Calling ${API_BASE}/api/targets` : "";
  }

  // ------------------------------------------------------------------
  // Inline field validation. Replaces a window.alert() that named no field
  // and left nothing on screen once dismissed, so a user who mistyped a
  // weight had to work out which of four boxes the browser meant.
  // ------------------------------------------------------------------

  function setFieldError(cellId, errId, message) {
    const cell = document.getElementById(cellId);
    const err = document.getElementById(errId);
    if (!cell || !err) return;
    cell.classList.toggle("ob-invalid", Boolean(message));
    err.hidden = !message;
    err.textContent = message || "";
  }

  function validateBodyStep() {
    const checks = [
      ["cellAge", "errAge", Number(form.age_years.value), "Age must be a number between 14 and 99."],
      ["cellWeight", "errWeight", Number(form.weight_kg.value), "Weight must be a positive number, in kilograms."],
      ["cellHeight", "errHeight", Number(form.height_cm.value), "Height must be a positive number, in centimetres."],
    ];
    let firstBad = null;
    for (const [cellId, errId, value, message] of checks) {
      const ok = Number.isFinite(value) && value > 0;
      setFieldError(cellId, errId, ok ? null : message);
      if (!ok && !firstBad) firstBad = document.getElementById(cellId);
    }
    if (firstBad) {
      const input = firstBad.querySelector("input");
      if (input) input.focus();
      return false;
    }
    return true;
  }

  // Clear a field's error as soon as it is edited — leaving a red box on a
  // value the user has already corrected trains people to ignore the colour.
  for (const [inputId, cellId, errId] of [
    ["fAge", "cellAge", "errAge"],
    ["fWeight", "cellWeight", "errWeight"],
    ["fHeight", "cellHeight", "errHeight"],
  ]) {
    document.getElementById(inputId).addEventListener("input", () => setFieldError(cellId, errId, null));
  }

  backBtn.addEventListener("click", () => {
    if (currentStep > 1) showStep(currentStep - 1);
  });

  nextBtn.addEventListener("click", async () => {
    if (currentStep === 1 && !validateBodyStep()) return;
    if (currentStep < 4) {
      showStep(currentStep + 1);
      return;
    }
    if (currentStep === 4) {
      showStep(5);
      fetchTargets();
      return;
    }
    if (currentStep === 5) {
      showStep(6);
      return;
    }
  });

  // ------------------------------------------------------------------
  // Step 2 — day picker + resistance toggle. Native radios/checkboxes
  // drive every other step's visual state via CSS :has(); these two
  // controls have no native equivalent, so they get a few lines of JS
  // that only ever set the hidden field a real <form> submission reads.
  // ------------------------------------------------------------------

  const dayPicker = document.getElementById("obDayPicker");
  const trainDaysField = document.getElementById("fTrainingDays");
  const trainDaysVal = document.getElementById("fTrainDaysVal");

  dayPicker.addEventListener("click", (e) => {
    const btn = e.target.closest(".ob-day-btn");
    if (!btn) return;
    const n = btn.dataset.n;
    const already = btn.classList.contains("is-selected");
    dayPicker.querySelectorAll(".ob-day-btn").forEach((b) => b.classList.remove("is-selected"));
    if (already) {
      trainDaysField.value = "";
      // Empty, not "—". The em dash rendered as a stray character floating at
      // the right of the label row, which read as a value that failed to bind
      // rather than as an optional field nobody has filled in.
      trainDaysVal.textContent = "";
    } else {
      btn.classList.add("is-selected");
      trainDaysField.value = n;
      trainDaysVal.textContent = n;
    }
  });

  const resistanceToggle = document.getElementById("obResistanceToggle");
  const resistanceField = document.getElementById("fResistanceTrained");

  resistanceToggle.addEventListener("click", () => {
    const on = !resistanceToggle.classList.contains("is-selected");
    resistanceToggle.classList.toggle("is-selected", on);
    resistanceToggle.setAttribute("aria-pressed", on ? "true" : "false");
    resistanceField.value = on ? "on" : "";
  });

  // ------------------------------------------------------------------
  // Profile assembly — read straight from the one <form>; every field
  // persists across steps because the fieldsets share one form and are only
  // hidden, never removed. Region preference is collected but not part of
  // ProfileIn (only diet/clinical_flags feed derive_target today; region is
  // read by core.planner.plan.plan_meal, which onboarding doesn't call).
  // ------------------------------------------------------------------

  function collectProfile() {
    const fd = new FormData(form);
    return {
      weight_kg: Number(fd.get("weight_kg")),
      height_cm: Number(fd.get("height_cm")),
      age_years: Number(fd.get("age_years")),
      sex: fd.get("sex"),
      activity: fd.get("activity"),
      goal: fd.get("goal"),
      diet: fd.get("diet"),
      clinical_flags: fd.getAll("clinical_flags"),
    };
  }

  // The reverse of collectProfile(): populate the form from a profile the
  // API already has on file (GET /api/profile), so a returning signed-in
  // user sees their own numbers instead of five blank steps.
  function prefillProfile(p) {
    form.weight_kg.value = p.weight_kg;
    form.height_cm.value = p.height_cm;
    form.age_years.value = p.age_years;
    const sexEl = form.querySelector(`input[name="sex"][value="${p.sex}"]`);
    if (sexEl) sexEl.checked = true;
    const activityEl = form.querySelector(`input[name="activity"][value="${p.activity}"]`);
    if (activityEl) activityEl.checked = true;
    const goalEl = form.querySelector(`input[name="goal"][value="${p.goal}"]`);
    if (goalEl) goalEl.checked = true;
    const dietEl = form.querySelector(`input[name="diet"][value="${p.diet}"]`);
    if (dietEl) dietEl.checked = true;
    form.querySelectorAll('input[name="clinical_flags"]').forEach((el) => {
      el.checked = p.clinical_flags.includes(el.value);
    });
  }

  // ------------------------------------------------------------------
  // Step 5 — POST /api/targets
  // ------------------------------------------------------------------

  const targetsLoadingEl = document.getElementById("obTargetsLoading");
  const targetsErrorEl = document.getElementById("obTargetsError");
  const targetsOutputEl = document.getElementById("obTargetsOutput");

  async function fetchTargets() {
    targetsLoaded = false;
    updateNav();
    targetsLoadingEl.hidden = false;
    targetsErrorEl.hidden = true;
    targetsOutputEl.hidden = true;

    let data;
    try {
      const res = await fetch(`${API_BASE}/api/targets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectProfile()),
      });
      if (res.status === 422) {
        const body = await res.json().catch(() => null);
        const detail = body && body.detail
          ? (Array.isArray(body.detail) ? body.detail.map((d) => d.msg || JSON.stringify(d)).join("; ") : body.detail)
          : "Invalid input.";
        throw new Error(`The API rejected this profile: ${detail}`);
      }
      if (!res.ok) throw new Error(`The API returned an unexpected error (HTTP ${res.status}).`);
      data = await res.json();
    } catch (err) {
      const message = err instanceof TypeError
        ? `Couldn't reach the targets API at ${API_BASE}. Is it running? Start it with: uvicorn api.main:app --reload`
        : err.message;
      targetsLoadingEl.hidden = true;
      targetsErrorEl.hidden = false;
      targetsErrorEl.textContent = message;
      return;
    }

    targetsLoadingEl.hidden = true;
    targetsOutputEl.hidden = false;
    renderTargets(data);
    targetsLoaded = true;
    updateNav();
  }

  function renderTargets(data) {
    const pill = document.getElementById("obStatusPill");
    // `data.status` is an API enum -- "dev_mode" / "validated". It was printed
    // verbatim, so the badge read "dev_mode": a code identifier, in the one
    // place on this screen whose whole job is to tell a non-technical reader
    // how much to trust the numbers beside it. The CLASS still keys off the
    // raw value (that is a code-to-code binding and correct); only the text
    // is translated. An unrecognised status falls through to the cautious
    // label rather than to the raw string -- a future enum value must not be
    // able to leak an identifier back onto the screen.
    pill.textContent = data.status === "validated" ? "Validated" : "Development estimate";
    pill.className = "ob-status-pill " + (data.status === "validated" ? "validated" : "dev-mode");

    const e = data.energy;
    const p = data.protein;
    // One flowing sentence (CLAUDE.md's number-display rule prefers this
    // over a stat grid) -- every value is a named slot filled from `data`,
    // the same discipline the LLM's narration templates use in core/planner.
    document.getElementById("obTargetSentence").innerHTML =
      `About <span class="accent">${fmtKcal(e.kcal)} kcal</span> a day — around ` +
      `<span class="accent">${fmtGrams(p.base_g)} g protein · ${fmtGrams(data.fat_g)} g fat · ` +
      `${fmtGrams(data.carb_g)} g carb</span>, with at least ${fmtGrams(data.fibre_g_min)} g fibre and sodium ` +
      `held under ${fmtKcal(data.sodium_mg_max)} mg. ${data.disclosure || ""}`;

    const warnBlock = document.getElementById("obWarningsBlock");
    const warnList = document.getElementById("obWarnings");
    warnList.innerHTML = "";
    if (data.warnings && data.warnings.length > 0) {
      warnBlock.hidden = false;
      for (const w of data.warnings) {
        const row = document.createElement("div");
        row.className = "ob-callout-item";
        row.innerHTML = `<span class="dot"></span><span>${w}</span>`;
        warnList.appendChild(row);
      }
    } else {
      warnBlock.hidden = true;
    }

    document.getElementById("obEnergy").textContent =
      `≈ ${fmtKcal(e.kcal)} kcal/day (±${fmtPct(e.uncertainty)}, so roughly ` +
      `${fmtKcal(e.low)}–${fmtKcal(e.high)} kcal) · BMR ${fmtKcal(data.bmr_kcal)} kcal · ` +
      `TDEE ${fmtKcal(data.tdee_kcal)} kcal`;

    // base_g, not quality_adjusted_g. Changed 2026-08-02 with the DIAAS
    // reversal in core/nutrition/targets.py: the planner now gates on base_g,
    // and this line showed the other number. A displayed target that is not
    // the target being solved against is the precise failure this project
    // exists to prevent, so the two must move together.
    //
    // quality_adjusted_g is still shown, demoted and labelled, because the
    // per-diet DIAAS constants are still in the registry and a reader who saw
    // them in the citation panel with nothing referencing them would
    // reasonably conclude something was broken.
    document.getElementById("obProtein").textContent =
      `${fmtGrams(p.base_g)} g/day (${fmtRatio(p.g_per_kg)} g/kg) · protein ` +
      `quality is not applied to this target: DIAAS ${p.diaas} would imply ` +
      `${fmtGrams(p.quality_adjusted_g)} g, which is not what the plan is checked against`;

    document.getElementById("obMacros").textContent =
      `${fmtGrams(data.fat_g)} g fat · ${fmtGrams(data.carb_g)} g carbohydrate`;

    document.getElementById("obFibreSodium").textContent =
      `≥ ${fmtGrams(data.fibre_g_min)} g fibre · ≤ ${fmtKcal(data.sodium_mg_max)} mg sodium`;

    // The citation panel now sits under the numbers in the same column with
    // no inner scroll of its own (styles.css .ob-review-side), so on anything
    // above a phone it opens eagerly rather than making the user find it.
    // Setting .open fires the existing "toggle" listener, which is the one
    // place /api/science is fetched — no separate load path is added.
    if (window.matchMedia("(min-width: 720px)").matches) {
      scienceExpander.open = true;
    }
  }

  // ------------------------------------------------------------------
  // "Why these numbers?" — GET /api/science, fetched live, never hardcoded
  // citation text in this file (DESIGN_SYSTEM.md, "Content redundancy rule").
  // ------------------------------------------------------------------

  const scienceExpander = document.getElementById("obScienceExpander");
  const scienceLoadingEl = document.getElementById("obScienceLoading");
  const scienceScopeEl = document.getElementById("obScienceScope");
  const scienceListEl = document.getElementById("obScienceList");

  scienceExpander.addEventListener("toggle", async () => {
    if (!scienceExpander.open || scienceCache) return;
    scienceLoadingEl.hidden = false;
    try {
      const res = await fetch(`${API_BASE}/api/science`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      scienceCache = await res.json();
      renderScience(scienceCache);
    } catch (err) {
      scienceScopeEl.textContent = `Couldn't load /api/science: ${err.message}`;
    } finally {
      scienceLoadingEl.hidden = true;
    }
  });

  // core.nutrition.citations.Grade's values, as display text. The panel used
  // to print the enum member verbatim, so the strongest and weakest grades in
  // the project both reached the screen as snake_case: "primary_measurement",
  // "national_table", "project_estimate", "project_decision".
  //
  // These are a strict 1:1 rename, and deliberately so. The brief says to
  // keep the source panel's DOIs and unverified flags exactly as they are,
  // and the same applies to the grades: "Project estimate" makes precisely
  // the claim "project_estimate" made, no softer. Nothing here abbreviates a
  // weak grade into sounding like a strong one -- that would be the failure
  // this panel exists to prevent, committed in the presentation layer.
  const GRADE_LABELS = {
    primary_measurement: "Primary measurement",
    national_table: "National food table",
    textbook: "Textbook",
    project_estimate: "Project estimate",
    project_decision: "Project decision",
  };

  // An unrecognised grade renders "Ungraded", NOT prettified prose. This is
  // the one place the dashboard's humanise() fallback would be wrong: a grade
  // added to core.nutrition.citations.Grade after this file was written would
  // come out of "_"->space as e.g. "Secondary compilation" — sentence case,
  // plausible, sitting in the same slot as "Primary measurement", and
  // asserting an evidence strength this file has no basis to assert. Falling
  // back to a label that is visibly weaker than every real grade is the only
  // safe direction to be wrong in. See dashboard.js, above humanise(), for
  // which fields may take the prettifying fallback and which may not.
  const gradeLabel = (g) => GRADE_LABELS[g] || "Ungraded";

  function renderScience(data) {
    scienceScopeEl.textContent = data.scope_statement;
    scienceListEl.innerHTML = "";
    for (const e of data.evidence) {
      const row = document.createElement("div");
      row.className = "ob-source-row";
      const verifiedCls = e.verified ? "verified-yes" : "verified-no";
      const verifiedTxt = e.verified ? "verified" : "unverified";
      const doi = e.doi ? ` · DOI ${e.doi}` : "";
      row.innerHTML =
        `<span class="k">${e.summary}</span> — measures: ${e.phenomenon}. ${e.source} ` +
        `(${gradeLabel(e.grade)}, ` +
        `<span class="${verifiedCls}">${verifiedTxt}</span>)${doi}`;
      scienceListEl.appendChild(row);
    }
  }

  // ------------------------------------------------------------------
  // Header — the shared one (web/header.js), in its "onboarding" state: the
  // logo, plus "Signed in as <email>" and Log out when a session cookie is
  // currently valid (real state via GET /api/auth/me), and nothing else.
  // That omission is the deliberate part; header.js states why.
  // ------------------------------------------------------------------

  let currentUser = null;

  function renderAuthBar() {
    ArusuvaiHeader.render("onboarding", currentUser);
  }

  ArusuvaiHeader.init({
    state: "onboarding",
    current: "onboarding",
    onLogout: async () => {
      await ArusuvaiAuth.logout();
      currentUser = null;
      renderAuthBar();
      // Step 6 branches on the session, so logging out mid-flow has to swap it
      // back to the create/sign-in shape rather than leave a confirmation panel
      // naming an account nobody is signed into any more.
      paintAccountStep();
    },
  });

  // ------------------------------------------------------------------
  // Step 6 — the account/save hinge, not a plan call. This step replaces
  // the shared auth-modal popup (web/auth.js's initAuthModal) on this page
  // with the design's own inline tabbed form; the modal itself is untouched
  // and still used by index.html. Whether the visitor creates an account or
  // signs into an existing one, the profile just filled in during steps 1-5
  // is what gets persisted (PUT /api/profile) -- the actual plate-picker and
  // POST /api/plan call live on dashboard.html, gated on the session this
  // step establishes.
  // ------------------------------------------------------------------

  const tabSignup = document.getElementById("obTabSignup");
  const tabSignin = document.getElementById("obTabSignin");
  const accountEmail = document.getElementById("obAccountEmail");
  const accountPassword = document.getElementById("obAccountPassword");
  const accountError = document.getElementById("obAccountError");
  const accountSubmit = document.getElementById("obAccountSubmit");
  const accountLoading = document.getElementById("obAccountLoading");
  const accountAnon = document.getElementById("obAccountAnon");
  const accountKnown = document.getElementById("obAccountKnown");
  const accountKnownEmail = document.getElementById("obAccountKnownEmail");
  const accountTitle = document.getElementById("obAccountTitle");
  const accountLede = document.getElementById("obAccountLede");

  let accountMode = "signup";
  let pendingColdSignin = false; // true only for the ?next=dashboard entry path

  // The step has two mutually exclusive shapes, chosen by whether a session
  // exists — not one shape with a header that contradicts it. Previously this
  // step always rendered the create-account form, so a signed-in user saw
  // "Signed in as you@example.com · Log out" in the header directly above a
  // panel asking them to "Create account & see my plan". There is nothing to
  // create; the only remaining job is confirming where the profile is saved.
  function paintAccountStep() {
    const known = Boolean(currentUser) && !pendingColdSignin;
    accountAnon.hidden = known;
    accountKnown.hidden = !known;

    if (known) {
      accountKnownEmail.textContent = currentUser.email;
      accountTitle.textContent = "Save these targets to your account.";
      accountLede.textContent =
        "You're already signed in, so there's nothing to set up — this just stores the profile you " +
        "filled in and takes you to your plan.";
      accountSubmit.textContent = "Save profile & build my plan";
      accountError.hidden = true;
      return;
    }

    accountTitle.textContent = "Save your profile and see your plan.";
    accountLede.textContent =
      "Your targets are ready. Create an account to keep them and generate your first plate — it takes a moment.";

    const signup = accountMode === "signup";
    tabSignup.classList.toggle("is-selected", signup);
    tabSignup.setAttribute("aria-selected", signup ? "true" : "false");
    tabSignin.classList.toggle("is-selected", !signup);
    tabSignin.setAttribute("aria-selected", !signup ? "true" : "false");
    accountSubmit.textContent = signup
      ? "Create account & build my plan"
      : pendingColdSignin ? "Sign in" : "Sign in & save my profile";
    accountError.hidden = true;
  }

  tabSignup.addEventListener("click", () => { accountMode = "signup"; paintAccountStep(); });
  tabSignin.addEventListener("click", () => { accountMode = "signin"; paintAccountStep(); });

  for (const [inputId, cellId, errId] of [
    ["obAccountEmail", "cellEmail", "errEmail"],
    ["obAccountPassword", "cellPassword", "errPassword"],
  ]) {
    document.getElementById(inputId).addEventListener("input", () => setFieldError(cellId, errId, null));
  }

  // Per-field, like step 1, rather than one message above the button that
  // left both inputs unmarked.
  function validateAccountStep() {
    const email = accountEmail.value.trim();
    const password = accountPassword.value;
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    const passwordOk = password.length >= 8;
    setFieldError("cellEmail", "errEmail", emailOk ? null : "Enter an email address in the form you@example.com.");
    setFieldError("cellPassword", "errPassword", passwordOk ? null : "Passwords need at least 8 characters.");
    if (!emailOk) { accountEmail.focus(); return false; }
    if (!passwordOk) { accountPassword.focus(); return false; }
    return true;
  }

  accountSubmit.addEventListener("click", async () => {
    const alreadySignedIn = Boolean(currentUser) && !pendingColdSignin;
    if (!alreadySignedIn && !validateAccountStep()) return;

    accountError.hidden = true;
    accountSubmit.disabled = true;
    accountSubmit.hidden = true;
    accountLoading.hidden = false;
    try {
      // Signed in already: no auth call at all, just persist the profile.
      if (alreadySignedIn) {
        await ArusuvaiAuth.saveProfile(collectProfile());
        window.location.href = "dashboard.html";
        return;
      }
      const email = accountEmail.value.trim();
      const password = accountPassword.value;
      const data = accountMode === "signup"
        ? await ArusuvaiAuth.signup(email, password, pendingColdSignin ? undefined : collectProfile())
        : await ArusuvaiAuth.login(email, password);
      currentUser = data.user;
      renderAuthBar();
      if (pendingColdSignin) {
        window.location.href = "dashboard.html";
        return;
      }
      // Signup already attached the profile above; a sign-in to an existing
      // account still needs the just-completed profile persisted explicitly.
      if (accountMode === "signin") {
        await ArusuvaiAuth.saveProfile(collectProfile());
      }
      window.location.href = "dashboard.html";
    } catch (err) {
      accountLoading.hidden = true;
      accountSubmit.hidden = false;
      accountSubmit.disabled = false;
      accountError.hidden = false;
      accountError.textContent = err.message || "Something went wrong.";
    }
  });

  // ------------------------------------------------------------------
  // Startup: figure out who (if anyone) is signed in, before the wizard
  // shows anything, so a returning user sees their own profile instead of
  // five blank steps, and a cold ?next=dashboard visit (bounced here by
  // dashboard.html's own auth gate) lands straight on step 6's sign-in tab.
  // ------------------------------------------------------------------

  async function init() {
    renderKolam();

    const params = new URLSearchParams(window.location.search);
    const wantsDashboard = params.get("next") === "dashboard";

    try {
      currentUser = await ArusuvaiAuth.me();
    } catch {
      currentUser = null;
    }
    renderAuthBar();

    if (wantsDashboard) {
      if (currentUser) {
        window.location.href = "dashboard.html";
        return;
      }
      pendingColdSignin = true;
      accountMode = "signin";
      paintAccountStep();
      showStep(6);
      return;
    }

    // Paint step 6 for whoever this is BEFORE the wizard shows anything, so
    // the create-account form is never briefly visible to a signed-in user.
    paintAccountStep();

    if (currentUser) {
      let profile = null;
      try {
        profile = await ArusuvaiAuth.getProfile();
      } catch {
        profile = null;
      }
      if (profile) {
        prefillProfile(profile);
        showStep(5);
        fetchTargets();
        return;
      }
    }

    showStep(1);
  }

  init();
})();
