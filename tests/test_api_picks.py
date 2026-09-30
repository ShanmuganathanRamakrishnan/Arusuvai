"""POST /api/plan carries the user's picks in and the swap options out (TASKS_3.md N8).

``tests/test_dish_picks.py`` is the mechanism, on synthetic data. This is the
wiring, on the real library: breaks if the library changes so that this
body's South breakfast no longer has the plates named below, which is a
reason to re-pick the example, not to doubt the mechanism.

Body: 70 kg, 175 cm, 28 y, male, moderate, maintain, eggetarian, South
breakfast. Measured 2026-09-29 (docs/audit_log.md): onion_tomato_uttapam is
on a valid plate at the rung this meal stops on; plain_dosa is on none.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

BODY = dict(
    weight_kg=70, height_cm=175, age_years=28, sex="male", activity="moderate",
    goal="maintain", diet="eggetarian", clinical_flags=[],
    region="south_indian", meal_slot="breakfast",
)


def _plan(picks=None):
    body = dict(BODY) if picks is None else dict(BODY, picks=picks)
    res = client.post("/api/plan", json=body)
    assert res.status_code == 200, res.text
    return res.json()


def _options(data):
    return {s["slot"]: [o["recipe_id"] for o in s["options"]] for s in data["swap_options"]}


def test_no_picks_field_is_the_plate_an_empty_pick_list_gives():
    assert _plan()["components"] == _plan([])["components"]


def test_every_shown_dish_is_among_its_own_slots_options():
    data = _plan()
    assert data["passed"]
    options = _options(data)
    for c in data["components"]:
        assert c["recipe_id"] in options[c["slot"]], c


def test_a_pick_is_on_the_plate_with_solver_counts():
    shown = {c["recipe_id"] for c in _plan()["components"]}
    assert "onion_tomato_uttapam" not in shown  # precondition: it is a swap

    data = _plan(["onion_tomato_uttapam"])
    assert data["passed"], data["disclosure"]
    tiffin = [c for c in data["components"] if c["slot"] == "tiffin_item"]
    assert [c["recipe_id"] for c in tiffin] == ["onion_tomato_uttapam"]
    assert all(c["unit_count"] >= 1 for c in data["components"])


def test_a_pick_with_no_valid_plate_declines_by_name_and_still_offers_its_slot():
    data = _plan(["plain_dosa"])
    assert not data["passed"]
    assert data["components"] == []
    assert "Plain dosa" in data["disclosure"]
    assert "plain_dosa" not in data["disclosure"]
    assert data["violation_detail"], "a decline names what the nearest plate breaks"
    # The tiffin slot still lists what fits, so the user can choose again.
    assert _options(data)["tiffin_item"] == _options(_plan())["tiffin_item"]
