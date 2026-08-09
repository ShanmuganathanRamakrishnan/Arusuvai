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

A second mode, ``text``, added for D4c-i, prints the decline **sentences**
themselves rather than the counts that summarise them -- the artifact D4's
original text asked for and D4a did not produce. See ``decline_text`` for the
profile-selection rule and why the phrase "the decline for each template" no
longer denotes anything without one.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py
    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py text

Both modes read only fields that exist on **both** sides of D4a, so either can
be run in a worktree of the pre-D4a commit to produce a before column. That is
a property to check when writing a probe, not when someone asks for the delta;
see the 2026-08-08 entry's amendment in ``docs/audit_log.md``.
"""
from __future__ import annotations

import itertools
import sys

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


def decline_text() -> None:
    """The decline sentences, per template. D4c-i.

    **There is no such thing as "the decline for each template."** Since D3 all
    four templates pass for the reference profile, so a decline only exists
    relative to a profile, and any artifact that prints four blocks without
    saying whose they are has quietly answered a question nobody asked. The
    selection rule is therefore part of the output, not part of the setup:

    Walk ``profiles()`` in grid order. Group each template's declines by the
    **shape of what the decline says** -- the sorted ``(macro, kind)`` pairs it
    names, and whether the profile has clinical flags. Then per template print

      1. the most common shape,
      2. the most common shape whose profile carries clinical flags, and
      3. the most common shape whose profile carries none,

    deduplicated -- (1) is always one of (2) or (3) -- each with the count of
    grid profiles sharing it and the first such profile in grid order as the
    representative. Ties break on grid order, so the output is a function of
    the grid and nothing else.

    (2) and (3) are called out rather than left to frequency because they
    produce the two sentence families D9 has to design separately: "we did not
    try, and here is what we would not compromise" versus "we tried everything
    and failed." Ranking by count alone buries whichever is rarer, and which
    one that is turned out to be an accident of the grid -- the first version
    of this rule guarded only (2), and on the real library the top shape
    already carried flags on all four templates, so the artifact printed four
    locked declines and not one ordinary one. The asymmetry was invisible
    until the output was read, which is the argument for reading it.

    Reads ``result.disclosure``, ``Violation.describe()``, ``.macro``, ``.kind``,
    ``result.relaxation_applied`` and ``outcome.skipped_locked_steps`` -- all
    present before D4a as well as after (checked against ``b72060e``, not
    assumed), so this mode produces both columns of a before/after.
    """

    print("Decline text, all four templates. Selection rule: see `decline_text`")
    print("in this file -- the representative profiles are chosen by the grid,")
    print("not by hand, and the rule is reproduced with the output on purpose.")

    for region, slot in TEMPLATES:
        shapes: dict[tuple, list[tuple]] = {}
        for profile in profiles():
            day = derive_target(profile).nutrition_target
            outcome = plan_meal(lib, day, region=region, meal_slot=slot,
                                diet_pattern=profile.diet, profile=profile,
                                dev_mode=True)
            if outcome.plan is not None:
                continue
            key = (
                tuple(sorted((v.macro, v.kind) for v in outcome.result.violations)),
                bool(profile.clinical_flags),
            )
            shapes.setdefault(key, []).append((profile, outcome))

        print()
        print("#" * 100)
        print(f"# {region.value} / {slot.value}")
        if not shapes:
            # Not an error and not a gap in the artifact: a template that never
            # declines across the grid is a fact about the library worth
            # printing, and printing nothing would read as a probe failure.
            print("#   no profile in the grid is declined on this template.")
            continue
        order = list(shapes)
        ranked = sorted(order, key=lambda k: (-len(shapes[k]), order.index(k)))
        chosen = [ranked[0]]
        for want_flags in (True, False):
            side = [k for k in ranked if k[1] is want_flags]
            if side and side[0] not in chosen:
                chosen.append(side[0])

        total = sum(len(v) for v in shapes.values())
        print(f"#   {total} declines across the grid in {len(shapes)} shape(s); "
              f"showing {len(chosen)}")
        print("#" * 100)

        for key in chosen:
            members = shapes[key]
            profile, outcome = members[0]
            why = ("most common shape overall" if key is ranked[0] else
                   "most common shape with clinical flags set" if key[1] else
                   "most common shape with no clinical flags")
            print()
            print(f"  [{why}] x{len(members)} profile(s)")
            print(f"  representative: {profile.weight_kg:g}kg {profile.goal.value} "
                  f"{profile.diet.value} flags="
                  f"{sorted(f.value for f in profile.clinical_flags) or 'none'}")
            print(f"  rungs walked: {list(outcome.result.relaxation_applied) or 'none'}"
                  f" | rungs refused as locked: "
                  f"{list(outcome.skipped_locked_steps) or 'none'}")
            print()
            print("  DISCLOSURE (the one string `web/dashboard.js` renders verbatim):")
            for line in _wrap(outcome.result.disclosure or "(empty)"):
                print(f"    {line}")
            print()
            print("  VIOLATIONS, each as the user would read it:")
            if not outcome.result.violations:
                print("    (none -- a decline that names no cause)")
            for violation in outcome.result.violations:
                for i, line in enumerate(_wrap(violation.describe())):
                    print(f"    {'-' if i == 0 else ' '} {line}")


def _wrap(text: str, width: int = 88) -> list[str]:
    """Wrap for the transcript. The sentences are long and the point of this
    artifact is that someone reads them to the end."""

    lines, current = [], ""
    for word in text.split():
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines or [""]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "text":
        decline_text()
    else:
        main()
