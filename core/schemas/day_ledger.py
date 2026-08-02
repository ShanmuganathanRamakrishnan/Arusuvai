"""What a day has already spent, for the nutrients budgeted per day.

``core/nutrition/meal_target.py`` splits a day target into one meal's share by
multiplying every bound by the meal's energy fraction. That is the definition
for energy and carbohydrate, and wrong for sodium: ``nutrient.sodium_max_mg`` is
a *daily* guideline, and enforcing 35% of it against a single plate forbids the
ordinary and healthy pattern of a salty lunch offset by a plain dinner. Replacing
that fraction with "what is left of the day" needs somewhere to record what the
day has already used. This is that record.

## Why a mapping and not a NutritionVector

``NutritionVector`` lives in ``core/foods/models.py``, which imports *from* this
package. CLAUDE.md's architecture rule is that ``core/schemas`` has no
dependencies on siblings, and this type has to be readable by both
``core/nutrition`` (which sets the budgets) and ``core/planner`` (which spends
against them), so it belongs here and cannot name that class without creating a
cycle. Contributions are therefore plain ``{macro: value}`` maps keyed by
:data:`~core.schemas.common.MACRO_KEYS`. ``NutritionVector.as_dict()`` is the
bridge, and callers already have it.

## Why per-slot contributions rather than a running total

Re-planning a slot must debit the old plate before crediting the new one. A
scalar total cannot do that — planning lunch twice would count lunch twice — so
the ledger stores what each slot contributed and :meth:`with_meal` replaces by
slot. A consequence worth having: because the ledger records *what* is spent and
not *when*, remaining budget is order-independent, so planning dinner before
lunch needs no special handling at all.

## Points gate. Intervals are display only.

:meth:`spent` sums point estimates, and it is the only accessor any budget
arithmetic may use. :meth:`spent_interval` exists because the remaining-budget
readout has to disclose its uncertainty somewhere, and it must never reach a
floor/ceiling comparison — gating on interval overlap means a plan built on
worse data passes more easily, which is the one failure mode
``core/planner/validator.py`` exists to prevent. Storing both on one object puts
those two a single attribute access apart, so the separation is checked by
perturbation rather than promised: ``tests/test_day_ledger.py`` widens every
interval, leaves the points alone, and asserts the computed meal ceiling does
not move.

This type carries no date and no timezone. ``core/`` never asks what day it is;
the caller owns day identity, which is why nothing here needs a day boundary
defined (``docs/methodology.md``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from core.schemas.common import MACRO_KEYS, MealSlot

__all__ = ["DayLedger"]


def _checked(contribution: Mapping[str, float], where: str) -> Mapping[str, float]:
    """Freeze a contribution map, rejecting any macro name that isn't real.

    A typo'd key would otherwise create an entry ``spent`` never reads, and the
    budget would silently behave as though that nutrient had never been eaten —
    the same class of bug ``MACRO_KEYS`` exists to prevent in recipe YAML.
    """

    unknown = sorted(set(contribution) - set(MACRO_KEYS))
    if unknown:
        raise ValueError(
            f"DayLedger {where}: unknown macro key(s) {unknown}. "
            f"Allowed: {list(MACRO_KEYS)}"
        )
    return MappingProxyType(dict(contribution))


@dataclass(frozen=True)
class DayLedger:
    """Per-slot contributions to one day, as a value. Never mutated in place."""

    #: slot -> {macro: point estimate}. The only thing budget arithmetic reads.
    meals: Mapping[MealSlot, Mapping[str, float]] = field(default_factory=dict)
    #: slot -> ({macro: low}, {macro: high}). Display only; see module docstring.
    intervals: Mapping[
        MealSlot, tuple[Mapping[str, float], Mapping[str, float]]
    ] = field(default_factory=dict)

    def __post_init__(self) -> None:
        meals = {
            slot: _checked(v, f"meals[{slot.value}]") for slot, v in self.meals.items()
        }
        intervals = {
            slot: (
                _checked(lo, f"intervals[{slot.value}].low"),
                _checked(hi, f"intervals[{slot.value}].high"),
            )
            for slot, (lo, hi) in self.intervals.items()
        }
        orphans = sorted(s.value for s in set(intervals) - set(meals))
        if orphans:
            raise ValueError(
                f"DayLedger: interval recorded for slot(s) {orphans} with no point "
                "contribution. An interval without a point estimate cannot be "
                "spent against, and would show a band around a number the budget "
                "never saw."
            )
        object.__setattr__(self, "meals", MappingProxyType(meals))
        object.__setattr__(self, "intervals", MappingProxyType(intervals))

    # ---------------------------------------------------------------- spending

    def spent(self, macro: str) -> float:
        """Total point estimate of ``macro`` across every planned slot.

        The one accessor budget arithmetic may call. Missing macros read as 0.0
        deliberately: a slot that recorded no sodium genuinely contributed none,
        unlike an *uncertainty* left unset, which CLAUDE.md's round-4 addendum
        requires to read as wide rather than confident. These are different
        quantities and the defaults are opposite for good reason.
        """

        return sum(m.get(macro, 0.0) for m in self.meals.values())

    def spent_interval(self, macro: str) -> tuple[float, float]:
        """(low, high) for ``macro``. **Display only — never gate on this.**

        Summed rather than combined in quadrature, and that is the honest
        arithmetic here rather than a shortcut: the same ``salt_iodised`` row and
        the same oil constant appear in every meal of the day, so the errors are
        strongly correlated and do not shrink by sqrt(n). A day total carries
        roughly the same fractional band as one plate.
        """

        low = sum(lo.get(macro, 0.0) for lo, _ in self.intervals.values())
        high = sum(hi.get(macro, 0.0) for _, hi in self.intervals.values())
        return low, high

    def planned_slots(self) -> tuple[MealSlot, ...]:
        """Slots with a contribution, in ``MealSlot`` declaration order."""

        return tuple(slot for slot in MealSlot if slot in self.meals)

    def is_empty(self) -> bool:
        return not self.meals

    # ---------------------------------------------------------------- updating

    def with_meal(
        self,
        meal_slot: MealSlot,
        point: Mapping[str, float],
        *,
        low: Mapping[str, float] | None = None,
        high: Mapping[str, float] | None = None,
    ) -> DayLedger:
        """This ledger with ``meal_slot``'s contribution **replaced**, not added.

        Replace, not accumulate: re-planning a slot the user already planned must
        debit the old plate before crediting the new one, and an ``+=`` here
        would count that slot twice. Returns a new value; the receiver is
        unchanged.
        """

        if (low is None) != (high is None):
            raise ValueError(
                "with_meal: pass both low and high, or neither — half an "
                "interval cannot be displayed and cannot be reasoned about"
            )
        meals = {**self.meals, meal_slot: point}
        intervals = dict(self.intervals)
        if low is not None and high is not None:
            intervals[meal_slot] = (low, high)
        else:
            # A replacement without an interval must not leave the *previous*
            # plate's interval sitting under the new plate's point estimate.
            intervals.pop(meal_slot, None)
        return DayLedger(meals=meals, intervals=intervals)

    def without_meal(self, meal_slot: MealSlot) -> DayLedger:
        """This ledger with ``meal_slot`` removed. Absent slot is not an error."""

        meals = {s: v for s, v in self.meals.items() if s is not meal_slot}
        intervals = {s: v for s, v in self.intervals.items() if s is not meal_slot}
        return DayLedger(meals=meals, intervals=intervals)

    @staticmethod
    def empty() -> DayLedger:
        """A day with nothing planned — the first-meal case, stated explicitly."""

        return DayLedger()
