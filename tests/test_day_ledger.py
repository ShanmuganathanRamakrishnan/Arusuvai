"""What a day has spent, and the wall between its points and its intervals.

Two properties here are worth more than the rest and are the reason this file
exists rather than a few cases bolted onto ``test_nutrition_meal_target.py``:

1. **Re-planning a slot replaces, never accumulates.** The debit-before-credit
   rule is the whole justification for storing per-slot contributions instead of
   a running total, so it is asserted directly rather than implied.
2. **Intervals cannot reach the budget arithmetic.** ``DayLedger`` deliberately
   holds both the point estimates that gate and the intervals that only display,
   one attribute access apart. CLAUDE.md's round-4 addendum says a rule is not
   demonstrated by being mentioned — the test has to perturb an input and check
   the output does not move. So: widen every interval, leave every point alone,
   assert nothing the budget reads has changed.
"""

from __future__ import annotations

import pytest

from core.nutrition.meal_target import meal_target, spent_before
from core.nutrition.target import simple_target
from core.schemas import DayLedger, MealSlot


def _ledger() -> DayLedger:
    return (
        DayLedger.empty()
        .with_meal(
            MealSlot.BREAKFAST,
            {"sodium_mg": 400.0, "energy_kcal": 600.0},
            low={"sodium_mg": 300.0, "energy_kcal": 450.0},
            high={"sodium_mg": 500.0, "energy_kcal": 750.0},
        )
        .with_meal(MealSlot.DINNER, {"sodium_mg": 350.0, "energy_kcal": 700.0})
    )


class TestSpending:
    def test_spent_sums_the_points_of_every_planned_slot(self):
        # 400 + 350 = 750
        assert _ledger().spent("sodium_mg") == pytest.approx(750.0)

    def test_an_unrecorded_macro_reads_as_zero_not_as_missing(self):
        # A slot that recorded no iron genuinely contributed none. This is the
        # OPPOSITE default to an unset *uncertainty*, which CLAUDE.md's round-4
        # addendum requires to read wide rather than confident -- different
        # quantities, and the asymmetry is deliberate.
        assert _ledger().spent("iron_mg") == pytest.approx(0.0)

    def test_an_empty_ledger_has_spent_nothing(self):
        assert DayLedger.empty().is_empty()
        assert DayLedger.empty().spent("sodium_mg") == pytest.approx(0.0)

    def test_planned_slots_are_reported_in_declaration_order(self):
        # Insertion order was dinner-last but BREAKFAST precedes DINNER in the
        # enum, so a transcript lists a day in the order a day happens.
        assert _ledger().planned_slots() == (MealSlot.BREAKFAST, MealSlot.DINNER)


class TestReplanningReplacesRatherThanAccumulates:
    def test_planning_the_same_slot_twice_leaves_one_contribution(self):
        twice = DayLedger.empty().with_meal(
            MealSlot.LUNCH, {"sodium_mg": 900.0}
        ).with_meal(MealSlot.LUNCH, {"sodium_mg": 200.0})

        # 200, not 1100: the first lunch was thrown away, not eaten.
        assert twice.spent("sodium_mg") == pytest.approx(200.0)
        assert twice.planned_slots() == (MealSlot.LUNCH,)

    def test_the_receiver_is_not_mutated(self):
        original = _ledger()
        original.with_meal(MealSlot.LUNCH, {"sodium_mg": 999.0})
        assert original.spent("sodium_mg") == pytest.approx(750.0)

    def test_replacing_without_an_interval_drops_the_stale_one(self):
        # Otherwise the previous plate's band would sit under the new plate's
        # point estimate and describe food nobody is being served.
        replaced = _ledger().with_meal(MealSlot.BREAKFAST, {"sodium_mg": 10.0})
        assert MealSlot.BREAKFAST not in replaced.intervals
        assert replaced.spent_interval("sodium_mg") == (0.0, 0.0)

    def test_without_meal_removes_both_point_and_interval(self):
        gone = _ledger().without_meal(MealSlot.BREAKFAST)
        assert gone.spent("sodium_mg") == pytest.approx(350.0)
        assert MealSlot.BREAKFAST not in gone.intervals

    def test_removing_an_unplanned_slot_is_not_an_error(self):
        assert DayLedger.empty().without_meal(MealSlot.SNACK).is_empty()


class TestSpentBeforeExcludesTheSlotBeingPlanned:
    def test_replanning_a_slot_is_not_charged_for_its_own_predecessor(self):
        # Planning breakfast again must see only dinner's 350 mg. Charging the
        # 400 mg of the breakfast about to be replaced would hold its
        # replacement to a budget its predecessor already spent.
        assert spent_before(_ledger(), MealSlot.BREAKFAST, "sodium_mg") == pytest.approx(350.0)

    def test_an_unplanned_slot_sees_the_whole_day(self):
        assert spent_before(_ledger(), MealSlot.LUNCH, "sodium_mg") == pytest.approx(750.0)

    def test_no_ledger_is_the_first_meal_of_the_day(self):
        assert spent_before(None, MealSlot.LUNCH, "sodium_mg") == pytest.approx(0.0)


class TestIntervalsCannotReachTheBudget:
    """The perturbation test. See this module's docstring."""

    @staticmethod
    def _widened(ledger: DayLedger) -> DayLedger:
        """Same points, every interval blown out by 10x. Nothing else changes."""

        return DayLedger(
            meals=ledger.meals,
            intervals={
                slot: (
                    {m: v * 0.1 for m, v in lo.items()},
                    {m: v * 10.0 for m, v in hi.items()},
                )
                for slot, (lo, hi) in ledger.intervals.items()
            },
        )

    def test_widening_every_interval_does_not_move_what_was_spent(self):
        base, wide = _ledger(), self._widened(_ledger())
        assert wide.spent_interval("sodium_mg") != base.spent_interval("sodium_mg")
        assert wide.spent("sodium_mg") == pytest.approx(base.spent("sodium_mg"))
        assert spent_before(wide, MealSlot.LUNCH, "sodium_mg") == pytest.approx(
            spent_before(base, MealSlot.LUNCH, "sodium_mg")
        )

    def test_widening_every_interval_does_not_move_a_single_bound(self):
        # Vacuous while `_DAY_BUDGETED` is empty and every bound is a plain
        # energy-fraction share -- and load-bearing the moment slice 1b puts
        # sodium on the ledger. Written now so the guard exists before the thing
        # it guards, rather than being remembered afterwards.
        day = simple_target(energy_kcal=2000.0, protein_g_min=100.0, sodium_mg_max=2000.0)
        tight = meal_target(day, MealSlot.LUNCH, ledger=_ledger())
        wide = meal_target(day, MealSlot.LUNCH, ledger=self._widened(_ledger()))

        assert dict(wide.ceilings) == pytest.approx(dict(tight.ceilings))
        assert dict(wide.floors) == pytest.approx(dict(tight.floors))


class TestTheLedgerRefusesNonsense:
    def test_an_unknown_macro_key_fails_rather_than_being_ignored(self):
        # A typo'd key would create an entry `spent` never reads, and the budget
        # would behave as though the nutrient had never been eaten.
        with pytest.raises(ValueError, match="unknown macro key"):
            DayLedger.empty().with_meal(MealSlot.LUNCH, {"sodum_mg": 400.0})

    def test_half_an_interval_is_rejected(self):
        with pytest.raises(ValueError, match="both low and high"):
            DayLedger.empty().with_meal(
                MealSlot.LUNCH, {"sodium_mg": 400.0}, low={"sodium_mg": 300.0}
            )

    def test_an_interval_with_no_point_estimate_is_rejected(self):
        with pytest.raises(ValueError, match="no point contribution"):
            DayLedger(intervals={MealSlot.LUNCH: ({"sodium_mg": 1.0}, {"sodium_mg": 2.0})})
