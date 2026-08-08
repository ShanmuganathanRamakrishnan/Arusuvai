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
| `core/schemas/`           | Partial — `common.py` (RawOrCooked, Region, MealSlot, DietPattern, MACRO_KEYS), `profile.py` (`Profile`, `ClinicalFlag`, `ActivityLevel`, `Goal`, `Sex`) and `day_ledger.py` (new 2026-08-02: `DayLedger`, per-slot contributions as `{macro: float}` maps — not `NutritionVector`, which lives in `core/foods` and would be a sibling dependency; `with_meal` replaces by slot so re-planning debits before it credits; points gate, intervals are display-only and a perturbation test proves they cannot reach the budget). `Profile` now carries `diet: DietPattern` and its body fields ARE read: `core/nutrition/targets.py` turns them into a target, and `clinical_flags` still drives the relaxation ladder. `diet` is read by target derivation (DIAAS protein adjustment), not only by a future candidate filter. |
| `core/nutrition/`         | Partial — `citations.py` (Evidence with `phenomenon` and `display_ref`, `RENDERED_FIELDS` + slot-resolving `register_evidence` — a raw evidence id written into a reader-facing field now fails registration rather than reaching the citation panel; Constant registry now including the target-derivation constants: Mifflin-St Jeor, activity/PAL, protein g/kg, per-diet DIAAS, goal energy factors, macro AMDR, fibre, sodium — all `verified=False`), `target.py` (`NutritionTarget`, `simple_target`, `band`; moved here from `core/planner`), and `targets.py` (`derive_target`: Profile→BMR→TDEE→energy/protein/macros, `dev_mode`-labelled, energy interval). **Slice 2 landed 2026-08-02: DIAAS no longer inflates the protein target.** The floor is `ProteinTarget.base_g`; `quality_adjusted_g` is computed and displayed but nothing gates on it, because answering a protein-*quality* problem with more grams of the same limiting-amino-acid profile supplies more of what was already there. Measured, reference profile, all four predicted before the change and all four held: protein day floor 124.4→112.00, carb day 341.6→354.01, lunch protein floor 43.6→39.20, lunch carb ceiling 137.5→142.49. The carb rise is a side effect nobody asked for — `_compute_macros` derives carb as the energy remainder — and carb is now diet-independent as a result. **`Profile.diet` currently changes no target value at all** until the quality-source rule (slice 4) lands; see `docs/methodology.md`, "Protein quality no longer inflates the target". **Nothing derived can ship as validated**, and — because activity/DIAAS/goal factors are `PROJECT_ESTIMATE`/`DECISION` — cannot even in principle until those are replaced, not merely opened; see `docs/methodology.md`. `clinical_flags` does NOT tighten any target value here (no cited clinical-sodium constant exists yet, and `core/nutrition` can't reach `core/planner`'s `LOCKED_CONSTRAINTS` to know what to tighten) — `derive_target` instead emits a mandatory warning when flags are set; see `docs/methodology.md`, "Clinical flags do not tighten a target." **Slice 4 landed 2026-08-07: protein quality came back as a source rule, not a multiplier.** `protein.quality_diaas_threshold` 0.75, `protein.quality_day_fraction` 0.33 and `protein.quality_meal_floor_fraction` 0.10, all `PROJECT_DECISION`. `meal_target` sets `NutritionTarget.quality_protein_floor_g` = 0.10 x day protein floor = 11.2 g for the reference profile, **flat on every slot** (not scaled by the energy share — quality protein has no day-level share to guard beneath). The day floor 0.33 x 112.0 = 36.96 g sits on `ProteinTarget.quality_source_day_g` and **gates on nothing**: a day floor is a reachability question, not a subtraction. **`Profile.diet` still changes no target number** and that is now the settled position — the threshold is a property of a food and the fraction comes off a diet-independent floor; what diet changes is which components can satisfy an identical floor, to the point of flipping a verdict (vegan declines where vegetarian passes once `soya_chunks_dry` is disqualified). No rung in `RELAXATION_ORDER` touches the quality floor: it is a composition rule, not a tolerance, so there is no looser version of it. See `docs/methodology.md`, "Protein quality is a rule about sources", for the harshness this rule has toward mixed grain-plus-legume Indian plates specifically, which is stated and not softened. `meal_target.py` splits a day-level target into one meal's share via the registered `meal_split.energy_fraction_*` constants, proportionally across every floor/ceiling/point **except sodium and protein**. Protein (slice 3, 2026-08-02) gets two `PROJECT_DECISION` fractions of the DAY FLOOR: `protein.meal_floor_fraction` 0.15 applied as `max(share, guard)` — a guard beneath the share, not a replacement, since the design's literal reading would have dropped the reference lunch floor 39.2 → 16.8 g; it binds on the snack slot alone. And `protein.meal_ceiling_fraction` 0.50, the first protein ceiling anywhere in the system, which the solver cannot reach by its own scoring (the protein point sits below it for every slot) and which therefore binds only when an energy floor drags protein up — the three-katoris-of-dal case. Not a `hard_ceiling`: nothing in `RELAXATION_ORDER` touches a protein ceiling, so the machinery would have no mechanism behind it. No verdict moved on the real library. `docs/audit_log.md` finding 24: when the ceiling empties the feasible set the decline names energy, not protein. Sodium — updated 2026-08-02: `sodium_mg` is now a day budget (`min(2000 - spent_by_other_meals, day_budget.absurdity_fraction x 2000)`), because 2000 x 0.35 = 700 mg was a daily population guideline apportioned by calories and is not a figure any guideline states. The 0.70 guard is a `PROJECT_DECISION` plausibility limit, registered as a `NutritionTarget.hard_ceiling` so no relaxation rung may widen past it — a widenable guard was measured to permit one plate carrying 105% of a day's sodium. Fibre stays proportional (its target already derives from energy); iron/calcium/B12 are not budgeted because they have no target at all. See `docs/methodology.md`, "Sodium is a day budget", for the three stated limitations including that a single-meal user is served worse than before. — the one place `core/planner` and a day-level target's differing scales are reconciled, so `core/planner/plan.py` never compares a single plate against a whole day's energy floor. LLM ranking/narration not started. |
| `core/foods/`             | Built — `quality.py` new 2026-08-07 (slice 4): `ingredient_qualifies`, `quality_protein_of_recipe`/`_of_components`. `quality_protein_g` is deliberately **not** a macro — absent from `MACRO_KEYS` and `NutritionVector`, because nothing measures it and putting it in the vector would make every `MACRO_KEYS` loop claim to know something about it. Aggregation is per qualifying ingredient **line**, the conservative arm of the mixture question `docs/design/target_model_v2.md` §3 left open: it credits a roti-and-dal plate for neither part, so it understates exactly the food this product plans. `diaas is None` means "does not qualify" — 17 of 29 rows — so a protein-dense row added without a DIAAS silently counts for nothing. — `templates.py` updated 2026-08-02 (D2b-i): `SOUTH_BREAKFAST` gains an **optional** `curd_course` (`curd`/`buttermilk`, filled by the existing `thayir_plain@curd`), closing `docs/audit_log.md` finding 25 — its four original slots could accept no high-quality protein source at all, so a per-meal quality floor would have made the template structurally unsatisfiable. Optional, not required like `SOUTH_LUNCH.curd_course`: a curd-less breakfast must still enumerate, and does (2 combinations, one each way). — models, templates, ifct_loader, recipe_loader, retention, portions, nutrition_of. Ingredient data is mostly a hand-entered fixture set, not IFCT (28 of 29 rows unverified; `water` is the exception) — updated 2026-08-02 (D2a): `paneer_fresh`, `tofu_firm` and `soya_chunks_dry` added so the quality-source rule has something to select, their DIAAS figures **authored at the low end of a recalled range, not sourced**; see `docs/methodology.md`, "DIAAS values are authored, and the quality rule turns on them" — updated 2026-07-24: four rows (`rice_milled_raw`/A015, `rajma_raw`/B020, `toor_dal_raw`/B021, `potato_raw`/F006) now carry real IFCT 2017 values but stay `verified=False` pending human sign-off; see `data/raw/ifct/README.md`. Updated 2026-08-07 (D3): three recipes — `idli` (`tiffin`), `steamed_rice` (`rice`) and `soya_kuzhambu` (`kuzhambu`) — make both south templates reachable, with **no new ingredient row and no new authored DIAAS**. Two of the three exist for SODIUM, not protein: the quality shortfall was 2.21 g, but neither south template could reach its energy floor under the 1400 mg `hard_ceiling`. `idli` is 1.73 mg Na/kcal against masala dosa's 2.62 and is near fat-free; `steamed_rice` is 0.008 mg Na/kcal because plain rice takes no salt. `soya_kuzhambu` is the qualifying source (13.00 g/katori) and is deliberately NOT `soya_chunk_curry` relabelled — tamarind, sambar powder, gingelly oil, mustard-and-curry-leaf tempering; see the file header and `docs/methodology.md`, "Making the south templates reachable". `idli` is the first recipe in the library with `min_count > 1`, which surfaced `docs/audit_log.md` finding 27 in `core/planner/candidates.py` (FIXED). Composition uncertainty is modelled and process uncertainty is derived, not pasted — but **nothing can ship as validated**. The energy-reconciliation Atwater check now charges fibre separately (`atwater.fibre_kcal_per_g`, 2 kcal/g) rather than at the general carbohydrate rate — see `docs/methodology.md`, "Known limitations, Phase 1" item 3. `docs/audit_log.md` finding 2 (a recipe with no `process:` lines reads as 0% process-uncertain) is still OPEN; `core/planner/candidates.py` gates on the *combined* composition+process band, so today's real library is unaffected in practice — every ingredient's composition uncertainty is mandatory-per-macro and never zero — but finding 2 remains a real gap in `core/foods` and should be closed before a verified ingredient with an undeclared process is added. See `docs/methodology.md`. |
| `core/planner/`           | Updated 2026-08-08 (D4a): **`docs/audit_log.md` finding 24 is CLOSED.** `_blocking_violations` no longer stops at the first cause — the structurally-unreachable bounds and the nearest-to-feasible plate's misses are both computed and merged, keyed by `(macro, kind)`. "Nearest" is now **fewest bounds broken**, tie-broken by score, because the solver's deviation score measures distance from each macro's ideal *point* and neither sodium nor fibre has one, so a plate's saltiness contributed nothing to the ranking that chose which plate a decline described. Measured over 144 profiles x 4 templates (`docs/design/probes/d4_declines.py`): declines omitting a real cause 12 -> 0, declines naming a bound the nearest plate meets 30 -> 0, empty-pool declines naming no slot 72 -> 0, verdicts unchanged at 156. `Violation` carries `reach` (`VIOLATION_REACH`) and `relaxability` (`VIOLATION_RELAXABILITY`) — token vocabularies in `BOUND_SOURCES`' style, validated at construction, never rendered raw — plus `blocking_slots`, sourced from `combinations.unfillable_slots`, which calls the enumerator's own `_slot_selections` rather than asking whether a slot has candidates (a slot with two candidates and `min_selections=3` has both candidates and no legal selection). `relaxability` is derived from `RELAXATION_ORDER` itself, not a table. Finding 30 FIXED here: `Violation.describe` was interpolating `ClinicalFlag.value` — `chronic_kidney_disease` — into the sentence `web/dashboard.js` renders, and `tests/test_planner_validator.py` asserted the leak. Finding 31 (macro identifiers in the same prose) is OPEN and deferred to D9. — Partial — `candidates.py` (hard filters + the uncertainty eligibility filter, gating on the combined band per finding 1 below; `for_slot` returns candidates **sorted by component id** — `accepted_categories` is a frozenset and iterating it directly made enumeration order, and every `demo.py` transcript, depend on `PYTHONHASHSEED`. `docs/audit_log.md` finding 18, CLOSED 2026-08-02; verified byte-stable across 12 seeds, with plate/score/verdict unchanged), `combinations.py` (enumeration, naive-bound logging, the O(1) feasibility pre-filter, the no-repeat variety filter), `solver.py` (exhaustive integer search with a shared point-vector cache, `swap_candidates`), `validator.py` (point-estimate gate, `RELAXATION_ORDER`, `LOCKED_CONSTRAINTS`, `plan_within_ladder`). The target shape moved OUT to `core/nutrition/target.py`; the planner imports `NutritionTarget`/`band` from there (downward). `docs/audit_log.md` finding 1 — "nothing in `core/` reads the eligibility ceiling" — is CLOSED by `candidates.py`; findings 13 and 14 (Phase 3 self-caught) are FIXED; findings 3–6 (interval edge cases in `nutrition_of.py`) remain OPEN. **`plan.py` (new) wires the whole pipeline end to end**: `load_library`/`default_library` load `data/raw/ifct` + `data/recipes` (once, cached), `plan_meal` picks a template via `template_for(region, meal_slot)`, splits the day target with `core.nutrition.meal_target`, and runs `build_candidate_pool` → `enumerate_combinations` → `plan_within_ladder`. Proven end to end against the real library. Updated 2026-08-02 (T4): six recipes filled every previously-empty required slot, so `no_candidates` no longer appears for any template (`docs/methodology.md` limitation 5, CLOSED) — combinations enumerated are south_breakfast 1, south_lunch 3, north_lunch 8, north_dinner 2. All four still decline for the reference profile, but on **named macros** with a walked ladder, and north_lunch/north_dinner solve for other profiles (54 and 28 of a 192-profile sweep). Updated 2026-08-07 (slice 4): the quality-source floor is gated in three places — `combinations.feasible_combinations` (an O(1) pre-filter, and a **pure optimisation**: removing it changes no verdict), `solver._within_target_point` (the real gate; `SolvedPlan.quality_protein_g` carries the figure to the validator, which has no ingredient table to recompute it from), and `validator._blocking_violations` (so an unreachable floor is named). Enumeration counts are unchanged. Both north templates still pass with zero rungs but on **different plates** — north_lunch phulka x5 + soya_chunk_curry x1 + paneer_masala x1, north_dinner phulka x3 + soya_chunk_curry x1 + aloo_sabzi x1 + onion_raita x2 — because `tofu_bhurji` contributes zero qualifying protein at an authored DIAAS of 0.65. north_dinner's sodium rose 889.2 -> 1371.3 mg against the 1400 mg guard: denser protein carries salt. Both south templates now decline **on quality** (8.99 g reachable against 11.2 g, `thayir_plain` capped at two katoris) rather than on energy/fat/sodium, and `docs/audit_log.md` 2026-08-07 records that the new decline says less than the old one did — OPEN, finding-24-shaped, not fixed. Updated 2026-08-07 (D3): **all four templates now pass for the reference profile** — south_breakfast at 0 rungs (idli x6 + soya_kuzhambu x1 + coconut_chutney x2 + thayir_plain x1, 623.6 kcal, 1189.8 mg Na, 17.5 g qualifying), south_lunch at 3 rungs (steamed_rice x1 + soya_kuzhambu x2 + carrot_poriyal x2 + thayir_plain x1, 848.1 kcal, **1391.1 mg Na against the 1400 mg guard — 8.9 mg of headroom**). Enumeration south_breakfast 2->8, south_lunch 3->12; both north plates byte-identical and 24/12 unchanged, which they could not fail to be — `candidates.py` rejects a recipe whose region is neither the template's nor `pan_indian`. south_lunch needs three rungs for SODIUM, not quality: clearing the 39.2 g protein floor forces two katoris of kuzhambu (647.0 mg) plus a required curd course (261.9) and a required vegetable (240-395), leaving only unsalted rice able to fit the base; energy tolerance is the rung that admits 848.1 kcal against an unrelaxed 854.9 floor. `candidates._eligibility_flags` now prices a candidate at its `min_count` rather than a hard-coded 1 (`docs/audit_log.md` finding 27, FIXED — the old literal crashed on the first recipe with a floor above 1). The finding-24-shaped decline observation above is still OPEN; it is a property of `_blocking_violations`, not of the south templates, which no longer decline. Updated 2026-08-02 (D2a): with `paneer_masala`, `tofu_bhurji` and `soya_chunk_curry` added, enumeration is south_breakfast 1, south_lunch 3, north_lunch 24, north_dinner 12, and **both north templates now pass for the reference profile with zero relaxation rungs** — the sabzi slot can be filled with less sodium per calorie than aloo sabzi allowed. The two south templates still decline; finding 22 is untouched. Sodium blocks all four; two south_lunch combinations are above the 1400 mg guard at their *minimum* counts, so no profile can reach them — `docs/audit_log.md` finding 22, OPEN. And, separately, against `tests/factories.py`'s richer synthetic library, where the identical wiring produces a passing plan, isolating "the wiring works" from "the data is thin." LLM ranking and narration are not started. |
| `core/commerce/`          | Not started                                                                                                                      |
| `api/`                    | Updated 2026-08-08 (D4a): `ViolationOut` gains `reach`, `relaxability`, `blocking_slots` and `locked_by` — the structure a decline screen needs, as stable tokens a client maps to its own copy. Still no nutritional computation here. — Partial — thin FastAPI (`api/main.py`, `api/models.py`): `GET /api/health`, `GET /api/science` (live citation registry), `POST /api/targets` (Profile JSON → `derive_target`, returns targets + energy interval + provenance + `dev_mode` disclosure), and `POST /api/plan` (Profile + region + meal_slot → `core.planner.plan.plan_meal`, returns either a solved plate's components/unit-counts/point-estimate or an honest decline with `relaxation_applied` and a specific `disclosure`) — all four unauthenticated, unchanged by the accounts increment. New this session: `api/db.py` (SQLite via SQLAlchemy, `User`/`StoredProfile`), `api/auth.py` (bcrypt hashing, session helpers), and five auth/profile endpoints (`POST /api/auth/signup`\|`login`\|`logout`, `GET /api/auth/me`, `GET`/`PUT /api/profile`) behind a signed session cookie. Translates HTTP to core calls (or to `api/db.py`'s ORM) only; computes no nutritional number anywhere in this package. Against today's real `data/` library `/api/plan` declines for the reference profile on all four templates, but now names the blocking macro rather than reporting an empty pool, and returns a real plate for other profiles on north_lunch and north_dinner (see `core/planner/`, `docs/methodology.md` limitation 5, CLOSED 2026-08-02). Updated 2026-08-07 (D3): against today's real library `/api/plan` now returns a **real plate on all four** region/slot pairs for the reference profile — south_breakfast and both north templates unrelaxed, south_lunch with three rungs reported in `relaxation_applied`. The decline path is unchanged and still exercised by other profiles. Updated 2026-08-07 (slice 4): `ProteinOut` gains `quality_source_day_g` (displayed, gates on nothing) and `web/onboarding.js`'s protein line no longer ends at "protein quality is not applied to this target" — true of the target, and misleading from the moment quality started deciding which dishes a plan may contain. Run: `uvicorn api.main:app --reload`. |
| `web/`                    | Partial — static landing page (`web/index.html/styles.css/app.js`, a documented non-Next.js deviation; see `web/README.md`); `web/onboarding.html`/`onboarding.js`, a six-step wizard — steps 1-5 call the real `POST /api/targets`/`GET /api/science` and need no account, step 6 is the account/save hinge (`POST /api/auth/signup`\|`login`, `PUT /api/profile`); and `web/dashboard.html`/`dashboard.js` (new), auth-gated, owning the plate-picker + `POST /api/plan` call. `web/auth.js` is the session/auth-modal code shared by the latter two pages, and `web/header.js` (new, 2026-07-30) owns the header nav for all three routes in three explicit states (`anonymous`/`onboarding`/`authenticated`) — each page declares its state and writes no nav item, closing the case where a signed-in user mid-wizard had no way to reach Log out. Selected-state, chip fill and advancing-button geometry are each one definition now; see `DESIGN_SYSTEM.md`. P0 closeout 2026-07-30: the identifier-in-copy class is now caught by DETECTION rather than by another label map — `tests/test_web_no_identifiers.py` sweeps every visible text node across all nine views for `snake_case`/`SCREAMING_CASE` and fails on any, allowlist empty; proven by restoring a previous leak and watching it fail. Three further raw-value fallbacks in `dashboard.js` were found by that rule and fixed. Evidence grade falls through to `Ungraded`, never to prettified prose. The onboarding brand is a link — the only exit from a wizard that deliberately renders no nav. No illustrative numbers anywhere outside the landing page's documented calculator-dock deviation. Verified against a live app in this session (signup, profile persistence across logout/login, dashboard auth gate — see the chat transcript for this build) before shipping, not merely written against the schema. P2 landing closeout 2026-07-30: the hero's placeholder copy is gone; `--kolam-opacity` is one token for all three routes (the landing breath is now a 0..1 envelope multiplying it, and the two reduced-motion overrides are removed) — the same element used to render three times stronger on the landing page than in the app; the script cycler's language label is anchored to the word's box (`align-items: flex-end`) instead of a per-font baseline, so it holds position across Tamil/Telugu/Kannada/Malayalam; and the calculator rail is in the layout system via `--calc-panel-w` with anchoring defined at the same 1100px `.ob-grid12` collapses at. `DESIGN_SYSTEM.md` known-inconsistency 0 is CLOSED, and its reading corrected: it was measuring the drawer CLOSED, where the card is clipped by its own 0px panel by design; the real gap was the OPEN state below ~372px. All four pinned by browser measurement in `tests/test_web_landing_geometry.py` (new) and `tests/test_web_wizard_layout.py`, each shown to fail on the restored defect. The plate picker's empty region needed no change: `POST /api/plan` renders its result into that space on the same route (measured — decline section at y=375 where content previously ended at y=322). |
| Audit workflow            | Partial — `docs/audit_log.md` exists. `.claude/agents/auditor.md` and `.claude/commands/grill.md` described in "Audit workflow" above **do not exist**; audits currently run via an ad-hoc read-only subagent. |

## Commands

```bash
python -m pytest tests/ -q          # run before trusting any status claim
python demo.py                      # reproduce the evidence: library, slot
                                    #   coverage, enumeration, plan_meal
python demo.py plan --region north_indian --meal-slot lunch --weight-kg 70
python demo.py --help               # profile and template are flags, not edits
uvicorn api.main:app --reload       # the targets API; POST /api/targets
ollama serve && ollama pull qwen2.5:7b-instruct
```

`demo.py` is the tracked entry point for every transcript in
`docs/audit_log.md`. Before pasting a result anywhere, regenerate it with a
command in this block — a finding that only a scratch script can produce is
exactly the unverifiable claim about the project's own state that the process
rule above forbids. It prints the **unrelaxed** target and the target the
ladder **stopped on**, separately labelled; reading one for the other caused a
miscalibrated prediction once already.

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
- **Writing a reproducibility check that reproduces itself.** Twice now: a
  transcript proving a transcript exists (finding 11), and a byte-diff run
  twice in one shell under one hash seed (finding 18). Both satisfied the rule
  and missed its purpose. A determinism or reproducibility claim has to be
  checked *across the axis it claims independence from* — a different process,
  a different machine — not by repeating the same run.
- **Writing a before/after probe that can only run on the "after" tree.** A
  probe measuring what a change improved must run on both sides of that change,
  so it must read only fields present in both — check that when writing it, not
  when someone asks. `d4_declines.py` read a field D4a introduced, so the
  before column in the 2026-08-08 audit entry was real when taken and
  unmeasurable an hour later. Same family as the two entries below: a claim
  about the repo's own state, satisfying the rule's letter, unverifiable in
  practice.
- Writing a test that cannot fail on the defect it names. Inject the defect and
  watch it go red before believing it. Finding 18's first three tests all
  passed against the defect: one exercised a slot with candidates in only one
  category (so the permutation was a no-op), and another compared unsorted
  order against sorted order, which coincide under many hash seeds.
