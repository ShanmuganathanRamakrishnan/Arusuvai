"""TASKS_3.md N3: how often the ONE plate a user is shown has an animal dish.

`probe_nonveg_variety.py` asks whether an egg, fish or poultry plate is
*among* the valid plates. The dashboard does not show the valid plates; it
calls `POST /api/plan`, which returns the single plate `plan_meal` picks
(nearest to target). An animal plate that is valid but never picked is never
seen. Owner report 2026-09-27: a non-vegetarian profile still gets
soya_chunk_poriyal at South dinner.

For each of the 72 bodies, per diet and template, this calls `plan_meal`
exactly as `api/main.py` does (default library, dev_mode=True, no ledger)
and records: shown plate has an animal dish / some valid plate has one /
neither. Read-only.

    PYTHONPATH=. python docs/design/probes/probe_nonveg_shown.py
"""

from __future__ import annotations

import runpy
from pathlib import Path

from core.nutrition.targets import derive_target
from core.planner.plan import plan_meal
from core.schemas import ActivityLevel, DietPattern, Profile, Sex

here = Path(__file__).parent
variety = runpy.run_path(str(here / "probe_nonveg_variety.py"), run_name="probe_variety")
nonveg = runpy.run_path(str(here / "probe_nonveg.py"), run_name="probe_nonveg")
lib = variety["lib"]
TEMPLATES = variety["TEMPLATES"]
is_animal = variety["_is_animal"]
valid_plates = variety["valid_plates"]

DIETS = (DietPattern.EGGETARIAN, DietPattern.NON_VEGETARIAN)


def main() -> None:
    print("Bodies of 72: shown plate has egg/fish/poultry / some valid plate has one")
    print(f"{'template':24s}" + "".join(f"{d.value:>20s}" for d in DIETS))
    for region, slot in TEMPLATES:
        row = f"{region.value + '/' + slot.value:24s}"
        for diet in DIETS:
            shown = anywhere = 0
            for weight, goal, flags in nonveg["bodies"]():
                p = Profile(weight_kg=weight, height_cm=175.0, age_years=28,
                            sex=Sex.MALE, activity=ActivityLevel.MODERATE,
                            goal=goal, diet=diet, clinical_flags=flags)
                outcome = plan_meal(
                    lib, derive_target(p).nutrition_target, region=region,
                    meal_slot=slot, diet_pattern=diet, profile=p, dev_mode=True,
                )
                if outcome.plan is not None and any(
                    is_animal(c) for c in outcome.plan.combination.components
                ):
                    shown += 1
                if any(is_animal(c) for pl in valid_plates(p, region, slot)
                       for c in pl.combination.components):
                    anywhere += 1
            row += f"{f'{shown} / {anywhere}':>20s}"
        print(row)


if __name__ == "__main__":
    main()
