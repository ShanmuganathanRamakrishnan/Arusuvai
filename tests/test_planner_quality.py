"""Slice 4: protein quality as a source constraint rather than a multiplier.

The rule under test is a floor on how much of a plate's protein comes from an
ingredient whose ``diaas`` clears ``protein.quality_diaas_threshold``. Three
things have to be true for it to be worth anything, and each has its own class
below:

1. It reads the data. A rule that behaves identically when the underlying DIAAS
   figures move is a hard-coded list of dairy foods wearing a threshold, which
   is what CLAUDE.md's round-4 addendum demands be disproved by perturbation
   rather than asserted. ``TestThePerturbationTest`` moves a DIAAS value and
   watches a *verdict* move.
2. It is outside the relaxation ladder. ``TestNoRungMovesTheQualityFloor``.
3. Quality is applied exactly once. Slice 2 removed it from target inflation;
   this slice must not put it back. ``TestQualityIsAppliedOnce``.

Every expected number is hand-derived in a comment from the fixture rows and
the registered constants, per CLAUDE.md's testing convention — never snapshotted
from a run.
"""

from __future__ import annotations

import dataclasses

import pytest

from core.foods.nutrition_of import nutrition_of_components
from core.foods.quality import (
    ingredient_qualifies,
    quality_protein_of_components,
    quality_protein_of_recipe,
)
from core.nutrition import citations
from core.nutrition.meal_target import meal_target
from core.nutrition.target import NutritionTarget, simple_target
from core.nutrition.targets import derive_target
from core.planner.plan import Library, plan_meal
from core.planner.validator import RELAXATION_ORDER
from core.schemas import (
    ActivityLevel,
    DietPattern,
    Goal,
    MealSlot,
    Profile,
    Region,
    Sex,
)

#: The reference profile every worked number in docs/design/target_model_v2.md
#: is stated for: 70 kg / 175 cm / 28 / male / moderate / maintain.
#: Day protein floor = 70 x protein.g_per_kg_maintain (1.6) = 112.0 g.
_DAY_PROTEIN_G = 112.0
#: protein.quality_meal_floor_fraction (0.10) x 112.0 = 11.2 g, every slot.
_MEAL_QUALITY_FLOOR_G = 11.2


def _profile(diet: DietPattern = DietPattern.VEGETARIAN) -> Profile:
    return Profile(
        weight_kg=70.0,
        height_cm=175.0,
        age_years=28,
        sex=Sex.MALE,
        activity=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        diet=diet,
    )


@pytest.fixture()
def real(ingredients, library) -> Library:
    return Library(ingredients=ingredients, recipes=library)


def _plan(lib: Library, region: Region, slot: MealSlot, diet=DietPattern.VEGETARIAN):
    profile = _profile(diet)
    return plan_meal(
        lib,
        derive_target(profile).nutrition_target,
        region=region,
        meal_slot=slot,
        diet_pattern=diet,
        profile=profile,
    )


def _with_diaas(lib: Library, ingredient_id: str, value: float | None) -> Library:
    """``lib`` with one ingredient row's DIAAS replaced. Never mutates ``lib``."""

    rows = dict(lib.ingredients)
    rows[ingredient_id] = dataclasses.replace(rows[ingredient_id], diaas=value)
    return Library(ingredients=rows, recipes=lib.recipes)


# --------------------------------------------------------------------------


class TestQualification:
    """Which rows clear the bar, and what a missing value means."""

    def test_the_threshold_partitions_the_library_where_expected(self, ingredients):
        # protein.quality_diaas_threshold = 0.75, against the authored DIAAS
        # figures in data/raw/ifct/fixture_ingredients.csv:
        #   curd_dahi       1.09  >= 0.75  qualifies
        #   paneer_fresh    1.00  >= 0.75  qualifies
        #   soya_chunks_dry 0.85  >= 0.75  qualifies
        #   tofu_firm       0.65  <  0.75  does NOT
        #   urad_dal_raw    0.62  <  0.75  does NOT
        #   toor_dal_raw    0.60  <  0.75  does NOT
        #   rice_cooked     0.47  <  0.75  does NOT
        qualifying = {i for i, ing in ingredients.items() if ingredient_qualifies(ing)}
        assert qualifying == {"curd_dahi", "paneer_fresh", "soya_chunks_dry"}

    def test_a_missing_diaas_does_not_qualify(self, ingredients):
        # 17 of the 29 rows carry no DIAAS at all. Absent must read as "does not
        # qualify", never as "assume the best" -- the same ordering CLAUDE.md's
        # round-4 addendum requires of uncertainty. The cost is real and is
        # recorded in docs/methodology.md: a protein-dense row added without a
        # DIAAS silently counts for nothing.
        assert ingredients["potato_boiled"].diaas is None
        assert not ingredient_qualifies(ingredients["potato_boiled"])

    def test_qualification_reads_the_registered_threshold(self, ingredients):
        # Not a hard-coded list: move the threshold above curd and curd stops
        # qualifying. Restored and proven restored.
        key = "protein.quality_diaas_threshold"
        original = citations.constant(key)
        assert ingredient_qualifies(ingredients["curd_dahi"])
        citations._CONSTANTS[key] = dataclasses.replace(original, value=1.5)
        try:
            assert not ingredient_qualifies(ingredients["curd_dahi"])
        finally:
            citations._CONSTANTS[key] = original
        assert ingredient_qualifies(ingredients["curd_dahi"])


class TestQualityProteinArithmetic:
    """Grams per serving unit, hand-derived from the recipe lines."""

    @pytest.mark.parametrize(
        "recipe_id,expected",
        [
            # paneer_masala: 70.0 g paneer_fresh x 18.3 g protein/100 g = 12.810
            ("paneer_masala", 12.810),
            # soya_chunk_curry: 28.0 g soya_chunks_dry x 52.0/100 = 14.560
            ("soya_chunk_curry", 14.560),
            # onion_raita: 128.0 g curd_dahi x 3.1/100 = 3.968
            ("onion_raita", 3.968),
            # thayir_plain: 145.0 g curd_dahi x 3.1/100 = 4.495
            ("thayir_plain", 4.495),
            # tofu_bhurji is 85 g of tofu and contributes NOTHING: tofu_firm's
            # authored DIAAS is 0.65, below the threshold. This row is the whole
            # point of the parametrisation -- it is the third densest protein
            # component in the library and the rule scores it at zero.
            ("tofu_bhurji", 0.0),
            ("dal_tadka", 0.0),
            ("phulka", 0.0),
            ("sambar", 0.0),
        ],
    )
    def test_per_unit(self, library, ingredients, recipe_id, expected):
        actual = quality_protein_of_recipe(
            library.recipes[recipe_id], 1, ingredients
        )
        assert actual == pytest.approx(expected, abs=1e-3)

    def test_it_scales_with_the_integer_unit_count(self, library, ingredients):
        # 3.968 x 2 = 7.936. Integer counts only -- quality_protein_of_recipe
        # runs the same ServingUnit.grams_for bounds check nutrition_of_recipe
        # does, so a fractional portion cannot enter through this path either.
        assert quality_protein_of_recipe(
            library.recipes["onion_raita"], 2, ingredients
        ) == pytest.approx(7.936, abs=1e-3)


class TestThePerMealFloor:
    """11.2 g, flat, on every slot."""

    def test_the_floor_is_a_tenth_of_the_day_protein_floor(self):
        # 70 kg x protein.g_per_kg_maintain (1.6) = 112.0 g/day.
        # x protein.quality_meal_floor_fraction (0.10)          = 11.2 g/meal.
        day = derive_target(_profile()).nutrition_target
        assert day.floor("protein_g") == pytest.approx(_DAY_PROTEIN_G)
        assert meal_target(day, MealSlot.LUNCH).quality_protein_floor() == pytest.approx(
            _MEAL_QUALITY_FLOOR_G
        )

    def test_it_does_not_scale_with_the_meal_energy_share(self):
        # Deliberately flat, unlike every other bound meal_target produces.
        # Breakfast takes 0.25 of the day's energy and lunch 0.35, and both get
        # the same quality floor: the rule is "no meal is pure lentil", which is
        # a statement about each plate rather than a share of a day. Asserted so
        # that making it proportional later is a visible decision.
        day = derive_target(_profile()).nutrition_target
        floors = {
            slot: meal_target(day, slot).quality_protein_floor() for slot in MealSlot
        }
        assert set(floors) == set(MealSlot)
        assert all(f == pytest.approx(_MEAL_QUALITY_FLOOR_G) for f in floors.values())

    def test_no_day_protein_floor_means_no_quality_floor(self):
        # Rather than inventing one, which would be a nutritional number written
        # outside citations.py.
        bare = NutritionTarget(ceilings={"energy_kcal": 800.0})
        assert meal_target(bare, MealSlot.LUNCH).quality_protein_floor() is None


class TestNoRungMovesTheQualityFloor:
    """The ladder widens tolerances. This is not one."""

    def test_every_rung_leaves_it_exactly_where_it_was(self):
        target = meal_target(
            derive_target(_profile()).nutrition_target, MealSlot.LUNCH
        )
        before = target.quality_protein_floor()
        assert before == pytest.approx(_MEAL_QUALITY_FLOOR_G)
        current = target
        for step in RELAXATION_ORDER:
            current = step.apply(current, frozenset())
            assert current.quality_protein_floor() == pytest.approx(before), (
                f"rung {step.name} moved the quality floor; no rung may. A "
                "composition rule has no looser version -- see "
                "core/planner/validator.py's module docstring."
            )

    def test_the_ladder_still_widens_what_it_is_supposed_to(self):
        # The control. Without it the test above would pass just as happily
        # against a ladder that had stopped working entirely.
        target = meal_target(
            derive_target(_profile()).nutrition_target, MealSlot.LUNCH
        )
        widened = target
        for step in RELAXATION_ORDER:
            widened = step.apply(widened, frozenset())
        assert widened.ceiling("carb_g") > target.ceiling("carb_g")
        assert widened.floor("protein_g") < target.floor("protein_g")


class TestQualityIsAppliedOnce:
    """Slice 2 took DIAAS out of the target. Slice 4 must not put it back."""

    def test_the_protein_floor_is_still_the_unadjusted_figure(self):
        # By inspection AND by assertion: compute_protein still computes
        # quality_adjusted_g (base_g / diaas) and derive_target still passes
        # base_g to simple_target. If slice 4 had inflated the target as well as
        # constraining the sources, this is the assertion that would go red.
        dt = derive_target(_profile(DietPattern.VEGAN))
        assert dt.nutrition_target.floor("protein_g") == pytest.approx(dt.protein.base_g)
        assert dt.protein.quality_adjusted_g > dt.protein.base_g

    def test_the_day_quality_floor_derives_from_base_not_from_the_adjustment(self):
        # protein.quality_day_fraction (0.33) x base_g (112.0) = 36.96 g.
        # Taking it off quality_adjusted_g instead would be DIAAS re-entering as
        # a multiplier by the back door: for a vegan (DIAAS 0.75) that would
        # give 0.33 x 149.33 = 49.28 g, a quality floor 33% higher for no reason
        # anyone stated. Both diets are checked so the assertion cannot pass by
        # coincidence on a diet whose DIAAS is 1.0.
        for diet in (DietPattern.VEGETARIAN, DietPattern.VEGAN):
            dt = derive_target(_profile(diet))
            assert dt.protein.quality_source_day_g == pytest.approx(36.96, abs=0.01)

    def test_the_day_quality_floor_gates_on_nothing(self):
        # It is computed and displayed, not enforced: enforcing a DAY floor
        # against a planner that solves one meal at a time is a reachability
        # question, and that is a separate slice. Asserted so the gap is visible
        # rather than assumed -- if a day-level gate lands, this test is the one
        # that should look wrong to whoever reads it next.
        day = derive_target(_profile()).nutrition_target
        assert day.quality_protein_floor() is None

    def test_simple_target_adds_no_quality_floor_unless_asked(self):
        assert simple_target(
            energy_kcal=2000.0, protein_g_min=100.0
        ).quality_protein_floor() is None


class TestAgainstTheRealLibrary:
    """Measured verdicts, per template."""

    def test_the_south_templates_now_reach_the_floor(self, real):
        # REPLACES test_the_south_templates_cannot_reach_the_floor_at_all,
        # 2026-08-07 (D3). That test pinned a real fact -- thayir_plain was the
        # only qualifying component either south template could reach, capped at
        #   145.0 g curd_dahi x 3.1/100 x 2 = 8.99 g  <  11.2 g
        # -- and D3 made it false on purpose by adding soya_kuzhambu, whose
        # single katori carries
        #   25.0 g soya_chunks_dry x 52.0/100 = 13.00 g   (diaas 0.85 >= 0.75)
        # so the floor is now clearable from the gravy slot alone, in both
        # templates. Note what did NOT change: no threshold, fraction or DIAAS
        # value moved. The library got wider.
        for region, slot in (
            (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
            (Region.SOUTH_INDIAN, MealSlot.LUNCH),
        ):
            outcome = _plan(real, region, slot)
            assert outcome.plan is not None, outcome.result.violations
            assert not [
                v for v in outcome.result.violations if v.macro == "quality_protein_g"
            ]
            assert outcome.plan.quality_protein_g >= _MEAL_QUALITY_FLOOR_G

    def test_the_reference_breakfast_plate_is_idli_kuzhambu_chutney_curd(self, real):
        # The plate, hand-computed before it was measured (see the D3 commit).
        # Qualifying protein: soya_kuzhambu x1 = 13.00 g, thayir_plain x1 =
        #   145.0 g curd_dahi x 3.1/100 = 4.495 g;  13.00 + 4.495 = 17.495 g.
        # Idli and coconut chutney carry none -- idli is in this plate because
        # it is 1.73 mg sodium per kcal against masala dosa's 2.62, not because
        # it helps the quality floor.
        outcome = _plan(real, Region.SOUTH_INDIAN, MealSlot.BREAKFAST)
        assert outcome.result.relaxation_applied == ()
        assert outcome.plan.unit_counts == {
            "idli@tiffin": 6,
            "soya_kuzhambu@kuzhambu": 1,
            "coconut_chutney@chutney": 2,
            "thayir_plain@curd": 1,
        }
        assert outcome.plan.quality_protein_g == pytest.approx(17.495, abs=1e-3)

    def test_the_reference_lunch_still_needs_three_rungs_and_why(self, real):
        # south_lunch passes, but not unrelaxed, and the reason is sodium rather
        # than quality: clearing the 39.2 g protein floor forces 2 katoris of
        # soya_kuzhambu (647.0 mg), and the required curd course (261.9) plus
        # the required vegetable leave the base almost no room -- which is why
        # the rice_base the solver picks is steamed_rice at 2.0 mg, not
        # sambar_sadam at 408.6. The plate lands at 1391.1 mg against the
        # 1400 mg hard ceiling: 8.9 mg of headroom. Energy tolerance is the rung
        # that lets it in at 848.1 kcal against an unrelaxed 854.9 floor.
        outcome = _plan(real, Region.SOUTH_INDIAN, MealSlot.LUNCH)
        assert outcome.result.relaxation_applied == (
            "sodium_max_fibre_min",
            "fat_carb_tolerance",
            "energy_tolerance",
        )
        assert outcome.plan.unit_counts == {
            "steamed_rice@rice": 1,
            "soya_kuzhambu@kuzhambu": 2,
            "carrot_poriyal@poriyal": 2,
            "thayir_plain@curd": 1,
        }
        point = nutrition_of_components(
            [(real.recipes.components[c.split("@")[0]], n)
             for c, n in outcome.plan.unit_counts.items()],
            real.ingredients,
        ).point
        assert point.sodium_mg == pytest.approx(1391.1, abs=0.5)

    def test_the_decline_never_shows_a_reader_the_identifier(self, real):
        # A Violation macro is a stable token crossing the API; the sentence a
        # user reads must not contain it. Same rule tests/test_web_no_identifiers.py
        # enforces on the browser side, checked here at the source.
        #
        # Re-homed 2026-08-07 (D3): this used to read the south breakfast
        # decline, which no longer declines. The vegan north dinner with
        # soya_chunks_dry disqualified is the same decline for the same reason
        # -- see test_the_rule_is_not_hard_coded_to_dairy, which pins the
        # verdict this one reads the prose of.
        outcome = _plan(
            _with_diaas(real, "soya_chunks_dry", 0.50),
            Region.NORTH_INDIAN,
            MealSlot.DINNER,
            DietPattern.VEGAN,
        )
        text = outcome.result.disclosure or ""
        assert "quality_protein_g" not in text
        assert "high-quality source" in text

    def test_both_north_templates_still_pass_with_no_relaxation(self, real):
        for slot in (MealSlot.LUNCH, MealSlot.DINNER):
            outcome = _plan(real, Region.NORTH_INDIAN, slot)
            assert outcome.plan is not None
            assert outcome.result.relaxation_applied == ()
            assert outcome.plan.quality_protein_g >= _MEAL_QUALITY_FLOOR_G

    def test_the_three_katoris_of_dal_plate_fails_on_quality(self, real):
        # docs/design/target_model_v2.md section 3's worked plate:
        # phulka x3 + dal_tadka x3 + onion_raita x2. Qualifying protein is the
        # raita alone -- 128 g curd x 3.1/100 x 2 = 7.936 g -- against an 11.2 g
        # floor, because toor dal (0.60) and atta (0.45) contribute nothing.
        #
        # It was ALREADY rejected before this slice, on sodium (1649.3 mg over a
        # 1400 mg guard) and on energy. Slice 4 adds a third and independent
        # reason, and it is the one that names what is actually wrong with the
        # plate as food.
        components = real.recipes.components
        items = [
            (components["phulka"], 3),
            (components["dal_tadka"], 3),
            (components["onion_raita"], 2),
        ]
        quality = quality_protein_of_components(items, real.ingredients)
        assert quality == pytest.approx(7.936, abs=1e-3)
        assert quality < _MEAL_QUALITY_FLOOR_G
        # And the plate is still over the bounds it already broke, so the new
        # reason is genuinely additional rather than a replacement.
        point = nutrition_of_components(items, real.ingredients).point
        assert point.sodium_mg == pytest.approx(1649.3, abs=0.5)


class TestTheSolverGateItself:
    """The gate inside the count search, isolated from the pre-filter.

    This class exists because of a defect injection that everything else in this
    file survived. Deleting the quality check from
    ``solver._within_target_point`` left all 31 other tests green: on the real
    library, ``feasible_combinations`` discards every quality-failing
    combination *before* the solver runs, so the solver's own gate is never the
    thing that decides those cases. A test suite that cannot fail on a deleted
    gate is not testing the gate.

    The isolating case needs a combination the pre-filter must PASS (its
    components can reach the floor at their maximum counts) whose best-scoring
    assignment nonetheless falls short (at the counts the solver prefers). The
    synthetic ``SOUTH_LUNCH`` pool provides it: ``curd_b`` carries
    2.5 g of qualifying protein per unit over a 1-2 unit domain, so it reaches
    5.0 g at max and 2.5 g at the count the deviation score would otherwise pick.
    """

    def _pool_and_combinations(self):
        from core.foods.templates import template_for
        from core.planner.candidates import build_candidate_pool
        from core.planner.combinations import enumerate_combinations
        from tests.factories import SOUTH_LUNCH_COMPONENTS, SOUTH_LUNCH_INGREDIENTS

        pool = build_candidate_pool(
            SOUTH_LUNCH_COMPONENTS,
            SOUTH_LUNCH_INGREDIENTS,
            template=template_for(Region.SOUTH_INDIAN, MealSlot.LUNCH),
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=False,
        )
        return SOUTH_LUNCH_INGREDIENTS, enumerate_combinations(pool)

    def _solve(self, target, ingredients, combinations):
        from core.planner.combinations import feasible_combinations
        from core.planner.solver import solve

        return solve(feasible_combinations(combinations, target, ingredients), target, ingredients)

    def test_the_gate_changes_the_chosen_unit_counts(self):
        # Day floor 40 g protein / 1800 kcal -> lunch quality floor
        # 0.10 x 40 = 4.0 g. The SAME combination survives the pre-filter with
        # and without the floor (curd_b reaches 5.0 g at 2 units, above 4.0), so
        # any difference below is the solver's gate and nothing else.
        ingredients, combinations = self._pool_and_combinations()
        target = meal_target(
            simple_target(energy_kcal=1800.0, protein_g_min=40.0), MealSlot.LUNCH
        )
        assert target.quality_protein_floor() == pytest.approx(4.0)
        without = dataclasses.replace(target, quality_protein_floor_g=None)

        gated = self._solve(target, ingredients, combinations)
        ungated = self._solve(without, ingredients, combinations)
        assert gated and ungated
        # Same combination, different counts: curd_b goes 1 -> 2 units purely to
        # clear the floor, and the qualifying total doubles with it.
        assert gated[0].combination.recipe_ids() == ungated[0].combination.recipe_ids()
        assert ungated[0].unit_counts["curd_b@buttermilk"] == 1
        assert gated[0].unit_counts["curd_b@buttermilk"] == 2
        assert ungated[0].quality_protein_g == pytest.approx(2.5)
        assert gated[0].quality_protein_g == pytest.approx(5.0)

    def test_the_gate_can_empty_a_solve_the_pre_filter_admitted(self):
        # 40 g / 2000 kcal: every combination the pre-filter admits is solvable
        # without the floor and none is solvable with it, because the counts
        # that reach the tighter energy band leave curd at one unit.
        ingredients, combinations = self._pool_and_combinations()
        target = meal_target(
            simple_target(energy_kcal=2000.0, protein_g_min=40.0), MealSlot.LUNCH
        )
        without = dataclasses.replace(target, quality_protein_floor_g=None)
        assert self._solve(without, ingredients, combinations)
        assert self._solve(target, ingredients, combinations) == ()


class TestThePerturbationTest:
    """CLAUDE.md's round-4 rule: move the input and watch the output move."""

    def test_disqualifying_curd_moves_the_south_breakfast_figure(self, real):
        # Rewritten 2026-08-07 (D3): this used to move a DECLINE's reported
        # figure from 8.99 g to 0.0 g. South breakfast now passes, so the
        # perturbation moves the PLAN's figure instead -- same axis, same proof
        # obligation. 17.495 g = soya_kuzhambu 13.00 + thayir_plain 4.495; drop
        # curd_dahi below the threshold and only the kuzhambu's 13.00 survives.
        # If the rule were a hard-coded list of dairy foods the figure would not
        # move at all.
        before = _plan(real, Region.SOUTH_INDIAN, MealSlot.BREAKFAST)
        after = _plan(
            _with_diaas(real, "curd_dahi", 0.50),
            Region.SOUTH_INDIAN,
            MealSlot.BREAKFAST,
        )
        assert before.plan.quality_protein_g == pytest.approx(17.495, abs=1e-3)
        assert after.plan is not None
        assert after.plan.quality_protein_g == pytest.approx(13.00, abs=1e-3)

    def test_disqualifying_both_sources_puts_south_breakfast_back_in_decline(self, real):
        # The stronger half of the same perturbation, and the one that keeps a
        # quality-named south decline covered by a test at all now that the real
        # library passes. Disqualify BOTH qualifying rows the template can reach
        # and the reachable figure is 0.0 g against 11.2 g.
        stripped = _with_diaas(
            _with_diaas(real, "curd_dahi", 0.50), "soya_chunks_dry", 0.50
        )
        outcome = _plan(stripped, Region.SOUTH_INDIAN, MealSlot.BREAKFAST)
        assert outcome.plan is None
        [v] = [v for v in outcome.result.violations if v.macro == "quality_protein_g"]
        assert v.actual == pytest.approx(0.0, abs=1e-9)
        assert v.bound == pytest.approx(_MEAL_QUALITY_FLOOR_G)

    def test_qualifying_tofu_hands_back_the_pre_slice_4_plate(self, real):
        # The sharpest available proof that the rule is what changed the answer.
        # Before slice 4 the reference north lunch was
        #   phulka x4 + dal_tadka x2 + tofu_bhurji x1
        # and it is now
        #   phulka x5 + soya_chunk_curry x1 + paneer_masala x1
        # solely because tofu_firm's authored 0.65 is below the threshold.
        # Raise that ONE number to 0.80 and the old plate comes back exactly.
        # Not an argument that 0.80 is right -- it is not, and the value is not
        # being changed -- but proof of what the rule is doing.
        after = _plan(
            _with_diaas(real, "tofu_firm", 0.80), Region.NORTH_INDIAN, MealSlot.LUNCH
        )
        assert after.plan is not None
        assert after.plan.unit_counts == {
            "phulka@roti": 4,
            "dal_tadka@dal": 2,
            "tofu_bhurji@sabzi": 1,
        }

    def test_the_rule_is_not_hard_coded_to_dairy(self, real):
        # docs/design/target_model_v2.md section 5's explicit requirement: the
        # quality rule must not assume qualifying sources are dairy, or every
        # non-vegetarian row added later needs the rule edited. soya_chunks_dry
        # is a plant row and it carries the entire vegan case, so disqualifying
        # it must change a verdict.
        stripped = _with_diaas(real, "soya_chunks_dry", 0.50)
        outcome = _plan(stripped, Region.NORTH_INDIAN, MealSlot.DINNER, DietPattern.VEGAN)
        assert outcome.plan is None
        assert any(v.macro == "quality_protein_g" for v in outcome.result.violations)


class TestDietChangesAnOutcomeNotANumber:
    """What slice 4 actually did to ``Profile.diet``, stated precisely.

    The queue expected slice 4 to make diet move a target value. It does not,
    and inventing a diet-conditional threshold to satisfy that expectation would
    be registering a constant to close a checklist item. The quality floor is a
    fraction of the day protein floor (weight and goal, not diet) and the
    threshold is a property of a food. Both stay diet-independent.

    What changed is downstream: diet decides which components can *satisfy* the
    floor, so two profiles with byte-identical targets can now get different
    plates and different verdicts. That is a real consequence and it is what
    these tests pin.
    """

    def test_every_target_number_is_still_diet_independent(self):
        targets = {diet: derive_target(_profile(diet)) for diet in DietPattern}
        assert len({t.nutrition_target.floor("protein_g") for t in targets.values()}) == 1
        assert len({round(t.carb_g, 6) for t in targets.values()}) == 1
        assert len({round(t.protein.quality_source_day_g, 6) for t in targets.values()}) == 1
        assert (
            len(
                {
                    meal_target(t.nutrition_target, MealSlot.LUNCH).quality_protein_floor()
                    for t in targets.values()
                }
            )
            == 1
        )

    def test_but_diet_now_decides_which_plate_satisfies_that_identical_floor(self, real):
        # Same body, same goal, same 11.2 g floor. A vegetarian's north dinner
        # can reach it through paneer or curd; a vegan's cannot, and rests
        # entirely on soya_chunk_curry. Different plates from identical numbers.
        veg = _plan(real, Region.NORTH_INDIAN, MealSlot.DINNER, DietPattern.VEGETARIAN)
        vegan = _plan(real, Region.NORTH_INDIAN, MealSlot.DINNER, DietPattern.VEGAN)
        assert veg.plan is not None and vegan.plan is not None
        assert veg.plan.unit_counts != vegan.plan.unit_counts

    def test_and_can_decide_the_verdict_itself(self, real):
        # The load-bearing version. With soya disqualified, the vegan library
        # has NO qualifying source at all while the vegetarian one still has
        # paneer and curd: identical targets, opposite verdicts. Before slice 4
        # diet could not do this, because nothing downstream of the candidate
        # filter cared which sources a plate's protein came from.
        stripped = _with_diaas(real, "soya_chunks_dry", 0.50)
        veg = _plan(stripped, Region.NORTH_INDIAN, MealSlot.LUNCH, DietPattern.VEGETARIAN)
        vegan = _plan(stripped, Region.NORTH_INDIAN, MealSlot.LUNCH, DietPattern.VEGAN)
        assert veg.plan is not None
        assert vegan.plan is None
        assert any(v.macro == "quality_protein_g" for v in vegan.result.violations)
