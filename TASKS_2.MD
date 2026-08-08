# TASKS.md

Working queue. Lives in the repo, versioned with the code, read directly by
Claude Code.

## How to work this file

Take the topmost task marked **NEXT**. Do only that task.

Every task ends the same way:

1. **Verify** — run the task's stated verification. Paste the raw
   transcript, not a description of it.
2. **Commit** — one task, one commit, task ID in the message.
3. **Reconsider the queue** — state whether anything found changes,
   invalidates or reorders any task below. Not a formality: this queue has
   been rewritten three times because a task's result changed what should
   come next.
4. **Stop.** Mark this task DONE, mark the next NEXT, and wait.

Each task has a **goal**. The goal is what the task is for, not a promise
about the outcome — if the work shows the goal was wrong, say so and stop.
That has happened twice already (T3b's premise was wrong; D3's framing was
wrong) and both times saying so was the right result.

If a task turns out substantially larger than described, stop and say so
before doing the work. If blocked, say what by. Do not work around a
blocker.

Do not fix things you notice in passing. Log them in `docs/audit_log.md`
and leave them.

---

## Where things stand

All four templates now produce plates for the reference profile — first
time in the project. The three-katoris-of-dal artefact is gone; north plates
are roti with soya curry and paneer, or roti with soya curry, sabzi and
raita.

Standing caveats: `dev_mode` is permanently on and empties every pool when
false. Passing plates report 47–58% unverified energy against a ~15%
threshold whose denominator is known wrong (finding 20). One test is
deliberately red.

D5 measured the margins behind those four plates. Sodium is not the fragile
axis it was assumed to be (22–38% of guard margin, 28–60% of salt margin);
energy is (three of four plates have zero feasible neighbours, and they die
on energy). Two new findings, both OPEN, both logged and left: **28**, the
guard is the only thing in the system that prefers less salt — loosening it
makes plates saltier; **29**, relaxation rung 1 widens a day's *remaining*
sodium budget, so two south meals reach 2281 mg against a 2000 mg day.

D4a made the declines behind those verdicts honest — finding 24 CLOSED, and
the 2026-08-07 "a decline says less than it used to" observation with it. Two
more findings: **30** (a clinical-flag identifier in user-facing prose, with a
test asserting the leak) FIXED; **31** (macro identifiers in the same prose)
OPEN, for D9. Both were invisible to `test_web_no_identifiers.py`, which never
renders a decline — that gap is itself queued (D4c).

---

## D5 — re-scope finding 22 — **DONE 2026-08-08**

Result: **the goal's premise was wrong.** The 8.9 mg is the chosen plate's
slack against the guard, not the verdict's sensitivity to it. south_lunch
passes for every guard from 1091.5 mg to 2000 mg — a 22% margin — and passes
with every salt figure in the library scaled +28.3%. Recipe work cannot
silently flip it. See `docs/audit_log.md` 2026-08-08.

What the measurement did surface, none of it acted on:

- **north_dinner has the tighter margin**, not south_lunch: 28.7 mg of sodium
  slack against a 59.9 mg smallest legal move. south_lunch's 8.9 mg has a
  2.0 mg move available, so it is not on a cliff.
- **Energy is the fragile axis, not sodium.** Three of four passing plates
  have zero feasible single-unit neighbours, and they die on `energy_kcal`.
  north_lunch's energy ceiling has 1.4% slack against a 98.9 kcal step.
  No task in this queue is about it.
- **Finding 28 (new, OPEN):** nothing in the solver objective prefers less
  sodium, so the guard is acting as the sodium objective rather than as a
  backstop. Loosening it to 0.90 raises north_lunch's plate from 992 to
  1733 mg (+75%) on the same library and profile.

Finding 22 re-stated and still OPEN in its narrower form; its 2026-08-02
wording is obsolete (D3 changed the enumerated set).

**Goal (as written, for the record):** stop the south_lunch verdict being
decided by a 9 mg margin against a number we invented, so that later recipe
work can't silently flip it.

south_lunch passes at 1391.1 mg against the 1400 mg guard. That guard is
`day_budget.absurdity_fraction`, a `PROJECT_DECISION` constant, chosen after
seeing which plate it excluded, and it never relaxes. So whether the app can
plan a South Indian lunch currently turns on half a percent of a number
nobody derived.

- Re-state finding 22 in its current form: not "some combinations
  unreachable" but "the passing plate has 8.9 mg of headroom."
- Lay out what could change and what each costs — the guard's value, the
  guard's existence, rule (ii)'s never-relaxing property, the salt
  estimates, or nothing. **Do not pick.**
- Say what a reader should conclude about the four passing templates given
  this margin. Are they a result or a coincidence?
- Check whether the other three templates have comparable margins on any
  bound. A 9 mg margin nobody noticed suggests others may exist.

**Do not** tune the guard, any salt line, or any threshold.

**Verify:** the margin on every bound for all four passing plates,
measured.

---

## D4a — declines that name the wrong constraint — **DONE 2026-08-08**

Finding 24 CLOSED. Measured over a 144-profile x 4-template sweep
(`docs/design/probes/d4_declines.py`), before -> after: declines omitting a
real cause 12 -> 0; declines naming a bound the nearest plate meets 30 -> 0;
empty-pool declines naming no slot 72 -> 0. 156 declines before and after —
this changed what a decline says, not who is declined.

Two causes, both "stop at the first thing found": an unreachable bound
returned early and hid every other blocking bound (this is the 2026-08-07
"a decline can now say less than it used to" observation, now CLOSED), and the
nearest plate was ranked by the solver's deviation score, which is silent on
sodium and fibre because neither has a registered ideal point. A 110 kg
fat-loss profile was declined on fat and sodium while a plate existed meeting
both and short only on protein.

`Violation` now carries `reach` (`unreachable` / `jointly_infeasible` /
`plate_miss` / `empty_pool`), `relaxability` (`locked` / `never_relaxed` /
`hard_capped` / `relaxed_to_limit` / `relaxable`, derived from
`RELAXATION_ORDER` rather than a table) and `blocking_slots`. All reach the
API; none render raw.

**D4 as written was two tasks.** Finding 26's standing practice is split to
D4b below, unstarted. The five mechanisms D4a introduced each got a deletion
test, confirmed red before restoring — that is finding 26's discipline applied
to this change, not to the suite.

Two findings raised: **30** (a `ClinicalFlag` identifier was written into
user-facing decline prose, and a test *asserted* the leak) FIXED here, and
**31** (macro identifiers still are, same prose, same missed detection) OPEN
and left for D9, because the remedy is a macro-to-copy map and D4 says not to
design the screen.

**Amended 2026-08-08, same day.** The before column above was not re-measurable
as first committed — the probe read a field D4a introduced, so it ran on the
after tree only. Fixed (one `getattr`, reason at the call site); both columns
re-taken from one probe implementation across a worktree of `b72060e` and
unchanged. The commands for each column are in `docs/audit_log.md`, "Reproduce".
Finding 24 was **not** validly closable before this: the entry claimed an
improvement nobody could measure a second time. Commits `6b89ed7` (D4a) and the
amendment are pushed to `origin/main`; the earlier report that D4a was unpushed
is superseded.

---

## D4b-i — count the gates and audit their coverage — **DONE 2026-08-09**

**55 mechanisms**, not the ~25 estimated: `candidates.py` 9,
`combinations.py` 8, `solver.py` 11, `validator.py` 27. The ladder alone is a
dozen. `docs/design/probes/d4b_mutations.py` holds one row per mechanism and
the edit that deletes it, applies each in a throwaway worktree, and runs the
suite. Result: **41 covered, 1 soft-covered, 13 survived, 0 harness errors.**

The suite is in better shape than feared. Two measurement errors were made and
corrected before they reached a conclusion: `-x` classifies by pytest's
alphabetical collection order rather than by relevance (it reported finding
26's own founding example, the solver quality gate, as held up by a wiring
test — `TestTheSolverGateItself` genuinely covers it), and plate-pinning
`TestAgainstTheRealLibrary` classes were excluded and the sweep re-run, which
moved no total: all six such rows had a properly-scoped test behind the pin.

Three findings raised, all OPEN and all D4b-ii: **32** (the region hard filter
is unenforced; its test asserts too little and says so in its own comment; the
real library's categories are region-partitioned so the gate is dormant),
**33** (`C8` and `B2` are dead code — behaviour-preserving deletions no test
can catch), **34** (eight mechanisms with no deletion coverage).

`V10` was misdiagnosed as a live clinical-safety hole and corrected by
instrumentation before any work was ordered around it: the guard is unreachable
because rung 4's only macro is protein, so the ladder skips the rung first.
No survivor is a live clinical-safety hole. `CLAUDE.md` gains the practice
("Deletion testing") and the misreading (standing list).

---

## D4b-ii — write the missing tests — **NEXT**

**Goal:** close findings 32 and 34, and decide 33.

Nine items, one batch: the eight of finding 34 (`S6` `S7` `V8` `V10` `V11`
`V16` `V20` `V22`) plus finding 32's fixture fix. Each must be shown red
against the deleted mechanism before being believed — that is what this whole
task is about.

Two the reviewer should look at closely:

- **`V10`** must call `_relax_protein` directly and **say so in its own body**,
  naming `is_fully_locked` as why the ladder path cannot reach it. Otherwise it
  reads as an ordinary clinical-locking test and the next reader believes the
  ladder path is covered by it — finding 32's failure mode running in reverse,
  a test overstating its reach rather than understating it.
- **`V11`** must assert the protein ceiling is **unchanged**, not merely that
  the plate fits under it. `_relax_protein`'s docstring argues the ceiling
  passes through untouched; the assertion should mirror that claim exactly.

Finding 33 is a judgement, not a test: remove the dead code, or keep it with a
comment saying it is defensive. Decide it explicitly; do not leave it.

---

## D4b — original text, for the record

**Goal:** stop shipping tests that cannot fail on the defect they name.

Finding 26. Deleting the solver's quality gate left all 31 of slice 4's new
tests green; the pre-filter caught everything first. That is the fourth
instance in this repo (also findings 18, 27, and the slice 3 vacuous test).

- Every gate and guard in the enumeration, solver and validator paths gets a
  deletion test: remove the mechanism, confirm something goes red. Roughly 25
  mechanisms across `candidates.py`, `combinations.py`, `solver.py`,
  `validator.py` — count them first and say the number.
- Audit the existing suite for gates without such coverage. Report what you
  find, **including any you decide not to cover and why**.
- Write the practice into `CLAUDE.md` so it isn't rediscovered a fifth time.

D4a's five injections (`docs/audit_log.md` 2026-08-08, "Finding 26's
discipline") are the worked example of the format; they are not part of the
count above.

**Verify:** the mechanism count, and for each, the test that goes red.

---

## D4c — declines that name the wrong constraint, part 2

**Goal:** what D4's original text asked for that D4a did not deliver.

D4a fixed which causes are reported. It did not produce before/after decline
text for all four templates as a single artifact, and it did not touch
`test_web_no_identifiers.py`, which cannot see either the fixed leak (finding
30) or the open one (finding 31) because it sweeps static views and never
renders a decline.

Small. May fold into **D9** — check before starting whether D9 subsumes it.

---

## D4 — original text, for the record

**Goal:** make a decline tell the truth about why, so the decline screen has
something honest to render.

Findings 24 and 26, same defect from opposite directions.

**Finding 24:** when a bound discards every combination before validation,
the decline names whatever survivors fail next. A user told "energy is
unreachable" adds an energy-dense dish; every one is already excluded on the
real blocker, and they are never told which.

**The other direction:** since slice 4, south declines named only quality —
energy, fat and sodium surfaced via the best-plate probe, which an
unreachable bound short-circuits. Four problems became one.

The fix must distinguish **structurally unreachable** (no assignment can
satisfy this, whatever the user does) from **jointly infeasible** (each
bound reachable alone, none together — what north_lunch's sodium decline
actually was, misread as a sodium wall for weeks), carry
**relaxable vs locked** through, and report **all** blocking causes rather
than the first to short-circuit.

Produce the structure the screen needs; do not design the screen. Extend
`bound_source` rather than inventing a parallel mechanism — and it must
never render raw (`test_web_no_identifiers.py` sweeps for snake_case).

**D5 supplies the joint-infeasibility cases to test against.** Three of the
four passing plates have zero feasible single-unit neighbours, every one of
them broken by two or more bounds at once (`docs/audit_log.md` 2026-08-08,
"SINGLE-UNIT NEIGHBOURS"). A decline one notch harsher than any of those
profiles is jointly infeasible on energy, not on the single macro that
short-circuits first — real cases, not synthetic ones.

**Finding 26 — make the testing pattern standing.** Deleting the solver's
quality gate left all 31 new tests green; the pre-filter caught everything
first. Fourth instance in this repo of a test that cannot fail on the defect
it names (also findings 26, 27, and the slice 3 vacuous test).

- Every gate and guard in the enumeration, solver and validator paths gets a
  deletion test: remove the mechanism, confirm something goes red.
- Audit the existing suite for gates without such coverage. Report what you
  find, including any you decide not to cover and why.
- Write the practice into `CLAUDE.md` so it isn't rediscovered a fifth time.

**Verify:** each of the four templates before/after, showing what the
decline says; the three cases above demonstrated on a real or synthetic
pool.

---

## D6 — fix the unverified-energy denominator

**Goal:** make the number that decides whether anything can ever be
certified actually measure what it claims.

Finding 20: the unverified-energy fraction is wrong in both directions —
dal_tadka's whole 519 kcal charged against a 5 g oil line, phulka charged
nothing.

Nothing depends on it today, but Task 6 and the `dev_mode` exit both would,
and both are queued. Fix it before either leans on it.

**Verify:** the fraction for all four passing plates, before and after, with
the arithmetic shown.

---

## D7 — verify the north_lunch ingredients

**Goal:** produce one plan the project can stand behind, proving the
verification machinery works end to end.

Formerly Task 6. Narrow the `dev_mode` exit condition
(`methodology.md:347`) from the whole library to just the ingredients used
by north_lunch. Write the narrowing in as a deliberate scope line, in the
same voice as the existing boundaries — a named choice, not a quiet gap.
Verify those rows against IFCT 2017 with correct grading. Complete the
API/web plumbing the exit condition requires.

**Depends on D6.** Verified ingredients feeding a wrong denominator certify
nothing.

**Note:** T3b established that verification will _not_ improve the
confidence picture — two constants sit in permanent contradiction. D7 may no
longer claim that benefit.

**Verify:** the methodology paragraph, the verified rows with sources, and
one end-to-end run showing a plan not flagged `dev_mode`.

---

## D8 — the web suite

**Goal:** stop the frontend test surface reporting green when it hasn't
looked at anything, before new frontend work lands on top of it.

12 failed / 30 errors, Playwright timeouts, undiagnosed. Previously
concealed by tests that passed silently when servers were down.

Split: **(a)** make conditional passing honest — absent servers produce a
hard failure or a loud skip naming the reason. **(b)** triage with a hard
ceiling — report counts and causes, fix nothing until the list has been
seen.

---

## D9 — the decline screen

**Goal:** show a person why the app can't help them, in a way that lets them
act on it. The portfolio payoff.

Name the actual blocking constraint. Distinguish relaxable from locked.
Surface the hypertension lock when it holds — it currently engages
invisibly, and a system that explains what it won't compromise on is the
most interesting thing here. Surface `dev_mode`. Offer only suggestions that
can change the outcome.

**Depends on D4 and D8.**

---

## D10 — the red test

**Goal:** settle whether a recipe can declare uncertainty with nothing to
attribute it to.

`test_declared_uncertainty_is_backed_by_registered_constants`. The loader
cannot distinguish "raw, so genuinely zero process uncertainty" from
"cooked, but the author skipped the work." Instances now exist on both sides
(phulka, onion_raita, idli). Meets open finding 2 from the opposite
direction. Answerable; still unanswered.

---

## Queued, not yet detailed

- **Slice 6 — day-level quality floor.** 36.96 g. All four templates now
  produce plates, so the reachability computation has real per-slot figures.
  But south_lunch already passes at three rungs — sequencing three south
  meals inside one day's sodium budget is the live question, not the quality
  arithmetic. **D5 confirmed this and found the mechanism** (finding 29):
  two south meals already reach 2281 mg against a 2000 mg day, because rung 1
  widens `day_remaining` and only the per-plate guard is a `hard_ceiling`.
  Whether `day_remaining` is a tolerance at all is slice 6's first decision.
  Consider promoting this above D7/D8.
- **Finding 15** — combo component alongside its own base. Did not dissolve
  with slice 4.
- **LLM ranking layer.** south_breakfast is the first template with a real
  choice to make.
- **Non-vegetarian axis** — onboarding, filtering, schema, library. Eggs
  live here, not in a breakfast slot.
- **Beverage and crisp slots** — cheapest remaining widening, but beverage
  needs a milk row, which means another authored DIAAS.

## Not scheduled

Continental cuisine. Cost and pricing. Commerce and delivery. Landing page
plate animation.

## Standing constraints

No evidence grade moves outside D7. Do not tune a threshold, DIAAS value or
salt line to make plans pass. Do not touch the web suite, the
deliberately-red test, or finding 15 unless the task says so. Every number
in a report is measured, not asserted, with the command shown. Probes go in
`docs/design/probes/`, never pasted-and-lost.
