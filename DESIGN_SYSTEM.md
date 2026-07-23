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
| `--rule`         | `rgba(43,38,34,.08)`   | Hairline dividers between sections/cards          |

**State / derived colors** (not yet tokenized — see "Known inconsistencies"):

- Muted text: `rgba(43,38,34,.5–.72)` opacity ramp on `--ink` for sub-copy,
  captions, fine print. Common stops: `.72` (hero sub), `.68` (body), `.6`,
  `.55`, `.5` (captions), `.4` (finest print).
- Borders on inputs/cards: `rgba(43,38,34,.09–.16)`.
- Error/success: **none defined yet.** The early-access and auth forms have no
  validation-error styling. First page that needs one defines it here.

**The one-accent rule.** `--amber` is the single primary accent, used
*sparingly, one thing at a time*. It marks exactly one focal element per
viewport — the hero credibility dot, the FAQ `+`/`×` sign, the "Notify me"
button, a dotted underline on one emphasized phrase. It is **not** a fill for
buttons (those are `--green`), not applied to multiple competing elements on
one screen. Green is the workhorse action color; amber is the single spark.
Terracotta is tertiary — it appears only as the third item in a set of three
(e.g. the third quality-list dot), never as a standalone accent.

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

**Container.** `max-width: var(--max)` = **1240px**, centered, with a fluid
gutter `padding: 0 clamp(18px, 4vw, 44px)` (`.wrap`, `styles.css:47–53`). The
header inner and footer share the same max + gutter so edges align.

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
| **Header**           | Sticky cream bar, blur-on-scroll, 1px hairline, brand + nav       | `index.html:49–62`; `.site-header` `styles.css:76–103`; `startHeader()` `app.js` |
| **Brand wordmark**   | Tamil `அறுசுவை` + uppercase latin `arusuvai`, baseline-aligned    | `.brand`/`.brand-ta`/`.brand-latin` `styles.css:98–100` |
| **Button — primary** | Green pill, cream text (`.btn-primary`)                           | `styles.css:109–110` |
| **Button — link**    | Text-only green action (`.btn-link`)                              | `styles.css:107–108` |
| **CTA — solid**      | Large green pill, lifts 1px on hover (`.cta.cta-solid`)           | `styles.css:111–113` |
| **CTA — ghost**      | Outlined pill, greens on hover (`.cta.cta-ghost`)                 | `styles.css:114–115` |
| **Eyebrow**          | Uppercase tracked green kicker above headings (`.eyebrow`)        | `styles.css:54–60` |
| **Section heading**  | `.sec-eyebrow` + `.sec-title` serif H2 pair                       | `styles.css:204–206` |
| **Bloom card**       | 140px taste card, scroll-reveals with stagger (`.bloom-card`)     | `styles.css:215–231`; `startBloom()` `app.js` |
| **Traditions card**  | Plate image (w/ ring fallback) + name + dishes + note             | `styles.css:238–253`; markup `index.html:123–140` |
| **Meal card**        | Dish + sentence + inline macro line (the number-display pattern)  | `styles.css:279–283` |
| **Macro line**       | `≈ … kcal · …g protein · …` inline stat (`.stat` / `.num`)        | `styles.css:283,286` |
| **Step**             | Numbered how-it-works item (`.step` `.n`/`.t`/`.b`)               | `styles.css:260–263` |
| **Tag / pill**       | Diet (`.tag-diet`, green tint) & goal (`.tag-goal`, amber tint)   | `styles.css:267–270` |
| **City pill**        | `.city.live` (green) / `.city.soon` (dashed muted)                | `styles.css:315–317` |
| **FAQ item**         | Serif question button + `+`→`×` sign + max-height accordion       | `styles.css:336–347`; `startFaq()` `app.js` |
| **Quality card**     | Recessed `--cream-sink` panel with colored-dot list               | `styles.css:296–301` |
| **Early-access card**| Green inset card with pill email input + amber submit             | `styles.css:318–329`; `startEarly()` `app.js` |
| **Auth modal**       | Centered dialog, blurred overlay, signin/signup toggle            | `styles.css:359–393`; markup `index.html:316–345`; `startAuth()` `app.js` |
| **Calc dock**        | Fixed slide-out illustrative protein calculator                  | `styles.css:118–170`; `startCalc()` `app.js` — **illustrative only**, see CLAUDE.md `web/` note |
| **Kolam background** | Runtime-generated SVG ambient layer                              | `#kolam` `styles.css:65–73`; `buildKolam()`/`renderKolam()` `app.js` |
| **Footer**           | Brand + link columns + illustrative-numbers disclaimer           | `styles.css:350–356`; markup `index.html:281–312` |

Everything currently lives in the single static trio (`web/index.html`,
`web/styles.css`, `web/app.js`). When this migrates to Next.js (per CLAUDE.md's
`web/` scope), each row above becomes a component; keep this table pointing at
wherever it lands.

---

## Known inconsistencies to fix

These are real discrepancies in the shipped pages, flagged rather than silently
normalized in this doc. Each needs a code fix, not just a doc edit.

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
