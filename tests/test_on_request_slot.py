"""An on-request course: offered, never served by default.

TASKS_3.md N19 (owner 2026-10-08): sundal is the ordinary South Indian
evening snack and is eaten alone; an egg is not a snack on its own, but some
people have one beside the sundal. So the South snack has an `egg_side`
course the planner leaves empty unless the user adds an egg to it
(docs/audit_log.md 2026-10-08, "N19").

The real-library tests use the eggetarian body for which, with the course
NOT held back, the nearest valid plate the planner shows is soya chunk
sundal + avicha muttai (measured in the audit entry). Holding it back is the
only thing between that body and an egg on its default snack.
"""

from __future__ import annotations

import pytest

from core.foods.models import TemplateSlot
from core.nutrition.targets import derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex


def _snack(diet, picks=frozenset()):
    p = Profile(
        weight_kg=70.0, height_cm=170.0, age_years=30, sex=Sex.MALE,
        activity=ActivityLevel.MODERATE, goal=Goal.MAINTAIN, diet=diet,
        clinical_flags=frozenset(),
    )
    return plan_meal(
        default_library(), derive_target(p).nutrition_target,
        region=Region.SOUTH_INDIAN, meal_slot=MealSlot.SNACK,
        diet_pattern=diet, profile=p, picks=frozenset(picks),
    )


def _categories(outcome):
    return {c.category for c in outcome.plan.combination.components}


def _options(outcome, slot):
    return dict(outcome.swap_options).get(slot, ())


def test_a_required_slot_cannot_be_on_request():
    with pytest.raises(ValueError, match="cannot wait to be requested"):
        TemplateSlot(name="main", accepted_categories=frozenset({"x"}), on_request=True)


def test_by_default_the_snack_holds_no_egg():
    outcome = _snack(DietPattern.EGGETARIAN)
    assert outcome.result.passed
    assert "egg" not in _categories(outcome)
    assert "sundal" in _categories(outcome)


def test_the_egg_side_is_still_offered():
    outcome = _snack(DietPattern.EGGETARIAN)
    assert "avicha_muttai" in _options(outcome, "egg_side")


def test_asking_for_an_egg_puts_it_beside_the_sundal():
    outcome = _snack(DietPattern.EGGETARIAN, picks={"avicha_muttai"})
    assert outcome.result.passed
    ids = {c.recipe.id for c in outcome.plan.combination.components}
    assert "avicha_muttai" in ids
    assert "sundal" in _categories(outcome)


def test_a_vegetarian_is_offered_no_egg():
    outcome = _snack(DietPattern.VEGETARIAN)
    assert outcome.result.passed
    assert _options(outcome, "egg_side") == ()
