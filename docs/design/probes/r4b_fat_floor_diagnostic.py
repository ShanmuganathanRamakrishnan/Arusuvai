"""TASKS_3.md R4b diagnostic: which combinations sole-fail `fat_g_floor`.

`probe_blocking_bounds.py` reports the aggregate sole-cause count (106 at
the accepted rung, template-wide) but not which recipes or which slot shape
are behind it -- not enough to decide what kind of dish R4b should add.
This probe answers that for `north_indian/lunch` specifically, the template
R4b's own text names ("sole cause 61 times", a pre-R2-re-derivation figure;
`probe_blocking_bounds.py`'s accepted-rung number is 106 template-wide, not
reproduced per-template here before this probe existed).

Same 144-profile grid as `probe_blocking_bounds.py` and
`probe_rank_input2.py` (`DietPattern.VEGETARIAN`/`VEGAN` only -- the same
structural gap documented in TASKS_3.md's R4a outcome: neither diet pattern
sees egg or fish, and this probe inherits that limit rather than fixing it,
same as `probe_blocking_bounds.py` does).

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/r4b_fat_floor_diagnostic.py
"""
from __future__ import annotations

import logging
from collections import Counter

from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations, macro_bounds, quality_protein_bounds
from core.planner.plan import load_library
from core.planner.validator import plan_within_ladder
from core.schemas import (
    ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

logging.disable(logging.WARNING)
lib = load_library()


def profiles():
    """Identical grid to probe_blocking_bounds.py -- see its docstring."""

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
    """Same logic as probe_blocking_bounds.py's function of the same name."""

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
            quality_protein_bounds(c, ingredients)[1] for c in combo.components
        )
        if reachable < quality_floor:
            broken.append("quality_protein_floor")
    return broken


def main() -> None:
    recipe_id_sets: Counter = Counter()
    category_sets: Counter = Counter()
    sabzi_present: Counter = Counter()
    diet_counter: Counter = Counter()
    example = None

    region, slot = Region.NORTH_INDIAN, MealSlot.LUNCH
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
        accepted_target = outcome.target_used
        for combo in combinations:
            broken = broken_bounds(combo, accepted_target, lib.ingredients)
            if broken == ["fat_g_floor"]:
                ids = tuple(sorted(c.recipe.id for c in combo.components))
                cats = tuple(sorted(c.category for c in combo.components))
                recipe_id_sets[ids] += 1
                category_sets[cats] += 1
                has_sabzi = any(c.category == "sabzi" for c in combo.components)
                sabzi_present["sabzi" if has_sabzi else "no_sabzi"] += 1
                diet_counter[profile.diet.value] += 1
                if example is None:
                    example = (ids, cats, accepted_target.floor("fat_g"))

    print("=" * 100)
    print("north_indian/lunch, accepted-rung target, combos sole-failing fat_g_floor")
    print()
    print("Distinct recipe-id combos, most frequent first:")
    for ids, count in recipe_id_sets.most_common(15):
        print(f"  {count:4d}  {ids}")
    print()
    print("Distinct category-shape combos:")
    for cats, count in category_sets.most_common(15):
        print(f"  {count:4d}  {cats}")
    print()
    print("sabzi presence:", dict(sabzi_present))
    print("diet-pattern breakdown:", dict(diet_counter))
    print()
    print("example (recipe ids, categories, fat_g floor value):", example)


if __name__ == "__main__":
    main()
