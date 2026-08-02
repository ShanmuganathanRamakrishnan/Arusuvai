"""Wire target derivation to the meal-generation pipeline for one meal slot.

Everything in ``core/planner`` before this file (``candidates`` ->
``combinations`` -> ``solver`` -> ``validator``) is real, tested code that
nothing yet calls end to end. This module is that call: load the recipe
library once, pick the template for a (region, meal_slot), build the
candidate pool, enumerate combinations, and walk the relaxation ladder — the
same sequence ``tests/test_planner_validator.py`` already exercises against
synthetic fixtures, run here against the real, hand-authored 3-recipe library
in ``data/recipes/``.

## Why the real library is expected to decline, structurally

Every one of the three real recipes carries a category that only one slot in
its own template accepts, and every *other* required slot in that template
has zero candidates:

- ``masala_dosa`` (category ``tiffin``) fills ``south_breakfast``'s
  ``tiffin_item`` slot, but nothing in the library carries ``sambar``/
  ``kuzhambu`` (the required ``gravy_accompaniment`` slot) or ``chutney``/
  ``podi`` (the required ``chutney`` slot).
- ``sambar_sadam`` (category ``mixed_rice``) fills ``south_lunch``'s
  ``rice_base`` slot, but nothing carries ``sambar``/``kuzhambu``/``rasam``
  (``gravy``), ``poriyal``/``kootu`` (``vegetable``), or ``curd``/
  ``buttermilk`` (``curd_course`` — all three required).
- ``rajma_chawal`` (category ``combo_rice_legume``) fills ``north_lunch``'s
  ``legume_curry`` slot, but nothing carries ``rice``/``roti`` (the required
  ``grain_base`` slot).

``core/planner/combinations.py``'s ``enumerate_combinations`` returns ``()``
the moment *any* required slot has zero legal selections — before the
feasibility pre-filter or the solver ever runs, and independent of the
profile's target. So every template call against this library declines with
``Violation(kind="no_candidates")`` regardless of who is asking or what
``dev_mode`` is set to: this is a fact about the library's breadth (one
recipe per category, no template's other required categories populated at
all), not about any one target being hard to hit.
``tests/test_planner_plan.py::test_every_real_template_declines_on_the_real_library``
asserts this for all four templates, and
``tests/test_planner_plan.py::TestHappyPathAgainstSyntheticLibrary`` proves
the wiring itself (loader -> pool -> combinations -> ladder -> plan) is not
what's broken, by running the identical call sequence against
``tests/factories.py``'s richer synthetic ``SOUTH_LUNCH`` fixture, where it
succeeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

from core.foods.ifct_loader import load_ingredients
from core.foods.models import Component, Ingredient
from core.foods.recipe_loader import RecipeLibrary, load_recipes
from core.foods.templates import template_for
from core.nutrition.meal_target import meal_target
from core.nutrition.target import NutritionTarget
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations
from core.planner.validator import LadderOutcome, plan_within_ladder
from core.schemas import DayLedger, DietPattern, MealSlot, Profile, Region

__all__ = ["Library", "load_library", "default_library", "plan_meal"]


@dataclass(frozen=True)
class Library:
    """A loaded ingredient set plus recipe library, ready for candidate pooling."""

    ingredients: Mapping[str, Ingredient]
    recipes: RecipeLibrary

    def components(self) -> tuple[Component, ...]:
        return tuple(self.recipes.components.values())


def load_library(
    ingredient_dir: Path | str = Path("data/raw/ifct"),
    recipe_dir: Path | str = Path("data/recipes"),
) -> Library:
    """Load ingredients then recipes. File loading only — no nutritional math."""

    ing_report = load_ingredients(ingredient_dir)
    recipes = load_recipes(recipe_dir, ing_report.loaded)
    return Library(ingredients=ing_report.loaded, recipes=recipes)


@lru_cache(maxsize=1)
def default_library() -> Library:
    """The real ``data/`` library, loaded once and cached.

    A process-lifetime cache, not a request-scoped one: the recipe and
    ingredient files do not change while the API is running, and reloading
    ~30 rows and 3 recipes from disk on every request would be pure overhead.
    ``api/main.py`` is the only caller that relies on the caching; tests call
    ``load_library`` directly so a mutated fixture directory is never masked
    by a stale cache.
    """

    return load_library()


def plan_meal(
    library: Library,
    day_target: NutritionTarget,
    *,
    region: Region,
    meal_slot: MealSlot,
    diet_pattern: DietPattern,
    profile: Profile | None = None,
    dev_mode: bool = True,
    allergens: frozenset[str] = frozenset(),
    ledger: DayLedger | None = None,
) -> LadderOutcome:
    """Solve one meal against its share of ``day_target``.

    ``ledger`` is what the rest of the day has already spent, for the nutrients
    budgeted per day rather than apportioned by energy fraction. ``None`` means
    a day with nothing planned yet. It is deliberately an *input* and not an
    output: this function returns a plate, and the caller decides whether that
    plate happened — composing the result with ``DayLedger.with_meal`` — because
    ``core/`` owns no state and must not decide that offering a plan is the same
    as eating it.

    ``dev_mode`` defaults ``True`` here (the opposite of
    ``build_candidate_pool``'s own default) because every ingredient in
    ``data/raw/ifct`` but ``water`` is ``verified=False`` today
    (``docs/methodology.md``), so ``dev_mode=False`` would exclude the whole
    library before a single combination is even enumerated — a different,
    earlier decline than the one this function exists to demonstrate
    honestly. Passing ``dev_mode=False`` explicitly still works and is the
    right choice once the library has verified rows to keep.
    """

    template = template_for(region, meal_slot)
    single_meal_target = meal_target(day_target, meal_slot, ledger=ledger)
    pool = build_candidate_pool(
        library.components(),
        library.ingredients,
        template=template,
        diet_pattern=diet_pattern,
        allergens=allergens,
        dev_mode=dev_mode,
    )
    combinations = enumerate_combinations(pool)
    return plan_within_ladder(
        combinations, single_meal_target, library.ingredients, profile=profile
    )
