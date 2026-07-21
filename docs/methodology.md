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

There are **two independent sources of error**, and an early version of this
system modelled only the second:

1. **Composition uncertainty** — how wrong the per-100 g nutrient record itself
   is. Resolved per ingredient from provenance:
   `composition.verified_primary` (0.05) for a value a human read out of a
   primary table, `composition.unverified_secondary` (0.25) otherwise. Assigned
   by the loader from a registered constant, never from a CSV column, so an
   author cannot quietly narrow the band on their own unverified row.
2. **Process uncertainty** — `Recipe.process_uncertainty`, a fractional band per
   macro at the dish level, covering oil uptake and cooking loss. Immutable
   after construction (`MappingProxyType`) so no downstream module can widen it
   to make a plan pass.

`nutrition_of_components` returns a point estimate **and** an interval. Both
terms are summed rather than root-sum-squared — the errors are treated as
perfectly correlated. For process constants the justification is mechanism (this
cook, this pan). For composition it is *provenance*: every value in the current
fixture was transcribed from memory by one author in one sitting, so the errors
plausibly share a bias. **That justification expires with the real IFCT ingest**,
where per-food laboratory errors are much closer to independent; see the caveat
in `nutrition_of_components`' docstring.

The validator (Phase 3) will gate on the **point estimate only**. Interval
overlap gating is disqualified: it would mean a plan built on worse data passes
more easily, which inverts the point of having a gate.

### Why composition uncertainty was added (2026-07-21)

Before it existed, the band came from process constants alone. On the masala
dosa that meant the displayed figure was derived from the griddle-oil constant,
which governs 8.84 kcal of a 223.65 kcal dish — and the remaining 96%, whose
composition values nobody has ever checked against a source, contributed exactly
zero. The dish rendered as `~220 kcal (+/-4%)`.

That is **tighter than the ±5% this project would claim for real IFCT data**, on
data that is admittedly worse. It is also worse than printing a bare
`1,847 kcal`: a bare number is merely silent about its error, whereas `±4%`
actively asserts the error is small. That is precisely the false-precision
failure this project exists to prevent in the LLM, committed instead by the
mechanism built to prevent it.

With both terms, the same dish is:

```
composition  223.65 kcal x 0.25             = 55.9125 kcal
process      223.65 kcal x 0.040            =  8.9460 kcal   (see below)
half-width                                   = 64.8585 kcal
                            = 29% of the point estimate
```

### Where the declared process bands come from

Each recipe's process uncertainty is derived arithmetically from a registered
constant, with the derivation written into the recipe file's `uncertainty_notes`
and enforced by the loader. Worked example, masala dosa energy:

```
griddle oil 3.5 g x 8.84 kcal/g x 0.20 band = 6.188 kcal
temper  oil 3.0 g x 8.84 kcal/g x 0.10 band = 2.652 kcal
(6.188 + 2.652) / 223.65 kcal total          = 0.040
```

Which line each constant governs is recorded on the ingredient line itself
(`process: oil_uptake.dosa_griddled`), not in a recipe-level list. The masala
dosa has two `gingelly_oil` lines that differ only by process, which a
recipe-level list cannot express; and `Recipe.process_constants` and
`process_exposure_g` are derived from the lines, so neither can go stale against
the ingredients it describes.

## Nothing can currently ship as validated (2026-07-21)

Stated plainly, because the alternative is discovering it after `core/planner`
has been built on the assumption that some plans clear the threshold.

**Every registered `Evidence` in `citations.py` is `verified=False`.** Nobody has
opened IFCT 2017, FAO FNP 77, or the NIN household-measures manual during this
build. Consequently every ingredient row carries the 0.25 unverified-composition
band, and every recipe's protein uncertainty is 0.25 against a
`eligibility.max_protein_uncertainty` ceiling of 0.15.

Protein is target-critical for essentially every profile this product serves. So
**the candidate pool is empty for every profile**, and the relaxation ladder
cannot rescue it: the ladder moves tolerance, and never uncertainty.

Two tests in `tests/test_nutrition_of.py` assert this rather than leaving it as
prose — `test_no_recipe_currently_clears_the_protein_eligibility_ceiling` and
`test_every_registered_evidence_is_still_unverified`. They exist because the
tempting fix, once the planner returns nothing, is to nudge 0.25 down or 0.15 up
until a demo works. Either edit looks reasonable in isolation; both must be
deliberate acts with a failing assertion attached.

### `dev_mode` versus `validated`

`core/planner` (not built) must therefore carry two distinct designations:

- **`validated`** — the plan's data clears the uncertainty ceilings and the
  unverified-energy threshold. Currently unreachable, by the above.
- **`dev_mode`** — plan generation and testing proceed on admittedly unverified
  data, with the ceilings suspended. This is the only mode the planner will run
  in until the real ingest lands.

`dev_mode` is a **deliberate suspension of a stated invariant**, not a
convenience flag. Its exit condition is named: a human opens IFCT 2017 and flips
`verified` per row, at which point the composition band drops to 0.05 and the
ceilings become satisfiable.

Because a portfolio project's output is a screenshot, "unvalidated" must survive
being viewed without surrounding context. A boolean on a dataclass does not. Any
rendered plan, any `demo.py` stdout, and any README transcript produced in
`dev_mode` must carry that label in the artifact itself.

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
   real-ingest TODO, and "Nothing can currently ship as validated" above for
   what that implies for the planner.

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

7. **Composition uncertainty is uniform across macros.** Every macro on a row
   gets the same band from its provenance constant, though the real dispersion
   is not uniform — B12 and iron are measured less reliably than energy, and a
   remembered sodium figure is a worse guess than a remembered protein one.
   `Ingredient.composition_uncertainty` is a per-macro mapping so this can be
   refined per nutrient without a schema change; it is simply populated
   uniformly today. A uniform band is honest about being an estimate; a
   per-macro one invented without a source would not be.

8. **`_depends_on_unverified` over-attributes.** A recipe with any unverified
   process constant charges its *whole* energy to the unverified bucket, though
   only the grams that constant governs actually depend on it. It is not
   narrowed yet because the opposite and larger error — `Ingredient.verified`
   not reaching the shipping-threshold calculation at all — is still open, and
   correcting the smaller one alone would move the reported figure away from the
   truth. The per-line attribution needed to fix both now exists
   (`Recipe.lines_for_process`).

## What is not built

`core/schemas/profile.py`, the rest of `core/nutrition/` (energy, protein,
macros, targets), `core/planner/`, `core/commerce/`, `api/` and `web/`. The
Phase 1 subset of `core/nutrition/` is `citations.py` only. The build-status
table in `CLAUDE.md` reflects this.
