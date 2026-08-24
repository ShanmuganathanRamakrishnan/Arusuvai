"""D4 / findings 24 and 26: a decline names every blocking cause, and the right
ones.

Built on ``tests/factories.py``'s FEASIBILITY fixture, where every serving unit
is pinned to ``min=max=1``, so each of the four combinations is one exact point
and no expected value below is an envelope:

    a1 = 100 kcal,  5 g protein,  500 mg sodium
    a2 = 200 kcal, 10 g protein,  100 mg sodium
    b1 =  50 kcal,  2 g protein, 1000 mg sodium
    b2 = 150 kcal,  8 g protein,   50 mg sodium

    a1+b1 = 150 kcal,  7 g, 1500 mg
    a1+b2 = 250 kcal, 13 g,  550 mg
    a2+b1 = 250 kcal, 12 g, 1100 mg
    a2+b2 = 350 kcal, 18 g,  150 mg

Enumeration order is (a1,b1), (a1,b2), (a2,b1), (a2,b2): candidates sort by
component id (``CandidatePool.for_slot``) and ``itertools.product`` varies the
last slot fastest. That order matters to one test below, which pins the defect
these replaced rather than only the behaviour that replaced it.
"""

from __future__ import annotations

import pytest

from core.foods import templates
from core.foods.models import MealTemplate, TemplateSlot
from core.foods.quality import QUALITY_PROTEIN_KEY
from core.nutrition.target import NutritionTarget, simple_target
from core.nutrition.targets import derive_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations, unfillable_slots
from core.planner.plan import load_library, plan_meal
from core.planner.validator import (
    RELAXATION_ORDER,
    VIOLATION_REACH,
    VIOLATION_RELAXABILITY,
    Violation,
    plan_within_ladder,
)
from core.schemas import (
    ActivityLevel,
    ClinicalFlag,
    DietPattern,
    Goal,
    MealSlot,
    Profile,
    Region,
    Sex,
)
from tests.factories import (
    FEASIBILITY_COMPONENTS,
    FEASIBILITY_INGREDIENTS,
    FEASIBILITY_TEMPLATE,
    SOUTH_LUNCH_COMPONENTS,
    SOUTH_LUNCH_INGREDIENTS,
)


def _profile(*flags: ClinicalFlag) -> Profile:
    return Profile(
        weight_kg=55.0,
        height_cm=160.0,
        age_years=30,
        sex=Sex.FEMALE,
        activity=ActivityLevel.LIGHT,
        goal=Goal.MAINTAIN,
        diet=DietPattern.VEGETARIAN,
        clinical_flags=frozenset(flags),
    )


def _combos():
    return enumerate_combinations(
        build_candidate_pool(
            FEASIBILITY_COMPONENTS,
            FEASIBILITY_INGREDIENTS,
            template=FEASIBILITY_TEMPLATE,
            diet_pattern=DietPattern.VEGETARIAN,
        )
    )


#: protein floor 14, energy ceiling 300, sodium ceiling 500. Every bound is
#: reachable on its own -- protein tops out at 18, energy bottoms out at 150,
#: sodium bottoms out at 150 -- and no single combination meets all three:
#:
#:     a1+b1  protein 7 short, sodium 1500 over   -> breaks 2
#:     a1+b2  protein 13 short, sodium 550 over   -> breaks 2
#:     a2+b1  protein 12 short, sodium 1100 over  -> breaks 2
#:     a2+b2  energy 350 over                     -> breaks 1
#:
#: ``points`` is empty on purpose: with no ideal point registered, rungs 2-4 are
#: no-ops, and pairing this target with a hypertensive profile makes rung 1 skip
#: sodium as well. The ladder therefore walks all four rungs and changes
#: nothing, so the target a decline is computed against is exactly this one.
_JOINT = dict(
    floors={"protein_g": 14.0},
    ceilings={"energy_kcal": 300.0, "sodium_mg": 500.0},
    points={},
)


def _joint_outcome(**extra):
    return plan_within_ladder(
        _combos(),
        NutritionTarget(**_JOINT, **extra),
        FEASIBILITY_INGREDIENTS,
        profile=_profile(ClinicalFlag.HYPERTENSION),
    )


class TestTheLadderIsInertOnThisTarget:
    def test_all_four_rungs_fire_and_the_target_does_not_move(self):
        # Every assertion in this file about "the target the decline was
        # computed against" rests on this. Checked rather than asserted in a
        # comment, because a rung gaining an effect later would quietly
        # invalidate every hand-computed figure above.
        outcome = _joint_outcome()
        assert outcome.result.relaxation_applied == tuple(
            s.name for s in RELAXATION_ORDER
        )
        used = outcome.target_used
        assert used.floor("protein_g") == pytest.approx(14.0)
        assert used.ceiling("energy_kcal") == pytest.approx(300.0)
        assert used.ceiling("sodium_mg") == pytest.approx(500.0)


class TestADeclineNamesEveryBlockingCause:
    def test_the_nearest_plate_is_the_one_breaking_fewest_bounds(self):
        outcome = _joint_outcome()
        assert outcome.plan is None
        # a2+b2 breaks one bound; the decline is about that plate and no other.
        assert {v.macro for v in outcome.result.violations} == {"energy_kcal"}
        (violation,) = outcome.result.violations
        assert violation.kind == "above_ceiling"
        assert violation.actual == pytest.approx(350.0)
        assert violation.bound == pytest.approx(300.0)
        assert violation.reach == "jointly_infeasible"

    def test_it_does_not_report_the_first_enumerated_plate_instead(self):
        # The defect this replaced, as its own assertion, so deleting the
        # (len(violations), score) ranking in `_nearest_plate_violations` turns
        # this red rather than merely changing a number elsewhere. Ranking by
        # score alone ties across all four combinations here -- no macro has a
        # registered point, so every deviation score is 0.0 -- and the tie
        # resolves to the first enumerated combination, a1+b1, which breaks
        # protein and sodium. Both are bounds the actually-nearest plate meets.
        named = {v.macro for v in _joint_outcome().result.violations}
        assert "protein_g" not in named
        assert "sodium_mg" not in named

    def test_an_unreachable_bound_no_longer_hides_the_reachable_ones(self):
        # Finding 24's mirror. From slice 4 until 2026-08-08 an unreachable
        # quality floor returned early and every other blocking bound went
        # unsaid. No FEASIBILITY ingredient carries a DIAAS, so 0 g of
        # qualifying protein is reachable against this 5 g floor.
        outcome = _joint_outcome(quality_protein_floor_g=5.0)
        by_macro = {v.macro: v for v in outcome.result.violations}
        assert set(by_macro) == {QUALITY_PROTEIN_KEY, "energy_kcal"}, (
            "the quality floor and the energy ceiling are both blocking; "
            "reporting only one of them is the defect"
        )
        assert by_macro[QUALITY_PROTEIN_KEY].reach == "unreachable"
        assert by_macro[QUALITY_PROTEIN_KEY].actual == pytest.approx(0.0)
        assert by_macro["energy_kcal"].reach == "jointly_infeasible"

    def test_a_bound_is_never_reported_twice_under_both_reaches(self):
        outcome = _joint_outcome(quality_protein_floor_g=5.0)
        keys = [(v.macro, v.kind) for v in outcome.result.violations]
        assert len(keys) == len(set(keys))

    def test_an_unreachable_bound_is_labelled_unreachable_not_joint(self):
        # protein floor 40 is above 18, the most any combination can reach.
        outcome = plan_within_ladder(
            _combos(),
            NutritionTarget(floors={"protein_g": 40.0}, points={}),
            FEASIBILITY_INGREDIENTS,
            profile=_profile(),
        )
        (violation,) = outcome.result.violations
        assert violation.macro == "protein_g"
        assert violation.reach == "unreachable"
        assert violation.actual == pytest.approx(18.0)

    def test_every_reported_reach_is_a_registered_token(self):
        outcome = _joint_outcome(quality_protein_floor_g=5.0)
        for violation in outcome.result.violations:
            assert violation.reach in VIOLATION_REACH
            assert violation.relaxability in VIOLATION_RELAXABILITY


class TestRelaxabilityIsDerivedFromTheLadderItself:
    def test_a_locked_bound_says_locked(self):
        outcome = plan_within_ladder(
            enumerate_combinations(
                build_candidate_pool(
                    SOUTH_LUNCH_COMPONENTS,
                    SOUTH_LUNCH_INGREDIENTS,
                    template=templates.SOUTH_LUNCH,
                    diet_pattern=DietPattern.VEGETARIAN,
                )
            ),
            simple_target(energy_kcal=600.0, protein_g_min=15.0, sodium_mg_max=500.0),
            SOUTH_LUNCH_INGREDIENTS,
            profile=_profile(ClinicalFlag.HYPERTENSION),
        )
        sodium = [v for v in outcome.result.violations if v.macro == "sodium_mg"]
        assert sodium and sodium[0].relaxability == "locked"

    def test_the_quality_floor_says_never_relaxed(self):
        outcome = _joint_outcome(quality_protein_floor_g=5.0)
        quality = [
            v for v in outcome.result.violations if v.macro == QUALITY_PROTEIN_KEY
        ]
        assert quality and quality[0].relaxability == "never_relaxed"

    def test_a_bound_a_rung_touched_and_could_not_save_says_relaxed_to_limit(self):
        outcome = _joint_outcome()
        (violation,) = outcome.result.violations
        assert violation.macro == "energy_kcal"
        assert "energy_tolerance" in outcome.result.relaxation_applied
        assert violation.relaxability == "relaxed_to_limit"

    def test_a_ceiling_sitting_on_its_hard_ceiling_says_hard_capped(self):
        # The sodium guard's shape: a ceiling a rung is free to widen, clipped
        # by a hard ceiling it may not pass. Nothing further is on offer however
        # many rungs remain, and that is a different answer from
        # "relaxed_to_limit" -- one says the ladder ran out, the other says the
        # ladder was never going to move this bound at all.
        outcome = plan_within_ladder(
            _combos(),
            NutritionTarget(
                floors={"protein_g": 14.0},
                ceilings={"sodium_mg": 120.0},
                hard_ceilings={"sodium_mg": 120.0},
                points={},
            ),
            FEASIBILITY_INGREDIENTS,
            profile=_profile(),
        )
        sodium = [v for v in outcome.result.violations if v.macro == "sodium_mg"]
        assert sodium, "sodium blocks: the least salty plate carries 150 mg"
        assert sodium[0].relaxability == "hard_capped"
        # And the guard really did hold: rung 1 fired and the ceiling stayed put.
        assert "sodium_max_fibre_min" in outcome.result.relaxation_applied
        assert outcome.target_used.ceiling("sodium_mg") == pytest.approx(120.0)

    def test_the_quality_floor_is_absent_from_every_rung(self):
        # Why "never_relaxed" is derivable rather than special-cased. Asserted
        # against RELAXATION_ORDER so a rung added later cannot leave a stale
        # classification behind.
        laddered = {m for step in RELAXATION_ORDER for m in step.macros}
        assert laddered == {
            "sodium_mg", "fibre_g", "fat_g", "carb_g", "energy_kcal", "protein_g",
        }
        assert QUALITY_PROTEIN_KEY not in laddered


class TestAnEmptyPoolNamesTheCourseThatIsMissing:
    def test_the_unfillable_slot_is_identified(self):
        pool = build_candidate_pool(
            FEASIBILITY_COMPONENTS,
            FEASIBILITY_INGREDIENTS,
            template=FEASIBILITY_TEMPLATE,
            diet_pattern=DietPattern.VEGAN,
        )
        # Every FEASIBILITY recipe is both vegetarian and vegan, so nothing is
        # filtered: the pool fills and no slot is unfillable. Stated as the
        # control for the two tests below.
        assert unfillable_slots(pool) == ()

    def test_a_slot_with_candidates_but_no_legal_selection_still_counts(self):
        # The case `not pool.for_slot(slot)` would miss, and the reason
        # `unfillable_slots` calls the enumerator's own helper: slot "a" has two
        # candidates and demands three, so it has candidates AND no legal
        # selection. Enumeration returns () and the obvious implementation would
        # name nothing.
        greedy = MealTemplate(
            id="test_greedy_slot",
            region=FEASIBILITY_TEMPLATE.region,
            meal_slot=FEASIBILITY_TEMPLATE.meal_slot,
            slots=(
                TemplateSlot(
                    name="a",
                    accepted_categories=frozenset({"cat_a"}),
                    min_selections=3,
                    max_selections=3,
                ),
            ),
        )
        pool = build_candidate_pool(
            FEASIBILITY_COMPONENTS,
            FEASIBILITY_INGREDIENTS,
            template=greedy,
            diet_pattern=DietPattern.VEGETARIAN,
        )
        assert len(pool.for_slot(greedy.slots[0])) == 2
        assert enumerate_combinations(pool) == ()
        assert unfillable_slots(pool) == ("a",)

    def test_the_decline_reports_the_slots_it_was_given(self):
        outcome = plan_within_ladder(
            (),
            simple_target(energy_kcal=700.0, protein_g_min=15.0),
            FEASIBILITY_INGREDIENTS,
            empty_required_slots=("curd_course",),
        )
        (violation,) = outcome.result.violations
        assert violation.kind == "no_candidates"
        assert violation.reach == "empty_pool"
        assert violation.blocking_slots == ("curd_course",)
        assert "1 required course" in violation.describe()
        # The slot name is an identifier and must not reach the sentence.
        assert "curd_course" not in violation.describe()
        assert "curd_course" not in (outcome.result.disclosure or "")

    def test_a_caller_that_supplies_no_slots_still_declines_honestly(self):
        outcome = plan_within_ladder(
            (),
            simple_target(energy_kcal=700.0, protein_g_min=15.0),
            FEASIBILITY_INGREDIENTS,
        )
        (violation,) = outcome.result.violations
        assert violation.blocking_slots == ()
        assert "nothing to solve" in violation.describe()


class TestAgainstTheRealLibrary:
    """The plumbing, end to end, on the data the product actually ships."""

    def test_a_vegan_south_lunch_now_gets_a_plate(self):
        # Until 2026-08-24, SOUTH_LUNCH.curd_course was required and accepted
        # only curd/buttermilk; the library's sole filler, thayir_plain, was
        # dairy, so this was the one profile/template pair in the real
        # library that enumerated zero combinations -- a structural zero, not
        # a bound failure (finding 51, docs/audit_log.md, 2026-08-22). This
        # test used to assert that decline by name (empty_pool,
        # blocking_slots == ("curd_course",)); soya_curd
        # (data/recipes/soya_curd.yaml), a vegan-safe fermented-soymilk curd,
        # now fills the slot, so the decline no longer happens. Asserted here
        # as a real plate, not just absence of the old violation.
        library = load_library()
        profile = Profile(
            weight_kg=70.0, height_cm=175.0, age_years=28, sex=Sex.MALE,
            activity=ActivityLevel.MODERATE, goal=Goal.MAINTAIN,
            diet=DietPattern.VEGAN,
        )
        outcome = plan_meal(
            library,
            derive_target(profile).nutrition_target,
            region=Region.SOUTH_INDIAN,
            meal_slot=MealSlot.LUNCH,
            diet_pattern=profile.diet,
            profile=profile,
        )
        assert outcome.plan is not None
        assert outcome.plan.unit_counts.get("soya_curd@curd", 0) >= 1

    def test_the_reference_profile_still_gets_a_plate_on_all_four_templates(self):
        # D3's result, re-asserted here because D4 changed the decline path and
        # a change that quietly turned a pass into a decline would otherwise
        # only show up as a nicer-looking decline message.
        library = load_library()
        profile = Profile(
            weight_kg=70.0, height_cm=175.0, age_years=28, sex=Sex.MALE,
            activity=ActivityLevel.MODERATE, goal=Goal.MAINTAIN,
            diet=DietPattern.VEGETARIAN,
        )
        day = derive_target(profile).nutrition_target
        for region, slot in (
            (Region.SOUTH_INDIAN, MealSlot.BREAKFAST),
            (Region.SOUTH_INDIAN, MealSlot.LUNCH),
            (Region.NORTH_INDIAN, MealSlot.LUNCH),
            (Region.NORTH_INDIAN, MealSlot.DINNER),
        ):
            outcome = plan_meal(
                library, day, region=region, meal_slot=slot,
                diet_pattern=profile.diet, profile=profile,
            )
            assert outcome.plan is not None, f"{region.value}/{slot.value} declined"


class TestViolationTokensAreValidatedAtConstruction:
    def test_an_unknown_reach_is_rejected(self):
        with pytest.raises(ValueError, match="unknown reach"):
            Violation("protein_g", "below_floor", 1.0, 2.0, reach="nearly")

    def test_an_unknown_relaxability_is_rejected(self):
        with pytest.raises(ValueError, match="unknown relaxability"):
            Violation("protein_g", "below_floor", 1.0, 2.0, relaxability="maybe")

    def test_blocking_slots_belong_only_to_a_no_candidates_violation(self):
        with pytest.raises(ValueError, match="blocking_slots"):
            Violation(
                "protein_g", "below_floor", 1.0, 2.0, blocking_slots=("curd_course",)
            )
