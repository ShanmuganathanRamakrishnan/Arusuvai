"""Integer unit-count solving: ranking by weighted deviation, the thin case,
the moderate-profile property test, and swap_candidates."""

from __future__ import annotations

import random

import pytest

from core.foods import templates
from core.foods.models import MealTemplate, TemplateSlot
from core.foods.quality import QUALITY_PROTEIN_KEY
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import (
    MealCombination,
    enumerate_combinations,
    feasible_combinations,
    macro_bounds,
)
from core.planner.solver import SolvedPlan, solve, solve_combination, swap_candidates
from core.planner.validator import validate
from core.nutrition.target import NutritionTarget, simple_target
from core.schemas import DietPattern, MealSlot, Region
from tests.factories import (
    FEASIBILITY_COMPONENTS,
    FEASIBILITY_INGREDIENTS,
    FEASIBILITY_TEMPLATE,
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
    SOUTH_LUNCH_MAX_PROTEIN_G,
)


def _feasibility_pool():
    return build_candidate_pool(
        FEASIBILITY_COMPONENTS,
        FEASIBILITY_INGREDIENTS,
        template=FEASIBILITY_TEMPLATE,
        diet_pattern=DietPattern.VEGETARIAN,
        dev_mode=False,
    )


def _south_lunch_pool():
    return build_candidate_pool(
        SOUTH_LUNCH_COMPONENTS,
        SOUTH_LUNCH_INGREDIENTS,
        template=templates.SOUTH_LUNCH,
        diet_pattern=DietPattern.VEGETARIAN,
        dev_mode=False,
    )


# Every serving unit in the feasibility fixture is pinned to exactly one
# legal count, so each combo's macro total is a single exact number:
#   (a1,b1) energy=150 protein=7   (a1,b2) energy=250 protein=13
#   (a2,b1) energy=250 protein=12  (a2,b2) energy=350 protein=18
# floor energy>=100, protein>=5; ceiling energy<=400 -> all four admissible.
# Deviation, weight protein=10 energy=5, ideal energy=250 protein=10:
#   (a1,b1): |150-250|/250*5 + |7-10|/10*10   = 0.4*5 + 0.3*10 = 2.0+3.0 = 5.0
#   (a1,b2): |250-250|/250*5 + |13-10|/10*10  = 0    + 3.0     = 3.0
#   (a2,b1): |250-250|/250*5 + |12-10|/10*10  = 0    + 2.0     = 2.0
#   (a2,b2): |350-250|/250*5 + |18-10|/10*10  = 2.0  + 8.0     = 10.0
_RANKING_TARGET = NutritionTarget(
    floors={"energy_kcal": 100.0, "protein_g": 5.0},
    ceilings={"energy_kcal": 400.0},
    points={"energy_kcal": 250.0, "protein_g": 10.0},
)


class TestRankingByDeviation:
    def test_all_four_combinations_are_admissible(self):
        combos = enumerate_combinations(_feasibility_pool())
        survivors = feasible_combinations(combos, _RANKING_TARGET, FEASIBILITY_INGREDIENTS)
        assert len(survivors) == 4

    def test_solved_plans_are_sorted_best_first_by_hand_computed_score(self):
        combos = enumerate_combinations(_feasibility_pool())
        solved = solve(combos, _RANKING_TARGET, FEASIBILITY_INGREDIENTS)
        assert len(solved) == 4
        got = [(p.combination.recipe_ids(), p.score) for p in solved]
        assert got == [
            (frozenset({"a2", "b1"}), pytest.approx(2.0)),
            (frozenset({"a1", "b2"}), pytest.approx(3.0)),
            (frozenset({"a1", "b1"}), pytest.approx(5.0)),
            (frozenset({"a2", "b2"}), pytest.approx(10.0)),
        ]

    def test_solve_combination_matches_the_top_of_solve(self):
        combos = enumerate_combinations(_feasibility_pool())
        best_combo = next(c for c in combos if c.recipe_ids() == frozenset({"a2", "b1"}))
        plan = solve_combination(best_combo, _RANKING_TARGET, FEASIBILITY_INGREDIENTS)
        assert plan is not None
        assert plan.score == pytest.approx(2.0)
        assert plan.estimate.point.energy_kcal == pytest.approx(250.0)
        assert plan.estimate.point.protein_g == pytest.approx(12.0)


class TestThinFeasibleSet:
    """The audit's 55kg / 1500kcal / 90g protein vegetarian case."""

    def test_the_synthetic_pool_cannot_reach_90g_protein_at_all(self):
        # Highest achievable protein by ANY single combination at every
        # component's max count (2 units each), taking each slot's richest
        # legal selection:
        #   rice_base   pick 1 of 2: rice_b  3.5 * 2 =  7.0
        #   gravy       pick 1 of 2: gravy_a 4.0 * 2 =  8.0
        #   vegetable   pick 1 or 2: (veg_a 2.0 + veg_b 3.0) * 2 = 10.0
        #   curd_course pick 1 of 2: curd_a  3.0 * 2 =  6.0
        #   crisp       pick 0 or 1: crisp_a 1.0 * 2 =  2.0
        #   total = 33.0 g
        assert SOUTH_LUNCH_MAX_PROTEIN_G == pytest.approx(33.0)
        assert SOUTH_LUNCH_MAX_PROTEIN_G < 90.0

    def test_the_hand_derived_max_matches_what_enumeration_actually_reaches(self):
        # The hand-derived figure above was wrong once (33.6, from summing two
        # crisps in a slot that admits at most one) and its own test agreed
        # with it, because both restated the same derivation. This pins it
        # against the combination space the planner really enumerates, so the
        # arithmetic and the code have to agree with each OTHER, not just with
        # themselves. Cross-check, not snapshot: the value on the left is
        # still hand-derived and readable in tests/factories.py.
        combos = enumerate_combinations(_south_lunch_pool())
        reachable = max(
            sum(
                macro_bounds(c, "protein_g", SOUTH_LUNCH_INGREDIENTS)[1]
                for c in combo.components
            )
            for combo in combos
        )
        assert reachable == pytest.approx(SOUTH_LUNCH_MAX_PROTEIN_G)

    def test_solve_reports_zero_feasible_rather_than_forcing_one(self):
        target = simple_target(energy_kcal=1500.0, protein_g_min=90.0)
        combos = enumerate_combinations(_south_lunch_pool())
        survivors = feasible_combinations(combos, target, SOUTH_LUNCH_INGREDIENTS)
        assert survivors == ()  # the O(1) pre-filter already catches it
        assert solve(combos, target, SOUTH_LUNCH_INGREDIENTS) == ()

    def test_the_real_library_yields_nothing_for_a_macro_reason_not_an_empty_pool(
        self, library, ingredients
    ):
        # A second, independent thin case, and it changed kind on 2026-08-02.
        # It used to be thin because south_breakfast's gravy and chutney slots
        # had no candidates at all, so enumeration returned nothing. T4 filled
        # both, so the template now enumerates and the "zero feasible" outcome
        # has to come from the macros instead -- which is the more interesting
        # version of the same claim, and the one that survives more recipes
        # landing. 90 g of protein at one breakfast is out of reach for any
        # combination of a dosa, a sambar and a chutney.
        pool = build_candidate_pool(
            library.components.values(),
            ingredients,
            template=templates.SOUTH_BREAKFAST,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        target = simple_target(energy_kcal=1500.0, protein_g_min=90.0)
        combos = enumerate_combinations(pool)
        assert combos != (), "south_breakfast must enumerate; it has been populated"
        assert feasible_combinations(combos, target, ingredients) == ()
        assert solve(combos, target, ingredients) == ()


class TestModerateProfileProperty:
    def test_200_random_moderate_profiles_all_solve(self):
        # Range chosen inside the synthetic pool's achievable envelope: the
        # single richest combination (every slot's most valuable option, max
        # counts) reaches 950 kcal / 33.6 g protein; the sparsest reaches 280
        # kcal / 8.7 g protein (see tests/factories.py). Sampling well inside
        # that envelope with a generous +/-20% energy tolerance leaves ample
        # room across the pool's 72 combinations x per-component count
        # domains for at least one to land in range — verified empirically
        # below (seeded, so the run is reproducible) rather than asserted.
        rng = random.Random(20260721)
        pool = _south_lunch_pool()
        combos = enumerate_combinations(pool)
        failures = []
        for _ in range(200):
            energy = rng.uniform(450.0, 650.0)
            protein_min = rng.uniform(9.0, 18.0)
            target = simple_target(
                energy_kcal=energy, protein_g_min=protein_min, energy_tolerance=0.20
            )
            survivors = feasible_combinations(combos, target, SOUTH_LUNCH_INGREDIENTS)
            solved = solve(survivors, target, SOUTH_LUNCH_INGREDIENTS)
            if not solved:
                failures.append((energy, protein_min))
        assert failures == [], f"{len(failures)}/200 moderate profiles found no solution: {failures[:5]}"


class TestSwapCandidates:
    def test_swap_holds_the_other_slot_fixed_and_matches_the_hand_computed_alternative(self):
        # Starting plan: best of the four is (a2,b1), score 2.0 (see
        # TestRankingByDeviation). Swapping slot "b" with a2 held fixed has
        # only one other candidate (b2, since the slot's k=2 and one is
        # "current"), giving combo (a2,b2) — already hand-computed above at
        # score 10.0.
        combos = enumerate_combinations(_feasibility_pool())
        solved = solve(combos, _RANKING_TARGET, FEASIBILITY_INGREDIENTS)
        best = solved[0]
        assert best.combination.recipe_ids() == frozenset({"a2", "b1"})

        slot_b = FEASIBILITY_TEMPLATE.slots[1]
        assert slot_b.name == "b"
        alternatives = swap_candidates(
            best, slot_b, _RANKING_TARGET, _feasibility_pool(), FEASIBILITY_INGREDIENTS
        )
        assert len(alternatives) == 1
        assert alternatives[0].combination.recipe_ids() == frozenset({"a2", "b2"})
        assert alternatives[0].score == pytest.approx(10.0)

    def test_swap_never_returns_the_current_selection_as_its_own_alternative(self):
        combos = enumerate_combinations(_feasibility_pool())
        solved = solve(combos, _RANKING_TARGET, FEASIBILITY_INGREDIENTS)
        best = solved[0]
        slot_a = FEASIBILITY_TEMPLATE.slots[0]
        alternatives = swap_candidates(
            best, slot_a, _RANKING_TARGET, _feasibility_pool(), FEASIBILITY_INGREDIENTS
        )
        assert all(alt.combination.recipe_ids() != best.combination.recipe_ids() for alt in alternatives)

    def test_swap_that_would_leave_target_unmet_is_not_offered(self):
        # Ceiling energy<=300 makes (a2,b2)=350 inadmissible, so it is one of
        # the four combos solve() itself excludes:
        #   (a1,b1)=150,7 ok   (a1,b2)=250,13 ok   (a2,b1)=250,12 ok
        #   (a2,b2)=350,18 -> over ceiling, not in `solved`.
        # Starting from (a1,b2) and swapping slot "a" (only other candidate is
        # a2, since k=2 and a1 is current) with b2 held fixed reproduces
        # exactly the excluded (a2,b2) combo — so no alternative is offered.
        tight = NutritionTarget(
            floors={"protein_g": 5.0},
            ceilings={"energy_kcal": 300.0},
            points={"energy_kcal": 250.0, "protein_g": 10.0},
        )
        combos = enumerate_combinations(_feasibility_pool())
        solved = solve(combos, tight, FEASIBILITY_INGREDIENTS)
        assert len(solved) == 3
        assert frozenset({"a2", "b2"}) not in {p.combination.recipe_ids() for p in solved}
        start = next(p for p in solved if p.combination.recipe_ids() == frozenset({"a1", "b2"}))
        slot_a = FEASIBILITY_TEMPLATE.slots[0]
        alternatives = swap_candidates(start, slot_a, tight, _feasibility_pool(), FEASIBILITY_INGREDIENTS)
        assert alternatives == ()


# --------------------------------------------------------------------------
# An all-optional template, built here rather than in tests/factories.py: it
# exists to reach one branch of `solve_combination` and nothing else in the
# suite has a use for it. Every real template in core/foods/templates.py has
# at least one required slot, so enumeration can never hand the solver an
# empty component tuple in production -- which is exactly why the branch
# needs a test rather than a plate.
# --------------------------------------------------------------------------

_ALL_OPTIONAL_TEMPLATE = MealTemplate(
    id="all_optional",
    region=Region.SOUTH_INDIAN,
    meal_slot=MealSlot.SNACK,
    slots=(
        TemplateSlot(
            name="crisp",
            accepted_categories=frozenset({"appalam"}),
            required=False,
            min_selections=0,
            max_selections=1,
        ),
    ),
)


def _empty_plate() -> MealCombination:
    """The zero-selection assignment of an all-optional template."""

    return MealCombination(template=_ALL_OPTIONAL_TEMPLATE, slot_selections=((),))


class TestTheEmptyPlate:
    """``solve_combination``'s no-components branch is still gated.

    A combination with nothing on it produces the all-zero point estimate, and
    the temptation in that branch is to short-circuit: no food, nothing to
    check. That is wrong in the one direction that matters. Zero meets every
    ceiling trivially, so an ungated empty plate is admissible against any
    target whose bounds are all ceilings -- the solver would return a plan
    holding no food and score it 0.0, the best possible score, and it would
    rank first.
    """

    def test_an_empty_plate_is_rejected_by_a_floor(self):
        target = simple_target(energy_kcal=600.0, protein_g_min=15.0)
        assert (
            solve_combination(_empty_plate(), target, FEASIBILITY_INGREDIENTS) is None
        )

    def test_an_empty_plate_is_rejected_by_a_quality_floor_alone(self):
        # Ceilings only, so every macro bound is met by zero. The quality floor
        # is the only thing left that can reject it, and it must: an empty plate
        # carries 0 g of protein from any source, qualifying or not.
        target = NutritionTarget(
            ceilings={"energy_kcal": 600.0, "sodium_mg": 800.0},
            quality_protein_floor_g=11.2,
        )
        assert (
            solve_combination(_empty_plate(), target, FEASIBILITY_INGREDIENTS) is None
        )

    def test_an_empty_plate_is_returned_when_no_bound_excludes_it(self):
        # Control, and the reason the branch exists at all rather than being
        # replaced by `return None`. With ceilings only and no quality floor,
        # zero really is admissible, and the honest answer is a plan with no
        # components -- not a decline.
        target = NutritionTarget(ceilings={"energy_kcal": 600.0})
        plan = solve_combination(_empty_plate(), target, FEASIBILITY_INGREDIENTS)
        assert plan is not None
        assert plan.unit_counts == {}
        assert plan.estimate.point.energy_kcal == pytest.approx(0.0)


class TestUnsetQualityProteinIsConservative:
    """``SolvedPlan.quality_protein_g`` defaults to 0.0, never to "plenty".

    CLAUDE.md's round-4 addendum, applied to a field rather than to a recipe:
    the cheapest authoring path -- omitting the value -- must not produce the
    most confident-looking output. Here the cheap path is any code that builds
    a ``SolvedPlan`` without saying how much qualifying protein it has, and the
    confident-looking output would be sailing past a quality floor the plate
    was never measured against.
    """

    def _plan_without_the_field(self):
        # Constructed positionally-by-keyword with `quality_protein_g` omitted,
        # which is the shape this test is about. Real components, so the plan
        # is otherwise well-formed and only the one field is unstated.
        combos = enumerate_combinations(_feasibility_pool())
        solved = solve(combos, _RANKING_TARGET, FEASIBILITY_INGREDIENTS)
        best = solved[0]
        return SolvedPlan(
            combination=best.combination,
            unit_counts=best.unit_counts,
            estimate=best.estimate,
            score=best.score,
        )

    def test_the_default_is_zero(self):
        assert self._plan_without_the_field().quality_protein_g == pytest.approx(0.0)

    def test_an_unstated_plan_fails_a_quality_floor_rather_than_passing_it(self):
        # The assertion that would go red on a permissive default. A plan that
        # never said what its quality protein was must be declined against any
        # floor above zero -- the direction of the failure is the whole point,
        # so a test asserting only `== 0.0` would not catch a default of, say,
        # 1e9 being compared as "plenty" somewhere downstream.
        target = NutritionTarget(
            ceilings={"energy_kcal": 10_000.0},
            quality_protein_floor_g=11.2,
        )
        result = validate(self._plan_without_the_field(), target)
        assert not result.passed
        assert any(v.macro == QUALITY_PROTEIN_KEY for v in result.violations)
