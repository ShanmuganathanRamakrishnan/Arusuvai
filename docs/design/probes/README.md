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
| `d4b_mutations.py` | the 2026-08-09 D4b-i and D4b-ii entries in `docs/audit_log.md` — every gate and guard in `core/planner`, each deleted in a throwaway worktree with the suite run against it, classified covered / soft-covered / survived. The one probe here that is **not** throwaway: `CLAUDE.md`'s "Deletion testing" convention points at it, so a new gate earns a new row. Unlike every other probe here it measures the **working tree**, not a fixed commit, which is the point — a test has to be gradeable before it is committed. Takes an optional filter: a module substring (`solver`) or a comma-separated id list (`C3,V10,V11`) |

These pin figures at one moment. They are not tests and nothing runs them in
CI; if the library changes they will report different numbers, which is the
point. A design document's figures are dated for the same reason.
