# Audit log

Dated, append-only. Per CLAUDE.md's audit-workflow section, this file is the
artifact: a finding that isn't written here did not happen. Findings are
recorded whether or not they are fixed; the "Disposition" line says which.

Newest entries at the top.

---

## 2026-08-12 — CLAUDE.md restructured to 199 lines; six stale claims corrected

`CLAUDE.md` went from 652 lines to **199**. No behaviour changed: `437 passed,
68 skipped` before and after, and `demo.py`'s plate, unit counts, point estimate
and band are identical.

New files: `docs/design/architecture.md`, `docs/design/round4_addendum.md`,
`docs/repo_policy.md`, `docs/build_status.md` (the build table, moved by
extraction rather than retyping), and directory-level `core/CLAUDE.md`,
`web/CLAUDE.md`, `tests/CLAUDE.md` — which now carry the **open-findings index**,
so a session meets the findings for the code it is editing rather than having to
know to look. `docs/methodology.md` gained an appendix for the three rules that
already had a section there.

### Six stale claims corrected on the move — not carried across

The rule applied: nothing moves verbatim without being read against this file
first. Recorded here because five of the six had been true when written and
quietly stopped being true, which is the class the restructure was most likely
to launder into a fresh-looking home.

1. **`web/` described as "Next.js"** in the architecture tree. It is static
   HTML/CSS/JS and always has been in this repo; the build-status table 20 lines
   below said so. Corrected in `docs/design/architecture.md`.
2. **Pipeline steps 5 and 6 (LLM ranking, narration) read as built.** They are
   specification. Marked not-built.
3. **The round-4 addendum's five items read as an outstanding queue.** All five
   are built. Each now carries a dated status line; carried across unchanged the
   file would have presented finished work as a TODO list.
4. **The audit-workflow section described `.claude/agents/auditor.md` and
   `.claude/commands/grill.md` in the present tense** while the build table
   recorded that they do not exist. Re-verified: `.claude/` has neither
   directory. Rewritten in `docs/repo_policy.md` with the gap stated first.
5. **The uncertainty filter claimed a conservative-estimate arm that does not
   exist.** `CLAUDE.md` said an over-ceiling recipe is excluded "**or** its
   contribution estimated conservatively (high-end)". `core/planner/candidates.py`
   either excludes the candidate or, in `dev_mode`, keeps it and records an
   `EligibilityFlag`. There is no conservative-estimate path and no evidence
   there ever was. The clause was dropped, not transcribed.
6. **`docs/methodology.md`'s own "What is not built" section had gone stale** —
   it listed `api/`, `web/` and `core/nutrition/targets.py` as unbuilt. All three
   exist. The Phase 3 text is retained as dated evidence, behind a correction.

Separately, the **15% shipping threshold** was moved with a correction attached
rather than a rewrite: it is stated as though it were the operative gate, and
finding 43 established that the protein eligibility ceiling bites first, at
pool-build time, on all four reference plates. The threshold is retained as the
rule it is; it is not what stands between this library and a servable plate.

### Finding 47 — code comments cite `CLAUDE.md` sections that have moved — **OPEN**

Roughly 20 comments across `api/`, `core/foods/` and `core/nutrition/` cite
`CLAUDE.md` by section name — "Uncertainty", "Architecture", "round-4 addendum",
"Relaxation ladder", "'wider tolerance on energy'". Those sections are now in
`docs/methodology.md`, `docs/design/architecture.md` and
`docs/design/round4_addendum.md`. The rules are unchanged and the citations still
date a decision correctly, so nothing is *wrong*; they just point at a file that
no longer contains the named section.

Not fixed in this pass, deliberately: the task protocol says do not fix things
noticed in passing, and a 20-file comment sweep is its own reviewable idea, not
a rider on a documentation restructure.

One exception was fixed, because it is user-visible rather than a comment:
`demo.py` printed `-- CLAUDE.md's shipping threshold is ~15%` on every run, and
`CLAUDE.md` no longer states that threshold. Changed to `-- the shipping
threshold is ~15%`. The number and the check are untouched.

*Disposition:* OPEN. Low stakes; do it as a single sweep when someone is next in
those files anyway.

```
$ python -m pytest tests/ -q
437 passed, 68 skipped, 1 warning in 110.17s (0:01:50)

$ wc -l CLAUDE.md
199 CLAUDE.md
```

---

## 2026-08-09 — D7 handoff: finding 43, and what D10 did to D7's own conclusion

No code changed. Three artifacts added — `docs/design/ifct_sitting.md`,
`docs/design/ifct_transcription_worksheet.csv`,
`docs/design/probes/d7b_after_verification.py` and
`docs/design/probes/d7b_transcription_diff.py` — so the one task in this project
that no automation can perform is one mechanical session rather than an open
question.

### Finding 43 — verifying every ingredient row cannot make any current plate servable — **OPEN**

`docs/design/probes/d7_verification_horizon.py` was written to answer, *before*
a human spends hours with IFCT 2017 open rather than after, whether verifying
the north_lunch ingredient rows would clear the ~15% unverified-energy shipping
threshold. It answered **INGREDIENTS 9.5% → SHIPS**.

That probe ran before D10. D10 gave `idli`, `phulka` and `steamed_rice` a
`process_uncertainty_unassessed` declaration on every macro, mapping to
`process.unassessed_uncertainty` = 0.20 — and D7's conclusion measures the
*second* of two gates while D10 moved the *first*.

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_after_verification.py
Protein eligibility band per recipe, against the 0.15 ceiling
(counterfactual assumes every composition record verified at 0.05 -- the best the sitting can buy)

  recipe                 comp   proc   TODAY    comp   proc VERIFIED   verdict
  idli                 0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  phulka               0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  steamed_rice         0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  [the other 15 recipes: 0.2500 0.0000 0.2500 -> 0.0500 0.0000 0.0500, clears]

  3 of 18 recipes remain protein-ineligible after full composition verification

  south_breakfast    BLOCKED by idli
  south_lunch        BLOCKED by steamed_rice
  north_lunch        BLOCKED by phulka
  north_dinner       BLOCKED by phulka

Cross-check: this probe's TODAY column vs core/
  18 of 18 components agree, 0 disagree.
```

The gate in `core/planner/candidates.py` runs at pool-build time, before
enumeration. A component over the ceiling never enters the pool, so the plate is
never enumerated and never solved — an earlier and harder failure than the
energy threshold D7 was watching for. Every one of the four reference plates
contains one of the three blocked recipes. Composition verification cannot move
them: the 0.20 is a process term, and there is no registered constant for
boiling, steaming or dry-griddle loss to replace it with.

So D7's *stated* conclusion is not wrong about what it measured, and is
misleading about what it implies. Verifying the ten rows is **necessary and not
sufficient**: it takes 15 of 18 recipes from 0.25 to 0.05, and leaves all four
plates unenumerable outside `dev_mode`.

*Disposition:* OPEN. This is finding 41 seen from the other end — 41 is the
missing process constants, and closing 41 is what makes the sitting cash out.
Neither ordering makes the other unnecessary. The sitting is still worth doing;
`docs/design/ifct_sitting.md` states this up front so nobody books the time
expecting a servable plate at the end of it.

### The sitting is realistically five or six rows, not ten

Triage in `docs/design/ifct_sitting.md`. Four of the ten are probably not IFCT
questions at all: `sunflower_oil` (**measured**, 2026-07-24 — IFCT's T012 row
carries no nutrient panel for oils), `ginger_garlic_paste` and `garam_masala`
(household compounds a composition table does not tabulate; the real fix is
decomposition into constituent foods, which is a recipe-data change), and
`salt_iodised` (a stoichiometric derivation deliberately chosen over a measured
value for reproducibility). **Only `sunflower_oil`'s verdict is measured; the
rest are predictions from what IFCT 2017 is, and a wrong one should be recorded
in the worksheet's `notes` as a result.**

Separately: IFCT does not tabulate DIAAS, so the authored 1.00 on `paneer_fresh`
and 0.85 on `soya_chunks_dry` — the latter being the only vegan-eligible row
clearing the 0.75 quality threshold — stay authored no matter how the sitting
goes. That is a different source and a different sitting.

### The worksheet is blind, and the diff writes nothing

`docs/design/ifct_transcription_worksheet.csv` is filled from IFCT alone, without
reading the current fixture values first: every one of these rows is a
hand-entered approximation, and transcribing with the guess visible anchors the
transcription to the guess it exists to check. An agreeing transcription then
looks identical, in the file, to a good approximation.

`d7b_transcription_diff.py` reports MATCH / DIFFERS / NOT FOUND per value, flags
a ratio past 2.5x as a probable raw-versus-cooked basis error rather than a
data-quality one, and **writes nothing** — no fixture edit, no `verified` flip.
That omission is the round-4 self-attestation rule applied to tooling: a script
that filled the fixture in would make running the script the cheapest path *and*
the most confident-looking output.

Shown able to fail before being trusted, per CLAUDE.md — a synthetic
`onion_raw` row exercising all four branches, then reverted:

```
  onion_raw   ifct_code=E011  page=p.142  state: worksheet=raw fixture=raw
      energy_kcal  match             40.00
      protein_g    DIFFERS            1.10 ->       1.40  (1.27x)
      carb_g       DIFFERS            9.30 ->      27.90  (3.00x)  <-- BASIS ERROR?
      fibre_g      NOT FOUND    (fixture holds 1.7)
```

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_after_verification.py
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_transcription_diff.py
```

---

## 2026-08-09 — D10: finding 2 CLOSED, findings 41 and 42 raised

### Finding 2 — a recipe with no `process:` line reads as fully process-certain — **CLOSED**

Open since 2026-07-21. The loader derives process uncertainty per macro from the
constants on each ingredient line, and the design's defence of the zeros was
that they are *computed*, not omitted — something an author cannot obtain by
leaving the work undone. That is true of a macro. It is false of a recipe. With
no `process:` line anywhere the numerator is empty for **every** macro, and the
arithmetic producing that zero is indistinguishable from the arithmetic
producing a real one.

Five recipes are in that population, and they are not the same kind of thing:

```
$ PYTHONPATH=. python docs/design/probes/d10_process_zero.py
process.unassessed_uncertainty = 0.2

recipe               preparation  proc  undeclared      now  combined
----------------------------------------------------------------------
aloo_sabzi           cooked          1      0.0311   0.0311    0.2811
carrot_kootu         cooked          1      0.0177   0.0177    0.2677
carrot_poriyal       cooked          1      0.0274   0.0274    0.2774
coconut_chutney      cooked          1      0.0137   0.0137    0.2637
dal_tadka            cooked          1      0.0255   0.0255    0.2755
idli                 cooked          0      0.0000   0.2000    0.4500  <-- moved
masala_dosa          cooked          2      0.0390   0.0390    0.2890
onion_raita          uncooked        0      0.0000   0.0000    0.2500
paneer_masala        cooked          1      0.0160   0.0160    0.2660
phulka               cooked          0      0.0000   0.2000    0.4500  <-- moved
rajma_chawal         cooked          1      0.0150   0.0150    0.2650
sambar               cooked          1      0.0231   0.0231    0.2731
sambar_sadam         cooked          1      0.0133   0.0133    0.2633
soya_chunk_curry     cooked          1      0.0274   0.0274    0.2774
soya_kuzhambu        cooked          1      0.0260   0.0260    0.2760
steamed_rice         cooked          0      0.0000   0.2000    0.4500  <-- moved
thayir_plain         uncooked        0      0.0000   0.0000    0.2500
tofu_bhurji          cooked          1      0.0235   0.0235    0.2735

Recipes with no process constant at all -- the population D10 rules on:
  idli             cooked        100.8 kcal   cooked; 9 of 9 macros declared unassessed
  onion_raita      uncooked       84.2 kcal   zero earned: nothing is heated
  phulka           cooked         98.9 kcal   cooked; 9 of 9 macros declared unassessed
  steamed_rice     cooked        260.0 kcal   cooked; 9 of 9 macros declared unassessed
  thayir_plain     uncooked       87.0 kcal   zero earned: nothing is heated
```

The `undeclared` column is what each recipe's energy band would be if it
declared neither `preparation` nor an unassessed list — the pre-D10 state, and
what a new recipe gets today if the rule is removed. Before D10 all five sat at
a combined **0.2500**, the composition floor and nothing else: a griddled phulka
claimed exactly the certainty of raw whisked curd.

**The column is a counterfactual, deliberately, not a git-history claim.** D10
changed the loader *and* three recipe files, so today's checkout cannot be asked
what yesterday's produced. The probe recomputes the derivation from the
ingredient lines rather than reading `Recipe.process_uncertainty`, so it runs on
either tree and cannot silently agree with the code it audits — the failure this
log records against `d4_declines.py` on 2026-08-08.

**Fix.** A recipe with no process constant must now say which case it is in:
`preparation: uncooked` (a claim about the food, rejected if any line also
carries a `process:` key) or `process_uncertainty_unassessed`, which takes the
registered wide band. `preparation` defaults to `cooked` — omission is the
cheapest authoring path and the round-4 rule is that the cheapest path must
never produce the most confident-looking output.

**What moved in the product.** Only the displayed band on one plate:

```
-  energy band  : 689.6 - 1172.9 kcal
+  energy band  : 590.7 - 1271.8 kcal
```

No plate, unit count, verdict or relaxation rung, on any of the four templates.
That is the expected shape rather than a lucky one: the validator gates on the
point estimate and intervals are display-only, so a widened band cannot reach a
decision. It reaches the user, which is the entire reason for displaying it.

**The red test.** `test_declared_uncertainty_is_backed_by_registered_constants`
has been red on purpose since 2026-07-24 (see the cross-reference entry of that
date). Reading it again while fixing this: its condition
`if recipe.process_uncertainty:` is **always true**, because
`Recipe.process_uncertainty` is mandatory per macro and never empty. So the
assertion it actually made was "every recipe carries a process constant" — which
held only by accident until `idli` and `steamed_rice` arrived in D3 as the
library's first oil-free cooked dishes. It was never a rule worth satisfying.
Rewritten to the invariant it was reaching for (every constant a recipe names is
registered), with the earned-zeros half moved to
`TestZeroProcessUncertaintyMustBeEarned` where the loader enforces it.
`d4b_mutations.py`'s `DESELECT` is now empty; there is no deliberately-red test
in the suite.

**Suite**, both dev servers up so the browser checks actually ran:

```
$ python -m pytest tests/ -q --color=no
........................................................................ [ 14%]
[...]
505 passed, 1 warning in 224.96s (0:03:44)
```

No skips and no failures. The suite has not been all-green since before
2026-07-24 — the deliberately-red test dates from then — so this is the first
run in which every browser check ran and nothing was excluded.

**Disposition: CLOSED.** `core/foods/recipe_loader.py`,
`data/recipes/schema.yaml`, five recipe files, `docs/methodology.md` ("A zero
process uncertainty has to be earned"), D3 limitation 2.

### Finding 41 — a declared process constant still leaves the macros it does not touch at a bare zero — **OPEN**

The rule D10 added fires only when a recipe has **no** process constant
whatsoever. A cooked dish that carries one still derives 0.0 for every macro
that constant does not touch. In this library that is protein on almost every
recipe: oil carries no protein, and oil uptake is the only kind of process
constant registered. Measured —

tail of the same probe run above:

```
Finding 41 -- protein process uncertainty is exactly 0.0 on 15 of 18 recipes:
  aloo_sabzi, carrot_kootu, carrot_poriyal, coconut_chutney, dal_tadka, masala_dosa, onion_raita, paneer_masala, rajma_chawal, sambar, sambar_sadam, soya_chunk_curry, soya_kuzhambu, thayir_plain, tofu_bhurji
  escaping only: idli, phulka, steamed_rice -- the three D10 forced to declare all nine macros unassessed
```

The only three that escape are the three D10 forced to declare all nine macros
unassessed. Every other recipe — including all 13 that were never in finding 2's
population, and `masala_dosa`, which is griddled in oil — still reports a protein
process uncertainty of exactly zero.

This is the same defect finding 2 named, one level down: a zero produced by an
empty numerator, presented as a measurement. It is worth separating because the
remedy is different in kind. Finding 2 was closeable with a loader rule, because
the author knows whether the food is cooked. This one is not: closing it needs
registered process constants for boiling loss, steaming loss and griddle
protein retention, which is a data problem — and per `CLAUDE.md`, Indian-specific
process literature is thin, so the honest outcome may be a row of
`verified=False` conservative estimates rather than sources.

Not fixed here, per the queue rule about tasks turning out larger than
described. Scope is stated in `_check_zero_process_is_earned`'s docstring so the
next reader meets it in the code rather than discovering it.

**It already invalidated a standing claim, which is how it was sized.** Two
tests in `tests/test_nutrition_of.py::TestEligibilityConsequence` went red on
D10, and both were right to:

- `test_every_recipe_sits_at_exactly_the_unverified_composition_band` asserted
  0.25 protein for every recipe, on the premise "oil carries no protein, so no
  process term touches this macro". True of 15 recipes and now false of three.
  Rewritten as two populations with the split named.
- `test_verifying_every_row_would_clear_the_protein_ceiling` asserted that
  flipping every ingredient to verified drops every recipe to 0.05, under the
  0.15 ceiling — i.e. that opening IFCT is *sufficient* to make this library
  shippable. It is not. `idli`, `phulka` and `steamed_rice` land at
  0.05 + 0.20 = **0.25**, still above the ceiling, and no amount of composition
  verification moves them. Renamed
  `test_verifying_every_row_clears_the_ceiling_for_all_but_three_recipes`.

That second one matters beyond D10: the ten-row human sign-off D7 is waiting on
would not, by itself, produce a shippable library. Process constants are a
separate prerequisite nobody had costed, and it took making the zeros honest to
see it.

**Disposition: OPEN.** Blocks nothing today — `candidates.py` gates on the
*combined* composition+process band and composition uncertainty is mandatory per
macro and never zero, so no recipe currently passes eligibility on the strength
of a fake zero. It would matter the moment a verified ingredient exists.

### Finding 42 — the mutation harness ran new code against old data, and reported "covered" for it — **FIXED**

The first D10 sweep returned this:

```
R1   covered      ...::test_silence_is_rejected_because_it_is_the_cheapest_path
R2   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R3   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R4   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R5   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

Four of five rows naming one test that is about none of them. `CLAUDE.md`
already warns that a `covered` row names the *first scoped failure*, which is
collection order rather than relevance, so the rows were re-derived by hand —
apply each mutation, run `tests/test_recipes.py`, take the whole failure list:

```
--- R1: a cooked dish may not derive zeros from silence  (1 red)
       TestZeroProcessUncertaintyMustBeEarned::test_silence_is_rejected_because_it_is_the_cheapest_path
--- R2: preparation defaults to cooked, the demanding case  (28 red)
       ...the library does not load at all...
--- R3: an unknown preparation is rejected, not assumed  (1 red)
       TestZeroProcessUncertaintyMustBeEarned::test_an_unknown_preparation_is_rejected_rather_than_assumed
--- R4: 'uncooked' and a process: line cannot both be true  (1 red)
       TestZeroProcessUncertaintyMustBeEarned::test_an_uncooked_dish_may_not_also_name_a_process
--- R5: a macro the dish contains none of is not the author's to justify  (0 red)
```

R5 is **red in the harness and green by hand**, which is not a difference the
mutation can explain. Cause: `main()` copies `core/` and `tests/` into the
worktree from the working tree and leaves everything else at HEAD — including
`data/`. D10 edited five recipe files, so the worktree ran the new loader
against the old YAML, every one of those five was rejected on load, and the
session-scoped `library` fixture errored on **every** run. The rows were
measuring a mismatch the harness created, mutation or no mutation.

This is finding 35's family — a harness is itself a measurement — and the same
class of blind spot: finding 35 was about parsing tool output, this is about
what the tool was pointed at. The docstring's claim, "the worktree contributes
isolation and nothing else," was the thing that was false.

**Fixed**: `data/` is copied from the working tree alongside `core/` and
`tests/`, and the docstring says why.

**And R5 was a genuine hole.** Its guard — `getattr(total, macro) != 0`, which
exempts a macro the dish contains none of — has no test, and the real library
cannot supply one: all three cooked no-process dishes declare every macro
unassessed, so the guard has nothing left to filter. Deleting it would force a
rice dish to declare B12 unassessed to load at all, a wide band on a macro it
does not contain. `test_a_macro_the_dish_contains_none_of_needs_no_justification`
added, built on `rice_cooked` (0 µg B12). Written **after** watching the
mutation survive, which is the only order that proves the test is about the
mechanism.

Re-run with `data/` copied and the new test in place:

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py R1,R2,R3,R4,R5
R1   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_silence_is_rejected_because_it_is_the_cheapest_path
R2   covered      tests/test_recipes.py::TestRecipeLoaderRules::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R3   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_an_unknown_preparation_is_rejected_rather_than_assumed
R4   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_an_uncooked_dish_may_not_also_name_a_process
R5   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_a_macro_the_dish_contains_none_of_needs_no_justification
====================================================================================================
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

Four of the five rows now name the test written for that mechanism. R2 still
names something incidental, and correctly: flipping the default to `uncooked`
makes every recipe with a `process:` line illegal, so the library does not load
and 28 tests in this file alone go red. Its own test
(`test_silence_is_rejected_because_it_is_the_cheapest_path`) is in that list —
verified by taking the whole per-mutation failure list, not the row.

**Disposition: FIXED.** `docs/design/probes/d4b_mutations.py`,
`tests/test_recipes.py`.

---

## 2026-08-09 — D9(a) closeout: advice that can actually change the outcome

Finishes D9. Two items were left open by D9(b), both small, both now built and
deletion-checked.

### The three suggestions were shown unconditionally, and two of them often could not help

`DECLINE_PATHS` rendered the same three strings for every decline. One of them —
"if your disclosed conditions have changed, update your profile" — sends a user
to a settings page that cannot affect a decline no clinical flag took part in.
Another — "check back as the recipe library grows" — is a real remedy when a
bound is structurally out of reach and a guess when the plate misses only in
combination. That guess is finding 24's shape exactly: an action offered against
a cause nobody established.

Each suggestion now carries an `applies(details)` predicate reading only tokens
already on the wire:

| suggestion | shows when |
| --- | --- |
| Try a different plate | always |
| Review your disclosed conditions | some violation has a non-empty `locked_by` |
| Wait for the library to grow | some violation is `unreachable` or `empty_pool` |

The first is unconditional **by design, not by omission**: it is what guarantees
the list is never empty, and a decline offering nothing at all is a worse screen
than a slightly loose suggestion. It is also always true — every `reach` value is
scoped to the template that was solved, `unreachable` included, so another
template genuinely can succeed.

Its wording was corrected in the same change. It ended "...to fit the same
*locked* limits", written when it only ever appeared beside a locked bound.
Now that it is the one suggestion shown on every decline, that was false on the
common case. Caught by rendering the screen and reading it, not by a test.

Measured, the jointly-infeasible shape (nothing locked, nothing unreachable):

```
--[paths]--
1
Try a different plate above — a different template draws on different recipes,
so the same limits may fit.
```

Two of three withheld, and the survivor renumbered to close the gap.

### The decline path now says it is not validated

`PlanOut.dev_mode` has existed since D11 and the decline view ignored it, so a
refusal computed entirely from unchecked figures was presented as settled. The
counterpart to D11's success-path line, in `#obDeclineProvenance`:

```
Not validated. The limits above were computed from nutrition data nobody has
checked against a primary source yet, so treat this as an illustration of the
method rather than dietary advice.
```

Deliberately **no percentage**. The success line quotes a share of the plate's
energy; there is no plate here, so that number does not exist and quoting one
would be a fabrication. Pinned by a test asserting `"%"` does not appear.

### A test that could not fail on the defect it named, caught before it was trusted

The first numbering test asserted consecutive numbering against the
`jointly_infeasible` payload — where only the *first* suggestion survives. Index
0 renders "1" whether the numbering runs before or after the filter, so the test
could not distinguish the two implementations and would have passed against the
defect.

Fixed by adding a payload where the *middle* suggestion is the one dropped
(`unreachable`, nothing locked → paths 1 and 3 apply). Pre-filter numbering
renders "1" and "3" there; post-filter renders "1" and "2". Confirmed by
deletion:

```
=== E2: numbering taken before the filter ===
FAILED ...TestOnlySuggestionsThatCanChangeTheOutcome::test_the_numbering_closes_the_gap_the_filter_opens
1 failed, 26 passed
```

This is the third time in two tasks that a test needed the perturbation before
it was worth anything (finding 40 and D8's stale premise being the others).

### Deletion checks — four mechanisms, four covered

```
=== E1: suggestions no longer filtered ===
FAILED ...::test_reviewing_conditions_is_withheld_when_no_condition_locked_anything
FAILED ...::test_waiting_for_the_library_is_withheld_when_the_library_is_not_the_limit
FAILED ...::test_the_numbering_closes_the_gap_the_filter_opens
3 failed, 24 passed

=== E2: numbering taken before the filter ===
FAILED ...::test_the_numbering_closes_the_gap_the_filter_opens
1 failed, 26 passed

=== E3: decline provenance never rendered ===
FAILED ...TestTheDeclineSaysItIsNotValidated::test_a_dev_mode_decline_says_so
1 failed, 26 passed

=== E4: dev_mode guard removed ===
FAILED ...TestTheDeclineSaysItIsNotValidated::test_nothing_is_claimed_when_the_plan_was_not_dev_mode
1 failed, 26 passed
```

E4's first attempt aborted rather than running: the guard's source is
byte-identical to `renderProvenance`'s on the success path, so the pattern
matched twice and the harness refused a non-unique mutation instead of editing
the wrong function and reporting a false result. Same protection
`d4b_mutations.py` has, for the same reason.

By hand again, for the reason recorded under D9(b): `d4b_mutations.py`
structurally cannot grade `web/`.

### Suite

```
$ python -m pytest tests/ -q --color=no --no-header       # both servers up
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
1 failed, 497 passed, 1 warning in 225.54s (0:03:45)
```

497 = 488 + 9. The single failure is D10's deliberately red test.

**D9 is now complete**, (a) and (b).

---

## 2026-08-09 — D9(b): the decline stopped saying `sodium_mg`

Closes **findings 31 and 36**. Done in the order D9 states, which is the repo's
own: extend the detector first, watch it fail, then write the copy.

### Finding 36 — the sweep claimed a decline it never rendered

`tests/test_web_no_identifiers.py`'s docstring said it covered "a solved plate
or an honest decline". The fixture clicked Generate once, on the default plate,
which solves. `renderPlanSuccess` and `renderPlanDecline` write into two
independent sections, so the violation list and the disclosure paragraph — the
two places a raw macro name was most likely to reach a reader, and the reason
the file exists — were swept zero times.

**Disposition: FIXED.** The fixture now selects a plate that declines for its
own profile and collects a tenth view, `dashboard_after_decline`.

Which plate declines was measured against the live API, not assumed:

| plate | verdict |
| --- | --- |
| south_indian:breakfast | passes |
| **south_indian:lunch** | **declines** — sodium 1546.0 mg vs a 1400.0 mg ceiling |
| north_indian:lunch | passes |
| north_indian:dinner | passes |

Three rungs were walked (`sodium_max_fibre_min`, `fat_carb_tolerance`,
`energy_tolerance`) before the ladder gave up, and the bound is `locked` by
`chronic_kidney_disease` — so this exercises the clinical-lock path, which D9
calls the most interesting thing on the screen.

The reachability test now requires that view to prove it *is* a decline: the
lede, the plate name (so a failed radio click cannot pass), and that some line
names sodium — asserted case-insensitively and accepting "salt", so it survives
the copy map below. If the library ever shifts and that plate starts passing,
this goes red rather than the sweep quietly becoming a second pass over the
success view.

### Finding 31 — measured before it was fixed

```
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_decline]
Leaks: [('sodium_mg', "sodium_mg is 1546.0mg, above its ceiling of 1400.0mg (more than one
         plate may take of a whole day's allowance) (locked b"),
        ('sodium_mg', 'No plan could be built for this profile: sodium_mg is 1546.0mg,
         above its ceiling of 1400.0mg (more than one plate may t')]
1 failed, 11 passed in 19.43s
```

Red on the new view only; every other view including the success path stayed
green, so this is finding 31 isolated rather than a broad regression.

**Two leak sites, not one.** `violation_detail[].text` renders into the
violation list, and `disclosure` renders into the closing paragraph — and the
disclosure *embeds* the same sentence rather than composing its own. Measured
rather than argued, by fixing only the list and re-running:

```
=== D2: disclosure renders the server string again (violations list left FIXED) ===
FAILED tests/test_web_decline_copy.py::TestNoTokenSurvivesAnyBranch::test_not_one_identifier_reaches_the_disclosure
FAILED tests/test_web_decline_copy.py::TestTheSentencesSayTheRightThing::test_the_disclosure_leads_with_the_clinical_refusal_when_one_holds
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_decline]
3 failed, 27 passed
```

A fix closing one site leaves the detector red — the task's own definition of
unfinished.

### The map is client-side, and needed two numbers the API was not sending

Copy lives in `web/dashboard.js`, consistent with D11: the server sends stable
tokens, the client writes the sentence. `core/planner/validator.py` still writes
`text` and `disclosure`, both still correct; they are simply not what this page
renders.

`ViolationOut` already carried `macro`/`kind`/`bound_source`/`reach`/
`relaxability`/`locked_by` but **not the two numbers any such sentence needs**.
Without them a client had to render `text` (which interpolates the raw key) or
parse the numbers back out of English, which would make prose an API contract —
the opposite of why the tokens exist. `actual` and `bound` have been on
`core.planner.validator.Violation` since D4a; `api/` now passes them through and
still computes nothing.

Every key `Violation.macro` can carry is mapped, not only the one a decline
produces today: all nine `MACRO_KEYS`, plus `quality_protein_g` (not a macro —
see `core/foods/quality.py` — but it reaches a decline like any bound). An
unmapped macro degrades to vague-but-clean prose rather than to its key, because
`humanise()` would render `potassium_mg` as "Potassium mg" and then state a
number against a unit the client cannot name.

Before, and after, for the real declining plate:

```
sodium_mg is 1546.0mg, above its ceiling of 1400.0mg (more than one plate may
take of a whole day's allowance) (locked by a condition you disclosed, and
never relaxed for that reason)
```

```
Sodium comes to 1,546mg, over the 1,400mg limit — more than one plate should
take of a whole day's allowance. We didn't loosen this one, because you told
us about chronic kidney disease.
```

and the disclosure, which no longer repeats the list it sits under:

```
We stopped rather than relax a limit tied to a condition you disclosed. This
system is not a substitute for clinical nutrition guidance — please take these
targets to your doctor or dietitian.
```

### Finding 40 — a default of `0.0` made the API's own deletion check pass

`ViolationOut.actual`/`bound` were first written with `= 0.0` defaults. Deleting
the pass-through in `api/main.py` then left every violation reporting 0.0
against 0.0 and **the suite stayed green** — the presence-and-type assertions
passed, and the prose check passed by coincidence, because `"0.0"` is a
substring of `"1400.0"`.

**Disposition: FIXED, in both places.** The fields are required, so a dropped
pass-through is a construction error rather than a plausible-looking
measurement; and the test asserts the numbers are non-zero. This is CLAUDE.md's
round-4 rule — the cheapest authoring path must never produce the most
confident-looking output — reappearing outside uncertainty, where the addendum
states it. Recorded because the mechanism survived its first check and the test
was the thing at fault, not the code.

### Nine of ten map entries are unreachable from the real library

`tests/test_web_decline_copy.py` (new) drives the real `renderPlanDecline` in a
real browser with `POST /api/plan` stubbed to return violations today's recipe
library cannot produce: every macro, both `kind`s, all three `bound_source`s,
every `relaxability` note, an unfillable plate, and a macro absent from the map.
Auth, profile and science still hit the real API, so the page reaches the
renderer the way it always does.

Three deletion checks, each shown red against its own mechanism:

```
=== D1: violations list renders server prose again ===
FAILED ...TestTheSentencesSayTheRightThing::test_a_floor_reads_as_a_shortfall_and_a_ceiling_as_an_excess
FAILED ...TestTheSentencesSayTheRightThing::test_a_locked_bound_names_the_condition_and_says_we_chose_not_to
FAILED ...TestTheSentencesSayTheRightThing::test_the_bound_source_is_explained_when_it_is_not_the_ordinary_one
FAILED ...TestTheSentencesSayTheRightThing::test_an_unfillable_plate_names_the_courses_in_words
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_decline]
17 failed, 13 passed

=== D3: unmapped-macro fallback removed ===
FAILED ...TestNoTokenSurvivesAnyBranch::test_an_unmapped_macro_degrades_to_prose_not_to_its_key
1 failed, 29 passed
```

**These were run by hand, not through `d4b_mutations.py`, and that is a
structural limit rather than an omission.** The harness mutates a copy of
`core/` and `tests/` inside a throwaway worktree; the browser loads `web/` from
a static server pointed at the real directory, so a mutated `web/` in the
worktree would have no effect and every row would falsely report "survived".
Adding `web` to the copied trees would not fix it. Left as-is and written down
here so the next person does not read the absence of W-style rows as an
oversight.

### Suite

```
$ python -m pytest tests/ -q --color=no --no-header       # both servers up
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
1 failed, 488 passed, 1 warning in 204.84s (0:03:24)
```

488 = 466 (426 + the 40 web tests, now running) + 18 decline-copy + 3 API + the
new tenth view. The single failure is D10's deliberately red test.

### What D9 still owes

This is **(b) plus the copy `(a)` needs**, not all of D9(a). Specifically still
open: the decline screen does not yet offer only suggestions that *can* change
the outcome — `DECLINE_PATHS` is still three static strings shown regardless of
whether they apply. "Try a different plate" is good advice for a
`jointly_infeasible` sodium miss and useless for an `unreachable` one, and the
payload now carries `reach` to tell them apart. Not started.

---

## 2026-08-09 — D8: the web suite reported green without looking

D8 was written as two halves: **(a)** make conditional passing honest, and
**(b)** triage "12 failed / 30 errors, Playwright timeouts, undiagnosed". Its
own re-scope note said to start by re-measuring rather than fixing. Doing that
changed both halves.

### Finding 38 — (b)'s triage list is empty, and the recorded failure count was stale

With both dev servers up, every browser-backed check passes:

```
$ python -m pytest tests/ -q --color=no --no-header -m web
.........................................                                [100%]
41 passed, 416 deselected, 1 warning in 86.60s (0:01:26)
EXIT=0
```

**Disposition: CLOSED, nothing fixed, because nothing was broken.** The "12
failed / 30 errors" figure predates work that has since landed and was never
re-taken. This is the second independent run showing 41/41 — the first was
D11's incidental `1 failed, 456 passed`, which is why D8's re-scope note
existed. Two runs on one machine is not a proof of health, and the tests remain
timing-sensitive Playwright checks; but the specific list D8 was written to
triage does not exist, and inventing work to match a stale number would be
worse than saying so.

Nothing in `web/`, `api/` or `core/` was touched for this half.

### Finding 39 — the skips were never silent; they were merely unseen

D8's premise, carried in the task text for weeks, is that the suite "passed
silently when servers were down". Measured, that is **false in its literal
form**. Every skip already names its cause:

```
$ python -m pytest tests/test_web_*.py -q --color=no --no-header -rsp
ssssssssssssss.ssssssssssssssssssssssssss                                [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_web_landing_geometry.py:90: no static server on http://localhost:3000
SKIPPED [9] tests\test_web_no_identifiers.py:198: no static server on http://localhost:3000 (python -m http.server 3000 --directory web)
...
1 passed, 40 skipped in 4.60s
EXIT=0
```

The reasons are good ones — several name the command that would fix them. They
appear **only under `-rs`**, which nobody passes by habit. The default view is
`1 passed, 40 skipped`, exit 0.

So the defect is real but it is not the one recorded: **naming a reason is not
the same as it being seen.** A distinction worth writing down, because the fix
that "silent" implies — add reasons — was already done, and doing it again
would have produced a satisfied task and an unchanged failure mode. This is the
same family as findings 11, 18 and 36: a check that satisfies the letter of its
rule while missing the purpose.

**Disposition: FIXED**, described below.

### The fix sits on the report, not on the fifteen call sites

`tests/conftest.py` gains one rule: a `web`-marked test that skips is recorded,
announced at the end of the run, and — under `FOODAI_WEB_TESTS=required` —
converted into a failure.

It deliberately does **not** edit the ~15 `pytest.skip` sites across the three
web files (`_listening` is defined three times; the skips split 4 / 2 / 9).
Two reasons, and the second is the load-bearing one:

1. One definition instead of fifteen.
2. It catches **every** cause of a web skip, including a missing Playwright —
   which no server check would ever see, because `importorskip` fires before
   any server is contacted. A gate written as "check the servers harder" would
   have left the bare-checkout case exactly as it was.

The call sites keep deciding *whether* a prerequisite is missing — they know
which of the two servers each test needs, and duplicating that into the gate
would have been the actual larger change — while the gate decides what a
missing prerequisite *means*.

`pyproject.toml` promises `python -m pytest tests/ -q` runs clean on a bare
checkout. That promise is kept: the default stays exit 0. It is also precisely
how a frontend surface reports green without looking, so the strict reading is
available to anyone who wants it rather than imposed on everyone.

### Both modes, measured with the servers genuinely stopped

Default — loud, exit preserved:

```
$ python -m pytest tests/test_web_landing_geometry.py tests/test_web_no_identifiers.py -q
ssssssssssssss.                                                          [100%]
============================ web tests did not run ============================
14 browser-backed check(s) skipped. Nothing in web/ was verified by this run.
  - no static server on http://localhost:3000
  - no static server on http://localhost:3000 (python -m http.server 3000 --directory web)
Start the servers (see web/README.md), or set FOODAI_WEB_TESTS=required to make this a failure.
1 passed, 14 skipped in 2.13s
EXIT=0
```

Strict — hard failure, exit 1:

```
$ FOODAI_WEB_TESTS=required python -m pytest tests/test_web_landing_geometry.py -q
FAILED tests/test_web_landing_geometry.py::test_the_kolam_never_exceeds_its_token_on_the_landing_page
FAILED tests/test_web_landing_geometry.py::test_every_route_renders_the_kolam_at_one_strength
FAILED tests/test_web_landing_geometry.py::test_the_language_label_holds_position_across_all_four_scripts
FAILED tests/test_web_landing_geometry.py::test_no_placeholder_copy_renders_in_the_hero
4 failed in 1.69s
EXIT=1
```

with each failure carrying the reason forward:
`FOODAI_WEB_TESTS=required, so a skipped browser check is a failure: no static
server on http://localhost:3000`. A strict run that said only "something was
skipped" would be reporting what it already reported.

And with the servers up, the summary correctly stays quiet: `4 passed in
32.62s`, no block.

### Deletion check: six rows, all covered

`d4b_mutations.py` gains `WEB_GATE = "tests/conftest.py"` and rows W1–W6. It
already copies `tests/` from the working tree, so hosting a `tests/` module cost
a module constant and an `OWN_TESTS` row — the same shape D6 found for
`core/foods/`.

```
$ python docs/design/probes/d4b_mutations.py W1,W2,W3,W4,W5,W6
W1   covered      tests/test_web_gate.py::TestStrictModeTurnsASkipIntoAFailure::test_a_skipped_web_test_fails_under_the_env_var
W2   covered      tests/test_web_gate.py::TestStrictModeTurnsASkipIntoAFailure::test_only_the_exact_word_arms_strict_mode
W3   covered      tests/test_web_gate.py::TestStrictModeTurnsASkipIntoAFailure::test_a_non_web_skip_is_untouched_even_under_strict
W4   covered      tests/test_web_gate.py::TestTheReasonIsRecoveredWhateverShapeItCameIn::test_a_bare_string_longrepr
W5   covered      tests/test_web_gate.py::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
W6   covered      tests/test_web_gate.py::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
====================================================================================================
6 mechanisms: 6 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

`OWN_TESTS[WEB_GATE]` is `test_web_gate.py` **only**. The three `test_web_*.py`
suites are the *subject* of this gate, not tests of it — they skip together for
one reason, so a row they turn red is reporting the weather.

W5 and W6 name the same test, which is the pattern `CLAUDE.md` says not to
believe on sight, so the full list was taken for both rather than trusting the
row:

```
=== W5 full failure list in test_web_gate.py ===
FAILED ...::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
1 failed, 9 passed in 0.06s
=== W6 full failure list in test_web_gate.py ===
FAILED ...::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
1 failed, 9 passed in 0.06s
```

Exactly one failure each, and it is the test about the summary's content in both
cases — a single test genuinely covering two mechanisms, not collection order
picking a bystander. Recorded because the check is cheap and the D6 sweep is the
reason it is now habitual.

### One thing the tests cannot grade, and where the evidence for it lives

`tests/test_web_gate.py` drives the hooks with stand-in report objects. It
cannot answer whether pytest honours `report.outcome = "failed"` set from a
wrapper — the two transcripts above answer that, taken against the real suite.
The file is scoped to the other half: that the rule survives edits. Recorded
here because a reader finding only the unit tests would over-trust them.

### Full suite, servers down — the state most readers will be in

```
$ python -m pytest tests/ -q --color=no --no-header
============================ web tests did not run ============================
40 browser-backed check(s) skipped. Nothing in web/ was verified by this run.
  - no static server on http://localhost:3000
  - no static server on http://localhost:3000 (python -m http.server 3000 --directory web)
Start the servers (see web/README.md), or set FOODAI_WEB_TESTS=required to make this a failure.
=========================== short test summary info ===========================
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
1 failed, 426 passed, 40 skipped, 1 warning in 109.68s (0:01:49)
```

426 = 414 + D11's 2 + this task's 10. The single failure is D10's deliberately
red test, unchanged.

### Still true after this change

The suite still reports exit 0 by default with the frontend unchecked. That is
a deliberate trade, not an oversight: the alternative breaks the bare-checkout
promise for every reader who is not running a browser. What changed is that the
run now says so in six lines nobody can miss, and that a caller who wants the
guarantee has one word to type.

---

## 2026-08-09 — D11: the `dev_mode` plate now says so

Closes **finding 37**. The dashboard had always rendered a plate built on
100%-unverified data as an ordinary result, against a requirement
`docs/methodology.md` states about exactly this case.

### D11's own part 1 was wrong, and the code said so

D11 specified, as its first and "only real decision", surfacing provenance from
`core/` — on the reasoning that `plan_meal` discards the candidate pool and
`LadderOutcome` carries no provenance field. That is true and it is not the
obstacle. `SolvedPlan.estimate` is a `NutritionEstimate`, which has carried
`unverified_energy_kcal` all along; `api/main.py` was already reading
`outcome.plan.estimate.point` and dropping the rest of the object. And
`dev_mode` is a parameter the API itself passes.

So **no `core/` change was needed** and none was made. Recorded rather than
quietly dropped, because the wrong premise was written into the queue and this
file yesterday, and a reader would otherwise be left expecting a refactor that
never happened. What is genuinely unreachable is `CandidatePool.flagged` — see
"What is still not surfaced" below.

### The shape: the server sends the number, the client writes the sentence

`PlanOut` gains `dev_mode: bool`. `PlanEstimateOut` gains
`unverified_energy_kcal` and `unverified_energy_fraction`, read off the
estimate `core/` already computed rather than recomputed in `api/`, which
computes no nutritional number.

The prose is written in `web/dashboard.js`. `dev_mode` is `snake_case` and must
never reach a visible text node — same rule as `bound_source` and
`VIOLATION_REACH` — and this is also the division `CLAUDE.md`'s central
invariant describes for the LLM: the number is computed deterministically
upstream, the language is written around it.

### The order, which is the point

The first draft of `renderProvenance` rendered the token itself. Run against
live servers **before** the real copy was written:

```
$ python -m pytest tests/test_web_no_identifiers.py -q
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_plan]
E   AssertionError: dashboard_after_plan renders internal identifiers to the user.
E   Leaks: [('dev_mode', 'Built with dev_mode')]
1 failed, 10 passed in 19.05s
```

Then the copy, then:

```
11 passed in 15.28s
```

That red run also **measures** a claim made yesterday on reasoning alone. The
2026-08-09 finding-37 entry argued this belonged outside D9 partly because the
identifier sweep already reaches the success view. It does, and now that is a
transcript rather than an inference.

### It renders

```
$ curl -s -X POST localhost:8000/api/plan -d '{...north_indian/lunch, 70kg...}'
passed      : True
dev_mode    : True
energy      : 931.2
unverified  : 931.2 kcal = 100.0%
```

Live browser, same profile and plate:

```
success section hidden : False
PROVENANCE LINE        : Not validated. About 100% of this plate's energy rests on
                         figures nobody has checked against a primary source yet. The
                         nutrition data behind these dishes is unconfirmed, so treat
                         the numbers as an illustration of the method rather than
                         dietary advice.
```

### A second false claim, found in the same function

`renderPlanSuccess`'s no-estimate fallback read **"A validated combination of
real components for this plate."** Nothing in this library can ship as
validated, so that sentence was false on every plate the app has ever served,
and it asserted precisely the thing finding 37 is about. Now "A combination of
real components for this plate." Found by reading the function being edited,
not by any test — no test covers a success render with a null estimate.

### Measured, per the deletion convention

Two mechanisms in `api/main.py`, each deleted with the full suite re-run:

```
A1  PlanOut echoes the dev_mode it actually ran with
      tests/test_api_targets.py::TestPlanProvenanceReachesTheClient::test_a_solved_plate_says_it_is_not_validated
A2  the unverified figure is carried onto the estimate
      tests/test_api_targets.py::TestPlanProvenanceReachesTheClient::test_the_unverified_figure_is_carried_not_dropped
```

Each caught by exactly its own named test, and by nothing else. The copy itself
is graded by `test_web_no_identifiers.py`, shown red above.

The harness's first run printed **empty names for both rows** — it took
`line.split(" ")[0]`, which is the word `FAILED`. Finding 35's lesson, that a
harness parsing tool output is itself a measurement, reproduced within a week of
being written down. Both mutations really had gone red; the harness could not
say which test caught them, which is the entire question it exists to answer.

### What is still not surfaced

`CandidatePool.flagged` — how many recipes were kept past their eligibility
ceiling. `docs/methodology.md` names it alongside `dev_mode`, and it is the one
thing here that *would* need the `core/` change: `plan_meal` builds the pool and
discards it. Deliberately not done, and the position is arguable rather than
obvious: a count of recipes that missed an internal threshold is a mechanism
detail, while "100% of this plate's energy" is the same fact in the units a
reader can act on. If that judgement is wrong, the fix is the refactor D11's
part 1 described, and it now has a reason to exist that this task did not
supply.

### Verify

```
$ python -m pytest tests/ -q
1 failed, 456 passed, 1 warning in 189.58s (0:03:09)
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
```

456, not 416, because the static server and API were up: the 40 web tests that
normally skip actually ran. 414 + 2 new + 40 = 456. The one failure is D10's
deliberately-red test.

**Relevant to D8, and not a claim about it.** D8 records the web suite as "12
failed / 30 errors, Playwright timeouts, undiagnosed". With servers up today it
ran clean. That is one run on one machine and does not close D8 — whose (a) is
about *conditional passing being honest*, which is untouched: the suite still
skips silently when the servers are down, which is how a green run can mean
nothing. But whoever picks up D8 should know the triage list may be much shorter
than recorded, or empty.

**Disposition:** finding 37 **CLOSED**. Findings 19, 31, 36, 2, 15, 22, 28, 29
untouched. `CandidatePool.flagged` remains unsurfaced, by decision, recorded
above.

---

## 2026-08-09 — D7, part 1: the verification horizon, and finding 37

**D7 is not complete and cannot be completed by an assistant.** Its central
deliverable — "verify those rows against IFCT 2017 with correct grading" — is
the one action this project reserves for a human, in `CLAUDE.md`'s second
invariant, in the round-4 addendum, and in this file's 2026-07-21 entry. What
follows is everything else D7 asked for, plus the measurement that says whether
the human half is worth anyone's afternoon.

### The question D7 put to D6, now answerable

D7's own text: *"Depends on D6. Verified ingredients feeding a wrong denominator
certify nothing."* D6 fixed the denominator yesterday, so the question is
answerable — and better answered before someone opens a reference book than
after.

`docs/design/probes/d7_verification_horizon.py`, north_lunch's plate (phulka x5
+ soya_chunk_curry x1 + paneer_masala x1, 931.2 kcal):

```
  TODAY          931.2 / 931.2 kcal = 100.0%   -> does NOT ship (threshold 15%)
  INGREDIENTS     88.4 / 931.2 kcal =   9.5%   -> SHIPS (threshold 15%)
      soya_chunk_curry:sunflower_oil              44.2 kcal  (process)
      paneer_masala:sunflower_oil                 44.2 kcal  (process)
  EVERYTHING       0.0 / 931.2 kcal =   0.0%   -> SHIPS (threshold 15%)

  cross-check: core/ reports 931.2 kcal, this probe's TODAY is 931.2 kcal -- agree
```

**Ten ingredient rows are sufficient on their own.** The process constants are
not on the critical path — which matters, because IFCT 2017 is a composition
table and does not contain oil-uptake figures for a tempered curry; those are
separate constants with separate sources, and `CLAUDE.md` warns Indian-specific
process literature is thin. Had the answer come out the other way, the ten rows
would have bought nothing and D7 would have needed rescoping before the work,
not after.

Stated against over-reading: 9.5% leaves 139.7 kcal of headroom, real but not
large; a second template gets its own answer; and ~15% is still the provisional
figure `CLAUDE.md` flags for revisiting.

The probe computes both hypotheticals itself and **never flips a flag**. A probe
that sets `verified=True` to answer a question is one interrupted session away
from leaving it set — the failure the flag exists to prevent, committed by the
tool built to measure it. Only the TODAY column has a shipped counterpart to
cross-check against, and it agrees.

### The rows, named

Ten of the eleven rows reachable from north_lunch need a human: `wheat_atta_raw`,
`paneer_fresh`, `soya_chunks_dry`, `onion_raw`, `tomato_raw`, `sunflower_oil`,
`ginger_garlic_paste`, `garam_masala`, `green_chilli`, `salt_iodised`. `water`
is the eleventh and is already verified.

**None of the ten carries an IFCT code**, so the task is "find the code, then
transcribe", not "transcribe". None of the four rows that already carry real
codes from 2026-07-24 (`rice_milled_raw`, `rajma_raw`, `toor_dal_raw`,
`potato_raw`) appears on this plate — the template D7 picked is the one with no
head start, which nobody had noticed.

`docs/methodology.md` now carries the narrowing as a deliberate scope line, per
D7's instruction to write it in the voice of the existing boundaries.

### Finding 37 — a `dev_mode` plate is rendered with no label — **OPEN**

Found while scoping D7's third deliverable. `docs/methodology.md` has required,
since Phase 2:

> Any rendered plan, any `demo.py` stdout, and any README transcript produced in
> `dev_mode` must carry that label in the artifact itself.

`demo.py` complies — it prints `unverified : 931.2 kcal (100.0% of plate)`. The
web does not. `PlanOut` carries `passed`, `disclosure`, `relaxation_applied`,
`violations`, `violation_detail`, `components`, `estimate`; `PlanEstimateOut`
carries six macros. **Neither carries `dev_mode`, `CandidatePool.flagged`, or
the unverified figure**, and `web/dashboard.js` renders none of them. Grepped,
not assumed: the only `unverified` in `api/` is `/api/science`'s registry count,
and `web/dashboard.js` mentions the word once, in a comment.

So the dashboard has always presented a `dev_mode` plate as an ordinary result.
That was true before D6 and is sharper after it: the number now absent from the
screen is 100%.

This is the "artifact survives without context" failure the same section names,
on the surface where a portfolio project's output is actually seen — and the
requirement it violates was written in this repository, about this case, and
then not implemented.

**Why it is not fixed here.** `plan_meal` builds the candidate pool and discards
it; `LadderOutcome` carries `plan`, `result`, `target_used` and
`skipped_locked_steps`, and nothing about provenance. Surfacing it is a `core/`
design decision with a wrong answer available — hanging `dev_mode` on
`LadderOutcome` would put candidate-pool knowledge on a validator dataclass that
has no business with it. `core/planner/plan.py` owns both halves and is the
right place, but that is a deliberate change, not a field addition, and D7's
headline is blocked regardless. Queued, not slipped in.

**Checked against D9 before queuing, because D4c had just turned out to be this
shape.** D9 already lists "surface `dev_mode`", so the question was whether
finding 37 was inside it. It is not, and the reason is not scope-drawing
preference: D9 is the *decline* screen in every other bullet, this is the
*success* path, and `web/dashboard.js` renders the two through independent
functions into independent DOM sections (`renderPlanSuccess`,
`renderPlanDecline`). The decisive asymmetry is detection, not surface —
`tests/test_web_no_identifiers.py` already reaches the success view (its own
fixture profile is served a plate on the default `south_indian:breakfast`), so
a naive `dev_mode` string there is caught today; it never reaches a decline,
which is finding 36 and is D9's own (b). One is verifiable now, the other is
blocked behind D8 and a detector that does not yet exist.

The two do share exactly one change — `PlanOut` gains `dev_mode` once, for both
paths. That is recorded in both task entries rather than in neither, which is
the failure mode finding 31 nearly had.

**Disposition:** D7 **part 1 done, part 2 blocked on a human.** The scope
narrowing and its justifying measurement are landed; the ten rows are named; the
plumbing is finding 37 and the verification is nobody-but-a-human's. Findings
19, 31, 36, 2, 15, 22, 28, 29 untouched.

---

## 2026-08-09 — D6: the unverified-energy denominator

Closes **finding 20**. The number the 15% shipping threshold and the `dev_mode`
exit both read was wrong in two directions at once. Nothing depended on it yet,
which is why it was fixed now — D7 and the `dev_mode` exit are next in the queue
and both would have leaned on it.

### The fix

Attribution moves from "one yes/no question per recipe" to per ingredient line.
A line is charged when its composition record is unverified **or** the process
constant that determined its quantity is, and charged **once** in either case.

Union rather than sum is deliberate: a line unverified for both reasons is still
only that much energy, and adding the terms could take a plate past 100% of its
own energy, which is not something a fraction of a quantity can do.

Charging a line's *whole* energy on an unverified process constant is not the
old over-attribution returning. `RecipeIngredient.process_key` marks a line
whose **quantity was determined by** that constant, so if the constant is
unopened, so is every calorie on that line. The old rule's error was charging
the *other* lines too.

`_depends_on_unverified` is gone, replaced by `_unverified_energy`.

### The measurement, all four passing plates

`docs/design/probes/d6_unverified.py` prints the per-line arithmetic and three
figures per plate: OLD (the previous rule, restated in the probe), NEW (the
corrected rule, reimplemented independently), and SHIPPED (whatever `core/`
returns). NEW and SHIPPED are printed side by side so the probe cannot quietly
agree with the code it audits — a difference between them is a bug in one.

```
  PLATE south_breakfast: 623.6 kcal        PLATE north_lunch: 931.2 kcal
    OLD        234.2 / 623.6 =  37.5%        OLD        436.8 / 931.2 =  46.9%
    NEW        623.6 / 623.6 = 100.0%        NEW        931.2 / 931.2 = 100.0%
    SHIPPED    623.6 / 623.6 = 100.0%        SHIPPED    931.2 / 931.2 = 100.0%
  PLATE south_lunch: 848.1 kcal            PLATE north_dinner: 782.5 kcal
    OLD        501.1 / 848.1 =  59.1%        OLD        317.4 / 782.5 =  40.6%
    NEW        848.1 / 848.1 = 100.0%        NEW        782.5 / 782.5 = 100.0%
    SHIPPED    848.1 / 848.1 = 100.0%        SHIPPED    782.5 / 782.5 = 100.0%
```

Before the `core/` change, SHIPPED equalled OLD on all four; after, it equals
NEW on all four. That transition is the whole verification, and it is why the
probe computes both columns itself instead of using a worktree — the comparison
does not depend on which tree it runs from, so it keeps working after D6 lands.

**Exactly 100% is the correct answer, not a rounding artifact.** 28 of 29
ingredient rows are `verified=False` and the exception, `water`, carries no
energy. Every calorie on every plate traces to a composition record nobody has
opened. The old 37–59% figures were understatements produced by ignoring
composition entirely.

Confirmed through the tracked entry point, plates unchanged:

```
$ PYTHONHASHSEED=0 python demo.py plan --region south_indian --meal-slot breakfast
  unit counts  : {'idli@tiffin': 6, 'soya_kuzhambu@kuzhambu': 1, ...}
  point        : 623.6 kcal, 29.6g protein, ...
  unverified   : 623.6 kcal (100.0% of plate) -- CLAUDE.md's shipping threshold is ~15%
```

### The real library cannot test this, and the old test said it could

`TestUnverifiedEnergyAttribution::test_all_three_recipes_rest_on_unverified_
process_constants` asserted `unverified_energy_fraction() == 1.0` and **passed
identically before and after the fix** — the old whole-recipe rule also charged
everything on this library. Under the correct rule every real plate is 100%,
and under most broken ones it still is. A test that cannot fail on the defect it
names is not evidence, whatever its name.

It is kept, renamed `test_the_real_library_is_entirely_unverified`, and its
comment now says what it does and does not show. Five new tests build their own
mixed data — a verified line, an unverified-composition line, a
verified-ingredient-on-unverified-process line — where the answer is 600 of 700
kcal rather than everything.

Measured, per the deletion-testing convention. Five mechanisms added to
`d4b_mutations.py` (which turned out never to have cared that its modules were
all in `core/planner`; `core/foods/nutrition_of.py` needed only a new constant
and an `OWN_TESTS` row):

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py N1,N2,N3,N4,N5
N1   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_the_real_library_is_entirely_unverified
N2   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_a_verified_line_with_no_process_is_not_charged
N3   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_the_real_library_is_entirely_unverified
N4   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_a_verified_line_with_no_process_is_not_charged
N5   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_the_real_library_is_entirely_unverified
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

**That table is not sufficient on its own, and it names the demoted test three
times.** The harness reports the first *scoped* failure, which is collection
order, not relevance — D4b-i's own lesson that a test in the right file is not
automatically the right test. So the full failure list was taken per mutation:

```
N1 composition charged     -> all four synthetic tests, plus the real-library one
N2 process charges its line -> test_a_verified_line_with_no_process_is_not_charged
                              test_unverified_composition_is_charged
                              test_the_charge_scales_with_the_serving_count
N3 charged once, not twice  -> test_a_line_unverified_twice_over_is_charged_once
                              (+ the real-library one)
N4 per line, not per recipe -> all four synthetic tests
N5 scales with count        -> test_the_charge_scales_with_the_serving_count
                              (+ the real-library one)
```

Every mechanism is caught by the test written for it. And the sharper result:
**N2 and N4 — the two directions finding 20 actually named — do not trip the
real-library test at all.** Under N4 the real library still charges everything
(whole recipe = everything); under N2 composition alone still charges
everything. The test that looked like coverage for this fix is blind to exactly
the defect the fix is about.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d6_unverified.py
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py N1,N2,N3,N4,N5
PYTHONHASHSEED=0 python demo.py plan --region south_indian --meal-slot breakfast
python -m pytest tests/ -q
```

```
1 failed, 414 passed, 40 skipped, 1 warning in 112.03s (0:01:52)
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
```

409 → 414 is the five new tests exactly (one old test renamed, not added). The
one failure is D10's deliberately-red test, unchanged.

**Disposition:** finding 20 **CLOSED**. `docs/methodology.md` limitation 8
closed with it, and a new dated section carries the corrected figures. No plate,
verdict or unit count moved — this changes what the system says about its own
evidence, not what it plans. Findings 19, 31, 36, 2, 15, 22, 28, 29 untouched.

---

## 2026-08-09 — D4c-i: the decline sentences, before and after D4a

D4a's entry proved the declines got better with four counts. Nobody had read
the sentences those counts summarise. This is that artifact: `d4_declines.py`
gains a `text` mode, run on both sides of D4a from one probe implementation.

### There is no "the decline for each template"

Since D3 all four templates **pass** for the reference profile. A decline
exists only relative to a profile, so an artifact printing four blocks without
saying whose they are has silently answered a question nobody asked. The
selection rule is therefore part of the output and is reproduced above it:
walk the existing profile grid in order, group each template's declines by the
`(macro, kind)` pairs the decline names plus whether the profile has clinical
flags, and print the most common shape, the most common flagged shape, and the
most common unflagged shape, deduplicated. Representative is first-in-grid-order.
Ties break on grid order, so the output is a function of the grid alone.

**The first version of that rule was wrong and the output said so.** It
guarded only the flagged side, on the reasoning that a locked bound is rare
and would be buried by frequency. On the real library the opposite held: the
top shape already carried flags on all four templates, so the artifact printed
four locked declines and not one ordinary one — the commonest case a user hits,
missing entirely. Fixed to be symmetric. Worth recording because the defect was
invisible in the rule and obvious in the transcript, which is the whole argument
for producing a transcript rather than asserting the rule was sound.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py text
```

The **before** column, same probe copied into a worktree of the pre-D4a commit
so a difference between the columns is a difference in `core/`:

```bash
git worktree add .d4c_pre b72060e
cp docs/design/probes/d4_declines.py .d4c_pre/docs/design/probes/
cd .d4c_pre && PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py text
git worktree remove .d4c_pre --force
```

Both modes read only fields present on both sides of D4a — `result.disclosure`,
`Violation.describe`/`.macro`/`.kind`, `result.relaxation_applied`,
`outcome.skipped_locked_steps` — checked against `b72060e` rather than assumed,
per the 2026-08-08 amendment.

### What changed, in the prose itself

Full transcripts are reproducible from the commands above; the diff between
them, taken 2026-08-09, is 115 lines each side and reduces to four changes.

**1. Finding 30, visible as a user would have met it.** south_breakfast and
north_dinner, both CKD representatives:

```
BEFORE  protein_g is 35.6g, below its floor of 38.2g (locked by disclosed
        condition: chronic_kidney_disease; never relaxed)
AFTER   protein_g is 35.6g, below its floor of 38.2g (locked by a condition you
        disclosed, and never relaxed for that reason)
```

**2. Finding 24's empty-pool half.** south_lunch, both representatives — this
is the shape 54 of the grid's 105 south_lunch declines take:

```
BEFORE  no recipe combination survived filtering for this profile, so there was
        nothing to solve
AFTER   1 required course of this meal cannot be filled from the recipe library
        for this profile, so there was nothing to solve
```

**3. Finding 24's wrong-plate half.** north_dinner, 110 kg fat-loss vegetarian
with CKD. Before, the plate chosen by deviation score broke two bounds and the
decline named both; after, ranking by fewest-bounds-broken found a plate that
breaks one, and the fat ceiling — which that plate meets — is correctly no
longer mentioned. The protein figure moves with the plate, 56.0 → 55.4 g:

```
BEFORE  fat_g is 29.6g, above its ceiling of 29.3g;
        protein_g is 56.0g, below its floor of 59.4g (locked ...)
AFTER   protein_g is 55.4g, below its floor of 59.4g (locked ...)
```

**4. Shape counts regrouped in both directions**: south_lunch 12 → 11 distinct
shapes, north_dinner 2 → 1, but north_lunch 12 → **13**. Shape is keyed on which
bounds a decline names, and D4a changed which bounds get named, so both merging
and splitting are expected. Recorded rather than explained: the direction of the
move carries no quality signal on its own, and reading one into it would be the
same mistake as reading the deviation score as nearness.

### What the artifact shows that the counts could not

Finding **31** is now legible rather than described. Every after-column sentence
above still contains `protein_g` or `fat_g`, and north_lunch's most common
decline — the quality-source floor — reads well precisely because someone wrote
it a bespoke sentence with no identifier in it. That contrast, in one
transcript, is the input D9's copy map needs and is the reason this ran before
D9 rather than inside it.

The locked-decline sentence is also visibly the strongest thing the system
currently says, and it is two clauses long. "We did not try, and here is what we
would not compromise" is D9's centrepiece; it exists today and no screen shows it.

**Disposition:** D4c-i done. No `core/` change; the suite is unmoved at
`1 failed, 409 passed, 40 skipped, 1 warning in 114.79s`, the failure being
D10's deliberately-red test. Findings 31 and 36 untouched and OPEN, both D9.

---

## 2026-08-09 — finding 36, raised while scoping D4c

### Finding 36 — the identifier sweep describes coverage it does not have — **OPEN**

`tests/test_web_no_identifiers.py`'s module docstring says, of the views it
walks:

> The eight views are the ones a user can reach: the landing page, wizard steps
> 1-6, and the dashboard (plate picker, then whatever `POST /api/plan`
> returns — a solved plate **or an honest decline, both of which render copy**).

The decline half is false, and has been since D3. The fixture's profile is
74 kg / 176 cm / 31 / male / moderate / maintain / vegetarian with
`chronic_kidney_disease`, and it clicks `#dashGenerate` without touching the
plate picker. `web/dashboard.html:71` has `south_indian:breakfast` checked by
default. Measured against today's real library:

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python -c "...plan_meal for the sweep profile..."
south_indian breakfast -> PLATE   | skipped_locked ()
south_indian lunch     -> DECLINE | skipped_locked ('protein_tolerance',)
     sodium_mg is 1546.0mg, above its ceiling of 1400.0mg (more than one plate
     may take of a whole day's allowance) (locked by a condition you disclosed,
     and never relaxed for that reason)
north_indian lunch     -> PLATE   | skipped_locked ()
north_indian dinner    -> PLATE   | skipped_locked ()
```

So `dashboard_after_plan` renders the success view on every run. The decline
view has never been swept. It is one radio click away, and the sentence waiting
there contains `sodium_mg` — finding 31, live, and exactly the token shape this
file exists to catch.

**Why this is its own finding and not a note inside D4c.** D4c already records
that the sweep never renders a decline. What it did not record is that the file
*claims otherwise in its own words*. Those are different defects. The first is
a coverage gap; the second is a coverage gap that reports itself as covered,
which is the class this repository's process rule is built against — and it is
worse here than elsewhere, because the docstring is a long, careful argument
about why grepping for known strings cannot work. A reader who accepts that
argument has no reason to check whether the sweep reaches the view it says it
reaches. The care in the prose is what makes the false clause load-bearing.

Same family as finding 32 (a region-filter test whose assertion documented the
unenforced filter) and the D4b-ii note about a test overstating its reach. This
is the third instance, so it is a pattern rather than a slip: **a test's own
description of its scope is not evidence of its scope, and is read by more
people than the code is.**

**Disposition: OPEN.** Not fixed here, per the queue's rule about not fixing
what a task notices in passing — and it cannot be honestly fixed in isolation
anyway. Correcting the docstring to describe what the sweep really does would
make the file accurate and leave the hole; making the sweep reach a decline
turns it red on finding 31, whose remedy is a macro-to-copy map that belongs to
D9. Both halves are therefore assigned to D9, which is renamed to say so.

---

## 2026-08-09 — D4b-ii: the nine missing tests, each shown red first

Closes findings **32** and **34**, and decides **33**. Fourteen tests across
three files, covering the nine mechanisms the D4b-i sweep left uncovered.

Every one was shown failing against its own deleted mechanism before being
believed, which is the entire point of the exercise and is not a claim to take
on trust — the transcript is below.

### The measurement

```
9 mechanisms: 9 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
C3   covered      tests/test_planner_candidates.py::TestHardFilters::test_region_mismatch_excludes_a_recipe
S6   covered      tests/test_planner_solver.py::TestTheEmptyPlate::test_an_empty_plate_is_rejected_by_a_floor
S7   covered      tests/test_planner_solver.py::TestUnsetQualityProteinIsConservative::test_the_default_is_zero
V8   covered      tests/test_planner_validator.py::TestBoundSourceIsProvenanceNotAGuess::test_the_source_becomes_the_guard_once_rung_one_is_clipped
V10  covered      tests/test_planner_validator.py::TestRungFourInIsolation::test_a_locked_protein_floor_is_returned_untouched
V11  covered      tests/test_planner_validator.py::TestRungFourInIsolation::test_the_protein_ceiling_passes_through_unchanged
V16  covered      tests/test_planner_validator.py::TestTheDeclineExplainsItself::test_a_failed_result_without_a_disclosure_is_refused
V20  covered      tests/test_planner_validator.py::TestBoundSourceIsProvenanceNotAGuess::test_the_source_is_read_off_the_target_not_inferred
V22  covered      tests/test_planner_validator.py::TestTheDeclineExplainsItself::test_the_protein_disclosure_keeps_one_decimal
```

Each row names a correctly-scoped test, and in each case it is the test written
for that mechanism rather than something incidental. The suite itself:

```
1 failed, 409 passed, 40 skipped, 1 warning in 111.18s
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
```

395 → 409 is the fourteen new tests exactly. The one failure is D10's
deliberately-red test, unchanged and untouched.

### Finding 35 — the harness's verdict depended on the shell that launched it — **FIXED**

The first run of the sweep above returned this, for all nine rows:

```
9 mechanisms: 0 covered, 9 soft-covered, 0 SURVIVED, 0 harness errors.
C3   soft-covered 1 incidental: (non-test failure; see output)
```

Nothing was wrong with the tests. `_run_suite` classified by matching
`line.startswith("FAILED ")`, and pytest had written its summary as
`"\x1b[31mFAILED\x1b[0m tests/..."`, so no line matched and every mutation was
recorded as a crash. Confirmed by running one mutation (`V22`) through the
identical `subprocess.run` call and printing the raw bytes:

```
returncode: 1
FAILED tests/test_planner_validator.py::TestTheDeclineExplainsItself::test_the_protein_disclosure_keeps_one_decimal - AssertionError: assert '29.5g' in 'This plan delivers 30g of protein agains...
1 failed, 408 passed, 40 skipped, 1 deselected, 1 warning in 108.02s
```

The right test failed, alone, for the right reason. Only the parser was blind.

**Why this is a finding and not a typo.** pytest colours output when
`FORCE_COLOR`/`PY_COLORS` is inherited, and suppresses colour when stdout is a
plain pipe. So the harness gave a *different answer for identical code
depending on which shell ran it* — the same class as findings 11 and 18 in this
log, and the one the probe exists to prevent. The D4b-i numbers already
recorded above were taken in an uncoloured shell (had they not been, all 55
rows would read "non-test failure" instead of naming test ids), so they stand
— but they stood by luck.

**Disposition:** FIXED. Three independent defences, since any one of them can
be defeated by an environment: `--color=no` on the command, the three colour
env vars forced off in the subprocess, and an ANSI strip before matching.

### Finding 32 — CLOSED

`test_region_mismatch_excludes_a_recipe` no longer feeds `SOUTH_LUNCH` a recipe
the category filter would have rejected anyway. It now builds two synthetic
components differing **only** in region — same category (`poriyal`, asserted to
be one `SOUTH_LUNCH` accepts), same ingredient, same serving unit — and checks
the southern twin survives before checking the northern one does not. The
control is the load-bearing half: without it, an empty pool proves nothing
about which filter emptied it, which is precisely how the old test passed
against a deleted region check.

A second test covers the other arm of the same condition,
`not in (template.region, Region.PAN_INDIAN)`: a mutation narrowing it to the
template's region alone would silently drop every pan-Indian recipe from every
plate while leaving the first test green.

The observation underneath finding 32 is unchanged and still true — the real
library's categories are region-partitioned, so the region filter does no work
on today's data. It is now tested rather than dormant-and-untested.

### Finding 33 — CLOSED, decided in opposite directions

The two dead-code survivors got different answers, because they are not the
same case.

**`C8`, `for_slot`'s `seen` dedup — REMOVED.** Being unreachable would on its
own argue for keeping it: harmless, cheap, defensive. The reason to remove it
is that it does not guard the duplicate a reader would assume it does. One
recipe offered under two categories a slot both accepts produces components
with *different* ids (`r@a`, `r@b`), so the same dish appears twice and the
dedup never fires. Code that reads like a duplicate guard, while not handling
the only duplicate that can actually occur, is worse than no guard — the next
person to face that case will believe it is already handled. The invariant that
makes the sort total without it is now stated in `for_slot`'s docstring.

**`B2`, `enumerate_combinations`' early `return ()` — KEPT, with a comment.**
Its deletion is behaviour-preserving for the return value, as recorded. What it
preserves is the *diagnosis*: falling through reaches the second `logger.info`,
which reports "0 combinations, naive bound N, Nx smaller" — an enumeration that
pruned everything — and never names the blocking slot. Those are different
facts about the library and only one of them is what a decline is built from.

`C8`'s row is deleted from the probe rather than left to report "pattern not
found" forever. `B2` keeps its row, retargeted at the surviving line, with its
expected result recorded as *survives* — a row whose answer is known is worth
more than no row, because it stops the next sweep rediscovering it as news.

Re-measured after both edits, since removing code from `for_slot` could have
taken the coverage of the mechanism beside it as well:

```
4 mechanisms: 3 covered, 0 soft-covered, 1 SURVIVED, 0 harness errors.
C3   covered      tests/test_planner_candidates.py::TestHardFilters::test_region_mismatch_excludes_a_recipe
C7   covered      tests/test_planner_determinism.py::TestOrderDoesNotDependOnCategoryIteration::test_candidates_come_back_sorted_by_id
B2   SURVIVED
V10  covered      tests/test_planner_validator.py::TestRungFourInIsolation::test_a_locked_protein_floor_is_returned_untouched
```

`C7` is finding 18's `for_slot` sort — the line immediately below the deleted
dedup — and it still goes red on its own deletion. `B2` survives with its
retargeted row located, which is the documented expected answer rather than a
harness error.

### A harness change that was needed to do this honestly

The probe ran whatever `git worktree add HEAD` checked out, so it could only
grade already-committed code. That inverts the practice it enforces:
`CLAUDE.md` says to watch a test fail before believing it, and a test you must
commit before you can watch it is a test you have already believed. It bit
twice in one session — first on the new tests, then again on `B2`'s retargeted
row, which reported "pattern not found" against a `core/` that predated the
edit the row was written for, reading as a harness error rather than as the
stale checkout it was.

Both `core/` and `tests/` are now copied in from the working tree. The worktree
contributes isolation and nothing else, which was its only stated job in this
probe anyway. The id filter (`... d4b_mutations.py C3,V10,V11`) exists for the
same reason — grading nine mechanisms should not cost a 55-run sweep.

### On the two tests the reviewer asked to look at

`V10`'s test states in its own body that it calls `_relax_protein` directly
because the ladder cannot reach the guard, and names `RelaxationStep.
is_fully_locked` as the reason, with the instrumentation result (395 passed,
branch never executed) quoted. Without that, it reads as an ordinary
clinical-locking test and the next reader concludes the ladder path is covered
by it — finding 32's failure mode inverted, a test overstating its reach. It
also points at `V13`, which is what actually covers the ladder path.

`V11`'s test asserts the protein ceiling's **value** is unchanged (90.0 before,
90.0 after), not that some plate fits under it, mirroring the claim
`_relax_protein`'s docstring makes. It then walks all four rungs cumulatively,
since a later rung reconstructing the target could move the ceiling just as
silently as this one could.

**Disposition:** findings 32, 33, 34 CLOSED. Finding 35 raised and FIXED.
**Finding 26 CLOSED** — it asked for a deletion test on every gate in the
enumeration, solver and validator paths, an audit of the gates without one, and
the practice written into `CLAUDE.md`. The count and audit landed in D4b-i, the
practice is in `CLAUDE.md`'s "Deletion testing" convention, and the gaps that
audit found are closed here. Two survivors remain and both are documented
expected results, not gaps: `B2` above, and `B8` (the quality pre-filter, which
`CLAUDE.md` already states is "a pure optimisation: removing it changes no
verdict"). `B5` remains a bad mutation of the probe's own and is not a
mechanism. Findings 22, 28, 29, 31, 2, 15, 20 untouched.

---

## 2026-08-09 — D4b-i: every gate in the planner, deleted one at a time

Finding 26 asked for a deletion test on every gate and guard in the
enumeration, solver and validator paths, and said to "count them first and say
the number." This entry is the count and the coverage audit. The tests the
audit calls for are **not** in this commit; they are D4b-ii.

Everything below comes from `docs/design/probes/d4b_mutations.py`, which holds
one entry per mechanism and the smallest edit that deletes it, applies each edit
to a throwaway git worktree, runs the suite, records which tests fail, and
reverts. The real checkout is never written to.

### The count: 55, not the ~25 the task estimated

| module | mechanisms |
| ---------------------------- | ---: |
| `core/planner/candidates.py` | 9 |
| `core/planner/combinations.py` | 8 |
| `core/planner/solver.py` | 11 |
| `core/planner/validator.py` | 27 |

`validator.py` is where the estimate went wrong. The ladder is not one
mechanism but roughly a dozen: `_capped`'s clip, `_widen_band`'s two skips and
its `replace`-rather-than-reconstruct, rung 1's widen-don't-drop, each rung's
locked-macro skip, the order of `RELAXATION_ORDER` itself, the fully-locked-rung
skip, and the three construction-time checks in
`ValidationResult.__post_init__`. Each is separately deletable and separately
load-bearing. D4a's five injections are excluded from the count, per the task.

### The result

```
55 mechanisms: 41 covered, 1 soft-covered, 13 SURVIVED, 0 harness errors.
```

**covered** — at least one correctly-scoped test fails when the mechanism is
deleted. **soft-covered** — tests fail, but only end-to-end ones that do not
know what they are protecting. **SURVIVED** — nothing in the suite fails.

"Correctly scoped" is a file-level judgement, written down in the probe as
`OWN_TESTS` rather than applied silently per row. `tests/test_planner_plan.py`
is deliberately scoped to nothing: it is the wiring test, by its own docstring.

### Two measurement errors made while producing this, both corrected

**`-x` cannot classify.** The first sweep ran `pytest -x`, so each row recorded
the first failure in pytest's *collection* order — alphabetical by filename,
unrelated to which test is about the mechanism. It reported the solver's
quality gate (`S3`, finding 26's own founding example) as held up by
`test_planner_plan.py`, and two mechanisms as held up by `test_api_auth.py`,
producing an apparent "a third of the suite is soft coverage" that was pure
alphabetical artifact. Running `tests/test_planner_quality.py` alone against
the same mutation gives:

```
FAILED tests/test_planner_quality.py::TestTheSolverGateItself::test_the_gate_changes_the_chosen_unit_counts
FAILED tests/test_planner_quality.py::TestTheSolverGateItself::test_the_gate_can_empty_a_solve_the_pre_filter_admitted
2 failed, 34 passed in 1.64s
```

Two tests named after the gate. **Finding 26's founding example is genuinely
covered** — `TestTheSolverGateItself` was added after the finding was raised.
The probe now runs the whole suite every time and collects every failure.

**Plate-pinning tests inflate "covered", and were checked rather than assumed.**
Six rows were attributed to `TestAgainstTheRealLibrary` classes, which pin an
exact plate and so break on almost any planner change despite living in scoped
files. `UNSCOPED_CLASSES` now excludes them, and the sweep was re-run. **The
totals did not move**: every one of the six had a second, properly-scoped test
behind the pin (`S1`/`S2`/`S8`/`S9` → `TestTheSolverGateItself`, `S5` →
`TestThePerturbationTest`, `V26` →
`TestLadderFires::test_the_sodium_rung_fires_first_and_silently`). 41 is not an
upper bound.

### Finding 32 — the region hard filter is unenforced, and its test says so — **OPEN**

Deleting the region check in `_passes_hard_filters` entirely — letting a North
Indian recipe into a South Indian template — breaks nothing in the suite. A
correctly-named test exists and asserts too little:

```python
def test_region_mismatch_excludes_a_recipe(self, library, ingredients):
    # rajma_chawal is north_indian; south_lunch's region is south_indian
    # and rajma_chawal is not pan_indian, so it must not appear even
    # though combo_rice_legume is not a south_lunch category anyway.
    ...
    assert pool.by_category == {}
```

The comment concedes the redundancy and the assertion is satisfied by the
*category* filter alone. Nor can the fixtures express the case: `make_recipe`
defaults `region=Region.SOUTH_INDIAN` and nothing overrides it.

Underneath that: **the real library's categories are region-partitioned**, so
the region filter is redundant with the category filter for every recipe that
exists today. North carries `sabzi`/`dal`/`roti`/`raita`/`legume_curry`/
`combo_rice_legume`; south carries `tiffin`/`sambar`/`kuzhambu`/`chutney`/
`rice`/`mixed_rice`/`poriyal`/`kootu`/`curd`. Nothing overlaps. The gate is real
but dormant, and starts binding the first time a category spans regions.

This qualifies a claim in `CLAUDE.md`'s build-status table: D3 argues the north
plates "could not fail to be" unchanged because "`candidates.py` rejects a
recipe whose region is neither the template's nor `pan_indian`." The conclusion
holds, but for today's data it holds via the category filter — the region filter
does no work. Noted rather than edited, since the conclusion stands.

**Disposition:** OPEN. The fix is a synthetic fixture carrying a south category
with `region=Region.NORTH_INDIAN`, following the precedent of
`test_allergen_overlap_excludes_a_recipe`, which builds synthetic rather than
borrowing from the library. D4b-ii.

### Finding 33 — two survivors are dead code, not missing coverage — **OPEN**

Neither can be covered by any test, because deleting them is behaviour-preserving
for every possible input.

- **`C8`**, `for_slot`'s `seen` deduplication. `Component.id` is
  `f"{recipe.id}@{category}"` and `build_candidate_pool` files each component
  under `by_category[component.category]`, so the bucket a component sits in is
  always the category embedded in its own id. Iterating a slot's accepted
  categories cannot yield the same id twice.
- **`B2`**, `enumerate_combinations`' early `return ()` when a required slot has
  no legal selection. `itertools.product` over a sequence containing an empty
  slot is empty anyway — verified, not reasoned:
  `list(itertools.product(('a','b'), (), ('c',))) == []`. The early return
  changes only a log line.

**Disposition:** OPEN, deliberately not fixed here. Deleting code in
`core/planner` is outside this commit's scope (harness plus audit), and the
right disposition for each — remove, or keep with a comment saying it is
defensive — is a judgement worth making on its own.

### Finding 34 — eight mechanisms have no test that fails on their deletion — **OPEN**

| id | module | mechanism |
| --- | --- | --- |
| `S6` | `solver.py` | an empty plate is still gated (0 g of qualifying protein) |
| `S7` | `solver.py` | unset quality protein defaults conservatively to 0.0 |
| `V8` | `validator.py` | the `bound_source` follows the number when the guard clips it |
| `V10` | `validator.py` | rung 4 skips protein entirely when a flag locks it |
| `V11` | `validator.py` | rung 4 lowers the floor only, never raises the ceiling |
| `V16` | `validator.py` | a failed result must carry a disclosure |
| `V20` | `validator.py` | `bound_source` is read off the target, never inferred |
| `V22` | `validator.py` | the protein disclosure keeps one decimal |

Three survivors are not in this table and are not gaps. `B5` is a bad mutation
of the probe's own: it mutates the *low* side of `quality_protein_bounds`, and
every caller reads `[1]` — grepped, nothing reads `[0]`. `B8` is expected and
already documented: `CLAUDE.md` states the quality pre-filter is "a pure
optimisation: removing it changes no verdict," and the sweep confirms the doc.
`C3` and the two dead-code rows are findings 32 and 33.

**Disposition:** OPEN. D4b-ii writes these eight plus finding 32's fixture fix.

### The V10 misdiagnosis — a survived mutation is not a hole until reachability is checked

`V10` was first reported as a live clinical-safety hole: deleting
`if "protein_g" in locked: return target` from `_relax_protein` would let a
chronic-kidney-disease profile have its protein floor lowered, and nothing
failed. That reading was wrong, and it was wrong in the direction that causes
work to be misprioritised — it was nearly given its own commit ahead of
lower-stakes tests on that basis.

Rung 4's `macros` is exactly `("protein_g",)`, and CKD is the only flag locking
protein, so `RelaxationStep.is_fully_locked` is true whenever the guard would
matter and the ladder skips the rung before `_relax_protein` is ever called.
Checked by instrumenting rather than by argument — an unconditional
`raise AssertionError` placed inside the guard, whole suite run:

```
395 passed, 40 skipped, 1 deselected, 1 warning in 88.77s
probe never fired: 0
```

The branch is never reached. The clinical property is enforced, by `V13`
(`test_a_fully_locked_rung_is_skipped_not_recorded_as_applied`, which pins the
CKD floor at 32.0 g). `V10` is defence-in-depth against a future rung that
groups protein with another macro, where `is_fully_locked` would be false. It
still earns a test — called directly, and the test must say in its own body why
it bypasses the ladder, or it will read as an ordinary clinical-locking test and
the next reader will believe the ladder path is covered by it.

**No survivor is a live clinical-safety hole.** Clinical locking is covered on
every rung: `V3` (rung 2), `V13` (rung 4 skip), `V27` (the decline sentence).

The general lesson, now in `CLAUDE.md`'s standing list: the harness makes
survivors cheap to produce, which makes this misreading the one most likely to
recur.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py solver
```

The second form limits the sweep to one module while iterating. A full run is
55 suite runs and takes roughly 40 minutes; it prints each row as it completes.

One note on the run that produced the figures above: it printed its complete
55-row table and summary and removed its worktree, but the shell reported exit
code -1. The artifact is complete and the numbers are the numbers; the exit code
is unexplained and is recorded here rather than guessed at.

**Disposition:** finding 26 measured, still OPEN — the count and the audit it
asked for exist; the tests do not yet. Findings 32, 33 and 34 raised, all OPEN,
all D4b-ii. Finding 24 CLOSED (2026-08-08) is untouched. Findings 22, 28, 29,
31, 2, 15, 20 untouched.

---

## 2026-08-08 — D4a: finding 24 closed on the decline path

> Title corrected 2026-08-09. It read "findings 24 and 26 closed" while this
> entry's own Disposition line said finding 26's sweep "is D4b and remains
> OPEN" — a heading claiming a closure the body denied, which is the class of
> unverified state claim `CLAUDE.md`'s process rule exists to prevent. Finding
> 26 is measured by the 2026-08-09 entry above and is still open until its
> tests land.

Scope note first, because it changes what the queue says. **D4 as written is
two tasks and only the first is done here.** Its second half — finding 26's
standing practice: a deletion test for every gate and guard in the
enumeration, solver and validator paths, an audit of the existing suite for
gates without one, and writing the practice into `CLAUDE.md` — is a full task
against three modules and ~25 mechanisms, and stapling it to a redesign of the
decline path would have produced one commit nobody can review. It is split out
as **D4b** and is NEXT. What is done here is the decline diagnosis, plus
deletion tests for the five mechanisms this change introduced (below), which is
finding 26's discipline applied to this change rather than to the whole suite.

Every figure below is from
`PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py`
(144 profiles x 4 templates, today's `data/` library, `dev_mode=True`) or from
the `demo.py` commands in "Reproduce".

### The measurement, before and after

The probe sweeps a profile grid, keeps every decline, and compares what the
decline **says** against two things computed independently of the code under
audit: which bounds are structurally unreachable (from each component's
serving-unit min/max), and which bounds the combination closest to feasible
misses.

|                                                        | before | after |
| ------------------------------------------------------ | -----: | ----: |
| declines across the grid                                |    156 |   156 |
| declining with an empty pool, naming no slot            |     72 |     0 |
| omitting a cause that is actually blocking              |     12 |     0 |
| naming a bound as blocking that the nearest plate meets |     30 |     0 |
| distinct decline shapes                                 |     50 |    36 |

The verdicts themselves did not move: 156 declines before and after, and
`tests/test_planner_decline.py::TestAgainstTheRealLibrary` pins that the
reference profile still gets a plate on all four templates. This changed what a
decline says, not who is declined.

**Both columns above are re-measurable; the commands are in "Reproduce" below.**
Corrected 2026-08-08, after the entry was first written: as originally committed
the before column was **not** reproducible. `d4_declines.py` read
`Violation.blocking_slots` directly, and that field does not exist before D4a,
so the probe raised on the pre-D4a tree and only the after column could be taken
again. The numbers were real when taken and both reproduce unchanged now that
the probe runs on both trees — but "real when taken" is precisely the standard
`CLAUDE.md`'s process rule rejects, and a delta nobody can re-measure is not
evidence, whatever its provenance. The fix is one `getattr` with the reason
written at the call site; every other field the probe touches was checked to be
present in both trees rather than assumed. A probe that measures a change has to
run on both sides of it, and that is a property to check when the probe is
written, not after someone asks.

### Finding 24 — CLOSED

Two defects, opposite directions, one cause: `_blocking_violations` stopped at
the first thing it found.

**It stopped at the first cause.** The function returned the
structurally-unreachable bounds *or*, only if there were none, the nearest
plate's misses. From slice 4 onward a South Indian decline named the
quality-protein floor and nothing else, because an unreachable quality floor
made the first half non-empty and the second half never ran. Recorded at the
time as "a decline can now say less than it used to" (2026-08-07, OPEN); it is
this. Both halves now always run and merge, keyed by `(macro, kind)` so a bound
reported unreachable is not also reported jointly infeasible.

**When it did reach the second half, it picked the wrong plate.** The nearest
combination was chosen by the solver's deviation score. That score measures
distance from each macro's ideal *point*, and sodium and fibre have no
registered point at all (`core.nutrition.target.simple_target`), so a plate's
saltiness contributes exactly nothing to it. Measured, 110 kg fat-loss
vegetarian, `north_lunch`:

    BEFORE
      kind='above_ceiling' macro='fat_g'     actual=37.1   bound=34.1
      kind='above_ceiling' macro='sodium_mg' actual=1418.5 bound=1400.0

    AFTER
      kind='below_floor'   macro='protein_g' actual=54.9   bound=58.9
        reach='jointly_infeasible' relaxability='relaxed_to_limit'

A plate existed — phulka x3, soya_chunk_curry x2, paneer_masala x1 — that met
both named bounds and broke only the protein floor. The user was told to go
looking for leaner, less salty dishes to fix a protein shortfall. Ranking is now
**fewest bounds broken**, tie-broken by score.

### The structure a decline screen needs

Two token vocabularies on `Violation`, in the same style as
`core.nutrition.target.BOUND_SOURCES` and subject to the same rule — they are
`snake_case` identifiers, they cross the API, and they must never reach a
visible text node.

- `VIOLATION_REACH`: `unreachable` (no plate this library can build satisfies
  it, so no substitution helps) | `jointly_infeasible` (reachable alone, not
  alongside the rest) | `plate_miss` | `empty_pool`. Finding 24's actual
  complaint was that these were indistinguishable.
- `VIOLATION_RELAXABILITY`: `relaxable` | `relaxed_to_limit` | `hard_capped`
  (a rung fired and `_capped` clipped it — the sodium guard's shape) | `locked`
  (a disclosed condition; the one case where "we did not try" is the honest
  answer) | `never_relaxed` (no rung touches it at all — the quality floor).
  Derived from `RELAXATION_ORDER` itself, not a hand-kept table, so a rung
  added later cannot leave a stale classification behind.

`Violation.blocking_slots` carries the required courses that had no legal
selection. Sourced from `core.planner.combinations.unfillable_slots`, which
calls the enumerator's own `_slot_selections` rather than asking whether the
slot has candidates — a slot with two candidates and `min_selections=3` has
candidates *and* no legal selection, and the obvious implementation would name
nothing. Measured, vegan `south_lunch` (the one real-library pair that
enumerates zero combinations):

    BEFORE  no recipe combination survived filtering for this profile, so
            there was nothing to solve
    AFTER   1 required course of this meal cannot be filled from the recipe
            library for this profile, so there was nothing to solve
            blocking_slots=['curd_course']

### Finding 30 — a clinical-flag identifier was being written into user-facing prose — FIXED in the same commit

Found while carrying relaxable-vs-locked through. `Violation.describe` built
`f"(locked by disclosed condition: {names}...)"` from `ClinicalFlag.value`, so a
kidney-disease decline rendered the string `chronic_kidney_disease` into the
sentence `web/dashboard.js` displays verbatim. This is precisely the class
`tests/test_web_no_identifiers.py` exists to catch, and it missed it because no
web test renders a locked decline — the sweep is over static views, and a
decline disclosure is server-supplied.

Worse, `tests/test_planner_validator.py` **asserted the leak**:
`assert "hypertension" in outcome.result.disclosure`. It passed for months.
The prose now names no condition and the tuple travels as `locked_by`; that
assertion is inverted, and now also loops every `ClinicalFlag` value rather
than checking the one that happened to be in the test.

### Finding 31 — macro identifiers are still written into the same prose — **OPEN**

Noticed while fixing finding 30, logged and left per the queue's rule.
`Violation.describe` writes `f"{self.macro} is {actual}..."`, so a decline reads
`energy_kcal is 350.0kcal, above its ceiling of 300.0kcal`. Same defect class as
finding 30, same missed detection, and unfixed here because the remedy is a
macro-to-copy map, which is a decision about the screen and D4 says explicitly
not to design the screen. The structured fields a client needs to render it
properly (`macro`, `kind`, `actual`, `bound`, `bound_source`, `reach`,
`relaxability`) are all present and reach the API. Belongs with **D9**.

Related and also unfixed: `test_web_no_identifiers.py` cannot see either leak,
because it sweeps rendered static views and never exercises a decline. Whatever
D9 does about the copy, the sweep needs a decline in it or the third instance
of this class will be found the same way.

### Finding 26's discipline, applied to this change

Five mechanisms were introduced. Each was deleted, the suite re-run, and the
test that names it confirmed red before the mechanism was restored:

| defect injected                                                      | went red                                          |
| -------------------------------------------------------------------- | ------------------------------------------------- |
| rank nearest plate by `score` alone (`key = (0, plan.score)`)         | 4 tests, incl. `test_it_does_not_report_the_first_enumerated_plate_instead` |
| restore `if unreachable: return unreachable`                          | `test_an_unreachable_bound_no_longer_hides_the_reachable_ones` |
| `unfillable_slots` asks `not pool.for_slot(slot)`                     | `test_a_slot_with_candidates_but_no_legal_selection_still_counts` |
| `_relaxability` returns a constant                                    | 3 tests in `TestRelaxabilityIsDerivedFromTheLadderItself` |
| re-interpolate `ClinicalFlag.value` into `describe`                   | `test_with_hypertension_the_same_target_is_declined_instead` |

The joint-infeasibility fixture is built so its expected values are exact
rather than envelopes: `tests/factories.py`'s FEASIBILITY components pin
`min_count = max_count = 1`, so each of the four combinations is one point.
`TestTheLadderIsInertOnThisTarget` checks that all four rungs fire and move
nothing, so every hand-computed figure in that file stays valid if a rung
gains an effect later — the alternative was a comment asserting it.

### Reproduce

The **after** column of the table above, and every figure in this entry that is
not marked "before":

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py
python demo.py plan --region north_indian --meal-slot lunch --weight-kg 110 --goal lose_fat
python demo.py plan --region south_indian --meal-slot lunch --diet vegan
python -m pytest tests/test_planner_decline.py -q
```

The **before** column. The probe is copied into a worktree of the pre-D4a
commit rather than run from the old tree's own copy, so both columns come from
one probe implementation and a difference between them is a difference in
`core/`, not in how the two probes counted:

```bash
git worktree add /tmp/pre_d4a b72060e
cp docs/design/probes/d4_declines.py /tmp/pre_d4a/docs/design/probes/
cd /tmp/pre_d4a && PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py
git worktree remove /tmp/pre_d4a --force
```

`b72060e` is D5, the commit D4a was built on. Both runs, 2026-08-08:

```
before: 156 declines across the grid, 50 distinct shapes.
          72 decline with an empty pool, naming no slot
          12 omit a cause that is actually blocking
          30 name a bound as blocking that the nearest plate meets

after:  156 declines across the grid, 36 distinct shapes.
          0 decline with an empty pool, naming no slot
          0 omit a cause that is actually blocking
          0 name a bound as blocking that the nearest plate meets
```

**Disposition:** finding 24 CLOSED. The 2026-08-07 observation "a decline can
now say less than it used to" CLOSED — it was finding 24. Finding 30 FIXED.
Finding 31 OPEN, for D9. Finding 26's full sweep is D4b and remains OPEN.
Findings 22, 28, 29, 2, 15, 20 untouched.

---

## 2026-08-08 — D5: finding 22 re-scoped, and D5's own premise was wrong

Every figure below is from
`PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d5_margins.py`,
reference profile (70 kg / 175 cm / 28 / male / moderate / maintain /
vegetarian), today's `data/` library, `dev_mode=True`. Nothing was edited:
the guard sweep wraps `citations.value_of` in memory and restores it.

### D5's premise, restated and then contradicted

TASKS_2.MD's D5 says: "whether the app can plan a South Indian lunch currently
turns on half a percent of a number nobody derived." That reads the 8.9 mg
figure as the verdict's sensitivity to the guard. It is not. It is the chosen
**plate's** slack against the guard. Those are different quantities, and the
second one was never measured until now.

Measured — the guard moved, everything else held, pass/decline bisected over 40
iterations:

```
  Bisected pass/decline boundary per template (40 iterations):
    south_indian/breakfast: flips at 0.504835 =  1009.7 mg; registered 0.70 = 1400.0 mg is 390.3 mg (27.9%) above it
    south_indian/lunch: flips at 0.545743 =  1091.5 mg; registered 0.70 = 1400.0 mg is 308.5 mg (22.0%) above it
    north_indian/lunch: flips at 0.466169 =   932.3 mg; registered 0.70 = 1400.0 mg is 467.7 mg (33.4%) above it
    north_indian/dinner: flips at 0.436229 =   872.5 mg; registered 0.70 = 1400.0 mg is 527.5 mg (37.7%) above it
```

south_lunch does not stop passing at 1391 mg, or at 1300, or at 1200. It stops
passing at **1091.5 mg** — the guard would have to fall 22% before the verdict
moves. The verdict's margin on the guard is 308.5 mg, not 8.9 mg. **The goal as
written was wrong**, in the specific way TASKS_2.MD's "How to work this file"
anticipates, and this is the third time.

What actually happens as the guard falls is that the plate changes and the
ladder walks further, verdict intact:

```
  0.55 -> guard  1100.0 mg | south_break=pass(2r,1072mg)  south_lunch=pass(4r,1091mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(2r,872mg)
  0.60 -> guard  1200.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(4r,1091mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1148mg)
  0.65 -> guard  1300.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(4r,1246mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1148mg)
  0.70 -> guard  1400.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(3r,1391mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1371mg)
  0.80 -> guard  1600.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(0r,1546mg)  north_lunch=pass(0r,1431mg)  north_dinne=pass(0r,1371mg)
```

The 4-rung south_lunch at 0.55–0.65 is worth noticing on its own: rung 4 is
protein tolerance, which carries mandatory disclosure. A tighter guard does not
turn south_lunch off, it turns it into a plate that has to apologise for its
protein.

### Finding 22, re-stated in its current form — still **OPEN**

The 2026-08-02 wording ("a multi-dish South Indian plate cannot get under the
sodium guard"; two of three south_lunch combinations unreachable at their
minimum counts) is **obsolete**: D3's `steamed_rice` and `soya_kuzhambu` changed
the enumerated set (3 -> 12 combinations), and all four templates now pass. The
finding survives in a narrower form:

> **Sodium is the only bound in the system whose ceiling is a project decision
> with no derivation, and it is simultaneously the bound closest to two of the
> four passing plates.** south_lunch sits 8.9 mg (0.6%) under it; north_dinner
> sits 28.7 mg (2.0%) under it. Both are hard-ceiling contacts — no relaxation
> rung may widen past 1400 mg, so a plate 9 mg over it is a decline with no
> recourse, however loose every other bound is.

Note the correction embedded there: the D5 task asked whether the other three
templates have comparable margins. **north_dinner does** — 28.7 mg, 2.0%, and
tighter still by the measure that matters (see below). Nobody had noticed it
either. south_breakfast (210.2 mg, 15.0%) and north_lunch (407.8 mg, 29.1%) do
not.

### Slack is the wrong unit; the smallest legal move is the right one

Portion space is integer unit counts, so a bound is not "nearly breached"
because slack is small in absolute terms — it is tight when slack is smaller
than the smallest legal one-unit move on that plate. By that measure the
sodium picture inverts:

| template | Na slack | smallest legal move raising Na | verdict |
|---|---|---|---|
| south_breakfast | 210.2 mg | 40.9 (chutney 2->3) | loose |
| south_lunch | **8.9 mg** | **2.0** (steamed_rice 1->2) | **loose** |
| north_lunch | 407.8 mg | 59.9 (phulka 5->6) | loose |
| north_dinner | **28.7 mg** | **59.9** (phulka 3->4) | **TIGHT** |

south_lunch's famous 8.9 mg is *not* a cliff edge in unit space: unsalted rice
is available in 2.0 mg increments, so the plate has room to move without
touching the guard. north_dinner's 28.7 mg **is** a cliff: every legal increment
on that plate costs at least 59.9 mg of sodium.

Both south plates and both north plates were also checked against every legal
single-unit neighbour, which is the honest version of the per-macro `step`
number because one unit move changes every macro at once:

```
south_lunch  -> 0 of the plate's single-unit neighbours are feasible
north_lunch  -> 0 of the plate's single-unit neighbours are feasible
north_dinner -> 0 of the plate's single-unit neighbours are feasible
south_breakfast -> 1 (coconut_chutney 2->3)
```

Three of the four passing plates are **point solutions**: not one adjacent
portion assignment is admissible. That is a property of a narrow library and
tight energy bands, not of sodium — the neighbours die on `energy_kcal` far
more often than on `sodium_mg`.

### What could change, and what each costs — **not picked, deliberately**

D5 says lay out the options and do not choose. Five, with the cost of each:

1. **Move the guard's value.** Cheapest to do, and now measured to buy nothing:
   the verdicts are stable from 0.55 to 1.00. Its real effect is on plate
   *choice* and rung count, not on pass/fail. Cost: re-registering a
   `PROJECT_DECISION` for an effect the sweep says is not the one anyone
   thought it had.
2. **Remove the guard.** The 2026-08-02 entry records why it exists: a bare
   remaining-budget check puts no limit at all on the first meal of a day, and
   a 1649.3 mg lunch passed one. Cost: that case returns.
3. **Let rule (ii) relax.** `core/nutrition/meal_target.py` states the reason it
   does not: rung 1 widens sodium by 0.50, so a widenable 0.70 guard permits a
   plate carrying 105% of a day's sodium. Cost: exactly that, and it is the
   outcome the guard was introduced to prevent.
4. **Re-derive the salt lines.** The sensitivity is measurable and is the axis
   D5's goal is actually about, since recipe work moves the plate and not the
   guard. Measured, every `sodium_mg` in the library scaled uniformly:
   ```
    south_indian/breakfast: still passes at x1.387 (+38.7% on every salt figure in the library)
    south_indian/lunch: still passes at x1.283 (+28.3% on every salt figure in the library)
    north_indian/lunch: still passes at x1.502 (+50.2% on every salt figure in the library)
    north_indian/dinner: still passes at x1.605 (+60.5% on every salt figure in the library)
   ```
   Every salt estimate in the library could be 28% low and all four templates
   would still pass. Cost: this is a *uniform* scaling and therefore an
   optimistic bound — a single dish being 30% under-salted is not covered by it.
5. **Nothing.** Defensible on this evidence, and it is what D5 forbids acting
   against anyway.

### What a reader should conclude about the four passing templates

They are a **result**, on the sodium axis, and something closer to a
**coincidence** on the energy axis.

Sodium: 22–38% of guard margin and 28–60% of salt-estimate margin behind every
verdict. Recipe work would have to be badly wrong, not slightly wrong, to flip
one. D5's fear does not survive measurement.

Energy: three of four plates have no feasible neighbour at all, and the
tightest bounds in the whole table are energy bounds — north_lunch's energy
ceiling has 13.6 kcal of slack against a 98.9 kcal smallest move (1.4%), and
south_lunch's *unrelaxed* energy floor is **missed by 6.7 kcal**, which is why
its third rung fires. One recipe's energy changing by a few percent moves those.
The honest reading: sodium is the bound everyone has been watching and is not
the fragile one; energy is fragile, on a band nobody has been watching, and no
task in the queue is about it.

### Finding 28 — the sodium guard is the only thing in the system that prefers less salt — **OPEN**

Raised by the sweep, not fixed here.

Nothing in the solver's objective penalises sodium: `NutritionTarget.points`
has no sodium entry, so any plate under the ceiling scores identically on that
macro. The consequence is visible as the guard rises:

```
  0.70 -> north_lunch=pass(0r, 992mg)   south_lunch=pass(3r,1391mg)
  0.80 -> north_lunch=pass(0r,1431mg)   south_lunch=pass(0r,1546mg)
  0.90 -> north_lunch=pass(0r,1733mg)   south_lunch=pass(0r,1546mg)
```

north_lunch's sodium **rises 741 mg (+75%) when the ceiling is loosened**, on
the same library and the same profile. Relaxing a limit made the plan worse in
the dimension the limit exists to protect. The guard is not acting as a
plausibility backstop here; it is acting as the sodium objective, because there
isn't one. A backstop and an objective are different mechanisms, and a system
where the only pressure toward less salt is a never-relaxing ceiling will always
serve the saltiest plate it is allowed to.

This is why option 1 above ("move the guard's value") is not the free
no-op the verdict sweep alone makes it look like: the verdicts do not move, but
the plates do, and they move in the wrong direction.

**Disposition.** OPEN. Not fixed here — D5 forbids tuning, and adding a sodium
term to the solver objective is a design decision about what the product
optimises for, not a defect fix.

### Finding 29 — relaxation rung 1 lets a *day* exceed its own sodium budget — **OPEN**

Raised while reconsidering the queue (slice 6 is about sequencing south meals
inside one day's sodium budget), not by the probe. Logged and left, per
TASKS_2.MD.

`core/nutrition/meal_target.py` sets two sodium bounds per plate:
`ceilings["sodium_mg"] = min(remaining, guard)` and
`hard_ceilings["sodium_mg"] = guard` — **the hard ceiling is always the
per-plate guard, never `remaining`.** So when the day's remaining budget is the
binding term, rung 1 of the ladder (`sodium_max_fibre_min`, ×1.5) is free to
widen it, and nothing catches the result at the day level.

Measured, south breakfast then south lunch for the reference profile:

```
$ python demo.py plan --region south_indian --meal-slot lunch --sodium-spent-mg 1189.8

      sodium_mg    floor         -   ceiling     810.2   [what the day has left]
  TARGET AS SOLVED (after 4 relaxation rung(s): ... ):
      sodium_mg    floor         -   ceiling    1215.3   [what the day has left]
  point        : 944.6 kcal, 35.0g protein, 24.3g fat, 144.8g carb, 1091.5mg sodium
```

The 1189.8 mg is the measured south_breakfast plate from the probe above.
2000 − 1189.8 = 810.2 remaining; 810.2 × 1.5 = 1215.3; the lunch plate takes
1091.5. Two meals, **2281.3 mg against a 2000 mg day budget — 14.1% over, with
one meal still to plan**, and no violation reported.

The 2026-08-02 entry that introduced the guard argued precisely this shape and
stopped one step short: it prevented *one plate* carrying 105% of a day, and
did not prevent *two plates* carrying 114% of one. `hard_ceilings` was made to
hold the guard still while tolerance moves around it; the day's remaining
budget was left with no such protection, and it is the bound that actually
encodes "a day".

Not a defect in rung 1 as such — the ladder is supposed to widen ceilings. The
question it raises is whether `day_remaining` is a tolerance at all, or a second
bound of the `hard_ceiling` kind that the ladder should skip. That is slice 6's
decision, not a fix to make here.

**Disposition.** OPEN. Blocks nothing today (nothing sequences a day yet); it
is the first thing slice 6 will hit.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d5_margins.py
python demo.py plan --region south_indian --meal-slot lunch --sodium-spent-mg 1189.8
```

Full transcript is the probe's own output; the excerpts above are verbatim from
it. `docs/design/probes/README.md` lists it.

---

## 2026-08-07 — D3: making the south templates reachable

Three recipes (`idli`, `steamed_rice`, `soya_kuzhambu`) added so both South
Indian templates can satisfy the quality floor slice 4 introduced. Full account
in `docs/methodology.md`, "Making the south templates reachable". One new
finding, one prediction scorecard.

### The prediction, and it held completely

Written and stated before any file was created, from the per-unit table alone.
All six calls held, including both exact plates and both sodium figures:

| Prediction | Measured |
|---|---|
| south_breakfast passes, **0 rungs**, idli ×6 + soya_kuzhambu ×1 + coconut_chutney ×2 + thayir_plain ×1, 623.8 kcal, 1189.7 mg Na | passes, 0 rungs, that plate, 623.6 kcal, 1189.8 mg Na |
| south_lunch passes, **3 rungs**, ≈ steamed_rice ×1 + soya_kuzhambu ×2 + vegetable + thayir_plain ×1, ~848 kcal | passes, 3 rungs, steamed_rice ×1 + soya_kuzhambu ×2 + carrot_poriyal ×2 + thayir_plain ×1, 848.1 kcal, 1391.1 mg Na |
| sodium binds, and it is why two of the three recipes exist | held — see below |
| north verdicts do not move, because `candidates.py` filters on region | held, byte-identical, 24 and 12 combinations |
| combinations 2 → 8 and 3 → 12 | held |

Worth recording *why* it held, since the previous session's prediction did not:
this one was made from a measured per-unit table (`nutrition_of_recipe` over the
whole library) and hand arithmetic against the printed meal targets, not from
reasoning about what the rule "should" do. The one thing not predicted was
finding 27 below, which is a crash rather than a wrong answer.

**The sodium claim is backed by defect injection, not assertion.** Removing
`steamed_rice.yaml` alone puts south_lunch back into decline with
`Violation(macro='sodium_mg', kind='above_ceiling')`; removing `idli.yaml` alone
drops south_breakfast from 0 rungs to 3. Removing `soya_kuzhambu.yaml` is the
only one of the three that produces a *quality* decline.

### Finding 27 — a serving unit whose floor is above 1 crashed the candidate filter — FIXED in the same commit

`core/planner/candidates.py::_eligibility_flags` priced every candidate at a
hard-coded count of 1, while `nutrition_of_recipe` enforces the serving unit's
`[min_count, max_count]` bounds. Every recipe in the library happened to have
`min_count == 1`, so the two agreed by coincidence for the project's whole life
so far. `idli` is the first with a floor of 2 — nobody is served one idli — and
adding it made `build_candidate_pool` raise `ValueError: idli: count 1 outside
[2, 6]` before it could filter anything, for every template containing it.

The line's own comment already read *"any count in the unit's domain gives the
same fraction"* while the code used a count that need not be in that domain. The
comment was right and the code did not implement it — the same class of gap
CLAUDE.md's round-4 addendum is about, in miniature.

Three tests in `tests/test_nutrition_of.py::TestEligibilityConsequence` carried
the identical hard-coded 1 and crashed the same way.

**Disposition: FIXED.** `_eligibility_flags` and the three tests now use
`component.recipe.serving_unit.min_count`, which is in the domain by
construction. `tests/test_planner_candidates.py::TestServingUnitsWhoseFloorIsAboveOne`
pins it, with a second test proving the substitution is *safe* rather than
merely working: the eligibility fraction is identical at every count across
idli's whole 2–6 domain. Injection: reverting the line to `1` turns 9 tests red
across three files, including both new ones.

**What this says about coverage.** Nothing detected it because nothing exercised
it. `ServingUnit.min_count` has been a settable field since `core/foods/models.py`
was written and every recipe author independently chose 1. A field whose only
tested value is its default is not tested.

### Disposition of the older findings D3 touched

- **Finding 22** (south_lunch combinations unreachable at minimum counts) —
  still OPEN and untouched. The two offending combinations are still
  unreachable; D3 added a third rice_base/gravy pairing that is reachable. The
  passing south_lunch plate clears the 1400 mg guard by **8.9 mg**.
- **Finding 2** (a recipe with no `process:` lines reads as 0% process-uncertain)
  — still OPEN, now reachable with three real files rather than one:
  `thayir_plain`, `idli`, `steamed_rice`.
- **The "a decline can now say less" observation** from the slice-4 entry below
  — still OPEN. It is no longer visible on the south templates, because they
  pass, but it is a property of `_blocking_violations` and nothing about it
  changed.
- `tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants`
  was red before D3 (on `onion_raita`) and is red after (on `idli`, which sorts
  first). Same assertion, same defect class, deliberately not touched.

---

## 2026-08-07 — D2b-ii, slice 4: the quality-source rule

A per-meal floor on protein from ingredients clearing
`protein.quality_diaas_threshold` (0.75). Full description in
`docs/methodology.md`, "Protein quality is a rule about sources". Three
observations recorded here, one of them a defect in this session's own testing.

### The prediction, and where it was wrong

Written before any code was changed. Four of six calls held exactly:

- south_breakfast and south_lunch decline on quality — **held**, at exactly the
  predicted 8.99 g reachable against 11.2 g.
- north_lunch and north_dinner still pass with zero rungs, on plates containing
  soya or paneer instead of tofu — **held**, both.
- the three-katoris-of-dal plate is rejected on quality at 7.94 g — **held**
  (measured 7.936 g).
- `Profile.diet` still moves no target number — **held**.

**Wrong: the shape of the two south declines.** The prediction was that quality
would be named *alongside* energy, fat and sodium, since all four looked
individually unreachable. Measured, quality is named **instead of** them. The
cause is `_blocking_violations`' two-branch structure: energy/fat/sodium were
never in the unreachable branch at all — their reach spans the bound
(south_breakfast energy reaches 373.5–1326.8 kcal against a 707.0 ceiling), so
they were being reported by the later best-plate-probe branch. A genuinely
unreachable bound returns from the first branch and the probe never runs.

### Observation — a decline can now say less than it used to

Before: *"energy_kcal is 777.1kcal, above its ceiling of 707.0kcal; fat_g is
33.2g...; sodium_mg is 2273.4mg, above its ceiling of 1400.0mg"*.

After: *"only 9.0g of this plate's protein comes from a high-quality source,
against a floor of 11.2g"*.

The new sentence is the truest single thing — quality is unreachable at every
count, whereas the others were one probe plate's misses — but the user no longer
learns the plate is also 60% over the sodium guard. **Disposition: OPEN,
recorded, not fixed.** It is the same shape as finding 24 (a decline naming the
symptom rather than the cause), arriving from the other direction, and the
commissioning task ruled finding 24 out of scope.

### Finding 24 itself: checked, unmoved

`tests/test_planner_plan.py::TestPerMealProteinCeiling::
test_the_decline_names_energy_though_the_cause_is_the_protein_ceiling` still
passes unchanged. The quality rule does not fire on that synthetic case, so the
finding is neither fixed nor worsened.

### Finding 26 — a defect injection that the whole new test file survived — FIXED in the same commit

Deleting the quality check from `solver._within_target_point` — i.e. removing
the gate this slice exists to add — left **all 31 new tests green**.

Cause: `feasible_combinations` discards quality-failing combinations before the
solver runs, so on the real library the solver's own gate never decides
anything. Every test was reaching the pre-filter and stopping there. This is
exactly CLAUDE.md's "writing a test that cannot fail on the defect it names",
and it is the third instance in this repo's log.

Fixed by `TestTheSolverGateItself`, which isolates the gate on the synthetic
`SOUTH_LUNCH` pool: a combination the pre-filter must admit (`curd_b` reaches
5.0 g at its maximum count, above a 4.0 g floor) whose best-scoring assignment
falls short (2.5 g at one unit). With the gate present the solver returns
`curd_b ×2`; with it deleted, `curd_b ×1`. Both new tests were re-run against the
re-injected defect and go red.

Five further defects were injected and each turned the suite red: the protein
rung relaxing the quality floor (4 red), the floor scaled by the energy share
(9 red), a missing DIAAS reading as qualifying (15 red), the day floor taken off
the DIAAS-inflated figure instead of `base_g` (2 red), and `_widen_band`
rebuilding the target with an explicit constructor that drops the new field
(6 red). That last one is why the ladder's three target rebuilds were converted
to `dataclasses.replace`.

---

## 2026-08-02 — D2b-i, finding 25 closed

`SOUTH_BREAKFAST` gains an **optional** `curd_course` slot accepting
`curd`/`buttermilk`. `thayir_plain@curd` already fills it — no new recipe and no
new ingredient row were needed, and `curd_dahi` qualifies at DIAAS 1.09.

It follows `SOUTH_LUNCH.curd_course` in category but not in obligation: south
lunch's is required, because a South Indian lunch ends with thayir close to
obligatorily; breakfast's is optional, because idli or dosa with sambar and
chutney is a complete breakfast. That difference is the whole design of the
slot, and it is asserted rather than commented — a curd-less combination must
still enumerate.

Slot coverage and enumeration, before → after
(`PYTHONHASHSEED=0 python demo.py`):

```
south_breakfast  curd_course slot added, n=1 ['thayir_plain@curd']   1 -> 2
south_lunch      unchanged                                           3 -> 3
north_lunch      unchanged                                          24 -> 24
north_dinner     unchanged                                          12 -> 12
```

Both breakfast combinations enumerate: with and without the curd.

**A verdict reason moved, and it is worth stating.** `south_breakfast` still
declines for the reference profile, but on different numbers, because the
best-scoring combination is now the one carrying curd:

```
before  fat 24.7 > 24.6 | protein 18.4 < 23.8 | sodium 1790.4 > 1400.0
after   energy 777.1 > 707.0 | fat 33.2 > 24.6 | sodium 2273.4 > 1400.0
```

The protein violation is gone and the sodium one is worse — a katori of curd
carries its own salt line. Nothing was tuned; this is what adding a real option
to a slot does.

**Eggs are not in this.** They are the deferred non-vegetarian axis (onboarding,
filtering, schema and library all change), and nothing added here could be
served to a vegetarian profile that should not be.

*Disposition:* Finding 25 CLOSED. Pinned by
`tests/test_planner_plan.py::TestSouthBreakfastCanReachAQualitySource`, both
tests shown red against injected defects — the slot removed (KeyError, and no
curd-bearing combination), and the slot made required (no curd-less
combination).

---

## 2026-08-02 — D2a, the high-quality protein rows

Three ingredient rows (`paneer_fresh`, `tofu_firm`, `soya_chunks_dry`) and three
recipes (`paneer_masala@sabzi`, `tofu_bhurji@sabzi`,
`soya_chunk_curry@legume_curry`) were added so the quality-source rule has
something to select. Four things measured, one of them a finding.

### The reference profile now gets a plate, and it took no relaxation

This is the larger result and it was not the goal of the task. Before D2a all
four templates declined for the reference profile (see `docs/methodology.md`,
"Every template enumerates, and every template still declines"). After:

```
$ PYTHONHASHSEED=0 python demo.py plan --region north_indian --meal-slot lunch
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 4, 'dal_tadka@dal': 2, 'tofu_bhurji@sabzi': 1}
  point        : 929.8 kcal, 42.6g protein, 25.8g fat, 133.9g carb, 1209.0mg sodium

$ PYTHONHASHSEED=0 python demo.py plan --region north_indian --meal-slot dinner
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 4, 'dal_tadka@dal': 1, 'tofu_bhurji@sabzi': 1}
  point        : 756.8 kcal, 35.4g protein, 20.2g fat, 111.3g carb, 889.2mg sodium
```

Both north templates pass **with zero relaxation rungs fired** — the first
plates this library has served the reference profile without walking the ladder.
The mechanism is not protein: it is that a 150 g katori of tofu bhurji is a
low-sodium, moderate-energy way to fill the `sabzi` slot, so the solver can
reach the energy floor without the salt load that made every previous
combination breach the 1400 mg guard. The two south templates still decline, on
sodium among others; finding 22 is untouched.

### Finding 25 — no high-quality protein source can reach south_breakfast — **OPEN**

`SOUTH_BREAKFAST`'s four slots accept `tiffin`, `sambar`/`kuzhambu`,
`chutney`/`podi` and `beverage`. None of the three new components can be written
into any of them without either miscategorising the dish or inventing a category,
and the existing library has no qualifying ingredient in that template either
(`curd_dahi` reaches only `raita` and `curd`, which south_breakfast does not
accept).

So when the quality-source rule ships with a per-meal quality floor, **south
breakfast becomes structurally undeclinable-to-satisfy**: not "the library is
thin," but "the plate grammar has no slot a quality source could occupy." A
paneer/soya-stuffed dosa or a milk-based beverage would close it; both are new
recipes, and inventing one to make a rule pass is the shape of tuning this
project refuses.

*Disposition:* OPEN. Recorded before slice 4 rather than discovered by it.

### Nothing was upgraded to make the rows work

`dev_mode=False` still empties every pool — the new rows are `verified=false`
and carry the same 0.25 composition band as every other hand-entered row:

```
south_breakfast dev_mode True/False candidates: [3, 0]
south_lunch     dev_mode True/False candidates: [5, 0]
north_lunch     dev_mode True/False candidates: [8, 0]
north_dinner    dev_mode True/False candidates: [7, 0]
```

The three DIAAS figures are **authored, not sourced** — no primary source was
opened — and each was entered at the low end of its recalled range, because a
high DIAAS is what makes a row *qualify* and the cheapest authoring path must not
produce the most permissive output. The visible cost: `tofu_firm` at 0.65 sits
below the 0.75 threshold, so tofu will not qualify as a quality source. That is a
statement about this project's confidence, not about tofu.

### Unverified energy fraction: measured, not acted on

The two passing plates report 57.5% and 47.7% of plate energy as unverified,
against CLAUDE.md's ~15% shipping threshold. Both figures come from the
denominator finding 20 says is wrong in two directions at once, so they are
recorded and nothing is concluded from them. Nothing ships as validated either
way.

---

## 2026-08-02 — finding 24, raised by slice 3

### Finding 24 — a decline can name the symptom instead of the cause — **OPEN**

**What.** When the new per-meal protein ceiling excludes every energy-dense
plate, the decline reports **`energy_kcal below_floor`**. The protein ceiling is
never mentioned, because plates above it are removed before the validator sees
them, so the only thing left to report is that what survived cannot reach the
energy floor.

**Measured**, synthetic pool, day protein floor 40 g (meal ceiling 20.0 g),
energy 2400 kcal — the same target run twice, differing only in the registered
ceiling fraction:

```
ceiling 0.50 (real)  declines: energy_kcal below_floor 510.0 vs 756.0
ceiling 10.0 (off)   returns:  26.5 g protein, 800.0 kcal
```

The second run proves the first decline is caused by the protein ceiling. The
first run's message says energy.

**Why it matters.** A user told "energy is unreachable" would reasonably add an
energy-dense dish, which cannot help — every such dish is already excluded on
protein. The decline is truthful about what the validator saw and misleading
about what to do, which is a worse failure than a vague message: it points
somewhere specific and wrong. `docs/design/target_model_v2.md`'s decline-screen
work assumes the named macro is actionable.

**Scope.** Not specific to protein. Any bound that empties the feasible set
before the validator runs will surface as a violation of whatever the survivors
fail next. The pre-filter and the solver both discard silently.

**Not fixed here.** Slice 3's brief is the two bounds. A fix means the solver or
pre-filter reporting *why* it discarded, which is a different piece of work with
its own shape (`solve()` currently returns survivors and nothing about the
rejected). Pinned by
`tests/test_planner_plan.py::TestPerMealProteinCeiling::test_the_decline_names_energy_though_the_cause_is_the_protein_ceiling`,
so the current behaviour is visible and improving it is a deliberate change with
a red test attached rather than a silent one.

**Disposition.** OPEN.

---

## 2026-08-02 — finding 23, a form field with no effect

### Finding 23 — onboarding asks for diet and nothing reads it — **OPEN**

**What.** `web/onboarding.js` collects `diet`, `api/db.py` persists it on
`StoredProfile`, and as of slice 2 it changes no target value at all. Two
profiles identical but for diet receive identical energy, protein, fat, carb,
fibre and sodium targets. The wizard asks a question whose answer is stored and
then ignored.

**Why it is a finding and not just a gap.** The gap itself is deliberate and
documented (`docs/methodology.md`, "Protein quality no longer inflates the
target"): quality moved out of target-inflation and the quality-source rule that
replaces it is blocked on the ingredient set. What is not deliberate is that a
**shipped, user-facing surface still presents the question as consequential**. A
form that collects an answer it does not use is a claim to the user that it
matters. This project's entire premise is not overstating what it knows; an
inert form field is that failure on the most visible surface there is.

Distinct from the internal gap in one important way: the internal gap is fixed
by slice 4, and this is fixed by slice 4 *or* by saying so in the wizard. They
have different costs and either is defensible.

**Not fixed here.** Three options, none picked, all cheap: label the field in
the wizard as not yet affecting the plan; remove the step until slice 4; or
leave it and accept that the honest answer is "we collect this for later". The
first is the most in keeping with how the rest of this project handles a thing
it cannot yet do.

**Disposition.** OPEN. Reopens or closes with slice 4.

---

## 2026-08-02 — finding 22, raised by filling the library (T4)

### Finding 22 — a multi-dish South Indian plate cannot get under the sodium guard — **OPEN**

**What.** Now that every template enumerates, sodium blocks all four of them.
For `south_lunch` it is not a matter of a demanding profile: two of its three
combinations have a sodium **floor** above the per-plate guard with every
component at its minimum serving count, so no profile can ever be served them.

**Measured**, per-combination reach at min and max counts — the diagnosis is
built on the reach table this time, not read off a single blocking figure, which
is the mistake made in the other direction earlier the same day:

```
south_lunch
  Na  1437.0.. 3654.0   sambar_sadam + sambar + carrot_kootu + thayir_plain
  Na  1282.1.. 3344.2   sambar_sadam + sambar + carrot_poriyal + thayir_plain
  Na  1677.1.. 4134.2   sambar_sadam + sambar + carrot_kootu + carrot_poriyal + thayir_plain
south_breakfast
  Na  1006.6.. 3060.7   masala_dosa + sambar + coconut_chutney
```

Guard: 1400.0 mg (`day_budget.absurdity_fraction` 0.70 x 2000). Rows 1 and 3 are
above it before the solver picks a single unit count.

**Why it happens, and why it is not obviously a recipe defect.** A South Indian
lunch is four or five separate dishes, each independently salted at the ordinary
domestic proportion — the salt lines here run 0.33% to 0.67% of finished weight
and each carries a written reason. Four dishes at one katori each is roughly
3.3 g of salt before anyone eats a second helping. The arithmetic is not
disputed; what it means is:

- either the guard is wrong for multi-dish regional plates (it is a
  `PROJECT_DECISION` plausibility limit derived from meal-split fractions that
  are themselves project decisions, and it was never checked against a plate
  with four salt lines in it);
- or the salt proportions are wrong (but each was authored from how the dish is
  salted, and tuning them downward until plans pass is precisely the defect the
  salt notes exist to prevent);
- or a South Indian lunch genuinely carries this much sodium and the honest
  answer is to decline and say so.

**Not resolved here, deliberately.** TASKS.md forbids fixing things noticed in
passing, and each of the three readings above is a different decision with
different consequences. Lowering a salt line to clear a ceiling would be the
worst available option and is explicitly not on the table.

**Connects to finding 19/20's territory.** This is the sharpest available
illustration of `docs/design/recipe_quantity_uncertainty.md` §1: sodium is 77-99%
attributable to authored quantities, and it is now the single constraint blocking
every template in the library. The number that decides whether anything can be
served is one nobody measured.

**Disposition.** OPEN.

---

## 2026-08-02 — finding 21, and a correction to finding 19's own explanation

### Finding 21 — two constants in permanent contradiction, neither wrong alone — **OPEN**

**What.** `composition.verified_primary` (0.05) and `tolerance.energy_default`
(0.05) are the same number. The first is how wrong a verified composition value
is; the second is how far a plan's energy may sit from its target. One is checked
against the other every time a band is compared with the room a target leaves,
and they have never been compared with each other by anybody.

Neither is wrong on its own terms. `0.05` is a defensible estimate of analytical
spread; `±5%` is a defensible energy tolerance. Together they make the top
confidence state unreachable, and they do it permanently — no amount of
verification changes it, because verification changes who read the number, not
how variable the food is.

**Measured** (`docs/design/probes/t3b_propagation.py`), reference plate, process
term forced to zero so the composition term is isolated:

```
point     702.130   midpoint  691.445   point/midpoint 1.015454
h          35.106   room       34.572   h/room         1.015454
identical to 6 dp: True
```

When the two constants are equal the comparison collapses to **point versus
target midpoint**. So:

- With no process term, `confident` is granted exactly when the plate's energy
  lands at or below the centre of its own window — a fact about solver rounding
  over integer serving counts, carrying no nutritional meaning. A label decided
  that way is worse than one that never fires, because it looks like it means
  something.
- With the library's real process term (0.0689 on energy), the plate would need
  to sit 27% below centre, which is below its own energy floor. Unreachable.

**Scope, narrower than finding 19 stated.** This is energy-only.
`tolerance.fat_carb_default` is 0.15 against the same 0.05 band and has three
times the room it needs. Protein also exceeds its room on the reference plate
(h=1.46 vs 1.21) but that room is `point − floor`, a solver-slack fact about one
plate, not a constant-versus-constant contradiction.

**Same class as the salt-note defect.** A value that cannot do what its
neighbours assume it does, where every individual check passes. Nothing in the
registry can express "these two are compared against each other" — they sit four
entries apart in `citations.py` (positions 12 and 16 of 63) and no mechanism
noticed.

**Disposition.** OPEN, **deferred by decision 2026-08-02.** Options laid out in
`docs/design/tolerance_versus_band.md`; no constant moved and none chosen. The
contradiction is permanent but inert — the confidence label is not built, so
nothing reads either constant against the other today. **The label is not to be
built until this is settled**, because building it first would force the choice
from inside an implementation, which is exactly how the sodium ladder ambiguity
came to be resolved in `validator.py` rather than in a document. Reopen when the
label is scheduled, or when any user-facing surface states a "within 5% of your
energy target" claim.

Note for whoever picks: widening the tolerance to make the label move is the
perverse incentive CLAUDE.md documents, wearing a different hat, and 0.10 is
already the value rung 3 relaxes *to*, so it would make that rung a no-op.

### Correction — finding 19's explanation was wrong, its conclusion was not

Finding 19 (and `docs/design/recipe_quantity_uncertainty.md` §6) says a 5%
composition band "produces a ~7% band on plate energy". The figure is right. The
reason given — that errors accumulate across the components of a plate — is
wrong, and the wrong reason was load-bearing: it made this look like a scaling
problem that worsens with bigger plates, and it is what T3b was commissioned to
investigate ("at what component count does it stabilise?").

Composition uncertainty is applied per line and weighted by that line's share of
the macro, then summed, so a uniform `u` sums to exactly `u` at any component
count. Measured, process terms zeroed:

```
u = 0.05, 1 through 6 components: 0.0500 on every macro, every count
u = 0.25, 1 through 6 components: 0.2500 on every macro, every count
```

Flat. It never accumulates and there is no count at which it stabilises. The
extra 1.89 points on energy is the **process** term — dal_tadka's tempering oil —
which is per-recipe and does not scale with plate size either. Protein, carb and
sodium carry no process term at all, because oil has none of them.

Corrected in place in the design doc rather than silently edited. The correction
makes the problem smaller and sharper: not a scaling law, two equal numbers.

---

## 2026-08-02 — two findings from the T3 design measurement

Both found while designing `docs/design/recipe_quantity_uncertainty.md` against
the real library. Neither is caused by that design; both were already true and
were invisible because nothing had measured them. Design is not implemented, so
nothing here is fixed.

### Finding 19 — the confidence label saturates: `confident` is unreachable — **OPEN**

**What.** The plain-language confidence label specified in T3 (*confident* /
*rough* / *very rough*, derived from band half-width against the room a target
leaves) has one reachable bucket. Every plate the library can produce is already
*very rough* today, and stays *very rough* under a simulation of Task 6 in which
every ingredient is verified.

**Measured.** North Indian lunch for a 45 kg / 165 cm / 35 / female / active /
maintain profile — the nearest profile whose plate solves with **zero**
relaxation rungs, so the comparison is against the tightest bounds the system
ever applies. Plate `phulka ×1, dal_tadka ×3, onion_raita ×1`.

```
                              energy      protein     fat        carb
band half-width today          h=188.8     h=7.3      h=7.1      h=23.4
room the target leaves         room=34.6   room=1.2   room=3.2   room=14.6
                              -> very rough on all four

simulating Task 6 (composition.unverified_secondary 0.25 -> verified 0.05):
band half-width                h=48.4      h=1.5      h=2.6      (passes)
room                           room=34.6   room=1.2   room=3.2
                              -> still very rough on energy and protein
```

**Why it does not resolve itself.** Energy is the binding case and it is
structural, not a data problem: a 5% composition band on every ingredient
produces roughly a 7% band on plate energy, while `tolerance.energy_default` is
5%. `confident` cannot be reached from any composition data this project could
plausibly obtain, because the tolerance is narrower than the uncertainty of a
national food table. The two constants were registered independently and have
never been compared to each other.

**Why it matters.** The label was specified as counter-pressure against the
documented perverse incentive (wider bands are easier to satisfy). A label with
one reachable value exerts none. Separately, the counter-pressure that *does*
exist — the candidate eligibility filter, which removes a recipe whose band
exceeds 0.15 protein / 0.20 energy — is also saturated: all four north-lunch
recipes already breach both (protein 0.250 vs 0.15; energy 0.250–0.276 vs 0.20)
and survive only under `dev_mode=True`.

**Disposition.** OPEN. Recorded in the design doc §6 and §7 as a stated
limitation rather than smoothed over. Resolving it means revisiting either
`tolerance.energy_default` or `composition.verified_primary` **against each
other**, which is a target-model decision, not a recipe-data one. Do not resolve
it by widening the tolerance to make the label move — that is the perverse
incentive wearing a different hat.

### Finding 20 — the unverified-energy fraction is wrong in both directions, measured — **OPEN**

**What.** The round-4 addendum predicted that
`NutritionEstimate.unverified_energy_kcal` gets its denominator wrong in both
directions. It does, and the size is now measured rather than argued.

**Measured**, same plate: `unverified_energy_kcal = 519.0 of 702.1 = 73.9%`
against CLAUDE.md's ~15% shipping threshold.

```
dal_tadka      process_constants=['oil_uptake.vegetable_tempering']  -> whole 519 kcal charged
phulka         process_constants=[]                                  -> 0.0 charged
onion_raita    process_constants=[]                                  -> 0.0 charged
```

- **Over-charged:** `_depends_on_unverified` charges a recipe's *entire* energy
  when any process constant is unverified. dal_tadka's 519 kcal is charged
  because of a 5 g tempering-oil line.
- **Under-charged:** unverified *composition* never enters the calculation at
  all. phulka and onion_raita rest entirely on hand-entered, `verified=False`
  ingredient rows and contribute 0.0.

73.9% is therefore not the true figure. It is two large errors in opposite
directions that happen not to cancel, and the direction of the net error is
unknown.

**Disposition.** OPEN. The known over-attribution is already documented in
`core/foods/nutrition_of.py::_depends_on_unverified`, deliberately left because
correcting the smaller error alone would move the reported figure *away* from
the truth. This entry adds the measurement and the consequence: **the 15%
threshold cannot be trusted against real data until the denominator is fixed**,
and no work should be measured against it in the meantime. It does not change
what can ship — nothing can ship as validated for the independent reason that
every registered constant is `verified=False`.

---

## 2026-08-02 — finding 18 CLOSED, and the reproducibility pattern behind it

### Finding 18 — CLOSED

`CandidatePool.for_slot` now iterates `sorted(slot.accepted_categories)` and
returns candidates sorted by `component.id`. Sorted by **id, not by category
name**: the id is the identity of the thing actually offered, so the order
survives a category rename or a slot accepting more categories, and it is a
total order because `for_slot` already deduplicates on that key.

**Before fixing, the spread was measured.** `demo.py plan` for the north_lunch
reference profile, 12 hash seeds:

- **2 distinct enumeration orderings** (5 seeds gave rajma-first, 7 gave
  dal-first).
- **Verdict identical in all 12**: `passed: False`,
  `above_ceiling sodium_mg actual=1649.3 bound=1400.0`.

**The winner does not change with seed.** This was the serious question and the
answer is no. Checked on a target the real library *can* satisfy, and on
`tests/factories.py`'s 144-combination synthetic library where ties are far more
likely, across 12 seeds each:

```
REAL  plate={'phulka@roti':3,'rajma_chawal@combo_rice_legume':1,'onion_raita@raita':1}
      score=0.301389  top4=[0.301389, 0.372667, 0.9585, 1.039]
SYNTH n=144  plate={'rice_b@mixed_rice':2,'gravy_b@rasam':2,'veg_a@poriyal':2,
                    'veg_c@poriyal':2,'curd_b@buttermilk':1,'crisp_b@pickle':2}
      score=0.121429  top4=[0.121429, 0.142857, 0.214286, 0.271429]
```

Identical at every seed. **No tie was ever reached** — top-two scores differ by
24% (real) and 18% (synthetic) — so `solver.py`'s stable sort never had to break
one. The tie-break path is **latent, not realised**: published results did not
depend on a hash seed. Finding 18 is a reproducibility defect, not a correctness
one.

**After the fix**: one ordering across all 12 seeds; plate, score, verdict and
violation all unchanged. Note what that last clause is and is not — *nothing
changed* is a statement about **this library at this size**. With four
combinations and scores 24% apart there was no tie to resolve. It is not a
guarantee for a larger library, where the stable sort's input order is exactly
which plate a user is served.

**Other set-iteration sites, checked rather than assumed.** `candidates.py:110`
was the only one in the ordering-relevant path. Examined and deliberately not
changed:

- `core/foods/recipe_loader.py:218` and `ifct_loader.py:270` already
  `sorted(...)` their globs, so file order was never the problem.
- `combinations.py` uses `itertools.combinations` / `itertools.product`, both
  order-preserving given deterministic input — so the one fix propagates.
- `candidates.py` `recipe_allergens` returns a frozenset, but it is only ever
  membership-tested, never iterated for order.
- `len({f.recipe_id for f in flagged})` builds a set for a count only.
- **`solver.py:214`, `solved.sort(key=lambda p: p.score)` — left alone.**
  Python's sort is stable, so with deterministic input the winner is now
  deterministic; the defect is fully closed by the one fix. Adding a secondary
  sort key would additionally make the winner independent of *enumeration* order,
  which is a stronger and different property — a decision about tie-break
  semantics, not a determinism fix, and not made here.

**Disposition: CLOSED.** `tests/test_planner_determinism.py` (new).

### The pattern — second instance, and it should be named as one

This is the **second time a reproducibility rule in this project has been
satisfied literally while missing its purpose.**

1. **Task 9 (2026-07-31, finding 11).** CLAUDE.md requires a pasted command
   transcript backing any status claim. Every transcript in this log had one.
   None could be re-run, because the command lived in an untracked scratch
   script. The rule was met; its purpose — that anyone can check the claim —
   was not.
2. **Finding 18 (today).** `demo.py` was built to close that hole, and slice
   1a's acceptance criterion asserted byte-identical output against a captured
   baseline. Both were satisfied. Neither could be *reliably* true while
   enumeration order was seed-dependent: 1a's byte-diff passed because the
   baseline and the comparison run happened to draw the same ordering. The
   check was real, and it was a coin flip.

The shape is the same both times: **a reproducibility check that reproduces
itself.** A transcript that proves a transcript exists; a byte-diff run twice in
one shell against one seed. Neither compared across the axis the property was
actually about — a different machine, a different process.

What follows from it, stated as a rule rather than an intention: **a
determinism claim has to be checked across the thing it claims independence
from.** `tests/test_planner_determinism.py` does that by spawning subprocesses
under different `PYTHONHASHSEED` values, because nothing checkable inside one
process can.

That is not a hypothetical concern — it was demonstrated while writing the
tests. The first draft's three fast in-process tests **all passed against the
defect they were written to catch**, for two separate reasons: one picked
`north_lunch.grain_base`, which declares two categories but has candidates in
only one, so permuting it is a no-op; and the sortedness check compares
frozenset order against sorted order, which coincide often enough to pass under
many seeds. Both were found by injecting the defect and watching the tests not
fail. Under the corrected tests the defect fails 3 of 4 at every seed tried
(0, 1, 5), and the remaining one is documented in its own body as a statement of
contract rather than a detector.

### Does finding 11's closure claim now hold?

**Yes, and it did not before today.** The 2026-07-31 entry closed finding 11 on
the claim that the evidence chain is reproducible. As of that entry the
*substance* reproduced — verdicts, bounds and violations were stable across
every seed measured — but the artifact did not: two people running the
documented command got textually different transcripts, and a diff between them
showed changes that were not changes. With `for_slot` ordered, `demo.py` output
is byte-stable across 12 hash seeds, and the claim holds as written.

---

## 2026-08-02 — sodium became a day budget; two findings raised on the way

Build notes for target-model slices 1a and 1b, plus two things measured while
building them that neither the design doc nor this log had right.

### Finding 18 — combination enumeration order is not deterministic — **CLOSED 2026-08-02**, see the entry above

`TemplateSlot.accepted_categories` is a `frozenset[str]`, and
`core/planner/candidates.py:110` iterates it directly. Python randomises string
hashes per process, so **candidate order — and therefore the order
`enumerate_combinations` returns combinations in — varies between runs of
identical code on the same machine.**

Measured. Five runs of `demo.py plan`, hashing the enumeration block only, on
the unmodified pre-slice-1a code:

```
09071a2e79c2b59a8d1e1a4c0fe257da     f737693bb608d5fdd2e891852e804f5e
09071a2e79c2b59a8d1e1a4c0fe257da     09071a2e79c2b59a8d1e1a4c0fe257da
f737693bb608d5fdd2e891852e804f5e
```

Two distinct orderings. With `PYTHONHASHSEED=0` fixed, three runs produce one
ordering, which identifies hash randomisation as the cause. The two orderings
differ in whether `dal_tadka` or `rajma_chawal` is listed first for
`north_lunch.legume_curry`, whose `accepted_categories` is
`frozenset({"legume_curry", "dal", "combo_rice_legume"})`.

**Why this matters more than a cosmetic listing order.** `demo.py` exists so
that the transcripts in this file can be regenerated by anyone, and the
2026-07-31 entry closed finding 11 on exactly that basis. The verdict, the
bounds and the violations are stable — what varies is the enumeration listing —
so the *substance* of every transcript here reproduces. But two people running
the identical command get textually different transcripts, and a diff between
them shows changes that are not changes. Byte-reproducibility was the claim, and
it does not hold.

**The second-order risk, not observed today but structural.** `solve` returns
plans ordered by score, and ties are broken by input order. With today's
four-combination library no tie arises, so the plate served is stable. With a
richer library, *which plate a user is served* could depend on the hash seed of
the process that answered their request.

**Disposition: was OPEN when written; CLOSED the same day in its own commit —
see the 2026-08-02 entry above for the measured spread, the winner-stability
check, and the pattern this is the second instance of.** Deliberately not fixed
in the slice that found it: changing enumeration order changes `demo.py` output
and can change which plate the solver picks among equals, and that must not ride
inside a commit whose acceptance criterion is that no behaviour moved. Found
while diffing slice 1a's output against its baseline; not caused by it.

### Correction — the north_lunch decline was never a sodium wall

The 2026-07-31 entry, and `docs/design/target_model_v2.md` §2–3, both read the
`sodium_mg actual=1649.3` decline as sodium being unreachably high in this
library. It is not. Measured per-combination sodium reach (min..max over legal
unit counts):

```
   856.6 ..  1952.8   ['phulka@roti', 'rajma_chawal@combo_rice_legume']
  1111.8 ..  2463.2   [... + 'onion_raita@raita']
   379.6 ..  1318.5   ['phulka@roti', 'dal_tadka@dal']
   634.8 ..  1828.9   [... + 'onion_raita@raita']
```

The library can build a **379.6 mg** north lunch. 1649.3 mg is the sodium of the
plate that best fits *energy and protein*: `_blocking_violations` found every
bound individually reachable and fell through to its "no single assignment meets
them together" branch, which reports the best-scoring plate's own misses. So the
decline is a **joint energy-vs-sodium infeasibility** — the low-sodium plates
cannot reach the 809.9 kcal floor — not a sodium ceiling the library cannot get
under. Reading it as the latter is what made "does the decline survive?" look
like the important question about the day-budget design. It was not.

### Correction — the design doc's absurdity guard did not survive its own ladder

`docs/design/target_model_v2.md` §2 and §3 state that the 1649.3 mg plate "still
fails" the proposed 1400 mg guard, "which is the behaviour this design wants."
That compares the plate against the **unrelaxed** guard. Rung 1 widens the
sodium ceiling by `tolerance.sodium_relaxed_fraction` (0.50), so the guard
became 2100 mg and the plate passed:

```
--- sodium ceiling 1400 (0.70 x 2000), guard widenable
    passed: True | rungs: all four | final sodium ceiling: 2100.0
    plate: {'phulka@roti': 3, 'dal_tadka@dal': 3, 'onion_raita@raita': 2}
    point: 984.1 kcal, 40.4g pro, 1649.3mg Na
```

Generally: a widenable guard permits one plate to carry `fraction x 1.5` of a
day. At 0.70 that is **105% of a whole day's sodium on a single plate** — the
outcome the guard was introduced to prevent. Fixed in slice 1b by registering
the guard as a `NutritionTarget.hard_ceiling`, which no rung may widen past.

**Disposition: both corrections applied to `docs/design/target_model_v2.md` in
the same commit as slice 1b.**

---

## 2026-07-31 — the evidence chain was not reproducible (finding 11, enlarged and CLOSED)

Not an audit pass. Recorded because the defect is about this log's own
trustworthiness, which makes it the one thing that could not be left to a
commit message.

**What was wrong.** Finding 11 below recorded that `demo.py` was referenced by
CLAUDE.md's Commands block and by `docs/methodology.md` and did not exist. That
was the visible symptom of something larger: *every* result the recent work
rests on — the library's first end-to-end plan, the sodium decline, the
rung-by-rung ladder table, the per-line salt provenance breakdown, the four
ladder-target rows quoted in the 4b write-up — was produced by a scratch script
in a session working directory. `git ls-files` returned nothing for it. None of
it could be reproduced by anyone, on any other machine, or by us the following
day.

The process rule in CLAUDE.md requires a pasted command transcript in the same
artifact as any claim about the repo's state. Every transcript quoted here
satisfied that rule literally and none of them satisfied its purpose, because
the command could not be re-run. That gap is worse than a missing file: it means
this log recorded conclusions whose evidence had already evaporated.

**What was built.** `demo.py`, tracked, at the repo root, with `library` / `plan`
/ `all` subcommands and profile and template as flags rather than edits. It
loads the real `data/` library, reports counts/rejections/warnings, prints slot
coverage for all four templates, enumerates a named template, and runs
`plan_meal` for a named profile printing the plan-or-decline, rungs applied,
skipped-locked steps, violations with actuals and bounds, and the disclosure.

Two properties are deliberate:

* **It prints the unrelaxed target and the target the ladder stopped on, each
  labelled.** The scratch script printed only `LadderOutcome.target_used` under
  a bare "meal target" heading, and that is what miscalibrated the Task 4b
  prediction — the fully-relaxed bounds were read as the bounds the plate was
  first asked to meet, so every rung looked like it still had room to give. The
  prediction was wrong for that reason and not for an arithmetic one.
* **Output is ASCII only and carries `STATUS: DEV_MODE` at both ends**, read
  from `DerivedTarget.status` rather than hard-coded. Transcripts get pasted
  into commit messages and markdown from Windows terminals; a stray em-dash
  arrives as mojibake and corrupts the evidence it was meant to preserve.

`tests/test_demo.py` (13 tests) is a smoke suite only: it asserts the script
runs, that each subcommand works, that both targets are printed, and that the
status banner appears at both ends. It asserts no nutrition value — those are
pinned in the existing suite, where a failure names the quantity.

**Reproduction check.** The reference run (`python demo.py`, north_lunch,
70 kg / 175 cm / 28 / male / moderate / maintain / vegetarian) reproduces the
Task 4b result as amended by `2c4f30f` **exactly**: 4 recipes enumerated to 4
combinations, all four rungs applied, `skipped_locked=()`, one violation —
`above_ceiling sodium_mg actual=1649.3 bound=1050.0` — and the same disclosure
string. Every ladder-target row matches. No discrepancy.

**Severity:** HIGH in kind. Nothing computed was wrong, and the reproduction
confirms that. But for a project whose entire claim is evidentiary discipline,
an unreproducible evidence chain is a failure of the thesis rather than of an
implementation, and it survived four rounds of adversarial review because every
individual transcript looked correct.

**Disposition: FIXED.** Finding 11 CLOSED. From this entry forward, a
transcript in this file that cannot be regenerated by a documented `demo.py`
invocation should be treated as not having happened.

---

## 2026-07-31 — three open questions raised by the first end-to-end plate

Not an independent audit pass. All three were observed while adding
`data/recipes/phulka.yaml` (the library's first `roti`) and running the
north_lunch pipeline end to end for the first time. None is resolved here:
each is recorded as an open question with the evidence attached, per the
audit-workflow section's rule that a finding not written here did not happen.

### Finding 15 — a combo component filled a slot alongside the base it already contains — OPEN

`core/foods/templates.py` (`NORTH_LUNCH`, `SOUTH_LUNCH`),
`core/planner/combinations.py`

The north_lunch enumeration produced exactly one combination:

```
combinations surviving the O(1) feasibility pre-filter: 1
    ['phulka@roti', 'rajma_chawal@combo_rice_legume']
```

That is a roti served alongside a rice-and-legume dish — two grain bases on
one plate. It is why carb came in far over its ceiling for the 70 kg profile:

```
above_ceiling carb_g      actual=222.8  bound=149.4
above_ceiling energy_kcal actual=1240.2 bound=989.9
```

The decline is arithmetically correct. The combination should never have been
enumerated: it is not a plate anyone would serve, and the numbers it produces
are the numbers of a plate nobody would serve.

Nothing in the slot semantics prevented it. `TemplateSlot` declares
`accepted_categories` — what a component may *be* — and has no way to declare
what a filling component may not also *provide*. `rajma_chawal`'s category is
`combo_rice_legume`, which `NORTH_LUNCH.legume_curry` accepts; that the dish
also contains 183 g of `rice_cooked`, i.e. the thing `grain_base` was filled
with separately, is invisible to the enumerator.

**The open question, unanswered here:** should a slot be able to declare what
a filling component may **not** also provide (a "provides" / "excludes"
relation between slots), or should combo-type components instead be excluded
from templates that fill their constituents in separate slots? Both have
costs — the first adds a second axis to a grammar whose whole point is being
per-meal and readable; the second means `rajma_chawal` becomes unplannable in
the only template that currently accepts it, which would return north_lunch to
zero combinations. No decision is taken in this entry and none is implemented.

**It generalises — checked, not assumed.** The same shape exists in
`SOUTH_LUNCH` and is reachable with today's data plus one recipe:
`rice_base` accepts `mixed_rice`, and `sambar_sadam` (category `mixed_rice`)
is rice *with sambar already in it*, while `gravy` is a separate required slot
accepting `sambar`/`kuzhambu`/`rasam`. The instant a `sambar` recipe is
authored, south_lunch will enumerate sambar sadam + sambar. This is not a
north_lunch quirk; it is a property of every template that accepts a composed
category in one slot and one of that composition's constituents in another.
`SOUTH_BREAKFAST` and `NORTH_DINNER` accept no composed category in any slot
and are not exposed today.

**Severity:** MEDIUM. It does not produce a wrong number — the arithmetic on
the enumerated plate is right, and the validator correctly declined it. It
produces a *correct number about the wrong plate*, and in the current library
it is the only combination there is, so the whole template's behaviour rests
on it.

**Disposition: OPEN.** Not fixed in this task by instruction; no
slot/template semantics were changed.

### Finding 16 — the interval spans the bounds the point estimate passed against — OPEN

`core/foods/nutrition_of.py`, CLAUDE.md ("Uncertainty"),
findings 3, 4 and 6 above.

The first plan the real library has ever produced end to end (loose target,
2000 kcal/day, 10 g protein floor):

```
passed: True   relaxation: ()
unit_counts: {'phulka@roti': 2, 'rajma_chawal@combo_rice_legume': 1}
point   : 669.5 kcal
interval: 495.1 - 844.0 kcal
```

±26% around the point estimate. The meal's energy band under the loose target
is narrower than the interval on the estimate that cleared it: the plan passes
on a point estimate whose own honest error bar spans well outside the bounds
being gated against.

This is **not a new finding** — it is the first observation on real data of
the incentive problem CLAUDE.md's "Uncertainty" section already states in the
abstract ("a plan with worse underlying data passes more easily than one with
better data"), and it is the reason that section disqualifies interval-overlap
gating outright. Recorded here as evidence, cross-referencing rather than
duplicating: findings 3 (double-counted bands producing ±45%), 4 (a zero point
estimate printing with no band) and 6 (the low-end clamp biasing the reported
fraction narrow) are the mechanisms; this is what they look like on a plate.

The gate itself behaved as designed — it gated on the point estimate only, and
did not consult the interval. Nothing here suggests changing that. What it
documents is that "passed" and "±26%" can be true of the same plate at the
same time, which is a fact the user-facing display has to carry.

**Severity:** LOW as a defect (nothing is wrong), MEDIUM as a disclosure
question. The plate is `dev_mode` regardless: 471.7 kcal of its 669.5 kcal —
**70.5%** — comes from `verified=False` process constants, against the ~15%
shipping threshold.

**Disposition: OPEN**, as a question about display and about the existing
open interval findings, not as a new defect in the gate.

### Finding 17 — the fat floor was missed by 0.1 g, on precisely the known data gap — OPEN

`data/raw/ifct/fixture_ingredients.csv` (`sunflower_oil`, `gingelly_oil`),
`docs/methodology.md`

For the 70 kg profile, three of four violations missed their bound by a wide
margin. The fourth did not:

```
below_floor fat_g actual=20.5 bound=20.6
```

0.1 g, or 0.5% of the floor. A phulka is essentially fat-free (0.5 g per
roti, all of it from the atta), so the plate's entire fat load is
`rajma_chawal`'s 8 g tempering-oil line — and oils are the one category IFCT
2017 structurally cannot supply. Both oil rows in the fixture carry the
provenance note that IFCT's tabulated rows for oils report `energy_kcal=0`
and all micronutrients zero alongside `fatce=100`, i.e. no full nutrient
panel; both remain hand-entered approximations. The single constant governing
how much of that oil is retained, `oil_uptake.vegetable_tempering`, is a
`verified=False` project estimate with no matching primary source.

So the one macro that came down to a coin-flip is the one macro whose value
rests entirely on the library's least-supportable data. This is a
coincidence, not a causal finding — a 0.1 g miss on a 20.6 g floor is well
inside any reasonable band on that oil line, which is the point: the verdict
on this macro is not distinguishable from noise, and it happens to be the
verdict that decided a bound.

**Worth watching, explicitly:** whether this near-miss survives the task-4b
recipes (`dal_tadka`, `onion_raita`), both of which add fat — the dal
through its own tempering line, the raita through curd. If the fat floor
clears comfortably once they are in, the observation stands as a warning about
thin-library behaviour rather than a live problem. If it stays marginal, the
oil rows move up the verification queue.

**Severity:** LOW today. Recorded because a bound decided inside the noise
floor of the underlying data is the shape of thing this log exists to notice
before it decides something that matters.

**Disposition: OPEN.** No constant moved, no evidence grade changed.

### Cross-reference — `process_uncertainty` without `process_constants`, against finding 2

`tests/test_recipes.py::TestRecipeLoaderRules::
test_declared_uncertainty_is_backed_by_registered_constants` is **red as of
this entry, deliberately left unfixed.** `phulka` has a non-empty
`process_uncertainty` (0.2 bands on `fibre_g`/`iron_mg`/`calcium_mg`/`b12_ug`,
from `process_uncertainty_unassessed`) and an empty `process_constants`,
because it declares no `process:` line on any ingredient — a phulka is
dry-griddled, so no oil-uptake constant applies. The test asserts
`if recipe.process_uncertainty: assert recipe.process_constants`.

This meets **finding 2** at the same seam from the opposite direction.
Finding 2 is that a recipe with no `process:` lines reads as fully
process-*certain* — uncertainty wrongly absent. This is a recipe with no
`process:` lines whose uncertainty is correctly *present*, via the
`unassessed` path, and a check that looks for it in the wrong field. Both are
about what the absence of a `process:` line is allowed to mean. The
`unassessed` band *is* backed by a registered constant
(`process.unassessed_uncertainty`), just not one attached to any line, which
`process_constants` is derived from.

`phulka` is the first recipe in the library to use the unassessed path without
also using the per-line path, which is why the assumption held until now.

**Disposition: OPEN**, deliberately, and the test stays red. Fixing it means
deciding what finding 2 decides, and that decision is not taken here.

---

## 2026-07-22 — Phase 3 build notes: two self-caught defects

Not an independent audit pass. Both were caught while building
`core/planner/validator.py`, and both are recorded because they are instances
of failure modes CLAUDE.md names by name.

### Finding 13 — a hand-computed test expectation was wrong, and its own test agreed with it

`tests/factories.SOUTH_LUNCH_MAX_PROTEIN_G` was `33.6 g`, and
`tests/test_planner_solver.py::TestThinFeasibleSet::
test_the_synthetic_pool_cannot_reach_90g_protein_at_all` asserted exactly that
value against a comment restating the same derivation. The derivation summed
*both* crisp candidates (`crisp_a` 1.0 + `crisp_b` 0.3, doubled), but the
`crisp` slot has `max_selections=1`, so no combination ever contains two. The
true maximum is `33.0 g`.

The test passed throughout Phase 2 because the assertion and the comment were
the same mistake written twice. CLAUDE.md's testing convention ("expected
values are hand-computed, with the arithmetic shown in a comment") is
necessary but, as this shows, not sufficient: a hand-computed value is only
worth what its derivation is worth, and a comment cannot check itself.

**Severity:** LOW in consequence — the conclusion the test drew (33.6 < 90, so
the audit's thin case really is infeasible) is still true at 33.0, and nothing
in `core/` read the constant. MEDIUM in kind: it is precisely the
"code and docs agree with each other and neither survives a concrete input"
shape this log exists to catch, committed in a test rather than in a doc.

**Disposition: FIXED.** Value corrected to 33.0 with the per-slot arithmetic
shown, and a second test
(`test_the_hand_derived_max_matches_what_enumeration_actually_reaches`) now
cross-checks the hand-derived figure against what `enumerate_combinations` +
`macro_bounds` actually reach, so the arithmetic and the code must agree with
*each other*, not only with themselves. This is a cross-check, not a snapshot:
the hand-derived value is still stated and readable in `tests/factories.py`.

### Finding 14 — the relaxation ladder searched a set pre-filtered against the un-relaxed target

First implementation of `plan_within_ladder` took an already-pre-filtered
combination set and re-solved it after each rung. The O(1) feasibility
pre-filter is target-dependent, so the set handed in had already been pruned
to fit the *tight* target: every rung then widened a target and searched a
population selected to fit the target it was widening. Plans the ladder should
have found were unreachable, and the failure is silent — the system declines,
with a decline message that correctly names a constraint, and nothing
indicates the search space was wrong.

Measured on the Phase 2 synthetic pool: 17 of 144 combinations survive the
pre-filter under a 500 mg sodium ceiling; 141 survive once rung 1 drops it.
The plan the corrected ladder returns is *not* in the 17.

**Severity:** HIGH. It defeats the ladder for exactly the profiles the ladder
exists for, and presents as a legitimate decline.

**Disposition: FIXED.** `plan_within_ladder` now runs `feasible_combinations`
itself, once per rung, against that rung's target, and its docstring states
that callers must pass the enumerated set rather than a pre-filtered one.
Pinned by `tests/test_planner_validator.py::TestLadderFires::
test_relaxation_recovers_combinations_the_tight_pre_filter_discarded`, which
asserts the chosen plan is one the tight pre-filter discarded — a test that
fails if the pre-filter is ever hoisted back out.

---

## 2026-07-21 — Phase 2 build note: finding 1 closed, finding 2 status clarified

Not an independent audit pass (no fresh read-only subagent run against this
diff yet — that is still open work). Recorded here because building
`core/planner/candidates.py` directly resolves one open finding and bears on
another, and CLAUDE.md's audit-workflow section says a finding's disposition
belongs in this file, not only in a commit message.

**Finding 1 ("the protein eligibility ceiling is applied to a quantity that
is 0.0 for every recipe") — CLOSED.** `core/planner/candidates.py` gates on
`core.foods.nutrition_of.NutritionEstimate.uncertainty_fraction` — composition
uncertainty (mandatory per ingredient, never zero) plus process uncertainty —
computed via `nutrition_of_components` for each candidate recipe, not on
`Recipe.process_uncertainty` alone. `tests/test_planner_candidates.py::
TestUncertaintyEligibility::test_every_real_recipe_is_excluded_in_validated_mode`
asserts, per real recipe, that the combined protein fraction is pinned at
0.25 against a 0.15 ceiling (matching the figure already pinned in
`tests/test_nutrition_of.py::TestEligibilityConsequence`) and that all three
are excluded with `dev_mode=False`. CLAUDE.md's "Uncertainty" section wording
is corrected to say "combined composition-plus-process uncertainty" rather
than "process uncertainty."

`dev_mode` (named as a requirement in `docs/methodology.md`'s "dev_mode versus
validated" section, not previously implemented anywhere) is now a real
parameter on `build_candidate_pool`: `False` (default) excludes a recipe that
misses a ceiling; `True` keeps it and records the miss in
`CandidatePool.flagged` rather than silently treating it as validated. The
Phase 2 property test (200 random moderate profiles) runs against a synthetic,
tightly-verified fixture (`tests/factories.py`, not real recipe data) that
clears both ceilings even with `dev_mode=False` — it does not depend on
suspending the ceiling, and a separate test confirms the real library still
clears nothing.

**Finding 2 ("a recipe with no `process:` lines reads as fully
process-certain") — still OPEN, scope note added.** This finding is about
`core/foods/recipe_loader.py`'s `_derive_process_uncertainty` and
`core/foods/nutrition_of.py`'s `_depends_on_unverified`, neither of which
`core/planner` touches. It is not silently inherited by the eligibility filter
today: `Ingredient.composition_uncertainty` is mandatory per macro (construction
fails on an unpopulated entry — see `core/foods/models.py`), so the *combined*
figure `candidates.py` gates on can never be zero for a recipe built from
today's fixture, independent of whether that recipe declares any process at
all. The exposure finding 2 actually describes — a *verified*, tight-composition
ingredient combined with an undeclared process on a griddled or fried dish —
does not exist in the current fixture (every ingredient but `water` is
unverified) and so cannot presently slip through `candidates.py` either. It
would as soon as that combination exists. Closing finding 2 before that point
is still the right order of work; it just is not blocking today's `dev_mode`
eligibility behaviour the way finding 1 was.

---

## 2026-07-21 — audit of `7d9bc41` and `26e5ff4`

**Scope.** Composition uncertainty (`7d9bc41`) and the derive-process-uncertainty
/ pin-guards / restore-build-status pass (`26e5ff4`). Diff audited:
`git diff 116c765..HEAD`.

**Auditor.** Read-only subagent (Read/Grep/Glob + read-only Bash), no write
access to `core/`. `.claude/agents/auditor.md` and `.claude/commands/grill.md`
described in CLAUDE.md do not exist yet; this ran as an ad-hoc equivalent under
the same permission boundary. Building the persistent definitions is open work.

**Suite at time of audit:** `python -m pytest tests/ -q` -> `124 passed in 0.17s`.
**Suite after the fixes below:** `python -m pytest tests/ -q` -> `124 passed in 0.19s`.

**Summary:** 12 findings — 2 HIGH, 1 MEDIUM/HIGH, 3 MEDIUM, 6 LOW/doc-drift.
Six fixed in the follow-up commit (all of them statements that were simply
false); six left OPEN because they need a design decision rather than a
correction. Findings 1 and 2 are both in the permissive direction — they would
let the planner ship plans the project says it cannot — and should be closed
before `core/planner` starts.

### Cleared — checked and found sound

Recorded because knowing what was tested and cleared is as useful as the
findings, and because a later reader should not re-derive these.

- **`_composition_band` weighting is genuinely per-ingredient**, not an artifact
  of every row currently carrying 0.25. Flipping only `rajma_cooked` to verified
  moved `rajma_chawal`'s protein band 0.25 -> 0.12564, matching
  `(9.570/15.391)*0.05 + (5.821/15.391)*0.25` exactly.
- **Same ingredient on two lines with different process keys** (masala dosa's two
  `gingelly_oil` lines) derives correctly: 6.188 + 2.652 = 8.84 kcal.
- **Derived uncertainty cannot currently exceed 1.0** — the numerator sums a
  subset of the denominator's lines, all non-negative, so it is bounded by the
  largest constant uncertainty (0.20 today). No guard exists, but it is not
  reachable. See finding 6 for the related clamp issue.
- **The macro-share table in `docs/methodology.md` is arithmetically correct.**
  Independently recomputed: `rice_cooked` 39.34%/28.49%, `rajma_cooked`
  14.53%/34.71%, top eight = 93.04% energy / 91.90% protein.
- **`test_mutating_a_constant_moves_every_recipe_that_depends_on_it` is a real
  perturbation test**, not a self-consistency check.

### Findings

**1. The protein eligibility ceiling is applied to a quantity that is 0.0 for
every recipe — HIGH**
`core/foods/models.py:291-293`, `core/nutrition/citations.py` (`eligibility.max_protein_uncertainty`),
CLAUDE.md:136-137, `docs/methodology.md`

CLAUDE.md says the filter excludes "a recipe whose **process uncertainty** on a
given macro exceeds a stated ceiling", and `Recipe.process_uncertainty`'s
docstring says it is "Read later by the candidate eligibility filter". Measured
process protein uncertainty:

```
masala_dosa  0.0
rajma_chawal 0.0
sambar_sadam 0.0
```

Oil carries no protein, so no derived process term ever touches that macro. A
`core/planner` author implementing exactly what the docs instruct gets
`0.0 < 0.15` -> **every recipe eligible**, `dev_mode` never needed, all 124 tests
still green. Nothing in `core/` reads `eligibility.max_protein_uncertainty` —
only the tests. The `TestEligibilityConsequence` guards assert on
`NutritionEstimate.uncertainty_fraction`, a *different* quantity from the one the
ceiling is documented to gate.

This is the specific edit that makes the library "pass" with no test failing,
and it is the edit the docs tell you to make. `docs/methodology.md`'s "the
candidate pool is empty for every profile" is not enforced by anything.

*Disposition:* OPEN. Needs a decision: the ceiling must gate the **combined**
band (composition + process), and CLAUDE.md's wording must change to say so.

**2. A recipe with no `process:` lines reads as fully process-certain and 0%
unverified — HIGH**
`core/foods/recipe_loader.py` (`_derive_process_uncertainty`),
`core/foods/nutrition_of.py` (`_depends_on_unverified`)

A plain idli (rice + urad + water + salt, no oil line, no
`process_uncertainty_unassessed`) loads with all nine macros at 0.0 and
`unverified_energy_fraction() == 0.0` — against the 15% shipping threshold.

The loader docstring claims "the author cannot obtain [zero] by leaving the work
undone." The author obtains it precisely by leaving the work undone: omit
`process:` from every line. Nothing checks that a griddled, fried or boiled dish
declares any process at all. `Recipe.__post_init__`'s mandatory-per-macro rule is
satisfied by nine computed zeros.

This is the **permissive** direction of the attribution error, the opposite of
the over-attribution recorded as methodology limitation 8.

*Disposition:* OPEN. This is the same class as the defect `26e5ff4` fixed and
was introduced by the same change.

**3. `unassessed` + composition double-counts on cooked-basis rows, producing
±45% — MEDIUM/HIGH**
`core/foods/nutrition_of.py` (`_interval_for_recipe`), `core/nutrition/citations.py`

All three recipes display iron and calcium at **±45%** (0.25 composition + 0.20
unassessed process). `rajma_chawal` renders iron as `~3.2 mg (+/-45%)`, of which
87.8% comes from `rice_cooked` and `rajma_cooked` — **cooked-basis composition
records**.

The composition constant's registered `phenomenon` is dispersion in a value "as
eaten"; the unassessed constant's is change "during domestic cooking". On a
cooked-basis row those two phenomena describe the same span, and the code adds
them. Roughly half the widest band in the product is charged twice for a step the
recipe does not perform.

This is a `phenomenon`-mismatch of the exact kind CLAUDE.md's citation section
exists to catch — caught between two constants rather than between a constant and
a paper. Neither the docs nor any test mentions 0.45.

*Disposition:* OPEN.

**4. A macro with a zero point estimate displays with no band, including
declared-unassessed ones — MEDIUM**
`core/foods/nutrition_of.py` (`uncertainty_fraction`, `_interval_for_recipe`)

Masala dosa declares `b12_ug` unassessed (0.20 process band) yet renders
`"0 ug"` — no band, no qualifier. Both bands are multiplicative, so zero is an
absorbing state. The author's explicit "we have not assessed this" is
indistinguishable from a measured exact zero, on a vegan plan, for the one
nutrient where the distinction matters most.

Since composition uncertainty now floors everything else at 0.25, the *only*
figures that print without a band are exactly the ones the system knows nothing
about.

Same mechanism: a zero-protein component (chutney, rasam) reports
`uncertainty_fraction("protein_g") == 0.0` and clears the 0.15 ceiling.

*Disposition:* OPEN.

**5. No `max()` guard — declaring a macro unassessed can NARROW the band —
MEDIUM**
`core/foods/recipe_loader.py` (`_derive_process_uncertainty`),
`core/nutrition/citations.py` (`process.unassessed_uncertainty` note)

The constant's note claims it is "deliberately worse than any measured process
constant currently in this registry." It is not — `oil_uptake.dosa_griddled` is
also 0.20, i.e. equal, not worse. And there is no `max(derived, unassessed_band)`.
With `oil_uptake.vegetable_tempering` widened to 0.35, doing the work derives
0.35 while declaring the macro unassessed yields 0.20. Declaring unassessed
becomes the cheaper path to the tidier number — the exact inversion the constant
was registered to prevent.

`test_an_unassessed_macro_takes_the_registered_wide_band` does not test this
claim: it compares 0.20 against a dish-level derived *fraction* of 0.0395, not
against any constant.

*Disposition:* note text corrected 2026-07-21 (the "worse than any measured
constant" claim was false as written). The missing `max()` guard is OPEN.

**6. The low-end clamp silently understates the reported uncertainty fraction —
MEDIUM (latent)**
`core/foods/nutrition_of.py` (`_interval_for_recipe`, `uncertainty_fraction`)

`lows.append(max(0.0, v - half_width))`, but `uncertainty_fraction` recovers the
band as `(high - low) / (2p)`. Point 10 with half-width 12 clamps low to 0, high
22, reported fraction 1.1 against a true 1.2. The comment two lines above says "a
band wider than the point estimate is a legitimate statement about very poor
data" — the code makes that statement unreportable, and biases it narrow.

Not reachable today (max total band 0.45); reachable as soon as a wider constant
lands, and it fails in the false-precision direction.

*Disposition:* OPEN.

**7. CLAUDE.md's build-status test count is contradicted by the commit that
wrote it — MEDIUM**
`CLAUDE.md` build-status table

The table said "114 tests pass … at commit `7d9bc41`" and "(110 -> 114 tests)".
The commit that wrote those lines, `26e5ff4`, says "110 -> 124 tests" and
"124 passed in 0.17s". HEAD gives 124.

A status line whose transcript *in the same commit* refutes it — a direct
violation of CLAUDE.md's own "no unverified claims about the project's own
state". Cause: the table was written mid-session at 114 and not re-derived after
later tests landed in the same commit.

*Disposition:* FIXED 2026-07-21.

**8. `docs/methodology.md` still makes the "every ingredient row" claim the same
commit says it corrected — MEDIUM**

> "Consequently every ingredient row carries the 0.25 unverified-composition band"

`water` carries 0.05. `26e5ff4`'s message claims "Both documents corrected";
`data/raw/ifct/README.md` was, `docs/methodology.md` was not — and its own
limitation 1 correctly says "22 of 23", so the file contradicts itself.

The premise is also a non-sequitur: `Evidence.verified` and `Ingredient.verified`
are separate flags, and `water` is verified with no verified Evidence anywhere.

*Disposition:* FIXED 2026-07-21.

**9. The methodology worked example uses the superseded hand-rounded figure —
LOW**

Doc shows `process 223.65 x 0.040 = 8.9460`, half-width `64.8585`. Code and tests
give `8.8400` and `64.7525` (derived 0.03952604). The 0.040 is exactly the pasted
figure `26e5ff4` removed from the YAML; the doc's arithmetic block was not
re-derived with it.

*Disposition:* FIXED 2026-07-21.

**10. Two factual slips in the verification-priority section — LOW**

- "Wheat/atta, curd, coconut **and paneer**" — there is no paneer row in the
  fixture. Unused set is exactly `{coconut_fresh, curd_dahi, wheat_atta_raw}`.
- "verifying the **six** protein-dominant rows … changes `dev_mode` status."
  Five suffice, and per recipe far fewer: `rajma_cooked` alone drops
  `rajma_chawal` to 0.1256 < 0.15; `{rice_cooked, toor_dal_cooked}` clears
  `sambar_sadam`; `{urad_dal_raw, rice_milled_raw}` clears `masala_dosa`.
  `potato_boiled` is not needed. The doc's inference skips that the band is a
  weighted mix.
- `test_verification_alone_would_not_clear_the_ceiling_for_free` asserts the
  opposite of what its name says.

*Disposition:* FIXED 2026-07-21 (including the test rename).

**11. `demo.py` does not exist — LOW**
`CLAUDE.md` Commands block, `docs/methodology.md`

CLAUDE.md lists `python demo.py`; methodology requires "any `demo.py` stdout" to
carry the `dev_mode` label. There is no `demo.py` and no README in the repo. Same
class as the file's own "Things that have gone wrong before" entry about claiming
artifacts that are not in the repo.

*Disposition:* **CLOSED 2026-07-31** — see the entry at the top of this file
("the evidence chain was not reproducible"). `demo.py` now exists and is
tracked; CLAUDE.md's Commands block and `docs/methodology.md` both name a
command that runs. The finding turned out to be larger than a missing file:
every result this project's recent work rests on was produced by an untracked
scratch script.

**12. Two tests pass the pre-`26e5ff4` argument type — LOW**
`tests/test_recipes.py`

`load_recipe_file(Path(bad), frozenset(ingredients))` — the signature now
requires `Mapping[str, Ingredient]`. They pass only because both raise before
reaching `_derive_process_uncertainty`; moving where the loader validates would
turn them into confusing `TypeError`s rather than the assertions they claim.

*Disposition:* FIXED 2026-07-21.
