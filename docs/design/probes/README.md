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

These pin figures at one moment. They are not tests and nothing runs them in
CI; if the library changes they will report different numbers, which is the
point. A design document's figures are dated for the same reason.
