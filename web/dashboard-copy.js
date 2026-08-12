// web/dashboard-copy.js — the dashboard's copy and label lookup tables.
//
// Extracted 2026-08-12 (D14) from web/dashboard.js as a structure-only split:
// pure data and pure string functions, no DOM access, no API calls. Consumed
// by web/dashboard-success.js and web/dashboard-decline.js.
//
// Same pattern as ArusuvaiAuth (auth.js) and ArusuvaiHeader (header.js): a
// plain script include, no build step, one global namespace.

(() => {
  "use strict";

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

  const ArusuvaiDashboardCopy = {
    PLATE_LABELS,
    DIET_LABELS,
    GOAL_LABELS,
    FLAG_LABELS,
    humanise,
    MACRO_COPY,
    BOUND_SOURCE_CLAUSE,
    RELAXABILITY_NOTE,
    SLOT_LABELS,
    DECLINE_PATHS,
  };

  window.ArusuvaiDashboardCopy = ArusuvaiDashboardCopy;
})();
