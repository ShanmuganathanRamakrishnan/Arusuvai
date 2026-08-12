# Architecture

Moved out of `CLAUDE.md` on 2026-08-12. The *rules* stayed in the root file;
this is the shape and the reasoning, which a session can also reconstruct by
reading `core/`.

Read this when you are adding a stage to the pipeline, adding a meal template,
or deciding which package something belongs in.

**Two claims were corrected in the move rather than carried across** — both
marked below. See "Corrections applied on the move" at the end.

## The pipeline

1. Deterministic candidate filter (diet, allergen, region, meal template).
2. Deterministic **enumeration of distinct recipe combinations** per meal
   template — combinations, not portions yet.
3. Cheap O(1) feasibility pre-filter per combination: sum each component's
   declared min/max contribution to each target macro, discard combinations
   that cannot reach the floor or must exceed the ceiling, before running a
   full solve on anything.
4. Solver runs only on combinations that survive the pre-filter, finding an
   integer-unit portion assignment per surviving combination, or discarding it
   as infeasible.
5. **(Not built as of 2026-08-12.)** LLM ranks/selects among the surviving,
   already-valid combinations for palatability and variety against recent
   history. It receives combinations as opaque IDs with computed macro
   summaries — never raw grams to reason about, never an invitation to propose
   a scaling factor.
6. **(Not built as of 2026-08-12.)** LLM writes narration using a template with
   named numeric slots (`"{dish_name} delivers a solid {protein_g}g of
   protein"`), where the Python layer substitutes `{protein_g}` from the
   validated plan. The model supplies only the surrounding language. Any raw
   digit in a model-authored field that is not a recognized slot placeholder is
   stripped and the response rejected — check this mechanically, do not rely on
   the model following the instruction unsupervised.

Steps 1–4 are wired end to end in `core/planner/plan.py` and proven against the
real library. Steps 5 and 6 are specification, not code.

## Why the LLM does not propose portions

The rejected alternative is "the LLM proposes portions, a solver checks them."
That shape has a real, examined failure mode: on final rejection after N
retries, what does the user see? Answering that honestly is only tractable
because this architecture moves portion determination to the solver entirely,
so the LLM cannot produce an invalid plan in the first place.

If you find yourself building a retry loop around LLM-proposed quantities, stop
— you have rebuilt the shape that was rejected.

What the LLM is for: a solver can enumerate every numerically feasible
combination; what it cannot do is know that sambar + curd rice + more sambar is
not a plate anyone in Chennai would eat. That is the job — cultural and
palatability ranking over an already-valid set, plus the human-facing
description. Nothing else.

## Serving units, not continuous multipliers

Portion space is not continuous in reality: 1.25 × one idli is 3.75 idlis,
which is not servable. Every recipe declares:

```
unit: str            # "idli", "dosa", "katori", "roti", "50g_scoop", ...
min_count: int
default_count: int
max_count: int
```

The solver optimizes over **integer unit counts**. A five-point multiplier
(0.5/0.75/1.0/1.25/1.5) is not an acceptable substitute — it produces the same
unservable fractional output, discretized to look tidier.

See also `docs/methodology.md`, "Serving units, not multipliers".

## Meal templates — the slot grammar is not uniform

Do not assume a fixed 5-slot grammar (base/protein/curry/vegetable/
accompaniment) applies to every meal. It does not: South Indian breakfast
(idli + sambar + chutney) has no separate vegetable slot and no base/curry
split; South lunch (rice + sambar + poriyal + curd) has a different shape
again; North dinner (roti + dal + sabzi) has no rice slot.

`MealTemplate` is keyed by `(region, meal_slot)`, each with its own named,
possibly variable-length, possibly-optional slot list. It is a data structure in
`core/foods/templates.py`, not an assumption baked into the solver.

**Combination arithmetic must be shown, not asserted.** Do not write "the
combination space is bounded" without computing it against the actual
post-filter recipe counts for the template in question. For a whole week, do not
cross-product all 21 meal-slots against each other — generate a single day's
combinations against its template, then repeat with a no-repeat variety
constraint across the week. If you assert a bound, show the arithmetic that
produced it in a comment.

## Package layout

```
core/                  Pure logic. No web framework, no I/O beyond file loading.
  schemas/             Dataclasses shared everywhere. No dependencies on siblings.
                       Profile.clinical_flags lives here.
  nutrition/           Targets from profile. Depends only on schemas.
                       citations.py: Evidence carries `phenomenon`.
  foods/               Ingredients, recipes, components, MealTemplate, portions
                       (serving units, not multipliers). Depends on schemas.
  planner/             candidates -> combination enumeration -> feasibility
                       pre-filter -> solver (integer unit counts) -> LLM
                       ranking/narration (not built) -> validator (point-estimate
                       gate, relaxation ladder). Depends on all above.
  commerce/            Plans, orders, zones. Seeded fixtures only. Not started.
api/                   FastAPI. Thin. Translates HTTP to core calls.
                       api/db.py: SQLite via SQLAlchemy — User + StoredProfile
                       only (accounts + profile persistence). No nutritional
                       computation happens here either; it stores the same
                       fields core.schemas.Profile validates.
web/                   Static HTML/CSS/JS. Displays. Never computes nutrition.
data/                  IFCT subset, recipe YAML (cooked weights), fixtures.
tests/
docs/
```

Dependency direction is strictly downward. `core/nutrition` must never import
from `core/planner`.

## Conventions that are not project-specific

Types: `from __future__ import annotations`, frozen dataclasses across module
boundaries, full annotations on public functions.

Errors: raise on impossible input; warn on implausible-but-valid input via a
`warnings: list[str]` field — never silently clamp without recording it.

Comments: explain *why* a choice was made over its alternatives, not what the
line below already says.

## Corrections applied on the move (2026-08-12)

Per the restructure rule that nothing moves verbatim without being read against
the current audit log first:

1. **`web/` was described as "Next.js".** It is not and never has been in this
   repo — `web/` is static HTML/CSS/JS, a deliberate deviation documented in
   `web/README.md`. The root `CLAUDE.md` carried the false line in its
   architecture tree while the build-status table two sections below described
   the real thing. Corrected here rather than transcribed.
2. **Pipeline steps 5 and 6 read as descriptions of built behaviour.** They are
   specification. LLM ranking and narration are not started; the build-status
   table has said so continuously. Marked as not-built rather than left to read
   as current.
