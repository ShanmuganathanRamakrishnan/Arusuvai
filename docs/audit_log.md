# Audit log

Dated, append-only. Per CLAUDE.md's audit-workflow section, this file is the
artifact: a finding that isn't written here did not happen. Findings are
recorded whether or not they are fixed; the "Disposition" line says which.

Newest entries at the top.

---

## 2026-08-08 — D5: finding 22 re-scoped, and D5's own premise was wrong

Every figure below is from
`PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d5_margins.py`,
reference profile (70 kg / 175 cm / 28 / male / moderate / maintain /
vegetarian), today's `data/` library, `dev_mode=True`. Nothing was edited:
the guard sweep wraps `citations.value_of` in memory and restores it.

### D5's premise, restated and then contradicted

TASKS_2.MD's D5 says: "whether the app can plan a South Indian lunch currently
turns on half a percent of a number nobody derived." That reads the 8.9 mg
figure as the verdict's sensitivity to the guard. It is not. It is the chosen
**plate's** slack against the guard. Those are different quantities, and the
second one was never measured until now.

Measured — the guard moved, everything else held, pass/decline bisected over 40
iterations:

```
  Bisected pass/decline boundary per template (40 iterations):
    south_indian/breakfast: flips at 0.504835 =  1009.7 mg; registered 0.70 = 1400.0 mg is 390.3 mg (27.9%) above it
    south_indian/lunch: flips at 0.545743 =  1091.5 mg; registered 0.70 = 1400.0 mg is 308.5 mg (22.0%) above it
    north_indian/lunch: flips at 0.466169 =   932.3 mg; registered 0.70 = 1400.0 mg is 467.7 mg (33.4%) above it
    north_indian/dinner: flips at 0.436229 =   872.5 mg; registered 0.70 = 1400.0 mg is 527.5 mg (37.7%) above it
```

south_lunch does not stop passing at 1391 mg, or at 1300, or at 1200. It stops
passing at **1091.5 mg** — the guard would have to fall 22% before the verdict
moves. The verdict's margin on the guard is 308.5 mg, not 8.9 mg. **The goal as
written was wrong**, in the specific way TASKS_2.MD's "How to work this file"
anticipates, and this is the third time.

What actually happens as the guard falls is that the plate changes and the
ladder walks further, verdict intact:

```
  0.55 -> guard  1100.0 mg | south_break=pass(2r,1072mg)  south_lunch=pass(4r,1091mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(2r,872mg)
  0.60 -> guard  1200.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(4r,1091mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1148mg)
  0.65 -> guard  1300.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(4r,1246mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1148mg)
  0.70 -> guard  1400.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(3r,1391mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1371mg)
  0.80 -> guard  1600.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(0r,1546mg)  north_lunch=pass(0r,1431mg)  north_dinne=pass(0r,1371mg)
```

The 4-rung south_lunch at 0.55–0.65 is worth noticing on its own: rung 4 is
protein tolerance, which carries mandatory disclosure. A tighter guard does not
turn south_lunch off, it turns it into a plate that has to apologise for its
protein.

### Finding 22, re-stated in its current form — still **OPEN**

The 2026-08-02 wording ("a multi-dish South Indian plate cannot get under the
sodium guard"; two of three south_lunch combinations unreachable at their
minimum counts) is **obsolete**: D3's `steamed_rice` and `soya_kuzhambu` changed
the enumerated set (3 -> 12 combinations), and all four templates now pass. The
finding survives in a narrower form:

> **Sodium is the only bound in the system whose ceiling is a project decision
> with no derivation, and it is simultaneously the bound closest to two of the
> four passing plates.** south_lunch sits 8.9 mg (0.6%) under it; north_dinner
> sits 28.7 mg (2.0%) under it. Both are hard-ceiling contacts — no relaxation
> rung may widen past 1400 mg, so a plate 9 mg over it is a decline with no
> recourse, however loose every other bound is.

Note the correction embedded there: the D5 task asked whether the other three
templates have comparable margins. **north_dinner does** — 28.7 mg, 2.0%, and
tighter still by the measure that matters (see below). Nobody had noticed it
either. south_breakfast (210.2 mg, 15.0%) and north_lunch (407.8 mg, 29.1%) do
not.

### Slack is the wrong unit; the smallest legal move is the right one

Portion space is integer unit counts, so a bound is not "nearly breached"
because slack is small in absolute terms — it is tight when slack is smaller
than the smallest legal one-unit move on that plate. By that measure the
sodium picture inverts:

| template | Na slack | smallest legal move raising Na | verdict |
|---|---|---|---|
| south_breakfast | 210.2 mg | 40.9 (chutney 2->3) | loose |
| south_lunch | **8.9 mg** | **2.0** (steamed_rice 1->2) | **loose** |
| north_lunch | 407.8 mg | 59.9 (phulka 5->6) | loose |
| north_dinner | **28.7 mg** | **59.9** (phulka 3->4) | **TIGHT** |

south_lunch's famous 8.9 mg is *not* a cliff edge in unit space: unsalted rice
is available in 2.0 mg increments, so the plate has room to move without
touching the guard. north_dinner's 28.7 mg **is** a cliff: every legal increment
on that plate costs at least 59.9 mg of sodium.

Both south plates and both north plates were also checked against every legal
single-unit neighbour, which is the honest version of the per-macro `step`
number because one unit move changes every macro at once:

```
south_lunch  -> 0 of the plate's single-unit neighbours are feasible
north_lunch  -> 0 of the plate's single-unit neighbours are feasible
north_dinner -> 0 of the plate's single-unit neighbours are feasible
south_breakfast -> 1 (coconut_chutney 2->3)
```

Three of the four passing plates are **point solutions**: not one adjacent
portion assignment is admissible. That is a property of a narrow library and
tight energy bands, not of sodium — the neighbours die on `energy_kcal` far
more often than on `sodium_mg`.

### What could change, and what each costs — **not picked, deliberately**

D5 says lay out the options and do not choose. Five, with the cost of each:

1. **Move the guard's value.** Cheapest to do, and now measured to buy nothing:
   the verdicts are stable from 0.55 to 1.00. Its real effect is on plate
   *choice* and rung count, not on pass/fail. Cost: re-registering a
   `PROJECT_DECISION` for an effect the sweep says is not the one anyone
   thought it had.
2. **Remove the guard.** The 2026-08-02 entry records why it exists: a bare
   remaining-budget check puts no limit at all on the first meal of a day, and
   a 1649.3 mg lunch passed one. Cost: that case returns.
3. **Let rule (ii) relax.** `core/nutrition/meal_target.py` states the reason it
   does not: rung 1 widens sodium by 0.50, so a widenable 0.70 guard permits a
   plate carrying 105% of a day's sodium. Cost: exactly that, and it is the
   outcome the guard was introduced to prevent.
4. **Re-derive the salt lines.** The sensitivity is measurable and is the axis
   D5's goal is actually about, since recipe work moves the plate and not the
   guard. Measured, every `sodium_mg` in the library scaled uniformly:
   ```
    south_indian/breakfast: still passes at x1.387 (+38.7% on every salt figure in the library)
    south_indian/lunch: still passes at x1.283 (+28.3% on every salt figure in the library)
    north_indian/lunch: still passes at x1.502 (+50.2% on every salt figure in the library)
    north_indian/dinner: still passes at x1.605 (+60.5% on every salt figure in the library)
   ```
   Every salt estimate in the library could be 28% low and all four templates
   would still pass. Cost: this is a *uniform* scaling and therefore an
   optimistic bound — a single dish being 30% under-salted is not covered by it.
5. **Nothing.** Defensible on this evidence, and it is what D5 forbids acting
   against anyway.

### What a reader should conclude about the four passing templates

They are a **result**, on the sodium axis, and something closer to a
**coincidence** on the energy axis.

Sodium: 22–38% of guard margin and 28–60% of salt-estimate margin behind every
verdict. Recipe work would have to be badly wrong, not slightly wrong, to flip
one. D5's fear does not survive measurement.

Energy: three of four plates have no feasible neighbour at all, and the
tightest bounds in the whole table are energy bounds — north_lunch's energy
ceiling has 13.6 kcal of slack against a 98.9 kcal smallest move (1.4%), and
south_lunch's *unrelaxed* energy floor is **missed by 6.7 kcal**, which is why
its third rung fires. One recipe's energy changing by a few percent moves those.
The honest reading: sodium is the bound everyone has been watching and is not
the fragile one; energy is fragile, on a band nobody has been watching, and no
task in the queue is about it.

### Finding 28 — the sodium guard is the only thing in the system that prefers less salt — **OPEN**

Raised by the sweep, not fixed here.

Nothing in the solver's objective penalises sodium: `NutritionTarget.points`
has no sodium entry, so any plate under the ceiling scores identically on that
macro. The consequence is visible as the guard rises:

```
  0.70 -> north_lunch=pass(0r, 992mg)   south_lunch=pass(3r,1391mg)
  0.80 -> north_lunch=pass(0r,1431mg)   south_lunch=pass(0r,1546mg)
  0.90 -> north_lunch=pass(0r,1733mg)   south_lunch=pass(0r,1546mg)
```

north_lunch's sodium **rises 741 mg (+75%) when the ceiling is loosened**, on
the same library and the same profile. Relaxing a limit made the plan worse in
the dimension the limit exists to protect. The guard is not acting as a
plausibility backstop here; it is acting as the sodium objective, because there
isn't one. A backstop and an objective are different mechanisms, and a system
where the only pressure toward less salt is a never-relaxing ceiling will always
serve the saltiest plate it is allowed to.

This is why option 1 above ("move the guard's value") is not the free
no-op the verdict sweep alone makes it look like: the verdicts do not move, but
the plates do, and they move in the wrong direction.

**Disposition.** OPEN. Not fixed here — D5 forbids tuning, and adding a sodium
term to the solver objective is a design decision about what the product
optimises for, not a defect fix.

### Finding 29 — relaxation rung 1 lets a *day* exceed its own sodium budget — **OPEN**

Raised while reconsidering the queue (slice 6 is about sequencing south meals
inside one day's sodium budget), not by the probe. Logged and left, per
TASKS_2.MD.

`core/nutrition/meal_target.py` sets two sodium bounds per plate:
`ceilings["sodium_mg"] = min(remaining, guard)` and
`hard_ceilings["sodium_mg"] = guard` — **the hard ceiling is always the
per-plate guard, never `remaining`.** So when the day's remaining budget is the
binding term, rung 1 of the ladder (`sodium_max_fibre_min`, ×1.5) is free to
widen it, and nothing catches the result at the day level.

Measured, south breakfast then south lunch for the reference profile:

```
$ python demo.py plan --region south_indian --meal-slot lunch --sodium-spent-mg 1189.8

      sodium_mg    floor         -   ceiling     810.2   [what the day has left]
  TARGET AS SOLVED (after 4 relaxation rung(s): ... ):
      sodium_mg    floor         -   ceiling    1215.3   [what the day has left]
  point        : 944.6 kcal, 35.0g protein, 24.3g fat, 144.8g carb, 1091.5mg sodium
```

The 1189.8 mg is the measured south_breakfast plate from the probe above.
2000 − 1189.8 = 810.2 remaining; 810.2 × 1.5 = 1215.3; the lunch plate takes
1091.5. Two meals, **2281.3 mg against a 2000 mg day budget — 14.1% over, with
one meal still to plan**, and no violation reported.

The 2026-08-02 entry that introduced the guard argued precisely this shape and
stopped one step short: it prevented *one plate* carrying 105% of a day, and
did not prevent *two plates* carrying 114% of one. `hard_ceilings` was made to
hold the guard still while tolerance moves around it; the day's remaining
budget was left with no such protection, and it is the bound that actually
encodes "a day".

Not a defect in rung 1 as such — the ladder is supposed to widen ceilings. The
question it raises is whether `day_remaining` is a tolerance at all, or a second
bound of the `hard_ceiling` kind that the ladder should skip. That is slice 6's
decision, not a fix to make here.

**Disposition.** OPEN. Blocks nothing today (nothing sequences a day yet); it
is the first thing slice 6 will hit.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d5_margins.py
python demo.py plan --region south_indian --meal-slot lunch --sodium-spent-mg 1189.8
```

Full transcript is the probe's own output; the excerpts above are verbatim from
it. `docs/design/probes/README.md` lists it.

---

## 2026-08-07 — D3: making the south templates reachable

Three recipes (`idli`, `steamed_rice`, `soya_kuzhambu`) added so both South
Indian templates can satisfy the quality floor slice 4 introduced. Full account
in `docs/methodology.md`, "Making the south templates reachable". One new
finding, one prediction scorecard.

### The prediction, and it held completely

Written and stated before any file was created, from the per-unit table alone.
All six calls held, including both exact plates and both sodium figures:

| Prediction | Measured |
|---|---|
| south_breakfast passes, **0 rungs**, idli ×6 + soya_kuzhambu ×1 + coconut_chutney ×2 + thayir_plain ×1, 623.8 kcal, 1189.7 mg Na | passes, 0 rungs, that plate, 623.6 kcal, 1189.8 mg Na |
| south_lunch passes, **3 rungs**, ≈ steamed_rice ×1 + soya_kuzhambu ×2 + vegetable + thayir_plain ×1, ~848 kcal | passes, 3 rungs, steamed_rice ×1 + soya_kuzhambu ×2 + carrot_poriyal ×2 + thayir_plain ×1, 848.1 kcal, 1391.1 mg Na |
| sodium binds, and it is why two of the three recipes exist | held — see below |
| north verdicts do not move, because `candidates.py` filters on region | held, byte-identical, 24 and 12 combinations |
| combinations 2 → 8 and 3 → 12 | held |

Worth recording *why* it held, since the previous session's prediction did not:
this one was made from a measured per-unit table (`nutrition_of_recipe` over the
whole library) and hand arithmetic against the printed meal targets, not from
reasoning about what the rule "should" do. The one thing not predicted was
finding 27 below, which is a crash rather than a wrong answer.

**The sodium claim is backed by defect injection, not assertion.** Removing
`steamed_rice.yaml` alone puts south_lunch back into decline with
`Violation(macro='sodium_mg', kind='above_ceiling')`; removing `idli.yaml` alone
drops south_breakfast from 0 rungs to 3. Removing `soya_kuzhambu.yaml` is the
only one of the three that produces a *quality* decline.

### Finding 27 — a serving unit whose floor is above 1 crashed the candidate filter — FIXED in the same commit

`core/planner/candidates.py::_eligibility_flags` priced every candidate at a
hard-coded count of 1, while `nutrition_of_recipe` enforces the serving unit's
`[min_count, max_count]` bounds. Every recipe in the library happened to have
`min_count == 1`, so the two agreed by coincidence for the project's whole life
so far. `idli` is the first with a floor of 2 — nobody is served one idli — and
adding it made `build_candidate_pool` raise `ValueError: idli: count 1 outside
[2, 6]` before it could filter anything, for every template containing it.

The line's own comment already read *"any count in the unit's domain gives the
same fraction"* while the code used a count that need not be in that domain. The
comment was right and the code did not implement it — the same class of gap
CLAUDE.md's round-4 addendum is about, in miniature.

Three tests in `tests/test_nutrition_of.py::TestEligibilityConsequence` carried
the identical hard-coded 1 and crashed the same way.

**Disposition: FIXED.** `_eligibility_flags` and the three tests now use
`component.recipe.serving_unit.min_count`, which is in the domain by
construction. `tests/test_planner_candidates.py::TestServingUnitsWhoseFloorIsAboveOne`
pins it, with a second test proving the substitution is *safe* rather than
merely working: the eligibility fraction is identical at every count across
idli's whole 2–6 domain. Injection: reverting the line to `1` turns 9 tests red
across three files, including both new ones.

**What this says about coverage.** Nothing detected it because nothing exercised
it. `ServingUnit.min_count` has been a settable field since `core/foods/models.py`
was written and every recipe author independently chose 1. A field whose only
tested value is its default is not tested.

### Disposition of the older findings D3 touched

- **Finding 22** (south_lunch combinations unreachable at minimum counts) —
  still OPEN and untouched. The two offending combinations are still
  unreachable; D3 added a third rice_base/gravy pairing that is reachable. The
  passing south_lunch plate clears the 1400 mg guard by **8.9 mg**.
- **Finding 2** (a recipe with no `process:` lines reads as 0% process-uncertain)
  — still OPEN, now reachable with three real files rather than one:
  `thayir_plain`, `idli`, `steamed_rice`.
- **The "a decline can now say less" observation** from the slice-4 entry below
  — still OPEN. It is no longer visible on the south templates, because they
  pass, but it is a property of `_blocking_violations` and nothing about it
  changed.
- `tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants`
  was red before D3 (on `onion_raita`) and is red after (on `idli`, which sorts
  first). Same assertion, same defect class, deliberately not touched.

---

## 2026-08-07 — D2b-ii, slice 4: the quality-source rule

A per-meal floor on protein from ingredients clearing
`protein.quality_diaas_threshold` (0.75). Full description in
`docs/methodology.md`, "Protein quality is a rule about sources". Three
observations recorded here, one of them a defect in this session's own testing.

### The prediction, and where it was wrong

Written before any code was changed. Four of six calls held exactly:

- south_breakfast and south_lunch decline on quality — **held**, at exactly the
  predicted 8.99 g reachable against 11.2 g.
- north_lunch and north_dinner still pass with zero rungs, on plates containing
  soya or paneer instead of tofu — **held**, both.
- the three-katoris-of-dal plate is rejected on quality at 7.94 g — **held**
  (measured 7.936 g).
- `Profile.diet` still moves no target number — **held**.

**Wrong: the shape of the two south declines.** The prediction was that quality
would be named *alongside* energy, fat and sodium, since all four looked
individually unreachable. Measured, quality is named **instead of** them. The
cause is `_blocking_violations`' two-branch structure: energy/fat/sodium were
never in the unreachable branch at all — their reach spans the bound
(south_breakfast energy reaches 373.5–1326.8 kcal against a 707.0 ceiling), so
they were being reported by the later best-plate-probe branch. A genuinely
unreachable bound returns from the first branch and the probe never runs.

### Observation — a decline can now say less than it used to

Before: *"energy_kcal is 777.1kcal, above its ceiling of 707.0kcal; fat_g is
33.2g...; sodium_mg is 2273.4mg, above its ceiling of 1400.0mg"*.

After: *"only 9.0g of this plate's protein comes from a high-quality source,
against a floor of 11.2g"*.

The new sentence is the truest single thing — quality is unreachable at every
count, whereas the others were one probe plate's misses — but the user no longer
learns the plate is also 60% over the sodium guard. **Disposition: OPEN,
recorded, not fixed.** It is the same shape as finding 24 (a decline naming the
symptom rather than the cause), arriving from the other direction, and the
commissioning task ruled finding 24 out of scope.

### Finding 24 itself: checked, unmoved

`tests/test_planner_plan.py::TestPerMealProteinCeiling::
test_the_decline_names_energy_though_the_cause_is_the_protein_ceiling` still
passes unchanged. The quality rule does not fire on that synthetic case, so the
finding is neither fixed nor worsened.

### Finding 26 — a defect injection that the whole new test file survived — FIXED in the same commit

Deleting the quality check from `solver._within_target_point` — i.e. removing
the gate this slice exists to add — left **all 31 new tests green**.

Cause: `feasible_combinations` discards quality-failing combinations before the
solver runs, so on the real library the solver's own gate never decides
anything. Every test was reaching the pre-filter and stopping there. This is
exactly CLAUDE.md's "writing a test that cannot fail on the defect it names",
and it is the third instance in this repo's log.

Fixed by `TestTheSolverGateItself`, which isolates the gate on the synthetic
`SOUTH_LUNCH` pool: a combination the pre-filter must admit (`curd_b` reaches
5.0 g at its maximum count, above a 4.0 g floor) whose best-scoring assignment
falls short (2.5 g at one unit). With the gate present the solver returns
`curd_b ×2`; with it deleted, `curd_b ×1`. Both new tests were re-run against the
re-injected defect and go red.

Five further defects were injected and each turned the suite red: the protein
rung relaxing the quality floor (4 red), the floor scaled by the energy share
(9 red), a missing DIAAS reading as qualifying (15 red), the day floor taken off
the DIAAS-inflated figure instead of `base_g` (2 red), and `_widen_band`
rebuilding the target with an explicit constructor that drops the new field
(6 red). That last one is why the ladder's three target rebuilds were converted
to `dataclasses.replace`.

---

## 2026-08-02 — D2b-i, finding 25 closed

`SOUTH_BREAKFAST` gains an **optional** `curd_course` slot accepting
`curd`/`buttermilk`. `thayir_plain@curd` already fills it — no new recipe and no
new ingredient row were needed, and `curd_dahi` qualifies at DIAAS 1.09.

It follows `SOUTH_LUNCH.curd_course` in category but not in obligation: south
lunch's is required, because a South Indian lunch ends with thayir close to
obligatorily; breakfast's is optional, because idli or dosa with sambar and
chutney is a complete breakfast. That difference is the whole design of the
slot, and it is asserted rather than commented — a curd-less combination must
still enumerate.

Slot coverage and enumeration, before → after
(`PYTHONHASHSEED=0 python demo.py`):

```
south_breakfast  curd_course slot added, n=1 ['thayir_plain@curd']   1 -> 2
south_lunch      unchanged                                           3 -> 3
north_lunch      unchanged                                          24 -> 24
north_dinner     unchanged                                          12 -> 12
```

Both breakfast combinations enumerate: with and without the curd.

**A verdict reason moved, and it is worth stating.** `south_breakfast` still
declines for the reference profile, but on different numbers, because the
best-scoring combination is now the one carrying curd:

```
before  fat 24.7 > 24.6 | protein 18.4 < 23.8 | sodium 1790.4 > 1400.0
after   energy 777.1 > 707.0 | fat 33.2 > 24.6 | sodium 2273.4 > 1400.0
```

The protein violation is gone and the sodium one is worse — a katori of curd
carries its own salt line. Nothing was tuned; this is what adding a real option
to a slot does.

**Eggs are not in this.** They are the deferred non-vegetarian axis (onboarding,
filtering, schema and library all change), and nothing added here could be
served to a vegetarian profile that should not be.

*Disposition:* Finding 25 CLOSED. Pinned by
`tests/test_planner_plan.py::TestSouthBreakfastCanReachAQualitySource`, both
tests shown red against injected defects — the slot removed (KeyError, and no
curd-bearing combination), and the slot made required (no curd-less
combination).

---

## 2026-08-02 — D2a, the high-quality protein rows

Three ingredient rows (`paneer_fresh`, `tofu_firm`, `soya_chunks_dry`) and three
recipes (`paneer_masala@sabzi`, `tofu_bhurji@sabzi`,
`soya_chunk_curry@legume_curry`) were added so the quality-source rule has
something to select. Four things measured, one of them a finding.

### The reference profile now gets a plate, and it took no relaxation

This is the larger result and it was not the goal of the task. Before D2a all
four templates declined for the reference profile (see `docs/methodology.md`,
"Every template enumerates, and every template still declines"). After:

```
$ PYTHONHASHSEED=0 python demo.py plan --region north_indian --meal-slot lunch
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 4, 'dal_tadka@dal': 2, 'tofu_bhurji@sabzi': 1}
  point        : 929.8 kcal, 42.6g protein, 25.8g fat, 133.9g carb, 1209.0mg sodium

$ PYTHONHASHSEED=0 python demo.py plan --region north_indian --meal-slot dinner
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 4, 'dal_tadka@dal': 1, 'tofu_bhurji@sabzi': 1}
  point        : 756.8 kcal, 35.4g protein, 20.2g fat, 111.3g carb, 889.2mg sodium
```

Both north templates pass **with zero relaxation rungs fired** — the first
plates this library has served the reference profile without walking the ladder.
The mechanism is not protein: it is that a 150 g katori of tofu bhurji is a
low-sodium, moderate-energy way to fill the `sabzi` slot, so the solver can
reach the energy floor without the salt load that made every previous
combination breach the 1400 mg guard. The two south templates still decline, on
sodium among others; finding 22 is untouched.

### Finding 25 — no high-quality protein source can reach south_breakfast — **OPEN**

`SOUTH_BREAKFAST`'s four slots accept `tiffin`, `sambar`/`kuzhambu`,
`chutney`/`podi` and `beverage`. None of the three new components can be written
into any of them without either miscategorising the dish or inventing a category,
and the existing library has no qualifying ingredient in that template either
(`curd_dahi` reaches only `raita` and `curd`, which south_breakfast does not
accept).

So when the quality-source rule ships with a per-meal quality floor, **south
breakfast becomes structurally undeclinable-to-satisfy**: not "the library is
thin," but "the plate grammar has no slot a quality source could occupy." A
paneer/soya-stuffed dosa or a milk-based beverage would close it; both are new
recipes, and inventing one to make a rule pass is the shape of tuning this
project refuses.

*Disposition:* OPEN. Recorded before slice 4 rather than discovered by it.

### Nothing was upgraded to make the rows work

`dev_mode=False` still empties every pool — the new rows are `verified=false`
and carry the same 0.25 composition band as every other hand-entered row:

```
south_breakfast dev_mode True/False candidates: [3, 0]
south_lunch     dev_mode True/False candidates: [5, 0]
north_lunch     dev_mode True/False candidates: [8, 0]
north_dinner    dev_mode True/False candidates: [7, 0]
```

The three DIAAS figures are **authored, not sourced** — no primary source was
opened — and each was entered at the low end of its recalled range, because a
high DIAAS is what makes a row *qualify* and the cheapest authoring path must not
produce the most permissive output. The visible cost: `tofu_firm` at 0.65 sits
below the 0.75 threshold, so tofu will not qualify as a quality source. That is a
statement about this project's confidence, not about tofu.

### Unverified energy fraction: measured, not acted on

The two passing plates report 57.5% and 47.7% of plate energy as unverified,
against CLAUDE.md's ~15% shipping threshold. Both figures come from the
denominator finding 20 says is wrong in two directions at once, so they are
recorded and nothing is concluded from them. Nothing ships as validated either
way.

---

## 2026-08-02 — finding 24, raised by slice 3

### Finding 24 — a decline can name the symptom instead of the cause — **OPEN**

**What.** When the new per-meal protein ceiling excludes every energy-dense
plate, the decline reports **`energy_kcal below_floor`**. The protein ceiling is
never mentioned, because plates above it are removed before the validator sees
them, so the only thing left to report is that what survived cannot reach the
energy floor.

**Measured**, synthetic pool, day protein floor 40 g (meal ceiling 20.0 g),
energy 2400 kcal — the same target run twice, differing only in the registered
ceiling fraction:

```
ceiling 0.50 (real)  declines: energy_kcal below_floor 510.0 vs 756.0
ceiling 10.0 (off)   returns:  26.5 g protein, 800.0 kcal
```

The second run proves the first decline is caused by the protein ceiling. The
first run's message says energy.

**Why it matters.** A user told "energy is unreachable" would reasonably add an
energy-dense dish, which cannot help — every such dish is already excluded on
protein. The decline is truthful about what the validator saw and misleading
about what to do, which is a worse failure than a vague message: it points
somewhere specific and wrong. `docs/design/target_model_v2.md`'s decline-screen
work assumes the named macro is actionable.

**Scope.** Not specific to protein. Any bound that empties the feasible set
before the validator runs will surface as a violation of whatever the survivors
fail next. The pre-filter and the solver both discard silently.

**Not fixed here.** Slice 3's brief is the two bounds. A fix means the solver or
pre-filter reporting *why* it discarded, which is a different piece of work with
its own shape (`solve()` currently returns survivors and nothing about the
rejected). Pinned by
`tests/test_planner_plan.py::TestPerMealProteinCeiling::test_the_decline_names_energy_though_the_cause_is_the_protein_ceiling`,
so the current behaviour is visible and improving it is a deliberate change with
a red test attached rather than a silent one.

**Disposition.** OPEN.

---

## 2026-08-02 — finding 23, a form field with no effect

### Finding 23 — onboarding asks for diet and nothing reads it — **OPEN**

**What.** `web/onboarding.js` collects `diet`, `api/db.py` persists it on
`StoredProfile`, and as of slice 2 it changes no target value at all. Two
profiles identical but for diet receive identical energy, protein, fat, carb,
fibre and sodium targets. The wizard asks a question whose answer is stored and
then ignored.

**Why it is a finding and not just a gap.** The gap itself is deliberate and
documented (`docs/methodology.md`, "Protein quality no longer inflates the
target"): quality moved out of target-inflation and the quality-source rule that
replaces it is blocked on the ingredient set. What is not deliberate is that a
**shipped, user-facing surface still presents the question as consequential**. A
form that collects an answer it does not use is a claim to the user that it
matters. This project's entire premise is not overstating what it knows; an
inert form field is that failure on the most visible surface there is.

Distinct from the internal gap in one important way: the internal gap is fixed
by slice 4, and this is fixed by slice 4 *or* by saying so in the wizard. They
have different costs and either is defensible.

**Not fixed here.** Three options, none picked, all cheap: label the field in
the wizard as not yet affecting the plan; remove the step until slice 4; or
leave it and accept that the honest answer is "we collect this for later". The
first is the most in keeping with how the rest of this project handles a thing
it cannot yet do.

**Disposition.** OPEN. Reopens or closes with slice 4.

---

## 2026-08-02 — finding 22, raised by filling the library (T4)

### Finding 22 — a multi-dish South Indian plate cannot get under the sodium guard — **OPEN**

**What.** Now that every template enumerates, sodium blocks all four of them.
For `south_lunch` it is not a matter of a demanding profile: two of its three
combinations have a sodium **floor** above the per-plate guard with every
component at its minimum serving count, so no profile can ever be served them.

**Measured**, per-combination reach at min and max counts — the diagnosis is
built on the reach table this time, not read off a single blocking figure, which
is the mistake made in the other direction earlier the same day:

```
south_lunch
  Na  1437.0.. 3654.0   sambar_sadam + sambar + carrot_kootu + thayir_plain
  Na  1282.1.. 3344.2   sambar_sadam + sambar + carrot_poriyal + thayir_plain
  Na  1677.1.. 4134.2   sambar_sadam + sambar + carrot_kootu + carrot_poriyal + thayir_plain
south_breakfast
  Na  1006.6.. 3060.7   masala_dosa + sambar + coconut_chutney
```

Guard: 1400.0 mg (`day_budget.absurdity_fraction` 0.70 x 2000). Rows 1 and 3 are
above it before the solver picks a single unit count.

**Why it happens, and why it is not obviously a recipe defect.** A South Indian
lunch is four or five separate dishes, each independently salted at the ordinary
domestic proportion — the salt lines here run 0.33% to 0.67% of finished weight
and each carries a written reason. Four dishes at one katori each is roughly
3.3 g of salt before anyone eats a second helping. The arithmetic is not
disputed; what it means is:

- either the guard is wrong for multi-dish regional plates (it is a
  `PROJECT_DECISION` plausibility limit derived from meal-split fractions that
  are themselves project decisions, and it was never checked against a plate
  with four salt lines in it);
- or the salt proportions are wrong (but each was authored from how the dish is
  salted, and tuning them downward until plans pass is precisely the defect the
  salt notes exist to prevent);
- or a South Indian lunch genuinely carries this much sodium and the honest
  answer is to decline and say so.

**Not resolved here, deliberately.** TASKS.md forbids fixing things noticed in
passing, and each of the three readings above is a different decision with
different consequences. Lowering a salt line to clear a ceiling would be the
worst available option and is explicitly not on the table.

**Connects to finding 19/20's territory.** This is the sharpest available
illustration of `docs/design/recipe_quantity_uncertainty.md` §1: sodium is 77-99%
attributable to authored quantities, and it is now the single constraint blocking
every template in the library. The number that decides whether anything can be
served is one nobody measured.

**Disposition.** OPEN.

---

## 2026-08-02 — finding 21, and a correction to finding 19's own explanation

### Finding 21 — two constants in permanent contradiction, neither wrong alone — **OPEN**

**What.** `composition.verified_primary` (0.05) and `tolerance.energy_default`
(0.05) are the same number. The first is how wrong a verified composition value
is; the second is how far a plan's energy may sit from its target. One is checked
against the other every time a band is compared with the room a target leaves,
and they have never been compared with each other by anybody.

Neither is wrong on its own terms. `0.05` is a defensible estimate of analytical
spread; `±5%` is a defensible energy tolerance. Together they make the top
confidence state unreachable, and they do it permanently — no amount of
verification changes it, because verification changes who read the number, not
how variable the food is.

**Measured** (`docs/design/probes/t3b_propagation.py`), reference plate, process
term forced to zero so the composition term is isolated:

```
point     702.130   midpoint  691.445   point/midpoint 1.015454
h          35.106   room       34.572   h/room         1.015454
identical to 6 dp: True
```

When the two constants are equal the comparison collapses to **point versus
target midpoint**. So:

- With no process term, `confident` is granted exactly when the plate's energy
  lands at or below the centre of its own window — a fact about solver rounding
  over integer serving counts, carrying no nutritional meaning. A label decided
  that way is worse than one that never fires, because it looks like it means
  something.
- With the library's real process term (0.0689 on energy), the plate would need
  to sit 27% below centre, which is below its own energy floor. Unreachable.

**Scope, narrower than finding 19 stated.** This is energy-only.
`tolerance.fat_carb_default` is 0.15 against the same 0.05 band and has three
times the room it needs. Protein also exceeds its room on the reference plate
(h=1.46 vs 1.21) but that room is `point − floor`, a solver-slack fact about one
plate, not a constant-versus-constant contradiction.

**Same class as the salt-note defect.** A value that cannot do what its
neighbours assume it does, where every individual check passes. Nothing in the
registry can express "these two are compared against each other" — they sit four
entries apart in `citations.py` (positions 12 and 16 of 63) and no mechanism
noticed.

**Disposition.** OPEN, **deferred by decision 2026-08-02.** Options laid out in
`docs/design/tolerance_versus_band.md`; no constant moved and none chosen. The
contradiction is permanent but inert — the confidence label is not built, so
nothing reads either constant against the other today. **The label is not to be
built until this is settled**, because building it first would force the choice
from inside an implementation, which is exactly how the sodium ladder ambiguity
came to be resolved in `validator.py` rather than in a document. Reopen when the
label is scheduled, or when any user-facing surface states a "within 5% of your
energy target" claim.

Note for whoever picks: widening the tolerance to make the label move is the
perverse incentive CLAUDE.md documents, wearing a different hat, and 0.10 is
already the value rung 3 relaxes *to*, so it would make that rung a no-op.

### Correction — finding 19's explanation was wrong, its conclusion was not

Finding 19 (and `docs/design/recipe_quantity_uncertainty.md` §6) says a 5%
composition band "produces a ~7% band on plate energy". The figure is right. The
reason given — that errors accumulate across the components of a plate — is
wrong, and the wrong reason was load-bearing: it made this look like a scaling
problem that worsens with bigger plates, and it is what T3b was commissioned to
investigate ("at what component count does it stabilise?").

Composition uncertainty is applied per line and weighted by that line's share of
the macro, then summed, so a uniform `u` sums to exactly `u` at any component
count. Measured, process terms zeroed:

```
u = 0.05, 1 through 6 components: 0.0500 on every macro, every count
u = 0.25, 1 through 6 components: 0.2500 on every macro, every count
```

Flat. It never accumulates and there is no count at which it stabilises. The
extra 1.89 points on energy is the **process** term — dal_tadka's tempering oil —
which is per-recipe and does not scale with plate size either. Protein, carb and
sodium carry no process term at all, because oil has none of them.

Corrected in place in the design doc rather than silently edited. The correction
makes the problem smaller and sharper: not a scaling law, two equal numbers.

---

## 2026-08-02 — two findings from the T3 design measurement

Both found while designing `docs/design/recipe_quantity_uncertainty.md` against
the real library. Neither is caused by that design; both were already true and
were invisible because nothing had measured them. Design is not implemented, so
nothing here is fixed.

### Finding 19 — the confidence label saturates: `confident` is unreachable — **OPEN**

**What.** The plain-language confidence label specified in T3 (*confident* /
*rough* / *very rough*, derived from band half-width against the room a target
leaves) has one reachable bucket. Every plate the library can produce is already
*very rough* today, and stays *very rough* under a simulation of Task 6 in which
every ingredient is verified.

**Measured.** North Indian lunch for a 45 kg / 165 cm / 35 / female / active /
maintain profile — the nearest profile whose plate solves with **zero**
relaxation rungs, so the comparison is against the tightest bounds the system
ever applies. Plate `phulka ×1, dal_tadka ×3, onion_raita ×1`.

```
                              energy      protein     fat        carb
band half-width today          h=188.8     h=7.3      h=7.1      h=23.4
room the target leaves         room=34.6   room=1.2   room=3.2   room=14.6
                              -> very rough on all four

simulating Task 6 (composition.unverified_secondary 0.25 -> verified 0.05):
band half-width                h=48.4      h=1.5      h=2.6      (passes)
room                           room=34.6   room=1.2   room=3.2
                              -> still very rough on energy and protein
```

**Why it does not resolve itself.** Energy is the binding case and it is
structural, not a data problem: a 5% composition band on every ingredient
produces roughly a 7% band on plate energy, while `tolerance.energy_default` is
5%. `confident` cannot be reached from any composition data this project could
plausibly obtain, because the tolerance is narrower than the uncertainty of a
national food table. The two constants were registered independently and have
never been compared to each other.

**Why it matters.** The label was specified as counter-pressure against the
documented perverse incentive (wider bands are easier to satisfy). A label with
one reachable value exerts none. Separately, the counter-pressure that *does*
exist — the candidate eligibility filter, which removes a recipe whose band
exceeds 0.15 protein / 0.20 energy — is also saturated: all four north-lunch
recipes already breach both (protein 0.250 vs 0.15; energy 0.250–0.276 vs 0.20)
and survive only under `dev_mode=True`.

**Disposition.** OPEN. Recorded in the design doc §6 and §7 as a stated
limitation rather than smoothed over. Resolving it means revisiting either
`tolerance.energy_default` or `composition.verified_primary` **against each
other**, which is a target-model decision, not a recipe-data one. Do not resolve
it by widening the tolerance to make the label move — that is the perverse
incentive wearing a different hat.

### Finding 20 — the unverified-energy fraction is wrong in both directions, measured — **OPEN**

**What.** The round-4 addendum predicted that
`NutritionEstimate.unverified_energy_kcal` gets its denominator wrong in both
directions. It does, and the size is now measured rather than argued.

**Measured**, same plate: `unverified_energy_kcal = 519.0 of 702.1 = 73.9%`
against CLAUDE.md's ~15% shipping threshold.

```
dal_tadka      process_constants=['oil_uptake.vegetable_tempering']  -> whole 519 kcal charged
phulka         process_constants=[]                                  -> 0.0 charged
onion_raita    process_constants=[]                                  -> 0.0 charged
```

- **Over-charged:** `_depends_on_unverified` charges a recipe's *entire* energy
  when any process constant is unverified. dal_tadka's 519 kcal is charged
  because of a 5 g tempering-oil line.
- **Under-charged:** unverified *composition* never enters the calculation at
  all. phulka and onion_raita rest entirely on hand-entered, `verified=False`
  ingredient rows and contribute 0.0.

73.9% is therefore not the true figure. It is two large errors in opposite
directions that happen not to cancel, and the direction of the net error is
unknown.

**Disposition.** OPEN. The known over-attribution is already documented in
`core/foods/nutrition_of.py::_depends_on_unverified`, deliberately left because
correcting the smaller error alone would move the reported figure *away* from
the truth. This entry adds the measurement and the consequence: **the 15%
threshold cannot be trusted against real data until the denominator is fixed**,
and no work should be measured against it in the meantime. It does not change
what can ship — nothing can ship as validated for the independent reason that
every registered constant is `verified=False`.

---

## 2026-08-02 — finding 18 CLOSED, and the reproducibility pattern behind it

### Finding 18 — CLOSED

`CandidatePool.for_slot` now iterates `sorted(slot.accepted_categories)` and
returns candidates sorted by `component.id`. Sorted by **id, not by category
name**: the id is the identity of the thing actually offered, so the order
survives a category rename or a slot accepting more categories, and it is a
total order because `for_slot` already deduplicates on that key.

**Before fixing, the spread was measured.** `demo.py plan` for the north_lunch
reference profile, 12 hash seeds:

- **2 distinct enumeration orderings** (5 seeds gave rajma-first, 7 gave
  dal-first).
- **Verdict identical in all 12**: `passed: False`,
  `above_ceiling sodium_mg actual=1649.3 bound=1400.0`.

**The winner does not change with seed.** This was the serious question and the
answer is no. Checked on a target the real library *can* satisfy, and on
`tests/factories.py`'s 144-combination synthetic library where ties are far more
likely, across 12 seeds each:

```
REAL  plate={'phulka@roti':3,'rajma_chawal@combo_rice_legume':1,'onion_raita@raita':1}
      score=0.301389  top4=[0.301389, 0.372667, 0.9585, 1.039]
SYNTH n=144  plate={'rice_b@mixed_rice':2,'gravy_b@rasam':2,'veg_a@poriyal':2,
                    'veg_c@poriyal':2,'curd_b@buttermilk':1,'crisp_b@pickle':2}
      score=0.121429  top4=[0.121429, 0.142857, 0.214286, 0.271429]
```

Identical at every seed. **No tie was ever reached** — top-two scores differ by
24% (real) and 18% (synthetic) — so `solver.py`'s stable sort never had to break
one. The tie-break path is **latent, not realised**: published results did not
depend on a hash seed. Finding 18 is a reproducibility defect, not a correctness
one.

**After the fix**: one ordering across all 12 seeds; plate, score, verdict and
violation all unchanged. Note what that last clause is and is not — *nothing
changed* is a statement about **this library at this size**. With four
combinations and scores 24% apart there was no tie to resolve. It is not a
guarantee for a larger library, where the stable sort's input order is exactly
which plate a user is served.

**Other set-iteration sites, checked rather than assumed.** `candidates.py:110`
was the only one in the ordering-relevant path. Examined and deliberately not
changed:

- `core/foods/recipe_loader.py:218` and `ifct_loader.py:270` already
  `sorted(...)` their globs, so file order was never the problem.
- `combinations.py` uses `itertools.combinations` / `itertools.product`, both
  order-preserving given deterministic input — so the one fix propagates.
- `candidates.py` `recipe_allergens` returns a frozenset, but it is only ever
  membership-tested, never iterated for order.
- `len({f.recipe_id for f in flagged})` builds a set for a count only.
- **`solver.py:214`, `solved.sort(key=lambda p: p.score)` — left alone.**
  Python's sort is stable, so with deterministic input the winner is now
  deterministic; the defect is fully closed by the one fix. Adding a secondary
  sort key would additionally make the winner independent of *enumeration* order,
  which is a stronger and different property — a decision about tie-break
  semantics, not a determinism fix, and not made here.

**Disposition: CLOSED.** `tests/test_planner_determinism.py` (new).

### The pattern — second instance, and it should be named as one

This is the **second time a reproducibility rule in this project has been
satisfied literally while missing its purpose.**

1. **Task 9 (2026-07-31, finding 11).** CLAUDE.md requires a pasted command
   transcript backing any status claim. Every transcript in this log had one.
   None could be re-run, because the command lived in an untracked scratch
   script. The rule was met; its purpose — that anyone can check the claim —
   was not.
2. **Finding 18 (today).** `demo.py` was built to close that hole, and slice
   1a's acceptance criterion asserted byte-identical output against a captured
   baseline. Both were satisfied. Neither could be *reliably* true while
   enumeration order was seed-dependent: 1a's byte-diff passed because the
   baseline and the comparison run happened to draw the same ordering. The
   check was real, and it was a coin flip.

The shape is the same both times: **a reproducibility check that reproduces
itself.** A transcript that proves a transcript exists; a byte-diff run twice in
one shell against one seed. Neither compared across the axis the property was
actually about — a different machine, a different process.

What follows from it, stated as a rule rather than an intention: **a
determinism claim has to be checked across the thing it claims independence
from.** `tests/test_planner_determinism.py` does that by spawning subprocesses
under different `PYTHONHASHSEED` values, because nothing checkable inside one
process can.

That is not a hypothetical concern — it was demonstrated while writing the
tests. The first draft's three fast in-process tests **all passed against the
defect they were written to catch**, for two separate reasons: one picked
`north_lunch.grain_base`, which declares two categories but has candidates in
only one, so permuting it is a no-op; and the sortedness check compares
frozenset order against sorted order, which coincide often enough to pass under
many seeds. Both were found by injecting the defect and watching the tests not
fail. Under the corrected tests the defect fails 3 of 4 at every seed tried
(0, 1, 5), and the remaining one is documented in its own body as a statement of
contract rather than a detector.

### Does finding 11's closure claim now hold?

**Yes, and it did not before today.** The 2026-07-31 entry closed finding 11 on
the claim that the evidence chain is reproducible. As of that entry the
*substance* reproduced — verdicts, bounds and violations were stable across
every seed measured — but the artifact did not: two people running the
documented command got textually different transcripts, and a diff between them
showed changes that were not changes. With `for_slot` ordered, `demo.py` output
is byte-stable across 12 hash seeds, and the claim holds as written.

---

## 2026-08-02 — sodium became a day budget; two findings raised on the way

Build notes for target-model slices 1a and 1b, plus two things measured while
building them that neither the design doc nor this log had right.

### Finding 18 — combination enumeration order is not deterministic — **CLOSED 2026-08-02**, see the entry above

`TemplateSlot.accepted_categories` is a `frozenset[str]`, and
`core/planner/candidates.py:110` iterates it directly. Python randomises string
hashes per process, so **candidate order — and therefore the order
`enumerate_combinations` returns combinations in — varies between runs of
identical code on the same machine.**

Measured. Five runs of `demo.py plan`, hashing the enumeration block only, on
the unmodified pre-slice-1a code:

```
09071a2e79c2b59a8d1e1a4c0fe257da     f737693bb608d5fdd2e891852e804f5e
09071a2e79c2b59a8d1e1a4c0fe257da     09071a2e79c2b59a8d1e1a4c0fe257da
f737693bb608d5fdd2e891852e804f5e
```

Two distinct orderings. With `PYTHONHASHSEED=0` fixed, three runs produce one
ordering, which identifies hash randomisation as the cause. The two orderings
differ in whether `dal_tadka` or `rajma_chawal` is listed first for
`north_lunch.legume_curry`, whose `accepted_categories` is
`frozenset({"legume_curry", "dal", "combo_rice_legume"})`.

**Why this matters more than a cosmetic listing order.** `demo.py` exists so
that the transcripts in this file can be regenerated by anyone, and the
2026-07-31 entry closed finding 11 on exactly that basis. The verdict, the
bounds and the violations are stable — what varies is the enumeration listing —
so the *substance* of every transcript here reproduces. But two people running
the identical command get textually different transcripts, and a diff between
them shows changes that are not changes. Byte-reproducibility was the claim, and
it does not hold.

**The second-order risk, not observed today but structural.** `solve` returns
plans ordered by score, and ties are broken by input order. With today's
four-combination library no tie arises, so the plate served is stable. With a
richer library, *which plate a user is served* could depend on the hash seed of
the process that answered their request.

**Disposition: was OPEN when written; CLOSED the same day in its own commit —
see the 2026-08-02 entry above for the measured spread, the winner-stability
check, and the pattern this is the second instance of.** Deliberately not fixed
in the slice that found it: changing enumeration order changes `demo.py` output
and can change which plate the solver picks among equals, and that must not ride
inside a commit whose acceptance criterion is that no behaviour moved. Found
while diffing slice 1a's output against its baseline; not caused by it.

### Correction — the north_lunch decline was never a sodium wall

The 2026-07-31 entry, and `docs/design/target_model_v2.md` §2–3, both read the
`sodium_mg actual=1649.3` decline as sodium being unreachably high in this
library. It is not. Measured per-combination sodium reach (min..max over legal
unit counts):

```
   856.6 ..  1952.8   ['phulka@roti', 'rajma_chawal@combo_rice_legume']
  1111.8 ..  2463.2   [... + 'onion_raita@raita']
   379.6 ..  1318.5   ['phulka@roti', 'dal_tadka@dal']
   634.8 ..  1828.9   [... + 'onion_raita@raita']
```

The library can build a **379.6 mg** north lunch. 1649.3 mg is the sodium of the
plate that best fits *energy and protein*: `_blocking_violations` found every
bound individually reachable and fell through to its "no single assignment meets
them together" branch, which reports the best-scoring plate's own misses. So the
decline is a **joint energy-vs-sodium infeasibility** — the low-sodium plates
cannot reach the 809.9 kcal floor — not a sodium ceiling the library cannot get
under. Reading it as the latter is what made "does the decline survive?" look
like the important question about the day-budget design. It was not.

### Correction — the design doc's absurdity guard did not survive its own ladder

`docs/design/target_model_v2.md` §2 and §3 state that the 1649.3 mg plate "still
fails" the proposed 1400 mg guard, "which is the behaviour this design wants."
That compares the plate against the **unrelaxed** guard. Rung 1 widens the
sodium ceiling by `tolerance.sodium_relaxed_fraction` (0.50), so the guard
became 2100 mg and the plate passed:

```
--- sodium ceiling 1400 (0.70 x 2000), guard widenable
    passed: True | rungs: all four | final sodium ceiling: 2100.0
    plate: {'phulka@roti': 3, 'dal_tadka@dal': 3, 'onion_raita@raita': 2}
    point: 984.1 kcal, 40.4g pro, 1649.3mg Na
```

Generally: a widenable guard permits one plate to carry `fraction x 1.5` of a
day. At 0.70 that is **105% of a whole day's sodium on a single plate** — the
outcome the guard was introduced to prevent. Fixed in slice 1b by registering
the guard as a `NutritionTarget.hard_ceiling`, which no rung may widen past.

**Disposition: both corrections applied to `docs/design/target_model_v2.md` in
the same commit as slice 1b.**

---

## 2026-07-31 — the evidence chain was not reproducible (finding 11, enlarged and CLOSED)

Not an audit pass. Recorded because the defect is about this log's own
trustworthiness, which makes it the one thing that could not be left to a
commit message.

**What was wrong.** Finding 11 below recorded that `demo.py` was referenced by
CLAUDE.md's Commands block and by `docs/methodology.md` and did not exist. That
was the visible symptom of something larger: *every* result the recent work
rests on — the library's first end-to-end plan, the sodium decline, the
rung-by-rung ladder table, the per-line salt provenance breakdown, the four
ladder-target rows quoted in the 4b write-up — was produced by a scratch script
in a session working directory. `git ls-files` returned nothing for it. None of
it could be reproduced by anyone, on any other machine, or by us the following
day.

The process rule in CLAUDE.md requires a pasted command transcript in the same
artifact as any claim about the repo's state. Every transcript quoted here
satisfied that rule literally and none of them satisfied its purpose, because
the command could not be re-run. That gap is worse than a missing file: it means
this log recorded conclusions whose evidence had already evaporated.

**What was built.** `demo.py`, tracked, at the repo root, with `library` / `plan`
/ `all` subcommands and profile and template as flags rather than edits. It
loads the real `data/` library, reports counts/rejections/warnings, prints slot
coverage for all four templates, enumerates a named template, and runs
`plan_meal` for a named profile printing the plan-or-decline, rungs applied,
skipped-locked steps, violations with actuals and bounds, and the disclosure.

Two properties are deliberate:

* **It prints the unrelaxed target and the target the ladder stopped on, each
  labelled.** The scratch script printed only `LadderOutcome.target_used` under
  a bare "meal target" heading, and that is what miscalibrated the Task 4b
  prediction — the fully-relaxed bounds were read as the bounds the plate was
  first asked to meet, so every rung looked like it still had room to give. The
  prediction was wrong for that reason and not for an arithmetic one.
* **Output is ASCII only and carries `STATUS: DEV_MODE` at both ends**, read
  from `DerivedTarget.status` rather than hard-coded. Transcripts get pasted
  into commit messages and markdown from Windows terminals; a stray em-dash
  arrives as mojibake and corrupts the evidence it was meant to preserve.

`tests/test_demo.py` (13 tests) is a smoke suite only: it asserts the script
runs, that each subcommand works, that both targets are printed, and that the
status banner appears at both ends. It asserts no nutrition value — those are
pinned in the existing suite, where a failure names the quantity.

**Reproduction check.** The reference run (`python demo.py`, north_lunch,
70 kg / 175 cm / 28 / male / moderate / maintain / vegetarian) reproduces the
Task 4b result as amended by `2c4f30f` **exactly**: 4 recipes enumerated to 4
combinations, all four rungs applied, `skipped_locked=()`, one violation —
`above_ceiling sodium_mg actual=1649.3 bound=1050.0` — and the same disclosure
string. Every ladder-target row matches. No discrepancy.

**Severity:** HIGH in kind. Nothing computed was wrong, and the reproduction
confirms that. But for a project whose entire claim is evidentiary discipline,
an unreproducible evidence chain is a failure of the thesis rather than of an
implementation, and it survived four rounds of adversarial review because every
individual transcript looked correct.

**Disposition: FIXED.** Finding 11 CLOSED. From this entry forward, a
transcript in this file that cannot be regenerated by a documented `demo.py`
invocation should be treated as not having happened.

---

## 2026-07-31 — three open questions raised by the first end-to-end plate

Not an independent audit pass. All three were observed while adding
`data/recipes/phulka.yaml` (the library's first `roti`) and running the
north_lunch pipeline end to end for the first time. None is resolved here:
each is recorded as an open question with the evidence attached, per the
audit-workflow section's rule that a finding not written here did not happen.

### Finding 15 — a combo component filled a slot alongside the base it already contains — OPEN

`core/foods/templates.py` (`NORTH_LUNCH`, `SOUTH_LUNCH`),
`core/planner/combinations.py`

The north_lunch enumeration produced exactly one combination:

```
combinations surviving the O(1) feasibility pre-filter: 1
    ['phulka@roti', 'rajma_chawal@combo_rice_legume']
```

That is a roti served alongside a rice-and-legume dish — two grain bases on
one plate. It is why carb came in far over its ceiling for the 70 kg profile:

```
above_ceiling carb_g      actual=222.8  bound=149.4
above_ceiling energy_kcal actual=1240.2 bound=989.9
```

The decline is arithmetically correct. The combination should never have been
enumerated: it is not a plate anyone would serve, and the numbers it produces
are the numbers of a plate nobody would serve.

Nothing in the slot semantics prevented it. `TemplateSlot` declares
`accepted_categories` — what a component may *be* — and has no way to declare
what a filling component may not also *provide*. `rajma_chawal`'s category is
`combo_rice_legume`, which `NORTH_LUNCH.legume_curry` accepts; that the dish
also contains 183 g of `rice_cooked`, i.e. the thing `grain_base` was filled
with separately, is invisible to the enumerator.

**The open question, unanswered here:** should a slot be able to declare what
a filling component may **not** also provide (a "provides" / "excludes"
relation between slots), or should combo-type components instead be excluded
from templates that fill their constituents in separate slots? Both have
costs — the first adds a second axis to a grammar whose whole point is being
per-meal and readable; the second means `rajma_chawal` becomes unplannable in
the only template that currently accepts it, which would return north_lunch to
zero combinations. No decision is taken in this entry and none is implemented.

**It generalises — checked, not assumed.** The same shape exists in
`SOUTH_LUNCH` and is reachable with today's data plus one recipe:
`rice_base` accepts `mixed_rice`, and `sambar_sadam` (category `mixed_rice`)
is rice *with sambar already in it*, while `gravy` is a separate required slot
accepting `sambar`/`kuzhambu`/`rasam`. The instant a `sambar` recipe is
authored, south_lunch will enumerate sambar sadam + sambar. This is not a
north_lunch quirk; it is a property of every template that accepts a composed
category in one slot and one of that composition's constituents in another.
`SOUTH_BREAKFAST` and `NORTH_DINNER` accept no composed category in any slot
and are not exposed today.

**Severity:** MEDIUM. It does not produce a wrong number — the arithmetic on
the enumerated plate is right, and the validator correctly declined it. It
produces a *correct number about the wrong plate*, and in the current library
it is the only combination there is, so the whole template's behaviour rests
on it.

**Disposition: OPEN.** Not fixed in this task by instruction; no
slot/template semantics were changed.

### Finding 16 — the interval spans the bounds the point estimate passed against — OPEN

`core/foods/nutrition_of.py`, CLAUDE.md ("Uncertainty"),
findings 3, 4 and 6 above.

The first plan the real library has ever produced end to end (loose target,
2000 kcal/day, 10 g protein floor):

```
passed: True   relaxation: ()
unit_counts: {'phulka@roti': 2, 'rajma_chawal@combo_rice_legume': 1}
point   : 669.5 kcal
interval: 495.1 - 844.0 kcal
```

±26% around the point estimate. The meal's energy band under the loose target
is narrower than the interval on the estimate that cleared it: the plan passes
on a point estimate whose own honest error bar spans well outside the bounds
being gated against.

This is **not a new finding** — it is the first observation on real data of
the incentive problem CLAUDE.md's "Uncertainty" section already states in the
abstract ("a plan with worse underlying data passes more easily than one with
better data"), and it is the reason that section disqualifies interval-overlap
gating outright. Recorded here as evidence, cross-referencing rather than
duplicating: findings 3 (double-counted bands producing ±45%), 4 (a zero point
estimate printing with no band) and 6 (the low-end clamp biasing the reported
fraction narrow) are the mechanisms; this is what they look like on a plate.

The gate itself behaved as designed — it gated on the point estimate only, and
did not consult the interval. Nothing here suggests changing that. What it
documents is that "passed" and "±26%" can be true of the same plate at the
same time, which is a fact the user-facing display has to carry.

**Severity:** LOW as a defect (nothing is wrong), MEDIUM as a disclosure
question. The plate is `dev_mode` regardless: 471.7 kcal of its 669.5 kcal —
**70.5%** — comes from `verified=False` process constants, against the ~15%
shipping threshold.

**Disposition: OPEN**, as a question about display and about the existing
open interval findings, not as a new defect in the gate.

### Finding 17 — the fat floor was missed by 0.1 g, on precisely the known data gap — OPEN

`data/raw/ifct/fixture_ingredients.csv` (`sunflower_oil`, `gingelly_oil`),
`docs/methodology.md`

For the 70 kg profile, three of four violations missed their bound by a wide
margin. The fourth did not:

```
below_floor fat_g actual=20.5 bound=20.6
```

0.1 g, or 0.5% of the floor. A phulka is essentially fat-free (0.5 g per
roti, all of it from the atta), so the plate's entire fat load is
`rajma_chawal`'s 8 g tempering-oil line — and oils are the one category IFCT
2017 structurally cannot supply. Both oil rows in the fixture carry the
provenance note that IFCT's tabulated rows for oils report `energy_kcal=0`
and all micronutrients zero alongside `fatce=100`, i.e. no full nutrient
panel; both remain hand-entered approximations. The single constant governing
how much of that oil is retained, `oil_uptake.vegetable_tempering`, is a
`verified=False` project estimate with no matching primary source.

So the one macro that came down to a coin-flip is the one macro whose value
rests entirely on the library's least-supportable data. This is a
coincidence, not a causal finding — a 0.1 g miss on a 20.6 g floor is well
inside any reasonable band on that oil line, which is the point: the verdict
on this macro is not distinguishable from noise, and it happens to be the
verdict that decided a bound.

**Worth watching, explicitly:** whether this near-miss survives the task-4b
recipes (`dal_tadka`, `onion_raita`), both of which add fat — the dal
through its own tempering line, the raita through curd. If the fat floor
clears comfortably once they are in, the observation stands as a warning about
thin-library behaviour rather than a live problem. If it stays marginal, the
oil rows move up the verification queue.

**Severity:** LOW today. Recorded because a bound decided inside the noise
floor of the underlying data is the shape of thing this log exists to notice
before it decides something that matters.

**Disposition: OPEN.** No constant moved, no evidence grade changed.

### Cross-reference — `process_uncertainty` without `process_constants`, against finding 2

`tests/test_recipes.py::TestRecipeLoaderRules::
test_declared_uncertainty_is_backed_by_registered_constants` is **red as of
this entry, deliberately left unfixed.** `phulka` has a non-empty
`process_uncertainty` (0.2 bands on `fibre_g`/`iron_mg`/`calcium_mg`/`b12_ug`,
from `process_uncertainty_unassessed`) and an empty `process_constants`,
because it declares no `process:` line on any ingredient — a phulka is
dry-griddled, so no oil-uptake constant applies. The test asserts
`if recipe.process_uncertainty: assert recipe.process_constants`.

This meets **finding 2** at the same seam from the opposite direction.
Finding 2 is that a recipe with no `process:` lines reads as fully
process-*certain* — uncertainty wrongly absent. This is a recipe with no
`process:` lines whose uncertainty is correctly *present*, via the
`unassessed` path, and a check that looks for it in the wrong field. Both are
about what the absence of a `process:` line is allowed to mean. The
`unassessed` band *is* backed by a registered constant
(`process.unassessed_uncertainty`), just not one attached to any line, which
`process_constants` is derived from.

`phulka` is the first recipe in the library to use the unassessed path without
also using the per-line path, which is why the assumption held until now.

**Disposition: OPEN**, deliberately, and the test stays red. Fixing it means
deciding what finding 2 decides, and that decision is not taken here.

---

## 2026-07-22 — Phase 3 build notes: two self-caught defects

Not an independent audit pass. Both were caught while building
`core/planner/validator.py`, and both are recorded because they are instances
of failure modes CLAUDE.md names by name.

### Finding 13 — a hand-computed test expectation was wrong, and its own test agreed with it

`tests/factories.SOUTH_LUNCH_MAX_PROTEIN_G` was `33.6 g`, and
`tests/test_planner_solver.py::TestThinFeasibleSet::
test_the_synthetic_pool_cannot_reach_90g_protein_at_all` asserted exactly that
value against a comment restating the same derivation. The derivation summed
*both* crisp candidates (`crisp_a` 1.0 + `crisp_b` 0.3, doubled), but the
`crisp` slot has `max_selections=1`, so no combination ever contains two. The
true maximum is `33.0 g`.

The test passed throughout Phase 2 because the assertion and the comment were
the same mistake written twice. CLAUDE.md's testing convention ("expected
values are hand-computed, with the arithmetic shown in a comment") is
necessary but, as this shows, not sufficient: a hand-computed value is only
worth what its derivation is worth, and a comment cannot check itself.

**Severity:** LOW in consequence — the conclusion the test drew (33.6 < 90, so
the audit's thin case really is infeasible) is still true at 33.0, and nothing
in `core/` read the constant. MEDIUM in kind: it is precisely the
"code and docs agree with each other and neither survives a concrete input"
shape this log exists to catch, committed in a test rather than in a doc.

**Disposition: FIXED.** Value corrected to 33.0 with the per-slot arithmetic
shown, and a second test
(`test_the_hand_derived_max_matches_what_enumeration_actually_reaches`) now
cross-checks the hand-derived figure against what `enumerate_combinations` +
`macro_bounds` actually reach, so the arithmetic and the code must agree with
*each other*, not only with themselves. This is a cross-check, not a snapshot:
the hand-derived value is still stated and readable in `tests/factories.py`.

### Finding 14 — the relaxation ladder searched a set pre-filtered against the un-relaxed target

First implementation of `plan_within_ladder` took an already-pre-filtered
combination set and re-solved it after each rung. The O(1) feasibility
pre-filter is target-dependent, so the set handed in had already been pruned
to fit the *tight* target: every rung then widened a target and searched a
population selected to fit the target it was widening. Plans the ladder should
have found were unreachable, and the failure is silent — the system declines,
with a decline message that correctly names a constraint, and nothing
indicates the search space was wrong.

Measured on the Phase 2 synthetic pool: 17 of 144 combinations survive the
pre-filter under a 500 mg sodium ceiling; 141 survive once rung 1 drops it.
The plan the corrected ladder returns is *not* in the 17.

**Severity:** HIGH. It defeats the ladder for exactly the profiles the ladder
exists for, and presents as a legitimate decline.

**Disposition: FIXED.** `plan_within_ladder` now runs `feasible_combinations`
itself, once per rung, against that rung's target, and its docstring states
that callers must pass the enumerated set rather than a pre-filtered one.
Pinned by `tests/test_planner_validator.py::TestLadderFires::
test_relaxation_recovers_combinations_the_tight_pre_filter_discarded`, which
asserts the chosen plan is one the tight pre-filter discarded — a test that
fails if the pre-filter is ever hoisted back out.

---

## 2026-07-21 — Phase 2 build note: finding 1 closed, finding 2 status clarified

Not an independent audit pass (no fresh read-only subagent run against this
diff yet — that is still open work). Recorded here because building
`core/planner/candidates.py` directly resolves one open finding and bears on
another, and CLAUDE.md's audit-workflow section says a finding's disposition
belongs in this file, not only in a commit message.

**Finding 1 ("the protein eligibility ceiling is applied to a quantity that
is 0.0 for every recipe") — CLOSED.** `core/planner/candidates.py` gates on
`core.foods.nutrition_of.NutritionEstimate.uncertainty_fraction` — composition
uncertainty (mandatory per ingredient, never zero) plus process uncertainty —
computed via `nutrition_of_components` for each candidate recipe, not on
`Recipe.process_uncertainty` alone. `tests/test_planner_candidates.py::
TestUncertaintyEligibility::test_every_real_recipe_is_excluded_in_validated_mode`
asserts, per real recipe, that the combined protein fraction is pinned at
0.25 against a 0.15 ceiling (matching the figure already pinned in
`tests/test_nutrition_of.py::TestEligibilityConsequence`) and that all three
are excluded with `dev_mode=False`. CLAUDE.md's "Uncertainty" section wording
is corrected to say "combined composition-plus-process uncertainty" rather
than "process uncertainty."

`dev_mode` (named as a requirement in `docs/methodology.md`'s "dev_mode versus
validated" section, not previously implemented anywhere) is now a real
parameter on `build_candidate_pool`: `False` (default) excludes a recipe that
misses a ceiling; `True` keeps it and records the miss in
`CandidatePool.flagged` rather than silently treating it as validated. The
Phase 2 property test (200 random moderate profiles) runs against a synthetic,
tightly-verified fixture (`tests/factories.py`, not real recipe data) that
clears both ceilings even with `dev_mode=False` — it does not depend on
suspending the ceiling, and a separate test confirms the real library still
clears nothing.

**Finding 2 ("a recipe with no `process:` lines reads as fully
process-certain") — still OPEN, scope note added.** This finding is about
`core/foods/recipe_loader.py`'s `_derive_process_uncertainty` and
`core/foods/nutrition_of.py`'s `_depends_on_unverified`, neither of which
`core/planner` touches. It is not silently inherited by the eligibility filter
today: `Ingredient.composition_uncertainty` is mandatory per macro (construction
fails on an unpopulated entry — see `core/foods/models.py`), so the *combined*
figure `candidates.py` gates on can never be zero for a recipe built from
today's fixture, independent of whether that recipe declares any process at
all. The exposure finding 2 actually describes — a *verified*, tight-composition
ingredient combined with an undeclared process on a griddled or fried dish —
does not exist in the current fixture (every ingredient but `water` is
unverified) and so cannot presently slip through `candidates.py` either. It
would as soon as that combination exists. Closing finding 2 before that point
is still the right order of work; it just is not blocking today's `dev_mode`
eligibility behaviour the way finding 1 was.

---

## 2026-07-21 — audit of `7d9bc41` and `26e5ff4`

**Scope.** Composition uncertainty (`7d9bc41`) and the derive-process-uncertainty
/ pin-guards / restore-build-status pass (`26e5ff4`). Diff audited:
`git diff 116c765..HEAD`.

**Auditor.** Read-only subagent (Read/Grep/Glob + read-only Bash), no write
access to `core/`. `.claude/agents/auditor.md` and `.claude/commands/grill.md`
described in CLAUDE.md do not exist yet; this ran as an ad-hoc equivalent under
the same permission boundary. Building the persistent definitions is open work.

**Suite at time of audit:** `python -m pytest tests/ -q` -> `124 passed in 0.17s`.
**Suite after the fixes below:** `python -m pytest tests/ -q` -> `124 passed in 0.19s`.

**Summary:** 12 findings — 2 HIGH, 1 MEDIUM/HIGH, 3 MEDIUM, 6 LOW/doc-drift.
Six fixed in the follow-up commit (all of them statements that were simply
false); six left OPEN because they need a design decision rather than a
correction. Findings 1 and 2 are both in the permissive direction — they would
let the planner ship plans the project says it cannot — and should be closed
before `core/planner` starts.

### Cleared — checked and found sound

Recorded because knowing what was tested and cleared is as useful as the
findings, and because a later reader should not re-derive these.

- **`_composition_band` weighting is genuinely per-ingredient**, not an artifact
  of every row currently carrying 0.25. Flipping only `rajma_cooked` to verified
  moved `rajma_chawal`'s protein band 0.25 -> 0.12564, matching
  `(9.570/15.391)*0.05 + (5.821/15.391)*0.25` exactly.
- **Same ingredient on two lines with different process keys** (masala dosa's two
  `gingelly_oil` lines) derives correctly: 6.188 + 2.652 = 8.84 kcal.
- **Derived uncertainty cannot currently exceed 1.0** — the numerator sums a
  subset of the denominator's lines, all non-negative, so it is bounded by the
  largest constant uncertainty (0.20 today). No guard exists, but it is not
  reachable. See finding 6 for the related clamp issue.
- **The macro-share table in `docs/methodology.md` is arithmetically correct.**
  Independently recomputed: `rice_cooked` 39.34%/28.49%, `rajma_cooked`
  14.53%/34.71%, top eight = 93.04% energy / 91.90% protein.
- **`test_mutating_a_constant_moves_every_recipe_that_depends_on_it` is a real
  perturbation test**, not a self-consistency check.

### Findings

**1. The protein eligibility ceiling is applied to a quantity that is 0.0 for
every recipe — HIGH**
`core/foods/models.py:291-293`, `core/nutrition/citations.py` (`eligibility.max_protein_uncertainty`),
CLAUDE.md:136-137, `docs/methodology.md`

CLAUDE.md says the filter excludes "a recipe whose **process uncertainty** on a
given macro exceeds a stated ceiling", and `Recipe.process_uncertainty`'s
docstring says it is "Read later by the candidate eligibility filter". Measured
process protein uncertainty:

```
masala_dosa  0.0
rajma_chawal 0.0
sambar_sadam 0.0
```

Oil carries no protein, so no derived process term ever touches that macro. A
`core/planner` author implementing exactly what the docs instruct gets
`0.0 < 0.15` -> **every recipe eligible**, `dev_mode` never needed, all 124 tests
still green. Nothing in `core/` reads `eligibility.max_protein_uncertainty` —
only the tests. The `TestEligibilityConsequence` guards assert on
`NutritionEstimate.uncertainty_fraction`, a *different* quantity from the one the
ceiling is documented to gate.

This is the specific edit that makes the library "pass" with no test failing,
and it is the edit the docs tell you to make. `docs/methodology.md`'s "the
candidate pool is empty for every profile" is not enforced by anything.

*Disposition:* OPEN. Needs a decision: the ceiling must gate the **combined**
band (composition + process), and CLAUDE.md's wording must change to say so.

**2. A recipe with no `process:` lines reads as fully process-certain and 0%
unverified — HIGH**
`core/foods/recipe_loader.py` (`_derive_process_uncertainty`),
`core/foods/nutrition_of.py` (`_depends_on_unverified`)

A plain idli (rice + urad + water + salt, no oil line, no
`process_uncertainty_unassessed`) loads with all nine macros at 0.0 and
`unverified_energy_fraction() == 0.0` — against the 15% shipping threshold.

The loader docstring claims "the author cannot obtain [zero] by leaving the work
undone." The author obtains it precisely by leaving the work undone: omit
`process:` from every line. Nothing checks that a griddled, fried or boiled dish
declares any process at all. `Recipe.__post_init__`'s mandatory-per-macro rule is
satisfied by nine computed zeros.

This is the **permissive** direction of the attribution error, the opposite of
the over-attribution recorded as methodology limitation 8.

*Disposition:* OPEN. This is the same class as the defect `26e5ff4` fixed and
was introduced by the same change.

**3. `unassessed` + composition double-counts on cooked-basis rows, producing
±45% — MEDIUM/HIGH**
`core/foods/nutrition_of.py` (`_interval_for_recipe`), `core/nutrition/citations.py`

All three recipes display iron and calcium at **±45%** (0.25 composition + 0.20
unassessed process). `rajma_chawal` renders iron as `~3.2 mg (+/-45%)`, of which
87.8% comes from `rice_cooked` and `rajma_cooked` — **cooked-basis composition
records**.

The composition constant's registered `phenomenon` is dispersion in a value "as
eaten"; the unassessed constant's is change "during domestic cooking". On a
cooked-basis row those two phenomena describe the same span, and the code adds
them. Roughly half the widest band in the product is charged twice for a step the
recipe does not perform.

This is a `phenomenon`-mismatch of the exact kind CLAUDE.md's citation section
exists to catch — caught between two constants rather than between a constant and
a paper. Neither the docs nor any test mentions 0.45.

*Disposition:* OPEN.

**4. A macro with a zero point estimate displays with no band, including
declared-unassessed ones — MEDIUM**
`core/foods/nutrition_of.py` (`uncertainty_fraction`, `_interval_for_recipe`)

Masala dosa declares `b12_ug` unassessed (0.20 process band) yet renders
`"0 ug"` — no band, no qualifier. Both bands are multiplicative, so zero is an
absorbing state. The author's explicit "we have not assessed this" is
indistinguishable from a measured exact zero, on a vegan plan, for the one
nutrient where the distinction matters most.

Since composition uncertainty now floors everything else at 0.25, the *only*
figures that print without a band are exactly the ones the system knows nothing
about.

Same mechanism: a zero-protein component (chutney, rasam) reports
`uncertainty_fraction("protein_g") == 0.0` and clears the 0.15 ceiling.

*Disposition:* OPEN.

**5. No `max()` guard — declaring a macro unassessed can NARROW the band —
MEDIUM**
`core/foods/recipe_loader.py` (`_derive_process_uncertainty`),
`core/nutrition/citations.py` (`process.unassessed_uncertainty` note)

The constant's note claims it is "deliberately worse than any measured process
constant currently in this registry." It is not — `oil_uptake.dosa_griddled` is
also 0.20, i.e. equal, not worse. And there is no `max(derived, unassessed_band)`.
With `oil_uptake.vegetable_tempering` widened to 0.35, doing the work derives
0.35 while declaring the macro unassessed yields 0.20. Declaring unassessed
becomes the cheaper path to the tidier number — the exact inversion the constant
was registered to prevent.

`test_an_unassessed_macro_takes_the_registered_wide_band` does not test this
claim: it compares 0.20 against a dish-level derived *fraction* of 0.0395, not
against any constant.

*Disposition:* note text corrected 2026-07-21 (the "worse than any measured
constant" claim was false as written). The missing `max()` guard is OPEN.

**6. The low-end clamp silently understates the reported uncertainty fraction —
MEDIUM (latent)**
`core/foods/nutrition_of.py` (`_interval_for_recipe`, `uncertainty_fraction`)

`lows.append(max(0.0, v - half_width))`, but `uncertainty_fraction` recovers the
band as `(high - low) / (2p)`. Point 10 with half-width 12 clamps low to 0, high
22, reported fraction 1.1 against a true 1.2. The comment two lines above says "a
band wider than the point estimate is a legitimate statement about very poor
data" — the code makes that statement unreportable, and biases it narrow.

Not reachable today (max total band 0.45); reachable as soon as a wider constant
lands, and it fails in the false-precision direction.

*Disposition:* OPEN.

**7. CLAUDE.md's build-status test count is contradicted by the commit that
wrote it — MEDIUM**
`CLAUDE.md` build-status table

The table said "114 tests pass … at commit `7d9bc41`" and "(110 -> 114 tests)".
The commit that wrote those lines, `26e5ff4`, says "110 -> 124 tests" and
"124 passed in 0.17s". HEAD gives 124.

A status line whose transcript *in the same commit* refutes it — a direct
violation of CLAUDE.md's own "no unverified claims about the project's own
state". Cause: the table was written mid-session at 114 and not re-derived after
later tests landed in the same commit.

*Disposition:* FIXED 2026-07-21.

**8. `docs/methodology.md` still makes the "every ingredient row" claim the same
commit says it corrected — MEDIUM**

> "Consequently every ingredient row carries the 0.25 unverified-composition band"

`water` carries 0.05. `26e5ff4`'s message claims "Both documents corrected";
`data/raw/ifct/README.md` was, `docs/methodology.md` was not — and its own
limitation 1 correctly says "22 of 23", so the file contradicts itself.

The premise is also a non-sequitur: `Evidence.verified` and `Ingredient.verified`
are separate flags, and `water` is verified with no verified Evidence anywhere.

*Disposition:* FIXED 2026-07-21.

**9. The methodology worked example uses the superseded hand-rounded figure —
LOW**

Doc shows `process 223.65 x 0.040 = 8.9460`, half-width `64.8585`. Code and tests
give `8.8400` and `64.7525` (derived 0.03952604). The 0.040 is exactly the pasted
figure `26e5ff4` removed from the YAML; the doc's arithmetic block was not
re-derived with it.

*Disposition:* FIXED 2026-07-21.

**10. Two factual slips in the verification-priority section — LOW**

- "Wheat/atta, curd, coconut **and paneer**" — there is no paneer row in the
  fixture. Unused set is exactly `{coconut_fresh, curd_dahi, wheat_atta_raw}`.
- "verifying the **six** protein-dominant rows … changes `dev_mode` status."
  Five suffice, and per recipe far fewer: `rajma_cooked` alone drops
  `rajma_chawal` to 0.1256 < 0.15; `{rice_cooked, toor_dal_cooked}` clears
  `sambar_sadam`; `{urad_dal_raw, rice_milled_raw}` clears `masala_dosa`.
  `potato_boiled` is not needed. The doc's inference skips that the band is a
  weighted mix.
- `test_verification_alone_would_not_clear_the_ceiling_for_free` asserts the
  opposite of what its name says.

*Disposition:* FIXED 2026-07-21 (including the test rename).

**11. `demo.py` does not exist — LOW**
`CLAUDE.md` Commands block, `docs/methodology.md`

CLAUDE.md lists `python demo.py`; methodology requires "any `demo.py` stdout" to
carry the `dev_mode` label. There is no `demo.py` and no README in the repo. Same
class as the file's own "Things that have gone wrong before" entry about claiming
artifacts that are not in the repo.

*Disposition:* **CLOSED 2026-07-31** — see the entry at the top of this file
("the evidence chain was not reproducible"). `demo.py` now exists and is
tracked; CLAUDE.md's Commands block and `docs/methodology.md` both name a
command that runs. The finding turned out to be larger than a missing file:
every result this project's recent work rests on was produced by an untracked
scratch script.

**12. Two tests pass the pre-`26e5ff4` argument type — LOW**
`tests/test_recipes.py`

`load_recipe_file(Path(bad), frozenset(ingredients))` — the signature now
requires `Mapping[str, Ingredient]`. They pass only because both raise before
reaching `_derive_process_uncertainty`; moving where the loader validates would
turn them into confusing `TypeError`s rather than the assertions they claim.

*Disposition:* FIXED 2026-07-21.
