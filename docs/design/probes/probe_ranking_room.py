"""Is there anything for an AI ranking step to choose between? (TASKS_3.md N12)

Architecture step 5 (docs/design/architecture.md): an LLM ranks plates that
are already valid, for how good they are to eat. That only matters if a meal
usually has several valid plates that differ in their dishes. Today the
planner shows the plate nearest the target (an animal-protein plate first,
where the diet permits one).

Per body and meal, real library, the same call the API makes: records the
valid plates at the rung the ladder stopped on (the last `solve` call is that
rung -- the ladder stops on the first non-empty one). Reports how many there
are, how many different dishes they use, and how many of the 10 nearest
differ from the shown plate in two or more dishes. Then lists the 5 nearest
for two meals so a person can judge whether the order reads as food.

    PYTHONPATH=. python docs/design/probes/probe_ranking_room.py
"""
import collections, statistics, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

import core.planner.validator as validator
from core.nutrition.targets import derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex

last = {}
_solve = validator.solve


def spy(*a, **k):
    out = _solve(*a, **k)
    last["solved"] = out
    return out


validator.solve = spy
lib = default_library()
MEALS = [(r, s) for r in (Region.SOUTH_INDIAN, Region.NORTH_INDIAN)
         for s in (MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER, MealSlot.SNACK)]


def run(diet, w, region, slot):
    p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=Sex.MALE, activity=ActivityLevel.MODERATE,
                goal=Goal.MAINTAIN, diet=DietPattern(diet), clinical_flags=frozenset())
    last.clear()
    out = plan_meal(lib, derive_target(p).nutrition_target, region=region, meal_slot=slot,
                    diet_pattern=DietPattern(diet), profile=p, dev_mode=True)
    return out, last.get("solved", ())


rows = collections.defaultdict(list)
for diet in ("vegetarian", "eggetarian", "non_vegetarian", "vegan"):
    for w in (55, 70, 90):
        for region, slot in MEALS:
            out, solved = run(diet, w, region, slot)
            key = f"{region.value.split('_')[0]} {slot.value}"
            if out.plan is None:
                rows[key].append(None)
                continue
            shown = out.plan.combination.recipe_ids()
            dishes = set().union(*(s.combination.recipe_ids() for s in solved))
            differ = sum(1 for s in solved[:10] if len(s.combination.recipe_ids() - shown) >= 2)
            rows[key].append((len(solved), len(dishes), differ))

print(f"{'meal':16s} bodies declined | valid plates min/median/max | different dishes median | "
      f"of nearest 10, differ from shown by 2+ dishes: median | bodies with only 1 plate")
for key, vals in rows.items():
    ok = [v for v in vals if v]
    if not ok:
        print(f"{key:16s} {len(vals):6d} {len(vals):8d} | all declined")
        continue
    n = [v[0] for v in ok]
    print(f"{key:16s} {len(vals):6d} {len(vals) - len(ok):8d} | {min(n):5d} {statistics.median(n):6.0f} {max(n):5d}"
          f"            | {statistics.median(v[1] for v in ok):6.0f}                  "
          f"| {statistics.median(v[2] for v in ok):6.0f}                                            "
          f"| {sum(1 for x in n if x == 1):3d}")

for diet, region, slot in (("vegetarian", Region.SOUTH_INDIAN, MealSlot.LUNCH),
                           ("non_vegetarian", Region.NORTH_INDIAN, MealSlot.DINNER)):
    out, solved = run(diet, 70, region, slot)
    if out.plan is None:
        print(f"\n{diet} 70 kg {region.value} {slot.value}: declined")
        continue
    names = lambda comb: ", ".join(sorted(c.recipe.name for c in comb.components))
    print(f"\n{diet} 70 kg {region.value} {slot.value}: {len(solved)} valid plates")
    print(f"   shown: {names(out.plan.combination)}")
    for i, s in enumerate(solved[:5], 1):
        print(f"   {i}. {names(s.combination)}")
