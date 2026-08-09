"""The gate that decides what a skipped browser check means.

`tests/conftest.py` owns one rule: a ``web``-marked test that skips is recorded
and announced, and under ``FOODAI_WEB_TESTS=required`` it is a failure instead.
This file grades that rule.

What these tests are and are not
--------------------------------

They drive the hooks directly with stand-in report objects. That is deliberate,
and it is only half the evidence. Whether pytest actually honours
``report.outcome = "failed"`` set from a wrapper is not something a stand-in can
answer, so it was measured against the real suite instead, with the servers
genuinely down (`docs/audit_log.md` 2026-08-09, D8): the default run printed the
summary and exited 0, and the same run under the env var reported
``4 failed`` and exited 1.

These tests exist for the half that transcript cannot cover -- that the rule
keeps holding as the file changes -- and each was shown red against its own
deleted mechanism before being trusted.
"""

from __future__ import annotations

import pytest

from tests import conftest as ct


class _Report:
    """Enough of a ``TestReport`` for the hook to read."""

    def __init__(self, *, skipped: bool, longrepr, nodeid: str = "tests/t.py::t"):
        self.skipped = skipped
        self.longrepr = longrepr
        self.nodeid = nodeid
        self.outcome = "skipped" if skipped else "passed"


class _Item:
    def __init__(self, *keywords: str):
        self.keywords = set(keywords)


class _Terminal:
    """Records what the summary wrote, in order."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def write_sep(self, _sep, title, **_kw) -> None:
        self.lines.append(title)

    def write_line(self, line, **_kw) -> None:
        self.lines.append(line)


def _fire(item: _Item, report: _Report) -> _Report:
    """Drive the hookwrapper by hand: it runs after ``yield``, not before."""

    class _Outcome:
        def get_result(self):
            return report

    gen = ct.pytest_runtest_makereport(item, None)
    next(gen)
    try:
        gen.send(_Outcome())
    except StopIteration:
        pass
    return report


@pytest.fixture(autouse=True)
def _clean_slate(monkeypatch):
    """The recorded-skip list is module state; do not leak it between tests."""
    monkeypatch.setattr(ct, "_web_skips", [])
    monkeypatch.delenv(ct.WEB_STRICT_ENV, raising=False)


class TestStrictModeTurnsASkipIntoAFailure:
    def test_a_skipped_web_test_fails_under_the_env_var(self, monkeypatch):
        monkeypatch.setenv(ct.WEB_STRICT_ENV, "required")
        report = _fire(
            _Item("web"),
            _Report(skipped=True, longrepr=("t.py", 9, "Skipped: no static server")),
        )
        assert report.outcome == "failed"
        # The reason has to survive into the failure, or a strict CI run says
        # only that something was skipped -- which is what it was already saying.
        assert "no static server" in str(report.longrepr)

    def test_without_the_env_var_the_skip_stays_a_skip(self):
        report = _fire(
            _Item("web"),
            _Report(skipped=True, longrepr=("t.py", 9, "Skipped: no static server")),
        )
        assert report.outcome == "skipped"

    def test_a_non_web_skip_is_untouched_even_under_strict(self, monkeypatch):
        # D10's deliberately-red test and every ordinary conditional skip in the
        # suite must not be swept up by a flag about the browser surface.
        monkeypatch.setenv(ct.WEB_STRICT_ENV, "required")
        report = _fire(
            _Item("slow"),
            _Report(skipped=True, longrepr=("t.py", 9, "Skipped: unrelated")),
        )
        assert report.outcome == "skipped"
        assert ct._web_skips == []

    def test_a_passing_web_test_is_untouched(self, monkeypatch):
        monkeypatch.setenv(ct.WEB_STRICT_ENV, "required")
        report = _fire(_Item("web"), _Report(skipped=False, longrepr=None))
        assert report.outcome == "passed"
        assert ct._web_skips == []

    def test_only_the_exact_word_arms_strict_mode(self, monkeypatch):
        # An env var set to "1" or "true" must not silently do nothing, nor
        # silently do something. It reads as one word so the failure message can
        # quote it back and mean it.
        monkeypatch.setenv(ct.WEB_STRICT_ENV, "1")
        assert ct._web_strict() is False
        monkeypatch.setenv(ct.WEB_STRICT_ENV, "  REQUIRED  ")
        assert ct._web_strict() is True


class TestTheReasonIsRecoveredWhateverShapeItCameIn:
    def test_a_triple_longrepr(self):
        report = _Report(skipped=True, longrepr=("t.py", 9, "Skipped: no API"))
        assert ct._skip_reason(report) == "no API"

    def test_a_bare_string_longrepr(self):
        # importorskip produces this shape. Indexing [2] would raise here, and
        # it would raise at the moment the reason is the entire point.
        report = _Report(skipped=True, longrepr="Skipped: playwright is missing")
        assert ct._skip_reason(report) == "playwright is missing"


class TestTheSummarySaysTheFrontendWasNotChecked:
    def test_it_names_the_count_and_every_distinct_reason(self):
        for item, reason in (
            (_Item("web"), "Skipped: no static server on http://localhost:3000"),
            (_Item("web"), "Skipped: no static server on http://localhost:3000"),
            (_Item("web"), "Skipped: no API on http://localhost:8000"),
        ):
            _fire(item, _Report(skipped=True, longrepr=("t.py", 1, reason)))

        term = _Terminal()
        ct.pytest_terminal_summary(term)
        blob = "\n".join(term.lines)

        assert "web tests did not run" in blob
        assert "3 browser-backed check(s) skipped" in blob
        assert "no static server on http://localhost:3000" in blob
        assert "no API on http://localhost:8000" in blob
        # Deduplicated: two tests missing the same server is one fact.
        assert blob.count("no static server on http://localhost:3000") == 1

    def test_nothing_is_printed_when_every_web_test_ran(self):
        term = _Terminal()
        ct.pytest_terminal_summary(term)
        assert term.lines == []

    def test_strict_mode_prints_no_summary_because_the_failures_are_the_report(
        self, monkeypatch
    ):
        monkeypatch.setenv(ct.WEB_STRICT_ENV, "required")
        _fire(_Item("web"), _Report(skipped=True, longrepr=("t.py", 1, "Skipped: x")))
        term = _Terminal()
        ct.pytest_terminal_summary(term)
        assert term.lines == []
