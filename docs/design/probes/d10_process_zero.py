"""D10: which recipes derive a zero process uncertainty, and which earned it.

`docs/audit_log.md` finding 2 — "a recipe with no `process:` lines reads as
fully process-certain" — open since 2026-07-21. This probe is the measurement
that made it answerable and the artifact that keeps the answer checkable.

## The "before" column is a counterfactual, not a history claim

D10 changed the loader *and* three recipe files, so "what this repo produced
yesterday" is not something today's checkout can be asked. A probe that pretends
otherwise is the failure `CLAUDE.md` records under "writing a before/after probe
that can only run on the after tree": `d4_declines.py` read a field D4a
introduced, and its before column was unmeasurable an hour after it was taken.

So the column below is a **counterfactual computable on either tree**: what this
recipe's energy band would be if it declared neither `preparation` nor
`energy_kcal` in `process_uncertainty_unassessed` — i.e. if its author had
simply left the field out. That is exactly the pre-D10 state for all five
no-process recipes, and it is what a *new* recipe would get today if the loader
rule were removed. It is computed here from the recipe's own ingredient lines,
not read off `Recipe.process_uncertainty`, so this probe cannot silently agree
with the code it audits.

Run from the repo root:

    PYTHONPATH=. python docs/design/probes/d10_process_zero.py
"""
from __future__ import annotations

from pathlib import Path

import yaml

from core.foods.ifct_loader import load_ingredients
from core.foods.nutrition_of import nutrition_of_components, nutrition_of_recipe
from core.foods.recipe_loader import load_recipes
from core.nutrition import citations

REPO = Path(__file__).resolve().parents[3]
RECIPE_DIR = REPO / "data/recipes"


def _docs_by_id() -> dict[str, dict]:
    """Recipe id -> its parsed YAML. Ids and filenames do not always match:
    `thayir_plain` lives in `thayir_sadam_curd.yaml`."""

    out: dict[str, dict] = {}
    for path in sorted(RECIPE_DIR.glob("*.yaml")):
        if path.name == "schema.yaml":
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        out[str(doc["id"])] = doc
    return out


def _energy_band_if_undeclared(recipe, ingredients) -> float:
    """Process uncertainty on energy for a recipe that declares nothing.

    The derivation, reimplemented: sum over the lines carrying a process
    constant of that line's energy times the constant's own band, divided by the
    dish total. With no process line the numerator is empty, so the answer is a
    bare 0.0 however the food was actually treated — which is finding 2.
    """

    # The unit's own floor, not 1: the fraction is scale-invariant, and
    # `idli` refuses a count of 1 (min_count 2).
    count = recipe.serving_unit.min_count
    total = nutrition_of_recipe(recipe, count, ingredients).energy_kcal
    if total == 0:
        return 0.0
    absolute = 0.0
    for line in recipe.ingredients:
        if not line.process_key:
            continue
        contribution = ingredients[line.ingredient_id].for_grams(line.quantity_g)
        absolute += (
            contribution.energy_kcal
            * citations.uncertainty_of(line.process_key)
            * count
        )
    return absolute / total


def main() -> None:
    ingredients = load_ingredients(REPO / "data/raw/ifct").loaded
    library = load_recipes(RECIPE_DIR, ingredients)
    docs = _docs_by_id()

    wide = citations.value_of("process.unassessed_uncertainty")
    print(f"process.unassessed_uncertainty = {wide}")
    print()
    print(f"{'recipe':<20} {'preparation':<11} {'proc':>5} "
          f"{'undeclared':>11} {'now':>8} {'combined':>9}")
    print("-" * 70)

    for rid in sorted(library.recipes):
        recipe = library.recipes[rid]
        doc = docs[rid]
        n_process = sum(1 for line in recipe.ingredients if line.process_key)
        undeclared = _energy_band_if_undeclared(recipe, ingredients)
        now = recipe.uncertainty_for("energy_kcal")

        # Combined composition+process, the figure `candidates.py` gates on.
        # Priced at the unit's own floor: `idli` has min_count 6, and asking for
        # one raises.
        estimate = nutrition_of_components(
            [(library.component(rid), recipe.serving_unit.min_count)], ingredients
        )
        combined = estimate.uncertainty_fraction("energy_kcal")
        moved = "  <-- moved" if abs(now - undeclared) > 1e-9 else ""

        print(f"{rid:<20} {str(doc.get('preparation', 'cooked')):<11} {n_process:>5} "
              f"{undeclared:>11.4f} {now:>8.4f} {combined:>9.4f}{moved}")

    print()
    print("Recipes with no process constant at all -- the population D10 rules on:")
    for rid in sorted(library.recipes):
        recipe = library.recipes[rid]
        if any(line.process_key for line in recipe.ingredients):
            continue
        doc = docs[rid]
        preparation = str(doc.get("preparation", "cooked"))
        unassessed = [str(m) for m in (doc.get("process_uncertainty_unassessed") or [])]
        verdict = (
            "zero earned: nothing is heated"
            if preparation == "uncooked"
            else f"cooked; {len(unassessed)} of 9 macros declared unassessed"
        )
        # The point estimate, printed so the reader can see it did not move: the
        # validator gates on this, and the band is display-only.
        point = nutrition_of_recipe(
            recipe, recipe.serving_unit.min_count, ingredients
        ).energy_kcal
        print(f"  {rid:<16} {preparation:<10} {point:8.1f} kcal   {verdict}")

    # Finding 41, the part D10 does NOT close: a recipe that carries a process
    # constant still derives 0.0 for every macro that constant does not touch.
    # Oil uptake is the only kind of constant registered and oil carries no
    # protein, so this is almost the whole library.
    print()
    zeroed = sorted(
        rid for rid, r in library.recipes.items()
        if r.uncertainty_for("protein_g") == 0.0
    )
    print(f"Finding 41 -- protein process uncertainty is exactly 0.0 on "
          f"{len(zeroed)} of {len(library.recipes)} recipes:")
    print(f"  {', '.join(zeroed)}")
    print(f"  escaping only: "
          f"{', '.join(sorted(set(library.recipes) - set(zeroed)))} "
          f"-- the three D10 forced to declare all nine macros unassessed")


if __name__ == "__main__":
    main()
