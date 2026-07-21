"""Public entry point: what does this plate actually contain?

Everything else in ``core/foods`` exists to make this module's answer
defensible. It returns a point estimate *and* an interval, always. Per
CLAUDE.md, the interval is for display and for candidate eligibility — the
validator will gate on the point estimate alone, because a plan built on worse
data must not become easier to pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from core.foods.models import Component, Ingredient, NutritionVector, Recipe
from core.nutrition import citations
from core.schemas import MACRO_KEYS, RawOrCooked

__all__ = [
    "NutritionEstimate",
    "nutrition_of_recipe",
    "nutrition_of_components",
    "format_macro",
]

#: Macros for which showing an interval is worth the ink. Below a few percent
#: the band says nothing a reader can act on, and a "+/-2%" on every line is
#: wallpaper by the second screen.
_INTERVAL_DISPLAY_FLOOR = 0.03


@dataclass(frozen=True)
class NutritionEstimate:
    """A point estimate with the honest band around it."""

    point: NutritionVector
    low: NutritionVector
    high: NutritionVector
    #: Energy attributable to recipes that depend on at least one constant
    #: whose evidence nobody has opened. Feeds the "disclose once" threshold in
    #: CLAUDE.md — reported here, decided elsewhere.
    unverified_energy_kcal: float = 0.0

    def uncertainty_fraction(self, macro: str) -> float:
        p = getattr(self.point, macro)
        if p == 0:
            return 0.0
        return (getattr(self.high, macro) - getattr(self.low, macro)) / (2 * p)

    def unverified_energy_fraction(self) -> float:
        if self.point.energy_kcal == 0:
            return 0.0
        return self.unverified_energy_kcal / self.point.energy_kcal

    def describe(self, macro: str) -> str:
        return format_macro(
            getattr(self.point, macro), self.uncertainty_fraction(macro), macro
        )


_UNITS: dict[str, str] = {
    "energy_kcal": "kcal",
    "protein_g": "g",
    "fat_g": "g",
    "carb_g": "g",
    "fibre_g": "g",
    "sodium_mg": "mg",
    "iron_mg": "mg",
    "calcium_mg": "mg",
    "b12_ug": "ug",
}


def format_macro(value: float, uncertainty: float, macro: str) -> str:
    """'~1,850 kcal (+/-10%)'.

    Showing a false-precise point estimate is the same failure this project
    exists to prevent in the LLM, committed by the data pipeline instead — so
    the rounding here is deliberately coarse and the band is shown whenever it
    is large enough to matter.
    """

    unit = _UNITS.get(macro, "")
    rounded = round(value, -1) if macro == "energy_kcal" and value >= 100 else round(value, 1)
    shown = f"{rounded:,.0f}" if macro == "energy_kcal" else f"{rounded:g}"
    if uncertainty >= _INTERVAL_DISPLAY_FLOOR:
        return f"~{shown} {unit} (+/-{uncertainty:.0%})"
    return f"{shown} {unit}"


def _ingredient(ingredients: Mapping[str, Ingredient], ingredient_id: str) -> Ingredient:
    try:
        return ingredients[ingredient_id]
    except KeyError:
        raise KeyError(
            f"recipe references unknown ingredient {ingredient_id!r}; it was "
            "either rejected at load time or never present. Check the LoadReport."
        ) from None


def _one_unit(recipe: Recipe, ingredients: Mapping[str, Ingredient]) -> NutritionVector:
    total = NutritionVector.zero()
    for line in recipe.ingredients:
        ing = _ingredient(ingredients, line.ingredient_id)
        if ing.state is not line.state and RawOrCooked.AS_USED not in (
            ing.state,
            line.state,
        ):
            # A raw composition record read against a cooked quantity is the 3x
            # error CLAUDE.md calls out. Refuse rather than guess a conversion:
            # the recipe author must either use the matching-state entry or go
            # through core.foods.retention explicitly.
            raise ValueError(
                f"recipe {recipe.id!r}: line {line.ingredient_id!r} is recorded on a "
                f"{line.state.value} basis but ingredient {ing.id!r} has "
                f"{ing.state.value} composition data. Convert via "
                "core.foods.retention, or use the matching-state entry."
            )
        total = total + ing.for_grams(line.quantity_g)
    return total


def nutrition_of_recipe(
    recipe: Recipe,
    unit_count: int,
    ingredients: Mapping[str, Ingredient],
) -> NutritionVector:
    """Point estimate for ``unit_count`` whole serving units of ``recipe``.

    ``unit_count`` is an integer by contract, checked by ``ServingUnit``: this
    is the one place a fractional portion could sneak back in, so it is refused
    loudly here as well.
    """

    recipe.serving_unit.grams_for(unit_count)  # bounds + integer check
    return _one_unit(recipe, ingredients) * unit_count


def _interval_for_recipe(
    recipe: Recipe, point: NutritionVector
) -> tuple[NutritionVector, NutritionVector]:
    lows: list[float] = []
    highs: list[float] = []
    for macro in MACRO_KEYS:
        v = getattr(point, macro)
        u = recipe.uncertainty_for(macro)
        lows.append(v * (1 - u))
        highs.append(v * (1 + u))
    return NutritionVector(*lows), NutritionVector(*highs)


def _depends_on_unverified(recipe: Recipe) -> bool:
    for key in recipe.process_constants:
        ev = citations.evidence(citations.constant(key).evidence_id)
        if not ev.verified:
            return True
    return False


def nutrition_of_components(
    items: Sequence[tuple[Component, int]],
    ingredients: Mapping[str, Ingredient],
) -> NutritionEstimate:
    """Summed estimate for a plate: components paired with integer unit counts.

    Interval arithmetic: the low ends are summed and the high ends are summed,
    i.e. the errors are treated as perfectly correlated. Root-sum-square would
    give a narrower, better-looking band, and would be wrong here — these are
    systematic errors (this cook, this pan, this recipe library's yield
    assumptions), not independent random draws, so they do not cancel. When in
    doubt the band is widened, never narrowed.
    """

    point = NutritionVector.zero()
    low = NutritionVector.zero()
    high = NutritionVector.zero()
    unverified_energy = 0.0

    for component, count in items:
        recipe = component.recipe
        p = nutrition_of_recipe(recipe, count, ingredients)
        lo, hi = _interval_for_recipe(recipe, p)
        point = point + p
        low = low + lo
        high = high + hi
        if _depends_on_unverified(recipe):
            unverified_energy += p.energy_kcal

    return NutritionEstimate(
        point=point, low=low, high=high, unverified_energy_kcal=unverified_energy
    )
