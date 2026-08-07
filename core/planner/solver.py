"""Integer unit-count solving over surviving combinations.

## Solver choice, stated rather than assumed

Exhaustive integer search over the Cartesian product of each component's
``ServingUnit.counts()`` domain — not ``scipy.optimize.linprog`` and not
OR-Tools CP-SAT, for two reasons:

1. **The domains are small by construction.** ``counts()`` is
   ``max_count - min_count + 1``; every recipe in ``data/recipes/`` sets
   ``max_count`` at 2 or 3. The largest template today, ``south_lunch``, has
   ``max_components() == 6`` (see ``core/foods/templates.py``), so the worst
   case is a domain product of ``3**6 == 729`` per combination — a plain
   Python loop over 729 tuples costs microseconds and needs no solver
   library. Neither dependency is even installed in this environment.
2. **An LP relaxation needs a rounding/repair step to recover integers.**
   ``linprog`` solves the continuous relaxation; turning its fractional
   answer back into integer serving counts is exactly the "propose a number,
   then have something else check it" shape CLAUDE.md's central invariant
   rules out for portions, just moved from the LLM into the solver. Direct
   integer search has no such step — every candidate it evaluates already is
   a legal integer assignment.

OR-Tools CP-SAT is the right tool once combinations regularly carry
double-digit component counts or domains; nothing in this library does yet.
Revisit if ``max_components()`` grows past roughly 8-10 across the template
set, at which point ``3**10 ~= 59000`` combinations per candidate combination
times a nontrivial combination count starts to matter.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Mapping, Sequence

from core.foods.models import Component, NutritionVector
from core.foods.nutrition_of import NutritionEstimate, nutrition_of_components, nutrition_of_recipe
from core.foods.quality import quality_protein_of_components, quality_protein_of_recipe
from core.planner.candidates import CandidatePool
from core.planner.combinations import MealCombination
from core.nutrition.target import NutritionTarget

__all__ = ["DEVIATION_WEIGHTS", "SolvedPlan", "solve_combination", "solve", "swap_candidates"]

#: Named per BUILD_PROMPTS Phase 2: "Weight protein deviation heaviest, then
#: energy, then fat/carb". Ordering follows CLAUDE.md's relaxation ladder
#: directly — the ladder relaxes sodium/fibre first and protein last, i.e.
#: protein is the most load-bearing macro and fat/carb the least, so the
#: solver should give up fat/carb accuracy before it gives up protein
#: accuracy when a combination can't hit every target exactly.
DEVIATION_WEIGHTS: Mapping[str, float] = {
    "protein_g": 10.0,  # relaxes last on the ladder; heaviest
    "energy_kcal": 5.0,  # tightest default tolerance (+/-5%) of what's left
    "fat_g": 1.0,  # "least load-bearing", absorbs leftover energy
    "carb_g": 1.0,  # same
}


@dataclass(frozen=True)
class SolvedPlan:
    """One combination with a chosen integer unit count per component."""

    combination: MealCombination
    unit_counts: Mapping[str, int]  # keyed by Component.id
    estimate: NutritionEstimate
    score: float
    #: Grams of protein from ingredients clearing the DIAAS threshold
    #: (``core.foods.quality``). Carried on the plan rather than recomputed by
    #: the validator, which has no ingredient table to recompute it from — and
    #: a second derivation could disagree with the one the solver gated on.
    #:
    #: Defaults to 0.0, which is the *conservative* default: a plan that does
    #: not say how much quality protein it has is treated as having none, so it
    #: fails a quality floor rather than sailing past one. That is the right
    #: direction for an unset value, per CLAUDE.md's round-4 addendum.
    quality_protein_g: float = 0.0

    def counts_for(self, component: Component) -> int:
        return self.unit_counts[component.id]


def _within_target_point(
    point: NutritionVector, target: NutritionTarget, quality_protein_g: float = 0.0
) -> bool:
    for macro in target.bounded_macros():
        value = getattr(point, macro)
        floor = target.floor(macro)
        ceiling = target.ceiling(macro)
        if floor is not None and value < floor:
            return False
        if ceiling is not None and value > ceiling:
            return False
    # Checked separately, and deliberately not by adding "quality_protein_g" to
    # `floors`: it is not in MACRO_KEYS and not a NutritionVector field, so the
    # loop above would raise on it. See NutritionTarget.quality_protein_floor_g.
    quality_floor = target.quality_protein_floor()
    if quality_floor is not None and quality_protein_g < quality_floor:
        return False
    return True


def _deviation_point(point: NutritionVector, target: NutritionTarget) -> float:
    """Weighted distance from each macro's *ideal point*, not from its band.

    Deliberately independent of floor/ceiling: ``_within_target_point`` already
    rejects anything outside the band, so every candidate this function scores
    is already valid, and floor/ceiling alone cannot distinguish between two
    valid candidates — both read as "inside the band" regardless of where.
    ``NutritionTarget.point`` is what actually ranks them, by how close each
    macro sits to its declared ideal. A macro with no registered point (only a
    floor/ceiling) contributes nothing to the score, which is correct: there
    is nothing to prefer beyond validity for it.
    """

    score = 0.0
    for macro, weight in DEVIATION_WEIGHTS.items():
        ideal = target.point(macro)
        if ideal is None:
            continue
        actual = getattr(point, macro)
        score += weight * abs(actual - ideal) / max(abs(ideal), 1e-9)
    return score


def _point_vector(
    items: Sequence[tuple[Component, int]], ingredients: Mapping, cache: dict
) -> NutritionVector:
    """Summed point estimate only — no composition/process interval.

    The search loop below evaluates up to a few thousand candidate
    assignments per combination; none of them need the interval
    (``_within_target_point``/``_deviation_point`` only ever read the point).
    ``nutrition_of_components`` computes the interval unconditionally, which
    dominated this module's runtime before this cache existed — a 200-profile
    property-test run took over four minutes. Only the one assignment that
    actually wins a combination gets a real ``NutritionEstimate``, built once,
    below. ``cache`` is keyed by ``(component.id, count)``, which is what a
    recipe's point contribution actually depends on; shared across every
    combination in one ``solve()`` call because the same handful of
    components recur across dozens of combinations and count assignments.
    """

    total = NutritionVector.zero()
    for component, count in items:
        key = (component.id, count)
        vector = cache.get(key)
        if vector is None:
            vector = nutrition_of_recipe(component.recipe, count, ingredients)
            cache[key] = vector
        total = total + vector
    return total


def _quality_protein(
    items: Sequence[tuple[Component, int]], ingredients: Mapping, cache: dict
) -> float:
    """Qualifying-protein total for one candidate assignment.

    Cached on the same ``(component.id, count)`` key as ``_point_vector`` but in
    its own dict, because the two return different types and sharing one would
    mean a tuple key collision waiting to be introduced. Same reason for the
    cache at all: this runs once per candidate integer assignment, up to a few
    thousand per combination.
    """

    total = 0.0
    for component, count in items:
        key = (component.id, count)
        grams = cache.get(key)
        if grams is None:
            grams = quality_protein_of_recipe(component.recipe, count, ingredients)
            cache[key] = grams
        total += grams
    return total


def _new_cache() -> dict:
    """The two per-``(component id, count)`` caches ``solve`` shares.

    Two sub-dicts rather than one keyed by a discriminator: they hold different
    types, and a single flat dict is one careless key away from a collision
    that would silently return a float where a NutritionVector was expected.
    """

    return {"point": {}, "quality": {}}


def solve_combination(
    combination: MealCombination,
    target: NutritionTarget,
    ingredients: Mapping,
    *,
    _cache: dict | None = None,
) -> SolvedPlan | None:
    """Best integer unit-count assignment for one combination.

    ``None`` if no assignment within every component's ``counts()`` domain
    satisfies ``target`` — a real outcome for a combination whose components
    simply cannot reach the target at any legal count, not a search failure.

    ``_cache`` is an internal (component id, count) -> point-vector cache;
    ``solve()`` shares one across a whole batch of combinations. Passed as a
    private, defaulted parameter so this function stays independently usable
    (e.g. directly from a test) without a caller having to know the cache
    exists.
    """

    cache = _new_cache() if _cache is None else _cache
    components = combination.components
    if not components:
        # An all-optional template with every optional slot at 0 selections.
        # Feasible only if the (all-zero) point estimate already meets the
        # target, e.g. a target with no floor on anything. An empty plate
        # carries 0 g of qualifying protein, so any quality floor rejects it.
        point = NutritionVector.zero()
        if not _within_target_point(point, target, 0.0):
            return None
        estimate = nutrition_of_components([], ingredients)
        return SolvedPlan(combination, {}, estimate, 0.0, 0.0)

    domains = [c.recipe.serving_unit.counts() for c in components]
    best_items: list[tuple[Component, int]] | None = None
    best_score = 0.0
    for counts in itertools.product(*domains):
        items = list(zip(components, counts))
        point = _point_vector(items, ingredients, cache["point"])
        quality = _quality_protein(items, ingredients, cache["quality"])
        if not _within_target_point(point, target, quality):
            continue
        score = _deviation_point(point, target)
        if best_items is None or score < best_score:
            best_items = items
            best_score = score
    if best_items is None:
        return None
    # The interval is only ever built for the assignment that actually won —
    # once per combination, not once per (up to a few thousand) domain tuple.
    estimate = nutrition_of_components(best_items, ingredients)
    return SolvedPlan(
        combination=combination,
        unit_counts={c.id: n for c, n in best_items},
        estimate=estimate,
        score=best_score,
        quality_protein_g=quality_protein_of_components(best_items, ingredients),
    )


def solve(
    combinations: Sequence[MealCombination],
    target: NutritionTarget,
    ingredients: Mapping,
) -> tuple[SolvedPlan, ...]:
    """Solve every surviving combination; return the feasible ones, best first.

    An empty result means zero feasible combinations exist for this profile —
    the real hard case per CLAUDE.md's "Relaxation ladder" section. Handling
    that (the ladder itself) is ``core/planner/validator.py``, Phase 3; this
    function's job stops at reporting the honest zero, never forcing a match.
    """

    cache: dict = _new_cache()
    solved = [
        plan
        for plan in (
            solve_combination(c, target, ingredients, _cache=cache) for c in combinations
        )
        if plan is not None
    ]
    solved.sort(key=lambda p: p.score)
    return tuple(solved)


def swap_candidates(
    plan: SolvedPlan,
    slot,
    target: NutritionTarget,
    pool: CandidatePool,
    ingredients: Mapping,
) -> tuple[SolvedPlan, ...]:
    """Alternative whole-day plans that replace only ``slot``'s selection.

    Every other slot's chosen components and unit counts are held fixed; each
    of the pool's other legal selections for ``slot`` (across its own
    min/max_selections range) is tried at every count in its own domain, and
    only assignments that keep the *whole* plan within ``target`` are
    returned — a swap that fixes one macro by breaking another is not an
    alternative, it's a different failure. Sorted best-scoring first.
    """

    combination = plan.combination
    current_ids = frozenset(c.id for c in combination.selection_for(slot))

    fixed_components = tuple(
        c
        for other_slot, selection in zip(combination.template.slots, combination.slot_selections)
        if other_slot is not slot
        for c in selection
    )
    fixed_items = [(c, plan.counts_for(c)) for c in fixed_components]

    alternatives: list[SolvedPlan] = []
    candidates = pool.for_slot(slot)
    cache: dict = _new_cache()
    for size in range(slot.min_selections, slot.max_selections + 1):
        for selection in itertools.combinations(candidates, size):
            if frozenset(c.id for c in selection) == current_ids:
                continue  # not actually a swap

            domains = [c.recipe.serving_unit.counts() for c in selection]
            best_items: list[tuple[Component, int]] | None = None
            best_score = 0.0
            count_space = itertools.product(*domains) if domains else ((),)
            for counts in count_space:
                items = fixed_items + list(zip(selection, counts))
                point = _point_vector(items, ingredients, cache["point"])
                quality = _quality_protein(items, ingredients, cache["quality"])
                if not _within_target_point(point, target, quality):
                    continue
                score = _deviation_point(point, target)
                if best_items is None or score < best_score:
                    best_items = items
                    best_score = score
            if best_items is not None:
                new_slot_selections = tuple(
                    selection if s is slot else sel
                    for s, sel in zip(combination.template.slots, combination.slot_selections)
                )
                new_combination = MealCombination(
                    template=combination.template, slot_selections=new_slot_selections
                )
                estimate = nutrition_of_components(best_items, ingredients)
                alternatives.append(
                    SolvedPlan(
                        combination=new_combination,
                        unit_counts={c.id: n for c, n in best_items},
                        estimate=estimate,
                        score=best_score,
                        quality_protein_g=quality_protein_of_components(
                            best_items, ingredients
                        ),
                    )
                )

    alternatives.sort(key=lambda p: p.score)
    return tuple(alternatives)
