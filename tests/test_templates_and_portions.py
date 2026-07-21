"""Meal grammars differ per (region, meal_slot); household measures are data."""

from __future__ import annotations

import pytest

from core.foods import portions, templates
from core.schemas import MealSlot, Region


class TestTemplatesAreNotUniform:
    def test_the_three_templates_have_genuinely_different_shapes(self):
        shapes = {
            t.id: tuple(s.name for s in t.slots)
            for t in (
                templates.SOUTH_BREAKFAST,
                templates.SOUTH_LUNCH,
                templates.NORTH_DINNER,
            )
        }
        # No two share a slot list, and none is the five-slot
        # base/protein/curry/vegetable/accompaniment grammar.
        assert len(set(shapes.values())) == 3
        assert len(shapes["south_breakfast"]) == 4
        assert len(shapes["south_lunch"]) == 5
        assert len(shapes["north_dinner"]) == 4

    def test_south_breakfast_has_no_separate_vegetable_slot(self):
        # Idli + sambar + chutney. The sambar is the vegetable and the protein;
        # adding a poriyal here produces a plate nobody in Chennai eats.
        names = {s.name for s in templates.SOUTH_BREAKFAST.slots}
        assert "vegetable" not in names
        assert "rice_base" not in names

    def test_north_dinner_has_no_rice_slot(self):
        categories = templates.NORTH_DINNER.categories()
        assert "rice" not in categories
        assert "roti" in categories

    def test_south_lunch_vegetable_slot_is_variable_length(self):
        slot = templates.SOUTH_LUNCH.slot("vegetable")
        assert (slot.min_selections, slot.max_selections) == (1, 2)

    def test_optional_slots_are_marked_optional(self):
        assert templates.SOUTH_LUNCH.slot("crisp").required is False
        assert templates.SOUTH_BREAKFAST.slot("beverage").required is False
        assert templates.SOUTH_LUNCH.slot("rice_base").required is True

    def test_rajma_chawal_belongs_to_a_north_lunch_grammar_not_north_dinner(self):
        # It is a rice-based North Indian meal. Widening NORTH_DINNER's bread
        # slot to fit it would let the enumerator build roti-with-chawal plates.
        assert "combo_rice_legume" in templates.NORTH_LUNCH.categories()
        assert "combo_rice_legume" not in templates.NORTH_DINNER.categories()

    def test_lookup_by_region_and_slot(self):
        t = templates.template_for(Region.SOUTH_INDIAN, MealSlot.BREAKFAST)
        assert t is templates.SOUTH_BREAKFAST

    def test_missing_grammar_raises_rather_than_substituting_another_region(self):
        with pytest.raises(KeyError, match="no meal template"):
            templates.template_for(Region.NORTH_INDIAN, MealSlot.SNACK)

    def test_max_components_counts_variable_length_slots(self):
        # south lunch: rice 1 + gravy 1 + vegetable up to 2 + curd 1 + crisp 1 = 6
        assert templates.SOUTH_LUNCH.max_components() == 6


class TestPortions:
    def test_measures_read_their_grams_from_the_registry(self):
        from core.nutrition import citations

        for m in portions.MEASURES.values():
            assert m.grams == citations.value_of(m.constant_key)

    def test_to_grams_for_an_integer_count(self):
        # 40 g per idli x 3 = 120 g
        assert portions.to_grams("idli", 3) == pytest.approx(120.0)

    def test_fractional_count_is_refused(self):
        with pytest.raises(TypeError, match="integer counts"):
            portions.to_grams("idli", 2.5)

    def test_describe_grams_rounds_to_a_household_phrase(self):
        # 120 g / 40 g per idli = 3 idlis exactly
        assert portions.describe_grams("idli", 120.0) == "3 idlis"
        # 100 g / 40 = 2.5, which is not a household phrase, so it is hedged
        assert portions.describe_grams("idli", 100.0) == "about 2.5 idlis"

    def test_unknown_measure_lists_what_is_available(self):
        with pytest.raises(KeyError, match="known measures"):
            portions.measure("thali")

    def test_serving_unit_can_override_the_generic_measure_weight(self):
        # A masala dosa is heavier than the generic 90 g dosa: it carries a
        # filling. The recipe is the authority on its own dish.
        generic = portions.serving_unit(
            "dosa", min_count=1, default_count=2, max_count=3
        )
        assert generic.grams_per_unit == pytest.approx(90.0)
        masala = portions.serving_unit(
            "dosa", min_count=1, default_count=2, max_count=3, grams_per_unit=150.0
        )
        assert masala.grams_per_unit == pytest.approx(150.0)
