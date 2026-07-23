"""Enumerate distinct Component combinations for a template, and the cheap
O(1) feasibility pre-filter that runs before anything reaches the solver.

## Enumeration

A template's slots are not uniform (CLAUDE.md, "Meal templates"): each slot
has its own ``min_selections``/``max_selections`` and its own accepted
categories, drawn from ``CandidatePool.for_slot``. This module iterates the
template's actual slot list — it never assumes a fixed slot count, and a
variable-length slot (south lunch's ``vegetable``, 1 or 2 poriyals) is handled
by enumerating every selection size in its range, not just one.

## The bound, demonstrated rather than asserted

For one slot with ``k`` surviving candidates and selection range
``[min_selections, max_selections]``, the number of legal selections is
``sum(C(k, s) for s in range(min_selections, max_selections + 1))``. The
*naive* bound this module logs alongside the real count is ``2**k`` per slot
— the size of the full power set of that slot's candidates, i.e. every subset
from 0 to k, which is a strict superset of any ``[min, max]`` sub-range and
therefore always >= the true count. It is "naive" precisely because it throws
away the slot's min/max structure; using it (rather than a tighter but
harder-to-state bound) is what makes the comparison a genuine demonstration
instead of restating the real formula under a different name.

## Week-level: no 21-slot cross product

For a week, BUILD_PROMPTS is explicit: do not cross-product all
``days * meals_per_day`` slots against each other (7 days * 3 meals = 21
cells; even a modest 10-combination-per-cell pool would make a naive cross
product 10**21). ``combinations_excluding_recent`` instead enumerates one
(day, meal_slot) cell's combinations against its own template — the same
``enumerate_combinations`` used for a single meal — and filters out any combo
that repeats a recipe from a caller-supplied trailing window. Assembling an
actual week (which day gets which surviving combo, and tracking the rolling
window across 21 calls) is a later phase's orchestration; this module stays a
pure, per-cell function so that assembly can be built on top of it without
combinations.py needing to know what a "week" is.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass
from typing import Mapping, Sequence

from core.foods.models import Component, Ingredient, MealTemplate, TemplateSlot
from core.foods.nutrition_of import nutrition_of_recipe
from core.planner.candidates import CandidatePool
from core.nutrition.target import NutritionTarget

logger = logging.getLogger(__name__)

__all__ = [
    "MealCombination",
    "enumerate_combinations",
    "combinations_excluding_recent",
    "feasible_combinations",
    "macro_bounds",
]


@dataclass(frozen=True)
class MealCombination:
    """One legal assignment of components to every slot of a template.

    ``slot_selections`` is aligned with ``template.slots`` — index i is what
    was chosen for ``template.slots[i]`` — so a later module (the solver's
    ``swap_candidates``) can identify which components belong to a given slot
    without falling back to matching on category, which would silently break
    if two slots ever accepted an overlapping category set.
    """

    template: MealTemplate
    slot_selections: tuple[tuple[Component, ...], ...]

    @property
    def components(self) -> tuple[Component, ...]:
        return tuple(c for selection in self.slot_selections for c in selection)

    def recipe_ids(self) -> frozenset[str]:
        return frozenset(c.recipe.id for c in self.components)

    def selection_for(self, slot: TemplateSlot) -> tuple[Component, ...]:
        index = self.template.slots.index(slot)
        return self.slot_selections[index]


def _slot_selections(slot: TemplateSlot, pool: CandidatePool) -> tuple[tuple[Component, ...], ...]:
    candidates = pool.for_slot(slot)
    options: list[tuple[Component, ...]] = []
    for size in range(slot.min_selections, slot.max_selections + 1):
        options.extend(itertools.combinations(candidates, size))
    return tuple(options)


def enumerate_combinations(pool: CandidatePool) -> tuple[MealCombination, ...]:
    """Every legal per-slot assignment for ``pool.template``.

    A required slot (``min_selections >= 1``) with zero surviving candidates
    makes the whole template unfillable — not an error, since "the candidate
    pool is empty for this profile" is a legitimate outcome the solver must
    report as zero feasible plans, not force. An optional slot always has at
    least the empty selection (``range(0, max+1)`` includes 0), so it never
    blocks enumeration on its own.
    """

    template = pool.template
    per_slot = [_slot_selections(slot, pool) for slot in template.slots]

    naive_bound = 1
    for slot in template.slots:
        naive_bound *= 2 ** len(pool.for_slot(slot))

    blocking = [
        slot.name
        for slot, options in zip(template.slots, per_slot)
        if not options
    ]
    if blocking:
        logger.info(
            "template %s: 0 combinations — slot(s) %s have no legal selection "
            "(naive worst-case bound was %d)",
            template.id,
            blocking,
            naive_bound,
        )
        return ()

    results = tuple(
        MealCombination(
            template=template,
            slot_selections=tuple(selection for selection in combo),
        )
        for combo in itertools.product(*per_slot)
    )
    logger.info(
        "template %s: %d combinations (naive worst-case bound %d, i.e. %.1fx smaller)",
        template.id,
        len(results),
        naive_bound,
        naive_bound / max(len(results), 1),
    )
    return results


def combinations_excluding_recent(
    pool: CandidatePool,
    *,
    recent_recipe_ids: frozenset[str] = frozenset(),
) -> tuple[MealCombination, ...]:
    """One (day, meal_slot) cell's combinations, minus variety violations.

    ``recent_recipe_ids`` is whatever a caller-tracked rolling window of the
    last N days' chosen recipe ids currently holds; this function does not
    maintain that window itself, so calling it once per cell of a week stays
    O(days * meals) work against a per-cell combination count, never a single
    cross product across all cells.
    """

    return tuple(
        combo
        for combo in enumerate_combinations(pool)
        if not (combo.recipe_ids() & recent_recipe_ids)
    )


def macro_bounds(
    component: Component, macro: str, ingredients: Mapping[str, Ingredient]
) -> tuple[float, float]:
    """This component's least and greatest possible contribution to ``macro``.

    Public because ``core/planner/validator.py`` needs the same arithmetic to
    say *why* it is declining ("the library tops out at 33.6g of protein"). A
    decline message computed a second, slightly different way could contradict
    the pre-filter that produced the empty set it is explaining.
    """

    unit = component.recipe.serving_unit
    low = getattr(nutrition_of_recipe(component.recipe, unit.min_count, ingredients), macro)
    high = getattr(nutrition_of_recipe(component.recipe, unit.max_count, ingredients), macro)
    return low, high


def feasible_combinations(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping[str, Ingredient],
) -> tuple[MealCombination, ...]:
    """Discard combinations whose declared min/max range cannot possibly work.

    O(1) per combination (bounded by component count, not by the solver's
    integer search): sum each component's macro contribution at its serving
    unit's min and max count, and discard a combination whose max sum still
    can't reach a macro's floor, or whose min sum already exceeds a macro's
    ceiling. This is a necessary-but-not-sufficient check — it can pass
    combinations the solver later finds infeasible at every specific count,
    but it never discards one the solver could have solved, and it is cheap
    enough to run on the full enumerated set before the solver's integer
    search touches anything.
    """

    survivors = []
    for combo in combinations:
        ok = True
        for macro in target.bounded_macros():
            total_low = 0.0
            total_high = 0.0
            for component in combo.components:
                low, high = macro_bounds(component, macro, ingredients)
                total_low += low
                total_high += high
            floor = target.floor(macro)
            ceiling = target.ceiling(macro)
            if floor is not None and total_high < floor:
                ok = False
                break
            if ceiling is not None and total_low > ceiling:
                ok = False
                break
        if ok:
            survivors.append(combo)

    logger.info(
        "feasibility pre-filter: %d/%d combinations survive",
        len(survivors),
        len(combinations),
    )
    return tuple(survivors)
