"""South snack with an on-request egg side. (TASKS_3.md N19)

Per diet, over 18 bodies (3 goals x 2 sexes x 3 weights): profiles with a
plate; shown plates holding an egg (expected 0 after N19: the course waits to
be asked for); and, for egg-eating diets, how many bodies get a valid plate
when they ask for each egg dish. Reads only `plan_meal`'s public outcome and
`Component.category`, so it runs on the tree before N19 too (where asking
for an egg means the egg takes the sundal's place).

    PYTHONPATH=. python docs/design/probes/probe_snack_egg_side.py
"""
import collections, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

from core.nutrition.targets import derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex

EGGS = ("avicha_muttai", "muttai_omelette", "muttai_podimas")
lib = default_library()


def run(diet, p, picks=frozenset()):
    return plan_meal(lib, derive_target(p).nutrition_target, region=Region.SOUTH_INDIAN,
                     meal_slot=MealSlot.SNACK, diet_pattern=diet, profile=p, picks=picks)


for name in ("vegetarian", "eggetarian", "non_vegetarian", "vegan"):
    diet = DietPattern(name)
    t = collections.Counter()
    for goal in Goal:
        for sex in (Sex.MALE, Sex.FEMALE):
            for w in (55, 70, 90):
                p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                            activity=ActivityLevel.MODERATE, goal=goal, diet=diet,
                            clinical_flags=frozenset())
                out = run(diet, p)
                t["bodies"] += 1
                if out.plan is not None:
                    t["with a plate"] += 1
                    t["shown egg"] += any(c.category == "egg" for c in out.plan.combination.components)
                if name in ("eggetarian", "non_vegetarian"):
                    for egg in EGGS:
                        asked = run(diet, p, frozenset({egg}))
                        t[f"asked {egg}: passes"] += asked.plan is not None and asked.result.passed
    print(f"{name:15s} {dict(t)}")
