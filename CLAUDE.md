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
plan is assembled**: a recipe whose process uncertainty on a given macro
exceeds a stated ceiling (default ±15% on protein, wider tolerance on energy)
is excluded from candidate pools where that macro is target-critical, or its
contribution to that macro is estimated conservatively (high-end, not
optimistic) rather than at the point estimate. Uncertain data makes a recipe
less usable, never makes a plan easier to pass.

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
   nutritional claim.
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

## Build status

Only update this table with a command transcript in the same message.

Corrected 2026-07-21 during the Phase 1 build: the two rows previously marked
"Built" described files that did not exist in this repo. That is exactly the
failure mode the process rule above names — a status claim with no artifact
behind it — so the table now records what `git`-less inspection of the working
tree and a fresh `pytest` run actually show.

| Module                    | State                                                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `core/schemas/`           | Partial — `common.py` (RawOrCooked, Region, MealSlot, DietPattern, MACRO_KEYS). `profile.py` does not exist; `clinical_flags` still to come. |
| `core/nutrition/`         | Partial — `citations.py` only (Evidence with `phenomenon`, Constant registry, mechanism-review checklist, rejected-citation record). Energy, protein, macros and targets are not built. |
| `core/foods/`             | Built — models, templates, ifct_loader, recipe_loader, retention, portions, nutrition_of. 110 tests pass (`python -m pytest tests/ -q` -> `110 passed in 0.15s`, at commit `9b93d22`). Ingredient data is a hand-entered fixture set, not IFCT; see `data/raw/ifct/README.md`. Displayed uncertainty bands are known to be understated — composition uncertainty is not modelled; see the audit defects recorded in commit `fc20fe5`. |
| `core/planner/`           | Not started — candidates, combination enumeration, feasibility pre-filter, solver, LLM ranking, validator with relaxation ladder |
| `core/commerce/`          | Not started                                                                                                                      |
| `api/`, `web/`            | Not started                                                                                                                      |

## Commands

```bash
python -m pytest tests/ -q          # run before trusting any status claim
python demo.py
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
