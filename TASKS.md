# TASKS.md

Working queue. Lives in the repo, versioned with the code, read directly by
Claude Code.

## How to work this file

Take the topmost task marked **NEXT**. Do only that task.

Every task ends the same way:

1. **Verify** — run the task's stated verification. Paste the raw
   transcript. Not a description of it.
2. **Commit** — one task, one commit, task ID in the message.
3. **Reconsider the queue** — state whether anything you found changes,
   invalidates, or reorders any task below. This is not a formality: this
   queue has been rewritten twice because a task's result changed what
   should come next.
4. **Stop.** Do not begin the next task. Mark this one DONE, mark the next
   NEXT, and wait.

If a task turns out substantially larger than described, stop and say so
before doing the work. If a task is blocked, say what by. Do not work
around a blocker.

Do not fix things you notice in passing. Log them as findings in
`docs/audit_log.md` and leave them.

---

## T1 — README — **DONE** (`e454644`)

The repo has no README. Everything interesting about this project is
invisible from outside.

**Audience:** a technical hiring manager giving it 90 seconds. They will not
clone it, install Ollama, or run the suite.

**Must land in the first screen:**

- The LLM never computes. It ranks pre-validated combinations and fills
  narration templates. Every gram, bound and verdict is deterministic
  Python.
- The system tracks its own uncertainty and declines rather than guessing.
  `dev_mode` is the system correctly reporting unverified inputs, not an
  unfinished state.

**The section that makes this repo unusual** — defects the project caught
in itself. A sentence or two each, each linking to its `docs/audit_log.md`
entry. Frame as the point of the project, not as apologies. Draw from:

- a salt figure whose stored note claimed a derivation that does not
  produce it;
- a rule requiring pasted transcripts, satisfied for months by a script
  that was never committed;
- a sodium ceiling that looked strict but was widened 50% by the ladder,
  permitting one plate to exceed a day's allowance;
- a decline diagnosed as a sodium wall that was a joint energy-vs-sodium
  infeasibility;
- enumeration order varying with hash seed.

**Also cover, briefly:** what it does; the two-stage pipeline; current
state stated honestly (four templates, small library, one verified
ingredient, `dev_mode` on); evidence discipline; how to run `demo.py` with
the reference transcript; scope boundaries pulled from
`docs/methodology.md`; links to the three docs.

**Constraints:** accurate to the repo as it is today — verify every claim
against the code. No aspirational features. No badges asserting unmeasured
things; if a test count appears it must be real and the deliberately-red
test noted. Not 2000 words.

**Verify:** state which claims you checked against code and how. List
anything you wanted to write but could not substantiate.

---

## T2 — Finding 18: deterministic enumeration order — **DONE** (`b9e14bf`)

`TemplateSlot.accepted_categories` is a frozenset and `candidates.py:110`
iterates it, so order follows `PYTHONHASHSEED`. Five runs of pre-1a code
gave two orderings. Verdicts are stable; byte-for-byte reproduction is not
— which is what `demo.py` exists to guarantee and what 1a's acceptance
asserted.

**This is verdict-visible, not a tidy-up.** Sorting changes enumeration
order, which can change which plate wins among near-equal scores. Own
commit, never folded in.

**Step 1, before changing anything.** Run `demo.py` for the north_lunch
reference profile across at least 10 `PYTHONHASHSEED` values. Report: how
many distinct orderings appear; per ordering the selected plate, unit
counts, score, verdict; whether the winner is stable across seeds.

**If the winner changes with seed, stop.** That is a worse finding than
finding 18 — it means published results depended on a hash seed. Record it
properly before fixing.

**Step 2.** Make ordering deterministic wherever a set or frozenset feeds
enumeration or candidate assembly. Grep the enumeration and solver paths
for other instances; report what you find including any you decide not to
change and why. Choose a stable, meaningful sort key (component id is the
obvious candidate) and state the reasoning.

**Step 3.** Commit message carries before/after on enumeration order,
selected plate and score, verdict. If the plate changed, say so
prominently. If nothing changed, note that this is a statement about this
library at this size, not a guarantee for a larger one.

**Step 4.** A test asserting order stability, demonstrated to fail on the
defect. Close finding 18 in the audit log. **Also record the
meta-finding, unsoftened:** finding 11 was closed on a reproducibility
claim, and 1a's acceptance asserted byte-identical output; neither could be
reliably true while order was seed-dependent. Second instance of a
reproducibility rule satisfied literally while missing its purpose — log as
a pattern, not an incident. Re-verify whether finding 11's closure now
holds.

**Verify:** the seed sweep, before and after.

---

## T3 — Design: declared estimates and a confidence label — **DONE**

Delivered: `docs/design/recipe_quantity_uncertainty.md`. Two findings raised
(`docs/audit_log.md` 19 and 20), both OPEN. Honest read on the counter-pressure
question: **the label is decoration** — it has one reachable value today and
still has one after Task 6 — and the real counter-pressure is the eligibility
filter, which is itself saturated.

Design only. No recipes, no implementation.

Task 5b established that every salt quantity was authored to be plausible,
not sourced, and that 91.7% of a blocking sodium figure came from four such
numbers. No authoritative table exists for how much salt goes in a dal.
This task stops pretending recipe quantities are measurements.

**Three decisions already made — design to them, do not reopen:**

1. **One uncertainty constant, not thirty.** A single registered
   `PROJECT_DECISION` constant covers all authored recipe quantities.
   Per-quantity bands mean guessing the value and guessing how wrong the
   guess is — two layers of invented precision, and thirty bands would
   never be audited. Propose the value with reasoning.
2. **Gating stays on the point estimate.** Bands do not gate. State
   plainly in the design that this is already current behaviour and
   therefore changes nothing on its own.
3. **Every plan reports a confidence label** — plain-language
   (_confident_ / _rough_ / _very rough_), derived from band width relative
   to the room the targets allow. Not a gate. Reuse the day-budget display
   mechanism (thresholds computed from the measured band, not chosen); do
   not invent a second uncertainty mechanism.

**Must cover:** where the constant lives and how it applies at load time;
what counts as authored vs sourced, mechanically rather than per recipe;
how the label is computed and what it says about today's reference plate,
measured; **the perverse-incentive check** — wider bands passing more
easily is documented from the start and this makes it worse, so state
whether the label is real counter-pressure or decoration (if decoration,
that is a finding); interaction with `dev_mode` and the 15% threshold;
tests that change; bands added retroactively to existing recipes and what
that does to measured results.

**Verify:** the measured before/after on the reference profile, and your
honest read on the counter-pressure question.

---

## T3b — reconcile the two constants that make `confident` unreachable — **DONE**

Delivered: `docs/design/tolerance_versus_band.md`, four options plus one the
brief did not list, none picked. `docs/audit_log.md` finding 21. Probe
`docs/design/probes/t3b_propagation.py`.

**Decision recorded 2026-08-02: deferred.** The contradiction is permanent but
inert — the label is not built, so nothing reads either constant against the
other. **Do not build the confidence label** until this is settled; building it
first forces the choice from inside an implementation. Reopen when the label is
scheduled, or when a surface states a "within 5% of your energy target" claim.

**T3b's own premise was wrong and is corrected in the finding.** Composition
uncertainty does **not** accumulate across components — measured flat at exactly
`u` for 1 through 6 components — so "at what component count does it stabilise?"
has no answer. The real defect is narrower: `composition.verified_primary` and
`tolerance.energy_default` are both 0.05, so the comparison collapses to point
versus target midpoint. Energy-only; `fat_carb_default` at 0.15 is fine.

Insert before T4. Small, but it invalidates the stated purpose of two
queued tasks until it's settled.

**Decision task, not a data task.** No verification work, no recipes.

## What T3 measured

A ±5% ingredient composition band produces roughly ±7% on plate energy,
because errors accumulate across the components of a plate.
`tolerance.energy_default` is 5%.

So the band is structurally wider than the tolerance it is checked against,
and `confident` can never be reached — measured under full simulated
verification, energy's half-width was still 48.4 kcal against the 34.6 kcal
the tolerance leaves.

These two constants were registered independently and have never been
compared to each other. Neither is wrong on its own. Together they are
incoherent.

## Why this blocks other work

Task 6 (verify the ten north_lunch ingredients) was justified partly on the
expectation that verification would tighten the confidence picture. T3
showed it does not. Slice 4 inherits the same assumption. Both need this
resolved before they can claim what they currently claim.

## What to do

### 1. Establish the relationship properly

Show how a per-ingredient composition band propagates to plate level across
a realistic component count. Is the ~7% figure specific to the reference
plate, or general? At what component count does it stabilise?

Do the same for every other gated macro, not just energy. Report which
tolerances are and are not exceeded by their propagated bands.

### 2. Lay out the options — do not pick

At least these:

- **Widen the tolerances** so they exceed the propagated band. What
  justifies the new value, and does a wider tolerance make the gate
  meaningless?
- **Tighten the composition bands.** What would have to be true of the
  data for a narrower band to be honest? Is it reachable with verified
  IFCT rows, or not?
- **Compare like with like** — gate against a propagated tolerance derived
  from the band rather than a flat registered figure, so the two are
  related by construction rather than by coincidence.
- **Accept it and remove `confident`** from the label scale, documenting
  that the top state is unreachable with data of this kind.

For each: what it costs, what it makes claimable, what it forecloses, and
whether it introduces another arbitrary number.

### 3. State which existing claims are affected

Anywhere in `CLAUDE.md`, `docs/methodology.md` or the audit log that
implies verification will improve confidence, or that treats these
tolerances as independently chosen. Quote them.

### 4. Record it

New finding in `docs/audit_log.md`: two independently registered constants
in permanent contradiction, neither wrong alone. Note that this is the same
class as the salt-note defect — a value that cannot do what its neighbours
assume it does.

Update T4, Task 6 and slice 4 in `TASKS.md` to reflect what they can no
longer claim.

## Do not

- Change either constant. This task ends with options, not a choice.
- Start T4.
- Verify any ingredient.
- Touch the web suite, the deliberately-red test, or finding 15.

## Verify

The propagation arithmetic, measured with the command shown. Probes tracked
in `docs/design/probes/`, not pasted-and-lost.

## T4 — Write six recipes — **DONE**

Written against today's format, per the design's own §9: the derived band
applies retroactively with no file edit, so authoring under the unimplemented
T3 design would have gained nothing.

Delivered: `sambar`, `coconut_chutney`, `carrot_poriyal`, `thayir_plain`,
`aloo_sabzi`, `carrot_kootu`. No new ingredient rows — every dish is built from
the existing 26, and where the usual ingredient was missing (drumstick, cumin,
roasted chana dal, beans) the substitution is named in the file rather than made
silently.

**Five would have sufficed**, not six: `sambar` is accepted by both
`south_breakfast.gravy_accompaniment` and `south_lunch.gravy`. The sixth,
`carrot_kootu`, is there because `enumerate_combinations` uses
`itertools.combinations` and cannot repeat a component, so `south_lunch.vegetable`
(min 1, max 2) behaved as a fixed-length slot with one candidate — the only
genuinely variable-length slot in the template module was untestable.

Result: all four templates enumerate (1 / 3 / 8 / 2). `no_candidates` is gone.
`docs/methodology.md` limitation 5 CLOSED. `north_dinner` produces plates for
the first time. All four still decline for the reference profile, on named
macros — **sodium in all four**, with two `south_lunch` combinations above the
guard at minimum counts: `docs/audit_log.md` finding 22, OPEN, deliberately not
resolved here.

Scope, fixed now: six recipes, enough to make all four templates enumerate
— one sabzi (north_dinner), a gravy and a chutney (south_breakfast), a
gravy, a vegetable and a curd course (south_lunch). Confirm against the
actual templates rather than trusting this list.

Four live templates is the point at which the solver can be judged on
whether it produces sensible plates. It also makes Option C — the
principled sodium reservation, currently inert because breakfast and dinner
enumerate zero — live for the first time.

Continental cuisine is out of scope: a new region axis needing its own
templates, slots and vocabulary. Deferred alongside the non-vegetarian
axis.

---

## T5 — Slice 2: the DIAAS reversal — **DONE**

**All four predicted figures held exactly**, measured after the change:
protein day floor 124.4 → 112.00, carb day 341.6 → 354.01, lunch protein
floor 43.6 → 39.20, lunch carb ceiling 137.5 → 142.49.

Two consequences beyond the prediction:

- **The carb target is now diet-independent.** `base_g` does not depend on
  diet, so neither does the energy remainder. A vegan and a non-vegetarian of
  identical body and goal used to get carb targets ~37 g apart.
- **`Profile.diet` now changes no target value at all** until slice 4. Stated
  in `docs/methodology.md` and asserted by two tests that exist to make the
  gap visible rather than to bless it.

As predicted, the plate got easier: `north_lunch` and `north_dinner` now pass
for the reference profile — the first plates this system has served for it —
after four rungs, with the protein shortfall disclosed. Not a validation of
the change; the plate the quality-source rule is meant to reject is exactly
the one a lower protein floor makes reachable.

Spec was `docs/design/target_model_v2.md`.

---

## D1 — Decide finding 22: the sodium guard or the salt figures

**Decision task.** Some South Indian combinations are unplannable at any
setting: two of `south_lunch`'s three have a sodium floor above the 1400 mg
guard with every component at its minimum count. Not a demanding-profile
problem — those plates are impossible.

Both sides of the comparison are unsourced project decisions:

- the guard is `day_budget.absurdity_fraction` (0.70) x `nutrient.sodium_max_mg`
  (2000), derived from meal-split fractions that are themselves project
  decisions, and never checked against a plate with four salt lines in it;
- the salt figures are 0.33–0.67% of finished weight, each with a written
  reason and none with a source.

So this is a choice between two numbers nobody measured, and saying that plainly
is part of the decision. **Lowering a salt line until plans pass is not on the
table** — that is the defect the salt notes exist to prevent.

Worth considering alongside: design slice 10 (reserve instead of guess) replaces
the guard with a bound derived from the library. Its stated trigger —
`south_breakfast` and `north_dinner` each enumerating at least one combination —
**fired with T4**. It may make this decision moot rather than needing an answer.

## D2 — Paneer, tofu and soya rows, then slice 4

### D2a — the ingredient rows — **DONE** (2026-08-02)

Three rows (`paneer_fresh` 1.00, `tofu_firm` 0.65, `soya_chunks_dry` 0.85) and
three recipes (`paneer_masala@sabzi`, `tofu_bhurji@sabzi`,
`soya_chunk_curry@legume_curry`). No fourth row was needed. All three DIAAS
figures are **authored at the low end of a recalled range, not sourced**; no
evidence grade moved and `dev_mode=False` still empties every pool.

Two results that change what follows:

- **Both north templates now pass for the reference profile with zero
  relaxation** — the first plates it has ever been served on the real library.
  The cause is sodium, not protein: tofu bhurji fills the `sabzi` slot with
  less salt per calorie than aloo sabzi. Enumeration is now 1 / 3 / 24 / 12.
- **Finding 25 raised:** no high-quality source can reach `south_breakfast` at
  all — its slot grammar accepts `tiffin`, `sambar`/`kuzhambu`,
  `chutney`/`podi`, `beverage` and nothing else. A per-meal quality floor will
  make that template unsatisfiable for a structural reason, not a thin-library
  one.

### D2b — slice 4, the quality-source rule — **NEXT**

Slice 4 cannot do anything without D2a: `curd_dahi` was the only row above
DIAAS 0.62, so the quality-source rule shipped before it made every plate
decline. Note what D2a now puts at stake — **both passing plates are carried by
`tofu_bhurji`, whose 0.65 does not qualify.** Slice 4 is therefore expected to
take back the two verdicts D2a just produced, and finding 25 says
`south_breakfast` has no way to satisfy the rule at all.

Also closes finding 23 — `web/onboarding.js` asks for diet, stores it, and since
slice 2 nothing reads it for gating. Either slice 4 lands or the wizard says so;
both are defensible and the second is nearly free.

Note the ingredient rows are Task 6 territory (evidence grades), so this needs
sequencing against it rather than being assumed independent.

## Queued, not yet detailed

- Slice 3 — protein per-meal floor and ceiling. **DONE.** Two
  `PROJECT_DECISION` constants (0.15 / 0.50 of the day protein floor). The
  floor is `max(share, guard)`, a departure from the design's table, which
  read literally would have dropped the reference lunch floor 39.2 -> 16.8;
  it binds on the snack slot alone. The ceiling is a backstop the solver
  cannot reach by its own scoring — it binds only when an energy floor drags
  protein up. No verdict moved on the real library. Finding 24 raised: when
  the ceiling empties the set, the decline names energy, not protein.
- Slice 4 — quality-source rule. Blocked until paneer/tofu/soya rows exist;
  `curd_dahi` is currently the only qualifying row, so shipping early makes
  every plate decline. **Cannot claim** it improves the confidence picture:
  finding 21 shows energy confidence is fixed by neither more data nor better
  data, only by reconciling two constants.
- Finding 15 — combo component alongside its own base. May partly dissolve
  once the quality rule stops volume-based protein; do not mistake that for
  closing it.
- Task 6 — verify the ten north_lunch ingredients; narrow the `dev_mode`
  exit; build the unmet plumbing. First point at which anything can be
  certified. **Scope corrected by finding 21:** measured, verification takes
  the reference plate's energy band 27% → 6.89% and protein 25% → 5%, which
  clears both eligibility ceilings — that is the justification, and it holds.
  It does **not** improve energy confidence, which no verification can. Do not
  justify this task on the confidence picture.
- Web suite — 12 failed / 30 errors, undiagnosed. Split: make conditional
  passing honest; triage with a hard ceiling.
- The red test — `test_declared_uncertainty_is_backed_by_registered_constants`.
  Raw-vs-lazy-author question, instances now on both sides.
- Decline screen rebuild — name the blocking constraint, distinguish
  relaxable from locked, surface the hypertension lock and `dev_mode`.
  `bound_source` already ships as a machine token; it must never render raw
  (`test_web_no_identifiers.py` sweeps for snake_case).
- Non-vegetarian diet axis.

## Not scheduled

Cost and pricing. Commerce and delivery. Landing page plate animation.

## Standing constraints

No evidence grade moves outside Task 6. Do not touch the web suite, the
deliberately-red test, or finding 15 unless the task says so. Every number
in a report is measured, not asserted, with the command shown.
