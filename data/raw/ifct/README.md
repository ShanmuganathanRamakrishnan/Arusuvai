# `data/raw/ifct/` — provenance

## What is actually in here

`fixture_ingredients.csv` is a **hand-entered fixture set**, not an IFCT
extract. Every row's `verified` column is `false` and every `ifct_code` is
empty. Both of those are deliberate:

- The nutrient values are approximations of commonly published figures,
  transcribed from memory. Nobody has opened *Indian Food Composition Tables*
  (Longvah et al., 2017) in the course of this build. Treat them as
  plausible-shaped test data, not as reference values.
- The `ifct_code` column is empty rather than filled with invented codes. A
  fabricated code that looks real is worse than an absent one, for the same
  reason a real-but-mismatched citation is worse than a missing one: it passes
  every automated check while being wrong, and only someone with the source
  document can catch it.

## Conventions

- One row per (food, state). `state` is `raw`, `cooked` or `as_used`.
- Nutrients are **per 100 g edible portion** in the stated `state`.
- `carb_g` is **total carbohydrate including dietary fibre**; `fibre_g` is the
  fibre subset of it. The loader's Atwater reconciliation (`4P + 9F + 4C`)
  assumes this. Foods high in fibre reconcile worst under that formula, since
  fibre yields well under 4 kcal/g — which is why the tolerance is 15% and not
  tighter.
- `allergens` is a `|`-separated list, empty for none.
- Booleans are `true`/`false`.

## TODO — real ingest

Replace this file with a genuine IFCT 2017 subset:

1. Obtain IFCT 2017 (NIN Hyderabad).
2. Extract the rows for the foods listed here, keeping the published food code
   in `ifct_code`.
3. Prefer IFCT's own cooked-state entries where they exist. Where they do not,
   convert through a registered yield factor in
   `core/nutrition/citations.py` — never an inline multiplication.
4. A human who has read the source may then set `verified` to `true`, per row.
   Nobody else may.
