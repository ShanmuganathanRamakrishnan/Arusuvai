"""Phase R's exit-condition tool. Source of the 22%/50%/30% figures TASKS_3.md
cites for R1's phase-exit gate, and re-run after R2, R4 and R5 to track it.

Formalised into the repo 2026-08-15, R1c. Before this, the 22% baseline
(HEAD 2026-08-13) existed only as a number in `TASKS_3.md`, produced by a
script that was never committed -- the same "a rule requiring pasted
evidence, satisfied by a script nobody could run" shape as
`docs/audit_log.md` finding 11, which is this directory's own reason to
exist (see `README.md`). This file is the fix for that gap, not a
byte-for-byte reproduction of whatever produced the original number: nobody
has the original script to diff against, so the 22% this version reports on
an unchanged library is corroboration, not proof of exact methodology
match, and is treated that way in this file's own commit message.

## What "a valid plate" means here

A distinct `MealCombination` (one assignment of components to every
template slot) for which `core.planner.solver.solve` finds at least one
legal integer unit-count assignment against the profile's **unrelaxed**
per-meal `NutritionTarget` -- no relaxation ladder walked. This is
deliberately the ladder's rung-0 gate and nothing looser: a "rank input" is
what a later ranking step (human, LLM, or otherwise) would choose among
*before* any bound has been loosened on the user's behalf, since relaxed
candidates carry a disclosure a plain candidate count would hide.

## The profile grid

Reuses the shape `d4_declines.py`'s `profiles()` established (6 weights x 3
goals x {VEGETARIAN, VEGAN} x 4 clinical-flag sets = 144 profiles), for the
same reason stated there: it straddles the passing reference profile on
every axis that can move a target's reachability. Diet is included even
though the shipped product is vegetarian-only (`docs/methodology.md`) because
VEGAN is the axis that makes the quality-protein floor structurally hardest
to reach, which is exactly the sensitivity this exit condition needs to see
-- restricting to VEGETARIAN alone would only measure the easy half of the
grid and over-report the true rankability.

144 profiles x 4 templates = 576 (profile, template) cases.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/probe_rank_input2.py
"""
from __future__ import annotations

import logging

from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations, feasible_combinations
from core.planner.plan import load_library
from core.planner.solver import solve
from core.schemas import (
    ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

#: >= this many valid plates is "offering choice" for the exit condition.
MIN_VALID_PLATES = 2

#: This fraction of (profile, template) cases must clear MIN_VALID_PLATES.
PASS_FRACTION = 0.50

#: No single template's own fraction may fall below this.
PER_TEMPLATE_FLOOR = 0.30

TEMPLATES = (
    (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
    (Region.SOUTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)

lib = load_library()
# 576 cells' worth of "N recipe(s) kept past their eligibility ceiling" and
# combination-count logging would drown the table below; the numbers this
# probe reports do not come from the log.
logging.disable(logging.WARNING)


def profiles():
    """144 profiles: 6 weights x 3 goals x 2 diets x 4 flag-sets.

    Same grid `d4_declines.py` uses, for the same reason -- see this file's
    module docstring.
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


def valid_plate_count(profile: Profile, region: Region, slot: MealSlot) -> int:
    """How many distinct combinations solve against the UNRELAXED per-meal
    target -- no relaxation ladder walked. See module docstring."""

    day_target = derive_target(profile).nutrition_target
    single_meal_target = meal_target(day_target, slot, ledger=None)
    pool = build_candidate_pool(
        lib.components(), lib.ingredients,
        template=template_for(region, slot),
        diet_pattern=profile.diet, dev_mode=True,
    )
    combinations = enumerate_combinations(pool)
    if not combinations:
        return 0
    survivors = feasible_combinations(combinations, single_meal_target, lib.ingredients)
    count = 0
    for combo in survivors:
        if solve((combo,), single_meal_target, lib.ingredients):
            count += 1
    return count


def main() -> None:
    per_template: dict[tuple[Region, MealSlot], list[bool]] = {
        t: [] for t in TEMPLATES
    }
    total_cases = 0
    total_pass = 0

    for profile in profiles():
        for region, slot in TEMPLATES:
            total_cases += 1
            count = valid_plate_count(profile, region, slot)
            passed = count >= MIN_VALID_PLATES
            per_template[(region, slot)].append(passed)
            if passed:
                total_pass += 1

    overall_fraction = total_pass / total_cases
    print("=" * 100)
    print(f"{total_cases} (profile, template) cases, {len(TEMPLATES)} templates x "
          f"{total_cases // len(TEMPLATES)} profiles")
    print(f"overall: {total_pass}/{total_cases} = {overall_fraction:.1%} offer "
          f">= {MIN_VALID_PLATES} valid plates "
          f"(exit condition: >= {PASS_FRACTION:.0%})")
    print()
    worst = None
    for region, slot in TEMPLATES:
        results = per_template[(region, slot)]
        frac = sum(results) / len(results)
        flag = "" if frac >= PER_TEMPLATE_FLOOR else "  <-- BELOW FLOOR"
        print(f"  {region.value:12s}/{slot.value:10s}: {sum(results):3d}/{len(results):3d} "
              f"= {frac:.1%}{flag}")
        if worst is None or frac < worst:
            worst = frac
    print()
    exit_met = overall_fraction >= PASS_FRACTION and worst >= PER_TEMPLATE_FLOOR
    print(f"phase exit condition met: {exit_met}")


if __name__ == "__main__":
    main()
