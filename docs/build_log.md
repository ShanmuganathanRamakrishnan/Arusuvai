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
