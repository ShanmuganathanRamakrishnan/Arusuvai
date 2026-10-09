"""The dashboard lets the user add a dish to an optional course the plate leaves empty (TASKS_3.md N9).

N8 gave each dish on the plate a swap menu. An optional course with no dish on
the plate -- curd at South breakfast -- had no row to hang one on, though the
server already lists what fits there in ``swap_options``. This pins the row
that fills that gap: one "Add ..." menu per empty course that has a dish to
offer, opening on a blank prompt rather than a dish, and sending the choice as
a pick so the server sets every count.

Measured 2026-09-30 (docs/audit_log.md, N9 entry), 70 kg eggetarian: the South
breakfast plate leaves ``curd_course`` empty with two dishes to offer and
``beverage`` empty with none; the South snack leaves ``drink`` empty with one
(neer mor). A change to the library that moves these is a reason to re-pick
the example, not to doubt the mechanism.

Re-picked 2026-10-09 (TASKS_3.md N26, docs/audit_log.md "N26"): milk tea
joined the snack drinks and now fills the 70 kg South snack's drink, and no
plate for that body leaves a course empty with exactly one dish to offer. The
snack step now uses a 55 kg eggetarian woman (same age, height, activity and
goal), whose North snack leaves ``drink`` empty with one dish (chaas).
"""

from __future__ import annotations

import socket

import pytest

from tests.test_web_no_identifiers import WEB_ORIGIN

pytestmark = pytest.mark.web

API_ORIGIN = "http://localhost:8000"
ADD_MENUS = "#obPlanMeals select[aria-label^='Add']"


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _add_menus(page):
    return page.eval_on_selector_all(
        ADD_MENUS,
        """els => els.map(s => ({
          label: s.closest('label').querySelector('span').innerText,
          value: s.value,
          options: [...s.options].map(o => o.textContent),
        }))""",
    )


def _put_profile(page, email, password, **body):
    page.evaluate(
        """async ([email, password, body]) => {
          const j = {'Content-Type': 'application/json'};
          let r = await fetch('http://localhost:8000/api/auth/signup', {method: 'POST',
            credentials: 'include', headers: j, body: JSON.stringify({email, password})});
          if (!r.ok) await fetch('http://localhost:8000/api/auth/login', {method: 'POST',
            credentials: 'include', headers: j, body: JSON.stringify({email, password})});
          await fetch('http://localhost:8000/api/profile', {method: 'PUT',
            credentials: 'include', headers: j, body: JSON.stringify(body)});
        }""",
        [email, password, body],
    )
    page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
    page.wait_for_selector("#dashGenerate")


_BODY = dict(
    age_years=28, sex="male", weight_kg=70, height_cm=175,
    activity="moderate", goal="maintain", diet="eggetarian", clinical_flags=[],
)


def _generate(page, plate):
    page.click(f'input[name="plate"][value="{plate}"]')
    with page.expect_response("**/api/plan", timeout=30000) as resp:
        page.click("#dashGenerate")
    page.wait_for_selector("#obPlanMeals .dash-dish-name", timeout=10000)
    page.wait_for_load_state("networkidle")
    return resp.value.json()


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
        account = ("add-dish@example.com", "add-dish-pw-52093")
        _put_profile(page, *account, **_BODY)

        seen["breakfast"] = _generate(page, "south_indian:breakfast")
        seen["breakfast_menus"] = _add_menus(page)
        seen["breakfast_rows"] = page.eval_on_selector_all(
            "#obPlanMeals .dash-dish-row", "els => els.length"
        )

        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.select_option(ADD_MENUS + " >> nth=0", "soya_curd")
        seen["add_request"] = resp.value.request.post_data_json
        seen["added"] = resp.value.json()
        page.wait_for_function(
            "() => [...document.querySelectorAll('#obPlanMeals .dash-dish-name')]"
            ".some(e => e.innerText === 'Soya curd')",
            timeout=10000,
        )
        seen["added_dishes"] = page.eval_on_selector_all(
            "#obPlanMeals .dash-dish-name", "els => els.map(e => e.innerText)"
        )
        seen["added_menus"] = _add_menus(page)
        seen["reset_visible_after_add"] = page.is_visible("#dashResetPicks")

        # The snack step's own body -- see the module docstring (N26).
        _put_profile(page, *account, **{**_BODY, "sex": "female", "weight_kg": 55})
        seen["snack"] = _generate(page, "north_indian:snack")
        seen["snack_menus"] = _add_menus(page)
        browser.close()
    return seen


def test_the_breakfast_plate_leaves_curd_empty(walk):
    # Precondition: with a curd row already on the plate there is nothing to add.
    assert walk["breakfast"]["passed"]
    assert "curd_course" not in {c["slot"] for c in walk["breakfast"]["components"]}


def test_one_menu_per_empty_course_with_a_dish_to_offer(walk):
    # beverage is empty too, but has no dish to offer, so it gets no menu.
    assert [m["label"] for m in walk["breakfast_menus"]] == ["Add a curd course"]
    assert walk["breakfast_menus"][0]["options"] == ["Choose a dish", "Soya curd", "Curd"]


def test_the_menu_opens_on_a_prompt_not_a_dish(walk):
    assert walk["breakfast_menus"][0]["value"] == ""


def test_the_add_row_is_not_counted_as_a_dish(walk):
    assert walk["breakfast_rows"] == len(walk["breakfast"]["components"])


def test_adding_a_dish_sends_it_and_shows_the_servers_plate(walk):
    assert walk["add_request"]["picks"] == ["soya_curd"]
    assert walk["added"]["passed"]
    assert walk["added_dishes"] == [c["recipe_name"] for c in walk["added"]["components"]]
    assert "Soya curd" in walk["added_dishes"]
    assert walk["reset_visible_after_add"]


def test_a_filled_course_has_no_add_menu(walk):
    assert all(m["label"] != "Add a curd course" for m in walk["added_menus"])


def test_a_course_with_one_dish_still_gets_a_menu(walk):
    # Unlike a swap, adding a lone dish or not is still a choice.
    assert walk["snack"]["passed"]
    assert walk["snack_menus"] == [
        {"label": "Add a drink", "value": "", "options": ["Choose a dish", "Chaas"]}
    ]
