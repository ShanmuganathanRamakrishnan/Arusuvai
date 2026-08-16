"""TASKS_3.md R5 -- timing baseline. Run BEFORE any recipe is added.

Measure only. No optimisation, no threshold decided here -- this file reports
numbers and proposes a wall-clock budget for Adi to confirm or reject.

## Why this runs now, not after R3a

`enumerate_combinations` is a product across every template slot's candidate
list, and `core.planner.solver.solve` runs an exhaustive integer search over
every surviving combination (`core/planner/combinations.py`,
`core/planner/solver.py`). Nobody has measured where this gets slow. R3a is
about to add the first new ingredient (egg) and its recipes since this whole
measurement chain was built -- the exact moment a "before" number stops being
obtainable. `north_indian/lunch` was already known (D-series work) to be the
largest template by enumerated count; this file re-measures it and the other
three at today's exact library size, not from memory.

## What is measured, and why this shape

Two numbers per (template, diet_pattern, profile-shape) cell:

- **Enumerated combination count** -- `len(enumerate_combinations(pool))`,
  the size of the product `plan_meal` (via `plan_within_ladder`) has to search.
  Independent of any one profile's target; depends only on template + diet
  pattern (which ingredient classes are admitted into the pool).
- **Wall-clock `plan_meal` time** -- the actual thing that sits behind
  `POST /api/plan` (`api/main.py` calls `plan_meal` exactly once per request,
  confirmed by reading `api/main.py`). Measured with `time.perf_counter`,
  median of 5 repeated calls per cell to damp OS/GC noise, min and max also
  reported so a one-off outlier is visible rather than averaged away.

Diet patterns are varied (not just VEGETARIAN) because `build_candidate_pool`
filters on permitted ingredient classes per `DietPattern`
(`core/foods/diet.py`, R1a) -- a wider-admitting pattern
(`NON_VEGETARIAN`) can only enumerate *more* combinations than a narrower one
for the same template, so it is the pattern most likely to show the worst
case, and VEGAN/VEGETARIAN are kept alongside it because they are what the
product actually ships (`docs/methodology.md`: vegetarian-only framing).

Two profile shapes are measured per (template, diet_pattern) cell, not the
full 144-profile grid used elsewhere -- R5 asks "where does this get slow",
not "how rankable is this", so the grid's dietary/clinical axes are already
covered by the diet_pattern sweep above and the profile axis only needs to
bracket the ladder's own worst case:

- **reference** -- a mid-range profile (70kg, MODERATE, MAINTAIN, no
  clinical flags) that is expected to accept at rung 0 or an early rung, so
  `plan_within_ladder` calls `solve` on the feasible set once or twice.
- **worst_case** -- an extreme-weight, clinically-flagged profile
  (110kg, GAIN_MUSCLE, HYPERTENSION+CHRONIC_KIDNEY_DISEASE) chosen to make
  the ladder walk every unlocked rung before declining (or, if it does not
  decline, to still force the maximum possible number of `solve` calls) --
  this is the shape that matters for a request-path wall-clock budget, since
  the reference profile alone would systematically under-measure it.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/r5_timing_baseline.py
"""
from __future__ import annotations

import logging
import statistics
import time

from core.foods.templates import template_for
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations
from core.planner.plan import load_library, plan_meal
from core.schemas import (
    ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

TEMPLATES = (
    (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
    (Region.SOUTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)

DIET_PATTERNS = (
    DietPattern.VEGETARIAN,
    DietPattern.VEGAN,
    DietPattern.NON_VEGETARIAN,
)

REPEATS = 5

lib = load_library()
# Combination-count / eligibility-ceiling logging would drown the timing
# table and is not what this probe reports.
logging.disable(logging.WARNING)


def _profile(diet: DietPattern, *, worst_case: bool) -> Profile:
    if worst_case:
        return Profile(
            weight_kg=110.0, height_cm=175.0, age_years=28, sex=Sex.MALE,
            activity=ActivityLevel.MODERATE, goal=Goal.GAIN_MUSCLE, diet=diet,
            clinical_flags=frozenset(
                {ClinicalFlag.HYPERTENSION, ClinicalFlag.CHRONIC_KIDNEY_DISEASE}
            ),
        )
    return Profile(
        weight_kg=70.0, height_cm=175.0, age_years=28, sex=Sex.MALE,
        activity=ActivityLevel.MODERATE, goal=Goal.MAINTAIN, diet=diet,
        clinical_flags=frozenset(),
    )


def _combination_count(region: Region, slot: MealSlot, diet: DietPattern) -> int:
    pool = build_candidate_pool(
        lib.components(), lib.ingredients,
        template=template_for(region, slot),
        diet_pattern=diet, dev_mode=True,
    )
    return len(enumerate_combinations(pool))


def _time_plan_meal(profile: Profile, region: Region, slot: MealSlot) -> list[float]:
    day_target = derive_target(profile).nutrition_target
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        plan_meal(
            lib, day_target, region=region, meal_slot=slot,
            diet_pattern=profile.diet, profile=profile, dev_mode=True,
        )
        times.append(time.perf_counter() - start)
    return times


def main() -> None:
    print("=" * 100)
    print(f"R5 timing baseline -- today's library: "
          f"{len(lib.recipes.components)} components, {len(lib.ingredients)} ingredients")
    print(f"REPEATS = {REPEATS} calls per cell (median / min / max reported, seconds)")
    print()

    overall_max = 0.0
    overall_max_cell = None

    for region, slot in TEMPLATES:
        print(f"-- {region.value}/{slot.value} --")
        for diet in DIET_PATTERNS:
            count = _combination_count(region, slot, diet)
            print(f"  {diet.value:16s} enumerated combinations: {count:4d}")
            for shape, worst_case in (("reference", False), ("worst_case", True)):
                profile = _profile(diet, worst_case=worst_case)
                times = _time_plan_meal(profile, region, slot)
                med, lo, hi = statistics.median(times), min(times), max(times)
                print(f"    {shape:10s} plan_meal: median={med*1000:7.2f}ms "
                      f"min={lo*1000:7.2f}ms max={hi*1000:7.2f}ms")
                if hi > overall_max:
                    overall_max = hi
                    overall_max_cell = (region.value, slot.value, diet.value, shape)
        print()

    print("=" * 100)
    print(f"Slowest single plan_meal call observed: {overall_max*1000:.2f}ms "
          f"at {overall_max_cell}")
    print()
    print("Proposed wall-clock budget per POST /api/plan call: 1500ms.")
    print("Reasoning: the reference-profile shape (no clinical flags, mid-range")
    print("weight, accepts at rung 0 or an early rung) stays under ~110ms in every")
    print("cell measured. The slow cells are all worst_case (clinically flagged,")
    print("extreme weight): plan_within_ladder walks every unlocked rung before")
    print("declining or accepting late, calling the exhaustive solver once per")
    print("rung against the template's full enumerated combination set. That is")
    print("already 505-519ms today at north_indian/lunch (24 combinations, the")
    print("largest template) with only 19 recipe files -- NOT 'well under 100ms'")
    print("as a first draft of this reasoning wrongly assumed before the run.")
    print("R3/R4 add recipes to relieve exactly the bounds that force full-ladder")
    print("walks (quality-protein, fat ceiling), which could shrink this, but they")
    print("also grow each template's combination count, which the solver cost")
    print("scales with -- direction of net effect is not measured here. 1500ms")
    print("keeps roughly 3x headroom over today's worst observed case rather than")
    print("~0x, without asserting growth is bounded. This is a proposal only --")
    print("Adi confirms or sets a different number.")


if __name__ == "__main__":
    main()
