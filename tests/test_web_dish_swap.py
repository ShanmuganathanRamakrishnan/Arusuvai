"""The dashboard lets the user swap a dish, and says so when one cannot fit (TASKS_3.md N8).

``tests/test_api_picks.py`` pins the server half. This pins the page: each
dish with alternatives gets a menu of names, choosing one sends it as a pick
and shows the plate the server returned, "Back to the suggested plate" drops
the picks, and a pick the server declines leaves the shown plate in place
with a sentence naming the dish -- not a decline page, and not a silent swap
to something else.

The menus only list dishes the server found on a valid plate, so the decline
path cannot be reached by clicking. It is reached by adding ``plain_dosa`` --
on no valid plate for this body (docs/audit_log.md 2026-09-29) -- to the
tiffin menu before choosing it, which is what a stale menu would send.

Body as tests/test_api_picks.py: 70 kg eggetarian, maintain, South breakfast.
"""

from __future__ import annotations

import socket

import pytest

from tests.test_web_no_identifiers import WEB_ORIGIN

pytestmark = pytest.mark.web

API_ORIGIN = "http://localhost:8000"
TIFFIN_MENU = "#obPlanMeals select[aria-label^='Swap'] >> nth=0"


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _dishes(page):
    return page.eval_on_selector_all(
        "#obPlanMeals .dash-dish-name", "els => els.map(e => e.innerText)"
    )


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
            ["dish-swap@example.com", "dish-swap-pw-40417"],
        )
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.wait_for_selector("#dashGenerate")
        page.click('input[name="plate"][value="south_indian:breakfast"]')

        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click("#dashGenerate")
        seen["suggested"] = resp.value.json()
        page.wait_for_selector(TIFFIN_MENU, timeout=10000)
        seen["suggested_dishes"] = _dishes(page)
        seen["reset_hidden_at_start"] = page.is_hidden("#dashResetPicks")
        seen["menu_count"] = page.eval_on_selector_all(
            "#obPlanMeals select[aria-label^='Swap']", "els => els.length"
        )
        seen["menu_labels"] = page.eval_on_selector_all(
            "#obPlanMeals select option", "els => els.map(e => e.textContent)"
        )

        with page.expect_request("**/api/plan", timeout=30000) as req:
            with page.expect_response("**/api/plan", timeout=30000) as resp:
                page.select_option(TIFFIN_MENU, "onion_tomato_uttapam")
        seen["swap_request"] = req.value.post_data_json
        seen["swapped"] = resp.value.json()
        page.wait_for_function(
            "() => [...document.querySelectorAll('#obPlanMeals .dash-dish-name')]"
            ".some(e => e.innerText === 'Onion tomato uttapam')",
            timeout=10000,
        )
        seen["swapped_dishes"] = _dishes(page)
        seen["reset_visible_after_swap"] = page.is_visible("#dashResetPicks")

        page.evaluate(
            """() => {
              const s = document.querySelector("#obPlanMeals select[aria-label^='Swap']");
              const o = document.createElement('option');
              o.value = 'plain_dosa'; o.textContent = 'Plain dosa';
              s.appendChild(o);
            }"""
        )
        with page.expect_request("**/api/plan", timeout=30000) as req:
            with page.expect_response("**/api/plan", timeout=30000) as resp:
                page.select_option(TIFFIN_MENU, "plain_dosa")
        seen["declined_request"] = req.value.post_data_json
        seen["declined"] = resp.value.json()
        page.wait_for_function(
            "() => document.getElementById('obPlanSwapNote').innerText.length > 0",
            timeout=10000,
        )
        seen["declined_note"] = page.inner_text("#obPlanSwapNote")
        seen["declined_dishes"] = _dishes(page)
        seen["decline_page_hidden"] = page.is_hidden("#obPlanDecline")

        with page.expect_request("**/api/plan", timeout=30000) as req:
            with page.expect_response("**/api/plan", timeout=30000):
                page.click("#dashResetPicks")
        seen["reset_request"] = req.value.post_data_json
        page.wait_for_function(
            "() => ![...document.querySelectorAll('#obPlanMeals .dash-dish-name')]"
            ".some(e => e.innerText === 'Onion tomato uttapam')",
            timeout=10000,
        )
        seen["reset_dishes"] = _dishes(page)
        seen["reset_hidden_after_reset"] = page.is_hidden("#dashResetPicks")

        # A refused dish must not ride along into the next swap. Uttapam has
        # one valid plate, so no other menu is left beside it; this runs on
        # the egg side instead (measured 2026-09-29: with the omelette picked,
        # the gravy menu still offers sambar and soya kuzhambu).
        def swap(value):
            menu = page.evaluate(
                """(v) => [...document.querySelectorAll("#obPlanMeals select[aria-label^='Swap']")]
                  .findIndex(s => [...s.options].some(o => o.value === v))""",
                value,
            )
            with page.expect_request("**/api/plan", timeout=30000) as req:
                with page.expect_response("**/api/plan", timeout=30000):
                    page.select_option(f"#obPlanMeals select[aria-label^='Swap'] >> nth={menu}", value)
            page.wait_for_load_state("networkidle")
            return req.value.post_data_json

        seen["egg_request"] = swap("muttai_omelette")
        page.evaluate(
            """() => {
              const s = [...document.querySelectorAll("#obPlanMeals select[aria-label^='Swap']")]
                .find(s => [...s.options].some(o => o.value === 'idli'));
              const o = document.createElement('option');
              o.value = 'plain_dosa'; o.textContent = 'Plain dosa';
              s.appendChild(o);
            }"""
        )
        seen["second_refused_request"] = swap("plain_dosa")
        seen["gravy_request"] = swap("sambar")

        # Moving the meal picker without pressing Generate must not send the
        # next swap to a different meal: the menu belongs to the plate shown.
        page.click('input[name="plate"][value="north_indian:lunch"]')
        seen["picker_moved_request"] = swap("soya_kuzhambu")
        browser.close()
    return seen


def test_the_suggested_plate_has_a_tiffin_menu_and_no_reset(walk):
    # Precondition for everything below: the plate passed and uttapam is an
    # alternative, not already shown.
    assert walk["suggested"]["passed"]
    assert "Onion tomato uttapam" not in walk["suggested_dishes"]
    assert "Onion tomato uttapam" in walk["menu_labels"]
    assert walk["reset_hidden_at_start"]


def test_only_slots_with_a_choice_get_a_menu(walk):
    # Coconut chutney is this plate's only chutney: a menu there would offer
    # nothing to choose.
    options = {s["slot"]: s["options"] for s in walk["suggested"]["swap_options"]}
    with_choice = [c for c in walk["suggested"]["components"] if len(options[c["slot"]]) >= 2]
    assert len(with_choice) < len(walk["suggested"]["components"])  # precondition
    assert walk["menu_count"] == len(with_choice)


def test_a_swap_goes_to_the_meal_on_screen(walk):
    r = walk["picker_moved_request"]
    assert (r["region"], r["meal_slot"]) == ("south_indian", "breakfast")


def test_the_menu_shows_names_not_ids(walk):
    assert all("_" not in label for label in walk["menu_labels"]), walk["menu_labels"]


def test_choosing_a_dish_sends_it_and_shows_the_servers_plate(walk):
    assert walk["swap_request"]["picks"] == ["onion_tomato_uttapam"]
    assert walk["swapped"]["passed"]
    assert walk["swapped_dishes"] == [c["recipe_name"] for c in walk["swapped"]["components"]]
    assert walk["reset_visible_after_swap"]


def test_a_dish_that_cannot_fit_leaves_the_plate_and_says_so(walk):
    # The new pick replaces the old one in the same slot.
    assert walk["declined_request"]["picks"] == ["plain_dosa"]
    assert not walk["declined"]["passed"]
    assert walk["decline_page_hidden"]
    assert walk["declined_dishes"] == walk["swapped_dishes"]
    assert "Plain dosa" in walk["declined_note"]
    assert "plain_dosa" not in walk["declined_note"]


def test_a_refused_dish_is_not_carried_into_the_next_swap(walk):
    assert walk["egg_request"]["picks"] == ["muttai_omelette"]
    assert sorted(walk["second_refused_request"]["picks"]) == ["muttai_omelette", "plain_dosa"]
    assert sorted(walk["gravy_request"]["picks"]) == ["muttai_omelette", "sambar"]


def test_back_to_the_suggested_plate_drops_the_picks(walk):
    assert walk["reset_request"]["picks"] == []
    assert walk["reset_dishes"] == walk["suggested_dishes"]
    assert walk["reset_hidden_after_reset"]
