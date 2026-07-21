"""Household measures: katori, cup, roti, dosa, idli, vada, ladle, spoons.

This module converts between a household measure and grams, and back for
display. It **feeds** ``ServingUnit.grams_per_unit``; it does not replace it. A
recipe still declares its own serving unit, because "one dosa" for a particular
recipe may legitimately weigh more than the generic dosa figure (a masala dosa
carries a potato filling), and the recipe is the authority on its own dish.

The gram weights themselves are nutritional constants — they decide how much a
person actually eats — so they live in ``citations.py`` and are only looked up
here.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.foods.models import ServingUnit
from core.nutrition import citations

__all__ = [
    "HouseholdMeasure",
    "MEASURES",
    "measure",
    "to_grams",
    "describe_grams",
    "serving_unit",
]


@dataclass(frozen=True)
class HouseholdMeasure:
    name: str
    constant_key: str
    #: Plural form, because "2 katoris" and "2 rotis" are fine but "2 cups of
    #: rice" reads differently from "2 cup"; keeping it explicit avoids an
    #: English-pluralisation rule inside display code.
    plural: str

    @property
    def grams(self) -> float:
        return citations.value_of(self.constant_key)

    @property
    def uncertainty(self) -> float:
        return citations.uncertainty_of(self.constant_key)


MEASURES: dict[str, HouseholdMeasure] = {
    m.name: m
    for m in (
        HouseholdMeasure("katori", "measure.katori_gravy_g", "katoris"),
        HouseholdMeasure("cup", "measure.cup_cooked_rice_g", "cups"),
        HouseholdMeasure("idli", "measure.idli_g", "idlis"),
        HouseholdMeasure("dosa", "measure.dosa_g", "dosas"),
        HouseholdMeasure("roti", "measure.roti_g", "rotis"),
        HouseholdMeasure("vada", "measure.vada_g", "vadas"),
        HouseholdMeasure("ladle", "measure.ladle_g", "ladles"),
        HouseholdMeasure("tablespoon", "measure.tablespoon_g", "tablespoons"),
        HouseholdMeasure("teaspoon", "measure.teaspoon_g", "teaspoons"),
    )
}


def measure(name: str) -> HouseholdMeasure:
    try:
        return MEASURES[name]
    except KeyError:
        raise KeyError(
            f"unknown household measure {name!r}; known measures are "
            f"{sorted(MEASURES)}"
        ) from None


def to_grams(measure_name: str, count: int) -> float:
    """Grams for an integer count of a measure.

    Deliberately rejects a float count. Half a dosa is not a household measure,
    and accepting one here is how a fractional portion multiplier gets back into
    a system that ruled them out.
    """

    if not isinstance(count, int) or isinstance(count, bool):
        raise TypeError(
            f"count must be an int, got {type(count).__name__}. Portions are "
            "integer counts of a serving unit, never a fractional multiplier."
        )
    if count < 0:
        raise ValueError("count cannot be negative")
    return measure(measure_name).grams * count


def describe_grams(measure_name: str, grams: float) -> str:
    """Back the other way, for display: 300 g of rice -> 'about 1.5 cups'.

    Display only. Nothing in the planner may round-trip through this to obtain
    a portion — the portion is the integer unit count the solver chose.
    """

    m = measure(measure_name)
    count = grams / m.grams
    if abs(count - round(count)) < 0.05:
        n = int(round(count))
        return f"{n} {m.name if n == 1 else m.plural}"
    return f"about {count:.1f} {m.plural}"


def serving_unit(
    measure_name: str,
    *,
    min_count: int,
    default_count: int,
    max_count: int,
    grams_per_unit: float | None = None,
    name: str | None = None,
) -> ServingUnit:
    """Build a :class:`ServingUnit` from a household measure.

    ``grams_per_unit`` overrides the generic measure weight for dishes where the
    unit genuinely differs (a masala dosa is heavier than a plain one). The
    override is explicit rather than computed so the difference is visible in
    the recipe file.
    """

    m = measure(measure_name)
    return ServingUnit(
        name=name or m.name,
        grams_per_unit=m.grams if grams_per_unit is None else grams_per_unit,
        min_count=min_count,
        default_count=default_count,
        max_count=max_count,
    )
