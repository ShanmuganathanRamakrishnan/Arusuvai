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

## T4 — Write six recipes — **NEXT**

T3 has landed as design only, so **nothing in the recipe file format has
actually changed yet**. Two options, and this needs a decision before drafting:
write the six recipes against today's format and let the derived band apply
retroactively (which is what `docs/design/recipe_quantity_uncertainty.md` §9
says happens, with no file edit); or implement that design first so the new
recipes are authored under it. The design deliberately adds no required field —
`quantity_from` is optional and absence is the wide case — so the first option
loses nothing.

T3b changes nothing here: finding 21 is about a label that is not built and a
tolerance nobody compared to anything. No gate, target or recipe format moves.
Six new recipes will widen no band and narrow none.

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

## T5 — Slice 2: the DIAAS reversal

**Detail to be filled in when reached.** Spec is in
`docs/design/target_model_v2.md`.

Protein quality stops inflating the gram target and becomes a constraint on
source selection. Prediction already recorded, unrevised: protein day floor
124.4 → 112.0, carb 341.6 → 354.0, lunch carb ceiling 137.5 → 142.5, lunch
protein floor 43.6 → 39.2.

**Note in the commit:** slice 2 in isolation makes the artefact plate
_easier_ to reach — a lower protein floor gives the solver more room to
answer protein with dal, and the correction only arrives with the
quality-source rule. This is not a regression.

---

## Queued, not yet detailed

- Slice 3 — protein per-meal floor and ceiling.
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
