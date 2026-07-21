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
        assert len(load_report.loaded) == 23

    def test_no_ifct_code_is_invented(self, ingredients):
        # The fixture set is hand-entered. An invented-but-plausible food code
        # is worse than an absent one: it passes every check while being wrong.
        assert all(i.ifct_code is None for i in ingredients.values())

    def test_unverified_rows_are_reported_not_silently_accepted(self, load_report):
        # 22 of 23 rows are unverified; only `water` (which has no nutrients to
        # get wrong) is marked verified.
        assert len(load_report.warnings) == 22

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
