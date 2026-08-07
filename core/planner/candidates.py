"""Deterministic pre-filter, plus the uncertainty eligibility filter.

Two independent gates, run in this order, and never merged (CLAUDE.md,
"Uncertainty" — tolerance and uncertainty are different axes):

1. **Hard filters.** Diet pattern, allergens, region/template compatibility.
   Nothing here is graded — a recipe either satisfies a dietary requirement or
   it does not.
2. **Uncertainty eligibility.** A recipe whose combined uncertainty on a
   target-critical macro exceeds a registered ceiling is excluded from pools
   where that macro matters (or, in ``dev_mode``, kept and flagged — see
   below). This never widens a tolerance; it only removes or flags a recipe.

Target-critical macros are exactly the two with a registered eligibility
ceiling: ``eligibility.max_protein_uncertainty`` and
``eligibility.max_energy_uncertainty`` (``core/nutrition/citations.py``).

## Why this gates on the *combined* band, not ``Recipe.process_uncertainty``

``docs/audit_log.md`` finding 1 (2026-07-21, OPEN until this module existed):
CLAUDE.md's prose says the filter excludes a recipe "whose process uncertainty
... exceeds a stated ceiling", but ``Recipe.process_uncertainty`` alone is
0.0 for protein on every recipe in the library today — oil carries no
protein, so no *process* term ever touches that macro. An implementation that
gated on that field literally would let every recipe through regardless of
how unreliable its composition data is, and would do so while following the
doc's wording exactly. The quantity CLAUDE.md is actually describing is
``core.foods.nutrition_of.NutritionEstimate.uncertainty_fraction``: composition
uncertainty (weighted by each ingredient's share of the macro) plus process
uncertainty, summed. This module gates on that combined figure, computed via
``nutrition_of_components`` for a single component at unit count 1 — the
fraction is scale-invariant (both the point estimate and the half-width scale
linearly with unit count), so the count chosen for the check does not matter.

## ``dev_mode``

Per ``docs/methodology.md`` ("dev_mode versus validated"): every ingredient
row in ``data/raw/ifct/`` bar ``water`` is ``verified=False``, so every
recipe in ``data/recipes/`` today carries a 0.25 combined protein band against
a 0.15 ceiling — none of the three clears it (see
``tests/test_nutrition_of.py::TestEligibilityConsequence``, pinned to that
exact figure). Calling this module with ``dev_mode=False`` (the default) is
therefore correct and returns an empty pool for any protein-critical target
against today's data. That is not a bug this module works around.
``dev_mode=True`` suspends exclusion so combinatorics, the solver and tests
can run against admittedly-unverified data — flagged recipes are recorded in
``CandidatePool.flagged`` rather than silently passed off as validated, and
every caller carrying a plan forward must plumb ``dev_mode`` into the plan's
own disclosure rather than defaulting it away.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping

from core.foods.models import Component, Ingredient, MealTemplate
from core.foods.nutrition_of import nutrition_of_components
from core.nutrition import citations
from core.schemas import DietPattern, Region

logger = logging.getLogger(__name__)

__all__ = [
    "TARGET_CRITICAL_MACROS",
    "EligibilityFlag",
    "CandidatePool",
    "recipe_allergens",
    "build_candidate_pool",
]

#: macro -> the citations.py key of the ceiling that governs it. The set of
#: keys IS the definition of "target-critical" in this module: there is no
#: separate list to keep in sync with the registry.
TARGET_CRITICAL_MACROS: Mapping[str, str] = MappingProxyType(
    {
        "protein_g": "eligibility.max_protein_uncertainty",
        "energy_kcal": "eligibility.max_energy_uncertainty",
    }
)


@dataclass(frozen=True)
class EligibilityFlag:
    """One macro on which a recipe's combined uncertainty exceeds its ceiling."""

    recipe_id: str
    macro: str
    fraction: float
    ceiling: float


@dataclass(frozen=True)
class CandidatePool:
    """Survivors of both filters, grouped by category for slot lookup."""

    template: MealTemplate
    by_category: Mapping[str, tuple[Component, ...]]
    #: Recipes removed because dev_mode was False and they missed a ceiling.
    excluded: tuple[EligibilityFlag, ...]
    #: Recipes kept (dev_mode True) despite missing a ceiling.
    flagged: tuple[EligibilityFlag, ...]
    dev_mode: bool

    def for_slot(self, slot) -> tuple[Component, ...]:
        """Every candidate this slot accepts, **ordered by component id**.

        The sort is not cosmetic and must not be removed as tidying-up.
        ``TemplateSlot.accepted_categories`` is a ``frozenset``, and Python
        randomises string hashes per process, so iterating it directly made
        candidate order -- and therefore the order ``enumerate_combinations``
        returns combinations in, and therefore every transcript ``demo.py``
        produces -- depend on ``PYTHONHASHSEED``. Two runs of identical code on
        one machine gave different output (``docs/audit_log.md``, finding 18).

        Sorting by ``component.id`` rather than by category name: the id is the
        identity of the thing actually offered, so the order survives a category
        being renamed or a slot accepting more of them, and it is a total order
        because this method already deduplicates on that same key. Ordering by
        category would make the output depend on how the categories happen to be
        spelled, which is incidental to every caller.

        Order matters beyond reproducibility: ``core/planner/solver.py`` sorts
        plans by score with Python's stable sort, so among equally-scoring plans
        the one enumerated first wins. That path is latent today -- no tie was
        observed across 12 hash seeds on either the real or the synthetic
        library -- but with a larger library it is which plate a user is served.
        """

        seen: set[str] = set()
        out: list[Component] = []
        for category in sorted(slot.accepted_categories):
            for component in self.by_category.get(category, ()):
                if component.id not in seen:
                    seen.add(component.id)
                    out.append(component)
        out.sort(key=lambda component: component.id)
        return tuple(out)


def recipe_allergens(recipe, ingredients: Mapping[str, Ingredient]) -> frozenset[str]:
    """Union of every ingredient line's declared allergens.

    A recipe carries no allergen field of its own — allergens are a property
    of what's in the dish, derived from the ingredients, never hand-duplicated
    onto the recipe where it could disagree with what's actually in it.
    """

    out: set[str] = set()
    for line in recipe.ingredients:
        out |= ingredients[line.ingredient_id].allergens
    return frozenset(out)


def _passes_hard_filters(
    component: Component,
    ingredients: Mapping[str, Ingredient],
    *,
    diet_pattern: DietPattern,
    allergens: frozenset[str],
    template: MealTemplate,
) -> bool:
    recipe = component.recipe
    if diet_pattern not in recipe.diet_patterns:
        return False
    if recipe_allergens(recipe, ingredients) & allergens:
        return False
    if recipe.region not in (template.region, Region.PAN_INDIAN):
        return False
    if component.category not in template.categories():
        return False
    return True


def _eligibility_flags(
    component: Component, ingredients: Mapping[str, Ingredient]
) -> tuple[EligibilityFlag, ...]:
    # The count is arbitrary; uncertainty_fraction is scale-invariant (see the
    # module docstring), so any count in the unit's domain gives the same
    # fraction. It must be IN the domain, though: this line read a hard-coded 1
    # until 2026-08-07, and `nutrition_of_recipe` enforces the serving unit's
    # bounds, so the first recipe in the library with `min_count > 1` (idli,
    # min 2 — nobody is served one idli) made `build_candidate_pool` raise
    # before it could filter anything. The old comment already said "any count
    # in the unit's domain" and the code then used a count that need not be in
    # it. min_count is always in the domain by construction.
    estimate = nutrition_of_components(
        [(component, component.recipe.serving_unit.min_count)], ingredients
    )
    flags = []
    for macro, ceiling_key in TARGET_CRITICAL_MACROS.items():
        ceiling = citations.value_of(ceiling_key)
        fraction = estimate.uncertainty_fraction(macro)
        if fraction > ceiling:
            flags.append(
                EligibilityFlag(
                    recipe_id=component.recipe.id,
                    macro=macro,
                    fraction=fraction,
                    ceiling=ceiling,
                )
            )
    return tuple(flags)


def build_candidate_pool(
    components: Iterable[Component],
    ingredients: Mapping[str, Ingredient],
    *,
    template: MealTemplate,
    diet_pattern: DietPattern,
    allergens: frozenset[str] = frozenset(),
    dev_mode: bool = False,
) -> CandidatePool:
    """Filter ``components`` down to what a solver may build a plan from.

    Eligibility is evaluated once per distinct recipe (not once per component)
    since it does not depend on the slot category a recipe happens to be
    playing.
    """

    by_category: dict[str, list[Component]] = {}
    excluded: list[EligibilityFlag] = []
    flagged: list[EligibilityFlag] = []
    flags_by_recipe: dict[str, tuple[EligibilityFlag, ...]] = {}

    for component in components:
        if not _passes_hard_filters(
            component,
            ingredients,
            diet_pattern=diet_pattern,
            allergens=allergens,
            template=template,
        ):
            continue

        recipe_id = component.recipe.id
        if recipe_id not in flags_by_recipe:
            flags_by_recipe[recipe_id] = _eligibility_flags(component, ingredients)
        flags = flags_by_recipe[recipe_id]

        if flags:
            if dev_mode:
                flagged.extend(flags)
            else:
                excluded.extend(flags)
                continue

        by_category.setdefault(component.category, []).append(component)

    if excluded:
        logger.info(
            "template %s: %d eligibility exclusion(s) (dev_mode=False)",
            template.id,
            len(excluded),
        )
    if flagged:
        logger.warning(
            "template %s: %d recipe(s) kept past their eligibility ceiling "
            "(dev_mode=True) — not validated",
            template.id,
            len({f.recipe_id for f in flagged}),
        )

    return CandidatePool(
        template=template,
        by_category={k: tuple(v) for k, v in by_category.items()},
        excluded=tuple(excluded),
        flagged=tuple(flagged),
        dev_mode=dev_mode,
    )
