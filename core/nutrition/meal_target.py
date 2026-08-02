"""Split a day-level :class:`NutritionTarget` into a target for one meal.

``core/nutrition/targets.py`` derives a whole-DAY target from a
``Profile``. ``core/planner`` solves one meal template at a time — one call
produces one plate, not a day. Feeding the unscaled day target to a single
meal's combinations would fail every plate on energy alone (no lunch plate is
meant to carry a whole day's ~1800 kcal on its own), which is a modelling
mismatch, not a finding about the recipe library. This module is the one
place that mismatch is resolved, so a caller cannot accidentally compare a
meal's estimate against the wrong scale.

## Two ways a day target becomes a meal target

**Proportional**, for quantities of food: every floor, ceiling and point is
multiplied by the registered fraction (``core.nutrition.citations``,
``meal_split.energy_fraction_*``) keyed by ``MealSlot``. For energy and
carbohydrate this is not a modelling compromise but the definition —
carbohydrate is derived as the energy remainder, so a meal that is 35% of the
day's calories genuinely carries about 35% of its carbohydrate.

**Day budget**, for a nutrient whose target is a *daily* figure: the meal is
checked against what the day has left (:class:`~core.schemas.DayLedger`) rather
than a fixed share. ``nutrient.sodium_max_mg`` is a WHO daily guideline;
enforcing 35% of it against a single plate forbids the ordinary and healthy
pattern of a salty lunch offset by a plain dinner, and apportions a
population-level daily figure by calories, which nothing in the guideline
supports.

``_DAY_BUDGETED`` is the list of macros on the second rule. **It is empty
today**: this module ships the mechanism (slice 1a) before the policy (slice
1b), so that when sodium's verdict moves it is attributable to the policy commit
and not to the plumbing. Everything below therefore behaves exactly as it did
before the ledger existed, which is that slice's acceptance criterion.

The fractions themselves are registered constants rather than literals here:
CLAUDE.md's "no magic numbers" rule applies to a meal split exactly as it does
to a yield factor, and there is no cited basis for anything more specific than
"lunch is the big meal of an Indian day."
"""

from __future__ import annotations

from typing import Mapping

from core.nutrition import citations
from core.nutrition.target import NutritionTarget
from core.schemas import DayLedger, MealSlot

__all__ = ["meal_energy_fraction", "meal_target", "spent_before"]


#: Macros checked against what the day has left rather than a share of it.
#: Empty until slice 1b adds ``sodium_mg``; see this module's docstring for why
#: the mechanism lands before the policy.
_DAY_BUDGETED: frozenset[str] = frozenset()


def meal_energy_fraction(meal_slot: MealSlot) -> float:
    """This meal's registered share of a day's target, e.g. 0.35 for lunch."""

    return citations.value_of(f"meal_split.energy_fraction_{meal_slot.value}")


def spent_before(
    ledger: DayLedger | None, meal_slot: MealSlot, macro: str
) -> float:
    """How much of ``macro`` the day has spent, *excluding* ``meal_slot`` itself.

    Excluding the slot being planned is the whole of the re-planning rule.
    Planning lunch a second time hands us a ledger that already contains the
    first lunch; counting it would charge the day for a plate that is about to be
    thrown away, and the replacement would be held to a budget its predecessor
    had already spent. Debit before credit, expressed as a read rather than a
    mutation so the ledger stays a value.

    ``None`` is the first-meal-of-the-day case and reads as zero spent, which is
    the honest answer and also the one that makes an unguarded budget dangerous
    — see the guard in slice 1b.
    """

    if ledger is None:
        return 0.0
    return ledger.without_meal(meal_slot).spent(macro)


def meal_target(
    day_target: NutritionTarget,
    meal_slot: MealSlot,
    *,
    ledger: DayLedger | None = None,
) -> NutritionTarget:
    """Scale ``day_target`` to one meal; day-budgeted macros use ``ledger``.

    ``ledger`` defaults to ``None`` — a day with nothing planned yet — so every
    caller written before day budgets existed keeps working unchanged.
    """

    fraction = meal_energy_fraction(meal_slot)

    def _scaled(bounds: Mapping[str, float]) -> dict[str, float]:
        return {m: v * fraction for m, v in bounds.items() if m not in _DAY_BUDGETED}

    floors = _scaled(day_target.floors)
    ceilings = _scaled(day_target.ceilings)
    points = _scaled(day_target.points)
    # Carried, not scaled: a hard ceiling is a bound on one plate already, not a
    # share of a day to be divided again.
    hard_ceilings = dict(day_target.hard_ceilings)

    for macro in sorted(_DAY_BUDGETED):  # pragma: no cover - empty until 1b
        day_ceiling = day_target.ceiling(macro)
        if day_ceiling is None:
            continue
        ceilings[macro] = day_ceiling - spent_before(ledger, meal_slot, macro)

    return NutritionTarget(
        floors=floors,
        ceilings=ceilings,
        points=points,
        hard_ceilings=hard_ceilings,
    )
