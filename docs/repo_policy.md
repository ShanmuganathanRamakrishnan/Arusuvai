# Repo policy — what gets tracked, and how audits run

Moved out of `CLAUDE.md` on 2026-08-12. Read this before adding a file to a
commit, or before setting up an audit.

## What belongs in the repo, and what stays local

This is a public repository. Before adding a file to a commit, ask what a reader
who is not the author gains from it. Two categories, and the line between them
is *durability*, not sensitivity.

**Tracked — the durable record.** Product code (`core/`, `api/`, `web/`,
`data/`), the test suite, `demo.py`, and `docs/` in full: `audit_log.md`,
`build_log.md`, `build_status.md`, `methodology.md`, `design/` and
`design/probes/`. These are what the process rule is about — a finding, a figure
or a transcript that must outlive the session that produced it. `CLAUDE.md`,
`README.md` and `DESIGN_SYSTEM.md` are tracked because they are the contract,
not a status report.

**Untracked — working scaffolding.** All removed from tracking 2026-08-09, all
still on disk, all in `.gitignore`:

- `TASKS.md` and `TASKS_2.MD` — the private queue a session is driven from. A
  task list is the one artifact whose entire purpose is to be stale tomorrow:
  "D4b-ii — NEXT" is true for an afternoon, and a reader who finds it a month
  later learns something false about the repo. Everything a task file records
  that *should* survive already lands in `docs/`, by the process rule.
- `.claude/settings.local.json`, `.claude/output-styles/`, `.claude/skills/`,
  `.agents/skills/`, `skills-lock.json` — per-machine tool state. The two skills
  trees were **byte-for-byte duplicates**, so the repo carried two copies of 28
  vendored third-party files (shadcn, frontend-design and four others, one
  shipping its own `LICENSE.txt`) that are nobody's product code. Nothing in
  `core/`, `api/`, `web/`, `tests/` or `docs/` referenced them.
- `BUILD_PROMPTS.md` — the original phase-by-phase build script. This one is
  worth the extra sentence, because it looked like history and was not. It is a
  *forward-looking instruction sheet* ("feed these to Claude Code one at a time,
  in order"), which makes it the same artifact class as `TASKS.md`; and unlike a
  stale task list it has gone actively wrong. It specifies `RecipeIngredient`
  without `process_key`, a hand-declared `process_uncertainty` dict, and an
  eligibility filter gating on `process_uncertainty` alone. The first is the
  field D6's per-line attribution rests on; the second is what the round-4
  addendum forbids; the third is `docs/audit_log.md` finding 1, which
  `CLAUDE.md` corrects by name. A reader following it would build three defects
  this repo has already fixed, carrying the repo's own authority.
  `docs/build_log.md` is the durable record of what was built.

**The test to apply is durability, not sensitivity.** None of the above is
secret. Each was removed because a reader who is not the author gains nothing
from it, or is actively misled.

### Accepted consequence: dangling citations

`docs/audit_log.md` and two files under `docs/design/` cite
`TASKS.md`/`TASKS_2.MD` by name for provenance ("Task T3 in `TASKS.md`"), and
seven places in `core/` and `tests/` cite `BUILD_PROMPTS.md` the same way
(`core/nutrition/citations.py`, `core/planner/{combinations,solver,validator}.py`,
`tests/test_planner_combinations.py`, `DESIGN_SYSTEM.md`). Those citations point
outside the repo. They are left as-is — they date a decision rather than direct
a reader, and rewriting history to hide a working file would be worse than a
dangling reference. **Do not add new ones**: cite the `docs/` artifact instead.

One was checked rather than assumed before removing: `citations.py`'s
`qa.energy_reconciliation_tolerance` carries `note="Specified in
BUILD_PROMPTS.md Phase 1."`, and `note` is in `RENDERED_FIELDS`. Only
`Evidence.note` is serialised by `GET /api/science` — `Constant.note` is not —
so this string does not reach the citation panel and the dangling reference
stays internal. If `Constant` notes are ever serialised, that note must be
rewritten first.

Applies to future commits, not just the one that established it. When staging,
look at the file list before committing, not after pushing.

## Audit workflow

**Corrected on the move (2026-08-12).** In `CLAUDE.md` this section described
`.claude/agents/auditor.md` and `.claude/commands/grill.md` in the present tense,
as though they were set up, while the build-status table 20 lines below recorded
that they **do not exist**. Verified again during the restructure: `.claude/`
contains neither an `agents/` nor a `commands/` directory. The section is
rewritten below as the design it is, with the gap stated first rather than
contradicted later.

**Today:** audits run via an ad-hoc read-only subagent, configured per session.
Findings land in `docs/audit_log.md`.

**Intended, not built:**

- `.claude/agents/auditor.md` — a subagent with **read-only** tool permissions
  (`Read`, `Grep`, `Glob`, `Bash(pytest:*)` — no `Edit`, no `Write` outside
  `docs/audit_log.md`). Its job is to find places where code and the docs agree
  with each other and neither survives a concrete input. It does not propose
  fixes and does not soften findings.
- `.claude/commands/grill.md` — invokes the auditor against modules changed
  since the last `docs/audit_log.md` entry.

**Already true regardless:** `docs/audit_log.md` is dated and append-only. It is
the artifact; a finding that is not in that file did not happen, per the process
rule about unverified claims regarding the project's own state.

The read-only permission boundary is load-bearing, not incidental: an auditor
that can edit the code it is reviewing can rubber-stamp its own work exactly the
way a self-edited mechanism-match dict did in round 4. Whether the auditor is a
committed file or an ad-hoc session, do not grant it write access to anything
under `core/`, `api/`, or `web/`.

When addressing an audit finding, reference it by its dated entry in
`docs/audit_log.md` in the commit or PR description, so the fix is traceable to
the finding rather than a description of the finding living only in a chat
transcript.
