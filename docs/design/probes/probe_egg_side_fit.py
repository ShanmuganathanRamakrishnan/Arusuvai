"""Why does the boiled-egg side fit only some snack plates? (TASKS_3.md N21)

N19 measured that asking for `avicha_muttai` beside the South snack's sundal
gives a valid plate for 12 of 36 egg-eating bodies, and did not measure why.

This probe tries every plate the planner itself could build with the egg in
it -- every combination `enumerate_combinations` yields that holds the egg,
at every legal integer serving count -- against the snack target at each rung
of the planner's own `RELAXATION_ORDER`, applied cumulatively, the way the
ladder widens it. A plate fits when every bounded macro is within its floor
and ceiling and quality protein meets its floor (which no rung relaxes).

Cross-check first: the body counts this arithmetic finds must equal what
`plan_meal` returns for the same request. If they disagree, the arithmetic is
not measuring the planner and nothing below it should be read.

For bodies where no plate fits at the last rung, it reports, per bound, on how
many bodies every plate misses it ("blocks every plate") and on how many
lifting that one bound alone would let some plate fit ("the only thing in the
way"). Output is sorted, so it does not depend on the hash seed.

    PYTHONPATH=. python docs/design/probes/probe_egg_side_fit.py
"""
import collections, itertools, logging, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)

from core.foods.nutrition_of import nutrition_of_recipe
from core.foods.quality import quality_protein_of_recipe
from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations
from core.planner.plan import default_library, plan_meal
from core.planner.validator import RELAXATION_ORDER
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex

EGG = "avicha_muttai"
KEYS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")
lib = default_library()


def plates(diet):
    """Every (recipe ids, totals) the planner could serve with the egg in it."""
    pool = build_candidate_pool(lib.components(), lib.ingredients,
                                template=template_for(Region.SOUTH_INDIAN, MealSlot.SNACK),
                                diet_pattern=diet, allergens=frozenset(), dev_mode=True)
    out = []
    for combo in enumerate_combinations(pool):
        recipes = [c.recipe for c in combo.components]
        if EGG not in {r.id for r in recipes}:
            continue
        for counts in itertools.product(*(r.serving_unit.counts() for r in recipes)):
            tot = dict.fromkeys(KEYS, 0.0)
            q = 0.0
            for r, n in zip(recipes, counts):
                v = nutrition_of_recipe(r, n, lib.ingredients)
                for k in KEYS:
                    tot[k] += getattr(v, k)
                q += quality_protein_of_recipe(r, n, lib.ingredients)
            tot["quality"] = q
            out.append((tuple(f"{r.id}x{n}" for r, n in zip(recipes, counts)), tot))
    return out


def misses(t, tot):
    out = set()
    for m in t.bounded_macros():
        f, c = t.floor(m), t.ceiling(m)
        if f is not None and tot[m] < f:
            out.add(f"{m} below floor")
        if c is not None and tot[m] > c:
            out.add(f"{m} above ceiling")
    qf = t.quality_protein_floor()
    if qf is not None and tot["quality"] < qf:
        out.add("quality protein below floor")
    return out


def rungs(t):
    """The target at rung 0 (unrelaxed), then after each step, cumulatively."""
    out = [("unrelaxed", t)]
    for step in RELAXATION_ORDER:
        t = step.apply(t, frozenset())
        out.append((step.name, t))
    return out


first_fit = collections.Counter()
blocks_all = collections.Counter()
only_thing = collections.Counter()
agree = disagree = 0
bodies = []
for name in ("eggetarian", "non_vegetarian"):
    diet = DietPattern(name)
    ps = plates(diet)
    for goal in Goal:
        for sex in (Sex.MALE, Sex.FEMALE):
            for w in (55, 70, 90):
                p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex,
                            activity=ActivityLevel.MODERATE, goal=goal, diet=diet,
                            clinical_flags=frozenset())
                day = derive_target(p).nutrition_target
                ladder = rungs(meal_target(day, MealSlot.SNACK))
                fit_at = next((rn for rn, t in ladder if any(not misses(t, tot) for _, tot in ps)), None)
                asked = plan_meal(lib, day, region=Region.SOUTH_INDIAN, meal_slot=MealSlot.SNACK,
                                  diet_pattern=diet, profile=p, picks=frozenset({EGG}))
                planner_ok = asked.plan is not None and asked.result.passed
                if planner_ok == (fit_at is not None):
                    agree += 1
                else:
                    disagree += 1
                first_fit[fit_at or "no rung"] += 1
                label = f"{name:14s} {goal.value:9s} {sex.value:6s} {w}kg"
                if fit_at is None:
                    last = ladder[-1][1]
                    sets = [misses(last, tot) for _, tot in ps]
                    for b in set().union(*sets):
                        if all(b in s for s in sets):
                            blocks_all[b] += 1
                        if any(s == {b} for s in sets):
                            only_thing[b] += 1
                    near = min(sets, key=lambda s: (len(s), sorted(s)))
                    bodies.append(f"{label}  no plate fits; nearest plate misses: {sorted(near)}")
                else:
                    bodies.append(f"{label}  fits at rung: {fit_at}")

print(f"plates with the egg: eggetarian {len(plates(DietPattern('eggetarian')))}, "
      f"non_vegetarian {len(plates(DietPattern('non_vegetarian')))}")
print(f"cross-check against plan_meal: {agree} agree, {disagree} disagree")
print("first rung at which some egg plate fits:")
for rn in [r for r, _ in rungs(meal_target(derive_target(p).nutrition_target, MealSlot.SNACK))] + ["no rung"]:
    print(f"  {rn:22s} {first_fit[rn]}")
print("bodies with no fitting plate, per bound:")
for b in sorted(set(blocks_all) | set(only_thing)):
    print(f"  {b:30s} blocks every plate on {blocks_all[b]:2d}   the only thing in the way on {only_thing[b]:2d}")
print("per body:")
for line in bodies:
    print("  " + line)

print("one serving of each dish on these plates (fat share = fat kcal / all kcal):")
for rid in ("avicha_muttai", "neer_mor", "soya_chana_sundal", "soya_chunk_sundal"):
    r = next(c.recipe for c in lib.components() if c.recipe.id == rid)
    v = nutrition_of_recipe(r, 1, lib.ingredients)
    print(f"  {rid:18s} 1 {r.serving_unit.name:14s} (allowed {r.serving_unit.min_count}-{r.serving_unit.max_count})"
          f"  {v.energy_kcal:5.1f} kcal  fat {v.fat_g:4.2f} g  fat share {9 * v.fat_g / v.energy_kcal:.2f}")

ps = plates(DietPattern("eggetarian"))
for goal, sex, w in ((Goal.MAINTAIN, Sex.MALE, 55), (Goal.MAINTAIN, Sex.MALE, 70)):
    p = Profile(weight_kg=w, height_cm=170, age_years=30, sex=sex, activity=ActivityLevel.MODERATE,
                goal=goal, diet=DietPattern("eggetarian"), clinical_flags=frozenset())
    t = meal_target(derive_target(p).nutrition_target, MealSlot.SNACK)
    print(f"eggetarian {goal.value} {sex.value} {w}kg, unrelaxed: energy {t.floor('energy_kcal'):.0f}-"
          f"{t.ceiling('energy_kcal'):.0f} kcal, fat <= {t.ceiling('fat_g'):.1f} g; egg plates missing at most one bound:")
    for ids, tot in sorted(ps, key=lambda x: (x[1]["energy_kcal"], x[0])):
        m = misses(t, tot)
        if len(m) <= 1:
            print(f"  {tot['energy_kcal']:4.0f} kcal  fat {tot['fat_g']:4.1f}  {' + '.join(ids):52s} {sorted(m)[0] if m else 'FITS'}")
