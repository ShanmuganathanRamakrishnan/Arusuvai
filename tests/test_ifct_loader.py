"""The loader's job is to refuse incoherent composition rows, loudly."""

from __future__ import annotations

import pytest

from core.foods.ifct_loader import load_ingredient_file, load_ingredients
from core.schemas import RawOrCooked

HEADER = (
    "id,name_en,name_ta,name_hi,ifct_code,state,energy_kcal,protein_g,fat_g,carb_g,"
    "fibre_g,sodium_mg,iron_mg,calcium_mg,b12_ug,diaas,is_animal_product,jain_safe,"
    "allergens,verified,source_note\n"
)


def write_csv(tmp_path, *rows):
    path = tmp_path / "test.csv"
    path.write_text(HEADER + "".join(r + "\n" for r in rows), encoding="utf-8")
    return path


class TestFixtureSet:
    def test_every_fixture_row_loads(self, load_report):
        assert load_report.rejected == []
        # 26 rows until 2026-08-02, when D2a added paneer_fresh, tofu_firm and
        # soya_chunks_dry -- the library's first ingredients carrying a DIAAS
        # above 0.62, without which the quality-source rule would decline every
        # plate.
        assert len(load_report.loaded) == 29

    def test_no_ifct_code_is_invented(self, ingredients):
        # Four rows (rice_milled_raw/A015, rajma_raw/B020, toor_dal_raw/B021,
        # potato_raw/F006) now carry real IFCT 2017 codes, extracted 2026-07-24
        # from a machine-readable re-publication of the source tables -- see
        # each row's source_note. Every other row is still hand-entered, and an
        # invented-but-plausible code would be worse than an absent one: it
        # passes every check while being wrong. So real codes are limited to
        # exactly this known set; nothing else may carry one.
        coded = {"rice_milled_raw": "A015", "rajma_raw": "B020", "toor_dal_raw": "B021", "potato_raw": "F006"}
        for ingredient_id, ingredient in ingredients.items():
            if ingredient_id in coded:
                assert ingredient.ifct_code == coded[ingredient_id]
            else:
                assert ingredient.ifct_code is None

    def test_unverified_rows_are_reported_not_silently_accepted(self, load_report):
        # 28 of 29 rows are unverified; only `water` (which has no nutrients to
        # get wrong) is marked verified. The three protein rows added 2026-08-02
        # (paneer_fresh, tofu_firm, soya_chunks_dry) are unverified like the
        # rest, and their DIAAS figures -- the field the quality-source rule
        # gates on -- are authored from recollection, which each row's
        # source_note states. The four real-IFCT-code rows above are
        # NOT included: their values were extracted by this build, not opened
        # by a human against the primary source, so they stay verified=false
        # pending that review (see CLAUDE.md, "only a human... may flip that
        # flag").
        assert len(load_report.warnings) == 28

    def test_states_parse(self, ingredients):
        assert ingredients["rice_cooked"].state is RawOrCooked.COOKED
        assert ingredients["rice_milled_raw"].state is RawOrCooked.RAW
        assert ingredients["gingelly_oil"].state is RawOrCooked.AS_USED

    def test_allergens_parse(self, ingredients):
        assert ingredients["gingelly_oil"].allergens == frozenset({"sesame"})
        assert ingredients["rice_cooked"].allergens == frozenset()

    def test_jain_safety_is_stated_not_inferred(self, ingredients):
        assert ingredients["onion_raw"].jain_safe is False
        assert ingredients["potato_boiled"].jain_safe is False
        assert ingredients["tomato_raw"].jain_safe is True

    def test_the_four_ifct_coded_rows_carry_their_real_values(self, ingredients):
        # Extracted 2026-07-24 from IFCT 2017 (via the Sahu & Sahu
        # machine-readable re-publication) -- see data/raw/ifct/README.md.
        # Pinned as literals so a future edit to the fixture must be a
        # deliberate, visible change to this test, not a silent drift.
        rice = ingredients["rice_milled_raw"]
        assert rice.energy_kcal == pytest.approx(356.4)
        assert rice.protein_g == pytest.approx(7.94)

        rajma = ingredients["rajma_raw"]
        assert rajma.ifct_code == "B020"
        assert rajma.fibre_g == pytest.approx(16.57)

        toor = ingredients["toor_dal_raw"]
        assert toor.ifct_code == "B021"
        assert toor.protein_g == pytest.approx(21.7)

        potato = ingredients["potato_raw"]
        assert potato.ifct_code == "F006"
        assert potato.energy_kcal == pytest.approx(69.8)

        # None of the four are Ingredient.verified -- extraction by this
        # project's own tooling is not a human opening the primary source.
        for ing in (rice, rajma, toor, potato):
            assert ing.verified is False

    def test_new_ifct_coded_rows_still_carry_the_unverified_composition_band(
        self, ingredients
    ):
        # Perturbation check the other way round: having a real ifct_code must
        # not, by itself, narrow composition_uncertainty -- only
        # Ingredient.verified does that (see ifct_loader._row_to_ingredient).
        # A code with no human sign-off must cost exactly as much as no code
        # at all.
        for ingredient_id in ("rice_milled_raw", "rajma_raw", "toor_dal_raw", "potato_raw"):
            ing = ingredients[ingredient_id]
            assert ing.composition_uncertainty_for("protein_g") == 0.25


class TestHighQualityProteinRows:
    """D2a, 2026-08-02. The three rows the quality-source rule needs to exist.

    Before them the only ingredient above DIAAS 0.62 was ``curd_dahi``, so a
    quality floor shipped against the library would have declined every plate
    (``docs/design/target_model_v2.md`` §3). These tests pin the two properties
    that make the rows honest rather than convenient: their DIAAS figures are
    present and load, and nothing about adding them upgraded any confidence.
    """

    _NEW = ("paneer_fresh", "tofu_firm", "soya_chunks_dry")

    def test_each_row_carries_a_diaas_value(self, ingredients):
        # A missing DIAAS reads as "does not qualify", so an omission here would
        # make the rows silently useless to the rule they were added for --
        # failing in the safe direction, but failing.
        for ingredient_id in self._NEW:
            assert ingredients[ingredient_id].diaas is not None

    def test_no_confidence_was_bought_by_adding_them(self, ingredients):
        # The rows exist to unblock a rule. That is exactly the pressure under
        # which a `verified` flag gets flipped or a band quietly narrowed, so
        # both are asserted: unverified, and carrying the same wide composition
        # band as every other hand-entered row.
        for ingredient_id in self._NEW:
            ing = ingredients[ingredient_id]
            assert ing.verified is False
            assert ing.composition_uncertainty_for("protein_g") == 0.25

    def test_the_soya_row_is_dry_basis(self, ingredients):
        # Soya chunks roughly triple on rehydration. Reading a dry composition
        # against a rehydrated quantity is the 3x raw-versus-cooked error the
        # recipe schema exists to prevent, and no rehydration yield constant is
        # registered -- soya_chunk_curry.yaml lists the absorbed water instead.
        assert ingredients["soya_chunks_dry"].state is RawOrCooked.RAW


class TestEnergyReconciliation:
    def test_row_whose_energy_disagrees_with_its_macros_is_rejected(self, tmp_path):
        # Stated 300 kcal against 5*4 + 2*9 + 20*4 = 20 + 18 + 80 = 118 kcal.
        # |300 - 118| / 300 = 60.7%, far past the 15% tolerance.
        path = write_csv(
            tmp_path,
            "bad,Bad,,,,raw,300,5,2,20,1,0,0,0,0,,false,true,,false,",
        )
        report = load_ingredient_file(path)
        assert report.loaded == {}
        assert len(report.rejected) == 1
        assert "energy reconciliation failed" in report.rejected[0].reason

    def test_fibre_is_charged_at_its_own_rate_not_the_carbohydrate_rate(
        self, tmp_path
    ):
        # A real case, not a synthetic one: rajma_raw's actual IFCT 2017
        # figures (299.2 kcal, 19.91 g protein, 1.77 g fat, 65.18 g total carb,
        # 16.57 g of it fibre). Charging ALL carbohydrate at 4 kcal/g gives
        # 4*19.91 + 9*1.77 + 4*65.18 = 79.64 + 15.93 + 260.72 = 356.29, which
        # disagrees with 299.2 by 19.1% -- past the 15% gate. Charging fibre
        # separately at 2 kcal/g (its own rate, matching IFCT's own energy
        # methodology) gives 79.64 + 15.93 + 4*48.61 + 2*16.57 = 79.64 + 15.93
        # + 194.44 + 33.14 = 323.15, which disagrees by only 8.0% -- comfortably
        # inside the gate. This is exactly why rajma_raw needed the fix and
        # not a hand-fudged number: the underlying data was right all along.
        path = write_csv(
            tmp_path,
            "rajma_test,Rajma,,,,raw,299.2,19.91,1.77,65.18,16.57,0,0,0,0,,false,true,,false,",
        )
        report = load_ingredient_file(path)
        assert report.rejected == []
        assert "rajma_test" in report.loaded

    def test_fibre_charged_at_the_carbohydrate_rate_would_reject_the_same_row(
        self, tmp_path
    ):
        # The perturbation half of the test above. If fibre were still charged
        # at the general carbohydrate rate (the pre-2026-07-24 behaviour), this
        # same rajma_raw-shaped row would fail the gate at 19.1%. Proves the
        # fix is load-bearing, not decorative: a static assertion that the row
        # loads today cannot catch a regression back to the flat formula.
        from dataclasses import replace

        from core.nutrition import citations

        original = citations._CONSTANTS["atwater.fibre_kcal_per_g"]
        flattened = replace(original, value=citations.value_of("atwater.carb_kcal_per_g"))
        citations._CONSTANTS["atwater.fibre_kcal_per_g"] = flattened
        try:
            path = write_csv(
                tmp_path,
                "rajma_test,Rajma,,,,raw,299.2,19.91,1.77,65.18,16.57,0,0,0,0,,false,true,,false,",
            )
            report = load_ingredient_file(path)
        finally:
            citations._CONSTANTS["atwater.fibre_kcal_per_g"] = original

        assert report.loaded == {}
        assert len(report.rejected) == 1
        assert "energy reconciliation failed" in report.rejected[0].reason

    def test_row_just_inside_tolerance_is_kept(self, tmp_path):
        # 10*4 + 1*9 + 20*4 = 40 + 9 + 80 = 129 kcal recomputed.
        # Stated 145: |145 - 129| / 145 = 11.0%, inside the 15% tolerance.
        path = write_csv(
            tmp_path,
            "ok,Ok,,,,cooked,145,10,1,20,1,0,0,0,0,,false,true,,false,",
        )
        report = load_ingredient_file(path)
        assert "ok" in report.loaded
        assert report.rejected == []

    def test_zero_energy_row_with_real_macros_is_rejected(self, tmp_path):
        # Salt and water legitimately state 0 kcal; a row claiming 0 kcal while
        # carrying 10 g of protein is a transcription slip, and a relative
        # check against zero would divide by zero rather than catch it.
        path = write_csv(
            tmp_path,
            "fake,Fake,,,,as_used,0,10,0,0,0,0,0,0,0,,false,true,,false,",
        )
        report = load_ingredient_file(path)
        assert report.loaded == {}
        assert len(report.rejected) == 1

    def test_genuine_zero_energy_row_is_kept(self, tmp_path):
        path = write_csv(
            tmp_path,
            "salty,Salt,,,,as_used,0,0,0,0,0,38758,0,0,0,,false,true,,false,",
        )
        report = load_ingredient_file(path)
        assert "salty" in report.loaded


class TestRowLevelValidation:
    def test_absent_macro_is_rejected(self, tmp_path):
        path = write_csv(tmp_path, "nomacro,No macro,,,,raw,300,,2,20,1,0,0,0,0,,false,true,,false,")
        report = load_ingredient_file(path)
        assert report.loaded == {}
        assert "protein_g" in report.rejected[0].reason

    def test_fibre_exceeding_carbohydrate_is_rejected(self, tmp_path):
        # carb_g is total carbohydrate and fibre is a subset of it; the reverse
        # means the two columns were filled on different conventions.
        path = write_csv(tmp_path, "f,F,,,,raw,100,1,1,5,9,0,0,0,0,,false,true,,false,")
        report = load_ingredient_file(path)
        assert "exceeds carb_g" in report.rejected[0].reason

    def test_bad_state_is_rejected(self, tmp_path):
        path = write_csv(tmp_path, "s,S,,,,steamed,100,1,1,20,1,0,0,0,0,,false,true,,false,")
        report = load_ingredient_file(path)
        assert "state" in report.rejected[0].reason

    def test_duplicate_id_is_rejected_not_overwritten(self, tmp_path):
        row = "dup,Dup,,,,cooked,130,2.7,0.3,28.2,0.4,1,0.2,3,0,,false,true,,false,"
        path = write_csv(tmp_path, row, row)
        report = load_ingredient_file(path)
        assert len(report.loaded) == 1
        assert "duplicate" in report.rejected[0].reason

    def test_every_rejection_names_its_source_line(self, tmp_path):
        path = write_csv(
            tmp_path,
            "good,Good,,,,cooked,130,2.7,0.3,28.2,0.4,1,0.2,3,0,,false,true,,false,",
            "bad,Bad,,,,raw,300,5,2,20,1,0,0,0,0,,false,true,,false,",
        )
        report = load_ingredient_file(path)
        # Header is line 1, so the bad row is line 3.
        assert report.rejected[0].line_number == 3
        assert report.rejected[0].row_id == "bad"

    def test_strict_mode_raises_on_any_rejection(self, tmp_path):
        write_csv(tmp_path, "bad,Bad,,,,raw,300,5,2,20,1,0,0,0,0,,false,true,,false,")
        with pytest.raises(ValueError, match="rejected rows"):
            load_ingredients(tmp_path, strict=True)

    def test_missing_directory_is_impossible_input(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_ingredients(tmp_path / "nope")
