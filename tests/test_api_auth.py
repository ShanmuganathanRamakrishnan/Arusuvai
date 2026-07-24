"""Accounts + profile persistence — Tier B auth (session cookie, SQLite, bcrypt).

Every test runs against an isolated in-memory database (``make_sessionmaker``
with ``sqlite:///:memory:`` and ``StaticPool``, see ``api/db.py``), overriding
``app.dependency_overrides[get_db]`` per test so no test can see another
test's users, and the real ``data/app.db`` is never touched by the suite.
``TestClient`` keeps a cookiejar across requests made on the same instance,
so "log in, then call an authenticated endpoint" exercises the real signed
session cookie end to end, not a mocked identity.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.db import Base, get_db, make_sessionmaker
from api.main import app

PROFILE = {
    "weight_kg": 68.0,
    "height_cm": 170.0,
    "age_years": 30,
    "sex": "male",
    "activity": "moderate",
    "goal": "maintain",
    "diet": "vegetarian",
    "clinical_flags": ["hypertension"],
}


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


class TestPasswordHashing:
    def test_a_real_bcrypt_hash_is_stored_not_the_plaintext_or_a_homemade_scheme(self, client):
        # Inspect the row bcrypt actually wrote, through the same overridden
        # session the endpoint used -- not a mocked hasher.
        from api.db import User

        client.post("/api/auth/signup", json={"email": "hash@test.com", "password": "password123"})

        # Reach the session factory the fixture installed via a fresh call to
        # the override generator, since the endpoint's own session is closed
        # by the time this assertion runs.
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        try:
            user = db.query(User).filter(User.email == "hash@test.com").one()
            assert user.hashed_password != "password123"
            # bcrypt's own format: "$2b$<cost>$<22-char-salt><31-char-hash>".
            assert user.hashed_password.startswith("$2b$")
            assert len(user.hashed_password) == 60

            import bcrypt

            assert bcrypt.checkpw(b"password123", user.hashed_password.encode("utf-8"))
        finally:
            db_gen.close()


class TestSignupLoginLogout:
    def test_signup_creates_an_account_and_signs_it_in(self, client):
        r = client.post("/api/auth/signup", json={"email": "a@test.com", "password": "password123"})
        assert r.status_code == 201
        body = r.json()
        assert body["user"]["email"] == "a@test.com"
        assert body["profile"] is None

        r = client.get("/api/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == "a@test.com"

    def test_signing_up_twice_with_the_same_email_is_rejected(self, client):
        client.post("/api/auth/signup", json={"email": "dup@test.com", "password": "password123"})
        r = client.post("/api/auth/signup", json={"email": "dup@test.com", "password": "password123"})
        assert r.status_code == 409

    def test_a_short_password_is_rejected_at_the_boundary(self, client):
        r = client.post("/api/auth/signup", json={"email": "short@test.com", "password": "abc"})
        assert r.status_code == 422

    def test_logout_ends_the_session(self, client):
        client.post("/api/auth/signup", json={"email": "b@test.com", "password": "password123"})
        assert client.get("/api/auth/me").status_code == 200

        r = client.post("/api/auth/logout")
        assert r.status_code == 200
        assert client.get("/api/auth/me").status_code == 401

    def test_login_with_wrong_password_is_401_and_does_not_leak_which_field_was_wrong(self, client):
        client.post("/api/auth/signup", json={"email": "c@test.com", "password": "password123"})
        client.post("/api/auth/logout")

        wrong_password = client.post("/api/auth/login", json={"email": "c@test.com", "password": "nope12345"})
        wrong_email = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "password123"})
        assert wrong_password.status_code == 401
        assert wrong_email.status_code == 401
        assert wrong_password.json()["detail"] == wrong_email.json()["detail"]

    def test_login_after_logout_restores_the_session(self, client):
        client.post("/api/auth/signup", json={"email": "d@test.com", "password": "password123"})
        client.post("/api/auth/logout")
        r = client.post("/api/auth/login", json={"email": "d@test.com", "password": "password123"})
        assert r.status_code == 200
        assert client.get("/api/auth/me").status_code == 200


class TestProfilePersistence:
    """The core acceptance claim: a profile survives logout/login, tied to user_id."""

    def test_profile_is_rejected_without_a_session(self, client):
        assert client.get("/api/profile").status_code == 401
        assert client.put("/api/profile", json=PROFILE).status_code == 401

    def test_no_profile_saved_yet_is_a_404_not_an_empty_object(self, client):
        client.post("/api/auth/signup", json={"email": "e@test.com", "password": "password123"})
        r = client.get("/api/profile")
        assert r.status_code == 404

    def test_signup_with_a_profile_persists_it_immediately(self, client):
        r = client.post(
            "/api/auth/signup",
            json={"email": "f@test.com", "password": "password123", "profile": PROFILE},
        )
        assert r.status_code == 201
        assert r.json()["profile"]["weight_kg"] == 68.0
        assert r.json()["profile"]["clinical_flags"] == ["hypertension"]

        r = client.get("/api/profile")
        assert r.status_code == 200
        assert r.json()["diet"] == "vegetarian"

    def test_saved_profile_survives_logout_and_login(self, client):
        # The literal acceptance scenario: sign up, save a profile, log out,
        # log back in, confirm the profile is still there.
        client.post(
            "/api/auth/signup",
            json={"email": "g@test.com", "password": "password123", "profile": PROFILE},
        )
        client.post("/api/auth/logout")
        assert client.get("/api/profile").status_code == 401  # gone with the session, not the data

        login = client.post("/api/auth/login", json={"email": "g@test.com", "password": "password123"})
        assert login.json()["profile"]["weight_kg"] == 68.0

        r = client.get("/api/profile")
        assert r.status_code == 200
        assert r.json() == login.json()["profile"]

    def test_put_profile_upserts_replacing_the_prior_value(self, client):
        client.post("/api/auth/signup", json={"email": "h@test.com", "password": "password123"})
        first = client.put("/api/profile", json=PROFILE)
        assert first.status_code == 200
        assert first.json()["weight_kg"] == 68.0

        changed = dict(PROFILE, weight_kg=75.0, clinical_flags=[])
        second = client.put("/api/profile", json=changed)
        assert second.status_code == 200
        assert second.json()["weight_kg"] == 75.0
        assert second.json()["clinical_flags"] == []

        # One row, not two: re-fetching shows the replacement, not the original.
        r = client.get("/api/profile")
        assert r.json()["weight_kg"] == 75.0

    def test_impossible_profile_input_is_422_and_not_persisted(self, client):
        client.post("/api/auth/signup", json={"email": "i@test.com", "password": "password123"})
        bad = dict(PROFILE, weight_kg=-5.0)
        r = client.put("/api/profile", json=bad)
        assert r.status_code == 422
        assert client.get("/api/profile").status_code == 404

    def test_two_users_profiles_do_not_collide(self, client):
        client.post(
            "/api/auth/signup",
            json={"email": "user1@test.com", "password": "password123", "profile": PROFILE},
        )
        client.post("/api/auth/logout")

        other_profile = dict(PROFILE, weight_kg=55.0, diet="vegan", clinical_flags=[])
        client.post(
            "/api/auth/signup",
            json={"email": "user2@test.com", "password": "password123", "profile": other_profile},
        )
        r = client.get("/api/profile")
        assert r.json()["weight_kg"] == 55.0
        assert r.json()["diet"] == "vegan"

        client.post("/api/auth/logout")
        client.post("/api/auth/login", json={"email": "user1@test.com", "password": "password123"})
        r = client.get("/api/profile")
        assert r.json()["weight_kg"] == 68.0
        assert r.json()["diet"] == "vegetarian"


class TestPlanEndpointUnaffected:
    """This increment must not touch the plan-call/decline logic at all."""

    def test_plan_endpoint_works_identically_with_no_session(self, client):
        # /api/plan takes a full profile in its own body, same as before this
        # increment -- it is not gated on auth and does not read StoredProfile.
        body = dict(PROFILE, region="south_indian", meal_slot="breakfast")
        r = client.post("/api/plan", json=body)
        assert r.status_code == 200
        assert "passed" in r.json()
