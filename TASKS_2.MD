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

## D4 — declines that name the wrong constraint — **NEXT**

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
