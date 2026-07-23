// web/onboarding.js — the onboarding page's only logic: collect the form,
// POST it to the real /api/targets endpoint, render exactly what comes back.
//
// This file computes NOTHING nutritional. Every number rendered below is a
// property read off the API response; there is no arithmetic on a gram value
// anywhere in this file (CLAUDE.md, "Central invariant" — the invariant binds
// web/ too, not only the LLM).

(() => {
  "use strict";

  // Dev-only: uvicorn's default port. api/main.py's CORS list assumes this
  // page is served from :3000 or :8000 (a different port than the API), per
  // its own comment. Change both together if you run the API elsewhere.
  const API_BASE = "http://localhost:8000";

  const form = document.getElementById("obForm");
  const submitBtn = document.getElementById("obSubmit");
  const empty = document.getElementById("obEmpty");
  const errorBox = document.getElementById("obError");
  const output = document.getElementById("obOutput");

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

  function showError(message) {
    empty.hidden = true;
    output.hidden = true;
    errorBox.hidden = false;
    errorBox.textContent = message;
  }

  function fmtKcal(n) {
    return Math.round(n).toLocaleString("en-IN");
  }

  function fmtG(n) {
    return Math.round(n * 10) / 10;
  }

  function fmtPct(fraction) {
    return `${Math.round(fraction * 100)}%`;
  }

  // Renders the API response verbatim — no field is recomputed here, only
  // formatted (rounding for display is not a nutritional computation; the
  // underlying value shown in "sources" and used by any real plan is exact).
  function renderResult(data) {
    empty.hidden = true;
    errorBox.hidden = true;
    output.hidden = false;

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

    const sourcesEl = document.getElementById("obSources");
    sourcesEl.innerHTML = "";
    for (const s of data.sources) {
      const row = document.createElement("div");
      row.className = "ob-source-row";
      const verifiedCls = s.verified ? "verified-yes" : "verified-no";
      const verifiedTxt = s.verified ? "verified" : "unverified";
      const doi = s.doi ? ` · DOI ${s.doi}` : "";
      row.innerHTML =
        `<span class="k">${s.key}</span> = ${s.value} ${s.unit} — ${s.source} ` +
        `(${s.grade}, <span class="${verifiedCls}">${verifiedTxt}</span>)${doi}`;
      sourcesEl.appendChild(row);
    }
  }

  async function submitProfile(profile) {
    let res;
    try {
      res = await fetch(`${API_BASE}/api/targets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
    } catch (networkErr) {
      throw new Error(
        `Couldn't reach the targets API at ${API_BASE}. Is it running? ` +
        `Start it with: uvicorn api.main:app --reload`
      );
    }

    if (res.status === 422) {
      const body = await res.json().catch(() => null);
      const detail = body && body.detail
        ? (Array.isArray(body.detail) ? body.detail.map((d) => d.msg || JSON.stringify(d)).join("; ") : body.detail)
        : "Invalid input.";
      throw new Error(`The API rejected this profile: ${detail}`);
    }

    if (!res.ok) {
      throw new Error(`The API returned an unexpected error (HTTP ${res.status}).`);
    }

    return res.json();
  }

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = "Computing…";
    try {
      const profile = collectProfile();
      const data = await submitProfile(profile);
      renderResult(data);
    } catch (err) {
      showError(err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Compute my targets";
    }
  });
})();
