"""D4: what a decline says, against what is actually true.

Finding 24 and its mirror. A decline names a blocking constraint; this probe
asks whether the constraint it names is the one that is actually blocking.

It sweeps a profile grid against all four real templates, keeps the declines,
and for each one prints three things side by side:

  SAYS        the disclosure the user would be shown today
  UNREACHABLE the bounds no legal assignment of any enumerated combination can
              satisfy, computed independently here from each component's
              min/max serving-unit contribution
  NEAREST     the bounds missed by the combination that comes closest to
              feasible, counted by number of bounds broken -- not by the
              solver's deviation score, which ranks closeness to the ideal
              POINT and is silent on sodium and fibre entirely (neither has a
              registered point), so the "best" plate by score can be the
              saltiest one on the table.

The gap between SAYS and the other two columns is the finding.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py
"""
from __future__ import annotations

import itertools

from core.foods.quality import QUALITY_PROTEIN_KEY
from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.target import NutritionTarget
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import (
    enumerate_combinations,
    macro_bounds,
    quality_protein_bounds,
)
from core.planner.plan import load_library, plan_meal
from core.planner.solver import solve
from core.schemas import (
    ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Profile, Region, Sex,
)

TEMPLATES = (
    (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
    (Region.SOUTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.LUNCH),
    (Region.NORTH_INDIAN, MealSlot.DINNER),
)

MACROS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g", "sodium_mg")

lib = load_library()


def profiles():
    """A grid chosen to straddle the passing reference profile on every axis
    that can produce a decline.

    Weight and goal move the energy and protein targets in opposite directions.
    Diet matters because `soya_chunks_dry` is the library's only vegan source
    clearing the DIAAS threshold via a curry, and paneer/curd are the north and
    south quality sources -- so VEGAN is the axis that makes a quality floor
    structurally unreachable rather than merely hard. Clinical flags are
    included because a locked bound is the one case where "we did not try"
    rather than "we tried and failed" is the honest decline.
    """

    diets = (DietPattern.VEGETARIAN, DietPattern.VEGAN)
    flag_sets = (
        frozenset(),
        frozenset({ClinicalFlag.HYPERTENSION}),
        frozenset({ClinicalFlag.CHRONIC_KIDNEY_DISEASE}),
        frozenset({ClinicalFlag.DIABETES}),
    )
    for weight in (45.0, 55.0, 70.0, 85.0, 95.0, 110.0):
        for goal in (Goal.LOSE_FAT, Goal.MAINTAIN, Goal.GAIN_MUSCLE):
            for diet in diets:
                for flags in flag_sets:
                    yield Profile(
                        weight_kg=weight, height_cm=175.0, age_years=28,
                        sex=Sex.MALE, activity=ActivityLevel.MODERATE, goal=goal,
                        diet=diet, clinical_flags=flags,
                    )


def combos_for(profile, region, slot):
    pool = build_candidate_pool(
        lib.components(), lib.ingredients,
        template=template_for(region, slot),
        diet_pattern=profile.diet, dev_mode=True,
    )
    return enumerate_combinations(pool)


def unreachable_bounds(combinations, target):
    """Bounds no legal assignment of any combination can satisfy.

    Deliberately a second, independent implementation of the same arithmetic
    `core/planner/validator.py::_reach` performs, so this probe is not simply
    agreeing with the code it is auditing.
    """

    out = []
    qfloor = target.quality_protein_floor()
    if qfloor is not None:
        best = max(
            sum(quality_protein_bounds(c, lib.ingredients)[1] for c in combo.components)
            for combo in combinations
        )
        if best < qfloor:
            out.append(f"quality floor ({best:.1f} reachable vs {qfloor:.1f})")
    for macro in MACROS:
        floor, ceiling = target.floor(macro), target.ceiling(macro)
        lows, highs = [], []
        for combo in combinations:
            lows.append(sum(macro_bounds(c, macro, lib.ingredients)[0]
                            for c in combo.components))
            highs.append(sum(macro_bounds(c, macro, lib.ingredients)[1]
                             for c in combo.components))
        if floor is not None and max(highs) < floor:
            out.append(f"{macro} floor ({max(highs):.1f} reachable vs {floor:.1f})")
        if ceiling is not None and min(lows) > ceiling:
            out.append(f"{macro} ceiling ({min(lows):.1f} reachable vs {ceiling:.1f})")
    return out


def nearest_plate(combinations, target):
    """The combination breaking the fewest bounds, and which bounds those are."""

    best = None
    for combo in combinations:
        solved = solve((combo,), NutritionTarget(points=target.points), lib.ingredients)
        if not solved:
            continue
        plan = solved[0]
        point = plan.estimate.point
        broken = []
        qfloor = target.quality_protein_floor()
        if qfloor is not None and plan.quality_protein_g < qfloor:
            broken.append(f"quality floor (by {qfloor - plan.quality_protein_g:.1f})")
        for macro in MACROS:
            value = getattr(point, macro)
            floor, ceiling = target.floor(macro), target.ceiling(macro)
            if floor is not None and value < floor:
                broken.append(f"{macro} floor (by {floor - value:.1f})")
            if ceiling is not None and value > ceiling:
                broken.append(f"{macro} ceiling (by {value - ceiling:.1f})")
        key = (len(broken), plan.score)
        if best is None or key < best[0]:
            best = (key, broken, plan)
    return best


def _names(texts):
    """Bound labels reduced to the macro (or "quality") they are about."""

    out = set()
    for text in texts:
        out.add("quality" if text.startswith("quality") else text.split(" ")[0])
    return out


def main() -> None:
    declines = 0
    omits = 0
    over_names = 0
    empty_pool = 0
    seen: dict[tuple, tuple] = {}
    for profile in profiles():
        day = derive_target(profile).nutrition_target
        for region, slot in TEMPLATES:
            outcome = plan_meal(lib, day, region=region, meal_slot=slot,
                                diet_pattern=profile.diet, profile=profile,
                                dev_mode=True)
            if outcome.plan is not None:
                continue
            declines += 1
            combinations = combos_for(profile, region, slot)
            used = outcome.target_used
            unreach = unreachable_bounds(combinations, used) if combinations else []
            near = nearest_plate(combinations, used) if combinations else None

            # An empty pool is its own bucket, not an over-naming: there is no
            # plate to compare a named bound against. It is still a decline that
            # does not say why -- which required slot went empty -- so it is
            # counted and reported separately rather than folded in either way.
            if not combinations:
                # `getattr`, not `v.blocking_slots`: this probe must run against
                # BOTH the pre-D4a and post-D4a trees to produce a delta, and
                # `Violation.blocking_slots` does not exist before D4a. Reading
                # it directly made the before-column unmeasurable -- the numbers
                # were real when taken, but nobody could take them again, which
                # is the same unverifiable-claim failure the process rule in
                # CLAUDE.md exists to prevent. Every other field this probe
                # touches is present in both trees (checked, not assumed).
                named_slots = tuple(
                    s for v in outcome.result.violations
                    for s in getattr(v, "blocking_slots", ())
                )
                if not named_slots:
                    empty_pool += 1
                said = {f"(empty pool: {list(named_slots) or 'no slot named'})"}
                truth, omitted, extra = set(), [], []
            else:
                said = _names(
                    "quality" if v.macro == QUALITY_PROTEIN_KEY else v.macro
                    for v in outcome.result.violations
                )
                truth = _names(unreach) | (_names(near[1]) if near else set())
                omitted = sorted(truth - said)
                extra = sorted(said - truth)
                if omitted:
                    omits += 1
                if extra:
                    over_names += 1

            # One printed block per distinct shape, not per profile: the grid
            # produces the same three or four situations many times over, and a
            # transcript nobody reads to the end is no evidence at all.
            key = (region, slot, tuple(sorted(truth)), tuple(sorted(said)),
                   bool(profile.clinical_flags))
            if key in seen:
                seen[key] = (seen[key][0] + 1, seen[key][1])
                continue
            seen[key] = (1, profile)

            print("=" * 100)
            print(f"{profile.weight_kg:g}kg {profile.goal.value} {profile.diet.value} "
                  f"flags={sorted(f.value for f in profile.clinical_flags) or 'none'} "
                  f"| {region.value}/{slot.value} | {len(combinations)} combos | "
                  f"rungs={len(outcome.result.relaxation_applied)}")
            print(f"  SAYS        : {outcome.result.disclosure}")
            print(f"  UNREACHABLE : {unreach or '(none -- every bound reachable alone)'}")
            if near is None:
                print("  NEAREST     : (no combination produced a plate)")
            else:
                (count, score), broken, plan = near
                print(f"  NEAREST     : breaks {count} bound(s): {broken}")
                print(f"                {dict(sorted(plan.unit_counts.items()))}")
            verdict = []
            if omitted:
                verdict.append(f"OMITS {omitted}")
            if extra:
                verdict.append(f"NAMES-AS-BLOCKING-BUT-ISN'T {extra}")
            print(f"  VERDICT     : {'; '.join(verdict) or 'accurate'}")

    print("=" * 100)
    print(f"{declines} declines across the grid, {len(seen)} distinct shapes.")
    print(f"  {empty_pool} decline with an empty pool, naming no slot")
    print(f"  {omits} omit a cause that is actually blocking")
    print(f"  {over_names} name a bound as blocking that the nearest plate meets")
    for key, (count, profile) in sorted(seen.items(), key=lambda kv: -kv[1][0]):
        region, slot, truth, said, flagged = key
        print(f"  x{count:<4} {region.value}/{slot.value:9s} "
              f"truth={list(truth)} said={list(said)}")


if __name__ == "__main__":
    main()
