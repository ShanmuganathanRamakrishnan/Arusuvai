# AGENTS.md

An AI meal planner for South and North Indian diets: profile in, validated meal
plan out, from 8 meal templates (South and North: breakfast, lunch, dinner,
snack). Portfolio project, hardened against named failure modes rather than
convention. The shared rules for every coding agent (moved from `CLAUDE.md`
2026-10-17; that file lists what was corrected on the move).

## Hard invariants

**1. The LLM never touches a gram value, a portion size, or any quantity that
determines nutritional content.** Its entire planning surface: rank among
already-valid candidate plans, and write narration around numbers supplied to
it. Do not restate this as "never produces a number anyone relies on" — tried,
and shown false: a portion multiplier is a number the user relies on even if a
validator later checks it, and proposing-then-checking is materially weaker than
never-touching. If a design has the LLM emit a quantity, route it through the
solver. (Today the app calls no model: `llm/ranker.py` exists but nothing in
`api/`, `core/` or `web/` imports it — audit entry 2026-10-07 "N13".)

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
needs the output in the same message or commit, from the same session, about
this repo — not an artifact somewhere else.

**6. Relaxation rung 1 widens sodium/fibre by a registered 0.50 fraction; it
does not remove the bound.** Dropping it was tried, reads as the natural
implementation, and leaves an unflagged profile with no sodium ceiling at all.
"Least load-bearing" is about relaxation order, not whether a bound applies.

**7. `Profile.clinical_flags` locks its constraint out of the ladder entirely.**
If a locked constraint empties the feasible set, decline and name it.

**8. One commit per reviewable idea.** *(Written down 2026-08-12. Applied
consistently — it is why D4b was split — but it emerged in conversation, never
in a rules file. Recorded as new rather than folded in: a rule that appears with
no history looks like it was always enforced.)*

**9. Reference the finding by its dated `docs/audit_log.md` entry** in the
commit that addresses it.

Not numbered, but learned from three defects (finding 40, D10's `preparation`
default, per-macro uncertainty): **silence must cost more, not less.** Omitting
an uncertainty field must not read as 0.0; a new wire field must not default to
`= 0.0`; a recipe silent about its process must not read as process-certain.

## Start of every task

1. `git fetch`, then confirm the branch. Work lands on a feature branch and
   reaches `main` through a pull request the owner merges; never commit to
   `main`. A new series of tasks gets a fresh branch off `origin/main`.
2. Read the notes for the directory you will touch: `core/CLAUDE.md`,
   `web/CLAUDE.md`, `tests/CLAUDE.md` (plain notes despite the name).
3. Search `docs/audit_log.md` for the task ID.
4. Read any claim you carry forward against the current audit log.

## Task queue

The queue is `TASKS_3.md` at the repo root, untracked, so this is the durable
copy of its protocol:

> Take the topmost task marked **NEXT**. Do only that task. Every task ends the
> same way: verify, commit, reconsider the queue, stop.
>
> Each task has a **goal** — what the task is for, not a promise about the
> outcome. If the work shows the goal was wrong, say so and stop. If a task is
> substantially larger than described, stop and say so before doing the work.
> If blocked, say what by; do not work around a blocker. Do not fix things you
> notice in passing — log them in `docs/audit_log.md` and leave them.

- **If the premise turns out wrong, say so and stop — do not reshape the work to
  fit it.** Fired in D5, D10, D8, D11, N13, N20, N22 and N24. Each time, saying
  so was the result.
- **Report before starting the next task.** Stopping is not reporting; the queue
  advances only after the result is stated.

## Finish sequence

In this order, every task:

1. **Verify.** Run the stated verification; paste the raw transcript.
2. **Commit.** One task, one commit, task ID in the message.
3. **Push** the branch.
4. **Confirm** with `git log origin/<branch> -1` that the remote has the commit.
5. **Reconsider the queue.** Does anything found change or reorder a task below?
6. **Report** (see "Reporting").
7. **Stop.** Mark this task DONE, mark the next NEXT, wait.

## Commands

```bash
python -m pytest tests/ -q -m "not web"     # fast loop, iterating only
python -m pytest tests/test_planner_*.py -q # planner only, fastest
FOODAI_WEB_TESTS=required python -m pytest tests/ -q
                    # full suite, before EVERY commit. Without the variable the
                    #   browser tests skip and the run still exits 0.
python demo.py                      # library, slot coverage, enumeration, plan
python demo.py plan --region north_indian --meal-slot lunch --weight-kg 70
python demo.py --help               # profile and template are flags, not edits
uvicorn api.main:app --reload       # serves /api/targets, /api/plan and others
ollama serve && ollama pull qwen2.5:7b-instruct   # only for llm/ probes
```

`demo.py` is the tracked entry point for every transcript in `docs/audit_log.md`;
regenerate results with a command above before pasting them anywhere. It prints
the **unrelaxed** target and the one the ladder **stopped on** separately —
reading one for the other miscalibrated a prediction once. When stating a bound
on the combination space, show the arithmetic against actual filtered recipe
counts.

## Deletion testing

A test that cannot fail on the defect it names is not evidence. Every gate and
guard — any conditional, ordering, clip or construction-time check whose removal
changes pipeline output — needs a test that goes red when it is deleted. Adding
one: delete the mechanism, run the suite, watch it fail, restore. If nothing
fails, the test you were about to trust does not exist yet (finding 18's first
three tests all passed against the defect).

`docs/design/probes/d4b_mutations.py` does this mechanically — one row per
mechanism, the smallest edit that removes it, in a throwaway worktree. Its
target list is the `= "core/..."` and `tests/conftest.py` constants at the top
of the file; read them there rather than from a summary. It copies `core/`,
`tests/` and `data/` from the **working tree**, so a test can be graded before
it is committed. Extend it when adding a gate. A mechanism deleted deliberately
loses its row; one kept as documented-dead keeps its row with "survives"
expected, so the next sweep does not report a known answer as news.

**It cannot grade `web/`, and copying `web` in would not fix that.** The browser
loads the real directory, so a mutated copy has no effect and every row would
falsely report "survived" — the most dangerous answer this harness can give. Web
mechanisms are checked by hand, transcript in `docs/audit_log.md` (D9b is the
worked example). Do not add `web/` rows.

What it taught, which applies to any such check:

- **Run the whole suite, never `-x`.** The first failure under `-x` is first in
  collection order — alphabetical by filename, unrelated to the mechanism.
- **A test in the right file is not automatically the right test.** A `covered`
  row names the *first* scoped failure (D6). Take the full failure list per
  mutation, and check the reverse.
- **Check reachability before calling a survivor a hole.** Put an
  unconditional `raise` in the branch and run the suite; do not decide by
  reading the code. `_relax_protein`'s locked-protein guard was nearly reported
  as a clinical-safety hole, but the ladder never reaches it.
- **A harness that parses tool output is itself a measurement.** Colour from an
  inherited `FORCE_COLOR`/`PY_COLORS` broke a `"FAILED "` match (finding 35).
  Strip formatting before matching; force the flag off.
- **An isolated run must isolate the whole input, not just the code.**
  Whatever a test reads is part of the tree under test (finding 42).
- **Check a determinism claim across the axis it claims independence from**:
  another process or machine, not twice in one shell (findings 11, 18).
- **A before/after probe reads only fields present on both sides**
  (`d4_declines.py`, 2026-08-08).

## Recipe authoring

The specification is `data/recipes/schema.yaml`; `core/foods/recipe_loader.py`
enforces it, and where they disagree the loader is the defect. The rules:

- **Quantities are finished weights** in the plated dish, summing to
  `serving_unit.grams_per_unit` within 2%. **State the basis per line**
  (`raw | cooked | as_used`); raw rice read as cooked is a 3x error. A raw
  constituent that absorbs water is listed raw, plus the absorbed `water`.
- **No yield factor inline**: go through `core/foods/retention.py`. **Oil lines
  record oil retained**, from a registered oil-uptake constant; the applied
  amount goes in `note`.
- **Never declare `process_uncertainty`, `process_constants` or
  `diet_patterns`.** All three are derived; the loader rejects a file that
  declares any of them.
- **Process attribution goes on the line**, naming the `citations.py` constant.
  A dish with no `process:` line declares `preparation: uncooked` or lists
  macros in `process_uncertainty_unassessed` (the default, `cooked`, is the
  demanding path on purpose).
- **`category` must be one a template in `core/foods/templates.py` accepts**;
  `main_ingredients` is required. **Portions are whole counts** in
  `[min_count, max_count]`; there is no continuous multiplier.

## Repo hygiene

- Add files by name. Never `git add -A` or `git add .`. Look at the staged file
  list before committing, not after pushing.
- Untracked on purpose: the task queue files, `BUILD_PROMPTS.md`, and vendored
  per-machine agent-tool state. The test is durability, not sensitivity
  (`docs/repo_policy.md`). Tracked files cite `docs/`, not untracked files.

## Where to read what

| Read | When |
|---|---|
| `core/CLAUDE.md`, `web/CLAUDE.md`, `tests/CLAUDE.md` | Before touching that directory. They carry its open findings. |
| `docs/audit_log.md` | The authority on any finding's status. A finding not in it did not happen. |
| `docs/build_status.md`, `docs/build_log.md` | Per-module state, and the dated session history with its transcripts. Update only with a transcript in the same message. |
| `docs/methodology.md` | Known limitations, uncertainty model, the ladder in full, the shipping threshold, why nothing ships as validated. |
| `docs/design/architecture.md` | Adding a pipeline stage or meal template; deciding which package something belongs in. |
| `docs/design/round4_addendum.md` | Touching uncertainty derivation, the unverified-energy denominator, or anything recording a review status. |
| `docs/repo_policy.md` | Before adding a file to a commit; before setting up an audit. |
| `data/recipes/schema.yaml` | Before adding or editing a recipe. |

## Reporting

The owner is Shanmu, who reads the reports and makes the decisions.

- Plain language, short sentences; explain a technical term once, where used.
- At most two options, with one recommendation and why.
- Label every claim **certain** (ran it, transcript shown), **likely** (strong
  evidence, not run) or **guess**.
- A settled decision is not reopened without new evidence; show it first.
- If something reported earlier as fixed turns out not to be, say so first.
