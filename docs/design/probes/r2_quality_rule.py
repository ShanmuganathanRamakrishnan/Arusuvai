"""R2 — measure the quality-protein rule's options. Adi decides; this file
changes no behaviour and picks nothing.

`TASKS_3.md` R2: "the quality-protein floor is the sole cause of [most]
combination failures... Report the rankable table under each of: (1) today's
rule, unchanged; (2) per-day rather than per-meal floor; (3) threshold
sensitivity at 0.65 and 0.70." This is that measurement.

## What "the rule" is, today

`core.foods.quality.ingredient_qualifies`: an ingredient's protein counts
toward a quality floor iff its `diaas` is present and >=
`protein.quality_diaas_threshold` (0.75). `core.nutrition.meal_target.
_quality_protein_floor` applies a FLAT floor to every meal slot --
`protein.quality_meal_floor_fraction` (0.10) of the day protein floor,
identically for a lunch and a snack, never scaled by the meal's own energy
share. `ProteinTarget.quality_source_day_g` (`protein.quality_day_fraction`,
0.33 of the day protein floor) is the day-level equivalent, computed and
displayed on every derived target, and per its own citation note "gated on
by nothing today ... enforcing a day floor against a one-meal-at-a-time
planner is a reachability question ... not a remaining-budget subtraction."
That gap is exactly what scenario 2 measures the size of.

## How each scenario is measured, and what "does not import what it audits"
means here

**Scenario 1 (today, unchanged) and scenario 3 (threshold sensitivity)**
run the REAL pipeline exactly as shipped -- `core.planner.validator.
plan_within_ladder` against the REAL `core.nutrition.meal_target.meal_target`
output, which means `core.foods.quality`'s real threshold check fires inside
the real solver for every unit-count assignment considered, precisely as it
does for a live user. This file does not reimplement that arithmetic; it
observes the real system's real output. For scenario 3 the one input that
changes is `protein.quality_diaas_threshold` itself, swapped via
`citations._CONSTANTS[key] = dataclasses.replace(original, value=X)` --
the exact pattern already used for exactly this purpose across the test
suite (`tests/test_planner_quality.py`, `tests/test_planner_validator.py`,
`tests/test_nutrition_meal_target.py`, `tests/test_recipes.py` all swap a
constant this same way, restore it in a ``finally``). Swapping the input a
real rule reads and observing real output is independent verification, not
an import of a conclusion.

**Scenario 2 (per-day floor)** cannot be produced this way: there is no
day-level gate to swap an input into, because none exists (the citation note
above is explicit that nothing enforces `quality_source_day_g` today). This
file builds the smallest simulation that can answer the question without
inventing a day-level solver core.planner does not have: for each of a
day's meal slots, strip `quality_protein_floor_g` from that meal's target
(`dataclasses.replace(target, quality_protein_floor_g=None)`) so the real
ladder picks its usual macro-best plate with no quality steering at all,
then read that plate's `quality_protein_g` -- computed by the same real
`core.foods.quality` machinery the solver already calls unconditionally for
every plan (`core.planner.solver.SolvedPlan.quality_protein_g`) -- and sum
it across the day's slots against `quality_source_day_g`. **This measures a
lower bound, not the best a day-aware rule could do**: a real per-day
allocator could deliberately concentrate quality protein into one or two
meals when the macro-optimal choice does not need to. This file states that
plainly rather than claiming to have measured day-level reachability at its
best; see the scenario 2 section of `main()`'s output for the same note.

## The day construction (scenario 2 only)

R4d (`TASKS_3.md`) is still open: no region has all three of
breakfast/lunch/dinner today (south has no dinner template, north has no
breakfast template). A single-region day cannot be built from the current
library, which is itself something R2 should know rather than something
this file works around. Two mixed-region day variants are used instead,
built from exactly the four templates the other probes already measure:

- `south_lunch_day`  = south_indian/breakfast + south_indian/lunch + north_indian/dinner
- `north_lunch_day`  = south_indian/breakfast + north_indian/lunch + north_indian/dinner

Both are reported. Neither is picked as "the" day; R4d is the task that
would make a single-region day possible.

## The profile grid

Same 144-profile grid (6 weights x 3 goals x {VEGETARIAN, VEGAN} x 4
clinical-flag sets) as `probe_rank_input2.py` and `probe_blocking_bounds.py`
-- see either's docstring for why.

## Don't

Per TASKS_3.md: this file changes no behaviour (`citations._CONSTANTS` is
restored after every swap; `core/` is never edited) and does not pick an
answer among the three scenarios. `main()` prints numbers and stops.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/r2_quality_rule.py
"""
from __future__ import annotations

import dataclasses
import logging

from core.foods.templates import template_for
from core.nutrition import citations
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations, feasible_combinations
from core.planner.plan import load_library
from core.planner.solver import solve
from core.planner.validator import plan_within_ladder
from core.schemas import (
    ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

#: >= this many valid plates is "offering choice" -- same threshold every
#: other Phase R probe uses, for the same reason (probe_rank_input2.py).
MIN_VALID_PLATES = 2

TEMPLATES = (
    (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
    (Region.SOUTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)

#: (label, [templates]) -- the two mixed-region day variants. See module
#: docstring, "The day construction".
DAY_VARIANTS = (
    (
        "south_lunch_day",
        (
            (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
            (Region.SOUTH_INDIAN, MealSlot.LUNCH),
            (Region.NORTH_INDIAN, MealSlot.DINNER),
        ),
    ),
    (
        "north_lunch_day",
        (
            (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
            (Region.NORTH_INDIAN, MealSlot.LUNCH),
            (Region.NORTH_INDIAN, MealSlot.DINNER),
        ),
    ),
)

lib = load_library()
logging.disable(logging.WARNING)


def profiles():
    """144 profiles: 6 weights x 3 goals x 2 diets x 4 flag-sets.

    Same grid every other Phase R probe uses -- see probe_rank_input2.py.
    """

    diets = (DietPattern.VEGETARIAN, DietPattern.VEGAN)
    flag_sets = (
        frozenset(),
        frozenset({ClinicalFlag.HYPERTENSION}),
        frozenset({ClinicalFlag.CHRONIC_KIDNEY_DISEASE}),
        frozenset({ClinicalFlag.DIABETES}),
    )
    for weight in (45.0, 55.0, 70.0, 85.0, 95.0, 110.0):
        for goal in (Goal.LOSE_FAT, Goal.MAINTAIN, Goal.GAIN_MUSCLE):
            for diet in diets:
                for flags in flag_sets:
                    yield Profile(
                        weight_kg=weight, height_cm=175.0, age_years=28,
                        sex=Sex.MALE, activity=ActivityLevel.MODERATE, goal=goal,
                        diet=diet, clinical_flags=flags,
                    )


class _swap_constant:
    """Temporarily replace a registered constant's value; restore on exit.

    Same pattern already used across the suite for exactly this purpose --
    see module docstring. A context manager here only so a raised exception
    mid-sweep cannot leave the registry mutated for whatever runs next in the
    same process.
    """

    def __init__(self, key: str, value: float) -> None:
        self.key = key
        self.value = value
        self.original = None

    def __enter__(self):
        self.original = citations._CONSTANTS[self.key]
        citations._CONSTANTS[self.key] = dataclasses.replace(
            self.original, value=self.value
        )
        return self

    def __exit__(self, *exc) -> None:
        citations._CONSTANTS[self.key] = self.original


def _combinations_for(profile: Profile, region: Region, slot: MealSlot):
    pool = build_candidate_pool(
        lib.components(), lib.ingredients,
        template=template_for(region, slot),
        diet_pattern=profile.diet, dev_mode=True,
    )
    return enumerate_combinations(pool)


def accepted_rung_valid_plate_count(profile: Profile, region: Region, slot: MealSlot) -> int:
    """Same measurement as probe_rank_input2.py's primary metric, standalone
    here so a threshold swap (scenario 3) can be observed without touching
    that file. Real pipeline, real quality gate, whatever
    `protein.quality_diaas_threshold` currently reads as."""

    combinations = _combinations_for(profile, region, slot)
    if not combinations:
        return 0
    day_target = derive_target(profile).nutrition_target
    single_meal_target = meal_target(day_target, slot, ledger=None)
    outcome = plan_within_ladder(
        combinations, single_meal_target, lib.ingredients, profile=profile
    )
    if outcome.plan is None:
        return 0
    solved = solve(
        feasible_combinations(combinations, outcome.target_used, lib.ingredients),
        outcome.target_used,
        lib.ingredients,
    )
    return len(solved)


def _quality_free_plan(profile: Profile, region: Region, slot: MealSlot):
    """The real ladder's winning plate with the per-meal quality floor
    stripped from the target it is walked against -- see module docstring,
    scenario 2. `None` if even the macro-only target is infeasible."""

    combinations = _combinations_for(profile, region, slot)
    if not combinations:
        return None
    day_target = derive_target(profile).nutrition_target
    single_meal_target = meal_target(day_target, slot, ledger=None)
    quality_free_target = dataclasses.replace(
        single_meal_target, quality_protein_floor_g=None
    )
    outcome = plan_within_ladder(
        combinations, quality_free_target, lib.ingredients, profile=profile
    )
    return outcome.plan


def _report_per_template(label: str, per_template: dict, total_cases: int, total_pass: int) -> None:
    overall = total_pass / total_cases
    print(f"-- {label} --")
    print(f"overall: {total_pass}/{total_cases} = {overall:.1%} offer "
          f">= {MIN_VALID_PLATES} valid plates")
    for region, slot in TEMPLATES:
        results = per_template[(region, slot)]
        frac = sum(results) / len(results)
        print(f"  {region.value:12s}/{slot.value:10s}: {sum(results):3d}/{len(results):3d} "
              f"= {frac:.1%}")
    print()


def scenario_1_and_3(label: str) -> None:
    per_template: dict = {t: [] for t in TEMPLATES}
    total_cases = 0
    total_pass = 0
    for profile in profiles():
        for region, slot in TEMPLATES:
            total_cases += 1
            count = accepted_rung_valid_plate_count(profile, region, slot)
            passed = count >= MIN_VALID_PLATES
            per_template[(region, slot)].append(passed)
            if passed:
                total_pass += 1
    _report_per_template(label, per_template, total_cases, total_pass)


def scenario_2() -> None:
    print("-- per-day floor (scenario 2) --")
    print("LOWER BOUND, not a best-case day-aware allocator -- see module docstring.")
    print()

    # Reused across both the "today's rule, day-level" and "per-day rule"
    # tallies below, so each (profile, template) plan is only solved twice
    # total (once quality-gated for real, once quality-free) rather than
    # four times.
    quality_gated_plan: dict = {}
    quality_free_plan: dict = {}
    for profile in profiles():
        for region, slot in TEMPLATES:
            key = (profile, region, slot)
            combinations = _combinations_for(profile, region, slot)
            if not combinations:
                quality_gated_plan[key] = None
                quality_free_plan[key] = None
                continue
            day_target = derive_target(profile).nutrition_target
            single_meal_target = meal_target(day_target, slot, ledger=None)
            gated = plan_within_ladder(
                combinations, single_meal_target, lib.ingredients, profile=profile
            )
            quality_gated_plan[key] = gated.plan
            free_target = dataclasses.replace(
                single_meal_target, quality_protein_floor_g=None
            )
            free = plan_within_ladder(
                combinations, free_target, lib.ingredients, profile=profile
            )
            quality_free_plan[key] = free.plan

    for day_label, day_templates in DAY_VARIANTS:
        today_unplannable = 0
        today_pass = 0
        today_total = 0
        per_day_unplannable = 0
        per_day_pass = 0
        per_day_total = 0

        for profile in profiles():
            day_target_obj = derive_target(profile)
            day_floor = day_target_obj.protein.quality_source_day_g

            gated_plans = [
                quality_gated_plan[(profile, region, slot)]
                for region, slot in day_templates
            ]
            today_total += 1
            if any(p is None for p in gated_plans):
                today_unplannable += 1
            else:
                today_pass += 1  # every slot individually cleared its own floor

            free_plans = [
                quality_free_plan[(profile, region, slot)]
                for region, slot in day_templates
            ]
            per_day_total += 1
            if any(p is None for p in free_plans):
                per_day_unplannable += 1
                continue
            day_quality_g = sum(p.quality_protein_g for p in free_plans)
            if day_quality_g >= day_floor:
                per_day_pass += 1

        print(f"  {day_label}:")
        print(f"    today's rule (all 3 meals individually clear the flat per-meal "
              f"floor):")
        print(f"      pass {today_pass}/{today_total} = {today_pass/today_total:.1%} "
              f"(unplannable regardless of quality: {today_unplannable})")
        print(f"    per-day rule (macro-best plates, summed quality >= day floor "
              f"{day_floor:.1f}g by profile, reported as overall pass rate):")
        print(f"      pass {per_day_pass}/{per_day_total} = "
              f"{per_day_pass/per_day_total:.1%} "
              f"(unplannable regardless of quality: {per_day_unplannable})")
    print()


def main() -> None:
    print("=" * 100)
    print("SCENARIO 1 -- today's rule, unchanged (threshold 0.75, per-meal flat floor)")
    scenario_1_and_3("threshold 0.75 (today)")

    print("=" * 100)
    print("SCENARIO 2 -- per-day rather than per-meal floor")
    scenario_2()

    print("=" * 100)
    print("SCENARIO 3 -- threshold sensitivity (sensitivity information only, per "
          "TASKS_3.md's Don't clause -- NOT a recommendation)")
    for threshold in (0.65, 0.70):
        with _swap_constant("protein.quality_diaas_threshold", threshold):
            scenario_1_and_3(f"threshold {threshold}")


if __name__ == "__main__":
    main()
