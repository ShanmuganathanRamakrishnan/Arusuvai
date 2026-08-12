# CLAUDE.md

An AI meal planner for South and North Indian diets: profile in, validated meal
plan out, simulated delivery on seeded fixtures. Portfolio project. Hardened
against named failure modes, not convention — where it conflicts with how meal
planners are usually built, it wins. Restructured 2026-08-12 from 652 lines.

## Hard invariants

**1. The LLM never touches a gram value, a portion size, or any quantity that
determines nutritional content.** Its entire planning surface: rank among
already-valid candidate plans, and write narration around numbers supplied to
it. Do not restate this as "never produces a number anyone relies on" — tried,
and shown false: a portion multiplier is a number the user relies on even if a
validator later checks it, and proposing-then-checking is materially weaker than
never-touching. If a design has the LLM emit a quantity, route it through the
solver.

**2. Every nutritional constant lives in `core/nutrition/citations.py`** (or
references an `Evidence` from it) with source, DOI where one exists, grade, and
`phenomenon`. Includes yield factors, cooking losses, oil uptake — the rule does
not stop at the boundary of `data/`. Constants from memory are `verified=False`.

**3. A citation must match the mechanism, not just exist.** `phenomenon` states
what the source actually measured — frying oil-absorption literature does not
describe surface oil pickup on a griddled dosa. A real-but-mismatched citation
passes every automated check while describing the wrong food, worse than a
fabricated one anyone can falsify. On a mismatch, mark `verified=False`.

**4. Only a human who has opened the primary source may set `verified=True`.**
Same for any "mechanism confirmed" status. Self-attestation can record "no
matching source found" or "not yet reviewed" — never a positive match.

**5. No status claim without a transcript in the same artifact.** "N tests pass"
needs the output in the same message or commit, from the same session.

**6. Relaxation rung 1 widens sodium/fibre by a registered 0.50 fraction; it
does not remove the bound.** Dropping it was tried, reads as the natural
implementation, and leaves an unflagged profile with no sodium ceiling at all.
"Least load-bearing" is about relaxation order, not whether a bound applies.

**7. `Profile.clinical_flags` locks its constraint out of the ladder entirely.**
If a locked constraint empties the feasible set, decline and name it.

**8. One commit per reviewable idea.** *(Written down 2026-08-12. Applied
consistently — it is why D4b was split — but it emerged in conversation, never
in this file. Recorded as new rather than folded in: a rule that appears with no
history looks like it was always enforced.)*

**9. Reference the finding by its dated `docs/audit_log.md` entry** in the
commit that addresses it.

## Task queue protocol

From `TASKS_2.MD`'s own header — the queue is untracked, so this is the durable
copy:

> Take the topmost task marked **NEXT**. Do only that task. Every task ends the
> same way: **verify** (run the stated verification, paste the raw transcript,
> not a description of it); **commit** (one task, one commit, task ID in the
> message); **reconsider the queue** (state whether anything found changes,
> invalidates or reorders any task below); **stop** (mark this task DONE, mark
> the next NEXT, wait).
>
> Each task has a **goal** — what the task is for, not a promise about the
> outcome. If the work shows the goal was wrong, say so and stop. If a task is
> substantially larger than described, stop and say so before doing the work. If
> blocked, say what by; do not work around a blocker. Do not fix things you
> notice in passing — log them in `docs/audit_log.md` and leave them.

Two rules that governed recent sessions and lived nowhere until 2026-08-12:

- **Report before starting the next task.** Stopping is not reporting; the queue
  advances only after the result is stated.
- **If the premise turns out wrong, say so and stop — do not reshape the work to
  fit it.** Fired four times in two weeks: D5, D10, D8's stale triage, and D11's
  part 1, whose specified `core/` refactor was unnecessary because the field
  already carried the value. Each time, saying so was the result.

## Deletion testing

A test that cannot fail on the defect it names is not evidence. Every gate and
guard — any conditional, ordering, clip or construction-time check whose removal
changes pipeline output — needs a test that goes red when it is deleted. Adding
one: delete the mechanism, run the suite, watch it fail, restore. If nothing
fails, the test you were about to trust does not exist yet.

`docs/design/probes/d4b_mutations.py` does this mechanically for the planner
modules, `core/foods/nutrition_of.py`, `core/foods/recipe_loader.py` and
`tests/conftest.py` — one row per mechanism, the smallest edit that removes it,
in a throwaway worktree. It copies `core/`, `tests/` and `data/` from the
**working tree**, so a test can be graded before it is committed. Extend it when
adding a gate. A mechanism deleted deliberately loses its row; one kept as
documented-dead keeps its row with "survives" expected, so the next sweep does
not report a known answer as news.

**It cannot grade `web/`, and copying `web` in would not fix that.** The browser
loads the real directory, so a mutated copy has no effect and every row would
falsely report "survived" — the most dangerous answer this harness can give. Web
mechanisms are checked by hand, transcript in `docs/audit_log.md` (D9b is the
worked example). Do not add `web/` rows.

Five things it taught, which apply to any such check:

- **Run the whole suite, never `-x`.** The first failure under `-x` is first in
  collection order — alphabetical by filename, unrelated to the mechanism. It
  names a wiring or API test and hides the real one.
- **A test in the right file is not automatically the right test.** A `covered`
  row names the *first* scoped failure — collection order, not relevance. On D6
  three of five rows named a test already demoted as not-evidence while the
  mechanism's own test was red further down. Take the full failure list per
  mutation, and check the reverse too.
- **Check reachability before calling a survivor a hole.** See the list below.
- **A harness that parses tool output is itself a measurement.** The sweep
  matched `line.startswith("FAILED ")`, which matches nothing once pytest
  colours output — and that depends on inherited `FORCE_COLOR`/`PY_COLORS`, i.e.
  on which shell launched it. Identical code scored differently in two shells
  (finding 35). Strip formatting before matching; force the flag off.
- **An isolated run must isolate the whole input, not just the code.** The sweep
  left `data/` at HEAD, so a new loader met old YAML, every edited recipe was
  rejected on load, and the shared fixture errored on every run — mutation or not.
  It reported "5 covered" for five mechanisms it never ran (finding 42). Whatever
  a test reads is part of the tree under test.

## Things that have gone wrong before

- Stating a combination-space bound without the arithmetic against actual
  filtered recipe counts. Show the math.
- Citing a real, correctly-formatted source for the wrong physical process.
  Check `phenomenon` matches the application, not just that a DOI exists.
- Asserting the LLM "never produces a number" when its output included a portion
  multiplier. State precisely what it touches and does not.
- Claiming a durable artifact (test results, file existence) in a location that
  is not the repo being discussed.
- **Letting the cheapest authoring path produce the most confident-looking
  output.** Omitting an uncertainty field must not read as 0.0; a new wire field
  must not default to `= 0.0`; a recipe silent about its process must not read as
  process-certain. Three defects so far (finding 40, D10's `preparation: cooked`
  default, mandatory-per-macro uncertainty). Silence must cost more, not less.
- **Writing a reproducibility check that reproduces itself.** Twice: a
  transcript proving a transcript exists (finding 11), and a byte-diff run twice
  in one shell under one hash seed (finding 18). Both satisfied the rule and
  missed its purpose. Check a determinism claim *across the axis it claims
  independence from* — a different process, a different machine.
- **Writing a before/after probe that can only run on the "after" tree.** It
  must read only fields present on both sides. `d4_declines.py` read a field D4a
  introduced, so the before column in the 2026-08-08 entry was real when taken
  and unmeasurable an hour later.
- **Calling a survived mutation a hole before checking it is reachable.**
  `_relax_protein`'s locked-protein guard was reported as a live clinical-safety
  hole and nearly given its own commit; rung 4's only macro is protein, so the
  ladder skips the rung and the guard never runs. Settled by putting an
  unconditional `raise` in the branch and running the suite — not by reading the
  code. Survivors are cheap to produce, so this misreading is likeliest to recur.
- **Writing a test that cannot fail on the defect it names.** Inject the defect
  and watch it go red first. Finding 18's first three tests all passed against
  the defect: one exercised a slot with candidates in one category only, so the
  permutation was a no-op; another compared unsorted against sorted order, which
  coincide under many hash seeds.
- **Carrying a stale claim into a fresh-looking home.** A restructure is the
  easiest moment for this. Anything moved verbatim gets read against the current
  audit log first; anything that no longer holds gets corrected in place with a
  note. The 2026-08-12 move corrected six.

## Commands

```bash
python -m pytest tests/ -q          # before trusting any status claim
FOODAI_WEB_TESTS=required python -m pytest tests/ -q
                                    # ...and this before trusting green to mean
                                    #   the frontend was checked: without it the
                                    #   browser tests skip and the run exits 0.
python demo.py                      # library, slot coverage, enumeration, plan
python demo.py plan --region north_indian --meal-slot lunch --weight-kg 70
python demo.py --help               # profile and template are flags, not edits
uvicorn api.main:app --reload       # POST /api/targets
ollama serve && ollama pull qwen2.5:7b-instruct
```

`demo.py` is the tracked entry point for every transcript in `docs/audit_log.md`;
regenerate results with a command above before pasting them anywhere. It prints
the **unrelaxed** target and the one the ladder **stopped on** separately —
reading one for the other miscalibrated a prediction once.

## Where to read what

| Read | When |
|---|---|
| `core/CLAUDE.md`, `web/CLAUDE.md`, `tests/CLAUDE.md` | Automatically, in those directories. They carry the open findings for that code. |
| `docs/audit_log.md` | The authority on any finding's status. A finding not in it did not happen. |
| `docs/build_status.md`, `docs/build_log.md` | Per-module state, and the dated session history with its transcripts. Update only with a transcript in the same message. |
| `docs/methodology.md` | Known limitations, uncertainty model, the ladder in full, the shipping threshold, why nothing ships as validated. |
| `docs/design/architecture.md` | Adding a pipeline stage or meal template; deciding which package something belongs in. |
| `docs/design/round4_addendum.md` | Touching uncertainty derivation, the unverified-energy denominator, or anything recording a review status. |
| `docs/repo_policy.md` | Before adding a file to a commit; before setting up an audit. |

The task queue, `BUILD_PROMPTS.md` and the vendored `.claude/`/`.agents/` trees
stay untracked; the test is durability, not sensitivity. Check the file list
before committing, not after pushing. Reasoning: `docs/repo_policy.md`.
