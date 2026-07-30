# CLAUDE.md

Project context for Claude Code. Read this before any task in this repo.
This file was revised after an architecture audit that found real defects in
v1. If anything below conflicts with your own instincts about "how AI meal
planners are usually built," this file wins — it was hardened against
specific, named failure modes, not written from convention.

## What this is

An AI meal planner for South and North Indian diets. A user supplies a body
and goal profile; the system produces a nutritionally validated daily or
weekly meal plan, and optionally lets them order those meals delivered
(simulated).

This is a portfolio project. It is not a real food business. Meal delivery,
subscriptions and kitchen operations run against seeded fixture data.

## Central invariant — precise wording matters here

**The LLM never touches a gram value, a portion size, or any quantity that
determines nutritional content.** Its entire input/output surface, for
planning, is: given a set of already-numerically-valid candidate plans, choose
or rank among them, and write connective narration around numbers supplied to
it, not computed by it.

Do not restate this as "the LLM never produces a number that anyone relies
on." That wording was tried and shown false: a portion multiplier is a number,
and a multiplier the LLM proposes is one the user relies on even if a
validator later checks it. Proposing-then-checking is a materially weaker
guarantee than never-touching, and the two must not be conflated in docs, in
code comments, or in this file.

### Why this isn't "the LLM proposes portions, a solver checks them"

That shape has a real, examined failure mode: on final rejection after N
retries, what does the user see? Answering that honestly (see "Relaxation" below)
is only tractable because the architecture below moves portion determination
to the solver entirely, so the LLM cannot produce an invalid plan in the first
place. If you find yourself building a retry loop around LLM-proposed
quantities, stop — you have rebuilt the shape that was rejected.

### What the LLM actually does

Everything numeric is deterministic: candidates pre-filtered, targets computed,
portions solved, validity gated. A solver can enumerate every numerically
feasible combination; what it cannot do is know that sambar + curd rice + more
sambar is not a plate anyone in Chennai would eat. That's the LLM's job:
**cultural and palatability ranking over an already-valid set**, plus writing
the human-facing description. Nothing else.

Pipeline, corrected:

1. Deterministic candidate filter (diet, allergen, region, meal template).
2. Deterministic **enumeration of distinct recipe combinations** per meal
   template (see "Meal templates," below) — combinations, not portions yet.
3. Cheap O(1) feasibility pre-filter per combination (sum each component's
   declared min/max contribution to each target macro; discard combinations
   that can't possibly reach the floor or must exceed the ceiling) before
   running a full solve on anything.
4. Solver runs only on combinations that survive the pre-filter, finding an
   integer-unit portion assignment (see "Serving units," below) per surviving
   combination, or discarding it as infeasible.
5. LLM ranks/selects among the surviving, already-valid combinations for
   palatability and variety against recent history. It receives combinations
   as opaque IDs with computed macro summaries — never raw grams to reason
   about, never an invitation to propose a scaling factor.
6. LLM writes narration using a **template with named numeric slots**
   (`"{dish_name} delivers a solid {protein_g}g of protein"`), where the
   Python layer substitutes `{protein_g}` from the validated plan. The model
   supplies only the surrounding language. Any raw digit in a model-authored
   field that isn't a recognized slot placeholder is stripped and the
   response is rejected — check this mechanically, do not rely on the model
   following the instruction unsupervised.

If a design decision would have the LLM emit a quantity — a multiplier, a
gram value, a serving count — that is the specific defect this file exists to
prevent. Route it through the solver instead.

## Serving units — not continuous multipliers

Portion space is not continuous in reality: 1.25 × one idli is 3.75 idlis,
which is not servable. Every recipe declares:

```
unit: str            # "idli", "dosa", "katori", "roti", "50g_scoop", ...
min_count: int
default_count: int
max_count: int
```

The solver optimizes over **integer unit counts**, never a continuous or
five-point multiplier scale. A five-point multiplier (0.5/0.75/1.0/1.25/1.5)
is not an acceptable substitute — it produces the same unservable fractional
output, just discretized to look tidier.

## Meal templates — the slot grammar is not uniform

Do not assume a fixed 5-slot grammar (base/protein/curry/vegetable/
accompaniment) applies to every meal. It doesn't: South Indian breakfast
(idli + sambar + chutney) has no separate vegetable slot and no base/curry
split; South lunch (rice + sambar + poriyal + curd) has a different shape
again; North dinner (roti + dal + sabzi) has no rice slot.

Declare a `MealTemplate` keyed by `(region, meal_slot)`, each with its own
named, possibly variable-length, possibly-optional slot list. This is a data
structure in `core/foods/`, not an assumption baked into the solver.

**Combination arithmetic must be shown, not asserted.** Do not write "the
combination space is bounded" without computing it against the actual
post-filter recipe counts for the actual template in question. For a whole
week, do not cross-product all 21 meal-slots against each other — generate a
single day's combinations against its template, then repeat with a no-repeat
variety constraint across the week. If you assert a bound (e.g. "hundreds of
combinations"), show the arithmetic that produced it in a comment.

## Uncertainty — a separate axis from tolerance, and it does not gate

Two different things, and they must not be merged:

- **Tolerance**: how far a plan's point estimate may sit from the target and
  still count as valid. This is what the validator gates on.
- **Uncertainty**: how much genuine measurement error exists in a constant
  (e.g. oil uptake on a griddled dosa varies with the cook and the pan —
  reasonably ±15-20% on that one ingredient's energy contribution). This is a
  property of the data, not a lever anyone adjusts.

**The validator gates on the point estimate against tolerance only.** It never
gates on interval overlap. Interval-overlap gating is disqualified: it means a
plan with worse underlying data (wider uncertainty) passes more easily than
one with better data, which is a perverse incentive baked into the core safety
mechanism and was caught specifically because it inverts the point of having
a gate at all.

Uncertainty is instead a **candidate eligibility filter, applied before a
plan is assembled**: a recipe whose *combined* composition-plus-process
uncertainty on a given macro exceeds a stated ceiling (default ±15% on
protein, wider tolerance on energy) is excluded from candidate pools where
that macro is target-critical, or its contribution to that macro is estimated
conservatively (high-end, not optimistic) rather than at the point estimate.
Uncertain data makes a recipe less usable, never makes a plan easier to pass.

Gate on the *combined* figure
(`core.foods.nutrition_of.NutritionEstimate.uncertainty_fraction`), never on
`Recipe.process_uncertainty` alone. Corrected 2026-07-21 (`docs/audit_log.md`
finding 1): the process field alone is 0.0 for protein on every recipe in the
library — oil carries no protein, so no process term ever touches that macro
— and an implementation that gated on it literally would admit every recipe
regardless of how unreliable its composition data is, while matching this
paragraph's previous wording exactly. `core/planner/candidates.py` gates on
the combined figure; see its module docstring for the worked argument.

**Display the interval to the user regardless.** "≈1,850 kcal (±10%)" is a
stronger and more honest artifact than "1,847 kcal." Precision the data
doesn't support is a liability, not a feature — showing a false-precise point
estimate is the same failure mode this whole project exists to avoid in the
LLM, committed instead by the data pipeline.

### Raw versus cooked weight — decide before authoring a single recipe

Recipe YAML stores **cooked/finished weights as the primary record**, sourced
from IFCT's cooked-value entries where they exist. Rice roughly triples on
cooking. Getting this backwards is a 3x error, not a tolerance-band problem,
and it must be settled in the schema before Phase 1 recipe authoring starts,
not discovered partway through.

### Process-loss constants need citations too — no exemption for `data/`

Yield factors, oil uptake, and cooking losses are nutritional constants
exactly as much as an RDA figure is. The "no magic numbers outside
`citations.py`" rule does not stop at the boundary of a data file. Where real
literature exists for the specific process (not an adjacent one — see
"Evidence.phenomenon" below), register it with a DOI. Where Indian-specific
process literature is thin (it usually is), register a conservative estimate
explicitly marked `verified=False`, with a wide uncertainty band, rather than
silently borrowing a number from an unrelated food-science paper.

## Evidence needs a `phenomenon` field — citation-presence is not citation-relevance

A real, findable, correctly-cited DOI can still describe the wrong physical
process. (Concretely: deep-fat frying oil-absorption literature, e.g. Bouchon
& Pyle on post-fry crust cooling in potato products, does not describe
surface oil pickup on a griddled dosa — a different mechanism entirely. A
citation like that passes every automated check the registry performs while
describing food that isn't the food in question. This is more dangerous than
a fabricated citation, because a fabricated one is falsifiable by anyone who
looks it up, and a mismatched-but-real one isn't, without domain expertise.)

`Evidence` must carry a `phenomenon: str` field stating precisely what
process the source measured, distinct from `summary`. Wherever a constant is
applied, the applying code should state, in a comment or field, the process
it's being used for. If those two don't plausibly describe the same
mechanism, do not register the citation — mark the constant `verified=False`
with an honest note that no matching primary source was found, rather than
attaching a real-but-wrong one. A registration path that lets relevance
substitute for mechanism-match is the actual hole in the citation defense;
close it structurally, not by promising to be more careful.

### Threshold for shipping with unverified constants

A plan may ship as validated if the aggregate energy contribution from
`verified=False` process constants is below roughly 15% of total plan energy
(provisional — revisit once real recipe data shows how common unverified
constants actually are; for Indian preparations specifically, expect this to
be common, not rare). Disclose this once, in one sentence, when it applies
("this plan's estimate carries wider uncertainty than usual because oil-uptake
data for two dishes hasn't been verified against a primary source") — not as
a per-dish asterisk. A per-item flag on every third recipe is wallpaper by day
three and stops functioning as a warning. Above the threshold, decline to
serve the plan as validated and say specifically why, rather than caveat
something you shouldn't be shipping.

## Relaxation ladder — ordered, disclosed, and profile-conditioned

When the solver finds zero feasible combinations for a profile (this is the
real hard case — under this architecture the LLM cannot fail validation, so
the only remaining failure is the solver having nothing to hand it), relax in
this order, and only this order, and only the tolerance axis (never the
uncertainty axis — those don't multiply, because uncertainty is never a knob):

1. Sodium max, fibre min — general health guidance, not the product's core
   nutritional claim. **This rung widens the bound by a stated, registered
   fraction (`tolerance.sodium_relaxed_fraction` / `tolerance.fibre_relaxed_fraction`,
   both 0.50) — it does not drop the bound to "no ceiling/floor at all."**
   Dropping it entirely was tried first, reads as the more natural
   implementation for a one-sided bound with no ideal point to widen a band
   around, and was caught precisely because it produces a fully unconstrained
   worst case for an unflagged profile: an unflagged profile's sodium ceiling
   would vanish the instant this rung fired, meaning the "least load-bearing
   constraint relaxes first" guidance became "least load-bearing constraint
   stops existing," which is a materially stronger claim than the ladder is
   meant to make. "Least load-bearing" is a claim about relaxation order, not
   about whether a bound applies at all — this ambiguity must not be resolved
   only inside `core/planner/validator.py`'s implementation, which is why it is
   stated here explicitly.
2. Fat/carb tolerance (15% → up to 25%) — least load-bearing macros, they
   absorb whatever energy is left over.
3. Energy tolerance (5% → up to 10%).
4. Protein tolerance — relaxes last, partially, with **mandatory disclosure**
   in the same units the target was originally stated in (e.g. "this plan
   delivers 76g of protein against a 90g target; the recipe library doesn't
   currently have a vegetarian component dense enough at this calorie level to
   close the gap"). Never disclosed silently, unlike the earlier steps.

**This ordering is not global.** `Profile.clinical_flags` (hypertension,
kidney disease, diabetes, etc.) locks the constraint tied to a disclosed
condition entirely out of the ladder — it becomes a hard floor/ceiling that
never relaxes for that profile. If a locked constraint makes the feasible set
empty, decline and name the specific blocking constraint rather than loosen
it. `docs/methodology.md` must state plainly, as prominently as the DIAAS
section: the default ordering assumes no clinical dietary condition; this
system is not a substitute for clinical nutrition guidance; a user with a
diagnosed condition should rely on `clinical_flags`, not on the default
behavior.

## Second invariant: no magic numbers, extended to `data/`

Every nutritional constant — in Python or in a recipe YAML file — lives in
`core/nutrition/citations.py` (or references an `Evidence` object from it)
with a source, DOI where one exists, evidence grade, and `phenomenon`. This
now explicitly includes yield factors, cooking losses, and oil uptake, not
only RDA-style targets. Constants transcribed from memory rather than a
primary document are marked `verified=False`. Only a human who has opened the
source document may flip that flag to `True`.

## Process rule: no unverified claims about the project's own state

Do not write a status line — "N tests pass," "module X is done" — without a
pasted command transcript backing it **in the same artifact**, produced in
the same session. A claim about the repo's state that isn't backed by an
artifact in the repo has a shorter half-life than the document asserting it,
and is exactly the failure mode this project's central thesis argues against.
If you claim a test count, the pytest output goes in the same message or
commit, not a reference to a prior run.

## Architecture

```
core/                  Pure logic. No web framework, no I/O beyond file loading.
  schemas/             Dataclasses shared everywhere. No dependencies on siblings.
                       Profile.clinical_flags lives here.
  nutrition/           Targets from profile. Depends only on schemas.
                       citations.py: Evidence now carries `phenomenon`.
  foods/               Ingredients, recipes, components, MealTemplate, portions
                       (serving units, not multipliers). Depends on schemas.
  planner/             candidates -> combination enumeration -> feasibility
                       pre-filter -> solver (integer unit counts) -> LLM
                       ranking/narration -> validator (point-estimate gate,
                       relaxation ladder). Depends on all above.
  commerce/            Plans, orders, zones. Seeded fixtures only.
api/                   FastAPI. Thin. Translates HTTP to core calls.
                       api/db.py: SQLite via SQLAlchemy — User + StoredProfile
                       only (accounts + profile persistence). No nutritional
                       computation happens here either; it stores the same
                       fields core.schemas.Profile validates.
web/                   Next.js. Displays. Never computes nutrition.
data/                  IFCT subset, recipe YAML (cooked weights), fixtures.
tests/
docs/
```

Dependency direction is strictly downward. `core/nutrition` must never import
from `core/planner`.

## Conventions

**Testing.** Expected values are hand-computed from published equations, with
the arithmetic shown in a comment. Never snapshot current output.

```python
def test_mifflin_male():
    # 10*70 + 6.25*175 - 5*28 + 5 = 700 + 1093.75 - 140 + 5 = 1658.75
    assert bmr_mifflin_st_jeor(make()) == pytest.approx(1658.75)
```

**Types.** `from __future__ import annotations`. Frozen dataclasses across
module boundaries. Full annotations on public functions.

**Errors.** Raise on impossible input. Warn on implausible-but-valid input via
a `warnings: list[str]` field — never silently clamp without recording it.

**Comments.** Explain _why_ a choice was made over its alternatives, not what
the line below already says.

**Known limitations go in `docs/methodology.md`,** documented, not hidden.

## Addendum — round 4 findings (uncertainty and self-review were both understated)

These were places where the code _followed_ the rules above and still produced
the failure the rules exist to prevent. That's a stricter bug than rounds 1–3:
it means "the doc's rule is implemented" is not sufficient evidence the rule
works — the test has to perturb an input and check the output actually moves,
not just check the rule is mentioned.

**Composition uncertainty is a separate, currently-missing axis from process
uncertainty.** `Recipe.process_uncertainty` (oil uptake, cooking loss) is not
the only source of error — the underlying ingredient composition data itself
carries uncertainty, and today that's silently treated as zero. Add
`Ingredient.composition_uncertainty: dict[str, float]` per macro, driven by
`Ingredient.verified`: a verified-against-IFCT ingredient gets a tight
registered default; an unverified fixture-sourced one gets a wide registered
default (itself an `Evidence`-backed constant, not a bare literal). The
displayed interval must combine composition uncertainty (weighted by each
ingredient's share of that macro) with process uncertainty. A dish that is
96% rice/lentil/vegetable and 4% griddle oil must not display a tighter band
than the rice/lentil/vegetable data actually supports — a narrow band on
mostly-unverified composition data is the same false-precision failure this
project exists to prevent in the LLM, committed instead by the data layer,
and is worse than a bare unqualified number because it actively asserts the
error is small.

**Missing uncertainty must never default to most-confident.** If a macro's
uncertainty is unset, it must not read as `0.0`. Make the field mandatory per
macro (fail the load on omission) or require an explicit `unassessed` sentinel
that maps to a wide registered default. The cheapest authoring path — skipping
the field — must never produce the most confident-looking output; today it
does, and that ordering is backwards.

**No nutritional number may be hand-duplicated outside `citations.py`,
including a derived uncertainty figure pasted into a recipe YAML file.** A
recipe's stored `process_uncertainty` value must be computed at load time from
the current constant in `citations.py` plus the recipe's declared exposure
(e.g. oil grams as a fraction of dish weight) — never hand-computed once and
pasted in. If a constant changes, every recipe depending on it must change
too, automatically, on next load. Test this directly: mutate a constant and
assert dependent recipes' computed uncertainty changes; a test that only
checks a fixed YAML value against itself cannot catch this class of bug.

**The unverified-energy threshold must be measured against the correct
denominator, in both directions.** A recipe is not "X% unverified" because
some process constant on it is unverified — it's unverified in the
_proportion of its energy that constant actually contributes_, not the whole
dish. Conversely, unverified _ingredient composition_ (see above) must also
count toward the total — a recipe with a fully verified process but
unverified composition data is not thereby "verified." Get both directions
right before trusting the 15% shipping threshold against real data.

**State plainly, once counted correctly, whether anything can ship as
validated today.** If every registered `Evidence` is currently
`verified=False`, the honest conclusion — once the denominator above is fixed
— may be that nothing can presently ship as validated. Say so directly in
`docs/methodology.md`, dated. That is a defensible thing for a portfolio
project to state. Discovering it silently after `core/planner` is built on
the assumption that some plans clear the threshold is not. Keep a `dev_mode`
designation distinct from `validated`, so plan generation and testing can
proceed on admittedly-unverified data, loudly labeled, without conflating
"the pipeline runs" with "the pipeline can stand behind a number."

**A mechanism-match review dict is not a structural fix if the same person
edits it in the same commit as the constant it reviews.** `verified=True`
must only ever be set by a human who opened the primary source — the same
standard applies to any "mechanism confirmed" review status. Self-attestation
by the constant's own author can only ever record "no matching source found"
or "not yet reviewed" — never a positive "match confirmed." A genuine
confirmed-match state requires a second party's sign-off, tracked separately
from who registered the constant, or a dedicated evidence grade
(`PROJECT_ESTIMATE`: self-reviewed, single-author) that is categorically
ineligible to satisfy the mechanism-match requirement or count toward
"reviewed" in the shipping threshold, no matter what its own checklist says.

## Audit workflow — how findings get produced and addressed

Adversarial review of this codebase happens inside Claude Code, against the
actual files, not in a separate chat requiring manual copy-paste. Structure:

- `.claude/agents/auditor.md` — a subagent with **read-only** tool
  permissions (`Read`, `Grep`, `Glob`, `Bash(pytest:*)` — no `Edit`, no
  `Write` outside `docs/audit_log.md`). Its job is to find places where code
  and this doc agree with each other and neither survives a concrete input.
  It does not propose fixes and does not soften findings.
- `.claude/commands/grill.md` — invokes the auditor against modules changed
  since the last `docs/audit_log.md` entry.
- `docs/audit_log.md` — dated, append-only findings. This is the artifact;
  a finding that isn't in this file did not happen, per the process rule
  above about unverified claims regarding the project's own state.

The read-only permission boundary is load-bearing, not incidental: an auditor
that can edit the code it's reviewing can rubber-stamp its own work exactly
the way a self-edited mechanism-match dict did in round 4. Do not grant the
auditor subagent write access to anything under `core/`, `api/`, or `web/`.

When addressing an audit finding, reference it by its dated entry in
`docs/audit_log.md` in the commit or PR description, so the fix is traceable
to the finding rather than a description of the finding living only in a chat
transcript.

## Build status

Only update this table with a command transcript in the same message.

Dated per-session build history — every "Updated <date> for <phase>" entry and
the pytest transcript backing it — now lives in `docs/build_log.md`, moved there
2026-07-29 verbatim. It was history, not something a session needs resident: the
process rule requires the transcript to exist in the repo, not in this file.
Append new entries there, and update the table below in the same commit.

| Module                    | State                                                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `core/schemas/`           | Partial — `common.py` (RawOrCooked, Region, MealSlot, DietPattern, MACRO_KEYS) and `profile.py` (`Profile`, `ClinicalFlag`, `ActivityLevel`, `Goal`, `Sex`). `Profile` now carries `diet: DietPattern` and its body fields ARE read: `core/nutrition/targets.py` turns them into a target, and `clinical_flags` still drives the relaxation ladder. `diet` is read by target derivation (DIAAS protein adjustment), not only by a future candidate filter. |
| `core/nutrition/`         | Partial — `citations.py` (Evidence with `phenomenon`, Constant registry now including the target-derivation constants: Mifflin-St Jeor, activity/PAL, protein g/kg, per-diet DIAAS, goal energy factors, macro AMDR, fibre, sodium — all `verified=False`), `target.py` (`NutritionTarget`, `simple_target`, `band`; moved here from `core/planner`), and `targets.py` (`derive_target`: Profile→BMR→TDEE→energy/protein/macros, DIAAS-adjusted protein, `dev_mode`-labelled, energy interval). **Nothing derived can ship as validated**, and — because activity/DIAAS/goal factors are `PROJECT_ESTIMATE`/`DECISION` — cannot even in principle until those are replaced, not merely opened; see `docs/methodology.md`. `clinical_flags` does NOT tighten any target value here (no cited clinical-sodium constant exists yet, and `core/nutrition` can't reach `core/planner`'s `LOCKED_CONSTRAINTS` to know what to tighten) — `derive_target` instead emits a mandatory warning when flags are set; see `docs/methodology.md`, "Clinical flags do not tighten a target." `meal_target.py` (new) splits a day-level target into one meal's share via the registered `meal_split.energy_fraction_*` constants, proportionally across every floor/ceiling/point — the one place `core/planner` and a day-level target's differing scales are reconciled, so `core/planner/plan.py` never compares a single plate against a whole day's energy floor. LLM ranking/narration not started. |
| `core/foods/`             | Built — models, templates, ifct_loader, recipe_loader, retention, portions, nutrition_of. Ingredient data is mostly a hand-entered fixture set, not IFCT (25 of 26 rows unverified; `water` is the exception) — updated 2026-07-24: four rows (`rice_milled_raw`/A015, `rajma_raw`/B020, `toor_dal_raw`/B021, `potato_raw`/F006) now carry real IFCT 2017 values but stay `verified=False` pending human sign-off; see `data/raw/ifct/README.md`. Composition uncertainty is modelled and process uncertainty is derived, not pasted — but **nothing can ship as validated**. The energy-reconciliation Atwater check now charges fibre separately (`atwater.fibre_kcal_per_g`, 2 kcal/g) rather than at the general carbohydrate rate — see `docs/methodology.md`, "Known limitations, Phase 1" item 3. `docs/audit_log.md` finding 2 (a recipe with no `process:` lines reads as 0% process-uncertain) is still OPEN; `core/planner/candidates.py` gates on the *combined* composition+process band, so today's real library is unaffected in practice — every ingredient's composition uncertainty is mandatory-per-macro and never zero — but finding 2 remains a real gap in `core/foods` and should be closed before a verified ingredient with an undeclared process is added. See `docs/methodology.md`. |
| `core/planner/`           | Partial — `candidates.py` (hard filters + the uncertainty eligibility filter, gating on the combined band per finding 1 below), `combinations.py` (enumeration, naive-bound logging, the O(1) feasibility pre-filter, the no-repeat variety filter), `solver.py` (exhaustive integer search with a shared point-vector cache, `swap_candidates`), `validator.py` (point-estimate gate, `RELAXATION_ORDER`, `LOCKED_CONSTRAINTS`, `plan_within_ladder`). The target shape moved OUT to `core/nutrition/target.py`; the planner imports `NutritionTarget`/`band` from there (downward). `docs/audit_log.md` finding 1 — "nothing in `core/` reads the eligibility ceiling" — is CLOSED by `candidates.py`; findings 13 and 14 (Phase 3 self-caught) are FIXED; findings 3–6 (interval edge cases in `nutrition_of.py`) remain OPEN. **`plan.py` (new) wires the whole pipeline end to end**: `load_library`/`default_library` load `data/raw/ifct` + `data/recipes` (once, cached), `plan_meal` picks a template via `template_for(region, meal_slot)`, splits the day target with `core.nutrition.meal_target`, and runs `build_candidate_pool` → `enumerate_combinations` → `plan_within_ladder`. Proven end to end against the real library — every one of the four real templates declines with a specific `no_candidates` violation, for every profile, because each of the three real recipes fills only one slot of one template and no other required slot in that template has any candidate at all (`docs/methodology.md`, limitation 5) — and, separately, against `tests/factories.py`'s richer synthetic library, where the identical wiring produces a passing plan, isolating "the wiring works" from "the data is thin." LLM ranking and narration are not started. |
| `core/commerce/`          | Not started                                                                                                                      |
| `api/`                    | Partial — thin FastAPI (`api/main.py`, `api/models.py`): `GET /api/health`, `GET /api/science` (live citation registry), `POST /api/targets` (Profile JSON → `derive_target`, returns targets + energy interval + provenance + `dev_mode` disclosure), and `POST /api/plan` (Profile + region + meal_slot → `core.planner.plan.plan_meal`, returns either a solved plate's components/unit-counts/point-estimate or an honest decline with `relaxation_applied` and a specific `disclosure`) — all four unauthenticated, unchanged by the accounts increment. New this session: `api/db.py` (SQLite via SQLAlchemy, `User`/`StoredProfile`), `api/auth.py` (bcrypt hashing, session helpers), and five auth/profile endpoints (`POST /api/auth/signup`\|`login`\|`logout`, `GET /api/auth/me`, `GET`/`PUT /api/profile`) behind a signed session cookie. Translates HTTP to core calls (or to `api/db.py`'s ORM) only; computes no nutritional number anywhere in this package. Against today's real `data/` library, `/api/plan` always declines (see `core/planner/`, `docs/methodology.md` limitation 5) — verified live in this session for all four templates. Run: `uvicorn api.main:app --reload`. |
| `web/`                    | Partial — static landing page (`web/index.html/styles.css/app.js`, a documented non-Next.js deviation; see `web/README.md`); `web/onboarding.html`/`onboarding.js`, a six-step wizard — steps 1-5 call the real `POST /api/targets`/`GET /api/science` and need no account, step 6 is the account/save hinge (`POST /api/auth/signup`\|`login`, `PUT /api/profile`); and `web/dashboard.html`/`dashboard.js` (new), auth-gated, owning the plate-picker + `POST /api/plan` call. `web/auth.js` is the session/auth-modal code shared by the latter two pages, and `web/header.js` (new, 2026-07-30) owns the header nav for all three routes in three explicit states (`anonymous`/`onboarding`/`authenticated`) — each page declares its state and writes no nav item, closing the case where a signed-in user mid-wizard had no way to reach Log out. Selected-state, chip fill and advancing-button geometry are each one definition now; see `DESIGN_SYSTEM.md`. No illustrative numbers anywhere outside the landing page's documented calculator-dock deviation. Verified against a live app in this session (signup, profile persistence across logout/login, dashboard auth gate — see the chat transcript for this build) before shipping, not merely written against the schema. |
| Audit workflow            | Partial — `docs/audit_log.md` exists. `.claude/agents/auditor.md` and `.claude/commands/grill.md` described in "Audit workflow" above **do not exist**; audits currently run via an ad-hoc read-only subagent. |

## Commands

```bash
python -m pytest tests/ -q          # run before trusting any status claim
uvicorn api.main:app --reload       # the targets API; POST /api/targets
ollama serve && ollama pull qwen2.5:7b-instruct
```

## Things that have gone wrong before

- Nested brace expansion in `mkdir -p a/{b/{c,d},e}` silently creates literal
  directories. Use separate `mkdir` calls.
- Stating a combination-space bound ("tens to low hundreds") without showing
  the arithmetic against actual filtered recipe counts. Show the math.
- Citing a real, findable, correctly-formatted source for the wrong physical
  process. Check `phenomenon` matches the application, not just that a DOI
  exists.
- Asserting the LLM "never produces a number" when its actual output included
  a portion multiplier. State precisely what it touches and doesn't.
- Claiming a durable artifact (test results, file existence) in a location
  that isn't actually the repo being discussed.
