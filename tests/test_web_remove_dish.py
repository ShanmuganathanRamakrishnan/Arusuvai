"""The dashboard lets the user take one dish off the plate (TASKS_3.md N10).

A "Remove" sits on each dish whose course the server says can be empty
(``swap_options[].can_be_empty``), whether the planner chose the dish or the
user added it. Removing sends the course's slot name in ``leave_empty`` and
drops any pick in that course; putting a dish back ends the removal. The
server decides every count.

Measured 2026-09-30 (docs/audit_log.md, N10 entry), 70 kg eggetarian South
breakfast: the suggested plate carries a dish in ``egg_side``, the only course
on it that can be empty. A library change that moves this is a reason to
re-pick the example, not to doubt the mechanism.

One ``expect_response`` per wait, never nested with a request wait
(tests/test_web_no_nested_waits.py).
"""

from __future__ import annotations

import json
import socket

import pytest

from tests.test_web_no_identifiers import WEB_ORIGIN

pytestmark = pytest.mark.web

API_ORIGIN = "http://localhost:8000"
REMOVE = "#obPlanMeals .dash-dish-remove"
EGG_ADD = "#obPlanMeals select[aria-label='Add an egg side']"
DISHES_JS = "els => els.map(e => e.innerText)"


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _dishes(page):
    return page.eval_on_selector_all("#obPlanMeals .dash-dish-name", DISHES_JS)


def _removes(page):
    return page.eval_on_selector_all(REMOVE, "els => els.map(e => e.getAttribute('aria-label'))")


def _settled(page, resp):
    """The request the page sent and the plate it then drew."""

    data = resp.value.json()
    names = [c["recipe_name"] for c in data["components"]]
    page.wait_for_function(
        "names => JSON.stringify([...document.querySelectorAll("
        "'#obPlanMeals .dash-dish-name')].map(e => e.innerText)) === JSON.stringify(names)",
        arg=names,
        timeout=10000,
    )
    return resp.value.request.post_data_json, data


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

    seen = {}
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
                  age_years: 28, sex: 'male', weight_kg: 70, height_cm: 175,
                  activity: 'moderate', goal: 'maintain', diet: 'eggetarian',
                  clinical_flags: []})});
            }""",
            ["remove-dish@example.com", "remove-dish-pw-71344"],
        )
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.wait_for_selector("#dashGenerate")

        page.click('input[name="plate"][value="south_indian:breakfast"]')
        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click("#dashGenerate")
        seen["first_request"], seen["first"] = _settled(page, resp)
        seen["first_removes"] = _removes(page)
        seen["first_rows"] = page.eval_on_selector_all(
            "#obPlanMeals .dash-dish-row", "els => els.length"
        )
        egg = next(c for c in seen["first"]["components"] if c["slot"] == "egg_side")
        seen["egg_name"] = egg["recipe_name"]

        # A removal the server refuses: answered here, not by the API, because
        # the button is only offered where the API says a plate exists.
        def refuse(route):
            if route.request.method != "POST":
                return route.continue_()
            route.fulfill(
                status=200,
                content_type="application/json",
                headers={
                    "Access-Control-Allow-Origin": WEB_ORIGIN,
                    "Access-Control-Allow-Credentials": "true",
                },
                body=json.dumps({"passed": False}),
            )

        page.route("**/api/plan", refuse)
        with page.expect_response("**/api/plan", timeout=30000):
            page.click(f"{REMOVE}[aria-label='Remove {egg['recipe_name']}']")
        page.wait_for_function(
            "() => document.getElementById('obPlanSwapNote').innerText.trim() !== ''",
            timeout=10000,
        )
        page.unroute("**/api/plan")
        seen["refused_note"] = page.inner_text("#obPlanSwapNote")
        seen["refused_dishes"] = _dishes(page)
        seen["refused_reset_visible"] = page.is_visible("#dashResetPicks")
        seen["refused_decline_visible"] = page.is_visible("#obPlanDecline")

        # The planner's own dish, removed.
        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click(f"{REMOVE}[aria-label='Remove {egg['recipe_name']}']")
        seen["remove_request"], seen["removed"] = _settled(page, resp)
        seen["removed_dishes"] = _dishes(page)
        seen["removed_reset_visible"] = page.is_visible("#dashResetPicks")
        seen["removed_egg_menu"] = page.locator(EGG_ADD).count()

        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click("#dashResetPicks")
        seen["reset_request"], seen["reset"] = _settled(page, resp)
        seen["reset_visible_after_reset"] = page.is_visible("#dashResetPicks")

        # Remove it again, put a dish back in that course, then take that off too.
        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click(f"{REMOVE}[aria-label='Remove {egg['recipe_name']}']")
        _settled(page, resp)
        back = next(s for s in seen["removed"]["swap_options"] if s["slot"] == "egg_side")["options"][0]
        seen["back"] = back
        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.select_option(EGG_ADD, back["recipe_id"])
        seen["back_request"], seen["back_plan"] = _settled(page, resp)

        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click(f"{REMOVE}[aria-label='Remove {back['recipe_name']}']")
        seen["remove_added_request"], seen["remove_added"] = _settled(page, resp)

        # A fresh plan starts from the suggested plate: no removal carried over.
        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click("#dashGenerate")
        seen["generate_request"], _ = _settled(page, resp)
        browser.close()
    return seen


def test_remove_is_offered_only_where_the_server_says_the_course_can_be_empty(walk):
    can = {s["slot"] for s in walk["first"]["swap_options"] if s["can_be_empty"]}
    expected = [
        f"Remove {c['recipe_name']}" for c in walk["first"]["components"] if c["slot"] in can
    ]
    # Precondition: some dishes get one and some do not, or this cannot fail.
    assert 0 < len(expected) < len(walk["first"]["components"])
    assert walk["first_removes"] == expected


def test_a_remove_button_is_not_counted_as_a_dish(walk):
    assert walk["first_rows"] == len(walk["first"]["components"])


def test_removing_sends_the_course_and_shows_the_servers_plate(walk):
    assert walk["first_request"]["leave_empty"] == []
    assert walk["remove_request"]["leave_empty"] == ["egg_side"]
    assert walk["remove_request"]["picks"] == []
    assert walk["removed"]["passed"]
    assert "egg_side" not in {c["slot"] for c in walk["removed"]["components"]}
    assert walk["removed_dishes"] == [c["recipe_name"] for c in walk["removed"]["components"]]
    assert walk["egg_name"] not in walk["removed_dishes"]


def test_a_removal_can_be_undone(walk):
    assert walk["removed_reset_visible"]
    assert walk["removed_egg_menu"] == 1
    assert walk["reset_request"]["leave_empty"] == []
    assert walk["reset_request"]["picks"] == []
    assert walk["reset"]["components"] == walk["first"]["components"]
    assert not walk["reset_visible_after_reset"]


def test_putting_a_dish_back_ends_the_removal(walk):
    assert walk["back_request"]["leave_empty"] == []
    assert walk["back_request"]["picks"] == [walk["back"]["recipe_id"]]
    assert walk["back_plan"]["passed"]


def test_removing_an_added_dish_drops_its_pick_and_keeps_the_course_empty(walk):
    # The flow that failed 67 times in 155 when only the pick was dropped.
    assert walk["remove_added_request"]["picks"] == []
    assert walk["remove_added_request"]["leave_empty"] == ["egg_side"]
    assert "egg_side" not in {c["slot"] for c in walk["remove_added"]["components"]}


def test_a_refused_removal_keeps_the_plate_and_says_so_by_name(walk):
    assert walk["egg_name"] in walk["refused_note"]
    assert "couldn't be removed" in walk["refused_note"]
    assert walk["refused_dishes"] == [c["recipe_name"] for c in walk["first"]["components"]]
    assert not walk["refused_decline_visible"]
    # The removal was undone, not left pending: nothing to go back from, and
    # the next request (the real removal) sends exactly one course.
    assert not walk["refused_reset_visible"]


def test_a_fresh_plan_carries_no_removal_over(walk):
    assert walk["remove_added_request"]["leave_empty"] == ["egg_side"]  # precondition
    assert walk["generate_request"]["leave_empty"] == []
    assert walk["generate_request"]["picks"] == []
