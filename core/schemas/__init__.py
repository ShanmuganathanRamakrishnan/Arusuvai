"""Dataclasses and enums shared across the whole system."""

from __future__ import annotations

from core.schemas.common import (
    DIET_PATTERN_PERMITTED_CLASSES,
    MACRO_KEYS,
    DietPattern,
    IngredientClass,
    MealSlot,
    RawOrCooked,
    Region,
    diet_pattern_permits,
)
from core.schemas.day_ledger import DayLedger
from core.schemas.profile import (
    ActivityLevel,
    ClinicalFlag,
    Goal,
    Profile,
    Sex,
)

__all__ = [
    "DIET_PATTERN_PERMITTED_CLASSES",
    "MACRO_KEYS",
    "ActivityLevel",
    "ClinicalFlag",
    "DayLedger",
    "DietPattern",
    "IngredientClass",
    "Goal",
    "MealSlot",
    "Profile",
    "RawOrCooked",
    "Region",
    "Sex",
    "diet_pattern_permits",
]
