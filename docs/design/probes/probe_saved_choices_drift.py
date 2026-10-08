"""Do a user's saved dish choices still fit after their body changes? (TASKS_3.md N11)

Saving favourites means replaying today's picks and removals on a later visit.
The planner never loosens a limit to fit a choice, so a saved choice that no
longer fits is a decline. This counts how often that happens, to decide how
much the page's "your saved choices no longer fit" path matters.

Sampled (two weights, every removal, first three swaps per plate) so it runs
in minutes. Flow per case, real library via TestClient: suggested plate at weight w; make
one choice (swap a dish, add a dish, or remove one) that gives a valid plate;
then replay exactly that choice at w - 5 and w + 5 kg and at the other goals,
which are the profile edits a returning user is likeliest to make.

    PYTHONPATH=. python docs/design/probes/probe_saved_choices_drift.py
"""
import collections, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
from fastapi.testclient import TestClient
from api.main import app
c = TestClient(app)


def plan(b, picks=(), leave_empty=()):
    return c.post("/api/plan", json=dict(b, picks=sorted(picks), leave_empty=sorted(leave_empty))).json()


replays = collections.Counter(); fails = collections.Counter(); examples = []
for diet in ("vegetarian", "eggetarian", "non_vegetarian", "vegan"):
    for w in (55, 90):
        for reg, meal in (("south_indian", "breakfast"), ("south_indian", "lunch"), ("south_indian", "snack"),
                          ("north_indian", "lunch"), ("north_indian", "dinner"), ("north_indian", "breakfast")):
            b = dict(weight_kg=w, height_cm=170, age_years=30, sex="male", activity="moderate", goal="maintain",
                     diet=diet, clinical_flags=[], region=reg, meal_slot=meal)
            s = plan(b)
            if not s.get("passed"):
                continue
            shown = {x["recipe_id"] for x in s["components"]}
            choices = []
            for so in s["swap_options"]:
                for o in so["options"]:
                    if o["recipe_id"] not in shown:
                        choices.append(("pick", (o["recipe_id"],), ()))
                if so["can_be_empty"] and any(x["slot"] == so["slot"] for x in s["components"]):
                    choices.append(("remove", (), (so["slot"],)))
            # A sample, not every option: every removal, and the first three
            # swaps per plate. The full sweep ran past ten minutes.
            choices = [x for x in choices if x[0] == "remove"] + [x for x in choices if x[0] == "pick"][:3]
            for kind, picks, empty in choices:
                if not plan(b, picks, empty)["passed"]:
                    continue
                edits = [("weight -5", dict(b, weight_kg=w - 5)), ("weight +5", dict(b, weight_kg=w + 5))]
                edits += [(f"goal {g}", dict(b, goal=g)) for g in ("lose_fat", "gain_muscle")]
                for edit, b2 in edits:
                    if not plan(b2).get("passed"):
                        continue  # the meal itself declines; not about the saved choice
                    replays[(kind, edit)] += 1
                    if not plan(b2, picks, empty)["passed"]:
                        fails[(kind, edit)] += 1
                        if len(examples) < 6:
                            examples.append((diet, w, reg, meal, kind, picks or empty, edit))

print(f"{'choice':8s} {'profile edit':12s} replays  no longer fit")
for key in sorted(replays):
    print(f"{key[0]:8s} {key[1]:12s} {replays[key]:7d}  {fails[key]:5d} ({100 * fails[key] / replays[key]:.0f}%)")
t, f = sum(replays.values()), sum(fails.values())
print(f"total    {'':12s} {t:7d}  {f:5d} ({100 * f / t:.0f}%)")
for x in examples:
    print(" ", x)
