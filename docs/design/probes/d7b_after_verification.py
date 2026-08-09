"""D7b: what the ten-row sitting buys, now that D10 has landed.

`d7_verification_horizon.py` answered "if every ingredient row in the
north_lunch plate were verified, would the plate clear the ~15%
unverified-energy shipping threshold?" and got **9.5%, SHIPS**. That probe was
written and run *before* D10.

D10 changed the input to that conclusion. Three recipes -- `idli`, `phulka`,
`steamed_rice` -- are cooked, carry no `process:` line, and now declare every
macro in `process_uncertainty_unassessed`, which maps to the registered
`process.unassessed_uncertainty` (0.20). Composition verification cannot touch
that term. And `phulka` is in the north_lunch plate.

So there are **two gates**, not one, and D7 only measured the second:

  1. `core/planner/candidates.py` eligibility -- combined composition+process
     band on a target-critical macro against a registered ceiling. Runs FIRST,
     at pool-build time. Suspended today by `dev_mode=True`.
  2. the ~15% unverified-energy shipping threshold -- what `d7` measured.

A plate that clears (2) and fails (1) is not servable outside `dev_mode`,
because it is never enumerated in the first place. That is a different and
earlier failure than the one D7 was watching for, and it is worth knowing
before a human opens IFCT 2017, for exactly the reason `d7`'s own docstring
gives about answering this before the hours are spent rather than after.

This probe recomputes the protein band per recipe from the ingredient lines --
the same recomputation-rather-than-trust stance as `d10_process_zero.py` -- so
it cannot silently agree with the code it audits, and so the counterfactual
(every composition record verified) needs no mutation of the real registry.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_after_verification.py
"""
from __future__ import annotations

from core.foods.nutrition_of import nutrition_of_components, nutrition_of_recipe
from core.nutrition import citations
from core.planner.plan import load_library

lib = load_library()

MACRO = "protein_g"
CEILING = citations.constant("eligibility.max_protein_uncertainty").value
VERIFIED_BAND = citations.constant("composition.verified_primary").value

#: The four reference plates from `CLAUDE.md`'s build-status row, hard-coded
#: for the same reason `d6_unverified.py` and `d7_verification_horizon.py`
#: hard-code theirs: re-solving here would let the figures move for reasons
#: that have nothing to do with verification.
PLATES = {
    "south_breakfast": (("idli", 6), ("soya_kuzhambu", 1),
                        ("coconut_chutney", 2), ("thayir_plain", 1)),
    "south_lunch": (("steamed_rice", 1), ("soya_kuzhambu", 2),
                    ("carrot_poriyal", 2), ("thayir_plain", 1)),
    "north_lunch": (("phulka", 5), ("soya_chunk_curry", 1), ("paneer_masala", 1)),
    "north_dinner": (("phulka", 3), ("soya_chunk_curry", 1),
                     ("aloo_sabzi", 1), ("onion_raita", 2)),
}


def protein_band(recipe_id: str, *, pretend_verified: bool) -> tuple[float, float, float]:
    """(composition term, process term, combined) for protein on one recipe.

    Mirrors `nutrition_of._composition_band` / `_interval_for_recipe`: the
    composition half-width is each line's protein contribution times that
    ingredient's declared band, and the process term is the recipe's own
    fraction applied to the point estimate. Summed, not in quadrature.

    `pretend_verified` substitutes `composition.verified_primary` for every
    ingredient's declared composition band -- the ceiling of what the ten-row
    sitting could possibly achieve, since a verified row cannot do better than
    the registered verified default.
    """

    recipe = lib.recipes.recipes[recipe_id]
    count = recipe.serving_unit.min_count
    half = 0.0
    for line in recipe.ingredients:
        ing = lib.ingredients[line.ingredient_id]
        contribution = getattr(ing.for_grams(line.quantity_g), MACRO) * count
        band = VERIFIED_BAND if pretend_verified else ing.composition_uncertainty_for(MACRO)
        half += contribution * band
    point = getattr(nutrition_of_recipe(recipe, count, lib.ingredients), MACRO)
    if point == 0:
        return 0.0, 0.0, 0.0
    composition = half / point
    process = recipe.uncertainty_for(MACRO)
    return composition, process, composition + process


def main() -> None:
    print("=" * 92)
    print(f"Protein eligibility band per recipe, against the {CEILING:.2f} ceiling")
    print(f"(counterfactual assumes every composition record verified at "
          f"{VERIFIED_BAND:.2f} -- the best the sitting can buy)")
    print("=" * 92)
    print(f"  {'recipe':<20} {'comp':>6} {'proc':>6} {'TODAY':>7}  "
          f"{'comp':>6} {'proc':>6} {'VERIFIED':>8}   verdict")

    blocked_after: list[str] = []
    for recipe_id in sorted(lib.recipes.recipes):
        c0, p0, t0 = protein_band(recipe_id, pretend_verified=False)
        c1, p1, t1 = protein_band(recipe_id, pretend_verified=True)
        if t1 > CEILING:
            blocked_after.append(recipe_id)
            verdict = "STILL BLOCKED"
        else:
            verdict = "clears"
        print(f"  {recipe_id:<20} {c0:6.4f} {p0:6.4f} {t0:7.4f}  "
              f"{c1:6.4f} {p1:6.4f} {t1:8.4f}   {verdict}")

    print(f"\n  {len(blocked_after)} of {len(lib.recipes.recipes)} recipes remain "
          f"protein-ineligible after full composition verification:")
    for r in blocked_after:
        print(f"      {r}")
    print("  Composition verification cannot move these: their protein band is")
    print("  process.unassessed_uncertainty, declared by D10 because the dish is")
    print("  cooked and no registered constant describes its cooking loss.")

    print()
    print("=" * 92)
    print("Which reference plates does that block?")
    print("=" * 92)
    for name, plate in PLATES.items():
        offenders = [r for r, _ in plate if r in blocked_after]
        state = f"BLOCKED by {', '.join(offenders)}" if offenders else "enumerable"
        print(f"  {name:<18} {state}")
    print("\n  A blocked plate is not merely unshippable -- outside dev_mode its")
    print("  components never enter the candidate pool, so it is never enumerated")
    print("  and never solved. That gate runs before the 15% energy threshold")
    print("  d7_verification_horizon.py measured, so d7's 'INGREDIENTS 9.5% SHIPS'")
    print("  describes a plate that, post-D10, cannot be built to be measured.")

    # Cross-check the TODAY column against the shipped implementation, for the
    # same reason d7_verification_horizon.py cross-checks its own: a
    # reimplementation that agrees with nothing is not independent, it is just
    # unverified. Only TODAY has a shipped counterpart -- the VERIFIED column is
    # a counterfactual by construction, which is why it lives in a probe.
    print()
    print("=" * 92)
    print("Cross-check: this probe's TODAY column vs core/")
    print("=" * 92)
    disagreements = checked = 0
    # Every component, not one per recipe: a recipe accepted under two
    # categories is two pool entries, and the gate runs per entry.
    for component_id in sorted(lib.recipes.components):
        component = lib.recipes.component(component_id)
        count = component.recipe.serving_unit.min_count
        shipped = nutrition_of_components(
            [(component, count)], lib.ingredients
        ).uncertainty_fraction(MACRO)
        _, _, mine = protein_band(component.recipe.id, pretend_verified=False)
        checked += 1
        if abs(shipped - mine) > 5e-4:
            disagreements += 1
            print(f"  {component_id:<24} core/={shipped:.4f} probe={mine:.4f}  DISAGREE")
    print(f"  {checked - disagreements} of {checked} components agree, "
          f"{disagreements} disagree.")


if __name__ == "__main__":
    main()
