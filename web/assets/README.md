# Plate images

The "One kitchen, three traditions" cards in `../index.html` use three
cut-out, top-down plate photos:

| File     | Card          |
| -------- | ------------- |
| `si.jpg` | South Indian  |
| `nt.jpg` | North Indian  |
| `ct.jpg` | Continental   |

These are present and wired into the markup. If an image is ever missing, the
`<img onerror>` in the markup removes it and the card falls back to a quiet
concentric-ring motif in the leaf/amber palette (see `.trad-plate` in
`../styles.css`), so the page still looks intentional.

To swap in new photos, keep those exact lowercase names (or update the `src`
attributes and this table together).
