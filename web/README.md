# web/ — Arusuvai landing page

Static landing page for the Arusuvai meal planner, ported from the Claude
Design canvas (`Arusuvai Landing.dc.html` in the "Arusuvai Landing Page
Design" project) to a self-contained page with no proprietary runtime and no
build step.

```
web/
  index.html    markup (semantic, class-based)
  styles.css    palette, type, layout, motion
  app.js        vanilla-JS behaviour (no framework)
  assets/       plate photos — see assets/README.md
```

## Run

Any static server, e.g.:

```bash
python -m http.server 8000 --directory web
# then open http://localhost:8000
```

Opening `index.html` directly works too; the Google Fonts and the plate images
are the only external requests.

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
