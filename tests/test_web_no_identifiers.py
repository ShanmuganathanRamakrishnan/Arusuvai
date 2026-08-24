"""No internal identifier may reach a rendered string, on any view.

Why this is a sweep and not another grep
----------------------------------------

This defect class has now escaped three times, each time after being reported
closed:

1. the Diet step rendering ``non_vegetarian`` as a chip label,
2. the plate picker rendering ``chronic_kidney_disease`` on the dashboard,
3. the citation panel rendering ``morton_2018_protein`` inside a sentence.

Every one of those was fixed by adding the specific string to a label map, and
every fix was verified by grepping for that specific string. That verification
method cannot work, because the failing string is by definition the one nobody
thought to grep for — a grep needs to know the answer first. Each fix was
therefore correct and provided no evidence about the next occurrence.

So this test does not look for known strings. It walks the rendered DOM of
every view, takes every piece of text a human can actually see, and fails on
any token shaped like a Python/JS identifier: ``snake_case`` or
``SCREAMING_CASE``. It cannot be satisfied by knowing which key leaked; it can
only be satisfied by no key leaking.

The ten views are the ones a user can reach: the landing page, wizard steps
1-6, and the dashboard in three states — the plate picker, a plate that solves,
and a plate that declines.

That last one was a claim before it was true. Until 2026-08-09 this paragraph
said the sweep covered "a solved plate or an honest decline", and the fixture
clicked Generate once, on the default plate, which solves. `renderPlanSuccess`
and `renderPlanDecline` write into two independent sections, so the violation
list and the disclosure paragraph — the two places most likely to show a reader
a raw macro name, and the ones this file exists for — were never swept at all
(`docs/audit_log.md` finding 36). The fixture now selects a plate that declines
for its own profile and collects that view too.

Legitimate exceptions go in ``ALLOWED`` below, each with a reason. Keep that
list short: every entry is a hole, and a long allowlist is how this test stops
working.

Running it
----------

Same dev-only prerequisites as ``test_web_wizard_layout.py``; skips rather
than fails when Playwright, the static server, or the API is missing::

    python -m http.server 3000 --directory web
    uvicorn api.main:app --reload
"""

from __future__ import annotations

import re
import socket

import pytest

WEB_ORIGIN = "http://localhost:3000"
API_ORIGIN = "http://localhost:8000"

pytestmark = pytest.mark.web

#: snake_case or SCREAMING_CASE. Deliberately NOT dotted names or camelCase:
#: a dotted token matches version strings ("v2.0.10") and filenames
#: ("index.csv") that are legitimately part of a citation, and camelCase
#: matches ordinary prose ("McKenzie"). Underscores are the shape that only
#: ever comes from an enum member or a registry key.
IDENTIFIER = re.compile(r"\b[a-z0-9]+(?:_[a-z0-9]+)+\b|\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")

#: Tokens allowed to appear despite matching. Each needs a reason, because
#: each is a hole in the check.
ALLOWED: dict[str, str] = {
    # Nothing yet. When something lands here, say why it must be visible to a
    # user rather than why it is inconvenient to rename.
}

#: Every visible text node, excluding the places where an identifier is the
#: legitimate subject rather than a leak: <code> (the API endpoint labels, e.g.
#: "POST /api/plan", which are shown on purpose as provenance) and <script>.
COLLECT = """() => {
  const out = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    const el = n.parentElement;
    if (!el || el.offsetParent === null) continue;
    if (el.closest('script, style, code, pre')) continue;
    const t = n.textContent.trim();
    if (t) out.push(t);
  }
  return out;
}"""


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _leaks(strings: list[str]) -> list[tuple[str, str]]:
    found = []
    for s in strings:
        for token in IDENTIFIER.findall(s):
            if token in ALLOWED:
                continue
            found.append((token, s[:120]))
    return found


@pytest.fixture(scope="module")
def rendered_text() -> dict[str, list[str]]:
    """Visible text from all eight views, in one browser run."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN} (python -m http.server 3000 --directory web)")
    if not _listening("localhost", 8000):
        pytest.skip(f"no API on {API_ORIGIN}; steps 5-6 and the dashboard need it")

    views: dict[str, list[str]] = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})

        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        page.wait_for_timeout(900)
        views["landing"] = page.evaluate(COLLECT)

        page.goto(f"{WEB_ORIGIN}/onboarding.html", wait_until="networkidle")
        page.wait_for_timeout(600)
        for step in range(1, 7):
            views[f"wizard_step{step}"] = page.evaluate(COLLECT)
            if step == 6:
                break
            # Step 5 waits on POST /api/targets before Continue enables, and
            # the science panel is opened explicitly so its citation strings
            # are actually in the DOM when they are swept -- an unopened
            # <details> renders nothing, which would have hidden the very leak
            # this file was written for.
            if step == 4:
                page.wait_for_selector("#obNext:not([disabled])", timeout=20000)
                page.evaluate(
                    "() => { const d = document.getElementById('obScienceExpander');"
                    " if (d) d.open = true; }"
                )
                page.wait_for_timeout(1500)
            page.wait_for_selector("#obNext:not([disabled])", timeout=20000)
            page.click("#obNext")
            page.wait_for_timeout(700)

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
            ["identifier-sweep@example.com", "sweep-pw-31882"],
        )

        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.wait_for_timeout(1400)
        views["dashboard"] = page.evaluate(COLLECT)
        page.click("#dashGenerate")
        page.wait_for_timeout(3500)
        views["dashboard_after_plan"] = page.evaluate(COLLECT)

        # The decline. `renderPlanSuccess` and `renderPlanDecline` write into two
        # independent sections, so the view above exercises neither the violation
        # list nor the disclosure paragraph -- the two places a raw macro name is
        # most likely to reach a reader, and the two this file's docstring
        # claimed to sweep while never selecting a plate that declines
        # (`docs/audit_log.md` finding 36).
        #
        # south_indian:lunch was chosen here as the plate that declines for
        # the CKD profile above. south_indian:dinner joined the plate picker
        # 2026-08-24 (TASKS_3.md R4d), making five options total, but that is
        # not what makes this comment stale: checked live 2026-08-24 while
        # touching this file for the south_dinner card, this exact profile
        # (weight_kg=74, goal=maintain) NO LONGER declines for south_indian:
        # lunch -- plan_within_ladder returns a plan, not None -- the same
        # sodium-mechanism side effect noted in tests/test_api_targets.py's
        # decline-fixture repoint (commit b28447f, finding 51 follow-up), just
        # not caught in this file at the time. Logged as a new finding in
        # docs/audit_log.md rather than fixed here -- this test's own repoint
        # is a distinct reviewable idea from the south_dinner template this
        # commit is actually about.
        page.click('input[name="plate"][value="south_indian:lunch"]')
        page.click("#dashGenerate")
        page.wait_for_timeout(3500)
        views["dashboard_after_decline"] = page.evaluate(COLLECT)

        browser.close()
    return views


def test_every_view_was_actually_reached(rendered_text):
    """A sweep that silently covered two views would pass and mean nothing."""
    assert len(rendered_text) >= 10, (
        "expected the landing page, six wizard steps, and the dashboard before "
        "a plan call, after one that succeeds, and after one that declines; "
        f"reached {sorted(rendered_text)}"
    )
    for view, strings in rendered_text.items():
        assert len(strings) > 5, f"{view} rendered almost no text ({len(strings)})"

    # The two views that carry the values most likely to leak must be shown to
    # have actually rendered them, or a clean sweep over an empty panel would
    # read as a pass. Step 5's citation panel is where morton_2018_protein
    # escaped; the dashboard's tag row is where chronic_kidney_disease did.
    step5 = " ".join(rendered_text["wizard_step5"])
    assert "Morton et al. (2018)" in step5, (
        "the science panel did not render its citations, so the sweep of step "
        "5 covered nothing — the panel is where this defect class last escaped"
    )
    dash = " ".join(rendered_text["dashboard"])
    assert "Chronic kidney disease" in dash, (
        "the clinical-flag tag did not render, so the dashboard sweep did not "
        "exercise the label map that used to leak the raw enum member"
    )

    # The decline view has to be shown to be a decline, and to have rendered the
    # violation list rather than an empty section. Without this a plate that
    # started passing would turn this into a second sweep of the success view --
    # green, and covering exactly nothing new.
    decline = rendered_text["dashboard_after_decline"]
    joined = " ".join(decline)
    assert "This library can't build you a plate yet" in joined, (
        "the decline section did not render; the plate selected for it may have "
        "started passing, in which case pick another that declines rather than "
        "deleting this assertion"
    )
    assert "South Indian lunch" in joined, (
        "the decline view did not name the plate it was asked for, so the radio "
        "click above did not take effect"
    )
    # Durable across the copy map this file is about to force: whatever prose
    # replaces `sodium_mg`, an honest decline still has to tell the reader that
    # salt is the blocking constraint. Asserted case-insensitively so it holds
    # for both the raw macro name today and a display label tomorrow.
    assert any("sodium" in s.lower() or "salt" in s.lower() for s in decline), (
        "the decline rendered no violation naming the blocking constraint, so "
        "the sweep covered the section but not the text that leaks into it"
    )


@pytest.mark.parametrize(
    "view",
    [
        "landing", "wizard_step1", "wizard_step2", "wizard_step3",
        "wizard_step4", "wizard_step5", "wizard_step6",
        "dashboard", "dashboard_after_plan", "dashboard_after_decline",
    ],
)
def test_no_identifier_reaches_a_rendered_string(rendered_text, view):
    leaks = _leaks(rendered_text[view])
    assert not leaks, (
        f"{view} renders internal identifiers to the user. Add a display label "
        "where the value is turned into text — do not add it to ALLOWED unless "
        f"a user genuinely needs to see the key. Leaks: {leaks[:8]}"
    )


def test_the_detector_actually_detects():
    """The sweep must fail on a known-bad string, or it proves nothing.

    Guards the regex itself: a pattern that silently stopped matching would
    turn every test above into a green light for an unswept page. The three
    strings below are the three real escapes this file exists to catch.
    """
    for bad in (
        "This project's decision, anchored on morton_2018_protein.",
        "chronic_kidney_disease",
        "non_vegetarian",
        "south_indian · breakfast",
        "(project_estimate, unverified)",
    ):
        assert _leaks([bad]), f"the detector missed {bad!r}"

    # And it must not fire on ordinary copy, or it would be turned off.
    for good in (
        "Morton et al. (2018). Br J Sports Med 52(6):376-384.",
        "Chronic kidney disease",
        "≈1,850 kcal (±10%)",
        "ifct2017/ifct2017 v2.0.10, Zenodo, energies/index.csv.",
        "This plan delivers 76 g of protein against a 90 g target.",
    ):
        assert not _leaks([good]), f"the detector false-positived on {good!r}"
