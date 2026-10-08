"""The dashboard keeps a user's dish choices for a meal between visits (TASKS_3.md N11).

"Remember these choices" saves the plate's swaps and removals for its meal;
the next plan for that meal starts from them. A saved choice is asked of the
planner afresh every visit and never forced: when it no longer fits, the page
shows the suggested plate, says so, and keeps the choice. "Forget saved
choices" removes it. Measured why that path matters: 20% of saved choices
stop fitting after a profile edit (docs/audit_log.md 2026-10-02).

Real library, 70 kg eggetarian South breakfast, as test_web_remove_dish.py:
the suggested plate carries a dish in ``egg_side``, which can be removed.
``plain_dosa`` is a breakfast dish on no valid plate for this body
(tests/test_api_picks.py), so a saved pick of it never fits.

Requests are read from a ``page.on("request")`` log, never a nested request
wait (tests/test_web_no_nested_waits.py).
"""

from __future__ import annotations

import socket

import pytest

from tests.test_web_no_identifiers import WEB_ORIGIN

pytestmark = pytest.mark.web

API_ORIGIN = "http://localhost:8000"
PLAN = "**/api/plan"
CHOICES = "**/api/choices"
SIGN_IN = """async ([email, password, choices]) => {
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
  // The account outlives the run (data/app.db): start from a known state.
  await fetch('http://localhost:8000/api/choices', {method: 'PUT',
    credentials: 'include', headers: j, body: JSON.stringify(Object.assign(
      {region: 'south_indian', meal_slot: 'breakfast'}, choices))});
}"""


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _controls(page):
    return {
        "remember": page.is_visible("#dashRememberChoices"),
        "forget": page.is_visible("#dashForgetChoices"),
        "note": page.inner_text("#dashSavedNote"),
        "dishes": page.eval_on_selector_all(
            "#obPlanMeals .dash-dish-name", "els => els.map(e => e.innerText)"
        ),
    }


def _generate(page, final=lambda body: True):
    """Plan South breakfast; wait for the plan request ``final`` picks out."""

    page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
    page.wait_for_selector("#dashGenerate")
    page.click('input[name="plate"][value="south_indian:breakfast"]')
    with page.expect_response(
        lambda r: "/api/plan" in r.url and r.request.method == "POST"
        and final(r.request.post_data_json),
        timeout=30000,
    ) as resp:
        page.click("#dashGenerate")
    data = resp.value.json()
    _drawn(page, data)
    return data


def _drawn(page, data):
    names = [c["recipe_name"] for c in data["components"]]
    page.wait_for_function(
        "names => JSON.stringify([...document.querySelectorAll("
        "'#obPlanMeals .dash-dish-name')].map(e => e.innerText)) === JSON.stringify(names)",
        arg=names,
        timeout=10000,
    )
    page.wait_for_load_state("networkidle")


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
        sent = []
        page.on(
            "request",
            lambda r: sent.append(r.post_data_json)
            if "/api/plan" in r.url and r.method == "POST" else None,
        )
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.evaluate(SIGN_IN, ["saved-choices@example.com", "saved-choices-pw-40417",
                                {"picks": [], "leave_empty": []}])

        # Visit 1: the suggested plate, then remove the egg and remember that.
        seen["first"] = _generate(page)
        seen["first_controls"] = _controls(page)
        egg = next(c for c in seen["first"]["components"] if c["slot"] == "egg_side")
        seen["egg_name"] = egg["recipe_name"]
        with page.expect_response(PLAN, timeout=30000) as resp:
            page.click(f"#obPlanMeals .dash-dish-remove[aria-label='Remove {egg['recipe_name']}']")
        removed = resp.value.json()
        _drawn(page, removed)
        seen["removed_controls"] = _controls(page)
        # And a swap, so what is saved holds a dish as well as a removal.
        tiffin = next(c for c in removed["components"] if c["slot"] == "tiffin_item")
        with page.expect_response(PLAN, timeout=30000) as resp:
            page.select_option(
                f"#obPlanMeals select[aria-label='Swap {tiffin['recipe_name']} for another dish']",
                "onion_tomato_uttapam",
            )
        _drawn(page, resp.value.json())
        with page.expect_response(CHOICES, timeout=30000) as resp:
            page.click("#dashRememberChoices")
        seen["save_request"] = resp.value.request.post_data_json
        page.wait_for_function(
            "() => document.getElementById('dashSavedNote').innerText.startsWith('Saved')",
            timeout=10000,
        )
        seen["saved_controls"] = _controls(page)

        # Visit 2: a fresh page load starts from the saved choices.
        del sent[:]
        seen["second"] = _generate(page)
        seen["second_requests"] = list(sent)
        seen["second_controls"] = _controls(page)
        # Forget while the saved choices are on the plate, then keep them again.
        with page.expect_response(CHOICES, timeout=30000) as resp:
            page.click("#dashForgetChoices")
        seen["forget_on_plate_request"] = resp.value.request.post_data_json
        page.wait_for_function(
            "() => document.getElementById('dashSavedNote').innerText.startsWith('Forgotten')",
            timeout=10000,
        )
        seen["forgot_on_plate_controls"] = _controls(page)
        with page.expect_response(CHOICES, timeout=30000) as resp:
            page.click("#dashRememberChoices")
        page.wait_for_function(
            "() => document.getElementById('dashSavedNote').innerText.startsWith('Saved')",
            timeout=10000,
        )
        with page.expect_response(PLAN, timeout=30000) as resp:
            page.click("#dashResetPicks")
        _drawn(page, resp.value.json())
        seen["reset_controls"] = _controls(page)

        # Visit 3: a saved choice that no longer fits is not forced.
        page.evaluate(SIGN_IN, ["saved-choices@example.com", "saved-choices-pw-40417",
                                {"picks": ["plain_dosa"], "leave_empty": []}])
        del sent[:]
        seen["third"] = _generate(page, final=lambda body: body["picks"] == [])
        seen["third_requests"] = list(sent)
        page.wait_for_function(
            "() => document.getElementById('dashSavedNote').innerText !== ''", timeout=10000
        )
        seen["third_controls"] = _controls(page)
        with page.expect_response(CHOICES, timeout=30000) as resp:
            page.click("#dashForgetChoices")
        seen["forget_request"] = resp.value.request.post_data_json
        page.wait_for_function(
            "() => document.getElementById('dashSavedNote').innerText.startsWith('Forgotten')",
            timeout=10000,
        )
        seen["forgot_controls"] = _controls(page)

        # Visit 4: nothing saved any more.
        del sent[:]
        _generate(page)
        seen["fourth_requests"] = list(sent)

        # Visit 5: the saved choices cannot be loaded.
        page.route(
            CHOICES,
            lambda route: route.fulfill(
                status=500,
                headers={
                    "Access-Control-Allow-Origin": WEB_ORIGIN,
                    "Access-Control-Allow-Credentials": "true",
                },
                body="",
            ) if route.request.method == "GET" else route.continue_(),
        )
        seen["unloaded"] = _generate(page)
        seen["unloaded_first"] = _controls(page)
        with page.expect_response(PLAN, timeout=30000) as resp:
            page.click(f"#obPlanMeals .dash-dish-remove[aria-label='Remove {egg['recipe_name']}']")
        _drawn(page, resp.value.json())
        seen["unloaded_controls"] = _controls(page)
        page.unroute(CHOICES)
        browser.close()
    return seen


def test_nothing_to_remember_on_the_suggested_plate(walk):
    assert walk["first_controls"]["remember"] is False
    assert walk["first_controls"]["forget"] is False
    assert walk["first_controls"]["note"] == ""


def test_a_choice_can_be_remembered(walk):
    assert walk["removed_controls"]["remember"] is True
    assert walk["save_request"] == {
        "region": "south_indian", "meal_slot": "breakfast",
        "picks": ["onion_tomato_uttapam"], "leave_empty": ["egg_side"],
    }
    # Once saved there is nothing new to remember, and it can be forgotten.
    assert walk["saved_controls"]["remember"] is False
    assert walk["saved_controls"]["forget"] is True


def test_the_next_visit_starts_from_the_saved_choices(walk):
    assert [r["leave_empty"] for r in walk["second_requests"]] == [["egg_side"]]
    assert [r["picks"] for r in walk["second_requests"]] == [["onion_tomato_uttapam"]]
    assert "Onion tomato uttapam" in walk["second_controls"]["dishes"]
    assert walk["second"]["passed"]
    assert walk["egg_name"] not in walk["second_controls"]["dishes"]
    assert walk["second_controls"]["note"] == "This plate uses your saved choices for this meal."
    assert walk["second_controls"]["remember"] is False


def test_forgetting_on_the_saved_plate_sends_nothing_and_offers_to_keep_again(walk):
    assert walk["forget_on_plate_request"] == {
        "region": "south_indian", "meal_slot": "breakfast", "picks": [], "leave_empty": [],
    }
    # The plate still has the choices; they are just no longer kept.
    assert walk["forgot_on_plate_controls"]["dishes"] == walk["second_controls"]["dishes"]
    assert walk["forgot_on_plate_controls"]["forget"] is False
    assert walk["forgot_on_plate_controls"]["remember"] is True


def test_back_to_the_suggested_plate_keeps_them_saved(walk):
    assert walk["egg_name"] in walk["reset_controls"]["dishes"]
    assert walk["reset_controls"]["forget"] is True
    assert walk["reset_controls"]["remember"] is False


def test_a_saved_choice_that_no_longer_fits_is_not_forced(walk):
    # Asked as saved first, then the suggested plate -- never a looser limit.
    assert [r["picks"] for r in walk["third_requests"]] == [["plain_dosa"], []]
    assert walk["third"]["passed"]
    assert "Plain dosa" not in walk["third_controls"]["dishes"]
    assert "don't fit" in walk["third_controls"]["note"]
    assert "still saved" in walk["third_controls"]["note"]
    assert walk["third_controls"]["forget"] is True


def test_saved_choices_can_be_forgotten(walk):
    assert walk["forget_request"] == {
        "region": "south_indian", "meal_slot": "breakfast", "picks": [], "leave_empty": [],
    }
    assert walk["forgot_controls"]["forget"] is False
    assert [r["picks"] for r in walk["fourth_requests"]] == [[]]
    assert [r["leave_empty"] for r in walk["fourth_requests"]] == [[]]


def test_choices_that_could_not_be_loaded_are_said_so_and_not_overwritten(walk):
    assert walk["unloaded"]["passed"]
    assert walk["unloaded_first"]["note"] == (
        "Your saved choices couldn't be loaded, so this is the suggested plate."
    )
    # Neither control: saving or forgetting blind could overwrite what is kept.
    assert walk["unloaded_controls"]["remember"] is False
    assert walk["unloaded_controls"]["forget"] is False
