"""Could a banana, tea, or both fit a snack? Arithmetic only. (TASKS_3.md N24)

The owner chose (2026-10-09) to add real low-protein snacks -- banana, vada,
tea -- each with a published source. UDAY (J Nutr 2023, PMC7616315) lists
"fried snacks (vada, samosa)", "tea/coffee" and "fruits" among the 10 snack
types it asked 8762 adults about. Nothing here is added to the library.

Per 100 g:
  Banana: IFCT 2017 E012 "Banana, ripe, robusta", 6 regions, read 2026-10-09
    from the primary NIN-published IFCT2017.pdf. Table 1 (pdftotext -table
    line for E012): water 71.93, protein 1.23, ash 0.94, fat 0.33, total
    fibre 1.94, available carbohydrate 23.63, energy 440 kJ. Sodium 0.85 mg,
    Table 5 (PDF page 168), placed by column position under (Na) -- the Hg
    and Se cells are blank on this row.
    carb_g = available carb + fibre (25.57), the potato_raw (F006) convention.
  Cow milk: IFCT 2017 L002 "Milk, whole, Cow", 6 regions: water 86.64,
    protein 3.26, ash 0.68, fat 4.48, carbohydrate 4.94, energy 305 kJ.
    Sodium 25.46 mg, Table 5 (PDF page 184), by column position (0.95 sits
    under Se, 25.46 under Na).
  Sugar: IFCT 2017 has no refined sugar (I001 jaggery, I002 cane juice only).
    USDA FDC 169655 "Sugars, granulated" (SR Legacy): 387 kcal, carb 99.98,
    sodium 1 mg.
  Brewed tea: not in IFCT. USDA FDC 173227 "Beverages, tea, black, brewed,
    prepared with tap water": 1 kcal, carb 0.3, sodium 3 mg.
  Banana piece: USDA FDC 173944 portion "medium (7 to 7-7/8 inch long)"
    118 g. That is the American Cavendish; robusta is a Cavendish type.

Assumptions, not sourced: one cup of tea = 70 g milk + 80 g brewed tea + 8 g
sugar (about 2 teaspoons), an authored ordinary proportion. Vada is not run:
no measured fat value for a fried urad dal vada was found (calorie-tracker
sites only, 7-16 g fat per 100 g), and frying oil uptake would need its own
registered constant.

Checked against 18 bodies (3 goals x 2 sexes x 55/70/90 kg, 170 cm, 30 y,
moderate) at the unrelaxed snack target and after each RELAXATION_ORDER step,
cumulatively.

    PYTHONPATH=. python docs/design/probes/probe_banana_tea_snack.py
"""
import collections, logging, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

from core.foods.nutrition_of import nutrition_of_recipe
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.plan import default_library
from core.planner.validator import RELAXATION_ORDER
from core.schemas import DietPattern, MealSlot, Profile
from core.schemas.profile import ActivityLevel, Goal, Sex

KEYS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")
# per 100 g
BANANA = dict(energy_kcal=440 / 4.184, protein_g=1.23, fat_g=0.33, carb_g=23.63 + 1.94,
              fibre_g=1.94, sodium_mg=0.85)                      # IFCT 2017 E012 robusta
MILK = dict(energy_kcal=305 / 4.184, protein_g=3.26, fat_g=4.48, carb_g=4.94,
            fibre_g=0.0, sodium_mg=25.46)                        # IFCT 2017 L002 cow
SUGAR = dict(energy_kcal=387.0, protein_g=0.0, fat_g=0.0, carb_g=99.98,
             fibre_g=0.0, sodium_mg=1.0)                         # USDA FDC 169655
TEA = dict(energy_kcal=1.0, protein_g=0.0, fat_g=0.0, carb_g=0.3,
           fibre_g=0.0, sodium_mg=3.0)                           # USDA FDC 173227


def mix(*parts):
    return {k: sum(src[k] * g / 100 for src, g in parts) for k in KEYS}


def add(*vs):
    return {k: sum(v[k] for v in vs) for k in KEYS}


lib = default_library()
by_id = {c.recipe.id: c.recipe for c in lib.components()}


def recipe(rid, n=1):
    v = nutrition_of_recipe(by_id[rid], n, lib.ingredients)
    return {k: getattr(v, k) for k in KEYS}


banana1 = mix((BANANA, 118))                    # USDA medium banana, 118 g
tea = mix((MILK, 70), (TEA, 80), (SUGAR, 8))    # one cup, authored proportion
plates = {
    "1 banana": banana1,
    "2 bananas": add(banana1, banana1),
    "tea": tea,
    "tea + 1 banana": add(tea, banana1),
    "tea + 2 bananas": add(tea, banana1, banana1),
    "tea + soya_chana_sundal": add(tea, recipe("soya_chana_sundal")),
}


def misses(t, tot):
    out = set()
    for m in t.bounded_macros():
        f, c = t.floor(m), t.ceiling(m)
        if f is not None and tot[m] < f:
            out.add(f"{m} below floor")
        if c is not None and tot[m] > c:
            out.add(f"{m} above ceiling")
    return out


def rungs(t):
    out = [t]
    for step in RELAXATION_ORDER:
        t = step.apply(t, frozenset())
        out.append(t)
    return out


targets = []
for goal in Goal:
    for sex in (Sex.MALE, Sex.FEMALE):
        for w in (55, 70, 90):
            p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                        activity=ActivityLevel.MODERATE, goal=goal, diet=DietPattern("vegetarian"),
                        clinical_flags=frozenset())
            targets.append(rungs(meal_target(derive_target(p).nutrition_target, MealSlot.SNACK)))

e = [(l[0].floor("energy_kcal"), l[0].ceiling("energy_kcal")) for l in targets]
fb = [l[0].floor("fibre_g") for l in targets]
print(f"18 bodies. snack energy window: lowest {min(e)[0]:.0f}-{min(e)[1]:.0f}, highest "
      f"{max(e)[0]:.0f}-{max(e)[1]:.0f} kcal; fibre floor {min(fb):.1f}-{max(fb):.1f} g")
for name, tot in plates.items():
    un = sum(not misses(l[0], tot) for l in targets)
    anyr = sum(any(not misses(t, tot) for t in l) for l in targets)
    why = collections.Counter(b for l in targets for b in misses(l[-1], tot))
    print(f"{name:24s} [{tot['energy_kcal']:4.0f} kcal, prot {tot['protein_g']:4.1f}, fat {tot['fat_g']:4.1f}, "
          f"carb {tot['carb_g']:5.1f}, fibre {tot['fibre_g']:3.1f}, Na {tot['sodium_mg']:5.1f}]  "
          f"unrelaxed {un:2d}/18, some rung {anyr:2d}/18  last-rung misses {dict(sorted(why.items()))}")
cu = [l[0].ceiling("carb_g") for l in targets]; cl = [l[-1].ceiling("carb_g") for l in targets]
ef = [l[-1].floor("energy_kcal") for l in targets]
print(f"carb ceiling unrelaxed {min(cu):.1f}-{max(cu):.1f} g, last rung {min(cl):.1f}-{max(cl):.1f} g")
for l in targets[:18:6]:
    t = l[-1]
    print(f"  e.g. last rung: energy {t.floor('energy_kcal'):.0f}-{t.ceiling('energy_kcal'):.0f} kcal, carb <= {t.ceiling('carb_g'):.1f} g"
          f" -> max carb share of energy at the energy floor {4*t.ceiling('carb_g')/t.floor('energy_kcal'):.0%}")
