# core/ — context

Root `CLAUDE.md` holds the invariants. This file holds what is specific to
`core/`, and the open findings that affect it.

## Shape

Dependency direction is strictly downward:
`schemas/` → `nutrition/` → `foods/` → `planner/`. `core/nutrition` must never
import from `core/planner`. Nothing in `core/` imports a web framework or does
I/O beyond file loading.

Pipeline order in `planner/`: `candidates` → `combinations` (enumeration + O(1)
feasibility pre-filter + variety) → `solver` (integer unit counts) → `validator`
(point-estimate gate, relaxation ladder). `plan.py` wires it end to end.

Full reasoning: `docs/design/architecture.md`. Per-module state:
`docs/build_status.md`.

## Local rules

- Every nutritional constant lives in `core/nutrition/citations.py`, including
  yield factors, cooking losses and oil uptake. This does not stop at the
  boundary of `data/`.
- `quality_protein_g` is deliberately **not** a macro — absent from
  `MACRO_KEYS` and `NutritionVector`, because nothing measures it and putting it
  in the vector would make every `MACRO_KEYS` loop claim to know something about
  it.
- The validator gates on the point estimate. Intervals are display-only, and a
  perturbation test in `core/schemas/day_ledger.py`'s suite proves they cannot
  reach the budget.
- `core/nutrition` cannot see `core/planner`'s `LOCKED_CONSTRAINTS`, which is
  why `derive_target` warns on clinical flags rather than tightening anything.

## Open findings that affect this directory

As of 2026-08-12, derived from `docs/audit_log.md`, which is the authority — if
this list and that file disagree, that file wins. Status here is the newest
mention of each finding, not its first.

**`core/foods/`**

| # | What |
|---|---|
| 3–6 | Interval edge cases in `nutrition_of.py`. 3 = double-counted bands producing ±45%; 4 = a zero point estimate printing with no band; 6 = the low-end clamp biasing the reported fraction narrow. |
| 16 | The interval spans the bounds the point estimate passed against. |
| 19 | The confidence label saturates — `confident` is unreachable. |
| 41 | A declared process constant still leaves untouched macros at a bare zero. Re-scoped by D12: 65.2% of library protein arrives on served-basis rows whose zero is earned; the real gap is the other 34.8%, concentrated in `soya_chunk_curry` (98.1%), `soya_kuzhambu` (94.7%), `carrot_poriyal` (90.1%), `coconut_chutney` (89.9%), `masala_dosa` (82.4%). Needs four constants — rehydration, sauteing, steaming, dry-griddling. |
| 43 | Verifying every ingredient row cannot make any current plate servable. The eligibility ceiling blocks `idli`, `phulka`, `steamed_rice` at pool-build time; all four reference plates contain one. Human sign-off is necessary, not sufficient. |
| 45 | Four `yield.*` constants are registered, graded and used by nothing, and four ingredient `source_note`s claim a derivation their numbers do not satisfy (up to 22% off on `potato_boiled` energy, 19% on `toor_dal_cooked` protein). |
| 46 | A recipe line's declared `state` is never checked against the row it points at. |

**`core/planner/`**

| # | What |
|---|---|
| 15 | A combo component filled a slot alongside the base it already contains. |
| 17 | The fat floor was missed by 0.1 g, on precisely the known data gap. |
| 21 | Two constants in permanent contradiction, neither wrong alone. |
| 22 | A multi-dish South Indian plate cannot get under the sodium guard. Two south_lunch combinations exceed it at their *minimum* counts, so no profile can reach them. |
| 28 | The sodium guard is the only thing in the system that prefers less salt. |
| 29 | Relaxation rung 1 lets a *day* exceed its own sodium budget. |

**Also live here:** the 2026-08-07 observation that when the protein ceiling
empties the feasible set, the decline names energy rather than protein.
Finding-24-shaped, logged, not fixed — it is a property of
`_blocking_violations`.

## Deletion-testing rows

`docs/design/probes/d4b_mutations.py` grades the four planner modules,
`core/foods/nutrition_of.py` (rows N1–N5) and `core/foods/recipe_loader.py`
(rows R1–R7). Adding a gate here means adding a row. See the root `CLAUDE.md`
for what the harness has taught and where it cannot reach.
