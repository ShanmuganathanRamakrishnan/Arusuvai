from __future__ import annotations

from pathlib import Path

import pytest

from core.foods.ifct_loader import LoadReport, load_ingredients
from core.foods.recipe_loader import RecipeLibrary, load_recipes

REPO_ROOT = Path(__file__).resolve().parents[1]
INGREDIENT_DIR = REPO_ROOT / "data" / "raw" / "ifct"
RECIPE_DIR = REPO_ROOT / "data" / "recipes"


@pytest.fixture(scope="session")
def load_report() -> LoadReport:
    return load_ingredients(INGREDIENT_DIR)


@pytest.fixture(scope="session")
def ingredients(load_report: LoadReport):
    return load_report.loaded


@pytest.fixture(scope="session")
def library(ingredients) -> RecipeLibrary:
    return load_recipes(RECIPE_DIR, ingredients, strict=True)
