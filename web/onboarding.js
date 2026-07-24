// web/onboarding.js — the six-step onboarding wizard.
//
// This file computes NOTHING nutritional. Every number rendered below is a
// property read off a real API response (POST /api/targets, POST /api/auth/*,
// GET /api/science); there is no arithmetic on a gram value anywhere in this
// file (CLAUDE.md, "Central invariant" — the invariant binds web/ too, not
// only the LLM). Steps 1-5 need no account: they collect the profile in
// browser memory and call /api/targets exactly as before this increment.
// Step 6 is the new account/save hinge — sign up or sign in, persist the
// profile against the resulting user_id (POST /api/profile), and hand off to
// dashboard.html, which is where POST /api/plan now lives, gated on the
// session this step establishes. See auth.js for the signup/login/session
// calls this file shares with dashboard.js.

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
  const restartBtn = document.getElementById("obRestart");
  const endpointLabel = document.getElementById("obEndpointLabel");
  const progressSteps = Array.from(document.querySelectorAll(".ob-progress-step"));

  let currentStep = 1;
  let targetsLoaded = false;
  let scienceCache = null;

  // ------------------------------------------------------------------
  // Formatting — display only. See onboarding.js's header note: nothing
  // below performs a nutritional computation, only rounds a value the API
  // already computed for presentation.
  // ------------------------------------------------------------------

  function fmtKcal(n) {
    return Math.round(n).toLocaleString("en-IN");
  }

  function fmtG(n) {
    return Math.round(n * 10) / 10;
  }

  function fmtPct(fraction) {
    return `${Math.round(fraction * 100)}%`;
  }


  // ------------------------------------------------------------------
  // Step navigation
  // ------------------------------------------------------------------

  function showStep(n) {
    currentStep = n;
    document.querySelectorAll(".ob-step").forEach((el) => {
      el.hidden = Number(el.dataset.step) !== n;
    });
    progressSteps.forEach((btn) => {
      const s = Number(btn.dataset.step);
      btn.classList.toggle("is-current", s === n);
      btn.classList.toggle("is-done", s < n);
    });
    updateNav();
    window.scrollTo({ top: form.offsetTop - 90, behavior: "smooth" });
  }

  function updateNav() {
    backBtn.hidden = currentStep === 1 || currentStep === TOTAL_STEPS;
    restartBtn.hidden = currentStep !== TOTAL_STEPS;
    nextBtn.hidden = currentStep === TOTAL_STEPS;

    if (currentStep === 5) {
      nextBtn.textContent = "Continue to save →";
      nextBtn.disabled = !targetsLoaded;
    } else {
      nextBtn.textContent = "Continue";
      nextBtn.disabled = false;
    }

    endpointLabel.textContent = currentStep === 5 ? `Calling ${API_BASE}/api/targets` : "";
  }

  backBtn.addEventListener("click", () => {
    if (currentStep > 1) showStep(currentStep - 1);
  });

  restartBtn.addEventListener("click", () => {
    window.location.reload();
  });

  nextBtn.addEventListener("click", async () => {
    if (currentStep === 1) {
      const weight = Number(form.weight_kg.value);
      const height = Number(form.height_cm.value);
      const age = Number(form.age_years.value);
      if (!(weight > 0 && height > 0 && age > 0)) {
        window.alert("Weight, height and age must all be positive numbers.");
        return;
      }
    }
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
      showSaveStep();
      return;
    }
  });

  // ------------------------------------------------------------------
  // Profile assembly — read straight from the one <form>; every field
  // persists across steps because the fieldsets share one form and are only
  // hidden, never removed.
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
    form.sex.value = p.sex;
    form.activity.value = p.activity;
    form.goal.value = p.goal;
    form.diet.value = p.diet;
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
    pill.textContent = data.status;
    pill.className = "ob-status-pill " + (data.status === "validated" ? "validated" : "dev-mode");

    document.getElementById("obDisclosure").textContent = data.disclosure || "";

    const e = data.energy;
    document.getElementById("obEnergy").textContent =
      `≈ ${fmtKcal(e.kcal)} kcal/day (±${fmtPct(e.uncertainty)}, so roughly ` +
      `${fmtKcal(e.low)}–${fmtKcal(e.high)} kcal) · BMR ${fmtKcal(data.bmr_kcal)} kcal · ` +
      `TDEE ${fmtKcal(data.tdee_kcal)} kcal`;

    const p = data.protein;
    document.getElementById("obProtein").textContent =
      `${fmtG(p.quality_adjusted_g)} g/day (${fmtG(p.g_per_kg)} g/kg base, ` +
      `${fmtG(p.base_g)} g before quality adjustment, DIAAS ${p.diaas})`;

    document.getElementById("obMacros").textContent =
      `${fmtG(data.fat_g)} g fat · ${fmtG(data.carb_g)} g carbohydrate`;

    document.getElementById("obFibreSodium").textContent =
      `≥ ${fmtG(data.fibre_g_min)} g fibre · ≤ ${fmtKcal(data.sodium_mg_max)} mg sodium`;

    const warnBlock = document.getElementById("obWarningsBlock");
    const warnList = document.getElementById("obWarnings");
    warnList.innerHTML = "";
    if (data.warnings && data.warnings.length > 0) {
      warnBlock.hidden = false;
      for (const w of data.warnings) {
        const li = document.createElement("li");
        li.textContent = w;
        warnList.appendChild(li);
      }
    } else {
      warnBlock.hidden = true;
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
        `(${e.grade}, <span class="${verifiedCls}">${verifiedTxt}</span>)${doi}`;
      scienceListEl.appendChild(row);
    }
  }

  // ------------------------------------------------------------------
  // Auth bar — shown on every step, reflects whether a session cookie is
  // currently valid. Real state (GET /api/auth/me), not a guess from
  // whether the modal has ever been opened.
  // ------------------------------------------------------------------

  const authBar = document.getElementById("obAuthBar");
  const authBarText = document.getElementById("obAuthBarText");
  const authBarDashboard = document.getElementById("obAuthBarDashboard");
  const authBarLogout = document.getElementById("obAuthBarLogout");
  const authBarSignin = document.getElementById("obAuthBarSignin");

  let currentUser = null;

  function renderAuthBar() {
    authBar.hidden = false;
    const signedIn = !!currentUser;
    authBarText.textContent = signedIn ? `Signed in as ${currentUser.email}` : "";
    authBarDashboard.hidden = !signedIn;
    authBarLogout.hidden = !signedIn;
    authBarSignin.hidden = signedIn;
  }

  authBarSignin.addEventListener("click", () => authModal.open("signin"));
  authBarLogout.addEventListener("click", async () => {
    await ArusuvaiAuth.logout();
    currentUser = null;
    renderAuthBar();
  });

  // ------------------------------------------------------------------
  // The auth modal, shared with dashboard.html via auth.js. getProfile()
  // only matters for a signup started mid-wizard (step 6); a cold "Sign in"
  // click from the auth bar has no in-progress profile to attach.
  // ------------------------------------------------------------------

  const authModal = ArusuvaiAuth.initAuthModal({
    getProfile: () => collectProfile(),
    onAuthed: handleAuthed,
  });

  let pendingColdSignin = false; // true only for the ?next=dashboard entry path

  async function handleAuthed(data) {
    currentUser = data.user;
    renderAuthBar();
    if (pendingColdSignin) {
      window.location.href = "dashboard.html";
      return;
    }
    if (currentStep === 6) {
      await saveAndGoToDashboard();
    }
  }

  // ------------------------------------------------------------------
  // Step 6 — the account/save hinge, not a plan call. Onboarding itself
  // never requires an account (steps 1-5 work for anyone); this is the one
  // step where creating or signing into an account matters, because saving
  // a profile against a user_id requires knowing which user. The actual
  // plate-picker and POST /api/plan call live on dashboard.html, gated on
  // the session this step establishes.
  // ------------------------------------------------------------------

  const saveSignedOutEl = document.getElementById("obSaveSignedOut");
  const saveSignedInEl = document.getElementById("obSaveSignedIn");
  const saveLoadingEl = document.getElementById("obSaveLoading");
  const saveErrorEl = document.getElementById("obSaveError");

  function showSaveStep() {
    saveErrorEl.hidden = true;
    saveLoadingEl.hidden = true;
    if (currentUser) {
      saveSignedOutEl.hidden = true;
      saveSignedInEl.hidden = false;
      document.getElementById("obSaveEmail").textContent = currentUser.email;
    } else {
      saveSignedOutEl.hidden = false;
      saveSignedInEl.hidden = true;
    }
  }

  document.getElementById("obOpenSignup").addEventListener("click", () => authModal.open("signup"));
  document.getElementById("obOpenSignin").addEventListener("click", () => authModal.open("signin"));
  document.getElementById("obSaveContinue").addEventListener("click", saveAndGoToDashboard);

  async function saveAndGoToDashboard() {
    saveErrorEl.hidden = true;
    saveLoadingEl.hidden = false;
    saveSignedOutEl.hidden = true;
    saveSignedInEl.hidden = true;
    try {
      await ArusuvaiAuth.saveProfile(collectProfile());
      window.location.href = "dashboard.html";
    } catch (err) {
      saveLoadingEl.hidden = true;
      saveErrorEl.hidden = false;
      saveErrorEl.textContent = `Couldn't save your profile: ${err.message}`;
      showSaveStep();
    }
  }

  // ------------------------------------------------------------------
  // Startup: figure out who (if anyone) is signed in, before the wizard
  // shows anything, so a returning user sees their own profile instead of
  // five blank steps (this increment's explicit requirement) and a cold
  // ?next=dashboard visit (bounced here by dashboard.html's own auth gate)
  // can go straight back once signed in.
  // ------------------------------------------------------------------

  async function init() {
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
      showStep(1);
      authModal.open("signin");
      return;
    }

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
