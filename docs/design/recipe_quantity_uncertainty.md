# Declared estimates and a confidence label — design

**Status: design only, 2026-08-02. Nothing in `core/` implements any of it.**
Task T3 in `TASKS.md`. Every number below is measured against the real library
with the probes reproduced in §9; none is asserted.

---

## 1. The problem this closes

Task 5b established that every salt and oil quantity in `data/recipes/` was
authored to be *plausible*, not read off anything, and that 91.7% of a blocking
sodium figure came from four such numbers. No authoritative table exists for how
much salt goes in a dal — the concept does not have a measurand.

Today those quantities enter the pipeline as if they were exact. `Ingredient`
carries `composition_uncertainty` (how wrong the per-100 g row is) and `Recipe`
carries a derived `process_uncertainty` (how wrong the oil-uptake and yield
constants are). There is no term at all for *how wrong the gram figure on the
recipe line is*, which on the macros that actually block plans is the dominant
error.

How dominant, measured. Share of each macro contributed by lines whose quantity
is a free authoring choice — salt, oils, spice, aromatics — rather than the bulk
of the dish:

```
recipe          disc. mass   energy   protein     fat    carb   sodium
dal_tadka            7.2%    29.4%      3.9%   92.6%    5.0%    98.8%
masala_dosa         12.3%    40.2%     42.8%   97.2%   15.3%    99.4%
onion_raita          1.0%     0.5%      0.5%    0.1%    1.6%    77.1%
phulka               0.3%     0.0%      0.0%    0.0%    0.0%    98.5%
rajma_chawal         4.9%     17.4%     3.1%   87.8%    2.3%    99.0%
sambar_sadam         4.5%     19.1%     8.7%   89.0%    3.4%    97.2%
```

**Sodium is 77–99% authored guesswork and fat is 88–97%.** Sodium is also the
constraint that currently declines the reference profile. The project's entire
premise is that it does not overstate what it knows, and it is presently
reporting a sodium figure to one decimal place that rests almost entirely on
numbers nobody measured.

## 2. Decisions taken as given

Three, from T3, designed to and not reopened:

1. **One uncertainty constant, not thirty.** Per-quantity bands mean guessing
   the value and then guessing how wrong the guess is; thirty of them would
   never be audited.
2. **Gating stays on the point estimate.** Bands do not gate. **This is already
   current behaviour** (`core/planner/validator.py` reads
   `SolvedPlan.estimate.point` and nothing else), so decision 2 changes nothing
   on its own — it is a statement that this design does not quietly introduce
   interval gating through the back door.
3. **Every plan reports a plain-language confidence label**, derived rather than
   chosen, not a gate.

## 3. The constant

```python
AUTHORED_QUANTITY = register_constant(Constant(
    key="quantity.authored_domestic",
    value=0.30,
    unit="fraction",
    evidence_id="project_decision",
    applied_to=(
        "the gram figure on a recipe line that a human wrote down as a "
        "plausible domestic quantity — how much salt goes in a dal, how much "
        "oil in a tadka — where no composition table, yield constant or "
        "measurement determined it"
    ),
    uncertainty=0.0,
    note=(
        "A PROJECT_DECISION, not a finding. 0.30 is the spread of the "
        "quantities it actually binds: household salting runs roughly "
        "0.4-0.8% of finished weight and a tadka is one teaspoon to one "
        "tablespoon of oil, both about +/-30% around the middle. It is NOT a "
        "band on the bulk of a dish, which the recipe mass check already pins "
        "to +/-2% -- see the cap in the loader, which is what makes a single "
        "constant defensible instead of a compromise between two "
        "incompatible cases. Estimated on the wide side per CLAUDE.md: "
        "uncertain data must make a recipe harder to use, never easier to "
        "pass."
    ),
))
```

Grade: `PROJECT_DECISION`, via the existing `project_decision` evidence,
`verified=False`. Per the round-4 addendum it is **categorically ineligible** to
count as reviewed or to satisfy a mechanism-match requirement, and a
`REVIEWED_MECHANISM_MATCHES` entry may only say "project decision, no physical
process claimed."

### Why 0.30 and not 0.15

A flat band is applied to every line and summed, so a flat `q` produces exactly
`q` on every macro. The measurement in §1 says that is wrong in both directions
at once: it would put ±0.15 on protein, whose lines are pinned by the recipe
mass check to ±2%, and only ±0.15 on sodium, which is one authored number with a
real domestic spread near ±30%. Choosing between under-stating sodium and
over-stating protein is a false choice — §4 removes it, and once removed the
constant should be set from the quantities it actually binds. That is 0.30.

## 4. Where it applies: the cap that makes one constant enough

`Recipe.__post_init__` already rejects any recipe whose ingredient weights do
not sum to its declared `grams_per_unit` within `_RECIPE_MASS_TOLERANCE`
(0.02). That check is load-bearing here: **an author could not have been 30%
wrong about the 95 g of dal in a 150 g katori, because the loader would have
refused the file.** They could easily have been 30% wrong about the 0.8 g of
salt, because 0.24 g is 0.16% of the katori and disappears into the tolerance.

So the effective band on a line is the authored band capped by the error the
mass check would have caught:

```
line_band(line) = min(quantity.authored_domestic,
                      recipe_mass_tolerance * serving_unit.grams_per_unit
                        / line.quantity_g)
```

Computed at load time in `core/foods/recipe_loader.py`, alongside
`_derive_process_uncertainty`, and stored as a new
`Recipe.quantity_uncertainty: Mapping[str, float]` with the same rules as
`process_uncertainty`: every macro mandatory, derived never pasted, frozen on
construction. `core/foods/nutrition_of.py` adds one term to
`_interval_for_recipe`'s half-width, weighted per line exactly as
`_composition_band` already weights composition uncertainty.

Measured, at `q = 0.30` (full per-line table in §9):

```
dal_tadka (150 g katori)          masala_dosa (150 g)
  toor_dal_cooked  95.00 g  0.032   rice_milled_raw 26.00 g  0.115
  water            20.20 g  0.149   water           51.00 g  0.059
  onion_raw        12.00 g  0.250   potato_boiled   44.00 g  0.068
  sunflower_oil     5.00 g  0.300   gingelly_oil     3.50 g  0.300
  salt_iodised      0.80 g  0.300   salt_iodised     1.00 g  0.300
```

The cap introduces **no new constant** — `_RECIPE_MASS_TOLERANCE` already
exists. It does change that constant's status, and this must be handled rather
than noted: `models.py` currently documents it as "not a nutritional constant —
it is an authoring-consistency check on our own data." The moment it sets the
width of a displayed band it *is* a nutritional constant and must move to
`citations.py` under the second invariant. That move is part of this design, not
a follow-up.

### What this does to the numbers

Per-recipe band, one serving unit, today versus flat versus capped:

```
                 today                              capped 0.30
dal_tadka    energy 28% protein 25% fat 34% Na 25%  → 40% / 30% / 62% / 55%
masala_dosa  energy 29% protein 25% fat 39% Na 25%  → 47% / 44% / 69% / 55%
onion_raita  energy 25% protein 25% fat 25% Na 25%  → 29% / 28% / 27% / 49%
phulka       energy 25% protein 25% fat 25% Na 25%  → 28% / 28% / 28% / 55%
rajma_chawal energy 26% protein 25% fat 33% Na 25%  → 36% / 32% / 61% / 55%
sambar_sadam energy 26% protein 25% fat 32% Na 25%  → 38% / 35% / 60% / 55%
```

A flat uncapped 0.30 would have put every one of these at 55–69% across the
board, including protein and carb. The cap is what buys precision where the data
has some and spends it where the data has none.

## 5. Authored versus sourced, mechanically

The rule must be mechanical, because a per-recipe judgement is exactly the
self-attestation the round-4 addendum rules out.

**A line's quantity is sourced only if the line names the registered constant
that determined it.** Proposed field, on `RecipeIngredient`, alongside the
existing `process_key`:

```yaml
- id: toor_dal_cooked
  quantity_g: 95.0
  state: cooked
  quantity_from: yield.toor_dal_boiled   # optional; absent means authored
```

- **Absent ⇒ authored ⇒ the full band.** The cheapest authoring path is the
  widest, which is the ordering the round-4 addendum demands and the opposite of
  what a `quantity_uncertainty:` field in the YAML would produce.
- `quantity_from` is validated against the registry at load time, the way
  `process_key` already is, so it cannot name a constant that does not exist.
- A sourced line still carries the *constant's own* uncertainty — it becomes a
  process term, not a zero. Nothing about naming a source makes a line certain.

**Today every line in `data/recipes/` is authored.** Six recipes, 49 lines, zero
`quantity_from`. `dal_tadka`'s note "About 38 g dry toor dal, via
yield.toor_dal_boiled" is prose, not an attribution, and the 38 g it converts
from is itself authored — so the honest reading is that the whole line is
authored, and this design does not let a comment upgrade it.

## 6. The confidence label

Derived from whether the band could change the verdict, using the same shape as
the day-budget display (`docs/methodology.md`, "Sodium is a day budget"):
thresholds come from the measured band against the target's own bounds, not from
a chosen number.

For each bounded macro, with point `p`, band half-width `h`, and `room` = the
distance from `p` to the bound it is nearest (half the window where a macro has
both a floor and a ceiling):

- **confident** — no bound falls inside `p ± h`. Every point in the band gives
  the same verdict.
- **rough** — some bound falls inside the band, but `h ≤ room`. The verdict
  could flip, but the data is at least the same order as the tolerance.
- **very rough** — some bound falls inside the band and `h > room`. The estimate
  cannot distinguish passing from failing on that macro at all.

Worst macro wins. One label per plan, alongside the existing `dev_mode`
disclosure, never in place of it.

### What it says about today's plate — and the finding

The reference profile declines, so the label needs a plate the real library can
actually produce. The nearest one that solves with **zero** relaxation rungs is a
45 kg / 165 cm / 35 / female / active / maintain profile, north Indian lunch:
`phulka ×1, dal_tadka ×3, onion_raita ×1`.

```
target  energy [656.9 .. 726.0]  protein [28.0 ..]  fat [17.96 .. 24.30]
        carb [82.7 .. 111.9]     fibre [9.68 ..]    sodium [.. 1400.0]
point   energy 702.1  protein 29.2  fat 22.4  carb 93.7  fibre 17.0  Na 1274.3

today (no quantity band)   → VERY ROUGH
    energy h=188.8 room=34.6 | protein h=7.3 room=1.2 | fat h=7.1 room=3.2
    carb   h=23.4 room=14.6  | sodium  h=318.6 room=125.7
with capped 0.30           → VERY ROUGH  (bands 37/30/53/31/35/54%)
```

**The label is decoration today, and saying so is the finding.** Every plate the
library can produce is already *very rough* before this design adds anything, by
factors of 2–6 on every gated macro. Adding the widest defensible authored-
quantity band cannot move a label that is already in its worst bucket.

Worse, it does not become live at the obvious trigger either. Simulating Task 6
— every ingredient verified, `composition.unverified_secondary` 0.25 replaced by
`composition.verified_primary` 0.05 — on the same plate:

```
after Task 6, no quantity band  → VERY ROUGH
    energy h=48.4 room=34.6 | protein h=1.5 room=1.2 | fat h=2.6 room=3.2
after Task 6, capped 0.30       → VERY ROUGH
    energy h=153.7 room=34.6 | sodium h=254.9 room=125.7
```

Even with fully verified composition data, energy's half-width (48.4 kcal) still
exceeds the room the ±5% energy tolerance leaves (34.6 kcal). **`confident` is
structurally unreachable**: composition uncertainty of 5% on every ingredient
produces a ~7% band on plate energy, and the energy tolerance is 5%. The three
buckets are not three buckets — they are one bucket and two that nothing can
enter.

That is not an argument against the label. It is an argument for reporting it
honestly and for recording what would have to change: the energy tolerance and
the composition band are the same order of magnitude, and until one of them
moves, the honest label for every plate this system produces is *very rough*.
Both remain project-decision constants nobody has revisited since they were
registered independently of each other.

### The one thing that is not decoration

Alongside the label, report the **dominant term** in the band — composition,
authored quantity, or process — as a share. It is derived, needs no constant,
and it is the only part of this design that gives a recipe author feedback that
moves when they change something:

```
sodium 1,274 mg (+/-54%) — very rough; 55% of that band is authored quantity
energy   702 kcal (+/-37%) — very rough; 68% of that band is composition data
```

The label says the estimate is poor. This says *which unread number to go and
read*, and it discriminates today, which the label does not.

## 7. The perverse-incentive check

CLAUDE.md documents the incentive from the start: gating on interval overlap
would let worse data pass more easily. This design widens bands on data that was
already the weakest, so the question is fair — does anything push back?

Honestly, three answers, in descending order of how much they matter:

1. **The eligibility filter is the real counter-pressure, and it is stronger
   than any label.** A recipe whose combined band exceeds
   `eligibility.max_protein_uncertainty` (0.15) or
   `eligibility.max_energy_uncertainty` (0.20) is *removed from the candidate
   pool*. Widening a band does not make a recipe easier to use; it makes it
   unusable. That is real counter-pressure and it already exists.
2. **It is currently saturated, which is why nothing is felt.** All four
   north-lunch recipes already breach both ceilings — protein 0.250 against
   0.15, energy 0.250–0.276 against 0.20 — and only `dev_mode=True` keeps them
   in the pool. Widening them further changes nothing, because they are already
   as excluded as exclusion goes.
3. **The label itself is decoration, per §6.** It cannot fall further than the
   bucket everything is already in.

So: **the counter-pressure question has a real answer, and it is not the
label.** The mechanism that punishes wide bands is the eligibility filter; the
label neither adds to it nor undermines it. The label's honest job is disclosure
to a reader, not incentive to an author — and it should be described that way in
`methodology.md` rather than credited with a pressure it does not exert.

One thing this design deliberately does *not* do: let the label, or the band,
touch a bound. Uncertainty stays off the ladder and off the gate. That is what
keeps this from becoming a knob.

## 8. Interactions

**`dev_mode`.** No change to when it applies. It is already permanent for a
different reason (every constant is `verified=False`), and this design adds a
`verified=False` constant that every recipe depends on, so nothing tightens. The
label and `dev_mode` must be reported as separate lines: `dev_mode` says "nobody
opened the sources"; the label says "and here is how wide that leaves the
answer." Collapsing them loses the second, which is the one that varies.

**The 15% shipping threshold, which is already unsatisfiable.** Measured on the
plate above, today: `unverified_energy_kcal = 519.0 of 702.1 = 73.9%` against a
threshold of roughly 15%. Two things follow, and neither should be hidden:

- The current figure is *wrong in both directions*, exactly as the round-4
  addendum predicted. `_depends_on_unverified` charges a recipe's **whole**
  energy when any process constant is unverified (dal_tadka's 519 kcal charged
  for a 5 g tempering line) and charges **nothing** for unverified composition
  (phulka and onion_raita contribute 0.0 despite resting entirely on
  hand-entered rows). 73.9% is not the true figure; it is two large errors that
  happen not to cancel.
- Attaching `quantity.authored_domestic` to every recipe pushes it to 100%
  under any reading. That is not this design making things worse — it is this
  design making an already-true fact visible. **Nothing can ship as validated,
  and the threshold is not the reason; it is now simply louder about it.**

Recommendation: do not touch the threshold in this work. Fix the denominator
first (round-4 addendum), or the fix will be measured against a number that is
known to be wrong.

## 9. Tests, and what changes

Changed, because they pin band arithmetic that gains a term:

- `tests/test_nutrition_of.py` — `test_uncertainty_fraction_of_the_plate`
  (0.2751722 for energy), `test_uncertainty_fraction_of_the_plate`'s protein
  0.25, and the hand-computed half-widths in the comments at lines 39–73. The
  arithmetic in those comments must be **re-derived by hand**, per CLAUDE.md, not
  adjusted until green.
- `tests/test_planner_candidates.py`, `tests/test_recipes.py` — the 0.250 /
  0.276 eligibility figures.

New, and each must be shown to fail on the defect it names:

- The cap is real: a 0.8 g line and a 95 g line in the same 150 g recipe get
  different bands, and the large one's band equals the mass tolerance, not the
  constant.
- **Perturbation, per the round-4 addendum:** change
  `quantity.authored_domestic` in the registry and assert every recipe's
  computed `quantity_uncertainty` moves. A test comparing a stored YAML figure
  against itself cannot catch a stale paste; there is no stored figure by
  design, and this proves it.
- Absence is the widest case: a line with no `quantity_from` gets the full
  constant, and no code path produces 0.0 for a macro.
- The label is derived: construct a target whose room exceeds the band and get
  `confident`; narrow the room and watch it degrade — the test must exercise all
  three buckets even though the real library only ever produces one.
- The label does not gate: perturb every band, assert `passed`,
  `relaxation_applied` and the chosen plate are byte-identical. This is the
  interval-perturbation test from the day-ledger slice, applied one layer up,
  and it is the only thing standing between a display band and the validator.

Untouched: the web suite, the deliberately-red
`test_declared_uncertainty_is_backed_by_registered_constants`, finding 15.

### Retroactive application

All six existing recipes gain a band on next load, with no file edit — that is
the point of deriving rather than storing. No verdict moves, because gating is
on the point estimate and no point estimate changes. The measured consequences
are confined to displayed bands (§4), the eligibility figures (which are already
past their ceilings), and the unverified fraction (§8).

## 10. Probes

Not `demo.py` invocations, because none of this is implemented — a probe
measures something that does not exist yet. They are **tracked**, in
`docs/design/probes/`, for the reason finding 11 exists: a rule requiring pasted
evidence was satisfied for months by a script nobody could run, and an untracked
probe here would be the same defect in the same repo.

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/t3_shares.py
```

| Figure | Probe |
|---|---|
| §1 discretionary macro shares | `t3_shares.py` |
| §4 per-line capped bands and per-recipe bands; §8's 73.9% | `t3_capped.py` |
| §6 the 45 kg reference plate | `t3_sweep.py` |
| §6 labels, today and under a simulation of Task 6 | `t3_future.py` |

Each loads the real library through `core.planner.plan.load_library` and touches
nothing else. They are not tests, nothing runs them in CI, and they will report
different numbers as the library grows — which is why the figures above are
dated.

## 11. What this forecloses, and what it does not

- It does **not** decide the energy-tolerance-versus-composition-band collision
  in §6. It measures it and names it. That is a target-model question, not a
  recipe-data one.
- It does **not** fix the unverified-energy denominator (§8). It makes the
  existing error louder and says so.
- It leaves the two-class alternative — separate constants for discretionary and
  bulk lines — available. Decision 1 rules it out for now and §4's cap makes it
  unnecessary, since the cap already produces the two-class *behaviour* from one
  constant. The trigger to revisit is a recipe where the mass check does not
  discriminate: one whose discretionary lines are a large fraction of its mass.
  `masala_dosa` is closest today at 12.3%, and still discriminates.
