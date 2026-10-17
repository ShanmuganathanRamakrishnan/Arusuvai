"""TASKS_3.md V1: what stands between today's library and one validated plate.

Measurement only. Nothing in ``data/`` or ``core/`` is edited: each scenario
is applied to an in-memory copy of the loaded library (and, for the process
scenario, to the in-memory constant registry before recipes load) and thrown
away.

Four scenarios, each a question about a blocker, not a plan to build:

- ``today``: the library as it is.
- ``rows_checked``: every ingredient row has been read from its primary source
  by a person (``verified=True``, so the loader's verified composition band,
  ``composition.verified_primary``, replaces ``composition.unverified_secondary``).
  Recipes' process bands are unchanged.
- ``process_known``: every process a recipe declares unassessed has a sourced,
  checked constant that adds NO band (``process.unassessed_uncertainty`` read
  as 0.0 at load; every ``process_key`` line counted as resting on opened
  evidence). This is the best case for finding 41, not a forecast: a real
  steaming or boiling constant would carry a band of its own.
- ``both``: both of the above.

Per scenario it reports:

1. recipes clearing both eligibility ceilings
   (``eligibility.max_protein_uncertainty``, ``eligibility.max_energy_uncertainty``),
   the gate ``build_candidate_pool(dev_mode=False)`` applies;
2. of the 864 bodies-and-meals in ``tests/test_meal_coverage.py``'s grid,
   how many get a passing plate with ``dev_mode=False``;
3. of those plates, how many are under the 15% unverified-energy threshold
   (``docs/methodology.md``, "The 15% unverified-energy shipping threshold").

Then two things no scenario can change:

4. the target side: which of the constants ``core.nutrition.targets`` reads
   rest on evidence that can never be marked verified (a project estimate has
   no document to open; ``Evidence.__post_init__`` refuses it);
5. for ``process_known``, the fewest ingredient rows each recipe needs checked
   to clear the protein ceiling (largest protein share first), and how many
   recipes each row unblocks -- the order a person checking rows should take.

Run from the repo root:
    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/v1_validated_plate.py
"""

from __future__ import annotations

import dataclasses
import logging
import re
from collections import Counter

import core.foods.nutrition_of as nutrition_of
from core.foods.nutrition_of import nutrition_of_components
from core.nutrition import citations
from core.nutrition import targets as targets_mod
from core.nutrition.targets import derive_target
from core.planner.candidates import TARGET_CRITICAL_MACROS, _eligibility_flags
from core.planner.plan import Library, load_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region

from core.schemas.profile import ActivityLevel, Goal, Sex

logging.disable(logging.WARNING)

THRESHOLD = 0.15  # docs/methodology.md's provisional figure; not a registered constant
DIETS = ("vegetarian", "eggetarian", "non_vegetarian", "vegan")


def _load(process_known: bool) -> Library:
    key = "process.unassessed_uncertainty"
    real = citations._CONSTANTS[key]
    real_check = nutrition_of._process_verified
    if process_known:
        citations._CONSTANTS[key] = dataclasses.replace(real, value=0.0)
        nutrition_of._process_verified = lambda process_key: True
    try:
        return load_library()
    finally:
        citations._CONSTANTS[key] = real


def _rows_checked(lib: Library) -> Library:
    band = citations.value_of("composition.verified_primary")
    ingredients = {
        k: dataclasses.replace(
            ing, verified=True,
            composition_uncertainty={m: band for m in ing.composition_uncertainty},
        )
        for k, ing in lib.ingredients.items()
    }
    return Library(ingredients=ingredients, recipes=lib.recipes)


def _eligible(lib: Library) -> list[str]:
    return sorted(
        c.recipe.id for c in lib.components()
        if not _eligibility_flags(c, lib.ingredients)
    )


def _grid(lib: Library) -> tuple[int, int, list[float]]:
    planned = 0
    under = 0
    fractions = []
    for eats_snack in (True, False):
        for slot in (MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER):
            for region in (Region.SOUTH_INDIAN, Region.NORTH_INDIAN):
                for d in DIETS:
                    diet = DietPattern(d)
                    for goal in Goal:
                        for sex in (Sex.MALE, Sex.FEMALE):
                            for w in (55, 70, 90):
                                p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                                            activity=ActivityLevel.MODERATE, goal=goal,
                                            diet=diet, eats_snack=eats_snack)
                                out = plan_meal(lib, derive_target(p).nutrition_target,
                                                region=region, meal_slot=slot,
                                                diet_pattern=diet, profile=p, dev_mode=False)
                                if out.plan is None or not out.result.passed:
                                    continue
                                planned += 1
                                f = out.plan.estimate.unverified_energy_fraction()
                                fractions.append(f)
                                if f < THRESHOLD:
                                    under += 1
    return planned, under, fractions


def _min_rows(component, ingredients, ceiling) -> list[str] | None:
    """Fewest rows to verify (largest protein share first) to clear the ceiling."""

    band = citations.value_of("composition.verified_primary")
    count = component.recipe.serving_unit.min_count
    lines = sorted(
        {line.ingredient_id for line in component.recipe.ingredients},
        key=lambda i: -ingredients[i].for_grams(
            sum(l.quantity_g for l in component.recipe.ingredients if l.ingredient_id == i)
        ).protein_g,
    )
    current = dict(ingredients)
    chosen: list[str] = []
    for row in [None, *lines]:
        if row is not None:
            if current[row].verified:
                continue
            current[row] = dataclasses.replace(
                current[row], verified=True,
                composition_uncertainty={m: band for m in current[row].composition_uncertainty},
            )
            chosen.append(row)
        est = nutrition_of_components([(component, count)], current)
        if est.uncertainty_fraction("protein_g") <= ceiling:
            return chosen
    return None


def main() -> None:
    real_check = nutrition_of._process_verified
    base = _load(process_known=False)
    known = _load(process_known=True)
    scenarios = {
        "today": (base, False),
        "rows_checked": (_rows_checked(base), False),
        "process_known": (known, True),
        "both": (_rows_checked(known), True),
    }
    n_recipes = len(base.components())
    print(f"recipes in library: {n_recipes}; ingredient rows: {len(base.ingredients)}, "
          f"verified today: {sum(i.verified for i in base.ingredients.values())}")
    print(f"ceilings: " + ", ".join(
        f"{m} {citations.value_of(k)}" for m, k in TARGET_CRITICAL_MACROS.items()))
    print()
    print(f"{'scenario':<14} {'eligible recipes':>17} {'plates (of 864)':>16} "
          f"{'under 15% unverified':>21}")
    for name, (lib, process_known) in scenarios.items():
        nutrition_of._process_verified = (lambda k: True) if process_known else real_check
        try:
            eligible = _eligible(lib)
            planned, under, fractions = _grid(lib)
        finally:
            nutrition_of._process_verified = real_check
        print(f"{name:<14} {len(eligible):>10} of {n_recipes:<4} {planned:>10} "
              f"{under:>14}" + (f"   (unverified energy {min(fractions):.0%}-{max(fractions):.0%})"
                                if fractions else ""))
        if name in ("rows_checked", "both"):
            print(f"{'':<14} eligible: {', '.join(eligible) if eligible else '(none)'}")

    print()
    print("target side -- constants derive_target reads, by evidence grade:")
    grades = Counter()
    never = []
    for k in targets_mod._SOURCE_KEYS:
        ev = citations.evidence(citations.constant(k).evidence_id)
        grades[ev.grade.value] += 1
        if ev.grade is citations.Grade.PROJECT_ESTIMATE:
            never.append(f"{k} ({ev.id})")
    for g, n in sorted(grades.items()):
        print(f"  {g:<22} {n}")
    print(f"  can never be verified (project estimate): {len(never)}")
    for line in never:
        print(f"    {line}")
    read_not_listed = sorted(
        k for k in ("protein.weight_cap_bmi", "diaas.pescatarian")
        if k not in targets_mod._SOURCE_KEYS
    )
    print(f"  read by derive_target but missing from _SOURCE_KEYS: {read_not_listed}")
    print("process constants (oil uptake, yields), by evidence grade:")
    for k in sorted(c.key for c in citations.all_constants()
                    if c.key.startswith(("oil_uptake.", "yield.", "process."))):
        print(f"  {k:<40} {citations.evidence(citations.constant(k).evidence_id).grade.value}")

    print()
    print("today's process bands: fewest rows each recipe needs checked to clear protein "
          f"{citations.value_of('eligibility.max_protein_uncertainty')}")
    need = Counter()
    unreachable = []
    for c in base.components():
        rows = _min_rows(c, base.ingredients, citations.value_of("eligibility.max_protein_uncertainty"))
        if rows is None:
            unreachable.append(c.recipe.id)
            continue
        for r in rows:
            need[r] += 1
    print(f"  recipes that cannot clear it even with every row checked: "
          f"{unreachable if unreachable else 'none'}")
    print("  rows by number of recipes that need them, and whether the row names a")
    print("  source a person could open today (IFCT code, or a USDA FDC id in its note):")
    for row, n in need.most_common():
        print(f"    {n:>3}  {row:<22} {_source_kind(base.ingredients[row])}")
    kinds = Counter(_source_kind(i).split(" (")[0].split(":")[0] for i in base.ingredients.values())
    print(f"  all {len(base.ingredients)} rows: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))


def _notes() -> dict[str, str]:
    import csv
    with open("data/raw/ifct/fixture_ingredients.csv", encoding="utf-8") as f:
        return {r["id"]: r["source_note"] for r in csv.DictReader(f)}


_NOTES: dict[str, str] = {}


def _source_kind(ing) -> str:
    if not _NOTES:
        _NOTES.update(_notes())
    note = _NOTES.get(ing.id, "").lower()
    if ing.ifct_code:
        return "names a source (IFCT " + ing.ifct_code + ")"
    # An FDC id, not the words: the two oil rows say "USDA FoodData Central"
    # only to say a source like it is still needed (docs/audit_log.md "V2").
    if re.search(r"fdc(?: id)? *\d{5,7}", note):
        return "names a source (USDA FDC)"
    return "no source named: needs sourcing first"


if __name__ == "__main__":
    main()
