"""How much of a plate's protein comes from a high-quality source.

One derived quantity, ``quality_protein_g``, and the rule that produces it.
It is deliberately **not** a macro: it is absent from ``MACRO_KEYS``, absent
from :class:`~core.foods.models.NutritionVector`, and carries no composition
or process uncertainty of its own. Nothing measures it in a laboratory; it is
an arithmetic consequence of a threshold this project chose applied to a field
this project authored. Putting it in the macro vector would have made every
loop that iterates ``MACRO_KEYS`` — the Atwater reconciliation, the composition
band, the ingredient CSV schema — quietly claim to know something about it.

## The rule

An ingredient qualifies when its ``diaas`` is present and at or above
``protein.quality_diaas_threshold``. A plate's qualifying protein is the sum of
the protein contributed by qualifying ingredient *lines*, at the plate's actual
integer unit counts.

``diaas is None`` means **does not qualify**, and that is the safe direction
rather than the right one. 17 of the 29 fixture rows carry no DIAAS at all, so
"nobody has assessed this food" and "this food scores badly" are indistinguishable
to this module. It is the same ordering CLAUDE.md's round-4 addendum demands of
uncertainty — the cheapest authoring path must not produce the most permissive
output — but the cost here is concrete: adding a protein-dense row and
forgetting its DIAAS silently makes that food count for nothing.

## Per line, not per component — and why that understates this cuisine

DIAAS is limiting-amino-acid based. A mixture can score *better* than the
protein-weighted mean of its parts, because grain and legume complement each
other: rice is short of lysine and long on methionine, dal the reverse. Summing
per qualifying line gives a roti-and-dal plate credit for **neither** part, so
this rule is systematically harsh on exactly the mixed Indian plates the product
plans. ``docs/design/target_model_v2.md`` §3 flags the aggregation question and
declines to resolve it; this module picks the conservative arm and states which
arm it picked, rather than implementing a protein-weighted mean that would look
more sophisticated while inventing a complementarity model nobody has evidence
for.

A protein-weighted mean would not fix it either. It would still score
roti+dal below both, because the mean of 0.45 and 0.60 is between them, and no
weighted mean of two numbers can exceed the larger. Modelling complementarity
honestly needs per-amino-acid composition data, which this library does not have.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from core.foods.models import Component, Ingredient, Recipe
from core.nutrition import citations

__all__ = [
    "QUALITY_PROTEIN_KEY",
    "ingredient_qualifies",
    "qualifying_ingredient_ids",
    "quality_protein_of_recipe",
    "quality_protein_of_components",
]

#: The name this quantity is reported under in a ``Violation``. A key, not
#: copy — ``tests/test_web_no_identifiers.py`` fails any snake_case string that
#: reaches a visible text node, so the web layer must map it to a label.
QUALITY_PROTEIN_KEY = "quality_protein_g"


def ingredient_qualifies(ingredient: Ingredient) -> bool:
    """Whether this row's protein counts toward a quality floor.

    Reads the threshold from the registry on every call rather than caching it
    at import time. That is deliberate and is what makes the perturbation test
    CLAUDE.md's round-4 addendum demands possible: flipping ``curd_dahi``'s
    DIAAS below the threshold has to change a verdict, which proves the rule
    reads the data instead of a hard-coded list of dairy foods.
    """

    if ingredient.diaas is None:
        return False
    return ingredient.diaas >= citations.value_of("protein.quality_diaas_threshold")


def qualifying_ingredient_ids(
    ingredients: Mapping[str, Ingredient],
) -> frozenset[str]:
    """Every row in ``ingredients`` that clears the threshold. For reporting."""

    return frozenset(i for i, ing in ingredients.items() if ingredient_qualifies(ing))


def quality_protein_of_recipe(
    recipe: Recipe,
    unit_count: int,
    ingredients: Mapping[str, Ingredient],
) -> float:
    """Grams of qualifying protein in ``unit_count`` whole units of ``recipe``.

    Mirrors ``nutrition_of_recipe``'s shape (integer counts only, same
    bounds check) so the two cannot disagree about what a serving is.
    """

    recipe.serving_unit.grams_for(unit_count)  # bounds + integer check
    total = 0.0
    for line in recipe.ingredients:
        ing = ingredients.get(line.ingredient_id)
        if ing is None:
            raise KeyError(
                f"recipe {recipe.id!r} references unknown ingredient "
                f"{line.ingredient_id!r}; check the LoadReport."
            )
        if ingredient_qualifies(ing):
            total += ing.protein_g * (line.quantity_g / 100.0) * unit_count
    return total


def quality_protein_of_components(
    items: Sequence[tuple[Component, int]],
    ingredients: Mapping[str, Ingredient],
) -> float:
    """Qualifying protein for a whole plate: components with their unit counts."""

    return sum(
        quality_protein_of_recipe(component.recipe, count, ingredients)
        for component, count in items
    )
