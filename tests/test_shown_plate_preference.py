"""An egg or non-veg eater is shown a plate with egg, fish or chicken when one is valid.

Owner report 2026-09-27: a non-vegetarian was shown soya at every dinner,
although valid egg plates existed -- the ladder returned the nearest plate and
the nearest was always soya (docs/audit_log.md 2026-09-27, shown plate for egg
and non-veg). ``plan_within_ladder``'s ``prefer`` chooses among the plates
already valid at the accepted rung; ``plan_meal`` supplies one for any diet
that permits an animal-protein class.

The ladder tests use ``tests/factories.py``'s synthetic South lunch, so which
plate is preferred is decided by a predicate the test picks, not by whatever
the real library happens to contain.
"""

from __future__ import annotations

from core.foods import templates
from core.nutrition.target import simple_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool, recipe_classes
from core.planner.combinations import enumerate_combinations, feasible_combinations
from core.planner.plan import (
    ANIMAL_PROTEIN_CLASSES,
    _animal_protein_preference,
    default_library,
    plan_meal,
)
from core.planner.solver import solve
from core.planner.validator import _repeated_mains, plan_within_ladder
from core.schemas import (
    ActivityLevel,
    DietPattern,
    Goal,
    IngredientClass,
    MealSlot,
    Profile,
    Region,
    Sex,
)
from tests.factories import SOUTH_LUNCH_COMPONENTS, SOUTH_LUNCH_INGREDIENTS

ING = SOUTH_LUNCH_INGREDIENTS


def _combos():
    return enumerate_combinations(
        build_candidate_pool(
            SOUTH_LUNCH_COMPONENTS, ING,
            template=templates.SOUTH_LUNCH, diet_pattern=DietPattern.VEGETARIAN,
        )
    )


def _ids(plan):
    return {c.recipe.id for c in plan.combination.components}


# The same target TestLadderFires uses for "already feasible": passes at rung 0.
FEASIBLE = simple_target(energy_kcal=700.0, protein_g_min=20.0)


def _solved(target):
    return solve(feasible_combinations(_combos(), target, ING), target, ING)


class TestPreferChoosesAmongValidPlates:
    def test_the_fixture_has_a_valid_plate_that_is_not_the_nearest(self):
        # Precondition: with only one valid plate every test below would pass
        # whether or not `prefer` did anything.
        solved = _solved(FEASIBLE)
        assert len(solved) >= 2
        assert _ids(solved[0]) != _ids(solved[1])

    def test_without_a_preference_the_nearest_plate_is_shown(self):
        outcome = plan_within_ladder(_combos(), FEASIBLE, ING)
        assert _ids(outcome.plan) == _ids(_solved(FEASIBLE)[0])

    def test_the_nearest_preferred_plate_is_shown_over_a_nearer_one(self):
        solved = _solved(FEASIBLE)
        nearest = _ids(solved[0])
        # A recipe the nearest plate lacks but some other valid plate has.
        wanted = next(r for p in solved[1:] for r in _ids(p) if r not in nearest)
        expected = next(p for p in solved if wanted in _ids(p))

        outcome = plan_within_ladder(
            _combos(), FEASIBLE, ING, prefer=lambda p: wanted in _ids(p)
        )
        assert _ids(outcome.plan) == _ids(expected) != nearest
        assert outcome.plan.unit_counts == expected.unit_counts
        assert outcome.result.passed

    def test_a_preference_nothing_satisfies_falls_back_to_the_nearest(self):
        outcome = plan_within_ladder(_combos(), FEASIBLE, ING, prefer=lambda p: False)
        assert _ids(outcome.plan) == _ids(_solved(FEASIBLE)[0])

    def test_a_preference_never_moves_the_ladder_to_a_later_rung(self):
        # TestLadderFires' sodium case: nothing valid until rung 1. A
        # preference nothing satisfies must not push the ladder on looking
        # for one -- the rung and the target stay what they were.
        target = simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)
        plain = plan_within_ladder(_combos(), target, ING)
        preferring = plan_within_ladder(_combos(), target, ING, prefer=lambda p: False)
        assert plain.result.relaxation_applied == ("sodium_max_fibre_min",)
        assert preferring.result.relaxation_applied == plain.result.relaxation_applied
        assert preferring.target_used == plain.target_used

    def test_the_preference_also_applies_on_a_relaxed_rung(self):
        target = simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0)
        plain = plan_within_ladder(_combos(), target, ING)
        solved = solve(
            feasible_combinations(_combos(), plain.target_used, ING), plain.target_used, ING
        )
        nearest = _ids(solved[0])
        wanted = next(r for p in solved[1:] for r in _ids(p) if r not in nearest)
        outcome = plan_within_ladder(
            _combos(), target, ING, prefer=lambda p: wanted in _ids(p)
        )
        assert wanted in _ids(outcome.plan)
        assert outcome.result.relaxation_applied == ("sodium_max_fibre_min",)


class TestWhichDietsPrefer:
    def test_diets_without_an_animal_protein_class_have_no_preference(self):
        for diet in (DietPattern.VEGETARIAN, DietPattern.VEGAN, DietPattern.JAIN):
            assert _animal_protein_preference(diet, ING) is None, diet

    def test_the_animal_protein_classes_are_egg_fish_and_poultry(self):
        assert ANIMAL_PROTEIN_CLASSES == {
            IngredientClass.EGG, IngredientClass.FISH, IngredientClass.POULTRY,
        }

    def test_egg_and_non_veg_diets_have_one(self):
        for diet in (DietPattern.EGGETARIAN, DietPattern.PESCATARIAN,
                     DietPattern.NON_VEGETARIAN):
            assert _animal_protein_preference(diet, ING) is not None, diet


class TestTheRealDinner:
    """Wiring, not coverage: pins the owner's reported case on the real library.

    Breaks if the library changes so that no valid North dinner has an egg
    dish for this body; the tests above are the ones about the mechanism.
    """

    def _profile(self, diet):
        return Profile(
            weight_kg=70.0, height_cm=175.0, age_years=28, sex=Sex.MALE,
            activity=ActivityLevel.MODERATE, goal=Goal.MAINTAIN, diet=diet,
        )

    def _shown(self, diet):
        p = self._profile(diet)
        lib = default_library()
        outcome = plan_meal(
            lib, derive_target(p).nutrition_target, region=Region.NORTH_INDIAN,
            meal_slot=MealSlot.DINNER, diet_pattern=diet, profile=p,
        )
        return outcome, lib

    def test_a_non_vegetarian_north_dinner_shows_an_animal_protein_dish(self):
        outcome, lib = self._shown(DietPattern.NON_VEGETARIAN)
        assert outcome.result.passed
        assert any(
            recipe_classes(c.recipe, lib.ingredients) & ANIMAL_PROTEIN_CLASSES
            for c in outcome.plan.combination.components
        ), _ids(outcome.plan)

    def test_a_vegetarian_north_dinner_is_the_nearest_plate_with_fewest_repeats(self):
        # No animal-protein preference for a vegetarian. Since N14
        # (2026-10-08) the shown plate is the nearest of those serving a main
        # ingredient in the fewest dishes -- no longer simply the nearest,
        # which put soya_onion_raita beside soya_chunk_masala.
        outcome, lib = self._shown(DietPattern.VEGETARIAN)

        combos = enumerate_combinations(build_candidate_pool(
            lib.components(), lib.ingredients,
            template=templates.template_for(Region.NORTH_INDIAN, MealSlot.DINNER),
            diet_pattern=DietPattern.VEGETARIAN, dev_mode=True,
        ))
        solved = solve(
            feasible_combinations(combos, outcome.target_used, lib.ingredients),
            outcome.target_used, lib.ingredients,
        )
        fewest = min(_repeated_mains(p) for p in solved)
        expected = next(p for p in solved if _repeated_mains(p) == fewest)
        assert _ids(outcome.plan) == _ids(expected)
