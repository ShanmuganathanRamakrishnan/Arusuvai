"""A user's dish choices for a meal are kept between visits (TASKS_3.md N11).

``GET /api/choices`` lists them and ``PUT /api/choices`` keeps, replaces or
(with two empty lists) forgets one meal's. They are recipe ids and course
names only; whether they fit is asked of the planner at plan time, every
visit, because a profile edit changes the answer 20% of the time
(docs/audit_log.md 2026-10-02).

Isolated in-memory database per test, as ``tests/test_api_auth.py``.
Real library: ``onion_tomato_uttapam`` and ``soya_curd`` are South breakfast
dishes, ``egg_side`` and ``curd_course`` its optional courses,
``tiffin_item`` a required one, and ``paneer_masala`` a North lunch dish.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.db import Base, get_db, make_sessionmaker
from api.main import app

BREAKFAST = {"region": "south_indian", "meal_slot": "breakfast"}


@pytest.fixture()
def client():
    SessionLocal, engine = make_sessionmaker("sqlite:///:memory:")

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)


def _sign_up(client, email="choices@test.com"):
    res = client.post("/api/auth/signup", json={"email": email, "password": "password123"})
    assert res.status_code == 201, res.text


def _put(client, picks, leave_empty, meal=BREAKFAST):
    return client.put("/api/choices", json=dict(meal, picks=picks, leave_empty=leave_empty))


class TestKeepingChoices:
    def test_saved_choices_come_back(self, client):
        _sign_up(client)
        res = _put(client, ["onion_tomato_uttapam"], ["egg_side"])
        assert res.status_code == 200, res.text
        assert client.get("/api/choices").json() == [
            dict(BREAKFAST, picks=["onion_tomato_uttapam"], leave_empty=["egg_side"])
        ]

    def test_saving_again_replaces_not_adds(self, client):
        _sign_up(client)
        _put(client, ["onion_tomato_uttapam"], ["egg_side"])
        _put(client, ["soya_curd"], [])
        assert client.get("/api/choices").json() == [
            dict(BREAKFAST, picks=["soya_curd"], leave_empty=[])
        ]

    def test_saving_nothing_forgets_the_meal(self, client):
        _sign_up(client)
        _put(client, ["onion_tomato_uttapam"], [])
        assert _put(client, [], []).status_code == 200
        assert client.get("/api/choices").json() == []

    def test_each_meal_is_kept_separately(self, client):
        _sign_up(client)
        _put(client, ["onion_tomato_uttapam"], [])
        _put(client, ["paneer_masala"], [], meal={"region": "north_indian", "meal_slot": "lunch"})
        meals = {(c["region"], c["meal_slot"]) for c in client.get("/api/choices").json()}
        assert meals == {("south_indian", "breakfast"), ("north_indian", "lunch")}

    def test_one_users_choices_are_not_anothers(self, client):
        _sign_up(client, "a@test.com")
        _put(client, ["onion_tomato_uttapam"], [])
        client.post("/api/auth/logout")
        _sign_up(client, "b@test.com")
        assert client.get("/api/choices").json() == []

    def test_another_user_saving_the_same_meal_leaves_mine_alone(self, client):
        _sign_up(client, "a@test.com")
        _put(client, ["onion_tomato_uttapam"], [])
        client.post("/api/auth/logout")
        _sign_up(client, "b@test.com")
        _put(client, ["soya_curd"], [])
        client.post("/api/auth/logout")
        client.post("/api/auth/login", json={"email": "a@test.com", "password": "password123"})
        assert client.get("/api/choices").json()[0]["picks"] == ["onion_tomato_uttapam"]


class TestWhatCanBeSaved:
    def test_a_dish_this_meal_cannot_hold_is_refused(self, client):
        _sign_up(client)
        # Precondition: it is a real dish, just not a breakfast one.
        assert _put(client, ["paneer_masala"], [], meal={"region": "north_indian", "meal_slot": "lunch"}).status_code == 200
        assert _put(client, ["paneer_masala"], []).status_code == 422

    def test_an_unknown_dish_is_refused(self, client):
        _sign_up(client)
        assert _put(client, ["no_such_dish"], []).status_code == 422

    def test_a_required_course_cannot_be_saved_as_removed(self, client):
        _sign_up(client)
        assert _put(client, [], ["egg_side"]).status_code == 200  # precondition
        assert _put(client, [], ["tiffin_item"]).status_code == 422

    def test_both_lists_are_required(self, client):
        # A client that forgets one must not save "nothing" by accident.
        _sign_up(client)
        _put(client, ["onion_tomato_uttapam"], [])
        res = client.put("/api/choices", json=dict(BREAKFAST, picks=["soya_curd"]))
        assert res.status_code == 422
        assert client.get("/api/choices").json()[0]["picks"] == ["onion_tomato_uttapam"]

    def test_a_meal_with_no_plate_is_refused_not_a_crash(self, client):
        _sign_up(client)
        res = _put(client, [], [], meal={"region": "pan_indian", "meal_slot": "lunch"})
        assert res.status_code == 422

    def test_signed_out_is_refused(self, client):
        assert client.get("/api/choices").status_code == 401
        assert _put(client, ["onion_tomato_uttapam"], []).status_code == 401
