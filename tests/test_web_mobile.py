"""The three routes on a phone: measured, not assumed (mobile-ui, 2026-10-17).

Every view a person passes through -- the landing page, all six wizard steps,
the dashboard before and after a plate is solved -- is loaded at three phone
widths (320, 375 and 414px) in a touch-emulating browser, and measured.

Why every check measures an element and never the page's scroll width:
``body { overflow-x: clip }`` means no amount of overflow can produce a
horizontal scrollbar, so ``scrollWidth == clientWidth`` is evidence that
overflow is hidden, not that content fits (DESIGN_SYSTEM.md, known
inconsistency 0). Before this file, every view already reported "no horizontal
scroll" at all three widths while the landing page's quality card overhung its
column by 16px at 320.

Running it
----------

Needs both dev servers; skips rather than fails without them, like the other
browser tests (``FOODAI_WEB_TESTS=required`` turns the skip into a failure)::

    python -m http.server 3000 --directory web
    uvicorn api.main:app --port 8000
"""

from __future__ import annotations

import socket

import pytest

WEB_ORIGIN = "http://localhost:3000"
API_ORIGIN = "http://localhost:8000"
PHONE_WIDTHS = (320, 375, 414)

pytestmark = pytest.mark.web


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


MEASURE = r"""() => {
  const vw = document.documentElement.clientWidth;
  const name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id :
    (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/)[0] : ''));
  const shown = el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const out = {grid_overhang: [], small_targets: [], small_inputs: [], tiny_text: []};

  // A grid's children must stay inside the grid. A fixed column minimum wider
  // than the column is the defect this catches, on any grid, present or future.
  for (const g of document.querySelectorAll('*')) {
    if (!shown(g) || getComputedStyle(g).display !== 'grid') continue;
    const gr = g.getBoundingClientRect();
    for (const c of g.children) {
      if (!shown(c)) continue;
      const r = c.getBoundingClientRect();
      if (r.right > gr.right + 0.5 || r.left < gr.left - 0.5)
        out.grid_overhang.push(`${name(c)} in ${name(g)}: child ${Math.round(r.left)}..${Math.round(r.right)}, grid ${Math.round(gr.left)}..${Math.round(gr.right)}`);
    }
  }

  // Tap targets. A radio or checkbox is tapped through its label; a text box
  // inside .ob-input-unit is tapped through the whole unit (the label wraps it).
  // The calculator's two inline number boxes sit inside a sentence and are
  // exempt by name: their height is the sentence's line height.
  const targets = document.querySelectorAll(
    'a[href], button, summary, select, input:not([type=hidden]), textarea');
  for (const el of targets) {
    if (!shown(el)) continue;
    if (el.closest('.calc-sentence')) continue;
    let box = el;
    if ((el.type === 'radio' || el.type === 'checkbox') && el.closest('label')) box = el.closest('label');
    else if (el.closest('.ob-input-unit')) box = el.closest('.ob-input-unit');
    const r = box.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.height < 44 || r.width < 24)
      out.small_targets.push(`${name(box)} "${(box.textContent || el.value || '').trim().slice(0, 24)}" ${Math.round(r.width)}x${Math.round(r.height)}`);
  }

  // iOS Safari zooms the page when a text box under 16px takes focus.
  for (const el of document.querySelectorAll('input:not([type=hidden]):not([type=radio]):not([type=checkbox]), select, textarea')) {
    if (!shown(el)) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 16) out.small_inputs.push(`${name(el)} ${fs}px`);
  }

  // Visible text below the design system's 11px floor (eyebrow/label row).
  for (const el of document.body.querySelectorAll('*')) {
    if (!shown(el)) continue;
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 11) out.tiny_text.push(`${name(el)} ${fs}px "${el.textContent.trim().slice(0, 24)}"`);
  }

  const segs = [...document.querySelectorAll('.ob-progress2-seg')].filter(shown);
  // Rows by vertical overlap, not by equal tops: a taller current pill beside
  // short number circles has a different top on the same row.
  out.stepper_rows = null;
  if (segs.length) {
    const rs = segs.map(e => e.getBoundingClientRect()).sort((a, b) => a.top - b.top);
    let rows = 1, bottom = rs[0].bottom;
    for (const r of rs.slice(1)) {
      if (r.top >= bottom - 0.5) { rows += 1; bottom = r.bottom; } else bottom = Math.max(bottom, r.bottom);
    }
    out.stepper_rows = rows;
  }
  const hi = document.querySelector('.header-inner');
  out.header_height = hi ? Math.round(hi.getBoundingClientRect().height) : null;
  const t = document.getElementById('calcToggle');
  if (t) { const r = t.getBoundingClientRect(); out.calc_toggle = {w: Math.round(r.width), h: Math.round(r.height), gap_below: Math.round(innerHeight - r.bottom)}; }
  return out;
}"""

LOGIN = """async ([email, password]) => {
  const j = {'Content-Type': 'application/json'};
  let r = await fetch('http://localhost:8000/api/auth/signup', {method: 'POST',
    credentials: 'include', headers: j, body: JSON.stringify({email, password})});
  if (!r.ok) await fetch('http://localhost:8000/api/auth/login', {method: 'POST',
    credentials: 'include', headers: j, body: JSON.stringify({email, password})});
  await fetch('http://localhost:8000/api/profile', {method: 'PUT',
    credentials: 'include', headers: j, body: JSON.stringify({
      age_years: 31, sex: 'male', weight_kg: 70, height_cm: 175,
      activity: 'moderate', goal: 'maintain', diet: 'vegetarian',
      clinical_flags: [], eats_snack: true})});
}"""


@pytest.fixture(scope="module")
def phone_views() -> dict[tuple[int, str], dict]:
    """Every view at every phone width, measured once."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN} (python -m http.server 3000 --directory web)")
    if not _listening("localhost", 8000):
        pytest.skip(f"no API on {API_ORIGIN}; steps 5-6 and the dashboard need it")

    views: dict[tuple[int, str], dict] = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        for width in PHONE_WIDTHS:
            ctx = browser.new_context(
                viewport={"width": width, "height": 800}, is_mobile=True, has_touch=True)
            page = ctx.new_page()
            page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
            page.wait_for_timeout(800)
            views[(width, "landing")] = page.evaluate(MEASURE)

            page.goto(f"{WEB_ORIGIN}/onboarding.html", wait_until="networkidle")
            page.wait_for_timeout(600)
            for step in range(1, 7):
                if step == 5:
                    # Step 5 fills from POST /api/targets; the sources panel is
                    # opened so its contents are measured too.
                    page.wait_for_selector("#obNext:not([disabled])", timeout=20000)
                    page.evaluate("() => { const d = document.getElementById('obScienceExpander');"
                                  " if (d) d.open = true; }")
                    page.wait_for_timeout(900)
                views[(width, f"wizard_step{step}")] = page.evaluate(MEASURE)
                if step == 6:
                    break
                page.wait_for_selector("#obNext:not([disabled])", timeout=20000)
                page.click("#obNext")
                page.wait_for_timeout(600)

            page.evaluate(LOGIN, [f"mobile-check-{width}@example.com", "mobile-pw-55102"])
            page.goto(f"{WEB_ORIGIN}/dashboard.html", wait_until="networkidle")
            page.wait_for_timeout(1200)
            views[(width, "dashboard")] = page.evaluate(MEASURE)
            page.click("#dashGenerate")
            page.wait_for_selector("#obPlanMeals .dash-dish-swap select", timeout=20000)
            page.wait_for_timeout(600)
            views[(width, "dashboard_after_plan")] = page.evaluate(MEASURE)
            ctx.close()
        browser.close()
    return views


def _collect(views, key):
    return {f"{w}px {v}": m[key] for (w, v), m in views.items() if m[key]}


def test_every_view_was_reached(phone_views):
    """A sweep that silently covered fewer views would pass and mean nothing."""
    assert len(phone_views) == len(PHONE_WIDTHS) * 9, sorted(phone_views)


def test_no_grid_child_overhangs_its_grid(phone_views):
    """Measured before the fix at 320px: the landing page's .science-grid had a
    300px column minimum in a 284px column, so .quality-card ran 16px past the
    column's right edge -- inside the viewport, so no scroll check saw it."""
    bad = _collect(phone_views, "grid_overhang")
    assert not bad, f"grid children past their grid's edge: {bad}"


def test_every_tap_target_is_at_least_44px_tall(phone_views):
    """44px is the platform guidance for a fingertip (Apple HIG; WCAG 2.5.5).
    Width is held only to WCAG 2.5.8's 24px: the seven day buttons of the
    activity step share one row, and at 320px seven 44px buttons do not fit.

    Measured before the fix at 375px: header buttons 36px, the brand 35px,
    the wizard's choice pills 35px, the account tabs 40px, the sources
    toggle 34px, the dashboard's swap boxes 31px, "Remove" 25px and the
    landing footer links 18px."""
    bad = _collect(phone_views, "small_targets")
    assert not bad, f"tap targets under 44px tall (or 24px wide): {bad}"


def test_the_header_stays_one_row(phone_views):
    """DESIGN_SYSTEM.md: every route's header is one 64px row. Taller tap
    targets must not cost a second row; at 320px the landing page's two
    buttons used to wrap under each other."""
    bad = {k: h for (w, v), m in phone_views.items()
           if (h := m["header_height"]) is not None and h > 64
           for k in [f"{w}px {v}"]}
    assert not bad, f"header taller than one 64px row: {bad}"


def test_no_text_box_makes_the_phone_zoom(phone_views):
    """iOS Safari zooms the whole page when a text box under 16px takes focus,
    and does not zoom back out. Measured before the fix: the wizard's number
    boxes 15px, the account email/password 15px, the early-access email 14px,
    the dashboard's swap boxes 13px."""
    bad = _collect(phone_views, "small_inputs")
    assert not bad, f"text boxes under 16px on a phone: {bad}"


def test_no_visible_text_under_11px(phone_views):
    """DESIGN_SYSTEM.md's floor is the 11px uppercase eyebrow. Measured before
    the fix: the wizard's six step labels shrank to 9px under 560px, to keep
    six labelled pills on two rows."""
    bad = _collect(phone_views, "tiny_text")
    assert not bad, f"visible text under 11px: {bad}"


def test_the_step_bar_is_one_row_on_a_phone(phone_views):
    """With readable labels the six pills would take three rows at 320px, so
    on a phone only the current step keeps its label; the others show their
    number. Before the fix: two rows at every phone width."""
    rows = {f"{w}px {v}": m["stepper_rows"] for (w, v), m in phone_views.items()
            if m["stepper_rows"] is not None}
    assert rows, "no view showed the step bar"
    bad = {k: r for k, r in rows.items() if r != 1}
    assert not bad, f"step bar on more than one row: {bad}"


def test_the_closed_calculator_tab_is_small_on_a_phone(phone_views):
    """Closed, the landing page's calculator tab sat on the right edge as a
    vertical rail 40px wide and 267px tall, over the hero text ("planned
    around yo|", "free, everywher|" were cut by it at 320px). On a phone it
    is a single-line pill in the bottom corner. The open drawer's fit is
    tests/test_web_wizard_layout.py::test_the_open_calculator_dock_fits_the_viewport."""
    sizes = {w: m["calc_toggle"] for (w, v), m in phone_views.items() if v == "landing"}
    assert len(sizes) == len(PHONE_WIDTHS), sizes
    bad = {w: s for w, s in sizes.items() if s["h"] > 48}
    assert not bad, f"closed calculator tab taller than one 48px line: {bad}"
    # In the corner, not floating: the first version of the pill stacked the
    # closed (0px-wide but full-height) drawer BELOW it and sat ~300px up the
    # screen, over the hero buttons. Height alone passed that.
    floating = {w: s for w, s in sizes.items() if s["gap_below"] > 32}
    assert not floating, f"closed calculator tab is not in the bottom corner: {floating}"


#: Short screens: the smallest phone upright, and a phone on its side.
SHORT_SCREENS = ((320, 568), (740, 360))


@pytest.fixture(scope="module")
def signup_modal() -> dict[tuple[int, int], dict]:
    """The sign-up box opened from the landing header, on short screens."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")
    out = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        for w, h in SHORT_SCREENS:
            ctx = browser.new_context(viewport={"width": w, "height": h}, is_mobile=True, has_touch=True)
            page = ctx.new_page()
            page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
            page.wait_for_timeout(600)
            page.tap("#hdrSignup")
            page.wait_for_timeout(500)
            out[(w, h)] = page.evaluate("""() => {
              const o = document.querySelector('.modal-overlay');
              o.scrollTop = 0;
              const m = document.querySelector('.modal').getBoundingClientRect();
              const c = document.querySelector('.modal-close').getBoundingClientRect();
              return {modal_top: Math.round(m.top), modal_gap_below: Math.round(innerHeight - m.bottom),
                      close_top: Math.round(c.top),
                      close_w: Math.round(c.width), close_h: Math.round(c.height),
                      fits: m.height <= innerHeight, can_scroll: o.scrollHeight > o.clientHeight
                        && ['auto', 'scroll'].includes(getComputedStyle(o).overflowY)};
            }""")
            ctx.close()
        browser.close()
    return out


def test_the_signup_box_can_be_closed_on_a_short_screen(signup_modal):
    """On a phone on its side (740x360) the box is 483px tall. It was centred
    in a non-scrolling overlay, so its top -- with the close button -- sat at
    y=-62, above the screen, with no way to scroll to it."""
    bad = {}
    for size, g in signup_modal.items():
        if g["close_top"] < 0 or g["modal_top"] < 0:
            bad[size] = g
        elif not g["fits"] and not g["can_scroll"]:
            bad[size] = g
    assert not bad, f"sign-up box top or close button off screen and unreachable: {bad}"
    # ...and where it does fit, it is still centred, as it always was.
    off = {s: g for s, g in signup_modal.items()
           if g["fits"] and abs(g["modal_top"] - g["modal_gap_below"]) > 2}
    assert any(g["fits"] for g in signup_modal.values()), (
        "no screen here fits the box, so the centring check below checks nothing")
    assert not off, f"sign-up box fits but is not centred: {off}"


def test_the_signup_close_button_is_44px(signup_modal):
    """The sweep above never sees the box (it is hidden until opened). Its
    close button was 34x34."""
    bad = {s: (g["close_w"], g["close_h"]) for s, g in signup_modal.items()
           if g["close_w"] < 44 or g["close_h"] < 44}
    assert not bad, f"close button under 44px: {bad}"


def test_a_phone_on_its_side_keeps_most_of_the_screen_for_content():
    """At 740x360 the sticky header (64px) and the wizard's sticky Continue bar
    (76px) left 219 of 360px for the form while scrolling -- 61%. On a short
    screen the header now scrolls away with the page; Continue stays pinned,
    because it is the action. Measured scrolled 300px into step 4 (the
    longest step before the targets), where the header used to stay put."""
    playwright = pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 740, "height": 360}, is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.goto(f"{WEB_ORIGIN}/onboarding.html", wait_until="networkidle")
        page.wait_for_timeout(500)
        for _ in range(3):
            page.wait_for_selector("#obNext:not([disabled])", timeout=20000)
            page.tap("#obNext")
            page.wait_for_timeout(500)
        g = page.evaluate("""() => {
          document.documentElement.style.scrollBehavior = 'auto';
          window.scrollTo(0, 300);
          const h = document.querySelector('.site-header').getBoundingClientRect();
          const n = document.querySelector('.ob-nav').getBoundingClientRect();
          return {header_bottom: Math.max(0, h.bottom), nav_top: n.top, inner: innerHeight, scrolled: scrollY};
        }""")
        browser.close()
    assert g["scrolled"] >= 300, f"step 4 was too short to scroll 300px: {g}"
    free = (g["nav_top"] - g["header_bottom"]) / g["inner"]
    assert free >= 0.7, f"only {free:.0%} of a 360px-tall screen is left for content: {g}"
