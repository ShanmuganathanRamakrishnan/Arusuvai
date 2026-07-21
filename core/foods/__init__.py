"""Ingredients, recipes, serving units and meal templates.

Public entry point for "what is on this plate": ``core.foods.nutrition_of``.
"""

from __future__ import annotations

from core.foods.models import (
    Component,
    Ingredient,
    MealTemplate,
    NutritionVector,
    Recipe,
    RecipeIngredient,
    ServingUnit,
    TemplateSlot,
)
from core.foods.nutrition_of import (
    NutritionEstimate,
    nutrition_of_components,
    nutrition_of_recipe,
)

__all__ = [
    "Component",
    "Ingredient",
    "MealTemplate",
    "NutritionEstimate",
    "NutritionVector",
    "Recipe",
    "RecipeIngredient",
    "ServingUnit",
    "TemplateSlot",
    "nutrition_of_components",
    "nutrition_of_recipe",
]
