"""Hand-computed checks for splitting a day target across a meal slot."""

from __future__ import annotations

import pytest

from core.nutrition.meal_target import meal_energy_fraction, meal_target
from core.nutrition.target import simple_target
from core.schemas import DayLedger, MealSlot


def test_fractions_match_the_registered_constants_and_sum_to_a_day():
    # citations.py: breakfast 0.25 + lunch 0.35 + dinner 0.30 + snack 0.10 = 1.00
    assert meal_energy_fraction(MealSlot.BREAKFAST) == pytest.approx(0.25)
    assert meal_energy_fraction(MealSlot.LUNCH) == pytest.approx(0.35)
    assert meal_energy_fraction(MealSlot.DINNER) == pytest.approx(0.30)
    assert meal_energy_fraction(MealSlot.SNACK) == pytest.approx(0.10)
    assert (
        meal_energy_fraction(MealSlot.BREAKFAST)
        + meal_energy_fraction(MealSlot.LUNCH)
        + meal_energy_fraction(MealSlot.DINNER)
        + meal_energy_fraction(MealSlot.SNACK)
        == pytest.approx(1.0)
    )


def _day() -> "object":
    # day energy 2000 kcal +/-5% -> floor 1900, ceiling 2100 (simple_target's
    # own default tolerance). protein floor 100 g. fat 60 g +/-15% -> floor 51,
    # ceiling 69. carb 250 g +/-15% -> floor 212.5, ceiling 287.5.
    # sodium ceiling 2000 mg. fibre floor 28 g.
    return simple_target(
        energy_kcal=2000.0,
        protein_g_min=100.0,
        fat_g=60.0,
        carb_g=250.0,
        sodium_mg_max=2000.0,
        fibre_g_min=28.0,
    )


def test_every_per_meal_bound_scales_by_the_energy_fraction():
    """The proportional rule, for the macros that are quantities of food.

    Renamed 2026-08-02 from "every bound scales by the same fraction": that is
    no longer true and had stopped being a description of the code. Sodium is
    now a day budget and is asserted separately below, precisely because it must
    NOT appear in this list.
    """

    lunch = meal_target(_day(), MealSlot.LUNCH)  # x0.35

    assert lunch.floor("energy_kcal") == pytest.approx(1900.0 * 0.35)
    assert lunch.ceiling("energy_kcal") == pytest.approx(2100.0 * 0.35)
    assert lunch.point("energy_kcal") == pytest.approx(2000.0 * 0.35)
    assert lunch.floor("protein_g") == pytest.approx(100.0 * 0.35)
    assert lunch.floor("fat_g") == pytest.approx(51.0 * 0.35)
    assert lunch.ceiling("fat_g") == pytest.approx(69.0 * 0.35)
    assert lunch.floor("carb_g") == pytest.approx(212.5 * 0.35)
    assert lunch.ceiling("carb_g") == pytest.approx(287.5 * 0.35)
    # Fibre stays proportional deliberately: its target already derives from
    # energy (14 g per 1000 kcal), so splitting it by the energy fraction is
    # self-consistent -- 28 g at 2000 kcal becomes 9.8 g at a 700 kcal lunch,
    # which is exactly 14.0 * 0.7. No information is destroyed.
    assert lunch.floor("fibre_g") == pytest.approx(28.0 * 0.35)


class TestSodiumIsADayBudgetNotAShare:
    """The defect this slice exists to remove, asserted from both directions.

    2000 mg x 0.35 = 700 mg was never a WHO figure: it is a *daily* population
    guideline apportioned by calories, which nothing in the guideline supports
    and which forbids the ordinary pattern of a salty lunch offset by a plain
    dinner. What follows pins that sodium no longer scales, AND what it does
    instead -- an assertion that it merely differs from 700 would pass against
    any number at all.
    """

    def test_the_first_meal_of_a_day_gets_the_guard_not_a_share(self):
        # Nothing spent, so remaining is the whole 2000 and the guard binds:
        # 0.70 * 2000 = 1400.
        lunch = meal_target(_day(), MealSlot.LUNCH)
        assert lunch.ceiling("sodium_mg") == pytest.approx(1400.0)
        assert lunch.ceiling("sodium_mg") != pytest.approx(2000.0 * 0.35)
        assert lunch.bound_sources["sodium_mg"] == "absurdity_guard"

    def test_a_spent_day_binds_below_the_guard(self):
        # 2000 - 1200 = 800 remaining, which is under the 1400 guard, so the
        # budget is what limits the plate. This is the assertion that proves the
        # ledger is load-bearing rather than decorative.
        ledger = DayLedger.empty().with_meal(
            MealSlot.BREAKFAST, {"sodium_mg": 1200.0}
        )
        lunch = meal_target(_day(), MealSlot.LUNCH, ledger=ledger)
        assert lunch.ceiling("sodium_mg") == pytest.approx(800.0)
        assert lunch.bound_sources["sodium_mg"] == "day_remaining"

    def test_an_overspent_day_leaves_nothing_rather_than_a_negative_bound(self):
        ledger = DayLedger.empty().with_meal(
            MealSlot.BREAKFAST, {"sodium_mg": 2500.0}
        )
        lunch = meal_target(_day(), MealSlot.LUNCH, ledger=ledger)
        assert lunch.ceiling("sodium_mg") == pytest.approx(0.0)

    def test_the_guard_is_registered_as_a_hard_ceiling_so_no_rung_widens_it(self):
        lunch = meal_target(_day(), MealSlot.LUNCH)
        assert lunch.hard_ceiling("sodium_mg") == pytest.approx(1400.0)

    def test_the_guard_moves_with_its_registered_constant(self):
        # CLAUDE.md: a test that checks a fixed number against itself cannot
        # catch a constant drifting from its call site. Perturb the constant and
        # the computed ceiling must move with it.
        import dataclasses

        from core.nutrition import citations

        key = "day_budget.absurdity_fraction"
        original = citations.constant(key)
        citations._CONSTANTS[key] = dataclasses.replace(original, value=0.40)
        try:
            moved = meal_target(_day(), MealSlot.LUNCH)
            assert moved.ceiling("sodium_mg") == pytest.approx(0.40 * 2000.0)
        finally:
            citations._CONSTANTS[key] = original

    def test_a_day_with_no_sodium_ceiling_gets_no_sodium_bound_invented(self):
        bare = simple_target(energy_kcal=2000.0, protein_g_min=100.0)
        lunch = meal_target(bare, MealSlot.LUNCH)
        assert lunch.ceiling("sodium_mg") is None


def test_different_slots_scale_the_same_day_target_differently():
    day = simple_target(energy_kcal=2000.0, protein_g_min=100.0)
    breakfast = meal_target(day, MealSlot.BREAKFAST)  # x0.25
    dinner = meal_target(day, MealSlot.DINNER)  # x0.30
    assert breakfast.floor("protein_g") == pytest.approx(25.0)
    assert dinner.floor("protein_g") == pytest.approx(30.0)
    assert breakfast.floor("protein_g") != dinner.floor("protein_g")
