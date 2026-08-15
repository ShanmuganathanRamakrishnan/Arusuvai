"""The per-bound diagnostic behind R2 and R4's prioritisation.

Formalised into the repo 2026-08-15, R1c, same reasoning as
`probe_rank_input2.py`'s module docstring: this replaces a script that
existed only as a number in `TASKS_3.md`.

Rebuilt 2026-08-15, same day, before R2 started, for the same reason
`probe_rank_input2.py` was rebuilt: the first committed version of this
file tallied "sole cause" against every profile's **unrelaxed** target only
-- rung 0, ladder not walked. That over-counts every bound the ladder is
designed to relax away. `sodium_mg_ceiling`, `fat_g_ceiling`,
`protein_g_floor`, `fat_g_floor`, `carb_g_ceiling` and `protein_g_ceiling`
are all touched by a rung in `core.planner.validator.RELAXATION_ORDER`;
counting a combination against one of those as "blocked" when a later rung
in the same run would in fact widen it past the block answers a question
nobody asked -- "what fails before any relaxation is even attempted",
not "what genuinely blocks a profile after the ladder has done everything
it is willing to do". Only `quality_protein_floor` is never relaxed
(`core.planner.validator._relax_protein`'s docstring), so it was the one
bound in the old table whose count was not inflated by this defect, and it
was already the largest by a wide margin.

## Two numbers, not one -- same shape as `probe_rank_input2.py`

- **`accepted_rung_broken_bounds`** -- for each (profile, template), the
  target actually used is whichever one `plan_within_ladder` stopped on:
  the unrelaxed target if rung 0 sufficed, the widened target of whichever
  rung succeeded, or -- if every rung fired and the profile still declines
  -- the fully-widened target after all four rungs, which is exactly what
  `core.planner.validator._blocking_violations` names a decline against.
  Every enumerated combination for that (profile, template) is then
  independently re-checked against that one target. This is the number
  that answers "which bound genuinely dominates once the ladder has done
  what it can" and is what R2 and R4's prioritisation should be keyed to.
- **`rung0_broken_bounds`** -- kept, renamed and demoted, matching
  `probe_rank_input2.py`'s secondary metric. Every bound blocked against
  the **unrelaxed** target only, ladder not walked. Not what R2/R4 should
  prioritise against, but still informative for R4: a bound that dominates
  at rung 0 but drops out of the accepted-rung table is one the ladder is
  already quietly absorbing, which is a weaker case for a new recipe than
  a bound that dominates at both.

## Re-baseline note (2026-08-15)

Neither this file's first run (quality_protein_floor 1160 / fat_g_ceiling
316 / sodium_mg_ceiling 92) nor TASKS_3.md's cited historical figures
(591 / 223 / 19) are the accepted-rung number below. The historical figures
were never reproduced by any grid this file tried (see the R1c commit
message, `a8d6973`, for the narrower-grid attempt) and remain unexplained;
they are superseded here, not because they were matched, but because the
methodology producing them is unknown and the corrected, ladder-aware
methodology is the one going forward. R2 should treat the accepted-rung
table below as authoritative.

## What "sole cause" means

For every enumerated `MealCombination`, independently recompute **every**
bound (each macro's floor/ceiling, plus the quality-protein floor) against
the target in question, rather than stopping at the first one that fails --
deliberately not calling `feasible_combinations` for the per-bound
breakdown, since its `ok = False; break` short-circuits at the first
failing bound and would misattribute a combination broken by two bounds to
whichever happens to be checked first. A combination is charged to a bound
only when that bound is the **only** one it fails; a combination failing
two or more bounds at once is counted separately, under "multiple causes",
and attributed to none of them individually -- charging it to whichever
bound the loop reaches first would inflate that bound's count with
failures it did not uniquely cause.

## The profile grid

Same 144-profile grid as `probe_rank_input2.py` and `d4_declines.py` -- see
either's docstring for why. Clinical flags are kept in the grid: a flag can
lock a rung out of the ladder entirely, which changes how far a profile's
accepted-rung target can widen before this probe evaluates it.

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
from core.planner.validator import plan_within_ladder
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


def _tally(combinations, target, ingredients, sole_cause: dict, counters: dict) -> None:
    for combo in combinations:
        broken = broken_bounds(combo, target, ingredients)
        counters["total"] += 1
        if not broken:
            continue
        counters["failing"] += 1
        if len(broken) == 1:
            sole_cause[broken[0]] = sole_cause.get(broken[0], 0) + 1
        else:
            counters["multiple"] += 1


def _accepted_rung_target(profile: Profile, region: Region, slot: MealSlot, combinations):
    """The target `plan_within_ladder` actually used or ended on.

    Mirrors `probe_rank_input2.accepted_rung_valid_plate_count`: rung 0's
    target if that sufficed, otherwise the winning rung's widened target,
    otherwise (decline) the fully-walked target `_blocking_violations`
    itself would be measured against.
    """

    day_target = derive_target(profile).nutrition_target
    single_meal_target = meal_target(day_target, slot, ledger=None)
    outcome = plan_within_ladder(
        combinations, single_meal_target, lib.ingredients, profile=profile
    )
    return outcome.target_used


def _report(label: str, sole_cause: dict, counters: dict) -> None:
    print(f"-- {label} --")
    print(f"{counters['total']} combinations checked across {len(TEMPLATES)} "
          f"templates x 144 profiles")
    print(f"{counters['failing']} fail at least one bound "
          f"({counters['multiple']} of those on 2+ bounds simultaneously, "
          f"attributed to none)")
    print("sole-cause counts, most first:")
    for bound, count in sorted(sole_cause.items(), key=lambda kv: -kv[1]):
        print(f"  {bound:24s}: {count}")
    if not sole_cause:
        print("  (none -- no combination in the grid fails exactly one bound)")
    print()


def main() -> None:
    accepted_sole: dict[str, int] = {}
    accepted_counters = {"total": 0, "failing": 0, "multiple": 0}
    rung0_sole: dict[str, int] = {}
    rung0_counters = {"total": 0, "failing": 0, "multiple": 0}

    for profile in profiles():
        day_target = derive_target(profile).nutrition_target
        for region, slot in TEMPLATES:
            pool = build_candidate_pool(
                lib.components(), lib.ingredients,
                template=template_for(region, slot),
                diet_pattern=profile.diet, dev_mode=True,
            )
            combinations = enumerate_combinations(pool)
            if not combinations:
                continue

            single_meal_target = meal_target(day_target, slot, ledger=None)
            _tally(combinations, single_meal_target, lib.ingredients, rung0_sole, rung0_counters)

            accepted_target = _accepted_rung_target(profile, region, slot, combinations)
            _tally(combinations, accepted_target, lib.ingredients, accepted_sole, accepted_counters)

    print("=" * 100)
    print("PRIMARY -- bound priority at the accepted rung, effective 2026-08-15")
    print("(walks the ladder via plan_within_ladder; this is what R2 and R4 should")
    print("prioritise against):")
    _report("accepted-rung bound priority", accepted_sole, accepted_counters)

    print("SECONDARY -- bound priority with NO relaxation walked (rung 0 only;")
    print("informative for R4, not the number to prioritise against):")
    _report("rung-0-only bound priority", rung0_sole, rung0_counters)


if __name__ == "__main__":
    main()
