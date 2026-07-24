"""End-to-end wiring: target -> per-meal split -> candidates -> ladder.

Two things are tested, deliberately kept apart so a failure in one cannot be
mistaken for the other:

1. **The real library, every template.** ``data/recipes/`` has one recipe per
   category and, per ``core/planner/plan.py``'s module docstring, no template
   has candidates for its *other* required slots. Every real template must
   therefore decline with a ``no_candidates`` violation, regardless of the
   profile asking or of ``dev_mode``. This is the thin-library case the
   product will hit almost by default with today's data, and the point of
   this test is to confirm the decline is specific and correct — not merely
   that the call doesn't crash.
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
from core.planner.plan import Library, plan_meal
from core.schemas import ActivityLevel, DietPattern, Goal, MealSlot, Profile, Region, Sex
from tests.factories import (
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
)


def _real_library(ingredients, library: RecipeLibrary) -> Library:
    return Library(ingredients=ingredients, recipes=library)


class TestRealLibraryDeclinesEveryTemplate:
    """The thin-library case: proven for all four templates, not asserted."""

    @pytest.mark.parametrize(
        "template",
        ALL_TEMPLATES,
        ids=[t.id for t in ALL_TEMPLATES],
    )
    def test_declines_with_a_specific_no_candidates_violation(
        self, template, ingredients, library
    ):
        lib = _real_library(ingredients, library)
        # A deliberately loose day target: if this template declined because
        # the target was hard to hit, a loose target like this would still
        # pass. It doesn't, for any of the four — confirming the decline is
        # about missing candidates, not about target tightness.
        day_target = simple_target(energy_kcal=2000.0, protein_g_min=10.0)

        outcome = plan_meal(
            lib,
            day_target,
            region=template.region,
            meal_slot=template.meal_slot,
            diet_pattern=DietPattern.VEGETARIAN,
        )

        assert outcome.plan is None
        assert outcome.result.passed is False
        assert len(outcome.result.violations) == 1
        (violation,) = outcome.result.violations
        assert violation.kind == "no_candidates"
        assert "nothing to solve" in violation.describe()
        assert outcome.result.disclosure is not None
        assert "No plan could be built for this profile" in outcome.result.disclosure
        assert "nothing to solve" in outcome.result.disclosure

    def test_dev_mode_does_not_change_the_verdict(self, ingredients, library):
        # dev_mode only suspends the *eligibility* filter (uncertainty too
        # wide); it cannot manufacture a candidate for a category the library
        # never populated at all. Checked explicitly so "just flip dev_mode"
        # is never mistaken for a fix to this specific decline.
        lib = _real_library(ingredients, library)
        day_target = simple_target(energy_kcal=2000.0, protein_g_min=10.0)
        for dev_mode in (True, False):
            outcome = plan_meal(
                lib,
                day_target,
                region=Region.SOUTH_INDIAN,
                meal_slot=MealSlot.LUNCH,
                diet_pattern=DietPattern.VEGETARIAN,
                dev_mode=dev_mode,
            )
            assert outcome.result.passed is False
            (violation,) = outcome.result.violations
            assert violation.kind == "no_candidates"

    def test_a_realistic_onboarding_profile_still_declines(self, ingredients, library):
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

        assert outcome.result.passed is False
        (violation,) = outcome.result.violations
        assert violation.kind == "no_candidates"
        # "it ran" is not "it ran correctly": the disclosure must actually
        # name the reason, not just be present.
        assert outcome.result.disclosure == (
            "No plan could be built for this profile: no recipe combination "
            "survived filtering for this profile, so there was nothing to solve"
        )


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
