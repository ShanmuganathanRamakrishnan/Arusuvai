@AGENTS.md

# CLAUDE.md — Claude Code only

The shared rules are in `AGENTS.md`, imported above. This file holds only what
is specific to Claude Code. Do not copy shared rules back in here: two copies
drift.

## Directory notes load automatically

`core/CLAUDE.md`, `web/CLAUDE.md` and `tests/CLAUDE.md` load on their own when
you work in those directories. They carry the open findings for that code.
Other agents are told in `AGENTS.md` to read them by hand.

## Output style

Reports use the `plain-report` output style
(`.claude/output-styles/plain-report.md`, per-machine and untracked). It matches
the "Reporting" section of `AGENTS.md`. If the style is not active in a session,
follow that section anyway.

## Auditor stays read-only

Audits run as an ad-hoc read-only subagent, configured per session.
`.claude/agents/auditor.md` and `.claude/commands/grill.md` do **not** exist;
they are a design, described in `docs/repo_policy.md`. Never give an auditor
write access to anything under `core/`, `api/` or `web/`: an auditor that can
edit what it reviews can rubber-stamp its own work. Its only writable file is
`docs/audit_log.md`.

## Plan mode first

Enter plan mode and get the owner's approval before editing any of:

- `core/planner/solver.py`
- `core/planner/validator.py` (the relaxation ladder, `plan_within_ladder`)
- `core/nutrition/citations.py`
- `core/foods/recipe_loader.py`

## Restructure note, 2026-10-17

The shared content moved to `AGENTS.md`. Every claim was checked against the
repo on the move; these were wrong or missing in the old `CLAUDE.md`:

1. **Queue file.** It named `TASKS_2.MD`. The live queue is `TASKS_3.md`.
2. **"Simulated delivery on seeded fixtures."** Dropped. No delivery code exists
   in `core/`, `api/` or `web/`; `README.md` says the project is not a commerce
   product.
3. **Mutation harness scope.** It listed the planner modules, `nutrition_of.py`,
   `recipe_loader.py` and `tests/conftest.py`. `d4b_mutations.py` now also
   targets `core/schemas/common.py`, `core/planner/plan.py`,
   `core/foods/models.py`, `core/foods/templates.py`,
   `core/nutrition/meal_target.py` and `core/nutrition/targets.py`. `AGENTS.md`
   now points at the file's own list instead of copying it.
4. **API.** The command list implied one endpoint, `POST /api/targets`.
   `api/main.py` serves 12 routes, including `POST /api/plan`.
5. **"Fired four times in two weeks."** The stop-at-premise rule has since fired
   in N13, N20, N22 and N24 as well.
6. **Missing: how work lands.** Never stated. Verified: feature branch, pull
   request into `main`, merged by the owner (PRs #41–#45).
7. **Missing: the LLM's actual state.** Invariant 1 described a ranking surface
   without saying it is not wired. `llm/ranker.py` exists; nothing in `api/`,
   `core/` or `web/` imports it (audit 2026-10-07 "N13").
8. **Missing: template count.** Never stated; `README.md` says 4. There are 8
   (`ALL_TEMPLATES` in `core/foods/templates.py`).

Previous restructure: 2026-08-12, 652 lines to 199, six claims corrected.
