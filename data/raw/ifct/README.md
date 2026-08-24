# `data/raw/ifct/` — provenance

## What is actually in here

`fixture_ingredients.csv` is mostly a **hand-entered fixture set**, not an
IFCT extract, plus seven rows carrying real IFCT 2017 values: four updated
2026-07-24, one (`egg_boiled`) added 2026-08-16 (TASKS_3.md R3a), and two
more (`chicken_breast_raw`, `pomfret_white_raw`) added the same day
(TASKS_3.md R3b — see below). 31 of its 32 rows have `verified` set to
`false`; 25 have an empty `ifct_code`. Both are deliberate:

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

## Two more rows carry real IFCT 2017 data, with a derived (not quoted) DIAAS (2026-08-16, TASKS_3.md R3b)

`chicken_breast_raw` (IFCT code N003, group N — Poultry) and
`pomfret_white_raw` (IFCT code P057, group P — Marine Fish) were added on the
same footing as `egg_boiled` for macro composition: retrieved from
`github.com/nodef/ifct2017`'s `compositions/index.csv`, `verified=false` for
the same reason (a second party's transcription, not a human having opened
the primary `IFCT2017.pdf`). Both reconcile cleanly under this build's
Atwater check. `chicken_breast_raw` uses N003 (breast) rather than N001
(leg): N001's own stated energy fails Atwater reconciliation by roughly 2x
(383.6 kcal stated vs 191.5 kcal implied by its protein and fat) — an
internal error in that IFCT row, found by this build's own check, not used
anywhere.

**Neither row has a cooked-state IFCT entry.** Unlike egg (which had a real
`M004`, "boiled"), IFCT's poultry and marine-fish groups are tabulated
raw-only. Both rows are therefore used **as raw** for what will be a cooked
quantity in any recipe built on them — an unresolved approximation, larger
than the accepted onion/tomato-in-gravy convention, because meat loses
substantially more mass to water on cooking than a vegetable does. No yield
factor is registered in `core/nutrition/citations.py` to correct for this,
and none was sourced in this task. Flagged here and in each row's
`source_note`; a future task should either source a cooked-state IFCT/USDA
entry or register a meat-specific cooking-yield factor.

**B12** for both rows is a single-field, flagged exception to the IFCT
sourcing above, the same pattern `egg_boiled` established: IFCT tabulates no
B12 for any food. `chicken_breast_raw`'s `b12_ug` (0.34) is USDA FoodData
Central FDC ID 171477 ("Chicken, broilers or fryers, breast, meat only,
cooked, roasted"). `pomfret_white_raw`'s `b12_ug` (1.86) is USDA FDC ID
175177 ("Fish, tilapia, cooked, dry heat") — **not pomfret**, which USDA does
not carry; tilapia stands in as the closest available lean-whitefish match,
the same substitution used for the DIAAS derivation below.

### `diaas` on both rows is DERIVED BY THIS BUILD, not quoted from a published score

This is a third, weaker evidentiary tier below `egg_boiled`'s "sourced, not
authored" DIAAS (itself already one step below a primary source a human has
opened): a published score is copied from a paper; a **derived** score is
computed here, by this build, by combining a published *digestibility* input
with a separately sourced *amino-acid-content* table against the published
FAO reference pattern. Every place either number appears — this README, the
CSV `source_note`, and any future recipe file's header comment — must say
"derived", not "sourced", for exactly this reason. The computation follows
FAO Food and Nutrition Paper 92 (2013), *Dietary protein quality evaluation
in human nutrition: Report of an FAO Expert Consultation*, Table 5's "older
child, adolescent, adult" scoring pattern (mg/g protein: His 16, Ile 30,
Leu 61, Lys 48, SAA 23, AAA 41, Thr 25, Trp 6.6, Val 40) — the same pattern
`egg_boiled`'s quoted DIAAS itself rests on, read here directly from the FAO
PDF. For each indispensable amino acid, `ratio = content_mg_per_g_protein ×
true_ileal_digestibility ÷ reference_mg_per_g_protein`; the DIAAS is the
*minimum* ratio across all amino acids assessed (the limiting amino acid),
not truncated at 100% — DIAAS scores for single foods are not capped, unlike
PDCAAS; FAO 2013's own worked example caps only mixed-diet calculations.
Where only one member of a combined group (SAA = Met+Cys, AAA = Phe+Tyr) had
a measured digestibility figure, that figure was applied to the whole
group's content — the same convention the source papers themselves use when
only one group member was assayed.

**Why amino-acid *content* was sourced from USDA, not from this file's own
IFCT columns.** IFCT's amino-acid columns were checked against typical
physiological ranges before use — the same discipline this build already
applies to macro energy via Atwater reconciliation, extended here to amino
acids because DIAAS is highly sensitive to whichever one is limiting. Three
implausible values turned up this way: IFCT's cysteine figure for N003
(chicken breast) implies roughly 92 mg cysteine per g protein against a
normal range near 13 mg/g; Rohu (S006) shows a similarly inflated cysteine
figure; and IFCT's phenylalanine figure for P057 (Pomfret) implies roughly
64 mg/g protein against a typical range of 38–42 mg/g. These are scattered
per-row/per-amino-acid errors, not a single correctable scale bug, so IFCT's
amino-acid columns are not used anywhere in either derivation below. Amino-
acid content for both rows instead comes from USDA FoodData Central — the
same cooked chicken-breast (FDC 171477) and tilapia (FDC 175177) items used
for B12 above.

**Chicken — digestibility.** Kashyap S, Shivakumar N, Varkey A, Duraisamy R,
Thomas T, Preston T, Devi S, Kurpad AV, "Ileal digestibility of intrinsically
labeled hen's egg and meat protein determined with the dual stable isotope
tracer method in Indian adults," *Am J Clin Nutr* 2018;108(5):980–987, DOI
10.1093/ajcn/nqy178 (open access, CC BY 4.0, full text at
eprints.gla.ac.uk/187598/1/187598.pdf) — Table 4, true ileal digestibility in
healthy Indian adults, cooked (pressure-cooked, pooled breast/wing/
thigh/drumstick) chicken meat, the same preparation this project's chicken
recipes use: methionine 92.7%, phenylalanine 94.4%, threonine 93.7%, lysine
95.5%, leucine 89.1%, isoleucine 88.8%, valine 89.6%. Tryptophan (95.9%) is
from the same lab's follow-up paper, Kashyap S, Devi S, Pasanna RM, Preston
T, Kurpad AV, "True Digestibility of Tryptophan in Plant and Animal
Protein," *J Nutr* 2024;154(11):3203–3209, DOI 10.1016/j.tjnut.2024.09.014,
PMID 39307282 — the Trp figure only, read from the freely visible PubMed
abstract; the paper's own full DIAAS table is paywalled (confirmed
not-open-access via the Unpaywall API) and was never reached. **Histidine is
unassessed, not guessed**: no histidine digestibility figure was found in
either paper, and none was estimated to fill the gap. Of the 8 amino acids
that do have both a digestibility and a content figure, **leucine is
limiting at 109.6%** (valine close behind at 111.1%); the resulting DIAAS is
**1.10**, reported to 2 significant figures because histidine, once
measured, could in principle move the true score. This 8-of-9, Indian-adult,
same-preparation dataset is a stronger foundation for chicken specifically
than the pig-model alternative below — real adult humans, not a cross-species
model, eating chicken cooked the way this project's recipes cook it.

**Fish — digestibility, and a named cross-species substitution.** Hodgkinson
SM, Stroebinger N, Stein HH, Fanelli NS, de Vries S, van der Wielen N,
Hendriks WH, Moughan PJ, "True Ileal Amino Acid Digestibility of Human Foods
Classified According to Food Type as Determined in the Growing Pig," *J
Nutrition* 2025;155:3384–3400 — a 97-food pig-model study. Its "Fish, white"
column was identified as **tilapia** (fillets, boiled 10 min then diced) by
elimination: the same table (Table 2) carries separate "Salmon" and
"Sardines" columns elsewhere, so "Fish, white" is the third tested species,
and "white" matches tilapia's white flesh against salmon's pink and
sardines' oily, dark flesh. Pomfret itself was not among the three fish
species Hodgkinson et al. tested. Tilapia was chosen as its proxy — over
salmon or sardines — because tilapia and pomfret are both lean, white-
fleshed fish of similar macro-composition (roughly 19–20% protein, under 6%
fat), where salmon and sardines are both markedly fattier, oilier fish and
would be a worse structural match. To keep the derivation internally
coherent, **both** the digestibility figures and the amino-acid-content
figures used are tilapia's (Hodgkinson for digestibility, USDA FDC 175177
for content) — not tilapia digestibility mixed with Pomfret's own (already
distrusted, see above) amino-acid content. The result is therefore a
**tilapia** DIAAS, applied to Pomfret as the best available proxy — a second,
distinct approximation layered on top of "derived, not quoted," named here
and in the row's `source_note` rather than left implicit. All 9 indispensable
amino acids have both a digestibility and a content figure for this
substitution (no gap, unlike chicken); **valine is limiting at 115.8%**, so
the resulting DIAAS is **1.16**.

## A sixth row carries a real, published DIAAS and USDA composition — not IFCT, and stronger than the derived-DIAAS tier above (2026-08-22, TASKS_3.md R4c)

`soya_flour_defatted` is not IFCT data at all — this build has no primary IFCT
entry for soya flour, and neither of the previous two evidentiary tiers
(`egg_boiled`'s IFCT-sourced macros with a quoted DIAAS from a second paper, or
`pomfret_white_raw`'s IFCT macros with a DIAAS *derived by this build* from raw
FAO amino-acid tables) applied. This row uses a **published, quoted DIAAS** —
the strongest tier yet, one step below a primary source a human has opened —
paired with USDA FoodData Central composition, because no IFCT row exists to
pair it with.

**DIAAS 1.05**, Mathai JC, Liu Y, Stein HH, "Values for digestible
indispensable amino acid scores (DIAAS) for some dairy and plant proteins may
better describe protein quality than values calculated using the concept for
protein digestibility-corrected amino acid scores (PDCAAS)," *British Journal
of Nutrition* (2017) 117:490–499, DOI 10.1017/S0007114517000125 — Table 7,
"3 years and above" row (the adult FAO 2013 reference amino-acid pattern, the
same standard `egg_boiled`, `chicken_breast_raw` and `pomfret_white_raw` are
matched to). Soya flour scores 105% (DIAAS 1.05), sulfur amino acids
first-limiting. The same table's soy protein isolate scores 98% and soy
protein concentrate 73% (below the 0.75 threshold) — soya flour, not one of
the other two soy products, is the row added here, because it is the one that
qualifies and the one whose composition is independently available (below).

The paper's own Table 1 states the tested soya flour was 52.29% crude protein
(Archer Daniels Midland Company). That figure is not this row's `protein_g` —
it constrains which composition source may honestly stand in for the same
product, per CLAUDE.md invariant 3 ("a citation must match the mechanism, not
just exist").

**Composition**: USDA FoodData Central, SR Legacy, FDC ID 174275, "Soy flour,
defatted," published 2019-04-01 — protein 51.46 g, fat 1.22 g,
carbohydrate-by-difference 33.92 g, fibre 17.50 g, sodium 20 mg, iron 9.24 mg,
calcium 241 mg, vitamin B-12 0 µg (reported, not absent — the correct
biological fact for a plant food, not a missing-data gap the way `chicken_breast_raw`'s
b12 substitution was). 51.46% protein is a close match to the DIAAS paper's own
52.29%, not the mismatched full-fat soy flour composition (much higher fat,
lower protein density per 100 g) that a less careful pairing would have used.
A second FDC entry (Foundation Foods, FDC ID 1104705, published 2020-10-30:
protein 51.1 g, fat 3.33 g, fibre 24.3 g) was checked and set aside — less
aligned on fat and fibre, no reason to prefer it over SR Legacy 174275.
Cross-checked against USDA Agriculture Handbook 8-16 (secondary citation,
via fearn.pair.com): sodium 20 mg, iron 9.24 mg and calcium 241 mg match
174275 exactly; protein/carb differ slightly (47.0 g / 38.4 g) across
editions, expected for different lots and years, not a discrepancy that
changes which row this is.

Energy reconciles under this build's own Atwater convention (see Conventions
below): 51.46×4 + 1.22×9 + (33.92−17.50)×4 + 17.50×2 = 317.6 kcal against the
stated 327 kcal — 2.9% off, well inside the 15% tolerance.

`verified=false`, same as every other row in this file, regardless of this
row's stronger sourcing tier: CLAUDE.md invariant 4 requires a human to have
opened the primary source before `verified=true` — the Mathai/Liu/Stein PDF
and the USDA FDC API were read and queried by this assistant, which does not
satisfy that rule. `classes=''` (plant protein, no `IngredientClass` applies)
and `allergens='soya'`, matching `tofu_firm` and `soya_chunks_dry`'s existing
convention for soya-derived rows.

## A seventh row closes a structural zero rather than adding a qualifying protein (2026-08-24, TASKS_3.md follow-up to finding 51)

`soya_curd_plain` is not sourced to make anything qualify as a protein source
— unlike `soya_flour_defatted` above, no DIAAS is claimed or derived here, and
the `diaas` column is left blank on purpose. Its job is narrower: finding 51
(`docs/audit_log.md`, 2026-08-22) established that `SOUTH_LUNCH.curd_course`
is a *required* slot accepting only the `curd`/`buttermilk` categories, and
the library's only recipe in either category was `thayir_plain`, which is
dairy. Vegan `south_indian/lunch` therefore enumerated **zero** combinations
— not a bound failure any relaxation rung could reach, a structural absence
of any eligible recipe. This row and the recipe built on it
(`data/recipes/soya_curd.yaml`) exist to close exactly that gap, with one real
dish, without touching the template or the category vocabulary.

**Composition**: USDA FoodData Central, SR Legacy, FDC ID 175227, "SILK Plain
soy yogurt," published 2019-04-01, retrieved 2026-08-24 — energy 66 kcal,
protein 2.64 g, fat 1.76 g, carbohydrate-by-difference 9.69 g, fibre 0.4 g,
sodium 13 mg, calcium 132 mg, vitamin B-12 0 µg (reported, not absent — an
unfortified soy product, the same "correct biological zero, not a missing-data
gap" distinction `soya_flour_defatted`'s b12 makes above). Energy reconciles
under this build's Atwater convention: 2.64×4 + 1.76×9 + (9.69−0.4)×4 + 0.4×2
= 64.36 kcal against the stated 66 kcal — 2.5% off, well inside the 15%
tolerance.

**Iron is a cross-product substitution**, named plainly rather than left
blank: FDC 175227's full nutrient list carries no iron row at all — confirmed
by reading the complete list returned by the FDC API, not inferred from an
absent field, per this project's own "silence must cost more, not less" rule
(CLAUDE.md, same concern `chicken_breast_raw`'s B12 gap raised). FDC ID
175218, "SILK Plain, soymilk" — same brand, same "Plain" unsweetened
formulation, same SR Legacy publication batch (2019-04-01, very likely the
same manufacturer submission cycle as the yogurt item) — reports iron 0.44 mg
per 100 g; that figure is used here. This is one step weaker than a
same-product measurement, flagged rather than hidden: fermenting soymilk into
yogurt does not itself add or remove iron, but the two products' own
formulations are not guaranteed identical. No iron figure for the yogurt item
itself, and no closer proxy, was found in FDC.

**Mechanism-match check** (CLAUDE.md invariant 3): FDC 175227 is a plain,
unsweetened cultured soy yogurt — the same preparation as the recipe this row
feeds (soymilk set into curd with a starter culture, the same way dairy milk
becomes dahi), not a sweetened or flavoured soy yogurt, which would misstate
`carb_g`.

`verified=false`, same as every row in this file: CLAUDE.md invariant 4
requires a human to have opened the primary source before `verified=true` —
the USDA FDC API was queried by this assistant, which does not satisfy that
rule. `classes=''` (fermented soymilk carries no dairy classification, so this
row is vegan-eligible by the same class-derivation mechanism as
`soya_flour_defatted`) and `allergens='soya'`, matching the existing
soya-derived-row convention.

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
