# The IFCT sitting: what to bring, what it buys, what it cannot

**Written 2026-08-09.** This is a handoff for the one task in this project that
no automation can do: a human opening IFCT 2017 and reading ten rows.

`CLAUDE.md`, second invariant: *"Only a human who has opened the source document
may flip that flag to `True`."* Nothing in this document, and nothing in the two
scripts it points at, changes a `verified` flag. That is the point of them.

## Why an assistant cannot shortcut this, demonstrated rather than asserted

The repo has already run the experiment. On 2026-07-24 four rows —
`rice_milled_raw` (A015), `rajma_raw` (B020), `toor_dal_raw` (B021),
`potato_raw` (F006) — were populated with real IFCT 2017 values sourced from the
Sahu & Sahu re-publication rather than the source document. Those four rows
carry real codes and real numbers today, and all four are still
`verified=False`. Automation moved the values and could not move the flag, which
is the flag working as designed. See `data/raw/ifct/README.md`.

## Read this part before booking the time

Two things measured this session change what the sitting is worth, and both
argue for doing it anyway — but for a different reason than the queue assumed.

### 1. Verification alone cannot make any current plate servable

`docs/design/probes/d7_verification_horizon.py` concluded, before D10 landed,
that verifying the north_lunch ingredient rows would take that plate to **9.5%
unverified energy — SHIPS**, against the 15% threshold. That conclusion is now
misleading, because it measures the *second* of two gates and D10 changed the
first.

`docs/design/probes/d7b_after_verification.py`, run 2026-08-09:

```
  recipe                 comp   proc   TODAY    comp   proc VERIFIED   verdict
  idli                 0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  phulka               0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  steamed_rice         0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  (the other 15 recipes: 0.2500 -> 0.0500, clears)

  3 of 18 recipes remain protein-ineligible after full composition verification

  south_breakfast    BLOCKED by idli
  south_lunch        BLOCKED by steamed_rice
  north_lunch        BLOCKED by phulka
  north_dinner       BLOCKED by phulka

  18 of 18 components agree, 0 disagree.   (cross-check vs core/)
```

All four reference plates contain one of the three. Their protein band is
`process.unassessed_uncertainty` (0.20), declared by D10 because the dish is
cooked and **no registered constant describes boiling, steaming or dry-griddle
loss**. Composition data cannot touch that term: verify every ingredient row in
the library and `phulka` still sits at 0.05 + 0.20 = 0.25 against a 0.15
ceiling, so outside `dev_mode` it never enters the candidate pool and the plate
is never enumerated — an earlier and harder failure than the energy threshold
D7 was watching.

That is finding 41, and it is why finding 41 is the next task. **The sitting is
necessary and not sufficient.** Both halves have to land before one plate can
ship as verified; neither ordering makes the other unnecessary.

### 2. Four of the ten rows are probably not IFCT questions at all

Triage below. **Confidence labels are honest: only `sunflower_oil` is measured.
The rest are predictions from what IFCT 2017 is, not from having opened it.**
Treat a wrong prediction here as expected, and record it in `notes` — a
recorded negative is a result.

| Row | Verdict | Basis |
|---|---|---|
| `wheat_atta_raw` | Likely coverable | Whole wheat flour is a staple cereal; IFCT's A-series covers these. *Predicted.* |
| `onion_raw` | Likely coverable | Common vegetable. *Predicted.* |
| `tomato_raw` | Likely coverable | Common vegetable. *Predicted.* |
| `green_chilli` | Likely coverable | Common vegetable. *Predicted.* |
| `paneer_fresh` | Probably coverable | Paneer/chhana is a tabulated Indian milk product. *Predicted.* See DIAAS caveat below. |
| `soya_chunks_dry` | Uncertain | Defatted soy nuggets are a *processed* product; IFCT tabulates soya bean. The row is on a dry basis, so a whole-bean figure is not a substitute. *Predicted.* |
| `sunflower_oil` | **Not coverable — measured** | Checked 2026-07-24: IFCT carries code T012, but the tabulated row reports `energy_kcal=0` and all micronutrients 0 alongside `fatce=100`. Oils get a fatty-acid profile elsewhere, not a nutrient panel. Needs a different source (USDA FoodData Central). |
| `ginger_garlic_paste` | Probably not coverable | A household compound, not a food a composition table tabulates. The real fix is to decompose it into ginger + garlic + water, which *are* IFCT foods — that is a recipe-data change, not a lookup. |
| `garam_masala` | Probably not coverable | A blend with no fixed composition. Same decomposition option, but the constituent spices vary by household. Note its `energy_kcal` was already back-solved to 321 for internal Atwater consistency; replacing that with a blend IFCT does not tabulate is not obviously an improvement. |
| `salt_iodised` | Not an IFCT question | Its sodium is a *stoichiometric derivation* — 22.99/58.44 = 39.339% NaCl by mass — chosen over a measured value precisely because anyone can rederive it from two atomic masses. Documented as a reproducible upper bound overstating a real product by ~1.5%. A composition table would replace a reproducible derivation with an unreproducible reading. |

**So the sitting is realistically five or six rows, not ten.** The worksheet
puts the four doubtful ones last, under a comment saying so.

### The DIAAS caveat — the sitting does not touch it

IFCT 2017 is a composition table. **It does not tabulate DIAAS.** The DIAAS
values on `paneer_fresh` (1.00) and `soya_chunks_dry` (0.85) are *authored* —
entered at the low end of a recalled range, never sourced — and the
quality-source rule turns on them. `soya_chunks_dry` is the only vegan-eligible
row in the library that clears the 0.75 threshold, so the entire quality
behaviour for vegan profiles rests on one authored number.

That is a **separate sitting with a separate source** (FAO 2013 or equivalent),
and no amount of IFCT work closes it. Do not let a green diff on composition
read as verification of the quality rule.

## How to do it

1. **Do not open `fixture_ingredients.csv` first.** The current values are
   hand-entered approximations. Reading them before transcribing anchors the
   transcription to the guess it is meant to check, and an agreeing transcription
   then looks identical, in the file, to a good approximation.

2. Fill `docs/design/ifct_transcription_worksheet.csv` from IFCT 2017 alone.
   Record the code and the page. Leave a cell **empty** if IFCT does not
   tabulate it — empty means "not found", `0` means "the table says zero", and
   those are different results.

3. Run the diff:

   ```bash
   PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_transcription_diff.py
   ```

   It reports MATCH / DIFFERS / NOT FOUND per value and flags any ratio past
   2.5x as a probable raw-versus-cooked basis error rather than a data-quality
   one. It writes nothing.

4. Copy values across by hand, set `ifct_code`, and **rewrite `source_note`** —
   "Hand-entered approximation" becomes false the moment a value is transcribed,
   and a stale note is worse than none.

5. Flip `verified` to `true` **only** for rows you personally read in the source
   document. If you transcribed from a re-publication rather than IFCT 2017
   itself, the flag stays `false` and the note says which. That is what happened
   to the four A015/B020/B021/F006 rows and it was the right call.

6. Re-run `python -m pytest tests/ -q` and `python demo.py`. Verification moves
   a row's composition band 0.25 → 0.05, which moves displayed intervals on
   every plate containing it. Point estimates move only where a transcribed
   value DIFFERS — and those can move a verdict.

## What is deliberately not automated here

The diff script does not write to `fixture_ingredients.csv`, does not flip
`verified`, and does not guess an IFCT code. Each of those omissions is the
round-4 rule about self-attestation applied to tooling: a script that filled in
the fixture from a worksheet would make the cheapest authoring path — running
the script — produce the most confident-looking output, which is the exact
ordering this project keeps catching and reversing.
