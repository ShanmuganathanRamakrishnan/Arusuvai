# Design probes

Throwaway measurement scripts that produced the figures in a design document.
Tracked, not because they are library code — they are not, and nothing imports
them — but because `docs/audit_log.md` finding 11 was exactly this: a rule
requiring pasted evidence, satisfied for months by a script nobody could run.

A probe measures something that does not exist yet, so it cannot be a `demo.py`
invocation. That is the only reason it is here rather than there. Anything a
`demo.py` flag can produce belongs in `demo.py`.

Run from the repo root:

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/t3_shares.py
```

| Probe | Produces |
|---|---|
| `t3_shares.py` | §1 of `recipe_quantity_uncertainty.md` — share of each macro contributed by lines whose quantity is a free authoring choice |
| `t3_sweep.py` | the 45 kg profile used as the reference plate: the nearest north_lunch that solves with zero relaxation rungs |
| `t3_capped.py` | §4 — per-line bands under the mass-check cap, per-recipe and per-plate bands, and §8's unverified-energy figure |
| `t3_future.py` | §6 — the confidence label today and under a simulation of Task 6 (every ingredient verified) |
| `t3b_propagation.py` | all of `tolerance_versus_band.md` — that the composition band does not accumulate with component count, which macro each propagated band exceeds, and the point-versus-midpoint identity behind finding 21 |
| `d4_declines.py` | the 2026-08-08 D4a entry in `docs/audit_log.md` — a 144-profile x 4-template sweep of every decline, comparing what it says against which bounds are structurally unreachable and which the nearest-to-feasible plate misses, both computed independently of the code under audit. Runs on the pre- and post-D4a trees both, which is what makes its before/after delta re-measurable; see that entry's "Reproduce" for the worktree command. A second mode, `text` (added for D4c-i, 2026-08-09), prints the decline **sentences** rather than the counts that summarise them, for the 2026-08-09 D4c-i entry — same both-trees property, and it states its profile-selection rule in the output because since D3 there is no such thing as "the decline for a template" without one |
| `d5_margins.py` | the 2026-08-08 D5 entry in `docs/audit_log.md` — slack and smallest-legal-move on every bound of all four passing plates, their single-unit neighbours, and two sensitivity bisections (the sodium guard's value, and a uniform scaling of every salt figure in the library) |
| `d7_verification_horizon.py` | the 2026-08-09 D7 entry in `docs/audit_log.md` — the ten north_lunch ingredient rows a human would have to verify, and what the plate's unverified-energy fraction would become if they were, against the ~15% shipping threshold. Computes both hypotheticals itself and **never flips a `verified` flag**: a probe that sets one to answer a question is one interrupted session away from leaving it set |
| `d6_unverified.py` | the 2026-08-09 D6 entry in `docs/audit_log.md` — per ingredient line, which of a plate's calories rest on evidence nobody opened, under both the pre-D6 rule and the corrected one, with `core/`'s own answer printed beside them. The two columns are computed here rather than taken from a worktree of the old tree, so the comparison does not depend on which tree the probe runs from |
| `d4b_mutations.py` | the 2026-08-09 D4b-i, D4b-ii and D6 entries in `docs/audit_log.md` — every gate and guard in `core/planner`, each deleted in a throwaway worktree with the suite run against it, classified covered / soft-covered / survived. The one probe here that is **not** throwaway: `CLAUDE.md`'s "Deletion testing" convention points at it, so a new gate earns a new row. Unlike every other probe here it measures the **working tree**, not a fixed commit, which is the point — a test has to be gradeable before it is committed. Takes an optional filter: a module substring (`solver`) or a comma-separated id list (`C3,V10,V11`) |
| `probe_rank_input2.py` | the second probe here that is **not** throwaway: Phase R's exit-condition tool, referenced by `TASKS_3.md` and re-run after R1, R2, R4 and R5. `(profile, template)` cases (144 profiles x 4 templates) offering >= 2 valid, unrelaxed plates — the % the phase-exit gate is measured against. Formalised into the repo 2026-08-15 (R1c); see its own docstring for what it replaces and how closely it reproduces the number it was cited for |
| `probe_blocking_bounds.py` | the per-bound diagnostic behind R2 and R4's prioritisation — for every combination the O(1) feasibility pre-filter discards, which single bound (if only one) is the sole cause. Same 144-profile grid as `probe_rank_input2.py`. Formalised 2026-08-15 (R1c); its own docstring records that it does **not** reproduce the historical 591/223/19 figures R2's text cites, and why that is stated rather than tuned away |

These pin figures at one moment. They are not tests and nothing runs them in
CI; if the library changes they will report different numbers, which is the
point. A design document's figures are dated for the same reason.
