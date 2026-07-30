"""Landing-page facts that only a running browser can establish (P2, 2026-07-30).

Three defects, one shape
------------------------

Each of the three things checked here was a value that existed in more than
one place, and each looked correct in every place it appeared:

1. **Kolam opacity.** ``styles.css`` set ``#kolam { opacity: .06 }``; the
   landing page's ``app.js`` animated an inline ``0.03 + 0.15 * envelope``,
   peaking at .18, and pinned .16 under reduced motion; a media query pinned
   .16 again. The same background element was three times stronger on one
   route than on the other two, and the seam showed on navigation. Nothing
   was individually wrong — there was simply no single number.

2. **The script cycler's language label.** ``.morph-row`` used
   ``align-items: baseline`` with a hand-tuned ``padding-bottom: 16px`` on the
   label. Tamil, Telugu, Kannada and Malayalam put their baseline at different
   heights within one font-size, so the label moved every 2.5 seconds — mid-
   glyph on the Malayalam frame, lower on the Kannada one.

3. **Placeholder copy in the hero.** A ``.draft-note`` div reading
   "Placeholder copy — written for the founder to rewrite in his own voice."
   rendered live, directly under the value proposition.

Why these are browser assertions and not greps over ``styles.css``: CLAUDE.md's
round-4 addendum. A grep proves the rule is written down. Only a measurement
proves the rendered output actually moved — and for the label, the measurement
has to be taken across *several frames of the animation*, because a single
sample would have passed on the broken version too.

Running it
----------

Dev-only, same as ``test_web_wizard_layout.py``; skips rather than fails::

    python -m http.server 3000 --directory web
"""

from __future__ import annotations

import socket

import pytest

WEB_ORIGIN = "http://localhost:3000"
ROUTES = ("index.html", "onboarding.html", "dashboard.html")

pytestmark = pytest.mark.web


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def _playwright():
    return pytest.importorskip(
        "playwright.sync_api",
        reason="playwright is a dev-only dependency; see requirements-dev.txt",
    )


# --------------------------------------------------------------------------
# 1. One kolam, one strength.
# --------------------------------------------------------------------------

KOLAM = """() => {
  const k = document.getElementById('kolam');
  return {
    token: getComputedStyle(document.documentElement)
             .getPropertyValue('--kolam-opacity').trim(),
    computed: parseFloat(getComputedStyle(k).opacity),
  };
}"""


def test_the_kolam_never_exceeds_its_token_on_the_landing_page():
    """Sampled across a full breathing cycle, not once.

    The landing page still animates — that is the point of the background —
    so the assertion is about the ENVELOPE: the held peak must equal the token
    the other two routes render at, and nothing in the cycle may exceed it.
    A single sample taken at a trough would have passed before the fix, when
    the peak was .18 against a .06 token.
    """
    playwright = _playwright()
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        page.wait_for_timeout(600)
        token = float(page.evaluate(KOLAM)["token"])
        # The envelope's cycle is 11s (web/app.js); 12s of sampling covers a
        # whole one from any starting phase, including the hold at the top.
        samples = []
        for _ in range(80):
            samples.append(page.evaluate(KOLAM)["computed"])
            page.wait_for_timeout(150)
        browser.close()

    peak = max(samples)
    assert peak <= token + 1e-6, (
        f"the landing kolam peaks at {peak} against a --kolam-opacity of "
        f"{token}. web/app.js must multiply the token by its 0..1 envelope, "
        "not carry its own opacity range."
    )
    assert peak == pytest.approx(token, abs=0.005), (
        f"the landing kolam never reaches its token (peak {peak} vs {token}); "
        "the envelope is not reaching 1, so the shared value is not what this "
        "route actually shows"
    )


def test_every_route_renders_the_kolam_at_one_strength():
    """The seam this closes: .06 on two routes, .18 at peak on the third.

    JavaScript off. Onboarding and the dashboard take the token straight from
    the stylesheet, and with JS off the landing page does too — so this
    measures the CSS agreement, and the test above measures what the landing
    page's script then does with it.
    """
    playwright = _playwright()
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")

    seen = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1600, "height": 950}, java_script_enabled=False
        )
        page = context.new_page()
        for route in ROUTES:
            page.goto(f"{WEB_ORIGIN}/{route}", wait_until="load")
            seen[route] = page.evaluate(KOLAM)
        browser.close()

    values = {r: g["computed"] for r, g in seen.items()}
    assert len(set(values.values())) == 1, (
        f"the kolam renders at more than one opacity across routes: {values}"
    )
    tokens = {r: g["token"] for r, g in seen.items()}
    assert len(set(tokens.values())) == 1, f"--kolam-opacity differs: {tokens}"


# --------------------------------------------------------------------------
# 2. The language label holds still while the script under it changes.
# --------------------------------------------------------------------------

MORPH = """() => {
  const w = document.getElementById('morphWord');
  const l = document.getElementById('morphLang');
  const wr = w.getBoundingClientRect(), lr = l.getBoundingClientRect();
  return {
    lang: l.textContent,
    labelBottom: Math.round(lr.bottom * 10) / 10,
    labelLeft: Math.round(lr.left * 10) / 10,
    // The distance from the word's own box bottom, which is what "anchored to
    // the glyph's bounding box" means: line-height .96 makes that box exactly
    // .96em tall whatever script is in it, so this delta is script-independent
    // by construction -- unlike a baseline, which is a font metric.
    deltaFromWordBox: Math.round((wr.bottom - lr.bottom) * 10) / 10,
  };
}"""


def test_the_language_label_holds_position_across_all_four_scripts():
    """Measured across frames, because the defect only exists between frames.

    The cycler holds each script for 2.5s and cross-fades in 520ms, so ~26
    samples at 420ms covers every script several times. Before the fix, a
    baseline-aligned label sat at a different Y on each of the four.
    """
    playwright = _playwright()
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")

    frames: dict[str, list[dict]] = {}
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        page.wait_for_timeout(500)
        for _ in range(26):
            m = page.evaluate(MORPH)
            frames.setdefault(m["lang"], []).append(m)
            page.wait_for_timeout(420)
        browser.close()

    assert set(frames) == {"Tamil", "Telugu", "Kannada", "Malayalam"}, (
        f"the cycler did not reach all four scripts in the sampled window: "
        f"{sorted(frames)} — the sampling, not the layout, is what failed"
    )

    bottoms = {lang: sorted({f["labelBottom"] for f in fs}) for lang, fs in frames.items()}
    distinct = {b for bs in bottoms.values() for b in bs}
    assert len(distinct) == 1, (
        "the language label sits at more than one Y as the script cycles: "
        f"{bottoms}. Anchor it to the word's box (align-items: flex-end), not "
        "to a baseline that every font places differently."
    )

    deltas = {lang: sorted({f["deltaFromWordBox"] for f in fs}) for lang, fs in frames.items()}
    distinct_deltas = {d for ds in deltas.values() for d in ds}
    assert len(distinct_deltas) == 1, (
        f"the label's offset from the word's own box varies by script: {deltas}"
    )


# --------------------------------------------------------------------------
# 3. No draft copy in a shipped hero.
# --------------------------------------------------------------------------


def test_no_placeholder_copy_renders_in_the_hero():
    """The .draft-note div is gone, and so is the class that styled it.

    Both halves matter: the element check fails if it comes back, and the text
    check fails if the same sentence returns under a different class name.
    """
    playwright = _playwright()
    if not _listening("localhost", 3000):
        pytest.skip(f"no static server on {WEB_ORIGIN}")

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 950})
        page.goto(f"{WEB_ORIGIN}/index.html", wait_until="networkidle")
        page.wait_for_timeout(600)
        found = page.evaluate(
            """() => ({
              nodes: document.querySelectorAll('.draft-note').length,
              text: document.body.innerText,
            })"""
        )
        browser.close()

    assert found["nodes"] == 0, "the .draft-note placeholder is back in the hero"
    for phrase in ("Placeholder copy", "rewrite in his own voice"):
        assert phrase not in found["text"], (
            f"draft copy is rendering on the landing page: {phrase!r}"
        )
