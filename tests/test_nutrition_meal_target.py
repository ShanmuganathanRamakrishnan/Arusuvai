"""Hand-computed checks for splitting a day target across a meal slot."""

from __future__ import annotations

import pytest

from core.nutrition.meal_target import meal_energy_fraction, meal_target
from core.nutrition.target import simple_target
from core.schemas import MealSlot


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


def test_every_bound_scales_by_the_same_fraction_not_just_energy():
    # day energy 2000 kcal +/-5% -> floor 1900, ceiling 2100 (simple_target's
    # own default tolerance). protein floor 100 g. fat 60 g +/-15% -> floor 51,
    # ceiling 69. carb 250 g +/-15% -> floor 212.5, ceiling 287.5.
    # sodium ceiling 2000 mg. fibre floor 28 g.
    day = simple_target(
        energy_kcal=2000.0,
        protein_g_min=100.0,
        fat_g=60.0,
        carb_g=250.0,
        sodium_mg_max=2000.0,
        fibre_g_min=28.0,
    )
    lunch = meal_target(day, MealSlot.LUNCH)  # x0.35

    assert lunch.floor("energy_kcal") == pytest.approx(1900.0 * 0.35)
    assert lunch.ceiling("energy_kcal") == pytest.approx(2100.0 * 0.35)
    assert lunch.point("energy_kcal") == pytest.approx(2000.0 * 0.35)
    assert lunch.floor("protein_g") == pytest.approx(100.0 * 0.35)
    assert lunch.floor("fat_g") == pytest.approx(51.0 * 0.35)
    assert lunch.ceiling("fat_g") == pytest.approx(69.0 * 0.35)
    assert lunch.floor("carb_g") == pytest.approx(212.5 * 0.35)
    assert lunch.ceiling("carb_g") == pytest.approx(287.5 * 0.35)
    assert lunch.ceiling("sodium_mg") == pytest.approx(2000.0 * 0.35)
    assert lunch.floor("fibre_g") == pytest.approx(28.0 * 0.35)


def test_different_slots_scale_the_same_day_target_differently():
    day = simple_target(energy_kcal=2000.0, protein_g_min=100.0)
    breakfast = meal_target(day, MealSlot.BREAKFAST)  # x0.25
    dinner = meal_target(day, MealSlot.DINNER)  # x0.30
    assert breakfast.floor("protein_g") == pytest.approx(25.0)
    assert dinner.floor("protein_g") == pytest.approx(30.0)
    assert breakfast.floor("protein_g") != dinner.floor("protein_g")
