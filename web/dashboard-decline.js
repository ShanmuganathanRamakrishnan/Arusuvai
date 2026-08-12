// web/dashboard-decline.js — the dashboard's decline view: why the library
// couldn't build a plate, and what to try next.
//
// Extracted 2026-08-12 (D14) from web/dashboard.js as a structure-only split.
// Takes plan data in, writes DOM out. Nothing else -- no API calls, no page
// state of its own. Shares `plateLabel` with the success view rather than
// duplicating it, since both need the same "Your plate · <label>" eyebrow.
//
// Same pattern as ArusuvaiAuth (auth.js) and ArusuvaiHeader (header.js): a
// plain script include, no build step, one global namespace.

(() => {
  "use strict";

  const Copy = ArusuvaiDashboardCopy;

  const fmt = (n, digits) =>
    Number(n).toLocaleString(undefined, {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });

  /** One violation as a sentence a person can read. Never returns a token. */
  function violationSentence(v) {
    if (v.kind === "no_candidates") {
      const slots = (v.blocking_slots || []).map(
        (s) => Copy.SLOT_LABELS[s] || Copy.humanise(s).toLowerCase()
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
    const copy = Copy.MACRO_COPY[v.macro];
    if (!copy) {
      return "One of this plate's nutritional limits couldn't be met.";
    }

    const actual = `${fmt(v.actual, copy.digits)}${copy.unit}`;
    const bound = `${fmt(v.bound, copy.digits)}${copy.unit}`;
    const source = Copy.BOUND_SOURCE_CLAUSE[v.bound_source] || "";

    let sentence;
    if (v.kind === "below_floor") {
      sentence = `${copy.name} reaches only ${actual}, short of the ${bound} this plate needs${source}.`;
    } else if (v.kind === "above_ceiling") {
      sentence = `${copy.name} comes to ${actual}, over the ${bound} limit${source}.`;
    } else {
      sentence = `${copy.name} is ${actual} against a limit of ${bound}${source}.`;
    }

    const flags = (v.locked_by || []).map((f) => Copy.FLAG_LABELS[f] || Copy.humanise(f));
    if (flags.length) {
      // The most important sentence on the screen: the system did not fail to
      // fix this, it declined to.
      sentence +=
        ` We didn't loosen this one, because you told us about ${flags
          .join(" and ")
          .toLowerCase()}.`;
    } else {
      sentence += Copy.RELAXABILITY_NOTE[v.relaxability] || "";
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
    document.getElementById("obPlanDecline").hidden = false;
    const label = ArusuvaiDashboardSuccess.plateLabel(plate);

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
    Copy.DECLINE_PATHS.filter((p) => p.applies(details)).forEach((p, i) => {
      const row = document.createElement("div");
      row.className = "ob-path-item";
      row.innerHTML = `<span class="ob-path-num">${i + 1}</span><span class="ob-path-text">${p.text}</span>`;
      paths.appendChild(row);
    });

    document.getElementById("obDeclineDisclosure").textContent =
      declineDisclosure(details);
    renderDeclineProvenance(data);
  }

  const ArusuvaiDashboardDecline = {
    render: renderPlanDecline,
    violationSentence,
    declineDisclosure,
    renderDeclineProvenance,
  };

  window.ArusuvaiDashboardDecline = ArusuvaiDashboardDecline;
})();
