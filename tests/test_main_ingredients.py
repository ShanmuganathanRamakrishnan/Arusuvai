"""Every dish says what it is built around (TASKS_3.md N14).

The planner prefers a plate that does not serve the same main ingredient in
two dishes. That needs a label on every dish, and an unlabelled or misspelt one
must fail to load: otherwise it would read as repeating nothing, the cheapest
path giving the most confident answer.
"""

from pathlib import Path

import pytest

from core.foods.models import MAIN_INGREDIENTS, Recipe
from core.foods.recipe_loader import load_recipe_file
from tests.factories import make_recipe, make_ingredient

_BASE = [
    "id: probe",
    "name: Probe",
    "region: south_indian",
    "category: rice",
    "serving_unit:",
    "  measure: cup",
    "  grams_per_unit: 100.0",
    "  min_count: 1",
    "  default_count: 1",
    "  max_count: 2",
    # A served-basis line: loads clean on every other rule, so a rejection
    # here is about the label and nothing else.
    "ingredients:",
    "  - id: rice_cooked",
    "    quantity_g: 100.0",
    "    state: cooked",
]


def _load(tmp_path, ingredients, *label):
    path = tmp_path / "probe.yaml"
    path.write_text("\n".join(_BASE + list(label)), encoding="utf-8")
    return load_recipe_file(Path(path), ingredients)[0]


def test_a_labelled_dish_loads_with_its_label(tmp_path, ingredients):
    recipe = _load(tmp_path, ingredients, "main_ingredients: [rice, dal]")
    assert recipe.main_ingredients == frozenset({"rice", "dal"})


def test_a_dish_with_no_label_does_not_load(tmp_path, ingredients):
    with pytest.raises(ValueError, match="missing required key 'main_ingredients'"):
        _load(tmp_path, ingredients)


def test_an_empty_label_does_not_load(tmp_path, ingredients):
    with pytest.raises(ValueError, match="names no main ingredient"):
        _load(tmp_path, ingredients, "main_ingredients: []")


def test_a_misspelt_label_does_not_load(tmp_path, ingredients):
    # "soy" for "soya": would never match a soya dish, so two soya dishes
    # on one plate would read as no repeat.
    with pytest.raises(ValueError, match=r"\['soy'\] are not in MAIN_INGREDIENTS"):
        _load(tmp_path, ingredients, "main_ingredients: [soy]")


def test_a_recipe_built_in_code_needs_a_label_too():
    built = make_recipe("x", make_ingredient("x_ing", energy_kcal=100.0, protein_g=1.0, fat_g=1.0, carb_g=20.0))
    fields = {f: getattr(built, f) for f in Recipe.__dataclass_fields__}
    fields["main_ingredients"] = frozenset()
    with pytest.raises(ValueError, match="names no main ingredient"):
        Recipe(**fields)


def test_every_real_dish_uses_only_listed_labels(library):
    labels = {r: c.recipe.main_ingredients for r, c in library.components.items()}
    assert labels and all(labels.values())
    assert set().union(*labels.values()) <= MAIN_INGREDIENTS
