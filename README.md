# Arusuvai — a meal planner that refuses to overstate what it knows

An AI meal planner for South and North Indian diets. Really, a project about
building a system that **declines rather than guesses**, using Indian meal
planning as the domain — because meal planning is a field where a confident
wrong number looks exactly like a confident right one.

Two decisions define it.

**The LLM is architecturally barred from computing anything.** Not "prompted
carefully" — structurally excluded. Every gram, portion, bound and verdict is
deterministic Python: candidates filtered, targets derived, portions solved over
**integer serving-unit counts**, validity gated. The model's only permitted
surface is ranking already-valid combinations for palatability and filling
narration templates whose numeric slots the Python layer substitutes. A solver
can enumerate every feasible plate; what it cannot know is that sambar + curd
rice + more sambar is not a plate anyone in Chennai would eat. That is the
model's job, and it is the whole of it.

> **The ranking/narration layer is not built.** There is no LLM code in this
> repo today — no client, no calls. What exists is the deterministic half, which
> is the half that has to be right for the constraint to mean anything, and the
> seams that make "the model proposes a portion multiplier" unrepresentable
> rather than merely discouraged.

**The system tracks its own uncertainty and refuses to certify output on
unverified inputs.** `dev_mode` is not an unfinished state — it is the system
correctly reporting that nobody has opened its source documents. All 63
registered constants rest on `verified=False` evidence, so nothing can ship as
`validated`, and every transcript says so in its own first and last line.

---

## What it does

You give it a body and goal profile; it derives a nutritional target with every
number traced to a registered source, then either produces a plate of real
recipes at servable portions — whole counts of a named unit, 3 phulka rather
than 1.25× a roti — or **declines and names the exact constraint it could not
meet, and by how much**.

Today, against its own small recipe library, it declines more often than not —
and when it does serve a plate it says what it could not do. The reference
profile's North Indian lunch passes only after four relaxation rungs, and
discloses the cost in the units the target was stated in: *"delivers 36.8g of
protein against a 39.2g target, a shortfall of 2.4g."* That is the system
working.

## How it works

```
Profile ─► target derivation ─► candidate filter ─► combination enumeration
                                                            │
                                    O(1) feasibility pre-filter
                                                            │
                              integer-unit solver ─► [LLM ranking: not built]
                                                            │
                                     validator ─► plate, or a named decline
```

The validator gates on the **point estimate only**, never on whether the
uncertainty interval overlaps the target. That restraint is the most important
line in the codebase: interval-overlap gating would mean a plan built on *worse*
data passes more easily, because a wider band overlaps more. It is also the more
natural-looking implementation, which is why it is guarded by a test rather than
a comment.

When nothing fits, a **relaxation ladder** loosens constraints in a fixed,
documented order — sodium/fibre, then fat/carb, then energy, then protein last
and never silently. Clinical flags lock their constraint out of the ladder
entirely; if that empties the feasible set, the system declines and says which
constraint blocked it.

## Defects it caught in itself

This is the part worth reading. Each of these was found inside the project, most
of them by its own tests or by verifying that a *previous* fix actually worked.

- **A real citation attached to a number it didn't produce.** A salt row stored
  38758 mg/100 g under a note claiming the figure was stoichiometric — but the
  stoichiometry gives 39339. A plausible derivation sitting over a number it
  never generated, inside the project's own data layer.
  ([target_model_v2.md §6](docs/design/target_model_v2.md))

- **A reproducibility rule satisfied for months by a script that was never
  committed.** Every result carried a pasted transcript, exactly as required. No
  one could re-run any of them.
  ([finding 11](docs/audit_log.md))

- **A sodium ceiling that was strict only before the ladder ran.** A proposed
  per-plate guard at 70% of a daily allowance is widened 50% by the first
  relaxation rung — permitting a single plate to carry **105% of a whole day's
  sodium**. Caught by measuring instead of reasoning.
  ([2026-08-02](docs/audit_log.md))

- **A decline diagnosed as the wrong thing entirely.** The blocking constraint
  was read as "sodium is unreachably high in this library." The library's
  cheapest north Indian lunch is 379.6 mg against a 1400 mg ceiling. The real
  cause was a *joint* energy-versus-sodium infeasibility — low-sodium plates
  can't reach the energy floor.
  ([2026-08-02](docs/audit_log.md))

- **Results that reproduced in substance but not byte-for-byte.** Enumeration
  order followed `PYTHONHASHSEED`, so two runs of identical code gave different
  transcripts. Verdicts were stable across 12 seeds and no published result ever
  depended on it — but the reproducibility claim was a coin flip.
  ([finding 18](docs/audit_log.md))

The last three share a shape the log now names explicitly: **a reproducibility
check that reproduces itself.** A transcript proving a transcript exists; a
byte-diff run twice in one shell under one hash seed. Each satisfied its rule and
missed its purpose.

## Current state, as the system reports it

| | |
|---|---|
| Recipes | **15** — every required slot in all four templates has a candidate |
| Templates | 4 (`south_breakfast`, `south_lunch`, `north_lunch`, `north_dinner`) |
| Ingredients | 29, of which **1** is verified (`water`, whose macros are all zero) |
| Registered constants | 65, of which **65** rest on unverified evidence |
| Status | `dev_mode`, permanently, until a human opens IFCT 2017 |
| Tests | `333 passed, 1 failed` (excluding 3 browser-driven web files) — the failure is deliberate, holding an open finding visible rather than letting it go quiet |

All four templates enumerate as of 2026-08-02. The gap that had kept three of
them at **zero** was *category breadth*, not recipe count, and it closed with six
files filling chutney, gravy, vegetable, curd and sabzi. Three further recipes
carrying paneer, tofu and soya then raised north_lunch to 24 combinations and
north_dinner to 12.

**The two North Indian templates now serve the reference profile, with no
relaxation rung fired.** Both south templates still decline, on sodium: a South
Indian lunch is four separately salted dishes, and two of `south_lunch`'s three
combinations sit above the per-plate sodium guard at their *minimum* serving
counts — unreachable for any profile. That the blocking number is one nobody
measured is the [open finding](docs/audit_log.md), not a detail.

This is stated, not apologised for. A portfolio project that claims validated
nutritional output on hand-entered fixture data would be demonstrating the exact
failure this codebase exists to prevent.

## Evidence discipline

Every nutritional constant — RDA figures, yield factors, oil uptake, household
measure weights — lives in one registry with a source, an evidence grade, and a
`phenomenon` field stating *what physical process the source actually measured*.

That last field exists because citation-*presence* is not citation-*relevance*.
A real, findable, correctly-formatted DOI can describe the wrong mechanism —
deep-fat frying literature does not describe surface oil pickup on a griddled
dosa. That is more dangerous than a fabricated citation, because a fabricated one
is falsifiable by anyone who looks it up. The registry keeps one such
[rejected citation](core/nutrition/citations.py) on record rather than quietly
not using it.

Constants that are project choices are graded `PROJECT_DECISION` and say so —
"a threshold this project chose, not a claim about the world" — and are
categorically ineligible to count as reviewed, however carefully argued. Only a
human who has opened the source document may set `verified=True`.

## Running it

```bash
python -m pytest tests/ -q     # browser-driven web tests need Playwright
python demo.py                 # everything, for the reference profile
python demo.py plan --region north_indian --meal-slot lunch
python demo.py plan --sodium-spent-mg 1200      # against a partly-eaten day
uvicorn api.main:app --reload  # POST /api/targets, POST /api/plan
```

`demo.py` is the reproducibility boundary: every transcript in the audit log
from 2026-07-31 onward must be regenerable by a documented invocation of it.

```
  STATUS: DEV_MODE
  These targets are dev-mode, not validated: the equations behind them have not
  yet been checked against their primary sources...

  TARGET AS ASKED (unrelaxed -- before any relaxation rung fires):
      energy_kcal  floor     854.9   ceiling     944.9
      protein_g    floor      43.6   ceiling         -
      sodium_mg    floor         -   ceiling    1400.0   [per-plate cap on a day's allowance]

  TARGET AS SOLVED (after 4 relaxation rung(s)):
      energy_kcal  floor     809.9   ceiling     989.9
      sodium_mg    floor         -   ceiling    1400.0   [per-plate cap on a day's allowance]

passed         : False
PLAN           : None (declined)
violations     :
    kind='above_ceiling' macro='sodium_mg' actual=1649.3 bound=1400.0

disclosure     : No plan could be built for this profile: sodium_mg is 1649.3mg,
                 above its ceiling of 1400.0mg (more than one plate may take of a
                 whole day's allowance)
```

Both targets are printed and labelled, because reading the fully-relaxed bounds
as the original ones caused a miscalibrated prediction once already.

## What this deliberately is not

- **Not clinical guidance.** The ladder's default ordering assumes no diagnosed
  condition. `clinical_flags` covers three conditions; anything else gets no
  protection at all.
- **Not a commerce product.** No orders, subscriptions, delivery zones or
  pricing. Accounts do exactly two things: exist, and hold one profile.
- **Not production auth.** No email verification, no password reset, no OAuth,
  and — named as a missing *safeguard* rather than a missing feature — no rate
  limiting on login.
- **Not a validated nutritional source.** See the whole of this README.

## Further reading

- **[docs/methodology.md](docs/methodology.md)** — what is known, what is
  assumed, and every limitation, including the ones that make the product worse.
- **[docs/audit_log.md](docs/audit_log.md)** — dated, append-only findings. A
  finding not written here did not happen.
- **[docs/design/target_model_v2.md](docs/design/target_model_v2.md)** — a
  design doc that opens by correcting three of its own claims.
- **[CLAUDE.md](CLAUDE.md)** — the architectural rules, written against specific
  named failure modes rather than from convention.
