# web/ — Arusuvai landing page

Static landing page for the Arusuvai meal planner, ported from the Claude
Design canvas (`Arusuvai Landing.dc.html` in the "Arusuvai Landing Page
Design" project) to a self-contained page with no proprietary runtime and no
build step.

```
web/
  index.html       landing page markup (semantic, class-based)
  onboarding.html  steps 1-5 (no account needed) + step 6, the account/save hinge
  onboarding.js    fetch + render for onboarding.html; computes nothing
  dashboard.html   auth-gated: saved profile + plate picker + POST /api/plan
  dashboard.js     fetch + render for dashboard.html; computes nothing
  auth.js          shared signup/login/logout/session calls + auth-modal wiring
  styles.css       palette, type, layout, motion (shared by all pages)
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
- **Six-food bloom**, **FAQ accordion**, **sticky header**.
- Honours `prefers-reduced-motion`: the kolam settles static, the bloom shows
  immediately, and the headline swaps without a fade.
- **Auth modal — real, not decorative** (since 2026-07-25). The header's
  Sign in/Sign up buttons open the same modal onboarding.html/dashboard.html
  use, wired to the real `POST /api/auth/signup`/`login` via `web/auth.js`.
  Landing-page signup never attaches a profile (there isn't one to attach),
  so the destination after auth is chosen by what's actually on file, not a
  fixed redirect: a fresh signup or a returning account with no saved profile
  goes to `onboarding.html`; a returning sign-in with a saved profile goes
  straight to `dashboard.html`. Signed-in visitors see their email plus
  Dashboard/Log out in the header instead of Sign in/Sign up.

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

Steps 1-5 need no account — anyone can walk through body/activity/goal/diet
and see a real target. Step 6 is the account/save hinge: create an account or
sign in, the just-completed profile is persisted against the resulting
`user_id` (`PUT /api/profile`, or attached to `POST /api/auth/signup`
directly), and the page hands off to `dashboard.html`. A signed-in visitor
who returns to `onboarding.html` is prefilled from their saved profile
(`GET /api/profile`) and dropped straight at step 5 rather than five blank
steps — see `docs/methodology.md`, "Accounts and persistence: scope".

**Reworked 2026-07-25** to port the visual design from the Claude Design
canvas `Arusuvai Onboarding.dc.html` (kolam background, a six-segment progress
bar, card/pill selectors instead of native `<select>`s, a one-sentence target
summary). The canvas's own `Component.compute()` computes BMR/TDEE/macros in
the browser — a fine shortcut for a visual mockup, but exactly the thing
CLAUDE.md's central invariant forbids in this codebase (nutrition computed
outside `core/`). Only the layout and interaction language were ported; every
number on the page still comes from a real `POST /api/targets` response,
and step 6's tabbed "Create account / Sign in" form calls the real
`/api/auth/*` endpoints directly rather than opening the shared auth modal
(which `index.html` still uses). A cold `?next=dashboard` visit (bounced back
by `dashboard.html`'s auth gate) lands directly on step 6 with "Sign in"
pre-selected instead of popping a modal.

## `dashboard.html` — the account-gated page

Requires an authenticated session; an unauthenticated visitor is redirected
to `onboarding.html?next=dashboard` rather than shown any dashboard content.
Renders the saved profile (`GET /api/profile`) and the plate-picker +
`POST /api/plan` flow that used to live in onboarding's step 6 — moved here
verbatim, not rewritten, per this increment's brief not to touch the
plan-call/decline logic. Success and honest-decline are still both real,
designed states, not an error path either way.

**Reworked 2026-07-25** to port the visual design from the Claude Design
canvas `Arusuvai Dashboard.dc.html` (kolam background, tag pills for the
saved profile's diet/goal, a serif headline+sentence, a "why we stopped"
callout for the decline state). Two things in the canvas were deliberately
**not** ported, because porting them would have overclaimed what the real
engine does:

- The canvas mocks a fabricated three-meal day (breakfast/lunch/dinner) with
  a day total. `core.planner.plan.plan_meal` solves one `(region, meal_slot)`
  plate per call, not a day, and there is no real template yet for e.g.
  "north_indian breakfast" — see CLAUDE.md's build-status table. The real
  page still solves and shows one plate at a time.
- The canvas's "Plan outcome" pill switcher (toggling between a fabricated
  success state and a fabricated decline state) is a design-prototyping
  affordance, not a feature. This page's success/decline state is whichever
  outcome the real `POST /api/plan` call actually returns.

The decline callout's bullet list is `data.violations` verbatim from that
response — never the canvas's own hardcoded per-condition copy (its demo
text about a fictional "priya@email.com" hitting a chronic-kidney-disease
protein cap describes its mock profile, not whatever profile actually
declines on this page).

## `auth.js` — shared by `onboarding.html` and `dashboard.html`

`signup`/`login`/`logout`/`me`/`getProfile`/`saveProfile` wrappers around the
five `/api/auth/*` and `/api/profile` endpoints (all `credentials: "include"`,
required for the signed session cookie to survive the cross-port fetch
between the static page and the API — see `api/main.py`'s CORS comment), plus
`initAuthModal()`, which wires the auth-modal markup originally added to
`index.html` as a decorative demo (`DESIGN_SYSTEM.md`'s "Auth modal" row) to
these real calls. `index.html`'s own modal is untouched and still decorative.

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
