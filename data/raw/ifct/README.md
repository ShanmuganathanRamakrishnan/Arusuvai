# `data/raw/ifct/` — provenance

## What is actually in here

`fixture_ingredients.csv` is mostly a **hand-entered fixture set**, not an
IFCT extract, plus five rows carrying real IFCT 2017 values: four updated
2026-07-24, one (`egg_boiled`) added 2026-08-16 (TASKS_3.md R3a — see below).
29 of its 30 rows have `verified` set to `false`; 25 have an empty
`ifct_code`. Both are deliberate:

Three of those rows — `paneer_fresh`, `tofu_firm` and `soya_chunks_dry`, added
2026-08-02 — deserve a specific warning beyond the general one below. Their
`diaas` figures are the field the quality-source rule gates on, and all three
are **authored from recollection at the low end of a wide remembered range**,
not read from FAO 2013 or any other source. Each row's `source_note` says so.
Entering the low end is deliberate: a high DIAAS makes a row *qualify*, so the
cheapest authoring path must not be the most permissive one.

The one *unconditionally* verified exception is `water` (`verified=true`).
All nine of its macros are zero, and "water contributes no nutrients" is not
a claim that needs IFCT open on the desk. It is therefore also the only
verified row that cannot move any uncertainty band. (This README previously
said *every* row was `false`; a test added on 2026-07-21 —
`test_water_is_the_only_verified_ingredient_row` — found otherwise.)

- The remaining nutrient values are approximations of commonly published
  figures, transcribed from memory. Nobody has opened *Indian Food
  Composition Tables* (Longvah et al., 2017) in the course of this build.
  Treat them as plausible-shaped test data, not as reference values.
- The `ifct_code` column is empty rather than filled with invented codes,
  except for the four rows below. A fabricated code that looks real is worse
  than an absent one, for the same reason a real-but-mismatched citation is
  worse than a missing one: it passes every automated check while being
  wrong, and only someone with the source document can catch it.

## Four rows carry real IFCT 2017 data, pending human verification (2026-07-24)

`rice_milled_raw` (A015), `rajma_raw` (B020, new), `toor_dal_raw` (B021, new)
and `potato_raw` (F006, new) were extracted from the Sahu & Sahu
machine-readable re-publication of IFCT 2017 (`ifct2017/ifct2017` on GitHub,
Zenodo DOI 10.5281/zenodo.7088653) — the actual `IFCT2017.pdf` exceeded this
build's fetch tooling (10 MB response cap). Each row's `source_note` states
this plainly and cites the code.

**This is not the same evidentiary weight as reading IFCT 2017 directly, even
though both describe the same underlying NIN measurements.** Each of the four
`source_note`s now says so explicitly, in these terms: read from a
third-party digitization (the Zenodo re-publication), *not* read directly
from the primary NIN-published `IFCT2017.pdf`. The digitization is a second
party's transcription of NIN's tables, and it has not itself been
cross-checked against the PDF for transcription error — a DOI-registered
re-publication matching on the numbers we could check is a weaker claim than
"a human opened the primary document at this code and confirmed this row,"
and the two must not be conflated when deciding whether to flip `verified`.

**These four rows still say `verified=false`.** Extracting real values via
this project's own tooling is not the same as a human opening the primary
source and checking them — see CLAUDE.md's round-4 addendum on
self-attestation. A human should cross-check the pasted grep/extract output
in this build's commit history against the primary IFCT2017.pdf — Table 1
spans book pages 1-30, organized by food-group code (A = cereals, B =
pulses/legumes, F = vegetables) — at each of A015, B020, B021 and F006
directly, and flip `verified` to `true` per row themselves, once satisfied.
Matching against the Zenodo re-publication a second time is not a substitute
for that step; it would just repeat the same secondary source.

The corresponding `*_cooked`/`*_boiled` rows (`rice_cooked`, `toor_dal_cooked`,
`rajma_cooked`, `potato_boiled`) are untouched and still fully hand-entered
approximations; each now points at its raw sibling and the relevant
`yield.*` constant in `citations.py` in its own `source_note`, rather than
being re-derived — that derivation is future work, not done here.

### The two oil rows are a different, closed case

IFCT 2017 does carry codes for gingelly oil (T004) and sunflower oil (T012),
but their tabulated rows (via the same re-publication) report
`energy_kcal=0` and every micronutrient at `0` alongside `fat=100 g` — this
source simply does not tabulate a full nutrient panel for oils, only a fatty
acid profile elsewhere in the tables. This isn't an ordinary unverified gap
that a human opening the PDF could close: a different source entirely (e.g.
USDA FoodData Central) would be needed, and that is out of scope here. Both
rows' `source_note` says this explicitly.

## A fifth row carries real IFCT 2017 data, from a different mirror (2026-08-16, TASKS_3.md R3a)

`egg_boiled` (IFCT code M004, "Egg, poultry, whole, boiled", group M) is the
first ingredient row this build added after R1a's diet-class model landed.
Its composition (energy, protein, fat, carb, fibre, sodium, iron, calcium)
was retrieved from **`github.com/nodef/ifct2017`**, not the Zenodo
re-publication (`ifct2017/ifct2017`) the four rows above used — same
underlying NIN measurement and the same digitization lineage (`nodef` is the
actively-maintained source repo the Zenodo releases are cut from), but a
different distribution, used specifically because the Zenodo mirror's own
`compositions/index.csv` (same file, byte-for-byte, just re-hosted) truncated
before reaching group M under this build's fetch tooling on every CDN tried
(`unpkg`, `jsdelivr`, `raw.githubusercontent.com`) — group M is the 13th of
20 food groups in file order, and the file is 1.15 MB, well past whatever
this build's tooling caps a single fetch at. `curl`-ing the raw file directly
and grepping it locally (rather than through a fetch tool that summarizes
the page) is what actually got past the cap; that method should work for any
future row this size or position blocks on. Same evidentiary weight as the
four rows above: a second party's transcription, not a human having opened
the primary `IFCT2017.pdf` — `verified=false` for the same reason.

**Vitamin B12 could not come from IFCT at all, for a structural reason, not
an egg-specific one.** The `compositions/index.csv` schema was checked
programmatically against every one of its 421 column headers for `b12`,
`cbl` or `cobal` in any form — zero matches. IFCT 2017's compositions table
does not tabulate vitamin B12 for *any* food, not just egg. `egg_boiled`'s
`b12_ug` (1.11) is therefore sourced from a different, DOI-free but
citable source instead — USDA FoodData Central, SR Legacy, FDC ID 173424
("Egg, whole, cooked, hard-boiled") — and the row's `source_note` says so in
capital letters at the point where the value appears, specifically so this
single field is never mistaken for an IFCT figure while every other field on
the same row is one. This is a **flagged, single-field exception**, not a
default: the alternative (leaving `b12_ug` at an implicit `0`, which every
loader-visible row before this one happened to have as a real possible
value) would have silently claimed egg has no B12, which is false and would
have been the exact "silence reads as certainty" failure CLAUDE.md's
"Things that have gone wrong before" section already lists three instances
of.

**`diaas` (1.35) is sourced, not authored** — unlike `paneer_fresh`,
`tofu_firm` and `soya_chunks_dry` above, all three of which are recalled
from a remembered range with no primary source opened. Fanelli NS, Martins
JCFR, Stein HH, "The digestible indispensable amino acid score (DIAAS) in
eggs and egg-containing breakfast meals is greater than in toast breads or
hash browns served without eggs," *Journal of Nutritional Science*
2024;13:e68, DOI 10.1017/jns.2024.71 — reports DIAAS = 135% for boiled egg
under the reference amino-acid pattern for individuals older than 3 years
(this project plans meals for adults, not infants; the same paper's
6–36-month reference pattern gives 110% instead, not the figure used here).

## Conventions

- One row per (food, state). `state` is `raw`, `cooked` or `as_used`.
- Nutrients are **per 100 g edible portion** in the stated `state`.
- `carb_g` is **total carbohydrate including dietary fibre**; `fibre_g` is the
  fibre subset of it. The loader's Atwater reconciliation charges protein and
  fat at 4/9 kcal/g, *available* carbohydrate (`carb_g - fibre_g`) at
  4 kcal/g, and fibre separately at 2 kcal/g (`atwater.fibre_kcal_per_g`,
  corrected 2026-07-24 to match IFCT 2017's own stated energy methodology).
  Before that correction, fibre was charged at the same 4 kcal/g rate as
  available carbohydrate, which over-estimated energy for fibre-rich foods —
  real IFCT rajma data failed the 15% reconciliation tolerance at 19% under
  the old formula and passes at 8% under the corrected one.
- `allergens` is a `|`-separated list, empty for none.
- Booleans are `true`/`false`.

## TODO — real ingest

Replace this file with a genuine IFCT 2017 subset:

1. Obtain IFCT 2017 (NIN Hyderabad).
2. Extract the rows for the foods listed here, keeping the published food code
   in `ifct_code`.
3. Prefer IFCT's own cooked-state entries where they exist. Where they do not,
   convert through a registered yield factor in
   `core/nutrition/citations.py` — never an inline multiplication.
4. A human who has read the source may then set `verified` to `true`, per row.
   Nobody else may.
