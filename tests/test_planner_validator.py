"""The point-estimate gate, the relaxation ladder, and clinical locking.

Every expected value here is hand-derived from ``tests/factories.py``'s
per-100g figures, which are readable without running anything: each synthetic
recipe is a single ingredient at ``grams_per_unit=100``, so one unit of
``rice_a`` is exactly ``rice_a``'s row.
"""

from __future__ import annotations

import pytest

from core.foods import templates
from core.foods.models import Component, NutritionVector
from core.foods.nutrition_of import nutrition_of_components
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import (
    MealCombination,
    enumerate_combinations,
    feasible_combinations,
)
from core.planner.solver import SolvedPlan, solve
from core.nutrition.target import NutritionTarget, simple_target
from core.planner.validator import (
    LOCKED_CONSTRAINTS,
    RELAXATION_ORDER,
    ValidationResult,
    Violation,
    locked_macros,
    plan_within_ladder,
    validate,
)
from core.schemas import (
    MACRO_KEYS,
    ActivityLevel,
    ClinicalFlag,
    DietPattern,
    Goal,
    Profile,
    Sex,
)
from tests.factories import (
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
    SOUTH_LUNCH_MAX_PROTEIN_G,
    SOUTH_LUNCH_RECIPES,
)

ING = SOUTH_LUNCH_INGREDIENTS


def _pool():
    return build_candidate_pool(
        SOUTH_LUNCH_COMPONENTS,
        SOUTH_LUNCH_INGREDIENTS,
        template=templates.SOUTH_LUNCH,
        diet_pattern=DietPattern.VEGETARIAN,
    )


def _combos():
    return enumerate_combinations(_pool())


def _profile(*flags: ClinicalFlag) -> Profile:
    """The audit's case: 55 kg vegetarian woman, light activity."""

    return Profile(
        weight_kg=55.0,
        height_cm=160.0,
        age_years=30,
        sex=Sex.FEMALE,
        activity=ActivityLevel.LIGHT,
        goal=Goal.MAINTAIN,
        diet=DietPattern.VEGETARIAN,
        clinical_flags=frozenset(flags),
    )


def _plan_of(*component_ids: str) -> SolvedPlan:
    """A one-slot plan holding the named components at 1 unit each.

    Built by hand rather than by solving, so the gate tests control the point
    estimate exactly instead of depending on what the solver happens to pick.
    """

    template = templates.SOUTH_LUNCH
    components = tuple(
        Component(recipe=SOUTH_LUNCH_RECIPES[cid], category=cid) for cid in component_ids
    )
    combo = MealCombination(
        template=template,
        slot_selections=tuple(components if i == 0 else () for i in range(len(template.slots))),
    )
    items = [(c, 1) for c in components]
    return SolvedPlan(
        combination=combo,
        unit_counts={c.id: 1 for c in components},
        estimate=nutrition_of_components(items, ING),
        score=0.0,
    )


class TestTheGateIsOnThePointEstimate:
    def test_a_plan_inside_every_bound_passes(self):
        # rice_a at 1 unit: 130 kcal, 2.7 g protein (tests/factories.py).
        plan = _plan_of("rice_a")
        target = NutritionTarget(
            floors={"energy_kcal": 100.0, "protein_g": 2.0},
            ceilings={"energy_kcal": 200.0},
        )
        result = validate(plan, target)
        assert result.passed
        assert result.violations == ()
        assert result.actual_point_estimate.energy_kcal == pytest.approx(130.0)

    def test_below_floor_is_reported_with_the_actual_and_the_bound(self):
        plan = _plan_of("rice_a")  # 2.7 g protein
        target = NutritionTarget(floors={"protein_g": 10.0})
        result = validate(plan, target)
        assert not result.passed
        (violation,) = result.violations
        assert violation.kind == "below_floor"
        assert violation.macro == "protein_g"
        assert violation.actual == pytest.approx(2.7)
        assert violation.bound == pytest.approx(10.0)
        assert "2.7g" in violation.describe() and "10.0g" in violation.describe()

    def test_above_ceiling_is_reported(self):
        plan = _plan_of("gravy_a")  # 300 mg sodium
        target = NutritionTarget(ceilings={"sodium_mg": 100.0})
        result = validate(plan, target)
        assert not result.passed
        (violation,) = result.violations
        assert violation.kind == "above_ceiling"
        assert violation.actual == pytest.approx(300.0)

    def test_both_directions_at_once_are_both_reported(self):
        plan = _plan_of("gravy_a")  # 80 kcal, 4.0 g protein, 300 mg sodium
        target = NutritionTarget(
            floors={"protein_g": 20.0}, ceilings={"sodium_mg": 100.0}
        )
        result = validate(plan, target)
        kinds = {(v.macro, v.kind) for v in result.violations}
        assert kinds == {("protein_g", "below_floor"), ("sodium_mg", "above_ceiling")}

    def test_a_wider_interval_never_makes_a_plan_pass(self):
        """The perverse-incentive test CLAUDE.md's uncertainty section names.

        Two plans with the SAME point estimate and different band widths must
        get the same verdict. If the gate ever read the interval, the wide one
        would pass a floor the narrow one misses — worse data buying an easier
        pass. Constructed directly rather than via two recipes so the only
        difference between them is the band.
        """

        point = NutritionVector(
            *(50.0 if macro == "protein_g" else 0.0 for macro in MACRO_KEYS)
        )
        target = NutritionTarget(floors={"protein_g": 60.0})

        narrow = _replace_estimate(_plan_of("rice_a"), point, spread=0.01)
        wide = _replace_estimate(_plan_of("rice_a"), point, spread=0.90)
        # wide.high.protein_g = 95 > 60: an interval-overlap gate would pass it.
        assert wide.estimate.high.protein_g > 60.0
        assert narrow.estimate.high.protein_g < 60.0
        assert validate(narrow, target).passed is False
        assert validate(wide, target).passed is False


def _replace_estimate(plan: SolvedPlan, point: NutritionVector, *, spread: float) -> SolvedPlan:
    from dataclasses import replace

    from core.foods.nutrition_of import NutritionEstimate

    return replace(
        plan,
        estimate=NutritionEstimate(
            point=point,
            low=point * (1.0 - spread),
            high=point * (1.0 + spread),
        ),
    )


class TestLadderShape:
    def test_the_order_is_claude_mds_order(self):
        assert [s.name for s in RELAXATION_ORDER] == [
            "sodium_max_fibre_min",
            "fat_carb_tolerance",
            "energy_tolerance",
            "protein_tolerance",
        ]

    def test_only_protein_requires_disclosure(self):
        disclosing = [s.name for s in RELAXATION_ORDER if s.requires_disclosure]
        assert disclosing == ["protein_tolerance"]

    def test_every_clinical_flag_locks_something(self):
        # A flag with no entry here would read as protective to a user and do
        # nothing at all, which is the failure mode this project is organised
        # around. Asserted rather than trusted.
        assert set(LOCKED_CONSTRAINTS) == set(ClinicalFlag)
        assert all(macros for macros in LOCKED_CONSTRAINTS.values())

    def test_locked_macros_unions_every_flag(self):
        profile = _profile(ClinicalFlag.HYPERTENSION, ClinicalFlag.DIABETES)
        assert locked_macros(profile) == frozenset({"sodium_mg", "carb_g"})
        assert locked_macros(None) == frozenset()


class TestLadderFires:
    def test_an_already_feasible_target_relaxes_nothing(self):
        # 700 kcal +/-5% with a 20 g protein floor is comfortably inside the
        # pool's reach (protein tops out at 33.0 g, energy at 910).
        target = simple_target(energy_kcal=700.0, protein_g_min=20.0)
        outcome = plan_within_ladder(_combos(), target, ING)
        assert outcome.result.passed
        assert outcome.result.relaxation_applied == ()
        assert outcome.result.disclosure is None

    def test_the_sodium_rung_fires_first_and_silently(self):
        # Every combination carries >= 406 mg sodium (gravy_b 250 + rice_a 1 +
        # veg_c 120 + curd_b 35 at 1 unit each), so a 500 mg ceiling with a
        # 15 g protein floor is unsatisfiable until sodium is dropped — and
        # sodium is rung 1, so nothing further should fire.
        target = simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)
        outcome = plan_within_ladder(_combos(), target, ING)
        assert outcome.result.passed
        assert outcome.result.relaxation_applied == ("sodium_max_fibre_min",)
        # Rung 1 is "general health guidance" — disclosed nowhere, by design.
        assert outcome.result.disclosure is None

    def test_the_sodium_rung_widens_the_ceiling_rather_than_dropping_it(self):
        # Pins CLAUDE.md's relaxation-ladder addendum directly: rung 1 must
        # widen sodium's ceiling by the registered 0.50 fraction, not remove
        # it. A prior implementation dropped the bound outright and every
        # other test in this file passed anyway, because none of them pinned
        # the actual widened value -- this one would have failed against that
        # implementation (ceiling would be None here, not 750.0).
        step = next(s for s in RELAXATION_ORDER if s.name == "sodium_max_fibre_min")
        target = simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)
        relaxed = step.apply(target, locked_macros(None))
        assert relaxed.ceiling("sodium_mg") == pytest.approx(750.0)

        # Mutate the registered constant and confirm the widened value moves
        # with it (CLAUDE.md, "no nutritional number may be hand-duplicated" —
        # a test that only checks a fixed number against itself cannot catch
        # a constant drifting from its call site).
        import dataclasses

        from core.nutrition import citations

        key = "tolerance.sodium_relaxed_fraction"
        original_constant = citations.constant(key)
        citations._CONSTANTS[key] = dataclasses.replace(
            original_constant, value=original_constant.value + 0.10
        )
        try:
            moved = step.apply(target, locked_macros(None))
            assert moved.ceiling("sodium_mg") == pytest.approx(
                500.0 * (1.0 + original_constant.value + 0.10)
            )
            assert moved.ceiling("sodium_mg") != pytest.approx(relaxed.ceiling("sodium_mg"))
        finally:
            citations._CONSTANTS[key] = original_constant

    def test_a_locked_sodium_ceiling_is_never_widened_by_this_rung(self):
        step = next(s for s in RELAXATION_ORDER if s.name == "sodium_max_fibre_min")
        target = simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)
        relaxed = step.apply(target, frozenset({"sodium_mg"}))
        assert relaxed.ceiling("sodium_mg") == pytest.approx(500.0)

    def test_relaxation_widens_tolerance_and_never_uncertainty(self):
        target = simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)
        outcome = plan_within_ladder(_combos(), target, ING)
        # The plan's own band is a property of the data; the ladder must not
        # have touched it. rice/gravy/... are all 3% composition, 0% process.
        assert outcome.plan is not None
        assert outcome.result.actual_interval[1].protein_g == pytest.approx(
            outcome.result.actual_point_estimate.protein_g * 1.03
        )

    def test_the_protein_rung_fires_last_and_discloses(self):
        # Highest protein any single combination reaches is 33.0 g, and the
        # solver must also satisfy the energy band. A 32 g floor is out of
        # reach; the relaxed floor is 32 * (1 - 0.15) = 27.2 g, which is
        # reachable, so the plan comes back only after rung 4.
        target = simple_target(energy_kcal=700.0, protein_g_min=32.0)
        outcome = plan_within_ladder(_combos(), target, ING)
        assert outcome.result.passed
        assert "protein_tolerance" in outcome.result.relaxation_applied
        assert outcome.result.relaxation_applied[-1] == "protein_tolerance"
        disclosure = outcome.result.disclosure or ""
        assert disclosure.strip()
        # Stated in the target's own units (g), naming both numbers.
        assert "32.0g" in disclosure
        assert "g of protein" in disclosure
        assert outcome.result.actual_point_estimate.protein_g >= 32.0 * 0.85

    def test_relaxation_recovers_combinations_the_tight_pre_filter_discarded(self):
        # The bug this pins: if the O(1) pre-filter runs once, against the
        # ORIGINAL target, every rung afterwards searches a set already pruned
        # to fit the target it is trying to widen — so relaxation cannot
        # recover anything the tight target excluded, and the ladder declines
        # plans it should find. The ladder therefore re-runs the pre-filter per
        # rung, and this asserts the recovered set is genuinely larger.
        combos = _combos()
        tight = simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)
        outcome = plan_within_ladder(combos, tight, ING)
        assert outcome.result.passed
        assert outcome.plan is not None

        under_tight = feasible_combinations(combos, tight, ING)
        under_relaxed = feasible_combinations(combos, outcome.target_used, ING)
        # Dropping the sodium ceiling takes the surviving set from 17 of 144
        # to 141 — the pre-filter is genuinely target-dependent, so which
        # target it runs against decides what the solver can ever see.
        assert len(under_tight) < len(under_relaxed)
        # And the plan actually chosen is one of the recovered ones: it does
        # not survive the tight pre-filter, so a caller who pre-filtered once
        # up front and handed the ladder that set would never have found it.
        assert outcome.plan.combination not in under_tight
        assert outcome.plan.combination in under_relaxed

    def test_a_disclosure_is_structurally_required_not_remembered(self):
        with pytest.raises(ValueError, match="never silent"):
            ValidationResult(
                passed=True,
                actual_point_estimate=NutritionVector.zero(),
                actual_interval=(NutritionVector.zero(), NutritionVector.zero()),
                relaxation_applied=("protein_tolerance",),
                disclosure=None,
            )

    def test_a_decline_may_not_be_generic(self):
        with pytest.raises(ValueError, match="at least one violation"):
            ValidationResult(
                passed=False,
                actual_point_estimate=NutritionVector.zero(),
                actual_interval=(NutritionVector.zero(), NutritionVector.zero()),
                violations=(),
                disclosure="nope",
            )


class TestClinicalLocking:
    """The rung a disclosed condition removes is never walked back onto."""

    SODIUM_BLOCKED = dict(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)

    def test_without_the_flag_the_sodium_ceiling_relaxes_and_the_plan_passes(self):
        outcome = plan_within_ladder(
            _combos(), simple_target(**self.SODIUM_BLOCKED), ING, profile=_profile()
        )
        assert outcome.result.passed
        assert "sodium_max_fibre_min" in outcome.result.relaxation_applied

    def test_with_hypertension_the_same_target_is_declined_instead(self):
        # Same profile, same target, one flag different. This is the whole
        # test: relaxing sodium WOULD have made this feasible (proved by the
        # test above), and the flag makes the system decline rather than take
        # the easy path.
        outcome = plan_within_ladder(
            _combos(),
            simple_target(**self.SODIUM_BLOCKED),
            ING,
            profile=_profile(ClinicalFlag.HYPERTENSION),
        )
        assert outcome.plan is None
        assert not outcome.result.passed
        sodium_violations = [v for v in outcome.result.violations if v.macro == "sodium_mg"]
        assert sodium_violations, "the decline must name sodium specifically"
        assert sodium_violations[0].locked_by == (ClinicalFlag.HYPERTENSION,)
        assert "hypertension" in outcome.result.disclosure
        assert "not a substitute for clinical nutrition guidance" in outcome.result.disclosure

    def test_the_sodium_ceiling_survives_every_rung_for_a_locked_profile(self):
        outcome = plan_within_ladder(
            _combos(),
            simple_target(**self.SODIUM_BLOCKED),
            ING,
            profile=_profile(ClinicalFlag.HYPERTENSION),
        )
        # The final target the ladder arrived at still carries the original
        # ceiling, unwidened: the rung fired for fibre and skipped sodium.
        assert outcome.target_used.ceiling("sodium_mg") == pytest.approx(500.0)

    def test_a_fully_locked_rung_is_skipped_not_recorded_as_applied(self):
        # Kidney disease locks protein, so rung 4's only macro is locked and
        # the rung must not run at all — not run-and-do-nothing, which would
        # report a protein relaxation that never happened.
        target = simple_target(energy_kcal=700.0, protein_g_min=32.0)
        outcome = plan_within_ladder(
            _combos(), target, ING, profile=_profile(ClinicalFlag.CHRONIC_KIDNEY_DISEASE)
        )
        assert "protein_tolerance" not in outcome.result.relaxation_applied
        assert "protein_tolerance" in outcome.skipped_locked_steps
        assert not outcome.result.passed
        assert outcome.target_used.floor("protein_g") == pytest.approx(32.0)

    def test_diabetes_locks_carb_out_of_the_fat_carb_rung(self):
        # Rung 2 touches fat AND carb, so a locked carb must not take the whole
        # rung down with it: fat still widens. Exercised against the rung
        # directly rather than through plan_within_ladder, because whether this
        # rung fires at all depends on the pool being infeasible at rung 1 —
        # a ladder-level version of this test passes vacuously the moment the
        # fixture's numbers shift.
        target = simple_target(
            energy_kcal=700.0, protein_g_min=15.0, fat_g=20.0, carb_g=90.0
        )
        # Default 15%: fat 17.0 - 23.0, carb 76.5 - 103.5.
        assert target.ceiling("fat_g") == pytest.approx(23.0)
        assert target.ceiling("carb_g") == pytest.approx(103.5)

        step = next(s for s in RELAXATION_ORDER if s.name == "fat_carb_tolerance")
        relaxed = step.apply(target, locked_macros(_profile(ClinicalFlag.DIABETES)))
        # Relaxed 25%: fat becomes 15.0 - 25.0; carb must not move at all.
        assert relaxed.floor("fat_g") == pytest.approx(15.0)
        assert relaxed.ceiling("fat_g") == pytest.approx(25.0)
        assert relaxed.floor("carb_g") == pytest.approx(76.5)
        assert relaxed.ceiling("carb_g") == pytest.approx(103.5)

        # Control: with no flag, the same rung widens carb to 67.5 - 112.5.
        unlocked = step.apply(target, frozenset())
        assert unlocked.floor("carb_g") == pytest.approx(67.5)
        assert unlocked.ceiling("carb_g") == pytest.approx(112.5)


class TestThinFeasibleSetDisclosure:
    """The audit's 55 kg / 1500 kcal / 90 g protein vegetarian case."""

    def test_it_declines_and_states_the_protein_gap_in_grams(self):
        target = simple_target(energy_kcal=1500.0, protein_g_min=90.0)
        outcome = plan_within_ladder(_combos(), target, ING, profile=_profile())

        assert outcome.plan is None
        assert not outcome.result.passed

        disclosure = outcome.result.disclosure or ""
        assert disclosure.strip(), "a decline must always explain itself"

        protein = [v for v in outcome.result.violations if v.macro == "protein_g"]
        assert protein, "protein is the blocking constraint and must be named"
        # The gap is stated against what the library can actually reach:
        # 33.0 g (tests/factories.py) versus the relaxed floor of
        # 90 * (1 - 0.15) = 76.5 g.
        assert protein[0].actual == pytest.approx(SOUTH_LUNCH_MAX_PROTEIN_G)
        assert protein[0].bound == pytest.approx(76.5)
        assert "33.0g" in disclosure and "76.5g" in disclosure

    def test_it_exhausts_the_ladder_rather_than_stopping_early(self):
        target = simple_target(energy_kcal=1500.0, protein_g_min=90.0)
        outcome = plan_within_ladder(_combos(), target, ING, profile=_profile())
        assert outcome.result.relaxation_applied == tuple(s.name for s in RELAXATION_ORDER)

    def test_an_empty_combination_set_declines_by_naming_the_empty_pool(self):
        target = simple_target(energy_kcal=700.0, protein_g_min=15.0)
        outcome = plan_within_ladder((), target, ING)
        assert outcome.plan is None
        (violation,) = outcome.result.violations
        assert violation.kind == "no_candidates"
        assert "nothing to solve" in violation.describe()
