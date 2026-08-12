// web/dashboard-success.js — the dashboard's success view: a solved plate.
//
// Extracted 2026-08-12 (D14) from web/dashboard.js as a structure-only split.
// Takes plan data (and the saved profile, needed for the diet/goal sentence)
// in, writes DOM out. Nothing else -- no API calls, no page state of its own.
//
// Same pattern as ArusuvaiAuth (auth.js) and ArusuvaiHeader (header.js): a
// plain script include, no build step, one global namespace.

(() => {
  "use strict";

  const Copy = ArusuvaiDashboardCopy;

  function fmtKcal(n) {
    return Math.round(n).toLocaleString("en-IN");
  }
  function fmtG(n) {
    return Math.round(n * 10) / 10;
  }

  // D15 visual pass: the icon-plus-sentence amber card ported from Claude
  // Design's "Arusuvai Dashboard v2.dc.html". Markup only -- the sentence
  // itself is still composed from real fields exactly as before this pass.
  function amberCallout(text) {
    return (
      '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v5M12 7.6v.1"></path></svg>' +
      `<p>${text}</p>`
    );
  }

  function plateLabel(plate) {
    // Both halves go through humanise(): a region or meal slot added to
    // core/schemas after this map was written would otherwise reach the
    // eyebrow as "south_indian · breakfast".
    return (
      Copy.PLATE_LABELS[`${plate.region}:${plate.meal_slot}`] ||
      `${Copy.humanise(plate.region)} · ${Copy.humanise(plate.meal_slot).toLowerCase()}`
    );
  }

  // Tag row: only diet and goal come from the saved profile -- ProfileIn/Out
  // carries no region preference (region_pref is collected on onboarding's
  // diet step but not part of the schema; only the plate picker below picks
  // a region, per plate). Fabricating a third "region" tag here from
  // something the profile doesn't actually store would be exactly the kind
  // of unverified claim CLAUDE.md's process rule forbids.
  function renderProfileTags(p) {
    const wrap = document.getElementById("dashProfileTags");
    wrap.innerHTML =
      `<span class="tag">${Copy.DIET_LABELS[p.diet] || Copy.humanise(p.diet)}</span>` +
      `<span class="tag">${Copy.GOAL_LABELS[p.goal] || Copy.humanise(p.goal)}</span>`;
    if (p.clinical_flags.length) {
      const flags = p.clinical_flags.map((f) => Copy.FLAG_LABELS[f] || Copy.humanise(f)).join(", ");
      wrap.innerHTML += `<span class="tag">${flags}</span>`;
    }
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
      el.className = "";
      el.innerHTML = "";
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
    const text =
      `Not validated. ${share}` +
      `The nutrition data behind these dishes is unconfirmed, so treat the numbers as ` +
      `an illustration of the method rather than dietary advice.`;
    el.className = "dash-callout-amber";
    el.innerHTML = amberCallout(text);
  }

  function renderPlanSuccess(data, plate, profile) {
    document.getElementById("obPlanSuccess").hidden = false;
    const label = plateLabel(plate);

    document.getElementById("obSuccessEyebrow").textContent = `Your plate · ${label}`;

    const est = data.estimate;
    document.getElementById("obSuccessSentence").innerHTML = est
      ? `${Copy.DIET_LABELS[profile.diet] || Copy.humanise(profile.diet)} components tuned to your ${(Copy.GOAL_LABELS[profile.goal] || Copy.humanise(profile.goal)).toLowerCase()} target — about ` +
        `<span class="accent">${fmtKcal(est.energy_kcal)} kcal</span> with <span class="accent">${fmtG(est.protein_g)} g protein</span>.`
      // Not "a validated combination", which is what this read until 2026-08-09
      // and which was false on every plate the app has ever served: nothing in
      // the library can ship as validated (docs/methodology.md), and the
      // provenance line below says so explicitly.
      : `A combination of real components for this plate.`;

    // "On the plate" -- one row per solved component, dot colour alternating
    // purely for visual rhythm (ported from the mockup's dish list), role
    // line reads the real component category (data already on the wire, not
    // invented for this pass).
    const wrap = document.getElementById("obPlanMeals");
    wrap.className = "dash-dish-card";
    wrap.innerHTML = `<div class="dash-dish-card-label">On the plate · ${label}</div>`;
    data.components.forEach((c, i) => {
      const row = document.createElement("div");
      row.className = "dash-dish-row";
      row.innerHTML =
        `<span class="dash-dish-dot ${i % 2 ? "b" : "a"}" aria-hidden="true"></span>` +
        `<div class="dash-dish-body">` +
        `<div class="dash-dish-name">${c.recipe_name}</div>` +
        `<div class="dash-dish-role">${c.category}</div>` +
        `</div>` +
        `<span class="dash-dish-qty">${c.unit_count} × ${c.unit_name}</span>`;
      wrap.appendChild(row);
    });

    // Plate total: kcal headline, then protein/carb/fat as bars sized to
    // each macro's own gram value relative to the largest of the three shown
    // (a real ratio between numbers already in `est` -- not a comparison
    // against a target, which this response doesn't carry), then fibre and
    // sodium as plain rows since neither shares a unit with the bar trio.
    const totalEl = document.getElementById("obPlanTotal");
    if (est) {
      totalEl.className = "dash-total-card";
      const barMacros = [
        { label: "Protein", value: `${fmtG(est.protein_g)} g`, raw: est.protein_g, color: "var(--green)" },
        { label: "Carbohydrate", value: `${fmtG(est.carb_g)} g`, raw: est.carb_g, color: "var(--amber-deep)" },
        { label: "Fat", value: `${fmtG(est.fat_g)} g`, raw: est.fat_g, color: "rgba(58, 90, 64, .45)" },
      ];
      const maxRaw = Math.max(...barMacros.map((m) => m.raw)) || 1;
      const plainRows = [
        { label: "Fibre", value: `${fmtG(est.fibre_g)} g` },
        { label: "Sodium", value: `${fmtKcal(est.sodium_mg)} mg` },
      ];
      totalEl.innerHTML =
        `<div class="dash-total-label">Plate total</div>` +
        `<div class="dash-total-kcal"><span class="n">${fmtKcal(est.energy_kcal)}</span><span class="u">kcal</span></div>` +
        `<div class="dash-macro-list">` +
        barMacros
          .map(
            (m) =>
              `<div class="dash-macro-row">` +
              `<div class="line"><span class="k">${m.label}</span><span class="v">${m.value}</span></div>` +
              `<div class="dash-macro-bar"><span style="width:${Math.round((m.raw / maxRaw) * 100)}%;background:${m.color}"></span></div>` +
              `</div>`
          )
          .join("") +
        plainRows
          .map(
            (m) =>
              `<div class="dash-macro-row"><div class="line"><span class="k">${m.label}</span><span class="v">${m.value}</span></div></div>`
          )
          .join("") +
        `</div>`;
    } else {
      totalEl.className = "";
      totalEl.innerHTML = "";
    }

    renderProvenance(data);

    const relaxationNote = document.getElementById("obPlanRelaxationNote");
    relaxationNote.textContent = data.relaxation_applied.length ? data.disclosure : "";
  }

  const ArusuvaiDashboardSuccess = {
    render: renderPlanSuccess,
    renderProvenance,
    plateLabel,
    renderProfileTags,
  };

  window.ArusuvaiDashboardSuccess = ArusuvaiDashboardSuccess;
})();
