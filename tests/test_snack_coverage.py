"""Every region and diet gets a snack plate, for every body on the grid.

TASKS_3.md N29 (owner 2026-10-10, docs/audit_log.md "N29"). N28 found three
North vegan bodies with no snack at all, and nothing had failed: the count
lived only in a probe (docs/design/probes/probe_banana_tea_dishes.py). This
turns that probe's "plate" column into a standing check, so a change that
takes a snack away from anyone on the grid goes red here.

The grid is the probe's: 3 goals x 2 sexes x 55/70/90 kg, 170 cm, 30 y,
moderate activity, for both regions and all four diets -- 144 cases. The
expected value is not a snapshot of current output: the owner's rule is that
every one of them gets a passing plate. Measured 2026-10-09 (N28): 144/144.

This pins an outcome of the real library, so almost any library change can
turn it red. That is the point here -- a lost plate is the defect -- but a
red run names the body, not the cause; read the decline to find it.
"""

from __future__ import annotations

import functools

import pytest

from core.nutrition.targets import derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import DietPattern, MealSlot, Profile, Region
from core.schemas.profile import ActivityLevel, Goal, Sex

DIETS = ("vegetarian", "eggetarian", "non_vegetarian", "vegan")
REGIONS = (Region.SOUTH_INDIAN, Region.NORTH_INDIAN)


@functools.lru_cache(maxsize=1)
def _library():
    return default_library()


@pytest.mark.parametrize("region", REGIONS, ids=lambda r: r.value)
@pytest.mark.parametrize("diet_name", DIETS)
def test_every_body_gets_a_snack_plate(region, diet_name):
    diet = DietPattern(diet_name)
    missing = []
    for goal in Goal:
        for sex in (Sex.MALE, Sex.FEMALE):
            for weight in (55, 70, 90):
                p = Profile(
                    weight_kg=weight, height_cm=170, age_years=30, sex=sex,
                    activity=ActivityLevel.MODERATE, goal=goal, diet=diet,
                    clinical_flags=frozenset(),
                )
                out = plan_meal(
                    _library(), derive_target(p).nutrition_target,
                    region=region, meal_slot=MealSlot.SNACK,
                    diet_pattern=diet, profile=p,
                )
                if out.plan is None or not out.result.passed:
                    missing.append(f"{goal.value} {sex.value} {weight} kg")
    # 3 goals x 2 sexes x 3 weights = 18 bodies, all with a plate.
    assert missing == [], f"{region.value} {diet_name}: no snack for {missing}"
