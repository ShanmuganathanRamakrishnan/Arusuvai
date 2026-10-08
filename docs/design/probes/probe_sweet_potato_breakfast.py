"""Could boiled egg with sweet potato fit a breakfast? Arithmetic only. (TASKS_3.md N22)

The owner's account (2026-10-08): a boiled egg with sundal or sweet potato is
a breakfast habit. Nothing here is added to the library.

Sweet potato per 100 g, two sources, used as a low and a high case:
  IFCT 2017 F013 "Sweet potato, brown skin (Ipomoea batatas)", RAW, read
    2026-10-08 from the primary NIN-published IFCT2017.pdf (Table 1 p.53 of
    the PDF file; Table 5 minerals p.176), 4 regions:
    water 69.21, protein 1.33, fat 0.26, fibre 3.99, available carb 24.25,
    energy 456 kJ, sodium 29.60 mg.
    carb_g = available carb + fibre (24.25 + 3.99 = 28.24), the convention
    potato_raw (F006) already follows: 14.89 + 1.71 = 16.60.
  USDA FoodData Central SR Legacy FDC 168484 "Sweet potato, cooked, boiled,
    without skin", fetched 2026-10-08: water 80.13, energy 76 kcal, protein
    1.37, fat 0.14, carb (by difference) 17.72, fibre 2.5, sodium 27 mg.
IFCT measured RAW Indian sweet potato and has no boiled row; USDA measured
BOILED, but American sweet potato (its raw row, FDC 168482, is 77.28% water
against IFCT's 69.21%). Using IFCT raw as eaten assumes boiling adds no
water, which overstates energy per gram; USDA boiled likely understates it for
the drier Indian tuber. Neither is the right food cooked the right way, so
both are run; the verdict counts only where they agree.

Assumptions, not sourced: sweet potato portion sizes (100-250 g tried);
sweet potato protein counted as NOT qualifying (no DIAAS row for it).
Egg = the library's avicha_muttai, 1 or 2 eggs. Checked at the unrelaxed
breakfast target and after each step of RELAXATION_ORDER, cumulatively.

    PYTHONPATH=. python docs/design/probes/probe_sweet_potato_breakfast.py
"""
import collections, logging, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

from core.foods.nutrition_of import nutrition_of_recipe
from core.foods.quality import quality_protein_of_recipe
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.plan import default_library
from core.planner.validator import RELAXATION_ORDER
from core.schemas import DietPattern, MealSlot, Profile
from core.schemas.profile import ActivityLevel, Goal, Sex

KEYS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")
SWEET_POTATO = {
    "IFCT raw": dict(energy_kcal=456 / 4.184, protein_g=1.33, fat_g=0.26, carb_g=24.25 + 3.99,
                     fibre_g=3.99, sodium_mg=29.60),
    "USDA boiled": dict(energy_kcal=76.0, protein_g=1.37, fat_g=0.14, carb_g=17.72,
                        fibre_g=2.5, sodium_mg=27.0),
}
GRAMS = (100, 150, 200, 250)
EGGS = (1, 2)

lib = default_library()
egg = next(c.recipe for c in lib.components() if c.recipe.id == "avicha_muttai")


def plate(src, grams, eggs):
    v = nutrition_of_recipe(egg, eggs, lib.ingredients)
    tot = {k: getattr(v, k) + SWEET_POTATO[src][k] * grams / 100 for k in KEYS}
    tot["quality"] = quality_protein_of_recipe(egg, eggs, lib.ingredients)
    return tot


def misses(t, tot):
    out = set()
    for m in t.bounded_macros():
        f, c = t.floor(m), t.ceiling(m)
        if f is not None and tot[m] < f:
            out.add(f"{m} below floor")
        if c is not None and tot[m] > c:
            out.add(f"{m} above ceiling")
    qf = t.quality_protein_floor()
    if qf is not None and tot["quality"] < qf:
        out.add("quality protein below floor")
    return out


def rungs(t):
    out = [("unrelaxed", t)]
    for step in RELAXATION_ORDER:
        t = step.apply(t, frozenset())
        out.append((step.name, t))
    return out


targets = []
for diet in ("eggetarian", "non_vegetarian"):
    for goal in Goal:
        for sex in (Sex.MALE, Sex.FEMALE):
            for w in (55, 70, 90):
                p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                            activity=ActivityLevel.MODERATE, goal=goal, diet=DietPattern(diet),
                            clinical_flags=frozenset())
                targets.append(rungs(meal_target(derive_target(p).nutrition_target, MealSlot.BREAKFAST)))

t0 = targets[0][0][1]
print(f"bodies: {len(targets)}; e.g. eggetarian lose_fat male 55kg breakfast, unrelaxed: energy "
      f"{t0.floor('energy_kcal'):.0f}-{t0.ceiling('energy_kcal'):.0f} kcal, protein >= {t0.floor('protein_g'):.1f} g, "
      f"quality >= {t0.quality_protein_floor():.1f} g, fat <= {t0.ceiling('fat_g'):.1f} g")
for src in SWEET_POTATO:
    for eggs in EGGS:
        for grams in GRAMS:
            tot = plate(src, grams, eggs)
            fit_any = sum(any(not misses(t, tot) for _, t in lad) for lad in targets)
            fit_un = sum(not misses(lad[0][1], tot) for lad in targets)
            why = collections.Counter(b for lad in targets for b in misses(lad[-1][1], tot))
            print(f"{src:11s} {eggs} egg + {grams:3d} g  [{tot['energy_kcal']:3.0f} kcal, prot {tot['protein_g']:4.1f}, "
                  f"qual {tot['quality']:4.1f}, fat {tot['fat_g']:4.1f}, fibre {tot['fibre_g']:3.1f}]  "
                  f"fits unrelaxed {fit_un:2d}/36, at some rung {fit_any:2d}/36  "
                  f"last-rung misses: {dict(sorted(why.items()))}")
