"""The snack question in onboarding and on the dashboard (TASKS_3.md N30).

Owner decision 2026-10-11 (docs/audit_log.md "N30"): a snack is the user's
choice. Onboarding asks "A snack in your day?" (default yes) and sends the
answer as ``eats_snack``; a returning user sees their saved answer. A
profile with no snack gets no snack plates on the dashboard, a "No snack"
tag, and every plan request carries ``eats_snack: false``.

Requests are read from a ``page.on("request")`` log, never a nested request
wait (tests/test_web_no_nested_waits.py).
"""

from __future__ import annotations

import socket

import pytest

from tests.test_web_no_identifiers import WEB_ORIGIN

pytestmark = pytest.mark.web

API_ORIGIN = "http://localhost:8000"
SIGN_IN = """async ([email, password, eats_snack]) => {
  const j = {'Content-Type': 'application/json'};
  let r = await fetch('http://localhost:8000/api/auth/signup', {method: 'POST',
    credentials: 'include', headers: j, body: JSON.stringify({email, password})});
  if (!r.ok) await fetch('http://localhost:8000/api/auth/login', {method: 'POST',
    credentials: 'include', headers: j, body: JSON.stringify({email, password})});
  await fetch('http://localhost:8000/api/profile', {method: 'PUT',
    credentials: 'include', headers: j, body: JSON.stringify({
      age_years: 28, sex: 'male', weight_kg: 70, height_cm: 175,
      activity: 'moderate', goal: 'maintain', diet: 'eggetarian',
      clinical_flags: [], eats_snack})});
}"""
PLATES = """() => [...document.querySelectorAll('input[name="plate"]')].map(el => ({
  value: el.value, visible: el.closest('label').offsetParent !== null,
  disabled: el.disabled, checked: el.checked}))"""
TAGS = "() => [...document.querySelectorAll('#dashProfileTags .tag')].map(e => e.innerText)"
SNACK_ANSWER = "() => document.querySelector('input[name=\"eats_snack\"]:checked').value"


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _dashboard(page, seen, key):
    page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
    page.wait_for_selector("#dashGenerate")
    seen[f"{key}_plates"] = page.evaluate(PLATES)
    seen[f"{key}_tags"] = page.evaluate(TAGS)
    seen[f"{key}_picker_note"] = page.inner_text("#dashPickerNote")
    page.click('input[name="plate"][value="north_indian:lunch"]')
    with page.expect_response(
        lambda r: "/api/plan" in r.url and r.request.method == "POST", timeout=30000
    ) as resp:
        page.click("#dashGenerate")
    seen[f"{key}_plan_status"] = resp.value.status


@pytest.fixture(scope="module")
def walk():
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN} (python -m http.server 3000 --directory web)")
    if not _listening("localhost", 8000):
        pytest.skip(f"no API on {API_ORIGIN}; the dashboard needs a session")

    seen = {"plan_bodies": [], "targets_bodies": []}
    account = ["no-snack@example.com", "no-snack-pw-61842"]
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()

        # A new visitor: the question defaults to yes.
        fresh = browser.new_page(viewport={"width": 1600, "height": 950})
        fresh.goto(f"{WEB_ORIGIN}/onboarding.html", wait_until="networkidle")
        seen["fresh_answer"] = fresh.evaluate(SNACK_ANSWER)
        fresh.close()

        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.on(
            "request",
            lambda r: (
                seen["plan_bodies"].append(r.post_data_json) if "/api/plan" in r.url
                else seen["targets_bodies"].append(r.post_data_json) if "/api/targets" in r.url
                else None
            ) if r.method == "POST" else None,
        )
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")

        page.evaluate(SIGN_IN, [*account, False])
        _dashboard(page, seen, "without")
        # A returning user: onboarding prefills the saved answer and sends it.
        # Prefill runs before the targets request, so waiting on its response
        # means the radio shows the saved answer, not the default.
        with page.expect_response("**/api/targets", timeout=30000):
            page.goto(f"{WEB_ORIGIN}/onboarding.html")
        seen["returning_answer"] = page.evaluate(SNACK_ANSWER)

        page.evaluate(SIGN_IN, [*account, True])
        _dashboard(page, seen, "with")
        browser.close()
    return seen


def test_a_new_visitor_is_asked_with_yes_preselected(walk):
    assert walk["fresh_answer"] == "yes"


def test_a_profile_without_a_snack_gets_no_snack_plates(walk):
    snack = [p for p in walk["without_plates"] if p["value"].endswith(":snack")]
    assert [p["value"] for p in snack] == ["south_indian:snack", "north_indian:snack"]
    assert all(not p["visible"] and p["disabled"] and not p["checked"] for p in snack)
    meals = [p for p in walk["without_plates"] if not p["value"].endswith(":snack")]
    assert len(meals) == 6 and all(p["visible"] and not p["disabled"] for p in meals)
    assert sum(p["checked"] for p in walk["without_plates"]) == 1


def test_a_profile_with_a_snack_keeps_its_snack_plates(walk):
    snack = [p for p in walk["with_plates"] if p["value"].endswith(":snack")]
    assert len(snack) == 2 and all(p["visible"] and not p["disabled"] for p in snack)


def test_the_page_says_no_snack(walk):
    assert "No snack" in walk["without_tags"]
    assert "No snack" not in walk["with_tags"]


def test_every_plan_request_carries_the_answer(walk):
    assert [b["eats_snack"] for b in walk["plan_bodies"]] == [False, True]
    assert walk["without_plan_status"] == 200 and walk["with_plan_status"] == 200


def test_a_returning_user_sees_and_sends_their_saved_answer(walk):
    assert walk["returning_answer"] == "no"
    assert walk["targets_bodies"] and all(b["eats_snack"] is False for b in walk["targets_bodies"])


def test_the_picker_does_not_count_plates_it_may_not_show(walk):
    # "These eight" sat above six plates for a profile with no snack, found
    # in the N30 screenshots (docs/audit_log.md "N30c").
    for key in ("without", "with"):
        assert "eight" not in walk[f"{key}_picker_note"].lower()
