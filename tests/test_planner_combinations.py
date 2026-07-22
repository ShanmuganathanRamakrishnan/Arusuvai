"""Combination enumeration, the naive-bound comparison, and the O(1)
feasibility pre-filter."""

from __future__ import annotations

import pytest

from core.foods import templates
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import (
    combinations_excluding_recent,
    enumerate_combinations,
    feasible_combinations,
)
from core.planner.target import NutritionTarget
from core.schemas import DietPattern
from tests.factories import (
    FEASIBILITY_COMPONENTS,
    FEASIBILITY_INGREDIENTS,
    FEASIBILITY_TEMPLATE,
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
)


def _south_lunch_pool(dev_mode: bool = False):
    return build_candidate_pool(
        SOUTH_LUNCH_COMPONENTS,
        SOUTH_LUNCH_INGREDIENTS,
        template=templates.SOUTH_LUNCH,
        diet_pattern=DietPattern.VEGETARIAN,
        dev_mode=dev_mode,
    )


class TestEnumeration:
    def test_the_actual_count_matches_the_hand_derived_formula(self):
        # rice_base: 2 candidates, exactly 1 selection      -> C(2,1) = 2
        # gravy:     2 candidates, exactly 1 selection       -> C(2,1) = 2
        # vegetable: 3 candidates, 1 or 2 selections          -> C(3,1)+C(3,2) = 3+3 = 6
        # curd_course: 2 candidates, exactly 1 selection      -> C(2,1) = 2
        # crisp:     2 candidates, 0 or 1 selections (optional) -> C(2,0)+C(2,1) = 1+2 = 3
        # total = 2 * 2 * 6 * 2 * 3 = 144
        combos = enumerate_combinations(_south_lunch_pool())
        assert len(combos) == 144

    def test_the_naive_bound_is_the_per_slot_power_set_product(self):
        # naive = 2**k per slot (the full power set, ignoring min/max entirely)
        # = 2**2 * 2**2 * 2**3 * 2**2 * 2**2 = 4*4*8*4*4 = 2048
        # 2048 > 144: the naive bound is a real, larger-than-actual upper
        # bound, not a restatement of the true count under another name.
        combos = enumerate_combinations(_south_lunch_pool())
        pool = _south_lunch_pool()
        naive = 1
        for slot in pool.template.slots:
            naive *= 2 ** len(pool.for_slot(slot))
        assert naive == 2048
        assert len(combos) < naive

    def test_every_combination_fills_every_required_slot(self):
        combos = enumerate_combinations(_south_lunch_pool())
        for combo in combos:
            for slot, selection in zip(combo.template.slots, combo.slot_selections):
                if slot.required:
                    assert len(selection) >= 1
                assert slot.min_selections <= len(selection) <= slot.max_selections

    def test_a_required_slot_with_no_candidates_yields_zero_combinations(self, library, ingredients):
        # masala_dosa is the only recipe compatible with south_breakfast's
        # tiffin_item category; nothing in the 3-recipe library satisfies
        # gravy_accompaniment or chutney, both required. Zero combinations is
        # the correct, honest answer — not an error.
        pool = build_candidate_pool(
            library.components.values(),
            ingredients,
            template=templates.SOUTH_BREAKFAST,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        assert enumerate_combinations(pool) == ()

    def test_no_repeat_window_filters_combinations_reusing_a_recent_recipe(self):
        pool = _south_lunch_pool()
        all_combos = enumerate_combinations(pool)
        filtered = combinations_excluding_recent(pool, recent_recipe_ids=frozenset({"rice_a"}))
        assert len(filtered) < len(all_combos)
        assert all("rice_a" not in c.recipe_ids() for c in filtered)
        # Every combo must select exactly one of {rice_a, rice_b} for
        # rice_base, so excluding rice_a leaves exactly the rice_b half.
        assert len(filtered) == len(all_combos) // 2

    def test_a_week_is_not_a_21_way_cross_product(self):
        # Regression against the shape BUILD_PROMPTS explicitly forbids: doing
        # this once per (day, meal_slot) cell costs O(cells * per_cell_count)
        # work, not per_cell_count ** cells. 7 days x 1 meal_slot here (using
        # south_lunch for every day, the simplest week shape) with a 1-day
        # no-repeat window (exclude only yesterday's recipes): total work
        # stays linear in the number of cells.
        #
        # Every required slot in this fixture has >= 2 candidates (rice_base
        # 2, gravy 2, curd_course 2) and each slot picks strictly fewer than
        # its full candidate count (rice_base/gravy/curd_course pick exactly
        # 1 of 2; vegetable picks 1 or 2 of 3), so excluding a single
        # previous day's recipes can never exhaust a slot. A wider window
        # (e.g. 2 days) CAN exhaust a 2-candidate required slot by day 3 —
        # that's a real fixture-variety limit, not a bug in the filter, so
        # this test pins the window BUILD_PROMPTS' constraint actually needs
        # (never repeat *yesterday*) rather than an arbitrary wider one.
        pool = _south_lunch_pool()
        single_day_count = len(enumerate_combinations(pool))
        recent: frozenset[str] = frozenset()
        total_survivor_combos = 0
        for _day in range(7):
            survivors = combinations_excluding_recent(pool, recent_recipe_ids=recent)
            assert len(survivors) > 0  # the pool is rich enough that variety never starves it
            total_survivor_combos += len(survivors)
            recent = survivors[0].recipe_ids()
        # Linear bound: at most 7 * (the single-day combo count), nowhere near
        # single_day_count ** 7, which is what a real cross product would cost.
        assert total_survivor_combos <= 7 * single_day_count
        assert single_day_count**7 > 10**12  # sanity: the forbidden shape really is astronomic


class TestFeasibilityPreFilter:
    def _pool(self):
        return build_candidate_pool(
            FEASIBILITY_COMPONENTS,
            FEASIBILITY_INGREDIENTS,
            template=FEASIBILITY_TEMPLATE,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=False,
        )

    def test_floor_side_exclusion(self):
        # Every serving unit here is pinned to exactly one legal count
        # (min=max=1), so each combo's macro total is a single exact number:
        #   (a1,b1) energy=100+50=150  protein=5+2=7
        #   (a1,b2) energy=100+150=250 protein=5+8=13
        #   (a2,b1) energy=200+50=250  protein=10+2=12
        #   (a2,b2) energy=200+150=350 protein=10+8=18
        # Target: energy floor 200, protein floor 10 -> only (a1,b1) fails
        # (150 < 200 and 7 < 10); the other three all clear both floors.
        combos = enumerate_combinations(self._pool())
        assert len(combos) == 4
        target = NutritionTarget(floors={"energy_kcal": 200.0, "protein_g": 10.0})
        survivors = feasible_combinations(combos, target, FEASIBILITY_INGREDIENTS)
        assert len(survivors) == 3
        surviving_ids = {c.recipe_ids() for c in survivors}
        assert frozenset({"a1", "b1"}) not in surviving_ids

    def test_ceiling_side_exclusion(self):
        # Sodium sums: (a1,b1)=500+1000=1500 (a1,b2)=500+50=550
        #              (a2,b1)=100+1000=1100 (a2,b2)=100+50=150
        # Ceiling 600 excludes both combos containing b1 (1500, 1100), because
        # b1's sodium alone (1000) already exceeds it regardless of the other
        # slot's choice.
        combos = enumerate_combinations(self._pool())
        target = NutritionTarget(ceilings={"sodium_mg": 600.0})
        survivors = feasible_combinations(combos, target, FEASIBILITY_INGREDIENTS)
        surviving_ids = {c.recipe_ids() for c in survivors}
        assert surviving_ids == {frozenset({"a1", "b2"}), frozenset({"a2", "b2"})}

    def test_an_unbounded_target_excludes_nothing(self):
        combos = enumerate_combinations(self._pool())
        target = NutritionTarget()
        assert len(feasible_combinations(combos, target, FEASIBILITY_INGREDIENTS)) == len(combos)

    def test_an_unreachable_floor_excludes_everything(self):
        # Highest possible single-combo energy is 350 (a2,b2); a floor above
        # that leaves nothing.
        combos = enumerate_combinations(self._pool())
        target = NutritionTarget(floors={"energy_kcal": 1000.0})
        assert feasible_combinations(combos, target, FEASIBILITY_INGREDIENTS) == ()
