"""Point estimate plus interval, for a whole plate."""

from __future__ import annotations

import pytest

from core.foods.models import Component, NutritionVector, RecipeIngredient
from core.foods.nutrition_of import format_macro, nutrition_of_components, nutrition_of_recipe
from core.nutrition import citations
from core.schemas import MACRO_KEYS, DietPattern, RawOrCooked, Region


class TestPlateTotals:
    def test_two_components_sum(self, library, ingredients):
        # 2 masala dosas (226.614 x 2 = 453.228) + 1 cup sambar sadam (265.04)
        # = 718.268 kcal. (masala dosa moved from 223.65 to 226.614 when
        # rice_milled_raw was corrected to real IFCT 2017 values 2026-07-24 —
        # see TestMasalaDosa.test_energy in test_recipes.py.)
        items = [
            (library.component("masala_dosa"), 2),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.point.energy_kcal == pytest.approx(718.268)

    def test_protein_sums(self, library, ingredients):
        # 5.3194 x 2 + 7.16 = 17.7988 g
        items = [
            (library.component("masala_dosa"), 2),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.point.protein_g == pytest.approx(17.7988)


class TestInterval:
    def test_interval_brackets_the_point_estimate(self, library, ingredients):
        # Two terms, summed. Every ingredient row is verified=False, so each
        # carries composition.unverified_secondary = 0.25, and the weighted sum
        # over lines collapses to 0.25 of the dish total. The process term is
        # now derived by the loader from the oil lines (884 kcal/100 g). Dish
        # total moved from 223.65 to 226.614 when rice_milled_raw was corrected
        # to real IFCT 2017 values 2026-07-24 (see test_recipes.py):
        #   composition band = 226.614 x 0.25                   = 56.6535
        #   process band     = 3.5 x 8.84 x 0.20 = 6.188 kcal
        #                    + 3.0 x 8.84 x 0.10 = 2.652 kcal   =  8.8400
        #   half-width                                           = 65.4935
        #   low  = 226.614 - 65.4935 = 161.1205
        #   high = 226.614 + 65.4935 = 292.1075
        items = [(library.component("masala_dosa"), 1)]
        est = nutrition_of_components(items, ingredients)
        assert est.low.energy_kcal == pytest.approx(161.1205)
        assert est.high.energy_kcal == pytest.approx(292.1075)

    def test_composition_uncertainty_dominates_the_process_term(
        self, library, ingredients
    ):
        # The defect this replaced: the band came from the oil constant alone,
        # so a dish that is 96% rice/urad/potato displayed +/-4% — narrower than
        # the acknowledged error of its own inputs. Composition is now 6.41x the
        # process term (56.6535 vs 8.84), which is the honest ratio.
        items = [(library.component("masala_dosa"), 1)]
        est = nutrition_of_components(items, ingredients)
        half_width = (est.high.energy_kcal - est.low.energy_kcal) / 2
        recipe = library.recipes["masala_dosa"]
        process_only = est.point.energy_kcal * recipe.uncertainty_for("energy_kcal")
        assert half_width == pytest.approx(65.4935)
        assert process_only == pytest.approx(8.84)
        assert half_width - process_only == pytest.approx(56.6535)

    def test_bands_are_summed_not_root_sum_squared(self, library, ingredients):
        # dosa         226.614 x 0.25 + 8.840 = 56.6535 + 8.840 = 65.4935
        # sambar sadam 265.04 x 0.25 + 3.536 = 66.2600 + 3.536 = 69.7960
        # summed half-width = 135.2895 ; RSS would be narrower and wrong: on
        # this library the errors share a provenance (one author, one sitting,
        # all from memory), so they do not cancel.
        items = [
            (library.component("masala_dosa"), 1),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        half_width = (est.high.energy_kcal - est.low.energy_kcal) / 2
        assert half_width == pytest.approx(135.2895)

    def test_uncertainty_fraction_of_the_plate(self, library, ingredients):
        # 135.2895 / (226.614 + 265.04) = 135.2895 / 491.654 = 0.2751722...
        items = [
            (library.component("masala_dosa"), 1),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.uncertainty_fraction("energy_kcal") == pytest.approx(0.2751722, abs=1e-6)

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
        #   226.614 x 0.05 + 8.84 = 11.3307 + 8.84 = 20.1707
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
        assert half_width == pytest.approx(20.1707)


class TestUnverifiedEnergyAttribution:
    """Finding 20's fix: attribution is per ingredient line, not per recipe.

    The real library cannot test this. Every ingredient row but `water` is
    `verified=False` and `water` carries no energy, so *every* plate comes out
    at exactly 100% under the correct rule — and under most incorrect ones too.
    A test against the real library therefore cannot fail on the defect it
    names, which is why the mechanism tests below build their own mixed data
    and the real-library test that follows is labelled as the weak check it is.
    """

    def test_the_real_library_is_entirely_unverified(self, library, ingredients):
        # Kept, but demoted: this passed identically before finding 20 was
        # fixed, because the old whole-recipe rule also charged everything here.
        # It pins the honest state of the data — the figure the "disclose once"
        # threshold reads today — and it is NOT evidence the attribution works.
        items = [
            (library.component("masala_dosa"), 2),
            (library.component("sambar_sadam"), 1),
        ]
        est = nutrition_of_components(items, ingredients)
        assert est.unverified_energy_fraction() == pytest.approx(1.0)

    # `oil_uptake.vegetable_tempering` is a real registered constant and is
    # unverified, as every registered constant currently is — pinned by
    # TestEligibilityConsequence::test_every_registered_evidence_is_still_
    # unverified above. If that ever changes these tests change with it, which
    # is correct: they would then be asserting something false.
    _UNVERIFIED_PROCESS = "oil_uptake.vegetable_tempering"

    def _mixed(self):
        """A recipe whose lines differ only in why they are (un)trustworthy.

        Three 100 g lines, energies 100 / 200 / 400 kcal per 100 g:
          verified_plain     verified, no process        -> not charged
          unverified_plain   unverified composition      -> charged, 200
          verified_processed verified, unverified process-> charged, 400
        Total 700 kcal, of which 600 rests on unopened evidence.
        """

        from dataclasses import replace

        from core.foods.models import Recipe, ServingUnit
        from tests.factories import make_ingredient

        verified_plain = make_ingredient(
            "verified_plain", energy_kcal=100.0, protein_g=0.0, fat_g=0.0, carb_g=25.0
        )
        unverified_plain = replace(
            make_ingredient(
                "unverified_plain", energy_kcal=200.0, protein_g=0.0,
                fat_g=0.0, carb_g=50.0,
            ),
            verified=False,
        )
        verified_processed = make_ingredient(
            "verified_processed", energy_kcal=400.0, protein_g=0.0,
            fat_g=44.0, carb_g=0.0,
        )
        ingredients = {
            i.id: i for i in (verified_plain, unverified_plain, verified_processed)
        }
        recipe = Recipe(
            id="mixed", name="mixed", region=Region.SOUTH_INDIAN,
            diet_patterns=frozenset({DietPattern.VEGETARIAN}),
            ingredients=(
                RecipeIngredient("verified_plain", 100.0, RawOrCooked.AS_USED),
                RecipeIngredient("unverified_plain", 100.0, RawOrCooked.AS_USED),
                RecipeIngredient(
                    "verified_processed", 100.0, RawOrCooked.AS_USED,
                    process_key=self._UNVERIFIED_PROCESS,
                ),
            ),
            serving_unit=ServingUnit(
                name="plate", grams_per_unit=300.0,
                min_count=1, default_count=1, max_count=3,
            ),
            prep_minutes=10,
            process_uncertainty={m: 0.0 for m in MACRO_KEYS},
        )
        return Component(recipe=recipe, category="base"), ingredients

    def test_a_verified_line_with_no_process_is_not_charged(self):
        # The whole point of finding 20's first direction: the old rule charged
        # this recipe's entire 700 kcal because ONE of its lines carries an
        # unverified process constant. 600 of 700, not 700 of 700.
        component, ingredients = self._mixed()
        est = nutrition_of_components([(component, 1)], ingredients)
        assert est.point.energy_kcal == pytest.approx(700.0)
        assert est.unverified_energy_kcal == pytest.approx(600.0)
        assert est.unverified_energy_fraction() == pytest.approx(600.0 / 700.0)

    def test_unverified_composition_is_charged(self):
        # Finding 20's second direction. Flipping the one unverified row to
        # verified must drop exactly its 200 kcal and nothing else — a
        # perturbation check, not a restatement of the rule.
        from dataclasses import replace

        component, ingredients = self._mixed()
        all_verified = {
            k: replace(v, verified=True) for k, v in ingredients.items()
        }
        est = nutrition_of_components([(component, 1)], all_verified)
        assert est.unverified_energy_kcal == pytest.approx(400.0)

    def test_an_unverified_process_constant_charges_its_own_line(self):
        # And only its own line. Dropping the process_key must remove exactly
        # 400 kcal, leaving the composition-only charge.
        from dataclasses import replace

        component, ingredients = self._mixed()
        recipe = component.recipe
        no_process = replace(
            recipe,
            ingredients=tuple(
                replace(line, process_key=None) for line in recipe.ingredients
            ),
        )
        est = nutrition_of_components(
            [(Component(recipe=no_process, category="base"), 1)], ingredients
        )
        assert est.unverified_energy_kcal == pytest.approx(200.0)

    def test_a_line_unverified_twice_over_is_charged_once(self):
        # The union. Marking the processed line's ingredient unverified too
        # makes it unverified for BOTH reasons; its 400 kcal must still be 400.
        # Summing the two terms instead would give 1000 of 700 -- a plate over
        # 100% of its own energy, which is the shape of the bug this guards.
        from dataclasses import replace

        component, ingredients = self._mixed()
        both = dict(ingredients)
        both["verified_processed"] = replace(
            both["verified_processed"], verified=False
        )
        est = nutrition_of_components([(component, 1)], both)
        assert est.unverified_energy_kcal == pytest.approx(600.0)
        assert est.unverified_energy_fraction() <= 1.0

    def test_the_charge_scales_with_the_serving_count(self):
        # 3 units: 1800 of 2100. A per-line attribution that forgot unit_count
        # would charge 600 against a 2100 kcal plate and report 28.6% -- and an
        # under-charge is the dangerous direction, because it is the one that
        # lets a plate slip under the shipping threshold it should fail.
        component, ingredients = self._mixed()
        est = nutrition_of_components([(component, 3)], ingredients)
        assert est.point.energy_kcal == pytest.approx(2100.0)
        assert est.unverified_energy_kcal == pytest.approx(1800.0)


class TestEligibilityConsequence:
    """What the uncertainty ceiling implies for the library as it stands.

    Recorded as a test rather than a note because the consequence is the kind
    that gets discovered late and then quietly designed around: the tempting
    fix, once core/planner returns nothing, is to nudge 0.25 down or 0.15 up
    until a demo works. Both edits look reasonable in isolation. This test makes
    either one a deliberate act with a failing assertion attached.
    """

    def test_the_four_load_bearing_constants_are_exactly_these_values(self):
        # Pinned to literals, not directions. Every one of these four decides
        # whether the library can plan anything, and the tempting fix once
        # core/planner returns nothing is to nudge one of them until a demo
        # works. Each edit looks reasonable alone. Changing any of these numbers
        # must mean deliberately editing this test and saying why in the commit.
        assert citations.value_of("composition.unverified_secondary") == 0.25
        assert citations.value_of("composition.verified_primary") == 0.05
        assert citations.value_of("eligibility.max_protein_uncertainty") == 0.15
        assert citations.value_of("eligibility.max_energy_uncertainty") == 0.20

    #: The three dishes that cook without oil — steamed, boiled, dry-griddled.
    #: D10 (2026-08-09) made them declare every macro `unassessed` rather than
    #: derive a bare zero from having no `process:` line, so they alone carry a
    #: process term on protein. Named here once, used by the two tests below.
    NO_OIL_COOKED = ("idli", "phulka", "steamed_rice")

    def test_every_recipe_sits_at_exactly_its_registered_band(
        self, library, ingredients
    ):
        # Exact figures, not "above the ceiling". A direction-only assertion
        # would survive a band drifting to 0.9 or to 0.16; these do not.
        #
        # Two populations, and the split is the whole point. Oil carries no
        # protein, so on an oil-cooked dish no process term touches this macro
        # and 0.25 is the composition band alone. On the three that cook without
        # oil there is no constant to attribute anything to, so D10 requires them
        # to declare the macro unassessed: 0.25 composition + 0.20 registered
        # wide band = 0.45. Before D10 they reported 0.25 too — the same number
        # as a raw raita — which is the false precision finding 2 named.
        #
        # min_count, not a hard-coded 1: uncertainty_fraction is scale-invariant
        # so the count is arbitrary, but nutrition_of_recipe enforces the
        # serving unit's bounds and idli's floor is 2. Same defect these three
        # tests shared with core/planner/candidates.py until 2026-08-07.
        unassessed_band = citations.value_of("process.unassessed_uncertainty")
        assert unassessed_band == 0.20
        for recipe_id, component in library.components.items():
            est = nutrition_of_components(
                [(component, component.recipe.serving_unit.min_count)], ingredients
            )
            expected = 0.25 + (unassessed_band if recipe_id in self.NO_OIL_COOKED else 0.0)
            assert est.uncertainty_fraction("protein_g") == pytest.approx(expected), (
                f"{recipe_id}: protein band is neither the unverified-composition "
                "constant nor that plus the registered unassessed band"
            )

    def test_no_recipe_currently_clears_the_protein_eligibility_ceiling(
        self, library, ingredients
    ):
        # 0.25 against a 0.15 ceiling, for all three. Protein is target-critical
        # for essentially every profile this product serves, so the candidate
        # pool is empty for all of them — and the relaxation ladder cannot help,
        # because it moves tolerance and never uncertainty.
        ceiling = citations.value_of("eligibility.max_protein_uncertainty")
        assert ceiling == 0.15
        for recipe_id, component in library.components.items():
            est = nutrition_of_components(
                [(component, component.recipe.serving_unit.min_count)], ingredients
            )
            assert est.uncertainty_fraction("protein_g") > ceiling, (
                f"{recipe_id} unexpectedly clears the ceiling; if this is real "
                "progress, update docs/methodology.md — the claim that nothing "
                "can ship as validated is stated there"
            )

    def test_verifying_every_row_clears_the_ceiling_for_all_but_three_recipes(
        self, library, ingredients
    ):
        """What ingredient verification buys, and where it stops buying.

        This test used to assert that verifying every row clears the protein
        ceiling for the whole library. D10 (2026-08-09) made that false, and the
        falsity is real rather than bookkeeping: `idli`, `phulka` and
        `steamed_rice` cook without oil, no registered constant describes
        steaming, boiling or dry-griddling, and so their protein carries the
        0.20 unassessed band no matter how good the composition data gets.
        0.05 + 0.20 = 0.25, still above the 0.15 ceiling.

        Opening IFCT for every ingredient is therefore **not sufficient** to
        make this library shippable. That needs process constants too — which is
        `docs/audit_log.md` finding 41, and is a different piece of work from the
        ten-row human sign-off D7 is waiting on. Stated as exact numbers so a
        future change to either constant surfaces here rather than quietly
        rewriting the shipping story.
        """
        from dataclasses import replace

        from core.schemas import MACRO_KEYS

        verified = {
            key: replace(
                ing,
                verified=True,
                composition_uncertainty={m: 0.05 for m in MACRO_KEYS},
            )
            for key, ing in ingredients.items()
        }
        ceiling = citations.value_of("eligibility.max_protein_uncertainty")
        cleared, blocked = [], []
        for recipe_id, component in library.components.items():
            est = nutrition_of_components(
                [(component, component.recipe.serving_unit.min_count)], verified
            )
            fraction = est.uncertainty_fraction("protein_g")
            if recipe_id in self.NO_OIL_COOKED:
                assert fraction == pytest.approx(0.25)
                assert fraction > ceiling
                blocked.append(recipe_id)
            else:
                assert fraction == pytest.approx(0.05)
                assert fraction < ceiling
                cleared.append(recipe_id)
        assert sorted(blocked) == sorted(self.NO_OIL_COOKED)
        assert len(cleared) == len(library.components) - 3

    def test_every_registered_evidence_is_still_unverified(self):
        # The precondition for the above. If this ever fails, someone has opened
        # a source document, and the shipping story genuinely changes.
        unverified_ids = sorted(ev.id for ev in citations.all_evidence() if not ev.verified)
        assert unverified_ids == sorted(ev.id for ev in citations.all_evidence()), (
            "some Evidence is now verified — docs/methodology.md's 'nothing can "
            "ship as validated' claim must be re-derived, not left standing"
        )

    def test_water_is_the_only_verified_ingredient_row(self, ingredients):
        # The other precondition, pinned to the exact set rather than a count.
        #
        # `water` is legitimately verified: "water contributes no nutrients" is
        # not a claim that needs IFCT open on the desk. It is also the only row
        # whose verification cannot move any band, since all nine of its macros
        # are zero — so its presence does not weaken the shipping story below.
        # Both data/raw/ifct/README.md and docs/methodology.md previously stated
        # that *every* row is unverified; they were wrong, and this test is what
        # found it.
        assert sorted(k for k, v in ingredients.items() if v.verified) == ["water"]
        assert ingredients["water"].composition_uncertainty_for("protein_g") == 0.05
        assert ingredients["water"].per_100g() == NutritionVector.zero()
        assert all(
            ing.composition_uncertainty_for("protein_g") == 0.25
            for k, ing in ingredients.items()
            if k != "water"
        )


class TestStateMismatch:
    def test_a_cooked_quantity_against_a_raw_record_is_refused(
        self, library, ingredients
    ):
        # Reading the 356.4 kcal/100 g raw rice record against a cooked
        # quantity is a 3x error, not a tolerance-band problem — so it raises
        # rather than guessing a yield factor.
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
