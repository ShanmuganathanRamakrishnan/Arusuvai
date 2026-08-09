"""The decline screen's copy map, across every token it can be handed.

``tests/test_web_no_identifiers.py`` proves the decline view is clean for the
one plate the real library actually declines on — sodium, above ceiling, locked
by a disclosed condition. That is one of ten entries in ``MACRO_COPY`` and one
of three ``kind`` values. The other nine entries and two kinds were written
against the schema and, without this file, would be believed rather than
checked; the first macro to reach a user through an unmapped branch would be a
raw ``protein_g`` on their screen.

So this drives the real ``renderPlanDecline`` in a real browser, with
``POST /api/plan`` stubbed to return violations the current recipe library
cannot produce. Everything else on the page is real: the same page, the same
function, the same DOM.

Prerequisites are the dev-only ones the other web suites use — a static server
and the API — and since D8 a skip here is announced and, under
``FOODAI_WEB_TESTS=required``, a failure.
"""

from __future__ import annotations

import json
import socket

import pytest

from tests.test_web_no_identifiers import IDENTIFIER, WEB_ORIGIN, _leaks

pytestmark = pytest.mark.web

API_ORIGIN = "http://localhost:8000"

#: One violation per branch the copy map has. Deliberately includes macros the
#: real library never blocks on, both ``kind`` values, all three
#: ``bound_source`` values, and every ``relaxability`` note.
STUB_VIOLATIONS = [
    {"macro": "energy_kcal", "kind": "below_floor", "bound_source": "meal_share",
     "reach": "jointly_infeasible", "relaxability": "relaxed_to_limit",
     "blocking_slots": [], "locked_by": [], "actual": 612.4, "bound": 854.9,
     "text": "energy_kcal is 612.4kcal, below its floor of 854.9kcal"},
    {"macro": "protein_g", "kind": "below_floor", "bound_source": "meal_share",
     "reach": "unreachable", "relaxability": "relaxable",
     "blocking_slots": [], "locked_by": [], "actual": 21.5, "bound": 39.2,
     "text": "protein_g is 21.5g, below its floor of 39.2g"},
    {"macro": "fat_g", "kind": "above_ceiling", "bound_source": "meal_share",
     "reach": "plate_miss", "relaxability": "hard_capped",
     "blocking_slots": [], "locked_by": [], "actual": 41.0, "bound": 33.8,
     "text": "fat_g is 41.0g, above its ceiling of 33.8g"},
    {"macro": "carb_g", "kind": "above_ceiling", "bound_source": "day_remaining",
     "reach": "plate_miss", "relaxability": "locked",
     "blocking_slots": [], "locked_by": ["diabetes"], "actual": 180.2,
     "bound": 142.5, "text": "carb_g is 180.2g, above its ceiling of 142.5g"},
    {"macro": "fibre_g", "kind": "below_floor", "bound_source": "meal_share",
     "reach": "plate_miss", "relaxability": "never_relaxed",
     "blocking_slots": [], "locked_by": [], "actual": 4.1, "bound": 9.8,
     "text": "fibre_g is 4.1g, below its floor of 9.8g"},
    {"macro": "sodium_mg", "kind": "above_ceiling", "bound_source": "absurdity_guard",
     "reach": "jointly_infeasible", "relaxability": "locked",
     "blocking_slots": [], "locked_by": ["hypertension"], "actual": 1546.0,
     "bound": 1400.0, "text": "sodium_mg is 1546.0mg, above its ceiling"},
    {"macro": "quality_protein_g", "kind": "below_floor", "bound_source": "meal_share",
     "reach": "unreachable", "relaxability": "never_relaxed",
     "blocking_slots": [], "locked_by": [], "actual": 8.99, "bound": 11.2,
     "text": "quality_protein_g is 8.99g, below its floor of 11.2g"},
    {"macro": "iron_mg", "kind": "below_floor", "bound_source": "meal_share",
     "reach": "plate_miss", "relaxability": "relaxable",
     "blocking_slots": [], "locked_by": [], "actual": 2.0, "bound": 4.5,
     "text": "iron_mg is 2.0mg, below its floor of 4.5mg"},
    {"macro": "calcium_mg", "kind": "below_floor", "bound_source": "meal_share",
     "reach": "plate_miss", "relaxability": "relaxable",
     "blocking_slots": [], "locked_by": [], "actual": 210.0, "bound": 333.0,
     "text": "calcium_mg is 210.0mg, below its floor of 333.0mg"},
    {"macro": "b12_ug", "kind": "below_floor", "bound_source": "meal_share",
     "reach": "plate_miss", "relaxability": "relaxable",
     "blocking_slots": [], "locked_by": [], "actual": 0.4, "bound": 0.8,
     "text": "b12_ug is 0.4ug, below its floor of 0.8ug"},
    {"macro": "", "kind": "no_candidates", "bound_source": "meal_share",
     "reach": "empty_pool", "relaxability": "never_relaxed",
     "blocking_slots": ["curd_course", "poriyal"], "locked_by": [],
     "actual": 0.0, "bound": 0.0, "text": "no candidates"},
]

#: A macro that is not in the client's map at all. The map covers every key
#: `core` can send today, so this is the case where `core` adds one and the web
#: layer has not caught up — the branch that must degrade to vague-but-true
#: rather than to a raw key.
UNMAPPED_VIOLATION = {
    "macro": "potassium_mg", "kind": "above_ceiling", "bound_source": "meal_share",
    "reach": "plate_miss", "relaxability": "relaxable", "blocking_slots": [],
    "locked_by": [], "actual": 3000.0, "bound": 2000.0,
    "text": "potassium_mg is 3000.0mg, above its ceiling of 2000.0mg",
}


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _render_decline(playwright, violations):
    """Render the real decline view against a stubbed `POST /api/plan`."""
    payload = {
        "passed": False,
        "dev_mode": True,
        "disclosure": "server prose containing sodium_mg, deliberately unused",
        "relaxation_applied": ["sodium_max_fibre_min"],
        "violations": [v["text"] for v in violations],
        "violation_detail": violations,
        "components": [],
        "estimate": None,
    }
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.evaluate(
            """async ([email, password]) => {
              const j = {'Content-Type': 'application/json'};
              let r = await fetch('http://localhost:8000/api/auth/signup', {method: 'POST',
                credentials: 'include', headers: j, body: JSON.stringify({email, password})});
              if (!r.ok) await fetch('http://localhost:8000/api/auth/login', {method: 'POST',
                credentials: 'include', headers: j, body: JSON.stringify({email, password})});
              await fetch('http://localhost:8000/api/profile', {method: 'PUT',
                credentials: 'include', headers: j, body: JSON.stringify({
                  age_years: 31, sex: 'male', weight_kg: 74, height_cm: 176,
                  activity: 'moderate', goal: 'maintain', diet: 'vegetarian',
                  clinical_flags: ['chronic_kidney_disease']})});
            }""",
            ["decline-copy@example.com", "decline-pw-31882"],
        )
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.wait_for_timeout(1200)

        # Only /api/plan is stubbed; auth, profile and science still hit the
        # real API, so the page reaches renderPlanDecline the way it always does.
        page.route(
            "**/api/plan",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(payload),
            ),
        )
        page.click("#dashGenerate")
        page.wait_for_timeout(1800)
        out = {
            "violations": page.inner_text("#obDeclineViolations"),
            "disclosure": page.inner_text("#obDeclineDisclosure"),
        }
        browser.close()
    return out


@pytest.fixture(scope="module")
def every_branch():
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN} (python -m http.server 3000 --directory web)")
    if not _listening("localhost", 8000):
        pytest.skip(f"no API on {API_ORIGIN}; the dashboard needs a session")
    return _render_decline(playwright, STUB_VIOLATIONS)


@pytest.fixture(scope="module")
def unmapped(every_branch):  # depends on the above so the skips are shared
    playwright = pytest.importorskip("playwright.sync_api")
    return _render_decline(playwright, [UNMAPPED_VIOLATION])


class TestNoTokenSurvivesAnyBranch:
    def test_not_one_identifier_reaches_the_violation_list(self, every_branch):
        leaks = _leaks(every_branch["violations"].splitlines())
        assert not leaks, f"the decline copy map leaked: {leaks[:8]}"

    def test_not_one_identifier_reaches_the_disclosure(self, every_branch):
        leaks = _leaks(every_branch["disclosure"].splitlines())
        assert not leaks, f"the decline disclosure leaked: {leaks[:8]}"

    def test_an_unmapped_macro_degrades_to_prose_not_to_its_key(self, unmapped):
        blob = unmapped["violations"]
        assert not IDENTIFIER.findall(blob), (
            "a macro the client has no copy for rendered its key; the fallback "
            f"must be vague and clean, not raw. Got: {blob!r}"
        )
        assert "nutritional limits couldn't be met" in blob


class TestEveryMacroIsNamedInWords:
    @pytest.mark.parametrize(
        "name",
        ["Calories", "Protein", "Fat", "Carbohydrate", "Fibre", "Sodium",
         "Iron", "Calcium", "Vitamin B12", "High-quality protein"],
    )
    def test_the_macro_appears_by_its_display_name(self, every_branch, name):
        assert name in every_branch["violations"]


class TestTheSentencesSayTheRightThing:
    def test_a_floor_reads_as_a_shortfall_and_a_ceiling_as_an_excess(self, every_branch):
        blob = every_branch["violations"]
        # 612.4 -> "612" at 0 digits, against the 854.9 -> "855" floor.
        assert "Calories reaches only 612 kcal, short of the 855 kcal" in blob
        assert "Fat comes to 41.0g, over the 33.8g limit" in blob

    def test_a_locked_bound_names_the_condition_and_says_we_chose_not_to(
        self, every_branch
    ):
        blob = every_branch["violations"]
        assert "We didn't loosen this one, because you told us about diabetes." in blob
        assert (
            "We didn't loosen this one, because you told us about hypertension."
            in blob
        )

    def test_the_bound_source_is_explained_when_it_is_not_the_ordinary_one(
        self, every_branch
    ):
        blob = every_branch["violations"]
        assert "more than one plate should take of a whole day's allowance" in blob
        assert "what's left of your day's allowance after your other meals" in blob

    def test_an_unfillable_plate_names_the_courses_in_words(self, every_branch):
        blob = every_branch["violations"]
        assert "a curd course and a vegetable side" in blob

    def test_the_disclosure_leads_with_the_clinical_refusal_when_one_holds(
        self, every_branch
    ):
        # Two violations are locked, so this is the sentence that must win over
        # the "reachable individually" wording.
        blob = every_branch["disclosure"]
        assert "We stopped rather than relax a limit tied to a condition" in blob
        assert "not a substitute for clinical nutrition guidance" in blob
