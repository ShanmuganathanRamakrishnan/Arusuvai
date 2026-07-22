# Audit log

Dated, append-only. Per CLAUDE.md's audit-workflow section, this file is the
artifact: a finding that isn't written here did not happen. Findings are
recorded whether or not they are fixed; the "Disposition" line says which.

Newest entries at the top.

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

*Disposition:* OPEN.

**12. Two tests pass the pre-`26e5ff4` argument type — LOW**
`tests/test_recipes.py`

`load_recipe_file(Path(bad), frozenset(ingredients))` — the signature now
requires `Mapping[str, Ingredient]`. They pass only because both raise before
reaching `_derive_process_uncertainty`; moving where the loader validates would
turn them into confusing `TypeError`s rather than the assertions they claim.

*Disposition:* FIXED 2026-07-21.
