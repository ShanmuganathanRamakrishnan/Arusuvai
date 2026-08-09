"""D7: what verifying north_lunch's ingredients would and would not buy.

D7's goal is one plan the project can stand behind. Its own text says it
"depends on D6 -- verified ingredients feeding a wrong denominator certify
nothing." D6 fixed the denominator, so that question is now answerable, and it
is worth answering **before** a human spends hours with IFCT 2017 open rather
than after.

The question is not "are the rows verified" -- they are not, and only a human
who has opened the source may change that. The question is: **if every one of
them were, would the plate clear the ~15% unverified-energy shipping threshold
in `CLAUDE.md`?**

Three scenarios, all computed here rather than by mutating the registry, so the
probe states its own arithmetic and cannot be confused with a change to the
project's data:

  TODAY       what `core/` reports now
  INGREDIENTS every ingredient row in the plate verified; process constants
              untouched. This is exactly the scope D7 proposes to narrow to.
  EVERYTHING  ingredients *and* the process constants their lines carry

The gap between INGREDIENTS and EVERYTHING is the point. Under D6's per-line
rule a line is charged when its composition record is unverified **or** the
process constant that determined its quantity is -- so verifying composition
alone leaves every process-attributed line fully charged. IFCT 2017 is a food
composition table; it does not contain oil-uptake figures for a tempered curry.
Those are separate constants with separate sources, and `CLAUDE.md` is explicit
that Indian-specific process literature is thin.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7_verification_horizon.py
"""
from __future__ import annotations

from core.foods.nutrition_of import nutrition_of_components
from core.nutrition import citations
from core.planner.plan import load_library

lib = load_library()

#: The plate the reference profile is served on north_lunch today, from
#: `CLAUDE.md`'s build-status row. Same hard-coding, and same reason, as
#: `d6_unverified.py`: re-solving here would let the figures move for reasons
#: that have nothing to do with verification.
PLATE = (("phulka", 5), ("soya_chunk_curry", 1), ("paneer_masala", 1))

#: `CLAUDE.md`, "Threshold for shipping with unverified constants".
THRESHOLD = 0.15


def _process_verified(key: str) -> bool:
    return citations.evidence(citations.constant(key).evidence_id).verified


def unverified_energy(*, pretend_ingredients: bool, pretend_process: bool):
    """D6's per-line rule, with either source of doubt optionally waived.

    Reimplemented rather than imported so a scenario is a change to this
    function's arguments and never to the registry. A probe that flips
    `verified` on real Evidence to answer a hypothetical is one interrupted
    session away from leaving it flipped.
    """

    charged = total = 0.0
    detail: list[tuple[str, float, str]] = []
    for recipe_id, count in PLATE:
        recipe = lib.recipes.recipes[recipe_id]
        for line in recipe.ingredients:
            ing = lib.ingredients[line.ingredient_id]
            energy = ing.for_grams(line.quantity_g).energy_kcal * count
            total += energy
            bad_comp = (not ing.verified) and not pretend_ingredients
            bad_proc = (
                line.process_key is not None
                and not _process_verified(line.process_key)
                and not pretend_process
            )
            if bad_comp or bad_proc:
                charged += energy
                why = ",".join(
                    w for w, f in (("composition", bad_comp), ("process", bad_proc)) if f
                )
                if energy > 0:
                    detail.append((f"{recipe_id}:{line.ingredient_id}", energy, why))
    return charged, total, detail


def main() -> None:
    rows = {}
    for recipe_id, _ in PLATE:
        for line in lib.recipes.recipes[recipe_id].ingredients:
            rows.setdefault(line.ingredient_id, set()).add(line.process_key)

    print("=" * 92)
    print("The rows D7 would put in front of a human")
    print("=" * 92)
    for key in sorted(rows):
        ing = lib.ingredients[key]
        processes = sorted(p for p in rows[key] if p) or ["-"]
        print(f"  {key:<22} verified={str(ing.verified):<5} "
              f"ifct_code={ing.ifct_code or '-':<7} process={','.join(processes)}")
    unverified_rows = sorted(k for k in rows if not lib.ingredients[k].verified)
    no_code = [k for k in unverified_rows if not lib.ingredients[k].ifct_code]
    print(f"\n  {len(unverified_rows)} of {len(rows)} rows need a human with IFCT 2017 open.")
    print(f"  {len(no_code)} of those carry no IFCT code at all, so the code must be "
          "found first,")
    print("  not merely the values transcribed. None of the four rows that already")
    print("  carry real IFCT codes (rice_milled_raw, rajma_raw, toor_dal_raw,")
    print("  potato_raw) appears in this plate.")

    print()
    print("=" * 92)
    print("Would verification clear the shipping threshold?")
    print("=" * 92)
    scenarios = (
        ("TODAY", False, False),
        ("INGREDIENTS", True, False),
        ("EVERYTHING", True, True),
    )
    for label, pretend_ing, pretend_proc in scenarios:
        charged, total, detail = unverified_energy(
            pretend_ingredients=pretend_ing, pretend_process=pretend_proc
        )
        fraction = charged / total if total else 0.0
        verdict = "SHIPS" if fraction <= THRESHOLD else "does NOT ship"
        print(f"\n  {label:<12} {charged:7.1f} / {total:.1f} kcal = {fraction:6.1%}"
              f"   -> {verdict} (threshold {THRESHOLD:.0%})")
        for name, energy, why in detail:
            print(f"      {name:<40} {energy:7.1f} kcal  ({why})")
        if not detail:
            print("      (nothing charged)")

    # Cross-check against the shipped implementation, so a wrong reimplementation
    # of D6's rule here would be visible rather than quietly producing a nicer
    # answer. Only TODAY is checkable this way -- the other two are hypotheticals
    # and have no shipped counterpart, which is the whole reason they live here.
    shipped = nutrition_of_components(
        [(lib.recipes.component(r), c) for r, c in PLATE], lib.ingredients
    )
    today, _, _ = unverified_energy(pretend_ingredients=False, pretend_process=False)
    print(f"\n  cross-check: core/ reports {shipped.unverified_energy_kcal:.1f} kcal, "
          f"this probe's TODAY is {today:.1f} kcal "
          f"-- {'agree' if abs(shipped.unverified_energy_kcal - today) < 0.05 else 'DISAGREE'}")


if __name__ == "__main__":
    main()
