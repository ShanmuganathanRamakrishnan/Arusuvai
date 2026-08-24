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


class TestPlanProvenanceReachesTheClient:
    """`docs/audit_log.md` finding 37.

    `docs/methodology.md` has required since Phase 2 that any rendered plan
    produced in ``dev_mode`` carry that label in the artifact itself. `demo.py`
    complied from the start; nothing on the web could, because `PlanOut` did
    not carry the fact and `PlanEstimateOut` dropped the unverified figure
    `core/` had already computed. These assert the payload a client needs, not
    the copy a client writes -- the sentence is pinned by
    `tests/test_web_no_identifiers.py`, which is what caught the first draft of
    it rendering the raw token.
    """

    def _plan(self):
        return client.post(
            "/api/plan",
            json=_body(diet="vegetarian", region="north_indian", meal_slot="lunch"),
        ).json()

    def test_a_solved_plate_says_it_is_not_validated(self):
        data = self._plan()
        # The precondition. If this plate ever stops passing, the assertion
        # below would hold vacuously on a decline, so it is checked explicitly.
        assert data["passed"] is True, data["disclosure"]
        assert data["dev_mode"] is True

    def test_the_unverified_figure_is_carried_not_dropped(self):
        # Every ingredient row but `water` is unverified and `water` has no
        # energy, so the whole plate is charged -- see docs/audit_log.md
        # finding 20 (D6). Pinned as an identity against the plate's own
        # energy rather than as the literal 931.2, which moves with the recipe
        # library; the point is that the API does not silently report a
        # smaller, nicer number than core/ computed.
        est = self._plan()["estimate"]
        assert est["unverified_energy_kcal"] == pytest.approx(est["energy_kcal"])
        assert est["unverified_energy_fraction"] == pytest.approx(1.0)


class TestADeclineCarriesItsNumbersNotJustItsProse:
    """`docs/audit_log.md` finding 31, the server half.

    `ViolationOut` has always carried stable tokens so a client could write its
    own copy, but not ``actual`` and ``bound`` -- the two numbers any such
    sentence needs. A client had to either render `text`, which interpolates the
    raw macro key, or parse the numbers back out of it, which would make English
    prose an API contract. Both numbers exist on
    `core.planner.validator.Violation` and are passed through here; nothing in
    this package computes them.

    The copy built on top of this is graded by `tests/test_web_decline_copy.py`.
    """

    def _decline(self):
        # Repointed 2026-08-24 (follow-up to finding 51): the previous
        # profile (weight_kg=74, goal=maintain) stopped declining once
        # soya_curd (data/recipes/soya_curd.yaml) gave south_lunch's
        # curd_course a lower-sodium option, freeing enough sodium headroom
        # to pass with only mild relaxation. This profile (weight_kg=55,
        # goal=lose_fat) still declines: its protein floor is locked by
        # chronic_kidney_disease's clinical flag (per-kg protein requirement
        # scales with weight; lose_fat's lower energy budget cannot supply
        # 55 kg's locked floor from this template's candidates), and a locked
        # floor is never relaxed regardless of what fills curd_course.
        # Confirmed directly: actual 29.6 g vs bound 34.6 g, kind
        # below_floor, locked_by chronic_kidney_disease.
        return client.post(
            "/api/plan",
            json=_body(
                weight_kg=55, height_cm=176, age_years=31, goal="lose_fat",
                diet="vegetarian",
                clinical_flags=["chronic_kidney_disease"],
                region="south_indian", meal_slot="lunch",
            ),
        ).json()

    def test_this_profile_still_declines(self):
        # If the library grows so that it passes, the two tests below stop
        # testing anything and must be repointed rather than deleted.
        assert self._decline()["passed"] is False

    def test_every_violation_carries_the_two_numbers_its_sentence_needs(self):
        details = self._decline()["violation_detail"]
        assert details, "a decline with no structured violations explains nothing"
        for v in details:
            assert "actual" in v and "bound" in v
            assert isinstance(v["actual"], float) and isinstance(v["bound"], float)

    def test_the_numbers_match_the_prose_the_planner_wrote(self):
        # Same source, so they must agree: the prose is what `describe` built
        # from these very fields. A mismatch would mean the API is reporting one
        # violation's numbers against another's text.
        #
        # The `!= 0.0` guards are the point of this test, not decoration. Its
        # first draft asserted only that the formatted number appeared in the
        # text, and passed against a build where the pass-through had been
        # deleted: the fields defaulted to 0.0, and "0.0" is a substring of
        # "1400.0". A test that green-lights the defect it names is not a test.
        for v in self._decline()["violation_detail"]:
            if v["kind"] == "no_candidates":
                continue
            assert v["actual"] != 0.0, "a real bound miss is not 0.0 against 0.0"
            assert v["bound"] != 0.0
            assert f"{v['actual']:.1f}" in v["text"]
            assert f"{v['bound']:.1f}" in v["text"]
