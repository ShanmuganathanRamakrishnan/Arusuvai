"""TASKS_3.md N2: how often an animal-protein dish is among a profile's valid plates.

`probe_nonveg.py` counts plates, and a plate count cannot show variety: a
template that already offered two vegetarian plates reads the same whether
or not an egg or chicken plate joins them. This asks the variety question
directly. For each body in the same 72-body grid, per diet and template: is
at least one of the valid plates at the accepted rung built with an egg,
fish or poultry ingredient?

The solved set is recomputed exactly as `probe_rank_input2.py`'s
`accepted_rung_valid_plate_count` does (same ladder call, same target), using
that module's own loaded library and helpers. Read-only.

    PYTHONPATH=. python docs/design/probes/probe_nonveg_variety.py
"""

from __future__ import annotations

import runpy
from pathlib import Path

from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.combinations import feasible_combinations
from core.planner.solver import solve
from core.planner.validator import plan_within_ladder
from core.schemas import ActivityLevel, DietPattern, Profile, Sex

here = Path(__file__).parent
base = runpy.run_path(str(here / "probe_rank_input2.py"), run_name="probe_base")
nonveg = runpy.run_path(str(here / "probe_nonveg.py"), run_name="probe_nonveg")
lib = base["lib"]
TEMPLATES = base["TEMPLATES"]
combinations_for = base["_combinations_for"]

ANIMAL = {"egg", "fish", "poultry"}
DIETS = (DietPattern.EGGETARIAN, DietPattern.NON_VEGETARIAN)


def _is_animal(component) -> bool:
    for line in component.recipe.ingredients:
        row = lib.ingredients[line.ingredient_id]
        if {c.value for c in row.classes} & ANIMAL:
            return True
    return False


def valid_plates(profile, region, slot):
    combos = combinations_for(profile, region, slot)
    if not combos:
        return []
    day = derive_target(profile).nutrition_target
    target = meal_target(day, slot, ledger=None)
    outcome = plan_within_ladder(combos, target, lib.ingredients, profile=profile)
    if outcome.plan is None:
        return []
    return solve(
        feasible_combinations(combos, outcome.target_used, lib.ingredients),
        outcome.target_used, lib.ingredients,
    )


def main() -> None:
    print("Bodies (of 72) with at least one valid plate containing an egg, fish or")
    print("poultry dish, at the accepted rung:")
    print(f"{'template':24s}" + "".join(f"{d.value:>18s}" for d in DIETS))
    for region, slot in TEMPLATES:
        row = f"{region.value + '/' + slot.value:24s}"
        for diet in DIETS:
            hit = 0
            for weight, goal, flags in nonveg["bodies"]():
                p = Profile(weight_kg=weight, height_cm=175.0, age_years=28,
                            sex=Sex.MALE, activity=ActivityLevel.MODERATE,
                            goal=goal, diet=diet, clinical_flags=flags)
                plates = valid_plates(p, region, slot)
                if any(_is_animal(c) for pl in plates for c in pl.combination.components):
                    hit += 1
            row += f"{hit:>18d}"
        print(row)


if __name__ == "__main__":
    main()
