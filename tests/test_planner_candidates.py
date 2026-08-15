"""Hard filters and the uncertainty eligibility filter."""

from __future__ import annotations

from dataclasses import replace

import pytest

from core.foods import templates
from core.foods.models import Component, MealTemplate, TemplateSlot
from core.foods.nutrition_of import nutrition_of_components
from core.nutrition import citations
from core.planner.candidates import (
    build_candidate_pool,
    recipe_allergens,
    recipe_classes,
    recipe_dairy_sourcing_verified,
)
from core.schemas import DietPattern, IngredientClass, MealSlot, Region, diet_pattern_permits
from tests.factories import (
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
    make_ingredient,
    make_recipe,
)


class TestHardFilters:
    def test_diet_pattern_excludes_a_dairy_recipe_from_vegan(self, library, ingredients):
        # 2026-08-14, TASKS_3.md R1a: eligibility is now derived from
        # ingredient classes, not a hand-listed Recipe.diet_patterns whitelist.
        # paneer_masala's only protein is dairy paneer, so a vegan pool must
        # exclude it even though 'sabzi' is a category north_lunch accepts —
        # while tofu_bhurji, the vegan dish in the same slot, is offered.
        pool = build_candidate_pool(
            library.components.values(),
            ingredients,
            template=templates.NORTH_LUNCH,
            diet_pattern=DietPattern.VEGAN,
            dev_mode=True,
        )
        ids = {c.recipe.id for c in pool.by_category.get("sabzi", ())}
        assert "paneer_masala" not in ids
        assert "tofu_bhurji" in ids

    def test_diet_pattern_reaches_parity_for_non_vegetarian(self, library, ingredients):
        # The bug R1a fixed: no recipe in the library ever declared
        # 'non_vegetarian' on the old hand-listed field, so this pattern
        # returned zero candidates in every slot even though every dish is
        # edible under it (nothing in the library carries egg, fish or
        # poultry). Derived eligibility reaches parity with vegetarian.
        vegetarian_pool = build_candidate_pool(
            library.components.values(),
            ingredients,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        non_veg_pool = build_candidate_pool(
            library.components.values(),
            ingredients,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.NON_VEGETARIAN,
            dev_mode=True,
        )
        assert non_veg_pool.by_category == vegetarian_pool.by_category

    def test_region_mismatch_excludes_a_recipe(self, library, ingredients):
        """The region filter alone, with the category filter held out of it.

        Rewritten 2026-08-09 for ``docs/audit_log.md`` finding 32. The previous
        version fed ``rajma_chawal`` to ``SOUTH_LUNCH`` and asserted an empty
        pool -- and said so in its own comment: "combo_rice_legume is not a
        south_lunch category anyway". Two filters could have produced that
        empty pool and the test could not tell which did, so deleting the
        region check left it green.

        That is not an accident of one badly chosen recipe. Every category in
        the real library is region-partitioned (north: sabzi/dal/roti/raita;
        south: tiffin/sambar/kuzhambu/chutney/poriyal), so for every recipe
        that actually exists the region filter is redundant with the category
        filter, and no real-library fixture can isolate it. Hence the synthetic
        pair below: same category, same ingredient, same everything except
        region.
        """

        south_category = "poriyal"
        assert any(
            south_category in slot.accepted_categories
            for slot in templates.SOUTH_LUNCH.slots
        ), "the category must be one SOUTH_LUNCH accepts, or this proves nothing"

        ingredient = SOUTH_LUNCH_INGREDIENTS["veg_a"]
        northern = Component(
            recipe=make_recipe("northern_poriyal", ingredient, region=Region.NORTH_INDIAN),
            category=south_category,
        )
        southern = Component(
            recipe=make_recipe("southern_poriyal", ingredient, region=Region.SOUTH_INDIAN),
            category=south_category,
        )

        def pool_of(*components):
            return build_candidate_pool(
                components,
                SOUTH_LUNCH_INGREDIENTS,
                template=templates.SOUTH_LUNCH,
                diet_pattern=DietPattern.VEGETARIAN,
                dev_mode=True,
            )

        # The control comes first and is the load-bearing half: it proves the
        # southern twin passes every OTHER filter, so the northern one's
        # absence below is attributable to region and to nothing else.
        assert {c.recipe.id for c in pool_of(southern).by_category[south_category]} == {
            "southern_poriyal"
        }
        assert pool_of(northern).by_category == {}
        # And together, so the filter is shown discriminating within one call
        # rather than only across two.
        assert {c.recipe.id for c in pool_of(northern, southern).by_category[south_category]} == {
            "southern_poriyal"
        }

    def test_a_pan_indian_recipe_survives_either_region(self, library, ingredients):
        # The other arm of the same condition: `not in (template.region,
        # Region.PAN_INDIAN)`. A mutation narrowing the check to the template's
        # region alone would keep the test above green while quietly dropping
        # every pan-Indian recipe from every plate.
        ingredient = SOUTH_LUNCH_INGREDIENTS["veg_a"]
        pan = Component(
            recipe=make_recipe("pan_poriyal", ingredient, region=Region.PAN_INDIAN),
            category="poriyal",
        )
        pool = build_candidate_pool(
            [pan],
            SOUTH_LUNCH_INGREDIENTS,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        assert {c.recipe.id for c in pool.by_category["poriyal"]} == {"pan_poriyal"}

    def test_category_not_in_template_excludes_a_recipe(self, library, ingredients):
        # masala_dosa's category is "tiffin", which no south_lunch slot accepts.
        pool = build_candidate_pool(
            [library.component("masala_dosa")],
            ingredients,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        assert pool.by_category == {}

    def test_allergen_overlap_excludes_a_recipe(self):
        # A synthetic ingredient carrying a declared allergen must remove its
        # recipe when that allergen is in the profile's exclusion set.
        from dataclasses import replace

        peanut_veg = replace(SOUTH_LUNCH_INGREDIENTS["veg_a"], allergens=frozenset({"peanut"}))
        ingredients = dict(SOUTH_LUNCH_INGREDIENTS)
        ingredients["veg_a"] = peanut_veg
        assert recipe_allergens(
            next(c.recipe for c in SOUTH_LUNCH_COMPONENTS if c.recipe.id == "veg_a"), ingredients
        ) == frozenset({"peanut"})

        pool = build_candidate_pool(
            SOUTH_LUNCH_COMPONENTS,
            ingredients,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            allergens=frozenset({"peanut"}),
            dev_mode=True,
        )
        assert "veg_a" not in {c.recipe.id for c in pool.by_category.get("poriyal", ())}
        # veg_c is also "poriyal" and carries no allergen, so it must survive.
        assert "veg_c" in {c.recipe.id for c in pool.by_category.get("poriyal", ())}


# ------------------------------------------------------------------------
# R1b (widened scope, 2026-08-15): the permitted-class table and the
# dairy_sourcing_verified gate are two independent mechanisms inside
# diet_pattern_permits (core/schemas/common.py) — a recipe passes only if
# BOTH agree. Finding 48 (docs/audit_log.md) is exactly a case where the
# class table alone said "permitted" and only the gate was actually
# blocking. TestHardFilters.test_diet_pattern_excludes_a_dairy_recipe_from_
# vegan and test_diet_pattern_reaches_parity_for_non_vegetarian exercise the
# call site; the tests below are written so each mechanism can fail on its
# own without the other's tests noticing — see docs/design/probes/
# d4b_mutations.py rows C1 (whole call), D1 (gate only) and D2 (table only).
# ------------------------------------------------------------------------


#: One recipe per IngredientClass, plus one with no class at all, each in the
#: same "dish" category so a single template slot can offer all of them at
#: once. dairy comes in both a verified- and an unverified-sourcing variant,
#: because that split is the entire point of the matrix below: the class is
#: identical on both, and only dairy_sourcing_verified differs.
_CLASS_MATRIX_SPECS: dict[str, frozenset[IngredientClass] | None] = {
    "plain": frozenset(),
    "dairy_unverified": frozenset({IngredientClass.DAIRY}),
    "dairy_verified": frozenset({IngredientClass.DAIRY}),
    "egg": frozenset({IngredientClass.EGG}),
    "fish": frozenset({IngredientClass.FISH}),
    "poultry": frozenset({IngredientClass.POULTRY}),
    "root_veg": frozenset({IngredientClass.ROOT_VEGETABLE}),
}

_CLASS_MATRIX_INGREDIENTS = {
    key: make_ingredient(
        key,
        energy_kcal=100.0,
        protein_g=5.0,
        fat_g=1.0,
        carb_g=10.0,
        classes=classes,
        dairy_sourcing_verified=(key == "dairy_verified"),
    )
    for key, classes in _CLASS_MATRIX_SPECS.items()
}

_CLASS_MATRIX_COMPONENTS = tuple(
    Component(recipe=make_recipe(key, ingredient), category="dish")
    for key, ingredient in _CLASS_MATRIX_INGREDIENTS.items()
)

_CLASS_MATRIX_TEMPLATE = MealTemplate(
    id="class_matrix",
    region=Region.SOUTH_INDIAN,
    meal_slot=MealSlot.LUNCH,
    slots=(TemplateSlot(name="slot", accepted_categories=frozenset({"dish"})),),
)

#: Expected survivors per pattern, derived directly from
#: core.schemas.DIET_PATTERN_PERMITTED_CLASSES plus the jain dairy-sourcing
#: gate — hand-derived here, not read back from the code under test.
# JAIN permits {DAIRY}, and only if sourcing is verified: plain, dairy_verified.
# VEGAN permits {ROOT_VEGETABLE}: plain, root_veg.
# VEGETARIAN permits {DAIRY, ROOT_VEGETABLE}, sourcing irrelevant outside jain:
#   plain, dairy_unverified, dairy_verified, root_veg.
# EGGETARIAN adds EGG: + egg.
# PESCATARIAN adds FISH, still no POULTRY: + fish.
# NON_VEGETARIAN permits everything: all seven.
_EXPECTED_SURVIVORS: dict[DietPattern, frozenset[str]] = {
    DietPattern.JAIN: frozenset({"plain", "dairy_verified"}),
    DietPattern.VEGAN: frozenset({"plain", "root_veg"}),
    DietPattern.VEGETARIAN: frozenset(
        {"plain", "dairy_unverified", "dairy_verified", "root_veg"}
    ),
    DietPattern.EGGETARIAN: frozenset(
        {"plain", "dairy_unverified", "dairy_verified", "root_veg", "egg"}
    ),
    DietPattern.PESCATARIAN: frozenset(
        {"plain", "dairy_unverified", "dairy_verified", "root_veg", "egg", "fish"}
    ),
    DietPattern.NON_VEGETARIAN: frozenset(_CLASS_MATRIX_SPECS),
}


class TestDietPatternPermittedClassTable:
    @pytest.mark.parametrize("pattern", list(DietPattern))
    def test_permitted_class_table_is_enforced_and_pool_is_non_empty(self, pattern):
        # Covers the "existing requirement" half of R1b's widened scope: every
        # DietPattern reaches a non-empty pool somewhere (the real library has
        # no egg/fish/poultry rows at all, so this needs the synthetic
        # matrix), and the permitted-class table itself discriminates — e.g. a
        # poultry-classed recipe cannot reach a pescatarian pool.
        pool = build_candidate_pool(
            _CLASS_MATRIX_COMPONENTS,
            _CLASS_MATRIX_INGREDIENTS,
            template=_CLASS_MATRIX_TEMPLATE,
            diet_pattern=pattern,
            dev_mode=True,
        )
        survivors = {c.recipe.id for c in pool.by_category.get("dish", ())}
        assert survivors == _EXPECTED_SURVIVORS[pattern]
        assert survivors, f"{pattern} reached an empty pool against the class matrix"

    def test_poultry_recipe_specifically_cannot_reach_a_pescatarian_pool(self):
        # Named explicitly, since "pescatarian cannot be expressed by a linear
        # ladder" is the reason DIET_PATTERN_PERMITTED_CLASSES is a table and
        # not a nesting order (core/schemas/common.py, DietPattern docstring).
        pool = build_candidate_pool(
            _CLASS_MATRIX_COMPONENTS,
            _CLASS_MATRIX_INGREDIENTS,
            template=_CLASS_MATRIX_TEMPLATE,
            diet_pattern=DietPattern.PESCATARIAN,
            dev_mode=True,
        )
        ids = {c.recipe.id for c in pool.by_category.get("dish", ())}
        assert "poultry" not in ids
        assert "fish" in ids


class TestDairySourcingGate:
    """The jain dairy-sourcing gate, proven independent of the class table.

    Every test here holds the class table's verdict fixed (dairy is a
    permitted JAIN class throughout) and varies only
    ``dairy_sourcing_verified`` — so a mutation that deletes the gate while
    leaving the class-subset check intact fails these without touching
    TestDietPatternPermittedClassTable, and a mutation that breaks the class
    table leaves these unaffected. See d4b_mutations.py row D1.
    """

    def test_synthetic_unverified_dairy_is_blocked_though_the_class_table_permits_it(self):
        classes = frozenset({IngredientClass.DAIRY})
        # Sanity check first: the class table alone (no ingredient context)
        # says jain permits this. If this line fails, the test below is not
        # isolating the gate.
        assert diet_pattern_permits(DietPattern.JAIN, classes)
        assert not diet_pattern_permits(
            DietPattern.JAIN, classes, dairy_sourcing_verified=False
        )
        assert diet_pattern_permits(
            DietPattern.JAIN, classes, dairy_sourcing_verified=True
        )

    def test_gate_blocks_a_pool_candidate_the_class_table_alone_would_admit(self):
        dairy_component = next(
            c for c in _CLASS_MATRIX_COMPONENTS if c.recipe.id == "dairy_unverified"
        )
        pool = build_candidate_pool(
            [dairy_component],
            _CLASS_MATRIX_INGREDIENTS,
            template=_CLASS_MATRIX_TEMPLATE,
            diet_pattern=DietPattern.JAIN,
            dev_mode=True,
        )
        assert pool.by_category == {}

        verified_ingredients = dict(_CLASS_MATRIX_INGREDIENTS)
        verified_ingredients["dairy_unverified"] = replace(
            verified_ingredients["dairy_unverified"], dairy_sourcing_verified=True
        )
        pool_with_verified_sourcing = build_candidate_pool(
            [dairy_component],
            verified_ingredients,
            template=_CLASS_MATRIX_TEMPLATE,
            diet_pattern=DietPattern.JAIN,
            dev_mode=True,
        )
        assert {c.recipe.id for c in pool_with_verified_sourcing.by_category["dish"]} == {
            "dairy_unverified"
        }

    def test_real_curd_dish_is_blocked_from_jain_by_the_gate_not_the_class_table(
        self, library, ingredients
    ):
        # thayir_plain (data/recipes/thayir_sadam_curd.yaml) is classed dairy
        # only -- no root vegetable -- so DIET_PATTERN_PERMITTED_CLASSES[JAIN]
        # (= {DAIRY}) alone permits it. Finding 48 (docs/audit_log.md): a
        # first pass at R1a's derivation read this dish as jain-eligible for
        # exactly that reason, before the sourcing gate existed.
        recipe = library.recipes["thayir_plain"]
        classes = recipe_classes(recipe, ingredients)
        assert classes == frozenset({IngredientClass.DAIRY})
        assert diet_pattern_permits(DietPattern.JAIN, classes), (
            "the class table alone must permit this recipe, or the test below "
            "proves nothing about the gate specifically"
        )

        # The real fixture data: curd_dahi's dairy_sourcing_verified is False
        # (docs/methodology.md, "Dairy sourcing for jain eligibility"), so the
        # gate -- not the class table -- is what excludes the dish.
        assert not recipe_dairy_sourcing_verified(recipe, ingredients)
        assert not diet_pattern_permits(
            DietPattern.JAIN,
            classes,
            dairy_sourcing_verified=recipe_dairy_sourcing_verified(recipe, ingredients),
        )

        # Flip only curd_dahi's sourcing flag -- nothing about the recipe or
        # the class table changes -- and the dish becomes jain-eligible.
        verified_ingredients = dict(ingredients)
        verified_ingredients["curd_dahi"] = replace(
            ingredients["curd_dahi"], dairy_sourcing_verified=True
        )
        assert recipe_classes(recipe, verified_ingredients) == classes
        assert recipe_dairy_sourcing_verified(recipe, verified_ingredients)
        assert diet_pattern_permits(
            DietPattern.JAIN,
            classes,
            dairy_sourcing_verified=recipe_dairy_sourcing_verified(
                recipe, verified_ingredients
            ),
        )

        # And at the pool level: south_lunch's curd_course slot gains
        # thayir_plain under jain only once sourcing is verified.
        south_lunch_pool = build_candidate_pool(
            library.components.values(),
            ingredients,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.JAIN,
            dev_mode=True,
        )
        assert "thayir_plain" not in {
            c.recipe.id for c in south_lunch_pool.by_category.get("curd", ())
        }

        south_lunch_pool_verified = build_candidate_pool(
            library.components.values(),
            verified_ingredients,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.JAIN,
            dev_mode=True,
        )
        assert "thayir_plain" in {
            c.recipe.id for c in south_lunch_pool_verified.by_category.get("curd", ())
        }


class TestUncertaintyEligibility:
    """Gates on the *combined* composition+process band, per the module
    docstring's account of docs/audit_log.md finding 1 — not on
    Recipe.process_uncertainty alone, which is 0.0 for protein on every real
    recipe (oil carries no protein) and would let everything through."""

    @pytest.mark.parametrize(
        "recipe_id,template",
        [
            ("masala_dosa", templates.SOUTH_BREAKFAST),
            ("sambar_sadam", templates.SOUTH_LUNCH),
            ("rajma_chawal", templates.NORTH_LUNCH),
        ],
    )
    def test_every_real_recipe_is_excluded_in_validated_mode(
        self, library, ingredients, recipe_id, template
    ):
        # Pinned to 0.25 exactly: this is
        # tests/test_nutrition_of.py::TestEligibilityConsequence's own pinned
        # figure (every ingredient row bar `water` is verified=False, so the
        # composition band is composition.unverified_secondary = 0.25, and no
        # process term touches protein on any of these three dishes).
        pool = build_candidate_pool(
            [library.component(recipe_id)],
            ingredients,
            template=template,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=False,
        )
        assert pool.by_category == {}
        protein_flags = [f for f in pool.excluded if f.macro == "protein_g"]
        assert len(protein_flags) == 1
        assert protein_flags[0].recipe_id == recipe_id
        assert protein_flags[0].fraction == pytest.approx(0.25)
        assert protein_flags[0].ceiling == pytest.approx(0.15)
        # Energy is also over its (looser, 0.20) ceiling for all three dishes
        # — composition uncertainty alone (0.25 x point) already exceeds it
        # before any process term is added.
        energy_flags = [f for f in pool.excluded if f.macro == "energy_kcal"]
        assert len(energy_flags) == 1
        assert energy_flags[0].fraction > energy_flags[0].ceiling

    def test_dev_mode_keeps_but_flags_the_same_recipes(self, library, ingredients):
        pool = build_candidate_pool(
            [library.component("masala_dosa")],
            ingredients,
            template=templates.SOUTH_BREAKFAST,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        assert "masala_dosa" in {c.recipe.id for c in pool.by_category.get("tiffin", ())}
        assert pool.excluded == ()
        assert {f.macro for f in pool.flagged} == {"protein_g", "energy_kcal"}
        assert pool.dev_mode is True

    def test_synthetic_verified_ingredients_clear_both_ceilings(self):
        # Contrast case: tight, verified composition data (0.03 band, no
        # process term) clears both ceilings even in validated mode — the
        # eligibility filter is not unconditionally empty, only empty against
        # today's real, unverified fixture.
        pool = build_candidate_pool(
            SOUTH_LUNCH_COMPONENTS,
            SOUTH_LUNCH_INGREDIENTS,
            template=templates.SOUTH_LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=False,
        )
        assert pool.excluded == ()
        assert pool.flagged == ()
        assert sum(len(v) for v in pool.by_category.values()) == len(SOUTH_LUNCH_COMPONENTS)

    def test_target_critical_macros_are_exactly_the_two_registered_ceilings(self):
        from core.planner.candidates import TARGET_CRITICAL_MACROS

        assert set(TARGET_CRITICAL_MACROS) == {"protein_g", "energy_kcal"}
        for macro, key in TARGET_CRITICAL_MACROS.items():
            assert citations.constant(key)  # raises if the key is stale


class TestServingUnitsWhoseFloorIsAboveOne:
    """Added 2026-08-07 (D3) after a latent crash, not a wrong answer.

    ``_eligibility_flags`` priced each candidate at a hard-coded count of 1
    while ``nutrition_of_recipe`` enforces the serving unit's bounds. Every
    recipe in the library happened to have ``min_count == 1``, so the two
    agreed by coincidence. ``idli`` is the first with a floor of 2 -- nobody is
    served one idli -- and adding it made ``build_candidate_pool`` raise
    ``ValueError`` before it could filter anything, for every template
    containing it. The old comment on the line already said "any count in the
    unit's domain"; the code then used a count that need not be in it.

    This is deliberately a *unit* test on the pool rather than an assertion
    about a plate: the failure was a crash, and a plate-level test would report
    it as some unrelated template going empty.
    """

    def test_a_recipe_with_min_count_two_can_be_priced(self, library, ingredients):
        idli = library.component("idli")
        assert idli.recipe.serving_unit.min_count == 2, (
            "this test is only meaningful while some recipe has a floor above 1; "
            "if idli's floor changed, re-point it at another such recipe"
        )
        pool = build_candidate_pool(
            [idli],
            ingredients,
            template=templates.SOUTH_BREAKFAST,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        assert [c.id for c in pool.by_category["tiffin"]] == ["idli@tiffin"]

    def test_the_flag_it_produces_is_count_independent(self, library, ingredients):
        # Why min_count is a safe substitute for 1 and not merely a working one:
        # uncertainty_fraction is scale-invariant, so the flag a recipe earns is
        # the same at every legal count. Checked across idli's whole domain
        # rather than asserted from the module docstring.
        idli = library.component("idli")
        fractions = set()
        for count in range(
            idli.recipe.serving_unit.min_count, idli.recipe.serving_unit.max_count + 1
        ):
            est = nutrition_of_components([(idli, count)], ingredients)
            fractions.add(round(est.uncertainty_fraction("protein_g"), 12))
        assert len(fractions) == 1
