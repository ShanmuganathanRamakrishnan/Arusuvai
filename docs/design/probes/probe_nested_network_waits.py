"""Does a timed-out Playwright wait break every browser test after it?

docs/audit_log.md 2026-09-30. N9's deletion check A4 produced 1 real timeout
and 28 errors across four files. The first guess logged was a missing
browser clean-up in every web fixture. This probe separates the candidates on
a blank page, with no servers: each case is one module whose fixture times
out, then one clean module that only launches and closes a browser. The
clean module passing means the first did not break the run.

    python docs/design/probes/probe_nested_network_waits.py

Needs Playwright with Chromium installed (requirements-dev.txt).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

PAGE = "<select><option>a</option><option value='b'>b</option></select>"

CASES = {
    "plain wait_for_selector timeout": """
        page.wait_for_selector("#nope", timeout=500)
    """,
    "single expect_response timeout": """
        with page.expect_response("**/nothing", timeout=1000) as resp:
            page.select_option("select", "b")
    """,
    "expect_request around expect_response": """
        with page.expect_request("**/nothing", timeout=1000):
            with page.expect_response("**/nothing", timeout=1000):
                page.select_option("select", "b")
    """,
}

FIXTURE = """
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="module")
def walk():
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.set_content({page!r})
{body}

def test_first(walk):
    pass
"""

AFTER = """
from playwright.sync_api import sync_playwright

def test_after():
    with sync_playwright() as p:
        p.chromium.launch().close()
"""


def main() -> None:
    for name, body in CASES.items():
        with tempfile.TemporaryDirectory() as d:
            body = textwrap.indent(textwrap.dedent(body).strip(), " " * 8)
            (Path(d) / "test_a_first.py").write_text(FIXTURE.format(page=PAGE, body=body))
            (Path(d) / "test_b_after.py").write_text(AFTER)
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                 "--color=no", "--rootdir", d, d],
                capture_output=True, text=True,
            )
            after = next(
                (l.split(" ")[0] for l in r.stdout.splitlines()
                 if "test_b_after" in l and l.startswith(("FAILED", "ERROR"))),
                "passed",
            )
            print(f"{name:40s} next module: {after:7s} {r.stdout.strip().splitlines()[-1]}")


if __name__ == "__main__":
    main()
