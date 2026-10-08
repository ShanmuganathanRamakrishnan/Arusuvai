"""What the live model does with real plates. (TASKS_3.md N13)

Same 96 body x meal cases as probe_ranking_room.py. Per case, the plates the
ranker would be offered (the nearest 8 valid plates at the stopping rung,
animal-protein plates only where the diet permits one and one exists), and
what the model answers: which plate, how long it took. Writes one line per
case to the file named on the command line, so two runs -- one either side
of an Ollama restart -- can be compared for the same answers (determinism
across a process, not within one: CLAUDE.md, finding 18).

    PYTHONPATH=. python docs/design/probes/probe_ranker_live.py OUT.json
"""
import json, statistics, sys, time, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

import core.planner.validator as validator
from core.nutrition.targets import derive_target
from core.planner.plan import _animal_protein_preference, default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex
from llm.ranker import DEFAULT_MODEL, DEFAULT_URL, _ask

last = {}
_solve = validator.solve


def spy(*a, **k):
    out = _solve(*a, **k)
    last["solved"] = out
    return out


validator.solve = spy
lib = default_library()
cases = []
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
                solved = last["solved"]
                prefer = _animal_protein_preference(d, lib.ingredients)
                pool = [s for s in solved if prefer(s)] if prefer else []
                pool = (pool or list(solved))[:8]
                if len(pool) < 2:
                    continue
                plates = tuple(tuple(c.recipe.name for c in s.combination.components) for s in pool)
                t = time.perf_counter()
                choice = _ask(DEFAULT_URL, DEFAULT_MODEL, region.value, slot.value, plates)
                cases.append(dict(case=f"{diet} {w} {region.value} {slot.value}", n=len(plates),
                                  choice=choice, seconds=round(time.perf_counter() - t, 2),
                                  plates=plates))
                print(f"{cases[-1]['case']:40s} n={len(plates)} choice={choice} {cases[-1]['seconds']}s", flush=True)

json.dump(cases, open(sys.argv[1], "w"), indent=1)
secs = [c["seconds"] for c in cases]
print(f"\ncases {len(cases)}  no answer {sum(c['choice'] is None for c in cases)}  "
      f"chose the nearest (A) {sum(c['choice'] == 0 for c in cases)}  "
      f"seconds: first {secs[0]}, median {statistics.median(secs)}, max after first {max(secs[1:])}")
