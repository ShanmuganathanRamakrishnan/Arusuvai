"""The shown plate repeats a main ingredient only when every valid plate does.

TASKS_3.md N14 (owner 2026-10-08): on 43 of 94 shown plates one main
ingredient was served in two dishes, nearly always soya, and for 31 of them
a valid plate without the repeat existed (docs/audit_log.md 2026-10-08,
"N14"). The planner now prefers fewer repeats among plates already valid at
the rung the ladder stopped on. It never widens a limit for it.

Uses tests/factories.py's synthetic South lunch, where every dish is its own
main ingredient, and relabels two dishes of the nearest plate as the same
thing, so the nearest plate is the one repeating.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from core.foods import templates
from core.foods.models import Component
from core.nutrition.target import simple_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations, feasible_combinations
from core.planner.solver import solve
from core.planner.validator import _repeated_mains, plan_within_ladder
from core.schemas import DietPattern
from tests.factories import SOUTH_LUNCH_COMPONENTS, SOUTH_LUNCH_INGREDIENTS

ING = SOUTH_LUNCH_INGREDIENTS
# Passes at rung 0 (test_shown_plate_preference.py's FEASIBLE).
FEASIBLE = simple_target(energy_kcal=700.0, protein_g_min=20.0)


def _combos(components):
    return enumerate_combinations(
        build_candidate_pool(
            components, ING,
            template=templates.SOUTH_LUNCH, diet_pattern=DietPattern.VEGETARIAN,
        )
    )


def _solved(components):
    combos = _combos(components)
    return solve(feasible_combinations(combos, FEASIBLE, ING), FEASIBLE, ING)


def _ids(plan):
    return {c.recipe.id for c in plan.combination.components}


@pytest.fixture(scope="module")
def relabelled():
    """Two dishes of the nearest plate both labelled "soya"; their ids."""

    nearest = _solved(SOUTH_LUNCH_COMPONENTS)[0]
    a, b = sorted(_ids(nearest))[:2]
    components = tuple(
        Component(
            recipe=replace(c.recipe, main_ingredients=frozenset({"soya"})),
            category=c.category,
        )
        if c.recipe.id in (a, b)
        else c
        for c in SOUTH_LUNCH_COMPONENTS
    )
    return components, (a, b)


def test_a_plate_counts_each_dish_past_the_first_per_main_ingredient():
    # masala dosa {rice, potato} + aloo sabzi {potato} + steamed rice {rice}:
    # potato once more, rice once more = 2.
    def dish(*mains):
        return SimpleNamespace(recipe=SimpleNamespace(main_ingredients=frozenset(mains)))

    plate = SimpleNamespace(combination=SimpleNamespace(
        components=(dish("rice", "potato"), dish("potato"), dish("rice"), dish("curd"))
    ))
    assert _repeated_mains(plate) == 2


def test_the_fixture_makes_the_nearest_plate_repeat_with_a_way_out(relabelled):
    # Preconditions, or every test below passes whatever the planner does.
    components, _ = relabelled
    solved = _solved(components)
    assert _repeated_mains(solved[0]) == 1
    without = [p for p in solved if _repeated_mains(p) == 0]
    assert len(without) >= 2  # ties among them, so "nearest of those" is tested


def test_a_valid_plate_without_the_repeat_is_shown_over_the_nearer_one(relabelled):
    components, _ = relabelled
    outcome = plan_within_ladder(_combos(components), FEASIBLE, ING)
    assert outcome.result.passed
    assert _repeated_mains(outcome.plan) == 0


def test_among_plates_without_a_repeat_the_nearest_is_shown(relabelled):
    components, _ = relabelled
    solved = _solved(components)
    first_without = next(p for p in solved if _repeated_mains(p) == 0)
    outcome = plan_within_ladder(_combos(components), FEASIBLE, ING)
    assert _ids(outcome.plan) == _ids(first_without)


def test_a_preference_still_comes_before_fewer_repeats(relabelled):
    # Only plates holding both relabelled dishes are preferred -- all of them
    # repeat. The preference (egg, fish or chicken in the real planner) wins.
    components, (a, b) = relabelled
    prefer = lambda plan: {a, b} <= _ids(plan)
    solved = _solved(components)
    first_preferred = next(p for p in solved if prefer(p))
    outcome = plan_within_ladder(_combos(components), FEASIBLE, ING, prefer=prefer)
    assert _ids(outcome.plan) == _ids(first_preferred)
    assert _repeated_mains(outcome.plan) == 1


def test_no_repeat_anywhere_leaves_the_nearest_plate(relabelled):
    # Unlabelled fixture: every dish its own main ingredient.
    outcome = plan_within_ladder(_combos(SOUTH_LUNCH_COMPONENTS), FEASIBLE, ING)
    assert _ids(outcome.plan) == _ids(_solved(SOUTH_LUNCH_COMPONENTS)[0])
