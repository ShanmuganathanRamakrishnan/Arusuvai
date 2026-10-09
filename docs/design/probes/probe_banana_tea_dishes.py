"""Which snack plates change when banana and tea join the library? (TASKS_3.md N26)

Reads only what exists before and after N26 -- `plan_meal`'s outcome (plan,
result.passed, result.relaxation_applied, swap_options) and the library's
recipe ids -- so it runs on both trees. Per region snack x diet, over 18 bodies
(3 goals x 2 sexes x 55/70/90 kg, 170 cm, 30 y, moderate):

  plate       -- bodies given a passing plate
  unrelaxed   -- of those, how many passed with no relaxation step applied
  options     -- distinct dishes offered across all swap menus, summed over bodies
  banana / tea in shown -- shown plates that contain the dish
  banana asked / tea asked -- bodies whose plate passes when they pick the
                 dish ("not in library" before N26)
  shown       -- the shown plates' dishes, counted over the bodies

Output is sorted, so it does not depend on the hash seed.

    PYTHONPATH=. python docs/design/probes/probe_banana_tea_dishes.py
"""
import collections, logging, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

from core.nutrition.targets import derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex

lib = default_library()
ids = {c.recipe.id for c in lib.components()}
NEW = ("banana", "milk_tea")

for region in (Region.SOUTH_INDIAN, Region.NORTH_INDIAN):
    for name in ("vegetarian", "eggetarian", "non_vegetarian", "vegan"):
        diet = DietPattern(name)
        t = collections.Counter()
        shown = collections.Counter()
        for goal in Goal:
            for sex in (Sex.MALE, Sex.FEMALE):
                for w in (55, 70, 90):
                    p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                                activity=ActivityLevel.MODERATE, goal=goal, diet=diet,
                                clinical_flags=frozenset())
                    day = derive_target(p).nutrition_target
                    out = plan_meal(lib, day, region=region, meal_slot=MealSlot.SNACK,
                                    diet_pattern=diet, profile=p)
                    if out.plan is not None and out.result.passed:
                        t["plate"] += 1
                        t["unrelaxed"] += not out.result.relaxation_applied
                        dishes = sorted(c.recipe.id for c in out.plan.combination.components)
                        shown[" + ".join(dishes)] += 1
                        t["options"] += len({r for _, rs in out.swap_options for r in rs})
                        for d in NEW:
                            t[f"{d} in shown"] += d in dishes
                    for d in NEW:
                        if d not in ids:
                            continue
                        asked = plan_meal(lib, day, region=region, meal_slot=MealSlot.SNACK,
                                          diet_pattern=diet, profile=p, picks=frozenset({d}))
                        t[f"{d} asked"] += asked.plan is not None and asked.result.passed
        cells = [f"{k} {t[k]}" for k in ("plate", "unrelaxed", "options")]
        cells += [f"{d} in shown {t[d + ' in shown']}" for d in NEW]
        cells += [f"{d} asked {t[d + ' asked'] if d in ids else 'not in library'}" for d in NEW]
        print(f"{region.value:13s} {name:15s} " + ", ".join(cells))
        for plate, n in sorted(shown.items()):
            print(f"    shown {n:2d}x  {plate}")
