"""D12: where a zero process uncertainty is earned, and where it is not.

Finding 41 says: "a declared process constant still leaves the macros it does
not touch at a bare zero", measured as protein = 0.0 on 15 of 18 recipes. That
count is right and the inference from it is not, which is what this probe is
for.

A recipe line derives no process uncertainty for one of three reasons, and they
are not the same reason:

  ATTRIBUTED    the line carries a `process:` key. Its uncertainty is computed
                from a registered constant. Nothing to fix.
  SERVED-BASIS  the ingredient row already describes the food as eaten -- state
                `cooked` (rice_cooked, toor_dal_cooked) or `as_used` (curd,
                paneer, oil, salt). The recipe applies no transformation to get
                from the row to the plate, so there is no process step whose
                uncertainty is missing. The zero is earned, and the remaining
                doubt is composition doubt, which is already charged at 0.25.
  UNATTRIBUTED  the row is raw-basis and the dish is cooked. The recipe IS the
                transformation, and nothing quantifies it. **This is finding 41.**

The distinction matters because the obvious fix is wrong. Declaring
`process: yield.rice_milled_boiled` on a `rice_cooked` line would attach a real,
registered, correctly-graded constant to a line whose quantity did not come from
it -- `RecipeIngredient.process_key` is documented as "the constant that
*determined this line's quantity*". See the second section below: the four
cooked-basis rows are not raw / yield. They are independent hand-entered
approximations that cite the yield factor as a cross-reference, and the factor
does not reproduce them.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d12_process_attribution.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

from core.nutrition import citations
from core.planner.plan import load_library
from core.schemas import MACRO_KEYS, RawOrCooked

REPO = Path(__file__).resolve().parents[3]
lib = load_library()

#: Cooked-basis row -> the yield constant its `source_note` names as
#: "connecting" it to a raw-basis row, and the raw row it names.
YIELD_CLAIMS = (
    ("rice_cooked", "rice_milled_raw", "yield.rice_milled_boiled"),
    ("toor_dal_cooked", "toor_dal_raw", "yield.toor_dal_boiled"),
    ("rajma_cooked", "rajma_raw", "yield.rajma_soaked_boiled"),
    ("potato_boiled", "potato_raw", "yield.potato_boiled"),
)

ATTRIBUTED, SERVED, UNATTRIBUTED = "ATTRIBUTED", "SERVED-BASIS", "UNATTRIBUTED"


def _preparations() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((REPO / "data/recipes").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or "id" not in doc:
            continue
        out[str(doc["id"])] = str(doc.get("preparation", "cooked"))
    return out


def classify(line, preparation: str) -> str:
    if line.process_key:
        return ATTRIBUTED
    if line.state is not RawOrCooked.RAW:
        return SERVED
    # A raw-basis line in an uncooked dish is raw food served raw: earned.
    return SERVED if preparation == "uncooked" else UNATTRIBUTED


def main() -> None:
    preparations = _preparations()

    print("=" * 96)
    print("Why each recipe's protein process uncertainty is what it is")
    print("=" * 96)
    print(f"  {'recipe':<18} {'prep':<9} {'prot_unc':>8}  "
          f"{'% protein on UNATTRIBUTED lines':>32}   lines")

    totals = {ATTRIBUTED: 0.0, SERVED: 0.0, UNATTRIBUTED: 0.0}
    worst: list[tuple[float, str, list[str]]] = []
    for recipe_id in sorted(lib.recipes.recipes):
        recipe = lib.recipes.recipes[recipe_id]
        prep = preparations.get(recipe_id, "cooked")
        buckets = {ATTRIBUTED: 0.0, SERVED: 0.0, UNATTRIBUTED: 0.0}
        names: list[str] = []
        for line in recipe.ingredients:
            ing = lib.ingredients[line.ingredient_id]
            protein = ing.for_grams(line.quantity_g).protein_g
            kind = classify(line, prep)
            buckets[kind] += protein
            totals[kind] += protein
            if kind is UNATTRIBUTED and protein > 0:
                names.append(f"{line.ingredient_id}({protein:.1f}g)")
        total = sum(buckets.values())
        share = buckets[UNATTRIBUTED] / total if total else 0.0
        unc = recipe.uncertainty_for("protein_g")
        print(f"  {recipe_id:<18} {prep:<9} {unc:8.4f}  {share:31.1%}   "
              f"{', '.join(names) or '-'}")
        if share > 0:
            worst.append((share, recipe_id, names))

    grand = sum(totals.values())
    print(f"\n  Library protein, by why its process uncertainty is zero:")
    for kind in (ATTRIBUTED, SERVED, UNATTRIBUTED):
        print(f"      {kind:<14} {totals[kind]:8.1f} g  ({totals[kind]/grand:5.1%})")
    print(f"\n  {len(worst)} of {len(lib.recipes.recipes)} recipes carry protein on a "
          "raw-basis line the recipe cooks and nothing quantifies.")
    print("  Those, and only those, are what finding 41 is about. A recipe at 0.0")
    print("  with no UNATTRIBUTED protein has a zero that is earned: every gram")
    print("  came from a row describing the food as served.")

    print()
    print("=" * 96)
    print("Does the yield factor actually connect the cooked row to the raw one?")
    print("=" * 96)
    print("  Each cooked-basis row's source_note says a yield constant connects it")
    print("  to a raw row. If that were true, cooked == raw / yield, and declaring")
    print("  the yield constant on the line would be mechanism-correct.")
    print()
    rows = {r["id"]: r for r in csv.DictReader(
        (REPO / "data/raw/ifct/fixture_ingredients.csv").read_text(encoding="utf-8")
        .splitlines())}
    print(f"  {'cooked row':<18} {'macro':<12} {'stated':>9} {'raw/yield':>10} {'ratio':>7}")
    for cooked, raw, key in YIELD_CLAIMS:
        y = citations.value_of(key)
        for macro in ("energy_kcal", "protein_g", "carb_g"):
            got, predicted = float(rows[cooked][macro]), float(rows[raw][macro]) / y
            flag = "" if abs(got / predicted - 1) <= 0.05 else "   <-- does not follow"
            print(f"  {cooked:<18} {macro:<12} {got:9.2f} {predicted:10.2f} "
                  f"{got/predicted:7.3f}{flag}")
    print("\n  None of the four is its raw row divided by its yield factor. They are")
    print("  independent hand-entered approximations; the note is a cross-reference,")
    print("  not a derivation. So `process: yield.*` on those lines would assert a")
    print("  provenance the number does not have -- the mechanism-mismatch failure")
    print("  CLAUDE.md's `phenomenon` field exists to prevent, committed in the")
    print("  process axis instead of the citation axis.")
    print("\n  Consequence worth stating on its own: all four yield.* constants are")
    print("  registered, graded, and load-bearing for NOTHING. No code multiplies by")
    print("  them and no recipe line derives from them.")


if __name__ == "__main__":
    main()
