"""The user removes a dish; that course stays empty and the plate still validates (TASKS_3.md N10).

Owner 2026-09-30: remove a single dish, whether the user added it or the
planner chose it. The cheap version -- drop the dish's pick and plan again --
was measured first and brought the course back in 67 of 155 flows
(docs/audit_log.md 2026-09-30), so "leave this course empty" is an input the
planner holds, exactly as it holds picks: the rung is chosen without it, a
plate is chosen among those that honour it, and none is a decline.

Synthetic South lunch from ``tests/factories.py``, as ``test_dish_picks.py``.
``crisp`` is the template's only optional slot. At 500 kcal, 1200 mg sodium
and a 10 g fibre floor, rung 0 has exactly one valid plate and it carries a
crisp; crisp-free plates are valid only after rung 1 widens the fibre floor.
"""

from __future__ import annotations

import dataclasses

from core.foods import templates
from core.nutrition.target import simple_target
from core.planner.candidates import build_candidate_pool
from core.planner.combinations import enumerate_combinations, feasible_combinations
from core.planner.solver import solve
from core.planner.validator import RELAXATION_ORDER, plan_within_ladder
from core.schemas import DietPattern
from tests.factories import SOUTH_LUNCH_COMPONENTS
from tests.test_dish_picks import FEASIBLE, ING, _combos, _ids, _options, _solved

SLOTS = templates.SOUTH_LUNCH.slots
CRISP = next(i for i, s in enumerate(SLOTS) if s.name == "crisp")
ONLY_CRISP_PLATES_AT_RUNG_0 = simple_target(
    energy_kcal=500.0, protein_g_min=20.0, sodium_mg_max=1200.0, fibre_g_min=10.0
)
# At 850 kcal, rice_a is on valid plates only beside a crisp (measured
# 2026-09-30: 27 valid plates, 3 crisp-free, 9 with rice_a, none both).
RICE_A_NEEDS_A_CRISP = simple_target(energy_kcal=850.0, protein_g_min=20.0)
NO_CRISP = frozenset({"crisp"})


def _crisp_free(solved):
    return [p for p in solved if not p.combination.slot_selections[CRISP]]


class TestACourseIsLeftEmpty:
    def test_the_fixture_is_the_shape_this_file_needs(self):
        assert [s.name for s in SLOTS if not s.required] == ["crisp"]

    def test_the_removed_course_is_off_the_plate(self):
        shown = plan_within_ladder(_combos(), FEASIBLE, ING)
        # Precondition: with no crisp shown there is nothing to remove.
        assert shown.plan.combination.slot_selections[CRISP]
        expected = _crisp_free(_solved(FEASIBLE))[0]

        outcome = plan_within_ladder(_combos(), FEASIBLE, ING, leave_empty=NO_CRISP)

        assert outcome.result.passed
        assert not outcome.plan.combination.slot_selections[CRISP]
        # The nearest crisp-free plate, with the solver's counts for it.
        assert _ids(outcome.plan) == _ids(expected)
        assert outcome.plan.unit_counts == expected.unit_counts

    def test_a_pick_is_still_honoured_beside_it(self):
        crisp_free = _crisp_free(_solved(FEASIBLE))
        nearest = _ids(crisp_free[0])
        wanted = next(r for p in crisp_free[1:] for r in _ids(p) if r not in nearest)

        outcome = plan_within_ladder(
            _combos(), FEASIBLE, ING, picks=frozenset({wanted}), leave_empty=NO_CRISP
        )

        assert outcome.result.passed
        assert wanted in _ids(outcome.plan)
        assert not outcome.plan.combination.slot_selections[CRISP]


class TestRemovingNeverLoosensALimit:
    def test_the_fixture_has_crisp_free_plates_only_after_rung_1(self):
        # Precondition: without it the test below passes whatever happens.
        rung_0 = _solved(ONLY_CRISP_PLATES_AT_RUNG_0)
        assert rung_0 and not _crisp_free(rung_0)
        rung_1 = RELAXATION_ORDER[0].apply(ONLY_CRISP_PLATES_AT_RUNG_0, frozenset())
        assert _crisp_free(_solved(rung_1))

    def test_a_removal_valid_only_on_a_looser_rung_is_declined(self):
        outcome = plan_within_ladder(
            _combos(), ONLY_CRISP_PLATES_AT_RUNG_0, ING, leave_empty=NO_CRISP
        )
        # Not the rung-0 plate with its crisp either: that would be ignoring
        # the removal without saying so.
        assert outcome.plan is None
        assert not outcome.result.passed
        assert outcome.result.relaxation_applied == ()
        assert outcome.target_used == ONLY_CRISP_PLATES_AT_RUNG_0
        assert "crisp" in outcome.result.disclosure
        assert outcome.result.violations

    def test_a_required_course_cannot_be_removed(self):
        outcome = plan_within_ladder(
            _combos(), FEASIBLE, ING, leave_empty=frozenset({"gravy"})
        )
        assert outcome.plan is None
        assert "gravy" in outcome.result.disclosure

    def test_a_pick_in_the_removed_course_is_declined_not_resolved(self):
        outcome = plan_within_ladder(
            _combos(), FEASIBLE, ING, picks=frozenset({"crisp_a"}), leave_empty=NO_CRISP
        )
        assert outcome.plan is None


class TestWhatCanBeRemoved:
    def test_only_a_course_some_valid_plate_lacks(self):
        outcome = plan_within_ladder(_combos(), FEASIBLE, ING)
        assert outcome.emptiable_slots == ("crisp",)

    def test_not_offered_when_no_plate_at_this_rung_lacks_it(self):
        outcome = plan_within_ladder(_combos(), ONLY_CRISP_PLATES_AT_RUNG_0, ING)
        assert outcome.result.passed
        assert outcome.emptiable_slots == ()

    def test_not_offered_when_the_other_slots_picks_need_it(self):
        solved = _solved(RICE_A_NEEDS_A_CRISP)
        # Precondition: crisp-free plates exist, and rice_a plates exist, but
        # no plate is both.
        assert _crisp_free(solved)
        assert any("rice_a" in _ids(p) for p in solved)
        assert not any("rice_a" in _ids(p) for p in _crisp_free(solved))

        plain = plan_within_ladder(_combos(), RICE_A_NEEDS_A_CRISP, ING)
        picked = plan_within_ladder(
            _combos(), RICE_A_NEEDS_A_CRISP, ING, picks=frozenset({"rice_a"})
        )
        assert "crisp" in plain.emptiable_slots
        assert "crisp" not in picked.emptiable_slots

    def test_a_dish_the_user_picked_can_itself_be_removed(self):
        # The flow N10 exists for: add a dish, then take it off again. The
        # pick in the course must not count against emptying that course.
        outcome = plan_within_ladder(
            _combos(), FEASIBLE, ING, picks=frozenset({"crisp_a"})
        )
        assert "crisp_a" in _ids(outcome.plan)
        assert "crisp" in outcome.emptiable_slots

    def test_still_offered_once_removed(self):
        # The page needs it to keep showing the course as removable state,
        # and the slot's own emptiness must not count against itself.
        outcome = plan_within_ladder(_combos(), FEASIBLE, ING, leave_empty=NO_CRISP)
        assert outcome.emptiable_slots == ("crisp",)


class TestSwapOptionsBesideARemoval:
    def test_other_slots_options_keep_the_removal(self):
        solved = _solved(RICE_A_NEEDS_A_CRISP)
        rice = SLOTS[0]
        unconstrained = {c.recipe.id for p in solved for c in p.combination.selection_for(rice)}
        beside = {
            c.recipe.id for p in _crisp_free(solved) for c in p.combination.selection_for(rice)
        }
        # Precondition: without a difference the assertion below cannot fail.
        assert beside != unconstrained

        outcome = plan_within_ladder(
            _combos(), RICE_A_NEEDS_A_CRISP, ING, leave_empty=NO_CRISP
        )
        assert outcome.result.passed
        assert set(_options(outcome)[rice.name]) == beside

    def test_the_removed_course_still_lists_what_could_go_back(self):
        plain = plan_within_ladder(_combos(), FEASIBLE, ING)
        removed = plan_within_ladder(_combos(), FEASIBLE, ING, leave_empty=NO_CRISP)
        assert _options(removed)["crisp"] == _options(plain)["crisp"] != ()


class TestTwoRemovableCourses:
    """``crisp`` is the fixture's only optional slot, and a rule about two
    removed courses cannot be exercised with one. Here the curd course is
    optional too. Measured 2026-09-30 at 800 kcal: 58 valid plates, 3 without
    curd, 12 without a crisp, none without both."""

    TEMPLATE = dataclasses.replace(
        templates.SOUTH_LUNCH,
        slots=tuple(
            dataclasses.replace(s, required=False, min_selections=0)
            if s.name == "curd_course" else s
            for s in SLOTS
        ),
    )
    TARGET = simple_target(energy_kcal=800.0, protein_g_min=20.0)

    def _combos(self):
        return enumerate_combinations(
            build_candidate_pool(
                SOUTH_LUNCH_COMPONENTS, ING,
                template=self.TEMPLATE, diet_pattern=DietPattern.VEGETARIAN,
            )
        )

    def test_a_course_is_not_removable_if_that_needs_a_removed_course_back(self):
        combos = self._combos()
        solved = solve(feasible_combinations(combos, self.TARGET, ING), self.TARGET, ING)
        curd = next(i for i, s in enumerate(SLOTS) if s.name == "curd_course")
        no_curd = [p for p in solved if not p.combination.slot_selections[curd]]
        # Precondition: each course can go on its own, never both.
        assert no_curd and _crisp_free(solved)
        assert not _crisp_free(no_curd)

        plain = plan_within_ladder(combos, self.TARGET, ING)
        assert set(plain.emptiable_slots) == {"curd_course", "crisp"}

        removed = plan_within_ladder(combos, self.TARGET, ING, leave_empty=NO_CRISP)
        assert removed.result.passed
        assert "curd_course" not in removed.emptiable_slots
        assert "crisp" in removed.emptiable_slots
