"""Shared enumerations. No dependencies on sibling packages (see CLAUDE.md)."""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Mapping


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


class IngredientClass(str, Enum):
    """Ingredient-class vocabulary a diet pattern's permission table is checked
    against (TASKS_3.md R1a).

    Validated at construction on :class:`~core.foods.models.Ingredient` and
    never rendered raw to a reader — same discipline as
    ``core.nutrition.target.BOUND_SOURCES`` and
    ``core.planner.validator.VIOLATION_REACH``.

    Five classes, not an open vocabulary: these are exactly the axes the
    permitted-class table below distinguishes. An ingredient carrying none of
    them (rice, dal, tomato, oil, spice) is irrelevant to every pattern's
    restrictions, which is why absence — not a sixth "neutral" class — is the
    normal case.

    This replaced ``Ingredient.is_animal_product`` and ``Ingredient.jain_safe``
    (D-something 2026-08-14, R1a): two hand-set booleans read by nothing but a
    recipe-level ``diet_patterns`` whitelist that was itself hand-listed per
    file and never declared ``eggetarian`` or ``non_vegetarian`` on any recipe,
    so both patterns returned zero candidates in every slot even though every
    dish in the library is edible under both.
    """

    DAIRY = "dairy"
    EGG = "egg"
    FISH = "fish"
    POULTRY = "poultry"
    ROOT_VEGETABLE = "root_vegetable"


class DietPattern(str, Enum):
    """Diet patterns a recipe can satisfy.

    Ordered loosely from most to least restrictive. Unlike before 2026-08-14,
    a recipe no longer declares its patterns by hand: eligibility is derived
    from the union of its ingredients' :class:`IngredientClass` membership,
    checked against :data:`DIET_PATTERN_PERMITTED_CLASSES` by
    :func:`diet_pattern_permits`. The edge cases that used to justify
    hand-listing (jain excludes onion/garlic but so does a satvik preference;
    egg is vegetarian in some Indian usage and not in others) are handled by
    the permitted-class table instead, which is the one place that
    distinction is made — not by a linear "more restrictive than" ordering,
    which cannot express pescatarian (fish yes, poultry no).
    """

    JAIN = "jain"
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    EGGETARIAN = "eggetarian"
    PESCATARIAN = "pescatarian"
    NON_VEGETARIAN = "non_vegetarian"


#: Per pattern, the ingredient classes a recipe is permitted to contain. A
#: class *absent* from a recipe never counts against it under any pattern —
#: this table says what a recipe may carry, not what it must. Mechanism only:
#: PESCATARIAN is registered here (R1a) but not yet offered in the onboarding
#: diet picker (a product decision left to a later task).
#:
#: Deliberately a table, not a linear nesting ladder — see the DietPattern
#: docstring. Reviewed against every recipe in ``data/recipes/`` when this
#: table replaced the hand-listed ``diet_patterns`` field: the derived
#: permission agrees with every prior hand-listed vegetarian/vegan/jain
#: judgement, recipe by recipe (TASKS_3.md R1a verification).
DIET_PATTERN_PERMITTED_CLASSES: Mapping[DietPattern, frozenset[IngredientClass]] = (
    MappingProxyType(
        {
            DietPattern.JAIN: frozenset({IngredientClass.DAIRY}),
            DietPattern.VEGAN: frozenset({IngredientClass.ROOT_VEGETABLE}),
            DietPattern.VEGETARIAN: frozenset(
                {IngredientClass.DAIRY, IngredientClass.ROOT_VEGETABLE}
            ),
            DietPattern.EGGETARIAN: frozenset(
                {
                    IngredientClass.DAIRY,
                    IngredientClass.EGG,
                    IngredientClass.ROOT_VEGETABLE,
                }
            ),
            DietPattern.PESCATARIAN: frozenset(
                {
                    IngredientClass.DAIRY,
                    IngredientClass.EGG,
                    IngredientClass.FISH,
                    IngredientClass.ROOT_VEGETABLE,
                }
            ),
            DietPattern.NON_VEGETARIAN: frozenset(IngredientClass),
        }
    )
)


def diet_pattern_permits(
    pattern: DietPattern,
    classes: frozenset[IngredientClass],
    *,
    dairy_sourcing_verified: bool = True,
) -> bool:
    """Whether every class in ``classes`` is permitted under ``pattern``.

    ``classes`` is normally a recipe's derived class union
    (``core.planner.candidates.recipe_classes``), and this is the sole place
    that union is compared against a pattern — nothing else in the system
    reads ``DIET_PATTERN_PERMITTED_CLASSES`` directly.

    ``dairy_sourcing_verified`` narrows JAIN specifically: the table says
    DAIRY is a class jain permits, but that is a statement about the class,
    not about any particular ingredient's sourcing, which a jain diet also
    restricts (no dairy from an animal treated in ways jain practice
    forbids). Ingredient.dairy_sourcing_verified is False on every row in the
    current library — nobody has traced any dairy row's sourcing — so the
    caller (``core.planner.candidates._passes_hard_filters``) passes the
    recipe's actual, derived value here rather than this function defaulting
    it away. The default of True is for callers with no ingredient context at
    all (e.g. exercising the class-only table in isolation); every caller
    that has ingredients must pass the real figure. Every other pattern
    ignores this parameter — dairy is either fully permitted (eggetarian and
    looser) or fully excluded (vegan) for them, with no sourcing question in
    between. TASKS_3.md R1a, found not fixed 2026-08-14 — see
    docs/methodology.md, "Dairy sourcing for jain eligibility".
    """

    if not classes <= DIET_PATTERN_PERMITTED_CLASSES[pattern]:
        return False
    if (
        pattern is DietPattern.JAIN
        and IngredientClass.DAIRY in classes
        and not dairy_sourcing_verified
    ):
        return False
    return True


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
