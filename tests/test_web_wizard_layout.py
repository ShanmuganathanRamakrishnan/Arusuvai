"""The onboarding wizard's layout contract, asserted against a real browser.

Why this test exists, and why it is not a CSS-string assertion
-------------------------------------------------------------

The six wizard steps were authored independently, and the two defects that
produced were both *emergent*: no single step's CSS was wrong, but each one
sized and positioned itself, so the composition drifted.

1. The wizard vertically centred its content, which makes every step's Y a
   function of its own height. Measured before the fix, the stepper sat at
   roughly 269 / 181 / 329 / 167 / 122 / 251 px from the top across steps 1-6
   — the whole UI jumped on every Continue.
2. Each step declared its own control-column width, so that column started at
   roughly 1037 / 845 / 975 / 866 / 893 px depending on the step, and the
   narrative column was a different width each time.

CLAUDE.md's round-4 addendum is the reason this is a browser test and not a
grep over styles.css: "the doc's rule is implemented" is not evidence the rule
works — the test has to perturb an input and check the output actually moves.
Here the perturbation is *navigating between steps*, and the assertion is that
two measured geometries do NOT move. A test that only checked that
``.ob-grid12`` appears in the stylesheet would pass against every version of
this page, including the two broken ones above.

Running it
----------

Needs Playwright and a static server for ``web/``; both are dev-only (see
``requirements-dev.txt``), so the test SKIPS rather than fails when either is
missing, and ``python -m pytest tests/ -q`` stays runnable on a bare checkout::

    pip install -r requirements-dev.txt && python -m playwright install chromium
    python -m http.server 3000 --directory web

Steps 1-4 and 6 render from static markup. Step 5 needs ``POST /api/targets``
to resolve before its Continue enables, so if the API is not up this test
covers the five steps it can reach and says so, rather than silently reporting
a five-step invariant as a six-step one.

The container check (added 2026-07-29)
--------------------------------------

A third defect of the same family survived the fix above, because the fix was
scoped to the wizard: the wizard, the landing page and the dashboard each had
their own measure (1200px from ``--wizard-max``, 1240px from ``--max``, and
1040px set inline on ``dashboard.html``'s ``.wrap``). Each page was internally
consistent, so nothing on a single screen looked wrong in isolation — except
the dashboard, whose header kept the global measure while its content took the
inline one, putting the brand at x=305 above a content column at x=415.

``test_header_logo_shares_content_left_edge`` is the assertion that would have
caught it, and it is per-route rather than per-step for the same reason the
step checks are per-step: the defect is only visible when two things that
should agree are measured against each other. A grep for ``--container-max``
would pass on the broken version too, since ``--max`` existed and every page
did reference *a* token.
"""

from __future__ import annotations

import socket

import pytest

WEB_ORIGIN = "http://localhost:3000"
API_ORIGIN = "http://localhost:8000"
PAGE = f"{WEB_ORIGIN}/onboarding.html"

pytestmark = pytest.mark.web


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


@pytest.fixture(scope="module")
def measurements():
    """Walk all reachable steps once; return one geometry dict per step."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN} (python -m http.server 3000 --directory web)")

    api_up = _listening("localhost", 8000)

    measure = """() => {
      const step = document.querySelector('.ob-step:not([hidden])');
      const box = el => { if (!el) return null; const r = el.getBoundingClientRect();
        return {x: Math.round(r.x), y: Math.round(r.y + window.scrollY)}; };
      const de = document.documentElement;
      return {
        step: Number(document.getElementById('obWizard').dataset.step),
        logo: box(document.querySelector('.brand')),
        stepper: box(document.querySelector('.ob-progress2')),
        narrative: box(step && step.querySelector('.ob-col-narrative')),
        controls: box(step && step.querySelector('.ob-col-controls')),
        hScroll: de.scrollWidth > de.clientWidth,
        primaries: [...document.querySelectorAll('.btn-primary, .ob-account-submit')]
          .filter(b => !b.hidden && b.offsetParent !== null).length,
      };
    }"""

    out = []
    errors: list[str] = []
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(PAGE, wait_until="networkidle")
        page.wait_for_timeout(500)
        for i in range(1, 7):
            page.wait_for_timeout(400)
            out.append(page.evaluate(measure))
            if i == 6:
                break
            try:
                page.wait_for_selector("#obNext:not([disabled])", timeout=15000)
            except Exception:
                # Only reachable at step 5 with the API down.
                break
            page.click("#obNext")
            page.wait_for_timeout(700)
        browser.close()

    if len(out) < 6 and not api_up:
        # Reported, not swallowed: a partial run must not look like a full one.
        print(f"\n[layout] API not reachable at {API_ORIGIN}; covered {len(out)} of 6 steps.")
    return {"steps": out, "errors": errors, "api_up": api_up}


def test_stepper_sits_at_one_vertical_offset(measurements):
    """Acceptance check 1. Top-aligned means the stepper never moves."""
    ys = {m["stepper"]["y"] for m in measurements["steps"]}
    assert len(ys) == 1, (
        "the stepper landed at more than one Y across steps — the wizard is "
        f"sizing itself off content height again. Offsets seen: {sorted(ys)}"
    )


def test_control_column_shares_one_left_edge(measurements):
    """Acceptance check 2. This is the assertion §1 of the brief asks for."""
    xs = {m["controls"]["x"] for m in measurements["steps"]}
    assert len(xs) == 1, (
        "the control column started at more than one X across steps — some "
        f"step is overriding its grid span or its width. Offsets seen: {sorted(xs)}"
    )


def test_narrative_column_shares_one_left_edge(measurements):
    """The corollary: a fixed control origin is worthless if the intro drifts."""
    xs = {m["narrative"]["x"] for m in measurements["steps"]}
    assert len(xs) == 1, f"narrative column left edges differ: {sorted(xs)}"


def test_narrative_column_starts_at_the_logo(measurements):
    """The live-page counterpart of the container check below.

    ``test_header_logo_shares_content_left_edge`` measures the container with
    JS off; this one measures the actual rendered first grid column with the
    wizard running, so a grid that started at column 2 would fail here even
    though its container was correct.
    """
    offenders = {
        m["step"]: (m["logo"]["x"], m["narrative"]["x"])
        for m in measurements["steps"]
        if m["logo"]["x"] != m["narrative"]["x"]
    }
    assert not offenders, f"steps where (logoX, narrativeX) disagree: {offenders}"


def test_exactly_one_primary_button_per_step(measurements):
    """Acceptance check 10."""
    offenders = {m["step"]: m["primaries"] for m in measurements["steps"] if m["primaries"] != 1}
    assert not offenders, f"steps with a primary-button count other than 1: {offenders}"


def test_no_horizontal_scroll_on_any_step(measurements):
    offenders = [m["step"] for m in measurements["steps"] if m["hScroll"]]
    assert not offenders, f"steps that overflow horizontally at 1600px: {offenders}"


def test_no_page_errors(measurements):
    assert not measurements["errors"], measurements["errors"]


# --------------------------------------------------------------------------
# The container contract: one measure, one inset, header through footer,
# on every route.
# --------------------------------------------------------------------------

ROUTES = ("index.html", "onboarding.html", "dashboard.html")


@pytest.fixture(scope="module")
def container_geometry():
    """Left edge of the brand vs. left edge of the content container, per route.

    JavaScript is disabled deliberately. The assertion is about CSS container
    geometry, which is fully determined before any script runs — and with JS
    on, ``dashboard.html`` redirects an unauthenticated visitor to onboarding,
    so the one route where this defect was worst would be the one route the
    test could not reach. Turning JS off is what makes the check cover all
    three routes from a plain checkout with no session.
    """
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN} (python -m http.server 3000 --directory web)")

    probe = """() => {
      const px = v => Math.round(parseFloat(v) || 0);
      const brand = document.querySelector('.brand');
      const wrap = document.querySelector('.wrap');
      const header = document.querySelector('.header-inner');
      const inner = el => {  // content-box left edge, i.e. where text starts
        const r = el.getBoundingClientRect();
        return Math.round(r.x) + px(getComputedStyle(el).paddingLeft);
      };
      return {
        brandX: Math.round(brand.getBoundingClientRect().x),
        contentX: inner(wrap),
        headerX: inner(header),
        wrapW: Math.round(wrap.getBoundingClientRect().width),
        headerW: Math.round(header.getBoundingClientRect().width),
      };
    }"""

    out = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1600, "height": 950}, java_script_enabled=False
        )
        page = context.new_page()
        for route in ROUTES:
            page.goto(f"{WEB_ORIGIN}/{route}", wait_until="load")
            out[route] = page.evaluate(probe)
        browser.close()
    return out


@pytest.mark.parametrize("route", ROUTES)
def test_header_logo_shares_content_left_edge(container_geometry, route):
    """The check that would have caught the dashboard's inline 1040px.

    Measured before the fix: dashboard brand at x=305, content column at
    x=415 — the logo hanging 110px left of everything beneath it, because the
    header used --max and the content used an inline override.
    """
    g = container_geometry[route]
    assert g["brandX"] == g["contentX"], (
        f"{route}: the brand starts at x={g['brandX']} but the content container's "
        f"content box starts at x={g['contentX']}. Something is setting its own "
        "width instead of deriving from --container-max / --container-pad."
    )


def test_every_route_shares_one_container_width(container_geometry):
    """No route-specific measure. Three pages, one number."""
    widths = {r: (g["wrapW"], g["headerW"]) for r, g in container_geometry.items()}
    distinct = {w for pair in widths.values() for w in pair}
    assert len(distinct) == 1, (
        f"more than one container width across routes and their headers: {widths}"
    )


# --------------------------------------------------------------------------
# The header contract: one nav, three named states (added 2026-07-30).
#
# Measured before the fix, with a session cookie set: the landing page showed
# four nav items, the dashboard showed three, and onboarding showed NOTHING —
# a signed-in user midway through the wizard could not reach Log out, because
# each page hand-wrote its own header and the wizard's version only appeared
# under conditions that page never rendered under.
#
# Both checks below are about agreement between routes, which is the only
# place this class of defect is visible: every one of the three headers was
# internally consistent and looked fine on its own screen.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def header_markup():
    """Static (JS-off) header shape per route: one brand, one empty nav."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")

    probe = """() => {
      const nav = document.getElementById('appNav');
      return {
        // Scoped to the header: the landing page also uses .brand in its
        // footer and its auth modal, which is fine and not what this counts.
        brands: document.querySelectorAll('#siteHeader .brand').length,
        navs: document.querySelectorAll('#appNav').length,
        // Written by header.js, so JS-off it must be empty: no route may
        // hand-write a nav item into its own markup.
        staticNavChildren: nav ? nav.children.length : -1,
        actions: [...document.querySelectorAll('.btn-action')].map(b => {
          const s = getComputedStyle(b);
          return [s.paddingTop, s.paddingBottom, s.paddingLeft, s.paddingRight,
                  s.fontSize, s.fontWeight, s.borderTopLeftRadius, s.lineHeight,
                  s.boxSizing].join(' ');
        }),
        inlineSizedActions: [...document.querySelectorAll('.btn-action[style]')]
          .map(b => b.id || b.textContent.trim().slice(0, 24))
          .filter(() => true),
      };
    }"""

    out = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1600, "height": 950}, java_script_enabled=False
        )
        page = context.new_page()
        for route in ROUTES:
            page.goto(f"{WEB_ORIGIN}/{route}", wait_until="load")
            out[route] = page.evaluate(probe)
        browser.close()
    return out


@pytest.mark.parametrize("route", ROUTES)
def test_no_route_hand_writes_its_own_nav(header_markup, route):
    """One nav element, empty until web/header.js fills it.

    The brand deliberately stays in static markup (the container check above
    measures it with JS off); the nav deliberately does not, because a nav
    item written into a page is a nav item that can disagree with the other
    two pages, which is exactly what happened.
    """
    m = header_markup[route]
    assert m["brands"] == 1, f"{route}: expected one .brand, found {m['brands']}"
    assert m["navs"] == 1, f"{route}: expected one #appNav, found {m['navs']}"
    assert m["staticNavChildren"] == 0, (
        f"{route}: #appNav has {m['staticNavChildren']} hand-written children. "
        "Nav items belong in web/header.js's three states, not in page markup."
    )


def test_one_action_button_geometry_across_routes(header_markup):
    """P1-3: the placement of the advancing action may differ; the button may not.

    Measured before the fix: the wizard's Continue was 13px/24px at 15px from
    a rule, the dashboard's Generate 14px/26px at 15px from an inline style,
    its Regenerate 14px/24px from another, and the filled and outlined
    variants rendered 46 / 48 / 48px tall.
    """
    seen = {}
    for route, m in header_markup.items():
        for spec in m["actions"]:
            seen.setdefault(spec, []).append(route)
        assert not m["inlineSizedActions"], (
            f"{route}: .btn-action carrying its own inline style: "
            f"{m['inlineSizedActions']}. The geometry lives in .btn-action."
        )
    assert len(seen) == 1, f"more than one .btn-action geometry: {seen}"


def test_header_states_differ_by_route_and_session():
    """The three states, asserted live — including the one that was empty.

    This needs JS (the header is rendered) and a real session for the
    authenticated states, so it skips rather than fails when the API is down.
    """
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")
    if not _listening("localhost", 8000):
        pytest.skip(f"no API on {API_ORIGIN}; the signed-in states need a session")

    email, password = "headerstate@example.com", "header-state-pw-8823"
    read = """() => {
      const hdr = document.getElementById('siteHeader');
      const nav = document.getElementById('appNav');
      return {state: hdr.dataset.headerState,
              ids: [...nav.children].map(e => e.id)};
    }"""

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})

        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        page.wait_for_timeout(700)
        anon_landing = page.evaluate(read)

        page.goto(f"{WEB_ORIGIN}/onboarding.html", wait_until="networkidle")
        page.wait_for_timeout(700)
        anon_wizard = page.evaluate(read)

        page.evaluate(
            """async ([email, password]) => {
              let r = await fetch('http://localhost:8000/api/auth/signup', {method: 'POST',
                credentials: 'include', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})});
              if (!r.ok) await fetch('http://localhost:8000/api/auth/login', {method: 'POST',
                credentials: 'include', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})});
            }""",
            [email, password],
        )

        page.goto(f"{WEB_ORIGIN}/onboarding.html", wait_until="networkidle")
        page.wait_for_timeout(1000)
        authed_wizard = page.evaluate(read)

        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        page.wait_for_timeout(1000)
        authed_landing = page.evaluate(read)
        browser.close()

    assert anon_landing["state"] == "anonymous"
    assert anon_landing["ids"] == ["hdrHow", "hdrTargets", "hdrSignin", "hdrSignup"]

    # The wizard is in its own state whether or not a session exists -- it does
    # NOT fall back to the marketing nav, which would put "Get your targets"
    # in front of someone already filling that form in.
    assert anon_wizard["state"] == "onboarding"
    assert anon_wizard["ids"] == []

    # This is the defect: before the fix this list was also empty, and the only
    # way out of the account was to leave the page.
    assert authed_wizard["state"] == "onboarding"
    assert authed_wizard["ids"] == ["hdrUserEmail", "hdrLogout"], (
        "a signed-in user mid-wizard must be able to see who they are and log "
        f"out; got {authed_wizard['ids']}"
    )

    assert authed_landing["state"] == "authenticated"
    assert authed_landing["ids"] == [
        "hdrDashboard", "hdrEditProfile", "hdrUserEmail", "hdrLogout",
    ]


# --------------------------------------------------------------------------
# The plate picker is the seventh view of the same grid (added 2026-07-30).
#
# ``test_control_column_shares_one_left_edge`` above proves the six wizard
# steps agree with each other. It cannot prove the dashboard agrees with them,
# because it never loads that route -- and the dashboard is where the original
# defect was worst (its .wrap carried an inline 1040px). The container check
# measures the wrap; this measures the CONTROL COLUMN inside it, which is the
# number the original brief named: it landed at roughly 1037 / 845 / 975 /
# 866 / 893 px across steps before the .ob-grid12 fix.
#
# The plate picker renders into .ob-grid12 too, so this ought to hold "by
# construction" -- which is exactly the round-4 addendum's warning. Measure it.
# --------------------------------------------------------------------------


def test_plate_picker_control_column_matches_the_wizard(measurements):
    """The dashboard's control column starts where the wizard's does."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")
    if not _listening("localhost", 8000):
        pytest.skip(f"no API on {API_ORIGIN}; the dashboard needs a session")

    wizard_xs = {m["controls"]["x"] for m in measurements["steps"]}
    assert len(wizard_xs) == 1, f"wizard control column already disagrees: {wizard_xs}"
    wizard_x = wizard_xs.pop()

    probe = """() => {
      const g = document.querySelector('.ob-grid12');
      const col = g && g.querySelector('.ob-col-controls');
      const nar = g && g.querySelector('.ob-col-narrative');
      if (!col) return null;
      return { controlsX: Math.round(col.getBoundingClientRect().x),
               narrativeX: Math.round(nar.getBoundingClientRect().x) };
    }"""

    email = "layout-platepicker@example.com"
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        # A session AND a saved profile: without the profile the dashboard
        # renders its "complete onboarding first" gate, which has no grid.
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
                  clinical_flags: []})});
            }""",
            [email, "layout-pw-77213"],
        )
        page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
        page.wait_for_timeout(1200)
        picker = page.evaluate(probe)
        browser.close()

    assert picker is not None, "no .ob-grid12 on the dashboard — is the gate still loading?"
    assert picker["controlsX"] == wizard_x, (
        "the plate picker's control column starts at "
        f"x={picker['controlsX']} but the wizard's starts at x={wizard_x}. "
        "One of the two routes is sizing its own column again."
    )


# --------------------------------------------------------------------------
# Item 4's resolution, pinned (added 2026-07-30).
#
# The P1 report claimed "zero horizontal scroll at 390px" and, in the same
# breath, listed .calc-card as overflowing at 390px. Both were true, and that
# is the problem: `body { overflow-x: clip }` means NO amount of overflow can
# ever produce a scrollbar, so "no horizontal scroll" is not evidence that
# nothing overflows -- it is evidence that overflow is being hidden.
#
# Measured at 390px: .calc-card is 308px wide starting at x=350, i.e. its right
# edge is at 658 against a 390px viewport, and its parent .calc-panel is 0px
# wide with overflow-x: hidden. Roughly 40px of a 308px card is on screen.
#
# The two facts are asserted SEPARATELY below so neither can be quoted as
# though it settled the other, and fact 3 -- which used to assert the card
# overflowed -- was flipped on 2026-07-30 when the dock was brought into the
# layout system (P2 item 2): both the panel and the card now take their width
# from --calc-panel-w, which is min(308px, 100vw - 64px). The test stays in
# place with its history rather than being deleted, because the useful part is
# fact 2: the clip means the page's own scroll geometry can never report this
# class of defect, on this element or any future one.
# --------------------------------------------------------------------------

#: Widths worth checking: either side of the dock's 1100px anchoring change,
#: the two common phone widths, and 320px, where the viewport is narrower than
#: the card's natural 308px plus the toggle and the min() actually binds.
DOCK_WIDTHS = (1600, 1280, 1100, 768, 390, 320)


@pytest.fixture(scope="module")
def calc_dock_geometry():
    """The dock measured OPEN at each width — closed it cannot overflow."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")

    probe = """() => {
      const de = document.documentElement;
      const card = document.querySelector('.calc-card');
      const dock = document.getElementById('calcDock');
      const r = card.getBoundingClientRect();
      const d = dock.getBoundingClientRect();
      return {
        hScroll: de.scrollWidth > de.clientWidth,
        clip: getComputedStyle(document.body).overflowX,
        clientWidth: de.clientWidth,
        cardLeft: Math.round(r.left),
        cardRight: Math.round(r.right),
        cardWidth: Math.round(r.width),
        panelWidth: Math.round(document.querySelector('.calc-panel')
                                       .getBoundingClientRect().width),
        dockCentred: Math.abs((d.top + d.bottom) / 2 - de.clientHeight / 2) < 24,
      };
    }"""

    out = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        for width in DOCK_WIDTHS:
            page.set_viewport_size({"width": width, "height": 900})
            page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
            page.wait_for_timeout(500)
            page.click("#calcToggle")
            page.wait_for_timeout(700)   # the panel's width transition is 420ms
            out[width] = page.evaluate(probe)
        browser.close()
    return out


@pytest.mark.parametrize("width", DOCK_WIDTHS)
def test_the_open_calculator_dock_fits_the_viewport(calc_dock_geometry, width):
    """Fact 3, flipped. Measured at 390px BEFORE the fix: a 308px card starting
    at x=350, right edge 658 against a 390px viewport — roughly 40px of it on
    screen, inside a 0px-wide `overflow-x: hidden` panel."""
    g = calc_dock_geometry[width]
    assert g["cardRight"] <= g["clientWidth"], (
        f"at {width}px the open calculator card's right edge is at "
        f"{g['cardRight']} against a {g['clientWidth']}px viewport — it is "
        "being clipped, not laid out. --calc-panel-w is what bounds this."
    )
    assert g["cardLeft"] >= 0, f"at {width}px the card starts off-screen left"
    assert g["cardWidth"] == g["panelWidth"], (
        f"at {width}px the card is {g['cardWidth']}px inside a "
        f"{g['panelWidth']}px panel. Both must read --calc-panel-w; their "
        "disagreement is exactly what produced the clipped state."
    )


def test_the_dock_drops_out_of_the_reading_column_below_1100(calc_dock_geometry):
    """The behaviour that was undefined: what the rail does as the page narrows.

    Above 1100px — the same width .ob-grid12 collapses at — the dock sits at
    the vertical centre, beside the content. At or below it the dock is bottom
    anchored, so an open panel covers the end of the page rather than the
    middle of the paragraph being read.
    """
    centred = {w: g["dockCentred"] for w, g in calc_dock_geometry.items()}
    offenders = {w: c for w, c in centred.items() if c != (w > 1100)}
    assert not offenders, (
        f"the dock's anchoring does not change at 1100px: {centred}"
    )


def test_the_closed_dock_paints_nothing_outside_the_viewport():
    """What known-inconsistency 0 was actually measuring, stated correctly.

    The 390px reading behind that entry — a 308px ``.calc-card`` with its right
    edge at 658 — was taken with the dock CLOSED. Closed, ``.calc-panel`` is
    0px wide with ``overflow: hidden``, so the card's rect sits off the right
    edge but its paint is clipped by its own parent, not by the page. That is a
    slide-out drawer working as designed, and it is a different fact from an
    element the page has to hide with ``overflow-x: clip``.

    Both halves are asserted, because the entry conflated them: the card is
    off-viewport by rect, AND its clipping parent has zero visible width.
    """
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")

    probe = """() => {
      const panel = document.querySelector('.calc-panel');
      const card = document.querySelector('.calc-card');
      return {
        open: document.getElementById('calcDock').classList.contains('open'),
        panelWidth: Math.round(panel.getBoundingClientRect().width),
        panelOverflow: getComputedStyle(panel).overflow,
        cardRight: Math.round(card.getBoundingClientRect().right),
        clientWidth: document.documentElement.clientWidth,
      };
    }"""

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        page.wait_for_timeout(800)
        g = page.evaluate(probe)
        browser.close()

    assert not g["open"], "the dock should start closed"
    assert g["panelWidth"] == 0, (
        f"the closed panel is {g['panelWidth']}px wide, so the card it holds "
        "is no longer clipped by it and the reasoning below does not apply"
    )
    assert g["panelOverflow"] == "hidden", (
        f"the closed panel's overflow is {g['panelOverflow']!r}; the card is "
        "only invisible because the panel hides it"
    )
    assert g["cardRight"] > g["clientWidth"], (
        "the closed card no longer sits past the right edge — if the drawer "
        "stopped being a drawer, retire this test rather than adjusting it"
    )


def test_no_horizontal_scroll_but_that_was_never_the_evidence(calc_dock_geometry):
    """Facts 1 and 2, kept: the clip is why fact 3 needed measuring at all."""
    for width, g in calc_dock_geometry.items():
        assert not g["hScroll"], f"the landing page scrolls horizontally at {width}px"
        assert g["clip"] in ("clip", "hidden"), (
            f"body overflow-x is {g['clip']!r} at {width}px. While it is clipped, "
            "'no horizontal scroll' cannot detect an element hanging off the "
            "right edge — which is why the test above measures the element."
        )
