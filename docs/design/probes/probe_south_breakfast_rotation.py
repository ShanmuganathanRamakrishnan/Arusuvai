"""TASKS_3.md N7 step 4: what a carb rotation would give at South breakfast.

Nothing in the app rotates dishes today: `combinations_excluding_recent`
exists but no app path calls it. This asks what it would give if one did.
Read-only.

    PYTHONPATH=. python docs/design/probes/probe_south_breakfast_rotation.py
"""
# Day 1: the planner's own pick. Each later day: same planner, with plates
# whose tiffin was eaten in the previous 2 days removed (only the tiffin is
# rotated; chutney, gravy and egg may repeat). 7 days per body.
import logging, runpy; logging.disable(logging.WARNING)
from collections import Counter
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.validator import plan_within_ladder
from core.schemas import *
base = runpy.run_path("docs/design/probes/probe_rank_input2.py", run_name="z")
nonveg = runpy.run_path("docs/design/probes/probe_nonveg.py", run_name="x")
lib = base["lib"]; combos_for = base["_combinations_for"]
R, M, DAYS, WINDOW = Region.SOUTH_INDIAN, MealSlot.BREAKFAST, 7, 2
cat = lambda rid: lib.recipes.components[rid].category
for diet in (DietPattern.VEGETARIAN, DietPattern.EGGETARIAN):
    distinct = Counter(); declined_days = 0; bodies = 0; used = Counter(); stuck = 0
    for w, g, f in nonveg["bodies"]():
        p = Profile(weight_kg=w, height_cm=175.0, age_years=28, sex=Sex.MALE,
                    activity=ActivityLevel.MODERATE, goal=g, diet=diet, clinical_flags=f)
        combos = combos_for(p, R, M)
        tgt = meal_target(derive_target(p).nutrition_target, M, ledger=None)
        first = plan_within_ladder(combos, tgt, lib.ingredients, profile=p)
        if first.plan is None: continue
        bodies += 1; hist = []
        for day in range(DAYS):
            recent = set(hist[-WINDOW:]) if day else set()
            pool = [c for c in combos if not (c.recipe_ids() & recent)]
            out = plan_within_ladder(pool, tgt, lib.ingredients, profile=p) if pool else None
            if out is None or out.plan is None:
                declined_days += 1; hist.append(None); continue
            t = [c.recipe.id for c in out.plan.combination.components if cat(c.recipe.id) == "tiffin"]
            hist.append(t[0] if t else None); used.update(t)
        k = len({h for h in hist if h}); distinct[k] += 1
    print(f"{diet.value:12s} bodies {bodies}  distinct carbs in {DAYS} days {dict(sorted(distinct.items()))}"
          f"  declined days {declined_days}/{bodies*DAYS}  carb-days {dict(used.most_common())}")
