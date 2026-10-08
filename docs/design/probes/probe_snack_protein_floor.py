"""What changes when a snack has no protein or quality-protein floor? (TASKS_3.md N23)

Reads only fields that exist before and after N23, so it runs on both trees:
`meal_target(...)` floor("protein_g") and quality_protein_floor(), and
`plan_meal`'s outcome (plan, result.passed, result.relaxation_applied,
swap_options). Per region snack x diet, over 18 bodies (3 goals x 2 sexes x
55/70/90 kg, 170 cm, 30 y, moderate):

  bodies      -- profiles tried
  floors      -- snack protein floor and quality floor, min-max over the bodies
                 ("none" when absent)
  plate       -- bodies given a passing plate
  unrelaxed   -- of those, how many passed with no relaxation step applied
  options     -- distinct dishes offered across all swap menus, summed over bodies
  egg asked   -- South only, egg-eating diets: bodies whose plate passes when
                 they ask for the boiled egg (avicha_muttai)
  shown       -- the shown plates' dishes, counted over the bodies

Output is sorted, so it does not depend on the hash seed.

    PYTHONPATH=. python docs/design/probes/probe_snack_protein_floor.py
"""
import collections, logging, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex

lib = default_library()


def span(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "none"
    return f"{min(xs):.1f}-{max(xs):.1f}"


for region in (Region.SOUTH_INDIAN, Region.NORTH_INDIAN):
    for name in ("vegetarian", "eggetarian", "non_vegetarian", "vegan"):
        diet = DietPattern(name)
        t = collections.Counter()
        shown = collections.Counter()
        pf, qf = [], []
        for goal in Goal:
            for sex in (Sex.MALE, Sex.FEMALE):
                for w in (55, 70, 90):
                    p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                                activity=ActivityLevel.MODERATE, goal=goal, diet=diet,
                                clinical_flags=frozenset())
                    day = derive_target(p).nutrition_target
                    mt = meal_target(day, MealSlot.SNACK)
                    pf.append(mt.floor("protein_g"))
                    qf.append(mt.quality_protein_floor())
                    out = plan_meal(lib, day, region=region, meal_slot=MealSlot.SNACK,
                                    diet_pattern=diet, profile=p)
                    t["bodies"] += 1
                    if out.plan is not None and out.result.passed:
                        t["plate"] += 1
                        t["unrelaxed"] += not out.result.relaxation_applied
                        shown[" + ".join(sorted(c.recipe.id for c in out.plan.combination.components))] += 1
                        t["options"] += len({r for _, rs in out.swap_options for r in rs})
                    if region is Region.SOUTH_INDIAN and name in ("eggetarian", "non_vegetarian"):
                        asked = plan_meal(lib, day, region=region, meal_slot=MealSlot.SNACK,
                                          diet_pattern=diet, profile=p,
                                          picks=frozenset({"avicha_muttai"}))
                        t["egg asked"] += asked.plan is not None and asked.result.passed
        keys = ["bodies", "plate", "unrelaxed", "options"] + (["egg asked"] if "egg asked" in t else [])
        print(f"{region.value:13s} {name:15s} protein floor {span(pf)}, quality floor {span(qf)}; "
              + ", ".join(f"{k} {t[k]}" for k in keys))
        for plate, n in sorted(shown.items()):
            print(f"    shown {n:2d}x  {plate}")
