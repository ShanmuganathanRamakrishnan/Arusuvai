# Methodology and known limitations

Current as of the onboarding build (2026-07-23): profile→target derivation
(`core/nutrition/targets.py`) and a thin `api/` exposing it, on top of the
Phase 3 validator and relaxation ladder. Sections for the LLM ranking/narration
layer, commerce and web will be added as those phases land — this document only
describes what exists.

## Scope statement — read this first

This is a portfolio project, not clinical nutrition guidance. Nothing here is a
substitute for advice from a dietitian or a doctor.

**The relaxation ladder's default ordering assumes no clinical dietary
condition.** By default, when no plan fits a profile, this system loosens
constraints in a fixed order — sodium and fibre first, then fat and carb, then
energy, then protein — and the first three of those are loosened *silently*.
That ordering is a general-population judgement about which constraints matter
least. It is the wrong judgement for someone whose sodium ceiling is a medical
instruction rather than general health guidance.

A user with a diagnosed condition must rely on `Profile.clinical_flags`
(`core/schemas/profile.py`), not on the default behaviour. A flag hard-locks
its constraint out of the ladder entirely: the constraint becomes a floor or
ceiling that is never relaxed for that profile, and if locking it makes the
feasible set empty, the system declines and names the blocking constraint
rather than loosening it. The mapping from flag to locked macro is
`core/planner/validator.LOCKED_CONSTRAINTS`:

| `ClinicalFlag`           | Locks                  |
| ------------------------ | ---------------------- |
| `hypertension`           | `sodium_mg`            |
| `chronic_kidney_disease` | `protein_g`, `sodium_mg` |
| `diabetes`               | `carb_g`               |

This list is short and it is not a diagnosis tool. A condition that is not in
it gets no protection at all — the default ordering applies in full — which is
the honest state of a portfolio project and the reason the paragraph above
matters more than the table does.

## Accounts and persistence: scope (2026-07-24)

**Built:** a `User` table (SQLite via SQLAlchemy — `api/db.py`), a real
`bcrypt` password hash per account (never a homemade scheme, never the
plaintext), and a signed session cookie
(`starlette.middleware.sessions.SessionMiddleware`, backed by `itsdangerous`
— not a heavier auth framework). A `Profile` persists against a `user_id`
once an account exists, replacing the prior session-storage-only handoff
between onboarding and the dashboard. `dashboard.html` requires an
authenticated session; an unauthenticated visitor is sent to onboarding's
signup/login surface rather than shown dashboard content.

**Deliberately not built, this increment — a named limit, not an oversight:**

- **No email verification.** Signup accepts any syntactically valid email and
  never confirms the account holder controls it.
- **No password reset flow.** A forgotten password is currently
  unrecoverable; there is no "forgot password" link anywhere in the UI.
- **No OAuth / social login.** Email + password only.
- **Nothing commerce-shaped.** No orders, no subscriptions, no delivery
  zones, no pricing — `core/commerce/` is untouched by this increment, and
  none of it was added as a side effect of "since a database exists now." An
  account today does exactly two things: it exists, and it holds one profile.
- **No rate limiting or brute-force protection on `POST /api/auth/login`.**
  This is a different category from the four items above — those are missing
  *features*; this is a missing *safeguard*. Nothing in this codebase throttles
  repeated login attempts, locks an account after N failures, or slows down a
  password-guessing script hitting the endpoint. `verify_password` is real
  bcrypt work (deliberately slow per attempt), which raises the cost of a
  brute-force run somewhat, but that is a side effect of the hashing choice,
  not a designed defense — nothing here counts or caps attempts. Named
  explicitly rather than left for a future reader to discover by writing a
  credential-stuffing script against a local instance.

None of these are hard — they're ordinary web-app features — but each is a
real surface (transactional email, token expiry, a credential-recovery path
that itself needs to resist abuse, a commerce data model with its own
integrity constraints) that this increment's brief scoped out explicitly.
Treat their absence as a stated boundary of what "accounts" currently means
in this codebase, not as something quietly missing that a future reader has
to discover by trying it.

**Session secret.** `api/main.py`'s `SessionMiddleware` reads
`FOODAI_SESSION_SECRET` from the environment. Corrected 2026-07-24: an earlier
version of this fell back to a fixed string checked into source when the
variable was unset, which is a real vulnerability, not a style nitpick —
anyone who read this public repo could forge a valid session cookie against
any deployment that never set the variable. The fallback now generates a
random secret (`secrets.token_hex(32)`) at process startup instead, with a
`warnings.warn` if it fires. That closes the forgeable-cookie hole but trades
in a disclosed, real limitation: sessions do not survive a process restart
without the environment variable set, and running this API as multiple
worker processes without it would give each worker a different secret, so a
session minted by one worker fails to validate on another.
`FOODAI_SESSION_SECRET` must be set explicitly for any deployment where
either of those matters.

**No rate limiting on login.** See "Accounts and persistence: scope" above —
this is named there as a missing safeguard, not folded into this paragraph,
because it is a different kind of gap than a session-secret bug: nothing was
done wrong here, nothing was ever built.

## Raw versus cooked weight

Recipes store **cooked/finished weights as the primary record**. Rice roughly
triples on cooking, so reading a raw composition value against a cooked quantity
is a 3x error rather than a tolerance-band problem — which is why:

- every recipe ingredient line carries its own `state` (`raw`, `cooked`,
  `as_used`), naming the composition basis to look it up on;
- `core/foods/nutrition_of.py` **refuses** to evaluate a line whose state does
  not match the ingredient's record, rather than silently applying a yield
  factor;
- conversions go through `core/foods/retention.py`, which reads its factors from
  the citation registry. There is no inline multiplication by a yield factor
  anywhere in the codebase.

Ingredient quantities in a recipe sum to the finished weight of **one serving
unit**, checked on construction within 2%. Where a dish is made from a raw
constituent that absorbs water — a dosa from rice-and-urad batter — the raw
constituents are recorded on a `raw` basis and the absorbed water is listed as
an explicit `water` line, so the masses still add up and nothing is hidden
inside a single derived number.

## Serving units, not multipliers

Portion space is not continuous. Every recipe declares a `ServingUnit` with a
name ("dosa", "cup", "plate"), a gram weight, and integer `min`/`default`/`max`
counts. The solver will search that integer domain.

There is deliberately no continuous multiplier and no five-point multiplier
scale (0.5/0.75/1.0/1.25/1.5) anywhere: 1.25 of an idli is 1.25 idlis, and a
five-point scale produces the same unservable fractional output with tidier
presentation. `ServingUnit.grams_for` and `portions.to_grams` both raise
`TypeError` on a non-integer count, so this cannot be reintroduced by accident.

## Uncertainty is a property of the data

There are **two independent sources of error**, and an early version of this
system modelled only the second:

1. **Composition uncertainty** — how wrong the per-100 g nutrient record itself
   is. Resolved per ingredient from provenance:
   `composition.verified_primary` (0.05) for a value a human read out of a
   primary table, `composition.unverified_secondary` (0.25) otherwise. Assigned
   by the loader from a registered constant, never from a CSV column, so an
   author cannot quietly narrow the band on their own unverified row.
2. **Process uncertainty** — `Recipe.process_uncertainty`, a fractional band per
   macro at the dish level, covering oil uptake and cooking loss. Immutable
   after construction (`MappingProxyType`) so no downstream module can widen it
   to make a plan pass.

`nutrition_of_components` returns a point estimate **and** an interval. Both
terms are summed rather than root-sum-squared — the errors are treated as
perfectly correlated. For process constants the justification is mechanism (this
cook, this pan). For composition it is *provenance*: every value in the current
fixture was transcribed from memory by one author in one sitting, so the errors
plausibly share a bias. **That justification expires with the real IFCT ingest**,
where per-food laboratory errors are much closer to independent; see the caveat
in `nutrition_of_components`' docstring.

The validator (Phase 3) will gate on the **point estimate only**. Interval
overlap gating is disqualified: it would mean a plan built on worse data passes
more easily, which inverts the point of having a gate.

### Why composition uncertainty was added (2026-07-21)

Before it existed, the band came from process constants alone. On the masala
dosa that meant the displayed figure was derived from the griddle-oil constant,
which governs 8.84 kcal of a 223.65 kcal dish — and the remaining 96%, whose
composition values nobody has ever checked against a source, contributed exactly
zero. The dish rendered as `~220 kcal (+/-4%)`.

That is **tighter than the ±5% this project would claim for real IFCT data**, on
data that is admittedly worse. It is also worse than printing a bare
`1,847 kcal`: a bare number is merely silent about its error, whereas `±4%`
actively asserts the error is small. That is precisely the false-precision
failure this project exists to prevent in the LLM, committed instead by the
mechanism built to prevent it.

With both terms, the same dish is:

```
composition  223.65 kcal x 0.25             = 55.9125 kcal
process      derived from the oil lines     =  8.8400 kcal   (see below)
half-width                                   = 64.7525 kcal
                            = 28.95% of the point estimate
```

(The process term is 8.84, not the 8.946 an earlier draft of this section
showed. That draft used the hand-rounded 0.040 that used to sit in the recipe
YAML; the derived figure is 0.03952604. See `docs/audit_log.md` finding 9 — the
doc kept the stale number after the code stopped using it, which is the same
staleness the derivation was built to eliminate.)

### Where the declared process bands come from

Each recipe's process uncertainty is derived arithmetically from a registered
constant, with the derivation written into the recipe file's `uncertainty_notes`
and enforced by the loader. Worked example, masala dosa energy:

```
griddle oil 3.5 g x 8.84 kcal/g x 0.20 band = 6.188 kcal
temper  oil 3.0 g x 8.84 kcal/g x 0.10 band = 2.652 kcal
(6.188 + 2.652) / 223.65 kcal total          = 0.040
```

Which line each constant governs is recorded on the ingredient line itself
(`process: oil_uptake.dosa_griddled`), not in a recipe-level list. The masala
dosa has two `gingelly_oil` lines that differ only by process, which a
recipe-level list cannot express; and `Recipe.process_constants` and
`process_exposure_g` are derived from the lines, so neither can go stale against
the ingredients it describes.

### There is no band on the recipe quantities themselves (2026-08-02)

A third source of error exists and is currently modelled as zero: **how wrong
the gram figure on a recipe line is.** `Ingredient.composition_uncertainty`
covers the per-100 g row and `Recipe.process_uncertainty` covers the oil-uptake
and yield constants, but nothing covers the fact that "0.8 g of salt in a dal"
was authored to be plausible rather than measured. There is no measurand for it;
no table states how much salt goes in a dal.

Measured, this is the dominant error on exactly the macros that decide plans:
sodium is 77–99% and fat 88–97% attributable to lines whose quantity is a free
authoring choice, across all six recipes. Sodium is also the constraint that
currently declines the reference profile.

Designed, not built: `docs/design/recipe_quantity_uncertainty.md` (2026-08-02),
including the two findings the measurement produced — the confidence label it
specifies has only one reachable value, and the unverified-energy fraction is
wrong in both directions by a measured amount. Finding 19 is OPEN; finding 20
is CLOSED 2026-08-09 (D6), and the figures that document quotes for the
unverified fraction are superseded by the section below.

## The unverified-energy fraction, measured correctly (2026-08-09, D6)

The fraction that decides whether a plan may ship as validated used to ask one
yes/no question per *recipe* — is any of its process constants unverified — and
charge the recipe's whole energy on a yes. That was wrong twice over
(`docs/audit_log.md` finding 20): it charged dal_tadka's entire 519 kcal for a
5 g tempering-oil line, and it charged **nothing** for unverified ingredient
composition, so dishes resting entirely on hand-entered rows reported 0.0.

Attribution is now per ingredient line. A line is charged when its composition
record is unverified **or** the process constant that determined its quantity
is, and charged once in either case — a line unverified for two reasons is
still only that much energy.

The result, for the four plates the reference profile is served today:

| plate | energy | old rule | corrected |
| --- | ---: | ---: | ---: |
| south_breakfast | 623.6 kcal | 37.5% | **100.0%** |
| south_lunch | 848.1 kcal | 59.1% | **100.0%** |
| north_lunch | 931.2 kcal | 46.9% | **100.0%** |
| north_dinner | 782.5 kcal | 40.6% | **100.0%** |

Reproduce with `PYTHONHASHSEED=0 PYTHONPATH=. python
docs/design/probes/d6_unverified.py`, which prints the per-line arithmetic.

**Exactly 100%, on every plate, is the correct answer and not a rounding
artifact.** 28 of 29 ingredient rows are `verified=False`; the exception,
`water`, carries no energy. So every calorie on every plate traces to a
composition record nobody has opened, and the old figures of 37–59% were
understatements produced by ignoring composition entirely.

This does not change what can ship — nothing could ship as validated before,
for the independent reason in the section above — but it removes the last
reading on which that might have looked close. It is not 15% away from the
threshold; it is the whole plate. Anything downstream that leans on this
number — the `dev_mode` exit in particular — now leans on a figure that means
what it says.

## Nothing can currently ship as validated (2026-07-21)

Stated plainly, because the alternative is discovering it after `core/planner`
has been built on the assumption that some plans clear the threshold.

**Every registered `Evidence` in `citations.py` is `verified=False`.** Nobody has
opened IFCT 2017, FAO FNP 77, or the NIN household-measures manual during this
build.

Separately — `Evidence.verified` and `Ingredient.verified` are distinct flags —
25 of the 26 ingredient rows are unverified and carry the 0.25 band (updated
2026-07-24: four rows now carry real IFCT codes and values but remain
`Ingredient.verified=False` pending human sign-off — see "Known limitations,
Phase 1" below — so this count is unchanged in substance). The exception is
`water`, at 0.05, which cannot move any band because all nine of its macros
are zero. So every recipe's protein uncertainty is 0.25 against an
`eligibility.max_protein_uncertainty` ceiling of 0.15.

Protein is target-critical for essentially every profile this product serves. So
**the candidate pool is empty for every profile**, and the relaxation ladder
cannot rescue it: the ladder moves tolerance, and never uncertainty.

Two tests in `tests/test_nutrition_of.py` assert this rather than leaving it as
prose — `test_no_recipe_currently_clears_the_protein_eligibility_ceiling` and
`test_every_registered_evidence_is_still_unverified`. They exist because the
tempting fix, once the planner returns nothing, is to nudge 0.25 down or 0.15 up
until a demo works. Either edit looks reasonable in isolation; both must be
deliberate acts with a failing assertion attached.

### Verification priority — by macro share, not by row count (2026-07-21)

Verifying the fixture row by row is the wrong unit of work. `composition_uncertainty`
is combined **weighted by each ingredient's share of the macro**, so a row that
contributes 0.1% of the library's protein moves no band whatever its provenance.
The ingredients worth a human's time are the ones that dominate the totals.

Summed absolute contribution across all three authored recipes, one serving unit
each (reproduce with the snippet in this section's commit):

| Rank | Ingredient        | Energy share | Protein share |
| ---- | ----------------- | ------------ | ------------- |
| 1    | `rice_cooked`     | 39.3%        | 28.5%         |
| 2    | `rajma_cooked`    | 14.5%        | 34.7%         |
| 3    | `gingelly_oil`    |  9.7%        | 0             |
| 4    | `rice_milled_raw` |  9.3%        |  6.4%         |
| 5    | `sunflower_oil`   |  7.4%        | 0             |
| 6    | `toor_dal_cooked` |  5.7%        | 11.4%         |
| 7    | `potato_boiled`   |  4.0%        |  3.0%         |
| 8    | `urad_dal_raw`    |  3.2%        |  7.8%         |

Those eight are **93.0% of library energy and 91.9% of library protein**. The
remaining 15 rows together move less than 9% of either.

Two things worth recording, because both contradict the obvious assumption:

- **Three fixture rows are used by no authored recipe at all:**
  `wheat_atta_raw`, `curd_dahi`, `coconut_fresh`. Verifying them today buys
  nothing. (There is no paneer row in the fixture; an earlier draft of this
  section claimed there was — `docs/audit_log.md` finding 10.) This is a
  property of having three recipes, and the ranking must be recomputed once the
  library grows — it is not a stable list.
- **The two oils are 17.1% of energy and 0% of protein.** They are worth
  verifying for the energy band and are irrelevant to the protein ceiling, which
  is the binding constraint. Oil composition is also the easiest of the eight to
  verify, and the least valuable.

### Nothing has been verified. `dev_mode` status is unchanged. (2026-07-21)

No `verified` flag was flipped, and none could be. The rule in `citations.py`
and in CLAUDE.md's second invariant is that **only a human who has opened the
source document may set `verified=True`**, and nobody has opened IFCT 2017.

This matters more than it might read. An assistant's recollection of what IFCT
says about cooked rice *is exactly the thing* `composition.unverified_secondary`
= 0.25 was registered to describe: a plausible value from a secondary source,
transcribed from memory. Flipping a flag on that basis would not be verification
that happened to be automated — it would be the project's central failure mode,
committed by the mechanism built to name it, and it would silently convert every
downstream band from 0.25 to 0.05 on no evidence at all.

So the correct output of this exercise is a **work order for a human**, not a
diff:

1. Obtain IFCT 2017 (NIN Hyderabad).
2. Look up the eight rows in the table above, in that order. Six of them
   (`rice_cooked`, `rajma_cooked`, `toor_dal_cooked`, `urad_dal_raw`,
   `rice_milled_raw`, `potato_boiled`) carry 91.9% of library protein between
   them and are what actually decide whether the 0.15 protein ceiling can be
   cleared.
3. Record the published food code in `ifct_code` and set `verified` per row.
4. Prefer IFCT's own cooked-state entries; where absent, convert through a
   registered yield factor, never an inline multiplication.

What that would buy: a verified row carries a 0.05 composition band, which **is**
below the 0.15 protein ceiling. But the band is a *weighted mix*, so a recipe
clears the ceiling once its protein-dominant ingredients are verified — it does
not need all of them. Measured per recipe:

| Recipe          | Verifying these clears 0.15                       |
| --------------- | -------------------------------------------------- |
| `rajma_chawal`  | `rajma_cooked` alone -> 0.1256                     |
| `sambar_sadam`  | `rice_cooked` + `toor_dal_cooked`                  |
| `masala_dosa`   | `urad_dal_raw` + `rice_milled_raw`                 |

Five rows, not six — `potato_boiled` is not needed for the protein ceiling. (An
earlier draft of this section said six and inferred it from an all-rows test;
`docs/audit_log.md` finding 10.)

So verification is a threshold crossing with a specific, small target set, not a
general improvement. Until someone opens the source, the status below stands
unchanged.

**Which macro that work does and does not fix (2026-08-02).** Measured: verifying
every row would take the reference plate's energy band from 27% to 6.89% and its
protein band from 25% to 5%, which clears the eligibility ceilings and is the
whole point. It does **not** improve the energy *confidence* picture at all,
because `composition.verified_primary` (0.05) and `tolerance.energy_default`
(0.05) are the same number and the band stays wider than the room the tolerance
leaves. Fat, carb, fibre and sodium do clear their tolerances after verification.
`docs/audit_log.md` finding 21; options in
`docs/design/tolerance_versus_band.md`, none chosen.

### `dev_mode` versus `validated`

`core/planner` therefore carries two distinct designations, implemented as of
Phase 2 (`core/planner/candidates.py::build_candidate_pool`, parameter
`dev_mode: bool`):

- **`validated`** (`dev_mode=False`, the default) — a recipe that misses an
  eligibility ceiling is excluded from the candidate pool outright, recorded
  in `CandidatePool.excluded`. Against today's real library this empties the
  pool for any protein-critical target, by the above — that is the honest
  result of unverified data, not a bug in the filter (see
  `tests/test_planner_candidates.py::TestUncertaintyEligibility::
  test_every_real_recipe_is_excluded_in_validated_mode`).
- **`dev_mode=True`** — plan generation and testing proceed on admittedly
  unverified data; a recipe that misses a ceiling is kept but recorded in
  `CandidatePool.flagged` rather than silently treated as validated. This is
  the only mode that returns anything against today's real library, and the
  only mode Phase 2's own tests exercising real recipes use for anything past
  the eligibility filter itself.

`dev_mode` is a **deliberate suspension of a stated invariant**, not a
convenience flag. Its exit condition is named: a human opens IFCT 2017 and flips
`verified` per row, at which point the composition band drops to 0.05 and the
ceilings become satisfiable. A later phase (API/web) must still plumb
`dev_mode`/`CandidatePool.flagged` into any rendered plan's disclosure — see
the paragraph below on artifacts surviving without context; Phase 2 records
the flag on the pool, it does not yet render it anywhere.

#### Scope of the exit: one template, named deliberately (2026-08-09, D7)

The exit condition above is stated over the whole library, which is why it has
never looked reachable — 28 of 29 rows, none of them anyone's afternoon. It is
**narrowed here, as a choice rather than a quiet gap, to the ingredient rows
reachable from `north_lunch`**: the first plan the project intends to stand
behind is one plate, not a library.

That is ten rows — `wheat_atta_raw`, `paneer_fresh`, `soya_chunks_dry`,
`onion_raw`, `tomato_raw`, `sunflower_oil`, `ginger_garlic_paste`,
`garam_masala`, `green_chilli`, `salt_iodised`. (`water` is the eleventh and is
already verified.) None of them carries an IFCT code today, so the work is
"find the code, then transcribe", not "transcribe" — and none of the four rows
that *do* carry real codes from 2026-07-24 appears on this plate.

**The narrowing is worth doing, and that is measured rather than assumed.**
`docs/design/probes/d7_verification_horizon.py` computes what the plate's
unverified-energy fraction would be if those ten rows were verified, against
`CLAUDE.md`'s ~15% shipping threshold:

| scenario | unverified energy | fraction | |
| --- | ---: | ---: | --- |
| today | 931.2 / 931.2 kcal | 100.0% | does not ship |
| the ten ingredient rows verified | 88.4 / 931.2 kcal | **9.5%** | **ships** |
| those *and* the process constants | 0.0 / 931.2 kcal | 0.0% | ships |

So the ten rows are sufficient on their own. The process constants — which IFCT
does not contain, being a composition table — are **not** on the critical path,
and the whole remaining charge is two `sunflower_oil` lines at 44.2 kcal each,
attributed to `oil_uptake.vegetable_tempering`.

Two things this does not license. The 9.5% has 139.7 kcal of headroom to the
threshold, so the margin is real but not large: adding process-attributed oil
to this plate consumes it, and a second template will have its own answer, not
this one. And the threshold itself is still the provisional ~15% figure
`CLAUDE.md` flags for revisiting — clearing it is a claim about this project's
stated bar, not about nutritional adequacy.

**Nothing here flips a flag.** The probe computes the hypothetical without
touching the registry, deliberately: a probe that sets `verified=True` to answer
a question is one interrupted session away from leaving it set, which is the
failure the flag exists to prevent, committed by the tool built to measure it.

Because a portfolio project's output is a screenshot, "unvalidated" must survive
being viewed without surrounding context. A boolean on a dataclass does not. Any
rendered plan, any `demo.py` stdout, and any README transcript produced in
`dev_mode` must carry that label in the artifact itself.

`demo.py` now exists (2026-07-31, closing `docs/audit_log.md` finding 11 — it
was referenced here and in CLAUDE.md's Commands block for months without being
in the repo). It satisfies the requirement above structurally rather than by
convention: it prints `STATUS: DEV_MODE` plus the derivation's own disclosure
before any number, and repeats the status on its last line, so a truncated
paste still carries the caveat. The status is read from
`DerivedTarget.status`, not hard-coded, so the banner flips on its own the day
a human verifies the last source constant — a hard-coded label would itself
become a false claim about the project's state.

It is also the **reproducibility boundary**. Every transcript in
`docs/audit_log.md` from 2026-07-31 onward must be regenerable by a documented
`demo.py` invocation. Before that date, several results — the library's first
end-to-end plan, the sodium decline, the rung-by-rung ladder table — were
produced by an untracked scratch script and could not be reproduced by anyone
else. Those results have since been reproduced through `demo.py` and matched
(see the finding 11 entry in `docs/audit_log.md`), but the general point stands
and is the reason this file names a command rather than a procedure.

## Validation and the relaxation ladder (2026-07-22, Phase 3)

`core/planner/validator.py`.

### The gate reads the point estimate and nothing else

A plan is valid when its **point estimate** sits inside the target's floors and
ceilings. The interval is computed and returned alongside it, for display, and
is never compared against anything.

This is deliberate and it is the single most important line in the module. The
alternative — passing a plan when its uncertainty interval *overlaps* the
target band — is the more natural-looking implementation and it inverts the
incentive of the entire project: a plan built on worse data has a wider band,
overlaps more, and would therefore pass more easily than one built on better
data. The one mechanism the system has for keeping its numbers honest would
reward the numbers being less honest.

Uncertainty instead acts before a plan exists, as a candidate eligibility
filter (`core/planner/candidates.py`). Uncertain data makes a recipe less
usable. It never makes a plan easier to pass, and it is never a knob the ladder
turns — every rung below widens a *tolerance*, and no rung reads, writes or
scales an uncertainty figure.

### The ladder

When the solver returns zero feasible plans, `plan_within_ladder` widens the
target one rung at a time, in this order, re-solving after each. The first rung
that yields a plan wins; the ladder stops there rather than continuing to the
loosest target that would also have worked.

1. **`sodium_max_fibre_min`** — **widens** the sodium ceiling by 50% and lowers
   the fibre floor by 50%; it does not drop either. Both are one-sided
   general-health guidance rather than the product's core nutritional claim.
   Applied silently. (This entry said "drops … outright" until 2026-08-02,
   describing an implementation CLAUDE.md's round-4 addendum had already
   rejected: an unflagged profile would then be solved against no sodium ceiling
   at all, which is a materially stronger thing than "the least load-bearing
   constraint relaxes first.") Since 2026-08-02 the widening is also **clipped
   to the per-plate sodium guard** — see "Sodium is a day budget" below.
2. **`fat_carb_tolerance`** — 15% → 25%. Least load-bearing macros; they absorb
   whatever energy is left over. Applied silently.
3. **`energy_tolerance`** — 5% → 10%. Applied silently.
4. **`protein_tolerance`** — lowers the protein floor by 15%, and never removes
   it. **Always disclosed**, in the units the target was stated in, e.g. "this
   plan delivers 27.2g of protein against a 32.0g target, a shortfall of 4.8g."

All five tolerance figures are registered constants
(`tolerance.*` in `core/nutrition/citations.py`), not literals — the same
constants `simple_target` reads for its defaults, so the ladder and the default
target constructor cannot drift apart.

The disclosure is enforced structurally rather than by convention:
`ValidationResult.__post_init__` refuses to construct a result that relaxed
protein without a disclosure, or that fails without naming a specific
violation. A generic decline is not representable.

Two behaviours worth naming because they are easy to get wrong:

- **The feasibility pre-filter is re-run per rung**, against that rung's
  widened target. Pre-filtering once against the original target would leave
  every later rung searching a set already pruned to fit the target it is
  trying to widen. In the fixture case this is the difference between 17 and
  141 surviving combinations, and the plan actually chosen is one of the
  recovered ones.
- **A fully locked rung is skipped, not run-and-ignored.** A rung whose every
  macro is locked by a clinical flag does not appear in `relaxation_applied`,
  because reporting a relaxation that did not happen misdescribes the plan.

### Known limitation: the ladder is cumulative, so it can over-relax

Rungs apply in order and cumulatively, which is what CLAUDE.md specifies
("relax in this order, and only this order"). A consequence: a profile that
only needs protein relaxed still arrives there with sodium dropped and
fat/carb/energy widened, because those rungs fired first and did not help. The
plan is still validated against the target it was solved against, and the
weighted-deviation objective keeps it near the ideal points regardless, but the
target it cleared is looser than it strictly needed to be. Fixing this would
mean searching rung subsets rather than prefixes, which trades a stated,
auditable order for a search — not obviously the right trade for a safety
mechanism, and not made here.

## Results are reproducible across processes, not just across reruns (2026-08-02)

`CandidatePool.for_slot` returns candidates sorted by `component.id`, and that
sort is load-bearing rather than cosmetic. `TemplateSlot.accepted_categories` is
a `frozenset`; Python randomises string hashes per process; iterating it
directly made candidate order — and therefore combination order, and therefore
every `demo.py` transcript — depend on `PYTHONHASHSEED`. Two runs of identical
code on one machine produced different output.

Measured before and after (`docs/audit_log.md`, finding 18): 12 hash seeds gave
**2 distinct enumeration orderings** before, **1** after. The verdict, the
selected plate and its score were identical at every seed both before and after
— checked on the real library and on the 144-combination synthetic fixture — so
no published result ever depended on a seed. **"Nothing changed" is a statement
about this library at this size**, not a guarantee: `core/planner/solver.py`
sorts plans by score with a stable sort, so among equally-scoring plans the one
enumerated first wins, and today's top-two scores differ by 18–24%. With a
larger library that path decides which plate a user is served.

`tests/test_planner_determinism.py` checks this by spawning subprocesses under
different seeds. That is the point of it: a determinism claim has to be checked
across the thing it claims independence from, and nothing inside one process
can. The first draft of those tests passed against the defect they were written
to catch — see the audit log for why, and for the pattern this is the second
instance of.

## Sodium is a day budget, not a share of one (2026-08-02)

Until 2026-08-02 every bound in a day target was scaled to a meal by the meal's
energy fraction, sodium included: `nutrient.sodium_max_mg` (2000 mg/day) ×
`meal_split.energy_fraction_lunch` (0.35) = a **700 mg per-lunch ceiling**.

That was not a defensible bound and is no longer used. 700 mg is not a figure
any guideline states. It is a *daily population* guideline apportioned by
calories — and apportioning it that way forbids the ordinary, entirely healthy
pattern of a salty lunch offset by a plain dinner. The 0.35 is itself a
`PROJECT_DECISION` this project's own registry describes as "the customary 'big
lunch' shape of an Indian day, nothing more."

Sodium is now checked against **what the day has left**:

```
remaining = 2000 - (sodium already spent by other meals today)
ceiling   = min(remaining, day_budget.absurdity_fraction x 2000)
```

Only sodium. Fibre stays proportional because its target already derives from
energy (14 g/1000 kcal), so splitting it by the energy fraction is
self-consistent. Iron, calcium and B12 are not budgeted because **they have no
target at all** — they are computed, displayed, and never gated.

### Three limitations, stated rather than smoothed over

**1. The guard is a chosen number, and it was chosen after its effect was
known.** `day_budget.absurdity_fraction = 0.70` exists because a
remaining-budget check alone puts *no limit whatsoever* on the first meal of a
day — with nothing spent, the whole day is available. Its derivation, "twice the
largest meal split," sounds principled and is not: those splits are themselves
project decisions. It is a **plausibility guard on one eating occasion, not a
nutritional claim**, and it is graded `PROJECT_DECISION`, which makes it
categorically ineligible to count as reviewed.

**2. The guard never relaxes, which is stricter than what it replaced.** It is
registered as a *hard ceiling*: the relaxation ladder may widen the remaining
budget but may not widen past the guard. That is a never-relaxing per-plate
fraction of a daily figure — the shape this change set out to remove, retained
deliberately in one place. The alternative was worse and was measured: rung 1
widens sodium by 50%, so a widenable guard at 0.70 would permit a single plate
to carry **105% of a whole day's sodium**.

**3. A user who plans one meal and never returns is served worse than before.**
Under the old model their plate was held to 700 mg. It is now held to 1400. If
they never plan another meal, the system permitted a saltier plate and can make
no claim at all about their day. Any statement about a day with unplanned meals
left in it must be conditional — "within your daily sodium *if* the rest of the
day stays under N" — never a flat claim. This is a real regression for
single-meal use, accepted because the 700 mg bound it replaces was not measuring
anything.

### The day boundary is undecided, and the trigger is recorded

`DayLedger` carries no date and no timezone: `core/` is handed a ledger and
never asks what day it is, so nothing in the current design needs a day
boundary. Deferring this assumes exactly two things, both true today: nothing
persists a ledger, and the ledger a caller sends is authoritative.

**It becomes blocking at the first change that persists a planned meal keyed by
`(user_id, date)`.** That is where a late dinner starts spending today's or
tomorrow's sodium, and `core.schemas.Profile` has no timezone field to decide
with.

### Where this is going

The guard is a stepping stone, not the end state. Two successors are known:

- **Reserve instead of guessing.** Rather than capping at a chosen fraction,
  subtract what the day's *unplanned* meals must minimally cost:
  `ceiling = 2000 - spent - Σ cheapest_reachable(unplanned slots)`. That bound is
  derived from the recipe library rather than chosen, needs no constant at all,
  and reuses machinery that already exists (`combinations.macro_bounds`). It is
  **inert today**: `south_breakfast` and `north_dinner` enumerate zero
  combinations, so the reservation is zero. It becomes live the moment each of
  those templates can enumerate at least one combination.
- **Take sodium off the relaxation ladder entirely.** A day budget is not a
  tolerance, so arguably no rung should touch it. Deferred rather than done:
  it would make rung 1 fibre-only and therefore skippable, changing
  `relaxation_applied` for every profile — too broad a change to ride along with
  the sodium work itself. This is the correct end state.

## Citations: mechanism must match, not just format

`Evidence` carries a `phenomenon` field stating precisely what physical process
the source measured, distinct from `summary`. Every `Constant` carries an
`applied_to` stating the process it is used for. A registration where those two
describe different mechanisms is the actual hole in a citation defence — a real,
findable, correctly-formatted citation for the wrong process passes every
automated check while being wrong, and unlike a fabricated citation it is not
falsifiable by anyone without domain expertise.

Concretely: deep-fat frying oil-absorption literature does not describe a
griddled dosa. Immersion frying deposits oil into a crust as steam condenses
during post-fry cooling; a dosa picks up oil spooned around the rim of a tawa.
The specific paper found and refused is recorded in `REJECTED_CITATIONS` in
`core/nutrition/citations.py`, so the next person to search does not have to
re-derive the rejection.

Where no matching source exists, the constant is registered as a
`PROJECT_ESTIMATE` with `verified=False` and a wide band. `Evidence` refuses to
let a project estimate be marked verified at all: there is no document to open.

## Target derivation from a profile (2026-07-23)

`core/nutrition/targets.py` turns a `Profile` into an energy/protein/macro
target. This is the first place the product computes a number a user would act
on, so two things are stated plainly here.

**The pipeline is deterministic and every coefficient is cited.** BMR comes from
Mifflin-St Jeor (`bmr.mifflin.*`), scaled by an activity factor (`activity.pal_*`)
to maintenance TDEE, then by a goal factor (`energy.goal_factor_*`). Protein is
`weight × g/kg` (`protein.g_per_kg_*`, anchored on Morton 2018) **divided by a
per-diet DIAAS factor** (`diaas.*`): a lower-quality-protein diet needs *more*
grams to deliver the same utilisable protein, so a vegan target is higher than a
non-vegetarian one for the same body. Fat takes the IOM AMDR midpoint; carbohydrate
is the remainder. No coefficient is written inline — all live in `citations.py`.

**These targets are `dev_mode`, never `validated` — and cannot become validated
as currently sourced.** `DerivedTarget.status` is computed from the backing
evidence, not hard-coded. The activity factors, the per-diet DIAAS rollup, and
the goal energy deltas are `PROJECT_ESTIMATE`/`PROJECT_DECISION` evidence, which
`Evidence` forbids from ever being `verified=True` (there is no single document
to open for "the DIAAS of a vegetarian day"). So even if a human verifies
Mifflin, Morton, the IOM DRIs and the WHO sodium guideline, the status stays
`dev_mode`. `tests/test_nutrition_targets.py::
test_targets_can_never_be_validated_while_they_rest_on_project_estimates` asserts
exactly this. A one-sentence disclosure accompanies every derived target; the
displayed energy figure carries the equation's ~±14% band (Mifflin's own RMR
prediction spread combined in quadrature with activity-factor uncertainty), not
a false-precise point.

The DIAAS per-diet values are deliberately conservative estimates, not measured
figures. Verifying them is not possible in the `Evidence.verified` sense; the
honest improvement path is to replace the single per-diet rollup with a
composition-weighted DIAAS computed from the actual recipes once `core/foods`
protein data is verified, at which point the estimate can be retired rather than
verified. `docs/audit_log.md` is where any finding against this reasoning belongs.

## Protein quality no longer inflates the target (2026-08-02, slice 2)

Until this slice, a low-DIAAS diet raised the protein *floor*:
`quality_adjusted_g = base_g / diaas`, and that inflated figure was what the
planner gated on. A vegetarian at 70 kg was told to eat 124.4 g/day instead of
112.0 g.

**That answers a quality problem with volume.** Eating 12 g/day more protein of
the same limiting-amino-acid profile supplies more of what was already there,
not the amino acid that was short. Quality is a constraint on *which sources*
fill a target, not a multiplier on the target. `ProteinTarget.base_g` is now the
floor; `quality_adjusted_g` is still computed and displayed, and nothing gates
on it.

Measured, reference profile (70 kg / 175 cm / 28 / male / moderate / maintain /
vegetarian). All four figures were predicted before the change was made and all
four held:

| | v1 | v2 |
| --- | --- | --- |
| protein day floor | 124.4 g | **112.00 g** |
| carb day target | 341.6 g | **354.01 g** |
| lunch protein floor | 43.6 g | **39.20 g** |
| lunch carb ceiling | 137.5 g | **142.49 g** |

### The carbohydrate side effect, which nobody asked for

`_compute_macros` derives carbohydrate as the energy **remainder** after protein
and fat. Removing 12.44 g of claimed protein hands 49.8 kcal back, so the carb
target *rises* by 12.44 g — one gram of carbohydrate per gram of protein no
longer claimed, which is the 4 kcal/g identity and a usable check on the sign.

It is arguably correct: the old carb figure was the remainder after an inflated
protein number, so it was understated for the same reason the protein floor was
overstated. But "arguably correct" is not "intended", and `carb_g` has never
been examined on its own terms. Pinned by
`tests/test_nutrition_targets.py::test_the_carb_target_moved_with_the_protein_floor`
with the arithmetic in comments, because a slice-2 test checking only protein
would have let this ship unnoticed.

**Second-order, and unpredicted: the carb target is now diet-independent.**
`base_g` does not depend on diet, so neither does the remainder. Previously a
vegan and a non-vegetarian of identical body and goal were handed carb targets
about 37 g apart on the strength of a protein-quality constant.

### The gap this opens, stated rather than papered over

**Between this slice and the quality-source rule (slice 4), `Profile.diet`
changes no target value at all.** The per-diet `diaas.*` constants are still
registered and still reported; nothing reads them for gating. Two profiles
identical but for diet now receive identical targets.

That is a real capability gap, not a cleanup. It is asserted directly by
`test_diet_pattern_no_longer_moves_the_protein_floor` and
`test_the_carb_target_is_now_diet_independent_too`, which exist to make it
visible: when slice 4 lands, quality must start mattering somewhere again, and
if it does not, those two assertions are the ones that should look wrong to
whoever reads them next. Slice 4 is blocked on the ingredient set — `curd_dahi`
is the only row above DIAAS 0.62, so shipping the rule early would make every
plate decline.

### What it did to the plates

The reference profile gets a plate for the first time. `north_lunch` and
`north_dinner` now pass; both declined before, on sodium.

```
north_lunch   phulka x4, dal_tadka x2, onion_raita x2
              910.0 kcal, 36.8 g protein, 23.4 g fat, 136.9 g carb, 1389.4 mg sodium
              4 relaxation rungs, protein disclosed:
              "delivers 36.8g of protein against a 39.2g target, a shortfall of 2.4g"
north_dinner  phulka x3, dal_tadka x1, aloo_sabzi x1, onion_raita x2
              794.4 kcal, 28.7 g protein, 1371.7 mg sodium
```

**This is slice 2 making the plate easier to reach, and that is expected rather
than good.** A lower protein floor gives the solver more room to answer protein
with dal — which is precisely the plate the quality-source rule is meant to
reject. The correction arrives with slice 4. Recording it here so the
improvement is not mistaken for a validation of the change.

The two South templates still decline, and `south_lunch`'s decline changed
shape: protein is now reachable, so the solver reaches for a bigger plate and
blows energy, fat and sodium instead — sodium went from 2441.8 mg to 2836.8 mg.
See `docs/audit_log.md` finding 22.

## Protein has per-meal bounds (2026-08-02, slice 3)

Two registered `PROJECT_DECISION` constants, both fractions of the **day protein
floor** so they move with the profile instead of being absolute grams:

| Constant | Value | Reference profile (day floor 112 g) |
| --- | --- | --- |
| `protein.meal_floor_fraction` | 0.15 | 16.8 g |
| `protein.meal_ceiling_fraction` | 0.50 | 56.0 g |

Neither has a source and neither should acquire one carelessly. The per-meal
protein literature that exists (leucine-threshold and per-meal dose work)
measures the muscle-protein-synthesis response to a bolus, which is not what
this product optimises; attaching it would be the mechanism-mismatch failure the
`phenomenon` field exists to prevent.

### The floor is a guard beneath the share, not a replacement for it

`docs/design/target_model_v2.md` §3's table reads as though 0.15 replaces the
energy-fraction share. Taken that way it would move the reference lunch protein
floor from 39.2 g down to **16.8 g** — a 22 g loosening nobody asked for, and the
same shape of unrequested side effect slice 2 had to be caught for.

The bound's purpose is that no meal is *empty* of protein. That is a guard, so it
is applied as `max(share, guard)`:

```
breakfast  share 0.25 x 112 = 28.0   guard 16.8   floor 28.0
lunch      share 0.35 x 112 = 39.2   guard 16.8   floor 39.2
dinner     share 0.30 x 112 = 33.6   guard 16.8   floor 33.6
snack      share 0.10 x 112 = 11.2   guard 16.8   floor 16.8   <- the only slot it binds
```

The snack slot is the only one whose share falls below the guard, which is
precisely the case the bound exists for.

### The ceiling is a backstop, not a shaper — and it is measurable

The ceiling is derived from the day **floor**, because protein has no day
ceiling: the day target states a minimum and nothing above it. So it is half of
a floor, not half of a ceiling.

It cannot be reached by the solver's own preferences. The solver scores by
deviation from each macro's target *point*, and the protein point is the energy
share (0.35 × day floor for lunch) while the ceiling is 0.50 × day floor — the
point sits below the ceiling for every slot. **The ceiling binds only when a
different constraint drags protein up**, i.e. an energy floor that needs more
servings. That is exactly the three-katoris-of-dal case it was introduced for.

Measured, synthetic pool, day protein floor 40 g (ceiling 20.0 g), energy 2400
kcal — the same target twice, differing only in the registered fraction:

```
ceiling 0.50 (real)  declines: energy_kcal below_floor 510.0 vs 756.0
ceiling 10.0 (off)   returns:  26.5 g protein, 800.0 kcal
```

The first draft of the test for this passed vacuously, against a target where
the collision never occurred; the control run is what caught it.

**No verdict moved on the real library.** All four templates return exactly what
they returned before slice 3 — `north_lunch` and `north_dinner` pass, the two
South templates decline unchanged. The ceiling is a guard against a plate this
library cannot currently build.

### Known limitation carried out of this slice

When the ceiling empties the feasible set, the decline names **energy**, not
protein — the survivors are reported failing whatever they fail next, because
the pre-filter and solver discard silently. See `docs/audit_log.md` finding 24.

## Clinical flags do not tighten a target (2026-07-23)

`Profile.clinical_flags` is read in exactly one place today:
`core/planner/validator.py::LOCKED_CONSTRAINTS`, which stops the relaxation
ladder from *loosening* a constraint for a flagged profile. `core/nutrition/
targets.py::derive_target` does not read `clinical_flags` at all — a
hypertensive profile and a general profile get the identical
`nutrient.sodium_max_mg` ceiling out of target derivation. Locking a ceiling
from being raised and lowering it in the first place are different things,
and only the first exists.

This is a decision, stated here because the onboarding page is about to put a
sodium number on screen next to a clinical-flags checkbox, and a user who
checks "hypertension" and sees the number not move would reasonably read that
as a bug rather than the documented behaviour.

**Decision: target-time tightening is out of scope for this increment, and
stays out until there is a real cited number to put there.** The reasons:

- `core/nutrition` cannot see `LOCKED_CONSTRAINTS` even if it wanted to reuse
  it — that mapping lives in `core/planner`, and `core/nutrition` must never
  import `core/planner` (CLAUDE.md, "Architecture"). A condition-specific
  ceiling would need its own registered constant in `core/nutrition/
  citations.py` (e.g. a WHO/AHA hypertension-specific sodium limit, likely
  ~1,500 mg against the general 2,000 mg used today), not a borrowed mapping.
- That constant does not exist yet. Registering one now, under time pressure
  from a UI page, is exactly the "transcribed from memory, marked
  `verified=False` forever" failure mode this project's citation discipline
  exists to slow down. It should be added deliberately, with its own
  `Evidence.phenomenon` (a hypertension-specific dietary sodium ceiling is a
  different claim than a general-population one, not the same number
  narrowed), when clinical targets are actually built out — not folded
  silently into this increment.

**What is done instead, so the gap is structural rather than a paragraph
nobody reads:** `derive_target` now inspects `profile.clinical_flags` and, if
any are set, appends a mandatory warning to `DerivedTarget.warnings` — visible
in the API response's `warnings` array and therefore renderable on the
onboarding page next to the checkbox — stating plainly that the displayed
numbers are general-population values, that the flag only affects plan
generation later, and that this is not a substitute for clinical guidance.
`tests/test_nutrition_targets.py::TestClinicalFlagsDoNotTightenTargets` pins
this: a flagged profile's `sodium_mg_max` equals an unflagged profile's
exactly, and the warning is present; an unflagged profile carries no such
warning.

The onboarding page must render this warning when present, not just the
headline numbers — see `web/onboarding.html`.

## Known limitations, Phase 1

1. **The ingredient data is a hand-entered fixture set, not IFCT — with four
   exceptions pending human sign-off (2026-07-24).** 25 of 26 rows are
   `verified=False` (the exception is `water`, whose macros are all zero) and
   21 of 26 have no `ifct_code`. Four rows — `rice_milled_raw` (A015),
   `rajma_raw` (B020, new), `toor_dal_raw` (B021, new), `potato_raw` (F006,
   new) — now carry real IFCT 2017 codes and values, extracted from the Sahu &
   Sahu machine-readable re-publication of IFCT 2017 (Zenodo DOI
   10.5281/zenodo.7088653; the primary `IFCT2017.pdf` itself exceeded this
   build's fetch tooling). Per CLAUDE.md, **this build did not flip
   `verified` on those four rows** — extraction by this project's own tooling
   is not the same as a human opening the primary source, and self-attestation
   of verification is the exact failure mode the round-4 addendum names. They
   stay `verified=False`, each with a `source_note` recording exactly where
   the values came from, pending a human cross-checking them against the
   primary PDF and flipping the flag themselves. The remaining rows are
   unchanged approximations of commonly published figures transcribed from
   memory. See `data/raw/ifct/README.md` for the real-ingest TODO, and
   "Nothing can currently ship as validated" above for what that implies for
   the planner (composition uncertainty is driven by `Ingredient.verified`,
   not by whether an `ifct_code` is present, so this changes nothing about
   eligibility yet).

   The two edible-oil rows (`gingelly_oil`, `sunflower_oil`) are a distinct
   case, also checked 2026-07-24: IFCT 2017 does carry codes for them (T004,
   T012), but their tabulated rows report `energy_kcal=0` and every
   micronutrient at `0` alongside `fat=100g`, i.e. **this source does not
   tabulate a full nutrient panel for oils**, only a fatty acid profile
   elsewhere in the tables. IFCT cannot close this gap regardless of who
   opens it; a different source (e.g. USDA FoodData Central) would be needed,
   as separately scoped work. Their rows say so explicitly rather than reading
   as an ordinary unverified gap.

2. **Every process constant in the library is unverified.** Yield factors, oil
   uptake and household measures are all project estimates or
   transcribed-from-memory national-table figures. `citations.unverified()` and
   `retention.unverified_processes()` report this honestly, and a test asserts
   nothing has been quietly flipped.

3. **The Atwater reconciliation is a coherence check, not a validation of
   truth.** It catches transcription slips and unit confusion; it cannot catch a
   row that is internally consistent and still wrong. `carb_g` is total
   carbohydrate including fibre, but — corrected 2026-07-24 — fibre is now
   charged at its own rate (`atwater.fibre_kcal_per_g`, 2 kcal/g) rather than
   the general 4 kcal/g carbohydrate rate, matching IFCT 2017's own stated
   energy methodology (`energies/index.csv` in the same re-publication above).
   This was found, not theorized: rajma's real IFCT figures (16.57 g
   fibre/100 g) failed the 15% reconciliation gate at 19% under the old,
   flat-4-kcal/g formula, and pass at 8% once fibre is charged correctly. One
   existing hand-entered fixture row, `garam_masala` (25 g fibre/100 g, the
   highest in the library), crossed the same gate under the corrected formula;
   its `energy_kcal` was nudged from 379 to 321 kcal — its own fibre-aware
   reconciliation value — since it was never a sourced number to begin with,
   only an internally-consistent approximation.

4. **Household measure weights vary by household more than most nutritional
   constants do.** Hence the double-digit uncertainty bands on all of them. A
   recipe may override the generic measure weight for its own dish, and the
   three example recipes do.

5. **Three recipes is not a library.** The combination-space arithmetic in
   Phase 2 must be computed against real post-filter recipe counts, not
   asserted from this set.

   Made concrete on 2026-07-24 by wiring `core/planner` end to end
   (`core/planner/plan.py`, `POST /api/plan`): the real library does not
   merely produce a *small* combination space — it produces **zero**
   combinations for all four templates, unconditionally. Each of the three
   recipes fills exactly one slot of exactly one template (`masala_dosa` ->
   `south_breakfast.tiffin_item`, `sambar_sadam` -> `south_lunch.rice_base`,
   `rajma_chawal` -> `north_lunch.legume_curry`), and every *other* required
   slot in that template — `south_breakfast`'s gravy and chutney,
   `south_lunch`'s gravy/vegetable/curd, `north_lunch`'s grain base — has no
   candidate at all. `core/planner/combinations.py::enumerate_combinations`
   returns `()` the moment any required slot is empty, before the feasibility
   pre-filter or the solver run and independent of the target or `dev_mode`.
   So every `/api/plan` call against today's data declines with a
   `no_candidates` violation, regardless of who is asking — proven for all
   four templates in
   `tests/test_planner_plan.py::TestRealLibraryDeclinesEveryTemplate`, and
   against a live server in this session (see the "Build status" transcript
   in `CLAUDE.md`). This is stronger and more useful to know than "the
   combination space is small": adding a fourth recipe in an already-filled
   category would still produce zero combinations, because the gap is
   *category breadth* (chutney, gravy, vegetable, curd, plain rice/roti — none
   exist yet), not recipe *count*.

   **CLOSED 2026-08-02 (T4).** Six recipes filled the missing categories —
   `sambar`, `coconut_chutney`, `carrot_poriyal`, `thayir_plain` (curd),
   `aloo_sabzi`, `carrot_kootu` — and every required slot in every template now
   has a candidate. Measured combination counts: `south_breakfast` 1,
   `south_lunch` 3, `north_lunch` 8, `north_dinner` 2. `no_candidates` no
   longer appears for any template, which is now asserted by construction in
   `tests/test_planner_plan.py::TestEveryTemplateIsPopulated`, parametrised over
   `ALL_TEMPLATES` so a template added later joins the strong claim by default.

   The category-breadth reading held up exactly: **five** recipes would have
   sufficed, not six, because `sambar` is accepted by both
   `south_breakfast.gravy_accompaniment` and `south_lunch.gravy` — one file,
   two templates. `carrot_kootu` is the sixth and is there for a different
   reason: `enumerate_combinations` builds selections with
   `itertools.combinations`, which cannot repeat a component, so
   `south_lunch.vegetable` (min 1, max 2) behaved exactly like a fixed-length
   slot while it had a single candidate. A second candidate is what makes the
   only genuinely variable-length slot in `core/foods/templates.py` testable
   against real data at all.

### Every template enumerates, and every template still declines (2026-08-02)

Closing limitation 5 did not make the system able to serve a plan for the
reference profile, and the reason changed rather than went away. All four
templates decline for the reference profile — but on **named macros** now,
with a walked relaxation ladder, instead of the empty-pool shortcut:

```
south_breakfast  fat 24.7 > 24.6 | protein 18.4 < 26.4 | sodium 1790.4 > 1400.0
south_lunch      protein 32.3 < 37.0 | sodium 2441.8 > 1400.0
north_lunch      sodium 1649.3 > 1400.0
north_dinner     energy 942.6 > 848.5 | fat 33.4 > 29.5 | sodium 1891.4 > 1400.0
```

`north_lunch` and `north_dinner` do solve for other profiles (54 and 28 of a
192-profile sweep respectively, some with zero relaxation rungs), so the
pipeline demonstrably produces plates now — `north_dinner` never had before.

**Sodium is the constraint in all four**, and this time the diagnosis is backed
by per-combination reach rather than read off a single blocking figure — the
error made on 2026-08-02 in the other direction. Two of `south_lunch`'s three
combinations have a sodium *floor* above the guard (1437.0 mg and 1677.1 mg
against 1400 mg) with every component at its minimum count, so those two are
unreachable for **any** profile, not merely a demanding one. See
`docs/audit_log.md` finding 22.

#### Superseded the same day for the two north templates (2026-08-02, D2a)

The heading above is left standing because it was true when written, and the
correction is more informative than an edit would be. After the three
high-quality protein rows landed, **`north_lunch` and `north_dinner` pass for
the reference profile with zero relaxation rungs** — the first plates served to
that profile on the real library without walking the ladder:

```
north_lunch   phulka x4 + dal_tadka x2 + tofu_bhurji x1
              929.8 kcal, 42.6 g protein, 25.8 g fat, 133.9 g carb, 1209.0 mg Na
north_dinner  phulka x4 + dal_tadka x1 + tofu_bhurji x1
              756.8 kcal, 35.4 g protein, 20.2 g fat, 111.3 g carb, 889.2 mg Na
```

The cause is sodium, not protein: a katori of tofu bhurji fills the `sabzi` slot
with less salt per calorie than aloo sabzi, so the solver reaches the energy
floor without breaching the 1400 mg per-plate guard. The two south templates
still decline, and finding 22 is untouched — `south_lunch` still has two
combinations unreachable at their minimum counts.

#### And superseded for the two south templates on 2026-08-07 (D3)

All four templates now pass for the reference profile: south_breakfast at zero
rungs, south_lunch at three. The diagnosis in the section above — **sodium is
the constraint in all four** — is the one that held; D3's fix was two
low-sodium recipes (`idli`, `steamed_rice`) plus one qualifying protein source.
Finding 22 is still untouched: `south_lunch`'s two minimum-count-unreachable
combinations are still unreachable, and the plate that now passes clears the
guard by 8.9 mg. See "Making the south templates reachable" below.

### DIAAS values are authored, and the quality rule turns on them (2026-08-02)

`paneer_fresh` (1.00), `tofu_firm` (0.65) and `soya_chunks_dry` (0.85) were
added so the quality-source rule has something to select; `curd_dahi` at 1.09
was previously the only row above 0.62. **None of the three DIAAS figures comes
from a source anyone opened.** They are recollections of published ranges, and
each was entered at the low end of its range rather than the midpoint, because a
high DIAAS is what makes a row qualify and the cheapest authoring path must not
produce the most permissive output.

Two consequences are stated rather than left to be found:

- **Tofu does not qualify.** 0.65 is below the 0.75 threshold. That is a
  statement about how much this project trusts its own number, not a nutritional
  finding about tofu, and `data/recipes/tofu_bhurji.yaml` says so in the file.
- **Vegan quality protein rests on one authored number.** `soya_chunks_dry` is
  the only vegan-eligible row above the threshold. If 0.85 is wrong, every vegan
  plate's quality verdict is wrong with it.

The rows are `verified=false` and carry the same 0.25 composition band as every
other hand-entered row: `dev_mode=False` still empties every candidate pool.
Nothing was upgraded to make the rule work.

### South breakfast can now reach a quality source (2026-08-02, D2b-i)

`SOUTH_BREAKFAST` originally accepted `tiffin`, `sambar`/`kuzhambu`,
`chutney`/`podi` and `beverage`, and no high-quality protein source belongs in
any of them. A per-meal quality floor would therefore have made that template
unsatisfiable **structurally** — not because the library is thin, but because
the plate grammar had nowhere to put the thing the rule asks for. That is a
different and worse failure than a decline, because no amount of recipe writing
fixes it.

An **optional** `curd_course` slot closes it, filled by the existing
`thayir_plain@curd`. Optional is the load-bearing word: south lunch's curd
course is required because a South Indian lunch ends with thayir; a breakfast of
idli or dosa with sambar and chutney is complete without curd, and a rule that
needed curd on the plate to be satisfiable would be the same hole-cut-to-fit
error in the opposite direction. Both combinations enumerate.

Eggs would have been the other obvious answer and are deliberately not used:
they belong to the deferred non-vegetarian axis, and nothing here may add a
component a vegetarian profile could be served.

## Protein quality is a rule about sources (2026-08-07, slice 4)

Slice 2 removed DIAAS from the protein target: answering a protein-*quality*
problem by demanding more grams of the same limiting amino-acid profile supplies
more of what was already there. Slice 4 is where quality comes back, as the
thing it always was — a constraint on **which sources** fill the target.

**The rule.** An ingredient qualifies when its `diaas` is present and at or
above `protein.quality_diaas_threshold` (0.75). A plate's qualifying protein is
the protein contributed by qualifying ingredient *lines*, at that plate's actual
integer unit counts. Every plate must carry at least
`protein.quality_meal_floor_fraction` (0.10) × the day protein floor — 11.2 g
for the reference profile, flat on every meal slot.

For the reference library, per serving unit:

| Component | Qualifying protein | From |
|---|---|---|
| `soya_chunk_curry` | 14.56 g | 28 g `soya_chunks_dry` × 52.0/100 |
| `paneer_masala` | 12.81 g | 70 g `paneer_fresh` × 18.3/100 |
| `thayir_plain` | 4.50 g | 145 g `curd_dahi` × 3.1/100 |
| `onion_raita` | 3.97 g | 128 g `curd_dahi` × 3.1/100 |
| everything else, including `tofu_bhurji` | 0 g | — |

### This is a project decision and it is harsh on this exact cuisine

DIAAS is limiting-amino-acid based. A grain-plus-legume plate scores *better*
than either part, because rice is short of lysine and long on methionine and dal
is the reverse. This rule aggregates per ingredient line, so a roti-and-dal
plate gets credit for **neither**. **It understates mixed Indian plates
specifically, which is the exact food this product plans.**

A protein-weighted mean across the component would not have fixed it: the mean
of 0.45 and 0.60 lies between them, and no weighted mean of two numbers exceeds
the larger. Modelling complementarity honestly needs per-amino-acid composition
data the library does not have. The conservative arm was picked and named rather
than dressed up.

The constant is graded `PROJECT_DECISION` with no citation. 0.75 is the boundary
of the band FAO's 2013 DIAAS report is *recalled* as calling "good quality", but
nobody here has opened it, and attaching that reference to a remembered number
would be the mismatched-but-real citation failure the registry exists to
prevent.

### `None` means "does not qualify", and that is the safe answer, not the right one

17 of the 29 ingredient rows carry no DIAAS at all. To this rule, "nobody has
assessed this food" and "this food scores badly" are the same thing. The
ordering is deliberate — CLAUDE.md's round-4 addendum requires that the cheapest
authoring path never produce the most permissive output — but the cost is
concrete: **adding a protein-dense row and forgetting its DIAAS silently makes
that food count for nothing**, and the plan that results looks entirely normal.

### The unsourced field this rests on

See "DIAAS values are authored, and the quality rule turns on them" above. That
section was written before this rule existed; it now describes the most
load-bearing unsourced data in the project. Twelve hand-entered numbers, none
read out of a document, decide which foods a user is told to eat. Three of them
clear the threshold. One of those three (`soya_chunks_dry`, 0.85) carries the
entire vegan case on its own.

Nothing in this slice moved a DIAAS value, the threshold, a salt line or an
evidence grade. `tofu_firm` at 0.65 fails its own threshold and was left
failing.

### What it did to the plates

Measured against the real library for the reference profile
(70 kg / 175 cm / 28 / male / moderate / maintain / vegetarian), before and
after, via `python demo.py plan`:

| Template | Before | After |
|---|---|---|
| `south_breakfast` | declines, 4 rungs, on energy/fat/sodium | declines, 4 rungs, **on quality protein: 8.99 g reachable against 11.2 g** |
| `south_lunch` | declines, 4 rungs, on energy/fat/sodium | declines, 4 rungs, **on quality protein: 8.99 g against 11.2 g** |
| `north_lunch` | passes, 0 rungs: phulka ×4 + dal_tadka ×2 + tofu_bhurji ×1 | passes, 0 rungs: **phulka ×5 + soya_chunk_curry ×1 + paneer_masala ×1** |
| `north_dinner` | passes, 0 rungs: phulka ×4 + dal_tadka ×1 + tofu_bhurji ×1 | passes, 0 rungs: **phulka ×3 + soya_chunk_curry ×1 + aloo_sabzi ×1 + onion_raita ×2** |

The two south templates cannot reach the floor at any count for any profile:
`thayir_plain` is the only qualifying component either can accept, and its
serving unit caps at two katoris — 8.99 g. That is a fact about the library's
breadth, and no relaxation rung can help, because the quality floor is not on
the ladder.

> **Superseded the same day by D3** — see "Making the south templates
> reachable" below. Three recipes were added and both south templates now pass.
> The paragraph above is left standing because it correctly describes what the
> rule did to the library *as it stood*, and because the fix was recipe work: no
> threshold, fraction or DIAAS value moved.

**A cost worth naming:** `north_dinner`'s sodium went 889.2 → 1371.3 mg,
against a 1400 mg absurdity guard. The rule pushed the solver onto denser
protein sources, and those carry salt. It passes with 29 mg of headroom.

### The rule is outside the relaxation ladder

No rung touches `NutritionTarget.quality_protein_floor_g`. The ladder widens
*tolerances* — how far a point estimate may sit from a number. "At least this
much protein came from a qualifying source" is a statement about what the plate
is made of, and there is no coherent 15%-looser version of it. Relaxing it would
mean answering "this plate is all lentil" with "then require less of it not to
be".

The visible consequence: a profile blocked on quality still walks all four
rungs, is relaxed on sodium, fat, carb, energy and protein, and declines anyway.
`relaxation_applied` on such a result therefore reports rungs that could not have
helped. That is reported rather than suppressed, because the target really was
widened that far.

### The day floor is computed and gates on nothing

`protein.quality_day_fraction` (0.33) × the day protein floor = 36.96 g for the
reference profile, carried on `ProteinTarget.quality_source_day_g` and shown in
onboarding. **Nothing enforces it.** Enforcing a day *floor* against a planner
that solves one meal at a time is a reachability question — can the remaining
slots still close the gap? — not a remaining-budget subtraction, and that is its
own slice (`docs/design/target_model_v2.md` §2). This is the second
computed-but-inert figure on `ProteinTarget`; it is inert for a different reason
than `quality_adjusted_g`, which is inert because it was found to be the wrong
answer rather than because the machinery is missing.

### Diet still changes no target number

`Profile.diet` was expected to start moving a target value in this slice. It
does not, and that is the settled position rather than an outstanding gap.

The rule's two levers are the DIAAS threshold — a property of a food — and the
per-meal floor fraction, taken off the day protein floor, which is weight × g/kg
and diet-independent. Making either diet-conditional would mean registering a
constant to close a checklist item, which is precisely what the registry exists
to stop.

**What diet changes instead is the outcome.** It decides which components can
*satisfy* an identical floor:

- Vegetarian north dinner: phulka ×3 + soya_chunk_curry ×1 + aloo_sabzi ×1 +
  onion_raita ×2.
- Vegan north dinner, same body and same 11.2 g floor: phulka ×3 +
  soya_chunk_curry ×2 + tofu_bhurji ×1 — paneer and curd are unavailable, so the
  whole vegan case rests on soya.
- Disqualify `soya_chunks_dry` and the vegan profile **declines on quality**
  while the vegetarian one still passes. Identical targets, opposite verdicts.
  Before slice 4, diet could not do that, because nothing downstream of the
  candidate filter cared where a plate's protein came from.

That last case is pinned in
`tests/test_planner_quality.py::TestDietChangesAnOutcomeNotANumber`.

### Known limitations carried out of this slice

1. **The per-meal floor is flat, not scaled.** Every slot gets 11.2 g, including
   a snack at a quarter of a lunch's energy. Flat is deliberate — the design
   wants most of a day's quality protein free to land in one or two meals, and a
   per-slot share would contradict that — but no template exists for the snack
   slot today, so the case is unexercised rather than resolved.
2. **The decline can now hide the other reasons.** When a bound is *unreachable*,
   `_blocking_violations` reports it from its first branch and returns
   immediately, so the energy, fat and sodium misses that came from the later
   best-plate probe are not shown. The user is told the single truest thing and
   not the whole picture. Recorded in `docs/audit_log.md` as a new observation,
   not fixed here. **Still open after D3**, though no longer visible on the two
   south templates, which now pass — it is a property of `_blocking_violations`,
   not of those templates.
3. **The pre-filter's quality check is a pure optimisation.** Removing it changes
   no verdict, because the solver's own gate catches everything it would have.
   No test can therefore detect its removal, and that is correct rather than a
   coverage hole — but it means the pre-filter check must never be made to carry
   a rule the gate does not also enforce.

6. **DIAAS is populated unevenly, and it is now load-bearing.** `Ingredient.diaas`
   is filled where a commonly cited figure was recalled and left `None`
   otherwise — 17 of 29 rows. **Corrected 2026-08-07:** this item used to read
   "stored but unused. Nothing reads it yet." `core/foods/quality.py` reads it,
   and it decides which dishes a plan may contain. `None` means "does not
   qualify", so the uneven population is no longer a cosmetic gap; see "Protein
   quality is a rule about sources" above. The values carry the same unverified
   caveat as everything else in the fixture.

7. **Composition uncertainty is uniform across macros.** Every macro on a row
   gets the same band from its provenance constant, though the real dispersion
   is not uniform — B12 and iron are measured less reliably than energy, and a
   remembered sodium figure is a worse guess than a remembered protein one.
   `Ingredient.composition_uncertainty` is a per-macro mapping so this can be
   refined per nutrient without a schema change; it is simply populated
   uniformly today. A uniform band is honest about being an estimate; a
   per-macro one invented without a source would not be.

8. ~~**`_depends_on_unverified` over-attributes.**~~ **CLOSED 2026-08-09 (D6);
   see "The unverified-energy fraction, measured correctly" below.** Both
   directions landed together, as this entry said they had to: attribution is
   now per ingredient line, charging composition and process alike, and
   `_depends_on_unverified` no longer exists.

## Making the south templates reachable (2026-08-07, D3)

Slice 4 left both South Indian templates declining for **every** profile. Three
recipes closed that. No threshold, fraction, DIAAS value or salt line was
changed — the diagnosis was that the library was too narrow, and the fix is
entirely in `data/recipes/`.

### The binding constraint was sodium, not quality

This is the part worth reading, because the obvious diagnosis was wrong. The
quality shortfall was 11.2 − 8.99 = **2.21 g**. The actual blocker was that
neither south template could reach its *energy floor* under the 1400 mg sodium
ceiling, which is a `hard_ceiling` no relaxation rung widens — a condition that
predates the quality rule and would have declined those templates anyway.

Measured, per unit, for the reference profile's breakfast target
(610.6–674.9 kcal, fat ≤ 22.59 g, sodium ≤ 1400 mg):

| | kcal | Na (mg) | fat (g) | **mg Na / kcal** |
|---|---|---|---|---|
| `masala_dosa` | 226.6 | 594.2 | 7.02 | **2.62** |
| `idli` (new) | 50.4 | 87.1 | 0.11 | **1.73** |
| `sambar_sadam` | 265.0 | 408.6 | 5.34 | **1.54** |
| `steamed_rice` (new) | 260.0 | 2.0 | 0.60 | **0.008** |

The cheapest complete breakfast (1 dosa + 1 sambar + 1 chutney) was 373.5 kcal
at 1006.6 mg — 393 mg of sodium left to buy 237 kcal, when a second dosa costs
594. Nothing in the library fitted. On the lunch side, `SOUTH_LUNCH.rice_base`
accepts `{rice, mixed_rice}` and the `rice` category was **empty**, so every
plate the enumerator could build used a one-pot mixed rice as its base.

### The three recipes, and what each answers

| Recipe | Category → slot | The constraint it answers |
|---|---|---|
| `idli` | `tiffin` → south_breakfast `tiffin_item` | Sodium *and* fat. Carries **no** qualifying protein. |
| `steamed_rice` | `rice` → south_lunch `rice_base` | Sodium. Carries **no** qualifying protein. Plain rice takes no salt — that is how the dish is cooked, not a health choice made here. |
| `soya_kuzhambu` | `kuzhambu` → both south gravy slots | Quality. 25.0 g dry soya × 52.0/100 = **13.00 g** qualifying protein per katori, clearing the 11.2 g floor in one unit. |

Two of the three exist for salt, not protein. `soya_kuzhambu` is held at the
library's existing 0.53% salting rate, the same as `sambar`, `dal_tadka` and
`soya_chunk_curry` — deliberately, since it exists to relieve a sodium-bound
template and a lower salt line here would be tuning a plate past a ceiling
rather than filling a slot.

**Zero new ingredient rows**, so no new authored DIAAS value. Filter coffee for
the still-empty `beverage` slot was considered and not written: it would need
`milk_whole`, `sugar_white` and a fourth authored DIAAS deciding what people are
told to eat, and the arithmetic above does not need it.

### `soya_kuzhambu` is not `soya_chunk_curry` relabelled

The risk in adding a South Indian dish to reach a protein was writing a North
Indian recipe wearing a south label. `soya_chunk_curry` is an onion-tomato gravy
finished with garam masala and ginger-garlic in sunflower oil — sabzi grammar.
`soya_kuzhambu` uses tamarind as the acid, sambar powder as the spice, gingelly
oil as the fat, and a mustard-and-curry-leaf tempering. Meal maker kuzhambu is
ordinary Tamil home cooking. They share a protein, not a dish.

One consequence is left alone rather than engineered around:
`SOUTH_BREAKFAST.gravy_accompaniment` accepts `{sambar, kuzhambu}`, so
`soya_kuzhambu` enumerates beside idli at breakfast. Kuzhambu with idli is real
food. What decided that was the template's slot vocabulary, written before this
recipe existed — not a category picked here to reach two slots.

### What it did to the plates

Measured via `python demo.py plan`, reference profile, before and after D3:

| Template | Combinations | Before | After |
|---|---|---|---|
| `south_breakfast` | 2 → **8** | declines, 4 rungs, quality 8.99 < 11.2 | **passes, 0 rungs**: idli ×6 + soya_kuzhambu ×1 + coconut_chutney ×2 + thayir_plain ×1 — 623.6 kcal, 1189.8 mg Na, 17.5 g qualifying |
| `south_lunch` | 3 → **12** | declines, 4 rungs, quality 8.99 < 11.2 | **passes, 3 rungs**: steamed_rice ×1 + soya_kuzhambu ×2 + carrot_poriyal ×2 + thayir_plain ×1 — 848.1 kcal, 1391.1 mg Na |
| `north_lunch` | 24 → 24 | passes, 0 rungs | **unchanged, byte-identical** |
| `north_dinner` | 12 → 12 | passes, 0 rungs | **unchanged, byte-identical** |

The north templates could not have moved, and not by luck:
`core/planner/candidates.py` rejects any recipe whose `region` is neither the
template's nor `pan_indian`, and all three new recipes are `south_indian`.

**Why south_lunch still needs three rungs, stated rather than smoothed over.**
It is sodium, not quality. Clearing the 39.2 g protein floor forces two katoris
of `soya_kuzhambu` (647.0 mg); the *required* curd course adds 261.9 and the
*required* vegetable 240–395. That leaves roughly 100–250 mg for the base, which
only unsalted rice fits inside — and the resulting plate lands at 1391.1 mg
against the 1400 mg hard ceiling, with **8.9 mg of headroom**. Energy tolerance
is the rung that admits it, at 848.1 kcal against an unrelaxed 854.9 floor: the
200 g rice cup is a 260 kcal step and there is no assignment that lands inside
the unrelaxed 854.9–944.9 window while clearing protein under the salt ceiling.

### Known limitations carried out of D3

1. **South lunch passes on 8.9 mg of sodium headroom.** Any future recipe that
   nudges that plate — or any profile whose day budget leaves less than a full
   2000 mg for lunch — puts it straight back into decline. This is
   `docs/audit_log.md` finding 22's territory and is not fixed here.
2. **`idli` and `steamed_rice` are the second and third recipes with no
   `process:` line at all**, so every macro derives to a *computed* zero
   process-uncertainty. That is `docs/audit_log.md` finding 2's shape, still
   OPEN, now reachable with three real files instead of one.
3. **`idli` uses `rice_milled_raw` for what is really parboiled idli rice**,
   which IFCT tabulates separately. Stated in the file; the least accurate thing
   in it.
4. **The `beverage` and `crisp` slots are still empty.** Both are optional, so
   neither blocks anything, but the south templates enumerate a narrower space
   than their grammar describes.

## What is not built

The rest of `core/nutrition/` (energy, protein, macros, targets), LLM ranking
and narration, `core/commerce/`, `api/` and `web/`. The subset of
`core/nutrition/` that exists is `citations.py` only.

`core/planner/` as of Phase 3 has `target.py`, `candidates.py`,
`combinations.py`, `solver.py` and `validator.py` — pure functions, no LLM call
anywhere.

`core/schemas/profile.py` exists but is deliberately partial: it records the
body, activity and goal inputs and the clinical flags, and derives nothing.
`Profile` is currently read only for `clinical_flags`; no code turns its body
fields into an energy or protein target yet. `NutritionTarget` is constructed
directly (`simple_target`) rather than derived from a profile, so the numbers
in every test are stated, not computed from a formula that does not exist. That
derivation is `core/nutrition/targets.py`, not built.

The build-status table in `CLAUDE.md` reflects this.
