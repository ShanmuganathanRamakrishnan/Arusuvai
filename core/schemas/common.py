"""Shared enumerations. No dependencies on sibling packages (see CLAUDE.md)."""

from __future__ import annotations

from enum import Enum


class RawOrCooked(str, Enum):
    """Whether a nutrient record or a quantity refers to raw or finished mass.

    Recipes store COOKED weights as the primary record (CLAUDE.md, "Raw versus
    cooked weight"). This enum exists so a raw-basis value can never be mistaken
    for a cooked-basis one silently: rice roughly triples on cooking, so the
    confusion is a 3x error, not a tolerance-band problem.
    """

    RAW = "raw"
    COOKED = "cooked"
    #: Applies to both bases because the process does not change the value
    #: meaningfully (oils, salt, spice powders added after cooking).
    AS_USED = "as_used"


class Region(str, Enum):
    SOUTH_INDIAN = "south_indian"
    NORTH_INDIAN = "north_indian"
    #: Recipes usable in either regional plan (rice, curd, plain roti).
    PAN_INDIAN = "pan_indian"


class MealSlot(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACK = "snack"
    DINNER = "dinner"


class DietPattern(str, Enum):
    """Diet patterns a recipe can satisfy.

    Ordered loosely from most to least restrictive; there is deliberately no
    implicit subset logic here — a recipe declares every pattern it satisfies
    explicitly, because the edge cases (jain excludes onion/garlic but so does
    a satvik preference; egg is vegetarian in some Indian usage and not in
    others) are not reliably derivable from a single hierarchy.
    """

    JAIN = "jain"
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    EGGETARIAN = "eggetarian"
    NON_VEGETARIAN = "non_vegetarian"


#: Macro names used as keys in ``Recipe.process_uncertainty`` and in target
#: dictionaries. Keeping these as plain strings (rather than an enum) matches
#: how they appear in recipe YAML; this tuple is the allowed set so a typo in a
#: YAML key fails loudly instead of creating an uncertainty entry nothing reads.
MACRO_KEYS: tuple[str, ...] = (
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carb_g",
    "fibre_g",
    "sodium_mg",
    "iron_mg",
    "calcium_mg",
    "b12_ug",
)
