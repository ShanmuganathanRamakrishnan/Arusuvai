"""The HTTP boundary for target derivation.

These assert the API is a faithful, thin passthrough to
``core.nutrition.targets`` — the numbers must match ``derive_target`` exactly
(the API computes nothing of its own) — plus the boundary behaviours: enum
validation, impossible vs implausible input, and provenance.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.nutrition.targets import derive_target
from core.schemas import ActivityLevel, DietPattern, Goal, Profile, Sex

client = TestClient(app)


def _body(**overrides) -> dict:
    body = {
        "weight_kg": 70,
        "height_cm": 175,
        "age_years": 28,
        "sex": "male",
        "activity": "moderate",
        "goal": "maintain",
        "diet": "non_vegetarian",
    }
    body.update(overrides)
    return body


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_targets_matches_derive_target_exactly():
    # The API must not compute or round anything of its own: its energy and
    # protein must equal the core derivation for the same profile, to the float.
    r = client.post("/api/targets", json=_body())
    assert r.status_code == 200
    data = r.json()

    expected = derive_target(
        Profile(
            weight_kg=70,
            height_cm=175,
            age_years=28,
            sex=Sex.MALE,
            activity=ActivityLevel.MODERATE,
            goal=Goal.MAINTAIN,
            diet=DietPattern.NON_VEGETARIAN,
        )
    )
    assert data["energy"]["kcal"] == pytest.approx(expected.energy_kcal)
    assert data["protein"]["quality_adjusted_g"] == pytest.approx(
        expected.protein.quality_adjusted_g
    )
    assert data["bmr_kcal"] == pytest.approx(expected.bmr_kcal)


def test_status_is_dev_mode_with_a_disclosure():
    data = client.post("/api/targets", json=_body()).json()
    assert data["status"] == "dev_mode"
    assert "not validated" in data["disclosure"]


def test_diet_drives_the_protein_target_over_http():
    # Same body, vegan must require more grams than non-vegetarian.
    non_veg = client.post("/api/targets", json=_body(diet="non_vegetarian")).json()
    vegan = client.post("/api/targets", json=_body(diet="vegan")).json()
    assert (
        vegan["protein"]["quality_adjusted_g"]
        > non_veg["protein"]["quality_adjusted_g"]
    )


def test_energy_interval_is_present_and_brackets_the_point():
    e = client.post("/api/targets", json=_body()).json()["energy"]
    assert e["low"] < e["kcal"] < e["high"]
    assert e["uncertainty"] > 0


def test_provenance_lists_real_sources_all_unverified():
    sources = client.post("/api/targets", json=_body()).json()["sources"]
    keys = {s["key"] for s in sources}
    assert "bmr.mifflin.weight_coeff" in keys
    assert "diaas.non_vegetarian" in keys
    # Mifflin carries a real DOI; nothing is verified yet (honest dev_mode).
    mifflin = next(s for s in sources if s["key"] == "bmr.mifflin.weight_coeff")
    assert mifflin["doi"] == "10.1093/ajcn/51.2.241"
    assert all(s["verified"] is False for s in sources)


def test_implausible_weight_is_accepted_with_a_warning_not_rejected():
    # 300 kg is out of range but valid input: 200 OK, warning surfaced.
    r = client.post("/api/targets", json=_body(weight_kg=300))
    assert r.status_code == 200
    assert any("outside the usual adult range" in w for w in r.json()["warnings"])


def test_impossible_weight_is_a_422():
    # Non-positive weight is impossible input: Profile raises -> 422.
    r = client.post("/api/targets", json=_body(weight_kg=-5))
    assert r.status_code == 422


def test_unknown_enum_value_is_rejected_at_the_boundary():
    r = client.post("/api/targets", json=_body(diet="carnivore"))
    assert r.status_code == 422
