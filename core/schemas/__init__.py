"""Dataclasses and enums shared across the whole system."""

from __future__ import annotations

from core.schemas.common import (
    MACRO_KEYS,
    DietPattern,
    MealSlot,
    RawOrCooked,
    Region,
)
from core.schemas.profile import (
    ActivityLevel,
    ClinicalFlag,
    Goal,
    Profile,
    Sex,
)

__all__ = [
    "MACRO_KEYS",
    "ActivityLevel",
    "ClinicalFlag",
    "DietPattern",
    "Goal",
    "MealSlot",
    "Profile",
    "RawOrCooked",
    "Region",
    "Sex",
]
