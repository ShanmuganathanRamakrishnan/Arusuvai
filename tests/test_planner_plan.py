"""End-to-end wiring: target -> per-meal split -> candidates -> ladder.

Two things are tested, deliberately kept apart so a failure in one cannot be
mistaken for the other:

1. **The real library, per template.** Every template now has a candidate in
   every required slot, so ``no_candidates`` must never appear for any of
   them: a decline has to name the macro that blocked it and show a walked
   relaxation ladder. See ``TestEveryTemplateIsPopulated``.

   This claim inverted on 2026-08-02 (T4). Until then three of the four
   templates had at least one required slot with no candidate at all and the
   test asserted the opposite — that they decline with ``no_candidates``,
   regardless of profile or ``dev_mode``. ``north_lunch`` left that group
   first, on 2026-07-31, when ``phulka`` filled ``grain_base``; six recipes
   closed the remaining gaps (``sambar``, ``coconut_chutney``,
   ``carrot_poriyal``, ``thayir_plain``, ``aloo_sabzi``, ``carrot_kootu``).

   The tests are deliberately about the *kind* of answer a template can give,
   not the numbers today's library happens to produce. Asserting current
   actuals would be a snapshot: it would go red on any recipe added and would
   not, on its own, say anything was wrong.
2. **The wiring itself, against a richer synthetic library.** If (1) were the
   *only* test, a bug in ``plan_meal``'s own wiring could hide behind "well,
   the library is thin anyway." ``TestHappyPathAgainstSyntheticLibrary`` reuses
   ``tests/factories.py``'s ``SOUTH_LUNCH`` fixture (already proven, in
   ``tests/test_planner_validator.py``, to produce a passing plan against a
   700 kcal/20 g-protein target) and drives it through the exact same
   ``plan_meal`` call, so a passing result here means the pipeline wiring is
   sound and today's decline in (1) is a fact about the data, not the code.
"""

from __future__ import annotations

import pytest

from core.foods.models import Component
from core.foods.recipe_loader import RecipeLibrary
from core.foods.templates import ALL_TEMPLATES
from core.nutrition.target import simple_target
from core.planner.candidates import build_candidate_pool
from core.planner.plan import Library, plan_meal
from core.schemas import ActivityLevel, DietPattern, Goal, MealSlot, Profile, Region, Sex
from tests.factories import (
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
)


def _real_library(ingredients, library: RecipeLibrary) -> Library:
    return Library(ingredients=ingredients, recipes=library)


class TestEveryTemplateIsPopulated:
    """No template may answer ``no_candidates`` any more. Proven per template.

    Parametrised over ``ALL_TEMPLATES`` rather than a hand-listed subset, so a
    template added later joins the *strong* claim by default and fails loudly
    until something fills its required slots. The previous version derived a
    weaker group by subtraction, which had the opposite bias: a new template
    would have silently joined the group that was allowed to have nothing.
    """

    @pytest.mark.parametrize(
        "template", ALL_TEMPLATES, ids=[t.id for t in ALL_TEMPLATES]
    )
    def test_every_required_slot_has_a_candidate(
        self, template, ingredients, library
    ):
        # The structural claim, checked directly rather than inferred from a
        # verdict: a decline for any other reason would otherwise hide an
        # empty slot behind a macro violation.
        pool = build_candidate_pool(
            library.components.values(),
            ingredients,
            template=template,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )
        empty = [s.name for s in template.required_slots if not pool.for_slot(s)]
        assert empty == [], f"{template.id}: required slots with no candidate: {empty}"

    @pytest.mark.parametrize(
        "template", ALL_TEMPLATES, ids=[t.id for t in ALL_TEMPLATES]
    )
    def test_no_candidates_never_appears(self, template, ingredients, library):
        # A deliberately loose day target. Whether the template passes or
        # declines against it is a fact about the data and this test takes no
        # position on it -- that part moves as recipes land. What may not
        # happen is the empty-pool shortcut.
        day_target = simple_target(energy_kcal=2000.0, protein_g_min=10.0)

        outcome = plan_meal(
            _real_library(ingredients, library),
            day_target,
            region=template.region,
            meal_slot=template.meal_slot,
            diet_pattern=DietPattern.VEGETARIAN,
        )

        assert all(v.kind != "no_candidates" for v in outcome.result.violations)
        assert "nothing to solve" not in (outcome.result.disclosure or "")


class TestNorthLunchIsPopulated:
    """north_lunch has a candidate in every required slot, so it never declines
    for want of one.

    This is the claim that changed on 2026-07-31, and it is deliberately a
    claim about the *kind* of answer the template can give, not about the
    numbers today's three-recipe library happens to produce. Asserting the
    current actuals would be a snapshot: it would go red on any recipe added
    to this template and would not, on its own, say anything was wrong.
    """

    def _lib(self, ingredients, library) -> Library:
        return _real_library(ingredients, library)

    def test_no_candidates_never_appears_whatever_the_verdict(
        self, ingredients, library
    ):
        # The durable invariant: with every required slot populated, the
        # solver always has something to hand the validator. Whether it then
        # passes or declines is a fact about the target, and this test takes
        # no position on it -- deliberately, because that is exactly the part
        # that moves as recipes land.
        day_target = simple_target(energy_kcal=2000.0, protein_g_min=10.0)
        outcome = plan_meal(
            self._lib(ingredients, library),
            day_target,
            region=Region.NORTH_INDIAN,
            meal_slot=MealSlot.LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
        )

        assert all(v.kind != "no_candidates" for v in outcome.result.violations)

    def test_an_unreachable_target_declines_on_a_named_macro_and_the_full_ladder(
        self, ingredients, library
    ):
        # A protein floor no combination of breads and legume dishes in this
        # library can reach at a lunch-sized portion. The decline must name
        # protein_g with an actual and a bound, and must have walked all four
        # rungs to get there -- i.e. it is a real relaxation failure, not the
        # empty-pool shortcut that used to be this template's only answer.
        day_target = simple_target(energy_kcal=2000.0, protein_g_min=500.0 / 0.35)
        outcome = plan_meal(
            self._lib(ingredients, library),
            day_target,
            region=Region.NORTH_INDIAN,
            meal_slot=MealSlot.LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
        )

        assert outcome.plan is None
        assert outcome.result.passed is False
        assert outcome.result.violations != ()
        assert all(v.kind != "no_candidates" for v in outcome.result.violations)
        assert outcome.result.relaxation_applied == (
            "sodium_max_fibre_min",
            "fat_carb_tolerance",
            "energy_tolerance",
            "protein_tolerance",
        )

        protein = [v for v in outcome.result.violations if v.macro == "protein_g"]
        assert protein, "the blocking macro must be named, not left generic"
        (shortfall,) = protein
        assert shortfall.kind == "below_floor"
        # Named with real quantities on both sides, whatever they are today.
        assert shortfall.actual < shortfall.bound

        disclosure = outcome.result.disclosure or ""
        assert "No plan could be built for this profile" in disclosure
        assert "protein_g" in disclosure
        assert "nothing to solve" not in disclosure

    def test_dev_mode_false_empties_the_pool_on_uncertainty_alone(
        self, ingredients, library
    ):
        # Renamed and inverted on 2026-08-02, because the old version --
        # "dev_mode does not change the verdict" -- passed for two different
        # reasons at once and could no longer tell them apart. Before T4 both
        # settings answered `no_candidates`: dev_mode=True because south_lunch
        # had unfilled required slots, dev_mode=False because the eligibility
        # filter emptied the pool. One assertion, two causes, and filling the
        # slots was always going to break it without saying which had moved.
        #
        # Now the two are separable and each is asserted on its own. Every
        # ingredient row bar `water` is verified=False, so every recipe carries
        # a 0.25 protein band against a 0.15 ceiling: dev_mode=False must empty
        # the pool for a protein-critical target, and dev_mode=True must not.
        # This is the documented behaviour in core/planner/candidates.py, and
        # it is the reason nothing in this library can ship as validated.
        lib = _real_library(ingredients, library)
        day_target = simple_target(energy_kcal=2000.0, protein_g_min=10.0)

        def _violations(dev_mode: bool):
            return plan_meal(
                lib,
                day_target,
                region=Region.SOUTH_INDIAN,
                meal_slot=MealSlot.LUNCH,
                diet_pattern=DietPattern.VEGETARIAN,
                dev_mode=dev_mode,
            ).result.violations

        strict = _violations(False)
        assert [v.kind for v in strict] == ["no_candidates"], (
            "dev_mode=False must empty the pool: every recipe is over the "
            "eligibility ceiling on protein"
        )
        assert all(v.kind != "no_candidates" for v in _violations(True)), (
            "dev_mode=True suspends eligibility, and every required slot is "
            "populated, so there is always something to solve"
        )

    def test_a_realistic_onboarding_profile_gets_a_specific_answer(
        self, ingredients, library
    ):
        # The exact shape of profile the onboarding page now collects end to
        # end: derive_target's real output, not a hand-built loose target.
        from core.nutrition.targets import derive_target

        profile = Profile(
            weight_kg=55.0,
            height_cm=160.0,
            age_years=30,
            sex=Sex.FEMALE,
            activity=ActivityLevel.LIGHT,
            goal=Goal.MAINTAIN,
            diet=DietPattern.VEGETARIAN,
        )
        dt = derive_target(profile)
        lib = _real_library(ingredients, library)

        outcome = plan_meal(
            lib,
            dt.nutrition_target,
            region=Region.SOUTH_INDIAN,
            meal_slot=MealSlot.LUNCH,
            diet_pattern=profile.diet,
            profile=profile,
        )

        # No position taken on the verdict -- that is a fact about the data and
        # it moved once already, on 2026-08-02, when six recipes turned this
        # profile's answer from "nothing to solve" into a real plate. What must
        # hold either way: the answer is specific. A plan names its components,
        # a decline names the macro that blocked it. "It ran" is not "it ran
        # correctly", and the empty-pool shortcut is neither.
        assert all(v.kind != "no_candidates" for v in outcome.result.violations)

        if outcome.plan is None:
            assert outcome.result.passed is False
            assert outcome.result.violations != ()
            disclosure = outcome.result.disclosure or ""
            assert "No plan could be built for this profile" in disclosure
            assert "nothing to solve" not in disclosure
            named = {v.macro for v in outcome.result.violations}
            assert named, "a decline must name the macro that blocked it"
        else:
            assert outcome.result.passed is True
            assert outcome.plan.unit_counts
            assert all(n >= 1 for n in outcome.plan.unit_counts.values())


class TestHappyPathAgainstSyntheticLibrary:
    """Proves plan_meal's own wiring, independent of today's thin real data."""

    def _synthetic_library(self) -> Library:
        components = {c.id: c for c in SOUTH_LUNCH_COMPONENTS}
        return Library(
            ingredients=SOUTH_LUNCH_INGREDIENTS,
            recipes=RecipeLibrary(recipes={}, components=components),
        )

    def test_a_reachable_target_produces_a_passing_plan(self):
        # tests/test_planner_validator.py::TestLadderFires already proves
        # simple_target(energy_kcal=700.0, protein_g_min=20.0) passes against
        # this exact pool with zero relaxation. plan_meal always scales a DAY
        # target down by MealSlot's registered fraction before solving
        # (core/nutrition/meal_target.py) -- lunch is x0.35 -- so the day
        # target that lands on that exact known-good meal target is
        # 700 / 0.35 = 2000 kcal, 20 / 0.35 = 57.142857... g protein.
        day_target = simple_target(
            energy_kcal=2000.0, protein_g_min=20.0 / 0.35
        )
        lib = self._synthetic_library()

        outcome = plan_meal(
            lib,
            day_target,
            region=Region.SOUTH_INDIAN,
            meal_slot=MealSlot.LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=False,  # factories.py: tight/verified data clears both
            # eligibility ceilings even with dev_mode off.
        )

        assert outcome.plan is not None
        assert outcome.result.passed is True
        assert outcome.result.violations == ()
        assert outcome.result.relaxation_applied == ()
        # The plan actually solved against the *scaled* target, not the day
        # target: 700 kcal +/- 5% -> [665, 735].
        assert 665.0 <= outcome.plan.estimate.point.energy_kcal <= 735.0
        assert outcome.plan.estimate.point.protein_g >= 20.0

    def test_an_unreachable_target_still_declines_specifically(self):
        # 33.0 g is the pool's own documented max reachable protein
        # (tests/factories.py, SOUTH_LUNCH_MAX_PROTEIN_G). A day target whose
        # scaled-down lunch floor (200 g) is far past that even after every
        # ladder rung fires -- including a 15%-lowered protein floor -- must
        # still decline, all four rungs tried, naming protein_g specifically
        # rather than a generic failure. Proves the wiring reaches the
        # ladder's last rung, not just its first.
        day_target = simple_target(energy_kcal=2000.0, protein_g_min=200.0 / 0.35)
        lib = self._synthetic_library()

        outcome = plan_meal(
            lib,
            day_target,
            region=Region.SOUTH_INDIAN,
            meal_slot=MealSlot.LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=False,
        )

        assert outcome.plan is None
        assert outcome.result.passed is False
        assert outcome.result.relaxation_applied == (
            "sodium_max_fibre_min",
            "fat_carb_tolerance",
            "energy_tolerance",
            "protein_tolerance",
        )
        assert any(v.macro == "protein_g" for v in outcome.result.violations)
        assert "No plan could be built for this profile" in (
            outcome.result.disclosure or ""
        )
        assert "protein_g" in (outcome.result.disclosure or "")
