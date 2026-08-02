"""Does the label ever have teeth? Simulate Task 6 (verified composition data).

Replaces every ingredient's composition_uncertainty with the registered
verified band (composition.verified_primary = 0.05) and re-measures the label
with and without the proposed authored-quantity band.
"""
from __future__ import annotations

import dataclasses

from core.foods.models import NutritionVector
from core.foods.nutrition_of import nutrition_of_components
from core.foods.templates import template_for
from core.nutrition import citations
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations
from core.planner.plan import load_library
from core.planner.validator import plan_within_ladder
from core.schemas import (
    MACRO_KEYS, ActivityLevel, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

GATED = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")
VERIFIED = citations.value_of("composition.verified_primary")

lib = load_library()
template = template_for(Region.NORTH_INDIAN, MealSlot.LUNCH)
pool = build_candidate_pool(lib.components(), lib.ingredients, template=template,
                            diet_pattern=DietPattern.VEGETARIAN, dev_mode=True)
combos = enumerate_combinations(pool)

tight = {
    k: dataclasses.replace(v, verified=True,
                           composition_uncertainty={m: VERIFIED for m in MACRO_KEYS})
    for k, v in lib.ingredients.items()
}


def quantity_band(items, ingredients, q):
    band = NutritionVector.zero()
    for component, count in items:
        for line in component.recipe.ingredients:
            ing = ingredients[line.ingredient_id]
            band = band + (ing.for_grams(line.quantity_g) * count) * q
    return band


def label(point, hw, target):
    verdict, detail = "confident", []
    for macro in target.bounded_macros():
        p, h = getattr(point, macro), hw.get(macro, 0.0)
        floor, ceiling = target.floor(macro), target.ceiling(macro)
        if not ((floor is not None and p - h < floor) or
                (ceiling is not None and p + h > ceiling)):
            continue
        room = ((ceiling - floor) / 2 if floor is not None and ceiling is not None
                else (ceiling - p if ceiling is not None else p - floor))
        detail.append(f"{macro}(h={h:.1f} room={room:.1f})")
        if h > room:
            verdict = "very rough"
        elif verdict != "very rough":
            verdict = "rough"
    return verdict, detail


p = Profile(weight_kg=45.0, height_cm=165.0, age_years=35, sex=Sex.FEMALE,
            activity=ActivityLevel.ACTIVE, goal=Goal.MAINTAIN,
            diet=DietPattern.VEGETARIAN)
dt = derive_target(p).nutrition_target
out = plan_within_ladder(combos, meal_target(dt, MealSlot.LUNCH),
                         lib.ingredients, profile=p)
plan, used = out.plan, out.target_used
items = [(c, plan.unit_counts[c.id]) for c in plan.combination.components]
print(f"plate {plan.unit_counts}, rungs {out.result.relaxation_applied}")

for name, ingredients in (("today (composition 0.25)", lib.ingredients),
                          ("after Task 6 (composition 0.05)", tight)):
    est = nutrition_of_components(items, ingredients)
    for q in (0.0, 0.05, 0.10, 0.15, 0.20):
        extra = quantity_band(items, ingredients, q) if q else None
        hw = {m: (getattr(est.high, m) - getattr(est.low, m)) / 2
              + (getattr(extra, m) if extra else 0.0) for m in GATED}
        verdict, detail = label(est.point, hw, used)
        frac = ", ".join(f"{m}={hw[m]/max(getattr(est.point,m),1e-9):.0%}" for m in GATED)
        print(f"  {name:<32} q={q:.2f} -> {verdict:<11} [{frac}]")
        print(f"       {detail}")
