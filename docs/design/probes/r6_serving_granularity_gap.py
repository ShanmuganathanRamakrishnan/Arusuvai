"""TASKS_3.md R6: how much of the solver-rejected gap is serving-granularity,
and how much of THAT is honestly recoverable.

R6's own framing: "512 combination-instances cleared the O(1) feasibility
filter and were still rejected by the solver -- no whole number of servings
lands inside the bounds. More recipes do not fix these." That 512 predates
R3a/R3b/R4a/R4b/R4c, all of which changed the recipe library the gap is
measured against; this probe re-measures it on the current library rather
than trusting a number computed before four recipes and one ingredient class
model landed.

Same 144-profile x 4-template grid every other probe in this file uses (see
``probe_rank_input2.py``'s module docstring for why). For every combination
that survives ``core.planner.combinations.feasible_combinations`` (the O(1)
bound pre-filter R6 names) but ``core.planner.solver.solve_combination``
rejects at every legal integer count, this probe asks one narrow question:
would widening ONE component's ``max_count`` by +1, or its ``min_count`` by
-1, in isolation, let the solver succeed? No recipe file is edited to find
out -- a throwaway ``dataclasses.replace`` on a copy of the component is
solved against, and discarded either way.

This is deliberately not an exhaustive search (not +2, not two components
at once, not smaller/larger serving-unit gram sizes) -- R6's "Don't" clause
rules out widening a range FOR THE PURPOSE of making the planner pass, so the
question worth answering is not "what is the maximum recoverable count under
an unconstrained search" but "does the smallest, most defensible widening
recover much, and does anything the search finds actually deserve to move."

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/r6_serving_granularity_gap.py
"""
from __future__ import annotations

import dataclasses
import logging
from collections import Counter

from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import MealCombination, enumerate_combinations, feasible_combinations
from core.planner.plan import load_library
from core.planner.solver import solve_combination
from core.planner.validator import plan_within_ladder
from core.schemas import (
    ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

logging.disable(logging.WARNING)
lib = load_library()

TEMPLATES = (
    (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
    (Region.SOUTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)


def profiles():
    """144 profiles: 6 weights x 3 goals x 2 diets x 4 flag-sets.

    Identical grid to ``probe_rank_input2.py`` and ``probe_blocking_bounds.py``
    -- see either module's docstring for why.
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


def _widened(component, *, extra_max=0, extra_min=0):
    """A copy of ``component`` whose serving unit's count domain is widened.

    Never touches the recipe file on disk -- a throwaway
    ``dataclasses.replace`` chain, solved against and discarded.
    """

    unit = component.recipe.serving_unit
    new_unit = dataclasses.replace(
        unit,
        max_count=unit.max_count + extra_max,
        min_count=max(1, unit.min_count - extra_min),
    )
    new_recipe = dataclasses.replace(component.recipe, serving_unit=new_unit)
    return dataclasses.replace(component, recipe=new_recipe)


def _combo_with_replaced(combo: MealCombination, flat_index: int, replacement) -> MealCombination:
    """``combo`` with its ``flat_index``-th component (flattened across
    ``slot_selections``, in the same order ``MealCombination.components``
    reports) swapped for ``replacement``."""

    new_slot_selections = []
    cursor = 0
    for selection in combo.slot_selections:
        n = len(selection)
        if cursor <= flat_index < cursor + n:
            local = flat_index - cursor
            new_slot_selections.append(
                tuple(replacement if j == local else c for j, c in enumerate(selection))
            )
        else:
            new_slot_selections.append(selection)
        cursor += n
    return dataclasses.replace(combo, slot_selections=tuple(new_slot_selections))


def main() -> None:
    gap_total = 0
    recoverable_by_plus1_max: Counter = Counter()
    recoverable_by_minus1_min: Counter = Counter()
    recoverable_by_template: Counter = Counter()
    unrecoverable_examples: Counter = Counter()

    for region, slot in TEMPLATES:
        for profile in profiles():
            day_target = derive_target(profile).nutrition_target
            pool = build_candidate_pool(
                lib.components(), lib.ingredients, template=template_for(region, slot),
                diet_pattern=profile.diet, dev_mode=True,
            )
            combinations = enumerate_combinations(pool)
            if not combinations:
                continue
            single_meal_target = meal_target(day_target, slot, ledger=None)
            outcome = plan_within_ladder(
                combinations, single_meal_target, lib.ingredients, profile=profile
            )
            target = outcome.target_used

            survivors = feasible_combinations(combinations, target, lib.ingredients)
            for combo in survivors:
                if solve_combination(combo, target, lib.ingredients) is not None:
                    continue  # solved fine -- not part of the gap R6 names
                gap_total += 1

                fixed = False
                components = combo.components
                for i, comp in enumerate(components):
                    trial = _combo_with_replaced(combo, i, _widened(comp, extra_max=1))
                    if solve_combination(trial, target, lib.ingredients) is not None:
                        recoverable_by_plus1_max[comp.recipe.id] += 1
                        fixed = True
                if not fixed:
                    for i, comp in enumerate(components):
                        trial = _combo_with_replaced(combo, i, _widened(comp, extra_min=1))
                        if solve_combination(trial, target, lib.ingredients) is not None:
                            recoverable_by_minus1_min[comp.recipe.id] += 1
                            fixed = True

                if fixed:
                    recoverable_by_template[(region.value, slot.value)] += 1
                else:
                    ids = tuple(sorted(c.recipe.id for c in combo.components))
                    unrecoverable_examples[(region.value, slot.value, ids)] += 1

    print("=" * 100)
    print(f"total bound-feasible-but-solver-rejected combination-instances: {gap_total}")
    print("(TASKS_3.md's own R6 text cites 512, measured before R3/R4 changed the")
    print(" library this is computed against -- see the number above for today's.)")
    print()
    print("recoverable via +1 max_count on a single component alone, by recipe:")
    for rid, n in recoverable_by_plus1_max.most_common(20):
        print(f"  {n:4d}  {rid}")
    print()
    print("recoverable via -1 min_count on a single component alone, by recipe:")
    for rid, n in recoverable_by_minus1_min.most_common(20):
        print(f"  {n:4d}  {rid}")
    print()
    recoverable_total = sum(recoverable_by_template.values())
    print(f"recoverable total (any single +1 max or -1 min fixes it): "
          f"{recoverable_total} / {gap_total}")
    print("recoverable, by template:")
    for k, n in recoverable_by_template.most_common():
        print(f"  {k}: {n}")
    print()
    print("top unrecoverable (region, slot, recipe-id-combo) instances:")
    for (region_v, slot_v, ids), n in unrecoverable_examples.most_common(20):
        print(f"  {n:4d}  {region_v}/{slot_v}  {ids}")


if __name__ == "__main__":
    main()
