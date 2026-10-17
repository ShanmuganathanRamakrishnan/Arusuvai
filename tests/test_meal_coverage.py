"""Breakfast, lunch and dinner: no body that has a plate today loses it.

TASKS_3.md N31 (owner 2026-10-11, docs/audit_log.md "N31"). The N29 snack
check (tests/test_snack_coverage.py) asserts every body gets a plate. For the
three meals that is not true yet: on 2026-10-11, 818 of 864 cases planned
and 46 did not, 45 of them lose_fat bodies. The owner chose to guard what
works now and fix the gaps after, so this pins both halves:

- a body not in ``KNOWN_GAPS`` must get a passing plate -- red names it as a
  lost plate, the defect this file exists for;
- a body in ``KNOWN_GAPS`` must still have none -- red names it as a closed
  gap. That is good news, not a defect: take it out of ``KNOWN_GAPS`` in
  the same commit that closes it, so the list stays the true to-do list.

The grid is the snack check's: 3 goals x 2 sexes x 55/70/90 kg, 170 cm,
30 y, moderate, both regions, all four diets -- 144 cases per meal -- run
with a snack in the day and without (N30), so 864 in all. Measured under
PYTHONHASHSEED 1 and 777, byte-identical. It plans every case for real:
about 1 minute since N33 (docs/audit_log.md 2026-10-16), 6 before it.
"""

from __future__ import annotations

import functools

import pytest

from core.nutrition.targets import derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex

DIETS = ("vegetarian", "eggetarian", "non_vegetarian", "vegan")
SLOTS = (MealSlot.BREAKFAST, MealSlot.LUNCH, MealSlot.DINNER)
REGIONS = (Region.SOUTH_INDIAN, Region.NORTH_INDIAN)

#: (eats_snack, meal, region, diet) -> bodies with no passing plate, as
#: measured 2026-10-11 (N31): 28 with a snack in the day, 18 without.
#: 2026-10-17 (N32a, a 120 g rice step): 12 with, 10 without.
#: 2026-10-17 (N32b, protein weight counted up to BMI 30): 8 with, 6 without.
#: Shrinks as gaps are fixed; must never grow.
KNOWN_GAPS: dict[tuple[bool, str, str, str], list[str]] = {
    (True, 'breakfast', 'north_indian', 'vegan'): ['lose_fat male 55 kg', 'lose_fat male 70 kg', 'lose_fat male 90 kg', 'lose_fat female 55 kg', 'lose_fat female 70 kg', 'lose_fat female 90 kg'],
    (True, 'dinner', 'south_indian', 'vegan'): ['lose_fat female 55 kg', 'lose_fat female 90 kg'],
    (False, 'breakfast', 'north_indian', 'vegan'): ['lose_fat male 70 kg', 'lose_fat male 90 kg', 'lose_fat female 55 kg', 'lose_fat female 70 kg', 'lose_fat female 90 kg'],
    (False, 'dinner', 'south_indian', 'vegan'): ['lose_fat female 70 kg'],
}


@functools.lru_cache(maxsize=1)
def _library():
    return default_library()


def _missing(eats_snack, slot, region, diet):
    out = []
    for goal in Goal:
        for sex in (Sex.MALE, Sex.FEMALE):
            for weight in (55, 70, 90):
                p = Profile(
                    weight_kg=weight, height_cm=170, age_years=30, sex=sex,
                    activity=ActivityLevel.MODERATE, goal=goal, diet=diet,
                    eats_snack=eats_snack,
                )
                plan = plan_meal(
                    _library(), derive_target(p).nutrition_target,
                    region=region, meal_slot=slot, diet_pattern=diet, profile=p,
                )
                if plan.plan is None or not plan.result.passed:
                    out.append(f"{goal.value} {sex.value} {weight} kg")
    return out


def test_the_known_gaps_add_up():
    # 6+2 = 8 with a snack; 5+1 = 6 without; 14 of 864 (46 at N31,
    # 2026-10-11; 24 closed by N32a's rice step, 8 by N32b's BMI-30 cap).
    assert sum(len(v) for k, v in KNOWN_GAPS.items() if k[0]) == 8
    assert sum(len(v) for k, v in KNOWN_GAPS.items() if not k[0]) == 6


@pytest.mark.parametrize("region", REGIONS, ids=lambda r: r.value)
@pytest.mark.parametrize("slot", SLOTS, ids=lambda s: s.value)
@pytest.mark.parametrize("eats_snack", (True, False), ids=("snack", "no_snack"))
def test_no_body_loses_its_plate(eats_snack, slot, region):
    lost, closed = [], []
    for name in DIETS:
        missing = _missing(eats_snack, slot, region, DietPattern(name))
        known = KNOWN_GAPS.get((eats_snack, slot.value, region.value, name), [])
        lost += [f"{name}: {b}" for b in missing if b not in known]
        closed += [f"{name}: {b}" for b in known if b not in missing]
    assert lost == [], f"lost a plate: {lost}"
    assert closed == [], f"gap closed, take it out of KNOWN_GAPS: {closed}"
