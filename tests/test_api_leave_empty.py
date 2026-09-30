"""POST /api/plan carries removed courses in and what may be removed out (TASKS_3.md N10).

``tests/test_leave_empty.py`` is the mechanism, on synthetic data. This is the
wiring, on the real library, with the body ``tests/test_api_picks.py`` uses:
70 kg eggetarian, South breakfast. Measured 2026-09-30 (docs/audit_log.md):
the suggested plate carries a dish in ``egg_side``, which some valid plate
lacks; ``tiffin_item``, ``gravy_accompaniment`` and ``chutney`` are required.
A library change that moves these is a reason to re-pick the example.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.models import SwapSlotOut
from tests.test_api_picks import BODY, client

REQUIRED = {"tiffin_item", "gravy_accompaniment", "chutney"}


def _plan(**extra):
    res = client.post("/api/plan", json=dict(BODY, **extra))
    assert res.status_code == 200, res.text
    return res.json()


def _slots(data):
    return {c["slot"] for c in data["components"]}


def _can_be_empty(data):
    return {s["slot"]: s["can_be_empty"] for s in data["swap_options"]}


def test_no_leave_empty_field_is_the_plate_an_empty_list_gives():
    assert _plan()["components"] == _plan(leave_empty=[])["components"]


def test_only_optional_courses_are_marked_removable():
    marks = _can_be_empty(_plan())
    assert all(marks[s] is False for s in REQUIRED)
    assert marks["egg_side"] is True


def test_a_removed_course_is_off_the_plate_with_solver_counts():
    assert "egg_side" in _slots(_plan())  # precondition: there is a dish to remove

    data = _plan(leave_empty=["egg_side"])
    assert data["passed"], data["disclosure"]
    assert "egg_side" not in _slots(data)
    assert REQUIRED <= _slots(data)
    assert all(c["unit_count"] >= 1 for c in data["components"])
    # Still removable state, and still lists what could go back.
    egg = next(s for s in data["swap_options"] if s["slot"] == "egg_side")
    assert egg["can_be_empty"] is True
    assert egg["options"]


def test_removing_a_required_course_declines_in_plain_words():
    data = _plan(leave_empty=["tiffin_item"])
    assert not data["passed"]
    assert data["components"] == []
    assert "tiffin item" in data["disclosure"]
    assert "tiffin_item" not in data["disclosure"]


def test_can_be_empty_is_required_on_the_wire():
    # An omitted answer must not read as "cannot be removed" (finding 40).
    with pytest.raises(ValidationError):
        SwapSlotOut(slot="egg_side", options=[])
