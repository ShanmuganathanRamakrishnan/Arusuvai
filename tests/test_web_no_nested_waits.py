"""No browser test waits on a request and its response at once (docs/audit_log.md 2026-09-30).

A timeout inside ``with page.expect_request(...)`` wrapped around ``with
page.expect_response(...)`` does not fail one test. The outer wait's exit
re-enters Playwright's event loop while it is still running, so the sync
driver is never released, and every browser module after it in the same run
errors with "using Playwright Sync API inside the asyncio loop". One real
failure then reads as dozens. That happened in N9's deletion check A4: 1
real timeout, 28 errors.

Reproduced on its own by ``docs/design/probes/probe_nested_network_waits.py``,
where a single ``expect_response`` that times out leaves the next module clean.
The request a response answers is ``resp.value.request``, so there is no
reason to wait on both. ``expect_request`` alone is not what wedges the
driver, but nothing needs it, and banning the name is a check that cannot be
satisfied by a nesting the scan fails to recognise.

Static, not a browser test: it has to hold whether or not the servers are up.
"""

from __future__ import annotations

from pathlib import Path

TESTS = Path(__file__).parent


def test_no_web_test_uses_expect_request():
    offenders = [
        f"{p.name}:{i}"
        for p in sorted(TESTS.glob("test_web_*.py"))
        if p.name != Path(__file__).name
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if "expect_request(" in line
    ]
    assert not offenders, (
        "expect_request in a browser test; read the request from "
        f"resp.value.request instead: {offenders}"
    )
