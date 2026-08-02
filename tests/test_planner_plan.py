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


class TestSouthBreakfastCanReachAQualitySource:
    """Finding 25, closed 2026-08-02 (D2b-i).

    ``SOUTH_BREAKFAST``'s four original slots accept ``tiffin``,
    ``sambar``/``kuzhambu``, ``chutney``/``podi`` and ``beverage``. No component
    carrying a high-quality protein source belongs in any of them, so the
    quality-source rule would have made this template unsatisfiable for a
    structural reason rather than a thin-library one. An optional
    ``curd_course`` closes it.
    """

    def _pool(self, ingredients, library):
        from core.foods.templates import SOUTH_BREAKFAST

        return SOUTH_BREAKFAST, build_candidate_pool(
            library.components.values(),
            ingredients,
            template=SOUTH_BREAKFAST,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=True,
        )

    def test_the_curd_slot_has_a_candidate(self, ingredients, library):
        template, pool = self._pool(ingredients, library)
        assert [c.id for c in pool.for_slot(template.slot("curd_course"))] == [
            "thayir_plain@curd"
        ]

    def test_a_breakfast_without_curd_still_enumerates(self, ingredients, library):
        # The whole point of making the slot optional rather than required, and
        # the assertion that would fail if a later edit tightened it: idli or
        # dosa with sambar and chutney is a complete breakfast, and a rule that
        # needed curd on the plate to be satisfiable would be the same
        # cut-the-hole-to-fit failure finding 25 describes, committed the other
        # way round.
        from core.planner.combinations import enumerate_combinations

        template, pool = self._pool(ingredients, library)
        shapes = [
            frozenset(c.id for c in combo.components)
            for combo in enumerate_combinations(pool)
        ]
        assert any("thayir_plain@curd" not in shape for shape in shapes)
        assert any("thayir_plain@curd" in shape for shape in shapes)


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


class TestPerMealProteinCeiling:
    """Slice 3's genuinely new gate: no meal packed with protein.

    The per-meal protein *floor* is not new -- the energy-fraction share already
    provided one, and slice 3 only added a guard beneath it that binds on the
    snack slot. The *ceiling* is new: nothing previously stopped the solver
    answering a protein floor by piling three katoris of dal onto one plate.

    **When the ceiling can bind at all**, measured, because the first draft of
    these tests passed vacuously and the control is what caught it: the solver
    scores by deviation from each macro's target *point*, and the protein point
    is the energy share (0.35 x day floor) while the ceiling is 0.50 x day
    floor. The point therefore always sits below the ceiling, for every slot, so
    the solver is never pulled through it by its own scoring. The ceiling binds
    only when a *different* constraint drags protein up -- an energy floor that
    needs more units, which is exactly the three-katoris-of-dal case it was
    introduced for. It is a backstop, not a shaper, and a test that does not set
    up that collision is testing nothing.
    """

    def _synthetic_library(self) -> Library:
        components = {c.id: c for c in SOUTH_LUNCH_COMPONENTS}
        return Library(
            ingredients=SOUTH_LUNCH_INGREDIENTS,
            recipes=RecipeLibrary(recipes={}, components=components),
        )

    def _plan(self, day_protein_g: float, energy_kcal: float):
        return plan_meal(
            self._synthetic_library(),
            simple_target(energy_kcal=energy_kcal, protein_g_min=day_protein_g),
            region=Region.SOUTH_INDIAN,
            meal_slot=MealSlot.LUNCH,
            diet_pattern=DietPattern.VEGETARIAN,
            dev_mode=False,
        )

    #: Day protein floor 40 g -> meal ceiling 0.50 x 40 = 20.0 g. Energy 2400
    #: kcal -> lunch floor 0.35 x 2400 x 0.95 = 798 before relaxation. Reaching
    #: that energy in this pool costs more than 20 g of protein, so the two
    #: constraints genuinely collide. Measured below rather than argued.
    _COLLIDING = (40.0, 2400.0)

    def test_the_ceiling_excludes_a_plate_the_solver_would_otherwise_return(self):
        # The pair, run against the same pool and the same target, differing
        # only in the registered ceiling fraction:
        #
        #   ceiling 0.50 (real) -> declines, energy 510.0 below its 756.0 floor
        #   ceiling 10.0 (off)  -> returns a 26.5 g / 800.0 kcal plate
        #
        # So the bound removes a plate the solver was otherwise willing to
        # serve. That is the whole claim, and it is why the control below is
        # part of the test rather than an optional extra.
        import dataclasses

        from core.nutrition import citations

        blocked = self._plan(*self._COLLIDING)
        assert blocked.plan is None

        key = "protein.meal_ceiling_fraction"
        original = citations.constant(key)
        citations._CONSTANTS[key] = dataclasses.replace(original, value=10.0)
        try:
            lifted = self._plan(*self._COLLIDING)
        finally:
            citations._CONSTANTS[key] = original

        assert lifted.plan is not None, (
            "with the ceiling lifted this target must be satisfiable, or the "
            "blocked case above proves nothing about the ceiling"
        )
        assert lifted.plan.estimate.point.protein_g > 20.0, (
            "the lifted plate must exceed the real ceiling, or the two runs "
            "differ for some reason other than the bound under test"
        )
        # Restored, and proven restored rather than assumed.
        assert self._plan(*self._COLLIDING).plan is None

    def test_the_decline_names_energy_though_the_cause_is_the_protein_ceiling(self):
        # Documented, not endorsed. The ceiling excludes protein-rich plates
        # before scoring, so what survives cannot reach the energy floor and the
        # violation reported is energy_kcal -- the symptom, not the cause. A
        # user told "energy is unreachable" would reasonably add an energy-dense
        # dish, which cannot help.
        #
        # Pinned so the current behaviour is visible rather than surprising, and
        # so that improving it is a deliberate change with a red test attached.
        # docs/audit_log.md finding 24.
        blocked = self._plan(*self._COLLIDING)
        macros = {v.macro for v in blocked.result.violations}
        assert "energy_kcal" in macros
        assert "protein_g" not in macros

    def test_a_returned_plate_is_never_above_the_ceiling(self):
        # The invariant, over the whole grid probed while building this class --
        # cheap, and it is what would catch the ceiling being dropped from
        # meal_target entirely while the collision test above still passed for
        # some unrelated reason.
        for day_protein in (40.0, 60.0):
            for energy in (1800.0, 2000.0, 2400.0, 2700.0):
                outcome = self._plan(day_protein, energy)
                if outcome.plan is None:
                    continue
                assert outcome.plan.estimate.point.protein_g <= 0.50 * day_protein + 1e-9
