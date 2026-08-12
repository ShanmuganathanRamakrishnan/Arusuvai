# web/ — context

Root `CLAUDE.md` holds the invariants. This file holds what is specific to
`web/`.

## Shape

**Static HTML/CSS/JS, not Next.js.** A deliberate deviation, documented in
`web/README.md`. The root file described this directory as Next.js until
2026-08-12; it was never true in this repo.

Three routes: `index.html` (landing), `onboarding.html` (six-step wizard;
steps 1–5 need no account, step 6 is the account/save hinge),
`dashboard.html` (auth-gated, owns the plate picker and the `POST /api/plan`
call). `auth.js` is shared session/auth-modal code; `header.js` owns the nav for
all three routes in three explicit states (`anonymous`/`onboarding`/
`authenticated`) — each page declares its state and writes no nav item.

`DESIGN_SYSTEM.md` owns selected-state, chip fill and advancing-button geometry;
each is one definition.

## Local rules

- **This directory never computes nutrition.** It renders what the API sends.
- **The server sends tokens; the client writes the sentence.** Copy maps live
  here, not in `api/`. This is why `dev_mode`, `sodium_mg` and
  `chronic_kidney_disease` do not reach a visible text node — they are
  `snake_case`, and identifiers in user-facing prose have been a defect class
  three times (findings 30, 31, 36).
- **No identifier in any visible text node.** `tests/test_web_no_identifiers.py`
  sweeps ten views for `snake_case`/`SCREAMING_CASE` and fails on any. The
  allowlist is empty. Keep it empty.
- An unmapped macro degrades to vague-but-clean prose, never to its key.
  Evidence grade falls through to `Ungraded`, never to prettified prose.
- No illustrative numbers anywhere outside the landing page's documented
  calculator-dock deviation.
- New fields crossing the wire are **required, not defaulted**. `= 0.0` was
  tried on `ViolationOut.actual`/`bound` and its own deletion check passed green
  — finding 40. The cheapest path must not look the most confident.

## The deletion harness cannot grade this directory

`docs/design/probes/d4b_mutations.py` mutates a copy inside a throwaway
worktree, but the browser loads `web/` from a static server pointed at the
**real** directory. A mutated copy has no effect, so every row would falsely
report "survived" — the most dangerous answer the harness can give. Adding
`web` to the copied trees would not fix it.

Web mechanisms are deletion-checked **by hand** against the working tree, with
the transcript in `docs/audit_log.md`. D9b (2026-08-09) is the worked example.
Do not add `web/` rows.

## Open findings that affect this directory

As of 2026-08-12, from `docs/audit_log.md`, which is the authority.

| # | What |
|---|---|
| 23 | Onboarding asks for diet and nothing reads it. |

Closed recently and worth knowing about, because the mechanisms are still here:
30 and 31 (identifiers in prose), 36 (the identifier sweep described coverage it
did not have — its fixture claimed to cover a decline and never selected a plate
that declines), 37 (a `dev_mode` plate rendered with no label).

## Running the browser checks

They skip when the servers are down, and the run still exits 0. Use
`FOODAI_WEB_TESTS=required` to turn each skip into a failure. See
`tests/CLAUDE.md`.
