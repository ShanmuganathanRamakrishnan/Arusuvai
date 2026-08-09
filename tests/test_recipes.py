"""Hand-computed macros for the three example recipes.

Every expected value below is arithmetic done from the composition rows in
``data/raw/ifct/fixture_ingredients.csv``, shown term by term. None of it is a
snapshot of what the code currently returns — if a fixture value changes, these
numbers must be recomputed by hand, which is the point.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from core.foods.nutrition_of import nutrition_of_recipe
from core.schemas import MACRO_KEYS, DietPattern, Region


class TestSambarSadam:
    """One cup, 200 g: rice 108, toor dal 45, tomato 12, onion 12, carrot 10,
    tamarind 3, sambar powder 3, gingelly oil 4, mustard 1, curry leaf 1, salt 1.
    108+45+12+12+10+3+3+4+1+1+1 = 200 g.
    """

    def test_energy(self, library, ingredients):
        # kcal, per-100 g record x grams/100:
        #   rice      1.30 x 108 = 140.40
        #   toor dal  1.21 x  45 =  54.45
        #   tomato    0.20 x  12 =   2.40
        #   onion     0.40 x  12 =   4.80
        #   carrot    0.41 x  10 =   4.10
        #   tamarind  2.39 x   3 =   7.17
        #   sambar pw 3.40 x   3 =  10.20
        #   oil       8.84 x   4 =  35.36
        #   mustard   5.08 x   1 =   5.08
        #   curry     1.08 x   1 =   1.08
        #   salt      0.00 x   1 =   0.00
        #   total                 = 265.04
        v = nutrition_of_recipe(library.recipes["sambar_sadam"], 1, ingredients)
        assert v.energy_kcal == pytest.approx(265.04)

    def test_protein(self, library, ingredients):
        #   rice     0.027 x 108 = 2.916
        #   toor dal 0.070 x  45 = 3.150
        #   tomato   0.009 x  12 = 0.108
        #   onion    0.011 x  12 = 0.132
        #   carrot   0.009 x  10 = 0.090
        #   tamarind 0.028 x   3 = 0.084
        #   sambar   0.140 x   3 = 0.420
        #   mustard  0.200 x   1 = 0.200
        #   curry    0.060 x   1 = 0.060
        #   total                = 7.160
        v = nutrition_of_recipe(library.recipes["sambar_sadam"], 1, ingredients)
        assert v.protein_g == pytest.approx(7.16)

    def test_fat(self, library, ingredients):
        #   rice 0.324 + dal 0.180 + tomato 0.024 + onion 0.012 + carrot 0.020
        #   + tamarind 0.018 + sambar powder 0.360 + oil 4.000 + mustard 0.397
        #   + curry 0.010 = 5.345
        v = nutrition_of_recipe(library.recipes["sambar_sadam"], 1, ingredients)
        assert v.fat_g == pytest.approx(5.345)

    def test_two_cups_is_exactly_double(self, library, ingredients):
        # 265.04 x 2 = 530.08. Portions scale by integer unit count, nothing else.
        v = nutrition_of_recipe(library.recipes["sambar_sadam"], 2, ingredients)
        assert v.energy_kcal == pytest.approx(530.08)

    def test_diet_patterns_and_region(self, library):
        r = library.recipes["sambar_sadam"]
        assert r.region is Region.SOUTH_INDIAN
        assert DietPattern.VEGAN in r.diet_patterns
        # Onion and carrot: not jain, and that is stated rather than derived
        # from "vegetarian".
        assert DietPattern.JAIN not in r.diet_patterns


class TestRajmaChawal:
    """One plate, 350 g: rice 183, rajma 110, onion 20, tomato 20, oil 8,
    ginger-garlic 5, garam masala 2, salt 2. Sums to 350 g.
    """

    def test_energy(self, library, ingredients):
        #   rice   1.30 x 183 = 237.90
        #   rajma  1.27 x 110 = 139.70
        #   onion  0.40 x  20 =   8.00
        #   tomato 0.20 x  20 =   4.00
        #   oil    8.84 x   8 =  70.72
        #   gg     1.00 x   5 =   5.00
        #   garam  3.21 x   2 =   6.42
        #   salt   0.00 x   2 =   0.00
        #   total             = 471.74
        # garam_masala corrected from 3.79 to 3.21 kcal/g (379->321 kcal/100g)
        # 2026-07-24 to reconcile against its own declared fibre content once
        # atwater.fibre_kcal_per_g was added — see citations.py and
        # docs/methodology.md, "Known limitations, Phase 1" item 3.
        v = nutrition_of_recipe(library.recipes["rajma_chawal"], 1, ingredients)
        assert v.energy_kcal == pytest.approx(471.74)

    def test_protein(self, library, ingredients):
        #   rice  0.027 x 183 = 4.941
        #   rajma 0.087 x 110 = 9.570
        #   onion 0.011 x  20 = 0.220
        #   tomato 0.009 x 20 = 0.180
        #   gg    0.040 x   5 = 0.200
        #   garam 0.140 x   2 = 0.280
        #   total             = 15.391
        v = nutrition_of_recipe(library.recipes["rajma_chawal"], 1, ingredients)
        assert v.protein_g == pytest.approx(15.391)

    def test_fat(self, library, ingredients):
        #   rice 0.549 + rajma 0.550 + onion 0.020 + tomato 0.040 + oil 8.000
        #   + gg 0.030 + garam 0.300 = 9.489
        v = nutrition_of_recipe(library.recipes["rajma_chawal"], 1, ingredients)
        assert v.fat_g == pytest.approx(9.489)

    def test_sodium_is_dominated_by_added_salt(self, library, ingredients):
        #   salt 393.39 mg/g x 2 g = 786.78
        #   rice 0.01 x 183 = 1.83 ; rajma 0.04 x 110 = 4.40 ; onion 0.80 ;
        #   tomato 1.00 ; gg 0.75 ; garam 1.20  -> 9.98
        #   total = 796.76
        # Rederived 2026-07-31: salt_iodised moved 38758 -> 39339 mg/100g, the
        # stoichiometric figure its own note already claimed (22.99/58.44).
        # The expectation is recomputed from the new constant, not snapshotted
        # from output -- 98.7% of this dish's sodium is the salt line, so a
        # change to that row must move this number and be seen to.
        v = nutrition_of_recipe(library.recipes["rajma_chawal"], 1, ingredients)
        assert v.sodium_mg == pytest.approx(796.76)


class TestMasalaDosa:
    """One dosa unit, 150 g = 90 g dosa + 60 g potato masala.
    Batter is recorded as raw rice 26 + raw urad 9 + water 51, because no
    cooked-basis composition entry exists for a fermented griddled batter.
    """

    def test_energy(self, library, ingredients):
        # rice_milled_raw corrected 2026-07-24 to real IFCT 2017 values
        # (code A015: 356.4 kcal, 7.94 g protein, 0.52 g fat per 100 g) — see
        # citations.py and data/raw/ifct/README.md.
        #   rice raw   3.564 x 26.0 = 92.664
        #   urad raw   3.41  x  9.0 = 30.69
        #   water      0.00  x 51.0 =  0.00
        #   griddle oil 8.84 x  3.5 = 30.94
        #   potato     0.87  x 44.0 = 38.28
        #   onion      0.40  x 10.0 =  4.00
        #   temper oil 8.84  x  3.0 = 26.52
        #   chilli     0.44  x  1.0 =  0.44
        #   mustard    5.08  x  0.5 =  2.54
        #   curry      1.08  x  0.5 =  0.54
        #   salt       0.00  x  1.5 =  0.00
        #   total                   = 226.614
        v = nutrition_of_recipe(library.recipes["masala_dosa"], 1, ingredients)
        assert v.energy_kcal == pytest.approx(226.614)

    def test_protein(self, library, ingredients):
        #   rice   0.0794 x 26.0 = 2.0644
        #   urad   0.240  x  9.0 = 2.160
        #   potato 0.019  x 44.0 = 0.836
        #   onion  0.011  x 10.0 = 0.110
        #   chilli 0.019  x  1.0 = 0.019
        #   mustard 0.200 x  0.5 = 0.100
        #   curry  0.060  x  0.5 = 0.030
        #   total                = 5.3194
        v = nutrition_of_recipe(library.recipes["masala_dosa"], 1, ingredients)
        assert v.protein_g == pytest.approx(5.3194)

    def test_fat(self, library, ingredients):
        #   rice 0.1352 + urad 0.126 + griddle oil 3.500 + potato 0.044
        #   + onion 0.010 + temper oil 3.000 + chilli 0.004 + mustard 0.1985
        #   + curry 0.005 = 7.0227
        v = nutrition_of_recipe(library.recipes["masala_dosa"], 1, ingredients)
        assert v.fat_g == pytest.approx(7.0227)

    def test_water_line_carries_no_nutrients_but_makes_the_mass_add_up(
        self, library, ingredients
    ):
        recipe = library.recipes["masala_dosa"]
        total_g = sum(line.quantity_g for line in recipe.ingredients)
        assert total_g == pytest.approx(recipe.serving_unit.grams_per_unit)
        assert ingredients["water"].energy_kcal == 0

    def test_default_serving_is_two_dosas(self, library, ingredients):
        # 226.614 x 2 = 453.228
        recipe = library.recipes["masala_dosa"]
        assert recipe.serving_unit.default_count == 2
        v = nutrition_of_recipe(recipe, recipe.serving_unit.default_count, ingredients)
        assert v.energy_kcal == pytest.approx(453.228)


class TestRecipeLoaderRules:
    def test_every_recipe_in_the_library_loads_with_no_warnings(self, library):
        # Deliberately not a hardcoded id set. The previous version of this
        # test named the three recipes that existed when it was written, so
        # adding a fourth failed it -- reporting "a recipe was added" as though
        # it were a defect, and saying nothing about whether that recipe loaded
        # cleanly. The claim worth pinning is that *whatever* is in
        # data/recipes/ loads: nothing rejected, nothing warned, and the count
        # is whatever the directory holds.
        assert library.recipes, "the recipe library must not be empty"
        assert library.rejected == []
        assert library.warnings == []

    def test_every_recipe_file_on_disk_is_present_in_the_loaded_library(
        self, library
    ):
        # The companion to the above: "nothing was rejected" is only
        # meaningful alongside "nothing was skipped". A file that never
        # reached the loader at all produces an empty `rejected` list too, so
        # the count is checked against the directory rather than assumed.
        from tests.conftest import RECIPE_DIR

        # schema.yaml is the format specification, not a recipe. Counted
        # rather than matched by name: nothing requires a recipe's id to equal
        # its filename, so asserting that would invent a rule schema.yaml does
        # not state.
        on_disk = [p for p in RECIPE_DIR.glob("*.yaml") if p.stem != "schema"]
        assert len(library.recipes) == len(on_disk)

    def test_every_recipe_category_is_plannable(self, library):
        from core.foods.templates import ALL_TEMPLATES

        accepted = frozenset().union(*(t.categories() for t in ALL_TEMPLATES))
        for component in library.components.values():
            assert component.category in accepted

    def test_declared_uncertainty_is_backed_by_registered_constants(self, library):
        """D10, settled 2026-08-09. This test was red on purpose for weeks.

        It used to read ``if recipe.process_uncertainty: assert
        recipe.process_constants``. That condition is **always true** —
        `Recipe.process_uncertainty` is mandatory per macro, so the mapping is
        never empty — which made the real assertion "every recipe carries a
        process constant". That held only by accident, until `idli` and
        `steamed_rice` arrived in D3 as the library's first dishes with no oil
        in them, and `onion_raita` as the first cooked by nothing at all.

        A steamed idli genuinely has no oil-uptake constant, so the old rule
        was not something to satisfy. What it was reaching for is below: every
        constant a recipe names must be registered, and no macro may sit at a
        zero nobody earned. The second half is enforced at load time and graded
        by `TestZeroProcessUncertaintyMustBeEarned`.
        """
        from core.nutrition import citations

        for recipe in library.recipes.values():
            for key in recipe.process_constants:
                assert citations.constant(key)


    def test_dosa_uncertainty_matches_its_own_arithmetic(self, library, ingredients):
        # Declared energy band, rederived here from the recipe's own oil lines.
        # Denominator is 226.614 kcal, not 223.65, since rice_milled_raw was
        # corrected to real IFCT values 2026-07-24 (see TestMasalaDosa.test_energy):
        #   griddle oil 3.5 g x 8.84 kcal/g x 0.20 = 6.188 kcal
        #   temper  oil 3.0 g x 8.84 kcal/g x 0.10 = 2.652 kcal
        #   (6.188 + 2.652) / 226.614 kcal = 0.03901
        recipe = library.recipes["masala_dosa"]
        expected = (3.5 * 8.84 * 0.20 + 3.0 * 8.84 * 0.10) / 226.614
        assert recipe.uncertainty_for("energy_kcal") == pytest.approx(expected, abs=1e-3)

    def test_process_constants_are_derived_from_the_ingredient_lines(self, library):
        # Not read from a recipe-level list: derived, so a stale list cannot
        # disagree with the lines it claims to describe.
        dosa = library.recipes["masala_dosa"]
        assert dosa.process_constants == frozenset(
            {"oil_uptake.dosa_griddled", "oil_uptake.vegetable_tempering"}
        )
        assert library.recipes["sambar_sadam"].process_constants == frozenset(
            {"oil_uptake.vegetable_tempering"}
        )

    def test_two_lines_of_the_same_ingredient_carry_different_processes(self, library):
        # The case a recipe-level list cannot express, and the reason the dosa's
        # energy band needed two terms: 3.5 g griddle oil at +/-20%, 3.0 g
        # tempering oil at +/-10%, same ingredient id.
        dosa = library.recipes["masala_dosa"]
        griddled = dosa.lines_for_process("oil_uptake.dosa_griddled")
        tempered = dosa.lines_for_process("oil_uptake.vegetable_tempering")
        assert [line.ingredient_id for line in griddled] == ["gingelly_oil"]
        assert [line.ingredient_id for line in tempered] == ["gingelly_oil"]
        assert griddled[0].quantity_g == pytest.approx(3.5)
        assert tempered[0].quantity_g == pytest.approx(3.0)

    def test_exposure_is_computed_from_the_lines_not_transcribed(self, library):
        from dataclasses import replace

        dosa = library.recipes["masala_dosa"]
        assert dosa.process_exposure_g("oil_uptake.dosa_griddled") == pytest.approx(3.5)

        # The regression this whole change exists to make impossible: edit a
        # quantity and the derived figure must move with it. A stored exposure
        # fraction would sit unchanged here with the suite still green.
        heavier = replace(
            dosa,
            ingredients=tuple(
                replace(line, quantity_g=7.0)
                if line.process_key == "oil_uptake.dosa_griddled"
                else line
                for line in dosa.ingredients
            ),
            # 3.5 g more oil, so the declared unit weight must move too or the
            # mass-consistency check in Recipe.__post_init__ rejects it.
            serving_unit=replace(
                dosa.serving_unit, grams_per_unit=dosa.serving_unit.grams_per_unit + 3.5
            ),
        )
        assert heavier.process_exposure_g("oil_uptake.dosa_griddled") == pytest.approx(7.0)

    def test_a_recipe_level_process_constants_key_is_rejected(self, tmp_path, ingredients):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        bad = tmp_path / "stale_list.yaml"
        bad.write_text(
            "\n".join(
                [
                    "id: stale",
                    "name: Stale",
                    "region: south_indian",
                    "diet_patterns: [vegetarian]",
                    "category: rice",
                    "serving_unit:",
                    "  measure: cup",
                    "  grams_per_unit: 100.0",
                    "  min_count: 1",
                    "  default_count: 1",
                    "  max_count: 2",
                    # Names a real constant, and no line uses it — exactly the
                    # silent disagreement the derived property rules out.
                    "process_constants: [oil_uptake.dosa_griddled]",
                    "ingredients:",
                    "  - id: rice_cooked",
                    "    quantity_g: 100.0",
                    "    state: cooked",
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="no longer read"):
            load_recipe_file(Path(bad), ingredients)

    def test_a_line_may_not_name_an_unregistered_process(self, tmp_path, ingredients):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        bad = tmp_path / "invented_process.yaml"
        bad.write_text(
            "\n".join(
                [
                    "id: invented",
                    "name: Invented",
                    "region: south_indian",
                    "diet_patterns: [vegetarian]",
                    "category: rice",
                    "serving_unit:",
                    "  measure: cup",
                    "  grams_per_unit: 100.0",
                    "  min_count: 1",
                    "  default_count: 1",
                    "  max_count: 2",
                    "ingredients:",
                    "  - id: rice_cooked",
                    "    quantity_g: 100.0",
                    "    state: cooked",
                    "    process: oil_uptake.deep_fried_vada",
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(KeyError, match="no constant registered"):
            load_recipe_file(Path(bad), ingredients)

    def test_process_uncertainty_is_derived_from_the_constants_not_pasted(
        self, library
    ):
        # 884 kcal/100 g oil. Denominator is 226.614 kcal, not 223.65, since
        # rice_milled_raw was corrected to real IFCT values 2026-07-24 (see
        # TestMasalaDosa.test_energy):
        #   griddle 3.5 g x 8.84 x 0.20 = 6.188 kcal
        #   temper  3.0 g x 8.84 x 0.10 = 2.652 kcal
        #   8.840 / 226.614 kcal          = 0.03900906...
        dosa = library.recipes["masala_dosa"]
        assert dosa.uncertainty_for("energy_kcal") == pytest.approx(0.03900906, abs=1e-8)
        #   fat: (3.5 x 1.0 x 0.20) + (3.0 x 1.0 x 0.10) = 1.0 g
        #   over the dish's exact 7.0227 g fat (see TestMasalaDosa.test_fat —
        #   the recipe file's note rounds this to 7.02, which is why the band is
        #   derived from the composition rows and not from that note)
        #   1.0 / 7.0227 = 0.14239537...
        assert dosa.uncertainty_for("fat_g") == pytest.approx(0.14239537, abs=1e-8)

    def test_mutating_a_constant_moves_every_recipe_that_depends_on_it(
        self, ingredients, tmp_path
    ):
        # The perturbation test. A static assertion against a fixed YAML value
        # cannot catch a stale figure — that is precisely how the pasted
        # 0.040 survived. Here the constant is changed and the recipe's derived
        # uncertainty must follow it, or the derivation is not real.
        from pathlib import Path

        from core.foods.recipe_loader import load_recipes
        from core.nutrition import citations

        recipe_dir = Path(__file__).resolve().parents[1] / "data" / "recipes"
        before = load_recipes(recipe_dir, ingredients, strict=True)
        dosa_before = before.recipes["masala_dosa"].uncertainty_for("energy_kcal")

        original = citations._CONSTANTS["oil_uptake.dosa_griddled"]
        doubled = replace(original, uncertainty=original.uncertainty * 2)
        citations._CONSTANTS["oil_uptake.dosa_griddled"] = doubled
        try:
            after = load_recipes(recipe_dir, ingredients, strict=True)
            dosa_after = after.recipes["masala_dosa"].uncertainty_for("energy_kcal")
        finally:
            citations._CONSTANTS["oil_uptake.dosa_griddled"] = original

        # Only the griddle term doubles; the tempering term is untouched.
        # Denominator is 226.614 kcal, not 223.65 (rice_milled_raw corrected
        # to real IFCT values 2026-07-24, see TestMasalaDosa.test_energy):
        #   (3.5 x 8.84 x 0.40) + (3.0 x 8.84 x 0.10) = 12.376 + 2.652 = 15.028
        #   15.028 / 226.614 = 0.06631541...
        assert dosa_before == pytest.approx(0.03900906, abs=1e-8)
        assert dosa_after == pytest.approx(0.06631541, abs=1e-8)
        assert dosa_after > dosa_before

        # And a recipe that does not use that constant must NOT move.
        assert after.recipes["sambar_sadam"].uncertainty_for(
            "energy_kcal"
        ) == pytest.approx(
            before.recipes["sambar_sadam"].uncertainty_for("energy_kcal")
        )

    def test_an_unassessed_macro_takes_the_registered_wide_band(self, library):
        # Declaring a macro unassessed must be worse than measuring it, never a
        # cheap way to a tidy number.
        from core.nutrition import citations

        wide = citations.value_of("process.unassessed_uncertainty")
        dosa = library.recipes["masala_dosa"]
        assert dosa.uncertainty_for("iron_mg") == pytest.approx(wide)
        assert dosa.uncertainty_for("b12_ug") == pytest.approx(wide)
        # Strictly worse than any measured process constant in the registry.
        assert wide > dosa.uncertainty_for("energy_kcal")

    def test_every_recipe_carries_a_value_for_every_macro(self, library):
        # No default-zero anywhere: an omitted macro cannot reach a Recipe.
        for recipe in library.recipes.values():
            for macro in MACRO_KEYS:
                assert isinstance(recipe.uncertainty_for(macro), float)

    def test_a_recipe_may_not_paste_a_process_uncertainty_figure(
        self, tmp_path, ingredients
    ):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        bad = tmp_path / "pasted.yaml"
        bad.write_text(
            "\n".join(
                [
                    "id: pasted",
                    "name: Pasted",
                    "region: south_indian",
                    "diet_patterns: [vegetarian]",
                    "category: rice",
                    "serving_unit:",
                    "  measure: cup",
                    "  grams_per_unit: 100.0",
                    "  min_count: 1",
                    "  default_count: 1",
                    "  max_count: 2",
                    "process_uncertainty:",
                    "  energy_kcal: 0.25",
                    "ingredients:",
                    "  - id: rice_cooked",
                    "    quantity_g: 100.0",
                    "    state: cooked",
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="no longer read from the recipe file"):
            load_recipe_file(Path(bad), ingredients)


class TestZeroProcessUncertaintyMustBeEarned:
    """`docs/audit_log.md` finding 2, and D10's question.

    "Can a recipe declare uncertainty with nothing to attribute it to?" Yes —
    but only by saying which case it is in, because a raw raita and a griddled
    phulka produced byte-identical zeros from byte-identical silence.
    """

    _BASE = [
        "id: probe",
        "name: Probe",
        "region: south_indian",
        "diet_patterns: [vegetarian]",
        "category: rice",
        "serving_unit:",
        "  measure: cup",
        "  grams_per_unit: 100.0",
        "  min_count: 1",
        "  default_count: 1",
        "  max_count: 2",
    ]

    #: The default probe is a RAW-basis line, deliberately. D12 gave the loader
    #: a third earned path — a macro fed only by served-basis rows needs no
    #: justification — which would make every rejection test in this class
    #: vacuous if the probe stayed on `rice_cooked`: the dish would load clean
    #: and the tests would pass without exercising anything they name.
    _RAW_LINES = ["ingredients:", "  - id: rice_milled_raw", "    quantity_g: 100.0",
                  "    state: raw"]
    _SERVED_LINES = ["ingredients:", "  - id: rice_cooked", "    quantity_g: 100.0",
                     "    state: cooked"]

    def _write(self, tmp_path, *extra, lines=None):
        bad = tmp_path / "probe.yaml"
        body = list(self._BASE) + list(extra) + (lines or self._RAW_LINES)
        bad.write_text("\n".join(body), encoding="utf-8")
        return bad

    def test_silence_is_rejected_because_it_is_the_cheapest_path(
        self, tmp_path, ingredients
    ):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        # No process line, no `preparation`, no unassessed list. Before D10 this
        # loaded and claimed perfect process certainty on every macro.
        with pytest.raises(ValueError, match="nothing behind it"):
            load_recipe_file(Path(self._write(tmp_path)), ingredients)

    def test_declaring_the_dish_uncooked_earns_the_zeros(self, tmp_path, ingredients):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        recipe, _ = load_recipe_file(
            Path(self._write(tmp_path, "preparation: uncooked")), ingredients
        )
        assert recipe.uncertainty_for("energy_kcal") == 0.0
        assert recipe.process_constants == frozenset()

    def test_listing_the_macros_unassessed_also_earns_them(self, tmp_path, ingredients):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file
        from core.nutrition import citations

        recipe, _ = load_recipe_file(
            Path(
                self._write(
                    tmp_path,
                    "process_uncertainty_unassessed:",
                    "  [energy_kcal, protein_g, fat_g, carb_g, fibre_g,"
                    " sodium_mg, iron_mg, calcium_mg, b12_ug]",
                )
            ),
            ingredients,
        )
        wide = citations.value_of("process.unassessed_uncertainty")
        assert recipe.uncertainty_for("energy_kcal") == pytest.approx(wide)

    def test_a_macro_the_dish_contains_none_of_needs_no_justification(
        self, tmp_path, ingredients
    ):
        """The guard that keeps the rule from demanding the impossible.

        Rice carries 0 µg of B12. Its process uncertainty on B12 derives to 0.0
        because there is no B12 to be uncertain about, which is not a claim
        about cooking and not the author's to earn. Without the filter, a rice
        dish would have to declare B12 unassessed to load at all — a wide band
        on a macro it does not contain, which is noise dressed as caution.

        This test exists because it did not: mutation R5 in
        `docs/design/probes/d4b_mutations.py` deleted the arm and nothing in
        `tests/test_recipes.py` went red. The real recipes hid it — the cooked
        no-process dishes declared every macro unassessed, so the arm had
        nothing left to filter.

        **The arm it guards changed in D12** and the test still holds, which is
        the useful part. D10 wrote the filter as ``getattr(total, macro) != 0``;
        D12 replaced it with ``from_raw[macro] != 0``, which subsumes it —
        nutrient values are non-negative, so no raw-basis grams means no grams
        at all from a line anyone must justify. The probe is a raw-basis line,
        so every other macro here IS unearned and B12 is genuinely the one being
        filtered; the assertion is not passing by accident of the served-basis
        path.
        """
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        every_macro_but_b12 = [m for m in MACRO_KEYS if m != "b12_ug"]
        recipe, _ = load_recipe_file(
            Path(
                self._write(
                    tmp_path,
                    "process_uncertainty_unassessed:",
                    f"  [{', '.join(every_macro_but_b12)}]",
                )
            ),
            ingredients,
        )
        assert recipe.uncertainty_for("b12_ug") == 0.0

    def test_an_uncooked_dish_may_not_also_name_a_process(self, tmp_path, ingredients):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        # Both statements cannot be true, and silently honouring one would pick
        # a winner the author did not choose.
        with pytest.raises(ValueError, match="preparation is 'uncooked'"):
            load_recipe_file(
                Path(
                    self._write(
                        tmp_path,
                        "preparation: uncooked",
                        lines=[
                            "ingredients:",
                            "  - id: rice_cooked",
                            "    quantity_g: 100.0",
                            "    state: cooked",
                            "  - id: gingelly_oil",
                            "    quantity_g: 3.0",
                            "    state: raw",
                            "    process: oil_uptake.vegetable_tempering",
                        ],
                    )
                ),
                ingredients,
            )

    def test_a_served_basis_row_earns_its_zeros_without_declaring_anything(
        self, tmp_path, ingredients
    ):
        """D12, `docs/audit_log.md` finding 44 — the third earned path.

        `rice_cooked` is a cooked-basis composition record. A recipe naming a
        portion of it applies no transformation, so there is no process step
        whose uncertainty went unmeasured, and the zero is earned without a
        `preparation:` claim or an unassessed list. This is what D10 got wrong
        on `steamed_rice`: it charged 0.20 on every macro for work the recipe
        does not do, on top of the 0.25 composition band already covering
        whether the row itself is right.
        """
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        recipe, _ = load_recipe_file(
            Path(self._write(tmp_path, lines=self._SERVED_LINES)), ingredients
        )
        assert recipe.uncertainty_for("energy_kcal") == 0.0
        assert recipe.uncertainty_for("protein_g") == 0.0

    def test_calling_a_raw_row_cooked_on_the_line_does_not_earn_the_zeros(
        self, tmp_path, ingredients
    ):
        """The hole the fix for finding 44 could have opened, closed on purpose.

        `RecipeIngredient.state` is author-declared and nothing cross-checks it
        against the composition row it points at (`docs/audit_log.md` finding
        46). Had the served-basis test read the *line's* state, writing
        `state: cooked` over a raw-basis row would have become the cheapest way
        to earn a full set of zeros — the exact ordering this check exists to
        prevent, reintroduced by its own fix. It reads `Ingredient.state`.
        """
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        lying = ["ingredients:", "  - id: rice_milled_raw", "    quantity_g: 100.0",
                 "    state: cooked"]
        with pytest.raises(ValueError, match="nothing behind it"):
            load_recipe_file(Path(self._write(tmp_path, lines=lying)), ingredients)

    def test_an_unknown_preparation_is_rejected_rather_than_assumed(
        self, tmp_path, ingredients
    ):
        from pathlib import Path

        from core.foods.recipe_loader import load_recipe_file

        with pytest.raises(ValueError, match="is not one of"):
            load_recipe_file(
                Path(self._write(tmp_path, "preparation: lightly_toasted")),
                ingredients,
            )

    def test_the_real_library_no_longer_confuses_raw_with_unmeasured(self, library):
        """The measurement that made D10 answerable, pinned — and corrected.

        Before D10: `idli` (steamed), `phulka` (griddled) and `steamed_rice`
        (boiled) each derived a process energy uncertainty of 0.0 — identical to
        `onion_raita` and `thayir_plain`, which are genuinely uncooked.

        D10 gave all three the registered wide band. D12 took `steamed_rice`
        back off it (`docs/audit_log.md` finding 44): its single line is 200 g
        of `rice_cooked`, a **cooked-basis** composition row, so the boiling
        happened before the record and this recipe transforms nothing. D10 was
        charging it 0.20 for work it does not do, on top of the 0.25
        composition band already covering whether that row is right.

        Three populations now, and the split is the point of the test:
        """
        from core.nutrition import citations

        wide = citations.value_of("process.unassessed_uncertainty")

        # (a) cooked, and fed by RAW-basis rows the recipe transforms. Nothing
        # quantifies that step, so the wide band is the honest answer.
        for rid in ("idli", "phulka"):
            assert library.recipes[rid].uncertainty_for("energy_kcal") == pytest.approx(
                wide
            ), f"{rid} cooks a raw-basis row; its process uncertainty is not a bare zero"

        # (b) cooked, but fed entirely by served-basis rows. Earned zero.
        assert library.recipes["steamed_rice"].uncertainty_for("energy_kcal") == 0.0, (
            "steamed_rice names a portion of an already-boiled composition row; "
            "charging it for a transformation it does not perform double-counts "
            "the composition band"
        )

        # (c) not cooked at all. Earned zero, for a different reason.
        for rid in ("onion_raita", "thayir_plain"):
            assert library.recipes[rid].uncertainty_for("energy_kcal") == 0.0, (
                f"{rid} involves no cooking step, so a computed zero is correct "
                "and must not be widened for tidiness"
            )
