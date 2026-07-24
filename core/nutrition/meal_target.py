"""Split a day-level :class:`NutritionTarget` into a target for one meal.

``core/nutrition/targets.py`` derives a whole-DAY target from a
``Profile``. ``core/planner`` solves one meal template at a time — one call
produces one plate, not a day. Feeding the unscaled day target to a single
meal's combinations would fail every plate on energy alone (no lunch plate is
meant to carry a whole day's ~1800 kcal on its own), which is a modelling
mismatch, not a finding about the recipe library. This module is the one
place that mismatch is resolved, so a caller cannot accidentally compare a
meal's estimate against the wrong scale.

The split is proportional: every floor, ceiling and point in the day target
is multiplied by the same registered fraction
(``core.nutrition.citations``, ``meal_split.energy_fraction_*``), keyed by
``MealSlot``. Proportional, not "energy scales but protein doesn't" or some
other asymmetric rule, because there is no cited basis for anything more
specific than "lunch is the big meal of an Indian day" — CLAUDE.md's
"no magic numbers" rule applies here exactly as it does to a yield factor or
an RDA figure, so the fractions themselves are registered constants, not
literals in this file.
"""

from __future__ import annotations

from core.nutrition import citations
from core.nutrition.target import NutritionTarget
from core.schemas import MealSlot

__all__ = ["meal_energy_fraction", "meal_target"]


def meal_energy_fraction(meal_slot: MealSlot) -> float:
    """This meal's registered share of a day's target, e.g. 0.35 for lunch."""

    return citations.value_of(f"meal_split.energy_fraction_{meal_slot.value}")


def meal_target(day_target: NutritionTarget, meal_slot: MealSlot) -> NutritionTarget:
    """Scale every bound in ``day_target`` by ``meal_slot``'s energy fraction."""

    fraction = meal_energy_fraction(meal_slot)
    return NutritionTarget(
        floors={m: v * fraction for m, v in day_target.floors.items()},
        ceilings={m: v * fraction for m, v in day_target.ceilings.items()},
        points={m: v * fraction for m, v in day_target.points.items()},
    )
