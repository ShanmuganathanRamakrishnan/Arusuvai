"""Does dropping an added dish's pick take that course off the plate? (docs/audit_log.md 2026-09-30)

The cheap "Remove" for a dish the user added (N9) is to drop its pick and ask
again. That only works if the planner then leaves the course empty. Flow per
case, real library via TestClient: suggested plate; add a dish to an empty
optional course; optionally swap one other dish; then drop the added dish's
pick. Counts how often the course is filled again anyway.

    PYTHONPATH=. python docs/design/probes/probe_remove_added_dish.py
"""
import itertools, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
from fastapi.testclient import TestClient
from api.main import app
c=TestClient(app)
def plan(b,picks): return c.post("/api/plan",json=dict(b,picks=sorted(picks))).json()
flows=comes_back=0; examples=[]
for diet in ("vegetarian","eggetarian","non_vegetarian","vegan"):
  for w in (55,70,90):
    for reg,meal in (("south_indian","breakfast"),("south_indian","lunch"),("south_indian","snack"),("north_indian","lunch"),("north_indian","dinner"),("north_indian","breakfast")):
      b=dict(weight_kg=w,height_cm=170,age_years=30,sex="male",activity="moderate",goal="maintain",diet=diet,clinical_flags=[],region=reg,meal_slot=meal)
      try: s=plan(b,[])
      except Exception: continue
      if not s.get("passed"): continue
      shown={x["slot"] for x in s["components"]}
      for so in s["swap_options"]:
        if so["slot"] in shown: continue
        for o in so["options"]:
          d=o["recipe_id"]; p1=plan(b,{d})
          if not p1["passed"]: continue
          # user then swaps something else, then removes the added dish
          seconds=[(x["slot"],e["recipe_id"]) for x in p1["swap_options"] if x["slot"]!=so["slot"] for e in x["options"]
                   if e["recipe_id"] not in {y["recipe_id"] for y in p1["components"]}]
          for slot2,e in [(None,None)]+seconds:
            picks={d}|({e} if e else set())
            if e and not plan(b,picks)["passed"]: continue
            after=plan(b,picks-{d})
            flows+=1
            back=[x["recipe_name"] for x in after.get("components",[]) if x["slot"]==so["slot"]]
            if back:
              comes_back+=1
              if len(examples)<6: examples.append((diet,w,reg,meal,"added",d,"other pick",e,"after remove:",back))
print("remove flows:",flows,"course comes back:",comes_back)
for x in examples: print(" ",x)
