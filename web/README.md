# web/ — Arusuvai landing page

Static landing page for the Arusuvai meal planner, ported from the Claude
Design canvas (`Arusuvai Landing.dc.html` in the "Arusuvai Landing Page
Design" project) to a self-contained page with no proprietary runtime and no
build step.

```
web/
  index.html       landing page markup (semantic, class-based)
  onboarding.html  the form that calls POST /api/targets — see below
  onboarding.js    fetch + render for onboarding.html; computes nothing
  styles.css       palette, type, layout, motion (shared by both pages)
  app.js           landing-page vanilla-JS behaviour (no framework)
  assets/          plate photos — see assets/README.md
```

## Run

`index.html` is a self-contained static page — any static server, or opening
it directly, works:

```bash
python -m http.server 8000 --directory web
# then open http://localhost:8000
```

`onboarding.html` additionally needs the real API running, on a **different**
port than the page itself (browsers treat different ports as different
origins, and `api/main.py`'s CORS list is scoped to exactly `:3000` and
`:8000` for the page, expecting the API on `:8000` when the page is on
`:3000`, or vice versa — see the comment in `api/main.py`):

```bash
uvicorn api.main:app --reload              # API on :8000
python -m http.server 3000 --directory web # page on :3000
# then open http://localhost:3000/onboarding.html
```

Opening `index.html` directly (no server) works too, for the landing page
only; the Google Fonts and the plate images are the only external requests.
`onboarding.html` needs an HTTP origin (not `file://`) for `fetch()` to carry
a matchable `Origin` header to the API's CORS check.

## What it does

- **Morphing headline** — cycles the word for *taste* across South Indian
  scripts (Tamil → Telugu → Kannada → Malayalam), resolving on Tamil அறுசுவை.
- **Breathing kolam background** — a woven pulli-and-line dot grid drawn in
  SVG that draws itself in, holds, then unravels on an 11 s loop.
- **Protein calculator dock** — a slide-out illustrative demo (weight × a
  published g/kg factor). See the note below.
- **Six-food bloom**, **FAQ accordion**, **auth modal**, **sticky header**.
- Honours `prefers-reduced-motion`: the kolam settles static, the bloom shows
  immediately, and the headline swaps without a fade.

## `onboarding.html` — the first page that does something real

A form (body, activity, goal, diet, disclosed clinical conditions) that POSTs
straight to `/api/targets` and renders the response. Unlike the calculator
dock on the landing page, **nothing here is illustrative**: every figure shown
is a field read off the JSON response, formatted (rounded) for display but
never recomputed. `onboarding.js`'s own docstring states this as the file's
central constraint.

Renders, from the real response: the energy interval (point + `±%`, matching
`DESIGN_SYSTEM.md`'s number-display rule — no boxed stat grid), the
DIAAS-quality-adjusted protein target, fat/carb/fibre/sodium, the `dev_mode`
status pill and its one-line disclosure, every `warnings` entry (including the
clinical-flags disclosure from `docs/methodology.md`, "Clinical flags do not
tighten a target" — checking a condition does not change the sodium number,
and the page says so rather than leaving that silent), and a collapsible
source list (`<details>`) with each constant's citation, grade, DOI and
verification state.

Failure states are explicit, not swallowed: a network failure (API not
running) shows a message naming the exact command to start it; a 422 shows the
API's own validation detail.

## Relationship to CLAUDE.md

CLAUDE.md scopes `web/` as "Next.js. Displays. Never computes nutrition." Two
deliberate deviations, both noted so a future migration is clean:

1. **Not Next.js.** The source design is a single vanilla-JS page with no
   React; a static port is the faithful, dependency-free equivalent. The
   markup is class-based and drops cleanly into a Next route later.
2. **The calculator computes a number.** It is an *illustrative* landing-page
   demo using a public rule of thumb (Morton et al.), not the product's target
   engine — every figure on the page is labelled illustrative, and the real,
   citation-backed targets are determined deterministically in
   `core/nutrition`, never in the browser. The invariant that the web layer
   never determines a quantity a user *relies on* is preserved.
