"""Flat band vs mass-check-capped band, measured per recipe and per plate."""
from __future__ import annotations

from core.foods.models import NutritionVector
from core.foods.nutrition_of import nutrition_of_components
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

GATED = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")
MASS_TOL = 0.02  # models._RECIPE_MASS_TOLERANCE

lib = load_library()


def line_band(recipe, line, q):
    cap = MASS_TOL * recipe.serving_unit.grams_per_unit / line.quantity_g
    return min(q, cap)


def band(items, q, capped):
    out = NutritionVector.zero()
    for component, count in items:
        r = component.recipe
        for line in r.ingredients:
            f = line_band(r, line, q) if capped else q
            v = lib.ingredients[line.ingredient_id].for_grams(line.quantity_g) * count
            out = out + v * f
    return out


print("=== per-line effective band, q=0.30 capped by the +/-2% recipe mass check ===")
for rid, r in sorted(lib.recipes.recipes.items()):
    print(f"{rid}  (unit {r.serving_unit.grams_per_unit:g} g)")
    for line in r.ingredients:
        print(f"    {line.ingredient_id:<22} {line.quantity_g:6.2f} g  "
              f"band {line_band(r, line, 0.30):.3f}")

print()
print("=== per-recipe macro bands: today | flat q | capped q (q=0.30) ===")
for rid, r in sorted(lib.recipes.recipes.items()):
    comp = lib.recipes.component(rid)
    est = nutrition_of_components([(comp, 1)], lib.ingredients)
    flat = band([(comp, 1)], 0.30, False)
    cap = band([(comp, 1)], 0.30, True)
    def frac(extra):
        return ", ".join(
            f"{m.split('_')[0]}="
            f"{(((getattr(est.high,m)-getattr(est.low,m))/2)+(getattr(extra,m) if extra else 0))/max(getattr(est.point,m),1e-9):.0%}"
            for m in GATED)
    print(f"  {rid}")
    print(f"    today  : {frac(None)}")
    print(f"    flat   : {frac(flat)}")
    print(f"    capped : {frac(cap)}")

print()
print("=== the plate that solves unrelaxed ===")
p = Profile(weight_kg=45.0, height_cm=165.0, age_years=35, sex=Sex.FEMALE,
            activity=ActivityLevel.ACTIVE, goal=Goal.MAINTAIN,
            diet=DietPattern.VEGETARIAN)
template = template_for(Region.NORTH_INDIAN, MealSlot.LUNCH)
pool = build_candidate_pool(lib.components(), lib.ingredients, template=template,
                            diet_pattern=DietPattern.VEGETARIAN, dev_mode=True)
combos = enumerate_combinations(pool)
dt = derive_target(p).nutrition_target
out = plan_within_ladder(combos, meal_target(dt, MealSlot.LUNCH), lib.ingredients,
                         profile=p)
plan, used = out.plan, out.target_used
items = [(c, plan.unit_counts[c.id]) for c in plan.combination.components]
est = plan.estimate
print(f"  plate {plan.unit_counts}")
for name, extra in (("today", None), ("flat 0.30", band(items, 0.30, False)),
                    ("capped 0.30", band(items, 0.30, True))):
    print(f"    {name:<12} " + ", ".join(
        f"{m.split('_')[0]}="
        f"{(((getattr(est.high,m)-getattr(est.low,m))/2)+(getattr(extra,m) if extra else 0))/max(getattr(est.point,m),1e-9):.0%}"
        for m in GATED))
print(f"  point  " + ", ".join(f"{m.split('_')[0]}={getattr(est.point,m):.1f}" for m in GATED))

print()
print("=== unverified-energy accounting on that plate, today ===")
print(f"  unverified_energy_kcal = {est.unverified_energy_kcal:.1f} of "
      f"{est.point.energy_kcal:.1f} = {est.unverified_energy_fraction():.1%}")
for rid, r in sorted(lib.recipes.recipes.items()):
    print(f"  {rid:<14} process_constants={sorted(r.process_constants)}")
