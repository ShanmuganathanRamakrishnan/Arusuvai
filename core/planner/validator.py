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
Every step widens or drops a *tolerance* — a floor or a ceiling. No step
reads, writes, or scales an uncertainty figure, because uncertainty is a
property of the data and not a knob (CLAUDE.md, "Uncertainty"). The two axes
never multiply: a plan does not become admissible because its data got worse.

Steps fire in order and cumulatively, each on a target already widened by the
ones before it, and the solver is re-run after each. The first step that
yields a feasible plan wins; the ladder stops there rather than continuing to
the loosest target that would also work.

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

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from core.foods.models import NutritionVector
from core.foods.nutrition_of import unit_for
from core.nutrition import citations
from core.planner.combinations import MealCombination, feasible_combinations, macro_bounds
from core.planner.solver import SolvedPlan, solve
from core.nutrition.target import NutritionTarget, band
from core.schemas import ClinicalFlag, Profile

__all__ = [
    "LOCKED_CONSTRAINTS",
    "RELAXATION_ORDER",
    "RelaxationStep",
    "Violation",
    "ValidationResult",
    "locked_macros",
    "validate",
    "plan_within_ladder",
]


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
    — step 1 *drops* two bounds outright while steps 2-4 widen a band around a
    point — and flattening that into a table would have meant a sentinel value
    standing for "remove this bound", which reads as a number and is not one.
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


def _drop_bounds(
    target: NutritionTarget, locked: frozenset[str], *, floors: tuple[str, ...] = (),
    ceilings: tuple[str, ...] = (),
) -> NutritionTarget:
    new_floors = {m: v for m, v in target.floors.items() if m in locked or m not in floors}
    new_ceilings = {m: v for m, v in target.ceilings.items() if m in locked or m not in ceilings}
    return NutritionTarget(floors=new_floors, ceilings=new_ceilings, points=target.points)


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
            ceilings[macro] = hi
    return NutritionTarget(floors=floors, ceilings=ceilings, points=target.points)


def _relax_sodium_fibre(target: NutritionTarget, locked: frozenset[str]) -> NutritionTarget:
    # Dropped outright rather than widened: both are one-sided guidance bounds
    # with no ideal point to widen around, and CLAUDE.md describes this rung as
    # setting aside "general health guidance, not the product's core
    # nutritional claim" — not as trading a tight guideline for a loose one.
    return _drop_bounds(target, locked, floors=("fibre_g",), ceilings=("sodium_mg",))


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
    """Lower the protein floor partially — never remove it.

    Protein has a floor and no ceiling, so ``_widen_band`` is the wrong shape:
    widening symmetrically would also invent a ceiling. This rung lowers the
    floor by the registered fraction and stops; the floor still exists, and a
    plan that cannot reach even the lowered floor is still declined.
    """

    if "protein_g" in locked:
        return target
    point = target.point("protein_g")
    if point is None or "protein_g" not in target.floors:
        return target
    fraction = citations.value_of("tolerance.protein_relaxed_fraction")
    floors = dict(target.floors)
    floors["protein_g"] = point * (1.0 - fraction)
    return NutritionTarget(floors=floors, ceilings=target.ceilings, points=target.points)


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

    def describe(self) -> str:
        unit = unit_for(self.macro)
        if self.kind == "no_candidates":
            return (
                "no recipe combination survived filtering for this profile, so "
                "there was nothing to solve"
            )
        direction = "below its floor of" if self.kind == "below_floor" else "above its ceiling of"
        text = (
            f"{self.macro} is {self.actual:.1f}{unit}, {direction} "
            f"{self.bound:.1f}{unit}"
        )
        if self.locked_by:
            names = ", ".join(f.value for f in self.locked_by)
            text += f" (locked by disclosed condition: {names}; never relaxed)"
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


def _violations_for(
    point: NutritionVector, target: NutritionTarget, profile: Profile | None
) -> tuple[Violation, ...]:
    out: list[Violation] = []
    for macro in sorted(target.bounded_macros()):
        value = getattr(point, macro)
        floor = target.floor(macro)
        ceiling = target.ceiling(macro)
        if floor is not None and value < floor:
            out.append(
                Violation(macro, "below_floor", value, floor, _flags_locking(macro, profile))
            )
        if ceiling is not None and value > ceiling:
            out.append(
                Violation(macro, "above_ceiling", value, ceiling, _flags_locking(macro, profile))
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
    violations = _violations_for(estimate.point, target, profile)
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


def _blocking_violations(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping,
    profile: Profile | None,
) -> tuple[Violation, ...]:
    """Which specific bound the library cannot reach, given the final target.

    Only genuinely unreachable bounds are reported. A target can also be
    infeasible because two individually-reachable bounds cannot be met at the
    same time; in that case this returns every bound the best-case combination
    misses, which is the closest honest answer available without solving the
    interaction — never a generic failure.
    """

    if not combinations:
        return (Violation("", "no_candidates", 0.0, 0.0),)

    out: list[Violation] = []
    for macro in sorted(target.bounded_macros()):
        lowest, highest = _reach(combinations, macro, ingredients)
        floor = target.floor(macro)
        ceiling = target.ceiling(macro)
        if floor is not None and highest < floor:
            out.append(
                Violation(macro, "below_floor", highest, floor, _flags_locking(macro, profile))
            )
        if ceiling is not None and lowest > ceiling:
            out.append(
                Violation(macro, "above_ceiling", lowest, ceiling, _flags_locking(macro, profile))
            )

    if out:
        return tuple(out)

    # Every bound is individually reachable but no single assignment meets them
    # together. Report the best available plan's own misses rather than
    # inventing a reason.
    best: tuple[float, tuple[Violation, ...]] | None = None
    for combo in combinations:
        loose = solve((combo,), NutritionTarget(points=target.points), ingredients)
        if not loose:
            continue
        violations = _violations_for(loose[0].estimate.point, target, profile)
        score = loose[0].score
        if violations and (best is None or score < best[0]):
            best = (score, violations)
    if best is not None:
        return best[1]
    return (Violation("", "no_candidates", 0.0, 0.0),)


def plan_within_ladder(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping,
    *,
    profile: Profile | None = None,
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

    violations = _blocking_violations(combinations, current, ingredients, profile)
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
