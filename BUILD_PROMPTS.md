# Build prompts

Feed these to Claude Code **one at a time**, in order. Each phase ends with a
green, freshly-run test suite — check the actual terminal output before moving
on, and before writing any status claim in `CLAUDE.md`.

Keep `CLAUDE.md` in the repo root; it loads automatically and contains the
architecture invariants these prompts assume. If a phase's output seems to
drift from `CLAUDE.md`, stop and re-read it rather than proceeding.

---

## Phase 1 — Food data layer

> Build `core/foods/`. Read `CLAUDE.md` first, especially "Serving units,"
> "Meal templates," "Uncertainty," and "Evidence needs a phenomenon field."
>
> **`models.py`** — frozen dataclasses:
> - `Ingredient`: id, name_en, name_ta, name_hi, ifct_code, per-100g nutrients
>   (energy_kcal, protein_g, fat_g, carb_g, fibre_g, sodium_mg, iron_mg,
>   calcium_mg, b12_ug), `diaas: float | None`, `is_animal_product: bool`,
>   `jain_safe: bool`, `allergens: frozenset[str]`, `state: RawOrCooked`
> - `RecipeIngredient`: ingredient_id, quantity_g, state — **quantity_g is the
>   cooked/finished weight**, per `CLAUDE.md`'s raw-vs-cooked decision. If IFCT
>   only has a raw value, apply a yield factor and register it as a constant
>   in `citations.py` with a `phenomenon` field, not an inline multiplication.
> - `ServingUnit`: name (e.g. "idli", "dosa", "katori"), grams_per_unit,
>   min_count, default_count, max_count. Every recipe declares one. No
>   continuous multipliers anywhere in this module.
> - `Recipe`: id, name, region, diet_patterns satisfied, ingredients,
>   serving_unit, prep_minutes, tags, `process_uncertainty: dict[str, float]`
>   keyed by macro name (e.g. `{"energy_kcal": 0.15}` for a griddled item with
>   uncertain oil uptake) — this is what the eligibility filter in
>   `core/planner` will read later.
> - `Component`: wraps a Recipe with a category label used inside a
>   `MealTemplate` slot.
> - `MealTemplate`: keyed conceptually by (region, meal_slot), holds a named,
>   possibly variable-length, possibly-optional list of category slots. Do
>   NOT hardcode one 5-slot grammar for every meal — South breakfast, South
>   lunch, and North dinner have different shapes. Write at least three
>   distinct templates and show in a comment why they differ.
> - `NutritionVector`: summed nutrient totals; supports `+` and scalar `*`.
>
> **`ifct_loader.py`** — load ingredients from `data/raw/ifct/*.csv`. Validate
> on load: reject rows where macros are absent, and assert
> `protein*4 + fat*9 + carb*4` is within 15% of stated energy. Log every
> failing row rather than silently dropping it.
>
> **`retention.py`** — cooking yield and retention factors, each registered in
> `citations.py` with a `phenomenon` field stating exactly what process it
> describes. Do not borrow a citation from an adjacent-but-different cooking
> method (e.g. do not cite deep-fry oil absorption for a griddled item) — if
> no matching source exists, register the constant `verified=False` with an
> honest note and a wide uncertainty band instead.
>
> **`portions.py`** — household measure lookups (katori, cup, roti, dosa,
> idli, vada, ladle, tablespoon, piece) to grams, and back for display. This
> feeds `ServingUnit.grams_per_unit`, not a replacement for it.
>
> **`nutrition_of.py`** — public entry point. Given a Recipe and a unit count,
> return a `NutritionVector`. Given a list of (Component, unit_count), return
> the summed vector, using each recipe's `process_uncertainty` to also return
> an interval, not only a point estimate.
>
> **Also create** `data/recipes/schema.yaml` documenting the format, plus three
> hand-authored example recipes — one South Indian (sambar rice), one North
> Indian (rajma chawal), one breakfast (masala dosa) — with real IFCT-sourced
> cooked-weight quantities and a real `process_uncertainty` estimate for the
> dosa's oil uptake, marked `verified=False` if no matching primary source is
> found.
>
> **Do not:**
> - Scrape recipes from the web. Hand-author them.
> - Invent IFCT codes or nutrient values. Build the loader against a small
>   hand-entered fixture set and leave a TODO for the real ingest if the full
>   IFCT dataset isn't available yet.
> - Put a nutritional constant outside `citations.py`, including inside
>   `retention.py` or recipe YAML.
> - Use a continuous or five-point multiplier anywhere. Integer serving units
>   only.
>
> **Acceptance:** `pytest tests/ -q`, freshly run, output pasted in the same
> message as any status claim. Include a test that hand-computes the macros
> of the three example recipes and asserts the loader agrees, and a test that
> asserts no `Evidence` in the registry has a `phenomenon` mismatched against
> its usage (this can be a manual-review checklist test to start, not
> necessarily automated).

---

## Phase 2 — Combination enumeration and the solver

> Build `core/planner/candidates.py`, `core/planner/combinations.py`, and
> `core/planner/solver.py`. Read `CLAUDE.md` first, especially "What the LLM
> actually does" steps 1-4 and "Meal templates."
>
> **`candidates.py`** — deterministic pre-filter: diet pattern, allergens,
> region, meal template compatibility. Also apply the uncertainty eligibility
> filter here: exclude a recipe from a target-critical macro's candidate pool
> if its `process_uncertainty` for that macro exceeds a stated ceiling
> (default 0.15), or flag it for conservative (high-end) estimation instead of
> point-estimate use. This is a filter, not something the validator does later
> — per `CLAUDE.md`, uncertainty never gates, it makes recipes ineligible.
>
> **`combinations.py`** — for a given `MealTemplate`, enumerate distinct
> assignments of one Component per slot (respecting optional slots). Do not
> assume a uniform 5-slot count — iterate the template's actual slot list.
> Before returning results, print/log the actual count and compare it against
> a naive worst-case estimate in a comment, so the bound is demonstrated, not
> asserted. For a week-level plan, generate one day's combinations against
> its template and repeat with a no-repeat-within-N-days variety constraint —
> do not cross-product all 21 meal-slots against each other.
>
> Apply the cheap O(1) feasibility pre-filter before handing anything to the
> solver: sum each combination's components' declared serving-unit min/max
> contribution to each target macro, and discard combinations whose max can't
> reach the floor or whose min already exceeds the ceiling.
>
> **`solver.py`** — for each surviving combination, find the integer
> unit-count assignment (within each component's `min_count`/`max_count`)
> that minimizes weighted deviation from target. Use
> `scipy.optimize.linprog` with integer rounding, or a small integer/constraint
> solver (OR-Tools CP-SAT is a reasonable fit for small integer domains) —
> state which and why in a comment. Weight protein deviation heaviest, then
> energy, then fat/carb; expose weights as a named constant with the ordering
> justified in a comment.
>
> Also implement `swap_candidates(plan, slot, target, pool)` returning
> alternatives for one slot that keep the whole day valid, for the swap
> feature.
>
> **Do not** call an LLM from any of these three modules. Pure functions only.
>
> **Acceptance:** a test constructing profiles where the combination space is
> knowably large (log and assert the actual pre-filter survival count is
> smaller than the naive bound) and profiles where it's knowably thin (the 55
> kg vegetarian / 1500 kcal / 90g protein case from the audit) — assert the
> solver correctly reports zero feasible combinations there rather than
> forcing one. Plus a property test: for 200 randomly generated *moderate*
> profiles, at least one combination survives to a valid solve.

---

## Phase 3 — Validator and relaxation ladder

> Build `core/planner/validator.py`. Read `CLAUDE.md`'s "Uncertainty" and
> "Relaxation ladder" sections in full before writing anything — this module
> is where both of those design decisions actually get enforced.
>
> Given a solved plan (component + integer unit count per slot) and a
> `NutritionTarget`, return:
>
> ```python
> @dataclass(frozen=True)
> class ValidationResult:
>     passed: bool
>     actual_point_estimate: NutritionVector
>     actual_interval: tuple[NutritionVector, NutritionVector]  # low, high
>     violations: list[Violation]
>     relaxation_applied: list[str]   # which ladder steps fired, if any
>     disclosure: str | None          # mandatory, non-empty, if protein relaxed
> ```
>
> **Gate on `actual_point_estimate` against tolerance only.** Never gate on
> interval overlap — a plan is not more valid because its data is less
> certain. Compute and return the interval purely for display.
>
> Implement the relaxation ladder as an explicit, ordered, named constant
> (`RELAXATION_ORDER`), exactly as listed in `CLAUDE.md`: sodium/fibre first,
> then fat/carb tolerance, then energy tolerance, then protein tolerance last
> with mandatory disclosure. Before applying any relaxation step, check
> `profile.clinical_flags` — a constraint tied to a disclosed flag is removed
> from the ladder entirely for that profile and never relaxed. If the
> feasible set is still empty after exhausting all *unlocked* ladder steps,
> return `passed=False` with a violation naming the specific blocking
> constraint (which may be a locked one), not a generic failure.
>
> **Acceptance:** a test per violation type. A test that a locked clinical
> constraint is never relaxed even when relaxing it would make an otherwise-
> infeasible profile feasible. A test reproducing the audit's thin-
> feasible-set case (55kg / 1500kcal / 90g protein vegetarian) and asserting
> the disclosure string is non-empty and states the actual gap in the target's
> own units.

---

## Phase 4 — LLM ranking and narration

> Build `core/planner/llm.py`. Read `CLAUDE.md`'s "What the LLM actually does"
> in full — this is the phase most likely to accidentally reintroduce the
> defect the whole architecture was corrected to avoid.
>
> Input to the model: a list of already-solved, already-valid combinations
> (from Phase 2/3), each as an opaque ID plus a computed macro summary and
> dish names — never raw ingredient grams for the model to reason about, and
> never an invitation to propose a scaling factor for anything.
>
> Output schema — strictly this, nothing else:
>
> ```json
> {
>   "ranked_combination_ids": ["cmb_003", "cmb_017", "cmb_002"],
>   "narration": {
>     "cmb_003": {
>       "name": "Idli with sambar and coconut chutney",
>       "note_template": "Fermented batter aids digestibility; delivers a solid {protein_g}g of protein after training."
>     }
>   }
> }
> ```
>
> The model may only reference numeric values via named template slots
> (`{protein_g}`, `{energy_kcal}`, etc.) that the Python layer fills in from
> the already-validated plan. **After parsing, scan every `note_template` for
> a raw digit that isn't part of a recognized `{slot}` placeholder — reject
> and retry if found.** Do not rely on the prompt instruction alone; enforce
> mechanically.
>
> Malformed JSON or an unknown combination ID → retry with the parse error,
> max 3 attempts. If the model still can't produce valid output after 3
> attempts, fall back to: rank combinations by a simple deterministic proxy
> (e.g. closest point-estimate to target) and use a fixed narration template
> with no model-authored text at all. Mark the plan `llm_assisted=False`. The
> user always gets a plan; the LLM improves its presentation, it is never
> load-bearing for correctness — note that under this architecture, "the LLM
> fails" can only mean "produced bad prose," never "produced an invalid plan,"
> since it never touches quantities.
>
> **Instrument this.** Log parse failures, digit-in-narration rejections, and
> fallback rate across the benchmark run below. These numbers, not the
> architecture description, are the interesting artifact for a README.
>
> **Acceptance:** `scripts/benchmark_llm.py` running 200 generated profiles end
> to end, reporting narration rejection rate (digits caught), parse failure
> rate, and fallback rate. Commit the actual output, pasted, not summarized.

---

## Phase 5 — API

> Build `api/` with FastAPI. Thin — translates HTTP to `core` calls, no
> computation of its own. Read `CLAUDE.md` first.
>
> Endpoints:
> - `POST /profile` → validate, return computed targets, the full
>   `TargetExplanation` with citations (including each citation's
>   `phenomenon` field, for the `/science` page), and whether any
>   `clinical_flags` are set
> - `POST /plan` → generate a day or week plan; response includes the point
>   estimate, the interval, and `relaxation_applied`/`disclosure` if the
>   ladder fired
> - `POST /plan/{id}/swap`
> - `GET /recipes`, `GET /recipes/{id}` — include `process_uncertainty` and
>   `serving_unit` in the response
> - `GET /science` → full citation registry as JSON, `phenomenon` field
>   included per entry
> - `GET /delivery/serviceability?pincode=`
> - `POST /orders`, `GET /orders/{id}` — fixture-backed
>
> Persist plans with macros **frozen at generation time**, point estimate and
> interval both, plus whatever relaxation was applied. A later recipe edit
> must not silently change a previously generated plan or its disclosure.
>
> **Acceptance:** `httpx`-based tests, happy path plus one failure mode per
> endpoint.

---

## Phase 6 — Web

> Build `web/` with Next.js App Router, TypeScript, Tailwind. Read
> `CLAUDE.md`.
>
> Screens:
> 1. Onboarding — body, activity, goal, diet, **clinical flags (optional,
>    clearly explained as affecting which constraints can relax)**, target
>    review with a "why these numbers?" expander showing citations and their
>    `phenomenon` field.
> 2. Plan view — meal cards showing dish name, household portion (from
>    `ServingUnit`, e.g. "2 idlis," never a decimal multiplier), macros as
>    "≈X (±Y%)" where uncertainty is non-trivial, swap button.
> 3. Swap drawer.
> 4. `/science` — full citation registry, grouped, with DOI links and the
>    `phenomenon` each source actually measured made visible, not just its
>    summary. If a constant is `verified=False`, show that plainly.
> 5. Delivery flow — pincode check, tier, meal slots, duration, week preview,
>    mock checkout, clearly labeled as simulated fulfilment.
>
> If a plan's disclosure field is non-empty (protein relaxation, or a locked
> clinical constraint made it infeasible), surface that prominently on the
> plan view — not buried in a tooltip.
>
> Design direction: warm off-white base, deep charcoal text, turmeric amber
> accent, muted terracotta/sage regional tags, humanist serif for dish names,
> clean sans for numbers. Avoid dark-UI-neon-green fitness aesthetics. Mobile
> first.
>
> The frontend never computes a macro or a portion. It displays what the API
> returns, including the interval and any disclosure text verbatim.
>
> **Acceptance:** full flow works against a locally running API.

---

## Phase 7 — Commerce and polish

> Build `core/commerce/` (thin: `zones.py` hardcoded Chennai pincodes,
> `plans.py`, `orders.py` with pause/resume) and finish the project.
>
> - README with the Phase 4 benchmark numbers stated plainly, pasted, not
>   paraphrased.
> - `docs/methodology.md` updated with every limitation found during the
>   build, including the raw-vs-cooked decision, the DIAAS framing, the
>   `phenomenon`-matching rule, and the clinical-flags scope statement.
> - A short screen recording in the README.
> - Dockerfile / `docker-compose.yml` for api + ollama.
> - Re-run `unverified()` and confirm the report is still honest; do not flip
>   any flag without having personally opened the source document.

---

## Appendix — reusable context blocks

**When Claude Code proposes an LLM-computed quantity:**

> Stop. Read `CLAUDE.md`'s "Central invariant" section again. The LLM ranks
> among already-solved combinations and fills narration templates — it does
> not propose a gram value, a multiplier, or a serving count under any
> framing, including "the solver will check it afterward."

**When it wants to add a nutritional constant, including in a data file:**

> Register an `Evidence` object in `citations.py` with a real citation, DOI
> if one exists, and a `phenomenon` field describing precisely what process
> was measured. Check the phenomenon matches where the constant is applied —
> a real citation for an adjacent-but-different process is worse than an
> absent one. If no matching source exists, mark `verified=False` honestly
> rather than attaching a plausible-but-wrong citation.

**When it asserts a combination count, latency figure, or test result:**

> Show the arithmetic or paste the command output in the same message. A
> claim about the system's own behavior needs the artifact attached, not a
> reference to having checked it earlier.

**When a test is snapshot-shaped:**

> Rewrite to assert a hand-computed expected value, arithmetic shown in a
> comment.

**When scope creeps:**

> Portfolio project, not a business. Kitchen operations, payments, routing,
> inventory: out of scope, simulate against fixtures.
