"""T3b: how a per-ingredient composition band actually reaches plate level.

T3's design doc claimed a 5% per-ingredient band "produces roughly a 7% band on
plate energy, because errors accumulate across the components of a plate". This
probe tests that claim by construction: it sets every ingredient's composition
uncertainty to a uniform u, then measures the resulting plate-level fraction at
every component count the library can build.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/t3b_propagation.py
"""

from __future__ import annotations

import dataclasses

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

lib = load_library()


def with_uniform_composition(u: float):
    return {
        k: dataclasses.replace(v, composition_uncertainty={m: u for m in MACRO_KEYS})
        for k, v in lib.ingredients.items()
    }


def with_zero_process(recipe):
    return dataclasses.replace(recipe, process_uncertainty={m: 0.0 for m in MACRO_KEYS})


def fractions(est):
    return {
        m: ((getattr(est.high, m) - getattr(est.low, m)) / 2)
        / max(getattr(est.point, m), 1e-12)
        for m in GATED
    }


print("=" * 74)
print("1. Does the plate band grow with component count?")
print("=" * 74)
print("Uniform composition uncertainty u on every ingredient; process term left")
print("as the library declares it. Plates built by adding one component at a time.")
print()

comps = [lib.recipes.component(r) for r in
         ("phulka", "dal_tadka", "onion_raita", "rajma_chawal", "sambar_sadam",
          "masala_dosa")]

for u in (0.05, 0.25):
    print(f"  u = {u:.2f}")
    for n in range(1, len(comps) + 1):
        items = [(c, 1) for c in comps[:n]]
        est = nutrition_of_components(items, with_uniform_composition(u))
        f = fractions(est)
        print(f"    {n} component(s): " + "  ".join(
            f"{m.split('_')[0]}={f[m]:.4f}" for m in GATED))
    print()

print("=" * 74)
print("2. Same, with every process term forced to zero")
print("=" * 74)
print("Isolates the composition term. If the composition band accumulates, these")
print("numbers move with n; if it does not, they are all exactly u.")
print()

zeroed = {r: dataclasses.replace(c, recipe=with_zero_process(c.recipe))
          for r, c in ((c.recipe.id, c) for c in comps)}

for u in (0.05, 0.25):
    print(f"  u = {u:.2f}")
    for n in range(1, len(comps) + 1):
        items = [(zeroed[c.recipe.id], 1) for c in comps[:n]]
        est = nutrition_of_components(items, with_uniform_composition(u))
        f = fractions(est)
        print(f"    {n} component(s): " + "  ".join(
            f"{m.split('_')[0]}={f[m]:.4f}" for m in GATED))
    print()

print("=" * 74)
print("3. Per-macro: propagated band against the tolerance it is checked on")
print("=" * 74)

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
print(f"plate {plan.unit_counts}, rungs {out.result.relaxation_applied}")
print()

for u, name in ((0.25, "today"), (0.05, "after Task 6")):
    est = nutrition_of_components(items, with_uniform_composition(u))
    f = fractions(est)
    print(f"  composition u = {u:.2f} ({name})")
    for m in GATED:
        pt = getattr(est.point, m)
        h = f[m] * pt
        floor, ceiling = used.floor(m), used.ceiling(m)
        if floor is not None and ceiling is not None:
            room = (ceiling - floor) / 2
            kind = "band"
        elif ceiling is not None:
            room, kind = ceiling - pt, "ceiling only"
        elif floor is not None:
            room, kind = pt - floor, "floor only"
        else:
            print(f"    {m:<12} unbounded")
            continue
        verdict = "OK" if h <= room else "EXCEEDS"
        print(f"    {m:<12} h={h:8.2f}  room={room:8.2f}  {verdict:<7} ({kind})")
    print()

print("=" * 74)
print("4. The two constants, side by side")
print("=" * 74)
for k in ("composition.verified_primary", "composition.unverified_secondary",
          "tolerance.energy_default", "tolerance.fat_carb_default",
          "tolerance.energy_relaxed", "tolerance.fat_carb_relaxed"):
    print(f"  {k:<36} {citations.value_of(k)}")

print()
print("=" * 74)
print("5. Where does the extra above u come from on this plate?")
print("=" * 74)
for u in (0.05,):
    ing = with_uniform_composition(u)
    full = fractions(nutrition_of_components(items, ing))
    flat = fractions(nutrition_of_components(
        [(dataclasses.replace(c, recipe=with_zero_process(c.recipe)), n)
         for c, n in items], ing))
    for m in GATED:
        print(f"  {m:<12} with process {full[m]:.4f}   without {flat[m]:.4f}"
              f"   process term {full[m]-flat[m]:.4f}")

print()
print("=" * 74)
print("6. The identity: when u == tolerance, confident reduces to point vs midpoint")
print("=" * 74)
zero_items = [(dataclasses.replace(c, recipe=with_zero_process(c.recipe)), n)
              for c, n in items]
est = nutrition_of_components(zero_items, with_uniform_composition(
    citations.value_of("composition.verified_primary")))
pt = est.point.energy_kcal
floor, ceiling = used.floor("energy_kcal"), used.ceiling("energy_kcal")
mid = (ceiling + floor) / 2
h = fractions(est)["energy_kcal"] * pt
room = (ceiling - floor) / 2
print(f"  u = tolerance.energy_default = {citations.value_of('tolerance.energy_default')}")
print(f"  process forced to zero, so the band is composition only")
print(f"  point    {pt:8.3f}   midpoint {mid:8.3f}   point/midpoint {pt/mid:.6f}")
print(f"  h        {h:8.3f}   room     {room:8.3f}   h/room         {h/room:.6f}")
print(f"  identical to 6 dp: {abs(pt/mid - h/room) < 1e-6}")
print()
print("  With the library's real process term the same plate needs")
print(f"  point <= midpoint * {citations.value_of('tolerance.energy_default')/0.0689:.3f}"
      f" to be confident, i.e. {(1-citations.value_of('tolerance.energy_default')/0.0689)*100:.0f}%")
print(f"  below centre -- which is below the energy floor at {floor:.1f}.")
