"""Serving units, nutrition vectors and the invariants baked into them."""

from __future__ import annotations

import pytest

from core.foods.models import (
    Component,
    Ingredient,
    NutritionVector,
    Recipe,
    RecipeIngredient,
    ServingUnit,
    TemplateSlot,
)
from core.schemas import MACRO_KEYS, RawOrCooked, Region


def make_unit(**overrides) -> ServingUnit:
    kwargs = dict(
        name="idli", grams_per_unit=40.0, min_count=1, default_count=2, max_count=6
    )
    kwargs.update(overrides)
    return ServingUnit(**kwargs)


class TestNutritionVector:
    def test_addition_is_componentwise(self):
        a = NutritionVector(energy_kcal=100.0, protein_g=5.0, fat_g=2.0)
        b = NutritionVector(energy_kcal=50.5, protein_g=1.5, fat_g=0.25)
        total = a + b
        # 100 + 50.5 = 150.5 ; 5 + 1.5 = 6.5 ; 2 + 0.25 = 2.25
        assert total.energy_kcal == pytest.approx(150.5)
        assert total.protein_g == pytest.approx(6.5)
        assert total.fat_g == pytest.approx(2.25)

    def test_scalar_multiply(self):
        v = NutritionVector(energy_kcal=130.0, protein_g=2.7, carb_g=28.2)
        # 108 g of a per-100 g record: factor 1.08
        # 130 * 1.08 = 140.4 ; 2.7 * 1.08 = 2.916 ; 28.2 * 1.08 = 30.456
        scaled = v * 1.08
        assert scaled.energy_kcal == pytest.approx(140.4)
        assert scaled.protein_g == pytest.approx(2.916)
        assert scaled.carb_g == pytest.approx(30.456)

    def test_sum_over_iterable_starts_from_zero(self):
        vs = [NutritionVector(energy_kcal=10.0) for _ in range(3)]
        assert sum(vs, NutritionVector.zero()).energy_kcal == pytest.approx(30.0)
        # __radd__ handles the bare sum() case too: 10 + 10 + 10 = 30
        assert sum(vs).energy_kcal == pytest.approx(30.0)


class TestServingUnit:
    def test_counts_enumerates_the_integer_domain(self):
        assert make_unit(min_count=2, default_count=3, max_count=5).counts() == (2, 3, 4, 5)

    def test_grams_for_count(self):
        # 40 g per idli x 3 idlis = 120 g
        assert make_unit().grams_for(3) == pytest.approx(120.0)

    def test_fractional_count_is_refused(self):
        # 1.25 idlis is not servable; a five-point multiplier scale would be the
        # same defect wearing a tidier hat.
        with pytest.raises(TypeError):
            make_unit().grams_for(1.25)

    def test_bool_is_not_an_acceptable_count(self):
        with pytest.raises(TypeError):
            make_unit().grams_for(True)

    def test_count_outside_declared_bounds_is_refused(self):
        with pytest.raises(ValueError):
            make_unit(max_count=4).grams_for(5)

    def test_bounds_must_be_ordered(self):
        with pytest.raises(ValueError):
            make_unit(min_count=3, default_count=2, max_count=6)

    def test_bounds_must_be_integers(self):
        with pytest.raises(TypeError):
            make_unit(max_count=6.0)

    def test_describe_uses_household_phrasing(self):
        assert make_unit().describe(1) == "1 idli"
        assert make_unit().describe(2) == "2 idlis"


def _ing(**kw) -> Ingredient:
    base = dict(
        id="x",
        name_en="X",
        name_ta="",
        name_hi="",
        ifct_code=None,
        energy_kcal=100.0,
        protein_g=5.0,
        fat_g=1.0,
        carb_g=15.0,
        fibre_g=2.0,
        sodium_mg=10.0,
        iron_mg=1.0,
        calcium_mg=20.0,
        b12_ug=0.0,
        state=RawOrCooked.COOKED,
    )
    base.update(kw)
    return Ingredient(**base)


def _full_uncertainty(**overrides) -> dict[str, float]:
    """A complete per-macro map. Recipe rejects a partial one — absent is not
    zero, so there is no shorthand for "the rest are certain"."""

    values = {macro: 0.0 for macro in MACRO_KEYS}
    values.update(overrides)
    return values


def _recipe(**kw) -> Recipe:
    base = dict(
        id="r",
        name="R",
        region=Region.SOUTH_INDIAN,
        ingredients=(
            RecipeIngredient("a", 60.0, RawOrCooked.COOKED),
            RecipeIngredient("b", 40.0, RawOrCooked.COOKED),
        ),
        serving_unit=make_unit(name="katori", grams_per_unit=100.0),
        prep_minutes=10,
        process_uncertainty=_full_uncertainty(),
    )
    base.update(kw)
    return Recipe(**base)


class TestRecipe:
    def test_ingredient_masses_must_sum_to_one_serving_unit(self):
        # 60 + 40 = 100 g, matching the declared serving unit exactly.
        assert _recipe().serving_unit.grams_per_unit == pytest.approx(100.0)

    def test_mass_mismatch_is_rejected(self):
        # 60 + 40 = 100 g against a declared 150 g unit — 33% out, well past
        # the 2% authoring tolerance.
        with pytest.raises(ValueError, match="serving unit"):
            _recipe(serving_unit=make_unit(name="katori", grams_per_unit=150.0))

    def test_unknown_uncertainty_macro_is_rejected(self):
        with pytest.raises(ValueError, match="not a known macro"):
            _recipe(process_uncertainty=_full_uncertainty(enrgy_kcal=0.1))

    def test_uncertainty_must_be_a_fraction(self):
        with pytest.raises(ValueError, match="fraction"):
            _recipe(process_uncertainty=_full_uncertainty(energy_kcal=1.5))

    def test_uncertainty_mapping_cannot_be_mutated_after_construction(self):
        # Uncertainty is a property of the data, never a knob a later module
        # turns to make a plan pass.
        r = _recipe(process_uncertainty=_full_uncertainty(energy_kcal=0.1))
        with pytest.raises(TypeError):
            r.process_uncertainty["energy_kcal"] = 0.0  # type: ignore[index]

    def test_an_omitted_macro_is_rejected_rather_than_reading_as_certain(self):
        # The other half of the composition-side fix. Absent used to mean 0.0,
        # so the cheapest authoring path — leaving a macro out — produced the
        # most confident-looking output. It now fails construction.
        partial = {"energy_kcal": 0.04, "fat_g": 0.14}
        with pytest.raises(ValueError, match="process_uncertainty is missing"):
            _recipe(process_uncertainty=partial)

    def test_uncertainty_for_an_absent_macro_raises_instead_of_returning_zero(self):
        r = _recipe()
        with pytest.raises(KeyError, match="Absent is not zero"):
            r.uncertainty_for("vitamin_d_ug")

    def test_empty_ingredients_rejected(self):
        with pytest.raises(ValueError, match="no ingredients"):
            _recipe(ingredients=())


class TestIngredient:
    def test_for_grams_scales_per_100g_record(self):
        # 45 g of a 121 kcal/100 g record: 121 * 0.45 = 54.45
        ing = _ing(energy_kcal=121.0, protein_g=7.0)
        v = ing.for_grams(45.0)
        assert v.energy_kcal == pytest.approx(54.45)
        # 7.0 * 0.45 = 3.15
        assert v.protein_g == pytest.approx(3.15)

    def test_negative_quantity_is_impossible_input(self):
        with pytest.raises(ValueError):
            _ing().for_grams(-1.0)


class TestTemplateSlot:
    def test_optional_slot_must_allow_zero(self):
        with pytest.raises(ValueError):
            TemplateSlot(
                name="crisp",
                accepted_categories=frozenset({"appalam"}),
                required=False,
                min_selections=1,
            )

    def test_required_slot_must_demand_one(self):
        with pytest.raises(ValueError):
            TemplateSlot(
                name="gravy",
                accepted_categories=frozenset({"sambar"}),
                required=True,
                min_selections=0,
            )

    def test_accepts_checks_component_category(self):
        slot = TemplateSlot(name="gravy", accepted_categories=frozenset({"sambar"}))
        assert slot.accepts(Component(recipe=_recipe(), category="sambar"))
        assert not slot.accepts(Component(recipe=_recipe(), category="chutney"))
