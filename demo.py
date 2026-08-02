"""Reproduce this project's evidence, from a clean checkout, with no servers.

Every result the recent audit and design work rests on -- the first plan the
real library ever produced, the sodium decline, the rung-by-rung ladder table,
the per-line salt breakdown -- came out of an untracked scratch script. None of
it could be reproduced by anyone, on any machine, including by us tomorrow. For
a project whose whole claim is evidentiary discipline that is the worst kind of
defect, and `docs/audit_log.md` finding 11 (this file was referenced by
CLAUDE.md and `docs/methodology.md` and did not exist) was the same hole seen
from the other side.

So: one tracked entry point, arguments not edits, and output that carries its
own `dev_mode` label so a pasted transcript cannot outlive the caveat
(`docs/methodology.md`, "unvalidated must survive being viewed without
surrounding context").

    python demo.py                     # everything, for the reference profile
    python demo.py library             # load report + slot coverage
    python demo.py plan --region north_indian --meal-slot lunch --weight-kg 70
    python demo.py plan --clinical-flag hypertension
    python demo.py --help

## Two things this script is deliberately careful about

**It prints the unrelaxed target AND the target the ladder stopped on, each
labelled.** ``LadderOutcome.target_used`` is the latter. The scratch script
printed only that, under a bare "meal target" heading, and it caused a
miscalibrated prediction in Task 4b: the fully-relaxed bounds were read as the
bounds the plate was first asked to meet, so every rung looked like it still
had room to give. Printing one without the other is the bug; the label is the
fix.

**Output is ASCII only.** These transcripts get pasted into commit messages and
markdown on Windows terminals, where a stray em-dash arrives as mojibake and
quietly corrupts the evidence it was meant to preserve.

This script computes nothing. It calls `core/` and formats what comes back --
no nutritional arithmetic lives here, exactly as `api/` computes none.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable, Sequence

from core.foods.nutrition_of import nutrition_of_components
from core.foods.templates import ALL_TEMPLATES, template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.target import NutritionTarget
from core.nutrition.targets import DerivedTarget, derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations
from core.planner.plan import Library, default_library, plan_meal
from core.schemas import (
    ActivityLevel,
    ClinicalFlag,
    DayLedger,
    DietPattern,
    Goal,
    MealSlot,
    Profile,
    Region,
    Sex,
)

RULE = "=" * 72
DASH = "-" * 72

#: The profile every recent finding was established against. Kept as the
#: default so `python demo.py` with no arguments reproduces the transcript in
#: the audit log, and kept as data so a second profile is a flag, not an edit.
REFERENCE_PROFILE = dict(
    weight_kg=70.0,
    height_cm=175.0,
    age_years=28,
    sex="male",
    activity="moderate",
    goal="maintain",
    diet="vegetarian",
)


def _banner(derived: DerivedTarget) -> None:
    """The dev_mode label, first thing on stdout and again at the end.

    Read from the derivation rather than hard-coded, so it flips on its own the
    day a human verifies the last source constant -- and so this banner cannot
    become a stale claim about the project's own state.
    """

    print(RULE)
    print(f"  STATUS: {derived.status.upper()}")
    if derived.disclosure:
        print(f"  {derived.disclosure}")
    print(RULE)
    print()


#: How each bound rule reads in a transcript. `BOUND_SOURCES` tokens are
#: identifiers, so they are mapped to words here rather than printed raw.
_BOUND_SOURCE_LABEL = {
    "meal_share": "registered share of the day",
    "day_remaining": "what the day has left",
    "absurdity_guard": "per-plate cap on a day's allowance",
}


def _fmt_target(target: NutritionTarget, macros: Sequence[str]) -> Iterable[str]:
    for macro in macros:
        floor = target.floor(macro)
        ceiling = target.ceiling(macro)
        if floor is None and ceiling is None:
            continue
        lo = f"{floor:9.1f}" if floor is not None else "        -"
        hi = f"{ceiling:9.1f}" if ceiling is not None else "        -"
        line = f"      {macro:12s} floor {lo}   ceiling {hi}"
        # Which rule produced the ceiling, so a pasted transcript says how the
        # number was reached and not only what it is. Printed for budgeted
        # macros only; a plain energy-fraction bound needs no annotation.
        source = target.bound_sources.get(macro)
        if source is not None and source != "meal_share":
            line += f"   [{_BOUND_SOURCE_LABEL.get(source, source)}]"
        yield line


_MACRO_ORDER = (
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carb_g",
    "fibre_g",
    "sodium_mg",
)


def build_profile(args: argparse.Namespace) -> Profile:
    return Profile(
        weight_kg=args.weight_kg,
        height_cm=args.height_cm,
        age_years=args.age_years,
        sex=Sex(args.sex),
        activity=ActivityLevel(args.activity),
        goal=Goal(args.goal),
        diet=DietPattern(args.diet),
        clinical_flags=frozenset(ClinicalFlag(f) for f in args.clinical_flag),
    )


def describe_profile(profile: Profile) -> str:
    flags = ",".join(sorted(f.value for f in profile.clinical_flags)) or "none"
    return (
        f"{profile.weight_kg:g}kg / {profile.height_cm:g}cm / {profile.age_years} / "
        f"{profile.sex.value} / {profile.activity.value} / {profile.goal.value} / "
        f"{profile.diet.value} / clinical_flags={flags}"
    )


def section_library(library: Library, profile: Profile, dev_mode: bool) -> None:
    """Load report, then slot coverage for all four templates."""

    print(RULE)
    print("1. LOAD THE REAL LIBRARY (data/raw/ifct + data/recipes)")
    print(RULE)
    recipes = library.recipes
    print(f"recipes loaded : {len(recipes.recipes)}  {sorted(recipes.recipes)}")
    print(f"rejected       : {recipes.rejected}")
    print(f"warnings       : {recipes.warnings}")
    print(f"ingredients    : {len(library.ingredients)}")
    print(f"components     : {sorted(c.id for c in library.components())}")
    print()

    print(RULE)
    print(f"2. SLOT COVERAGE, ALL FOUR TEMPLATES (dev_mode={dev_mode}, "
          f"diet={profile.diet.value})")
    print(RULE)
    for template in ALL_TEMPLATES:
        pool = build_candidate_pool(
            library.components(),
            library.ingredients,
            template=template,
            diet_pattern=profile.diet,
            dev_mode=dev_mode,
        )
        print(f"{template.id}:")
        for slot in template.slots:
            candidates = pool.for_slot(slot)
            kind = "REQ" if slot.required else "opt"
            print(f"    {slot.name:20s} {kind} n={len(candidates)} "
                  f"{[c.id for c in candidates]}")
        empty = [s.name for s in template.slots if s.required and not pool.for_slot(s)]
        print(f"    -> empty REQUIRED slots: {empty or 'NONE'}")
    print()


def build_ledger(args: argparse.Namespace, meal_slot: MealSlot) -> DayLedger:
    """A day with `--sodium-spent-mg` already eaten, booked to another slot.

    A demo affordance, not a model concept: the honest way to populate a ledger
    is to plan an earlier meal and carry its result forward, and that cannot be
    demonstrated while three of the four templates enumerate zero combinations
    (`demo.py library`). Booking the spend to some *other* slot is what makes it
    count -- `core.nutrition.meal_target.spent_before` excludes the slot being
    planned, so a figure parked on the slot under test would correctly read as
    zero and the flag would look broken.
    """

    if not args.sodium_spent_mg:
        return DayLedger.empty()
    elsewhere = next(s for s in MealSlot if s is not meal_slot)
    return DayLedger.empty().with_meal(
        elsewhere, {"sodium_mg": float(args.sodium_spent_mg)}
    )


def describe_ledger(ledger: DayLedger) -> str:
    if ledger.is_empty():
        return "nothing planned yet (first meal of the day)"
    slots = ",".join(s.value for s in ledger.planned_slots())
    return f"sodium_mg {ledger.spent('sodium_mg'):.1f}mg spent across {slots}"


def section_plan(
    library: Library,
    profile: Profile,
    region: Region,
    meal_slot: MealSlot,
    dev_mode: bool,
    ledger: DayLedger,
) -> None:
    """Enumeration for the named template, then the full plan_meal result."""

    template = template_for(region, meal_slot)

    print(RULE)
    print(f"3. ENUMERATION -- {template.id}")
    print(RULE)
    pool = build_candidate_pool(
        library.components(),
        library.ingredients,
        template=template,
        diet_pattern=profile.diet,
        dev_mode=dev_mode,
    )
    combinations = enumerate_combinations(pool)
    print(f"combinations enumerated: {len(combinations)}")
    for combo in combinations:
        print("   ", [c.id for sel in combo.slot_selections for c in sel])
    print()

    print(RULE)
    print(f"4. plan_meal() -- {region.value} / {meal_slot.value}")
    print(RULE)
    print(f"profile        : {describe_profile(profile)}")
    print(f"day so far     : {describe_ledger(ledger)}")
    print()

    derived = derive_target(profile)
    outcome = plan_meal(
        library,
        derived.nutrition_target,
        region=region,
        meal_slot=meal_slot,
        diet_pattern=profile.diet,
        profile=profile,
        dev_mode=dev_mode,
        ledger=ledger,
    )

    # Both targets, always, each labelled. See this module's docstring: showing
    # only `target_used` is what caused the Task 4b miscalibration.
    unrelaxed = meal_target(derived.nutrition_target, meal_slot, ledger=ledger)
    print("  TARGET AS ASKED (unrelaxed -- before any relaxation rung fires):")
    for line in _fmt_target(unrelaxed, _MACRO_ORDER):
        print(line)
    print()
    if outcome.result.relaxation_applied:
        print(f"  TARGET AS SOLVED (after {len(outcome.result.relaxation_applied)} "
              f"relaxation rung(s): "
              f"{', '.join(outcome.result.relaxation_applied)}):")
        for line in _fmt_target(outcome.target_used, _MACRO_ORDER):
            print(line)
    else:
        print("  TARGET AS SOLVED: identical -- no relaxation rung fired.")
    print()

    print(f"passed         : {outcome.result.passed}")
    print(f"relaxation     : {outcome.result.relaxation_applied}")
    print(f"skipped locked : {outcome.skipped_locked_steps}")
    print()

    if outcome.plan is not None:
        plan = outcome.plan
        point = plan.estimate.point
        low, high = plan.estimate.low, plan.estimate.high
        print("PLAN")
        print(f"  unit counts  : {plan.unit_counts}")
        print(f"  point        : {point.energy_kcal:.1f} kcal, "
              f"{point.protein_g:.1f}g protein, {point.fat_g:.1f}g fat, "
              f"{point.carb_g:.1f}g carb, {point.sodium_mg:.1f}mg sodium")
        print(f"  energy band  : {low.energy_kcal:.1f} - {high.energy_kcal:.1f} kcal")
        unverified = plan.estimate.unverified_energy_kcal
        fraction = plan.estimate.unverified_energy_fraction()
        print(f"  unverified   : {unverified:.1f} kcal ({100 * fraction:.1f}% of plate) "
              f"-- CLAUDE.md's shipping threshold is ~15%")
    else:
        print("PLAN           : None (declined)")
    print()

    print("violations     :")
    if not outcome.result.violations:
        print("    (none)")
    for violation in outcome.result.violations:
        print(f"    kind={violation.kind!r} macro={violation.macro!r} "
              f"actual={violation.actual:.1f} bound={violation.bound:.1f} "
              f"locked_by={violation.locked_by}")
    print()
    print(f"disclosure     : {outcome.result.disclosure}")
    print()


def _add_profile_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--weight-kg", type=float, default=REFERENCE_PROFILE["weight_kg"])
    parser.add_argument("--height-cm", type=float, default=REFERENCE_PROFILE["height_cm"])
    parser.add_argument("--age-years", type=int, default=REFERENCE_PROFILE["age_years"])
    parser.add_argument("--sex", choices=[e.value for e in Sex],
                        default=REFERENCE_PROFILE["sex"])
    parser.add_argument("--activity", choices=[e.value for e in ActivityLevel],
                        default=REFERENCE_PROFILE["activity"])
    parser.add_argument("--goal", choices=[e.value for e in Goal],
                        default=REFERENCE_PROFILE["goal"])
    parser.add_argument("--diet", choices=[e.value for e in DietPattern],
                        default=REFERENCE_PROFILE["diet"])
    parser.add_argument("--clinical-flag", action="append", default=[],
                        choices=[e.value for e in ClinicalFlag],
                        help="repeatable; locks the affected macro out of the ladder")
    parser.add_argument("--dev-mode", dest="dev_mode", action="store_true", default=True,
                        help="keep candidates past the uncertainty eligibility ceiling "
                             "(default: on, because nothing in data/ clears it)")
    parser.add_argument("--no-dev-mode", dest="dev_mode", action="store_false")


def _add_template_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--region", choices=[e.value for e in Region],
                        default="north_indian")
    parser.add_argument("--meal-slot", choices=[e.value for e in MealSlot],
                        default="lunch")
    parser.add_argument("--sodium-spent-mg", type=float, default=0.0,
                        help="sodium already eaten today, booked to another "
                             "meal slot, so the plate is planned against what "
                             "the day has left (see build_ledger)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="demo.py",
        description="Reproduce this project's evidence from the real data/ library.",
    )
    parser.add_argument("--verbose", action="store_true",
                        help="show core/'s INFO logging (load reports, pre-filter counts)")
    subparsers = parser.add_subparsers(dest="command")

    library_parser = subparsers.add_parser(
        "library", help="load report and slot coverage for all four templates")
    _add_profile_args(library_parser)

    plan_parser = subparsers.add_parser(
        "plan", help="enumeration and plan_meal() for one template and profile")
    _add_profile_args(plan_parser)
    _add_template_args(plan_parser)

    all_parser = subparsers.add_parser(
        "all", help="library then plan (the default when no subcommand is given)")
    _add_profile_args(all_parser)
    _add_template_args(all_parser)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # No subcommand means "all", so a bare `python demo.py` reproduces the
    # transcript in docs/audit_log.md rather than printing usage.
    if not any(a in {"library", "plan", "all"} for a in argv) and "-h" not in argv \
            and "--help" not in argv:
        argv = ["all", *argv]

    args = build_parser().parse_args(argv)
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="  [%(levelname)s] %(message)s")

    profile = build_profile(args)
    derived = derive_target(profile)
    _banner(derived)

    library = default_library()
    command = args.command or "all"

    if command in {"library", "all"}:
        section_library(library, profile, args.dev_mode)
    if command in {"plan", "all"}:
        meal_slot = MealSlot(args.meal_slot)
        section_plan(
            library,
            profile,
            Region(args.region),
            meal_slot,
            args.dev_mode,
            build_ledger(args, meal_slot),
        )

    print(DASH)
    print(f"  END OF RUN -- STATUS: {derived.status.upper()}. "
          "Nothing above can ship as validated.")
    print(DASH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
