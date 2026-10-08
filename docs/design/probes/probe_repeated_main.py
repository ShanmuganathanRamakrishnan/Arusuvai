"""How often does the shown plate serve one main ingredient twice? (TASKS_3.md N14)

Same 96 body x meal cases as probe_ranking_room.py, the call the API makes.
For each, the plate shown today and the valid plates at the rung the ladder
stopped on. A plate's repeats: for each main ingredient, the number of dishes
carrying it beyond the first. Counts how many shown plates repeat one, which
ingredient, and how many of those have a valid plate with fewer repeats that
keeps the planner's existing animal-protein preference (an animal-protein
plate stays an animal-protein plate).

Reads only fields present before and after N14's planner change, so it can
be run on both trees.

    PYTHONPATH=. python docs/design/probes/probe_repeated_main.py
"""
import collections, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

import core.planner.validator as validator
from core.nutrition.targets import derive_target
from core.planner.plan import _animal_protein_preference, default_library, plan_meal
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


def repeats(plan):
    c = collections.Counter(m for comp in plan.combination.components for m in comp.recipe.main_ingredients)
    return {m: n - 1 for m, n in c.items() if n > 1}


cases = repeating = fixable = 0
which = collections.Counter(); examples = []
for diet in ("vegetarian", "eggetarian", "non_vegetarian", "vegan"):
    for w in (55, 70, 90):
        for region in (Region.SOUTH_INDIAN, Region.NORTH_INDIAN):
            for slot in (MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER, MealSlot.SNACK):
                d = DietPattern(diet)
                p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=Sex.MALE,
                            activity=ActivityLevel.MODERATE, goal=Goal.MAINTAIN, diet=d,
                            clinical_flags=frozenset())
                last.clear()
                out = plan_meal(lib, derive_target(p).nutrition_target, region=region,
                                meal_slot=slot, diet_pattern=d, profile=p)
                if out.plan is None:
                    continue
                cases += 1
                shown = repeats(out.plan)
                if not shown:
                    continue
                repeating += 1
                which.update(shown.keys())
                prefer = _animal_protein_preference(d, lib.ingredients)
                keep = prefer(out.plan) if prefer else False
                pool = [s for s in last["solved"] if not keep or prefer(s)]
                best = min(pool, key=lambda s: sum(repeats(s).values()))
                if sum(repeats(best).values()) < sum(shown.values()):
                    fixable += 1
                    if len(examples) < 8:
                        names = lambda pl: ", ".join(c.recipe.name for c in pl.combination.components)
                        examples.append((f"{diet} {w} {region.value} {slot.value}", names(out.plan), names(best)))

print(f"plates shown {cases}; repeat a main ingredient {repeating}; "
      f"of those, a valid plate with fewer repeats exists {fixable}")
print("repeated ingredient on shown plates:", dict(which.most_common()))
for case, a, b in examples:
    print(f"  {case}\n     shown : {a}\n     fewer : {b}")
