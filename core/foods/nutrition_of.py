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

from core.foods.models import (
    Component,
    Ingredient,
    NutritionVector,
    Recipe,
    RecipeIngredient,
)
from core.nutrition import citations
from core.schemas import MACRO_KEYS, RawOrCooked

__all__ = [
    "NutritionEstimate",
    "nutrition_of_lines",
    "nutrition_of_recipe",
    "nutrition_of_components",
    "format_macro",
    "unit_for",
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
    #: Energy on ingredient lines whose composition record, or whose
    #: quantity-determining process constant, rests on evidence nobody has
    #: opened. Attributed per line, not per recipe — see ``_unverified_energy``
    #: and `docs/audit_log.md` finding 20. Feeds the "disclose once" threshold
    #: in CLAUDE.md — reported here, decided elsewhere.
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
    # Not a macro and not in MACRO_KEYS (core/foods/quality.py explains why),
    # but it is a real quantity in grams that reaches a Violation, and a
    # missing entry here would render it unitless.
    "quality_protein_g": "g",
}


def unit_for(macro: str) -> str:
    """The unit a macro's target was stated in ('g', 'kcal', 'mg').

    Public because CLAUDE.md requires the protein relaxation disclosure to be
    written "in the same units the target was originally stated in", and the
    validator must not keep its own second copy of this mapping — a disclosure
    that says 90 mg of protein because two tables drifted apart is worse than
    no disclosure.
    """

    return _UNITS.get(macro, "")


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


def nutrition_of_lines(
    lines: Sequence[RecipeIngredient],
    ingredients: Mapping[str, Ingredient],
    *,
    recipe_id: str = "<unnamed>",
) -> NutritionVector:
    """Summed nutrition for a bare list of recipe lines.

    Separate from :func:`nutrition_of_recipe` because the recipe loader needs
    this arithmetic *before* a ``Recipe`` exists: it derives each recipe's
    process uncertainty from the actual macro contribution of the lines a
    process constant governs, and a Recipe cannot be constructed until that
    derivation is done.
    """

    total = NutritionVector.zero()
    for line in lines:
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
                f"recipe {recipe_id!r}: line {line.ingredient_id!r} is recorded on a "
                f"{line.state.value} basis but ingredient {ing.id!r} has "
                f"{ing.state.value} composition data. Convert via "
                "core.foods.retention, or use the matching-state entry."
            )
        total = total + ing.for_grams(line.quantity_g)
    return total


def _one_unit(recipe: Recipe, ingredients: Mapping[str, Ingredient]) -> NutritionVector:
    return nutrition_of_lines(recipe.ingredients, ingredients, recipe_id=recipe.id)


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


def _composition_band(
    recipe: Recipe,
    unit_count: int,
    ingredients: Mapping[str, Ingredient],
) -> NutritionVector:
    """Absolute half-width contributed by uncertainty in the composition data.

    Weighted by each ingredient's share of each macro, which is what makes it
    behave correctly on a dish like the masala dosa: 96% of its energy comes
    from rice, urad and potato, so a band derived only from the griddle-oil
    constant described 4% of the dish and called it the whole error.
    """

    band = NutritionVector.zero()
    for line in recipe.ingredients:
        ing = _ingredient(ingredients, line.ingredient_id)
        contribution = ing.for_grams(line.quantity_g) * unit_count
        band = band + NutritionVector(
            *(
                getattr(contribution, macro) * ing.composition_uncertainty_for(macro)
                for macro in MACRO_KEYS
            )
        )
    return band


def _interval_for_recipe(
    recipe: Recipe,
    point: NutritionVector,
    unit_count: int,
    ingredients: Mapping[str, Ingredient],
) -> tuple[NutritionVector, NutritionVector]:
    """Point estimate bracketed by composition *and* process uncertainty.

    The two are summed rather than combined in quadrature, for the same reason
    the plate-level sum is: see ``nutrition_of_components``. Note the summing is
    load-bearing in the conservative direction here — the composition term
    dominates by roughly an order of magnitude on this library.
    """

    composition = _composition_band(recipe, unit_count, ingredients)
    lows: list[float] = []
    highs: list[float] = []
    for macro in MACRO_KEYS:
        v = getattr(point, macro)
        half_width = getattr(composition, macro) + v * recipe.uncertainty_for(macro)
        # Clamped because a nutrient cannot go negative; a band wider than the
        # point estimate is a legitimate statement about very poor data.
        lows.append(max(0.0, v - half_width))
        highs.append(v + half_width)
    return NutritionVector(*lows), NutritionVector(*highs)


def _process_verified(process_key: str) -> bool:
    return citations.evidence(citations.constant(process_key).evidence_id).verified


def _unverified_energy(
    recipe: Recipe,
    unit_count: int,
    ingredients: Mapping[str, Ingredient],
) -> float:
    """Energy in ``unit_count`` units of ``recipe`` that rests on unopened evidence.

    Attributed **per ingredient line**, which is the fix for finding 20. The
    previous rule asked one yes/no question of the whole recipe — is any process
    constant unverified — and was wrong in both directions at once:

    - *Over*, because a True charged the recipe's entire energy. dal_tadka's
      whole 519 kcal was charged for a 5 g tempering-oil line.
    - *Under*, because ``Ingredient.verified`` never entered the calculation, so
      composition data transcribed from memory — most of a dish's energy —
      counted as verified. phulka and onion_raita charged 0.0 while resting
      entirely on hand-entered rows.

    Neither error was correctable alone: fixing the smaller one moves the
    reported figure *away* from the truth, which is why both land here together.

    A line is charged when **either** its composition record is unverified or
    the process constant that determined its quantity is — and charged **once**
    in either case. Union rather than sum, because a line that is unverified for
    two reasons is still only that much energy, and adding the terms could take
    a plate past 100% of its own energy, which is not something a fraction of a
    quantity can do.

    Charging the line's *whole* energy on an unverified process constant is
    deliberate and is not the over-attribution above: ``process_key`` marks a
    line whose **quantity was determined by** that constant (see
    ``RecipeIngredient.process_key``), so if the constant is unopened, so is
    every calorie on that line. The old rule's error was charging the *other*
    lines too.
    """

    total = 0.0
    for line in recipe.ingredients:
        ing = _ingredient(ingredients, line.ingredient_id)
        unverified_composition = not ing.verified
        unverified_process = line.process_key is not None and not _process_verified(
            line.process_key
        )
        if unverified_composition or unverified_process:
            total += ing.for_grams(line.quantity_g).energy_kcal * unit_count
    return total


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

    For the *composition* term the correlation argument is provenance rather
    than mechanism: every value in the current fixture was transcribed from
    memory by one author in one sitting, so the errors plausibly share a common
    bias. That justification expires the moment real IFCT data lands — per-food
    laboratory errors are far closer to independent, and summing them linearly
    would then over-widen every band substantially. Over-wide is not free: the
    candidate eligibility filter excludes on uncertainty, so an inflated band
    silently shrinks the recipe library. Revisit this with the real ingest, and
    prefer making correlation a declared property of the evidence over leaving
    the convention hardcoded in this loop.
    """

    point = NutritionVector.zero()
    low = NutritionVector.zero()
    high = NutritionVector.zero()
    unverified_energy = 0.0

    for component, count in items:
        recipe = component.recipe
        p = nutrition_of_recipe(recipe, count, ingredients)
        lo, hi = _interval_for_recipe(recipe, p, count, ingredients)
        point = point + p
        low = low + lo
        high = high + hi
        unverified_energy += _unverified_energy(recipe, count, ingredients)

    return NutritionEstimate(
        point=point, low=low, high=high, unverified_energy_kcal=unverified_energy
    )
