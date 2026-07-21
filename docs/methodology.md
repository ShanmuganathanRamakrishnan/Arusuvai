# Methodology and known limitations

Current as of the Phase 1 build (food data layer). Sections for the solver,
validator, relaxation ladder and LLM layer will be added as those phases land —
this document only describes what exists.

## Scope statement — read this first

This is a portfolio project, not clinical nutrition guidance. Nothing here is a
substitute for advice from a dietitian or a doctor. Once `clinical_flags` exists
on the profile (not yet — see "What is not built"), a user with a diagnosed
dietary condition should be relying on it rather than on any default behaviour
of this system.

## Raw versus cooked weight

Recipes store **cooked/finished weights as the primary record**. Rice roughly
triples on cooking, so reading a raw composition value against a cooked quantity
is a 3x error rather than a tolerance-band problem — which is why:

- every recipe ingredient line carries its own `state` (`raw`, `cooked`,
  `as_used`), naming the composition basis to look it up on;
- `core/foods/nutrition_of.py` **refuses** to evaluate a line whose state does
  not match the ingredient's record, rather than silently applying a yield
  factor;
- conversions go through `core/foods/retention.py`, which reads its factors from
  the citation registry. There is no inline multiplication by a yield factor
  anywhere in the codebase.

Ingredient quantities in a recipe sum to the finished weight of **one serving
unit**, checked on construction within 2%. Where a dish is made from a raw
constituent that absorbs water — a dosa from rice-and-urad batter — the raw
constituents are recorded on a `raw` basis and the absorbed water is listed as
an explicit `water` line, so the masses still add up and nothing is hidden
inside a single derived number.

## Serving units, not multipliers

Portion space is not continuous. Every recipe declares a `ServingUnit` with a
name ("dosa", "cup", "plate"), a gram weight, and integer `min`/`default`/`max`
counts. The solver will search that integer domain.

There is deliberately no continuous multiplier and no five-point multiplier
scale (0.5/0.75/1.0/1.25/1.5) anywhere: 1.25 of an idli is 1.25 idlis, and a
five-point scale produces the same unservable fractional output with tidier
presentation. `ServingUnit.grams_for` and `portions.to_grams` both raise
`TypeError` on a non-integer count, so this cannot be reintroduced by accident.

## Uncertainty is a property of the data

`Recipe.process_uncertainty` is a fractional band per macro, at the dish level,
and it is immutable after construction (`MappingProxyType`) so no downstream
module can widen it to make a plan pass.

`nutrition_of_components` returns a point estimate **and** an interval. The
interval is computed by summing the low ends and summing the high ends — the
errors are treated as perfectly correlated rather than root-sum-squared, because
they are systematic (this cook, this pan, this library's yield assumptions), not
independent random draws. RSS would give a narrower and more flattering band.

The validator (Phase 3) will gate on the **point estimate only**. Interval
overlap gating is disqualified: it would mean a plan built on worse data passes
more easily, which inverts the point of having a gate.

### Where the declared bands come from

Each recipe's uncertainty is derived arithmetically from a registered constant,
with the derivation written into the recipe file's `uncertainty_notes` and
enforced by the loader. Worked example, masala dosa energy:

```
griddle oil 3.5 g x 8.84 kcal/g x 0.20 band = 6.188 kcal
temper  oil 3.0 g x 8.84 kcal/g x 0.10 band = 2.652 kcal
(6.188 + 2.652) / 223.65 kcal total          = 0.040
```

## Citations: mechanism must match, not just format

`Evidence` carries a `phenomenon` field stating precisely what physical process
the source measured, distinct from `summary`. Every `Constant` carries an
`applied_to` stating the process it is used for. A registration where those two
describe different mechanisms is the actual hole in a citation defence — a real,
findable, correctly-formatted citation for the wrong process passes every
automated check while being wrong, and unlike a fabricated citation it is not
falsifiable by anyone without domain expertise.

Concretely: deep-fat frying oil-absorption literature does not describe a
griddled dosa. Immersion frying deposits oil into a crust as steam condenses
during post-fry cooling; a dosa picks up oil spooned around the rim of a tawa.
The specific paper found and refused is recorded in `REJECTED_CITATIONS` in
`core/nutrition/citations.py`, so the next person to search does not have to
re-derive the rejection.

Where no matching source exists, the constant is registered as a
`PROJECT_ESTIMATE` with `verified=False` and a wide band. `Evidence` refuses to
let a project estimate be marked verified at all: there is no document to open.

## Known limitations, Phase 1

1. **The ingredient data is a hand-entered fixture set, not IFCT.** All 23 rows
   are `verified=False`, every `ifct_code` is empty, and the values are
   approximations of commonly published figures transcribed from memory. Nobody
   has opened IFCT 2017 during this build. See `data/raw/ifct/README.md` for the
   real-ingest TODO.

2. **Every process constant in the library is unverified.** Yield factors, oil
   uptake and household measures are all project estimates or
   transcribed-from-memory national-table figures. `citations.unverified()` and
   `retention.unverified_processes()` report this honestly, and a test asserts
   nothing has been quietly flipped.

3. **The Atwater reconciliation is a coherence check, not a validation of
   truth.** It catches transcription slips and unit confusion; it cannot catch a
   row that is internally consistent and still wrong. Its 15% tolerance is loose
   because `carb_g` is total carbohydrate including fibre, and fibre yields well
   under 4 kcal/g, so high-fibre foods reconcile worst.

4. **Household measure weights vary by household more than most nutritional
   constants do.** Hence the double-digit uncertainty bands on all of them. A
   recipe may override the generic measure weight for its own dish, and the
   three example recipes do.

5. **Three recipes is not a library.** The combination-space arithmetic in
   Phase 2 must be computed against real post-filter recipe counts, not
   asserted from this set.

6. **DIAAS is stored but unused.** `Ingredient.diaas` is populated where a
   commonly cited figure exists and left `None` otherwise. Nothing reads it yet;
   protein quality scoring is a later phase, and the values carry the same
   unverified caveat as everything else in the fixture.

## What is not built

`core/schemas/profile.py`, the rest of `core/nutrition/` (energy, protein,
macros, targets), `core/planner/`, `core/commerce/`, `api/` and `web/`. The
Phase 1 subset of `core/nutrition/` is `citations.py` only. The build-status
table in `CLAUDE.md` reflects this.
