"""TASKS_3.md N5: why an eggetarian South Indian plate almost never has an egg.

N3/N4 measured eggetarian South breakfast 0/72, lunch 1/72, dinner 1/72, snack
0/72 bodies with a valid egg plate, although an egg dish exists for each:
egg_dosa (tiffin), mutta_kuzhambu (kuzhambu, breakfast/lunch/dinner gravy),
muttai_podimas (egg, snack). Before adding dishes, this asks what blocks the
ones already there.

For each of the 72 bodies (eggetarian), per South template: take the target
the ladder stops on for the full pool, keep only combinations containing an
egg dish, and record the bounds broken by the nearest such plate (fewest bounds
broken, the validator's own `_nearest_plate_violations`). Tallies which bound
each egg dish fails on. Read-only.

    PYTHONPATH=. python docs/design/probes/probe_south_egg_blockers.py
"""

from __future__ import annotations

import runpy
from collections import Counter
from pathlib import Path

from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.combinations import feasible_combinations
from core.planner.solver import solve
from core.planner.validator import _nearest_plate_violations, plan_within_ladder
from core.schemas import ActivityLevel, DietPattern, MealSlot, Profile, Region, Sex

here = Path(__file__).parent
base = runpy.run_path(str(here / "probe_rank_input2.py"), run_name="probe_base")
nonveg = runpy.run_path(str(here / "probe_nonveg.py"), run_name="probe_nonveg")
lib = base["lib"]
combinations_for = base["_combinations_for"]

EGG_DISHES = ("egg_dosa", "mutta_kuzhambu", "muttai_podimas")
SOUTH = [(Region.SOUTH_INDIAN, s) for s in
         (MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER, MealSlot.SNACK)]


def main() -> None:
    for region, slot in SOUTH:
        per_dish: dict[str, Counter] = {}
        reachable = Counter()
        for weight, goal, flags in nonveg["bodies"]():
            p = Profile(weight_kg=weight, height_cm=175.0, age_years=28,
                        sex=Sex.MALE, activity=ActivityLevel.MODERATE, goal=goal,
                        diet=DietPattern.EGGETARIAN, clinical_flags=flags)
            combos = combinations_for(p, region, slot)
            if not combos:
                continue
            day = derive_target(p).nutrition_target
            outcome = plan_within_ladder(
                combos, meal_target(day, slot, ledger=None), lib.ingredients,
                profile=p)
            if outcome.plan is None:
                continue
            for dish in EGG_DISHES:
                egg = [c for c in combos if dish in c.recipe_ids()]
                if not egg:
                    continue
                tally = per_dish.setdefault(dish, Counter())
                tally["(bodies)"] += 1
                # `_nearest_plate_violations` skips a plate that breaks
                # nothing, so a valid egg plate must be looked for first or
                # the body would be tallied under the next-nearest plate's
                # misses.
                if solve(feasible_combinations(egg, outcome.target_used,
                                               lib.ingredients),
                         outcome.target_used, lib.ingredients):
                    reachable[dish] += 1
                    continue
                for x in _nearest_plate_violations(
                        egg, outcome.target_used, lib.ingredients, p, ()):
                    tally[f"{x.macro} {x.kind}"] += 1
        print(f"== {region.value}/{slot.value}")
        for dish, tally in per_dish.items():
            print(f"  {dish}: bodies {tally.pop('(bodies)')}, "
                  f"a valid egg plate in {reachable[dish]}; nearest egg "
                  f"plate's misses in the rest:")
            for k, n in tally.most_common():
                print(f"      {k:32s} {n}")


if __name__ == "__main__":
    main()
