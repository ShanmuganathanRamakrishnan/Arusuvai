"""Point estimate plus interval, for a whole plate."""

from __future__ import annotations

import pytest

from core.foods.models import Component, RecipeIngredient
from core.foods.nutrition_of import format_macro, nutrition_of_components, nutrition_of_recipe
from core.schemas import RawOrCooked


class TestPlateTotals:
    def test_two_components_sum(self, library, ingredients):
        # 2 masala dosas (223.65 x 2 = 447.30) + 1 cup sambar sadam (265.04)
        # = 712.34 kcal
        items = [
            (library.component("masala_dosa"), 2),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.point.energy_kcal == pytest.approx(712.34)

    def test_protein_sums(self, library, ingredients):
        # 5.023 x 2 + 7.16 = 17.206 g
        items = [
            (library.component("masala_dosa"), 2),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.point.protein_g == pytest.approx(17.206)


class TestInterval:
    def test_interval_brackets_the_point_estimate(self, library, ingredients):
        # masala dosa declares +/-4.0% on energy:
        #   low  = 223.65 x 0.960 = 214.704
        #   high = 223.65 x 1.040 = 232.596
        items = [(library.component("masala_dosa"), 1)]
        est = nutrition_of_components(items, ingredients)
        assert est.low.energy_kcal == pytest.approx(214.704)
        assert est.high.energy_kcal == pytest.approx(232.596)

    def test_bands_are_summed_not_root_sum_squared(self, library, ingredients):
        # dosa energy band 223.65 x 0.040 = 8.946
        # sambar sadam     265.04 x 0.013 = 3.44552
        # summed half-width = 12.39152 ; RSS would be 9.586, i.e. narrower and
        # wrong: both errors come from the same cook and the same pan.
        items = [
            (library.component("masala_dosa"), 1),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        half_width = (est.high.energy_kcal - est.low.energy_kcal) / 2
        assert half_width == pytest.approx(12.39152)

    def test_uncertainty_fraction_of_the_plate(self, library, ingredients):
        # 12.39152 / (223.65 + 265.04) = 12.39152 / 488.69 = 0.025357...
        items = [
            (library.component("masala_dosa"), 1),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.uncertainty_fraction("energy_kcal") == pytest.approx(0.0253568, abs=1e-6)

    def test_a_macro_with_no_declared_uncertainty_has_a_zero_width_band(
        self, library, ingredients
    ):
        # No recipe declares protein uncertainty: the protein in cooked rice and
        # dal is not process-sensitive in the way griddle oil is.
        items = [(library.component("rajma_chawal"), 1)]
        est = nutrition_of_components(items, ingredients)
        assert est.low.protein_g == pytest.approx(est.high.protein_g)


class TestUnverifiedEnergyAttribution:
    def test_all_three_recipes_rest_on_unverified_process_constants(
        self, library, ingredients
    ):
        # Every process constant in the library is currently unverified, so the
        # whole plate's energy is attributed as such. This is the honest state
        # of the data, and the number the "disclose once" threshold will read.
        items = [
            (library.component("masala_dosa"), 2),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.unverified_energy_fraction() == pytest.approx(1.0)


class TestStateMismatch:
    def test_a_cooked_quantity_against_a_raw_record_is_refused(
        self, library, ingredients
    ):
        # Reading the 345 kcal/100 g raw rice record against a cooked quantity
        # is a 3x error, not a tolerance-band problem — so it raises rather
        # than guessing a yield factor.
        from dataclasses import replace

        recipe = library.recipes["sambar_sadam"]
        broken = replace(
            recipe,
            ingredients=(
                RecipeIngredient("rice_milled_raw", 200.0, RawOrCooked.COOKED),
            ),
            serving_unit=replace(recipe.serving_unit, grams_per_unit=200.0),
        )
        with pytest.raises(ValueError, match="retention"):
            nutrition_of_recipe(broken, 1, ingredients)

    def test_unknown_ingredient_points_at_the_load_report(self, library, ingredients):
        from dataclasses import replace

        recipe = library.recipes["sambar_sadam"]
        broken = replace(
            recipe,
            ingredients=(RecipeIngredient("moon_cheese", 200.0, RawOrCooked.COOKED),),
        )
        with pytest.raises(KeyError, match="LoadReport"):
            nutrition_of_recipe(broken, 1, ingredients)


class TestDisplay:
    def test_energy_is_shown_coarsely_with_its_band(self):
        # Precision the data does not support is a liability: 1,847 kcal reads
        # as measured, "~1,850 kcal (+/-10%)" reads as estimated.
        assert format_macro(1847.3, 0.10, "energy_kcal") == "~1,850 kcal (+/-10%)"

    def test_a_negligible_band_is_not_shown(self):
        # A "+/-2%" on every line is wallpaper by the second screen.
        assert format_macro(76.0, 0.01, "protein_g") == "76 g"

    def test_protein_gap_phrasing_keeps_the_target_units(self):
        assert format_macro(76.0, 0.0, "protein_g").endswith("g")
