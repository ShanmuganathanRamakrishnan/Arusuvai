"""The user swaps a dish by liking; the plate still validates (TASKS_3.md N8).

Owner 2026-09-29: "the user can alternate between dishes based on their
liking, like individual items". Two owner decisions the same day: a pick is
offered and honoured only at the rung the ladder stopped on for the whole set
-- a liking never loosens a limit -- and picks last for one request.

Synthetic South lunch from ``tests/factories.py``, as the shown-plate
preference tests, so each case is decided by the fixture's own numbers:
``crisp_b`` is the salty dish. At a 1000 mg sodium ceiling rung 0 has valid
plates but none with ``crisp_b``; rung 1 admits it.
"""

from __future__ import annotations

from core.foods import templates
from core.nutrition.target import simple_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations, feasible_combinations
from core.planner.solver import solve
from core.planner.validator import RELAXATION_ORDER, plan_within_ladder
from core.schemas import DietPattern
from tests.factories import SOUTH_LUNCH_COMPONENTS, SOUTH_LUNCH_INGREDIENTS

ING = SOUTH_LUNCH_INGREDIENTS
FEASIBLE = simple_target(energy_kcal=700.0, protein_g_min=20.0)
SALTY_NEEDS_RUNG_1 = simple_target(
    energy_kcal=700.0, protein_g_min=20.0, sodium_mg_max=1000.0
)


def _combos():
    return enumerate_combinations(
        build_candidate_pool(
            SOUTH_LUNCH_COMPONENTS, ING,
            template=templates.SOUTH_LUNCH, diet_pattern=DietPattern.VEGETARIAN,
        )
    )


def _ids(plan):
    return {c.recipe.id for c in plan.combination.components}


def _solved(target):
    return solve(feasible_combinations(_combos(), target, ING), target, ING)


def _options(outcome):
    return dict(outcome.swap_options)


class TestAPickIsHonoured:
    def test_a_pick_the_shown_plate_lacks_is_on_the_plate(self):
        solved = _solved(FEASIBLE)
        nearest = _ids(solved[0])
        wanted = next(r for p in solved[1:] for r in _ids(p) if r not in nearest)
        expected = next(p for p in solved if wanted in _ids(p))

        outcome = plan_within_ladder(_combos(), FEASIBLE, ING, picks=frozenset({wanted}))

        assert outcome.result.passed
        assert _ids(outcome.plan) == _ids(expected) != nearest
        # Counts are the solver's, for the nearest plate holding the pick.
        assert outcome.plan.unit_counts == expected.unit_counts

    def test_no_picks_changes_nothing(self):
        plain = plan_within_ladder(_combos(), FEASIBLE, ING)
        assert _ids(plain.plan) == _ids(_solved(FEASIBLE)[0])
        assert plain.plan.unit_counts == _solved(FEASIBLE)[0].unit_counts


class TestAPickNeverLoosensALimit:
    def test_the_fixture_admits_crisp_b_only_after_rung_1(self):
        # Precondition: without it the test below passes whatever picks do.
        assert _solved(SALTY_NEEDS_RUNG_1)
        assert all("crisp_b" not in _ids(p) for p in _solved(SALTY_NEEDS_RUNG_1))
        rung_1 = RELAXATION_ORDER[0].apply(SALTY_NEEDS_RUNG_1, frozenset())
        assert any("crisp_b" in _ids(p) for p in _solved(rung_1))

    def test_a_pick_valid_only_on_a_looser_rung_is_declined(self):
        outcome = plan_within_ladder(
            _combos(), SALTY_NEEDS_RUNG_1, ING, picks=frozenset({"crisp_b"})
        )
        assert outcome.plan is None
        assert not outcome.result.passed
        assert outcome.result.relaxation_applied == ()
        assert outcome.target_used == SALTY_NEEDS_RUNG_1
        assert "crisp_b" in outcome.result.disclosure

    def test_a_declined_pick_is_not_quietly_replaced(self):
        # The nearest plate without the pick is valid; returning it would be
        # the quiet substitution the owner ruled out.
        outcome = plan_within_ladder(
            _combos(), FEASIBLE, ING, picks=frozenset({"no_such_dish"})
        )
        assert outcome.plan is None
        assert "no_such_dish" in outcome.result.disclosure


class TestSwapOptions:
    def test_options_are_every_dish_on_a_valid_plate_per_slot(self):
        outcome = plan_within_ladder(_combos(), FEASIBLE, ING)
        solved = _solved(FEASIBLE)
        for i, slot in enumerate(templates.SOUTH_LUNCH.slots):
            expected = {
                c.recipe.id for p in solved for c in p.combination.slot_selections[i]
            }
            assert set(_options(outcome)[slot.name]) == expected, slot.name

    def test_options_hold_the_rung_the_ladder_stopped_on(self):
        # crisp_b is valid only after rung 1, so it must not be offered.
        outcome = plan_within_ladder(_combos(), SALTY_NEEDS_RUNG_1, ING)
        assert "crisp_b" not in _options(outcome)["crisp"]
        assert _options(outcome)["crisp"]

    def test_other_slots_options_keep_the_pick(self):
        # At the salty target only rice_b sits beside crisp_a on a valid
        # plate, though rice_a is valid on plates without it.
        solved = _solved(SALTY_NEEDS_RUNG_1)
        rice = templates.SOUTH_LUNCH.slots[0]
        with_pick = {c.recipe.id for p in solved if "crisp_a" in _ids(p)
                     for c in p.combination.selection_for(rice)}
        unconstrained = {c.recipe.id for p in solved
                         for c in p.combination.selection_for(rice)}
        # Precondition: without a difference the assertion below cannot fail.
        assert with_pick != unconstrained

        outcome = plan_within_ladder(
            _combos(), SALTY_NEEDS_RUNG_1, ING, picks=frozenset({"crisp_a"})
        )
        assert outcome.result.passed
        assert set(_options(outcome)[rice.name]) == with_pick

    def test_the_picks_own_slot_still_offers_the_other_dishes(self):
        # Swapping back must stay possible: a pick narrows other slots, not
        # its own.
        plain = plan_within_ladder(_combos(), FEASIBLE, ING)
        picked = plan_within_ladder(_combos(), FEASIBLE, ING, picks=frozenset({"rice_a"}))
        assert _options(picked)["rice_base"] == _options(plain)["rice_base"]
        assert len(_options(plain)["rice_base"]) >= 2

    def test_a_decline_of_the_whole_ladder_offers_nothing(self):
        impossible = simple_target(energy_kcal=5000.0, protein_g_min=300.0)
        outcome = plan_within_ladder(_combos(), impossible, ING)
        assert outcome.plan is None
        assert outcome.swap_options == ()
