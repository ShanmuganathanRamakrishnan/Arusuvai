"""TASKS_3.md N1: how eggetarian and non-vegetarian profiles fare today.

`probe_rank_input2.py` measures vegetarian and vegan profiles only, so no
eggetarian or non-vegetarian plate has ever been counted. This runs that
probe's own per-case function (`accepted_rung_valid_plate_count`, loaded
unmodified via runpy) over the same 72-profile body grid -- 6 weights x 3
goals x 4 flag-sets -- once per diet, vegetarian included as the baseline.

A non-vegetarian may eat every vegetarian dish, but its count is NOT bounded
below by the vegetarian count. The count is taken at whichever rung the ladder
accepts, and an extra dish can let the ladder stop at an earlier, stricter
rung where fewer plates fit. Measured 2026-09-27: south_indian/dinner, 70 kg
lose_fat, vegetarian 6 plates at protein_tolerance vs non_vegetarian 1 plate
at fat_carb_tolerance (docs/audit_log.md 2026-09-27, non-vegetarian
baseline). Read-only: changes no recipe, no constant, no threshold.

    PYTHONPATH=. python docs/design/probes/probe_nonveg.py
"""

from __future__ import annotations

import runpy
from pathlib import Path

from core.schemas import ClinicalFlag, DietPattern, Goal, Profile, Sex, ActivityLevel

base = runpy.run_path(
    str(Path(__file__).with_name("probe_rank_input2.py")), run_name="probe_base"
)
count_for = base["accepted_rung_valid_plate_count"]
TEMPLATES = base["TEMPLATES"]
MIN_VALID_PLATES = base["MIN_VALID_PLATES"]

DIETS = (DietPattern.VEGETARIAN, DietPattern.EGGETARIAN, DietPattern.NON_VEGETARIAN)


def bodies():
    """The 72 (weight, goal, flags) bodies of the base probe's grid, diet removed."""

    flag_sets = (
        frozenset(),
        frozenset({ClinicalFlag.HYPERTENSION}),
        frozenset({ClinicalFlag.CHRONIC_KIDNEY_DISEASE}),
        frozenset({ClinicalFlag.DIABETES}),
    )
    for weight in (45.0, 55.0, 70.0, 85.0, 95.0, 110.0):
        for goal in (Goal.LOSE_FAT, Goal.MAINTAIN, Goal.GAIN_MUSCLE):
            for flags in flag_sets:
                yield weight, goal, flags


def main() -> None:
    # counts[(template, diet)] -> list of plate counts, one per body, same order.
    counts: dict = {}
    for weight, goal, flags in bodies():
        for diet in DIETS:
            profile = Profile(
                weight_kg=weight, height_cm=175.0, age_years=28, sex=Sex.MALE,
                activity=ActivityLevel.MODERATE, goal=goal, diet=diet,
                clinical_flags=flags,
            )
            for region, slot in TEMPLATES:
                n, _ = count_for(profile, region, slot)
                counts.setdefault(((region, slot), diet), []).append(n)

    n_bodies = len(next(iter(counts.values())))
    print(f"{n_bodies} bodies per diet; cells are profiles with 0 / 1 / "
          f"{MIN_VALID_PLATES}+ valid plates at the accepted rung")
    print()
    header = f"{'template':24s}" + "".join(f"{d.value:>22s}" for d in DIETS)
    print(header)
    totals = {d: 0 for d in DIETS}
    for region, slot in TEMPLATES:
        row = f"{region.value + '/' + slot.value:24s}"
        for d in DIETS:
            c = counts[((region, slot), d)]
            z = sum(1 for x in c if x == 0)
            o = sum(1 for x in c if x == 1)
            t = sum(1 for x in c if x >= MIN_VALID_PLATES)
            totals[d] += t
            row += f"{f'{z} / {o} / {t}':>22s}"
        print(row)
    print(f"{'2+ total':24s}" + "".join(
        f"{f'{totals[d]}/{n_bodies * len(TEMPLATES)}':>22s}" for d in DIETS))
    print()

    print("Bodies where the diet has MORE valid plates than vegetarian, per template")
    print("(where the animal-protein dishes add choice at all):")
    for region, slot in TEMPLATES:
        veg = counts[((region, slot), DietPattern.VEGETARIAN)]
        parts = []
        for d in DIETS[1:]:
            other = counts[((region, slot), d)]
            more = sum(1 for a, b in zip(veg, other) if b > a)
            lifted = sum(1 for a, b in zip(veg, other)
                         if a < MIN_VALID_PLATES <= b)
            parts.append(f"{d.value}: {more} more, {lifted} crossed to 2+")
        print(f"  {region.value + '/' + slot.value:24s}" + "; ".join(parts))


if __name__ == "__main__":
    main()
