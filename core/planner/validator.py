"""The point-estimate gate and the relaxation ladder.

This is where CLAUDE.md's two most load-bearing decisions stop being prose.

## The gate is on the point estimate. Full stop.

``validate`` compares ``NutritionEstimate.point`` against the target's
floors and ceilings and nothing else. The interval is computed and returned
for display, and is never read by any comparison in this module — grep for
``\\.low`` and ``\\.high`` below and you will find them only in
``ValidationResult`` construction.

That restraint is the entire point. Gating on interval overlap ("the plan's
band touches the target band, so pass it") would mean a plan built on worse
data passes more easily than one built on better data, because a wider band
overlaps more. It inverts the incentive of the one mechanism the project has
for keeping its numbers honest. It is also the more natural-looking
implementation, which is why it is called out here rather than left implicit:
somebody, at some point, will read ``ValidationResult.actual_interval`` sitting
right there and think it should be used.

## The ladder relaxes tolerance, never uncertainty

``RELAXATION_ORDER`` is CLAUDE.md's list, in CLAUDE.md's order, as data.
Every step widens a *tolerance* — a floor or a ceiling — never drops one to
"no bound at all"; CLAUDE.md's relaxation-ladder section states this
explicitly for step 1 specifically, since dropping is the more natural-looking
implementation for a one-sided bound with no point to widen around. No step
reads, writes, or scales an uncertainty figure, because uncertainty is a
property of the data and not a knob (CLAUDE.md, "Uncertainty"). The two axes
never multiply: a plan does not become admissible because its data got worse.

Steps fire in order and cumulatively, each on a target already widened by the
ones before it, and the solver is re-run after each. The first step that
yields a feasible plan wins; the ladder stops there rather than continuing to
the loosest target that would also work.

## One bound is outside the ladder entirely

``NutritionTarget.quality_protein_floor_g`` (slice 4) is checked by the gate and
touched by **no** rung. Every macro bound here is a tolerance — how far a point
estimate may sit from a number — and the ladder's whole job is widening
tolerances. "At least this many grams came from a source clearing the DIAAS
threshold" is not a distance from a number; it is a statement about what the
plate is made of. There is no coherent 15%-looser version of it.

Practically this means a profile blocked on quality walks all four rungs, is
relaxed on sodium, fat, carb, energy and protein, and still declines. That is
the intended behaviour and it is not free: the plan it declines may have been
relaxed further than it needed to be before the decline was reached, so
``relaxation_applied`` on such a result reports rungs that could not have
helped. Reported honestly rather than suppressed — the target really was
widened that far.

## Clinical flags remove rungs; they do not reorder them

``LOCKED_CONSTRAINTS`` maps each ``ClinicalFlag`` to the macros it hard-locks.
A locked macro is dropped from every step that would have touched it — the
step still fires for its other macros (relaxing fibre for a hypertensive
profile is fine; relaxing sodium is not). A step all of whose macros are
locked is skipped entirely and does not appear in ``relaxation_applied``,
because recording a relaxation that did not happen would misreport the plan.

If the ladder is exhausted, the result is a decline that names the specific
blocking constraint and, where the constraint is locked, says so — never a
generic "no plan found". CLAUDE.md is explicit that a locked constraint making
the feasible set empty is an outcome to report, not to work around.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Mapping, Sequence

from core.foods.models import NutritionVector
from core.foods.nutrition_of import unit_for
from core.foods.quality import QUALITY_PROTEIN_KEY
from core.nutrition import citations
from core.planner.combinations import (
    MealCombination,
    feasible_combinations,
    macro_bounds,
    quality_protein_bounds,
)
from core.planner.solver import SolvedPlan, solve
from core.nutrition.target import NutritionTarget, band
from core.schemas import ClinicalFlag, Profile

__all__ = [
    "LOCKED_CONSTRAINTS",
    "RELAXATION_ORDER",
    "VIOLATION_REACH",
    "VIOLATION_RELAXABILITY",
    "RelaxationStep",
    "Violation",
    "ValidationResult",
    "locked_macros",
    "validate",
    "plan_within_ladder",
]


#: How far out of reach a bound is. Stable tokens in the same style as
#: ``core.nutrition.target.BOUND_SOURCES``, and for the same reason: a decline
#: screen has to tell "no plate can ever do this" apart from "each bound is
#: reachable but not all at once", and parsing English to find out is not a
#: mechanism. Like ``BOUND_SOURCES`` these are identifiers and must never reach
#: a visible text node (``tests/test_web_no_identifiers.py``).
#:
#: The distinction is load-bearing, not cosmetic. ``docs/audit_log.md`` finding
#: 24: a user told "energy is unreachable" adds an energy-dense dish, when every
#: such dish was already excluded on a bound nobody named. "Unreachable" is a
#: claim the library cannot serve them at all; "jointly infeasible" is a claim
#: about this combination of demands, and only the second is worth acting on.
VIOLATION_REACH: tuple[str, ...] = (
    #: No legal assignment of any enumerated combination satisfies this bound,
    #: whatever the user does. Computed from each component's serving-unit
    #: min/max, the same arithmetic the pre-filter uses.
    "unreachable",
    #: Reachable on its own; the plate that comes closest to feasible still
    #: misses it. The bound is part of a set that cannot be met together.
    "jointly_infeasible",
    #: This specific solved plate misses it. Only reachable when the solver and
    #: the gate disagree, which they should not.
    "plate_miss",
    #: There was no combination to evaluate at all — a required course of the
    #: template has no dish this profile can eat.
    "empty_pool",
)

#: Why a bound did not move out of the way. The ladder's own vocabulary, made
#: explicit so a screen can offer "relax this" only where relaxing is a thing
#: that exists. Same identifier rule as above.
VIOLATION_RELAXABILITY: tuple[str, ...] = (
    #: A rung touches this bound and has not fired yet.
    "relaxable",
    #: A rung touches this bound, fired, and it still blocks.
    "relaxed_to_limit",
    #: A rung touches this bound but a ``hard_ceiling`` stops it widening.
    "hard_capped",
    #: A disclosed clinical condition holds it. Deliberately not relaxed —
    #: the one case where "we did not try" is the honest answer.
    "locked",
    #: No rung in ``RELAXATION_ORDER`` touches this bound at all. The quality
    #: protein floor is the case that matters: it is a composition rule, not a
    #: tolerance, so there is no looser version of it to offer.
    "never_relaxed",
)


#: Which macro each disclosed condition hard-locks. Deliberately narrow: a flag
#: appears here only when there is a specific constraint it makes unsafe to
#: relax, and every flag in ``ClinicalFlag`` appears exactly once, so a flag can
#: never be added to the enum and silently do nothing (``test_planner_validator``
#: asserts the two stay in sync).
#:
#: Kidney disease locks protein *and* sodium: protein restriction is the
#: constraint most often prescribed in CKD, and it is the one rung CLAUDE.md's
#: default ladder is willing to relax with disclosure — which is exactly the
#: behaviour that must not happen for this profile. Diabetes locks carbohydrate,
#: which the default ladder otherwise treats as "least load-bearing" and
#: relaxes second.
LOCKED_CONSTRAINTS: Mapping[ClinicalFlag, frozenset[str]] = {
    ClinicalFlag.HYPERTENSION: frozenset({"sodium_mg"}),
    ClinicalFlag.CHRONIC_KIDNEY_DISEASE: frozenset({"protein_g", "sodium_mg"}),
    ClinicalFlag.DIABETES: frozenset({"carb_g"}),
}


def locked_macros(profile: Profile | None) -> frozenset[str]:
    """Every macro this profile's flags remove from the ladder."""

    if profile is None:
        return frozenset()
    out: set[str] = set()
    for flag in profile.clinical_flags:
        out |= LOCKED_CONSTRAINTS[flag]
    return frozenset(out)


def _flags_locking(macro: str, profile: Profile | None) -> tuple[ClinicalFlag, ...]:
    if profile is None:
        return ()
    return tuple(
        flag for flag in sorted(profile.clinical_flags) if macro in LOCKED_CONSTRAINTS[flag]
    )


# --------------------------------------------------------------------------
# The ladder
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RelaxationStep:
    """One rung: a name, the macros it touches, and how it widens them.

    ``apply`` receives the already-partly-relaxed target and the set of macros
    it may not touch, and returns a new target. It is a function rather than a
    (macro -> new tolerance) table because the rungs are not all the same shape
    — step 1 widens sodium's ceiling and fibre's floor proportionally to their
    *existing* bound (they have no registered ideal point to widen a band
    around), while steps 2-4 widen a band around a point — and flattening that
    into a table would have meant a second widening mechanism hidden behind a
    single row, which is exactly the kind of implementation detail CLAUDE.md's
    relaxation-ladder section now states explicitly rather than leaving to this
    docstring alone.
    """

    name: str
    macros: tuple[str, ...]
    #: Whether reaching a feasible plan via this step obliges a user-facing
    #: disclosure. Only protein's rung sets this, per CLAUDE.md: the earlier
    #: rungs relax "general health guidance" and the product's less
    #: load-bearing macros, and are applied silently by design.
    requires_disclosure: bool
    apply: Callable[[NutritionTarget, frozenset[str]], NutritionTarget]

    def is_fully_locked(self, locked: frozenset[str]) -> bool:
        return all(macro in locked for macro in self.macros)


def _capped(widened: float, hard_ceiling: float | None) -> float:
    """A widened ceiling, clipped to the bound relaxation may not pass.

    Rule (ii) of the day-budget design, in one line. Without this clip, a rung
    widening a day-budget ceiling by ``tolerance.sodium_relaxed_fraction``
    (0.50) would let a single plate carry 1.5x its whole share of a *daily*
    guideline — measured at 105% of a day's sodium on one plate for the
    reference profile, which is why the guard is a hard cap and not another
    ceiling. Targets built from a tolerance alone register no hard ceiling, so
    this is the identity function for every one of them.
    """

    if hard_ceiling is None:
        return widened
    return min(widened, hard_ceiling)


def _widen_band(
    target: NutritionTarget,
    locked: frozenset[str],
    *,
    macros: tuple[str, ...],
    tolerance: float,
) -> NutritionTarget:
    """Re-derive each macro's floor/ceiling as a wider band around its point.

    Recomputed from ``NutritionTarget.point`` rather than by scaling the
    existing floor and ceiling: scaling compounds across rungs (a band widened
    twice by 'multiply by 1.1' is not the same as a band stated once at the
    registered relaxed tolerance), and the registered constants state absolute
    tolerances, not increments.
    """

    floors = dict(target.floors)
    ceilings = dict(target.ceilings)
    for macro in macros:
        if macro in locked:
            continue
        point = target.point(macro)
        if point is None:
            # No ideal point to widen around: the macro was given a bare
            # floor/ceiling, so there is nothing this rung can do for it. Left
            # untouched rather than guessed at from the existing bound.
            continue
        lo, hi = band(point, tolerance)
        if macro in floors:
            floors[macro] = lo
        if macro in ceilings:
            ceilings[macro] = _capped(hi, target.hard_ceiling(macro))
    # `replace`, not a fresh NutritionTarget: every field this rung does not
    # touch must survive it, and a hand-written constructor call silently drops
    # any field added later. That is not hypothetical — slice 4's quality floor
    # is exactly such a field, and dropping it here would have let the ladder
    # relax a bound no rung is allowed to touch.
    return replace(target, floors=floors, ceilings=ceilings)


def _relax_sodium_fibre(target: NutritionTarget, locked: frozenset[str]) -> NutritionTarget:
    """Widen the sodium ceiling and fibre floor by a registered fraction.

    Not ``_widen_band``: sodium and fibre are one-sided guidance bounds with no
    ideal ``point`` registered by ``simple_target`` (see its docstring), so
    "widen around the point" has nothing to widen around — calling
    ``_widen_band`` here would silently no-op, which is the trap its own
    docstring warns about. Widened proportionally to the *existing bound*
    instead — CLAUDE.md ("Relaxation ladder, round-4 addendum") is explicit
    that this rung must not drop the bound outright: an unflagged profile
    would then be solved against zero sodium ceiling at all, which is a
    materially different (and unbounded) thing from "the least load-bearing
    constraint relaxes first."
    """

    ceilings = dict(target.ceilings)
    sources = dict(target.bound_sources)
    if "sodium_mg" in ceilings and "sodium_mg" not in locked:
        fraction = citations.value_of("tolerance.sodium_relaxed_fraction")
        widened = ceilings["sodium_mg"] * (1.0 + fraction)
        hard = target.hard_ceiling("sodium_mg")
        ceilings["sodium_mg"] = _capped(widened, hard)
        # The reason must track the number. Once the clamp bites, the bound the
        # user is being declined against is the guard, not what the day had
        # left, and reporting the stale reason would explain the wrong bound.
        if hard is not None and widened > hard:
            sources["sodium_mg"] = "absurdity_guard"
    floors = dict(target.floors)
    if "fibre_g" in floors and "fibre_g" not in locked:
        fraction = citations.value_of("tolerance.fibre_relaxed_fraction")
        floors["fibre_g"] = floors["fibre_g"] * (1.0 - fraction)
    return replace(target, floors=floors, ceilings=ceilings, bound_sources=sources)


def _relax_fat_carb(target: NutritionTarget, locked: frozenset[str]) -> NutritionTarget:
    return _widen_band(
        target,
        locked,
        macros=("fat_g", "carb_g"),
        tolerance=citations.value_of("tolerance.fat_carb_relaxed"),
    )


def _relax_energy(target: NutritionTarget, locked: frozenset[str]) -> NutritionTarget:
    return _widen_band(
        target,
        locked,
        macros=("energy_kcal",),
        tolerance=citations.value_of("tolerance.energy_relaxed"),
    )


def _relax_protein(target: NutritionTarget, locked: frozenset[str]) -> NutritionTarget:
    """Lower the protein floor partially — never remove it, never touch a ceiling.

    ``_widen_band`` is the wrong shape here: it widens symmetrically, and this
    rung must move one bound only. It lowers the floor by the registered
    fraction and stops; the floor still exists, and a plan that cannot reach
    even the lowered floor is still declined.

    Updated 2026-08-02 (slice 3). The original reason given was "protein has a
    floor and no ceiling, so widening symmetrically would *invent* one". That is
    no longer true — ``meal_target`` now sets a per-meal protein ceiling from
    ``protein.meal_ceiling_fraction`` — but the behaviour is unchanged and
    deliberately so. The ceiling is a plausibility bound ("no single meal carries
    more than half the day's protein"), and a ladder that relaxed a protein floor
    *downward* while relaxing its ceiling *upward* would be widening the band on
    both sides to admit a plate the bound exists to reject. Ceilings pass through
    untouched, which is why the ceiling needs no ``hard_ceilings`` entry: nothing
    in ``RELAXATION_ORDER`` can move it.

    Updated again 2026-08-07 (slice 4). The **quality-protein floor is not
    touched by this rung, or by any other.** It is not a tolerance: CLAUDE.md's
    ladder widens how far a point estimate may sit from a target, and "at least
    this much of the protein came from a qualifying source" is a statement about
    composition, not about distance from a number. Relaxing it would mean
    answering "this plate is all lentil" with "then require less of it not to
    be", which is not a compromise, it is abandoning the rule. The consequence
    is stated rather than hidden: when the quality floor is what blocks a
    profile, the ladder walks all four rungs, changes nothing relevant, and
    declines — see ``docs/methodology.md``.
    """

    if "protein_g" in locked:
        return target
    point = target.point("protein_g")
    if point is None or "protein_g" not in target.floors:
        return target
    fraction = citations.value_of("tolerance.protein_relaxed_fraction")
    floors = dict(target.floors)
    floors["protein_g"] = point * (1.0 - fraction)
    return replace(target, floors=floors)


#: CLAUDE.md's ladder, in CLAUDE.md's order. The order is the safety property:
#: the least load-bearing constraint is given up first and the product's core
#: nutritional claim last. Reordering this tuple changes what the product is
#: willing to compromise before it compromises protein.
RELAXATION_ORDER: tuple[RelaxationStep, ...] = (
    RelaxationStep(
        name="sodium_max_fibre_min",
        macros=("sodium_mg", "fibre_g"),
        requires_disclosure=False,
        apply=_relax_sodium_fibre,
    ),
    RelaxationStep(
        name="fat_carb_tolerance",
        macros=("fat_g", "carb_g"),
        requires_disclosure=False,
        apply=_relax_fat_carb,
    ),
    RelaxationStep(
        name="energy_tolerance",
        macros=("energy_kcal",),
        requires_disclosure=False,
        apply=_relax_energy,
    ),
    RelaxationStep(
        name="protein_tolerance",
        macros=("protein_g",),
        requires_disclosure=True,
        apply=_relax_protein,
    ),
)


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    """One bound the plan does not meet, or cannot be made to meet."""

    macro: str
    #: "below_floor" | "above_ceiling" | "no_candidates"
    kind: str
    actual: float
    bound: float
    #: Non-empty when the bound could not be relaxed because a disclosed
    #: condition locks it. This is the difference between "we tried everything"
    #: and "we deliberately refused to try one thing", and the user is owed the
    #: distinction.
    locked_by: tuple[ClinicalFlag, ...] = ()
    #: Which rule produced ``bound`` — one of ``core.nutrition.target.
    #: BOUND_SOURCES``. Read off the target rather than inferred here. A stable
    #: token, not copy: it crosses the API so a client can render "this plate is
    #: too salty" and "your day is already spent" as the different messages they
    #: are, and it must never reach a visible text node itself.
    bound_source: str = "meal_share"
    #: One of :data:`VIOLATION_REACH`. Whether anything the user could choose
    #: differently would help.
    reach: str = "plate_miss"
    #: One of :data:`VIOLATION_RELAXABILITY`. Whether the ladder had anything
    #: left to give on this bound, and if not, why not.
    relaxability: str = "relaxable"
    #: ``TemplateSlot.name`` per required course that had no legal selection.
    #: Only populated on a ``no_candidates`` violation. Structured rather than
    #: written into ``describe`` because slot names are ``snake_case``
    #: identifiers — the screen maps them to the name of a course a person would
    #: recognise ("the curd course"), which is not this module's job.
    blocking_slots: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # Validated at construction, like NutritionTarget.bound_sources, and for
        # the identical reason: these reach the API as tokens a client switches
        # on, so a typo would fall through to a default message rather than fail.
        if self.reach not in VIOLATION_REACH:
            raise ValueError(
                f"violation: unknown reach {self.reach!r}. Allowed: "
                f"{list(VIOLATION_REACH)}"
            )
        if self.relaxability not in VIOLATION_RELAXABILITY:
            raise ValueError(
                f"violation: unknown relaxability {self.relaxability!r}. "
                f"Allowed: {list(VIOLATION_RELAXABILITY)}"
            )
        if self.blocking_slots and self.kind != "no_candidates":
            raise ValueError(
                "violation: blocking_slots describes an unfillable template "
                "course, which only a 'no_candidates' violation has"
            )

    def describe(self) -> str:
        unit = unit_for(self.macro)
        if self.kind == "no_candidates":
            if self.blocking_slots:
                count = len(self.blocking_slots)
                course = "course" if count == 1 else "courses"
                return (
                    f"{count} required {course} of this meal cannot be filled "
                    "from the recipe library for this profile, so there was "
                    "nothing to solve"
                )
            return (
                "no recipe combination survived filtering for this profile, so "
                "there was nothing to solve"
            )
        if self.macro == QUALITY_PROTEIN_KEY:
            # Its own sentence, because "quality_protein_g is 7.9g, below its
            # floor of 11.2g" would tell a reader nothing about what the bound
            # means, and the identifier must not reach them at all
            # (tests/test_web_no_identifiers.py).
            return (
                f"only {self.actual:.1f}g of this plate's protein comes from a "
                f"high-quality source, against a floor of {self.bound:.1f}g "
                "(this is a project rule, not a clinical one, and it judges "
                "each ingredient on its own rather than crediting the way a "
                "grain and a legume complement each other)"
            )
        direction = "below its floor of" if self.kind == "below_floor" else "above its ceiling of"
        text = (
            f"{self.macro} is {self.actual:.1f}{unit}, {direction} "
            f"{self.bound:.1f}{unit}"
        )
        # Same number, different reason, so different sentence. Without this a
        # day already spent by other meals reads as a fault in this plate.
        #
        # ASCII, deliberately, like every other string this function builds:
        # these go into `demo.py` transcripts that get pasted into commit
        # messages and markdown on Windows terminals, where an em-dash arrives
        # as mojibake and quietly corrupts the evidence it was preserving.
        if self.bound_source == "day_remaining":
            text += " (what the rest of today has left, not this plate's own limit)"
        elif self.bound_source == "absurdity_guard":
            text += " (more than one plate may take of a whole day's allowance)"
        if self.locked_by:
            # The flag values are NOT interpolated here, though they were until
            # 2026-08-08. `ClinicalFlag.CHRONIC_KIDNEY_DISEASE.value` is
            # "chronic_kidney_disease" — a snake_case identifier, written
            # straight into the sentence a decline screen renders, which is the
            # exact class `tests/test_web_no_identifiers.py` exists to catch and
            # which it missed because no test rendered a locked decline. Which
            # condition it was travels as `locked_by`, a tuple of enum members
            # the screen maps to its own copy.
            count = len(self.locked_by)
            which = "a condition" if count == 1 else f"{count} conditions"
            text += (
                f" (locked by {which} you disclosed, and never relaxed for that "
                "reason)"
            )
        return text


@dataclass(frozen=True)
class ValidationResult:
    """The verdict, plus everything needed to explain it.

    Tuples rather than the ``list``s BUILD_PROMPTS sketches: this is a frozen
    dataclass crossing a module boundary (CLAUDE.md, "Types"), and a mutable
    list inside one is frozen in name only.
    """

    passed: bool
    actual_point_estimate: NutritionVector
    #: (low, high). Display only — see this module's docstring. Nothing in this
    #: file compares against it.
    actual_interval: tuple[NutritionVector, NutritionVector]
    violations: tuple[Violation, ...] = ()
    #: Ladder steps that were applied to the target this plan was solved
    #: against. On a decline this lists every unlocked step that was tried and
    #: still did not help — the target really was widened that far, so
    #: reporting them is accurate, and omitting them would hide how much was
    #: given up before declining.
    relaxation_applied: tuple[str, ...] = ()
    disclosure: str | None = None

    def __post_init__(self) -> None:
        # Structural, not a convention to remember: CLAUDE.md says the protein
        # rung is "never disclosed silently", and that a decline must "name the
        # specific blocking constraint". Both are enforced at construction, so
        # a caller cannot build a result that violates either.
        protein_relaxed = "protein_tolerance" in self.relaxation_applied
        if protein_relaxed and not (self.disclosure or "").strip():
            raise ValueError(
                "protein tolerance was relaxed but no disclosure was written; "
                "CLAUDE.md requires this one to be disclosed, never silent"
            )
        if not self.passed:
            if not self.violations:
                raise ValueError(
                    "a failed ValidationResult must name at least one violation, "
                    "not decline generically"
                )
            if not (self.disclosure or "").strip():
                raise ValueError(
                    "a failed ValidationResult must explain the decline to the user"
                )

    def describe_violations(self) -> str:
        return "; ".join(v.describe() for v in self.violations)


# --------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------


def _bound_source(macro: str, target: NutritionTarget) -> str:
    """Which rule produced this macro's ceiling. Only floors have no source.

    Read off the target, never inferred by comparing the ceiling against the
    hard ceiling: those are floats, they can coincide for unrelated reasons, and
    a guess here would put the wrong sentence in front of a user.
    """

    return target.bound_sources.get(macro, "meal_share")


def _relaxability(
    macro: str,
    kind: str,
    target: NutritionTarget,
    locked_by: tuple[ClinicalFlag, ...],
    applied: tuple[str, ...],
) -> str:
    """Why this bound did not move, as one of :data:`VIOLATION_RELAXABILITY`.

    Derived from ``RELAXATION_ORDER`` itself rather than from a hand-kept table
    of "which macros are relaxable". A rung added to the ladder, or a macro
    added to an existing rung's ``macros``, changes this answer automatically;
    a table would have to be remembered, and would be wrong the first time it
    was not.
    """

    if locked_by:
        return "locked"
    step = next((s for s in RELAXATION_ORDER if macro in s.macros), None)
    if step is None:
        # Includes QUALITY_PROTEIN_KEY, which is not a macro and appears in no
        # rung, and any macro bounded by a target the ladder does not cover.
        return "never_relaxed"
    if kind == "above_ceiling":
        hard = target.hard_ceiling(macro)
        ceiling = target.ceiling(macro)
        if hard is not None and ceiling is not None and ceiling >= hard:
            # Sitting on the guard: the rung fires but `_capped` clips it, so
            # there is no further widening to offer however many rungs remain.
            return "hard_capped"
    return "relaxed_to_limit" if step.name in applied else "relaxable"


def _violations_for(
    point: NutritionVector,
    target: NutritionTarget,
    profile: Profile | None,
    quality_protein_g: float = 0.0,
    *,
    reach: str = "plate_miss",
    applied: tuple[str, ...] = (),
) -> tuple[Violation, ...]:
    out: list[Violation] = []
    quality_floor = target.quality_protein_floor()
    if quality_floor is not None and quality_protein_g < quality_floor:
        # No `locked_by`: no ClinicalFlag maps to qualifying protein, and this
        # bound is outside the ladder for every profile rather than locked for
        # some. Reporting it as locked would claim a disclosed condition is the
        # reason it did not move.
        out.append(
            Violation(
                QUALITY_PROTEIN_KEY,
                "below_floor",
                quality_protein_g,
                quality_floor,
                reach=reach,
                relaxability="never_relaxed",
            )
        )
    for macro in sorted(target.bounded_macros()):
        value = getattr(point, macro)
        floor = target.floor(macro)
        ceiling = target.ceiling(macro)
        if floor is not None and value < floor:
            locked = _flags_locking(macro, profile)
            out.append(
                Violation(
                    macro,
                    "below_floor",
                    value,
                    floor,
                    locked,
                    reach=reach,
                    relaxability=_relaxability(
                        macro, "below_floor", target, locked, applied
                    ),
                )
            )
        if ceiling is not None and value > ceiling:
            locked = _flags_locking(macro, profile)
            out.append(
                Violation(
                    macro,
                    "above_ceiling",
                    value,
                    ceiling,
                    locked,
                    _bound_source(macro, target),
                    reach=reach,
                    relaxability=_relaxability(
                        macro, "above_ceiling", target, locked, applied
                    ),
                )
            )
    return tuple(out)


def validate(
    plan: SolvedPlan,
    target: NutritionTarget,
    *,
    profile: Profile | None = None,
    relaxation_applied: tuple[str, ...] = (),
    disclosure: str | None = None,
) -> ValidationResult:
    """Gate one solved plan's **point estimate** against ``target``.

    ``target`` is whatever target the plan was actually solved against — the
    relaxed one, if the ladder fired. Passing the original here instead would
    report a relaxed plan as failing, which is why ``plan_within_ladder``
    threads the relaxed target through rather than keeping the original.
    """

    estimate = plan.estimate
    violations = _violations_for(
        estimate.point,
        target,
        profile,
        plan.quality_protein_g,
        reach="plate_miss",
        applied=relaxation_applied,
    )
    passed = not violations
    if not passed and not (disclosure or "").strip():
        disclosure = (
            "This plan does not meet its nutritional target: "
            + "; ".join(v.describe() for v in violations)
        )
    return ValidationResult(
        passed=passed,
        actual_point_estimate=estimate.point,
        actual_interval=(estimate.low, estimate.high),
        violations=violations,
        relaxation_applied=relaxation_applied,
        disclosure=disclosure,
    )


# --------------------------------------------------------------------------
# Walking the ladder
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class LadderOutcome:
    """What the ladder produced: a plan and its verdict, or a decline.

    ``plan is None`` exactly when ``result.passed`` is False and no rung
    yielded anything solvable.
    """

    plan: SolvedPlan | None
    result: ValidationResult
    #: The target actually solved against, after any relaxation. Kept so a
    #: caller can show what the plan was held to, rather than the original the
    #: plan may no longer meet.
    target_used: NutritionTarget
    skipped_locked_steps: tuple[str, ...] = ()


def _protein_disclosure(point: NutritionVector, original: NutritionTarget) -> str:
    """CLAUDE.md's worked example, in the target's own units.

    One decimal, not whole grams. Rounding 29.5 against a 30 g floor to
    "30 g against a 30 g target, a shortfall of 0 g" turns a mandatory
    disclosure into a statement that nothing is wrong — the disclosure would
    still fire, and would say the opposite of what it fired for. The units are
    read from ``core.foods.nutrition_of.unit_for`` rather than written here so
    the disclosure is guaranteed to be in the units the target was stated in.
    """

    floor = original.floor("protein_g")
    target_value = floor if floor is not None else original.point("protein_g")
    target_value = target_value or 0.0
    unit = unit_for("protein_g")
    actual = point.protein_g
    gap = max(0.0, target_value - actual)
    return (
        f"This plan delivers {actual:.1f}{unit} of protein against a "
        f"{target_value:.1f}{unit} target, a shortfall of {gap:.1f}{unit}. "
        "The recipe library does not currently have a component dense enough in "
        "protein at this energy level to close the gap."
    )


def _reach(
    combinations: Sequence[MealCombination], macro: str, ingredients: Mapping
) -> tuple[float, float]:
    """(lowest reachable, highest reachable) for ``macro`` across all combos.

    Reuses the pre-filter's per-component min/max bounds, so a decline message
    names a limit computed the same way the pre-filter computed it — not a
    second, possibly disagreeing estimate of what the library can reach.
    """

    lowest = float("inf")
    highest = float("-inf")
    for combo in combinations:
        lo = 0.0
        hi = 0.0
        for component in combo.components:
            c_lo, c_hi = macro_bounds(component, macro, ingredients)
            lo += c_lo
            hi += c_hi
        lowest = min(lowest, lo)
        highest = max(highest, hi)
    return lowest, highest


def _unreachable_violations(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping,
    profile: Profile | None,
    applied: tuple[str, ...],
) -> tuple[Violation, ...]:
    """Bounds no legal assignment of any combination can satisfy, all of them.

    "Structurally unreachable" in finding 24's sense: not a fact about the plate
    the solver happened to look at, a fact about the library. Computed from each
    component's serving-unit min/max via the pre-filter's own ``macro_bounds``
    and ``quality_protein_bounds``, so a decline never explains an empty set
    with a number arrived at some other way.
    """

    out: list[Violation] = []
    quality_floor = target.quality_protein_floor()
    if quality_floor is not None:
        # One-sided, so only the max side is computed.
        best_quality = max(
            sum(
                quality_protein_bounds(component, ingredients)[1]
                for component in combo.components
            )
            for combo in combinations
        )
        if best_quality < quality_floor:
            out.append(
                Violation(
                    QUALITY_PROTEIN_KEY,
                    "below_floor",
                    best_quality,
                    quality_floor,
                    reach="unreachable",
                    relaxability="never_relaxed",
                )
            )
    for macro in sorted(target.bounded_macros()):
        lowest, highest = _reach(combinations, macro, ingredients)
        floor = target.floor(macro)
        ceiling = target.ceiling(macro)
        locked = _flags_locking(macro, profile)
        if floor is not None and highest < floor:
            out.append(
                Violation(
                    macro,
                    "below_floor",
                    highest,
                    floor,
                    locked,
                    reach="unreachable",
                    relaxability=_relaxability(
                        macro, "below_floor", target, locked, applied
                    ),
                )
            )
        if ceiling is not None and lowest > ceiling:
            out.append(
                Violation(
                    macro,
                    "above_ceiling",
                    lowest,
                    ceiling,
                    locked,
                    _bound_source(macro, target),
                    reach="unreachable",
                    relaxability=_relaxability(
                        macro, "above_ceiling", target, locked, applied
                    ),
                )
            )
    return tuple(out)


def _nearest_plate_violations(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping,
    profile: Profile | None,
    applied: tuple[str, ...],
) -> tuple[Violation, ...]:
    """Every bound missed by the combination that comes closest to feasible.

    "Closest" is **fewest bounds broken**, tie-broken by the solver's deviation
    score. Ranking by score alone — which is what this did until 2026-08-08 — is
    wrong for this job in a way that is easy to miss: ``_deviation_point``
    measures distance from each macro's ideal *point*, and sodium and fibre have
    no registered point at all (``core.nutrition.target.simple_target``), so a
    plate's saltiness contributes exactly nothing to its score. The plate the
    old ranking called "best available" could therefore be one that breaks two
    bounds while another breaks one.

    Measured, before the change, on the real library: a 110 kg fat-loss profile
    against ``north_lunch`` was declined on "fat is 37.1g above its ceiling of
    34.1g; sodium is 1418.5mg above its ceiling of 1400.0mg" while a plate
    existed — phulka x3, soya_chunk_curry x2, paneer_masala x1 — breaking only
    the protein floor, by 4.0g. Both named bounds were ones that plate met. A
    user acting on that decline would have gone looking for leaner, less salty
    dishes to fix a protein shortfall. See ``docs/design/probes/d4_declines.py``.
    """

    best: tuple[tuple[int, float], tuple[Violation, ...]] | None = None
    for combo in combinations:
        loose = solve((combo,), NutritionTarget(points=target.points), ingredients)
        if not loose:
            continue
        plan = loose[0]
        violations = _violations_for(
            plan.estimate.point,
            target,
            profile,
            plan.quality_protein_g,
            reach="jointly_infeasible",
            applied=applied,
        )
        if not violations:
            continue
        key = (len(violations), plan.score)
        if best is None or key < best[0]:
            best = (key, violations)
    return best[1] if best is not None else ()


def _blocking_violations(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping,
    profile: Profile | None,
    *,
    applied: tuple[str, ...] = (),
    empty_required_slots: tuple[str, ...] = (),
) -> tuple[Violation, ...]:
    """Every bound blocking this profile, structural and joint together.

    ``docs/audit_log.md`` findings 24 and 26, which are the same defect from
    opposite directions and are both fixed by not stopping early.

    This function used to return the structurally-unreachable bounds *or*, only
    if there were none, the nearest plate's misses. Both halves were wrong:

    - **It stopped at the first cause.** From slice 4 onward a South Indian
      decline named the quality-protein floor and nothing else, because an
      unreachable quality floor made the first half non-empty and the second
      half never ran. Energy, fat and sodium were blocking too and went unsaid.
      Four problems were reported as one.
    - **When it did reach the second half, it picked the wrong plate.** See
      ``_nearest_plate_violations``.

    Both halves now always run and their results are merged, keyed by
    (macro, kind) so a bound reported as structurally unreachable is not also
    reported as jointly infeasible — the stronger claim wins, because
    "no plate can do this" and "no plate can do this *alongside the rest*" are
    not two problems.
    """

    if not combinations:
        return (
            Violation(
                "",
                "no_candidates",
                0.0,
                0.0,
                reach="empty_pool",
                relaxability="never_relaxed",
                blocking_slots=tuple(empty_required_slots),
            ),
        )

    unreachable = _unreachable_violations(
        combinations, target, ingredients, profile, applied
    )
    already = {(v.macro, v.kind) for v in unreachable}
    joint = tuple(
        v
        for v in _nearest_plate_violations(
            combinations, target, ingredients, profile, applied
        )
        if (v.macro, v.kind) not in already
    )
    out = unreachable + joint
    if out:
        return out
    # No bound is unreachable and the nearest plate meets every one of them --
    # which means `solve` should have found it. Reaching here is a disagreement
    # between the solver's gate and this module's, not a profile the library
    # cannot serve, so it is reported as the honest "nothing to hand you"
    # rather than dressed up as a nutritional cause.
    return (
        Violation(
            "", "no_candidates", 0.0, 0.0, reach="empty_pool",
            relaxability="never_relaxed",
        ),
    )


def plan_within_ladder(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping,
    *,
    profile: Profile | None = None,
    empty_required_slots: tuple[str, ...] = (),
) -> LadderOutcome:
    """Solve, and if nothing is feasible, walk the ladder in order.

    The ladder exists because under this architecture the LLM cannot produce
    an invalid plan (CLAUDE.md, "Relaxation ladder"): the only remaining
    failure is the solver having nothing to hand it, which is what an empty
    result from ``solve`` means.

    ``combinations`` must be the **enumerated** set, not one already narrowed
    by ``feasible_combinations``. The pre-filter is run here, once per rung,
    against that rung's widened target: a combination discarded under the
    original target may well be feasible under a relaxed one, and pre-filtering
    outside this function would make those unrecoverable — the ladder would
    widen a target and then search a set that had already been pruned to fit
    the tight one, declining plans it should have found. Running it inside is
    also faster, since each rung's solve sees fewer combinations.

    ``empty_required_slots`` is which of the template's required courses had no
    legal selection, when ``combinations`` is empty because of that. This
    function cannot work it out for itself — it receives combinations, not a
    pool — and without it a decline can only say "nothing survived filtering",
    which tells a vegan asking for a South Indian lunch nothing about the curd
    course being the reason. Optional so a caller holding only combinations
    still works; ``core.planner.plan.plan_meal`` supplies it from
    ``core.planner.combinations.unfillable_slots``.
    """

    locked = locked_macros(profile)

    def _attempt(t: NutritionTarget) -> tuple[SolvedPlan, ...]:
        return solve(feasible_combinations(combinations, t, ingredients), t, ingredients)

    solved = _attempt(target)
    if solved:
        return LadderOutcome(
            plan=solved[0],
            result=validate(solved[0], target, profile=profile),
            target_used=target,
        )

    current = target
    applied: list[str] = []
    skipped: list[str] = []
    for step in RELAXATION_ORDER:
        if step.is_fully_locked(locked):
            # Every macro this rung would touch is locked by a disclosed
            # condition, so the rung is not merely ineffective — it must not
            # run. Recorded, but not as a relaxation that happened.
            skipped.append(step.name)
            continue

        current = step.apply(current, locked)
        applied.append(step.name)
        solved = _attempt(current)
        if not solved:
            continue

        plan = solved[0]
        disclosure = None
        if any(
            s.requires_disclosure for s in RELAXATION_ORDER if s.name in applied
        ):
            disclosure = _protein_disclosure(plan.estimate.point, target)
        return LadderOutcome(
            plan=plan,
            result=validate(
                plan,
                current,
                profile=profile,
                relaxation_applied=tuple(applied),
                disclosure=disclosure,
            ),
            target_used=current,
            skipped_locked_steps=tuple(skipped),
        )

    violations = _blocking_violations(
        combinations,
        current,
        ingredients,
        profile,
        applied=tuple(applied),
        empty_required_slots=empty_required_slots,
    )
    locked_hits = tuple(v for v in violations if v.locked_by)
    decline = "No plan could be built for this profile: " + "; ".join(
        v.describe() for v in violations
    )
    if locked_hits:
        decline += (
            ". The blocking constraint is locked by a disclosed condition and was "
            "deliberately not relaxed; this system is not a substitute for "
            "clinical nutrition guidance."
        )
    return LadderOutcome(
        plan=None,
        result=ValidationResult(
            passed=False,
            actual_point_estimate=NutritionVector.zero(),
            actual_interval=(NutritionVector.zero(), NutritionVector.zero()),
            violations=violations,
            relaxation_applied=tuple(applied),
            disclosure=decline,
        ),
        target_used=current,
        skipped_locked_steps=tuple(skipped),
    )
