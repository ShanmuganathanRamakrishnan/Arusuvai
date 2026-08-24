"""Phase R's exit-condition tool. Source of the figures TASKS_3.md cites for
R1's phase-exit gate, and re-run after R2, R4 and R5 to track it.

Formalised into the repo 2026-08-15, R1c. Rebuilt 2026-08-15, same day,
**before R2 started**: the first committed version (`a8d6973`) counted a
combination as a valid plate only if it solved against the profile's
**unrelaxed** target -- rung 0 of the ladder, no relaxation walked. That is
not what "a valid plate" means anywhere else in this codebase.
`core.planner.validator.plan_within_ladder` is what actually decides whether
a profile gets a plan: it solves against the unrelaxed target first and, if
that is empty, walks `RELAXATION_ORDER` rung by rung, silently for the first
three steps and with mandatory disclosure for the fourth (protein), stopping
at the first rung that yields anything. A rung-0-only probe was measuring a
stricter, easier-to-fail question than the one the product actually asks,
and its 21.5%/22% number was never the right one to hold the 50%/30% exit
thresholds against. This file now walks the ladder the same way
`plan_within_ladder` does -- imports and calls it directly, rather than
reimplementing its rung order and locked-macro handling -- and reports the
count of combinations that solve at whichever rung the ladder actually
accepts.

## Two numbers, not one

- **`accepted_rung_valid_plate_count`** -- the number the phase exit
  condition is measured against, effective 2026-08-15. How many distinct
  combinations solve at the rung `plan_within_ladder` stops on for this
  (profile, template): rung 0 if nothing needed relaxing, otherwise the
  first relaxed rung that worked. Zero if the ladder is exhausted and the
  profile declines. This is "how much choice does the ranking step
  actually get", which is what the exit condition was always meant to ask.
- **`rung0_valid_plate_count`** -- kept, renamed and demoted. This is what
  the original (and this file's first committed version) measured: choice
  available with **no** relaxation walked at all. It is not the exit-
  condition number and must not be read as one. It remains a legitimate,
  separate thing to track: R4's recipe prioritisation cares about how rich
  the library is *before* any tolerance is given up, since a profile that
  only ever clears via a relaxed rung is telling a different story (the
  ladder is doing the work) than one with rich rung-0 choice (the library
  is doing the work). Reported as "library richness, relaxation-independent"
  below, never folded into the pass/fail line.

## Re-baseline note (2026-08-15)

The 22% baseline TASKS_3.md cited (HEAD 2026-08-13) and this file's own first
run (21.5%) are both **rung-0-only** numbers under the corrected vocabulary
above -- superseded as the exit-condition figure, not wrong as a measurement
of what they measured. The accepted-rung number reported by this run is the
new, final baseline the 50%/30% thresholds are held against going forward.
Why it moves rather than the thresholds: the thresholds describe how much
choice a user should get; measuring rung-0 alone was undercounting that
choice for every case the ladder resolves via silent relaxation, which is
by design not supposed to read as "no choice" to the person using the
product.

## What "a valid plate" means here

At the accepted rung: a distinct `MealCombination` (one assignment of
components to every template slot) for which `core.planner.solver.solve`
finds at least one legal integer unit-count assignment against the target
`plan_within_ladder` actually solved against for this (profile, template) --
the unrelaxed target if rung 0 sufficed, otherwise the target as widened by
whichever rung `plan_within_ladder` stopped on. At rung 0 specifically
(the secondary metric): the same, but always against the unrelaxed target,
ladder not walked.

## The profile grid

Reuses the shape `d4_declines.py`'s `profiles()` established (6 weights x 3
goals x {VEGETARIAN, VEGAN} x 4 clinical-flag sets = 144 profiles), for the
same reason stated there: it straddles the passing reference profile on
every axis that can move a target's reachability. Diet is included even
though the shipped product is vegetarian-only (`docs/methodology.md`) because
VEGAN is the axis that makes the quality-protein floor structurally hardest
to reach, which is exactly the sensitivity this exit condition needs to see
-- restricting to VEGETARIAN alone would only measure the easy half of the
grid and over-report the true rankability. Clinical flags are kept in the
grid for the same reason: a flag can lock a rung out of the ladder entirely
(`core.planner.validator.LOCKED_CONSTRAINTS`), which changes how far the
ladder can walk, not just what target it starts from.

144 profiles x 5 templates = 720 (profile, template) cases. SOUTH_DINNER
joined 2026-08-24 (TASKS_3.md R4d) -- the count and every per-template line
below derive from ``TEMPLATES`` and ``len(TEMPLATES)`` rather than being
hardcoded, so this docstring is the only place the arithmetic needed
updating.

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
from core.planner.validator import plan_within_ladder
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
    (Region.SOUTH_INDIAN, MealSlot.DINNER),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)

lib = load_library()
# 720 cells' worth of "N recipe(s) kept past their eligibility ceiling" and
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


def _combinations_for(profile: Profile, region: Region, slot: MealSlot):
    pool = build_candidate_pool(
        lib.components(), lib.ingredients,
        template=template_for(region, slot),
        diet_pattern=profile.diet, dev_mode=True,
    )
    return enumerate_combinations(pool)


def accepted_rung_valid_plate_count(
    profile: Profile, region: Region, slot: MealSlot
) -> tuple[int, str]:
    """(count, rung label) at whichever rung `plan_within_ladder` accepts.

    THE exit-condition number, effective 2026-08-15. Walks the ladder via
    `plan_within_ladder` itself -- not a reimplementation of
    `RELAXATION_ORDER` or `locked_macros` -- then recomputes the full solved
    set at `outcome.target_used` the same way `plan_within_ladder` did
    internally to find its own winning plan, so the count and the plan it
    is counted alongside are guaranteed to agree on what target they were
    solved against.
    """

    combinations = _combinations_for(profile, region, slot)
    if not combinations:
        return 0, "empty_pool"
    day_target = derive_target(profile).nutrition_target
    single_meal_target = meal_target(day_target, slot, ledger=None)
    outcome = plan_within_ladder(
        combinations, single_meal_target, lib.ingredients, profile=profile
    )
    if outcome.plan is None:
        return 0, "declined"
    solved = solve(
        feasible_combinations(combinations, outcome.target_used, lib.ingredients),
        outcome.target_used,
        lib.ingredients,
    )
    applied = outcome.result.relaxation_applied
    rung = applied[-1] if applied else "rung_0"
    return len(solved), rung


def rung0_valid_plate_count(profile: Profile, region: Region, slot: MealSlot) -> int:
    """Choice available with NO relaxation walked. Secondary metric only --
    see module docstring. Not the exit-condition number."""

    combinations = _combinations_for(profile, region, slot)
    if not combinations:
        return 0
    day_target = derive_target(profile).nutrition_target
    single_meal_target = meal_target(day_target, slot, ledger=None)
    survivors = feasible_combinations(combinations, single_meal_target, lib.ingredients)
    count = 0
    for combo in survivors:
        if solve((combo,), single_meal_target, lib.ingredients):
            count += 1
    return count


def _report(label: str, per_template: dict, total_cases: int, total_pass: int) -> bool:
    overall_fraction = total_pass / total_cases
    print(f"-- {label} --")
    print(f"overall: {total_pass}/{total_cases} = {overall_fraction:.1%} offer "
          f">= {MIN_VALID_PLATES} valid plates "
          f"(exit condition: >= {PASS_FRACTION:.0%})")
    worst = None
    for region, slot in TEMPLATES:
        results = per_template[(region, slot)]
        frac = sum(results) / len(results)
        flag = "" if frac >= PER_TEMPLATE_FLOOR else "  <-- BELOW FLOOR"
        print(f"  {region.value:12s}/{slot.value:10s}: {sum(results):3d}/{len(results):3d} "
              f"= {frac:.1%}{flag}")
        if worst is None or frac < worst:
            worst = frac
    exit_met = overall_fraction >= PASS_FRACTION and worst >= PER_TEMPLATE_FLOOR
    print(f"  exit condition met: {exit_met}")
    print()
    return exit_met


def main() -> None:
    accepted_per_template: dict = {t: [] for t in TEMPLATES}
    rung0_per_template: dict = {t: [] for t in TEMPLATES}
    rung_labels: dict[str, int] = {}
    total_cases = 0
    accepted_pass = 0
    rung0_pass = 0

    for profile in profiles():
        for region, slot in TEMPLATES:
            total_cases += 1

            count, rung = accepted_rung_valid_plate_count(profile, region, slot)
            rung_labels[rung] = rung_labels.get(rung, 0) + 1
            passed = count >= MIN_VALID_PLATES
            accepted_per_template[(region, slot)].append(passed)
            if passed:
                accepted_pass += 1

            r0_count = rung0_valid_plate_count(profile, region, slot)
            r0_passed = r0_count >= MIN_VALID_PLATES
            rung0_per_template[(region, slot)].append(r0_passed)
            if r0_passed:
                rung0_pass += 1

    print("=" * 100)
    print(f"{total_cases} (profile, template) cases, {len(TEMPLATES)} templates x "
          f"{total_cases // len(TEMPLATES)} profiles")
    print()
    print("PRIMARY -- exit-condition number, effective 2026-08-15 (walks the ladder,")
    print("same logic as plan_within_ladder):")
    _report("accepted-rung rankability", accepted_per_template, total_cases, accepted_pass)

    print(f"Rung distribution across all {total_cases} cases (where the ladder stopped, "
          "including declines):")
    for rung, n in sorted(rung_labels.items(), key=lambda kv: -kv[1]):
        print(f"  {rung:24s}: {n}")
    print()

    print("SECONDARY -- library richness, relaxation-independent (NOT the exit")
    print("condition; tracked for R4 recipe prioritisation only):")
    _report("rung-0-only rankability", rung0_per_template, total_cases, rung0_pass)


if __name__ == "__main__":
    main()
