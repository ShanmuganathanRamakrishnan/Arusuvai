"""D5: the margin on every bound, for all four passing plates.

Answers one question: south_lunch passes at 1391.1 mg against a 1400 mg guard.
Is a 8.9 mg margin unique to that plate and that bound, or is the whole set of
four passing templates sitting on margins nobody has looked at?

For each template it prints, per bound:

  slack      how far the plate sits from the bound, absolute and as a percent
             of the bound
  step       the smallest *legal* unit move on this plate that pushes the
             plate toward that bound

`step` is the figure that matters. Portion space is integer unit counts
(CLAUDE.md, "Serving units"), so a bound is not tight because its slack is a
small number of milligrams — it is tight when slack is smaller than the
smallest move available. A 8.9 mg slack against a 261.9 mg next step means the
plate is not near a cliff it could fall off by rounding; it means the bound is
*load-bearing*, holding out an entire discrete alternative.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d5_margins.py
"""
from __future__ import annotations

import dataclasses

from core.nutrition import citations
from core.foods.nutrition_of import nutrition_of_components, nutrition_of_recipe
from core.foods.quality import quality_protein_of_recipe
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.plan import Library, load_library, plan_meal
from core.schemas import (
    ActivityLevel, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

# demo.py's REFERENCE_PROFILE, duplicated rather than imported because demo.py
# builds it through argparse. If these drift the probe is measuring a different
# person than every other transcript in the repo.
PROFILE = Profile(
    weight_kg=70.0, height_cm=175.0, age_years=28, sex=Sex.MALE,
    activity=ActivityLevel.MODERATE, goal=Goal.MAINTAIN,
    diet=DietPattern.VEGETARIAN,
)

TEMPLATES = (
    (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
    (Region.SOUTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)

MACROS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")

lib = load_library()
day = derive_target(PROFILE).nutrition_target


def unit_step(plan, macro, direction):
    """Smallest legal one-unit move on this plate that moves ``macro``
    in ``direction`` (+1 = up, toward a ceiling; -1 = down, toward a floor).

    Legal means the component's own min_count/max_count allows the move
    (`core.foods.models.ServingUnit`) -- a component already at max_count cannot
    be incremented, so its contribution is not an available step.
    """

    best = None
    for component in plan.combination.components:
        count = plan.unit_counts[component.id]
        unit = component.recipe.serving_unit
        nxt = count + direction
        if nxt < unit.min_count or nxt > unit.max_count:
            continue
        here = getattr(nutrition_of_recipe(component.recipe, count, lib.ingredients), macro)
        there = getattr(nutrition_of_recipe(component.recipe, nxt, lib.ingredients), macro)
        delta = abs(there - here)
        if delta <= 0:
            continue
        if best is None or delta < best[0]:
            best = (delta, component.id, count, nxt)
    return best


def quality_step(plan, direction):
    best = None
    for component in plan.combination.components:
        count = plan.unit_counts[component.id]
        unit = component.recipe.serving_unit
        nxt = count + direction
        if nxt < unit.min_count or nxt > unit.max_count:
            continue
        here = quality_protein_of_recipe(component.recipe, count, lib.ingredients)
        there = quality_protein_of_recipe(component.recipe, nxt, lib.ingredients)
        delta = abs(there - here)
        if delta <= 0:
            continue
        if best is None or delta < best[0]:
            best = (delta, component.id, count, nxt)
    return best


def report(label, value, bound, kind, step, unit):
    """One bound line. ``kind`` is floor/ceiling/hard_ceiling/quality."""

    slack = (value - bound) if kind == "floor" or kind == "quality" else (bound - value)
    pct = 100.0 * slack / bound if bound else float("nan")
    line = (f"    {label:<26} plate {value:9.1f}  bound {bound:9.1f}  "
            f"slack {slack:9.1f} {unit} ({pct:5.1f}% of bound)")
    if step is None:
        line += "   step: none available"
    else:
        delta, cid, a, b = step
        tight = "TIGHT" if delta > slack else "loose"
        line += f"   step: {delta:8.1f} via {cid} {a}->{b}  [{tight}]"
    print(line)


UNITS = {"energy_kcal": "kcal", "protein_g": "g", "fat_g": "g", "carb_g": "g",
         "fibre_g": "g", "sodium_mg": "mg"}

for region, slot in TEMPLATES:
    print("=" * 100)
    print(f"{region.value} / {slot.value}")
    print("=" * 100)
    outcome = plan_meal(lib, day, region=region, meal_slot=slot,
                        diet_pattern=PROFILE.diet, profile=PROFILE, dev_mode=True)
    if outcome.plan is None:
        print(f"  DECLINED -- {outcome.result.disclosure}")
        print()
        continue
    plan = outcome.plan
    point = plan.estimate.point
    unrelaxed = meal_target(day, slot)
    print(f"  plate            : {dict(sorted(plan.unit_counts.items()))}")
    print(f"  rungs fired      : {outcome.result.relaxation_applied or '(none)'}")
    print(f"  quality protein  : {plan.quality_protein_g:.2f} g")

    for name, target in (("AS ASKED (unrelaxed)", unrelaxed),
                         ("AS SOLVED (target_used)", outcome.target_used)):
        if name.startswith("AS SOLVED") and not outcome.result.relaxation_applied:
            print("  AS SOLVED: identical to AS ASKED -- no rung fired.")
            break
        print(f"  {name}")
        for macro in MACROS:
            value = getattr(point, macro)
            u = UNITS[macro]
            floor = target.floor(macro)
            if floor is not None:
                report(f"{macro} floor", value, floor, "floor",
                       unit_step(plan, macro, -1), u)
            ceiling = target.ceiling(macro)
            if ceiling is not None:
                report(f"{macro} ceiling", value, ceiling, "ceiling",
                       unit_step(plan, macro, +1), u)
            hard = target.hard_ceiling(macro)
            if hard is not None:
                report(f"{macro} HARD ceiling", value, hard, "ceiling",
                       unit_step(plan, macro, +1), u)
        qfloor = target.quality_protein_floor()
        if qfloor is not None:
            report("quality protein floor", plan.quality_protein_g, qfloor,
                   "quality", quality_step(plan, -1), "g")
    print()

    # A per-macro `step` reads one bound at a time, and a unit move changes
    # every macro at once. So: enumerate every legal single-unit neighbour of
    # the passing plate and say which bound each one breaks. A plate with no
    # feasible neighbour is a point solution -- the solver did not choose it
    # from a region, it was the only thing there.
    print("  SINGLE-UNIT NEIGHBOURS (against target_used)")
    used = outcome.target_used
    feasible = 0
    for component in plan.combination.components:
        count = plan.unit_counts[component.id]
        u = component.recipe.serving_unit
        for nxt in (count - 1, count + 1):
            if nxt < u.min_count or nxt > u.max_count:
                continue
            items = [(c, nxt if c.id == component.id else plan.unit_counts[c.id])
                     for c in plan.combination.components]
            est = nutrition_of_components(items, lib.ingredients)
            broken = []
            for macro in MACROS:
                v = getattr(est.point, macro)
                f, c_ = used.floor(macro), used.ceiling(macro)
                h = used.hard_ceiling(macro)
                if f is not None and v < f:
                    broken.append(f"{macro} floor by {f - v:.1f}")
                if c_ is not None and v > c_:
                    broken.append(f"{macro} ceiling by {v - c_:.1f}")
                if h is not None and v > h:
                    broken.append(f"{macro} HARD ceiling by {v - h:.1f}")
            q = sum(quality_protein_of_recipe(c.recipe, n, lib.ingredients)
                    for c, n in items)
            qf = used.quality_protein_floor()
            if qf is not None and q < qf:
                broken.append(f"quality floor by {qf - q:.1f}")
            if not broken:
                feasible += 1
            print(f"    {component.id} {count}->{nxt}: "
                  + ("FEASIBLE" if not broken else "; ".join(broken)))
    print(f"    -> {feasible} of the plate's single-unit neighbours are feasible")
    print()


# ---------------------------------------------------------------------------
# Sensitivity of the four verdicts to `day_budget.absurdity_fraction`.
#
# NOT a tuning exercise: nothing is edited. `citations.value_of` is wrapped for
# the duration of this loop so the same pipeline can be asked what it would say
# if the guard sat somewhere else. The question D5 asks is whether the four
# passing verdicts are a property of the recipe library or of one unregistered
# fraction; the only way to answer it is to move the fraction and watch.
# ---------------------------------------------------------------------------
print("=" * 100)
print("GUARD SENSITIVITY -- verdict per template as day_budget.absurdity_fraction moves")
print("(0.70 is the registered value; nothing is written back)")
print("=" * 100)

_real_value_of = citations.value_of


def with_guard(fraction, fn):
    def patched(key, _f=fraction):
        return _f if key == "day_budget.absurdity_fraction" else _real_value_of(key)

    citations.value_of = patched
    try:
        return fn()
    finally:
        citations.value_of = _real_value_of


def outcome_for(library, region, slot):
    return plan_meal(library, day, region=region, meal_slot=slot,
                     diet_pattern=PROFILE.diet, profile=PROFILE, dev_mode=True)


for fraction in (0.20, 0.35, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 0.90, 1.00):
    def row():
        cells = []
        for region, slot in TEMPLATES:
            out = outcome_for(lib, region, slot)
            tag = f"{region.value[:5]}_{slot.value[:5]}"
            if out.plan is None:
                cells.append(f"{tag}=DECLINE")
            else:
                na = out.plan.estimate.point.sodium_mg
                cells.append(f"{tag}=pass({len(out.result.relaxation_applied)}r,{na:.0f}mg)")
        return cells

    print(f"  {fraction:.2f} -> guard {2000 * fraction:7.1f} mg | "
          + "  ".join(with_guard(fraction, row)))

print()
print("  Bisected pass/decline boundary per template (40 iterations):")
for region, slot in TEMPLATES:
    lo, hi = 0.10, 1.00  # lo declines, hi passes
    for _ in range(40):
        mid = (lo + hi) / 2
        if with_guard(mid, lambda: outcome_for(lib, region, slot).plan) is not None:
            hi = mid
        else:
            lo = mid
    print(f"    {region.value}/{slot.value}: flips at {hi:.6f} = {2000 * hi:7.1f} mg; "
          f"registered 0.70 = 1400.0 mg is {2000 * (0.70 - hi):.1f} mg "
          f"({100 * (0.70 - hi) / 0.70:.1f}%) above it")

print()
print("=" * 100)
print("SALT SENSITIVITY -- how wrong may every sodium value in the library be")
print("before a template stops passing? (guard left at its registered 0.70)")
print("=" * 100)
print("  The axis D5 actually asks about: recipe work changes the plate, not")
print("  the guard. Every ingredient row's sodium_mg is scaled by k in memory.")


def scaled_library(k):
    ings = {i: dataclasses.replace(v, sodium_mg=v.sodium_mg * k)
            for i, v in lib.ingredients.items()}
    return Library(ingredients=ings, recipes=lib.recipes)


for region, slot in TEMPLATES:
    lo, hi = 1.0, 6.0  # lo passes, hi declines
    for _ in range(30):
        mid = (lo + hi) / 2
        if outcome_for(scaled_library(mid), region, slot).plan is not None:
            lo = mid
        else:
            hi = mid
    print(f"    {region.value}/{slot.value}: still passes at x{lo:.3f} "
          f"(+{100 * (lo - 1):.1f}% on every salt figure in the library)")
