# tests/ — context

Root `CLAUDE.md` holds the invariants, including the deletion-testing rule and
what the mutation harness has taught. This file is the local detail.

## Expected values are hand-computed, never snapshotted

Show the arithmetic in a comment. Never assert against current output.

```python
def test_mifflin_male():
    # 10*70 + 6.25*175 - 5*28 + 5 = 700 + 1093.75 - 140 + 5 = 1658.75
    assert bmr_mifflin_st_jeor(make()) == pytest.approx(1658.75)
```

A test that pins an exact plate from the real library breaks on almost any
change, so it reports red without protecting anything specific. Useful; not
coverage. `test_the_real_library_is_entirely_unverified` is the standing example
— it was renamed and demoted in its own comment after it was measured to pass
*identically* before and after the fix it was supposed to be about.

## Running

```bash
python -m pytest tests/ -q
FOODAI_WEB_TESTS=required python -m pytest tests/ -q
```

The second one matters. Without it the ~40 browser tests skip when the dev
servers are down and the run still exits 0. `conftest.py` records every skipped
`web`-marked test and prints a block naming the count and each distinct reason;
under `FOODAI_WEB_TESTS=required` each becomes a failure. It sits on the report
rather than on the ~15 `pytest.skip` call sites — one definition instead of
fifteen, and it catches a missing Playwright, which no server check can see.

The bare-checkout promise in `pyproject.toml` is deliberate: the default still
exits 0. Naming a reason is not the same as it being seen (finding 39).

`conftest.py`'s skip rule is itself a gate and has rows W1–W6 in the mutation
harness.

## The library fixture reads `data/`

Whatever a test reads is part of the tree under test. The mutation harness once
copied `core/` and `tests/` from the working tree and left `data/` at HEAD, so a
new loader met old recipe YAML, every edited recipe was rejected on load, and
the shared `library` fixture errored on every run — mutation or not. It reported
"5 covered" for five mechanisms it never exercised (finding 42, FIXED). `data/`
is copied too now.

## Before trusting a green run

`python demo.py` is the tracked entry point for every transcript in
`docs/audit_log.md`. It prints the **unrelaxed** target and the target the
ladder **stopped on**, separately labelled. Reading one for the other caused a
miscalibrated prediction once already.
