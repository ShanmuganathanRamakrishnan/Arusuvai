"""Hard filters and the uncertainty eligibility filter."""

from __future__ import annotations

import pytest

from core.foods import templates
from core.foods.models import Component
from core.foods.nutrition_of import nutrition_of_components
from core.nutrition import citations
from core.planner.candidates import build_candidate_pool, recipe_allergens
from core.schemas import DietPattern, Region
from tests.factories import (
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
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
