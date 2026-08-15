"""The per-bound diagnostic behind R2 and R4's prioritisation. Source of the
figures R2's text cites ("quality-protein floor is the sole cause of 591
combination failures ... fat_g ceiling is second at 223; sodium_mg is 19").

Formalised into the repo 2026-08-15, R1c, same reasoning as
`probe_rank_input2.py`'s module docstring: this replaces a script that
existed only as a number in `TASKS_3.md`. Re-running this version on an
unchanged library is corroboration of the historical figures, not proof of
an identical methodology -- there is nothing to diff the original script
against.

**That corroboration did not hold for this probe.** `probe_rank_input2.py`
reproduced its cited baseline closely (21.5% against a stated 22%) on the
first run with the 144-profile grid below. This one does not: against the
same grid it reports quality-protein floor as sole cause 1160 times,
fat_g_ceiling 316, and sodium_mg_ceiling 92 (plus four bound types R2's
text never mentions at all) -- not 591 / 223 / 19. A narrower grid
(vegetarian only, no clinical flags, 18 profiles) gives 195 / 77 / 23,
closer in *ratio* but still off by roughly 3x in scale, and still surfaces
bounds R2's text is silent on. Neither grid reproduces the cited figures,
and no grid search was exhaustive enough to rule out that the original
script measured something structurally different (a different pre-filter
ordering, a different definition of "sole cause", or a profile axis this
reconstruction does not vary). This is stated here rather than tuned away:
R2, which actually consumes this probe's output, should treat the numbers
this file reports as the authoritative, freshly-measured figures and treat
591/223/19 as superseded pending that task's own investigation -- not as a
target this probe should be adjusted to hit.

## What "sole cause" means

For every `MealCombination` the O(1) feasibility pre-filter
(`core.planner.combinations.feasible_combinations`) discards, this probe
independently recomputes **every** bound (each macro's floor/ceiling, plus
the quality-protein floor) rather than stopping at the first one that fails
-- deliberately not calling `feasible_combinations` itself for the
per-bound breakdown, since its `ok = False; break` short-circuits at the
first failing bound and would misattribute a combination broken by two
bounds to whichever happens to be checked first. A combination is charged
to a bound only when that bound is the **only** one it fails; a combination
failing two or more bounds at once is counted separately, under "multiple
causes", and attributed to none of them individually -- charging it to
whichever bound the loop reaches first would inflate that bound's count
with failures it did not uniquely cause.

## The profile grid

Same 144-profile grid as `probe_rank_input2.py` and `d4_declines.py` --see
either's docstring for why.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/probe_blocking_bounds.py
"""
from __future__ import annotations

import logging

from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import (
    enumerate_combinations,
    macro_bounds,
    quality_protein_bounds,
)
from core.planner.plan import load_library
from core.schemas import (
    ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

TEMPLATES = (
    (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
    (Region.SOUTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)

#: Bound label used as both the quality-floor's key and the printed name.
QUALITY_LABEL = "quality_protein_floor"

lib = load_library()
logging.disable(logging.WARNING)


def profiles():
    """144 profiles: 6 weights x 3 goals x 2 diets x 4 flag-sets.

    Identical to `probe_rank_input2.py`'s grid -- see its docstring.
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


def broken_bounds(combo, target, ingredients) -> list[str]:
    """Every bound this combination's declared min/max range cannot satisfy.

    Independent of `feasible_combinations`: checks every bound rather than
    stopping at the first failure. See module docstring, "sole cause".
    """

    broken = []
    for macro in target.bounded_macros():
        total_low = total_high = 0.0
        for component in combo.components:
            low, high = macro_bounds(component, macro, ingredients)
            total_low += low
            total_high += high
        floor = target.floor(macro)
        ceiling = target.ceiling(macro)
        if floor is not None and total_high < floor:
            broken.append(f"{macro}_floor")
        if ceiling is not None and total_low > ceiling:
            broken.append(f"{macro}_ceiling")
    quality_floor = target.quality_protein_floor()
    if quality_floor is not None:
        reachable = sum(
            quality_protein_bounds(component, ingredients)[1]
            for component in combo.components
        )
        if reachable < quality_floor:
            broken.append(QUALITY_LABEL)
    return broken


def main() -> None:
    sole_cause: dict[str, int] = {}
    multiple_causes = 0
    total_failing = 0
    total_combinations = 0

    for profile in profiles():
        day_target = derive_target(profile).nutrition_target
        for region, slot in TEMPLATES:
            single_meal_target = meal_target(day_target, slot, ledger=None)
            pool = build_candidate_pool(
                lib.components(), lib.ingredients,
                template=template_for(region, slot),
                diet_pattern=profile.diet, dev_mode=True,
            )
            combinations = enumerate_combinations(pool)
            total_combinations += len(combinations)
            for combo in combinations:
                broken = broken_bounds(combo, single_meal_target, lib.ingredients)
                if not broken:
                    continue
                total_failing += 1
                if len(broken) == 1:
                    sole_cause[broken[0]] = sole_cause.get(broken[0], 0) + 1
                else:
                    multiple_causes += 1

    print("=" * 100)
    print(f"{total_combinations} combinations enumerated across {len(TEMPLATES)} "
          f"templates x 144 profiles")
    print(f"{total_failing} fail the O(1) feasibility pre-filter on at least one bound "
          f"({multiple_causes} of those on 2+ bounds simultaneously, attributed to none)")
    print()
    print("sole-cause counts, most first:")
    for bound, count in sorted(sole_cause.items(), key=lambda kv: -kv[1]):
        print(f"  {bound:24s}: {count}")
    if not sole_cause:
        print("  (none -- no combination in the grid fails exactly one bound)")


if __name__ == "__main__":
    main()
