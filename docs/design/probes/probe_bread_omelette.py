"""Could a bread omelette fit a snack? (TASKS_3.md N20) Arithmetic only.

Nothing is added to the library. IFCT 2017 has no bread row (searched the
full text of the NIN PDF, 2026-10-08), so bread per 100 g is from USDA
FoodData Central, SR Legacy, fetched 2026-10-08 -- the source this project
already used for egg B12 when IFCT lacked a figure:
  white  FDC 174924: 1110 kJ, protein 8.85, fat 3.33, carb 49.4, fibre 2.7, Na 490
  wheat  FDC 172688: 1060 kJ, protein 12.4, fat 3.5,  carb 42.7, fibre 6.0, Na 455
kJ -> kcal by / 4.184. Omelette = the library's muttai_omelette, per egg.

Assumptions, stated: a slice is 25 g (not sourced); bread protein does not
qualify toward the quality floor (wheat DIAAS below 0.75 is from memory,
not opened -- unverified); no butter or oil on the bread is counted, which
can only make the dish fit LESS often. Each version is checked against the
UNRELAXED snack target of 36 egg-eating bodies; the quality floor has no
relaxation rung at all.

    PYTHONPATH=. python docs/design/probes/probe_bread_omelette.py
"""
import collections, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

from core.foods.nutrition_of import nutrition_of_recipe
from core.foods.quality import quality_protein_of_recipe
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.plan import default_library
from core.schemas import DietPattern, MealSlot, Profile
from core.schemas.profile import ActivityLevel, Goal, Sex

lib = default_library()
om = next(c.recipe for c in lib.components() if c.recipe.id == "muttai_omelette")
nm = next(c.recipe for c in lib.components() if c.recipe.id == "neer_mor")
BREAD = {
    "white": dict(energy_kcal=1110 / 4.184, protein_g=8.85, fat_g=3.33, carb_g=49.4, fibre_g=2.7, sodium_mg=490),
    "wheat": dict(energy_kcal=1060 / 4.184, protein_g=12.4, fat_g=3.5, carb_g=42.7, fibre_g=6.0, sodium_mg=455),
}
KEYS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")


def plate(bread, eggs, drink, slices=None):
    v = nutrition_of_recipe(om, eggs, lib.ingredients)
    tot = {k: getattr(v, k) + BREAD[bread][k] * 0.25 * (slices or 2 * eggs) for k in KEYS}
    q = quality_protein_of_recipe(om, eggs, lib.ingredients)
    if drink:
        d = nutrition_of_recipe(nm, 1, lib.ingredients)
        for k in KEYS:
            tot[k] += getattr(d, k)
        q += quality_protein_of_recipe(nm, 1, lib.ingredients)
    tot["quality_protein_g"] = q
    return tot


def misses(t, tot):
    out = []
    for m in t.bounded_macros():
        f, c = t.floor(m), t.ceiling(m)
        if f is not None and tot[m] < f:
            out.append(f"{m}<{f:.1f}")
        if c is not None and tot[m] > c:
            out.append(f"{m}>{c:.1f}")
    qf = t.quality_protein_floor()
    if qf is not None and tot["quality_protein_g"] < qf:
        out.append(f"quality<{qf:.1f}")
    return out


fits = collections.Counter(); why = collections.Counter(); n = 0
for diet in ("eggetarian", "non_vegetarian"):
    for goal in Goal:
        for sex in (Sex.MALE, Sex.FEMALE):
            for w in (55, 70, 90):
                p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                            activity=ActivityLevel.MODERATE, goal=goal, diet=DietPattern(diet),
                            clinical_flags=frozenset())
                t = meal_target(derive_target(p).nutrition_target, MealSlot.SNACK)
                n += 1
                for bread in BREAD:
                    for eggs, slices in ((1, 2), (2, 2), (2, 4)):
                        for drink in (False, True):
                            key = f"{bread} {eggs}egg {slices}sl{' +nm' if drink else ''}"
                            m = misses(t, plate(bread, eggs, drink, slices))
                            fits[key] += not m
                            for x in m:
                                why[(key, x.split('<')[0].split('>')[0] + ('<' if '<' in x else '>'))] += 1

print(f"bodies: {n}")
for bread in BREAD:
    for eggs, slices in ((1, 2), (2, 2), (2, 4)):
        for drink in (False, True):
            key = f"{bread} {eggs}egg {slices}sl{' +nm' if drink else ''}"
            tot = plate(bread, eggs, drink, slices)
            fails = dict(sorted((k[1], v) for k, v in why.items() if k[0] == key))
            print(f"{key:24s} fits {fits[key]:2d}/{n}  "
                  f"[{tot['energy_kcal']:.0f} kcal, prot {tot['protein_g']:.1f}, qual {tot['quality_protein_g']:.1f}, "
                  f"fat {tot['fat_g']:.1f}, fibre {tot['fibre_g']:.1f}]  misses: {fails}")
