"""A portion is shown in grams beside its household unit (TASKS_3.md G1).

``tests/test_api_targets.py`` pins the server half: each component's ``grams``
is its count times the recipe's own unit weight. This pins the other half --
that the dashboard actually shows that figure on each dish row, and shows the
one the server sent rather than some other number.

Real path, no stub: the page calls the real ``POST /api/plan`` and the
response it received is read back with ``expect_response``, so the rendered
text is compared against the exact payload that produced it. Needs the static
server and the API, like every web suite here.
"""

from __future__ import annotations

import re
import socket

import pytest

from tests.test_web_no_identifiers import WEB_ORIGIN

pytestmark = pytest.mark.web

API_ORIGIN = "http://localhost:8000"


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


@pytest.fixture(scope="module")
def rendered():
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN} (python -m http.server 3000 --directory web)")
    if not _listening("localhost", 8000):
        pytest.skip(f"no API on {API_ORIGIN}; the dashboard needs a session")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        # No clinical flag: north_indian lunch passes for this profile, the
        # same one tests/test_api_targets.py's passing-plate tests use.
        page.evaluate(
            """async ([email, password]) => {
              const j = {'Content-Type': 'application/json'};
              let r = await fetch('http://localhost:8000/api/auth/signup', {method: 'POST',
                credentials: 'include', headers: j, body: JSON.stringify({email, password})});
              if (!r.ok) await fetch('http://localhost:8000/api/auth/login', {method: 'POST',
                credentials: 'include', headers: j, body: JSON.stringify({email, password})});
              await fetch('http://localhost:8000/api/profile', {method: 'PUT',
                credentials: 'include', headers: j, body: JSON.stringify({
                  age_years: 31, sex: 'male', weight_kg: 70, height_cm: 175,
                  activity: 'moderate', goal: 'maintain', diet: 'vegetarian',
                  clinical_flags: []})});
            }""",
            ["portion-grams@example.com", "portion-pw-31882"],
        )
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.wait_for_selector("#dashGenerate")
        page.click('input[name="plate"][value="north_indian:lunch"]')
        with page.expect_response("**/api/plan", timeout=30000) as resp:
            page.click("#dashGenerate")
        payload = resp.value.json()
        page.wait_for_selector("#obPlanMeals .dash-dish-qty", timeout=10000)
        rows = page.eval_on_selector_all(
            "#obPlanMeals .dash-dish-row",
            "els => els.map(e => ({name: e.querySelector('.dash-dish-name').innerText,"
            " qty: e.querySelector('.dash-dish-qty').innerText}))",
        )
        browser.close()
    return payload, rows


def test_the_plate_passed(rendered):
    # Precondition: on a decline there are no rows and the test below would
    # hold vacuously.
    payload, rows = rendered
    assert payload["passed"] is True, payload.get("disclosure")
    assert len(rows) == len(payload["components"]) > 0


def test_each_row_shows_the_grams_the_server_sent(rendered):
    payload, rows = rendered
    by_name = {c["recipe_name"]: c for c in payload["components"]}
    for row in rows:
        c = by_name[row["name"]]
        m = re.fullmatch(r"(\d+) × (.+) · (\d+) g", row["qty"])
        assert m, f"portion not shown as 'N × unit · G g': {row['qty']!r}"
        assert int(m.group(1)) == c["unit_count"]
        assert int(m.group(3)) == round(c["grams"]), (row, c)
