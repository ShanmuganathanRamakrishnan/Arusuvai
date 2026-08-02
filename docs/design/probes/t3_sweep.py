"""Find a profile whose north_lunch actually solves, so the label has a plate."""
from __future__ import annotations

from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations
from core.planner.plan import load_library
from core.planner.validator import plan_within_ladder
from core.schemas import (
    ActivityLevel, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

lib = load_library()
template = template_for(Region.NORTH_INDIAN, MealSlot.LUNCH)
pool = build_candidate_pool(lib.components(), lib.ingredients, template=template,
                            diet_pattern=DietPattern.VEGETARIAN, dev_mode=True)
combos = enumerate_combinations(pool)

for weight in (45, 50, 55, 60, 65, 70, 80, 90):
    for goal in Goal:
        for activity in ActivityLevel:
            p = Profile(weight_kg=float(weight), height_cm=165.0, age_years=35,
                        sex=Sex.FEMALE, activity=activity, goal=goal,
                        diet=DietPattern.VEGETARIAN)
            dt = derive_target(p).nutrition_target
            out = plan_within_ladder(combos, meal_target(dt, MealSlot.LUNCH),
                                     lib.ingredients, profile=p)
            if out.plan is not None:
                print(f"FEASIBLE {weight}kg {goal.value} {activity.value} "
                      f"rungs={out.result.relaxation_applied} "
                      f"plate={out.plan.unit_counts} "
                      f"Na={out.plan.estimate.point.sodium_mg:.1f}")
