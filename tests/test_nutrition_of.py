"""Point estimate plus interval, for a whole plate."""

from __future__ import annotations

import pytest

from core.foods.models import Component, RecipeIngredient
from core.foods.nutrition_of import format_macro, nutrition_of_components, nutrition_of_recipe
from core.nutrition import citations
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
        # Two terms, summed. Every ingredient row is verified=False, so each
        # carries composition.unverified_secondary = 0.25, and the weighted sum
        # over lines collapses to 0.25 of the dish total:
        #   composition band = 223.65 x 0.25  = 55.9125
        #   process band     = 223.65 x 0.040 =  8.946   (declared, oil uptake)
        #   half-width       = 64.8585
        #   low  = 223.65 - 64.8585 = 158.7915
        #   high = 223.65 + 64.8585 = 288.5085
        items = [(library.component("masala_dosa"), 1)]
        est = nutrition_of_components(items, ingredients)
        assert est.low.energy_kcal == pytest.approx(158.7915)
        assert est.high.energy_kcal == pytest.approx(288.5085)

    def test_composition_uncertainty_dominates_the_process_term(
        self, library, ingredients
    ):
        # The defect this replaced: the band came from the oil constant alone,
        # so a dish that is 96% rice/urad/potato displayed +/-4% — narrower than
        # the acknowledged error of its own inputs. Composition is now 6.25x the
        # process term (55.9125 vs 8.946), which is the honest ratio.
        items = [(library.component("masala_dosa"), 1)]
        est = nutrition_of_components(items, ingredients)
        half_width = (est.high.energy_kcal - est.low.energy_kcal) / 2
        process_only = est.point.energy_kcal * 0.040
        assert half_width == pytest.approx(64.8585)
        assert half_width > 6 * process_only

    def test_bands_are_summed_not_root_sum_squared(self, library, ingredients):
        # dosa         223.65 x (0.25 + 0.040) = 223.65 x 0.290 = 64.8585
        # sambar sadam 265.04 x (0.25 + 0.013) = 265.04 x 0.263 = 69.70552
        # summed half-width = 134.56402 ; RSS would be 95.28, i.e. narrower and
        # wrong: on this library the errors share a provenance (one author, one
        # sitting, all from memory), so they do not cancel.
        items = [
            (library.component("masala_dosa"), 1),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        half_width = (est.high.energy_kcal - est.low.energy_kcal) / 2
        assert half_width == pytest.approx(134.56402)

    def test_uncertainty_fraction_of_the_plate(self, library, ingredients):
        # 134.56402 / (223.65 + 265.04) = 134.56402 / 488.69 = 0.2753566...
        items = [
            (library.component("masala_dosa"), 1),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.uncertainty_fraction("energy_kcal") == pytest.approx(0.2753566, abs=1e-6)

    def test_a_macro_with_no_declared_process_uncertainty_still_has_a_band(
        self, library, ingredients
    ):
        # Previously asserted the opposite — that an undeclared macro has a
        # zero-width band — which encoded the defect as intended behaviour. No
        # recipe declares *process* uncertainty on protein (protein in cooked
        # rice and dal is not oil-sensitive), but the composition data behind it
        # is still unread, and that must show:
        #   15.391 g protein x 0.25 = 3.84775 g half-width
        items = [(library.component("rajma_chawal"), 1)]
        est = nutrition_of_components(items, ingredients)
        half_width = (est.high.protein_g - est.low.protein_g) / 2
        assert half_width == pytest.approx(3.84775)
        assert est.uncertainty_fraction("protein_g") == pytest.approx(0.25)

    def test_a_verified_ingredient_would_narrow_the_band(self, library, ingredients):
        # Perturbation test: the band must actually move when provenance
        # changes, not merely be described as depending on it. Flipping every
        # row to verified swaps composition.unverified_secondary (0.25) for
        # composition.verified_primary (0.05):
        #   223.65 x (0.05 + 0.040) = 223.65 x 0.090 = 20.1285
        from dataclasses import replace

        from core.schemas import MACRO_KEYS

        verified = {
            key: replace(
                ing,
                verified=True,
                composition_uncertainty={macro: 0.05 for macro in MACRO_KEYS},
            )
            for key, ing in ingredients.items()
        }
        items = [(library.component("masala_dosa"), 1)]
        est = nutrition_of_components(items, verified)
        half_width = (est.high.energy_kcal - est.low.energy_kcal) / 2
        assert half_width == pytest.approx(20.1285)


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


class TestEligibilityConsequence:
    """What the uncertainty ceiling implies for the library as it stands.

    Recorded as a test rather than a note because the consequence is the kind
    that gets discovered late and then quietly designed around: the tempting
    fix, once core/planner returns nothing, is to nudge 0.25 down or 0.15 up
    until a demo works. Both edits look reasonable in isolation. This test makes
    either one a deliberate act with a failing assertion attached.
    """

    def test_no_recipe_currently_clears_the_protein_eligibility_ceiling(
        self, library, ingredients
    ):
        # Every ingredient is unverified, so every recipe's protein uncertainty
        # is 0.25 against a 0.15 ceiling. Protein is target-critical for
        # essentially every profile this product serves, so the candidate pool
        # is empty for all of them — and the relaxation ladder cannot help,
        # because it moves tolerance and never uncertainty.
        ceiling = citations.value_of("eligibility.max_protein_uncertainty")
        for recipe_id, component in library.components.items():
            est = nutrition_of_components([(component, 1)], ingredients)
            assert est.uncertainty_fraction("protein_g") > ceiling, (
                f"{recipe_id} unexpectedly clears the ceiling; if this is real "
                "progress, update docs/methodology.md — the claim that nothing "
                "can ship as validated is stated there"
            )

    def test_every_registered_evidence_is_still_unverified(self):
        # The precondition for the above. If this ever fails, someone has opened
        # a source document, and the shipping story genuinely changes.
        assert all(not ev.verified for ev in citations.all_evidence())


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
