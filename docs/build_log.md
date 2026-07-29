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
