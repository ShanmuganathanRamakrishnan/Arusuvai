"""Hand-computed checks for splitting a day target across a meal slot."""

from __future__ import annotations

import pytest

from core.nutrition.meal_target import meal_energy_fraction, meal_target
from core.nutrition.target import NutritionTarget, simple_target
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
    # Protein is in this list only because the share DOMINATES its per-meal
    # guard here (0.35 x 100 = 35.0 against 0.15 x 100 = 15.0). Since slice 3 it
    # is max(share, guard), not the share alone -- see
    # TestProteinHasPerMealBounds, and do not read this line as proof that
    # protein still scales purely.
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


class TestASnackHasAWiderEnergyBand:
    """Owner decision 2026-09-26 (docs/audit_log.md, snack energy band).

    A snack's energy band is +/-10% around its point (tolerance.energy_snack),
    not the day's +/-5% scaled down. Every other slot keeps the scaled band.
    """

    def test_snack_band_is_ten_percent_around_its_point(self):
        snack = meal_target(_day(), MealSlot.SNACK)  # x0.10
        # point 2000 x 0.10 = 200.0 ; 200 x 0.90 = 180.0 ; 200 x 1.10 = 220.0
        assert snack.point("energy_kcal") == pytest.approx(200.0)
        assert snack.floor("energy_kcal") == pytest.approx(180.0)
        assert snack.ceiling("energy_kcal") == pytest.approx(220.0)

    @pytest.mark.parametrize(
        "slot", [MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER]
    )
    def test_every_other_slot_keeps_the_scaled_five_percent_band(self, slot):
        # 1900 and 2100 are the day band in _day(); the slot's own share.
        target = meal_target(_day(), slot)
        fraction = meal_energy_fraction(slot)
        assert target.floor("energy_kcal") == pytest.approx(1900.0 * fraction)
        assert target.ceiling("energy_kcal") == pytest.approx(2100.0 * fraction)

    def test_the_energy_rung_leaves_a_snack_band_unchanged(self):
        # The ladder's energy rung re-bands at tolerance.energy_relaxed (0.10),
        # the same value, so for a snack it widens nothing.
        from core.planner.validator import _relax_energy

        snack = meal_target(_day(), MealSlot.SNACK)
        relaxed = _relax_energy(snack, frozenset())
        assert relaxed.floor("energy_kcal") == pytest.approx(180.0)
        assert relaxed.ceiling("energy_kcal") == pytest.approx(220.0)


class TestASnackHasNoFatOrCarbFloor:
    """Owner decision 2026-09-25 (docs/audit_log.md, snack fat/carb floors).

    A snack keeps its fat and carb ceilings but has no floor on either, so a
    lean chaat or a low-carb tikka is not declined for being lopsided. Every
    other slot keeps both bounds.
    """

    def test_snack_drops_both_floors_and_keeps_both_ceilings(self):
        snack = meal_target(_day(), MealSlot.SNACK)  # x0.10
        assert snack.floor("fat_g") is None
        assert snack.floor("carb_g") is None
        # 69.0 x 0.10 = 6.9 ; 287.5 x 0.10 = 28.75
        assert snack.ceiling("fat_g") == pytest.approx(6.9)
        assert snack.ceiling("carb_g") == pytest.approx(28.75)
        # Points stay: they are what the ladder widens ceilings around.
        # 60.0 x 0.10 = 6.0 ; 250.0 x 0.10 = 25.0
        assert snack.point("fat_g") == pytest.approx(6.0)
        assert snack.point("carb_g") == pytest.approx(25.0)

    def test_only_fat_and_carb_lose_a_floor_on_a_snack(self):
        snack = meal_target(_day(), MealSlot.SNACK)
        # Energy point 2000 x 0.10 = 200.0, band +/-10% (TestASnackHasAWider
        # EnergyBand below) -> 180.0 ; fibre 28.0 x 0.10 = 2.8 ; protein guard
        # 15.0 (TestProteinHasPerMealBounds below).
        assert snack.floor("energy_kcal") == pytest.approx(180.0)
        assert snack.floor("fibre_g") == pytest.approx(2.8)
        assert snack.floor("protein_g") == pytest.approx(15.0)

    @pytest.mark.parametrize(
        "slot", [MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER]
    )
    def test_every_other_slot_keeps_both_floors(self, slot):
        # 51.0 and 212.5 are the day floors in _day(); the slot's own share.
        target = meal_target(_day(), slot)
        fraction = meal_energy_fraction(slot)
        assert target.floor("fat_g") == pytest.approx(51.0 * fraction)
        assert target.floor("carb_g") == pytest.approx(212.5 * fraction)

    def test_the_fat_carb_rung_does_not_restore_a_dropped_floor(self):
        # The ladder's fat_carb rung re-derives bounds around the point; it
        # must widen the ceilings and leave the absent floors absent.
        from core.nutrition import citations
        from core.planner.validator import _relax_fat_carb

        relaxed = _relax_fat_carb(meal_target(_day(), MealSlot.SNACK), frozenset())
        assert relaxed.floor("fat_g") is None
        assert relaxed.floor("carb_g") is None
        tol = citations.value_of("tolerance.fat_carb_relaxed")
        assert tol == 0.25
        # 6.0 x 1.25 = 7.5 ; 25.0 x 1.25 = 31.25
        assert relaxed.ceiling("fat_g") == pytest.approx(7.5)
        assert relaxed.ceiling("carb_g") == pytest.approx(31.25)


class TestProteinHasPerMealBounds:
    """Slice 3: no meal empty of protein, no meal packed with it.

    Both bounds are fractions of the DAY protein floor (100.0 g in ``_day()``),
    so the arithmetic below is against 100, not against the meal's energy share.
    """

    def test_the_floor_is_the_larger_of_the_share_and_the_guard(self):
        # guard = protein.meal_floor_fraction (0.15) x 100.0 = 15.0 g
        #
        # lunch share = 0.35 x 100.0 = 35.0  -> share wins, floor 35.0
        # snack share = 0.10 x 100.0 = 10.0  -> guard wins, floor 15.0
        #
        # The snack row is the whole point of the bound: it is the only slot
        # whose energy share falls below the guard, so it is the only place
        # "no meal empty of protein" has anything to do.
        assert meal_target(_day(), MealSlot.LUNCH).floor("protein_g") == pytest.approx(
            35.0
        )
        assert meal_target(_day(), MealSlot.SNACK).floor("protein_g") == pytest.approx(
            15.0
        )

    def test_the_guard_never_lowers_a_floor(self):
        # The departure from docs/design/target_model_v2.md §3, asserted rather
        # than left in a comment. Read literally, the design's table replaces the
        # share with the fraction, which would move lunch from 35.0 down to 15.0
        # -- a loosening nobody asked for. Every slot's floor must be >= its
        # share.
        day = _day()
        for slot in MealSlot:
            share = 100.0 * meal_energy_fraction(slot)
            assert meal_target(day, slot).floor("protein_g") >= share - 1e-9, slot

    def test_the_ceiling_is_half_the_day_floor_for_every_slot(self):
        # protein.meal_ceiling_fraction (0.50) x 100.0 = 50.0, and it does NOT
        # scale by the meal share: a ceiling that shrank with the slot would
        # make a snack's ceiling 5 g, which forbids a snack containing an egg.
        for slot in MealSlot:
            assert meal_target(_day(), slot).ceiling("protein_g") == pytest.approx(50.0)

    def test_the_ceiling_sits_above_the_floor_on_every_slot(self):
        # A ceiling below its own floor would decline every plate with two
        # contradictory violations and no way to satisfy both. Cheap to assert,
        # and it is what would break first if either constant were edited.
        day = _day()
        for slot in MealSlot:
            mt = meal_target(day, slot)
            assert mt.floor("protein_g") < mt.ceiling("protein_g"), slot

    def test_both_bounds_are_read_from_the_registry_not_hardcoded(self):
        # The round-4 perturbation rule: move the constant, the derived bound
        # must move. A test comparing a computed bound against a literal cannot
        # tell a registry read from a paste.
        import dataclasses

        from core.nutrition import citations

        original_floor = citations.constant("protein.meal_floor_fraction")
        original_ceiling = citations.constant("protein.meal_ceiling_fraction")
        try:
            citations._CONSTANTS["protein.meal_floor_fraction"] = dataclasses.replace(
                original_floor, value=0.40
            )
            citations._CONSTANTS["protein.meal_ceiling_fraction"] = dataclasses.replace(
                original_ceiling, value=0.90
            )
            # 0.40 x 100 = 40.0 now beats lunch's 35.0 share; 0.90 x 100 = 90.0.
            lunch = meal_target(_day(), MealSlot.LUNCH)
            assert lunch.floor("protein_g") == pytest.approx(40.0)
            assert lunch.ceiling("protein_g") == pytest.approx(90.0)
        finally:
            citations._CONSTANTS["protein.meal_floor_fraction"] = original_floor
            citations._CONSTANTS["protein.meal_ceiling_fraction"] = original_ceiling
        # Restored, and proven restored rather than assumed.
        assert meal_target(_day(), MealSlot.LUNCH).ceiling(
            "protein_g"
        ) == pytest.approx(50.0)

    def test_no_day_protein_floor_means_no_per_meal_protein_bounds(self):
        # A target with no protein floor has nothing to take a fraction of.
        # Inventing one here would be a nutritional number written outside
        # citations.py, so the correct behaviour is to add neither bound.
        #
        # Built directly rather than via simple_target, which requires
        # protein_g_min -- there is deliberately no way to ask that constructor
        # for a protein-free day target. This exercises the guard clause a
        # different caller could still reach.
        no_protein = NutritionTarget(
            floors={"energy_kcal": 1900.0}, ceilings={"energy_kcal": 2100.0}
        )
        lunch = meal_target(no_protein, MealSlot.LUNCH)
        assert lunch.floor("protein_g") is None
        assert lunch.ceiling("protein_g") is None
