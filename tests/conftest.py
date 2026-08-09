from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.foods.ifct_loader import LoadReport, load_ingredients
from core.foods.recipe_loader import RecipeLibrary, load_recipes

REPO_ROOT = Path(__file__).resolve().parents[1]
INGREDIENT_DIR = REPO_ROOT / "data" / "raw" / "ifct"
RECIPE_DIR = REPO_ROOT / "data" / "recipes"

#: Set this to make a skipped ``web`` test a failure instead. The web tests are
#: dev-only by design -- a bare checkout has no Playwright and no servers, and
#: `pyproject.toml` promises `python -m pytest tests/ -q` runs clean there. That
#: promise is worth keeping and is also exactly how a frontend test surface
#: reports green without having looked at anything, so the strict reading has to
#: be available to whoever wants it: CI, or a person about to trust a green run.
WEB_STRICT_ENV = "FOODAI_WEB_TESTS"

#: Reasons for every ``web`` test that skipped this session, as
#: ``(nodeid, reason)``. Collected in the report hook below and read by the
#: terminal summary, so the count printed is the count actually observed rather
#: than a second guess at which tests are web tests.
_web_skips: list[tuple[str, str]] = []


def _web_strict() -> bool:
    return os.environ.get(WEB_STRICT_ENV, "").strip().lower() == "required"


def _skip_reason(report) -> str:
    """The reason out of a skip report, whatever shape pytest used for it.

    A skip's ``longrepr`` is a ``(path, lineno, reason)`` triple, but
    ``importorskip`` and a few other paths produce a plain string. Reading
    ``[2]`` unconditionally would raise on those and lose the reason at the one
    moment it is the whole point of the message.
    """
    longrepr = report.longrepr
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        reason = str(longrepr[2])
    else:
        reason = str(longrepr)
    return reason.removeprefix("Skipped: ")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Record -- and under strict mode, fail on -- a skipped ``web`` test.

    This sits on the report rather than on the ~15 individual ``pytest.skip``
    call sites in the three web test files, for two reasons. It is one
    definition instead of fifteen; and it catches every cause of a web skip,
    including a missing Playwright, which no server check would ever see. The
    call sites keep deciding *whether* a prerequisite is missing -- they know
    which of the two servers each test needs, and that knowledge should not be
    duplicated here -- while this decides what a missing prerequisite means.
    """
    outcome = yield
    report = outcome.get_result()
    if not report.skipped or "web" not in item.keywords:
        return
    reason = _skip_reason(report)
    _web_skips.append((report.nodeid, reason))
    if _web_strict():
        report.outcome = "failed"
        report.longrepr = (
            f"{WEB_STRICT_ENV}={os.environ[WEB_STRICT_ENV]}, so a skipped browser "
            f"check is a failure: {reason}"
        )


def pytest_terminal_summary(terminalreporter) -> None:
    """Say plainly that the frontend was not looked at.

    Without this the only trace is the skip count in `1 passed, 40 skipped`,
    which reads as a clean run. The reasons exist -- measured 2026-08-09, every
    one of them names its missing server -- but only under `-rs`, which nobody
    passes by habit. Naming the reason is not the same as being seen.
    """
    if not _web_skips or _web_strict():
        return
    reasons = sorted({reason for _, reason in _web_skips})
    terminalreporter.write_sep("=", "web tests did not run", yellow=True, bold=True)
    terminalreporter.write_line(
        f"{len(_web_skips)} browser-backed check(s) skipped. Nothing in web/ was "
        f"verified by this run."
    )
    for reason in reasons:
        terminalreporter.write_line(f"  - {reason}")
    terminalreporter.write_line(
        f"Start the servers (see web/README.md), or set {WEB_STRICT_ENV}=required "
        f"to make this a failure."
    )


@pytest.fixture(scope="session")
def load_report() -> LoadReport:
    return load_ingredients(INGREDIENT_DIR)


@pytest.fixture(scope="session")
def ingredients(load_report: LoadReport):
    return load_report.loaded


@pytest.fixture(scope="session")
def library(ingredients) -> RecipeLibrary:
    return load_recipes(RECIPE_DIR, ingredients, strict=True)
