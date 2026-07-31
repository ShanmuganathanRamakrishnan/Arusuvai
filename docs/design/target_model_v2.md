# Target model v2 — design

**Status: design only. Dated 2026-07-31. Nothing in `core/` implements any of
this.** The only code/data changes made alongside this document are the two
authorised in its commissioning task (`salt_iodised`'s stored value, and the
target labelling in the scratch walkthrough script); neither depends on
anything below.

## Why

Two defects, established by measurement, not by argument:

1. **`core/nutrition/meal_target.py` apportions every bound by the meal's
   *energy* fraction.** Confirmed 2026-07-31 (see `docs/audit_log.md`,
   2026-07-31 entry, and the sodium verification that followed): the 700 mg
   per-lunch sodium ceiling is `nutrient.sodium_max_mg (2000) ×
   meal_split.energy_fraction_lunch (0.35)`. Sodium does not scale with
   calories. Neither do iron, calcium or B12. Fibre is a separate case, argued
   below.
2. **Protein quality is applied by inflating the gram target.**
   `compute_protein` returns `quality_adjusted_g = base_g / diaas`, and that
   inflated figure is the floor the planner gates on. For the reference
   profile it turns a 112.0 g/day protein target into 124.4 g/day, a 43.6 g
   lunch floor, and a solver whose cheapest answer is 450 g of dal. Quality
   was asked for and quantity was delivered.

Four decisions are settled and this design is written to them, not around
them: day budgets for the non-scaling nutrients; energy and macros stay
per-meal; protein takes a third pattern (day floor + per-meal floor and
ceiling + a quality-source rule); and DIAAS moves from target-inflation to
source-selection.

**Reference profile** used for every worked number below: 70 kg / 175 cm / 28 /
male / moderate / maintain / vegetarian. Current derived day target: 2571.1
kcal; protein base 112.0 g, quality-adjusted 124.4 g (DIAAS 0.9); fat 78.6 g;
carb 341.6 g; fibre floor 36.0 g; sodium ceiling 2000 mg.

---

## 1. The three target categories

Every bound the system computes today, plus the ones it computes values for but
does not bound. `MACRO_KEYS` is the authority on the list:
`energy_kcal, protein_g, fat_g, carb_g, fibre_g, sodium_mg, iron_mg,
calcium_mg, b12_ug`.

| Target | Bounded today? | v2 category |
|---|---|---|
| `energy_kcal` | floor + ceiling | **Per-meal** (unchanged) |
| `carb_g` | floor + ceiling | **Per-meal** (unchanged) |
| `protein_g` | floor only | **Protein pattern** |
| `sodium_mg` | ceiling only | **Day budget** |
| `fibre_g` | floor only | **Ambiguous** — argued below, not decided |
| `fat_g` | floor + ceiling | **Ambiguous** — argued below, not decided |
| `iron_mg` | **no** | **Day budget**, when it acquires a bound |
| `calcium_mg` | **no** | **Day budget**, when it acquires a bound |
| `b12_ug` | **no** | **Day budget**, when it acquires a bound |

### Correction to the commissioning brief

The brief says "fibre, iron, calcium and B12 have the same defect." Iron,
calcium and B12 **have no target at all today.** `simple_target` accepts
`energy_kcal`, `protein_g_min`, `fat_g`, `carb_g`, `sodium_mg_max`,
`fibre_g_min` and nothing else; `derive_target` computes no RDA for the three
micronutrients and registers no constant for them. They are carried through
`NutritionVector` and displayed, never gated.

This matters for sequencing: they are not a migration, they are new work.
Each needs a registered RDA constant with evidence before it can be a budget of
anything, and — per CLAUDE.md's second invariant — that constant cannot be
transcribed from memory and left to look settled. They are listed as day-budget
because that is the category they will belong to, not because there is
something to move.

### Per-meal, and why

`energy_kcal` and `carb_g` are quantities of food. A meal that is 35% of the
day's calories genuinely carries about 35% of the day's carbohydrate, because
carbohydrate is derived as the energy remainder in `_compute_macros`. The
energy-fraction split is not a modelling compromise for these two; it is the
definition. No change.

### Day budget, and why

Sodium's ceiling is a **daily intake guideline** (`who_sodium_2012`: "the daily
sodium intake below which population blood-pressure and cardiovascular risk
benefits were observed"). Enforcing 35% of it against a single plate forbids
the ordinary and entirely healthy pattern of a salty lunch offset by a plain
dinner. The same is true of every micronutrient RDA: they are daily adequacy
figures, and there is no nutritional claim that each meal must be independently
adequate in iron.

### The two ambiguous ones — argument on both sides, no decision taken

**`fibre_g`.** The brief lists it with sodium. It is not the same case, because
its target is *already* derived from energy: `fibre_g_min =
nutrient.fibre_g_per_1000kcal (14.0) × energy / 1000`. It is a per-1000-kcal
figure by construction.

- *For per-meal:* the constant is stated per unit energy. Splitting a target
  that is a function of energy by the energy fraction is self-consistent and
  loses nothing — 36.0 g/day at 2571 kcal becomes 12.6 g at a 900 kcal lunch,
  which is exactly `14.0 × 0.9`. No information is destroyed.
- *For day budget:* the underlying IOM figure is a daily adequate intake, and
  the per-1000-kcal form is a scaling convenience, not a claim that each
  eating occasion must independently hit it. A low-fibre breakfast followed by
  a high-fibre lunch is not a nutritional problem, and a per-meal floor
  declares it one. It is also a floor with a real cost: it pushes the solver
  toward bulk, which is one of the pressures that produced the 450 g dal plate.

I have not resolved this and am not resolving it here. It affects whether the
fibre floor participates in relaxation rung 1 as a day quantity or a plate
quantity, so it must be settled before the ladder is touched.

**`fat_g`.** Derived as the AMDR midpoint fraction of energy, so it scales like
carb, and on those grounds is per-meal.

- *For per-meal:* it is a fixed fraction of energy. Same argument as carb.
- *For day budget, or for dropping the floor:* the AMDR is a *distribution*
  range for a diet, not a requirement for a plate. The per-meal fat **floor**
  is the bound that produced the finding-17 near-miss (20.5 g against a 20.6 g
  floor, decided entirely by one unverified tempering-oil constant). A plate
  being below 20% of its own energy from fat is not a health finding; a *day*
  being so might be. The ceiling has a better claim to being per-meal than the
  floor does, which means fat may not be one category at all — floor and
  ceiling may belong in different ones.

Also unresolved. Flagged because "fat is per-meal, unchanged" is the reading
the brief's decision 2 invites, and it is not obviously right for the floor.

---

## 2. Day-budget mechanics

### Where the running day state lives, and its lifetime

A new frozen dataclass in `core/schemas/` — call it `DayLedger` — holding the
day's date, the profile it was derived for, and per-budgeted-nutrient
`spent` totals plus the list of meal slots already planned. It belongs in
`schemas` because both `core/nutrition` (which sets the budgets) and
`core/planner` (which spends against them) need it, and `core/nutrition` may
never import `core/planner`.

**`core/` must not own its lifetime.** `core/` is pure logic with no I/O beyond
file loading, so the ledger is a value passed in and a new value returned —
`plan_meal(..., ledger: DayLedger) -> (LadderOutcome, DayLedger)` — never
mutated in place and never persisted by `core/`. Persistence is `api/db.py`'s
problem: a `PlannedDay` row keyed by `(user_id, date)`, alongside the existing
`User`/`StoredProfile`. An anonymous user's ledger lives in the request/session
only and dies with it, which is consistent with `/api/plan` being
unauthenticated today.

Lifetime is one calendar day in the user's local timezone. The timezone is a
real question — the day boundary decides whether a late dinner spends today's
or tomorrow's sodium — and the profile carries no timezone field today. Noted;
not designed here.

### How a meal is checked against remaining budget

Replace the proportional split for budgeted nutrients only. `meal_target` keeps
its current behaviour for per-meal targets and gains a second input:

```
remaining(nutrient) = day_ceiling(nutrient) - ledger.spent(nutrient)
meal_ceiling(nutrient) = min(remaining(nutrient), absurdity_ceiling(nutrient))
```

For floors (a day-budget nutrient with a floor, e.g. iron when it exists), the
symmetric statement is *not* `remaining` — a floor cannot be spent down. It is
a **reachability** check: the meal must not make the day's floor unreachable
given the slots left. That is a different computation and a harder one, and it
is the part of this design I am least confident in; it is called out again in
§7 as its own slice.

The validator's `Violation` needs a new `kind` or a field distinguishing "this
plate exceeds its own ceiling" from "this plate exceeds what the day has left,"
because the disclosures are different sentences: one says the plate is too
salty, the other says the rest of the day was.

### The first-meal problem

With nothing spent, `remaining` is the whole day, and nothing stops breakfast
consuming 2000 mg of sodium. This is not hypothetical: **today's blocking plate
at 1649.3 mg would pass a pure remaining-budget check outright** if lunch were
the first meal planned, because 1649.3 < 2000. The decline that this whole
investigation is about would silently disappear, and not because anything got
better.

**Proposed rule: a per-plate absurdity ceiling, applied as `min()` against
remaining.** A plate may never take more than a stated share of the day's
budget regardless of how much is left.

**What "generous" is derived from — and the admission.** The honest answer is
that it is arbitrary. The least-arbitrary derivation available: the largest
registered meal-split fraction is lunch at 0.35, so a plate that takes more
than *twice* the largest ordinary meal's share — 0.70 of the day — is
implausible for any single eating occasion. That gives
`day_budget.absurdity_fraction = 0.70`, i.e. 1400 mg sodium per plate for this
profile. The blocking plate at 1649.3 mg still fails, which is the behaviour
this design wants; but I note plainly that I chose 2× after knowing that, and a
different multiplier chosen before would have produced a different answer.

It must be graded `PROJECT_DECISION` and its `applied_to` must say it is a
plausibility guard, not a nutritional claim.

**Weaknesses, stated:**

- It is a magic number wearing a derivation. "Twice the largest meal split"
  sounds principled and is not; the meal splits are themselves
  `PROJECT_DECISION` values described in `citations.py` as "the customary 'big
  lunch' shape of an Indian day, nothing more." A guard derived from an
  arbitrary constant is arbitrary.
- It reintroduces a per-plate fraction of a daily figure — the exact shape this
  redesign exists to remove — through a side door. The difference is that it is
  now a *guard* rather than *the check*, and is labelled as such. That is a real
  difference, but it is a difference in framing, and framing is what the sodium
  investigation caught us on once already.
- It interacts badly with a genuinely large single meal. A festival thali or a
  single-meal-a-day eating pattern is a real thing, and this rule declares it
  absurd.
- It does not solve the underlying problem, which is that a per-meal decision
  cannot know what the rest of the day will hold. It bounds the damage; it does
  not remove the incoherence.

**The alternative I am not proposing, and why it is worth knowing about:**
plan the whole day at once, so no meal is ever evaluated against an unknown
future. This makes the first-meal problem vanish rather than bounding it. It is
rejected here only because it is a much larger change — it breaks the current
one-template-per-call shape of `plan_meal` and the dashboard's one-plate
interaction — not because it is worse. If the absurdity ceiling proves as
unprincipled in practice as it looks on paper, this is the fallback.

### Out-of-order planning, and abandoned days

- **Out of order** (dinner before lunch) works without special handling: the
  ledger records what is spent, not which slots came first. Remaining budget is
  order-independent. The absurdity ceiling is per-plate and also
  order-independent. This is a genuine advantage of the budget model over
  fractions, which implicitly assume a forward sequence.
- **Re-planning a slot already planned** must debit the old plate before
  crediting the new one, or the ledger double-counts. The ledger therefore
  stores per-slot contributions, not just a running total. This is why
  `DayLedger` holds a slot→contribution mapping rather than a scalar per
  nutrient.
- **Only one meal planned, user never returns.** Nothing to reconcile: the
  ledger is a constraint input, not a promise. But the *user-facing* claim must
  not overstate — a single plate that used 1400 of 2000 mg cannot be described
  as "within your daily sodium," only as "within your daily sodium if the rest
  of the day stays under 600 mg." The disclosure must be conditional whenever
  the day is incomplete, and that is a wording requirement on the API response,
  not just a display nicety.

### Migration: a day already partly planned when this ships

There are no persisted plans today — `api/db.py` stores `User` and
`StoredProfile` only, and `/api/plan` returns a plate without recording it. So
**there is no migration problem for existing data**, and this is the cheapest
moment to make the change.

The rule for when persistence does exist: a day planned under v1 has no ledger.
It must not be back-filled by re-deriving contributions, because a v1 plate was
validated against a different (fractional) bound and reconstructing a ledger
entry would assert a check that never happened. Such a day is marked
`ledger_unavailable` and its remaining meals are planned against the full day
budget with the absurdity ceiling doing all the work, disclosed as such.

---

## 3. Protein

### The per-meal floor and ceiling

Both are `PROJECT_DECISION`. There is no literature stating that a meal must
contain between X and Y grams of protein; the per-meal distribution literature
that exists (leucine-threshold / per-meal-dose work) is about maximising
muscle-protein-synthesis response, which is not what this product claims to
optimise, and citing it here would be exactly the mechanism-mismatch failure
CLAUDE.md's `phenomenon` field exists to prevent.

Proposed, stated as fractions of the **day floor** so they move with the
profile rather than being absolute grams:

| Constant | Value | Reference profile |
|---|---|---|
| `protein.meal_floor_fraction` | 0.15 | 16.8 g per meal |
| `protein.meal_ceiling_fraction` | 0.50 | 56.0 g per meal |
| `protein.quality_day_fraction` | 0.33 | 37.0 g/day from quality sources |
| `protein.quality_meal_floor_fraction` | 0.10 | 11.2 g per meal |

Derivations, such as they are: 0.15 is below the smallest meal split (0.10 for
snack, 0.25 for breakfast) so it cannot make an ordinary light breakfast
infeasible on its own; 0.50 is "no single meal carries more than half the day";
0.33 is "roughly a third of protein from quality sources," which is a judgement
about what a plant-forward Indian diet can plausibly reach, not a finding; 0.10
is deliberately low so that the quality requirement can be satisfied mostly in
one or two meals, per decision 3.

Every one of these is a number I chose. They should be registered with
`evidence_id="project_decision"` and `applied_to` text that says so, and
`docs/methodology.md` should list them among the limitations rather than among
the derivations.

### "High-quality protein source" — the options and their costs

The property must attach to something that can fill a slot. Three candidates:

**Option A — a DIAAS threshold on `Ingredient.diaas`.**
`Ingredient.diaas` already exists, is already loaded by `ifct_loader`, and is
**read by nothing** (confirmed: the only references are the loader that writes
it, the dataclass that declares it, and the per-*diet* constants in
`targets.py`, which are a different thing). A component qualifies if its
protein-weighted mean DIAAS clears a registered threshold.

- *Cost:* **17 of 26 ingredient rows have no DIAAS value at all** (`None`). The
  9 that do are the grains and legumes plus `curd_dahi` at 1.09. A missing value
  must never read as qualifying — the same "cheapest authoring path must not
  produce the most confident output" rule CLAUDE.md's round-4 addendum states
  for uncertainty. So `None` must mean "does not qualify", which means adding a
  paneer row without a DIAAS figure silently makes paneer not count as quality
  protein. That is the safe failure direction but a confusing one.
- *Cost:* every DIAAS figure in the fixture is unverified and hand-entered. A
  threshold at 0.75 versus 0.80 changes which foods qualify, on data nobody has
  opened.
- *Benefit:* it is continuous, principled, and it is the same quantity the
  per-diet constants were abusing — so it puts DIAAS where it actually belongs.

**Option B — a boolean `Ingredient.high_quality_protein` field.**
- *Cost:* it is an assertion with no derivation, per row, authored by whoever
  adds the row. It is the mechanism-match self-attestation problem again.
- *Benefit:* explicit, and cannot be silently wrong through a missing value if
  made mandatory.

**Option C — a category list on the component** (`{paneer, tofu, curd, egg,
meat, fish, soya}` qualify).
- *Cost:* categories are about the role a dish plays in a plate grammar, not
  about its protein. A `raita` is a curd dish and would qualify; a *cucumber*
  raita that is 90% cucumber would also qualify, wrongly. The property is being
  inferred from the wrong axis.
- *Benefit:* cheapest to implement, no new data.

**Recommendation: Option A, with `None` excluded and the threshold registered.**
It reuses a field that already exists and is presently dead, and it is the only
option where the qualification is derived from the same quantity the nutrition
literature uses. The 17 missing values become a stated data gap in
`docs/methodology.md` rather than a hidden default.

Note the unit question, which is not resolved: DIAAS is a property of a protein
source, and a *component* is a mixture. "Protein-weighted mean DIAAS across the
component's ingredient lines" is the obvious aggregation and is not obviously
correct — DIAAS is limiting-amino-acid based, and rice-plus-dal
complementarity means the mixture can score better than the weighted mean of
its parts. Getting this wrong understates mixed Indian plates specifically.
Flagged, not resolved.

### The DIAAS reversal — the correctness risk

**Where DIAAS inflates today.** One place only, `core/nutrition/targets.py`:

```python
quality_adjusted_g = base_g / diaas     # 112.0 / 0.9 = 124.44
```

and that value, not `base_g`, is passed to `simple_target(protein_g_min=...)`.
Grepping confirms no second application: `diaas` appears in `ifct_loader`
(writes the ingredient field), `models.py` (declares it), `targets.py` (the
inflation and the five per-diet constant keys), and `api/main.py`/`api/models.py`
(display only). **`core/planner` never reads DIAAS at all.** So today quality is
applied exactly once, and it is applied to the target.

**What the targets become.** The protein floor becomes `base_g`:

| | v1 | v2 |
|---|---|---|
| protein day floor | 124.4 g | **112.0 g** |
| protein lunch floor | 43.6 g | day floor 112.0 + meal floor 16.8 / ceiling 56.0 |

**The consequence that is easy to miss, and is the actual correctness risk.**
`_compute_macros` computes carbohydrate as the energy *remainder* after protein
and fat:

```python
protein_energy = protein_g * kcal_p
carb_energy = energy_kcal - protein_energy - fat_energy
```

It is called with `protein.quality_adjusted_g`. Drop the inflation and 12.44 g
of protein (49.8 kcal) stops being claimed, so **carbohydrate rises**:

```
v1: 2571.1 - (124.44 x 4) - 707.05 = 1366.3 kcal -> 341.6 g carb
v2: 2571.1 - (112.00 x 4) - 707.05 = 1416.0 kcal -> 354.0 g carb   (+12.4 g)
```

Lunch carb ceiling therefore moves 137.5 g → 142.5 g. **The plate gets a more
permissive carb ceiling as a side effect of a protein change**, which is not
something the brief asks for and not something anyone would expect from
"quality moves to source selection." It is a real behavioural change and it
must be stated in the commit, not discovered later.

It is also arguably *correct* — the v1 carb figure was the remainder after an
inflated protein number, so it was understated for the same reason the protein
floor was overstated — but "arguably correct" is not "intended", and the
`carb_g` figure has never been examined on its own terms.

**Is quality applied twice under v2?** No, provided one rule holds:
`compute_protein` must stop dividing, and the per-diet `diaas.*` constants must
stop being read for target derivation. If they are left in place "for display"
while the source rule also runs, a vegetarian's target is inflated *and* their
components are quality-filtered, which is double-counting in the direction of
demanding more food — precisely the failure this redesign is correcting.

Consequences that follow and must be handled in the same change:

- The five `diaas.{non_vegetarian,eggetarian,vegetarian,jain,vegan}` constants
  become **unused**. They should not be quietly left registered: either remove
  them or re-register with `applied_to` text saying they are retained for
  display only and gate nothing.
- `_SOURCE_KEYS` in `targets.py` lists all five. It drives both
  `DerivedTarget.sources` (provenance shown to the user) and
  `_status_and_disclosure`. Leaving them listed would claim the target derives
  from constants it no longer reads. `status` stays `dev_mode` either way —
  every remaining source is unverified — but the provenance list would be a
  false statement about the project's own state.
- `api/models.py` exposes `diaas` in the target response and `web/` renders it.
  That field now describes something that does not affect the number beside it.

### What this does to today's blocking plate

The plate is `phulka ×3 + dal_tadka ×3 + onion_raita ×2` (recomputed with the
corrected `salt_iodised` value: 1649.3 mg sodium, 40.4 g protein, 984.1 kcal).

Under v2, per bound:

| Bound | Plate | v2 bound | Verdict |
|---|---|---|---|
| energy (per-meal) | 984.1 kcal | 854.9–944.9 | **over ceiling** (unchanged from v1) |
| carb (per-meal) | 139.4 g | ≤142.5 g | passes (v1: ≤137.5, failed) |
| protein per-meal floor | 40.4 g | ≥16.8 g | passes |
| protein per-meal ceiling | 40.4 g | ≤56.0 g | passes |
| sodium (day budget, first meal) | 1649.3 mg | ≤1400 mg absurdity ceiling | **over** |
| sodium (day budget, no absurdity ceiling) | 1649.3 mg | ≤2000 mg remaining | **would pass** |
| high-quality protein, per-meal | **7.9 g** | ≥11.2 g | **fails** |

The high-quality figure: `curd_dahi` (DIAAS 1.09) is the only qualifying
ingredient on the plate, contributing `128 g × 2 units × 3.1 g/100 g = 7.94 g`.
Toor dal is 0.60 and atta is 0.45; under any threshold that admits curd and
excludes dal, they contribute nothing to the quality floor.

**So: no, `phulka ×3 + dal ×3 + raita ×2` would not be the solver's best
answer.** It fails the per-meal high-quality protein floor and the sodium
absurdity ceiling, and still misses the energy ceiling. That is the design
working as intended — the quality-source rule rejects the pure-lentil plate
directly, rather than the old model's route of inflating the gram target and
hoping the solver picked something sensible.

**But note what happens next, and it is not comfortable:** with the current
six-recipe library there is *no* qualifying alternative. `curd_dahi` is the only
ingredient in the entire 26-row fixture with a DIAAS above 0.62, and
`onion_raita` is the only component containing it. To reach 11.2 g of quality
protein the solver needs ~3 katoris of raita, which is not a plate either. **v2
does not make north_lunch solvable; it changes which constraint blocks it**,
from sodium to protein quality. That is an improvement in the honesty of the
decline and not an improvement in the product. The library needs a paneer,
tofu, soya or egg row before v2 can produce a passing north Indian plate at
this profile's protein target.

---

## 4. Interaction with open findings

### Finding 15 — combo component alongside its own base

**Left untouched.** Finding 15 is about slot semantics: nothing in
`TemplateSlot` lets a slot declare what a filling component may not also
provide, so `rajma_chawal` (`combo_rice_legume`, containing 183 g of cooked
rice) can fill `legume_curry` while `phulka` separately fills `grain_base`.
Target categories have no bearing on which combinations are enumerated.

Two second-order effects worth recording, neither of which is a fix:

- The per-meal carb ceiling — the arithmetic that currently catches the
  double-grain plate — gets *looser* under v2 (137.5 → 142.5 g, from the DIAAS
  reversal above). Finding 15's symptom is therefore very slightly easier to
  reach, not harder.
- The quality-source rule bites the combo plate independently: `rajma_cooked`
  is DIAAS 0.60 and `rice_cooked` 0.47, so a roti-plus-rajma-chawal plate
  contributes zero qualifying protein and fails the per-meal quality floor
  outright. That is a real constraint on the enumerated-but-nonsensical plate,
  arriving for an unrelated reason. **It must not be mistaken for closing
  finding 15** — it rejects this particular combo for its amino-acid profile,
  not for containing two grain bases, and a combo dish built on curd would sail
  through.

### Interval gating across a day — the real risk, addressed

The concern: a day budget accumulates uncertainty across meals, so by dinner the
interval is so wide it gates nothing.

**It does not break the gate, for a structural reason.** `core/planner/validator.py`
gates on the **point estimate only** and never reads `actual_interval` — that
restraint is the module's stated purpose, because interval-overlap gating means
worse data passes more easily. A day budget is a sum of point estimates
subtracted from a point ceiling. Widening intervals do not enter the comparison.
So the answer to "does a day's worth of intervals become so wide it gates
nothing" is **no, because intervals are not what gates.**

**What it does break is the display, and that is not a small thing.** The
project's other rule is that the interval is always shown. Consider the sodium
budget after two meals:

- Per-plate energy uncertainty measured on the real library is ±26%
  (`docs/audit_log.md` finding 16). Sodium's band is comparable, being driven by
  the same unverified composition rows.
- Errors across meals are **not independent**. The same `salt_iodised` row, the
  same `oil_uptake.vegetable_tempering` constant, and the same handful of
  fixture rows appear in every meal of the day. Independent errors would shrink
  the fractional band by √n; correlated ones do not shrink it at all. Ours are
  strongly correlated, so **the fractional band on a day total is roughly the
  same as on one plate — around ±25%, not ±12%.**
- Applied to a remaining budget, that is ruinous to communicate. "You have
  350 mg of sodium left today (±430 mg)" is not a sentence that can be shown to
  a user. The absolute band on the *spent* figure does not shrink as the
  remaining figure does, so the interval overwhelms the remainder precisely when
  the remainder matters most.

**Consequence for the design, stated rather than deferred:** the remaining-budget
figure must not be displayed as an interval at all. It should be displayed as a
point with a *qualitative* status band — "comfortably within / close to / over"
— with thresholds set wide enough to be meaningful given ±25% data, and the
underlying uncertainty disclosed once at the day level rather than attached to
each remaining-budget readout. A per-readout ±430 mg is wallpaper by the second
meal, which is the same failure mode CLAUDE.md's "per-dish asterisk" paragraph
identifies for unverified constants.

This is a display design decision I am flagging, not making. What I am asserting
is the measurement: the band does not shrink across meals, and any design that
assumed it would is wrong.

### `dev_mode` and the 15% unverified-energy threshold

Current state, verified: **the threshold is not implemented anywhere.**
`NutritionEstimate.unverified_energy_fraction()` exists in
`core/foods/nutrition_of.py` and is computed per plate; **no code reads it**,
and there is no registered constant for 0.15 (`eligibility.max_protein_uncertainty`
and `tolerance.fat_carb_default` also happen to be 0.15 and are unrelated). It
exists as prose in CLAUDE.md and as an unread method.

Under a day model it should be **per day**, and CLAUDE.md already says so
without anyone having noticed: the wording is "the aggregate energy contribution
from `verified=False` process constants is below roughly 15% of **total plan
energy**" — plan, not plate. A per-plate reading was an unexamined convenience.

Two consequences:

- The per-plate method stays (it is the input), but the *gate*, when built,
  takes the day's total. A day whose lunch is 70% unverified and whose other
  meals are clean is a different object from a day where every plate is 70%
  unverified, and only the day-level figure distinguishes them.
- It changes nothing today. Every plate the real library can produce is far
  above the threshold (the reference plate is 70.5% unverified energy), so no
  day can clear it either. `dev_mode` remains the only reachable status, per
  `docs/methodology.md`.

---

## 5. Non-vegetarian — deferred, and what it will touch

**Not in scope for this task or the implementation that follows.** Documented
only so the target model is not built in a way that makes it expensive.

Current state: `DietPattern` already has `non_vegetarian` and `eggetarian`;
`Profile.diet` already carries them; `web/dashboard.js` already has display
labels for both; `data/recipes/schema.yaml` already lists them as valid
`diet_patterns`. **No recipe declares either, and `curd_dahi` is the only
`is_animal_product` row in the 26-row fixture.** So the axis is declared
everywhere and populated nowhere.

What it will need to touch:

- **Ingredient library.** Animal-protein rows (egg, chicken, fish, mutton,
  paneer as the vegetarian neighbour) with composition, `is_animal_product`,
  allergens, and — directly relevant to §3 — **DIAAS values**, since these are
  exactly the rows that would qualify under the quality-source rule. This is the
  binding dependency: the quality rule is inert until these exist. Note that
  IFCT 2017 does cover animal foods (groups L–P), so unlike the oils these are
  sourceable.
- **Recipe schema.** No change needed — `diet_patterns` already expresses it.
  The `state` basis question is sharper for meat (raw/cooked yield differs a
  lot), but the existing per-line `state` field handles it.
- **Templates.** This is the real work. No current template has a slot that
  accepts a meat dish: `NORTH_DINNER` is `bread + dal + sabzi`, and a chicken
  curry is not a `dal`. Either new categories are added to existing slots, or —
  more likely correct, given the module's whole thesis — new `(region,
  meal_slot)` templates are declared for non-vegetarian plates, since a
  non-veg South Indian lunch is a different plate shape, not the same shape with
  a substitution.
- **Candidate filtering.** `build_candidate_pool` already filters by
  `diet_pattern`; the semantics of "a vegetarian may not eat a non_vegetarian
  dish, but a non_vegetarian may eat a vegetarian dish" needs checking — it is
  an ordering, not an equality, and I have not verified which the current filter
  implements.
- **Onboarding.** The wizard collects diet today; whether it offers the non-veg
  options and what it does with them is out of scope here.

**The one thing the target model must not do:** hard-code any assumption that
qualifying protein sources are dairy. If the quality rule is written as "curd
and paneer qualify" rather than as a DIAAS threshold, every non-veg row added
later needs the rule edited. Option A in §3 is chosen partly for this reason.

---

## 6. Changes made alongside this document

Two, each its own commit, both authorised explicitly.

### `salt_iodised`: 38758 → 39339 mg/100 g

The row's note claimed "Sodium content is stoichiometric (39.3% of NaCl by
mass)" while storing 38758, which implies 98.52% NaCl purity — a measured
table-salt figure under a note describing a derivation. The number and its
stated justification did not match.

```diff
-salt_iodised,...,38758,...,Sodium content is stoichiometric (39.3% of NaCl by mass)
+salt_iodised,...,39339,...,"Sodium content DERIVED, not measured: 22.99/58.44 =
+ 39.339% of pure NaCl by mass, x 100 g = 39339 mg. Corrected 2026-07-31 from
+ 38758, which was a measured table-salt value (implying ~98.5% NaCl purity)
+ sitting under a note that claimed the stoichiometric derivation -- the number
+ and its stated justification did not match. The derivation is chosen over the
+ measured value for reproducibility: anyone can rederive it from two atomic
+ masses, whereas the measured figure needs a source document nobody here has
+ opened. NOTE THE COST: iodised table salt is NOT pure NaCl (anti-caking
+ agents, potassium iodate, moisture), so this figure describes the derivation
+ and overstates a real product's sodium by roughly 1.5%. It is a reproducible
+ upper bound, not a product measurement. verified=false: no primary source has
+ been opened for either figure"
```

Resulting sodium totals, per serving unit:

| Recipe | Before | After | Salt line's share |
|---|---|---|---|
| `phulka` | 59.0 mg | **59.9 mg** | 98.5% |
| `dal_tadka` | 315.1 mg | **319.8 mg** | 98.4% |
| `onion_raita` | 252.3 mg | **255.2 mg** | 77.1% |
| `rajma_chawal` | 785.1 mg | **796.8 mg** | 98.7% |

Blocking plate: 1626.9 → **1649.3 mg** against the same 1050 mg relaxed
ceiling. The decline is unchanged in kind.

`tests/test_recipes.py::TestRajmaChawal::test_sodium_is_dominated_by_added_salt`
hand-computes this total and was updated in the same commit, with the new
arithmetic shown per CLAUDE.md's testing convention (`393.39 mg/g × 2 g =
786.78`, `+ 9.98 = 796.76`). It is a rederivation from the changed constant, not
a snapshot.

### `walkthrough.py` target labelling

It printed `out.target_used` — the target the ladder *stopped* on — under a bare
`meal target` heading, which is what miscalibrated the Task 4b prediction: the
fully-relaxed bounds were read as the unrelaxed ones. It now prints both,
labelled:

```
meal target    : energy floor 854.9 ceiling 944.9
                 protein floor 43.6, fat floor 23.4, carb ceiling 137.5, sodium ceiling 700.0
                 ^ UNRELAXED — what the plate is asked for before any rung fires
target used    : energy floor 809.9 ceiling 989.9
                 protein floor 37.0, fat floor 20.6, carb ceiling 149.4, sodium ceiling 1050.0
                 ^ AFTER 4 relaxation rung(s): sodium_max_fibre_min, fat_carb_tolerance, energy_tolerance, protein_tolerance
```

**This is not a repo file.** See the note at the end of this document.

---

## 7. Implementation slices

Ordered, each independently shippable, each with what would demonstrate it.
**None started.**

1. **Register the protein per-meal and quality constants.** Four
   `PROJECT_DECISION` constants (§3), with `applied_to` text stating they are
   project decisions, plus `docs/methodology.md` limitations entries.
   *Demonstrated by:* the constants resolving, and a test asserting each is
   graded `PROJECT_DECISION` and thus categorically ineligible to count as
   reviewed — the round-4 addendum rule.

2. **The DIAAS reversal, alone.** `compute_protein` stops dividing; the five
   per-diet constants are removed from `_SOURCE_KEYS` and either dropped or
   re-registered as display-only; `api/models.py` and `web/` follow.
   *Demonstrated by:* protein day floor moves 124.4 → 112.0 for the reference
   profile **and carb moves 341.6 → 354.0 in the same test**, with both figures
   hand-derived in comments. A test that checks only protein would miss the
   side effect that §3 identifies as the correctness risk. Shipped alone so the
   change is attributable if something moves unexpectedly.

3. **Per-meal protein floor and ceiling.** `simple_target`/`meal_target` gain
   the two bounds. No quality rule yet.
   *Demonstrated by:* a synthetic plate carrying 5 g of protein now declines
   naming `protein_g` below its per-meal floor, and one carrying 80 g declines
   on the ceiling. The reference profile's north_lunch decline is unchanged.

4. **`DayLedger` as a value type, not yet wired to the solver.** The dataclass,
   the per-slot contribution mapping, and the debit-then-credit re-plan rule.
   *Demonstrated by:* re-planning the same slot twice leaves the ledger with one
   slot's contribution, not two.

5. **Sodium moves to a day budget, with the absurdity ceiling.** The registered
   `day_budget.absurdity_fraction`, the `min(remaining, absurdity)` rule, the new
   violation kind distinguishing "this plate" from "what the day has left."
   *Demonstrated by:* the reference plate declines as first-meal-of-day at
   1649.3 mg against the 1400 mg absurdity ceiling, **and** passes at 1649.3
   against a 2000 mg remaining budget when the absurdity ceiling is lifted — the
   second assertion is what proves the guard is load-bearing rather than
   decorative.

6. **Quality-source selection.** The DIAAS threshold on components, `None`
   excluded, the aggregation rule for mixtures (with its stated limitation).
   *Demonstrated by:* `onion_raita` qualifies and `dal_tadka` does not; the
   reference plate's quality protein computes to 7.94 g and declines against the
   11.2 g per-meal floor. And — the perturbation test CLAUDE.md's round-4
   addendum demands — flipping `curd_dahi`'s DIAAS below the threshold changes
   the verdict, proving the rule reads the data rather than a hard-coded list.

7. **Resolve fibre and fat** (§1), which is a decision, not a build. Blocks any
   change to relaxation rung 1.

8. **Iron, calcium, B12 as day budgets.** New RDA constants with evidence
   first; the budget mechanics are already built by slice 5.
   *Demonstrated by:* nothing, until a human has opened a source — these are
   the constants most likely to be transcribed from memory and left looking
   settled.

Slices 1–3 are independent of the ledger and can ship immediately. Slice 6 is
the one that changes what the product recommends, and it is inert until the
ingredient library has a qualifying protein source that is not curd.

---

## Underspecified, flagged rather than resolved

- **`walkthrough.py` is not in the repository.** It has never been tracked
  (`git ls-files` returns nothing for it); it is a scratch script in the session
  working directory. The brief asks for its fix "as its own commit," which is
  not possible without first deciding whether it becomes a repo artifact. That
  decision interacts with open finding 11 (`demo.py` is referenced in CLAUDE.md's
  Commands block and `docs/methodology.md` and does not exist), so it is
  plausibly the same piece of work. **The relabelling is done in the scratch
  copy and is not committed.** I have not chosen where it should live.
- **Fibre and fat categories** (§1) — both arguments given, neither picked.
- **DIAAS aggregation across a mixture** (§3) — the weighted-mean rule
  understates amino-acid complementarity in exactly the rice-and-dal case this
  product is about.
- **Day boundary timezone** (§2) — `Profile` has no timezone field.
