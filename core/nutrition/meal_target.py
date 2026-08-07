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

``_DAY_BUDGETED`` is the list of macros on the second rule. Sodium is on it;
nothing else is yet. Fibre is deliberately not: its target already derives from
energy (``nutrient.fibre_g_per_1000kcal``, 14 g per 1000 kcal), so splitting it
by the energy fraction is self-consistent and destroys no information. Iron,
calcium and B12 are not budgeted because they have no target at all today — they
are new work, not a migration.

**Flat**, for the per-meal quality-protein floor (slice 4): neither scaled by
the energy fraction nor checked against a day ledger. It is a fraction of the
day protein floor applied identically to every slot, because the rule it
implements is "no meal is pure lentil", which is a statement about each plate
rather than a share of anything. See :func:`_quality_protein_floor`.

## The first-meal problem, and the guard

A remaining-budget check alone puts **no limit whatsoever** on the first meal of
a day: with nothing spent, ``remaining`` is the entire day. Measured, the
reference profile's blocking 1649.3 mg lunch passes a bare remaining check
outright. So a plate may never take more than
``day_budget.absurdity_fraction`` of the day's budget however much is left.

That guard is registered as a hard ceiling, not as another ceiling, and the
distinction is the whole of it: rung 1 of the relaxation ladder widens a sodium
ceiling by 0.50, so a *widenable* guard at 0.70 would permit one plate to carry
105% of a whole day's sodium — the exact outcome the guard was introduced to
prevent. The bound the ladder may move is ``remaining``; the guard stays put.
The cost, accepted rather than hidden: this is a never-relaxing per-plate
fraction of a daily figure, which is stricter than the per-meal share it
replaces, since that share did relax. ``citations.py``'s note on the constant
states all of it, including that 0.70 was chosen after its effect was known.

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
#: Sodium only: see this module's docstring for why fibre and the three
#: micronutrients are each excluded for a different reason.
_DAY_BUDGETED: frozenset[str] = frozenset({"sodium_mg"})


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


def _apply_protein_meal_bounds(
    day_target: NutritionTarget,
    floors: dict[str, float],
    ceilings: dict[str, float],
) -> None:
    """Add slice 3's per-meal protein bounds. Mutates ``floors``/``ceilings``.

    Both bounds are fractions of the **day protein floor**, so they move with the
    profile rather than being absolute grams. Protein has no day ceiling — the
    day target states a minimum and nothing above it — so the ceiling here is
    half of a floor, not half of a ceiling.

    **The floor is applied as a maximum, not a replacement**, and this is a
    deliberate departure from `docs/design/target_model_v2.md` §3, whose table
    reads as though 0.15 replaces the energy-fraction share outright. Taken that
    way it would move the reference profile's lunch protein floor from 39.2 g to
    16.8 g — a 22 g loosening nobody asked for, and the same shape of unrequested
    side effect slice 2 had to be caught for. The purpose of the bound is that no
    meal is *empty* of protein, which is a guard beneath the share, not a new
    share. So it binds only where the energy share falls below it, which today is
    the snack slot alone (0.10 < 0.15) — precisely the case it exists for.

    The ceiling is genuinely new: nothing previously stopped the solver answering
    a protein floor by piling three katoris of dal onto one plate.
    """

    day_floor = day_target.floor("protein_g")
    if day_floor is None:
        # No day protein floor to take a fraction of. Not an error: a caller may
        # build a target without one, and inventing a bound here would be a
        # nutritional number written outside citations.py.
        return

    guard_floor = citations.value_of("protein.meal_floor_fraction") * day_floor
    share_floor = floors.get("protein_g")
    floors["protein_g"] = (
        guard_floor if share_floor is None else max(share_floor, guard_floor)
    )
    ceilings["protein_g"] = (
        citations.value_of("protein.meal_ceiling_fraction") * day_floor
    )


def _quality_protein_floor(day_target: NutritionTarget) -> float | None:
    """Slice 4's per-meal floor on protein from qualifying sources.

    A flat fraction of the day protein floor, applied identically to every
    slot — **not** scaled by the meal's energy share and **not** a ``max()``
    guard beneath a share, unlike ``protein.meal_floor_fraction`` above. There
    is nothing to guard beneath: the day quality floor
    (``ProteinTarget.quality_source_day_g``) is never apportioned across slots,
    because the design deliberately wants most of a day's quality protein to be
    free to land in one or two meals. A per-slot share would contradict that
    directly.

    The cost of flat, stated rather than discovered: a snack gets the same
    floor as a lunch on a quarter of the energy. No template exists for the
    snack slot today, so the case is unexercised, not solved.

    Returns ``None`` when the day target states no protein floor, for the same
    reason ``_apply_protein_meal_bounds`` returns early: inventing a bound here
    would be a nutritional number written outside ``citations.py``.
    """

    day_floor = day_target.floor("protein_g")
    if day_floor is None:
        return None
    return citations.value_of("protein.quality_meal_floor_fraction") * day_floor


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

    _apply_protein_meal_bounds(day_target, floors, ceilings)
    # Carried, not scaled: a hard ceiling is a bound on one plate already, not a
    # share of a day to be divided again.
    hard_ceilings = dict(day_target.hard_ceilings)

    bound_sources: dict[str, str] = {}
    guard_fraction = citations.value_of("day_budget.absurdity_fraction")

    for macro in sorted(_DAY_BUDGETED):
        day_ceiling = day_target.ceiling(macro)
        if day_ceiling is None:
            # No day bound to budget against. Not an error: a caller may build a
            # target without one, and inventing a ceiling here would be a
            # nutritional number written outside citations.py.
            continue
        # Floored at zero: a day already over its budget leaves nothing to
        # spend, and a negative ceiling would decline with a bound no reader can
        # interpret. Every plate still fails, which is the correct outcome.
        remaining = max(0.0, day_ceiling - spent_before(ledger, meal_slot, macro))
        guard = guard_fraction * day_ceiling
        ceilings[macro] = min(remaining, guard)
        hard_ceilings[macro] = guard
        # Which term won, recorded rather than left to be inferred downstream by
        # comparing floats. `<=` so a day already spent past the guard reports
        # the day as the reason, which is the true one and the more useful one.
        bound_sources[macro] = (
            "day_remaining" if remaining <= guard else "absurdity_guard"
        )

    return NutritionTarget(
        floors=floors,
        ceilings=ceilings,
        points=points,
        hard_ceilings=hard_ceilings,
        bound_sources=bound_sources,
        quality_protein_floor_g=_quality_protein_floor(day_target),
    )
