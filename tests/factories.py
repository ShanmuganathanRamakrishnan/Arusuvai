"""Synthetic (non-production) fixtures for exercising ``core/planner``.

Not test cases themselves — a helper module, deliberately named so pytest's
default ``test_*.py`` collection pattern skips it (see ``pyproject.toml``).

These are **not** nutrition claims about real food and do not go through
``core.foods.ifct_loader`` or ``core.foods.recipe_loader`` — they are
``Ingredient``/``Recipe`` objects built directly, the same pattern
``tests/test_models.py`` and ``tests/test_nutrition_of.py`` already use for
unit-testing ``core/foods``. Real recipes live in ``data/recipes/`` and go
through the loader; these exist only to give ``core/planner``'s tests a
template with more than one candidate per slot, which the three real,
hand-authored recipes from Phase 1 do not provide — see
``docs/methodology.md`` limitation 5, "Three recipes is not a library."

Every ingredient below is a single-ingredient recipe at ``grams_per_unit=100``,
so a recipe's per-unit ``NutritionVector`` equals its ingredient's per-100 g
record exactly, and every figure a test derives from these fixtures can be
checked by reading this file, without running anything.

Composition uncertainty is set tight (0.03, ``verified=True``) and process
uncertainty to an explicit, computed zero (no process is modelled for these
single-ingredient synthetic dishes) — deliberately, so these fixtures clear
both eligibility ceilings (0.15 protein, 0.20 energy) in ``dev_mode=False``
too. Eligibility itself is exercised separately, against the real
(unverified) library — see ``tests/test_planner_candidates.py``.
"""

from __future__ import annotations

from core.foods.models import (
    Component,
    Ingredient,
    MealTemplate,
    Recipe,
    RecipeIngredient,
    ServingUnit,
    TemplateSlot,
)
from core.schemas import IngredientClass, MACRO_KEYS, MealSlot, RawOrCooked, Region

_TIGHT_UNCERTAINTY = {m: 0.03 for m in MACRO_KEYS}
_NO_PROCESS_UNCERTAINTY = {m: 0.0 for m in MACRO_KEYS}


def make_ingredient(
    id: str,
    *,
    energy_kcal: float,
    protein_g: float,
    fat_g: float,
    carb_g: float,
    fibre_g: float = 0.0,
    sodium_mg: float = 0.0,
    iron_mg: float = 0.0,
    calcium_mg: float = 0.0,
    b12_ug: float = 0.0,
    diaas: float | None = None,
    classes: frozenset[IngredientClass] = frozenset(),
    dairy_sourcing_verified: bool = False,
) -> Ingredient:
    return Ingredient(
        id=id,
        name_en=id,
        name_ta="",
        name_hi="",
        ifct_code=None,
        energy_kcal=energy_kcal,
        protein_g=protein_g,
        fat_g=fat_g,
        carb_g=carb_g,
        fibre_g=fibre_g,
        sodium_mg=sodium_mg,
        iron_mg=iron_mg,
        calcium_mg=calcium_mg,
        b12_ug=b12_ug,
        state=RawOrCooked.AS_USED,
        diaas=diaas,
        classes=classes,
        dairy_sourcing_verified=dairy_sourcing_verified,
        verified=True,
        composition_uncertainty=_TIGHT_UNCERTAINTY,
    )


def make_recipe(
    id: str,
    ingredient: Ingredient,
    *,
    min_count: int = 1,
    default_count: int = 1,
    max_count: int = 2,
    region: Region = Region.SOUTH_INDIAN,
) -> Recipe:
    return Recipe(
        id=id,
        name=id,
        region=region,
        ingredients=(RecipeIngredient(ingredient.id, 100.0, RawOrCooked.AS_USED),),
        serving_unit=ServingUnit(
            name=id,
            grams_per_unit=100.0,
            min_count=min_count,
            default_count=default_count,
            max_count=max_count,
        ),
        prep_minutes=10,
        process_uncertainty=_NO_PROCESS_UNCERTAINTY,
    )


# --------------------------------------------------------------------------
# south_lunch-shaped pool: rice_base(2) x gravy(2) x vegetable(3, 1-2 picked)
# x curd_course(2) x crisp(2, optional). Mirrors core.foods.templates.SOUTH_
# LUNCH's slot shape and categories exactly, with enough candidates per slot
# to make the combination arithmetic non-trivial. See
# tests/test_planner_combinations.py for the hand-derived combination count.
#
# curd_course needs >= 2 candidates, not 1: a no-repeat variety window (see
# TestEnumeration.test_a_week_is_not_a_21_way_cross_product) exhausts a
# single-candidate required slot after its first use — every later day's
# combos come back empty, which is a real modelling constraint (this fixture
# lacked variety), not a bug in the no-repeat filter itself.
# --------------------------------------------------------------------------

_SPECS = {
    # id: (category, energy, protein, fat, carb, fibre, sodium, iron, calcium, b12)
    "rice_a": ("rice", 130, 2.7, 0.3, 28, 0.4, 1, 0.2, 10, 0),
    "rice_b": ("mixed_rice", 150, 3.5, 1.0, 30, 0.6, 5, 0.3, 12, 0),
    "gravy_a": ("sambar", 80, 4.0, 2.0, 10, 2, 300, 1.0, 20, 0),
    "gravy_b": ("rasam", 40, 1.5, 0.5, 6, 1, 250, 0.5, 10, 0),
    "veg_a": ("poriyal", 60, 2.0, 3.0, 6, 3, 150, 0.8, 30, 0),
    "veg_b": ("kootu", 70, 3.0, 2.5, 8, 2.5, 180, 1.0, 40, 0),
    "veg_c": ("poriyal", 50, 1.5, 2.0, 5, 2, 120, 0.6, 25, 0),
    "curd_a": ("curd", 60, 3.0, 3.5, 4, 0, 40, 0.1, 120, 0.2),
    "curd_b": ("buttermilk", 50, 2.5, 2.0, 3, 0, 35, 0.1, 100, 0.15),
    "crisp_a": ("appalam", 35, 1.0, 1.5, 4, 0.5, 200, 0.2, 5, 0),
    "crisp_b": ("pickle", 20, 0.3, 1.0, 2, 0.5, 400, 0.1, 3, 0),
}

#: DIAAS for the two dairy rows only, mirroring the real library, where
#: ``curd_dahi`` is 1.09 and every grain/legume row sits between 0.45 and 0.62.
#: Added 2026-08-07 with slice 4's quality-source rule: without it this whole
#: fixture carries zero qualifying protein, and every test built on it would
#: have started measuring the quality floor instead of the thing it names.
#: 1.09 is copied from the real fixture row, not chosen to make anything pass —
#: any value at or above the 0.75 threshold produces identical behaviour, since
#: the rule is a cutoff and not a weighting.
_DIAAS: dict[str, float] = {"curd_a": 1.09, "curd_b": 1.09}

SOUTH_LUNCH_INGREDIENTS: dict[str, Ingredient] = {
    id: make_ingredient(
        id,
        diaas=_DIAAS.get(id),
        energy_kcal=spec[1],
        protein_g=spec[2],
        fat_g=spec[3],
        carb_g=spec[4],
        fibre_g=spec[5],
        sodium_mg=spec[6],
        iron_mg=spec[7],
        calcium_mg=spec[8],
        b12_ug=spec[9],
    )
    for id, spec in _SPECS.items()
}

SOUTH_LUNCH_RECIPES: dict[str, Recipe] = {
    id: make_recipe(id, SOUTH_LUNCH_INGREDIENTS[id]) for id in _SPECS
}

SOUTH_LUNCH_COMPONENTS: tuple[Component, ...] = tuple(
    Component(recipe=SOUTH_LUNCH_RECIPES[id], category=spec[0]) for id, spec in _SPECS.items()
)

#: Max protein reachable by ANY single combination at every component's max
#: count (2 units each). Per slot, the richest legal selection:
#:   rice_base  (pick exactly 1): rice_b  3.5 * 2 =  7.0
#:   gravy      (pick exactly 1): gravy_a 4.0 * 2 =  8.0
#:   vegetable  (pick 1 or 2):    veg_a 2.0 + veg_b 3.0 = 5.0, * 2 = 10.0
#:   curd_course(pick exactly 1): curd_a  3.0 * 2 =  6.0
#:   crisp      (pick 0 or 1):    crisp_a 1.0 * 2 =  2.0
#: total = 7.0 + 8.0 + 10.0 + 6.0 + 2.0 = 33.0 g
#:
#: Corrected while deriving Phase 3's decline messages: this read 33.6, from
#: a derivation that summed BOTH crisp candidates (1.0 + 0.3). The crisp slot
#: has max_selections=1, so no combination ever contains two. The old figure
#: was wrong and its test passed anyway, because the test asserted the
#: constant against a comment restating the same mistake — a hand-computed
#: expected value is only worth what its derivation is worth. The test now
#: also checks this against what core/planner actually reaches, so the two
#: cannot agree with each other while both being wrong.
SOUTH_LUNCH_MAX_PROTEIN_G = 33.0


# --------------------------------------------------------------------------
# A minimal two-required-slot template for the feasibility pre-filter test,
# where every serving unit is pinned to exactly one legal count (min=max=1)
# so a combination's macro total is a single exact number, not a range —
# keeping the pre-filter arithmetic exact rather than an envelope.
# --------------------------------------------------------------------------

FEASIBILITY_TEMPLATE = MealTemplate(
    id="test_two_slot",
    region=Region.SOUTH_INDIAN,
    meal_slot=MealSlot.LUNCH,
    slots=(
        TemplateSlot(name="a", accepted_categories=frozenset({"cat_a"})),
        TemplateSlot(name="b", accepted_categories=frozenset({"cat_b"})),
    ),
)

_FEASIBILITY_SPECS = {
    # id: (category, energy, protein, sodium)
    "a1": ("cat_a", 100, 5, 500),
    "a2": ("cat_a", 200, 10, 100),
    "b1": ("cat_b", 50, 2, 1000),
    "b2": ("cat_b", 150, 8, 50),
}

FEASIBILITY_INGREDIENTS: dict[str, Ingredient] = {
    id: make_ingredient(
        id, energy_kcal=spec[1], protein_g=spec[2], fat_g=0.0, carb_g=0.0, sodium_mg=spec[3]
    )
    for id, spec in _FEASIBILITY_SPECS.items()
}

FEASIBILITY_RECIPES: dict[str, Recipe] = {
    id: make_recipe(id, FEASIBILITY_INGREDIENTS[id], min_count=1, default_count=1, max_count=1)
    for id in _FEASIBILITY_SPECS
}

FEASIBILITY_COMPONENTS: tuple[Component, ...] = tuple(
    Component(recipe=FEASIBILITY_RECIPES[id], category=spec[0])
    for id, spec in _FEASIBILITY_SPECS.items()
)
