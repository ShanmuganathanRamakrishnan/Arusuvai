# Two constants that contradict each other — options, not a choice

**Status: decision material, 2026-08-02. Nothing changed. No constant moved.**
Task T3b in `TASKS.md`. Ends with options; picking one is a separate task.

Probe: `docs/design/probes/t3b_propagation.py`. Every figure below comes from it.

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/t3b_propagation.py
```

---

## 1. The relationship, measured — and T3's stated mechanism was wrong

`docs/design/recipe_quantity_uncertainty.md` §6 says a 5% per-ingredient
composition band "produces roughly a ~7% band on plate energy". The figure is
right. **The reason given for it is wrong**, and the wrong reason was doing work
— it is what made this look like a scaling problem that gets worse with bigger
plates.

T3b was written on that reason too: *"because errors accumulate across the
components of a plate"*. They do not.

Composition uncertainty is applied per line and weighted by that line's share of
the macro, then summed. A uniform fraction `u` on every ingredient therefore
sums to exactly `u` of the total, at any component count. Measured, process
terms forced to zero so the composition term is isolated:

```
u = 0.05
  1 component(s): energy=0.0500  protein=0.0500  fat=0.0500  carb=0.0500  sodium=0.0500
  2 component(s): energy=0.0500  protein=0.0500  fat=0.0500  carb=0.0500  sodium=0.0500
  3 component(s): energy=0.0500  ...
  6 component(s): energy=0.0500  protein=0.0500  fat=0.0500  carb=0.0500  sodium=0.0500

u = 0.25
  1..6 component(s): 0.2500 on every macro, at every count
```

**Flat. It does not accumulate, and there is no component count at which it
"stabilises" — it never moves.** The question T3b asks ("at what component count
does it stabilise?") has no answer because it rests on the same wrong mechanism.

The extra above `u` is entirely the **process term**, which is per-recipe and
does not scale with plate size either. On the reference plate at `u = 0.05`:

```
energy_kcal  with process 0.0689   without 0.0500   process term 0.0189
protein_g    with process 0.0500   without 0.0500   process term 0.0000
fat_g        with process 0.1169   without 0.0500   process term 0.0669
carb_g       with process 0.0500   without 0.0500   process term 0.0000
fibre_g      with process 0.0875   without 0.0500   process term 0.0375
sodium_mg    with process 0.0500   without 0.0500   process term 0.0000
```

Energy's 1.89 points come from dal_tadka's tempering oil. Protein, carb and
sodium carry no process term at all, because oil has none of them.

This correction makes the problem **smaller and sharper**: it is not a scaling
law, it is two numbers that happen to be equal.

## 2. Which tolerances are exceeded, per macro

Reference plate — the nearest north Indian lunch that solves with **zero**
relaxation rungs, so this is against the tightest bounds the system ever
applies. 45 kg / 165 cm / 35 / female / active / maintain; `phulka ×1,
dal_tadka ×3, onion_raita ×1`.

```
composition u = 0.25 (today)
  energy_kcal  h=  188.79  room=   34.57  EXCEEDS (band)
  protein_g    h=    7.30  room=    1.21  EXCEEDS (floor only)
  fat_g        h=    7.10  room=    3.17  EXCEEDS (band)
  carb_g       h=   23.41  room=   14.60  EXCEEDS (band)
  fibre_g      h=    4.89  room=    7.32  OK      (floor only)
  sodium_mg    h=  318.58  room=  125.66  EXCEEDS (ceiling only)

composition u = 0.05 (after Task 6)
  energy_kcal  h=   48.37  room=   34.57  EXCEEDS (band)
  protein_g    h=    1.46  room=    1.21  EXCEEDS (floor only)
  fat_g        h=    2.62  room=    3.17  OK      (band)
  carb_g       h=    4.68  room=   14.60  OK      (band)
  fibre_g      h=    1.49  room=    7.32  OK      (floor only)
  sodium_mg    h=   63.72  room=  125.66  OK      (ceiling only)
```

Two different kinds of failure, and they must not be lumped together:

- **Energy is a constant-versus-constant contradiction.** Its room is
  `tolerance.energy_default × midpoint` — a registered figure. It fails for
  every plate, permanently.
- **Protein's room is `point − floor`,** which depends on where the solver
  landed, not on any registered constant. It fails on *this* plate by 0.25 g.
  A plate further above its protein floor would pass. That is a solver-slack
  fact, not a contradiction, and no constant change fixes or breaks it.
- **Fat, carb, fibre and sodium are fine after verification.** `fat_carb_default`
  is 0.15 against a 0.05 composition band — three times the room needed.

**So the contradiction is energy-only.** That is a much narrower statement than
T3 made, and it is worth stating precisely.

## 3. Why energy specifically: the two numbers are equal

```
composition.verified_primary         0.05
tolerance.energy_default             0.05
composition.unverified_secondary     0.25
tolerance.fat_carb_default           0.15
tolerance.energy_relaxed             0.1
tolerance.fat_carb_relaxed           0.25
```

With the process term at zero and `u = tolerance`, the half-width is
`u × point` and the room is `tolerance × midpoint`, so the whole comparison
collapses to **point versus target midpoint**. Measured on the same plate:

```
point     702.130   midpoint  691.445   point/midpoint 1.015454
h          35.106   room       34.572   h/room         1.015454
identical to 6 dp: True
```

Two consequences, both worth stating because they say different things:

1. **With a zero process term, `confident` is not unreachable — it is a coin
   flip.** It is granted exactly when the plate's energy lands at or below the
   centre of its own target window, which is a fact about solver rounding over
   integer serving counts and carries no nutritional meaning whatsoever. A label
   decided by which side of centre a plate falls on is worse than one that never
   fires, because it looks like it means something.
2. **With the library's real process term (0.0689 total), `confident` *is*
   unreachable.** The plate would need to sit at `midpoint × 0.726` — 27% below
   centre — which is below its own energy floor of 656.9. The plate would be
   rejected before it could be labelled.

T3 reported outcome 2 and gave the mechanism for neither. Outcome 1 is the more
uncomfortable one and had not been noticed.

## 4. Options — four, none picked

### A. Widen `tolerance.energy_default`

Raise it until it exceeds the propagated band, e.g. 0.05 → 0.10.

- **Cost:** the energy gate stops being a gate. 0.10 is already
  `tolerance.energy_relaxed`, i.e. the value rung 3 relaxes *to* — so the
  unrelaxed target would equal the relaxed one and ladder rung 3 becomes a no-op.
  That is a real, checkable regression, not a stylistic objection.
- **Claimable:** "the label can reach `confident`."
- **Forecloses:** any future claim that a plan is within 5% of its energy target.
  Nothing in `web/` states that today (checked), but it is the obvious thing for
  a decline screen or a plan summary to say, and A spends it in advance.
- **New arbitrary number:** yes, and worse than the one it replaces — it would be
  chosen to make a label move, which is the perverse incentive documented in
  CLAUDE.md wearing a different hat. Widening a tolerance so that worse data
  passes is precisely the thing interval-overlap gating was disqualified for.

### B. Tighten `composition.verified_primary`

For a 0.05 band to be honest against a 0.05 tolerance, verified composition data
would have to be better than ±5%.

- **What would have to be true:** IFCT 2017 reports single values, not intervals.
  The real spread on a proximate energy value across cultivar, season and
  laboratory is not something the table states, and 0.05 was itself registered as
  a project estimate of analytical spread with no matching primary source (its
  own `REVIEWED_MECHANISM_MATCHES` entry says exactly that: *"reviewed: NO
  matching primary source; project estimate of analytical spread"*).
- **Reachable with verified IFCT rows?** **No.** Verification changes who read
  the number, not how variable the food is. Tightening the band on that basis
  would assert a precision the source does not claim — the same defect as the
  salt note.
- **Cost:** low effort, high dishonesty. Listed for completeness, not viability.

### C. Derive the tolerance from the band

Make the two related by construction: gate against `k × propagated_band` rather
than a flat registered figure, so a tolerance is always wider than the
uncertainty it is compared with.

- **Cost:** the tolerance stops being a nutritional statement and becomes a
  data-quality statement. It also **re-introduces the disqualified shape**: a
  plan built on worse data gets a wider tolerance and passes more easily. That is
  interval-overlap gating by another route, and CLAUDE.md rules it out by name.
  Unless `k` is applied only to the *label* and never to the gate — in which case
  it is option D with extra machinery.
- **Claimable:** the two numbers can no longer drift apart.
- **New arbitrary number:** yes, `k`.

### D. Remove `confident` from the scale

Two states: *rough* and *very rough*. Document that the top state is unreachable
with data of this kind and say why.

- **Cost:** the label admits it cannot deliver good news. A reader may reasonably
  ask what a scale is for when its best value is "rough".
- **Claimable:** everything the label currently claims, minus a state nothing can
  enter. Nothing is lost that was ever reachable.
- **Forecloses:** nothing — a third state can be added the day a tolerance and a
  band are reconciled deliberately.
- **New arbitrary number:** **none.** The only option on this list that adds no
  constant.

### E — noted, not in T3b's list

**Change nothing and delete the label.** T3 already found the label is
decoration: the counter-pressure that actually exists is the eligibility filter.
If the label's honest job is disclosure and the existing `±%` band and `dev_mode`
line already disclose, a three-word summary of a number already on screen may not
earn its place. Cost: nothing. Forecloses: nothing that isn't recoverable.
Mentioned because options A–D all assume the label ships.

## 5. Existing claims this affects

Quoted, so the affected text is findable rather than described.

**`docs/methodology.md`, "Verification priority":**

> "So verification is a threshold crossing with a specific, small target set,
> not a general improvement."

Still true, and now more pointedly so — but its neighbouring text lists the eight
ingredients that are "93.0% of library energy" as the work worth doing, which
reads as though doing it improves the energy picture. Measured: verifying every
row takes the energy band from 27% to 6.89%, and the energy label does not move.
The section needs a sentence saying which macro that work does and does not fix.

**`docs/design/recipe_quantity_uncertainty.md` §6:**

> "`confident` is structurally unreachable: composition uncertainty of 5% on
> every ingredient produces a ~7% band on plate energy, and the energy tolerance
> is 5%."

Conclusion right, mechanism wrong (§1), and it misses that the zero-process case
is a coin flip rather than a bar (§3). Amended in place, not silently edited.

**`docs/audit_log.md` finding 19:**

> "a 5% composition band produces a ~7% band on plate energy"

Same correction. The finding stands; its explanation does not.

**`core/nutrition/citations.py`** — `tolerance.energy_default` and
`composition.verified_primary` both carry `"reviewed: project decision"` /
`"reviewed: NO matching primary source"` entries, neither of which mentions the
other. They are registered four entries apart in the same file (positions 12 and
16 of 63) and were never compared. Nothing in the registry can express "these two
are checked against each other", so nothing flagged it.

**`CLAUDE.md`** — checked, nothing to correct. It says uncertainty is "a property
of the data, not a lever anyone adjusts", which is what makes option A improper,
and it does not claim verification improves confidence anywhere.

## 6. What this does not do

- Picks nothing. Options only, per T3b.
- Moves no constant, no evidence grade, no recipe, no ingredient.
- Does not touch the energy gate. The validator's behaviour is unchanged; this is
  about a label that is not built and a tolerance nobody has compared to
  anything.
