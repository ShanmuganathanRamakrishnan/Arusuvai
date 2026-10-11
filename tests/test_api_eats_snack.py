"""The snack setting on the wire and in storage (TASKS_3.md N30).

Owner decision 2026-10-11 (docs/audit_log.md "N30"): a snack is the user's
choice. ``eats_snack`` is required on every profile body (web/CLAUDE.md: a
new wire field is required, not defaulted), stored with the profile, and a
snack plate is refused for a profile that eats none. The planner side --
the three meals taking the snack's share -- is tested in
``tests/test_nutrition_meal_target.py`` and ``tests/test_snack_coverage.py``.
"""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.db import Base, get_db, make_sessionmaker
from api.main import app
from tests.test_api_auth import PROFILE
from tests.test_api_picks import BODY


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


def test_a_profile_without_the_setting_is_rejected(client):
    body = {k: v for k, v in PROFILE.items() if k != "eats_snack"}
    assert client.post("/api/targets", json=body).status_code == 422


def test_the_setting_is_stored_and_read_back(client):
    client.post("/api/auth/signup", json={"email": "s@test.com", "password": "password123"})
    put = client.put("/api/profile", json=dict(PROFILE, eats_snack=False))
    assert put.status_code == 200
    assert put.json()["eats_snack"] is False
    assert client.get("/api/profile").json()["eats_snack"] is False

    client.put("/api/profile", json=dict(PROFILE, eats_snack=True))
    assert client.get("/api/profile").json()["eats_snack"] is True


def test_a_snack_plate_is_refused_for_a_profile_without_one(client):
    r = client.post("/api/plan", json=dict(BODY, meal_slot="snack", eats_snack=False))
    assert r.status_code == 422
    assert "no snack" in r.json()["detail"]
    # The same body with a snack in its day gets a plate.
    assert client.post("/api/plan", json=dict(BODY, meal_slot="snack", eats_snack=True)).status_code == 200


def test_a_meal_for_a_profile_without_a_snack_is_planned(client):
    r = client.post("/api/plan", json=dict(BODY, meal_slot="lunch", eats_snack=False))
    assert r.status_code == 200


def test_an_older_database_gains_the_column_with_every_profile_keeping_its_snack(tmp_path):
    # A profiles table as it was before N30: no eats_snack column, one row.
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR(320), "
        "hashed_password VARCHAR(255), created_at DATETIME)"
    )
    con.execute(
        "CREATE TABLE profiles (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE NOT NULL, "
        "weight_kg FLOAT NOT NULL, height_cm FLOAT NOT NULL, age_years INTEGER NOT NULL, "
        "sex VARCHAR(16) NOT NULL, activity VARCHAR(32) NOT NULL, goal VARCHAR(32) NOT NULL, "
        "diet VARCHAR(32) NOT NULL, clinical_flags TEXT NOT NULL, "
        "created_at DATETIME, updated_at DATETIME)"
    )
    con.execute(
        "INSERT INTO profiles (user_id, weight_kg, height_cm, age_years, sex, activity, "
        "goal, diet, clinical_flags) VALUES (1, 70, 175, 28, 'male', 'moderate', "
        "'maintain', 'vegetarian', '')"
    )
    con.commit()
    con.close()

    _, engine = make_sessionmaker(f"sqlite:///{path}")
    engine.dispose()

    con = sqlite3.connect(path)
    assert "eats_snack" in [r[1] for r in con.execute("PRAGMA table_info(profiles)")]
    assert con.execute("SELECT eats_snack FROM profiles").fetchall() == [(1,)]
    con.close()
