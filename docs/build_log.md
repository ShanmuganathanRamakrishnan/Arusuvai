# Build log

Dated, append-only build history moved out of `CLAUDE.md` on 2026-07-29 so it
stops loading into every session. The content below is verbatim from that
file's `## Build status` section; nothing was summarized or dropped. The
module-state table it annotated stays in `CLAUDE.md`.

CLAUDE.md's process rule still applies here: no status line without a pasted
command transcript in the same entry.

Corrected 2026-07-21 during the Phase 1 build: rows previously marked "Built"
described files that did not exist in this repo. That is exactly the failure
mode the process rule above names — a status claim with no artifact behind it.
The table records what a fresh `pytest` run and inspection of the working tree
actually show. **Where this table and an external draft of CLAUDE.md disagree,
the repo's git history is authoritative.**

Restored 2026-07-21 from commit `116c765` after an external draft reintroduced
the fictional rows. The counts below are *not* `116c765`'s — the repo moved
since (110 -> 124 tests, and the understated-band caveat that row carried has
since been fixed), so they were re-derived from a run in this session rather
than copied.

An earlier draft of this table said 114, having been written mid-session and not
re-derived after further tests landed in the same commit. That is finding 7 in
`docs/audit_log.md`, and it is the same failure the process rule above names:
the transcript in the commit that wrote the line already refuted it.

Updated 2026-07-21 for the Phase 2 build (`core/planner/candidates.py`,
`combinations.py`, `solver.py`, `target.py`). Transcript in the same session:
`python -m pytest tests/ -q` -> `154 passed in 55.01s`.

Updated 2026-07-22 for the Phase 3 build (`core/planner/validator.py`,
`core/schemas/profile.py`, tolerance constants in `citations.py`). Transcript
in the same session, re-derived after the last edit rather than copied from the
earlier run in that session: `python -m pytest tests/ -q` -> `179 passed in
69.97s`.

Updated 2026-07-23 for the onboarding build (`core/nutrition/targets.py` and its
constants in `citations.py`; `Profile.diet` added; `NutritionTarget` moved from
`core/planner/target.py` to `core/nutrition/target.py` so the derivation can
produce it without `core/nutrition` importing `core/planner`; thin `api/`
exposing `POST /api/targets`). Transcript in the same session, re-derived after
the last edit: `python -m pytest tests/ -q` -> `215 passed in 67.44s`.

Updated 2026-07-23, same day, after adding the `clinical_flags` mandatory
disclosure to `derive_target` (see `docs/methodology.md`, "Clinical flags do
not tighten a target") and its three tests in
`tests/test_nutrition_targets.py::TestClinicalFlagsDoNotTightenTargets`.
Transcript in the same session: `python -m pytest tests/ -q` ->
`218 passed in 68.70s`.

Updated 2026-07-24 for wiring `core/planner` end to end
(`core/nutrition/meal_target.py`, `core/planner/plan.py`, `POST /api/plan`;
`meal_split.energy_fraction_*` constants in `citations.py`). Transcript in the
same session, re-derived after the last edit: `python -m pytest tests/ -q` ->
`229 passed in 74.73s`. Separately verified against a live `uvicorn` instance
in this session: `POST /api/plan` against the real `data/` library declines
with an identical, specific disclosure ("No plan could be built for this
profile: no recipe combination survived filtering for this profile, so there
was nothing to solve") for all four real templates
(`south_indian`/breakfast, `south_indian`/lunch, `north_indian`/lunch,
`north_indian`/dinner) and for a hypertension-flagged profile — see
`docs/methodology.md`, limitation 5, for why this is the expected outcome of
today's data, not a bug.

Updated 2026-07-24, same day, for real IFCT 2017 data on four ingredient rows
(`rice_milled_raw`/A015, `rajma_raw`/B020 new, `toor_dal_raw`/B021 new,
`potato_raw`/F006 new — see `data/raw/ifct/README.md`) and a correctness fix
to the energy-reconciliation Atwater check (`atwater.fibre_kcal_per_g` added,
`core/foods/ifct_loader.py`), found because real rajma data failed the old
flat-carbohydrate formula at 19% and passes IFCT's own fibre-aware formula at
8% — see `docs/methodology.md`, "Known limitations, Phase 1" items 1 and 3.
None of the four rows are `Ingredient.verified`; extraction by this project's
own tooling is not a human opening the primary source, per CLAUDE.md's
round-4 addendum on self-attestation. Transcript in the same session,
re-derived after the last edit: `python -m pytest tests/ -q` -> `233 passed
in 76.68s`.

Updated 2026-07-24, same day, for real, minimal accounts + profile persistence
(Tier B: `api/db.py` — SQLite via SQLAlchemy, `User` + `StoredProfile`;
`api/auth.py` — real `bcrypt` password hashing; `starlette.middleware.sessions.SessionMiddleware`,
a signed session cookie, added to `api/main.py`; five new endpoints,
`POST /api/auth/signup`\|`login`\|`logout`, `GET /api/auth/me`,
`GET`/`PUT /api/profile`). `core/nutrition`, `core/planner`, and the
`/api/plan` call/decline logic are untouched — `tests/test_api_auth.py::TestPlanEndpointUnaffected`
asserts `/api/plan` behaves identically with no session. `web/dashboard.html`
(new) is auth-gated and now owns the plate-picker + `POST /api/plan` call
that used to live in onboarding's step 6; `web/onboarding.html`'s step 6
became the account/save hinge instead (steps 1-5 still need no account).
`docs/methodology.md`, "Accounts and persistence: scope" states what this
increment explicitly did not build (no email verification, no password
reset, no OAuth, nothing commerce-shaped) as a named limit. Transcript in the
same session, re-derived after the last edit: `python -m pytest tests/ -q` ->
`256 passed in 82.20s`.

Updated 2026-07-30 for the "UI correction" P0 closeout — the round where the
fix stopped being another label map. `morton_2018_protein` reached the citation
panel inside a sentence, the third escape of the identifier-in-copy class after
two closures, each closure verified by grepping for the string it had just
fixed. That method cannot work: the failing string is by construction the one
nobody thought to grep for. So: `core/nutrition/citations.py` gained
`Evidence.display_ref` and `RENDERED_FIELDS`, and `register_evidence` now
resolves `{other_evidence_id}` slots and REJECTS a raw evidence id left in any
reader-facing field (`tests/test_citations.py` feeds it the exact string that
shipped and asserts the refusal, rather than asserting today's registry happens
to be clean). `tests/test_web_no_identifiers.py` (new) walks the rendered DOM
of all nine reachable views and fails on any `snake_case`/`SCREAMING_CASE`
token, allowlist empty; its failure was demonstrated by restoring the round-2
`chronic_kidney_disease` leak — `3 failed, 8 passed in 15.29s` — and then
restoring the fix. Applying the "which fields may fall through to `_`->space"
rule found three more raw-value fallbacks in `web/dashboard.js` (`plateLabel`'s
region/meal-slot pair and the success sentence's diet/goal) and fixed them;
evidence grade now falls through to `Ungraded`, never to prettified prose,
because an unrecognised grade rendered as sentence case is indistinguishable
from a real one. Measurement, no code change: the control column starts at
x=714 on all six wizard steps AND the plate picker at 1600x950 (it was ~1037 /
845 / 975 / 866 / 893 before the `.ob-grid12` refactor), now asserted by
`test_plate_picker_control_column_matches_the_wizard`. The P1 report's apparent
contradiction is resolved: at 390px nothing scrolls on any route
(`scrollWidth == clientWidth == 390`) AND `.calc-card` still overflows to
x=658 — both true, because `body { overflow-x: clip }` means a scroll check can
never detect an element hanging off the edge; both facts are now pinned
separately so neither can be quoted as settling the other. `web/onboarding.html`'s
brand is a link, the deliberate single exception to a wizard header that renders
no nav. Transcript in the same session, re-derived after the last edit:
`python -m pytest tests/ -q` -> `289 passed, 1 warning in 80.48s (0:01:20)`.

Updated 2026-07-30 for the P2 landing-page closeout — four values that each
existed in more than one place, plus one non-defect measured rather than
assumed.

The hero's `.draft-note` ("Placeholder copy — written for the founder to
rewrite in his own voice.") is removed, along with the class that styled it.

`--kolam-opacity` (`.06`) is now the single declaration for the background on
every route. It previously lived in four disagreeing places: `styles.css`'s
`.06`, `web/app.js`'s inline `0.03 + 0.15 * envelope` peaking at `.18`, a
reduced-motion `.16` in `app.js`, and a reduced-motion `.16` in a media query —
so the same element rendered three times stronger on the landing page than on
onboarding and the dashboard, and the seam showed on navigation. `app.js` now
reads the token from `getComputedStyle` and multiplies it by a `0..1` envelope,
so the landing page still breathes but its held peak EQUALS what the other two
routes show; both reduced-motion overrides are gone, because a second number in
that path restores the seam for precisely the users who cannot see the
animation that justified it.

The script cycler's language label is anchored to the word's box
(`align-items: flex-end` on `.morph-row`, and the hand-tuned
`padding-bottom: 16px` that compensated for the old baseline drift is gone).
The word is an inline-block at `line-height: .96`, so its box is exactly
`.96em` tall whatever script is in it; baseline alignment was wrong because
Tamil, Telugu, Kannada and Malayalam place their baseline at different heights
within one font-size, and the label moved every 2.5s as a result. Measured
across all four scripts after the fix: `labelBottom` 258 and
`deltaFromWordBox` 0 on every frame.

The calculator rail is in the layout system. It stays anchored to the viewport
— it is a utility rail, not page content, and is now the single documented
exception to the container token — but its responsive behaviour, previously
undefined, is now two rules: width comes from `--calc-panel-w` =
`min(308px, calc(100vw - 64px))`, read by BOTH the drawer and the card so the
two can never disagree; and anchoring drops from vertical-centre to bottom at
1100px, the same width `.ob-grid12` already collapses at rather than a new
number. Measured open at 1600 / 1280 / 1100 / 768 / 390 / 320px: fully on
screen at every width (308px card down to 390, 256px at 320).

`DESIGN_SYSTEM.md` known-inconsistency 0 is CLOSED, and its reading corrected
rather than just satisfied. The original 390px measurement — a 308px card with
its right edge at 658 — was taken with the drawer CLOSED, where `.calc-panel`
is 0px wide with `overflow: hidden`, so the card's paint is clipped by its own
drawer and not by the page. That is the component working. The real gap was the
OPEN state below ~372px. Both facts are now pinned separately
(`test_the_closed_dock_paints_nothing_outside_the_viewport` and
`test_the_open_calculator_dock_fits_the_viewport`) so the conflation cannot
recur. The durable lesson stands: `body { overflow-x: clip }` means
`scrollWidth == clientWidth` is evidence overflow is being hidden, not that
content fits.

The plate picker's large empty region needed no code change, and that was
established by measurement rather than by reading the markup: `POST /api/plan`
renders into that space on the same route. Before Generate, content ends at
y=322 with the footer at y=817; after, the decline section occupies y=375-952
and the footer moves to y=1052.

Every one of the four fixes was shown to be capable of failing. Perturbing the
landing three back to their broken form: `3 failed, 1 passed in 34.70s`
(`test_the_kolam_never_exceeds_its_token_on_the_landing_page` — "peaks at 0.18
against a --kolam-opacity of 0.06"; `test_the_language_label_holds_position_...`;
`test_no_placeholder_copy_renders_in_the_hero`). Perturbing `--calc-panel-w`
back to a bare `308px`: `1 failed, 8 passed in 22.23s` — "at 320px the card
starts off-screen left, assert -28 >= 0". All four then restored.

Transcript in the same session, after the last edit: `python -m pytest tests/ -q`
-> `301 passed, 1 warning in 128.95s (0:02:08)`. The suite went 289 -> 301; the
single warning is the pre-existing `FOODAI_SESSION_SECRET is not set` notice
from `api/main.py:91`.

---

Updated 2026-08-07 for D2b-ii, slice 4 — the quality-source rule.

Per-meal floor on protein from ingredients clearing
`protein.quality_diaas_threshold` (0.75). New `core/foods/quality.py`; new
`NutritionTarget.quality_protein_floor_g` set by `core/nutrition/meal_target.py`
at 0.10 x the day protein floor; gates in `combinations.feasible_combinations`,
`solver._within_target_point` and `validator._violations_for` /
`_blocking_violations`. No relaxation rung touches it. Full account in
`docs/methodology.md`, "Protein quality is a rule about sources".

The prediction was written before any code changed and is quoted in
`docs/audit_log.md`, 2026-08-07: four of six calls held exactly, and the one
that missed was the *shape* of the two south declines (quality is named instead
of energy/fat/sodium, not alongside them).

Measured verdicts, reference profile, via the tracked entry point
`python demo.py plan --region <r> --meal-slot <s>`:

```
south_breakfast  before: declines, 4 rungs, energy 777.1>707.0 / fat 33.2>24.6 / sodium 2273.4>1400.0
                 after : declines, 4 rungs, quality protein 8.99 < 11.20
south_lunch      before: declines, 4 rungs, energy 1033.1>989.9 / fat 39.7>34.4 / sodium 2836.8>1400.0
                 after : declines, 4 rungs, quality protein 8.99 < 11.20
north_lunch      before: passes, 0 rungs, phulka x4 + dal_tadka x2 + tofu_bhurji x1   (929.8 kcal, 1209.0 mg Na)
                 after : passes, 0 rungs, phulka x5 + soya_chunk_curry x1 + paneer_masala x1 (931.2 kcal, 992.2 mg Na)
north_dinner     before: passes, 0 rungs, phulka x4 + dal_tadka x1 + tofu_bhurji x1   (756.8 kcal,  889.2 mg Na)
                 after : passes, 0 rungs, phulka x3 + soya_chunk_curry x1 + aloo_sabzi x1 + onion_raita x2 (782.5 kcal, 1371.3 mg Na)
```

Six defects were injected and each turned the new test file red. The first
injection — deleting the gate from `solver._within_target_point` — left all 31
tests green, because `feasible_combinations` discards quality-failing
combinations before the solver runs. That is finding 26 in `docs/audit_log.md`
and it was fixed in the same commit by `TestTheSolverGateItself`, which isolates
the gate on the synthetic pool. Re-injected afterward:

```
FAILED tests/test_planner_quality.py::TestTheSolverGateItself::test_the_gate_changes_the_chosen_unit_counts - assert 1 == 2
FAILED tests/test_planner_quality.py::TestTheSolverGateItself::test_the_gate_can_empty_a_solve_the_pre_filter_admitted
2 failed, 31 passed in 1.08s
```

The other five: protein rung relaxing the quality floor (4 failed, 29 passed);
floor scaled by the energy share (9 failed, 24 passed); a missing DIAAS reading
as qualifying (15 failed, 18 passed); day floor taken off `quality_adjusted_g`
instead of `base_g` (2 failed, 31 passed); `_widen_band` rebuilding the target
with an explicit constructor that drops the new field (6 failed, 27 passed). All
restored, and proven restored: `33 passed in 1.01s`.

Transcript in the same session, after the last edit: `python -m pytest tests/ -q`
-> `1 failed, 369 passed, 40 skipped, 1 warning in 109.50s (0:01:49)`. The suite
went 337 -> 370 collected. The single failure is
`tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants`,
the deliberately-red test that predates this work (`onion_raita` and
`thayir_plain` carry a fully-populated map of computed zeros and no process
constants — the open cross-reference against finding 2); it is red for the same
reason and with the same message as before this commit. The warning is the
pre-existing `FOODAI_SESSION_SECRET is not set` notice from `api/main.py`.

---

## Updated 2026-08-07 for D3 — three recipes make the south templates reachable

Slice 4's quality floor left both South Indian templates declining for every
profile. D3 closes that with three recipe files and no rule change: no
threshold, fraction, DIAAS value or salt line moved, and no ingredient row was
added. See `docs/methodology.md`, "Making the south templates reachable", and
`docs/audit_log.md`, the 2026-08-07 D3 entry.

The diagnosis is the part worth recording: the quality shortfall was 2.21 g, but
the binding constraint was **sodium**. Neither south template could reach its
energy floor under the 1400 mg `hard_ceiling`, which predates the quality rule.
Two of the three recipes therefore exist for salt, not protein.

Per-unit table, measured from the loaded library:

```
recipe             unit            g min max    kcal   prot    fat   carb   fib      Na
idli               idli           40   2   6    50.4   1.71   0.11   10.8   0.7    87.1
soya_kuzhambu      katori        150   1   2   169.9  14.24   5.96   15.5   4.9   323.5
steamed_rice       cup           200   1   3   260.0   5.40   0.60   56.4   0.8     2.0
masala_dosa        dosa          150   1   3   226.6   5.32   7.02   36.5   2.7   594.2
sambar_sadam       cup           200   1   3   265.0   7.16   5.34   46.1   3.8   408.6
```

Slot coverage and enumeration, all four templates, after:

```
south_breakfast:
    tiffin_item          REQ n=2 ['idli@tiffin', 'masala_dosa@tiffin']
    gravy_accompaniment  REQ n=2 ['sambar@sambar', 'soya_kuzhambu@kuzhambu']
    chutney              REQ n=1 ['coconut_chutney@chutney']
    curd_course          opt n=1 ['thayir_plain@curd']
    beverage             opt n=0 []
south_lunch:
    rice_base            REQ n=2 ['sambar_sadam@mixed_rice', 'steamed_rice@rice']
    gravy                REQ n=2 ['sambar@sambar', 'soya_kuzhambu@kuzhambu']
    vegetable            REQ n=2 ['carrot_kootu@kootu', 'carrot_poriyal@poriyal']
    curd_course          REQ n=1 ['thayir_plain@curd']
    crisp                opt n=0 []
north_lunch, north_dinner: unchanged

combinations: south_breakfast 2 -> 8, south_lunch 3 -> 12,
              north_lunch 24 -> 24, north_dinner 12 -> 12
```

`python demo.py plan`, reference profile, after:

```
=== south_indian / breakfast ===
passed         : True
relaxation     : ()
  unit counts  : {'idli@tiffin': 6, 'soya_kuzhambu@kuzhambu': 1,
                  'coconut_chutney@chutney': 2, 'thayir_plain@curd': 1}
  point        : 623.6 kcal, 29.6g protein, 18.5g fat, 87.3g carb, 1189.8mg sodium
=== south_indian / lunch ===
passed         : True
relaxation     : ('sodium_max_fibre_min', 'fat_carb_tolerance', 'energy_tolerance')
  unit counts  : {'steamed_rice@rice': 1, 'soya_kuzhambu@kuzhambu': 2,
                  'carrot_poriyal@poriyal': 2, 'thayir_plain@curd': 1}
  point        : 848.1 kcal, 40.4g protein, 29.3g fat, 107.4g carb, 1391.1mg sodium
=== north_indian / lunch ===
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 5, 'soya_chunk_curry@legume_curry': 1, 'paneer_masala@sabzi': 1}
  point        : 931.2 kcal, 46.6g protein, 27.7g fat, 123.1g carb, 992.2mg sodium
=== north_indian / dinner ===
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 3, 'soya_chunk_curry@legume_curry': 1,
                  'aloo_sabzi@sabzi': 1, 'onion_raita@raita': 2}
  point        : 782.5 kcal, 36.8g protein, 23.0g fat, 109.0g carb, 1371.3mg sodium
```

Both north plates are byte-identical to the pre-D3 run. They could not have
moved: `core/planner/candidates.py` rejects any recipe whose region is neither
the template's nor `pan_indian`, and all three new recipes are `south_indian`.

### Finding 27, found by the first recipe with `min_count > 1`

`build_candidate_pool` raised `ValueError: idli: count 1 outside [2, 6]` before
it could filter anything. `_eligibility_flags` priced candidates at a hard-coded
1 while `nutrition_of_recipe` enforces the unit's bounds; every recipe until now
had `min_count == 1`. Fixed to `min_count`, with the same fix in three
`tests/test_nutrition_of.py` tests carrying the same literal.

### Defect injections — four, each red, each restored

```
1. revert candidates.py min_count -> 1
   9 failed, 58 passed   (tests/test_planner_candidates.py, _quality.py, _plan.py)
   ValueError: idli: count 1 outside [2, 6]

2. rm data/recipes/soya_kuzhambu.yaml
   4 failed, 32 passed
   FAILED ...TestAgainstTheRealLibrary::test_the_south_templates_now_reach_the_floor
   FAILED ...test_the_reference_breakfast_plate_is_idli_kuzhambu_chutney_curd
   FAILED ...test_the_reference_lunch_still_needs_three_rungs_and_why
   FAILED ...TestThePerturbationTest::test_disqualifying_curd_moves_the_south_breakfast_figure

3. rm data/recipes/steamed_rice.yaml
   2 failed, 34 passed
   AssertionError: (Violation(macro='sodium_mg', kind='above_ceiling', ...
   -- the sodium diagnosis, checked rather than asserted

4. rm data/recipes/idli.yaml
   4 failed, 44 passed
   AssertionError: assert ('sodium_max_...gy_tolerance') == ()
   -- south_breakfast falls from 0 rungs to 3 without it
```

Restored and proven restored: `48 passed in 1.18s`.

Transcript, after the last edit:

```
python -m pytest tests/ -q
1 failed, 374 passed, 40 skipped, 1 warning in 106.91s (0:01:46)
```

The suite went 370 -> 375 collected: three tests in
`tests/test_planner_quality.py` were replaced by five (the two south-template
facts D3 inverted, plus a re-homed decline-prose test and a split perturbation),
and `tests/test_planner_candidates.py::TestServingUnitsWhoseFloorIsAboveOne`
added two for finding 27. The
single failure is
`tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants`,
the deliberately-red test that predates this work. It was verified red *before*
D3 with the new files stashed (`git stash -u`), failing on `onion_raita`; it now
fails on `idli`, which sorts first and carries the same defect. Same assertion,
same message class, untouched. The warning is the pre-existing
`FOODAI_SESSION_SECRET is not set` notice from `api/main.py`.

Updated 2026-08-09 for D10 (`core/foods/recipe_loader.py`'s
`_check_zero_process_is_earned` and `preparation:`; five recipe YAML files;
`data/recipes/schema.yaml`; `docs/design/probes/d10_process_zero.py`;
`docs/design/probes/d4b_mutations.py`). Closes `docs/audit_log.md` finding 2;
raises finding 41 (unfixed, by scope) and finding 42 (fixed).

**The suite has no deliberately-red test any more.** The one that stood since
2026-07-24 was retired because reading it while fixing finding 2 showed its
condition `if recipe.process_uncertainty:` is *always* true —
`Recipe.process_uncertainty` is mandatory per macro and never empty — so what it
actually asserted was "every recipe carries a process constant", which held by
accident until D3 added the library's first oil-free cooked dishes. It was never
a rule worth satisfying.

Transcript, after the last edit, with the API on :8000 and a static server on
:3000 so the browser checks genuinely ran rather than skipping:

```
python -m pytest tests/ -q --color=no
........................................................................ [ 14%]
[...]
505 passed, 1 warning in 224.96s (0:03:44)
```

497 -> 505 collected and **zero skipped, zero failed**. The eight are the D10
tests in `tests/test_recipes.py` (six new in
`TestZeroProcessUncertaintyMustBeEarned`, one of which —
`test_a_macro_the_dish_contains_none_of_needs_no_justification` — was written
only after mutation R5 survived); the other two are net of
`test_declared_uncertainty_is_backed_by_registered_constants` being rewritten
rather than added. Two existing tests in
`tests/test_nutrition_of.py::TestEligibilityConsequence` went red on D10 and
were rewritten rather than restored: one asserted every recipe's protein band is
0.25, now true of 15 of 18; the other asserted that verifying every ingredient
row clears the eligibility ceiling for the whole library, which D10 showed is
false for the three dishes that cook without oil. That second correction is the
one with consequences outside this task — see `docs/methodology.md`, "A zero
process uncertainty has to be earned".

Deletion-checked, after fixing the harness itself (finding 42: it copied `core/`
and `tests/` from the working tree but left `data/` at HEAD, so the new loader
met the old recipe files and the library fixture errored on every run):

```
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py R1,R2,R3,R4,R5
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

The warning is the pre-existing `FOODAI_SESSION_SECRET is not set` notice from
`api/main.py`.
