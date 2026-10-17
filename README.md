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

> **The app calls no model today.** `llm/ranker.py` was built and measured
> live against a local 7B model (2026-10-07, [N13](docs/audit_log.md)): its
> choices were no better than the planner's own nearest plate, so nothing in the
> app calls it. A written rule does that job instead — among valid plates,
> prefer one that does not serve the same main ingredient twice
> ([N14](docs/audit_log.md)). Narration is not built.

**The system tracks its own uncertainty and refuses to certify output on
unverified inputs.** `dev_mode` is not an unfinished state — it is the system
correctly reporting that nobody has opened its source documents. All 76
registered constants rest on `verified=False` evidence, so nothing can ship as
`validated`, and every transcript says so in its own first and last line.

---

## What it does

You give it a body and goal profile; it derives a nutritional target with every
number traced to a registered source, then either produces a plate of real
recipes at servable portions — whole counts of a named unit, 3 phulka rather
than 1.25× a roti — or **declines and names the exact constraint it could not
meet, and by how much**.

Across a fixed test grid of 144 bodies (3 goals × 2 sexes × 55/70/90 kg × 2
regions × 4 diets), every body gets a snack plate, and **850 of 864** breakfast,
lunch and dinner cases get a plate (each meal planned with and without a snack
in the day). The other 14 are all fat-loss vegan bodies at North breakfast or
South dinner, and for those it declines and names the constraint it could not
meet: *"carb_g is 76.3g, above its ceiling of 74.2g."* That is the system
working.

## How it works

```
Profile ─► target derivation ─► candidate filter ─► combination enumeration
                                                            │
                                    O(1) feasibility pre-filter
                                                            │
                  integer-unit solver ─► prefer no main ingredient served twice
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
| Recipes | **55** — vegetarian, vegan, egg, chicken and fish dishes |
| Templates | 8 — South and North Indian breakfast, lunch, dinner and snack |
| Ingredients | 40, of which **1** is verified (`water`, whose macros are all zero) |
| Registered constants | 76, of which **76** rest on unverified evidence |
| Status | `dev_mode`, permanently, until a human opens IFCT 2017 |
| Tests | `723 passed`, browser tests included (`FOODAI_WEB_TESTS=required`) |
| Plate coverage | snack: 144 of 144 bodies; breakfast, lunch, dinner: 850 of 864 cases |

The reference profile's North Indian lunch passes with no relaxation rung
fired. The 14 cases with no plate are pinned by name in
`tests/test_meal_coverage.py`: the test fails if any other body loses its plate,
and fails if one of the 14 gets a plate without being taken off the list.
The list has only shrunk (46 cases on 2026-10-11, 14 on 2026-10-17).

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
uvicorn api.main:app --reload  # the API: /api/targets, /api/plan, accounts
python -m http.server 3000 --directory web     # the page, at :3000
```

The page and the API run on different ports; `web/README.md` has the details.

`demo.py` is the reproducibility boundary: every transcript in the audit log
from 2026-07-31 onward must be regenerable by a documented invocation of it.

```
$ python demo.py plan --region north_indian --meal-slot breakfast --goal lose_fat     --diet vegan --weight-kg 70 --height-cm 170 --age-years 30 --sex male

  TARGET AS ASKED (unrelaxed -- before any relaxation rung fires):
      energy_kcal  floor     476.4   ceiling     526.5
      protein_g    floor      31.5   ceiling      63.0
      carb_g       floor      50.5   ceiling      68.3
      ...
  TARGET AS SOLVED (after 4 relaxation rung(s): sodium_max_fibre_min, fat_carb_tolerance, energy_tolerance, protein_tolerance):
      energy_kcal  floor     451.3   ceiling     551.6
      protein_g    floor      26.8   ceiling      63.0
      carb_g       floor      44.5   ceiling      74.2
      ...
passed         : False
PLAN           : None (declined)
violations     :
    kind='above_ceiling' macro='carb_g' actual=76.3 bound=74.2 locked_by=()
      reach='jointly_infeasible' relaxability='relaxed_to_limit'

disclosure     : No plan could be built for this profile: carb_g is 76.3g, above its ceiling of 74.2g

  END OF RUN -- STATUS: DEV_MODE. Nothing above can ship as validated.
```

Both targets are printed and labelled, because reading the fully-relaxed bounds
as the original ones caused a miscalibrated prediction once already.

## What this deliberately is not

- **Not clinical guidance.** The ladder's default ordering assumes no diagnosed
  condition. `clinical_flags` covers three conditions; anything else gets no
  protection at all.
- **Not a commerce product.** No orders, subscriptions, delivery zones or
  pricing. Accounts do exactly three things: exist, hold one profile, and
  remember the user's dish choices per meal.
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
- **[AGENTS.md](AGENTS.md)** — the architectural rules, written against specific
  named failure modes rather than from convention.
