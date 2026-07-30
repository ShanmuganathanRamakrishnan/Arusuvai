# DESIGN_SYSTEM.md

Visual and interaction consistency for every Arusuvai page. Sibling to
`CLAUDE.md`, same auto-loaded status, different scope: `CLAUDE.md` governs
architecture and nutritional invariants; this file governs how pages look and
behave. **Every new page is checked against this file before it is considered
done.**

This file was extracted from what actually shipped — `web/styles.css`,
`web/index.html`, `web/app.js` — not from the design brief. Where the brief
(`uploads/arusuvai_design_brief.md`) and the shipped page disagree, **the
shipped page wins and the brief is stale.** Do not invent new values; if a
page needs something not listed here, add it here in the same change, sourced
from real code.

Line references below point at `web/styles.css` unless noted; they were
current at extraction and should be re-confirmed if the file has moved since.

---

## Color tokens

Defined once as CSS custom properties in `:root` (`styles.css:9–24`). Use the
variable, never a re-typed hex.

| Token            | Hex / value            | Role                                             |
| ---------------- | ---------------------- | ------------------------------------------------ |
| `--cream`        | `#FBF6EC`              | Page base background                             |
| `--cream-card`   | `#FCF9F1`              | Card surface (slightly lifted off the base)      |
| `--cream-sink`   | `#F4ECD9`              | Recessed panel (e.g. `.quality-card`)            |
| `--ink`          | `#2B2622`              | Primary text (charcoal, not black)               |
| `--green`        | `#3A5A40`              | Banana-leaf green — primary brand / actions      |
| `--green-dark`   | `#2E4833`              | Green hover / pressed                            |
| `--amber`        | `#E0A526`              | **The one accent** — turmeric amber              |
| `--amber-deep`   | `#B98416`              | Amber for text/links on cream (contrast-safe)    |
| `--terracotta`   | `#C1694F`              | Secondary/tertiary only (e.g. a third dot)       |
| `--surface`        | `#FFFFFF`            | **Every** interactive control, whatever its shape |
| `--surface-page`   | `var(--cream)`       | The page itself                                   |
| `--surface-panel`  | `var(--cream-sink)`  | Read-only panels only (the citation box)          |
| `--border`         | `rgba(43,38,34,.16)` | Border on a `--surface` control                   |
| `--border-selected`| `var(--green)`       | Border on a **chosen** control                    |
| `--accent-selected`| `rgba(58,90,64,.08)` | Fill on a **chosen** control                      |
| `--accent-current` | `var(--amber-deep)`  | Stepper current-step marker — nothing else        |
| `--rule`         | `rgba(43,38,34,.08)`   | Hairline dividers between sections/cards          |
| `--error`        | `#B3392C`              | Form/API error states (`web/onboarding.html`)    |
| `--error-bg`     | `rgba(179,57,44,.08)`  | Error message background                         |

`--field` / `--field-border` were **removed 2026-07-29** and folded into
`--surface` / `--border`. They are listed here only so an old reference is
recognisable; do not reintroduce them. See "Surface and state are orthogonal"
below for why the split itself was the bug.

**State / derived colors** (not yet tokenized — see "Known inconsistencies"):

- Muted text: `rgba(43,38,34,.5–.72)` opacity ramp on `--ink` for sub-copy,
  captions, fine print. Common stops: `.72` (hero sub), `.68` (body), `.6`,
  `.55`, `.5` (captions), `.4` (finest print).
- Borders on inputs/cards: `rgba(43,38,34,.09–.16)`.
- Error/success: **`--error`/`--error-bg`, defined 2026-07-23** by
  `web/onboarding.html` (`.ob-error`) — the first page with a real submission
  failure state (an unreachable API, a 422). The early-access and auth forms
  still have no validation-error styling; when they get one, reuse these
  tokens rather than inventing a second pair.

**Surface and state are orthogonal. This is the load-bearing rule.**

Revised 2026-07-29 after the onboarding audit. The previous version of this
section said "controls sit above the page, cards sit within it" and gave
controls `--field` while cards kept `--cream-card`/`--cream-sink`. That rule
was followed exactly, and the flow still ended up with **one fill value
carrying two different meanings**: cream/tan said *"this is a card"* on the
activity and goal cards, while a green tint said *"this is selected"* on the
very same component — and the day picker said *selected* a third way, solid
green with white text. Three selected dialects on one flow, plus a surface
colour doing double duty.

The token layer itself encoded the split that caused it: `--field` said "text
input" specifically, so a radio card was never covered by it and was free to
pick its own fill — and did. The rule now:

1. **`--surface` (white) is every interactive control**, regardless of shape —
   text input, radio card, pill, checkbox card, toggle, day button. If a user
   can click or type in it, it is white.
2. **Cream/tan survives only on non-interactive panels.** In the wizard that
   is exactly one element: the "Why these numbers?" citation box
   (`--surface-panel`).
3. **Exactly one selected treatment**, everywhere: `--accent-selected` fill +
   `--border-selected` 1.5px border + the native indicator filled via
   `accent-color`. Implemented as a single `.ob-selectable` component with one
   declaration block; a grep for the state returns one class, `.is-selected`.
   The solid-dark-green-with-white-text treatment is **deleted** — it was
   heavier than every other selected state and read as a button, not a choice.
4. **Selection indicators go on the LEFT**, on every selection control in the
   flow. Circles for single-select, squares only where multi-select is
   genuinely allowed (the clinical-conditions group). They used to be
   left-inside on the pills and absolutely positioned top-right on the cards.

The one exception to (1) is `.modal label input`, which stays on
`--cream-card` because it already sits on a modal card rather than on the
page. Do not reach for a shadow to separate a control — the border does it,
per the header-rule restraint below.

**The one-accent rule, and amber's single meaning.** `--amber` is the single
primary accent, used *sparingly, one thing at a time*. On the landing page it
marks exactly one focal element per viewport — the hero credibility dot, the
FAQ `+`/`×` sign, the "Notify me" button, a dotted underline on one emphasized
phrase.

**In the onboarding wizard, amber has exactly one job: marking the current
step in the stepper** (`--accent-current`). Tightened 2026-07-29 — it had also
been tinting the `dev_mode` badge and inline numbers in step 5's prose, so on
one screen amber meant "you are here", "this data is provisional" and "this
number matters" at once, which means it signalled none of them. `dev_mode`
now gets a neutral bordered chip; emphasis inside prose gets **weight, not
colour**. Do not reintroduce amber anywhere in the flow.

It is **not** a fill for buttons (those are `--green`), not applied to
multiple competing elements on one screen. Green is the workhorse action
color; amber is the single spark. Terracotta is tertiary — it appears only as
the third item in a set of three (e.g. the third quality-list dot), never as a
standalone accent.

---

## Typography

Fonts loaded from Google Fonts (`index.html:8–10`), tokenized at
`styles.css:19–21`.

- **Serif** — headings, dish names, the calculator sentence:
  `'Spectral', Georgia, serif` (`--serif`). Weights 400/500/600 + 400 italic.
- **Sans** — body, UI, numbers: `'Hanken Grotesk', system-ui, sans-serif`
  (`--sans`). Weights 400/500/600/700.
- **Tamil** — the brand wordmark, taste words, in-language dish names:
  `'Noto Serif Tamil', serif` (`--tamil`). This is a first-class pairing, not
  a fallback — Tamil sits *beside* the serif at heading scale, never shrunk to
  an afterthought.
- **Morphing headline only** loads four more scripts at 400/600 for the word
  swap: Noto Serif Telugu / Kannada / Malayalam. These are used *nowhere else*
  — do not reach for them in general layout.

Numbers use `--sans` with `font-variant-numeric: tabular-nums` wherever they
sit in a row that could shift (`.meal-card .stat`, `.day-total .num`).

**Type scale** — actual shipped sizes. Headings use `clamp(min, vw, max)` so
they breathe with viewport; the min/max are the real bounds.

| Role                        | Size                          | Family | Weight |
| --------------------------- | ----------------------------- | ------ | ------ |
| Hero morph word             | `clamp(44px, 7vw, 74px)`      | Tamil  | 600    |
| Hero H1 (`.hero-title`)     | `clamp(30px, 4.8vw, 50px)`    | serif  | 500    |
| Section H2 (bloom/how/etc.) | `clamp(24px, 3.4vw, 42px)`*   | serif  | 400    |
| Free-band statement         | `clamp(23px, 3.2vw, 34px)`    | serif  | 400    |
| Modal H2                    | `26px`                        | serif  | 500    |
| Card title (`.trad-name`)   | `23px`                        | serif  | —      |
| Quality-card H3             | `20px`                        | serif  | 400    |
| Step title / meal dish      | `19px` / `18px`               | serif  | —      |
| FAQ question                | `clamp(16px, 2vw, 19px)`      | serif  | —      |
| Hero sub-lede               | `clamp(16px, 1.7vw, 18px)`    | sans   | 400    |
| Body copy                   | `14.5px–15.5px`               | sans   | 400    |
| Small / caption             | `13.5px–14px`                 | sans   | —      |
| Fine print / illustrative   | `11.5px–12.5px`               | sans   | —      |
| Eyebrow / label (uppercase) | `11px–12px`, `letter-spacing .14–.18em`, `text-transform: uppercase` | sans | 600 |

\* Section H2 max varies by section (bloom 42px, traditions 38px, how/sample/
science/faq 36px, delivery 34px). See "Known inconsistencies" — these should
converge.

**Line-height:** headings `1.08–1.2`; body `1.5–1.65`. **Letter-spacing:**
negative only on the largest heading (`-.01em` on H1); positive tracking
(`.1–.18em`) only on uppercase eyebrows/labels.

---

## Spacing and layout

### The container token — one measure, every route

Revised 2026-07-29 (round 2). **There is exactly one container measure and one
container inset in this project, and no page, route or component may declare
its own.**

| Token             | Value                    | Role                                    |
| ----------------- | ------------------------ | --------------------------------------- |
| `--container-max` | `1280px`                 | The measure. Header, content and footer |
| `--container-pad` | `clamp(18px, 4vw, 44px)` | The horizontal inset                    |
| `--max`           | alias of `--container-max` | Kept as the name the sheet already used |

Derived by `.wrap` (`max-width` + `padding`) and `.header-inner` (same two,
plus its own vertical padding). Nothing else.

**What this replaced, and why it is a token rather than a per-page value.**
There were three measures: the landing page at 1240px, the wizard at its own
`--wizard-max: 1200px`, and the dashboard at `style="max-width: 1040px"` set
inline on its `.wrap` in `dashboard.html`. Each page was internally consistent,
so nothing looked wrong in isolation — except the dashboard, whose *header*
kept the global measure while its *content* took the inline override:

| Route             | Logo left | Content left |
| ----------------- | --------- | ------------ |
| Landing           | ~290px    | ~290px       |
| Onboarding step 1 | —         | ~325px       |
| Dashboard         | ~305px    | ~415px       |

A 110px misalignment inside a single page, with the brand visibly hanging off
the left of everything beneath it. Measured after the fix, at 1600px: logo,
content container and footer all at **x=204** on all three routes, with a
single container width of 1280px everywhere.

The previous version of this section blessed the wizard's separate measure on
editorial grounds ("1240px is a reading measure; the wizard places two columns
at opposite edges") and warned that a *third* value would mean the token had
stopped meaning anything. That warning was right and the exception was the
thing that made it come true — a second value is already a value that is not
the token. A page may change what it puts **inside** the container. It may not
change the container. Column count, gutters and content alignment inside the
grid are the levers; width is not.

**Enforcement.** `tests/test_web_wizard_layout.py::test_header_logo_shares_content_left_edge`
asserts brand-left == content-container-left on `index.html`, `onboarding.html`
and `dashboard.html`, and `::test_every_route_shares_one_container_width`
asserts one width across all three and their headers. Both run with JavaScript
disabled — the assertion is about CSS geometry, and with JS on the dashboard
redirects an unauthenticated visitor away, which would leave the worst route
untested. A grep for `--container-max` would have passed on the broken version
too, since `--max` existed and every page referenced *a* token.

### The wizard layout contract — one grid, six steps

Added 2026-07-29. **Every onboarding step renders into the same grid at the
same measure and the same vertical offset. No step may override its span, and
there is no per-step width variable to set.** Tokens:

| Token             | Value                      | Role                                      |
| ----------------- | -------------------------- | ----------------------------------------- |
| `--wizard-max`    | alias of `--container-max` | No longer a value of its own (round 2)    |
| `--wizard-gutter` | `32px`                     | Grid gutter                               |
| `--wizard-top`    | `72px`                     | Fixed offset below the header             |
| `--ob-nav-h`      | `76px`                     | Sticky action bar; reserved as step padding |

Classes: `.ob-grid12` (12 columns), `.ob-col-narrative` (columns 1–4),
`.ob-col-controls` (columns 6–12; column 5 is the optical gutter). Collapse
point **1100px**, below which the columns stack narrative-above-controls.

**`.ob-grid12` is the only layout grid in this project.** `.ob-step-grid` /
`.ob-step-intro` / `.ob-step-fields` — a `minmax(0,380px) minmax(0,1fr)` pair
— were deleted 2026-07-29 (round 2). The wizard had already left them because
that shape has no fixed column origin; the dashboard was allowed to keep them
on the reasoning that it is a single page with no step-to-step comparison to
preserve. That reasoning was wrong: on a single page the comparison that
matters is between the page and its own header, and the content-or-380px first
track is what put the dashboard's content column 110px right of its own logo.
`dashboard.html`'s plate picker now renders into `.ob-grid12` like every
wizard step, so its narrative column starts where the brand starts.

**Why this is a contract and not a convention.** The six steps were authored
independently and each sized itself, so two defects emerged that no individual
step's CSS was responsible for:

- The wizard **vertically centred** its content, which makes each step's Y a
  function of its own height. Measured: the stepper sat at 269 / 181 / 329 /
  167 / 122 / 251 px across steps 1–6, so the whole UI jumped on every
  Continue. Content is now **top-aligned** at `--wizard-top`. Do not
  reintroduce `justify-content: center` on `.ob-wizard` — that was a previous
  fix for a footer stranded mid-page, and it caused this. `.page-fill`'s
  `margin-top: auto` pins the footer without caring how tall a step is.
- Each step declared its own control-column width, so that column started at
  1037 / 845 / 975 / 866 / 893 px depending on the step, and the narrative
  column was a different width each time — which is why it read as dead space
  on steps 1, 3 and 6 and as a reasonable column on 2 and 4.

A step that needs a different internal shape changes **what it puts in a
column** (`.ob-two-up`, `.ob-stat-grid`, `.ob-goal-row.is-three`), never which
columns it spans.

**Enforced, not documented.** `tests/test_web_wizard_layout.py` drives a real
browser through all six steps and asserts the stepper Y and the control-column
X are single-valued. Per CLAUDE.md's round-4 addendum, a grep over `styles.css`
would have passed against both broken versions above; the test perturbs an
input (navigating between steps) and checks the measured output does not move.
It skips when playwright or the static server is absent.

**Step 5 renders into the same grid as the rest**, deliberately against the
letter of the correction brief, which asked for columns 1–5 / 7–12 for that one
step. That would put its second column at a different origin from every other
step's control column, contradicting both "no step overrides the span" and the
acceptance check requiring one control-column left edge across all six. The
citation panel instead gains width by sitting *under* the numbers in the
control column rather than beside them — which also removes its nested
scrollbar.

**Sticky bars must reserve their own height.** `.ob-nav` is
`position: sticky; bottom: 0` in the same scroll container as the step, so it
paints over the step's last element once the step is taller than the viewport
— measured on step 5, where it clipped the "Fibre & sodium" heading. `.ob-step`
carries `padding-bottom: var(--ob-nav-h)` so the bar floats over reserved space
instead of over content.

**The action bar is flat, not blurred.** It was
`rgba(251,246,236,.94)` + `backdrop-filter: blur(12px)`, which rendered as a
pinkish stripe (~`#FBF0EE`) against the `#FAF6EC` page: `#kolam` is a fixed
layer of amber dots, and blurring it through a near-opaque cream panel averages
those dots in as a warm cast. A band four units off the page colour reads as a
rendering artifact rather than a decision. It is now exactly
`--surface-page` with a single hairline.

**At most two hairlines in the lower region.** The wizard had three stacked:
the action bar's `border-top`, `.site-footer`'s, and `.footer-bottom`'s. On
pages where `.footer-bottom` is the footer's *only* child (onboarding,
dashboard) its rule is redundant with `.site-footer`'s, so
`.site-footer > .footer-bottom:only-child` drops it. On `index.html` the
footer holds a link grid above that row, so there the second rule is doing
real work and stays.

**Full-viewport pages pin their footer — use `.page-fill`.** A page whose
content can be shorter than the viewport must claim the height explicitly, not
pad its way there. `.page-fill` (on `<body>`) sets `min-height: 100dvh` +
flex column, gives `> .wrap` `flex: 1` **and `width: 100%`**, and pins the
footer with `margin-top: auto`. Applied to `onboarding.html` and
`dashboard.html`. Use `100dvh`, not `100vh`, so mobile browser chrome doesn't
push the footer below the fold.

Two traps this encodes, both measured rather than assumed:

- **Do not solve a mid-page footer with section padding.** Any value that fills
  a 1080px screen overflows a 720px one, and it must be re-tuned every time
  content changes. Measured before the fix: footer at y=513 on the signed-in
  dashboard's empty state, ~570px of bare cream below it.
- **A flex item with `margin: 0 auto` shrink-wraps to its content.** `.wrap`
  and `.ob-wizard-card` both centre themselves that way, so making an ancestor
  a flex column silently drops their `max-width` and collapses them to
  fit-content — measured at 1007px against a 1400px container, which read as
  "the page is still centred in a narrow column." Any element that centres with
  auto margins needs an explicit `width: 100%` once it becomes a flex item.

**Section vertical rhythm.** Most sections use `padding: clamp(50px, 7vw,
90px) 0`. Denser bands run smaller (`.free-band` `clamp(44px,6vw,72px)`,
`.delivery`/`.faq` same 50→90 family). Sections are separated by a top
hairline `border-top: 1px solid var(--rule)`; a section that should not carry
the rule gets `.no-rule` (hero, bloom).

**Spacing values in use** (px). There is no single enforced 4/8 scale, but the
de-facto set is: **6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 32, 36, 56**, plus
`clamp()` for section-scale gaps. Gaps between grid items: `clamp(18px, 2.5vw,
30px)` for step/meal grids, wider `clamp(24px, 4vw, 48px)` for traditions/
delivery/footer. Prefer an existing value over inventing a new one.

**Grids.** Multi-card sections use
`grid-template-columns: repeat(auto-fit, minmax(<Npx>, 1fr))` — the min column
width is the only knob: traditions `260px`, meals `250px`, science `300px`,
steps/facts `230–240px`, footer `190px`. The six-food bloom is the exception:
a centered flex-wrap of fixed `140px` cards, not a grid.

**Border-radius** (exact, shipped):

| Element                              | Radius        |
| ------------------------------------ | ------------- |
| Pills / buttons / tags / inputs-pill | `999px`       |
| Bloom card, meal card, calc card†    | `16px`        |
| Quality card                         | `18px`        |
| Traditions plate, early-access card  | `20px`        |
| Modal                                | `22px`        |
| Modal text input                     | `11px`        |
| Modal close (circle)                 | `50%`         |

† The calc card is `16px 0 0 16px` (flat right edge — it docks against the
screen edge). See "Known inconsistencies": cards do **not** currently share one
radius, and inputs use two different ones. Until that's resolved, match the
nearest existing component rather than picking a fresh number.

---

## Motion

Motion is **slow and warm; one element animates at a time.** No bounce, no
pop-in, no spring overshoot, no attention-seeking loops on content.

**Durations / easing actually in use:**

- **Hovers / color & background transitions:** `.3s ease` (the default across
  buttons, links, nav). Some smaller controls `.25s`.
- **Calc panel slide + bloom card reveal:** the one "considered" easing,
  `cubic-bezier(.22, .61, .36, 1)` — panel width `.42s`, bloom transform
  `.7s`, bloom opacity `.7s ease`.
- **Bloom stagger:** cards reveal in sequence at **80ms** steps
  (`nth-child` delays 0→400ms), one after another — never all at once.
- **Morph headline:** opacity cross-fade `.5s ease`, swapping every 2.5s.
- **FAQ accordion:** `max-height`/opacity `.4s ease`; the `+`→`×` sign rotates
  `.3s`.
- **Chevron on calc toggle:** rotate `.4s ease`.
- **Kolam background:** an 11s breathing cycle (draw-in → hold → unravel →
  rest), opacity ramping ~`0.03`→`0.18`; deliberately the slowest thing on the
  page and always behind content at low opacity.
- **Modal:** `ar-fadein .3s ease` on the overlay.
- **Onboarding step change:** `ob-step-in .3s ease` — opacity plus an 8px
  upward slide on the incoming `.ob-step`, and nothing else. **A step
  transition must not animate a box dimension or a scale.** The wizard
  previously also transitioned its `max-width` (`.45s`) as the per-step width
  envelope changed; that reflowed the incoming step's text repeatedly over the
  duration and read as the fields warping into place rather than appearing.
  Removed 2026-07-29 — the width now snaps and only the fade/slide is
  animated.
- **`ar-nudge`:** the only decorative loop — a 5px vertical nudge on the scroll
  cue, `2s ease-in-out infinite`. Reserved for a "scroll" affordance; do not
  apply it to content.

**`prefers-reduced-motion: reduce`** (`styles.css:403–408`) is mandatory on
every page: it collapses all animation/transition to `.001ms`, shows bloom
cards immediately, settles the kolam to a static `opacity: .16`, and (in
`app.js`) swaps the headline without a fade and freezes the kolam. Any new
motion must have a reduced-motion resting state.

**Header rule — the reference example of restraint over decoration.** The
sticky header (`.site-header`, `styles.css:76–103`) is **solid cream at rest**
with no shadow. On scroll it gains only `background: rgba(251,246,236,.82)` +
`backdrop-filter: blur(16px) saturate(1.4)`, toggled by a `.scrolled` class
that `app.js` adds past 6px of scroll (rAF-throttled). Separation from content
is a **1px hairline** (`.header-rule`), never a drop shadow. When you build a
new sticky/elevated component, copy this pattern: a hairline and a subtle blur,
not a shadow stack. (Note: the brief called for a "kolam-dot hairline" here;
what shipped is a plain solid rule — see "Known inconsistencies.")

---

## The kolam-dot motif

**Implementation.** The kolam is generated as an inline `<svg>` at runtime in
`app.js` (`buildKolam()` / `renderKolam()`), not an image file and not a CSS
`background`. It's a woven pulli-and-line dot grid: amber dots (`#B98416`,
r=4.6) at loop centres, green sinusoidal threads (`#3A5A40`, 1.5px) drawn with
`stroke-dasharray` so they can animate in. It lives in a single fixed,
full-viewport, `pointer-events:none`, `aria-hidden` layer (`#kolam`,
`styles.css:65–73`) at `z-index:0`, base opacity `.06`, behind all content
(`.wrap` is `z-index:1`).

**Where it's allowed:** as the whole-page background *rhythm* (the one place it
appears now), and — if ever needed — as a section divider or the header
border, always low-contrast and behind content. The dot color echoes
`--amber-deep`, the line echoes `--green`.

**Where it must not go:** do not stamp the kolam onto cards, buttons, badges,
or empty space "to use the motif." It is ambient texture at ~6% opacity, not
an ornament applied to components. One page = one kolam layer. If a section
feels empty, the answer is spacing and type, not more kolam. The traditions
plate fallback (a quiet concentric-ring gradient, `styles.css:239–249`) is a
separate motif and is **not** the kolam — don't conflate them.

---

## Number display rule

**Hard rule: numbers are never shown in a bordered table or a grid of stat
cards.** No `<table>` of macros, no row of boxed "94g / 218g / 52g" tiles.
Macros, kcal and prices appear as **plain inline text on one line**, joined by
middot separators, alongside a warm descriptive sentence.

**Reference example — the sample-day section** (`index.html:184–189`):

```
≈ 480 kcal · 22g protein · 68g carb · 12g fat
```

rendered as `.meal-card .stat` (plain text, `tabular-nums`, muted ink), sitting
under a serif dish name and a human sentence — never in its own bordered cell.
The day total is the same shape (`.day-total .num`). Every such figure carries
the honesty markers this project requires: the `≈`, and an
`illustrative`/`placeholder` note nearby (`.illus`, `styles.css:287`).

This is the visual counterpart to CLAUDE.md's uncertainty rule: a false-precise
boxed stat grid asserts a confidence the data doesn't have. One warm line with
a `≈` does not. New pages showing nutrition follow the meal-card pattern.

### Rounding policy — displayed precision must not exceed stated uncertainty

Added 2026-07-29. **Displayed macro masses round to the nearest whole gram.
Ratios (protein g/kg, DIAAS) keep one decimal. Full precision stays in the API
response and in `core/`; only the display rounds.**

`web/onboarding.js` implements this as `fmtGrams` (integer) and `fmtRatio` (one
decimal) — the previous single `fmtG` applied one-decimal rounding to both.

This is a correctness-of-presentation rule, not a style preference. Step 5 was
stating energy as `±14%, so roughly 1,905–2,533 kcal` and then reporting
`120.9 g protein · 67.8 g fat · 281.3 g carb · 31.1 g fibre` on the same
screen. A tenth of a gram is four significant figures sitting under a
two-significant-figure interval: the displayed precision asserts an accuracy
the page itself has just said the data does not have. That is the same
false-precision failure the boxed-stat-grid ban exists to prevent, committed
by the formatter instead of the layout — and it is worse than an unqualified
number, because it actively asserts the error is small.

Ratios are excluded because rounding them destroys them, not because they are
exempt from the principle: `1.6 g/kg` to the nearest whole number is `2`, a
25% error.

---

## Copy register — dev-mode honesty, end-user vocabulary

Added 2026-07-29. This project's disclosure habit is a genuine differentiator
and stays. But **honesty is about what you disclose, not which vocabulary you
disclose it in**, and the onboarding flow was mixing two registers: some
helper text was written for a user ("These set the baseline every target is
computed from"), and some for a developer.

**Never name an internal identifier in a user-facing string** — no function
names, no module paths, no repo filenames. Name what the *user* controls, and
say the same thing:

| Instead of                                       | Say                                                                     |
| ------------------------------------------------ | ----------------------------------------------------------------------- |
| `derive_target` currently uses weight/height/age/sex only | Body fat isn't used in today's calculation yet — it's saved for a future refinement. |
| see CLAUDE.md's "Meal templates"                 | South and North Indian are the two regions with verified recipe data today. |
| only activity level feeds the PAL factor          | Only your overall activity level changes today's energy target.          |
| see CLAUDE.md's "Meal templates" and the build-status table for why the library is this thin | These four are the only region-and-meal combinations with verified recipe data today. One plate is solved per request, not a full day. |

**An API enum value is an internal identifier too** (added round 2, 2026-07-29).
The rule above was applied to hand-written strings only, so the same defect
survived anywhere a `snake_case` enum member was printed straight from a JSON
response. Four places, all fixed by a label map beside the render:

| Rendered                                             | Source                          | Now                          |
| ---------------------------------------------------- | ------------------------------- | ---------------------------- |
| `dev_mode`                                            | `/api/targets` → `status`        | `Development estimate`       |
| `chronic_kidney_disease`                              | `/api/profile` → `clinical_flags`| `Chronic kidney disease`     |
| `primary_measurement`, `national_table`, `project_estimate`, `project_decision` | `/api/science` → `grade` | `Primary measurement`, `National food table`, `Project estimate`, `Project decision` |

Two rules for these maps: the **class** may keep keying off the raw value —
that is a code-to-code binding and correct; only the text is translated. And
an unrecognised value must fall through to a cautious label or a `_`→space
humanisation, **never** to the raw string, so a future enum member cannot leak
an identifier back onto the screen.

**What stays exactly as it is:** the DOIs, the `unverified` flags and the
whole citation panel. Those are addressed to a reader evaluating the work
rather than using the product, and naming a source precisely is the point of
them. The grade labels above are a strict 1:1 rename and are held to that:
`Project estimate` makes precisely the claim `project_estimate` made, no
softer. Abbreviating a weak grade into something that reads stronger would be
the exact failure the panel exists to prevent, committed in the presentation
layer.

Note one boundary case, resolved 2026-07-29: the `project_decision` Evidence's
`source` field read `"CLAUDE.md and BUILD_PROMPTS.md."` and is rendered
verbatim to end users through `GET /api/science`. It is now `"This project's
own design documents."` — same provenance claim, same grade, same
`verified=False`, no number touched, but no longer pointing a reader at two
files they cannot open. **A citation's `source` is user-facing copy as well as
a provenance record; it has to satisfy both.**

### Round 3, 2026-07-30: the class escaped a third time, so stop patching it

`project_protein_target_policy.source` read `"This project's decision, anchored
on morton_2018_protein."` — one registry entry citing another *by key*, inside
a sentence, served verbatim to the browser. That is the third escape of this
class after two closures, and each closure was verified by grepping for the
string that had just been fixed. **That verification cannot work: the failing
string is always the one nobody thought to grep for.** Three changes, none of
which are another label map:

1. **Cross-references are now slots, resolved by the registry.**
   `core/nutrition/citations.py` gained `Evidence.display_ref` ("Morton et al.
   (2018)") and `RENDERED_FIELDS = (summary, phenomenon, source, note)` — the
   four fields `GET /api/science` serves verbatim. A citation of another entry
   is written `{morton_2018_protein}` and substituted at registration; a raw id
   left in any of those four fields **fails registration**. Same shape CLAUDE.md
   mandates for LLM narration: prose from the author, identifier substituted by
   the layer that owns it.
2. **Which fields may take the `_`→space fallback, and which may not.** The
   round-2 rule said "a cautious label *or* a `_`→space humanisation" and left
   the choice open. It is not open:

   | Field | Fallback | Why |
   | ----- | -------- | --- |
   | diet, goal, clinical flag, region, meal slot | `humanise()` — `some_new_flag` → `Some new flag` | The user chose this value and can already read it back. Restating their own input in worse words is a cosmetic failure. |
   | evidence grade — and anything else stating how far to trust a number | **`Ungraded`**, never humanised | `Some new grade` is typographically indistinguishable from `Primary measurement`. Prettifying an unrecognised grade asserts an evidence strength the code cannot vouch for; the only safe direction to be wrong in is visibly weaker than every real grade. |

   Applying that rule found three more raw-value fallbacks in `dashboard.js`
   that the round-2 sweep missed — `plateLabel()`'s `${region} · ${meal_slot}`
   and the success sentence's `|| profile.diet` / `|| profile.goal` — each of
   which would have printed `south_indian` on a screen the moment an enum
   member was added. All now go through `humanise()`.
3. **Detection instead of another grep.** `tests/test_web_no_identifiers.py`
   walks the rendered DOM of all nine views (landing, wizard steps 1-6,
   dashboard before and after a plan call), takes every visible text node, and
   fails on any `snake_case` / `SCREAMING_CASE` token, with an allowlist that
   is currently empty. It cannot be satisfied by knowing which key leaked —
   only by no key leaking. Proven by restoring the round-2
   `chronic_kidney_disease` leak and watching it fail, then restoring; the
   transcript is in the closeout commit.

---

## Button labels

Added 2026-07-29. **Either every step names its destination, or every step
says `Continue` — the variation itself must be consistent.** The wizard was
mixing three registers with no rule: `Continue` (steps 1, 2, 3, 6),
`See my targets` (4), `Looks right` (5).

The rule now: **name the destination on the steps where something meaningful
is produced, `Continue` everywhere else.**

| Step | Label                             |
| ---- | --------------------------------- |
| 1–3  | `Continue`                        |
| 4    | `See my targets`                  |
| 5    | `Use these targets`               |
| 6    | `Save profile & build my plan` (in the panel; no action-bar CTA) |

`Looks right` was replaced because it acknowledges rather than acts — it named
a judgement about the screen you were on, not the thing about to happen.

**One primary per screen.** Step 6 previously showed `Create account & see my
plan` in the panel *and* a filled `Continue` in the action bar, two identical
dark-green buttons with no stated difference. A terminal step gets no
action-bar CTA at all. `Back`, by contrast, is now available from step 2
onward **including** the final step — it used to be hidden there, making the
account step a one-way door.

### Where the advancing action lives — and why the button must not care

Added 2026-07-30. Two placements were live and neither was a decision: the
wizard put its primary in a sticky bottom bar above a hairline; the dashboard
put `Generate my plate` inline, directly under the option grid, with no bar
and no rule. Both are defensible in isolation. Together they teach two places
to look.

**The rule:**

| Page shape             | Placement                                     | Why |
| ---------------------- | --------------------------------------------- | --- |
| Multi-step flow        | Sticky bottom action bar (`.ob-nav`)          | Progression is the mental model; the eye learns one spot and Continue never moves between steps |
| Single-purpose page    | Inline, directly beneath the controls it acts on (`.ob-save-actions`) | There is no progression to anchor, and a sticky bar around one button is chrome |

**The placements differ because the pages differ. The buttons must not.**
Before this, the same act was a slightly different control depending on where
you met it — the wizard's `Continue` at 13px/24px from a rule, the dashboard's
`Generate my plate` at 14px/26px from an inline style, its `Regenerate` at
14px/24px from a third — rendering **46 / 48 / 48px** tall. `.btn-action` now
carries that geometry, `.is-quiet` is its outlined emphasis, and **neither
placement may set its own size**. `box-sizing: border-box` plus a transparent
border keeps the outlined variant from being 2px taller than the filled one,
and an explicit `line-height` keeps an `<a class="btn btn-action">` from being
taller than a `<button>` inheriting the body's 1.6.

Enforced by `test_one_action_button_geometry_across_routes` in
`tests/test_web_wizard_layout.py`, which measures computed geometry across all
three routes and fails on any `.btn-action[style]`.

---

## Header — one nav, three named states

Added 2026-07-30. Three routes had three hand-written headers, and the result
was three navs nobody had decided on:

| Route             | What it showed                                             |
| ----------------- | ---------------------------------------------------------- |
| `index.html`      | How it works · Get your targets · Sign in · Sign up        |
| `onboarding.html` | *nothing at all*                                            |
| `dashboard.html`  | Edit profile · Signed in as `<email>` · Log out            |

The onboarding row is what marks this as drift rather than design: a signed-in
user midway through the wizard had **no way to reach Log out, or anything
else**. Its auth bar only rendered when a session existed, and the page had no
other nav to fall back on.

`web/header.js` now owns the nav for all three routes, in three explicit
states. Each page declares which state it is in; none writes a nav item.

| State             | Contents                                                   | Used by |
| ----------------- | ---------------------------------------------------------- | ------- |
| `anonymous`       | How it works · Get your targets · Sign in · Sign up         | `index.html`, no session |
| `onboarding`      | Logo, plus `Signed in as <email>` · Log out when a session exists — **and nothing else, ever** | `onboarding.html`, always |
| `authenticated`   | Dashboard · Edit profile · `<email>` · Log out (self-link dropped via `current`) | `index.html` with a session, `dashboard.html` |

**Why the onboarding state is deliberately near-empty.** The wizard holds
unsaved profile state in memory across six steps. Every nav link is a way to
lose a half-filled form to a stray click, and none of them lead anywhere the
flow doesn't already reach — step 6 *is* the sign-in point, so an anonymous
visitor needs no `Sign in` link. `Log out` is the single exception: being
signed into an account with no visible way out is worse than the escape-hatch
risk it introduces.

**The brand is the wizard's exit, and is therefore a link** (`a.brand`, added
2026-07-30). The reasoning above holds — every nav link is a way to lose a
half-filled form — but it argues for *no nav items*, not for *no way out*. An
anonymous visitor mid-wizard would otherwise have only the browser's back
button, and a logo that returns to the home page is the convention a user
already expects rather than a new escape hatch. It carries no colour of its
own (`.brand-ta` / `.brand-latin` set theirs), so the global
`a:hover { color: var(--amber-deep) }` would recolour the wordmark; the
affordance is a cursor plus `opacity: .62`, which is the one property that
reaches both spans. On `index.html` the brand stays a `<div>` — it is the
current page.

**The brand stays in each page's static HTML**, not in `header.js`. It must
not depend on JavaScript, and `test_header_logo_shares_content_left_edge`
measures it with JS disabled — a JS-rendered brand would make the route it
most needed to check unmeasurable.

**Below 560px, three things drop, in this order — and `Log out` survives all
three.** Measured at 390px, where `.header-inner` is 390px wide: the brand took
210 of it and left the nav 128 against 139px of items, so the authenticated
nav wrapped to three rows and the header grew to **160px** tall.

| Drop | What goes | Why it is the one to lose |
| ---- | --------- | ------------------------- |
| 1 | `.hdr-email` | Identity, not navigation; the account step states it anyway |
| 2 | `.brand-latin` | The Tamil `அறுசுவை` is the mark; `arusuvai` is its gloss |
| 3 | `Edit profile`, **only where a `Dashboard` link is also present** (`#hdrDashboard ~ #hdrEditProfile`) | One tap past Dashboard. The sibling combinator is the condition: `dashboard.html` has no Dashboard link (it is the self-link `header.js` drops), so `Edit profile` survives there — the one page where it is the only route to the wizard |

All three routes are 64px — a single row — at 390px and at 1600px after this.

Enforced by `test_no_route_hand_writes_its_own_nav` (JS off: exactly one
`.brand` in the header, exactly one empty `#appNav`) and
`test_header_states_differ_by_route_and_session` (JS on, real session: the
exact ID list per state, including the assertion that a signed-in wizard
visitor gets `hdrUserEmail` + `hdrLogout`).

---

## Content redundancy rule

**Every fact lives on exactly one canonical page.** Elsewhere it is a one-line
teaser plus a link — never re-explained in full.

Canonical homes (target information architecture):

| Content                              | Canonical home |
| ------------------------------------ | -------------- |
| Full methodology, citations, DIAAS   | `/science`     |
| Full delivery cities, pricing, terms | `/delivery`    |
| Full FAQ                             | `/faq`         |

The home page and onboarding **link** to these; they never restate them in
full. When adding a page, first check whether its content already has a
canonical home — if so, teaser + link, don't re-author.

**Current state (single landing page):** these are still *sections* on the one
shipped page (`#faq`, `#early`/delivery, the science section), not separate
routes. The home page already models the teaser discipline correctly — e.g. the
science section gives a two-line summary and the free-planner claim appears as
a one-line band (`.free-band`) rather than being re-argued. When this is split
into real routes, the section copy moves to its canonical page and the home
page keeps only the teaser.

---

## Component inventory

Reusable pieces already built. Reuse these before building a near-duplicate.

| Component            | What it is                                                        | Defined in |
| -------------------- | ----------------------------------------------------------------- | ---------- |
| **Header**           | Sticky cream bar, blur-on-scroll, 1px hairline, brand + `#appNav`  | `.site-header` `styles.css` (shell); `startHeader()` `app.js`. **Identical markup on all three routes as of 2026-07-30** — the brand static, the nav rendered by `web/header.js`. See "Header — one nav, three named states" |
| **Brand wordmark**   | Tamil `அறுசுவை` + uppercase latin `arusuvai`, baseline-aligned    | `.brand`/`.brand-ta`/`.brand-latin` `styles.css:98–100` |
| **Button — primary** | Green pill, cream text (`.btn-primary`)                           | `styles.css` (buttons) |
| **Button — link**    | Text-only green action (`.btn-link`)                              | `styles.css` (buttons) |
| **Button — action** | `.btn-action` — **the** page-advancing button geometry: 13px/24px, 15px/600, full pill, `border-box` + transparent 1px border so the outlined `.is-quiet` variant is the same height. Used by the wizard's Back/Continue **and** the dashboard's Generate/Regenerate/Adjust/Try-another | Added 2026-07-30 to collapse three separately-sized versions of the same act (46/48/48px tall). See "Where the advancing action lives"; `styles.css` (buttons) |
| **CTA — solid**      | Large green pill, lifts 1px on hover (`.cta.cta-solid`)           | `styles.css:111–113` |
| **CTA — ghost**      | Outlined pill, greens on hover (`.cta.cta-ghost`)                 | `styles.css:114–115` |
| **Eyebrow**          | Uppercase tracked green kicker above headings (`.eyebrow`)        | `styles.css:54–60` |
| **Section heading**  | `.sec-eyebrow` + `.sec-title` serif H2 pair                       | `styles.css:204–206` |
| **Bloom card**       | 140px taste card, scroll-reveals with stagger (`.bloom-card`)     | `styles.css:215–231`; `startBloom()` `app.js` |
| **Traditions card**  | Plate image (w/ ring fallback) + name + dishes + note             | `styles.css:238–253`; markup `index.html:123–140` |
| **Meal card**        | Dish + sentence + inline macro line (the number-display pattern)  | `styles.css:279–283`; reused verbatim on `web/dashboard.html` for the solved plate's component list as of 2026-07-25 (no new card component for the real dashboard) |
| **Macro line**       | `≈ … kcal · …g protein · …` inline stat (`.stat` / `.num`)        | `styles.css:283,286` |
| **Step**             | Numbered how-it-works item (`.step` `.n`/`.t`/`.b`)               | `styles.css:260–263` |
| **Tag / pill**       | Read-only summary chip, **one fill** (`.tag`, neutral ink tint)    | `styles.css`. **2026-07-30:** `.tag-diet` (sage) and `.tag-goal` (amber) were deleted — same class of element, same saved profile, two colours carrying nothing the label wasn't already carrying. Neutral rather than sage on purpose: these sit directly above the plate picker, whose chosen pill is `--accent-selected`, and a read-only chip in the selected colour invites the reading that it is selectable |
| **City pill**        | `.city.live` (green) / `.city.soon` (dashed muted)                | `styles.css:315–317` |
| **FAQ item**         | Serif question button + `+`→`×` sign + max-height accordion       | `styles.css:336–347`; `startFaq()` `app.js` |
| **Quality card**     | Recessed `--cream-sink` panel with colored-dot list               | `styles.css:296–301` |
| **Early-access card**| Green inset card with pill email input + amber submit             | `styles.css:318–329`; `startEarly()` `app.js` |
| **Auth modal**       | Centered dialog, blurred overlay, signin/signup toggle            | `styles.css:359–393`; markup `index.html:316–345`; `startAuth()` `app.js` — real, `web/auth.js` `initAuthModal()`, on `index.html` only as of 2026-07-25 (was real on `onboarding.html`/`dashboard.html` too from 2026-07-24 until onboarding's redesign that day replaced it there with the inline Account tabs step below; `dashboard.html` never used it directly — its auth gate redirects to `onboarding.html`) |
| **Calc dock**        | Fixed slide-out illustrative protein calculator                  | `styles.css:118–170`; `startCalc()` `app.js` — **illustrative only**, see CLAUDE.md `web/` note |
| **Kolam background** | Runtime-generated SVG ambient layer                              | `#kolam` `styles.css:65–73`; `buildKolam()`/`renderKolam()` in `app.js`, duplicated (not shared) in `onboarding.js`/`dashboard.js` as of 2026-07-25 — same per-page-duplication convention as the rest of this component list |
| **Footer**           | Brand + link columns + illustrative-numbers disclaimer           | `styles.css:350–356`; markup `index.html:281–312` |
| **Onboarding form**  | Boxed number+unit fields (`.ob-input-unit`), pill radios (`.ob-plate-opt`) for sex/diet/region, checkbox flag row reusing the goal card (`.ob-flags`) | `web/onboarding.html`; `.ob-*` `styles.css` (onboarding section) — reworked 2026-07-25 porting `Arusuvai Onboarding.dc.html`; step 1's two flex rows became `.ob-body-grid`, a fixed **two-up** grid (Age \| Weight, Height \| Body fat, Sex across both), collapsing to one column below 420px. **2026-07-29:** every control moved to `--surface`; `.ob-selectable` now supplies surface + selected state for all of them; body-fat's placeholder is the word "optional", not an em dash; per-field `.ob-field-error` + `.ob-invalid` replaced a `window.alert` on step 1 and a single unanchored message on step 6 |
| **Step layout**      | `.ob-grid12` — the project's **only** layout grid: 12 columns at `--container-max` (1280px), `--wizard-gutter` (32px). Narrative in `.ob-col-narrative` (cols 1–4), controls in `.ob-col-controls` (cols 6–12), column 5 the optical gutter. **Identical on all six wizard steps and on the dashboard's plate picker; nothing overrides the span, and there is no per-step or per-page width variable.** Top-aligned at `--wizard-top` (72px) — never vertically centred. Collapses to stacked at 1100px | `styles.css` (onboarding section). Replaced the `--step-w`/`--fields-w` per-step system 2026-07-29; `.ob-step-grid`/`.ob-step-intro`/`.ob-step-fields` deleted the same day in round 2 when the dashboard migrated onto this grid. See "The container token" and "The wizard layout contract" above, and `tests/test_web_wizard_layout.py` for the enforcement |
| **Page container**   | `.wrap` — `max-width: var(--container-max)`, `margin: 0 auto`, `padding: 0 var(--container-pad)`. `.header-inner` uses the same two so the brand shares a left edge with the content. **No page sets its own width** | `styles.css` (shell). See "The container token" — the rule exists because three routes had three measures |
| **Status pill**      | `dev_mode`/`validated` badge (`.ob-status-pill`). `dev_mode` is a **neutral bordered chip**; `validated` keeps the green tint | `web/onboarding.html`; `styles.css`. De-ambered 2026-07-29 — amber is the stepper's current-step marker and nothing else |
| **Error message**    | Inline error banner using `--error`/`--error-bg` (`.ob-error`)   | `web/onboarding.html`; `styles.css` (onboarding section) |
| **Source list**      | Collapsible `<details>` of cited constants (`.ob-sources`)       | `web/onboarding.html`; `styles.css` (onboarding section) |
| **Progress bar**     | Six-chip stepper, done=green / current=`--accent-current` / future=flat (`.ob-progress2`, `.ob-progress2-seg`) | `web/onboarding.html`; `styles.css`. **2026-07-29:** the `Step N of 6 · Name` sub-line was removed — the chips already show position and name the step, so it was duplicated signposting |
| **Goal card**        | Radio-as-card picker (`.ob-goal-card` + `.ob-selectable`), white surface, **left-side** indicator, `--accent-selected` fill when chosen; `.is-stacked` for single-column long-copy lists, `.is-three` for exactly-three groups (goal, clinical conditions) | Added 2026-07-24, extended 2026-07-25 to also cover activity level and the clinical-flag checkboxes rather than adding two more card components. **2026-07-29:** surface moved tan→white, indicator moved top-right→left, and `.is-three` added because auto-fit resolved three cards to a 2×2 with an empty fourth cell |
| **Day picker**       | 0–7 button row for training days/week (`.ob-day-picker`, `.ob-day-btn` + `.ob-selectable`) | Added 2026-07-25 porting `Arusuvai Onboarding.dc.html`. **2026-07-29:** its solid-green/white-text selected state was the heaviest of the flow's three selected dialects and was replaced by the shared one; its value readout renders empty rather than `—` until a day is picked |
| **Toggle row**       | Full-width card with an inline pill switch, used for "I do resistance training" (`.ob-toggle-row`) | Added 2026-07-25; `web/onboarding.html`; `styles.css` |
| **Target sentence**  | One flowing serif sentence with named number slots, replacing a stat-grid summary (`.ob-target-sentence`). Emphasis is **weight, not colour**; sized on `--text-lead` | `web/onboarding.html`; `styles.css`. De-ambered and moved onto the shared type scale 2026-07-29 — it had been `clamp(18px,3.4vw,22px)` against every other step's flat 15px |
| **Callout**          | Recessed `--cream-sink` card with a green eyebrow + dot list, used for the target-review disclosures (`.ob-callout`) | Added 2026-07-25; content is `data.warnings` verbatim from the API, not authored copy — see CLAUDE.md on clinical flags not tightening a target at this stage; `web/onboarding.html`; `styles.css` |
| **Plate picker**      | Pill radio group for (region, meal_slot) choice (`.ob-plate-opt`) | Added 2026-07-24; moved to `web/dashboard.html` the same day (accounts increment) — onboarding no longer collects a plate, only a target; also reused as the generic pill-radio style for onboarding's sex/diet/region pickers as of 2026-07-25; `styles.css` |
| **Decline card**     | Honest-decline state: green-eyebrow "why we stopped" callout (`.ob-callout`, reused from onboarding's target-review disclosures) over a serif headline+sentence, **not** styled with `--error` — an expected, disclosed outcome is not styled as a failure | Added 2026-07-24 as `.ob-decline` (amber-tinted `--cream-sink` card); reworked 2026-07-25 porting `Arusuvai Dashboard.dc.html`'s "We'd rather not build this one" layout — the callout's bullet list is `data.violations` verbatim from `POST /api/plan`, never the design canvas's fabricated per-condition copy (e.g. its hardcoded "chronic kidney disease... 0.8 g/kg... 54 g/day" text describes a demo profile, not whatever profile actually declined); `web/dashboard.html`; `styles.css` |
| **Loading line**      | Plain inline "Calling `POST /api/…`…" text, no spinner (`.ob-loading`) | Added 2026-07-24; `web/onboarding.html`, `web/dashboard.html`; `styles.css` |
| **Site nav**          | `.app-nav` — **the** header nav strip, filled by `web/header.js` in one of three states (`anonymous` / `onboarding` / `authenticated`); `.hdr-email` truncates the address rather than forcing horizontal scroll | Added 2026-07-30, replacing `.ob-authbar` and `.nav`, which were two layouts for the same strip (18px gap left-aligned vs 10px gap right-aligned) and had drifted into three different headers. See "Header — one nav, three named states" |
| **Account tabs**      | Pill-tab switch (Create account / Sign in) over inline email+password fields, no popup (`.ob-account-tabs`, `.ob-account-fields`) | Added 2026-07-25 for onboarding step 6, porting `Arusuvai Onboarding.dc.html`'s account hinge; replaces the shared auth modal *on this page only* — `index.html` still uses the modal (see Auth modal row) and `dashboard.html`'s cold-entry gate gets bounced to this step via `onboarding.html?next=dashboard`; fields reuse `.modal label input`'s exact CSS (see that rule's comment); `web/onboarding.html`; `styles.css` |
| ~~**Auth status bar**~~ / ~~**Header auth state**~~ | Both folded into **Site nav** above on 2026-07-30. `.ob-authbar` (`onboarding.html`/`dashboard.html`, added 2026-07-24) and `index.html`'s `navUserEmail`/Dashboard/Log out swap (added 2026-07-25) were the same idea implemented twice, which is precisely how onboarding ended up with no signed-in nav at all | Listed only so an old reference is recognisable; do not reintroduce either |
| **Profile tag row**   | `.tag-row`/`.tag` (shared with the landing page's illustrative sample-day tags) on `web/dashboard.html`, for the *real* saved profile's diet, goal and any disclosed clinical flags — deliberately **not** a "region" tag, because `ProfileIn`/`ProfileOut` carry no region-preference field (only the plate picker picks a region, per plate); inventing one would be an unverified claim about what the profile stores | Added 2026-07-25 porting `Arusuvai Dashboard.dc.html`; the per-kind colour fork was removed 2026-07-30 (see **Tag / pill**); `web/dashboard.html`; `styles.css` |
| **Selectable**        | **The** selection primitive (`.ob-selectable`): white `--surface` + `--border`, and one selected treatment — `--accent-selected` fill + `--border-selected`. Covers goal/activity/condition cards, diet+region pills, day buttons and the resistance toggle. `:has(input:checked)` for native controls, `.is-selected` for the two JS-driven ones, **one declaration block** | Added 2026-07-29 to collapse three competing selected treatments into one; `styles.css` |
| **Action bar**        | Sticky bottom bar rendered once by the shell, outside every step (`.ob-nav`). Flat `--surface-page` + one hairline (never a backdrop-filter — see the layout contract). **The bar is a placement, not a button style** — Back and Continue carry `.btn-action` like every other advancing action | `web/onboarding.html`; `styles.css`. Reworked 2026-07-29: Back had no container or hit area, and the blurred band rendered pink over the kolam layer. 2026-07-30: geometry moved out to `.btn-action` |
| **Group caption**     | Caption above a control group (`.ob-group-lbl`, `.ob-group-lbl-row` for a caption with a value readout) | Added 2026-07-29; was an inline style repeated per site, which is how step 2's two headings ended up ~6px out of alignment |
| **Field error**       | Per-field inline error + red border (`.ob-field-error`, `.ob-invalid`) | Added 2026-07-29. Step 1 used a `window.alert` that named no field and vanished; step 6 had one message above the button with neither input marked |
| **Account confirm**   | Signed-in branch of step 6 (`.ob-account-confirm`): names the account the profile is about to be saved to, in place of the create/sign-in form | Added 2026-07-29. The step used to render the create-account form unconditionally, so a signed-in user saw "Create account" directly under a header reading "Signed in as …" |

Everything currently lives in three static pages (`web/index.html`,
`web/onboarding.html`, `web/dashboard.html`) sharing `web/styles.css`, plus
page-specific `web/app.js` / `web/onboarding.js` / `web/dashboard.js` and two
shared files: `web/auth.js` (session calls + the auth-modal wiring, used by
both `onboarding.html` and `dashboard.html` — added 2026-07-24 rather than
duplicating the fetch/modal logic per page) and `web/header.js` (the nav's
three states, added 2026-07-30, loaded by all three pages). When this migrates to Next.js
(per CLAUDE.md's `web/` scope), each row above becomes a component; keep this
table pointing at wherever it lands.

---

## Quality floor

Added 2026-07-29 — previously unspecified, which is why none of it existed in
the onboarding flow. Every interactive page meets all four:

1. **Visible keyboard focus.** A `:focus-visible` ring
   (`2px solid var(--green)`, `outline-offset: 2px`) on every focusable
   element, including ones that used to be bare text. `:focus-visible`, not
   `:focus`, so mouse users don't see outlines. Watch specificity: the shared
   `.modal label input, .ob-account-fields label input { outline: none }` rule
   is `(0,1,2)` and silently outranked a bare `input:focus-visible` at
   `(0,1,1)`, which left step 6's two inputs ringless. Verify by tabbing, not
   by reading the stylesheet.
2. **Required-field and error states.** Per-field, never a `window.alert` and
   never one unanchored message for a whole form — `.ob-field-error` +
   `.ob-invalid` on the field's own cell, cleared on `input` so a corrected
   value stops looking wrong.
3. **A defined collapse point.** A fixed two-column split states where it
   stacks; the wizard's is **1100px**. Below it, narrative sits above
   controls. Do not let a two-column grid squeeze itself to unreadable.
4. **`prefers-reduced-motion` respected.** The global rule in `styles.css`
   flattens animations and transitions; JS-driven scrolling must opt in too —
   `onboarding.js` passes `behavior: "auto"` instead of `"smooth"` when the
   query matches, since a CSS media query cannot reach a `scrollTo` option.

---

## Known inconsistencies to fix

These are real discrepancies in the shipped pages, flagged rather than silently
normalized in this doc. Each needs a code fix, not just a doc edit.

0. **The landing page overflows on mobile — clipped, not scrolling.** At a
   390px viewport `.calc-card` (the fixed calculator dock) is 308px wide
   starting at x=350, so its right edge sits at 658 against a 390px document.
   Roughly 40px of a 308px card is on screen. Found 2026-07-29, still open.

   **Read the "no horizontal scroll at 390px" measurement carefully — it does
   not contradict this.** Measured 2026-07-30 across all three routes:
   `clientWidth` 390, `scrollWidth` 390, no scrollbar anywhere. That is true
   *and* compatible with the overflow above, because `body { overflow-x: clip }`
   and `.calc-panel { overflow-x: hidden }` mean no amount of overflow can ever
   produce a scrollbar. A scroll check is therefore not evidence that content
   fits; it is evidence that content which doesn't fit is being hidden. Both
   facts are now pinned separately by
   `tests/test_web_wizard_layout.py::test_scroll_absence_at_390_is_not_evidence_of_fitting`,
   so neither can be quoted as settling the other. The mobile evidence on
   record is: nothing scrolls, and one element is cut off.

1. **Cards don't share one border-radius.** Bloom/meal/calc cards are `16px`,
   quality card `18px`, traditions plate & early-access card `20px`, modal
   `22px`. Several of these are "a card on cream" and should agree. Pick one
   card radius (likely `16px`) and reserve larger radii for a deliberately
   distinct surface (e.g. the modal), then update the code.

2. **Inputs use two different radii.** The modal text inputs are `11px`
   (`styles.css:384`) while the early-access email input is a `999px` pill
   (`styles.css:324`). Same semantic control, two shapes. Decide one input
   style and apply it to both forms.

3. **The header rule isn't the kolam-dot hairline the brief specified.**
   `.header-rule` is a plain `1px solid rgba(43,38,34,.1)` (`styles.css:97`).
   The brief called for a kolam-dot hairline. Either update the brief's
   intent as intentionally dropped, or implement the dotted-kolam border —
   currently the doc describes the solid rule because that's what shipped.

4. **Section H2 max-size varies (34–42px) with no clear rule.** bloom 42,
   traditions 38, how/sample/science/faq 36, delivery 34. Some variation may be
   intentional emphasis (bloom is the showpiece), but 36 vs 34 vs 38 reads as
   drift. Define which sections are "showpiece" vs "standard" and collapse to
   two H2 sizes.

5. **Fractional / near-duplicate font sizes.** Body copy appears as 14px,
   14.5px, 15px, 15.5px across sections; fine print as 11.5/12/12.5px. There's
   no strict scale, so small deltas creep in. Consider snapping to a fixed
   ramp (e.g. 12 / 13.5 / 15 / 17) and removing the half-pixel one-offs.

6. **A few colors are hardcoded past the tokens.** The quality-list dots use
   inline `style="background:#3A5A40|#E0A526|#C1694F"` (`index.html:206–208`)
   instead of the CSS vars, and the kolam colors are literals in `app.js`
   (`#B98416`, `#3A5A40`). Functionally correct (they match the tokens today),
   but a token change wouldn't propagate. Route them through the variables.

7. **Muted-text opacity ramp is un-tokenized.** The `.4`–`.72` alpha stops on
   `--ink` recur dozens of times as raw `rgba(43,38,34,.NN)`. Promote the
   common stops (`.72`, `.68`, `.6`, `.5`, `.4`) to named tokens
   (`--ink-70` … `--ink-40`) so muted text is consistent and adjustable.
