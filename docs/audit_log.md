# Audit log

Dated, append-only. Per CLAUDE.md's audit-workflow section, this file is the
artifact: a finding that isn't written here did not happen. Findings are
recorded whether or not they are fixed; the "Disposition" line says which.

Newest entries at the top.

## 2026-10-09 — N26: banana and milk tea join the snack plates

**Asked.** Owner, 2026-10-09, "option 1": after removing the snack carb
ceiling (N25), add banana and tea with their sources, and show before and
after before merging. Separate commit from N25 (CLAUDE.md rule 8).

**Sources.** All four rows `verified=false` (invariant 4); each row's
`source_note` carries the full reading.
- `banana_ripe`: IFCT 2017 E012 "Banana, ripe, robusta", n=6, read from the
  primary `IFCT2017.pdf`. Table 1 PDF p.49; Ca/Fe Table 5 p.167; Na p.168.
- `milk_cow_whole`: IFCT 2017 L002 "Milk, whole, Cow", n=6. Table 1 PDF p.57;
  Ca/Fe p.183; Na p.184. B12 0.45 ug is a cross-source substitution from
  USDA FDC 171265 (IFCT gives none), named in the note. DIAAS blank: not
  sourced, so milk is not counted as quality protein.
- `sugar_white`: USDA FDC 169655 (IFCT 2017 has no refined sugar).
- `tea_black_brewed`: USDA FDC 173227 (not in IFCT 2017).
- One banana = 118 g, USDA FDC 173944 "medium".
- **Not sourced, stated as assumptions:** one cup of tea = 70 g milk + 80 g
  brewed tea + 8 g sugar (no source for a typical Indian cup found); at most
  two bananas per snack.

**Built.**
- `data/recipes/banana.yaml` (pan-Indian, category `fruit`, uncooked,
  1-2 bananas) and `data/recipes/milk_tea.yaml` (pan-Indian, category `tea`,
  one cup). Milk tea is boiled and no boiled-milk constant is registered, so
  the loader required every macro the milk row feeds to be declared
  unassessed; it is, so milk tea carries the wide band (protein 0.45, the
  same as idli and phulka).
- `core/foods/templates.py`: South snack's main slot accepts `fruit`; North
  snack's main slot accepts `fruit`; both drink slots accept `tea`. No other
  template accepts either kind, so breakfast, lunch and dinner cannot change.
- `core/foods/models.py`: "banana" and "tea" added to `MAIN_INGREDIENTS`.

**Before / after.** `docs/design/probes/probe_banana_tea_dishes.py`, 18
bodies per row (3 goals x 2 sexes x 55/70/90 kg, 170 cm, 30 y, moderate).
"options" is the number of different dishes offered in the swap menus,
summed over bodies. "asked" is bodies whose plate passes when they pick that
dish. Both sides byte-identical under PYTHONHASHSEED=1 and 777.

Before (HEAD d3eb627, N25):
```
south_indian  vegetarian      plate 18, unrelaxed 18, options 54, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown 10x  neer_mor + soya_chana_sundal
    shown  8x  soya_chana_sundal
south_indian  eggetarian      plate 18, unrelaxed 18, options 60, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown 10x  neer_mor + soya_chana_sundal
    shown  8x  soya_chana_sundal
south_indian  non_vegetarian  plate 18, unrelaxed 18, options 60, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown 10x  neer_mor + soya_chana_sundal
    shown  8x  soya_chana_sundal
south_indian  vegan           plate 18, unrelaxed 18, options 29, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown 13x  soya_chana_sundal
    shown  5x  soya_chunk_sundal
north_indian  vegetarian      plate 18, unrelaxed 18, options 51, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown  7x  chaas + soya_chana_chaat
    shown  8x  soya_chana_chaat
    shown  3x  soya_chana_chaat + soya_tikka
north_indian  eggetarian      plate 18, unrelaxed 18, options 63, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  8x  anda_chaat + soya_chana_chaat
    shown  4x  chaas + soya_chana_chaat
    shown  1x  soya_chana_chaat
    shown  1x  soya_chana_chaat + soya_tikka
north_indian  non_vegetarian  plate 18, unrelaxed 18, options 63, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  8x  anda_chaat + soya_chana_chaat
    shown  4x  chaas + soya_chana_chaat
    shown  1x  soya_chana_chaat
    shown  1x  soya_chana_chaat + soya_tikka
north_indian  vegan           plate 8, unrelaxed 8, options 8, banana in shown 0, milk_tea in shown 0, banana asked not in library, milk_tea asked not in library
    shown  8x  soya_chana_chaat
```

After:
```
south_indian  vegetarian      plate 18, unrelaxed 18, options 82, banana in shown 0, milk_tea in shown 12, banana asked 10, milk_tea asked 18
    shown 10x  milk_tea + soya_chana_sundal
    shown  2x  milk_tea + soya_chunk_sundal
    shown  5x  neer_mor + soya_chana_sundal
    shown  1x  soya_chana_sundal
south_indian  eggetarian      plate 18, unrelaxed 18, options 88, banana in shown 0, milk_tea in shown 12, banana asked 10, milk_tea asked 18
    shown 10x  milk_tea + soya_chana_sundal
    shown  2x  milk_tea + soya_chunk_sundal
    shown  5x  neer_mor + soya_chana_sundal
    shown  1x  soya_chana_sundal
south_indian  non_vegetarian  plate 18, unrelaxed 18, options 88, banana in shown 0, milk_tea in shown 12, banana asked 10, milk_tea asked 18
    shown 10x  milk_tea + soya_chana_sundal
    shown  2x  milk_tea + soya_chunk_sundal
    shown  5x  neer_mor + soya_chana_sundal
    shown  1x  soya_chana_sundal
south_indian  vegan           plate 18, unrelaxed 18, options 35, banana in shown 2, milk_tea in shown 0, banana asked 6, milk_tea asked 0
    shown  2x  banana
    shown 12x  soya_chana_sundal
    shown  4x  soya_chunk_sundal
north_indian  vegetarian      plate 18, unrelaxed 18, options 86, banana in shown 13, milk_tea in shown 4, banana asked 18, milk_tea asked 16
    shown  1x  banana + chaas
    shown  3x  banana + chaas + soya_chana_chaat
    shown  6x  banana + chaas + soya_tikka
    shown  3x  banana + soya_tikka
    shown  3x  milk_tea + soya_chana_chaat
    shown  1x  milk_tea + soya_tikka
    shown  1x  soya_chana_chaat
north_indian  eggetarian      plate 18, unrelaxed 18, options 102, banana in shown 2, milk_tea in shown 7, banana asked 18, milk_tea asked 16
    shown  1x  anda_chaat + banana
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  7x  anda_chaat + milk_tea + soya_chana_chaat
    shown  4x  anda_chaat + soya_chana_chaat
    shown  1x  banana + chaas
    shown  1x  soya_chana_chaat
north_indian  non_vegetarian  plate 18, unrelaxed 18, options 102, banana in shown 2, milk_tea in shown 7, banana asked 18, milk_tea asked 16
    shown  1x  anda_chaat + banana
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  7x  anda_chaat + milk_tea + soya_chana_chaat
    shown  4x  anda_chaat + soya_chana_chaat
    shown  1x  banana + chaas
    shown  1x  soya_chana_chaat
north_indian  vegan           plate 15, unrelaxed 15, options 23, banana in shown 10, milk_tea in shown 0, banana asked 11, milk_tea asked 0
    shown  4x  banana
    shown  6x  banana + soya_chana_chaat
    shown  5x  soya_chana_chaat
```

**Read.**
- No region or diet lost a plate. North vegan rose from 8/18 to 15/18
  snack plates, all unrelaxed; every other row stays 18/18 unrelaxed.
- Banana is on 29 of 144 shown plates, mostly North (vegetarian 13, vegan
  10). In the South it is shown only to vegans (2): for other diets the
  sundal fits better. Picked by hand it passes for 10/18 South
  non-vegan bodies, 6/18 South vegan, 18/18 North non-vegan, 11/18 North
  vegan.
- Milk tea is on 54 of 144 shown plates and passes when picked for 18/18
  South and 16/18 North bodies of every non-vegan diet. It never appears for
  vegans (dairy).
- Swap menus grew: South vegetarian 54 to 82 options, North eggetarian 63
  to 102.
- Neer mor is shown less (South: 10 to 5 plates per non-vegan diet): milk
  tea now takes the drink place on most of those plates.

**Deletion check.** `d4b_mutations.py` gains a `TEMPLATES` module and rows
FT1-FT4, one per accepted kind added. Full failure lists,
PYTHONHASHSEED=0:
```
   all failures (1):
      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_south_snack_is_one_dish_and_an_optional_drink
FT1  covered      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_south_snack_is_one_dish_and_an_optional_drink
   all failures (1):
      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_south_snack_is_one_dish_and_an_optional_drink
FT2  covered      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_south_snack_is_one_dish_and_an_optional_drink
   all failures (1):
      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_north_snack_offers_two_dish_kinds_and_an_optional_drink
FT3  covered      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_north_snack_offers_two_dish_kinds_and_an_optional_drink
   all failures (1):
      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_north_snack_offers_two_dish_kinds_and_an_optional_drink
FT4  covered      tests/test_templates_and_portions.py::TestTemplatesAreNotUniform::test_north_snack_offers_two_dish_kinds_and_an_optional_drink
====================================================================================================
4 mechanisms: 4 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```
Each mutation turns exactly one test red: the shape test that pins the
slot's accepted kinds. No end-to-end test notices a fruit or tea removal on
its own.

**Tests changed.** Fixed counts and lists updated with dated comments:
ingredient rows 37 to 41, unverified warnings 36 to 40, IFCT-coded rows plus
E012 and L002, `NO_OIL_COOKED` plus milk_tea, and the two snack shape tests
(now also pin both drink slots). `tests/test_web_add_dish.py` re-picked its
example as its own header asks: milk tea now fills the 70 kg South snack's
drink, and no plate for that body leaves a course empty with exactly one
dish to offer; the snack step now uses a 55 kg eggetarian woman's North
snack (drink empty, chaas the one option).

**Suite.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q`, servers
up, same session:
```
674 passed, 1 warning in 281.69s (0:04:41)
```

**Open.** Vada (no measured source, needs an oil-uptake constant). No
boiled-milk constant. The cup proportion and the two-banana ceiling are
authored, not sourced.

## 2026-10-09 — N25: a snack has no carbohydrate ceiling

**Asked.** Owner, 2026-10-09, after N24 stopped at the snack carb ceiling:
search for evidence on how much of a real snack's energy is carbohydrate,
show it, then (owner chose option 1) remove the ceiling for snacks only and
measure before and after.

**What the code had.** A snack's carb ceiling was the day carbohydrate
target scaled by 0.10, plus `tolerance.fat_carb_default` (0.15), widened to
`tolerance.fat_carb_relaxed` (0.25) by the ladder. The day carbohydrate is
the energy left after protein and the AMDR-midpoint fat (`_compute_macros`
in `core/nutrition/targets.py`). Both tolerances are `PROJECT_DECISION`, no
source. N24 measured it: at most 70-79% of a snack's energy floor may be
carbohydrate, and a banana is 97% (IFCT 2017 E012).

**Sources searched, intake data first.** Found:
- Norkost 3, Norway (Food Nutr Res 2015, PMC4409996; 1787 adults, two
  24-hour recalls). Snacks: 52% (men) and 53% (women) of energy from
  carbohydrate; main meals 42%. Snacks eaten at work 64%. Fruits among the
  top five snack energy sources (cakes, fruits, sugar/sweets, bread,
  alcoholic beverages).
- NutriNet-Sante, France (PMC5828417; 104,265 adults, 24-hour records).
  Fruit and hot beverages among the main food groups giving snack energy. No
  snack carbohydrate share reported.
- UDAY, India (PMC7616315): fruits and tea/coffee among the 10 snack types
  asked about; no nutrient content.
Searched, no per-snack nutrient split: ICMR-INDIAB-21 (Nat Med 2025,
day-level, 62% carbohydrate), I-STARCH-1 (Nutrients 2026, day-level, 62.1%),
NIN What India Eats (day-level), ultra-processed food intake in Indian adults
(PMC10755415, day-level). **No Indian study found splits nutrients by
snack.**

**Read, stated plainly.** The Norway averages (52-64%) sit *under* the old
ceiling. What the ceiling blocked was single-food snacks such as fruit,
which are common in all three studies. The case for removing it is that one
snack is often one food, not that the average snack is over it -- the same
reasoning as the 2026-09-25 decision to drop the snack's fat and carb floors.
The snack's energy ceiling still caps an all-carbohydrate snack.

**Change.** `core/nutrition/meal_target.py`: new `_CEILINGLESS_BY_SLOT =
{SNACK: {"carb_g"}}`, popped beside the floors. The carb point stays; the
fat ceiling stays. `_widen_band` widens only ceilings that exist, so no rung
restores it (tested). Methodology: new section "A snack has no carbohydrate
ceiling", and a dated note on the fat/carb floor section, which said a snack
keeps both ceilings.

**Before and after.** `docs/design/probes/probe_snack_carb_ceiling.py` (the
N23 probe with the bounds column changed), 18 bodies per region x diet. Each
side byte-identical under PYTHONHASHSEED=1 and 777. Before is identical to
N23's AFTER apart from that column. `diff before after`:

```
1c1
< south_indian  vegetarian      carb ceiling 22.3-46.0; bodies 18, plate 18, unrelaxed 18, options 54
---
> south_indian  vegetarian      carb ceiling none; bodies 18, plate 18, unrelaxed 18, options 54
4c4
< south_indian  eggetarian      carb ceiling 22.3-46.0; bodies 18, plate 18, unrelaxed 18, options 60, egg asked 6
---
> south_indian  eggetarian      carb ceiling none; bodies 18, plate 18, unrelaxed 18, options 60, egg asked 6
7c7
< south_indian  non_vegetarian  carb ceiling 22.3-46.0; bodies 18, plate 18, unrelaxed 18, options 60, egg asked 6
---
> south_indian  non_vegetarian  carb ceiling none; bodies 18, plate 18, unrelaxed 18, options 60, egg asked 6
10c10
< south_indian  vegan           carb ceiling 22.3-46.0; bodies 18, plate 18, unrelaxed 17, options 29
---
> south_indian  vegan           carb ceiling none; bodies 18, plate 18, unrelaxed 18, options 29
13,16c13,15
< north_indian  vegetarian      carb ceiling 22.3-46.0; bodies 18, plate 18, unrelaxed 18, options 50
<     shown  6x  chaas + soya_chana_chaat
<     shown  4x  chaas + soya_chana_chaat + soya_tikka
<     shown  3x  soya_chana_chaat
---
> north_indian  vegetarian      carb ceiling none; bodies 18, plate 18, unrelaxed 18, options 51
>     shown  7x  chaas + soya_chana_chaat
>     shown  8x  soya_chana_chaat
18,19c17
<     shown  2x  soya_tikka
< north_indian  eggetarian      carb ceiling 22.3-46.0; bodies 18, plate 18, unrelaxed 18, options 63
---
> north_indian  eggetarian      carb ceiling none; bodies 18, plate 18, unrelaxed 18, options 63
22a21
>     shown  1x  soya_chana_chaat
24,25c23
<     shown  1x  soya_tikka
< north_indian  non_vegetarian  carb ceiling 22.3-46.0; bodies 18, plate 18, unrelaxed 18, options 63
---
> north_indian  non_vegetarian  carb ceiling none; bodies 18, plate 18, unrelaxed 18, options 63
28a27
>     shown  1x  soya_chana_chaat
30,32c29,30
<     shown  1x  soya_tikka
< north_indian  vegan           carb ceiling 22.3-46.0; bodies 18, plate 6, unrelaxed 3, options 6
<     shown  6x  soya_chana_chaat
---
> north_indian  vegan           carb ceiling none; bodies 18, plate 8, unrelaxed 8, options 8
>     shown  8x  soya_chana_chaat
```

**Read.** No banana or tea yet, so this only changes existing dishes:
- A passing snack plate: 132 -> 134 of 144 (North vegan 6 -> 8).
- Passing with no relaxation: 128 -> 134 (South vegan 17 -> 18, North vegan
  3 -> 8).
- North vegetarian shows soya_chana_chaat alone more often and the tikka
  plates less (the chaat was being held back by carbohydrate).

**Deletion checks.** New row SP4 in `docs/design/probes/d4b_mutations.py`.
Full failure list per mutation (SP1-SP3 rerun), whole suite, no `-x`,
`PYTHONHASHSEED=0`:

```
   all failures (1):
      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
SP1  covered      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
   all failures (1):
      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_quality_protein_floor
SP2  covered      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_quality_protein_floor
   all failures (1):
      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
SP3  covered      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
   all failures (2):
      tests/test_nutrition_meal_target.py::TestASnackHasNoFatOrCarbFloor::test_the_fat_carb_rung_does_not_restore_a_dropped_floor
      tests/test_nutrition_meal_target.py::TestASnackHasNoCarbCeiling::test_a_snack_has_no_carb_ceiling
SP4  covered      tests/test_nutrition_meal_target.py::TestASnackHasNoFatOrCarbFloor::test_the_fat_carb_rung_does_not_restore_a_dropped_floor
====================================================================================================
4 mechanisms: 4 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

**Suite.** Both dev servers running:

```
$ FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p no:cacheprovider
674 passed, 1 warning in 285.63s (0:04:45)
```

**Disposition.** DONE on branch `everyday-snacks`. Banana and tea dishes
are the next commit (N26), measured separately.

## 2026-10-09 — N24: a banana or tea snack cannot fit any snack target -- stopped at premise

**Asked.** Owner, 2026-10-09, after N23 merged: add real low-protein snacks
-- banana, vada, tea -- each backed by a published source.

**Premise.** N23 removed the snack's protein floors so that snacks like
these could be served. That assumed protein was what kept them out. Before
building any dish, the arithmetic.

**Which snacks, from intake data.** UDAY (J Nutr 2023, DOI
10.1016/j.tjnut.2022.12.032, PMC7616315; 8762 adults, Visakhapatnam and
Sonipat) asked about 10 snack types, among them "fried snacks (vada,
samosa, etc.)", "tea/coffee" and "fruits". It gives no per-item amounts.

**Sources read.**
- Banana: IFCT 2017 E012 "Banana, ripe, robusta", 6 regions, from the
  primary `IFCT2017.pdf` (same file as N20/N22). Table 1, PDF page 49: water 71.93,
  protein 1.23, fat 0.33, total fibre 1.94, available carbohydrate 23.63,
  energy 440 kJ (105.2 kcal) per 100 g. Sodium 0.85 mg, Table 5 PDF page
  168, placed under (Na) by column position (the Hg and Se cells are blank).
- Cow milk: IFCT 2017 L002 "Milk, whole, Cow", 6 regions, Table 1 PDF page 57: protein 3.26,
  fat 4.48, carbohydrate 4.94, energy 305 kJ (72.9 kcal). Sodium 25.46 mg,
  Table 5 PDF page 184, by column position (0.95 sits under Se).
- Sugar: IFCT 2017 has none refined (I001 jaggery, I002 cane juice only).
  USDA FDC 169655 "Sugars, granulated": 387 kcal, carb 99.98, sodium 1 mg.
- Brewed tea: not in IFCT. USDA FDC 173227 "Beverages, tea, black, brewed,
  prepared with tap water": 1 kcal, carb 0.3, sodium 3 mg.
- Banana piece: USDA FDC 173944, "medium" 118 g (Cavendish; robusta is a
  Cavendish type).
- **Vada: no measured source found.** Two searches turned up no laboratory
  fat value for a fried urad dal vada. Calorie-tracker sites disagree, 7 to
  16 g fat per 100 g. A vada would also need a deep-frying oil-uptake
  constant of its own. Not run.

Assumption, not sourced: one cup of tea = 70 g milk + 80 g brewed tea + 8 g
sugar.

**Measured.** `docs/design/probes/probe_banana_tea_snack.py`, 18 bodies,
unrelaxed snack target and after every step of `RELAXATION_ORDER`.
Byte-identical under PYTHONHASHSEED=1 and 777:

```
18 bodies. snack energy window: lowest 145-178, highest 279-341 kcal; fibre floor 2.3-4.3 g
1 banana                 [ 124 kcal, prot  1.5, fat  0.4, carb  30.2, fibre 2.3, Na   1.0]  unrelaxed  0/18, some rung  0/18  last-rung misses {'carb_g above ceiling': 5, 'energy_kcal below floor': 18}
2 bananas                [ 248 kcal, prot  2.9, fat  0.8, carb  60.3, fibre 4.6, Na   2.0]  unrelaxed  0/18, some rung  0/18  last-rung misses {'carb_g above ceiling': 18, 'energy_kcal above ceiling': 9, 'energy_kcal below floor': 4}
tea                      [  83 kcal, prot  2.3, fat  3.1, carb  11.7, fibre 0.0, Na  20.3]  unrelaxed  0/18, some rung  0/18  last-rung misses {'energy_kcal below floor': 18, 'fibre_g below floor': 18}
tea + 1 banana           [ 207 kcal, prot  3.7, fat  3.5, carb  41.9, fibre 2.3, Na  21.3]  unrelaxed  0/18, some rung  0/18  last-rung misses {'carb_g above ceiling': 12, 'energy_kcal above ceiling': 3, 'energy_kcal below floor': 8}
tea + 2 bananas          [ 331 kcal, prot  5.2, fat  3.9, carb  72.0, fibre 4.6, Na  22.3]  unrelaxed  0/18, some rung  0/18  last-rung misses {'carb_g above ceiling': 18, 'energy_kcal above ceiling': 17}
tea + soya_chana_sundal  [ 148 kcal, prot  7.0, fat  5.0, carb  19.4, fibre 2.5, Na 120.8]  unrelaxed  1/18, some rung  1/18  last-rung misses {'energy_kcal below floor': 17}
carb ceiling unrelaxed 22.3-46.0 g, last rung 24.2-50.0 g
  e.g. last rung: energy 164-200 kcal, carb <= 28.9 g -> max carb share of energy at the energy floor 70%
  e.g. last rung: energy 205-250 kcal, carb <= 40.5 g -> max carb share of energy at the energy floor 79%
  e.g. last rung: energy 225-275 kcal, carb <= 44.3 g -> max carb share of energy at the energy floor 79%
```

**Read.** 0/18 for every banana and tea plate, at every rung. Protein is not
in any miss list. What stops them:
- **The snack carb ceiling.** A banana takes 97% of its energy from
  carbohydrate (30.2 g x 4 / 124 kcal). The snack's carb ceiling allows at
  most 70-79% of the energy floor even at the last rung. Two bananas are
  over it for all 18 bodies; one banana is also too small for every energy
  window.
- **Energy steps.** A banana is 124 kcal and the windows are 33-62 kcal
  wide, so whole bananas skip over most of them.
- **Fibre floor** for tea alone: tea has none; the snack floor is 2.3-4.3 g.
The snack carb ceiling is the day carbohydrate range scaled to the snack's
energy share -- daily guidance, the same reasoning N23 and the 2026-09-25
fat/carb floor decision questioned for floors. N23's premise holds for
protein but did not reach these snacks: a second limit stops them first.

**Disposition.** STOPPED at premise. No dish, ingredient or template added,
no limit changed. The IFCT E012 and L002 readings above are ready for later
rows; unverified until a human opens PDF pages 49, 168 (E012) and 57, 184 (L002).
Changing the snack carb ceiling is a rule change and needs the owner's
decision and evidence first.

## 2026-10-08 — N23: a snack has no protein floor and no quality-protein floor

**Asked.** Owner, 2026-10-08, from experience: most people do not eat protein
at a snack -- a banana, a rice cake with peanut butter -- so protein at every
meal is ideal but not realistic. A South Indian breakfast is coffee/tea,
idli/dosa, sambar/chutney, eggs/omelette. The owner asked for data on meals
people actually ate, not dietary guidelines ("guidelines wouldnt tell actual
meals people have"), then chose: drop the protein floor and the
quality-protein floor for snacks only, keep both for breakfast, lunch and
dinner, and show the before and after before anything is merged.

**What the code had.** Every per-meal protein floor was a `PROJECT_DECISION`
with no source, and `citations.py` said so: `protein.meal_floor_fraction`
0.15 (a guard beneath each meal's energy share; it bound only on the snack,
whose share is 0.10) and `protein.quality_meal_floor_fraction` 0.10 (flat on
every plate, snack included, kept flat for snacks by owner decision
2026-09-25).

**Sources searched, intake data first.** What was found:
- UDAY (J Nutr 2023, DOI 10.1016/j.tjnut.2022.12.032; 8762 adults,
  Visakhapatnam and Sonipat). Food-frequency questionnaire over 10 predefined
  snack types. Savoury snacks most frequent, fruit second; tea/coffee alongside.
  In Visakhapatnam 60% eat savoury snacks weekly, mostly in the morning.
  Agrees with the owner on *which foods*. **Limitation:** the list is fixed
  and holds no protein foods, so it cannot say how much protein a snack
  carries.
- Mumbai breakfast (Sivaramakrishnan & Kamath, Public Health Nutr 2012, DOI
  10.1017/S1368980012002777; n=1027). 64% of breakfasts give 15% or less of
  the day's energy RDA; breakfast protein well below 25% of the day's RDA;
  21% of adults 18-40 skip breakfast. About breakfast, not snacks; the
  tables are images and were not transcribed. Not used for any change here.

What was searched and holds no per-meal or per-snack protein:
- NIN "What India Eats" (NNMB): day-level only.
- CURES-68 (Chennai): day-level.
- Kerala KDPP: dietary patterns only.
- Hyderabad older adults: day-level.
- I-STARCH-1 (Nutrients 2026, PMC13610836): no meal breakdown.
- Bengaluru CGM study (BMC Endocr Disord 2026, PMC13563805, n=46):
  correlations only.
- South Asia Biobank Intake24 (PMC11847516): records eating occasions, but
  the paper is methods only and the data is access-restricted. Applying for
  it is the owner's option, not done.
- A Kellogg-linked breakfast survey: 1 in 4 urban Indians skip breakfast.
  Sponsor-linked; not used.

**No study found measured protein per snack in Indian adults.** The decision
rests on the owner's account, consistent with UDAY's food list. Nothing here
is a sourced number, and no constant was added or changed.

**Change.** `core/nutrition/meal_target.py`:
- `_FLOORLESS_BY_SLOT[SNACK]` now holds `protein_g` beside `fat_g` and
  `carb_g`. The pop moved to after `_apply_protein_meal_bounds`, which adds a
  guard floor of its own; popping first would let the guard put 15% back.
- New `_NO_QUALITY_FLOOR_SLOTS = {SNACK}`: a snack's
  `quality_protein_floor_g` is `None`.
- The snack keeps the protein ceiling (0.50 x day floor) and the protein
  point (0.10 x day floor).

Stale wording corrected in place, each with a dated note: the two constants'
notes in `core/nutrition/citations.py`, two docstrings in `meal_target.py`,
two passages in `docs/methodology.md` (plus a new section "A snack has no
protein floor"), and the onboarding sentence in `web/onboarding.js`, which
said "every plate carries a share of that floor" and now says "every
breakfast, lunch and dinner ... (a snack does not)".

**Before and after.** `docs/design/probes/probe_snack_protein_floor.py`,
18 bodies per region x diet (3 goals x 2 sexes x 55/70/90 kg). It reads only
fields present on both trees. BEFORE was run on this branch with only the
probe added (code at main 5fa8f9d); AFTER on the change. Each side is
byte-identical under PYTHONHASHSEED=1 and 777.

BEFORE:

```
south_indian  vegetarian      protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 18, unrelaxed 15, options 39
    shown  4x  neer_mor + soya_chana_sundal
    shown  7x  neer_mor + soya_chunk_sundal
    shown  1x  soya_chana_sundal
    shown  6x  soya_chunk_sundal
south_indian  eggetarian      protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 18, unrelaxed 15, options 45, egg asked 6
    shown  4x  neer_mor + soya_chana_sundal
    shown  7x  neer_mor + soya_chunk_sundal
    shown  1x  soya_chana_sundal
    shown  6x  soya_chunk_sundal
south_indian  non_vegetarian  protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 18, unrelaxed 15, options 45, egg asked 6
    shown  4x  neer_mor + soya_chana_sundal
    shown  7x  neer_mor + soya_chunk_sundal
    shown  1x  soya_chana_sundal
    shown  6x  soya_chunk_sundal
south_indian  vegan           protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 16, unrelaxed 14, options 18
    shown  2x  soya_chana_sundal
    shown 14x  soya_chunk_sundal
north_indian  vegetarian      protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 17, unrelaxed 14, options 45
    shown  4x  chaas + soya_chana_chaat
    shown  5x  chaas + soya_chana_chaat + soya_tikka
    shown  1x  chaas + soya_tikka
    shown  2x  soya_chana_chaat
    shown  3x  soya_chana_chaat + soya_tikka
    shown  2x  soya_tikka
north_indian  eggetarian      protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 17, unrelaxed 14, options 53
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  4x  anda_chaat + soya_chana_chaat
    shown  2x  chaas + soya_chana_chaat
    shown  2x  chaas + soya_chana_chaat + soya_tikka
    shown  1x  chaas + soya_tikka
    shown  2x  soya_chana_chaat + soya_tikka
    shown  2x  soya_tikka
north_indian  non_vegetarian  protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 17, unrelaxed 14, options 53
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  4x  anda_chaat + soya_chana_chaat
    shown  2x  chaas + soya_chana_chaat
    shown  2x  chaas + soya_chana_chaat + soya_tikka
    shown  1x  chaas + soya_tikka
    shown  2x  soya_chana_chaat + soya_tikka
    shown  2x  soya_tikka
north_indian  vegan           protein floor 13.2-24.3, quality floor 8.8-16.2; bodies 18, plate 4, unrelaxed 2, options 4
    shown  4x  soya_chana_chaat
```

AFTER:

```
south_indian  vegetarian      protein floor none, quality floor none; bodies 18, plate 18, unrelaxed 18, options 54
    shown 10x  neer_mor + soya_chana_sundal
    shown  8x  soya_chana_sundal
south_indian  eggetarian      protein floor none, quality floor none; bodies 18, plate 18, unrelaxed 18, options 60, egg asked 6
    shown 10x  neer_mor + soya_chana_sundal
    shown  8x  soya_chana_sundal
south_indian  non_vegetarian  protein floor none, quality floor none; bodies 18, plate 18, unrelaxed 18, options 60, egg asked 6
    shown 10x  neer_mor + soya_chana_sundal
    shown  8x  soya_chana_sundal
south_indian  vegan           protein floor none, quality floor none; bodies 18, plate 18, unrelaxed 17, options 29
    shown 13x  soya_chana_sundal
    shown  5x  soya_chunk_sundal
north_indian  vegetarian      protein floor none, quality floor none; bodies 18, plate 18, unrelaxed 18, options 50
    shown  6x  chaas + soya_chana_chaat
    shown  4x  chaas + soya_chana_chaat + soya_tikka
    shown  3x  soya_chana_chaat
    shown  3x  soya_chana_chaat + soya_tikka
    shown  2x  soya_tikka
north_indian  eggetarian      protein floor none, quality floor none; bodies 18, plate 18, unrelaxed 18, options 63
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  8x  anda_chaat + soya_chana_chaat
    shown  4x  chaas + soya_chana_chaat
    shown  1x  soya_chana_chaat + soya_tikka
    shown  1x  soya_tikka
north_indian  non_vegetarian  protein floor none, quality floor none; bodies 18, plate 18, unrelaxed 18, options 63
    shown  4x  anda_chaat + chaas + soya_chana_chaat
    shown  8x  anda_chaat + soya_chana_chaat
    shown  4x  chaas + soya_chana_chaat
    shown  1x  soya_chana_chaat + soya_tikka
    shown  1x  soya_tikka
north_indian  vegan           protein floor none, quality floor none; bodies 18, plate 6, unrelaxed 3, options 6
    shown  6x  soya_chana_chaat
```

**Read.** Over all 144 region x diet x body cases:
- A passing snack plate: 125 before (18+18+18+16+17+17+17+4), 132 after
  (18x7+6).
- Passing with no relaxation: 103 before (15x3+14x4+2), 128 after
  (18x3+17+18x3+3).
- Swap choices offered rise in every row (e.g. South vegetarian 39 to 54).
- The shown plate shifts from soya-chunk sundal to the lighter soya-chana
  sundal in the South (soya_chunk_sundal shown 13 of 18 times before for
  vegetarian, 0 after).
- **Unchanged:** the boiled egg asked for in the South, still 6 of 18 per egg
  diet. N21 found that blocked by the energy floor and the fat ceiling, not
  protein, and this confirms protein was not what held it.
- **Unchanged in kind:** North vegan reaches 6 of 18 (was 4). What blocks the
  other 12 was not measured here.
- No new kind of snack appears. The library holds no low-protein snack dish
  (no banana, vada or tea): dropping the floor changes which existing plates
  fit; it does not add the snacks the owner described. Those would be new
  dishes, each with its own source.

**Cost, stated.**
- The snack's share of the day protein floor (10% of it) is now asked of no
  meal. One plate is solved per request, so nothing checks that the rest of
  the day makes it up.
- With the snack exempt, `protein.meal_floor_fraction` (0.15) binds on no
  slot at the registered shares (0.25 / 0.35 / 0.30 are all above it). It is
  kept, not deleted: it is live code, a change to a share or to 0.15 makes it
  bind again, and `test_the_floor_is_the_larger_of_the_share_and_the_guard`
  now raises it to 0.30 to show the max() still works.
  `test_at_the_registered_guard_it_binds_on_no_slot` asserts the cost so it
  is not forgotten.

**Deletion checks.** Three new rows in `docs/design/probes/d4b_mutations.py`
(SP1-SP3, `meal_target.py`, own tests `test_nutrition_meal_target.py` and
`test_planner_quality.py`). Full failure list per mutation, whole suite, no
`-x`, `PYTHONHASHSEED=0`:

```
   all failures (1):
      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
SP1  covered      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
   all failures (1):
      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_quality_protein_floor
SP2  covered      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_quality_protein_floor
   all failures (1):
      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
SP3  covered      tests/test_nutrition_meal_target.py::TestASnackHasNoProteinFloor::test_a_snack_has_no_protein_floor
====================================================================================================
3 mechanisms: 3 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

SP3 moves the pop back above `_apply_protein_meal_bounds`; the guard then
re-adds a 15.0 g floor and the snack test goes red. Each mutation turned
exactly one test red, the one named for it. `meal_target.py`'s older bounds
(fat/carb pop, energy band, protein ceiling) still have no rows; logged, not
added here.

The `web/onboarding.js` sentence is copy, not a mechanism; no hand deletion
check applies. It was not looked at on screen.

**Suite.** Both dev servers started (API :8000, page :3000), then:

```
$ FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p no:cacheprovider
669 passed, 1 warning in 241.86s (0:04:01)
```

The one warning is `FOODAI_SESSION_SECRET` unset (local dev, as always).

**Disposition.** DONE on branch `snack-protein`, not merged; the owner sees
the before and after above first.
Logged for later, not started:
- Real low-protein snack dishes (fruit/banana, vada, tea/coffee), each with
  a source.
- Breakfast protein: Mumbai 2012 suggests real breakfasts carry less than the
  25% share, but it is one city, 2012, tables not transcribed; wait for
  better data.
- South Asia Biobank meal-level data, if the owner applies.

## 2026-10-08 — N22: boiled egg with sweet potato cannot fit any breakfast target -- stopped at premise

**Asked.** Owner, 2026-10-08: boiled egg with sundal or sweet potato is a
breakfast habit; add sweet potato with boiled egg at South breakfast, "with
proper backing" (a published source shown before building).

**Source.** IFCT 2017 has sweet potato, read from the primary NIN-published
`IFCT2017.pdf` (downloaded for N20; sha256
`7fc5a5112a57240d25bf695dca82cccd8d93ed54e8c39530e42b5ad1820d0e8c`), not from a
digitization:
- F013 "Sweet potato, brown skin (Ipomoea batatas)", 4 regions, RAW, Table 1
  (PDF page 53): water 69.21, protein 1.33, ash 0.96, fat 0.26, total fibre
  3.99, available carbohydrate 24.25 g, energy 456 kJ (109.0 kcal) per 100 g.
- Sodium 29.60 mg, Table 5 (PDF page 176). The selenium cell is blank on
  this row, so the column was settled with `pdftotext -table`, which keeps
  column alignment: 29.60 sits under NA.
- F014 (pink skin) is nearly identical (69.58 water, 1.27 protein, 0.33 fat,
  3.94 fibre, 23.93 carbohydrate, 452 kJ, sodium 29.04).
- Column reading cross-checked on a row already in the library: F006 potato
  on the same page reads 80.72 / 1.54 / 0.23 / 1.71 fibre / 14.89 / 292 kJ,
  matching `potato_raw` (carb_g 16.6 = 14.89 + 1.71; 292 kJ = 69.8 kcal).
IFCT measured RAW sweet potato only. For boiled, USDA FoodData Central SR
Legacy FDC 168484 "Sweet potato, cooked, boiled, without skin" (fetched
2026-10-08): 76 kcal, protein 1.37, fat 0.14, carb 17.72, fibre 2.5, sodium
27 mg, water 80.13. That is American sweet potato: USDA's raw row (FDC
168482) is 77.28% water against IFCT's 69.21%, so it is not the Indian tuber.
Neither source is the right food cooked the right way; the probe runs both as
a low and a high case.

**Plate shape.** `template_for` holds one template per region and meal, and
`SOUTH_BREAKFAST` requires a tiffin, a gravy and a chutney. Egg with sweet
potato as its own breakfast is a second shape, which the planner cannot hold
today. Before proposing that change, the arithmetic.

**Measured.** `docs/design/probes/probe_sweet_potato_breakfast.py`, 36
egg-eating bodies (as N19-N21), unrelaxed breakfast target and every rung of
`RELAXATION_ORDER`. Output byte-identical under PYTHONHASHSEED=1 and 777:

```
bodies: 36; e.g. eggetarian lose_fat male 55kg breakfast, unrelaxed: energy 432-478 kcal, protein >= 24.8 g, quality >= 9.9 g, fat <= 17.7 g
IFCT raw    1 egg + 100 g  [183 kcal, prot  8.0, qual  6.7, fat  5.5, fibre 4.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'fibre_g below floor': 16, 'protein_g below floor': 36, 'quality protein below floor': 36}
IFCT raw    1 egg + 150 g  [237 kcal, prot  8.7, qual  6.7, fat  5.7, fibre 6.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 30, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'protein_g below floor': 36, 'quality protein below floor': 36}
IFCT raw    1 egg + 200 g  [292 kcal, prot  9.4, qual  6.7, fat  5.8, fibre 8.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 20, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'protein_g below floor': 36, 'quality protein below floor': 36}
IFCT raw    1 egg + 250 g  [346 kcal, prot 10.0, qual  6.7, fat  5.9, fibre 10.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g above ceiling': 6, 'carb_g below floor': 2, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'protein_g below floor': 36, 'quality protein below floor': 36}
IFCT raw    2 egg + 100 g  [257 kcal, prot 14.8, qual 13.4, fat 10.8, fibre 4.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 30, 'fibre_g below floor': 16, 'protein_g below floor': 36, 'quality protein below floor': 12}
IFCT raw    2 egg + 150 g  [311 kcal, prot 15.4, qual 13.4, fat 10.9, fibre 6.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 30, 'energy_kcal below floor': 36, 'fat_g below floor': 30, 'protein_g below floor': 36, 'quality protein below floor': 12}
IFCT raw    2 egg + 200 g  [366 kcal, prot 16.1, qual 13.4, fat 11.1, fibre 8.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 20, 'energy_kcal below floor': 34, 'fat_g below floor': 30, 'protein_g below floor': 36, 'quality protein below floor': 12}
IFCT raw    2 egg + 250 g  [420 kcal, prot 16.8, qual 13.4, fat 11.2, fibre 10.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g above ceiling': 6, 'carb_g below floor': 2, 'energy_kcal below floor': 30, 'fat_g below floor': 28, 'protein_g below floor': 36, 'quality protein below floor': 12}
USDA boiled 1 egg + 100 g  [150 kcal, prot  8.1, qual  6.7, fat  5.4, fibre 2.5]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'fibre_g below floor': 36, 'protein_g below floor': 36, 'quality protein below floor': 36}
USDA boiled 1 egg + 150 g  [188 kcal, prot  8.8, qual  6.7, fat  5.5, fibre 3.8]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'fibre_g below floor': 24, 'protein_g below floor': 36, 'quality protein below floor': 36}
USDA boiled 1 egg + 200 g  [226 kcal, prot  9.5, qual  6.7, fat  5.5, fibre 5.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'fibre_g below floor': 2, 'protein_g below floor': 36, 'quality protein below floor': 36}
USDA boiled 1 egg + 250 g  [264 kcal, prot 10.1, qual  6.7, fat  5.6, fibre 6.2]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 28, 'energy_kcal below floor': 36, 'fat_g below floor': 36, 'protein_g below floor': 36, 'quality protein below floor': 36}
USDA boiled 2 egg + 100 g  [224 kcal, prot 14.8, qual 13.4, fat 10.7, fibre 2.5]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 30, 'fibre_g below floor': 36, 'protein_g below floor': 36, 'quality protein below floor': 12}
USDA boiled 2 egg + 150 g  [262 kcal, prot 15.5, qual 13.4, fat 10.8, fibre 3.8]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 30, 'fibre_g below floor': 24, 'protein_g below floor': 36, 'quality protein below floor': 12}
USDA boiled 2 egg + 200 g  [300 kcal, prot 16.2, qual 13.4, fat 10.8, fibre 5.0]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 36, 'energy_kcal below floor': 36, 'fat_g below floor': 30, 'fibre_g below floor': 2, 'protein_g below floor': 36, 'quality protein below floor': 12}
USDA boiled 2 egg + 250 g  [338 kcal, prot 16.9, qual 13.4, fat 10.9, fibre 6.2]  fits unrelaxed  0/36, at some rung  0/36  last-rung misses: {'carb_g below floor': 28, 'energy_kcal below floor': 36, 'fat_g below floor': 30, 'protein_g below floor': 36, 'quality protein below floor': 12}
```

**Read.** 0/36 for all 16 versions, both sources, at every rung. The
protein floor is missed by all 36 bodies in every version: the best plate (2
eggs, 250 g) carries 16.9 g against a floor of at least 24.8 g. Energy and
fat also fall short for at least 28 of 36 bodies in every version. As a whole breakfast, egg
with sweet potato is too small; the source chosen does not change that.

**Assumptions, stated in the probe:** portions 100-250 g (not sourced);
sweet potato protein non-qualifying (no DIAAS row).

**Not measured.** Egg and sweet potato as part of a larger breakfast (beside
a tiffin, or with sundal) -- the owner has not described that plate, and
building one to make the numbers fit would be reshaping the task to fit.

**Disposition.** STOPPED at premise. Nothing added to the library, no
template changed, no limit widened. The IFCT F013 reading above is ready for
any later sweet potato row; it is unverified until a human opens page 53.

## 2026-10-08 — N21: why the boiled-egg snack side fits only 12 of 36 bodies

**Asked.** Owner, 2026-10-08 (option 1 after N20). N19 found that asking for
`avicha_muttai` beside the South snack's sundal gives a valid plate for 12 of
36 egg-eating bodies, and logged the other 24 as not measured. Measure only;
no change.

**Method.** `docs/design/probes/probe_egg_side_fit.py` tries every plate the
planner could build with the egg in it (every combination
`enumerate_combinations` yields that holds the egg, at every legal serving
count: 64 plates per diet) against the snack target at each rung of
`RELAXATION_ORDER`, applied cumulatively. It first checks itself against
`plan_meal`: the bodies it says fit must be the bodies the planner passes.
Output is byte-identical under PYTHONHASHSEED=1 and 777.

```
plates with the egg: eggetarian 64, non_vegetarian 64
cross-check against plan_meal: 36 agree, 0 disagree
first rung at which some egg plate fits:
  unrelaxed              12
  sodium_max_fibre_min   0
  fat_carb_tolerance     0
  energy_tolerance       0
  protein_tolerance      0
  no rung                24
bodies with no fitting plate, per bound:
  energy_kcal below floor        blocks every plate on  0   the only thing in the way on 16
  fat_g above ceiling            blocks every plate on  2   the only thing in the way on 24
per body:
  eggetarian     lose_fat  male   55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     lose_fat  male   70kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  eggetarian     lose_fat  male   90kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     lose_fat  female 55kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  eggetarian     lose_fat  female 70kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  eggetarian     lose_fat  female 90kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  eggetarian     maintain  male   55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     maintain  male   70kg  fits at rung: unrelaxed
  eggetarian     maintain  male   90kg  fits at rung: unrelaxed
  eggetarian     maintain  female 55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     maintain  female 70kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     maintain  female 90kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     gain_muscle male   55kg  fits at rung: unrelaxed
  eggetarian     gain_muscle male   70kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     gain_muscle male   90kg  fits at rung: unrelaxed
  eggetarian     gain_muscle female 55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  eggetarian     gain_muscle female 70kg  fits at rung: unrelaxed
  eggetarian     gain_muscle female 90kg  fits at rung: unrelaxed
  non_vegetarian lose_fat  male   55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian lose_fat  male   70kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  non_vegetarian lose_fat  male   90kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian lose_fat  female 55kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  non_vegetarian lose_fat  female 70kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  non_vegetarian lose_fat  female 90kg  no plate fits; nearest plate misses: ['fat_g above ceiling']
  non_vegetarian maintain  male   55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian maintain  male   70kg  fits at rung: unrelaxed
  non_vegetarian maintain  male   90kg  fits at rung: unrelaxed
  non_vegetarian maintain  female 55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian maintain  female 70kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian maintain  female 90kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian gain_muscle male   55kg  fits at rung: unrelaxed
  non_vegetarian gain_muscle male   70kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian gain_muscle male   90kg  fits at rung: unrelaxed
  non_vegetarian gain_muscle female 55kg  no plate fits; nearest plate misses: ['energy_kcal below floor']
  non_vegetarian gain_muscle female 70kg  fits at rung: unrelaxed
  non_vegetarian gain_muscle female 90kg  fits at rung: unrelaxed
one serving of each dish on these plates (fat share = fat kcal / all kcal):
  avicha_muttai      1 egg            (allowed 1-2)   73.8 kcal  fat 5.27 g  fat share 0.64
  neer_mor           1 glass          (allowed 1-1)   30.9 kcal  fat 2.01 g  fat share 0.58
  soya_chana_sundal  1 quarter katori (allowed 1-8)   65.6 kcal  fat 1.89 g  fat share 0.26
  soya_chunk_sundal  1 quarter katori (allowed 1-8)   52.1 kcal  fat 1.41 g  fat share 0.24
eggetarian maintain male 55kg, unrelaxed: energy 205-250 kcal, fat <= 8.8 g; egg plates missing at most one bound:
   178 kcal  fat  8.1  soya_chunk_sundalx2 + avicha_muttaix1                energy_kcal below floor
   205 kcal  fat  9.1  soya_chana_sundalx2 + avicha_muttaix1                fat_g above ceiling
   209 kcal  fat 10.1  soya_chunk_sundalx2 + avicha_muttaix1 + neer_morx1   fat_g above ceiling
   230 kcal  fat  9.5  soya_chunk_sundalx3 + avicha_muttaix1                fat_g above ceiling
   236 kcal  fat 11.1  soya_chana_sundalx2 + avicha_muttaix1 + neer_morx1   fat_g above ceiling
eggetarian maintain male 70kg, unrelaxed: energy 226-276 kcal, fat <= 9.7 g; egg plates missing at most one bound:
   230 kcal  fat  9.5  soya_chunk_sundalx3 + avicha_muttaix1                FITS
   236 kcal  fat 11.1  soya_chana_sundalx2 + avicha_muttaix1 + neer_morx1   fat_g above ceiling
   261 kcal  fat 11.5  soya_chunk_sundalx3 + avicha_muttaix1 + neer_morx1   fat_g above ceiling
   271 kcal  fat 11.0  soya_chana_sundalx3 + avicha_muttaix1                fat_g above ceiling
```

**Read.**
- The cross-check holds (36 agree, 0 disagree), so the arithmetic measures
  the planner.
- Every body that fits, fits before any loosening. No rung rescues a body.
  For a snack the energy and fat rungs change nothing, by design: the snack's
  energy band is already the relaxed width (`tolerance.energy_snack` =
  `tolerance.energy_relaxed` = 0.10), and the fat band from the AMDR
  (`tolerance.fat_default` = 0.2727) is already wider than the fat rung's
  0.25, and a rung only widens. So the question is settled at the unrelaxed
  limits.
- The 24 bodies that cannot fit are stopped by two limits together, energy
  floor and fat ceiling: on 24 of 24 some plate is stopped by fat alone, and
  on 16 some plate is stopped by too little energy alone. Fat blocks every
  plate outright on only 2. No other bound (quality protein, protein, carb,
  fibre, sodium) is ever the only thing in the way or blocks every plate.
- Why: one boiled egg is 64% of its energy from fat (5.27 g in 73.8 kcal).
  The snack's fat ceiling is 35% of the snack's energy (the AMDR upper bound,
  applied per meal by project decision). The sundal (24-26% fat) has to
  dilute the egg; enough sundal to do that pushes energy past the band's top,
  too little leaves fat over the ceiling. Portions move in whole quarter
  katoris (52-66 kcal) and whole eggs (74 kcal), so for most bodies no step
  lands in the gap. The 55 kg / 70 kg pair above shows it: the same plate
  (3 quarter katoris of chunk sundal, 1 egg, 230 kcal, 9.5 g fat) fits a
  9.7 g ceiling and misses an 8.8 g one.
- Which bodies fit does not rise with body size (maintain male fits at 70 and
  90 kg, not 55; gain_muscle male fits at 55 and 90, not 70). Expected from
  whole-portion steps against a band that moves with the body.

**Not checked.** The egg's fat figure is an unverified IFCT-derived row like
the rest of the library; nothing here re-checks it. Whether a daily fat range
should be applied to a single snack is a project decision (citations.py,
`tolerance.fat_default`), not a sourced fact; changing it would need a
published source first.

**Disposition.** DONE, measurement only. No code, rule or limit changed. The
omelette and podimas fitting no snack (N19) is probably the same fat
arithmetic; that is a guess, not measured.

## 2026-10-08 — N20: a bread omelette cannot fit any snack target -- stopped at premise

**Asked.** Owner, 2026-10-08: include bread omelette as a snack ("a normal
snack throughout India"). Owner chose to start from the IFCT 2017 PDF and
permitted its download.

**Source search.** `IFCT2017.pdf` downloaded from
`https://www.nin.res.in/ebooks/IFCT2017.pdf` (12,401,190 bytes, sha256
`7fc5a5112a57240d25bf695dca82cccd8d93ed54e8c39530e42b5ad1820d0e8c`), text
extracted with `pdftotext -layout`, searched for bread, bun and rusk. The
only "bread" is a lab-method reference (AOAC, acetic and propionic acids in
bread); "bun" appears only inside a fish name. **IFCT 2017 has no bread
row.** Bread was taken from USDA FoodData Central SR Legacy instead, the
source this project already used for egg B12 when IFCT lacked a figure:
white FDC 174924, whole wheat FDC 172688 (values in the probe's docstring).
American commercial bread is not Indian bread; nothing here is added to the
library, so no row carries that mismatch.

**Measured.** `docs/design/probes/probe_bread_omelette.py`, against the
unrelaxed snack target of the same 36 egg-eating bodies as N19:

```
bodies: 36
white 1egg 2sl           fits  0/36  [226 kcal, prot 11.2, qual 6.6, fat 8.8, fibre 1.5]  misses: {'carb_g>': 6, 'energy_kcal<': 10, 'energy_kcal>': 12, 'fat_g>': 16, 'fibre_g<': 36, 'protein_g<': 36, 'quality<': 36}
white 1egg 2sl +nm       fits  0/36  [257 kcal, prot 12.8, qual 8.2, fat 10.8, fibre 1.6]  misses: {'carb_g>': 10, 'energy_kcal<': 2, 'energy_kcal>': 20, 'fat_g>': 30, 'fibre_g<': 36, 'protein_g<': 36, 'quality<': 36}
white 2egg 2sl           fits  0/36  [320 kcal, prot 17.9, qual 13.3, fat 15.8, fibre 1.7]  misses: {'carb_g>': 8, 'energy_kcal>': 34, 'fat_g>': 36, 'fibre_g<': 36, 'protein_g<': 20, 'quality<': 12}
white 2egg 2sl +nm       fits  0/36  [351 kcal, prot 19.5, qual 14.8, fat 17.8, fibre 1.8]  misses: {'carb_g>': 10, 'energy_kcal>': 36, 'fat_g>': 36, 'fibre_g<': 36, 'protein_g<': 12, 'quality<': 8}
white 2egg 4sl           fits  0/36  [453 kcal, prot 22.4, qual 13.3, fat 17.5, fibre 3.1]  misses: {'carb_g>': 36, 'energy_kcal>': 36, 'fat_g>': 36, 'fibre_g<': 24, 'protein_g<': 8, 'quality<': 12}
white 2egg 4sl +nm       fits  0/36  [484 kcal, prot 24.0, qual 14.8, fat 19.5, fibre 3.1]  misses: {'carb_g>': 36, 'energy_kcal>': 36, 'fat_g>': 36, 'fibre_g<': 22, 'protein_g<': 8, 'quality<': 8}
wheat 1egg 2sl           fits  0/36  [220 kcal, prot 13.0, qual 6.6, fat 8.8, fibre 3.2]  misses: {'carb_g>': 2, 'energy_kcal<': 16, 'energy_kcal>': 6, 'fat_g>': 18, 'fibre_g<': 16, 'protein_g<': 36, 'quality<': 36}
wheat 1egg 2sl +nm       fits  0/36  [251 kcal, prot 14.6, qual 8.2, fat 10.8, fibre 3.2]  misses: {'carb_g>': 4, 'energy_kcal<': 6, 'energy_kcal>': 20, 'fat_g>': 30, 'fibre_g<': 16, 'protein_g<': 32, 'quality<': 36}
wheat 2egg 2sl           fits  0/36  [314 kcal, prot 19.7, qual 13.3, fat 15.9, fibre 3.4]  misses: {'carb_g>': 4, 'energy_kcal>': 34, 'fat_g>': 36, 'fibre_g<': 16, 'protein_g<': 12, 'quality<': 12}
wheat 2egg 2sl +nm       fits  0/36  [345 kcal, prot 21.3, qual 14.8, fat 17.9, fibre 3.4]  misses: {'carb_g>': 6, 'energy_kcal>': 36, 'fat_g>': 36, 'fibre_g<': 16, 'protein_g<': 12, 'quality<': 8}
wheat 2egg 4sl           fits  0/36  [441 kcal, prot 25.9, qual 13.3, fat 17.7, fibre 6.4]  misses: {'carb_g>': 34, 'energy_kcal>': 36, 'fat_g>': 36, 'quality<': 12}
wheat 2egg 4sl +nm       fits  0/36  [472 kcal, prot 27.5, qual 14.8, fat 19.7, fibre 6.4]  misses: {'carb_g>': 36, 'energy_kcal>': 36, 'fat_g>': 36, 'quality<': 8}
```

The first run doubled the bread with the eggs (two eggs, four slices only);
corrected to add two eggs on two slices, which also fits 0/36.
Output order is sorted; the same table came out byte-identical under
`PYTHONHASHSEED=1` and `PYTHONHASHSEED=777` (an unsorted first version listed
the same counts in a seed-dependent order).

**Why, in one line each.** One egg: 6.6 g qualifying protein against a
floor no rung relaxes, missed by all 36. Two eggs: the egg's own fat puts
every body over its fat ceiling (36/36) and nearly every body over its
energy ceiling. The bread is not what fails it, so a different bread value
would not rescue it; no toasting fat was counted, which would only add fat.

**Assumptions, stated in the probe:** 25 g slice (not sourced); bread
protein non-qualifying (wheat DIAAS below 0.75 from memory, unverified).

**Disposition.** STOPPED at premise. Not added. No limit was widened to make
it fit. The downloaded PDF stays outside the repo (untracked scratch).

## 2026-10-08 — N19: the South snack's egg is a side, offered on request

**Asked.** Owner, 2026-10-08 (option 1 after N18): an egg option for the
South Indian snack. The task as first stated -- add an egg dish -- rested on
a wrong premise, and the egg claim already in the template was wrong too.

**Premise check.** Three South egg dishes already existed and the snack's
one required course already accepted them (N2c, 2026-09-27). Measured, 36
egg-eating bodies (eggetarian and non-vegetarian x 3 goals x 2 sexes x 55/70/90
kg): 0 shown plates and 0 valid plates held an egg. Reference eggetarian
(70 kg, 170 cm, 30, male, maintain) snack target: energy 225.6-275.8 kcal,
fat <= 9.75 g, fibre >= 3.51 g, protein >= 16.8 g, quality protein >= 11.2 g.
avicha_muttai x2 = 147.7 kcal, fat 10.5 g, fibre 0.0 g, protein 13.4 g;
neer_mor adds 0.1 g fibre. An egg alone can never meet the fibre floor, so
no added egg dish could have changed the count.

**Owner's correction (lived experience).** Sundal is the snack and is eaten
alone. An egg is not eaten alone as an evening snack; boiled egg with sundal
or sweet potato is a breakfast habit. An egg beside the sundal is acceptable
as an option, "not a regular thing". This contradicts the N2c comment that
a boiled egg or podimas is "the ordinary Tamil egg eaten as an evening snack,
in the place a sundal takes". The comment is corrected in place with a dated
note, not deleted.

**Changed.**
- `TemplateSlot.on_request` (`core/foods/models.py`): an optional course the
  planner leaves empty unless a pick belongs to it. A required slot cannot
  be one (construction-time check).
- `SOUTH_SNACK`: the `sundal` course takes sundal only; a new `egg_side`
  course takes egg, optional, `on_request=True`; the drink is unchanged.
- `plan_meal` joins every on-request course with no pick in it to
  `leave_empty`. Swap options, emptiable courses and declines then treat it
  exactly as a course the user emptied. The animal-protein preference
  therefore never puts an egg on the snack by itself.

**Measured** (`docs/design/probes/probe_snack_egg_side.py`; reads only
`plan_meal`'s outcome and `Component.category`, so it ran on both trees):

```
--- before (main 65d0e63)
vegetarian      {'bodies': 18, 'with a plate': 18, 'shown egg': 0}
eggetarian      {'bodies': 18, 'with a plate': 18, 'shown egg': 0, 'asked avicha_muttai: passes': 0, 'asked muttai_omelette: passes': 0, 'asked muttai_podimas: passes': 0}
non_vegetarian  {'bodies': 18, 'with a plate': 18, 'shown egg': 0, 'asked avicha_muttai: passes': 0, 'asked muttai_omelette: passes': 0, 'asked muttai_podimas: passes': 0}
vegan           {'bodies': 18, 'with a plate': 16, 'shown egg': 0}
--- after
vegetarian      {'bodies': 18, 'with a plate': 18, 'shown egg': 0}
eggetarian      {'bodies': 18, 'with a plate': 18, 'shown egg': 0, 'asked avicha_muttai: passes': 6, 'asked muttai_omelette: passes': 0, 'asked muttai_podimas: passes': 0}
non_vegetarian  {'bodies': 18, 'with a plate': 18, 'shown egg': 0, 'asked avicha_muttai: passes': 6, 'asked muttai_omelette: passes': 0, 'asked muttai_podimas: passes': 0}
vegan           {'bodies': 18, 'with a plate': 16, 'shown egg': 0}
```

Default plates unchanged for every diet. A boiled egg can be added for 6 of
18 bodies per egg-eating diet; omelette and podimas fit none (why is not
measured). The egg is offered only where it fits: over
the same 36 bodies, `egg_side` swap options list `avicha_muttai` for 12 and
are empty for the other 24. Why the other 24 cannot fit it is not measured.

**Deletion rows.** M2 (MODELS), N19a and N19b (PLAN), `OWN_TESTS` extended:

```
M2   covered      tests/test_on_request_slot.py::test_a_required_slot_cannot_be_on_request
N19a covered      tests/test_on_request_slot.py::test_by_default_the_snack_holds_no_egg
N19b covered      tests/test_on_request_slot.py::test_asking_for_an_egg_puts_it_beside_the_sundal
3 mechanisms: 3 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

**Web, by hand** (the harness cannot grade `web/`). Playwright script against
the dev servers, eggetarian 70 kg / 170 cm / 30 / male / maintain:

```
default dishes: ['Soya chana sundal']
add menus: [{'label': 'Add an egg side', 'options': ['Choose a dish', 'Avicha muttai (boiled egg)']}, {'label': 'Add a drink', 'options': ['Choose a dish', 'Neer mor']}]
request: {..., 'picks': ['avicha_muttai'], 'leave_empty': [], 'region': 'south_indian', 'meal_slot': 'snack'}
passed: True
after adding: ['Soya chunk sundal', 'Avicha muttai (boiled egg)']
```

Adding the egg re-solves the plate, so the sundal can change (chana to chunk
here) to keep the snack within its limits. `tests/test_web_add_dish.py`'s
snack body (175 cm, 28) is one the egg does not fit, so it still sees only
the drink menu and passes unchanged.

**Logged, not done.**
- Bread omelette (owner, 2026-10-08: a normal snack across India). No bread
  row exists in `data/raw/ifct`. Owner chose to do it after N19, starting
  with the IFCT 2017 PDF (download permitted by the owner for that task).
  A rough check from memory, not a source, suggests it misses the snack's
  protein and fibre floors; to be measured, not assumed.
- Sweet potato with boiled egg at South breakfast (owner's description of
  the breakfast habit). `SOUTH_BREAKFAST` already has an optional egg side
  (N7); no sweet potato dish exists.

**Disposition.** DONE. The N2c snack claim is CORRECTED.

## 2026-10-08 — N18: the three accepted survivors get tests after all

**Asked.** Owner, 2026-10-08, after N17: fix the remaining flags now rather
than leave them. Entry "N16" left three rows surviving, each documented as
expected: B2 (finding 33), B5 (D4b, "a bad mutation of the probe's own"),
B8 ("a pure optimisation: removing it changes no verdict"). Each statement
was about the *pipeline's* verdict. Each mechanism still changes what its
own function returns or logs, and that is testable directly, as N17 did for
B4. One commit per row.

### B8 — the quality pre-filter

`feasible_combinations` drops a combination whose components, all at their
maximum count, cannot reach `quality_protein_floor_g`. The solver re-checks
the floor, so the final plate never changes; the pre-filter's own return
value does. No test called `feasible_combinations` with a quality floor.

New: `tests/test_planner_combinations.py::TestFeasibilityPreFilter::test_a_combination_that_cannot_reach_the_quality_floor_is_dropped`.
Fixture a1 given DIAAS 1.0; hand arithmetic in the test (4 g floor keeps the
two combinations holding a1's 5 g).

```
B8   covered      tests/test_planner_combinations.py::TestFeasibilityPreFilter::test_a_combination_that_cannot_reach_the_quality_floor_is_dropped
1 mechanisms: 1 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

The statement "removing it changes no verdict" stays true and stays in
`docs/build_status.md`; it no longer means "no test can see it".

### B5 — the low side of `quality_protein_bounds`

Earlier called "a bad mutation of the probe's own" because no caller reads
`[0]`. That is still true of the callers (`combinations.py` and
`validator.py` both read `[1]`), but the function returns the pair and
promises both sides in its docstring. A direct test pins both, so the row is
kept and now graded.

New: `tests/test_planner_combinations.py::TestMacroBounds::test_quality_protein_bounds_span_the_fewest_to_the_most_servings`
(2..4 servings of a1 at DIAAS 1.0: low 10 g, high 20 g).

```
B5   covered      tests/test_planner_combinations.py::TestMacroBounds::test_quality_protein_bounds_span_the_fewest_to_the_most_servings
1 mechanisms: 1 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

### B2 — the early return on an unfillable required slot

Finding 33 kept this `return ()` on purpose: deleting it leaves the return
value the same, but falls through to the second log line, which says "0
combinations" and never names the blocking slot. The finding recorded that
no assertion reads the log line. One now does.

New: `tests/test_planner_combinations.py::TestEnumeration::test_an_unfillable_slot_is_logged_once_and_by_name`
(two-slot fixture with only its cat_a dishes; exactly one log record from
`core.planner.combinations`, saying "no legal selection" and naming `['b']`).

```
B2   covered      tests/test_planner_combinations.py::TestEnumeration::test_an_unfillable_slot_is_logged_once_and_by_name
1 mechanisms: 1 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

Two comments that said otherwise now carry a dated note rather than being
rewritten: the one above the `return ()` in `core/planner/combinations.py`
(comment only, no code change) and the B2 row in
`docs/design/probes/d4b_mutations.py`.

**Disposition.** FIXED for B2, B5, B8. With N17's B4, every row the N16
sweep did not grade "covered" is now covered by a test that names it.
Finding 33's decision to keep the early return stands; its "no test can
catch" no longer does.

## 2026-10-08 — N17: B4 gets a test of its own

**Asked.** Owner, 2026-10-08 (option 1 after N16): close the one gap the
full sweep found. Entry "N16" below: harness row B4 (`macro_bounds`' low
bound uses the unit's `min_count`) was soft-covered, caught by 37 tests,
none in `OWN_TESTS[COMBINATIONS]`.

**Why the combinations tests could not see it.** Their feasibility fixture
(`tests/factories.py`, `FEASIBILITY_RECIPES`) pins every serving unit at
`min_count = max_count = 1`. At those counts the low and high bounds are the
same number, so moving the low side to `max_count` changes nothing any test
in that file reads.

**Changed.** `tests/test_planner_combinations.py::TestMacroBounds`, one test:
`a1` (100 kcal, 500 mg sodium per 100 g, one unit = 100 g) with a unit of
2..4 servings. Hand arithmetic in the test: energy (200, 400), sodium
(1000, 2000). No code under `core/` changed; the fixture is untouched, so no
other test moves.

**Before** (entry "N16"):

```
  soft-covered B4   combinations.py    macro_bounds low uses the unit's min_count
               37 incidental: tests/test_api_leave_empty.py::test_only_optional_courses_are_marked_removable
```

**After:**

```
B4   covered      tests/test_planner_combinations.py::TestMacroBounds::test_the_low_bound_is_the_fewest_servings_and_the_high_the_most
1 mechanisms: 1 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

**Disposition.** FIXED. B4 is covered by a test that names it.

## 2026-10-08 — N16: full deletion sweep after N15, every row read

**Asked.** Owner, 2026-10-08 (option 1 after N15): run the whole harness to
find any other row that tests nothing. Report only.

**Run.** Branch `full-sweep` off main `61531f8`, working tree clean apart
from the untracked queue file:

```
PYTHONHASHSEED=0 PYTHONPATH=. NO_COLOR=1 PY_COLORS=0 python docs/design/probes/d4b_mutations.py
98 mechanisms: 94 covered, 1 soft-covered, 3 SURVIVED, 0 harness errors.
  soft-covered B4   combinations.py    macro_bounds low uses the unit's min_count
               37 incidental: tests/test_api_leave_empty.py::test_only_optional_courses_are_marked_removable
  SURVIVED     B2   combinations.py    unfillable required slot returns no combinations
  SURVIVED     B5   combinations.py    quality_protein_bounds spans min..max count
  SURVIVED     B8   combinations.py    pre-filter discards combos that cannot reach the quality floor
```

Started 12:54, finished after 15:10 (about 2 h 20 min).

**No harness errors.** No other row matches nothing, so the N3b/N3c defect
(entry "N15" below) has no siblings today.

**Survivors: all three already documented, none new.** `B2` is finding 33's
accepted survivor (comment on the row). `B5` is a bad mutation of the probe's
own: it moves the low side of `quality_protein_bounds`, which no caller
reads (D4b entries, "Three survivors are not in this table"). `B8` is the
quality pre-filter, documented as an optimisation that changes no verdict.

**B4, soft-covered: guarded, but not by a test written for it.** Full
failure list by hand (same edit, non-browser suite, restored after; `git
status --short core/` empty):

```
B4 37 failed, 514 passed, 102 deselected, 1 warning in 63.47s (0:01:03)
   10 tests/test_planner_quality.py      4 tests/test_shown_plate_preference.py
    4 tests/test_planner_validator.py    4 tests/test_dish_picks.py
    3 tests/test_leave_empty.py          3 tests/test_api_targets.py
    3 tests/test_api_picks.py            3 tests/test_api_leave_empty.py
    2 tests/test_planner_decline.py      1 tests/test_planner_solver.py
```

Among them `test_planner_validator.py::TestAHardCeilingIsNeverWidened::test_relaxation_recovers_combinations_the_tight_pre_filter_discarded`
and `test_planner_solver.py::TestModerateProfileProperty::test_200_random_moderate_profiles_all_solve`.
None is in `OWN_TESTS[COMBINATIONS]` (`test_planner_combinations.py`,
`test_planner_determinism.py`), so the harness grades it soft. Deleting the
mechanism is not silent; what is missing is a test in the combinations file
that pins the low bound of `macro_bounds` at the unit's `min_count` by hand
arithmetic. The D4b-i sweep (55 rows) listed `C3`, not `B4`, as its one
soft-covered row; when `B4` stopped being caught by a scoped test is not
established here.

**Disposition.** OPEN, low: B4 needs one focused test in
`tests/test_planner_combinations.py`. Not fixed here (report-only task).

## 2026-10-08 — N15: deletion rows N3b/N3c had tested nothing since N8

**Asked.** Owner, 2026-10-08 (option 1 after N14): fix the two broken
removal checks, so the egg/fish/chicken preference is really guarded.

**Found.** Rows N3b ("rung 0 returns the picked plate") and N3c ("a relaxed
rung returns the picked plate") in `docs/design/probes/d4b_mutations.py`
searched for `plan = _pick(solved)` at two call sites. N8 (`deba558`,
2026-09-29) removed both and added one shared call, `plan = _pick(chosen)`,
in `_accepted`. Checked with `git show deba558 -- core/planner/validator.py`:
two `-        plan = _pick(solved)` lines, one `+        plan = _pick(chosen)`.
From then both rows reported a harness error and deleted nothing. Before,
old rows run against today's tree:

```
2 mechanisms: 0 covered, 0 soft-covered, 0 SURVIVED, 2 harness errors.
  ERROR        N3b  validator.py       rung 0 returns the picked plate, not solved[0]
               pattern not found in source
  ERROR        N3c  validator.py       a relaxed rung returns the picked plate, not solved[0]
               pattern not found in source
```

**Changed.** One call site, so one row: N3b now replaces
`plan = _pick(chosen)` with `plan = chosen[0]` (show the nearest plate,
ignoring both the preference and N14's fewer-repeats rule). N3c is retired,
not kept as documented-dead: the mechanism it named still exists and is
covered by the new N3b. Comment in the row says so.

**After.**

```
N3b  covered      tests/test_planner_quality.py::TestThePerturbationTest::test_disqualifying_soya_chunks_moves_the_south_breakfast_figure
1 mechanisms: 1 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

The harness names only the first failure. Full list, by hand (same edit,
non-browser suite, then restored; `git diff --stat core/` empty after):

```
N3b 10 failed, 541 passed, 102 deselected, 1 warning in 68.15s (0:01:08)
    FAILED tests/test_api_leave_empty.py::test_a_removed_course_is_off_the_plate_with_solver_counts
    FAILED tests/test_planner_quality.py::TestAgainstTheRealLibrary::test_the_reference_breakfast_plate_is_idli_soya_kuzhambu_chutney
    FAILED tests/test_planner_quality.py::TestThePerturbationTest::test_disqualifying_soya_chunks_moves_the_south_breakfast_figure
    FAILED tests/test_planner_quality.py::TestThePerturbationTest::test_qualifying_tofu_hands_back_the_pre_slice_4_plate
    FAILED tests/test_repeated_mains.py::test_a_valid_plate_without_the_repeat_is_shown_over_the_nearer_one
    FAILED tests/test_repeated_mains.py::test_among_plates_without_a_repeat_the_nearest_is_shown
    FAILED tests/test_shown_plate_preference.py::TestPreferChoosesAmongValidPlates::test_the_nearest_preferred_plate_is_shown_over_a_nearer_one
    FAILED tests/test_shown_plate_preference.py::TestPreferChoosesAmongValidPlates::test_the_preference_also_applies_on_a_relaxed_rung
    FAILED tests/test_shown_plate_preference.py::TestTheRealDinner::test_a_non_vegetarian_north_dinner_shows_an_animal_protein_dish
    FAILED tests/test_shown_plate_preference.py::TestTheRealDinner::test_a_vegetarian_north_dinner_is_the_nearest_plate_with_fewest_repeats
restored
```

Both rungs the old rows split are red: rung 0
(`test_the_nearest_preferred_plate_is_shown_over_a_nearer_one`) and a
relaxed rung (`test_the_preference_also_applies_on_a_relaxed_rung`).

**Not checked.** A sweep of every row was started to look for other
"pattern not found" rows; it hit a 5-minute limit and printed nothing, so
it says nothing either way. How N3b/N3c went unnoticed for nine days: the
sweep reports harness errors in its summary line, and no full sweep was
read after N8. Worth a full sweep before the next harness change.

**Disposition.** FIXED for N3b/N3c. Other rows not re-swept.

## 2026-10-08 — N14: the shown plate avoids serving one main ingredient twice

**Asked.** Owner, 2026-10-08 (option 1 after N13): simple written rules
instead of AI ranking. First rule: prefer a plate where no main ingredient
appears in more than one dish. Never loosen a limit for it.

**Not a nutrition rule.** It changes which valid plate is shown, never what
counts as valid: no target, band, tolerance or count moves. That is why no
paper is cited for it. It is a judgment about how a plate is served, and
the labels below are the owner's to check.

**Labels (`a535939`).** Every recipe file now carries `main_ingredients`:
what the dish is named for or built around, from a closed list of 15
(`core/foods/models.py` `MAIN_INGREDIENTS`). Required. A misspelt word fails
to load. Judgment calls for the owner to confirm:
- Soya curd, soya onion raita and tofu bhurji count as **soya**, not curd.
  This is the soya-in-three-courses case from N12.
- Curd, onion raita, chaas and neer mor are all **curd**: raita with
  buttermilk counts as a repeat. No shown plate hits this today.
- Base dishes name their grain as well: masala dosa is rice and potato;
  aloo paratha is wheat and potato.
- Coconut is the label only for coconut chutney. Poriyals that use coconut
  are labelled for their vegetable.

**Premise measured before the planner change.**
`docs/design/probes/probe_repeated_main.py`, the 96 cases of N12:

```
before: plates shown 94; repeat a main ingredient 43; of those, a valid plate with fewer repeats exists 31
repeated ingredient on shown plates: {'soya': 41, 'carrot': 6}
```

**Change.** `plan_within_ladder`'s `_pick`, among plates valid at the
rung the ladder stopped on: the preferred plates (egg, fish or chicken where
the diet permits) if any, then the fewest repeated main ingredients, then
the nearest. The egg/chicken preference still comes first, as decided
2026-09-27.

```
after:  plates shown 94; repeat a main ingredient 21; of those, a valid plate with fewer repeats exists 0
repeated ingredient on shown plates: {'soya': 21, 'carrot': 1}
```

The 21 left have no valid plate with fewer repeats. All 31 plates that had a
better option improved: 22 now repeat nothing, and 9 repeat less. Most of
the 21 are vegan or vegetarian meals where soya is the only protein that
meets the floor.

**Plates that changed in pinned tests**, each re-derived by hand in its comment:
- South breakfast reference: soya curd x2 -> plain curd x1, idli 3 -> 5.
  Quality protein 13.0 + curd 145 g x 3.1/100 = 4.495 -> 17.495 g.
- The same plate with curd's DIAAS disqualified keeps its dishes and drops to
  13.0 g. With soya chunks disqualified it moves to soya idli 6, sambar 2,
  chutney 3, at 12.3504 g (soya flour alone).
- Tofu at DIAAS 0.80, North lunch: the soya onion raita is dropped, so
  phulka 4 + dal tadka 2 + tofu bhurji 1, the pre-slice-4 plate exactly.
- Vegetarian North dinner: soya onion raita -> onion raita. The test now
  asks for the nearest plate with the fewest repeats.

**Deletion checks.** Rows R8, R9 and M1 (labels): all covered, transcript in
`a535939`. Planner rows, from `docs/design/probes/d4b_mutations.py` and the
full failure list by hand:

```
N3a  covered      tests/test_dish_picks.py
V43  covered      tests/test_repeated_mains.py::test_a_valid_plate_without_the_repeat_is_shown_over_the_nearer_one
V44  covered      tests/test_dish_picks.py::TestAPickIsHonoured::test_a_pick_the_shown_plate_lacks_is_on_the_plate
V45  covered      tests/test_dish_picks.py::TestAPickIsHonoured::test_a_pick_the_shown_plate_lacks_is_on_the_plate
```

**Correction during the work.** The N3a line above is false. The mutation
deleted a line and left an empty block, so every planner test file failed
to import ("16 errors"). The harness scored that as covered. Fixed to
`pass`, then re-graded by hand with the full failure list:

```
N3a 5 failed, 534 passed, 94 deselected, 1 warning in 62.44s (0:01:02)
    FAILED tests/test_api_leave_empty.py::test_a_removed_course_is_off_the_plate_with_solver_counts
    FAILED tests/test_repeated_mains.py::test_a_preference_still_comes_before_fewer_repeats
    FAILED tests/test_shown_plate_preference.py::TestPreferChoosesAmongValidPlates::test_the_nearest_preferred_plate_is_shown_over_a_nearer_one
    FAILED tests/test_shown_plate_preference.py::TestPreferChoosesAmongValidPlates::test_the_preference_also_applies_on_a_relaxed_rung
    FAILED tests/test_shown_plate_preference.py::TestTheRealDinner::test_a_non_vegetarian_north_dinner_shows_an_animal_protein_dish
```

V44 (equal repeats: nearest) and V45 (count repeats, not dishes) each have
their own test among the failures listed by hand: V44 fails
`test_among_plates_without_a_repeat_the_nearest_is_shown`, and V45 fails all
six tests in `tests/test_repeated_mains.py`. The harness named
`test_dish_picks.py` only because it is first in collection order.

**Found in passing, not fixed** (queue rule). Rows N3b and N3c search for
`plan = _pick(solved)`. Since N8 the code says `plan = _pick(chosen)`, once,
for every rung. Both rows report "pattern not found" and test nothing. The
2026-09-27 transcript showing them covered predates that change. They should
become one row.

**Not explained.** One run of the non-browser suite stalled for over 10
minutes at near-zero CPU and was stopped. The immediate rerun took 59 s and
passed, and the full run below did not stall. Cause unknown.

**Full suite.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q` (on
`ai-ranking`, which does not yet include N11's 8 tests):
`633 passed, 1 warning in 212.10s (0:03:32)`.

**Owner's check (2026-10-08).** Soya curd, soya onion raita and tofu stay
soya. Grains in base dishes stay counted. Chaas and neer mor change from curd
to a new word, buttermilk: raita with buttermilk is a usual pairing, not a
repeat. Re-measured after the change, with the same results, since no shown
plate had paired them:

```
plates shown 94; repeat a main ingredient 21; of those, a valid plate with fewer repeats exists 0
repeated ingredient on shown plates: {'soya': 21, 'carrot': 1}
```

`FOODAI_WEB_TESTS=required python -m pytest tests/ -q`:
`633 passed, 1 warning in 249.78s (0:04:09)`.

**Disposition.** Done; labels checked by the owner.

## 2026-10-07 — N13: stopped at the premise — the local model does not choose better plates

**Asked.** Owner, 2026-10-07 (option 1): build AI ranking. The model picks
among plates the planner has already made valid; the planner's nearest plate
stays the fallback; the model never touches a count.

**Checked before wiring anything in.** `llm/ranker.py` (the model call) was
written and measured live; nothing in the app calls it. Model
`qwen2.5:7b-instruct` on Ollama 0.13.5, RTX 4060 laptop GPU. The model sees
the region, the meal and, per plate, a letter and dish names: no digit at
all. Its reply is held to one of the letters. Cases: the 96 of entry "N12";
83 had two or more plates to choose from. Offered: the nearest 8 plates,
animal-protein plates only where the diet permits one and one exists (the
planner's existing preference).

`docs/design/probes/probe_ranker_live.py`, run twice, with an Ollama restart
in between:

```
run 1: cases 83  no answer 4  chose the nearest (A) 43  seconds: first 15.07, median 0.52, max after first 15.02
run 2: cases 83  no answer 0  chose the nearest (A) 45  seconds: first 0.64, median 0.55, max after first 0.95
answered in both runs 79 same plate 75
```

- Speed is fine once loaded: about half a second. Run 1's four misses were
  the first four requests while the model was still loading; each waited the
  full 15 s and fell back, as designed.
- Not fully repeatable: 4 of 79 answers changed across the restart, despite
  temperature 0 and a fixed seed.

**The question that decides it: are its choices better?** "Better to eat"
cannot be counted, but one part of it can: the same main ingredient in
several dishes. N12's reason for ranking was exactly that (soya in three
courses). The count, over the plates each run answered:

```
run 1: soya dishes on the plate: nearest 103, model 102; model plate has more soya dishes in 10 cases, fewer in 9
run 2: soya dishes on the plate: nearest 108, model 106; model plate has more in 10 cases, fewer in 10
```

No better than the nearest plate. One fairer try, so the result is not just
the first prompt: `docs/design/probes/probe_ranker_reason.py` asks for a short
reason per plate before the choice (often helps small models). The prompt
names no ingredient, so the count is not the prompt's own words coming back.

```
cases 83 no answer 0 chose A 9 seconds median 5.31 max 11.26
soya dishes: nearest 108 model 137
model more soya than nearest 34 fewer 11
```

Worse, and ten times slower. Its reasons do not match the plates. On the
vegetarian 55 kg South Indian lunch, it wrote that plate A ("Soya kuzhambu …
Soya curd") repeats no main ingredient, then chose plate C, which its own
reason said repeats two.

**Conclusion.** The goal was a better plate from the model. On the one
property that can be checked, this model gives a different plate, not a
better one. Wiring it in would change what people see on no evidence that it
helps. Stopped under the queue rule: the premise was wrong, so the work was not
reshaped to fit it. No planner, API or page change.

**Not tested.** Larger or hosted models; other prompt styles beyond the two
above; any property of "good to eat" other than repeated main ingredient.

**Disposition.** Stopped. The next step is the owner's decision.

## 2026-10-07 — N12: is there anything for an AI ranking step to choose between?

**Asked.** Owner, 2026-10-07: start the AI ranking series (architecture step
5: the model ranks plates that are already valid; it never sets a count).
Measure first whether a meal usually has several valid plates that differ.

**How.** `docs/design/probes/probe_ranking_room.py`, real library, the call
the API makes. 4 diets (vegetarian, eggetarian, non-vegetarian, vegan) x 3
weights (55, 70, 90 kg; male, 170 cm, 30 y, moderate, maintain) x 8 meals =
96 cases. The valid plates are those `solve` returns at the rung the ladder
stopped on (the probe records the last `solve` call; the ladder stops on the
first non-empty one).

**Result.**

```
meal             bodies declined | valid plates min/median/max | different dishes median | of nearest 10, differ from shown by 2+ dishes: median | bodies with only 1 plate
south breakfast      12        0 |     7     20    41            |     10                  |      5                                            |   0
south lunch          12        0 |     1      8    20            |      8                  |      4                                            |   1
south dinner         12        0 |     2     12    22            |     10                  |      6                                            |   0
south snack          12        0 |     1      2     3            |      2                  |      0                                            |   2
north breakfast      12        0 |     1     10    14            |      9                  |      5                                            |   1
north lunch          12        0 |     4     15    30            |      8                  |      5                                            |   0
north dinner         12        0 |     7     16    25            |     11                  |      7                                            |   0
north snack          12        2 |     1      3     4            |      3                  |      0                                            |   1

vegetarian 70 kg south_indian lunch: 9 valid plates
   shown: Carrot poriyal, Soya curd, Soya kuzhambu, Steamed rice
   1. Carrot poriyal, Soya curd, Soya kuzhambu, Steamed rice
   2. Sambar, Soya chunk poriyal, Soya curd, Steamed rice
   3. Carrot poriyal, Curd, Soya kuzhambu, Steamed rice
   4. Carrot kootu, Soya chunk poriyal, Soya curd, Soya kuzhambu, Steamed rice
   5. Carrot poriyal, Soya chunk poriyal, Soya curd, Soya kuzhambu, Steamed rice

non_vegetarian 70 kg north_indian dinner: 25 valid plates
   shown: Anda curry, Dal tadka, Phulka
   1. Aloo sabzi, Phulka, Soya chunk masala, Soya onion raita
   2. Aloo sabzi, Onion raita, Phulka, Soya chunk masala
   3. Anda curry, Dal tadka, Phulka
   4. Anda curry, Dal tadka, Phulka, Soya onion raita
   5. Aloo sabzi, Paneer paratha, Soya chunk curry, Soya onion raita
```

Run time 18.6 s.

**Reading.**
- Main meals: yes, there is room. A median of 8 to 20 valid plates, and about
  half of the nearest 10 differ from the shown plate in two or more dishes.
- Snacks: little room. A median of 2 to 3 plates, and none of the nearest
  differ by two dishes. Ranking would change almost nothing there.
- Nearest-to-target order is a number fit, not a food judgment. It ranks
  plates with soya in three courses high: plate 5 of the vegetarian lunch, and
  plate 1 of the dinner (soya chunk masala and soya onion raita). Plate 3 of
  the vegetarian lunch swaps soya curd for plain curd at no loss of validity.
  Whether any of these is worse to eat is a judgment, not a measurement. This
  is the gap ranking is meant to fill.
- Seven cases have only one valid plate. Ranking there must leave the plate
  as it is.

**Not measured.** Whether the model's order is better than the current
order. That needs a person to judge plates side by side. It is the check the
ranking step itself must carry.

**Disposition.** Premise holds for main meals. Ranking (N13) only with the
owner's go-ahead.
## 2026-10-02 — N11: a user's dish choices are kept per meal between visits

**Asked.** Owner, 2026-10-02: save favourites. Built on the measurement in the
entry below (saved choices stop fitting after a profile edit 20% of the time).

**What was built.**
- API (`3868f1e`): table `saved_choices`, one row per (user, region,
  meal_slot), holding recipe ids and course names, never a quantity.
  `GET /api/choices` lists them; `PUT /api/choices` keeps, replaces or (two
  empty lists) forgets one meal's. Both lists required. A pick must be a dish
  the meal can hold; a removed course must be optional. Fit to the user's
  limits is not checked here: the planner asks that afresh every visit.
- Page: "Remember these choices" (shown when the plate has choices that
  differ from what is kept) and "Forget saved choices" (shown when something
  is kept). Generating a meal starts from its kept choices. When they don't
  fit, the page asks again with none, shows the suggested plate and says
  "Your saved choices for this meal don't fit its limits today, so this is
  the suggested plate. They are still saved." Nothing is loosened and nothing
  is deleted. If kept choices cannot be loaded, the page says so and offers
  neither button, since either could overwrite what is kept.
- Invariant 1 holds: nothing saved is a quantity; every count is solved.

**Deletion checks.**
- API, by hand, `tests/test_api_saved_choices.py`: C1–C9 all RED, each on
  the test named for it.
- Web, by hand, `tests/test_web_saved_choices.py`, rows F1–F14. **Correction
  during the work:** the first run was stopped at the ten-minute tool limit
  partway through F13, which left F13's deliberate break in
  `web/dashboard.js`. Found by checking every row's original line was
  present; restored before anything else ran. In that run F7 (remember sends
  no picks) and F8 (forget sends the current choices) **survived**: the walk
  saved only a removal, and forgot only when the plate had no choices, so
  neither mutation changed anything the test saw. The walk now saves a swap
  (onion tomato uttapam) beside the removal, and forgets while the saved
  choices are on the plate. All 14 rows were then re-graded against the final
  test:

```
F1  RED 8 errors        F2  RED 8 errors        F3  RED 8 errors
F4  RED 8 errors        F5  RED 2 failed        F6  RED 4 failed
F7  RED 2 failed        F8  RED 8 errors        F9  RED 2 failed
F10 RED 8 errors        F11 RED 1 failed        F12 RED 1 failed
F13 RED 1 failed        F14 RED 8 errors
```

"8 errors" means the browser walk stopped (a wait it needed never came):
a real failure, but it does not say which step broke.

**Not covered.** Layout: screenshots at 1300 px and 390 px show the buttons
and note correctly; no test guards layout. Saved choices in a database that
existed before this change: `create_all` adds the new table at start-up;
checked by the live servers in this session, not by a test.

**Full suite.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q`:
`641 passed, 1 warning in 271.12s (0:04:31)`.

**Disposition.** Done.

## 2026-10-02 — Saved dish choices stop fitting after a profile edit 20% of the time (measured before building N11)

**Asked.** Owner, 2026-10-02: save favourites, so a user's swaps and
removals for a meal carry over to the next visit.

**Premise tested before building.** Saving means replaying the same picks and
removed courses later. The planner never loosens a limit to fit a choice, so
a saved choice that no longer fits is a decline. How often is that?
`docs/design/probes/probe_saved_choices_drift.py`, real library via
TestClient: 4 diets × 2 weights × 6 meals; for each suggested plate, every
removal the server offers and the first three swaps; each choice that fits
today is replayed after the profile edits a returning user is likeliest to
make.

```
$ PYTHONPATH=. python docs/design/probes/probe_saved_choices_drift.py
choice   profile edit replays  no longer fit
pick     goal gain_muscle     110     10 (9%)
pick     goal lose_fat     109     74 (68%)
pick     weight +5        110     15 (14%)
pick     weight -5        110      5 (5%)
remove   goal gain_muscle      36      0 (0%)
remove   goal lose_fat      36      5 (14%)
remove   weight +5         36      3 (8%)
remove   weight -5         36      3 (8%)
total                     583    115 (20%)
```

A sample, not the full sweep: the first version (3 weights, every swap) was
stopped at the ten-minute tool limit before printing anything.

**What it means for the build.** Replaying a saved choice is fine most of the
time, but not rarely-failing: a user who switches to fat loss loses most
swapped-in dishes. So:
- a saved choice that no longer fits must never be forced (no limit
  loosened) and never silently dropped: the page shows the suggested plate
  and says the saved choices don't fit this meal's limits today;
- saved choices are kept, not deleted, when they don't fit, since the user
  may change back; a "forget" control removes them;
- saving is explicit ("Remember these choices"), not automatic, so a one-off
  swap does not become a standing preference.

**Disposition.** Building N11 on this basis.

## 2026-09-30 — N10: "Remove" on any optional dish, built as a planner input (core, API, web)

**Asked.** Owner, 2026-09-30, chose the real build: remove a single dish,
whether the user added it or the planner chose it ("no egg today"). Follows
the entry below, which showed that dropping the pick brings the course back.

**What was built.** "Leave this course empty" is an input the planner holds
exactly as it holds picks.
- Core (`d64c9c2`): `leave_empty` on `plan_within_ladder` and `plan_meal`.
  The rung is chosen without it; the plate is chosen among those valid at that
  rung with no dish in any named slot; none is a decline that names the course
  ("leaves out the egg side"). No limit is loosened. `LadderOutcome.emptiable_slots`
  says which courses have such a plate, keeping the other slots' picks and
  removals.
- API (`153cc07`): `POST /api/plan` takes `leave_empty`; each `swap_options`
  entry carries `can_be_empty`, required on the wire (finding 40).
- Web: a "Remove" on each dish whose course the server marks removable.
  Removing sends the slot in `leave_empty` and drops any pick in that course;
  putting a dish back into a course ends its removal; "Back to the suggested
  plate" and "Generate" clear removals; a refused removal keeps the plate on
  screen and says which dish, by name.
- Invariant 1 holds: no quantity is set by anything but the solver. Removing
  the egg re-solves the whole plate (measured on screen: idli 6 → 3, sambar →
  soya kuzhambu, curd added at 2 katori), because the protein the egg carried
  has to come from somewhere. The page shows the server's plate, not an edit
  of the old one.

**Measured on the real library** (70 kg eggetarian South breakfast,
`can_be_empty`): tiffin_item False, gravy_accompaniment False, chutney False,
egg_side True, curd_course True, beverage True. Removing any of the three
required courses declines by name and leaves the plate alone.

**Deletion checks.**
- Planner, `d4b_mutations.py` rows V30–V42 (V41, V42 new this task):
  13 mechanisms: 13 covered, 0 survived, 0 harness errors. Two problems on
  the way, both fixed: V32's search line existed twice after this work (the
  harness refused to guess; the line is now one shared helper), and V41
  survived because the synthetic template has one optional course. Added
  `TestTwoRemovableCourses`, which makes the curd course optional too
  (800 kcal: 58 valid plates, 3 without curd, 12 without crisp, none
  without both).
- API, by hand, `tests/test_api_leave_empty.py`: P1 (leave_empty not passed on)
  RED 2, P2 (can_be_empty hard-coded True) RED 1, P3 (can_be_empty defaulted)
  RED 1.
- Web, by hand, `web/` (the harness cannot grade it), tests
  `test_web_remove_dish.py`, `test_web_add_dish.py`, `test_web_dish_swap.py`:
  R1–R11 all RED. R1, R8, R9, R10: one named test fails. R2–R7, R11: the
  whole browser walk stops (8 errors) because a click or wait it needs never
  happens. That is a real failure, but it is coarse: it does not say which
  test's mechanism broke, so read it as "something in the removal flow".

**Not covered.** Layout. The screenshot check (desktop 1300 px and phone
390 px) found one defect: the egg menu was cut off ("Avicha muttai (boil")
when "Remove" shared its line. Fixed by letting that line wrap; re-shot, full
name shown, "Remove" drops below when tight. No test guards this.

**Full suite.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q`:
`621 passed, 1 warning in 205.43s`.

**Disposition.** Done. Still open, not part of this task: saving favourites
across visits; South snack egg side; the AI ranking layer; chicken fat
review; owner check of the AMDR source; omelette oil constant.

## 2026-09-30 — "Remove an added dish" cannot be done by dropping its pick (found before building)

**Asked.** Owner, 2026-09-30: remove a single dish the user added (N9)
without undoing every other swap.

**Premise tested before building.** The cheap design is a "Remove" button
that drops the added dish's pick and asks the planner again. That only
removes the dish if the planner then leaves the course empty.
`docs/design/probes/probe_remove_added_dish.py` runs the realistic flow on
the real library (4 diets × 3 weights × 6 templates, 70 kg-style bodies):
suggested plate, add a dish to an empty optional course, optionally swap one
other dish, then drop the added dish's pick.

```
$ PYTHONPATH=. python docs/design/probes/probe_remove_added_dish.py
remove flows: 155 course comes back: 67
  ('vegetarian', 70, 'north_indian', 'lunch', 'added', 'paneer_masala', 'other pick', 'soya_chunk_curry', 'after remove:', ['Paneer masala'])
  ('vegetarian', 70, 'north_indian', 'lunch', 'added', 'paneer_masala', 'other pick', 'soya_onion_raita', 'after remove:', ['Paneer masala'])
  ('vegetarian', 70, 'north_indian', 'lunch', 'added', 'tofu_bhurji', 'other pick', 'soya_onion_raita', 'after remove:', ['Paneer masala'])
  ('eggetarian', 55, 'north_indian', 'lunch', 'added', 'soya_onion_raita', 'other pick', 'soya_chunk_masala', 'after remove:', ['Soya onion raita'])
  ('eggetarian', 55, 'north_indian', 'lunch', 'added', 'soya_onion_raita', 'other pick', 'aloo_sabzi', 'after remove:', ['Soya onion raita'])
  ('eggetarian', 55, 'north_indian', 'dinner', 'added', 'onion_raita', 'other pick', 'soya_chunk_curry', 'after remove:', ['Soya onion raita'])
```

In 67 of 155 flows (43%) the course comes back, often with the very dish the
user just removed. This happens because a swap elsewhere moves the planner's
best plate to one that includes that course. A "Remove" built this way would
visibly do nothing almost half the time. That is a control that lies. Not
built.

**What a real remove needs.** The planner has to accept "leave this course
empty" as an input, the way it accepts picks:
- a new argument through `plan_within_ladder`, `plan_meal` and
  `POST /api/plan`;
- a decline when no valid plate leaves the course empty (the added dish may
  have been carrying protein), named, never loosened;
- `swap_options` that respect it;
- mutation rows;
- the page control.

That is core, API and web, which is larger than the small page change this
was proposed as. Stopped here for the owner to decide scope, in particular
whether "remove" also applies to optional dishes the planner itself chose
(e.g. the egg side on an eggetarian plate), which the same mechanism would
cover.

## 2026-09-30 — one timed-out browser wait broke every browser test after it: cause was nested waits, not missing clean-up

**Correction first.** The N9 entry below logged this and said the fix was
`try/finally` around the browser in every `tests/test_web_*.py` fixture.
That diagnosis was a guess, and it was wrong about both the cause and the
reach. A timeout does not break the run in general. Only one pattern does,
and only the two newest web test files used it.

**Reproduced in isolation.** `docs/design/probes/probe_nested_network_waits.py`
runs, on a blank page with no servers, a module whose fixture times out, then
a clean module that only launches a browser:

```
$ python docs/design/probes/probe_nested_network_waits.py
plain wait_for_selector timeout          next module: passed  1 passed, 1 error in 1.58s
single expect_response timeout           next module: passed  1 passed, 1 error in 2.09s
expect_request around expect_response    next module: FAILED  1 failed, 1 error in 1.62s
```

Only `expect_request` wrapped around `expect_response` breaks the next module
("This event loop is already running", then "using Playwright Sync API inside
the asyncio loop" everywhere after). In scratch runs, `try/finally` around
that nesting also stopped the cascade. The nesting has no purpose, though: the
request a response answers is `resp.value.request`.

**Fixed.** The five nested waits (`tests/test_web_dish_swap.py` 4,
`tests/test_web_add_dish.py` 1) are now a single `expect_response`, with the
request read from it. `tests/test_web_no_nested_waits.py` fails if any
`tests/test_web_*.py` calls `expect_request`. Deletion check: with the old
`test_web_dish_swap.py` restored it went red, naming lines 92, 113, 126, 148.

**Before and after, the case that exposed it** (N9 row A4, same four web
files):

```
before  A4 choice is sent as a pick              RED  1 passed, 28 errors in 35.19s
after   A4 choice is sent as a pick              RED  22 passed, 7 errors in 73.01s (0:01:13)
```

The 7 are all in `tests/test_web_add_dish.py`, where the fault is.

**The N8 and N9 web deletion checks, rerun on the changed tests.** All 17
are still red. S8's search text now matched twice (N9's add menu repeats the
line), so the sweep stopped at S8 without editing anything. It was narrowed to
the swap menu, and S8 to S10 were run on their own:

```
S1 picks sent in the request             RED  12 passed, 8 errors in 36.76s
S2 a refused swap keeps the plate        RED  12 passed, 8 errors in 38.02s
S3 a refused swap is undone              RED  1 failed, 19 passed in 32.21s
S4 a swap replaces its slot's pick       RED  1 failed, 19 passed in 31.56s
S5 reset drops the picks                 RED  12 passed, 8 errors in 39.35s
S6 reset hidden with no picks            RED  2 failed, 18 passed in 32.18s
S7 note names the dish                   RED  1 failed, 19 passed in 32.73s
S8 menu shows names                      RED  2 failed, 18 passed in 36.88s
S9 no menu for a one-dish slot           RED  1 failed, 19 passed in 36.27s
S10 swap uses the shown meal             RED  1 failed, 19 passed in 35.53s
A1 skip courses already on the plate     RED  22 passed, 7 errors in 72.04s (0:01:12)
A2 no menu for a course with no dish     RED  1 failed, 28 passed in 42.48s
A3 menu opens on a prompt                RED  3 failed, 26 passed in 43.57s
A4 choice is sent as a pick              RED  22 passed, 7 errors in 73.01s (0:01:13)
A5 course named in the label             RED  1 failed, 28 passed in 47.52s
A6 add row is not a dish row             RED  1 failed, 26 passed, 2 errors in 46.78s
A7 add rows are drawn at all             RED  22 passed, 7 errors in 76.17s (0:01:16)
```

**Suite.**

```
$ FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p no:cacheprovider --color=no
593 passed, 1 warning in 294.39s (0:04:54)
```

## 2026-09-30 — add a dish to an empty optional course (N9)

**Asked.** Owner, 2026-09-30, chose the first N8 follow-up: let the user add a
dish to an optional course the plate leaves empty. The N8 entry below logged
the gap: the server lists `curd_course` dishes for the South breakfast plate,
but that plate has no curd row, so there was no menu to choose one from.

**Premise checked before building.** Asking for one of those dishes already
returns a valid plate, so no core or API change is needed. TestClient, 70 kg
male, maintain, 2026-09-30:

```
eggetarian south_indian breakfast True empty slots: [('curd_course', ['Soya curd', 'Curd']), ('beverage', [])]
   add soya_curd -> True [('tiffin_item', 'soya_idli', 5), ('gravy_accompaniment', 'sambar', 1), ('chutney', 'coconut_chutney', 3), ('egg_side', 'muttai_omelette', 1), ('curd_course', 'soya_curd', 1)]
vegetarian south_indian lunch True empty slots: [('crisp', [])]
vegetarian north_indian lunch True empty slots: [('sabzi', ['Aloo sabzi', 'Paneer masala', 'Tofu bhurji'])]
   add aloo_sabzi -> True [('grain_base', 'phulka', 3), ('legume_curry', 'soya_chunk_masala', 2), ('sabzi', 'aloo_sabzi', 1)]
non_vegetarian north_indian dinner True empty slots: [('salad_or_raita', ['Onion raita', 'Soya onion raita'])]
   add onion_raita -> True [('bread', 'phulka', 3), ('dal', 'dal_tadka', 1), ('sabzi', 'anda_curry', 1), ('salad_or_raita', 'onion_raita', 1)]
vegetarian south_indian snack True empty slots: [('drink', ['Neer mor'])]
   add neer_mor -> True [('sundal', 'soya_chunk_sundal', 4), ('drink', 'neer_mor', 1)]
```

**What was built** (page only). Below the dishes, the page shows one "Add a
curd course" style menu for each course the plate leaves empty that has a dish
to offer. The menu opens on "Choose a dish", not on a dish: a preselected dish
would read as if it were on the plate. A course with a single dish still gets
a menu, because adding it or not is a choice. The chosen dish is sent as a
pick, exactly like an N8 swap. The server sets every count, and the limits
are not loosened. The row is deliberately not a `.dash-dish-row`, because
`tests/test_web_portion_grams.py` reads every such row as a dish on the
plate. New course names in `SLOT_LABELS`: egg side, drink, crisp side, salad
or raita, curd or raita, pickle, bread.

**Deletion checks, by hand.** Each mechanism was removed from the real file,
the four web files touching this page were run with
`FOODAI_WEB_TESTS=required`, and the file was restored (`git diff --stat
web/` unchanged after):

```
A1 skip courses already on the plate     RED  22 passed, 7 errors in 69.65s (0:01:09)
A2 no menu for a course with no dish     RED  1 failed, 28 passed in 39.69s
A3 menu opens on a prompt                RED  3 failed, 26 passed in 39.63s
A4 choice is sent as a pick              RED  1 passed, 28 errors in 35.19s
A5 course named in the label             RED  1 failed, 28 passed in 39.34s
A6 add row is not a dish row             RED  1 failed, 26 passed, 2 errors in 39.99s
A7 add rows are drawn at all             RED  22 passed, 7 errors in 69.52s (0:01:09)
```

A1 and A7 go red by the shared fixture timing out, not by a named assertion.
A4's 28 errors overstate the catch. Rerun against `tests/test_web_add_dish.py`
alone, the real failure is `TimeoutError: Timeout 30000ms exceeded while
waiting for event "response"` (choosing a dish sent nothing). The other 21
errors across three files are `It looks like you are using Playwright Sync
API inside the asyncio loop`. That is a cascade, so every later browser module in the same run errors too.
*(Corrected 2026-09-30, entry above: the cause is a timeout inside nested
`expect_request`/`expect_response` waits, not any timeout inside
`sync_playwright()`.)*

**Suite, final tree.**

```
$ FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p no:cacheprovider --color=no
592 passed, 1 warning in 226.93s (0:03:46)
```

**Found, not fixed.**

- **One timed-out browser fixture crashes every browser module after it** in
  the same run (the cascade above). It makes a single real failure read as
  dozens. A deletion check that reads only the count would over-report. *(Corrected 2026-09-30, entry above: the cause is nested
  network waits in two files, not missing clean-up in every fixture.)* Fixed there.
- **An added dish can only be removed by "Back to the suggested plate"**, which
  drops every swap. A "remove" control for an optional dish was not asked
  for, and is not built.

## 2026-09-29 — dish swap: the user picks a dish, the planner keeps the plate valid (N8)

**Asked.** Owner, 2026-09-29: "the user can alternate between dishes based on
their liking, like individual items". Owner decisions the same day: (1a) a pick
is offered and honoured only at the rung the ladder stopped on for the meal as
a whole — a liking never loosens a limit, and a pick that fits no valid plate is
declined, never quietly replaced; (2a) picks last for one visit. Saving
favourites is a later task.

**What was built.**

- `plan_within_ladder(..., picks=)` (deba558): the rung is chosen exactly as
  before, then the plate is chosen only among valid plates holding every pick.
  Every count still comes from the solver (invariant 1). No such plate is a
  decline naming the dish. `LadderOutcome.swap_options` lists, per slot, every
  dish on a valid plate at that rung that keeps the picks in the other slots.
- A declined pick's own slot still lists what fits (6af1a9d). Before it, a
  pick on no valid plate matched no slot, so every menu came back empty.
- `POST /api/plan` takes `picks` and returns `swap_options` with names; each
  component names its slot (c5f6240).
- Dashboard: a "Swap for" menu under each dish whose slot has a choice. It
  shows names only. Choosing a dish replaces any earlier pick in that slot and
  keeps the others. "Regenerate this plate" (entry below: it could only
  return the same plate) is now "Back to the suggested plate", hidden until
  there is a pick. A swap the server refuses leaves the shown plate, undoes
  the pick and says "Plain dosa couldn't be fitted into a plate that stays
  within this meal's limits, so your plate is unchanged." It does not show the
  decline page, which would read as the meal failing.

**Measured, real library, 70 kg eggetarian South breakfast** (TestClient,
2026-09-29):

```
[] [('tiffin_item', 'idli', 6), ('gravy_accompaniment', 'sambar', 1), ('chutney', 'coconut_chutney', 3), ('egg_side', 'avicha_muttai', 2)]
   tiffin_item ['idli', 'onion_tomato_uttapam', 'soya_idli']
   gravy_accompaniment ['sambar', 'soya_kuzhambu']
   chutney ['coconut_chutney']
   egg_side ['avicha_muttai', 'muttai_omelette', 'muttai_podimas']
   curd_course ['soya_curd', 'thayir_plain']
   beverage []
['onion_tomato_uttapam'] [('tiffin_item', 'onion_tomato_uttapam', 1), ('gravy_accompaniment', 'soya_kuzhambu', 2), ('chutney', 'coconut_chutney', 1), ('curd_course', 'soya_curd', 2)]
   tiffin_item ['idli', 'onion_tomato_uttapam', 'soya_idli']
   gravy_accompaniment ['soya_kuzhambu']
   chutney ['coconut_chutney']
   egg_side []
   curd_course ['soya_curd']
   beverage []
['muttai_omelette'] True [('idli', 6), ('soya_kuzhambu', 1), ('coconut_chutney', 2), ('muttai_omelette', 1)]
```

**Deletion checks.** Core, by the harness:

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py V25,V30,V31,V32,V33,V34
V25  covered      tests/test_planner_validator.py::TestAHardCeilingIsNeverWidened::test_the_protein_rung_fires_last_and_discloses
V30  covered      tests/test_dish_picks.py::TestAPickIsHonoured::test_a_pick_the_shown_plate_lacks_is_on_the_plate
V31  covered      tests/test_dish_picks.py::TestAPickNeverLoosensALimit::test_a_pick_valid_only_on_a_looser_rung_is_declined
V32  covered      tests/test_dish_picks.py::TestSwapOptions::test_the_picks_own_slot_still_offers_the_other_dishes
V33  covered      tests/test_dish_picks.py::TestSwapOptions::test_other_slots_options_keep_the_pick
V34  covered      tests/test_dish_picks.py::TestSwapOptions::test_the_picks_own_slot_still_offers_the_other_dishes
====================================================================================================
6 mechanisms: 6 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

Web, by hand (the harness cannot grade `web/`). Each mechanism was removed from
the real file, `tests/test_web_dish_swap.py` and `tests/test_web_no_identifiers.py`
were run with `FOODAI_WEB_TESTS=required`, and the file was restored
(`git diff --stat web/` unchanged after). On the first pass S9 and S10 survived,
and S1, S2 and S5 were scored "survived" by a parser that read only `FAILED`
lines while the fixture was erroring. Two tests were added
(`test_only_slots_with_a_choice_get_a_menu`,
`test_a_swap_goes_to_the_meal_on_screen`), and the parser now reads `ERROR`
too. Final pass, after the last layout edit:

```
S1 picks sent in the request             RED  12 passed, 8 errors in 34.51s
S2 a refused swap keeps the plate        RED  12 passed, 8 errors in 35.57s
S3 a refused swap is undone              RED  1 failed, 19 passed in 28.71s
S4 a swap replaces its slot's pick       RED  1 failed, 19 passed in 28.22s
S5 reset drops the picks                 RED  12 passed, 8 errors in 36.59s
S6 reset hidden with no picks            RED  2 failed, 18 passed in 28.65s
S7 note names the dish                   RED  1 failed, 19 passed in 28.53s
S8 menu shows names                      RED  2 failed, 18 passed in 28.46s
S9 no menu for a one-dish slot           RED  1 failed, 19 passed in 28.25s
S10 swap uses the shown meal             RED  1 failed, 19 passed in 27.65s
```

S1, S2 and S5 go red by the shared fixture timing out while waiting for a page
state that never comes. That is a real failure, but no single assertion names
it.

**Suite**, on the final tree (after the layout fix that moved the menu onto its
own line, because names were cut to "Mutt…" in the narrow desktop card):

```
$ FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p no:cacheprovider --color=no
585 passed, 1 warning in 187.74s (0:03:07)
```

**Found, not fixed.**

- **An optional slot the plate leaves empty cannot be filled.** The server
  lists `curd_course` options (soya curd, plain curd) for the suggested plate,
  but that plate has no curd row, so there is no menu to choose one from. An
  "add a dish" control is a separate idea.
- **Some picks leave nothing else to choose.** With uttapam picked, exactly one
  valid plate remains, so every other menu has one dish and disappears. It is
  a fact about the library's size at this rung, not a defect in the swap.
- **The page cannot reach a refused swap by clicking**, because every menu
  lists only dishes that fit. The refusal path is still needed for a stale
  menu, and it is tested by adding a dish to the menu from the test.

## 2026-09-29 — "Regenerate this plate" returns the same plate (found in N8 design)

Found while sizing the owner's dish-swap request (TASKS_3.md N8). The
dashboard's "Regenerate this plate" button (web/dashboard.html, `dashRegenerate`)
re-sends the same POST /api/plan, and the planner is deterministic by design
(finding 18), so it can only return the identical plate. Three calls, same
profile (70 kg, 175 cm, 28 y, male, moderate, maintain, eggetarian,
south_indian breakfast), via FastAPI's TestClient:

```
200 [('idli', 6), ('sambar', 1), ('coconut_chutney', 3), ('avicha_muttai', 2)]
200 [('idli', 6), ('sambar', 1), ('coconut_chutney', 3), ('avicha_muttai', 2)]
200 [('idli', 6), ('sambar', 1), ('coconut_chutney', 3), ('avicha_muttai', 2)]
```

A button labelled as producing something new that cannot is a claim the page
does not keep. Logged, not fixed; N8 is where it gets an honest meaning or is
removed.

## 2026-09-29 — South breakfast measured together, and a carb rotation (N7 step 4)

Steps 1-3 together (egg_side slot; avicha_muttai, muttai_omelette; plain_dosa,
onion_tomato_uttapam), against main before N7.

South breakfast, bodies with 0/1/2+ valid plates (`probe_nonveg.py`):
vegetarian 4/8/60 -> 4/8/60; eggetarian 4/8/60 -> 2/0/70; non-veg 2/10/60
-> 2/4/66. Shown an egg or other animal dish: eggetarian 0 -> 70/72, non-veg
58 -> 70/72.

Whole library, 2+ plates at the accepted rung:

```
===NONVEG
template                            vegetarian            eggetarian        non_vegetarian
south_indian/breakfast              4 / 8 / 60            2 / 0 / 70            2 / 4 / 66
south_indian/lunch                 6 / 24 / 42           6 / 23 / 43            2 / 8 / 62
south_indian/dinner                10 / 8 / 54           10 / 7 / 55            1 / 8 / 63
north_indian/breakfast             1 / 14 / 57           1 / 14 / 57           1 / 14 / 57
south_indian/snack                 2 / 19 / 51           2 / 19 / 51           2 / 19 / 51
north_indian/snack                  3 / 8 / 61            3 / 4 / 65            3 / 4 / 65
north_indian/lunch                  3 / 6 / 63            3 / 6 / 63            0 / 4 / 68
north_indian/dinner                 1 / 4 / 67            1 / 4 / 67            0 / 0 / 72
2+ total                               455/576               471/576               504/576
===RANK (vegetarian + vegan)
overall: 779/1152 = 67.6% offer >= 2 valid plates (exit condition: >= 50%)
  south_indian/breakfast : 118/144 = 81.9%
```

Against N6's figures (2026-09-29): vegetarian 455 unchanged, eggetarian 461
-> 471, non-veg 498 -> 504, vegetarian + vegan 779 unchanged. No other
template moved.

**Rotation.** Nothing in the app varies dishes: `combinations_excluding_recent`
(core/planner/combinations.py) is tested but no app path calls it, and
/api/plan returns one best plate per meal, so the same plate repeats every
day. `docs/design/probes/probe_south_breakfast_rotation.py` asks what a
rotation would give: 7 days, each day barring the tiffin eaten on the
previous 2 days, everything else free.

```
vegetarian   bodies 68  distinct carbs in 7 days {1: 7, 2: 1, 3: 60}  declined days 30/476  carb-days {'soya_idli': 156, 'idli': 126, 'plain_dosa': 94, 'onion_tomato_uttapam': 70}
eggetarian   bodies 70  distinct carbs in 7 days {1: 2, 2: 6, 3: 62}  declined days 20/490  carb-days {'idli': 155, 'soya_idli': 144, 'plain_dosa': 108, 'onion_tomato_uttapam': 63}
```

Run from a scratch copy; the tracked file differs only in its header. With
a rotation, 60/68 vegetarian and 62/70 eggetarian bodies get three different
carbs in a week, and plain dosa and uttapam get a third of carb-days. The
cost: 30/476 and 20/490 days have no valid plate once the fitting carbs are
barred. A rotation that declines rather than falling back is not shippable
as is.

**Owner request, 2026-09-29, queued as TASKS_3.md N8:** "the user can
alternate between dishes based on their liking, like individual items" --
swap one dish (idli -> dosa -> uttapam, boiled egg -> omelette) and get back
a plate that still validates. Any swap goes through the solver (invariant
1). The declined days above are the case its design must answer.

## 2026-09-29 — plain dosa and onion tomato uttapam (N7 step 3)

Owner's basis (2026-09-29): "we can alternate the carbs with idli, dosa,
utthappam which are common household breakfast". The library had idli and
soya_idli, and dosa only as masala_dosa and egg_dosa.

Added, proportions fixed before measuring:

- `plain_dosa`: masala_dosa's dosa lines unchanged, 90 g = `measure.dosa_g`.
- `onion_tomato_uttapam`: per uttapam from the Indian Nutrient Databank
  (Vijayakumar et al., Curr Dev Nutr 2024;8:103790, DOI
  10.1016/j.cdnut.2024.103790; open data, github.com/lindsayjaacks/
  Indian-Nutrient-Databank-INDB-, `recipes.xlsx` and
  `recipes_servingsize.xlsx` read 2026-09-29), recipe ASC148 (source
  `asc_manual`, serving not marked guessed): 60 g rice + 20 g urad + 50 g
  onion + 50 g tomato for 2 servings x 2 uttapams, so 15 / 5 / 12.5 / 12.5 g
  each. Water, oil and salt at masala_dosa's ratios; 78.8 g. INDB's other
  uttapam (BFP152) is marked "serving unit - guessed" and was not used; web
  calorie sites (45-150 g, no method) were not used.

Cross-check of that INDB manual against the library: ASC146 masala dosa ~40 g
dry grain per dosa (library 35); ASC144 idli 10 g per idli (library 14.3).

Measured, South breakfast, 72 bodies per diet (scratch drivers on
`accepted_rung_valid_plate_count` and `plan_meal`):

```
BEFORE
vegan            tiffin shown {'idli': 32, 'soya_idli': 35, '(declined)': 5}
vegetarian       tiffin shown {'idli': 32, 'soya_idli': 36, '(declined)': 4}
eggetarian       tiffin shown {'soya_idli': 35, 'idli': 33, '(declined)': 4}
non_vegetarian   tiffin shown {'soya_idli': 38, 'idli': 32, '(declined)': 2}
AFTER
vegan            tiffin shown {'idli': 24, 'soya_idli': 35, 'plain_dosa': 4, 'onion_tomato_uttapam': 4, '(declined)': 5}
vegetarian       tiffin shown {'idli': 24, 'soya_idli': 36, 'plain_dosa': 4, 'onion_tomato_uttapam': 4, '(declined)': 4}
eggetarian       tiffin shown {'soya_idli': 32, 'idli': 29, 'onion_tomato_uttapam': 3, 'plain_dosa': 6, '(declined)': 2}
non_vegetarian   tiffin shown {'soya_idli': 38, 'idli': 28, 'plain_dosa': 4, '(declined)': 2}
```

Plate counts (0/1/2+): vegan 5/9/58 and vegetarian 4/8/60 unchanged;
eggetarian 4/0/68 -> 2/0/70; non-veg 2/4/66 unchanged. Eggetarian shown an
egg 68 -> 70.

**Finding, logged not fixed.** The shown plate is the single best one per
body, so dosa or uttapam is picked for only 4-9 of 72 bodies; idli and
soya_idli take the rest, and masala_dosa and egg_dosa are never shown. The
owner's "alternate the carbs" is a day-to-day rotation, which one best plate
per meal does not do. This is for step 4 to look at, not a recipe defect.
Suite with browser tests: 562 passed.

## 2026-09-29 — boiled egg and omelette for the South breakfast egg side (N7 step 2)

Owner's basis (2026-09-29, their experience as a South Indian): an ordinary
home breakfast is dosa or idli with "some boiled eggs or omelette" and a
chutney. Step 1 added the optional `egg_side` slot; the only dish that could
fill it was `muttai_podimas`.

Added, proportions fixed before measuring:

- `avicha_muttai` (boiled egg): `egg_boiled` 50 g (a large egg, USDA FDC
  173424) + 0.3 g salt; 1-2 eggs.
- `muttai_omelette`: `muttai_podimas`'s per-egg lines without the tempering
  (egg 50 g raw, onion 10, oil 2.5, chilli 0.5, salt 0.4); 1-2 eggs.

**Logged, not acted on — omelette oil.** The omelette reuses podimas's
`oil_uptake.vegetable_tempering` (0.95), not an exact mechanism match (oil
under a poured egg, not tossed with vegetables). Samia et al., Int J
Gastronomy Food Sci 2022;29:100552, DOI 10.1016/j.ijgfs.2022.100552, measures
oil uptake by fried and scrambled eggs. Its abstract could not be read
(paywalled; none in Crossref, OpenAlex, Semantic Scholar); a search-index
summary gives 64-73% for fried whole eggs and 78-88% for scrambled. Not
verified, so no constant is registered on it. If it holds, 0.95 overstates
the omelette and podimas oil lines by at most ~0.6 g and ~0.4 g fat per egg.

Measured (scratch driver on the tracked probes' own functions:
`accepted_rung_valid_plate_count` and `plan_meal`, 72 bodies per diet):

```
BEFORE snack
vegetarian       0/1/2+ = 2/19/51   shown animal 0/72  {}
eggetarian       0/1/2+ = 2/19/51   shown animal 0/72  {}
non_vegetarian   0/1/2+ = 2/19/51   shown animal 0/72  {}
AFTER breakfast
vegetarian       0/1/2+ = 4/8/60   shown animal 0/72  {}
eggetarian       0/1/2+ = 4/0/68   shown animal 68/72  {'avicha_muttai': 41, 'muttai_omelette': 20, 'muttai_podimas': 7}
non_vegetarian   0/1/2+ = 2/4/66   shown animal 70/72  {'avicha_muttai': 36, 'muttai_omelette': 20, 'muttai_podimas': 4, 'meen_kuzhambu': 8, 'chicken_kuzhambu': 6}
AFTER snack
vegetarian       0/1/2+ = 2/19/51   shown animal 0/72  {}
eggetarian       0/1/2+ = 2/19/51   shown animal 0/72  {}
non_vegetarian   0/1/2+ = 2/19/51   shown animal 0/72  {}
```

Breakfast before (step 1 entry): eggetarian 4/8/60, shown egg 60/72 (all
podimas); non-veg 2/10/60, shown animal 70/72. Eggetarian bodies with 2+
valid plates 60 -> 68, shown an egg 60 -> 68; podimas now 7 of them.
Vegetarian unchanged. South snack unchanged: the egg-only snack is still
blocked (fibre floor, open since N5). Suite with browser tests: 562 passed.

## 2026-09-29 — egg side at South breakfast (N7 step 1) — owner decision

**Owner decision (2026-09-29).** After N6, South breakfast still had no egg
plate for any eggetarian body. Offered egg paniyaram (recipe sites); the
owner declined it: "egg paniyaram is not a staple in many houses; most
people just have dosa or muttai dosa... a better idea would be dosa and
some boiled eggs or omelette and some sort of chutney, since that is what
happens in most households. We can alternate the carbs with idli, dosa,
uttapam." Stated as the owner's life experience as a South Indian and
recorded as that -- no published source was found or claimed for which
dishes households eat. Four steps approved in order: (1) an egg side slot,
(2) boiled egg and omelette, (3) plain dosa and uttapam, (4) measure.

**Why a slot.** SOUTH_BREAKFAST had no place for an egg beside the tiffin:
egg could only be inside it (egg_dosa) or in the gravy slot
(mutta_kuzhambu, replacing the sambar). New optional `egg_side`
(category `egg`, 0-1), after the chutney. Optional as curd_course is: a
vegetarian breakfast is unchanged.

**Measured** (South breakfast only; scratch script calling
`probe_rank_input2.py`'s `accepted_rung_valid_plate_count` and
`plan_meal` exactly as `probe_nonveg_shown.py` does; before = N6 after,
2026-09-29 fat band entry):

```
vegetarian       0/1/2+ = 4/8/60   shown animal 0/72  {}
eggetarian       0/1/2+ = 4/8/60   shown animal 60/72  {'muttai_podimas': 60}
non_vegetarian   0/1/2+ = 2/10/60   shown animal 70/72  {'muttai_podimas': 48, 'meen_kuzhambu': 12, 'chicken_kuzhambu': 10}
```

Eggetarian shown an egg plate **0 -> 60/72**; non-veg 58 -> **70/72**.
Plate counts identical to the N6 run for all three diets. The only egg-
category South dish today is muttai_podimas, which now reaches breakfast;
boiled egg and omelette are step 2.

**Tests.** `test_templates_and_portions.py`: slot count 5 -> 6; new test
pins `egg_side` exactly (`{"egg"}`, optional, 0-1). Deletion check:
category changed to `egg_x` -> `1 failed, 23 passed`
(`test_south_breakfast_egg_side_is_optional_and_egg_only`); restored.
`python -m pytest tests/ -q -p no:cacheprovider` → `492 passed, 70 skipped,
1 warning in 55.14s`.

## 2026-09-29 — fat band from the AMDR (N6) — owner decision, evidence first

**Owner request (2026-09-29):** "it's okay to go above the fat threshold
sometimes... try to have a plus or minus threshold", the same for every
diet (the owner rejected a non-vegetarian-only widening: a different rule
per diet makes the same problem either way). A first edit set fat to ±25%
straight from the request; the owner stopped it and asked for "factual
studies and proof before changing the tolerance". Then, standing: "from now
onwards try to have some factual proof before proceeding".

**What the sources say** (read online 2026-09-29; summary pages, not the
2005 report itself, so nothing here is `verified=True` -- invariant 4):

- Fat AMDR for adults, 20-35% of energy: National Academies, *Rethinking
  the AMDR for the 21st Century* (2024 letter report,
  nationalacademies.org/read/27957/chapter/5); Health Canada DRI tables
  (canada.ca, reference values for macronutrients). Already registered here
  as `macro.fat_energy_fraction_min/max` (iom_dri_2005).
- ICMR-NIN (nin.res.in/rdabook/brief_note.pdf): visible fat 20-50 g per
  person per day by energy need. A search snippet gave 15-35% of energy;
  not confirmed in any readable ICMR text, so not used.
- **No source found states a per-meal fat band.** The AMDR describes a
  whole diet. The statement that meals may vary as long as the day is in
  range came only from secondary study-guide sites. A per-meal tolerance is
  therefore this project's decision (invariant 3: a daily range applied per
  meal is not the mechanism the source measured).

**Derivation.** The fat target is the AMDR midpoint, 27.5% of energy
(`_compute_macros`). The AMDR's edges relative to it: (0.35 - 0.20) /
(0.35 + 0.20) = 0.15 / 0.55 = **0.2727**. New `tolerance.fat_default` is
computed from the two AMDR constants, not typed, evidence
`project_decision`: at a meal's energy point its fat band runs from exactly
20% to 35% of that energy. Owner chose this over a round ±25%. Carb stays
±15% (`tolerance.fat_carb_default`, now carb only): the owner asked about
fat, and diabetes locks carb. Since 0.2727 > the fat_carb rung's 0.25, the
rung would have narrowed fat; guarded first (entry below, 32efbf9).

**Measured, before = 32efbf9 (the guard, no fat change).**

`probe_rank_input2.py` (vegetarian + vegan, 1152 cases):

| | before | after |
|---|---|---|
| >= 2 valid plates at accepted rung | 734 (63.7%) | **779 (67.6%)** |
| rung-0-only >= 2 plates | 640 (55.6%) | **708 (61.5%)** |
| stopped at rung 0 | 764 | **824** |
| stopped at fat_carb_tolerance | 85 | 33 |
| declined | 171 | 168 |

Per template (accepted rung, of 144): S breakfast 114 -> 118, S lunch 78 ->
82, N breakfast 85 -> 99, N snack 58 -> 61, N lunch 118 -> 126, N dinner
122 -> 134; S dinner, S snack unchanged.

`probe_nonveg.py`, 2+ valid plates of 576: vegetarian 436 -> **455**,
eggetarian 438 -> **461**, non-vegetarian 487 -> **498**.

`probe_nonveg_shown.py`, bodies of 72 shown an egg/fish/poultry plate
(eggetarian / non-veg): N breakfast 32 -> 40 / 32 -> 40, N snack 24 -> 36 /
24 -> 36, N dinner 47 -> 51 / 52 -> 60. South eggetarian unchanged (0, 14,
42, 0).

**Two drops, both traced per body** (script run on a worktree of 32efbf9
and on this tree, non-vegetarian):

- S lunch shown-with-animal, non-veg 50 -> **46**: the four 95 kg
  gain_muscle bodies. Before, nothing fit at rung 0 and the ladder relaxed
  sodium/fibre, where an animal plate was valid. Now a vegetarian plate fits
  at rung 0 -- full sodium ceiling and fibre floor -- and no animal plate
  does, so the ladder stops there. N3's preference chooses only among plates
  valid at the accepted rung, by design.
- S breakfast non-veg 2+ plates 64 -> 60: the four 110 kg lose_fat bodies
  went from three or four relaxed rungs (sodium/fibre, fat/carb, energy,
  and protein for diabetes) to **none**, with fewer plates at the stricter
  rung. Their shown plate still has an animal dish.

Both are the ladder stopping at a stricter rung, which it is built to
prefer. Stated because the headline numbers are not uniformly up.

`probe_south_egg_blockers.py`: South breakfast egg still 0/68 for both
dishes; fat above ceiling fell 56 -> 32 (egg_dosa) and 60 -> 32
(mutta_kuzhambu), now level with carb below floor (32 each). Fat is no
longer the single breakfast blocker.

**Reference plate moved.** 70 kg maintain vegetarian South breakfast:
`idli x3, soya_kuzhambu, coconut_chutney x4, soya_curd x2` (was `soya_idli
x6, sambar, coconut_chutney x4, soya_curd`). `test_planner_quality.py`'s
two pinned tests re-derived by hand (13.0 g = 25.0 g soya_chunks_dry x
52.0/100), the perturbation test now disqualifies soya_chunks_dry, which
moves the plate back to soya_idli (12.3504 g).

**Tests.** Hand-computed fat bounds in `test_nutrition_meal_target.py`
re-derived at 3/11 (60 x 8/11, 60 x 14/11); the diabetes locking test now
builds its own 15% fat band so it still sees fat widen. Deletion check:
`band(fat_g, fat_tolerance)` reverted to `fat_carb_tolerance` ->
`8 failed, 483 passed, 70 skipped`; restored.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p
no:cacheprovider` → `561 passed, 1 warning in 186.22s (0:03:06)`.

## 2026-09-29 — a relaxation rung never narrows a band (N6, guard) — found while planning the fat band

**Found.** `_widen_band` re-derived each bound from the point at the rung's
tolerance and assigned it outright. Correct while every default band was
narrower than its rung's relaxed band. N6 (entry above) makes fat's default
band the AMDR-derived ±27.3%, wider than `tolerance.fat_carb_relaxed`
(±25%): the fat_carb rung, meant to loosen fat, would have tightened it
from ±27.3% to ±25%. Seen by reading the code while planning N6, before the
fat change was written; never reached a plan.

**Change.** A rung takes the looser of the existing bound and its own:
floor `min(existing, lo)`, ceiling `max(existing, capped hi)`. No output
change today -- every default band is currently at or inside its rung's
band -- which is why the test builds its own target (carb at ±40% through
`fat_carb_tolerance`) instead of reading the real library.

**Deletion-tested.** `tests/test_planner_validator.py::TestARungNeverNarrowsABand`,
harness rows V28 (floor) and V29 (ceiling):

```
V2   covered      tests/test_planner_decline.py::TestRelaxabilityIsDerivedFromTheLadderItself::test_a_ceiling_sitting_on_its_hard_ceiling_says_hard_capped
V3   covered      tests/test_planner_validator.py::TestClinicalLocking::test_diabetes_locks_carb_out_of_the_fat_carb_rung
V5   covered      tests/test_planner_decline.py::TestRelaxabilityIsDerivedFromTheLadderItself::test_a_locked_bound_says_locked
V28  covered      tests/test_planner_validator.py::TestARungNeverNarrowsABand::test_a_default_band_wider_than_the_rung_survives_it
V29  covered      tests/test_planner_validator.py::TestARungNeverNarrowsABand::test_a_default_band_wider_than_the_rung_survives_it
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

V2, V3 and V5 rerun because their target lines sit next to the edit and
still match. `python -m pytest tests/ -q -p no:cacheprovider` → `491
passed, 70 skipped, 1 warning in 55.56s`.

## 2026-09-29 — muttai carrot poriyal (N5): an egg dish in the South Indian vegetable course — owner decision

**Owner decision (2026-09-29):** option 1 of two after the South Indian egg
blockers measurement (next entry): a new egg dish for SOUTH_LUNCH/DINNER's
vegetable course (poriyal/kootu), so egg can sit beside the sambar instead
of replacing it. Option 2, letting muttai_podimas (0.3 g fibre) into that
slot by template change, not taken: fibre was lunch's first blocker.

**Proportions, fixed before any probe run:** carrot_poriyal's lines
unchanged, plus one large egg (50 g raw, muttai_podimas's per-egg quantity);
coconut out, the egg takes its place; salt at carrot_poriyal's 0.63% of the
new weight. Oil `oil_uptake.vegetable_tempering`, both parent dishes' line
(tempering that stays with the vegetables and egg; no new constant).
Raw-egg basis. Per katori (122.3 g): 120 kcal, protein 7.4, fat 7.4, carb
6.6, fibre 1.9, sodium 418 mg; counts 1-2.

**Measured.** `probe_nonveg_shown.py`, bodies of 72 whose shown plate has an
egg, fish or poultry dish / whose valid plates include one. Before = N4's
tree (d594a59), from the entry of that date.

| template | eggetarian before | after | non_vegetarian before | after |
|---|---|---|---|---|
| south_indian/breakfast | 0 / 0 | 0 / 0 | 58 / 58 | 58 / 58 |
| south_indian/lunch | 1 / 1 | **14 / 14** | 50 / 50 | 50 / 50 |
| south_indian/dinner | 1 / 1 | **42 / 42** | 59 / 59 | **67 / 67** |
| south_indian/snack | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

North rows identical (32, 24, 51, 47 eggetarian; 32, 24, 68, 52 non-veg).
`probe_nonveg.py`: 2+ plates vegetarian 436/576, eggetarian 438/576,
non-vegetarian 487/576, all unchanged -- the dish adds egg plates where
plates already existed, it does not add plates to bodies that had fewer
than two.

70 kg maintain, eggetarian: South lunch `steamed_rice, soya_kuzhambu,
muttai_carrot_poriyal, soya_chunk_poriyal, soya_curd`; dinner
`steamed_rice, soya_kuzhambu, carrot_kootu, muttai_carrot_poriyal,
soya_curd`. Non-vegetarian, same body, shows the same two plates: at dinner
the nearest valid animal plate is now this one, not N4's meen_varuval
plate. Correct per N3's rule (nearest valid animal plate), stated because it
changes what the owner saw after N4.

**Tests.** A recipe is not a gate. `test_planner_candidates.py`'s non-veg
parity test lists each category's animal dishes by hand; it went red on the
new dish (`1 failed, 488 passed`) and now lists it.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p
no:cacheprovider` → `559 passed, 1 warning in 180.45s (0:03:00)`.

**Open.** Breakfast and snack unchanged at 0 (next entry for why).

## 2026-09-29 — South Indian egg blockers (N5, measurement) — owner request

**Owner request (2026-09-29):** egg dishes for South Indian lunch, dinner and
snack, "also breakfast?". N4's measurement had the eggetarian column at
breakfast 0/72, lunch 1/72, dinner 1/72, snack 0/72 bodies with a valid egg
plate, although an egg dish exists for each: egg_dosa (tiffin), mutta_kuzhambu
(the breakfast/lunch/dinner gravy slot), muttai_podimas (snack). Before adding
dishes: what blocks the ones already there?

`docs/design/probes/probe_south_egg_blockers.py` (new, read-only). Per body
(eggetarian, the 72-body grid), per South template: the target the ladder
stops on for the full pool; the egg dish's combinations only; is any valid
there, and if not, which bounds the nearest one breaks (the validator's own
`_nearest_plate_violations`). The first draft counted "nearest plate breaks
nothing", which `_nearest_plate_violations` can never report -- it skips a
plate that breaks nothing -- so it read 0 at lunch where N3 had measured 1.
Corrected to solve the egg combinations first, before the run below.

```
== south_indian/breakfast
  egg_dosa: bodies 68, a valid egg plate in 0; nearest egg plate's misses in the rest:
      fat_g above_ceiling              56
      carb_g below_floor               32
      fibre_g below_floor              20
      sodium_mg above_ceiling          12
      protein_g below_floor            11
      quality_protein_g below_floor    8
      energy_kcal above_ceiling        8
      energy_kcal below_floor          4
  mutta_kuzhambu: bodies 68, a valid egg plate in 0; nearest egg plate's misses in the rest:
      fat_g above_ceiling              60
      fibre_g below_floor              36
      carb_g below_floor               32
      protein_g below_floor            16
      sodium_mg above_ceiling          16
      energy_kcal below_floor          8
      energy_kcal above_ceiling        4
== south_indian/lunch
  mutta_kuzhambu: bodies 66, a valid egg plate in 1; nearest egg plate's misses in the rest:
      fibre_g below_floor              36
      fat_g above_ceiling              27
      protein_g below_floor            23
      energy_kcal above_ceiling        8
      sodium_mg above_ceiling          6
== south_indian/dinner
  mutta_kuzhambu: bodies 62, a valid egg plate in 1; nearest egg plate's misses in the rest:
      fat_g above_ceiling              49
      fibre_g below_floor              40
      energy_kcal above_ceiling        17
      sodium_mg above_ceiling          9
      protein_g below_floor            4
      carb_g below_floor               4
== south_indian/snack
  muttai_podimas: bodies 70, a valid egg plate in 0; nearest egg plate's misses in the rest:
      fibre_g below_floor              70
      protein_g below_floor            64
      fat_g above_ceiling              62
      energy_kcal below_floor          44
      quality_protein_g below_floor    23
      energy_kcal above_ceiling        3
```

**Reading.** At lunch and dinner the only egg dish takes the gravy slot, so
it replaces the sambar: the plate loses the lentil's fibre and gains
mutta_kuzhambu's fat (16.3 g per katori against meen_kuzhambu's 10.4 g).
Chicken and fish reached these meals through the vegetable course (N4); egg
had nothing there. Breakfast: fat first, for both dishes. Snack: fibre below
floor in 70 of 70 -- an egg-only snack cannot meet it, so more egg-only
dishes would not help there.

**Disposition.** Owner chose an egg dish for the lunch/dinner vegetable
course (N5, next entry). Breakfast and snack open. Owner also asked for fat
to be allowed above its bound "sometimes", queued as N6, not acted on here.

## 2026-09-29 — chicken and fish mains (N4): chicken curry, chicken kuzhambu, chicken chukka, meen varuval — owner decision

**Owner decision (2026-09-29):** all four dishes proposed after N3's
measurement: chicken curry (North lunch and dinner, `sabzi`), chicken
kuzhambu (South, `kuzhambu`), chicken chukka and meen varuval (South
vegetable course, `poriyal`). N3 found no chicken main anywhere, no fish in
the North, and nothing animal for SOUTH_LUNCH/DINNER's vegetable course --
the owner's own South dinner case (70 kg maintain, non-veg), where
soya_chunk_poriyal was shown because no valid plate had an animal dish.

**Proportions, fixed before any probe run**, each from an existing recipe's
lines (stated in each file): chicken_curry = anda_curry's gravy, egg → 90 g
raw chicken; chicken_kuzhambu = meen_kuzhambu's lines, fish → 90 g raw
chicken, tamarind back to mutta_kuzhambu's 3 g; chicken_chukka =
soya_chunk_poriyal's poriyal lines, soya → 60 g raw chicken, coconut out,
paste/masala/salt at chicken_tikka's ratios; meen_varuval = 80 g raw pomfret
with a sambar-powder and ginger-garlic paste. All raw-weight basis:
understates, never overstates. Per unit:

| dish | g | kcal | protein | fat | sodium mg |
|---|---|---|---|---|---|
| chicken_curry | 150.0 | 212 | 20.2 | 13.3 | 350 |
| chicken_kuzhambu | 150.0 | 229 | 20.7 | 13.9 | 354 |
| chicken_chukka | 74.5 | 132 | 13.4 | 8.2 | 298 |
| meen_varuval | 90.6 | 147 | 15.8 | 8.5 | 277 |

**Oil, per invariant 3.** Curry and kuzhambu: the tempering goes into a
served gravy -- `oil_uptake.vegetable_tempering`, anda_curry's and
meen_kuzhambu's line. Chukka: chicken pieces and onion tossed on a hot pan
until the masala clings -- `oil_uptake.chicken_tikka_pan_roasted`'s
mechanism (lean chicken pieces, surface application); the tikka's curd
marinade is not part of what that constant describes. Meen varuval: new
`oil_uptake.fish_tawa_fried` = 0.80, a thin film on a tawa under a
paste-coated piece; not shallow or deep frying, which
`project_oil_uptake_estimate` explicitly excludes. Recorded "reviewed: NO
matching primary source".

**Measured.** `probe_nonveg_shown.py`, bodies of 72 whose shown plate has
an egg, fish or poultry dish (shown = valid in every cell, since N3). Before
= HEAD ef5a918. Each South dish also run alone in a scratch copy, so each
row is attributable; chicken_curry is in every copy and only reaches North
templates.

| template (non_vegetarian) | before | + all four | kuzhambu alone | chukka alone | varuval alone |
|---|---|---|---|---|---|
| south_indian/breakfast | 47 | **58** | 58 | 47 | 47 |
| south_indian/lunch | 38 | **50** | 38 | 50 | 50 |
| south_indian/dinner | 34 | **59** | 38 | 54 | 59 |
| north_indian/lunch | 51 | **68** | 68 | 68 | 68 |
| north_indian/dinner | 47 | **52** | 52 | 52 | 52 |

Every other row, and the whole eggetarian column, identical. Chicken
kuzhambu's gain is mostly at breakfast: SOUTH_BREAKFAST's gravy slot takes
`kuzhambu` (as it does meen and mutta kuzhambu).

`probe_nonveg.py` with all four: vegetarian 436/576 and eggetarian 438/576,
unchanged, so nothing leaks. Non-vegetarian 2+ plates 451 → **487**/576;
no template's zero-plate count rose.

Owner's case, 70 kg maintain non-veg South dinner, shown plate:
`steamed_rice, soya_kuzhambu, carrot_kootu, meen_varuval, soya_curd`
(was `… soya_chunk_poriyal …`).

**Tests.** `test_planner_candidates.py`'s non-veg parity test lists each
category's animal dishes by hand; it went red on chukka and varuval as it
should, and now lists them, one dish per commit. A recipe is not a gate;
the new oil constant is held by the registry's review check. Deleted its
REVIEWED entry and ran the suite: `1 failed, 488 passed`, failing
`test_citations.py::TestMechanismReview::test_no_constant_escapes_mechanism_review`.
Restored.

**Verification.** All four in the tree: `FOODAI_WEB_TESTS=required python -m
pytest tests/ -q -p no:cacheprovider` → `559 passed, 1 warning in 179.49s
(0:02:59)`. Browser, 70 kg non_vegetarian account: South dinner shows
`['Steamed rice', 'Soya kuzhambu', 'Carrot kootu', 'Meen varuval (fish fry)',
'Soya curd']`; North dinner `['Phulka', 'Dal tadka', 'Anda curry']` (the
nearest animal plate for this body is still the egg one).

## 2026-09-27 — shown plate for egg and non-veg (N3): the diet setting now shows on the plate — owner report

**Owner report (2026-09-27):** "I still am unable to see non vegetarian
dishes; it still gives me veg dishes such as soya chunk poriyal for South
dinner." Asked to check every meal.

**Diagnosis.** The diet setting did reach the planner (`api/main.py` passes
`body.diet` to `plan_meal`; the candidate pool included the animal dishes).
The dashboard shows one plate, the one `plan_within_ladder` returns, and it
returned `solved[0]`, the plate nearest to target. Soya plates were nearest
nearly everywhere. So a non-vegetarian was *permitted* egg, fish and chicken
and almost never *shown* any. Two separate causes, measured:

1. **Selection** — valid animal plates existed and lost on nearness.
2. **Library** — for some templates no valid animal plate exists at all. The
   owner's own South dinner case (70 kg, maintain) is this one: 14 valid
   plates, none with egg, fish or chicken.

**Measured** (`docs/design/probes/probe_nonveg_shown.py`, new): bodies of 72
whose *shown* plate has an egg, fish or poultry dish / whose *valid* plates
include one, calling `plan_meal` exactly as the API does.

| template | eggetarian before | after | non_vegetarian before | after |
|---|---|---|---|---|
| south_indian/breakfast | 0 / 0 | 0 / 0 | 14 / 47 | **47** / 47 |
| south_indian/lunch | 0 / 1 | **1** / 1 | 28 / 38 | **38** / 38 |
| south_indian/dinner | 1 / 1 | 1 / 1 | 26 / 34 | **34** / 34 |
| north_indian/breakfast | 28 / 32 | **32** / 32 | 28 / 32 | **32** / 32 |
| south_indian/snack | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| north_indian/snack | 8 / 24 | **24** / 24 | 8 / 24 | **24** / 24 |
| north_indian/lunch | 13 / 51 | **51** / 51 | 13 / 51 | **51** / 51 |
| north_indian/dinner | 0 / 47 | **47** / 47 | 0 / 47 | **47** / 47 |

The "before" run imported the planner before the change was written; the
"after" run is the same script on the changed tree.

**Change.** `plan_within_ladder` takes an optional `prefer`: among the
plates valid at the rung the ladder stopped on, return the nearest one it
accepts, else the nearest plate. `plan_meal` supplies one for any diet
permitting egg, fish or poultry. It never widens a target, never moves the
ladder to a later rung, never touches a unit count (invariant 1 unaffected:
no quantity is chosen by anything new). Vegetarian, vegan and jain get no
preference and the same plate as before.

**What this does not fix.** The second column. Where no valid animal plate
exists (eggetarian South meals, South snack, 25 of 72 non-veg bodies at
South breakfast, 34 at lunch, 38 at dinner) the plate is still vegetarian.
That is a recipe gap: the library's animal dishes are anda_chaat,
anda_curry, chicken_tikka, egg_bhurji, egg_dosa, meen_kuzhambu,
mutta_kuzhambu, muttai_podimas -- no chicken main anywhere, no fish in the
North, nothing animal for the South vegetable course.

**Tests.** `tests/test_shown_plate_preference.py`, 11 tests: preferred plate
over a nearer one, fallback to nearest, preference never moves the rung,
preference applies on a relaxed rung, which diets prefer, and a wiring test
on the owner's North dinner case. Mutation rows N3a–N3d added to
`docs/design/probes/d4b_mutations.py`:

```
N3a  covered      tests/test_shown_plate_preference.py::TestPreferChoosesAmongValidPlates::test_the_nearest_preferred_plate_is_shown_over_a_nearer_one
N3b  covered      tests/test_shown_plate_preference.py::TestPreferChoosesAmongValidPlates::test_the_nearest_preferred_plate_is_shown_over_a_nearer_one
N3c  covered      tests/test_shown_plate_preference.py::TestPreferChoosesAmongValidPlates::test_the_preference_also_applies_on_a_relaxed_rung
N3d  covered      tests/test_shown_plate_preference.py::TestTheRealDinner::test_a_non_vegetarian_north_dinner_shows_an_animal_protein_dish
4 mechanisms: 4 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

N3d (the `plan_meal` hookup) is caught only by the real-library wiring
test; no synthetic test reaches `plan_meal`'s preference. Stated, not
hidden.

Full suite: `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider` → `559 passed, 1 warning in 286.69s (0:04:46)`.
Browser, by hand, fresh account, 70 kg non_vegetarian: North dinner shows
`['Phulka', 'Dal tadka', 'Anda curry']`; South dinner still shows
`['Steamed rice', 'Sambar', 'Carrot poriyal', 'Soya chunk poriyal',
'Neer mor']` -- cause 2, as measured.

## 2026-09-27 — egg breakfasts and snack (N2d): egg bhurji places; egg dosa and muttai podimas written, measured, and place nowhere

**What was written.** Three egg dishes, proportions fixed before any probe
run, each on the new raw-egg row (N2b) and each for a slot opened in N2c or
already open:

- *Egg bhurji* (North breakfast protein course, category `egg`): one large
  raw egg with half of tofu_bhurji's onion, tomato, oil, paste, masala and
  chilli; 80.4 g per egg, counts 1–4. 100.3 kcal, 7.0 g protein, 7.2 g fat.
- *Egg dosa* (South breakfast, a `tiffin`): masala_dosa's dosa lines
  unchanged plus one raw egg, 5 g onion, 0.5 g chilli, 0.3 g salt; 145.8 g,
  counts 1–3. 223.9 kcal, 10.9 g protein, 8.3 g fat, 377.8 mg sodium.
- *Muttai podimas* (South snack, category `egg`): one raw egg with
  carrot_poriyal's tempering lines and 10 g onion; 64.4 g per egg, counts
  1–3. 96.8 kcal, 6.9 g protein, 7.3 g fat, 0.3 g fibre.

**Measured.** Both probes, on a copy of the tree without the three files
and on the tree with them, run side by side. Plate counts
(`probe_nonveg.py`) identical in every cell, every diet, before and after:
2+ totals 436 / 438 / 451 of 576. Variety (`probe_nonveg_variety.py`),
bodies of 72 with a valid plate containing an egg, fish or poultry dish:

| template | eggetarian before → after | non_vegetarian before → after |
|---|---|---|
| north_indian/breakfast | 0 → **32** | 0 → **32** |
| south_indian/breakfast | 0 → **0** | 47 → 47 |
| south_indian/snack | 0 → **0** | 0 → 0 |

Every other row identical. Vegetarian column identical, so nothing leaks.

**Why egg dosa and podimas place nowhere, diagnosed** (every count
assignment of every combination containing the dish, three eggetarian
bodies, against the target the ladder stopped on):

- *Egg dosa.* The rest of a South breakfast (chutney, kuzhambu) already
  carries fat. Closest plates: 55 kg lose_fat, fat 42 g vs 16 g ceiling;
  70 kg maintain, fat 26 g vs 23 g and carbs 61 g under a 75 g floor at one
  dosa; 95 kg gain_muscle, sodium 1497 mg vs 1400 mg, the only miss.
- *Muttai podimas.* A South snack is one dish plus an optional buttermilk,
  and egg brings no fibre, so the snack's fibre floor (3–5 g) fails at
  every count for all three bodies. Fat is also over: 7.3 g per egg against
  snack ceilings of 7–11 g, so two eggs miss at every body tested.

**Not tuned.** Shrinking the egg, cutting the oil or adding a vegetable to
make a number pass is fitting the recipe to the target.

**Owner decision (2026-09-27): keep both in the library, unplaced.** They
load, are correct as authored, and appear in no plan today; they are ready
if the South breakfast fat ceiling or the South snack's shape is revisited.
Committed separately after egg bhurji, as their own reviewable ideas.

**Verification.** Egg bhurji only in the tree:
`FOODAI_WEB_TESTS=required python -m pytest tests/ -q -p no:cacheprovider`
→ `548 passed, 1 warning in 175.22s (0:02:55)`. A recipe adds no gate, so
there is no deletion test; the probe table is its evidence.
All three in the tree, same command: `548 passed, 1 warning in 169.58s
(0:02:49)`.

## 2026-09-27 — egg category (N2c): North breakfast protein course and South snack accept an egg dish — owner decision

**Owner decision (2026-09-27):** egg dishes for breakfasts and snacks. Two
slots could not hold one: `NORTH_BREAKFAST.protein_course` accepted only
`dal_chilla`, and `SOUTH_SNACK.sundal` only `sundal`. Both now also accept a
new category, `egg`: bhurji or an omelette as the North breakfast's protein
course, and a boiled egg with pepper or muttai podimas in the South snack's
place. `SOUTH_SNACK`'s slot keeps the name `sundal` because `blocking_slots`
carries slot names on the wire.

Egg dosa needs no template change: it is a `tiffin`, which
`SOUTH_BREAKFAST.tiffin_item` already accepts.

**No plan changes by construction.** No recipe has `category: egg` yet
(checked with grep), so no candidate pool can differ. Vegetarian and vegan
plates cannot gain an egg dish later either, because diet is decided by
ingredient classes, not by category.

**Tests.** `tests/test_templates_and_portions.py` pins both sets exactly.
Deletion check, `"egg"` removed from each set in turn, full suite:
`1 failed, 477 passed, 70 skipped` both times, failing
`test_north_breakfast_bread_is_optional_unlike_every_other_template` and
`test_south_snack_is_one_dish_and_an_optional_drink` respectively. Restored:
green.

## 2026-09-27 — raw whole egg row (N2b): IFCT M001, DIAAS matched to fried and scrambled egg

**Why.** Egg dosa and egg bhurji cook raw egg on a pan. The only egg row was
`egg_boiled` (M004), a boiled egg. Using it for those dishes would be a real
figure describing the wrong food, the invariant 3 failure. Before any egg
breakfast is written, the right row has to exist.

**Added** `egg_whole_raw`, IFCT 2017 **M001**, from the same
`nodef/ifct2017` file and by the same curl-and-grep method as M004. 564 kJ =
134.8 kcal (Atwater 135.5). Protein 13.28 g, fat 9.15 g, sodium 123.0 mg,
iron 1.82 mg, calcium 49.44 mg per 100 g. Rejected: M007 "omlet", whose fat
(11.6 g) very likely already includes frying fat that recipes add as their
own oil line.

**DIAAS: sourced, and the preparation checked, not assumed.** Fanelli et al.
2024, Table 8, >3-years pattern, read from the open-access full text
(PMC11658930): fried 135%, boiled 135%, scrambled 137%. Recorded 1.35, the
lower of the two pan-cooked forms. PubMed returned a bot check and was not
used. B12 0.89 µg, USDA FDC 171287. `verified=false`.

**Tests.** Four listing tests updated deliberately (row count 36 → 37;
real-code set gains M001; unverified-row warnings 35 → 36; qualifying set
gains `egg_whole_raw`). Deletion check, row removed: `3 failed, 57 passed`
(`test_every_fixture_row_loads`,
`test_unverified_rows_are_reported_not_silently_accepted`,
`test_the_threshold_partitions_the_library_where_expected`). The code-set test
does not react to a missing row by design, because it guards against
invented codes. Restored: `python -m pytest tests/ -q -p no:cacheprovider`,
`478 passed, 70 skipped, 1 warning`. No recipe uses the row yet, so no plan
changes.

**Noticed, not fixed — nothing stops a raw-egg row in a no-cook dish.** This
row's DIAAS describes cooked egg. A recipe declaring `preparation: uncooked`
with an `egg_whole_raw` line would load and be credited 1.35 for raw egg,
whose protein is less digestible and was not measured. The limit is stated
in the row's `source_note`; no loader rule enforces it. Left open.

## 2026-09-27 — North Indian snack: chicken tikka and anda chaat (N2, first pair)

**Owner decision (2026-09-27):** N2 is "variety first" — egg and chicken dishes
for breakfasts and snacks, where the N1 baseline found no animal dish at all.
Order: the two North snack dishes first, because they fit the template and
the ingredient table as they stand. Egg breakfasts need a raw-egg row, and the
North breakfast protein course and South snack need their templates widened;
those come after, each its own step.

**A second probe, because a plate count cannot see variety.**
`probe_nonveg.py` counts plates; north_indian/snack already had 2+ plates for
58/72 bodies under every diet, so an added dish is invisible there.
`docs/design/probes/probe_nonveg_variety.py` (new) asks: for how many of the
72 bodies is at least one valid plate, at the accepted rung, built with an
egg, fish or poultry ingredient? Same solved set as the base probe.

**Chicken tikka** (`data/recipes/chicken_tikka.yaml`): four bite-sized pieces
from 80 g raw chicken breast, soya_tikka's method and lines, marinade scaled
at ordinary home ratios; 110.8 g per plate, counts 1–2. Proportions fixed
before any probe run.

- *New constant, not a reuse.* `oil_uptake.tikka_pan_roasted` is applied to
  porous rehydrated soya chunks; chicken pieces are not porous, so reusing it
  would be a real citation describing the wrong food (invariant 3).
  `oil_uptake.chicken_tikka_pan_roasted` = 0.80, `project_oil_uptake_estimate`,
  high side by the same convention, recorded as "NO matching primary source".
- *Raw-weight basis, stated in the file.* No cooked chicken row or sourced
  yield exists, so the plate's 110.8 g is what goes into the pan. Since G1 the
  dashboard shows that figure. Nutrition per gram of finished dish is
  understated, never overstated.
- *Measured.* Plate counts unchanged (north_indian/snack non-veg 4 / 10 / 58).
  Variety, non-vegetarian north snack: **0 → 4/72** bodies.
- *Why so few, diagnosed* (70 kg maintain, snack band 231–283 kcal, fat
  ceiling 9.0 g unrelaxed): one plate is 168.9 kcal / **9.9 g fat**, two are
  337.9 kcal / 19.9 g. Below the energy band at one plate, far above it at
  two, and over the fat ceiling either way. 7.2 of the 9.9 g comes from
  `chicken_breast_raw`'s IFCT N003 figure of 9.0 g fat / 100 g, high for
  skinless breast. **Not tuned, not replaced.** Recorded as a question for
  the human review of that row (`verified=False`): whether N003's fat figure
  is what the primary IFCT table says.

**Anda chaat** (`data/recipes/anda_chaat.yaml`): one large boiled egg (50 g)
per unit with soya_chana_chaat's toppings scaled; 68.4 g, counts 1–3,
`preparation: uncooked` (the egg row is IFCT's boiled, served-basis
composition — the one egg dish that needs no raw-egg data). 83.0 kcal,
7.0 g protein per egg. Proportions fixed before any probe run.

- *Measured.* Plate counts unchanged for 2+ (58/72, every diet); 24 bodies
  per egg-permitting diet gain extra valid plates. Vegetarian column
  identical, so nothing leaks to vegetarian plans. Variety, north snack:
  eggetarian **0 → 24/72**, non-vegetarian **4 → 24/72**.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider`: `548 passed, 1 warning in 176.38s`, both dishes
present. Variety probe, three runs on one tree (both files moved aside, then
tikka restored, then chaat):

| north_indian/snack | eggetarian | non_vegetarian |
|---|---|---|
| neither dish | 0 | 0 |
| + chicken tikka | 0 | 4 |
| + anda chaat | 24 | 24 |

Every other template's row is identical across the three runs.

**Disposition:** North snack now offers egg eaters an egg plate for a third
of bodies. Chicken tikka is correct as authored and mostly unplannable at a
snack's size; the chicken fat figure is the open question, not the recipe.

## 2026-09-27 — non-vegetarian baseline (N1): egg and non-veg profiles already match vegetarian; the animal dishes add little

**Why.** Owner asked for chicken, egg and fish dishes so that macros are
"filled much more easily". `probe_rank_input2.py` has only ever measured
vegetarian and vegan profiles, so that premise was unmeasured. Measured first,
no recipe changed.

**Method.** `docs/design/probes/probe_nonveg.py` (new) runs the base probe's
own `accepted_rung_valid_plate_count`, loaded unmodified, over its 72-body grid
(6 weights x 3 goals x 4 flag-sets) once per diet. Library today: three
animal-protein dishes, all gravies — `anda_curry` (north, egg),
`mutta_kuzhambu` (south, egg), `meen_kuzhambu` (south, fish). No chicken dish.

**Result** (`PYTHONPATH=. python docs/design/probes/probe_nonveg.py`),
profiles with 0 / 1 / 2+ valid plates, 72 per cell:

| template | vegetarian | eggetarian | non_vegetarian |
|---|---|---|---|
| south_indian/breakfast | 4 / 12 / 56 | 4 / 12 / 56 | 4 / 8 / 60 |
| south_indian/lunch | 6 / 28 / 38 | 6 / 27 / 39 | 2 / 13 / 57 |
| south_indian/dinner | 11 / 7 / 54 | 10 / 7 / 55 | 2 / 24 / 46 |
| north_indian/breakfast | 1 / 18 / 53 | 1 / 18 / 53 | 1 / 18 / 53 |
| south_indian/snack | 2 / 19 / 51 | 2 / 19 / 51 | 2 / 19 / 51 |
| north_indian/snack | 4 / 10 / 58 | 4 / 10 / 58 | 4 / 10 / 58 |
| north_indian/lunch | 3 / 6 / 63 | 3 / 6 / 63 | 3 / 6 / 63 |
| north_indian/dinner | 1 / 8 / 63 | 1 / 8 / 63 | 1 / 8 / 63 |
| **2+ total** | **436/576** | **438/576** | **451/576** |

Bodies crossing to 2+ versus vegetarian: eggetarian 2 (one each south lunch
and dinner); non_vegetarian 29 (south lunch 22, south breakfast 7). North
lunch and dinner gain extra plates for ~50 bodies under both diets, but every
one of those bodies already had 2+.

**The premise, stated plainly: mostly wrong as a coverage claim.** Egg and
non-veg profiles already get two plates as often as vegetarians (75.7% /
76.0% / 78.3%). Egg dishes change almost nothing (+2); fish helps South
Indian lunch (38 → 57). Breakfasts and snacks cannot change at all: no
animal dish exists for them. What the gap is, is variety — an eggetarian is
never offered an egg breakfast — not whether a plate can be built.

**Counter-intuitive, checked, not a defect.** South Indian dinner is *lower*
for non-veg (46 vs 54). Confirmed for 8 bodies, e.g. 70 kg lose_fat:
vegetarian 6 plates at `protein_tolerance`, non_vegetarian 1 plate at
`fat_carb_tolerance`. The fish plate lets the ladder stop at an earlier,
stricter rung where fewer plates fit — a closer plate, fewer alternatives. The
probe's docstring first claimed the non-veg count could only equal or exceed
vegetarian; corrected before commit.

**Disposition:** baseline recorded; N2's scope is the owner's call (variety
dishes for breakfast/snack vs. lunch/dinner protein). No code change.

## 2026-09-27 — portions shown in grams beside the household unit (G1) — owner decision

**Owner decision (2026-09-27):** show every portion in grams as well as its
katori/roti/dosa count, for easy measuring. Grams only: no ml for liquids,
because converting needs a per-dish density and none is sourced here.

**What changed.** `ComponentOut` gains `grams` = `unit_count` x the recipe's
own `grams_per_unit`, via `ServingUnit.grams_for`. Required, not defaulted
(finding 40). The dashboard's dish row reads `5 × roti · 225 g` instead of
`5 × roti`, grams rounded to whole. No planner change: the solver still picks
whole units, and the grams are the figure the plate's nutrition was already
computed from. No new constant.

**Tests, each shown red first by hand:**

- `tests/test_api_targets.py::TestEachPortionCarriesItsWeight` reads each
  dish's `grams_per_unit` from its YAML, not through `core`. With the server
  sending `grams_per_unit` alone (count dropped): `assert 45.0 == 225.0`,
  red. Restored: green.
- `tests/test_web_portion_grams.py` (new) drives the real `POST /api/plan`
  and compares each rendered row with the response that produced it. With
  the grams removed from the row: `portion not shown as 'N × unit · G g':
  '5 × roti'`, red. With `c.unit_count` rendered in place of `c.grams`:
  `assert 5 == 225`, red. Restored: green.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider`: `548 passed, 1 warning in 170.84s`. In the browser,
north_indian lunch for a 70 kg vegetarian: `5 × roti · 225 g`,
`1 × katori · 150 g`, `2 × katori · 300 g`.

**Noticed, not fixed — raw category token on the plate.** The same dish
row's role line renders `component.category` as-is, so Soya chunk masala
shows `Legume_curry` (CSS capitalises `legume_curry`). This is the
identifier-in-copy class `tests/test_web_no_identifiers.py` exists to catch,
and it misses it because its one success view (the CKD profile's
south_indian breakfast) has no underscored category on its plate. Two
defects: the missing label map, and a sweep that cannot see it. Left open.

## 2026-09-27 — intermittent web failure: 25 reruns, not reproduced — still open

Follows up the failure logged in the 2026-09-26 North Indian breakfast
entry: `tests/test_web_no_identifiers.py::test_every_view_was_actually_reached`
failed once in a full run, message not captured, then passed.

**Reruns, on `main` at `697d046`, both servers started from this checkout:**

| run | how | result |
|---|---|---|
| 20 × | that file alone | `12 passed` every time |
| 3 × | that file alone, CPU loaded (2 busy processes per core, 20 cores) | `12 passed` in 51.26 s, 57.91 s, 63.18 s |
| 2 × | full suite, `FOODAI_WEB_TESTS=required` | `545 passed, 1 warning` in 177.73 s and 169.97 s |

Plus the four full runs already recorded as green on 2026-09-26/27. The
failure has not come back in 25 runs today.

**Leading suspect, not confirmed.** The fixture reads the dashboard after
fixed waits (`wait_for_timeout(3500)` after each Generate click), not after
waiting for the result to appear. `POST /api/plan` for this profile took
2.01–2.04 s on every one of 18 direct calls (6 plates × 3), so the margin is
about 1.5 s. But the timing held at ~2.0 s and the test still passed under
heavy CPU load, so load alone did not break it. Other web tests each use their
own account, so shared server state is not an obvious cause either.

**Disposition: not fixed, cause unknown.** Changing the fixed waits to
wait-for-element would be a reasonable hardening but, with no reproduction,
there is no red run to show it addresses this failure; left alone. If it fails
again, save the full output (`... 2>&1 | tee`) before rerunning — the missing
message is the whole reason this is still open.

## 2026-09-27 — South Indian lunch: sodium guard is the main limit; soya chunk poriyal lifts SOUTH_LUNCH 33 → 78/144

**Diagnosis first** (in-memory what-ifs patching the probe's own
`__globals__`, one bound removed at a time; nothing changed on disk).
SOUTH_LUNCH two-plate count, 33/144 today:

| bound removed | 2+ plates |
|---|---|
| none | 33 |
| fat ceiling / carb floor / quality floor | 33 each |
| energy ceiling | 35 |
| carb ceiling / fibre floor | 37 each |
| energy floor | 40 |
| fat floor | 41 |
| protein floor | 51 |
| **sodium ceiling** | **83** |

The per-plate sodium guard (`day_budget.absurdity_fraction` 0.70 × 2000 mg
= 1400 mg, identical for every profile at lunch) is the main limit, then the
protein floor. Each gravy or vegetable katori adds about 240–440 mg sodium,
and plates need several to reach the protein floor. The vegetable slot's
only fillers are carrot dishes: `carrot_poriyal` carries 1.0 g protein for
240 mg sodium. The guard is a registered owner decision and was not touched.

**What was added.** `data/recipes/soya_chunk_poriyal.yaml` ("meal maker
poriyal"): `carrot_poriyal`'s lines unchanged, its 60 g carrot replaced by
20 g dry soya chunks and 40 g retained water; `south_indian`, `poriyal`,
vegan, 80 g katori, counts 1–2. Proportions fixed before any probe run.

**Measured** (`probe_rank_input2.py`). First on a branch off main without
`moong_soya_chilla`:

- SOUTH_LUNCH 33 → **78/144 = 54.2%**, above the 30% floor.
- Side effect, the poriyal also fills SOUTH_DINNER's vegetable slot:
  51 → 92/144.
- Other six templates unchanged. Grid 598 → **684/1152 = 59.4%**.
- Then rebased onto `moong_soya_chilla` (entry below) and measured again
  on that tree: SOUTH_LUNCH 78, SOUTH_DINNER 92, NORTH_BREAKFAST 85, other
  templates as above. Grid **734/1152 = 63.7%**, every template at or above
  30% — **the probe reports `exit condition met: True`**, the first time.

**Two test fixtures repointed**, both because a profile they relied on to
decline now passes; no assertion changed:

- `tests/test_api_targets.py` decline: 70 kg → **100 kg** lose_fat
  vegetarian CKD, still a locked protein decline (57.2 g vs 63.0 g).
  80, 85, 95, 100, 110 decline; 90 passes.
- `tests/test_web_no_identifiers.py` sodium decline: 88 kg → **121 kg**
  maintain vegetarian CKD, sodium alone (2281.1 mg vs 1400.0 mg), the middle
  of the contiguous 118–125 run found by scanning 45–130 kg.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider`: 545 passed, 1 warning — on the branch off main, and
again on the rebased tree with `moong_soya_chilla`. No new gate, so no
deletion check.

**Disposition:** SOUTH_LUNCH above floor; probe exit condition met.

## 2026-09-27 — moong soya chilla: NORTH_BREAKFAST 35 → 85/144, above the 30% floor

**What was added.** `data/recipes/moong_soya_chilla.yaml`: `moong_dal_chilla`
with its 30 g dry dal split 21 g moong + 9 g `soya_flour_defatted` — 30% of
the dry mass, `soya_idli`'s own share (4 of 14 g). Every other line and the
serving unit (81 g, counts 1–5) unchanged. `north_indian`, `dal_chilla`,
vegan. Proportions fixed before any probe run.

**Why.** Entry 2026-09-26 (North Indian breakfast dishes): vegans reached at
most one North breakfast plate, because `soya_keema_paratha` was the only
vegan dish in the template carrying qualifying protein. Soya flour (DIAAS
1.05, a literature value) in the protein course is the second.

**Measured on the tree** (`probe_rank_input2.py`), NORTH_BREAKFAST profiles
with 0 / 1 / 2+ plates:

| | vegetarian | vegan | 2+ total |
|---|---|---|---|
| before | 17 / 20 / 35 | 54 / 18 / 0 | 35/144 (24.3%) |
| after | 1 / 18 / 53 | 24 / 16 / 32 | **85/144 (59.0%)** |

Vegetarians gain too: the dish is vegan, so it is open to them. Other seven
templates unchanged. Grid 598 → **648/1152 = 56.3%**; declined 311 → 265.
The exit condition is now blocked only by `south_indian/lunch` (33/144).

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider`: 545 passed, 1 warning. No new gate, so no deletion
check.

**Disposition:** NORTH_BREAKFAST above floor.

## 2026-09-26 — North Indian breakfast dishes: soya onion raita, paneer moong chilla, soya keema paratha

**Diagnosis first** (in-memory what-ifs patching the probe's own
`__globals__`, nothing changed on disk). NORTH_BREAKFAST stood at 4/144
two-plate, profiles with 0 / 1 / 2+ plates by diet:

| what-if | vegetarian | vegan |
|---|---|---|
| none | 59 / 9 / 4 | 72 / 0 / 0 |
| no quality-protein floor | 14 / 23 / 35 | 72 / 0 / 0 |
| no fat ceiling | 33 / 35 / 4 | 72 / 0 / 0 |
| no fat/carb bounds at all | 26 / 42 / 4 | 72 / 0 / 0 |

Two causes. (1) Vegan is a structural zero: `curd_or_raita` is required and
its only north_indian filler, `onion_raita`, is dairy (already logged
2026-08-24). (2) Vegetarian plates are held mainly by the quality-protein
floor: only `paneer_paratha` and `onion_raita` carry qualifying protein.

**CORRECTION, before any dish was written.** I first told the owner a
soya-curd raita would carry qualifying protein. It does not:
`soya_curd_plain` has no DIAAS in the ingredient table. The only vegan rows
that qualify are `soya_chunks_dry` (0.85) and `soya_flour_defatted` (1.05).
The owner then chose three dishes instead of two, each proportioned from an
existing recipe before any probe run.

**Commit 1 — `soya_onion_raita`.** `onion_raita` gram for gram with
`soya_curd_plain` in place of `curd_dahi`; `north_indian`, `raita`,
uncooked. Makes a vegan North breakfast buildable; cannot make one pass.
Measured on the tree (`probe_rank_input2.py`):

- NORTH_BREAKFAST 4/144, unchanged. Vegan 72 cases move from `empty_pool`
  to `declined` — which is why the probe's declined count rises 303 → 371
  while nothing got worse.
- Side effect, the raita also fills the optional raita slot in NORTH_LUNCH
  and NORTH_DINNER: north lunch 91 → 118, north dinner 98 → 114.
- Grid 516 → 559/1152.

Two tests in `tests/test_planner_quality.py` moved with it, both corrected
in place with a dated note: the tofu perturbation plate now carries one
soya raita and one phulka fewer (the tofu-and-dal core it exists to show is
unchanged), and the diet-decides-the-plate test is repointed from north
dinner — where both diets now get the same all-plant plate — to north
lunch, where they still differ. Deletion check on the repointed test:
bypassing `diet_pattern_permits` in `core/planner/candidates.py` turns it
red (6 failed in that file, it among them); restored.

`python -m pytest tests/ -q -p no:cacheprovider` on this commit's tree:
477 passed, 68 skipped.

**Commit 2 — `paneer_moong_chilla`.** Every `moong_dal_chilla` line
unchanged plus 20 g paneer (about 100 g for five chillas); `dal_chilla`,
101 g unit, counts 1–4 (one below the plain chilla's 5, the library's
existing plain-to-stuffed step for parathas). Measured on the tree:
NORTH_BREAKFAST 4 → 7/144; vegetarian 0 / 1 / 2+ 34 / 31 / 7 (was
59 / 9 / 4) — 25 vegetarian profiles gain a first plate, few a second.
Other seven templates unchanged. Grid 559 → 562; declined 371 → 346.
Suite on this tree: 477 passed, 68 skipped.

**Commit 3 — `soya_keema_paratha`.** `paneer_paratha`'s dough, oil and
spice lines unchanged, its 35 g paneer filling replaced by 35 g soya keema
(10 g dry soya chunks, 20 g retained water, 5 g onion); `paratha`, vegan,
93.3 g unit, counts 1–4. Measured on the tree:

| | vegetarian 0 / 1 / 2+ | vegan 0 / 1 / 2+ | NORTH_BREAKFAST 2+ |
|---|---|---|---|
| before this task | 59 / 9 / 4 | 72 / 0 / 0 | 4/144 (2.8%) |
| after commit 3 | 17 / 20 / 35 | 54 / 18 / 0 | **35/144 (24.3%)** |

**Still below the 30% floor (43).** Vegans can now get a North breakfast
(18/72) but never two plates: the keema paratha is their only qualifying
source, so exactly one bread choice can pass. A second vegan qualifying
dish is what a further gain needs; not attempted here.

Side effect: the paratha also fills NORTH_DINNER's bread slot, north
dinner 114 → 122. Grid 562 → **598/1152 = 51.9%**, above the 50% overall
exit condition for the first time; the exit condition is still unmet
because `south_indian/lunch` (33) and `north_indian/breakfast` (35) are
below the per-template floor. Declined 346 → 311.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider`: first run 1 failed, 544 passed —
`tests/test_web_no_identifiers.py::test_every_view_was_actually_reached`,
failure message not captured. That file alone: 12 passed. Full run again:
545 passed, 1 warning. **Logged as intermittent, not fixed, cause not
known.**

**Noticed, not fixed:** `web/dashboard.html`'s plate-picker comment still
gives North Indian breakfast as 2.8% and the South snack as 0/144; both
are stale. A source comment, not shown to users.

**Disposition:** three dishes landed; NORTH_BREAKFAST 4 → 35/144, still
below floor, documented, not tuned.

## 2026-09-26 — sundal quarter katori: South snack 67/144, above the 30% floor — owner decision

**Decision (project owner, 2026-09-26):** both sundals
(`soya_chana_sundal`, `soya_chunk_sundal`) are served in quarter katoris
(40 g), counts 1–8, default 4. The second of the two changes chosen together
(entry above, snack energy band). Every ingredient line is exactly half the
half-katori line, so the recipe ratio is unchanged; the ceiling of 8 is the
same 320 g total as the old 4. Per unit (measured): chana 65.6 kcal, chunk 52.1 kcal —
half the half-katori figures in the soya chunk sundal entry below.

**Why.** A quarter katori is about two serving spoonfuls, the way sundal is
ordinarily served; it halves the energy step the solver has to land in the
snack band.

**Measured on the tree** (`probe_rank_input2.py`), profiles with 0 / 1 / 2+
plates: South snack **20 / 57 / 67 — 67/144 = 46.5%, above the 30% floor**,
matching the what-if in the entry above; rung-0-only 64/144. North snack
56 / 30 / 58, unchanged by this commit. Other six templates unchanged. Grid
516/1152 = 44.8% (from 473); declined 330 → 303.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider`: 545 passed, 1 warning. Data change only; no new gate,
so no deletion check.

**Disposition:** implemented. South snack no longer below floor.

## 2026-09-26 — snack energy band: ±10% before any relaxation — owner decision

**Decision (project owner, 2026-09-26): a snack's energy band is ±10% around
its energy point**, registered as `tolerance.energy_snack` (0.10) and applied
in `meal_target` via `_ENERGY_TOLERANCE_BY_SLOT`. Breakfast, lunch and dinner
keep the day's ±5% scaled down. The first of two changes the owner chose
together; the second (quarter-katori sundals) is its own commit.

**Why.** Entry below (soya chunk sundal): the scaled ±5% band is 17–32 kcal
wide for a snack, and whole 104–131 kcal units almost never land in it two
ways. 0.10 equals `tolerance.energy_relaxed`, which the ladder already accepts
for every meal, so the ladder's energy rung is now a no-op for a snack
(tested).

**Measured before deciding** (in-memory what-ifs patching the probe's own
`__globals__`; quarter-katori rows on a scratch copy of `core/`, `data/` and
the probe with both sundals halved to 40 g units, counts 1–8), profiles with
0 / 1 / 2+ plates:

| change | south snack | north snack |
|---|---|---|
| none | 47 / 97 / 0 | 56 / 42 / 46 |
| band ±10% | 47 / 73 / 24 | 56 / 30 / 58 |
| band ±15% | 19 / 73 / 52 | 52 / 34 / 58 |
| quarter katori | 20 / 89 / 35 | 56 / 42 / 46 |
| quarter katori + band ±10% (**chosen**) | 20 / 57 / 67 | 56 / 30 / 58 |

The ±15% row is approximate: the energy rung re-bands at 0.10 and can
narrow a ±15% band on that rung. Not investigated, as it was not chosen.

**This commit, measured on the tree** (`probe_rank_input2.py`): South snack
47 / 73 / 24 (24/144 = 16.7%, still below floor until the portion commit);
North snack 56 / 30 / 58 (40.3%, was 31.9%). Other six templates unchanged.
Grid 473/1152 = 41.1% (from 437); declined 330, unchanged.

**Deletion check.** Replacing the `if tolerance_key is not None and
"energy_kcal" in points:` guard with `if False:` turns two tests red —
`TestASnackHasAWiderEnergyBand::test_snack_band_is_ten_percent_around_its_point`
and `TestASnackHasNoFatOrCarbFloor::test_only_fat_and_carb_lose_a_floor_on_a_snack`
— 2 failed, 475 passed; restored, 477 passed.

**Disposition:** implemented.

## 2026-09-26 — soya chunk sundal: South snack declines 116 → 47, still 0/144 at two plates — the limit is energy granularity, not protein

**What was added.** `data/recipes/soya_chunk_sundal.yaml` ("meal maker
sundal"), `category: sundal`, the second dish `SOUTH_SNACK.sundal` can
take. Chosen by the owner for its quality protein per kcal, since 112 of
the 116 South snack declines were on the quality-protein floor (entry
2026-09-25, South Indian snack). Proportions fixed before any probe run:
tempering, coconut and salt lines are `soya_chana_sundal`'s unchanged;
chickpeas replaced by 21 g dry soya chunks (with 42.25 g retained water)
and 10 g onion. Per 80 g half katori: 104.2 kcal, 11.3 g protein.

**Measured on the tree** (`probe_rank_input2.py`), South snack profiles with
0 / 1 / 2+ plates: **47 / 97 / 0** (was 116 / 28 / 0). Declined 399 → 330
across the grid. Two-plate count unchanged at 437/1152 = 37.9%; other seven
templates unchanged.

Which plate each planned profile gets (at the accepted rung):

| plate | profiles |
|---|---|
| soya_chunk_sundal | 51 |
| soya_chunk_sundal + neer_mor | 22 |
| soya_chana_sundal | 20 |
| soya_chana_sundal + neer_mor | 4 |
| declined | 47 |

No profile gets two. The two sundals split the grid; they never both fit.

**CORRECTION to my own premise.** Before building it I told the owner the
quality-protein floor was what kept the South snack from two plates. It was
what kept it from *one*. The two-plate limit is energy granularity:

- The snack energy window at rung 0 is about ±5% of 10% of the day —
  e.g. 166.0–183.4 kcal (45 kg lose_fat), 303.2–335.1 kcal (110 kg maintain):
  17–32 kcal wide.
- Portions are whole half-katoris: 104.2 kcal (chunk), 131.3 kcal (chana),
  plus 0 or 1 neer mor at 30.9 kcal. Reachable totals, 1–4 units:
  chunk 104, 208, 313, 417 (+31); chana 131, 263, 394, 525 (+31).
- Counting only whether a plate can land in the rung-0 window at any unit
  count — ignoring every other bound and every rung — profiles with
  0 / 1 / 2+ plates: **24 / 112 / 8**. At most 8/144 = 5.6% could ever
  get two plates from these four combinations; the floor is 30% (43).

More dishes of this size will not fix that on their own. Settling it is an
owner decision, measured in the next entry when made.

**Verification.** `FOODAI_WEB_TESTS=required python -m pytest tests/ -q
-p no:cacheprovider`: 540 passed, 1 warning. No new gate, so no deletion
check.

**Disposition:** dish saved; South snack stays below floor, documented, not
tuned.

## 2026-09-25 — snack fat/carb floors: dropped for snacks, ceilings kept — owner decision

**Decision (project owner, 2026-09-25): a snack has no fat floor and no carb
floor. Its fat and carb ceilings stay**, as do its points, energy band,
protein floor and guard, quality-protein floor, fibre floor and sodium.
Breakfast, lunch and dinner are unchanged. Implemented as
`_FLOORLESS_BY_SLOT` in `core/nutrition/meal_target.py`.

**Why.** `meal_target` scaled every day bound by the slot's energy share,
so a snack had to carry the day's macro split in miniature (≈23–32% of
energy from fat, ≈47–63% from carbohydrate): a balanced small meal. Both
North Indian snack dishes are ordinary and lopsided — the chaat ≈9% fat, the
tikka ≈30% carbohydrate — and both were declined for it (entry below). Fat
and carbohydrate ranges are daily guidance; a lean or low-carb snack does
not breach them.

**Cost, stated.** The planner solves one plate per request. Nothing yet
checks that the rest of the day makes up what a snack leaves out.

**Measured before deciding**, in-memory what-ifs patching the probe
functions' own `__globals__` (the method corrected in the entry below),
profiles with 0 / 1 / 2+ plates:

| change | south snack | north snack |
|---|---|---|
| none | 119 / 25 / 0 | 144 / 0 / 0 |
| no snack fat/carb floor | 116 / 28 / 0 | 86 / 58 / 0 |
| chaat + tikka on one plate | — | 98 / 46 / 0 |
| both | — | 56 / 42 / 46 |
| (rejected) fat/carb band ±50% | 116 / 28 / 0 | 114 / 26 / 4 |
| (rejected) fat/carb band ±75% | 116 / 28 / 0 | 94 / 46 / 4 |

The owner chose "both", saved as two commits: this floor change, then the
mixed plate.

**This commit, measured on the tree** (`probe_rank_input2.py`): other six
templates unchanged; declined 490 → 429 (North snack 58, South snack 3
now plan); two-plate counts unchanged at 391/1152, since no snack yet offers
two plates.

**Deletion check.** Replacing `floors.pop(macro, None)` with `pass` turns
two tests red —
`TestASnackHasNoFatOrCarbFloor::test_snack_drops_both_floors_and_keeps_both_ceilings`
and `::test_the_fat_carb_rung_does_not_restore_a_dropped_floor` — 2 failed,
470 passed; restored.

**Second commit: chaat + tikka on one plate.** `NORTH_SNACK.snack` takes
`max_selections=2`; with one chaat and one tikka in the library that can only
be the pair. Measured on the tree, profiles with 0 / 1 / 2+ plates: north
snack **56 / 42 / 46 — 46/144 = 31.9%, above the 30% floor**, matching the
what-if; rung-0-only 28/144. South snack 116 / 28 / 0, unchanged by this
commit. Grid 437/1152 = 37.9% (from 391); declined 429 → 399. Other six
templates unchanged. Deletion check: `max_selections=1` on that line alone
turns `test_north_snack_offers_two_dish_kinds_and_an_optional_drink` red
(1 failed, 471 passed); restored. Only that shape pin catches it — no
behaviour test does, same as SOUTH_SNACK's shape. (A first attempt at this
mutation hit all four `max_selections=2` lines in the file and failed 9
tests; discarded as not measuring this mechanism.)

## 2026-09-25 — North Indian snack: NORTH_SNACK plans 0/144 — each dish misses a different floor; saved, not tuned, no web card

TASKS_3.md R4d, North Indian snack, built with two main dishes from the start
per the pass-mark decision (entry below). Owner chose, after seeing the
numbers, to save it as it is and withhold the web card.

**What was added.** `oil_uptake.tikka_pan_roasted` (0.90, project estimate,
unverified — commit cf7f089). `soya_chana_chaat` (category `chaat`, vegan,
half-katori unit), `soya_tikka` (category `tikka`, 4-piece plate, max 3),
`chaas` (category `buttermilk`, north_indian), and `NORTH_SNACK` (required
`snack` accepting {chaat, tikka}; optional `drink`).

**Result.** `probe_rank_input2.py`, north_indian/snack: **0/144 plan at all**
(every case declines; declined 346 → 490 of the grid). Other seven templates
unchanged. Full grid 391/1152 = 33.9%.

**Correction.** Before building, the owner was told the chaat "should give
two plates to roughly the profiles the sundal serves". **That was wrong.**
The sundal's fat comes from coconut and tempering oil; the chaat has almost
none, and the snack target has a fat floor.

**Why, measured per unit** (`nutrition_of_components`, point values):

| dish | kcal | protein g | fat g | carb g |
|---|---|---|---|---|
| soya_chana_chaat (half katori) | 100.3 | 8.5 | 1.0 | 14.8 |
| soya_tikka (4 pieces) | 71.9 | 6.8 | 2.6 | 5.4 |
| chaas (glass) | 30.2 | 1.6 | 2.0 | 1.5 |

Against the reference snack target (70 kg maintain: 244–270 kcal, fat
6.7–9.0 g, carb 30.1–40.7 g), arithmetic from the rows above:

| plate | kcal | fat g | carb g | fails |
|---|---|---|---|---|
| 2 chaat + chaas | 230 | 4.0 | 31.2 | energy, fat floor |
| 3 chaat | 301 | 3.0 | 44.5 | energy, fat floor, carb ceiling |
| 3 tikka | 216 | 7.9 | 16.3 | energy, carb floor |
| 3 tikka + chaas | 246 | 9.9 | 17.8 | fat ceiling, carb floor |

The chaat is too lean; the tikka too low in carbohydrate. The ladder's
`fat_carb_tolerance` rung does not close either gap.

**CORRECTED 2026-09-25, same day — the sentence that stood here was false.**
It read: "What-if, in memory only (no file changed): letting the main slot
hold one chaat **and** one tikka together still plans 0/144." That what-if
never ran. It patched the dict `runpy.run_path` returns, which is a *copy*
of the probe's globals, so the probe kept calling the real `template_for`
and simply re-measured the template as built. Re-run by patching the probe
functions' own `__globals__` (asserted to be the dict they read): **chaat +
tikka on one plate gives 46/144 one plate, 0/144 two** (0/1/2+ =
98/46/0). The same commit message (36132d5) and PR #10's first description
carry the false figure. The two earlier in-memory what-ifs on 2026-09-25
(quality floor off; identical second sundal) patched a shared module or
object rather than that dict, and their numbers moved, so they did run.
Lesson, same family as findings 11 and 18: a what-if that returns the
baseline unchanged must be checked for having run at all.

**Not done, and why.** No oil, sev or coconut added to the chaat and no
bread added to the tikka: each would be moving a dish to fit a window. The
open question the numbers raise is a target one — whether a snack should
carry the same fat and carb floors as a meal, which appear to exclude many
ordinary lopsided snacks. That is the owner's decision, left as its own task.

**No web card.** `web/dashboard.html` is unchanged: a North Indian snack card
that never solves would tell the user something false. The reason is
recorded at `NORTH_SNACK` in `core/foods/templates.py`.

**The chaat declares every macro unassessed.** Its soya soak is a process on
a raw-basis row and it has no oil line, so the loader (rightly) refused a
0.0 process band. It joins `NO_OIL_COOKED` in `tests/test_nutrition_of.py`
with idli, phulka and soya_idli; outside `dev_mode` it is not plannable.

**Logged, not fixed.** `soya_chana_sundal` (and any soya-chunk dish with an
oil line) soaks the same raw-basis row, but its oil line satisfies the
loader, so its protein band shows 0.25 while the chaat's shows 0.45. The
oil constant covers the oil, not the soak. Same shape as finding 41: a
process with no registered constant, hidden by an unrelated one.

**Test repointed.** `test_missing_grammar_raises_rather_than_substituting_another_region`
used (NORTH_INDIAN, SNACK); every regional pair now has a template, so it
uses (PAN_INDIAN, SNACK).

## 2026-09-25 — pass mark stays at two plates for every slot, snacks included — owner decision

**Decision (project owner, 2026-09-25): `MIN_VALID_PLATES` stays 2 for
every template, snacks included.** A snack meets it the same way a lunch
does: with genuinely different dishes, not a lower bar.

**Why it was asked.** SOUTH_SNACK landed at 0/144 (entry below). The
question was whether "two distinct plates" fits a one-dish slot at all.

**Correction to how the question was first put.** It was framed to the owner
as "a one-dish snack can't reach two plates". **That was wrong.** A plate is
a distinct combination of dishes, not a distinct portion count, so a
one-dish template with two sundal recipes has two plates. The wall is one
recipe, not one slot.

**Measured.** `probe_rank_input2.py`'s own `profiles()` and
`accepted_rung_valid_plate_count`, south_indian/snack, with an in-memory
identical copy of `soya_chana_sundal` added (a ceiling, not a real dish; no
file changed):

| | 0 plates | 1 plate | ≥ 2 plates |
|---|---|---|---|
| library as is | 119 | 25 | 0 |
| + identical second sundal | 119 | 0 | 25 |

So a second dish lifts every profile that gets a snack to the pass mark,
but 119/144 still get none. The option declined — count one plate as a pass
for snacks — would score 25/144 = 17.4%, still below the 30% floor. It
changes the label, not the result, and leaves the ranking step nothing to
rank.

**What follows.** The snack gap is a library problem: more genuinely
different snack dishes, each chosen as an ordinary snack first and measured
after, never tuned to a window.

## 2026-09-25 — South Indian snack: SOUTH_SNACK lands at 0/144, below the 30% floor — documented, not gamed

TASKS_3.md R4d, South Indian snack. Three pieces, saved in two commits:

- `chickpea_boiled` (USDA FDC 173757, `verified=false`) — commit d89d908.
- `neer_mor.yaml` (category `buttermilk`), alone, because
  `SOUTH_BREAKFAST.curd_course` and `SOUTH_LUNCH.curd_course` already accept
  that category — commit f32c84a.
- `soya_chana_sundal.yaml` (category `sundal`, half-katori unit, approved by
  the owner) with the `SOUTH_SNACK` template — this commit. They go together
  because `tests/test_recipes.py` needs every recipe category to be accepted
  by some template.

**Result.** `probe_rank_input2.py`, 144 profiles, south_indian/snack:
**0/144 reach the two-plate pass mark**; 25/144 get one valid plate; 119/144
get none. The rung-0-only line is also 0/144.

**Why, structurally.** A snack's energy window is roughly 20–35 kcal wide. The
template has one required dish and one optional drink, and portions move in
whole units. The only two plates are "sundal" and "sundal + neer mor", 31 kcal
apart, so they rarely fit the same window. Two plates would need a second
sundal or a second snack dish, not a wider bound. Heavier lose_fat profiles
also need more quality protein per kcal than a sundal carries (110 kg
lose_fat: 19.8 g within ≤ 268 kcal).

**The quality-protein floor, tested as the entry below asked.** The 2026-09-25
floor decision said to revisit "only if a real snack template fails on this
bound". Measured with the floor set to 0 in-process (measurement only, no
file changed): 46/144 get one plate, still 0/144 get two. So the floor costs
21 profiles their only plate but is **not** why the snack misses the pass
mark. That is evidence for a future decision, not a decision; the floor stays
flat.

**neer_mor's side effect on the other templates** (before = d89d908,
after = + neer_mor, each a separate worktree with its own `data/`):

| template | before | after |
|---|---|---|
| south_indian/breakfast | 117 | 114 |
| south_indian/lunch | 33 | 33 |
| south_indian/dinner | 49 | 51 |
| north_indian/* | unchanged | unchanged |
| overall (864) | 392 | 391 |

The breakfast drop is the ladder, not the food. 95 kg lose_fat vegetarian
(no flag, hypertension, CKD) went from 2 plates at `fat_carb_tolerance` to 1
plate at `rung_0`: neer mor lets an earlier rung plan, and the ladder stops at
the first rung that plans. Other breakfast profiles gained plates.

It also made `tests/test_api_targets.py`'s CKD decline fixture pass, honestly:
55 kg lose_fat lunch now fits 2 katori soya_kuzhambu with neer mor, 36.5 g
protein against the locked 34.6 g floor, 1226 mg sodium under 1400 mg.
Repointed to 70 kg, which still declines on the locked floor (39.2 g vs
44.1 g).

**Full grid after this commit**, 1008 cases: 391/1008 = 38.8% (the other six
templates match the neer_mor row above; the drop from 45.3% is the extra
template's zeros, arithmetic not regression).

**Corrected in place.** `core/nutrition/citations.py`
(`protein.quality_meal_floor_fraction` note), `core/nutrition/meal_target.py`
and `docs/methodology.md` said no snack template existed. Each now carries a
dated correction.

**Logged, not fixed.** `web/dashboard-copy.js` `PLATE_LABELS` has no entry for
`south_indian:dinner`, `north_indian:breakfast` or `south_indian:snack`. The
success card falls back to `humanise()`, e.g. "South indian · snack": readable,
not wrong, but not the written label. Predates this task for the first two.

**Open.** Whether a two-plate pass mark fits a one-dish meal slot at all is a
question for the owner, not something to settle by adding filler dishes.
*(Settled 2026-09-25, entry above: the mark stays at two; snacks need more
real dishes.)*
North Indian snack not started.

## 2026-09-25 — snack quality-protein floor: kept flat, decided before any snack template exists

**Decision (project owner, 2026-09-25): `protein.quality_meal_floor_fraction`
stays flat at 0.10 for every slot, snack included.** Asked before R4d's snack
templates were started, because `core/nutrition/citations.py` and
`docs/methodology.md` both record the snack case as "unexercised rather than
resolved".

**What was measured.** Reference profile (70 kg, male, 175 cm, 28 y,
moderate, maintain, vegetarian): snack target energy 244.3–270.0 kcal,
protein ≥ 16.8 g, fat ≤ 9.0 g, carb 30.1–40.7 g; quality floor 0.10 × 112 =
11.2 g, same as lunch. Cost of 11.2 g protein from each library ingredient
with DIAAS ≥ 0.75:

| ingredient | grams | kcal | fat g |
|---|---|---|---|
| soya_chunks_dry | 22 | 74 | 0.1 |
| soya_flour_defatted | 22 | 71 | 0.3 |
| pomfret_white_raw | 59 | 72 | 3.0 |
| chicken_breast_raw | 51 | 86 | 4.6 |
| egg_boiled | 83 | 123 | 8.8 |
| paneer_fresh | 61 | 181 | 12.7 — over the fat ceiling alone |
| curd_dahi | 361 | 217 | 14.5 — over the fat ceiling alone |

So the flat floor does not make a snack unreachable; it makes every snack
soya-, fish-, chicken- or egg-based, and every vegetarian or vegan snack
soya-based. The alternative offered — exempt the snack slot, on the grounds
that the floor's stated purpose is "no *meal* is pure lentil" — was declined:
changing the bound before a single snack plate had been tried would be a
number moved for convenience. **Revisit only if a real snack template fails
on this bound**, with that failure as the evidence.

Ingredient-level arithmetic only; no snack template, recipe or plan was
built or solved for this entry.

## 2026-09-25 — north_indian/dinner's 86→98/144 is aloo_paratha filling NORTH_DINNER.bread — explained, not a defect

Addresses the unexplained move logged in the 2026-08-24 NORTH_BREAKFAST entry
below. That entry said the move was "not caused by this task (neither
`NORTH_DINNER` nor any recipe it uses was touched here)" and guessed at R4b/R4c.
**Both halves were wrong.** `NORTH_DINNER.bread` has accepted
`{"roti", "paratha"}` since it was written, and that commit added the library's
first three `category: paratha` recipes. `aloo_paratha.yaml`'s own header
already says it "incidentally fills that gap too" — the entry contradicted a
file in its own commit.

**Measured, not read.** `probe_rank_input2.py`'s own
`accepted_rung_valid_plate_count` and `profiles()`, north_indian/dinner only,
each tree a separate `git worktree` (code *and* `data/` from that tree):

| tree | north_indian/dinner |
|---|---|
| A: `bb8af95` (before NORTH_BREAKFAST) | 86/144 |
| B: `08ef4b0` (NORTH_BREAKFAST) | 98/144 |
| C: `08ef4b0` minus `aloo_`/`plain_`/`paneer_paratha.yaml` | 86/144, row-for-row identical to A |
| `422f769` (main today) | 98/144, row-for-row identical to B |

Removing the three parathas restores every one of the 144 rows, so they
account for the whole move and nothing else between the two runs moved it.
40 profiles gained valid plates (none lost any); 12 crossed
`MIN_VALID_PLATES = 2` from 1 to 2, all at rung 0: 45 kg `gain_muscle`
vegetarian and vegan, and 55 kg `maintain` vegan, each under all four
clinical-flag settings. For 45 kg vegetarian and 55 kg vegan the new second
plate is `aloo_paratha + soya_chunk_curry + aloo_sabzi`, next to the existing
`phulka + soya_chunk_masala + aloo_sabzi`.

**Disposition: explained, no code change.** A paratha at dinner is what the
template already allowed; the bread slot simply had no recipe before. Whether
a paratha *should* be a dinner option is a product question, not raised here.

## 2026-09-25 — web decline fixture repointed: the CKD profile declines on sodium again — **FIXED**

Addresses the finding raised in the 2026-08-24 SOUTH_DINNER entry below:
`tests/test_web_no_identifiers.py`'s CKD profile (weight_kg=74) no longer
declined for `south_indian/lunch`, so `test_every_view_was_actually_reached`
failed under `FOODAI_WEB_TESTS=required`.

**Not caused by the open PR.** Checked against `origin/main` (`b8142bd`) in a
separate worktree, with the API and static server *also* started from that
worktree: same failure, same assertion. (A first attempt ran main's tests
against servers still serving the PR branch; that comparison was discarded,
not reported.)

**Why not reuse `test_api_targets.py`'s repoint (weight_kg=55,
goal=lose_fat).** That profile declines on a locked *protein* floor. This
test also asserts the decline names sodium or salt, so it needs a sodium
decline. Searched vegetarian + `chronic_kidney_disease`, male, 31 y,
176 cm, moderate, `maintain`, via `POST /api/plan`:

| weight_kg | result | sodium actual vs bound (mg) |
|---|---|---|
| 74 | passes | — |
| 76, 77 | declines, sodium only | 1560.3 vs 1400.0 |
| 78, 79 | passes | — |
| 80 | declines, sodium only | 1654.5 vs 1400.0 |
| 83–91 | declines, sodium only | 1808.0–2276.6 vs 1400.0 |
| 92–95 | declines, sodium + protein floor | 2276.6 vs 1400.0 |

Sodium misses are not monotonic in weight, so 80 sat next to passing
weights. **88** was chosen from the middle of the 83–91 run: 1962.9 mg vs
1400.0 mg, `locked_by: chronic_kidney_disease`. Only the weight changed;
every other field of the profile is as before. `test_web_decline_copy.py`
and `test_web_wizard_layout.py` also use weight_kg=74 but neither depends on
a real decline (one stubs `/api/plan`, the other has no clinical flag); left
alone.

**Red before, green after.** Before: under `FOODAI_WEB_TESTS=required`,
`1 failed, 525 passed`, the failure being
`test_every_view_was_actually_reached` ("the decline section did not
render"). After: `526 passed, 1 warning in 161.17s`, API and static server
started from this worktree (API's warning path confirmed
`...worktrees\r1a-ingredient-classes\api\main.py`).

## 2026-08-24 — NORTH_BREAKFAST added; lands below the 30% per-template floor, documented not gamed (R4d, north breakfast sub-task)

**What was done.** Per the user's explicit choice, R4d's next sub-task after
SOUTH_DINNER was North Indian breakfast — genuinely new work, no existing
grammar to reuse (unlike SOUTH_DINNER's deliberate mirror of SOUTH_LUNCH).
Four structural blockers were hit in sequence during design; at each, work
stopped and the user was asked how to proceed (CLAUDE.md's "if a task is
substantially larger than described, stop and say so before doing the work"),
and each time chose to keep going:

1. **Structural zero.** An initial single-paratha-variant `bread_base` +
   `curd_or_raita` grammar had exactly one legal combination in the whole
   pool — added a second paratha (`plain_paratha.yaml`, sharing
   `aloo_paratha`'s wheat/water/oil ratios minus the potato filling).
2. **Quality-protein floor unreachable.** `onion_raita` alone tops out at
   7.94g qualifying protein against an 11.2g floor, and by that serving
   level energy/fat already breach their ceilings — a paneer paratha
   (`paneer_paratha.yaml`, DIAAS 1.00 filling) was added to put a
   quality-protein source directly in the bread slot.
3. **Systemic 0% across all 144 profiles.** Every paratha variant is too
   fat-dense/carb-light for the breakfast target at any serving count that
   also clears the protein floor. `bread_base` was widened to also accept
   `roti` (reusing the existing `phulka` recipe) — a genuine dietary
   alternative, not a gamed range.
4. **Still 0% with phulka.** Range-checking showed `phulka`+`raita`'s own fat
   range never reaches the fat floor (too lean), while `paratha`+`raita`
   combos always breach the fat ceiling before the protein floor. A real
   3-slot tension (protein floor 28g, quality-protein floor 11.2g, fat
   ceiling ~22.6g, carb floor ~75.2g) that no 2-component bread+curd
   combination can satisfy together. Added a third, separate required slot
   (`protein_course`, filled by a new `moong_dal_chilla.yaml` — a moong dal
   pancake, protein-dense and low-fat, the standard fix for this shape of gap
   in Indian home cooking) and made `bread_base` optional (a chilla-only
   breakfast is realistic, not invented).

This moved the template from a guaranteed 0% to 4/144 = 2.8% pooled (vegan
0/72 = 0.0%, vegetarian 4/72 = 5.6%) — still below the 30% per-template floor.
Asked the user whether to land here or keep tuning; chosen: keep tuning. A
brute-force exhaustive search over all legal integer serving-count triples of
`paneer_paratha` + `moong_dal_chilla` + `onion_raita` against the hardest
reference profile (weight 70kg, MAINTAIN, VEGETARIAN, no clinical flags)
confirmed no exact integer solution exists: the closest combination (1
paratha, 2 chilla, 1 raita) misses on carb (short ~4g), quality-protein
(short ~0.83g) and energy (short ~14.7kcal) simultaneously; every other
combination trades those misses for a fat-ceiling breach instead. A
considered non-gaming lever — correcting `paneer_paratha`'s dough:filling
ratio from 35g:35g to ~40g:35g wheat, matching `aloo_paratha`'s own ~52:48
ratio — was evaluated by hand and found to close only the carb/energy misses
(+~3.5g carb, +~17kcal), not the quality-protein one, since wheat's DIAAS
(0.45) sits below the 0.75 qualifying threshold. It was not applied: it would
not have moved any profile from fail to pass, only reduced the margin on a
miss that stays a miss. No further non-gaming lever was found. Per the
project's standing rule (never widen a bound "for the purpose of" passing —
`onion_raita`'s own `max_count` ceiling was explicitly left untouched, since
its file header names that ceiling as a deliberate anti-gaming choice), the
task lands here: below-floor, fully documented, rather than closed by
loosening a constraint that does not genuinely support it.

**Vegan structural zero (separate, undisturbed by this task):**
`curd_or_raita`'s only filler eligible for `north_indian` is `onion_raita`
(dairy), so no vegan plate can ever fill that slot — 0/72 = 0.0% vegan
against this template is a hard structural floor, not a tuning gap, until a
non-dairy north_indian raita/curd recipe is added.

**New nutrition constant.** `oil_uptake.paratha_griddled` (`core/nutrition/
citations.py`) — 0.80 fraction retained, reusing `PROJECT_OIL_UPTAKE_ESTIMATE`
Evidence (broad "oil applied to a hot flat griddle" phenomenon, already
covering surface-application mechanics) with `applied_to` text specific to a
folded, re-brushed paratha rather than a spread dosa batter. `verified=False`
(no human has opened a matching primary source), same convention as
`oil_uptake.dosa_griddled`.

**New ingredient.** `moong_dal_raw` (`data/raw/ifct/fixture_ingredients.csv`)
— sourced from USDA FDC 174256 ("Mung beans, mature seeds, raw," retrieved
2026-08-24). The mechanism caveat is stated plainly in the row's own
`source_note`: FDC has no split-dehusked-moong-dal-specific entry, so this
reuses the whole-mung-bean composition — close but not identical. Atwater
reconciliation is 296.4 vs. 347 stated kcal, 14.6% off, inside the 15%
tolerance but at its edge. DIAAS is 0.60, explicitly stated as REUSED from
this project's own toor_dal/rajma/urad_dal precedent, not a fresh
measurement, and explicitly below `protein.quality_diaas_threshold` (0.75) —
this ingredient does not count as quality protein anywhere in the system.

**Before/after, full `probe_rank_input2.py` grid** (5 templates/720 cases
before, 6 templates/864 cases after):

| | before (5 templates) | after (6 templates) |
|---|---|---|
| overall | 376/720 = 52.2% | 392/864 = 45.4% |
| `south_indian/breakfast` | 117/144 = 81.2% | 117/144 = 81.2% (identical) |
| `south_indian/lunch` | 33/144 = 22.9% (BELOW FLOOR) | 33/144 = 22.9% (identical, still BELOW FLOOR) |
| `south_indian/dinner` | 49/144 = 34.0% | 49/144 = 34.0% (identical) |
| `north_indian/breakfast` | — | 4/144 = 2.8% (NEW, BELOW FLOOR) |
| `north_indian/lunch` | 91/144 = 63.2% | 91/144 = 63.2% (identical) |
| `north_indian/dinner` | 86/144 = 59.7% (2026-08-24 south-dinner entry) | 98/144 = 68.1% |

The four templates untouched by this task are bit-for-bit identical to the
south-dinner entry's own "after" figures except `north_indian/dinner`, which
moved 86/144→98/144 between that run and this one — *[corrected 2026-09-25: wrong; this task's `aloo_paratha` caused all of it — see that date's entry]* not caused by this task
(neither `NORTH_DINNER` nor any recipe it uses was touched here); most likely
attributable to library changes landed between the two runs (R4c's
`soya_flour_defatted`/`soya_idli`, R4b's `soya_chunk_masala`). Not
investigated further here — logged, not fixed, per the "don't fix things you
notice in passing" queue rule; worth a dedicated finding if it recurs
unexplained. Overall percentage moving 52.2%→45.4% is arithmetic (averaging
in a template at 2.8% pulls the mean down), not a regression in any other
template. The exit condition (overall ≥50%, no template <30%) remains unmet:
now for three reasons instead of one (`south_indian/lunch`,
`north_indian/breakfast`, and the overall fraction itself).

**Disposition.** Landed as-is: below the 30% per-template floor, fully
documented, no bound widened to force a pass. `NORTH_BREAKFAST` is real and
loadable (added to `web/dashboard.html`'s plate picker with its low pass rate
named in the surrounding comment) — the low rankability is a known limitation
of the current 4-recipe library against this profile grid's protein/quality-
protein/fat/carb tension, not a defect to hide. Full test suite (`python -m
pytest tests/ -q -m "not web"`): 457 passed, 0 failed (up from 455; two
row-count assertions in `tests/test_ifct_loader.py` bumped 34→35 loaded rows
and 33→34 warnings for the new `moong_dal_raw` row).

## 2026-08-24 — SOUTH_DINNER added, mirrors SOUTH_LUNCH's grammar exactly (R4d, south dinner sub-task)

**What was done.** TASKS_3.md R4d as written bundled at least three distinct
new templates (North Indian breakfast, South Indian dinner, snacks for both
regions) into one task; per CLAUDE.md invariant 8 and the queue protocol, the
user was asked how to split it and chose South Indian dinner first. Added
`SOUTH_DINNER` to `core/foods/templates.py`: a `MealTemplate` for
`(Region.SOUTH_INDIAN, MealSlot.DINNER)` that deliberately mirrors
`SOUTH_LUNCH`'s five slots and categories exactly (rice_base, gravy,
vegetable, curd_course, crisp) — a South Indian family dinner is, in the
ordinary case, the same meal grammar as lunch, unlike `SOUTH_BREAKFAST`
(documented structural difference from lunch) or `NORTH_DINNER` (counted-bread
grammar, genuinely different from `NORTH_LUNCH`'s rice option). No genuine
structural difference was identified for south dinner, so none was invented;
a real one, if found later, earns its own slot list the way south_breakfast's
did. Zero new recipes or ingredients were needed — the sub-task closes using
the existing South Indian library alone. Wired into `ALL_TEMPLATES`, `__all__`,
`docs/design/probes/probe_rank_input2.py`'s `TEMPLATES` tuple (with its
docstring's hardcoded "4 templates / 576 cases" arithmetic corrected — the
per-template report lines already derived from `TEMPLATES` dynamically, so
only the prose needed fixing), the `web/dashboard.html` plate picker (a third
South Indian card, `south_indian:dinner`, matching the existing card markup;
the "these N are the only combinations" copy line updated 4→5), and
`tests/test_templates_and_portions.py` (a lookup test and a test pinning the
mirrored-grammar design choice as intentional). `tests/test_planner_plan.py`'s
per-template tests and `tests/test_recipes.py`'s category-union test both
parametrize over `ALL_TEMPLATES` already, so they picked up `SOUTH_DINNER`
with no edit needed.

**Verified the "reuses much of south lunch" premise before committing to the
design**, not after: a standalone measurement (isolated from the full probe
grid) showed `south_indian/dinner` clears the 30% per-template floor using
existing recipes alone — vegetarian 34/72 = 47.2%, vegan 15/72 = 20.8%, pooled
49/144 = 34.0%.

**Before/after, full `probe_rank_input2.py` grid** (4 templates/576 cases
before adding `SOUTH_DINNER`, 5 templates/720 cases after — not a git-stash
diff this time, since the "before" figures are the same ones already recorded
in the 2026-08-24 entry above and were re-checked for exact match rather than
re-run):

| | before (4 templates) | after (5 templates) |
|---|---|---|
| overall | 327/576 = 56.8% | 376/720 = 52.2% |
| `south_indian/breakfast` | 117/144 = 81.2% | 117/144 = 81.2% (identical) |
| `south_indian/lunch` | 33/144 = 22.9% (BELOW FLOOR) | 33/144 = 22.9% (identical, still BELOW FLOOR) |
| `south_indian/dinner` | — | 49/144 = 34.0% (NEW, clears floor) |
| `north_indian/lunch` | 91/144 = 63.2% | 91/144 = 63.2% (identical) |
| `north_indian/dinner` | 86/144 = 59.7% | 86/144 = 59.7% (identical) |

The four pre-existing templates are bit-for-bit identical before and after,
confirming isolation — `south_indian/dinner`'s addition did not perturb any
other template's combinatorics, as expected (it is a structurally separate
template sharing no recipe eligibility mechanism with the others beyond the
common library). The overall percentage moving 56.8%→52.2% is arithmetic, not
regression: averaging in a template that individually passes (34.0% > 30%
floor) but sits below the pre-existing mean pulls the mean down. The exit
condition (overall ≥ 50%, no template < 30%) is still not met, because
`south_indian/lunch` remains below its own floor — unchanged by this task,
which did not touch that template.

**A new finding surfaced while editing `web/dashboard.html` for this
sub-task, not fixed here.** `tests/test_web_no_identifiers.py`'s browser
sweep selects `south_indian:lunch` specifically because it is expected to
decline for a fixture CKD profile (weight_kg=74, height_cm=176, age=31,
vegetarian, `chronic_kidney_disease`), and asserts the decline actually
rendered. Checked live (`plan_within_ladder` invoked directly against that
exact profile and `south_indian/lunch`): **it no longer declines** —
`outcome.plan is not None`. This is the identical sodium-mechanism side
effect the 2026-08-24 entry above already found and fixed in
`tests/test_api_targets.py` (commit `b28447f`) — the same profile, in a
different test file, that commit's own repoint never touched because these
`web`-marked browser tests skip by default unless
`FOODAI_WEB_TESTS=required` is set, so the existing suite run did not surface
it. The stale comment in that test file has been corrected to state the
finding plainly rather than repeat the now-false decline claim; the test's
own fixture profile has **not** been repointed — that is a distinct
reviewable idea from the `south_dinner` template this commit is about, per
CLAUDE.md invariant 8 and the "do not fix things noticed in passing" rule.
Whoever picks this up next: repoint following the same method as the API
test's repoint above (search for a profile that still genuinely declines on
a locked CKD floor for `south_indian/lunch`), then re-run under
`FOODAI_WEB_TESTS=required` to confirm.

**Full suite**: see transcript below, run with the browser-required flag off
(per the pattern established for template-only, non-web changes; this task
did not change any behaviour the `web`-marked tests exercise beyond the
plate-picker markup, which those tests do not assert on — the stale comment
above is a data finding, not code this commit changes).

**Disposition.** Fixed (the sub-task's own goal — `SOUTH_DINNER` added,
clears its own floor, wired everywhere the template roster is consumed).
Not fixed, logged: the `test_web_no_identifiers.py` stale-decline-fixture
issue found in passing. `south_indian/lunch` remains below the 30% floor;
North Indian breakfast and snacks (both regions) remain the rest of R4d,
unstarted, per the user's explicit "South dinner first" direction.

## 2026-08-24 — soya_curd closes finding 51's vegan structural zero; south_lunch moves further than expected

**What was done.** Finding 51 (below) established that `SOUTH_LUNCH.curd_course`
is required, accepts only `curd`/`buttermilk`, and the library's sole filler,
`thayir_plain`, is dairy — so vegan `south_indian/lunch` enumerated zero
combinations, a structural zero no relaxation rung could reach. Per explicit
instruction, this was closed with one recipe, sourced with the same discipline
as R4c: `soya_curd` (`data/recipes/soya_curd.yaml`), a real South Indian dish
(fermented soymilk set into curd the same way dairy milk becomes dahi — see
e.g. "Soya milk curd", swayampaaka.com), built on a new ingredient row,
`soya_curd_plain` (`data/raw/ifct/fixture_ingredients.csv`, documented in
`data/raw/ifct/README.md`). Composition: USDA FDC 175227 "SILK Plain soy
yogurt" (energy 66 kcal, protein 2.64 g, fat 1.76 g, carb 9.69 g, fibre 0.4 g,
sodium 13 mg, calcium 132 mg — Atwater-reconciles to 64.36 kcal, 2.5% off,
inside the 15% tolerance). Iron (0.44 mg/100 g) is a named cross-product
substitution from FDC 175218 "SILK Plain, soymilk" (same brand, same "Plain"
formulation, same publication batch) because FDC 175227 carries no iron row
at all — confirmed by reading its full nutrient list, not inferred from a
blank field. No DIAAS is claimed: this ingredient exists only to fill a
required category slot for vegan diets, not to qualify as a protein source.
`verified=false`, per CLAUDE.md invariant 4 (a human, not this assistant, must
open the primary source). The template and category vocabulary were not
touched.

**Before/after, git-stash based** (same method as the R4c reconciliation
above): `probe_rank_input2.py`'s primary accepted-rung number, and a
diet-split variant restricted to `south_indian/lunch` (per explicit
instruction, since vegan and vegetarian are two different problems there):

| | before | after |
|---|---|---|
| overall (576 cases) | 286/576 = 49.7% | 327/576 = 56.8% |
| `south_indian/breakfast` | 100/144 = 69.4% | 117/144 = 81.2% |
| `south_indian/lunch` | 9/144 = 6.2% (still BELOW FLOOR) | 33/144 = 22.9% (still BELOW FLOOR) |
| `north_indian/lunch` | 91/144 = 63.2% | 91/144 = 63.2% (bit-for-bit identical) |
| `north_indian/dinner` | 86/144 = 59.7% | 86/144 = 59.7% (bit-for-bit identical) |
| `south_indian/lunch`, vegan only (72 cases) | 0/72 = 0.0% | 12/72 = 16.7% |
| `south_indian/lunch`, vegetarian only (72 cases) | 9/72 = 12.5% | 21/72 = 29.2% |

The overall figure clears the 50% exit-condition threshold for the first time.
`south_indian/lunch` itself is still below the 30% per-template floor, so the
exit condition as a whole is still not met — this task closed the structural
zero it targeted, not the floor.

**Two effects, not one — reconciled rather than taken on faith (finding 50's
rule).** The vegan column moving 0.0%→16.7% is the targeted fix and needs no
further explanation. Two effects were NOT anticipated and were traced before
being accepted:

1. **Vegetarian `south_indian/lunch` also moved (12.5%→29.2%), and every
   south_lunch reference plate now solves at rung 0** — `curd_dahi` (in
   `thayir_plain`) is 45 mg sodium/100 g; `soya_curd_plain` is 13 mg/100 g,
   under a third. Sodium was the binding constraint in this template
   (finding 50's own trace showed south_lunch landing 8.9 mg under its 1400 mg
   ceiling). The solver now prefers `soya_curd` over `thayir_plain` for the
   curd course whenever both are legal candidates — confirmed directly:
   the real-library reference plate (`tests/test_planner_quality.py`,
   `test_the_reference_lunch_now_passes_unrelaxed`) went from needing three
   relaxation rungs (`sodium_max_fibre_min`, `fat_carb_tolerance`,
   `energy_tolerance`) to zero, sodium landing at 1344.7 mg against the same
   1400 mg ceiling — this is an incidental consequence of the ingredient's
   real composition, not something aimed at.
2. **`south_indian/breakfast` also moved (69.4%→81.2%)**, despite this task
   targeting `south_lunch`: `SOUTH_BREAKFAST.curd_course` is optional and
   already accepted `thayir_plain`; `soya_curd` is now a second legal
   candidate there too, which widens the combination space directly (more
   candidates per optional slot means more distinct combinations), not
   through any sodium mechanism. Confirmed via the real-library reference
   breakfast plate, which now uses `soya_curd` for its own curd course
   (`test_the_reference_breakfast_plate_is_soya_idli_sambar_chutney`).

Both effects are logged, not folded silently into "the fix worked" — per
finding 50's standing rule that a favourable swing gets reconciled the same
way an unfavourable one would.

**A previously-declining API test stopped declining.**
`tests/test_api_targets.py::TestADeclineCarriesItsNumbersNotJustItsProse`'s
fixture profile (weight_kg=74, goal=maintain, vegetarian, CKD,
south_indian/lunch) passed with only mild relaxation after this change —
the same sodium mechanism as above. Its own comment anticipated this
("if the library grows so that it passes... must be repointed rather than
deleted"); repointed to weight_kg=55/goal=lose_fat, same other fields, which
still declines — confirmed directly: `protein_g` 29.6 g against a 34.6 g
floor, locked by the CKD clinical flag (`locked_by: chronic_kidney_disease`),
a bound relaxation cannot touch regardless of what fills `curd_course`.

**Full suite**: `PYTHONHASHSEED=0 FORCE_COLOR=0 PY_COLORS=0 python -m pytest
tests/ -q -m "not web"` — 449 passed, 0 failed, run after the stash
round-trip completed (working tree restored via `git stash apply`, never bare
`pop`, entry dropped after confirming restoration).

**Disposition.** Fixed. One recipe, one ingredient row, no template or
category vocabulary change. `south_indian/lunch` remains below the 30% floor;
R6 already established (below) that no further serving-range widening is
honestly available, so closing that floor fully would need either a new
recipe/ingredient reaching a currently-thin category, or a deliberate
decision to accept the floor as currently unreachable for this template.

## 2026-08-22 — R4c reconsideration: a large favourable swing, checked this time before moving on

**What happened.** TASKS_3.md R4c ("a vegan-safe qualifying protein source")
added `soya_flour_defatted` (DIAAS 1.05, sourced from Mathai, Liu & Stein 2017,
Br J Nutr 117:490–499, DOI 10.1017/S0007114517000125) and a new recipe,
`soya_idli`, reaching `SOUTH_BREAKFAST.tiffin_item` — the required slot
finding 25 named as the one no south-breakfast dish could carry a
high-quality protein source in. `probe_rank_input2.py`'s primary
(accepted-rung) exit-condition number moved from 39.6% (228/576) to 49.7%
(286/576), entirely on `south_indian/breakfast`: 29.2% (42/144) → 69.4%
(100/144).

**Why this entry exists at all, given the number moved the right way.**
Finding 50 (below) is the standing correction: "reconsider the queue" is
unconditional, not a check that gets skipped once a metric clears some
threshold in the favourable direction. A +20-point swing on one template is,
if anything, a LARGER move than finding 50's own +12.0 that triggered the
correction — so it was reconciled properly rather than taken on faith,
per that correction.

**How it was reconciled** (not just asserted):

1. Re-ran `probe_rank_input2.py` against the exact pre-R4c tree, by
   `git stash push -u` on the R4c changes, re-running the probe, then
   `git stash apply` (never bare `stash pop`, per this session's own
   worktree-safety rule) to restore them. Baseline: overall 39.6%,
   `south_indian/breakfast` 29.2%, `south_indian/lunch` 6.2%,
   `north_indian/lunch` 63.2%, `north_indian/dinner` 59.7% — matching the
   standing numbers TASKS_3.md already recorded before this task, confirming
   the stash round-trip reproduced the right state.
2. Compared template-by-template: `south_indian/lunch`, `north_indian/lunch`
   and `north_indian/dinner` are BIT-FOR-BIT IDENTICAL before and after (9/144,
   91/144, 86/144 respectively, both runs) — expected, since R4c touched no
   recipe or ingredient reachable by those templates' categories. Only
   `south_indian/breakfast` moved, and only in the direction the new recipe's
   mechanism predicts.
3. Traced the mechanism directly, not just the aggregate count: solved the
   real reference profile's `south_breakfast` plate before and after. Before:
   idli + soya_kuzhambu + coconut_chutney + thayir_plain, quality protein
   17.495 g (needs the curd course to clear the floor). After: soya_idli x6 +
   sambar x2 + coconut_chutney x3, quality protein 12.3504 g — all of it from
   `soya_idli`'s own soya flour, no curd or kuzhambu needed. Disqualifying
   `soya_flour_defatted` alone (DIAAS forced to 0.50) reverts the solved plan
   to the exact pre-R4c plate and figure (17.495 g) — confirms the swing is
   this ingredient's effect and nothing else, the same before/after-DIAAS
   perturbation `TestThePerturbationTest` already required of the rule itself.
4. Ran the full suite (`PYTHONHASHSEED=0 FORCE_COLOR=0 PY_COLORS=0 python -m
   pytest tests/ -q -m "not web"`) after restoring: 449 passed, 0 failed,
   confirming no other template's tests regressed.

**Disposition.** No correction needed this time — the swing is real, isolated
to the template the task targeted, and traced to a specific, reversible
mechanism. Logged as a worked example of finding 50's rule applied
successfully, not as a new defect.

## 2026-08-22 — finding 51: south_indian/lunch's 6.2% has two separate causes, neither an R4d problem

**What was investigated.** Per this session's own reconsideration step after
R4c, `south_indian/lunch` is now the only template below TASKS_3.md's 30%
floor (6.2%, 9/144). The next queued task, R4d, is scoped to MISSING meal
types (North breakfast, South dinner, snacks) and does not touch this
template at all, so before doing R4d the queue was checked for whether it
should be reordered — not reshaped silently, reported here instead.

**Finding, part 1 — vegan south_lunch is a hard structural zero, not a
rankability problem.** `SOUTH_LUNCH.curd_course` is REQUIRED
(`accepted_categories={"curd", "buttermilk"}`, `templates.py`), and the only
recipe in either category, `thayir_plain`, is dairy. There is no
`buttermilk`-category recipe in the library at all. Built the candidate pool
for `south_indian/lunch` under `DietPattern.VEGAN` directly: **0 combinations
enumerate**, for every vegan profile, unconditionally — not a bound failure,
not a declined plan, the template cannot be assembled at all. This alone caps
`south_indian/lunch`'s achievable rankability at 50% (72 of 144 profiles are
vegan) regardless of anything else the library does.

**Finding, part 2 — among vegetarian profiles, the real blocker is the
solver's integer counts, not missing recipes.** A bound-reachability check
(same `broken_bounds` logic `probe_blocking_bounds.py` and the R4b diagnostic
use — continuous macro bounds, no integer-count search) found 70 of 72
vegetarian `south_indian/lunch` profiles have a combination with **no broken
bound at all** at the ladder's own accepted target. But
`probe_rank_input2.py`'s real number — which additionally requires
`core.planner.solver.solve` to find a legal INTEGER unit-count assignment —
counts only 9 of 144 (all vegetarian, since vegan is structurally 0) with
>= 2 such plates: roughly 9/72 ≈ 12.5% of the profiles a bound-only check
says should pass 97% of the time. That gap is the signature TASKS_3.md's own
R6 task names: "512 combination-instances cleared the O(1) feasibility filter
and were still rejected by the solver — no whole number of servings lands
inside the bounds. More recipes do not fix these." `south_indian/lunch` looks
like exactly the template R6 was written for, not a recipe-library gap.

**Why this is not an R4-shaped fix.** `south_indian/lunch`'s pool is thin
(2 rice/mixed-rice, 4 gravy, 2 vegetable, 1 curd — for vegetarian; 0 curd
options for vegan) but bound-reachable at close to full rate already; the
scarce resource here is INTEGER-count solvability and a vegan curd/buttermilk
substitute, neither of which "add one more recipe of the type R4a/b/c added"
addresses on its own.

**Disposition.** Not fixed here — reported per this session's queue
protocol rather than reshaped into new work. Two candidate next tasks, not
yet queued: (a) R6 as already specified, now with `south_indian/lunch` as a
concrete, measured target case; (b) a vegan-safe buttermilk/curd substitute
recipe for `SOUTH_LUNCH.curd_course`, structurally required before vegan
`south_indian/lunch` can ever pass regardless of (a). Left for a human
decision on ordering, per this task's own "investigate south lunch first"
instruction — not carried further without direction.

---

## 2026-08-22 — R6: the serving-granularity gap is real, current, and not honestly recoverable

**What was measured.** `docs/design/probes/r6_serving_granularity_gap.py`
(committed), same 144-profile x 4-template grid every other probe here uses.
For every combination that survives `feasible_combinations` (the O(1) bound
pre-filter) but `solve_combination` rejects at every legal integer count —
the exact gap TASKS_3.md's R6 text names — the probe tries widening ONE
component's `max_count` by +1, or its `min_count` by -1, in isolation
(`dataclasses.replace` on a throwaway copy, never touching a recipe file), to
see whether the smallest possible widening would let the solver succeed.

**The number itself has grown, and that is expected, not a regression.**
TASKS_3.md's R6 text cites 512 gap-instances. Re-measured on today's library
(after R3a/R3b/R4a/R4b/R4c and R1a's ingredient-class model, none of which
existed when 512 was recorded): **2093**. More recipes and more profiles that
can now reach further templates mechanically enumerate more combinations,
and more of those combinations sit in the bound-feasible-but-unsolved gap —
consistent with finding 51's own observation that `south_indian/lunch`'s
bound-reachable rate (70/72) vastly exceeds its solved rate, and that this
specific gap is what R6 was written to explain.

**Recoverable, mechanically: 93 of 2093 (4.4%).** Only by widening one of
five recipes' ranges: `soya_chunk_curry` (43), `soya_idli` (36),
`onion_raita` (8), `soya_kuzhambu` (5), `thayir_plain` (1). Lowering a
`min_count` by 1 recovered nothing anywhere — the gap is entirely a ceiling
problem, not a floor one.

**Recoverable, honestly: 0 of 2093.** Every one of the five recipes above
already carries an EXPLICIT, PRIOR reason its current ceiling must not move,
written into its own file before this investigation and for reasons that had
nothing to do with solver granularity:

- `soya_chunk_curry.yaml`, `soya_kuzhambu.yaml`: "a katori of this carries
  roughly [two/three] times the protein of a katori of [dal/sambar], so the
  same ceiling would hand the solver [four/three] times the room to close a
  protein gap by volume."
- `onion_raita.yaml`: "a plate carrying three katoris of it is one the
  solver invented to reach a protein floor, not one anyone was served."
- `thayir_plain` (`thayir_sadam_curd.yaml`): "curd is the one component here
  the solver could otherwise use to answer protein cheaply... three katoris
  of curd is not how the meal ends."
- `soya_idli.yaml`: "Six is a large breakfast and an ordinary one" — a real
  portion-size judgment, not a solver accommodation; a seventh is not.

Widening any of the five for this task would be exactly what TASKS_3.md's own
standing rule forbids: "Never adjust a threshold, bound or serving range
**for the purpose of** making the planner pass." Each was already reasoned
about once, independently of R6, and each reasoning still holds.

**Disposition.** No recipe file changed. "Very little is recoverable" —
TASKS_3.md's own stated acceptable answer — is the honest one, and in this
case it rounds down further, to zero. The gap (2093 instances, concentrated
in combinations built around `soya_chunk_curry`/`soya_chunk_masala`/
`soya_kuzhambu`/`masala_dosa` — dishes the solver keeps stretching toward a
protein floor) is a real, current, and apparently structural property of this
library's serving-unit design, not a coarse-graining bug to fix.

---

---

## 2026-08-20 — finding 50: a large probe-metric swing was used to skip the queue's own reconsideration step

**What was claimed**, in the chat report and commit message for R4b
(`7338e35`, `soya_chunk_masala`): the probe-gate jump (+12.0 points,
27.6% -> 39.6%, well past `TASKS_3.md`'s "less than 3 points, stop and
reconsider" line) was read as license to skip reconsidering the queue
before starting R4c — "not stopping to reconsider the queue's shape as a
result, per the standing rule (a task that moves the number by a lot is
grounds to continue, not pause)."

**Why that is wrong.** `TASKS_3.md`'s own protocol text (quoted in root
`CLAUDE.md`) requires "reconsider the queue" after **every** task,
unconditionally. The 3-point line is a trigger for one specific failure
mode — a task that moved nothing, which is itself grounds to stop and ask
whether the work was pointed at the right thing. It says nothing about the
opposite case. Treating "the number moved a lot in the direction I wanted"
as a substitute for the reconsideration step it was never conditioned on
is the same shape of error as reading a large p-value as proof of the null:
a big favourable swing is exactly when a real mechanism might be doing
something surprising, which is a *stronger* reason to check what changed,
not a weaker one. Caught by the user, not found internally, before any
further task was started.

**Checked, not just corrected in prose.** `soya_chunk_masala`'s own probe
delta (recorded in `7338e35`'s commit message) showed `fat_g_ceiling`
sole-cause count nearly doubling (284 -> 568) at the same time the phase
gate improved sharply, and that was flagged as "probably inert enumeration-
space noise" without checking whether it was actually blocking any
profile. Checked directly here: comparing `north_indian/lunch` +
`north_indian/dinner` decline counts with and without
`soya_chunk_masala.yaml` in the library (288 (profile, template) cases
each side, `soya_chunks_masala` moved out of `data/recipes/` and back for
the "before" run) —

  BEFORE: 25 declines. Sole/joint reasons: quality_protein_g:below_floor
  (7), protein_g:below_floor (6), fat_g:below_floor (4),
  fat_g:above_ceiling + sodium_mg:above_ceiling (3), three more at 1 each.

  AFTER:  12 declines. fat_g:above_ceiling + sodium_mg:above_ceiling: still
  exactly 3 — the same combinations, not new ones. fat_g:below_floor: 0
  (fixed). quality_protein_g:below_floor: 0 (fixed, as a side effect —
  soya_chunk_masala's larger soya-chunk mass also qualifies). protein_g:
  below_floor: 8, up from 6 — the one wrinkle, not chased further here.

So the raw `fat_g_ceiling` sole-cause count rising WAS inert with respect
to actual declines, as guessed — but it was a guess stated as settled
before this check existed, and the guess could have been wrong. The
`protein_g:below_floor` count rising from 6 to 8 is a real, small, new
wrinkle this recipe introduced and is left here, unfixed, for whoever
picks up R4c to be aware of rather than surprised by.

*Disposition:* OPEN as a standing-discipline note (not a code defect): the
"reconsider the queue" step is not conditional on the size or direction of
a probe-metric move. `protein_g:below_floor`'s 6 -> 8 rise is OPEN as a
minor, unchased finding.

---

## 2026-08-15 — finding 49: R1b's D1/D2 "isolated from each other" claim was wrong in one direction

**What was claimed** (commit `e9b4aa7`, R1b, and the chat report alongside it):
D1 (the jain dairy-sourcing gate) and D2 (the permitted-class subset check)
were reported as symmetrically isolated — "a mutation that deletes the gate
… fails these without touching TestDietPatternPermittedClassTable", and in
the chat summary, "Deleting the sourcing gate fails all 3
TestDairySourcingGate tests; the class-table tests stay green." The commit
message's own transcript technically avoided the false statement (it listed
which five of six class-table rows stayed green without naming jain, rather
than saying "the class-table tests stay green" outright) but nothing said
plainly that the sixth row — jain — did not stay green. Read at normal
speed, both the commit and the chat report land as a stronger, false claim:
full symmetry.

**What's actually true**, re-verified by hand (mutate, run, read the whole
failure list, revert — not just the harness's first-covering-test report):

```
$ python - <<'PYEOF'   # mutate D1: delete the gate's if-block in
                        # core/schemas/common.py
...
mutated D1
PYEOF
$ python -m pytest tests/test_planner_candidates.py -q
...
FAILED tests/test_planner_candidates.py::TestDietPatternPermittedClassTable::test_permitted_class_table_is_enforced_and_pool_is_non_empty[jain]
FAILED tests/test_planner_candidates.py::TestDairySourcingGate::test_synthetic_unverified_dairy_is_blocked_though_the_class_table_permits_it
FAILED tests/test_planner_candidates.py::TestDairySourcingGate::test_gate_blocks_a_pool_candidate_the_class_table_alone_would_admit
FAILED tests/test_planner_candidates.py::TestDairySourcingGate::test_real_curd_dish_is_blocked_from_jain_by_the_gate_not_the_class_table
4 failed, 20 passed
```

Deleting D1 fails **four** tests, not three: all of `TestDairySourcingGate`,
plus `TestDietPatternPermittedClassTable`'s jain-parametrized case. That
row's expected survivor set (`{"plain", "dairy_verified"}`, excluding
`"dairy_unverified"`) is correct only because of D1 — the synthetic matrix's
`dairy_unverified`/`dairy_verified` split makes the jain parametrization
depend on both mechanisms at once. This is not a flaw in the gate or a
flaw in the class table; it is a coupling in one fixture's one row that the
original report did not check for and then reported the opposite of.

Deleting D2 remains cleanly isolated — re-confirmed the same way: 7 failures
(`TestHardFilters::test_diet_pattern_excludes_a_dairy_recipe_from_vegan` +
all six `TestDietPatternPermittedClassTable` rows/tests), none of them in
`TestDairySourcingGate`. So the asymmetry is real and specific: D2 → D1's
tests is a clean cut; D1 → D2's tests is not, on exactly one of six rows.

**Why this happened.** The commit-message transcript was constructed by
listing which named tests failed and then summarizing — the summary
("class-table-only tests … stay green") silently dropped jain from the
"stays green" list without saying it didn't, which reads as an omission an
inattentive author would not themselves notice was doing rhetorical work.
The chat report compressed further and lost the hedge entirely. Neither
was a fabricated transcript — the underlying pytest output was real and
included in the commit — but the prose summarizing it overclaimed.

**Fix applied**, this entry's own commit: corrected the docstrings in
`tests/test_planner_candidates.py` (module comment above
`TestDietPatternPermittedClassTable`, and `TestDairySourcingGate`'s class
docstring) and the two comments in `docs/design/probes/d4b_mutations.py`
(`SCHEMAS_COMMON`'s definition, and its `OWN_TESTS` entry) that repeated the
symmetric-isolation claim, so a reader hitting the code directly gets the
corrected version, not just this log entry.

*Disposition:* CLOSED — corrected in place, not amended out of history. The
underlying tests, mutation rows, and R1b result are unchanged and still
good: D1 and D2 are each still proven load-bearing, D2's isolation is clean,
and D1's near-isolation (three dedicated tests plus one shared row) is now
stated accurately instead of rounded up to "independent."

```
$ python -m pytest tests/ -q -m "not web"
449 passed, 69 deselected, 1 warning in 111.87s (0:01:51)
```

---

## 2026-08-14 — R1a: ingredient classes replace hand-listed diet patterns; finding 48 raised

**Task:** `TASKS_3.md` R1a. `Ingredient.is_animal_product`/`jain_safe` were
parsed and read by nothing; `Recipe.diet_patterns` was a hand-listed
whitelist that no recipe ever populated with `eggetarian` or
`non_vegetarian`, so both patterns returned zero candidates in every slot.
Replaced with `IngredientClass` (`dairy`, `egg`, `fish`, `poultry`,
`root_vegetable`) declared per ingredient, a recipe's eligibility derived as
the union of its ingredients' classes, and a per-`DietPattern` permitted-class
table (`core.schemas.DIET_PATTERN_PERMITTED_CLASSES`,
`diet_pattern_permits`). Added `DietPattern.PESCATARIAN` (mechanism only, not
in the web diet picker). Migrated all 17 recipes and all 29 fixture ingredient
rows; removed `is_animal_product`/`jain_safe` (fields, CSV columns, loader
lines) entirely.

### Finding 48 — derivation is more honest than the hand-listed field it replaced, which broke a stated verify clause — found, not fixed

R1a's verify clause required `vegetarian`/`vegan`/`jain` `demo.py` output to be
byte-identical before/after. The first pass (class-union derivation only)
was **not** byte-identical for jain: `thayir_sadam_curd.yaml` (`thayir_plain`,
plain curd) became jain-eligible, unblocking `south_lunch`'s `curd_course`
required slot. The recipe's own pre-R1a comment admits why: *"jain-safe by
ingredient, but not declared jain — the file makes no claim either way about
the dairy sourcing that would decide it."* The old hand-listed
`diet_patterns: [vegetarian]` field simply never said jain, which was a real
gap in what the data claimed to know, not a fact about the dish — and the
class-only derivation, correctly, could not reproduce a gap it has no
representation for.

Resolution (not a workaround, a model addition): jain eligibility for dairy is
not "dairy is a permitted class" but "dairy is permitted, conditional on
sourcing, and sourcing is presently unresolved for every dairy row in the
library." Added `Ingredient.dairy_sourcing_verified: bool = False` — meaningful
only where `IngredientClass.DAIRY in classes`, `False` on every row including
`curd_dahi`, and checked in `diet_pattern_permits` so a recipe with an
unverified-sourcing dairy line cannot read as jain-eligible regardless of the
class table. With every row defaulting `False`, this reproduces the original
jain exclusion of `thayir_plain` — same output, but because the model now
states an unresolved question explicitly, not because a hand-listed field
happened to omit it. Full writeup: `docs/methodology.md`, "Dairy sourcing for
jain eligibility."

*Disposition:* **found, not fixed**. The gap in what the data claims to know
about dairy sourcing (jain-relevant) predates R1a and remains open — this
entry documents that it is now representable and honestly defaulted, not that
it is resolved. Resolving it needs a human to identify or adopt a named
sourcing standard for the fixture set's two dairy rows and flip the flag with
a `source_note`; nobody has done that.

```
$ diff -rq /tmp/r1a_verify/before /tmp/r1a_verify/after2
(no output — byte-identical: vegetarian, vegan, jain across
 south_indian/breakfast, south_indian/lunch, north_indian/lunch,
 north_indian/dinner, and library listings)

$ python -m pytest tests/ -q -m "not web"
439 passed, 69 deselected, 1 warning in 106.45s (0:01:46)
```

(The `-m "not web"` deselection is pre-existing and out of scope: `git diff
--stat HEAD -- web/` shows zero files touched by this task, and R1a explicitly
excludes UI changes. Un-marked-web suite is fully green.)

*Disposition:* CLOSED (R1a itself). Finding 48 above stands OPEN as a
separate, narrower item.

---

## 2026-08-12 — CLAUDE.md restructured to 199 lines; six stale claims corrected

`CLAUDE.md` went from 652 lines to **199**. No behaviour changed: `437 passed,
68 skipped` before and after, and `demo.py`'s plate, unit counts, point estimate
and band are identical.

New files: `docs/design/architecture.md`, `docs/design/round4_addendum.md`,
`docs/repo_policy.md`, `docs/build_status.md` (the build table, moved by
extraction rather than retyping), and directory-level `core/CLAUDE.md`,
`web/CLAUDE.md`, `tests/CLAUDE.md` — which now carry the **open-findings index**,
so a session meets the findings for the code it is editing rather than having to
know to look. `docs/methodology.md` gained an appendix for the three rules that
already had a section there.

### Six stale claims corrected on the move — not carried across

The rule applied: nothing moves verbatim without being read against this file
first. Recorded here because five of the six had been true when written and
quietly stopped being true, which is the class the restructure was most likely
to launder into a fresh-looking home.

1. **`web/` described as "Next.js"** in the architecture tree. It is static
   HTML/CSS/JS and always has been in this repo; the build-status table 20 lines
   below said so. Corrected in `docs/design/architecture.md`.
2. **Pipeline steps 5 and 6 (LLM ranking, narration) read as built.** They are
   specification. Marked not-built.
3. **The round-4 addendum's five items read as an outstanding queue.** All five
   are built. Each now carries a dated status line; carried across unchanged the
   file would have presented finished work as a TODO list.
4. **The audit-workflow section described `.claude/agents/auditor.md` and
   `.claude/commands/grill.md` in the present tense** while the build table
   recorded that they do not exist. Re-verified: `.claude/` has neither
   directory. Rewritten in `docs/repo_policy.md` with the gap stated first.
5. **The uncertainty filter claimed a conservative-estimate arm that does not
   exist.** `CLAUDE.md` said an over-ceiling recipe is excluded "**or** its
   contribution estimated conservatively (high-end)". `core/planner/candidates.py`
   either excludes the candidate or, in `dev_mode`, keeps it and records an
   `EligibilityFlag`. There is no conservative-estimate path and no evidence
   there ever was. The clause was dropped, not transcribed.
6. **`docs/methodology.md`'s own "What is not built" section had gone stale** —
   it listed `api/`, `web/` and `core/nutrition/targets.py` as unbuilt. All three
   exist. The Phase 3 text is retained as dated evidence, behind a correction.

Separately, the **15% shipping threshold** was moved with a correction attached
rather than a rewrite: it is stated as though it were the operative gate, and
finding 43 established that the protein eligibility ceiling bites first, at
pool-build time, on all four reference plates. The threshold is retained as the
rule it is; it is not what stands between this library and a servable plate.

### Finding 47 — code comments cite `CLAUDE.md` sections that have moved — **OPEN**

Roughly 20 comments across `api/`, `core/foods/` and `core/nutrition/` cite
`CLAUDE.md` by section name — "Uncertainty", "Architecture", "round-4 addendum",
"Relaxation ladder", "'wider tolerance on energy'". Those sections are now in
`docs/methodology.md`, `docs/design/architecture.md` and
`docs/design/round4_addendum.md`. The rules are unchanged and the citations still
date a decision correctly, so nothing is *wrong*; they just point at a file that
no longer contains the named section.

Not fixed in this pass, deliberately: the task protocol says do not fix things
noticed in passing, and a 20-file comment sweep is its own reviewable idea, not
a rider on a documentation restructure.

One exception was fixed, because it is user-visible rather than a comment:
`demo.py` printed `-- CLAUDE.md's shipping threshold is ~15%` on every run, and
`CLAUDE.md` no longer states that threshold. Changed to `-- the shipping
threshold is ~15%`. The number and the check are untouched.

*Disposition:* OPEN. Low stakes; do it as a single sweep when someone is next in
those files anyway.

```
$ python -m pytest tests/ -q
437 passed, 68 skipped, 1 warning in 110.17s (0:01:50)

$ wc -l CLAUDE.md
199 CLAUDE.md
```

---

## 2026-08-09 — D12: finding 44 FIXED, findings 45 and 46 raised, finding 41 re-scoped

**D12's premise was partly wrong, and the measurement is the deliverable.** The
task read: "the three cooked-but-process-silent recipes (`idli`, `phulka`,
`steamed_rice`) stop deriving their uncertainty from
`process.unassessed_uncertainty`", expecting three new registered constants.
Two of the three need constants. The third needed the opposite — it had been
over-charged — and finding it took asking *why* each zero was zero rather than
counting the zeros.

### Finding 41, re-scoped with the arithmetic it was missing — still **OPEN**

Finding 41 measured protein process uncertainty = 0.0 on 15 of 18 recipes and
inferred a library-wide fake zero. The count is right; the inference is not. A
line derives no process uncertainty for three different reasons:

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d12_process_attribution.py

  Library protein, by why its process uncertainty is zero:
      ATTRIBUTED          0.0 g  ( 0.0%)   line carries a process: key
      SERVED-BASIS       80.6 g  (65.2%)   row already describes the food as eaten
      UNATTRIBUTED       43.0 g  (34.8%)   raw-basis row the recipe cooks  <-- finding 41
```

Two thirds of the library's protein arrives on `cooked`- or `as_used`-basis
rows — `rice_cooked`, `toor_dal_cooked`, curd, paneer, tofu. The recipe applies
no transformation to those, so no process step went unmeasured and the zero is
earned; the doubt that remains is doubt about the row, already charged at 0.25
composition. Finding 41 is the other 34.8%, and it is concentrated rather than
spread: `soya_chunk_curry` 98.1%, `soya_kuzhambu` 94.7%, `carrot_poriyal`
90.1%, `coconut_chutney` 89.9%, `masala_dosa` 82.4%, against `rajma_chawal`
2.6% and `dal_tadka` 3.6%.

The largest single item is `soya_chunks_dry` — 14.6 g of protein on a dry-basis
row rehydrated and simmered, with no rehydration constant registered. It is also
the only vegan-eligible row clearing the DIAAS quality threshold, so the rule
that decides vegan plates rests on a row whose cooking transformation is
entirely unquantified.

*Disposition:* OPEN, and now costed. Closing it needs registered constants for
rehydration, sauteing/simmering, steaming and dry-griddling — four, not the one
"cooking loss" the finding implied. Queued as D13.

### Finding 44 — D10 charged a recipe for a transformation it does not perform — **FIXED**

`steamed_rice` is one ingredient line: 200 g of `rice_cooked`, a **cooked-basis**
composition row. D10 put it in the same population as `idli` and `phulka` and
made it declare all nine macros `process_uncertainty_unassessed`, reasoning
that "boiling is still a cooking step whatever the basis the composition row is
stated on."

That sentence is true about rice and false about this file. The boiling happened
before the composition record was made. The recipe names a portion of an
already-boiled food; it transforms nothing. So the 0.20 was charged on top of
the 0.25 composition band that already covers whether the cooked row is right —
the same quantity counted twice, and D10's own probe could not see it because it
asked whether a `process:` key existed, not whether anything needed one.

The loader now earns those zeros structurally: **a macro fed by no raw-basis
line needs no justification.** Keyed off `Ingredient.state`, the composition
record's own basis, and deliberately not off `RecipeIngredient.state` — see
finding 46.

Measured, south_lunch (the plate `steamed_rice` sits on):

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python demo.py plan --region south_indian --meal-slot lunch
  unit counts  : {'steamed_rice': 1, 'soya_kuzhambu': 2, 'carrot_poriyal': 2, 'thayir_plain': 1}
  relaxation   : ('sodium_max_fibre_min', 'fat_carb_tolerance', 'energy_tolerance')
  point        : 848.1 kcal, 40.4g protein, 29.3g fat, 107.4g carb, 1391.1mg sodium
  energy band  : 622.9 - 1073.4 kcal        [was 570.9 - 1125.4]
```

Plate, unit counts, point estimate, sodium, rungs and verdict all unchanged —
only the displayed band, which is the expected shape and not a lucky one: the
validator gates on the point estimate and intervals are display-only. The
arithmetic behind the before-column: `steamed_rice` is 260.0 kcal at one cup,
D10 charged 0.20 of that as process half-width = 52.0 kcal each side.

The three micronutrients `steamed_rice` declared unassessed **before** D10
(`iron_mg`, `calcium_mg`, `b12_ug`) are kept, at the original author's judgment
rather than the loader's requirement — draining boiled rice leaches minerals,
and whether a hand-entered cooked row accounts for that is genuinely unknown.
Free, too: none of the three has a target anywhere in the system.

And it moves a plate. From `d7b_after_verification.py`, re-run:

```
  2 of 18 recipes remain protein-ineligible after full composition verification:
      idli, phulka
  south_breakfast    BLOCKED by idli
  south_lunch        enumerable          <-- was BLOCKED by steamed_rice
  north_lunch        BLOCKED by phulka
  north_dinner       BLOCKED by phulka
```

So finding 43's count improves from four blocked plates to three, without a
single new constant — because one of the four was never blocked by a real gap.

**Four D10 assertions went red and all four were right to.** In
`tests/test_nutrition_of.py::TestEligibilityConsequence`, both tests turn on a
`NO_OIL_COOKED` tuple whose name was already the wrong generalisation: what
separates that population is not "cooks without oil" but "cooks a **raw-basis**
row with no constant describing the step". `steamed_rice` left the tuple, and
`test_verifying_every_row_clears_the_ceiling_for_all_but_three_recipes` is now
`..._for_all_but_two_recipes`. Its `len(cleared) == len(library.components) - 3`
became `- len(self.NO_OIL_COOKED)`: the literal encoded a population size that
changed one commit later, which is the second time in two sessions a hard-coded
count outlived the fact behind it.

In `tests/test_recipes.py`:
`test_silence_is_rejected_because_it_is_the_cheapest_path` built its probe from
`rice_cooked`, which is now legitimately earned, so the test would have passed
without exercising anything it names — its base is now a raw-basis line, and the
reason is a comment on `_RAW_LINES`. `test_the_real_library_no_longer_confuses_raw_with_unmeasured`
asserted all three recipes carry the wide band; it now names three populations
(cooked-from-raw, cooked-from-served, uncooked) with the split stated.

**One condition became dead and was removed rather than left.** D10 filtered
"a macro the dish contains none of" as `getattr(total, macro) != 0`. Nutrient
values are non-negative, so `from_raw[m] > 0` implies `total[m] > 0`: the old arm
is strictly subsumed. Keeping both would leave a condition no input can reach on
its own, which the next sweep would correctly report as untested. R5's row is
edited to the new line rather than retired — same mechanism, same test.

### Finding 45 — four registered constants are load-bearing for nothing, and a `source_note` claims a derivation that does not hold — **OPEN**

The obvious fix for finding 41 was to declare the already-registered yield
constant on each cooked-basis line: `process: yield.rice_milled_boiled` on
`rice_cooked`, and so on. It is wrong, and checking why turned up something
worse.

`RecipeIngredient.process_key` is documented as the constant that *determined
this line's quantity*. Each cooked row's `source_note` says a yield factor
"connect[s] the two" — so if `cooked == raw / yield`, the claim would hold.

```
  cooked row         macro           stated  raw/yield   ratio
  rice_cooked        energy_kcal     130.00     118.80   1.094   <-- does not follow
  toor_dal_cooked    protein_g         7.00       8.68   0.806   <-- does not follow
  rajma_cooked       carb_g           22.80      27.16   0.840   <-- does not follow
  potato_boiled      energy_kcal      87.00      71.22   1.221   <-- does not follow
```

None of the four is its raw row divided by its yield factor; the worst gap is
22%. They are independent hand-entered approximations and the note is a
navigational cross-reference, not a derivation. Declaring the constant would
attach a real, registered, correctly-graded figure to a line whose number did
not come from it — the mechanism-mismatch failure `CLAUDE.md`'s `phenomenon`
field exists to prevent, committed in the process axis instead of the citation
axis, and undetectable by every automated check the registry performs.

Two things follow, neither fixed here. **(a)** All four `yield.*` constants are
registered, graded and used by nothing: no code multiplies by them, no line
derives from them. **(b)** The `source_note` on four ingredient rows asserts a
relationship the numbers do not satisfy — the same defect already caught once on
`salt_iodised`, where a measured figure sat under a note claiming a
stoichiometric derivation (corrected 2026-07-31).

*Disposition:* OPEN. Logged and left per the queue rule. The honest repair is
either to derive the cooked rows from the raw ones at load time — which is the
round-4 "no nutritional number may be hand-duplicated" rule applied to a place
nobody has applied it — or to rewrite four notes to stop claiming a connection
that is not there. That is a decision, not a typo fix.

### Finding 46 — a recipe line's declared `state` is never checked against the row it points at — **OPEN**

`RecipeIngredient.state` is author-declared. `models.py` has a branch for it:

```python
if self.state is RawOrCooked.RAW:
    # Not forbidden outright — a raw-basis line is legitimate for
    # something eaten raw — but it must be a deliberate choice, so the
    # loader records it rather than letting it look like an oversight.
    pass
```

The comment says the loader records it. Nothing records it, and nothing compares
`line.state` against `ingredients[line.ingredient_id].state`. A line may declare
`state: cooked` over a raw-basis composition row with no complaint.

This was load-bearing for finding 44's fix and is why that fix reads the
ingredient's state: had it read the line's, writing `state: cooked` over a raw
row would have become the cheapest way to earn a full set of zeros — this
check's own failure mode, reintroduced by its own repair.
`test_calling_a_raw_row_cooked_on_the_line_does_not_earn_the_zeros` pins that,
and mutation R7 grades it.

*Disposition:* OPEN. Harmless today only because nothing reads `line.state` for
any decision. A comment asserting behaviour that does not exist is the same
class as the notes in finding 45.

### Deletion coverage, and why the sweep's own answer was not taken at face value

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py R1,R2,R3,R4,R5,R6,R7
R1   covered  ...::test_silence_is_rejected_because_it_is_the_cheapest_path
R2   covered  ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R3   covered  ...::test_an_unknown_preparation_is_rejected_rather_than_assumed
R4   covered  ...::test_an_uncooked_dish_may_not_also_name_a_process
R5   covered  ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R6   covered  ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R7   covered  ...::test_calling_a_raw_row_cooked_on_the_line_does_not_earn_the_zeros
7 mechanisms: 7 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

R5 and R6 both name `test_mutating_a_constant_moves_every_recipe_that_depends_on_it`,
which is not the test written for either — the exact shape `CLAUDE.md` records
from D6, where a `covered` row named the *first* scoped failure in collection
order rather than the relevant one. Taking the full failure list per mutation by
hand, as that lesson requires:

```
R6 (delete the served-basis path):
  FAILED ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
  FAILED ...::test_a_served_basis_row_earns_its_zeros_without_declaring_anything
  + 26 errors — steamed_rice stops loading, so the shared library fixture dies

R5 (delete the from_raw filter):
  FAILED ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
  FAILED ...::test_a_macro_the_dish_contains_none_of_needs_no_justification
  FAILED ...::test_a_served_basis_row_earns_its_zeros_without_declaring_anything
  + 26 errors, same cause
```

Both mechanisms are red on their own test. The alphabetically-earlier name is a
real failure too, not a false positive — it is simply not the test anyone editing
that mechanism would look at. Also worth noting for the next sweep: unlike D10's
R3/R4/R5, mutations R5 and R6 are now graded by the **real library** as well,
because `steamed_rice` no longer declares its way past the check and a deleted
served-basis path rejects it at load.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d12_process_attribution.py
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_after_verification.py
PYTHONHASHSEED=0 PYTHONPATH=. python demo.py plan --region south_indian --meal-slot lunch
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py R1,R2,R3,R4,R5,R6,R7
```

---

## 2026-08-09 — D7 handoff: finding 43, and what D10 did to D7's own conclusion

No code changed. Three artifacts added — `docs/design/ifct_sitting.md`,
`docs/design/ifct_transcription_worksheet.csv`,
`docs/design/probes/d7b_after_verification.py` and
`docs/design/probes/d7b_transcription_diff.py` — so the one task in this project
that no automation can perform is one mechanical session rather than an open
question.

### Finding 43 — verifying every ingredient row cannot make any current plate servable — **OPEN**

`docs/design/probes/d7_verification_horizon.py` was written to answer, *before*
a human spends hours with IFCT 2017 open rather than after, whether verifying
the north_lunch ingredient rows would clear the ~15% unverified-energy shipping
threshold. It answered **INGREDIENTS 9.5% → SHIPS**.

That probe ran before D10. D10 gave `idli`, `phulka` and `steamed_rice` a
`process_uncertainty_unassessed` declaration on every macro, mapping to
`process.unassessed_uncertainty` = 0.20 — and D7's conclusion measures the
*second* of two gates while D10 moved the *first*.

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_after_verification.py
Protein eligibility band per recipe, against the 0.15 ceiling
(counterfactual assumes every composition record verified at 0.05 -- the best the sitting can buy)

  recipe                 comp   proc   TODAY    comp   proc VERIFIED   verdict
  idli                 0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  phulka               0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  steamed_rice         0.2500 0.2000  0.4500  0.0500 0.2000   0.2500   STILL BLOCKED
  [the other 15 recipes: 0.2500 0.0000 0.2500 -> 0.0500 0.0000 0.0500, clears]

  3 of 18 recipes remain protein-ineligible after full composition verification

  south_breakfast    BLOCKED by idli
  south_lunch        BLOCKED by steamed_rice
  north_lunch        BLOCKED by phulka
  north_dinner       BLOCKED by phulka

Cross-check: this probe's TODAY column vs core/
  18 of 18 components agree, 0 disagree.
```

The gate in `core/planner/candidates.py` runs at pool-build time, before
enumeration. A component over the ceiling never enters the pool, so the plate is
never enumerated and never solved — an earlier and harder failure than the
energy threshold D7 was watching for. Every one of the four reference plates
contains one of the three blocked recipes. Composition verification cannot move
them: the 0.20 is a process term, and there is no registered constant for
boiling, steaming or dry-griddle loss to replace it with.

So D7's *stated* conclusion is not wrong about what it measured, and is
misleading about what it implies. Verifying the ten rows is **necessary and not
sufficient**: it takes 15 of 18 recipes from 0.25 to 0.05, and leaves all four
plates unenumerable outside `dev_mode`.

*Disposition:* OPEN. This is finding 41 seen from the other end — 41 is the
missing process constants, and closing 41 is what makes the sitting cash out.
Neither ordering makes the other unnecessary. The sitting is still worth doing;
`docs/design/ifct_sitting.md` states this up front so nobody books the time
expecting a servable plate at the end of it.

### The sitting is realistically five or six rows, not ten

Triage in `docs/design/ifct_sitting.md`. Four of the ten are probably not IFCT
questions at all: `sunflower_oil` (**measured**, 2026-07-24 — IFCT's T012 row
carries no nutrient panel for oils), `ginger_garlic_paste` and `garam_masala`
(household compounds a composition table does not tabulate; the real fix is
decomposition into constituent foods, which is a recipe-data change), and
`salt_iodised` (a stoichiometric derivation deliberately chosen over a measured
value for reproducibility). **Only `sunflower_oil`'s verdict is measured; the
rest are predictions from what IFCT 2017 is, and a wrong one should be recorded
in the worksheet's `notes` as a result.**

Separately: IFCT does not tabulate DIAAS, so the authored 1.00 on `paneer_fresh`
and 0.85 on `soya_chunks_dry` — the latter being the only vegan-eligible row
clearing the 0.75 quality threshold — stay authored no matter how the sitting
goes. That is a different source and a different sitting.

### The worksheet is blind, and the diff writes nothing

`docs/design/ifct_transcription_worksheet.csv` is filled from IFCT alone, without
reading the current fixture values first: every one of these rows is a
hand-entered approximation, and transcribing with the guess visible anchors the
transcription to the guess it exists to check. An agreeing transcription then
looks identical, in the file, to a good approximation.

`d7b_transcription_diff.py` reports MATCH / DIFFERS / NOT FOUND per value, flags
a ratio past 2.5x as a probable raw-versus-cooked basis error rather than a
data-quality one, and **writes nothing** — no fixture edit, no `verified` flip.
That omission is the round-4 self-attestation rule applied to tooling: a script
that filled the fixture in would make running the script the cheapest path *and*
the most confident-looking output.

Shown able to fail before being trusted, per CLAUDE.md — a synthetic
`onion_raw` row exercising all four branches, then reverted:

```
  onion_raw   ifct_code=E011  page=p.142  state: worksheet=raw fixture=raw
      energy_kcal  match             40.00
      protein_g    DIFFERS            1.10 ->       1.40  (1.27x)
      carb_g       DIFFERS            9.30 ->      27.90  (3.00x)  <-- BASIS ERROR?
      fibre_g      NOT FOUND    (fixture holds 1.7)
```

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_after_verification.py
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_transcription_diff.py
```

---

## 2026-08-09 — D10: finding 2 CLOSED, findings 41 and 42 raised

### Finding 2 — a recipe with no `process:` line reads as fully process-certain — **CLOSED**

Open since 2026-07-21. The loader derives process uncertainty per macro from the
constants on each ingredient line, and the design's defence of the zeros was
that they are *computed*, not omitted — something an author cannot obtain by
leaving the work undone. That is true of a macro. It is false of a recipe. With
no `process:` line anywhere the numerator is empty for **every** macro, and the
arithmetic producing that zero is indistinguishable from the arithmetic
producing a real one.

Five recipes are in that population, and they are not the same kind of thing:

```
$ PYTHONPATH=. python docs/design/probes/d10_process_zero.py
process.unassessed_uncertainty = 0.2

recipe               preparation  proc  undeclared      now  combined
----------------------------------------------------------------------
aloo_sabzi           cooked          1      0.0311   0.0311    0.2811
carrot_kootu         cooked          1      0.0177   0.0177    0.2677
carrot_poriyal       cooked          1      0.0274   0.0274    0.2774
coconut_chutney      cooked          1      0.0137   0.0137    0.2637
dal_tadka            cooked          1      0.0255   0.0255    0.2755
idli                 cooked          0      0.0000   0.2000    0.4500  <-- moved
masala_dosa          cooked          2      0.0390   0.0390    0.2890
onion_raita          uncooked        0      0.0000   0.0000    0.2500
paneer_masala        cooked          1      0.0160   0.0160    0.2660
phulka               cooked          0      0.0000   0.2000    0.4500  <-- moved
rajma_chawal         cooked          1      0.0150   0.0150    0.2650
sambar               cooked          1      0.0231   0.0231    0.2731
sambar_sadam         cooked          1      0.0133   0.0133    0.2633
soya_chunk_curry     cooked          1      0.0274   0.0274    0.2774
soya_kuzhambu        cooked          1      0.0260   0.0260    0.2760
steamed_rice         cooked          0      0.0000   0.2000    0.4500  <-- moved
thayir_plain         uncooked        0      0.0000   0.0000    0.2500
tofu_bhurji          cooked          1      0.0235   0.0235    0.2735

Recipes with no process constant at all -- the population D10 rules on:
  idli             cooked        100.8 kcal   cooked; 9 of 9 macros declared unassessed
  onion_raita      uncooked       84.2 kcal   zero earned: nothing is heated
  phulka           cooked         98.9 kcal   cooked; 9 of 9 macros declared unassessed
  steamed_rice     cooked        260.0 kcal   cooked; 9 of 9 macros declared unassessed
  thayir_plain     uncooked       87.0 kcal   zero earned: nothing is heated
```

The `undeclared` column is what each recipe's energy band would be if it
declared neither `preparation` nor an unassessed list — the pre-D10 state, and
what a new recipe gets today if the rule is removed. Before D10 all five sat at
a combined **0.2500**, the composition floor and nothing else: a griddled phulka
claimed exactly the certainty of raw whisked curd.

**The column is a counterfactual, deliberately, not a git-history claim.** D10
changed the loader *and* three recipe files, so today's checkout cannot be asked
what yesterday's produced. The probe recomputes the derivation from the
ingredient lines rather than reading `Recipe.process_uncertainty`, so it runs on
either tree and cannot silently agree with the code it audits — the failure this
log records against `d4_declines.py` on 2026-08-08.

**Fix.** A recipe with no process constant must now say which case it is in:
`preparation: uncooked` (a claim about the food, rejected if any line also
carries a `process:` key) or `process_uncertainty_unassessed`, which takes the
registered wide band. `preparation` defaults to `cooked` — omission is the
cheapest authoring path and the round-4 rule is that the cheapest path must
never produce the most confident-looking output.

**What moved in the product.** Only the displayed band on one plate:

```
-  energy band  : 689.6 - 1172.9 kcal
+  energy band  : 590.7 - 1271.8 kcal
```

No plate, unit count, verdict or relaxation rung, on any of the four templates.
That is the expected shape rather than a lucky one: the validator gates on the
point estimate and intervals are display-only, so a widened band cannot reach a
decision. It reaches the user, which is the entire reason for displaying it.

**The red test.** `test_declared_uncertainty_is_backed_by_registered_constants`
has been red on purpose since 2026-07-24 (see the cross-reference entry of that
date). Reading it again while fixing this: its condition
`if recipe.process_uncertainty:` is **always true**, because
`Recipe.process_uncertainty` is mandatory per macro and never empty. So the
assertion it actually made was "every recipe carries a process constant" — which
held only by accident until `idli` and `steamed_rice` arrived in D3 as the
library's first oil-free cooked dishes. It was never a rule worth satisfying.
Rewritten to the invariant it was reaching for (every constant a recipe names is
registered), with the earned-zeros half moved to
`TestZeroProcessUncertaintyMustBeEarned` where the loader enforces it.
`d4b_mutations.py`'s `DESELECT` is now empty; there is no deliberately-red test
in the suite.

**Suite**, both dev servers up so the browser checks actually ran:

```
$ python -m pytest tests/ -q --color=no
........................................................................ [ 14%]
[...]
505 passed, 1 warning in 224.96s (0:03:44)
```

No skips and no failures. The suite has not been all-green since before
2026-07-24 — the deliberately-red test dates from then — so this is the first
run in which every browser check ran and nothing was excluded.

**Disposition: CLOSED.** `core/foods/recipe_loader.py`,
`data/recipes/schema.yaml`, five recipe files, `docs/methodology.md` ("A zero
process uncertainty has to be earned"), D3 limitation 2.

### Finding 41 — a declared process constant still leaves the macros it does not touch at a bare zero — **OPEN**

The rule D10 added fires only when a recipe has **no** process constant
whatsoever. A cooked dish that carries one still derives 0.0 for every macro
that constant does not touch. In this library that is protein on almost every
recipe: oil carries no protein, and oil uptake is the only kind of process
constant registered. Measured —

tail of the same probe run above:

```
Finding 41 -- protein process uncertainty is exactly 0.0 on 15 of 18 recipes:
  aloo_sabzi, carrot_kootu, carrot_poriyal, coconut_chutney, dal_tadka, masala_dosa, onion_raita, paneer_masala, rajma_chawal, sambar, sambar_sadam, soya_chunk_curry, soya_kuzhambu, thayir_plain, tofu_bhurji
  escaping only: idli, phulka, steamed_rice -- the three D10 forced to declare all nine macros unassessed
```

The only three that escape are the three D10 forced to declare all nine macros
unassessed. Every other recipe — including all 13 that were never in finding 2's
population, and `masala_dosa`, which is griddled in oil — still reports a protein
process uncertainty of exactly zero.

This is the same defect finding 2 named, one level down: a zero produced by an
empty numerator, presented as a measurement. It is worth separating because the
remedy is different in kind. Finding 2 was closeable with a loader rule, because
the author knows whether the food is cooked. This one is not: closing it needs
registered process constants for boiling loss, steaming loss and griddle
protein retention, which is a data problem — and per `CLAUDE.md`, Indian-specific
process literature is thin, so the honest outcome may be a row of
`verified=False` conservative estimates rather than sources.

Not fixed here, per the queue rule about tasks turning out larger than
described. Scope is stated in `_check_zero_process_is_earned`'s docstring so the
next reader meets it in the code rather than discovering it.

**It already invalidated a standing claim, which is how it was sized.** Two
tests in `tests/test_nutrition_of.py::TestEligibilityConsequence` went red on
D10, and both were right to:

- `test_every_recipe_sits_at_exactly_the_unverified_composition_band` asserted
  0.25 protein for every recipe, on the premise "oil carries no protein, so no
  process term touches this macro". True of 15 recipes and now false of three.
  Rewritten as two populations with the split named.
- `test_verifying_every_row_would_clear_the_protein_ceiling` asserted that
  flipping every ingredient to verified drops every recipe to 0.05, under the
  0.15 ceiling — i.e. that opening IFCT is *sufficient* to make this library
  shippable. It is not. `idli`, `phulka` and `steamed_rice` land at
  0.05 + 0.20 = **0.25**, still above the ceiling, and no amount of composition
  verification moves them. Renamed
  `test_verifying_every_row_clears_the_ceiling_for_all_but_three_recipes`.

That second one matters beyond D10: the ten-row human sign-off D7 is waiting on
would not, by itself, produce a shippable library. Process constants are a
separate prerequisite nobody had costed, and it took making the zeros honest to
see it.

**Disposition: OPEN.** Blocks nothing today — `candidates.py` gates on the
*combined* composition+process band and composition uncertainty is mandatory per
macro and never zero, so no recipe currently passes eligibility on the strength
of a fake zero. It would matter the moment a verified ingredient exists.

### Finding 42 — the mutation harness ran new code against old data, and reported "covered" for it — **FIXED**

The first D10 sweep returned this:

```
R1   covered      ...::test_silence_is_rejected_because_it_is_the_cheapest_path
R2   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R3   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R4   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R5   covered      ...::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

Four of five rows naming one test that is about none of them. `CLAUDE.md`
already warns that a `covered` row names the *first scoped failure*, which is
collection order rather than relevance, so the rows were re-derived by hand —
apply each mutation, run `tests/test_recipes.py`, take the whole failure list:

```
--- R1: a cooked dish may not derive zeros from silence  (1 red)
       TestZeroProcessUncertaintyMustBeEarned::test_silence_is_rejected_because_it_is_the_cheapest_path
--- R2: preparation defaults to cooked, the demanding case  (28 red)
       ...the library does not load at all...
--- R3: an unknown preparation is rejected, not assumed  (1 red)
       TestZeroProcessUncertaintyMustBeEarned::test_an_unknown_preparation_is_rejected_rather_than_assumed
--- R4: 'uncooked' and a process: line cannot both be true  (1 red)
       TestZeroProcessUncertaintyMustBeEarned::test_an_uncooked_dish_may_not_also_name_a_process
--- R5: a macro the dish contains none of is not the author's to justify  (0 red)
```

R5 is **red in the harness and green by hand**, which is not a difference the
mutation can explain. Cause: `main()` copies `core/` and `tests/` into the
worktree from the working tree and leaves everything else at HEAD — including
`data/`. D10 edited five recipe files, so the worktree ran the new loader
against the old YAML, every one of those five was rejected on load, and the
session-scoped `library` fixture errored on **every** run. The rows were
measuring a mismatch the harness created, mutation or no mutation.

This is finding 35's family — a harness is itself a measurement — and the same
class of blind spot: finding 35 was about parsing tool output, this is about
what the tool was pointed at. The docstring's claim, "the worktree contributes
isolation and nothing else," was the thing that was false.

**Fixed**: `data/` is copied from the working tree alongside `core/` and
`tests/`, and the docstring says why.

**And R5 was a genuine hole.** Its guard — `getattr(total, macro) != 0`, which
exempts a macro the dish contains none of — has no test, and the real library
cannot supply one: all three cooked no-process dishes declare every macro
unassessed, so the guard has nothing left to filter. Deleting it would force a
rice dish to declare B12 unassessed to load at all, a wide band on a macro it
does not contain. `test_a_macro_the_dish_contains_none_of_needs_no_justification`
added, built on `rice_cooked` (0 µg B12). Written **after** watching the
mutation survive, which is the only order that proves the test is about the
mechanism.

Re-run with `data/` copied and the new test in place:

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py R1,R2,R3,R4,R5
R1   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_silence_is_rejected_because_it_is_the_cheapest_path
R2   covered      tests/test_recipes.py::TestRecipeLoaderRules::test_mutating_a_constant_moves_every_recipe_that_depends_on_it
R3   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_an_unknown_preparation_is_rejected_rather_than_assumed
R4   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_an_uncooked_dish_may_not_also_name_a_process
R5   covered      tests/test_recipes.py::TestZeroProcessUncertaintyMustBeEarned::test_a_macro_the_dish_contains_none_of_needs_no_justification
====================================================================================================
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

Four of the five rows now name the test written for that mechanism. R2 still
names something incidental, and correctly: flipping the default to `uncooked`
makes every recipe with a `process:` line illegal, so the library does not load
and 28 tests in this file alone go red. Its own test
(`test_silence_is_rejected_because_it_is_the_cheapest_path`) is in that list —
verified by taking the whole per-mutation failure list, not the row.

**Disposition: FIXED.** `docs/design/probes/d4b_mutations.py`,
`tests/test_recipes.py`.

---

## 2026-08-09 — D9(a) closeout: advice that can actually change the outcome

Finishes D9. Two items were left open by D9(b), both small, both now built and
deletion-checked.

### The three suggestions were shown unconditionally, and two of them often could not help

`DECLINE_PATHS` rendered the same three strings for every decline. One of them —
"if your disclosed conditions have changed, update your profile" — sends a user
to a settings page that cannot affect a decline no clinical flag took part in.
Another — "check back as the recipe library grows" — is a real remedy when a
bound is structurally out of reach and a guess when the plate misses only in
combination. That guess is finding 24's shape exactly: an action offered against
a cause nobody established.

Each suggestion now carries an `applies(details)` predicate reading only tokens
already on the wire:

| suggestion | shows when |
| --- | --- |
| Try a different plate | always |
| Review your disclosed conditions | some violation has a non-empty `locked_by` |
| Wait for the library to grow | some violation is `unreachable` or `empty_pool` |

The first is unconditional **by design, not by omission**: it is what guarantees
the list is never empty, and a decline offering nothing at all is a worse screen
than a slightly loose suggestion. It is also always true — every `reach` value is
scoped to the template that was solved, `unreachable` included, so another
template genuinely can succeed.

Its wording was corrected in the same change. It ended "...to fit the same
*locked* limits", written when it only ever appeared beside a locked bound.
Now that it is the one suggestion shown on every decline, that was false on the
common case. Caught by rendering the screen and reading it, not by a test.

Measured, the jointly-infeasible shape (nothing locked, nothing unreachable):

```
--[paths]--
1
Try a different plate above — a different template draws on different recipes,
so the same limits may fit.
```

Two of three withheld, and the survivor renumbered to close the gap.

### The decline path now says it is not validated

`PlanOut.dev_mode` has existed since D11 and the decline view ignored it, so a
refusal computed entirely from unchecked figures was presented as settled. The
counterpart to D11's success-path line, in `#obDeclineProvenance`:

```
Not validated. The limits above were computed from nutrition data nobody has
checked against a primary source yet, so treat this as an illustration of the
method rather than dietary advice.
```

Deliberately **no percentage**. The success line quotes a share of the plate's
energy; there is no plate here, so that number does not exist and quoting one
would be a fabrication. Pinned by a test asserting `"%"` does not appear.

### A test that could not fail on the defect it named, caught before it was trusted

The first numbering test asserted consecutive numbering against the
`jointly_infeasible` payload — where only the *first* suggestion survives. Index
0 renders "1" whether the numbering runs before or after the filter, so the test
could not distinguish the two implementations and would have passed against the
defect.

Fixed by adding a payload where the *middle* suggestion is the one dropped
(`unreachable`, nothing locked → paths 1 and 3 apply). Pre-filter numbering
renders "1" and "3" there; post-filter renders "1" and "2". Confirmed by
deletion:

```
=== E2: numbering taken before the filter ===
FAILED ...TestOnlySuggestionsThatCanChangeTheOutcome::test_the_numbering_closes_the_gap_the_filter_opens
1 failed, 26 passed
```

This is the third time in two tasks that a test needed the perturbation before
it was worth anything (finding 40 and D8's stale premise being the others).

### Deletion checks — four mechanisms, four covered

```
=== E1: suggestions no longer filtered ===
FAILED ...::test_reviewing_conditions_is_withheld_when_no_condition_locked_anything
FAILED ...::test_waiting_for_the_library_is_withheld_when_the_library_is_not_the_limit
FAILED ...::test_the_numbering_closes_the_gap_the_filter_opens
3 failed, 24 passed

=== E2: numbering taken before the filter ===
FAILED ...::test_the_numbering_closes_the_gap_the_filter_opens
1 failed, 26 passed

=== E3: decline provenance never rendered ===
FAILED ...TestTheDeclineSaysItIsNotValidated::test_a_dev_mode_decline_says_so
1 failed, 26 passed

=== E4: dev_mode guard removed ===
FAILED ...TestTheDeclineSaysItIsNotValidated::test_nothing_is_claimed_when_the_plan_was_not_dev_mode
1 failed, 26 passed
```

E4's first attempt aborted rather than running: the guard's source is
byte-identical to `renderProvenance`'s on the success path, so the pattern
matched twice and the harness refused a non-unique mutation instead of editing
the wrong function and reporting a false result. Same protection
`d4b_mutations.py` has, for the same reason.

By hand again, for the reason recorded under D9(b): `d4b_mutations.py`
structurally cannot grade `web/`.

### Suite

```
$ python -m pytest tests/ -q --color=no --no-header       # both servers up
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
1 failed, 497 passed, 1 warning in 225.54s (0:03:45)
```

497 = 488 + 9. The single failure is D10's deliberately red test.

**D9 is now complete**, (a) and (b).

---

## 2026-08-09 — D9(b): the decline stopped saying `sodium_mg`

Closes **findings 31 and 36**. Done in the order D9 states, which is the repo's
own: extend the detector first, watch it fail, then write the copy.

### Finding 36 — the sweep claimed a decline it never rendered

`tests/test_web_no_identifiers.py`'s docstring said it covered "a solved plate
or an honest decline". The fixture clicked Generate once, on the default plate,
which solves. `renderPlanSuccess` and `renderPlanDecline` write into two
independent sections, so the violation list and the disclosure paragraph — the
two places a raw macro name was most likely to reach a reader, and the reason
the file exists — were swept zero times.

**Disposition: FIXED.** The fixture now selects a plate that declines for its
own profile and collects a tenth view, `dashboard_after_decline`.

Which plate declines was measured against the live API, not assumed:

| plate | verdict |
| --- | --- |
| south_indian:breakfast | passes |
| **south_indian:lunch** | **declines** — sodium 1546.0 mg vs a 1400.0 mg ceiling |
| north_indian:lunch | passes |
| north_indian:dinner | passes |

Three rungs were walked (`sodium_max_fibre_min`, `fat_carb_tolerance`,
`energy_tolerance`) before the ladder gave up, and the bound is `locked` by
`chronic_kidney_disease` — so this exercises the clinical-lock path, which D9
calls the most interesting thing on the screen.

The reachability test now requires that view to prove it *is* a decline: the
lede, the plate name (so a failed radio click cannot pass), and that some line
names sodium — asserted case-insensitively and accepting "salt", so it survives
the copy map below. If the library ever shifts and that plate starts passing,
this goes red rather than the sweep quietly becoming a second pass over the
success view.

### Finding 31 — measured before it was fixed

```
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_decline]
Leaks: [('sodium_mg', "sodium_mg is 1546.0mg, above its ceiling of 1400.0mg (more than one
         plate may take of a whole day's allowance) (locked b"),
        ('sodium_mg', 'No plan could be built for this profile: sodium_mg is 1546.0mg,
         above its ceiling of 1400.0mg (more than one plate may t')]
1 failed, 11 passed in 19.43s
```

Red on the new view only; every other view including the success path stayed
green, so this is finding 31 isolated rather than a broad regression.

**Two leak sites, not one.** `violation_detail[].text` renders into the
violation list, and `disclosure` renders into the closing paragraph — and the
disclosure *embeds* the same sentence rather than composing its own. Measured
rather than argued, by fixing only the list and re-running:

```
=== D2: disclosure renders the server string again (violations list left FIXED) ===
FAILED tests/test_web_decline_copy.py::TestNoTokenSurvivesAnyBranch::test_not_one_identifier_reaches_the_disclosure
FAILED tests/test_web_decline_copy.py::TestTheSentencesSayTheRightThing::test_the_disclosure_leads_with_the_clinical_refusal_when_one_holds
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_decline]
3 failed, 27 passed
```

A fix closing one site leaves the detector red — the task's own definition of
unfinished.

### The map is client-side, and needed two numbers the API was not sending

Copy lives in `web/dashboard.js`, consistent with D11: the server sends stable
tokens, the client writes the sentence. `core/planner/validator.py` still writes
`text` and `disclosure`, both still correct; they are simply not what this page
renders.

`ViolationOut` already carried `macro`/`kind`/`bound_source`/`reach`/
`relaxability`/`locked_by` but **not the two numbers any such sentence needs**.
Without them a client had to render `text` (which interpolates the raw key) or
parse the numbers back out of English, which would make prose an API contract —
the opposite of why the tokens exist. `actual` and `bound` have been on
`core.planner.validator.Violation` since D4a; `api/` now passes them through and
still computes nothing.

Every key `Violation.macro` can carry is mapped, not only the one a decline
produces today: all nine `MACRO_KEYS`, plus `quality_protein_g` (not a macro —
see `core/foods/quality.py` — but it reaches a decline like any bound). An
unmapped macro degrades to vague-but-clean prose rather than to its key, because
`humanise()` would render `potassium_mg` as "Potassium mg" and then state a
number against a unit the client cannot name.

Before, and after, for the real declining plate:

```
sodium_mg is 1546.0mg, above its ceiling of 1400.0mg (more than one plate may
take of a whole day's allowance) (locked by a condition you disclosed, and
never relaxed for that reason)
```

```
Sodium comes to 1,546mg, over the 1,400mg limit — more than one plate should
take of a whole day's allowance. We didn't loosen this one, because you told
us about chronic kidney disease.
```

and the disclosure, which no longer repeats the list it sits under:

```
We stopped rather than relax a limit tied to a condition you disclosed. This
system is not a substitute for clinical nutrition guidance — please take these
targets to your doctor or dietitian.
```

### Finding 40 — a default of `0.0` made the API's own deletion check pass

`ViolationOut.actual`/`bound` were first written with `= 0.0` defaults. Deleting
the pass-through in `api/main.py` then left every violation reporting 0.0
against 0.0 and **the suite stayed green** — the presence-and-type assertions
passed, and the prose check passed by coincidence, because `"0.0"` is a
substring of `"1400.0"`.

**Disposition: FIXED, in both places.** The fields are required, so a dropped
pass-through is a construction error rather than a plausible-looking
measurement; and the test asserts the numbers are non-zero. This is CLAUDE.md's
round-4 rule — the cheapest authoring path must never produce the most
confident-looking output — reappearing outside uncertainty, where the addendum
states it. Recorded because the mechanism survived its first check and the test
was the thing at fault, not the code.

### Nine of ten map entries are unreachable from the real library

`tests/test_web_decline_copy.py` (new) drives the real `renderPlanDecline` in a
real browser with `POST /api/plan` stubbed to return violations today's recipe
library cannot produce: every macro, both `kind`s, all three `bound_source`s,
every `relaxability` note, an unfillable plate, and a macro absent from the map.
Auth, profile and science still hit the real API, so the page reaches the
renderer the way it always does.

Three deletion checks, each shown red against its own mechanism:

```
=== D1: violations list renders server prose again ===
FAILED ...TestTheSentencesSayTheRightThing::test_a_floor_reads_as_a_shortfall_and_a_ceiling_as_an_excess
FAILED ...TestTheSentencesSayTheRightThing::test_a_locked_bound_names_the_condition_and_says_we_chose_not_to
FAILED ...TestTheSentencesSayTheRightThing::test_the_bound_source_is_explained_when_it_is_not_the_ordinary_one
FAILED ...TestTheSentencesSayTheRightThing::test_an_unfillable_plate_names_the_courses_in_words
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_decline]
17 failed, 13 passed

=== D3: unmapped-macro fallback removed ===
FAILED ...TestNoTokenSurvivesAnyBranch::test_an_unmapped_macro_degrades_to_prose_not_to_its_key
1 failed, 29 passed
```

**These were run by hand, not through `d4b_mutations.py`, and that is a
structural limit rather than an omission.** The harness mutates a copy of
`core/` and `tests/` inside a throwaway worktree; the browser loads `web/` from
a static server pointed at the real directory, so a mutated `web/` in the
worktree would have no effect and every row would falsely report "survived".
Adding `web` to the copied trees would not fix it. Left as-is and written down
here so the next person does not read the absence of W-style rows as an
oversight.

### Suite

```
$ python -m pytest tests/ -q --color=no --no-header       # both servers up
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
1 failed, 488 passed, 1 warning in 204.84s (0:03:24)
```

488 = 466 (426 + the 40 web tests, now running) + 18 decline-copy + 3 API + the
new tenth view. The single failure is D10's deliberately red test.

### What D9 still owes

This is **(b) plus the copy `(a)` needs**, not all of D9(a). Specifically still
open: the decline screen does not yet offer only suggestions that *can* change
the outcome — `DECLINE_PATHS` is still three static strings shown regardless of
whether they apply. "Try a different plate" is good advice for a
`jointly_infeasible` sodium miss and useless for an `unreachable` one, and the
payload now carries `reach` to tell them apart. Not started.

---

## 2026-08-09 — D8: the web suite reported green without looking

D8 was written as two halves: **(a)** make conditional passing honest, and
**(b)** triage "12 failed / 30 errors, Playwright timeouts, undiagnosed". Its
own re-scope note said to start by re-measuring rather than fixing. Doing that
changed both halves.

### Finding 38 — (b)'s triage list is empty, and the recorded failure count was stale

With both dev servers up, every browser-backed check passes:

```
$ python -m pytest tests/ -q --color=no --no-header -m web
.........................................                                [100%]
41 passed, 416 deselected, 1 warning in 86.60s (0:01:26)
EXIT=0
```

**Disposition: CLOSED, nothing fixed, because nothing was broken.** The "12
failed / 30 errors" figure predates work that has since landed and was never
re-taken. This is the second independent run showing 41/41 — the first was
D11's incidental `1 failed, 456 passed`, which is why D8's re-scope note
existed. Two runs on one machine is not a proof of health, and the tests remain
timing-sensitive Playwright checks; but the specific list D8 was written to
triage does not exist, and inventing work to match a stale number would be
worse than saying so.

Nothing in `web/`, `api/` or `core/` was touched for this half.

### Finding 39 — the skips were never silent; they were merely unseen

D8's premise, carried in the task text for weeks, is that the suite "passed
silently when servers were down". Measured, that is **false in its literal
form**. Every skip already names its cause:

```
$ python -m pytest tests/test_web_*.py -q --color=no --no-header -rsp
ssssssssssssss.ssssssssssssssssssssssssss                                [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_web_landing_geometry.py:90: no static server on http://localhost:3000
SKIPPED [9] tests\test_web_no_identifiers.py:198: no static server on http://localhost:3000 (python -m http.server 3000 --directory web)
...
1 passed, 40 skipped in 4.60s
EXIT=0
```

The reasons are good ones — several name the command that would fix them. They
appear **only under `-rs`**, which nobody passes by habit. The default view is
`1 passed, 40 skipped`, exit 0.

So the defect is real but it is not the one recorded: **naming a reason is not
the same as it being seen.** A distinction worth writing down, because the fix
that "silent" implies — add reasons — was already done, and doing it again
would have produced a satisfied task and an unchanged failure mode. This is the
same family as findings 11, 18 and 36: a check that satisfies the letter of its
rule while missing the purpose.

**Disposition: FIXED**, described below.

### The fix sits on the report, not on the fifteen call sites

`tests/conftest.py` gains one rule: a `web`-marked test that skips is recorded,
announced at the end of the run, and — under `FOODAI_WEB_TESTS=required` —
converted into a failure.

It deliberately does **not** edit the ~15 `pytest.skip` sites across the three
web files (`_listening` is defined three times; the skips split 4 / 2 / 9).
Two reasons, and the second is the load-bearing one:

1. One definition instead of fifteen.
2. It catches **every** cause of a web skip, including a missing Playwright —
   which no server check would ever see, because `importorskip` fires before
   any server is contacted. A gate written as "check the servers harder" would
   have left the bare-checkout case exactly as it was.

The call sites keep deciding *whether* a prerequisite is missing — they know
which of the two servers each test needs, and duplicating that into the gate
would have been the actual larger change — while the gate decides what a
missing prerequisite *means*.

`pyproject.toml` promises `python -m pytest tests/ -q` runs clean on a bare
checkout. That promise is kept: the default stays exit 0. It is also precisely
how a frontend surface reports green without looking, so the strict reading is
available to anyone who wants it rather than imposed on everyone.

### Both modes, measured with the servers genuinely stopped

Default — loud, exit preserved:

```
$ python -m pytest tests/test_web_landing_geometry.py tests/test_web_no_identifiers.py -q
ssssssssssssss.                                                          [100%]
============================ web tests did not run ============================
14 browser-backed check(s) skipped. Nothing in web/ was verified by this run.
  - no static server on http://localhost:3000
  - no static server on http://localhost:3000 (python -m http.server 3000 --directory web)
Start the servers (see web/README.md), or set FOODAI_WEB_TESTS=required to make this a failure.
1 passed, 14 skipped in 2.13s
EXIT=0
```

Strict — hard failure, exit 1:

```
$ FOODAI_WEB_TESTS=required python -m pytest tests/test_web_landing_geometry.py -q
FAILED tests/test_web_landing_geometry.py::test_the_kolam_never_exceeds_its_token_on_the_landing_page
FAILED tests/test_web_landing_geometry.py::test_every_route_renders_the_kolam_at_one_strength
FAILED tests/test_web_landing_geometry.py::test_the_language_label_holds_position_across_all_four_scripts
FAILED tests/test_web_landing_geometry.py::test_no_placeholder_copy_renders_in_the_hero
4 failed in 1.69s
EXIT=1
```

with each failure carrying the reason forward:
`FOODAI_WEB_TESTS=required, so a skipped browser check is a failure: no static
server on http://localhost:3000`. A strict run that said only "something was
skipped" would be reporting what it already reported.

And with the servers up, the summary correctly stays quiet: `4 passed in
32.62s`, no block.

### Deletion check: six rows, all covered

`d4b_mutations.py` gains `WEB_GATE = "tests/conftest.py"` and rows W1–W6. It
already copies `tests/` from the working tree, so hosting a `tests/` module cost
a module constant and an `OWN_TESTS` row — the same shape D6 found for
`core/foods/`.

```
$ python docs/design/probes/d4b_mutations.py W1,W2,W3,W4,W5,W6
W1   covered      tests/test_web_gate.py::TestStrictModeTurnsASkipIntoAFailure::test_a_skipped_web_test_fails_under_the_env_var
W2   covered      tests/test_web_gate.py::TestStrictModeTurnsASkipIntoAFailure::test_only_the_exact_word_arms_strict_mode
W3   covered      tests/test_web_gate.py::TestStrictModeTurnsASkipIntoAFailure::test_a_non_web_skip_is_untouched_even_under_strict
W4   covered      tests/test_web_gate.py::TestTheReasonIsRecoveredWhateverShapeItCameIn::test_a_bare_string_longrepr
W5   covered      tests/test_web_gate.py::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
W6   covered      tests/test_web_gate.py::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
====================================================================================================
6 mechanisms: 6 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

`OWN_TESTS[WEB_GATE]` is `test_web_gate.py` **only**. The three `test_web_*.py`
suites are the *subject* of this gate, not tests of it — they skip together for
one reason, so a row they turn red is reporting the weather.

W5 and W6 name the same test, which is the pattern `CLAUDE.md` says not to
believe on sight, so the full list was taken for both rather than trusting the
row:

```
=== W5 full failure list in test_web_gate.py ===
FAILED ...::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
1 failed, 9 passed in 0.06s
=== W6 full failure list in test_web_gate.py ===
FAILED ...::TestTheSummarySaysTheFrontendWasNotChecked::test_it_names_the_count_and_every_distinct_reason
1 failed, 9 passed in 0.06s
```

Exactly one failure each, and it is the test about the summary's content in both
cases — a single test genuinely covering two mechanisms, not collection order
picking a bystander. Recorded because the check is cheap and the D6 sweep is the
reason it is now habitual.

### One thing the tests cannot grade, and where the evidence for it lives

`tests/test_web_gate.py` drives the hooks with stand-in report objects. It
cannot answer whether pytest honours `report.outcome = "failed"` set from a
wrapper — the two transcripts above answer that, taken against the real suite.
The file is scoped to the other half: that the rule survives edits. Recorded
here because a reader finding only the unit tests would over-trust them.

### Full suite, servers down — the state most readers will be in

```
$ python -m pytest tests/ -q --color=no --no-header
============================ web tests did not run ============================
40 browser-backed check(s) skipped. Nothing in web/ was verified by this run.
  - no static server on http://localhost:3000
  - no static server on http://localhost:3000 (python -m http.server 3000 --directory web)
Start the servers (see web/README.md), or set FOODAI_WEB_TESTS=required to make this a failure.
=========================== short test summary info ===========================
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
1 failed, 426 passed, 40 skipped, 1 warning in 109.68s (0:01:49)
```

426 = 414 + D11's 2 + this task's 10. The single failure is D10's deliberately
red test, unchanged.

### Still true after this change

The suite still reports exit 0 by default with the frontend unchecked. That is
a deliberate trade, not an oversight: the alternative breaks the bare-checkout
promise for every reader who is not running a browser. What changed is that the
run now says so in six lines nobody can miss, and that a caller who wants the
guarantee has one word to type.

---

## 2026-08-09 — D11: the `dev_mode` plate now says so

Closes **finding 37**. The dashboard had always rendered a plate built on
100%-unverified data as an ordinary result, against a requirement
`docs/methodology.md` states about exactly this case.

### D11's own part 1 was wrong, and the code said so

D11 specified, as its first and "only real decision", surfacing provenance from
`core/` — on the reasoning that `plan_meal` discards the candidate pool and
`LadderOutcome` carries no provenance field. That is true and it is not the
obstacle. `SolvedPlan.estimate` is a `NutritionEstimate`, which has carried
`unverified_energy_kcal` all along; `api/main.py` was already reading
`outcome.plan.estimate.point` and dropping the rest of the object. And
`dev_mode` is a parameter the API itself passes.

So **no `core/` change was needed** and none was made. Recorded rather than
quietly dropped, because the wrong premise was written into the queue and this
file yesterday, and a reader would otherwise be left expecting a refactor that
never happened. What is genuinely unreachable is `CandidatePool.flagged` — see
"What is still not surfaced" below.

### The shape: the server sends the number, the client writes the sentence

`PlanOut` gains `dev_mode: bool`. `PlanEstimateOut` gains
`unverified_energy_kcal` and `unverified_energy_fraction`, read off the
estimate `core/` already computed rather than recomputed in `api/`, which
computes no nutritional number.

The prose is written in `web/dashboard.js`. `dev_mode` is `snake_case` and must
never reach a visible text node — same rule as `bound_source` and
`VIOLATION_REACH` — and this is also the division `CLAUDE.md`'s central
invariant describes for the LLM: the number is computed deterministically
upstream, the language is written around it.

### The order, which is the point

The first draft of `renderProvenance` rendered the token itself. Run against
live servers **before** the real copy was written:

```
$ python -m pytest tests/test_web_no_identifiers.py -q
FAILED tests/test_web_no_identifiers.py::test_no_identifier_reaches_a_rendered_string[dashboard_after_plan]
E   AssertionError: dashboard_after_plan renders internal identifiers to the user.
E   Leaks: [('dev_mode', 'Built with dev_mode')]
1 failed, 10 passed in 19.05s
```

Then the copy, then:

```
11 passed in 15.28s
```

That red run also **measures** a claim made yesterday on reasoning alone. The
2026-08-09 finding-37 entry argued this belonged outside D9 partly because the
identifier sweep already reaches the success view. It does, and now that is a
transcript rather than an inference.

### It renders

```
$ curl -s -X POST localhost:8000/api/plan -d '{...north_indian/lunch, 70kg...}'
passed      : True
dev_mode    : True
energy      : 931.2
unverified  : 931.2 kcal = 100.0%
```

Live browser, same profile and plate:

```
success section hidden : False
PROVENANCE LINE        : Not validated. About 100% of this plate's energy rests on
                         figures nobody has checked against a primary source yet. The
                         nutrition data behind these dishes is unconfirmed, so treat
                         the numbers as an illustration of the method rather than
                         dietary advice.
```

### A second false claim, found in the same function

`renderPlanSuccess`'s no-estimate fallback read **"A validated combination of
real components for this plate."** Nothing in this library can ship as
validated, so that sentence was false on every plate the app has ever served,
and it asserted precisely the thing finding 37 is about. Now "A combination of
real components for this plate." Found by reading the function being edited,
not by any test — no test covers a success render with a null estimate.

### Measured, per the deletion convention

Two mechanisms in `api/main.py`, each deleted with the full suite re-run:

```
A1  PlanOut echoes the dev_mode it actually ran with
      tests/test_api_targets.py::TestPlanProvenanceReachesTheClient::test_a_solved_plate_says_it_is_not_validated
A2  the unverified figure is carried onto the estimate
      tests/test_api_targets.py::TestPlanProvenanceReachesTheClient::test_the_unverified_figure_is_carried_not_dropped
```

Each caught by exactly its own named test, and by nothing else. The copy itself
is graded by `test_web_no_identifiers.py`, shown red above.

The harness's first run printed **empty names for both rows** — it took
`line.split(" ")[0]`, which is the word `FAILED`. Finding 35's lesson, that a
harness parsing tool output is itself a measurement, reproduced within a week of
being written down. Both mutations really had gone red; the harness could not
say which test caught them, which is the entire question it exists to answer.

### What is still not surfaced

`CandidatePool.flagged` — how many recipes were kept past their eligibility
ceiling. `docs/methodology.md` names it alongside `dev_mode`, and it is the one
thing here that *would* need the `core/` change: `plan_meal` builds the pool and
discards it. Deliberately not done, and the position is arguable rather than
obvious: a count of recipes that missed an internal threshold is a mechanism
detail, while "100% of this plate's energy" is the same fact in the units a
reader can act on. If that judgement is wrong, the fix is the refactor D11's
part 1 described, and it now has a reason to exist that this task did not
supply.

### Verify

```
$ python -m pytest tests/ -q
1 failed, 456 passed, 1 warning in 189.58s (0:03:09)
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
```

456, not 416, because the static server and API were up: the 40 web tests that
normally skip actually ran. 414 + 2 new + 40 = 456. The one failure is D10's
deliberately-red test.

**Relevant to D8, and not a claim about it.** D8 records the web suite as "12
failed / 30 errors, Playwright timeouts, undiagnosed". With servers up today it
ran clean. That is one run on one machine and does not close D8 — whose (a) is
about *conditional passing being honest*, which is untouched: the suite still
skips silently when the servers are down, which is how a green run can mean
nothing. But whoever picks up D8 should know the triage list may be much shorter
than recorded, or empty.

**Disposition:** finding 37 **CLOSED**. Findings 19, 31, 36, 2, 15, 22, 28, 29
untouched. `CandidatePool.flagged` remains unsurfaced, by decision, recorded
above.

---

## 2026-08-09 — D7, part 1: the verification horizon, and finding 37

**D7 is not complete and cannot be completed by an assistant.** Its central
deliverable — "verify those rows against IFCT 2017 with correct grading" — is
the one action this project reserves for a human, in `CLAUDE.md`'s second
invariant, in the round-4 addendum, and in this file's 2026-07-21 entry. What
follows is everything else D7 asked for, plus the measurement that says whether
the human half is worth anyone's afternoon.

### The question D7 put to D6, now answerable

D7's own text: *"Depends on D6. Verified ingredients feeding a wrong denominator
certify nothing."* D6 fixed the denominator yesterday, so the question is
answerable — and better answered before someone opens a reference book than
after.

`docs/design/probes/d7_verification_horizon.py`, north_lunch's plate (phulka x5
+ soya_chunk_curry x1 + paneer_masala x1, 931.2 kcal):

```
  TODAY          931.2 / 931.2 kcal = 100.0%   -> does NOT ship (threshold 15%)
  INGREDIENTS     88.4 / 931.2 kcal =   9.5%   -> SHIPS (threshold 15%)
      soya_chunk_curry:sunflower_oil              44.2 kcal  (process)
      paneer_masala:sunflower_oil                 44.2 kcal  (process)
  EVERYTHING       0.0 / 931.2 kcal =   0.0%   -> SHIPS (threshold 15%)

  cross-check: core/ reports 931.2 kcal, this probe's TODAY is 931.2 kcal -- agree
```

**Ten ingredient rows are sufficient on their own.** The process constants are
not on the critical path — which matters, because IFCT 2017 is a composition
table and does not contain oil-uptake figures for a tempered curry; those are
separate constants with separate sources, and `CLAUDE.md` warns Indian-specific
process literature is thin. Had the answer come out the other way, the ten rows
would have bought nothing and D7 would have needed rescoping before the work,
not after.

Stated against over-reading: 9.5% leaves 139.7 kcal of headroom, real but not
large; a second template gets its own answer; and ~15% is still the provisional
figure `CLAUDE.md` flags for revisiting.

The probe computes both hypotheticals itself and **never flips a flag**. A probe
that sets `verified=True` to answer a question is one interrupted session away
from leaving it set — the failure the flag exists to prevent, committed by the
tool built to measure it. Only the TODAY column has a shipped counterpart to
cross-check against, and it agrees.

### The rows, named

Ten of the eleven rows reachable from north_lunch need a human: `wheat_atta_raw`,
`paneer_fresh`, `soya_chunks_dry`, `onion_raw`, `tomato_raw`, `sunflower_oil`,
`ginger_garlic_paste`, `garam_masala`, `green_chilli`, `salt_iodised`. `water`
is the eleventh and is already verified.

**None of the ten carries an IFCT code**, so the task is "find the code, then
transcribe", not "transcribe". None of the four rows that already carry real
codes from 2026-07-24 (`rice_milled_raw`, `rajma_raw`, `toor_dal_raw`,
`potato_raw`) appears on this plate — the template D7 picked is the one with no
head start, which nobody had noticed.

`docs/methodology.md` now carries the narrowing as a deliberate scope line, per
D7's instruction to write it in the voice of the existing boundaries.

### Finding 37 — a `dev_mode` plate is rendered with no label — **OPEN**

Found while scoping D7's third deliverable. `docs/methodology.md` has required,
since Phase 2:

> Any rendered plan, any `demo.py` stdout, and any README transcript produced in
> `dev_mode` must carry that label in the artifact itself.

`demo.py` complies — it prints `unverified : 931.2 kcal (100.0% of plate)`. The
web does not. `PlanOut` carries `passed`, `disclosure`, `relaxation_applied`,
`violations`, `violation_detail`, `components`, `estimate`; `PlanEstimateOut`
carries six macros. **Neither carries `dev_mode`, `CandidatePool.flagged`, or
the unverified figure**, and `web/dashboard.js` renders none of them. Grepped,
not assumed: the only `unverified` in `api/` is `/api/science`'s registry count,
and `web/dashboard.js` mentions the word once, in a comment.

So the dashboard has always presented a `dev_mode` plate as an ordinary result.
That was true before D6 and is sharper after it: the number now absent from the
screen is 100%.

This is the "artifact survives without context" failure the same section names,
on the surface where a portfolio project's output is actually seen — and the
requirement it violates was written in this repository, about this case, and
then not implemented.

**Why it is not fixed here.** `plan_meal` builds the candidate pool and discards
it; `LadderOutcome` carries `plan`, `result`, `target_used` and
`skipped_locked_steps`, and nothing about provenance. Surfacing it is a `core/`
design decision with a wrong answer available — hanging `dev_mode` on
`LadderOutcome` would put candidate-pool knowledge on a validator dataclass that
has no business with it. `core/planner/plan.py` owns both halves and is the
right place, but that is a deliberate change, not a field addition, and D7's
headline is blocked regardless. Queued, not slipped in.

**Checked against D9 before queuing, because D4c had just turned out to be this
shape.** D9 already lists "surface `dev_mode`", so the question was whether
finding 37 was inside it. It is not, and the reason is not scope-drawing
preference: D9 is the *decline* screen in every other bullet, this is the
*success* path, and `web/dashboard.js` renders the two through independent
functions into independent DOM sections (`renderPlanSuccess`,
`renderPlanDecline`). The decisive asymmetry is detection, not surface —
`tests/test_web_no_identifiers.py` already reaches the success view (its own
fixture profile is served a plate on the default `south_indian:breakfast`), so
a naive `dev_mode` string there is caught today; it never reaches a decline,
which is finding 36 and is D9's own (b). One is verifiable now, the other is
blocked behind D8 and a detector that does not yet exist.

The two do share exactly one change — `PlanOut` gains `dev_mode` once, for both
paths. That is recorded in both task entries rather than in neither, which is
the failure mode finding 31 nearly had.

**Disposition:** D7 **part 1 done, part 2 blocked on a human.** The scope
narrowing and its justifying measurement are landed; the ten rows are named; the
plumbing is finding 37 and the verification is nobody-but-a-human's. Findings
19, 31, 36, 2, 15, 22, 28, 29 untouched.

---

## 2026-08-09 — D6: the unverified-energy denominator

Closes **finding 20**. The number the 15% shipping threshold and the `dev_mode`
exit both read was wrong in two directions at once. Nothing depended on it yet,
which is why it was fixed now — D7 and the `dev_mode` exit are next in the queue
and both would have leaned on it.

### The fix

Attribution moves from "one yes/no question per recipe" to per ingredient line.
A line is charged when its composition record is unverified **or** the process
constant that determined its quantity is, and charged **once** in either case.

Union rather than sum is deliberate: a line unverified for both reasons is still
only that much energy, and adding the terms could take a plate past 100% of its
own energy, which is not something a fraction of a quantity can do.

Charging a line's *whole* energy on an unverified process constant is not the
old over-attribution returning. `RecipeIngredient.process_key` marks a line
whose **quantity was determined by** that constant, so if the constant is
unopened, so is every calorie on that line. The old rule's error was charging
the *other* lines too.

`_depends_on_unverified` is gone, replaced by `_unverified_energy`.

### The measurement, all four passing plates

`docs/design/probes/d6_unverified.py` prints the per-line arithmetic and three
figures per plate: OLD (the previous rule, restated in the probe), NEW (the
corrected rule, reimplemented independently), and SHIPPED (whatever `core/`
returns). NEW and SHIPPED are printed side by side so the probe cannot quietly
agree with the code it audits — a difference between them is a bug in one.

```
  PLATE south_breakfast: 623.6 kcal        PLATE north_lunch: 931.2 kcal
    OLD        234.2 / 623.6 =  37.5%        OLD        436.8 / 931.2 =  46.9%
    NEW        623.6 / 623.6 = 100.0%        NEW        931.2 / 931.2 = 100.0%
    SHIPPED    623.6 / 623.6 = 100.0%        SHIPPED    931.2 / 931.2 = 100.0%
  PLATE south_lunch: 848.1 kcal            PLATE north_dinner: 782.5 kcal
    OLD        501.1 / 848.1 =  59.1%        OLD        317.4 / 782.5 =  40.6%
    NEW        848.1 / 848.1 = 100.0%        NEW        782.5 / 782.5 = 100.0%
    SHIPPED    848.1 / 848.1 = 100.0%        SHIPPED    782.5 / 782.5 = 100.0%
```

Before the `core/` change, SHIPPED equalled OLD on all four; after, it equals
NEW on all four. That transition is the whole verification, and it is why the
probe computes both columns itself instead of using a worktree — the comparison
does not depend on which tree it runs from, so it keeps working after D6 lands.

**Exactly 100% is the correct answer, not a rounding artifact.** 28 of 29
ingredient rows are `verified=False` and the exception, `water`, carries no
energy. Every calorie on every plate traces to a composition record nobody has
opened. The old 37–59% figures were understatements produced by ignoring
composition entirely.

Confirmed through the tracked entry point, plates unchanged:

```
$ PYTHONHASHSEED=0 python demo.py plan --region south_indian --meal-slot breakfast
  unit counts  : {'idli@tiffin': 6, 'soya_kuzhambu@kuzhambu': 1, ...}
  point        : 623.6 kcal, 29.6g protein, ...
  unverified   : 623.6 kcal (100.0% of plate) -- CLAUDE.md's shipping threshold is ~15%
```

### The real library cannot test this, and the old test said it could

`TestUnverifiedEnergyAttribution::test_all_three_recipes_rest_on_unverified_
process_constants` asserted `unverified_energy_fraction() == 1.0` and **passed
identically before and after the fix** — the old whole-recipe rule also charged
everything on this library. Under the correct rule every real plate is 100%,
and under most broken ones it still is. A test that cannot fail on the defect it
names is not evidence, whatever its name.

It is kept, renamed `test_the_real_library_is_entirely_unverified`, and its
comment now says what it does and does not show. Five new tests build their own
mixed data — a verified line, an unverified-composition line, a
verified-ingredient-on-unverified-process line — where the answer is 600 of 700
kcal rather than everything.

Measured, per the deletion-testing convention. Five mechanisms added to
`d4b_mutations.py` (which turned out never to have cared that its modules were
all in `core/planner`; `core/foods/nutrition_of.py` needed only a new constant
and an `OWN_TESTS` row):

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py N1,N2,N3,N4,N5
N1   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_the_real_library_is_entirely_unverified
N2   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_a_verified_line_with_no_process_is_not_charged
N3   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_the_real_library_is_entirely_unverified
N4   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_a_verified_line_with_no_process_is_not_charged
N5   covered      tests/test_nutrition_of.py::TestUnverifiedEnergyAttribution::test_the_real_library_is_entirely_unverified
5 mechanisms: 5 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
```

**That table is not sufficient on its own, and it names the demoted test three
times.** The harness reports the first *scoped* failure, which is collection
order, not relevance — D4b-i's own lesson that a test in the right file is not
automatically the right test. So the full failure list was taken per mutation:

```
N1 composition charged     -> all four synthetic tests, plus the real-library one
N2 process charges its line -> test_a_verified_line_with_no_process_is_not_charged
                              test_unverified_composition_is_charged
                              test_the_charge_scales_with_the_serving_count
N3 charged once, not twice  -> test_a_line_unverified_twice_over_is_charged_once
                              (+ the real-library one)
N4 per line, not per recipe -> all four synthetic tests
N5 scales with count        -> test_the_charge_scales_with_the_serving_count
                              (+ the real-library one)
```

Every mechanism is caught by the test written for it. And the sharper result:
**N2 and N4 — the two directions finding 20 actually named — do not trip the
real-library test at all.** Under N4 the real library still charges everything
(whole recipe = everything); under N2 composition alone still charges
everything. The test that looked like coverage for this fix is blind to exactly
the defect the fix is about.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d6_unverified.py
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py N1,N2,N3,N4,N5
PYTHONHASHSEED=0 python demo.py plan --region south_indian --meal-slot breakfast
python -m pytest tests/ -q
```

```
1 failed, 414 passed, 40 skipped, 1 warning in 112.03s (0:01:52)
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
```

409 → 414 is the five new tests exactly (one old test renamed, not added). The
one failure is D10's deliberately-red test, unchanged.

**Disposition:** finding 20 **CLOSED**. `docs/methodology.md` limitation 8
closed with it, and a new dated section carries the corrected figures. No plate,
verdict or unit count moved — this changes what the system says about its own
evidence, not what it plans. Findings 19, 31, 36, 2, 15, 22, 28, 29 untouched.

---

## 2026-08-09 — D4c-i: the decline sentences, before and after D4a

D4a's entry proved the declines got better with four counts. Nobody had read
the sentences those counts summarise. This is that artifact: `d4_declines.py`
gains a `text` mode, run on both sides of D4a from one probe implementation.

### There is no "the decline for each template"

Since D3 all four templates **pass** for the reference profile. A decline
exists only relative to a profile, so an artifact printing four blocks without
saying whose they are has silently answered a question nobody asked. The
selection rule is therefore part of the output and is reproduced above it:
walk the existing profile grid in order, group each template's declines by the
`(macro, kind)` pairs the decline names plus whether the profile has clinical
flags, and print the most common shape, the most common flagged shape, and the
most common unflagged shape, deduplicated. Representative is first-in-grid-order.
Ties break on grid order, so the output is a function of the grid alone.

**The first version of that rule was wrong and the output said so.** It
guarded only the flagged side, on the reasoning that a locked bound is rare
and would be buried by frequency. On the real library the opposite held: the
top shape already carried flags on all four templates, so the artifact printed
four locked declines and not one ordinary one — the commonest case a user hits,
missing entirely. Fixed to be symmetric. Worth recording because the defect was
invisible in the rule and obvious in the transcript, which is the whole argument
for producing a transcript rather than asserting the rule was sound.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py text
```

The **before** column, same probe copied into a worktree of the pre-D4a commit
so a difference between the columns is a difference in `core/`:

```bash
git worktree add .d4c_pre b72060e
cp docs/design/probes/d4_declines.py .d4c_pre/docs/design/probes/
cd .d4c_pre && PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py text
git worktree remove .d4c_pre --force
```

Both modes read only fields present on both sides of D4a — `result.disclosure`,
`Violation.describe`/`.macro`/`.kind`, `result.relaxation_applied`,
`outcome.skipped_locked_steps` — checked against `b72060e` rather than assumed,
per the 2026-08-08 amendment.

### What changed, in the prose itself

Full transcripts are reproducible from the commands above; the diff between
them, taken 2026-08-09, is 115 lines each side and reduces to four changes.

**1. Finding 30, visible as a user would have met it.** south_breakfast and
north_dinner, both CKD representatives:

```
BEFORE  protein_g is 35.6g, below its floor of 38.2g (locked by disclosed
        condition: chronic_kidney_disease; never relaxed)
AFTER   protein_g is 35.6g, below its floor of 38.2g (locked by a condition you
        disclosed, and never relaxed for that reason)
```

**2. Finding 24's empty-pool half.** south_lunch, both representatives — this
is the shape 54 of the grid's 105 south_lunch declines take:

```
BEFORE  no recipe combination survived filtering for this profile, so there was
        nothing to solve
AFTER   1 required course of this meal cannot be filled from the recipe library
        for this profile, so there was nothing to solve
```

**3. Finding 24's wrong-plate half.** north_dinner, 110 kg fat-loss vegetarian
with CKD. Before, the plate chosen by deviation score broke two bounds and the
decline named both; after, ranking by fewest-bounds-broken found a plate that
breaks one, and the fat ceiling — which that plate meets — is correctly no
longer mentioned. The protein figure moves with the plate, 56.0 → 55.4 g:

```
BEFORE  fat_g is 29.6g, above its ceiling of 29.3g;
        protein_g is 56.0g, below its floor of 59.4g (locked ...)
AFTER   protein_g is 55.4g, below its floor of 59.4g (locked ...)
```

**4. Shape counts regrouped in both directions**: south_lunch 12 → 11 distinct
shapes, north_dinner 2 → 1, but north_lunch 12 → **13**. Shape is keyed on which
bounds a decline names, and D4a changed which bounds get named, so both merging
and splitting are expected. Recorded rather than explained: the direction of the
move carries no quality signal on its own, and reading one into it would be the
same mistake as reading the deviation score as nearness.

### What the artifact shows that the counts could not

Finding **31** is now legible rather than described. Every after-column sentence
above still contains `protein_g` or `fat_g`, and north_lunch's most common
decline — the quality-source floor — reads well precisely because someone wrote
it a bespoke sentence with no identifier in it. That contrast, in one
transcript, is the input D9's copy map needs and is the reason this ran before
D9 rather than inside it.

The locked-decline sentence is also visibly the strongest thing the system
currently says, and it is two clauses long. "We did not try, and here is what we
would not compromise" is D9's centrepiece; it exists today and no screen shows it.

**Disposition:** D4c-i done. No `core/` change; the suite is unmoved at
`1 failed, 409 passed, 40 skipped, 1 warning in 114.79s`, the failure being
D10's deliberately-red test. Findings 31 and 36 untouched and OPEN, both D9.

---

## 2026-08-09 — finding 36, raised while scoping D4c

### Finding 36 — the identifier sweep describes coverage it does not have — **OPEN**

`tests/test_web_no_identifiers.py`'s module docstring says, of the views it
walks:

> The eight views are the ones a user can reach: the landing page, wizard steps
> 1-6, and the dashboard (plate picker, then whatever `POST /api/plan`
> returns — a solved plate **or an honest decline, both of which render copy**).

The decline half is false, and has been since D3. The fixture's profile is
74 kg / 176 cm / 31 / male / moderate / maintain / vegetarian with
`chronic_kidney_disease`, and it clicks `#dashGenerate` without touching the
plate picker. `web/dashboard.html:71` has `south_indian:breakfast` checked by
default. Measured against today's real library:

```
$ PYTHONHASHSEED=0 PYTHONPATH=. python -c "...plan_meal for the sweep profile..."
south_indian breakfast -> PLATE   | skipped_locked ()
south_indian lunch     -> DECLINE | skipped_locked ('protein_tolerance',)
     sodium_mg is 1546.0mg, above its ceiling of 1400.0mg (more than one plate
     may take of a whole day's allowance) (locked by a condition you disclosed,
     and never relaxed for that reason)
north_indian lunch     -> PLATE   | skipped_locked ()
north_indian dinner    -> PLATE   | skipped_locked ()
```

So `dashboard_after_plan` renders the success view on every run. The decline
view has never been swept. It is one radio click away, and the sentence waiting
there contains `sodium_mg` — finding 31, live, and exactly the token shape this
file exists to catch.

**Why this is its own finding and not a note inside D4c.** D4c already records
that the sweep never renders a decline. What it did not record is that the file
*claims otherwise in its own words*. Those are different defects. The first is
a coverage gap; the second is a coverage gap that reports itself as covered,
which is the class this repository's process rule is built against — and it is
worse here than elsewhere, because the docstring is a long, careful argument
about why grepping for known strings cannot work. A reader who accepts that
argument has no reason to check whether the sweep reaches the view it says it
reaches. The care in the prose is what makes the false clause load-bearing.

Same family as finding 32 (a region-filter test whose assertion documented the
unenforced filter) and the D4b-ii note about a test overstating its reach. This
is the third instance, so it is a pattern rather than a slip: **a test's own
description of its scope is not evidence of its scope, and is read by more
people than the code is.**

**Disposition: OPEN.** Not fixed here, per the queue's rule about not fixing
what a task notices in passing — and it cannot be honestly fixed in isolation
anyway. Correcting the docstring to describe what the sweep really does would
make the file accurate and leave the hole; making the sweep reach a decline
turns it red on finding 31, whose remedy is a macro-to-copy map that belongs to
D9. Both halves are therefore assigned to D9, which is renamed to say so.

---

## 2026-08-09 — D4b-ii: the nine missing tests, each shown red first

Closes findings **32** and **34**, and decides **33**. Fourteen tests across
three files, covering the nine mechanisms the D4b-i sweep left uncovered.

Every one was shown failing against its own deleted mechanism before being
believed, which is the entire point of the exercise and is not a claim to take
on trust — the transcript is below.

### The measurement

```
9 mechanisms: 9 covered, 0 soft-covered, 0 SURVIVED, 0 harness errors.
C3   covered      tests/test_planner_candidates.py::TestHardFilters::test_region_mismatch_excludes_a_recipe
S6   covered      tests/test_planner_solver.py::TestTheEmptyPlate::test_an_empty_plate_is_rejected_by_a_floor
S7   covered      tests/test_planner_solver.py::TestUnsetQualityProteinIsConservative::test_the_default_is_zero
V8   covered      tests/test_planner_validator.py::TestBoundSourceIsProvenanceNotAGuess::test_the_source_becomes_the_guard_once_rung_one_is_clipped
V10  covered      tests/test_planner_validator.py::TestRungFourInIsolation::test_a_locked_protein_floor_is_returned_untouched
V11  covered      tests/test_planner_validator.py::TestRungFourInIsolation::test_the_protein_ceiling_passes_through_unchanged
V16  covered      tests/test_planner_validator.py::TestTheDeclineExplainsItself::test_a_failed_result_without_a_disclosure_is_refused
V20  covered      tests/test_planner_validator.py::TestBoundSourceIsProvenanceNotAGuess::test_the_source_is_read_off_the_target_not_inferred
V22  covered      tests/test_planner_validator.py::TestTheDeclineExplainsItself::test_the_protein_disclosure_keeps_one_decimal
```

Each row names a correctly-scoped test, and in each case it is the test written
for that mechanism rather than something incidental. The suite itself:

```
1 failed, 409 passed, 40 skipped, 1 warning in 111.18s
FAILED tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants
```

395 → 409 is the fourteen new tests exactly. The one failure is D10's
deliberately-red test, unchanged and untouched.

### Finding 35 — the harness's verdict depended on the shell that launched it — **FIXED**

The first run of the sweep above returned this, for all nine rows:

```
9 mechanisms: 0 covered, 9 soft-covered, 0 SURVIVED, 0 harness errors.
C3   soft-covered 1 incidental: (non-test failure; see output)
```

Nothing was wrong with the tests. `_run_suite` classified by matching
`line.startswith("FAILED ")`, and pytest had written its summary as
`"\x1b[31mFAILED\x1b[0m tests/..."`, so no line matched and every mutation was
recorded as a crash. Confirmed by running one mutation (`V22`) through the
identical `subprocess.run` call and printing the raw bytes:

```
returncode: 1
FAILED tests/test_planner_validator.py::TestTheDeclineExplainsItself::test_the_protein_disclosure_keeps_one_decimal - AssertionError: assert '29.5g' in 'This plan delivers 30g of protein agains...
1 failed, 408 passed, 40 skipped, 1 deselected, 1 warning in 108.02s
```

The right test failed, alone, for the right reason. Only the parser was blind.

**Why this is a finding and not a typo.** pytest colours output when
`FORCE_COLOR`/`PY_COLORS` is inherited, and suppresses colour when stdout is a
plain pipe. So the harness gave a *different answer for identical code
depending on which shell ran it* — the same class as findings 11 and 18 in this
log, and the one the probe exists to prevent. The D4b-i numbers already
recorded above were taken in an uncoloured shell (had they not been, all 55
rows would read "non-test failure" instead of naming test ids), so they stand
— but they stood by luck.

**Disposition:** FIXED. Three independent defences, since any one of them can
be defeated by an environment: `--color=no` on the command, the three colour
env vars forced off in the subprocess, and an ANSI strip before matching.

### Finding 32 — CLOSED

`test_region_mismatch_excludes_a_recipe` no longer feeds `SOUTH_LUNCH` a recipe
the category filter would have rejected anyway. It now builds two synthetic
components differing **only** in region — same category (`poriyal`, asserted to
be one `SOUTH_LUNCH` accepts), same ingredient, same serving unit — and checks
the southern twin survives before checking the northern one does not. The
control is the load-bearing half: without it, an empty pool proves nothing
about which filter emptied it, which is precisely how the old test passed
against a deleted region check.

A second test covers the other arm of the same condition,
`not in (template.region, Region.PAN_INDIAN)`: a mutation narrowing it to the
template's region alone would silently drop every pan-Indian recipe from every
plate while leaving the first test green.

The observation underneath finding 32 is unchanged and still true — the real
library's categories are region-partitioned, so the region filter does no work
on today's data. It is now tested rather than dormant-and-untested.

### Finding 33 — CLOSED, decided in opposite directions

The two dead-code survivors got different answers, because they are not the
same case.

**`C8`, `for_slot`'s `seen` dedup — REMOVED.** Being unreachable would on its
own argue for keeping it: harmless, cheap, defensive. The reason to remove it
is that it does not guard the duplicate a reader would assume it does. One
recipe offered under two categories a slot both accepts produces components
with *different* ids (`r@a`, `r@b`), so the same dish appears twice and the
dedup never fires. Code that reads like a duplicate guard, while not handling
the only duplicate that can actually occur, is worse than no guard — the next
person to face that case will believe it is already handled. The invariant that
makes the sort total without it is now stated in `for_slot`'s docstring.

**`B2`, `enumerate_combinations`' early `return ()` — KEPT, with a comment.**
Its deletion is behaviour-preserving for the return value, as recorded. What it
preserves is the *diagnosis*: falling through reaches the second `logger.info`,
which reports "0 combinations, naive bound N, Nx smaller" — an enumeration that
pruned everything — and never names the blocking slot. Those are different
facts about the library and only one of them is what a decline is built from.

`C8`'s row is deleted from the probe rather than left to report "pattern not
found" forever. `B2` keeps its row, retargeted at the surviving line, with its
expected result recorded as *survives* — a row whose answer is known is worth
more than no row, because it stops the next sweep rediscovering it as news.

Re-measured after both edits, since removing code from `for_slot` could have
taken the coverage of the mechanism beside it as well:

```
4 mechanisms: 3 covered, 0 soft-covered, 1 SURVIVED, 0 harness errors.
C3   covered      tests/test_planner_candidates.py::TestHardFilters::test_region_mismatch_excludes_a_recipe
C7   covered      tests/test_planner_determinism.py::TestOrderDoesNotDependOnCategoryIteration::test_candidates_come_back_sorted_by_id
B2   SURVIVED
V10  covered      tests/test_planner_validator.py::TestRungFourInIsolation::test_a_locked_protein_floor_is_returned_untouched
```

`C7` is finding 18's `for_slot` sort — the line immediately below the deleted
dedup — and it still goes red on its own deletion. `B2` survives with its
retargeted row located, which is the documented expected answer rather than a
harness error.

### A harness change that was needed to do this honestly

The probe ran whatever `git worktree add HEAD` checked out, so it could only
grade already-committed code. That inverts the practice it enforces:
`CLAUDE.md` says to watch a test fail before believing it, and a test you must
commit before you can watch it is a test you have already believed. It bit
twice in one session — first on the new tests, then again on `B2`'s retargeted
row, which reported "pattern not found" against a `core/` that predated the
edit the row was written for, reading as a harness error rather than as the
stale checkout it was.

Both `core/` and `tests/` are now copied in from the working tree. The worktree
contributes isolation and nothing else, which was its only stated job in this
probe anyway. The id filter (`... d4b_mutations.py C3,V10,V11`) exists for the
same reason — grading nine mechanisms should not cost a 55-run sweep.

### On the two tests the reviewer asked to look at

`V10`'s test states in its own body that it calls `_relax_protein` directly
because the ladder cannot reach the guard, and names `RelaxationStep.
is_fully_locked` as the reason, with the instrumentation result (395 passed,
branch never executed) quoted. Without that, it reads as an ordinary
clinical-locking test and the next reader concludes the ladder path is covered
by it — finding 32's failure mode inverted, a test overstating its reach. It
also points at `V13`, which is what actually covers the ladder path.

`V11`'s test asserts the protein ceiling's **value** is unchanged (90.0 before,
90.0 after), not that some plate fits under it, mirroring the claim
`_relax_protein`'s docstring makes. It then walks all four rungs cumulatively,
since a later rung reconstructing the target could move the ceiling just as
silently as this one could.

**Disposition:** findings 32, 33, 34 CLOSED. Finding 35 raised and FIXED.
**Finding 26 CLOSED** — it asked for a deletion test on every gate in the
enumeration, solver and validator paths, an audit of the gates without one, and
the practice written into `CLAUDE.md`. The count and audit landed in D4b-i, the
practice is in `CLAUDE.md`'s "Deletion testing" convention, and the gaps that
audit found are closed here. Two survivors remain and both are documented
expected results, not gaps: `B2` above, and `B8` (the quality pre-filter, which
`CLAUDE.md` already states is "a pure optimisation: removing it changes no
verdict"). `B5` remains a bad mutation of the probe's own and is not a
mechanism. Findings 22, 28, 29, 31, 2, 15, 20 untouched.

---

## 2026-08-09 — D4b-i: every gate in the planner, deleted one at a time

Finding 26 asked for a deletion test on every gate and guard in the
enumeration, solver and validator paths, and said to "count them first and say
the number." This entry is the count and the coverage audit. The tests the
audit calls for are **not** in this commit; they are D4b-ii.

Everything below comes from `docs/design/probes/d4b_mutations.py`, which holds
one entry per mechanism and the smallest edit that deletes it, applies each edit
to a throwaway git worktree, runs the suite, records which tests fail, and
reverts. The real checkout is never written to.

### The count: 55, not the ~25 the task estimated

| module | mechanisms |
| ---------------------------- | ---: |
| `core/planner/candidates.py` | 9 |
| `core/planner/combinations.py` | 8 |
| `core/planner/solver.py` | 11 |
| `core/planner/validator.py` | 27 |

`validator.py` is where the estimate went wrong. The ladder is not one
mechanism but roughly a dozen: `_capped`'s clip, `_widen_band`'s two skips and
its `replace`-rather-than-reconstruct, rung 1's widen-don't-drop, each rung's
locked-macro skip, the order of `RELAXATION_ORDER` itself, the fully-locked-rung
skip, and the three construction-time checks in
`ValidationResult.__post_init__`. Each is separately deletable and separately
load-bearing. D4a's five injections are excluded from the count, per the task.

### The result

```
55 mechanisms: 41 covered, 1 soft-covered, 13 SURVIVED, 0 harness errors.
```

**covered** — at least one correctly-scoped test fails when the mechanism is
deleted. **soft-covered** — tests fail, but only end-to-end ones that do not
know what they are protecting. **SURVIVED** — nothing in the suite fails.

"Correctly scoped" is a file-level judgement, written down in the probe as
`OWN_TESTS` rather than applied silently per row. `tests/test_planner_plan.py`
is deliberately scoped to nothing: it is the wiring test, by its own docstring.

### Two measurement errors made while producing this, both corrected

**`-x` cannot classify.** The first sweep ran `pytest -x`, so each row recorded
the first failure in pytest's *collection* order — alphabetical by filename,
unrelated to which test is about the mechanism. It reported the solver's
quality gate (`S3`, finding 26's own founding example) as held up by
`test_planner_plan.py`, and two mechanisms as held up by `test_api_auth.py`,
producing an apparent "a third of the suite is soft coverage" that was pure
alphabetical artifact. Running `tests/test_planner_quality.py` alone against
the same mutation gives:

```
FAILED tests/test_planner_quality.py::TestTheSolverGateItself::test_the_gate_changes_the_chosen_unit_counts
FAILED tests/test_planner_quality.py::TestTheSolverGateItself::test_the_gate_can_empty_a_solve_the_pre_filter_admitted
2 failed, 34 passed in 1.64s
```

Two tests named after the gate. **Finding 26's founding example is genuinely
covered** — `TestTheSolverGateItself` was added after the finding was raised.
The probe now runs the whole suite every time and collects every failure.

**Plate-pinning tests inflate "covered", and were checked rather than assumed.**
Six rows were attributed to `TestAgainstTheRealLibrary` classes, which pin an
exact plate and so break on almost any planner change despite living in scoped
files. `UNSCOPED_CLASSES` now excludes them, and the sweep was re-run. **The
totals did not move**: every one of the six had a second, properly-scoped test
behind the pin (`S1`/`S2`/`S8`/`S9` → `TestTheSolverGateItself`, `S5` →
`TestThePerturbationTest`, `V26` →
`TestLadderFires::test_the_sodium_rung_fires_first_and_silently`). 41 is not an
upper bound.

### Finding 32 — the region hard filter is unenforced, and its test says so — **OPEN**

Deleting the region check in `_passes_hard_filters` entirely — letting a North
Indian recipe into a South Indian template — breaks nothing in the suite. A
correctly-named test exists and asserts too little:

```python
def test_region_mismatch_excludes_a_recipe(self, library, ingredients):
    # rajma_chawal is north_indian; south_lunch's region is south_indian
    # and rajma_chawal is not pan_indian, so it must not appear even
    # though combo_rice_legume is not a south_lunch category anyway.
    ...
    assert pool.by_category == {}
```

The comment concedes the redundancy and the assertion is satisfied by the
*category* filter alone. Nor can the fixtures express the case: `make_recipe`
defaults `region=Region.SOUTH_INDIAN` and nothing overrides it.

Underneath that: **the real library's categories are region-partitioned**, so
the region filter is redundant with the category filter for every recipe that
exists today. North carries `sabzi`/`dal`/`roti`/`raita`/`legume_curry`/
`combo_rice_legume`; south carries `tiffin`/`sambar`/`kuzhambu`/`chutney`/
`rice`/`mixed_rice`/`poriyal`/`kootu`/`curd`. Nothing overlaps. The gate is real
but dormant, and starts binding the first time a category spans regions.

This qualifies a claim in `CLAUDE.md`'s build-status table: D3 argues the north
plates "could not fail to be" unchanged because "`candidates.py` rejects a
recipe whose region is neither the template's nor `pan_indian`." The conclusion
holds, but for today's data it holds via the category filter — the region filter
does no work. Noted rather than edited, since the conclusion stands.

**Disposition:** OPEN. The fix is a synthetic fixture carrying a south category
with `region=Region.NORTH_INDIAN`, following the precedent of
`test_allergen_overlap_excludes_a_recipe`, which builds synthetic rather than
borrowing from the library. D4b-ii.

### Finding 33 — two survivors are dead code, not missing coverage — **OPEN**

Neither can be covered by any test, because deleting them is behaviour-preserving
for every possible input.

- **`C8`**, `for_slot`'s `seen` deduplication. `Component.id` is
  `f"{recipe.id}@{category}"` and `build_candidate_pool` files each component
  under `by_category[component.category]`, so the bucket a component sits in is
  always the category embedded in its own id. Iterating a slot's accepted
  categories cannot yield the same id twice.
- **`B2`**, `enumerate_combinations`' early `return ()` when a required slot has
  no legal selection. `itertools.product` over a sequence containing an empty
  slot is empty anyway — verified, not reasoned:
  `list(itertools.product(('a','b'), (), ('c',))) == []`. The early return
  changes only a log line.

**Disposition:** OPEN, deliberately not fixed here. Deleting code in
`core/planner` is outside this commit's scope (harness plus audit), and the
right disposition for each — remove, or keep with a comment saying it is
defensive — is a judgement worth making on its own.

### Finding 34 — eight mechanisms have no test that fails on their deletion — **OPEN**

| id | module | mechanism |
| --- | --- | --- |
| `S6` | `solver.py` | an empty plate is still gated (0 g of qualifying protein) |
| `S7` | `solver.py` | unset quality protein defaults conservatively to 0.0 |
| `V8` | `validator.py` | the `bound_source` follows the number when the guard clips it |
| `V10` | `validator.py` | rung 4 skips protein entirely when a flag locks it |
| `V11` | `validator.py` | rung 4 lowers the floor only, never raises the ceiling |
| `V16` | `validator.py` | a failed result must carry a disclosure |
| `V20` | `validator.py` | `bound_source` is read off the target, never inferred |
| `V22` | `validator.py` | the protein disclosure keeps one decimal |

Three survivors are not in this table and are not gaps. `B5` is a bad mutation
of the probe's own: it mutates the *low* side of `quality_protein_bounds`, and
every caller reads `[1]` — grepped, nothing reads `[0]`. `B8` is expected and
already documented: `CLAUDE.md` states the quality pre-filter is "a pure
optimisation: removing it changes no verdict," and the sweep confirms the doc.
`C3` and the two dead-code rows are findings 32 and 33.

**Disposition:** OPEN. D4b-ii writes these eight plus finding 32's fixture fix.

### The V10 misdiagnosis — a survived mutation is not a hole until reachability is checked

`V10` was first reported as a live clinical-safety hole: deleting
`if "protein_g" in locked: return target` from `_relax_protein` would let a
chronic-kidney-disease profile have its protein floor lowered, and nothing
failed. That reading was wrong, and it was wrong in the direction that causes
work to be misprioritised — it was nearly given its own commit ahead of
lower-stakes tests on that basis.

Rung 4's `macros` is exactly `("protein_g",)`, and CKD is the only flag locking
protein, so `RelaxationStep.is_fully_locked` is true whenever the guard would
matter and the ladder skips the rung before `_relax_protein` is ever called.
Checked by instrumenting rather than by argument — an unconditional
`raise AssertionError` placed inside the guard, whole suite run:

```
395 passed, 40 skipped, 1 deselected, 1 warning in 88.77s
probe never fired: 0
```

The branch is never reached. The clinical property is enforced, by `V13`
(`test_a_fully_locked_rung_is_skipped_not_recorded_as_applied`, which pins the
CKD floor at 32.0 g). `V10` is defence-in-depth against a future rung that
groups protein with another macro, where `is_fully_locked` would be false. It
still earns a test — called directly, and the test must say in its own body why
it bypasses the ladder, or it will read as an ordinary clinical-locking test and
the next reader will believe the ladder path is covered by it.

**No survivor is a live clinical-safety hole.** Clinical locking is covered on
every rung: `V3` (rung 2), `V13` (rung 4 skip), `V27` (the decline sentence).

The general lesson, now in `CLAUDE.md`'s standing list: the harness makes
survivors cheap to produce, which makes this misreading the one most likely to
recur.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4b_mutations.py solver
```

The second form limits the sweep to one module while iterating. A full run is
55 suite runs and takes roughly 40 minutes; it prints each row as it completes.

One note on the run that produced the figures above: it printed its complete
55-row table and summary and removed its worktree, but the shell reported exit
code -1. The artifact is complete and the numbers are the numbers; the exit code
is unexplained and is recorded here rather than guessed at.

**Disposition:** finding 26 measured, still OPEN — the count and the audit it
asked for exist; the tests do not yet. Findings 32, 33 and 34 raised, all OPEN,
all D4b-ii. Finding 24 CLOSED (2026-08-08) is untouched. Findings 22, 28, 29,
31, 2, 15, 20 untouched.

---

## 2026-08-08 — D4a: finding 24 closed on the decline path

> Title corrected 2026-08-09. It read "findings 24 and 26 closed" while this
> entry's own Disposition line said finding 26's sweep "is D4b and remains
> OPEN" — a heading claiming a closure the body denied, which is the class of
> unverified state claim `CLAUDE.md`'s process rule exists to prevent. Finding
> 26 is measured by the 2026-08-09 entry above and is still open until its
> tests land.

Scope note first, because it changes what the queue says. **D4 as written is
two tasks and only the first is done here.** Its second half — finding 26's
standing practice: a deletion test for every gate and guard in the
enumeration, solver and validator paths, an audit of the existing suite for
gates without one, and writing the practice into `CLAUDE.md` — is a full task
against three modules and ~25 mechanisms, and stapling it to a redesign of the
decline path would have produced one commit nobody can review. It is split out
as **D4b** and is NEXT. What is done here is the decline diagnosis, plus
deletion tests for the five mechanisms this change introduced (below), which is
finding 26's discipline applied to this change rather than to the whole suite.

Every figure below is from
`PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py`
(144 profiles x 4 templates, today's `data/` library, `dev_mode=True`) or from
the `demo.py` commands in "Reproduce".

### The measurement, before and after

The probe sweeps a profile grid, keeps every decline, and compares what the
decline **says** against two things computed independently of the code under
audit: which bounds are structurally unreachable (from each component's
serving-unit min/max), and which bounds the combination closest to feasible
misses.

|                                                        | before | after |
| ------------------------------------------------------ | -----: | ----: |
| declines across the grid                                |    156 |   156 |
| declining with an empty pool, naming no slot            |     72 |     0 |
| omitting a cause that is actually blocking              |     12 |     0 |
| naming a bound as blocking that the nearest plate meets |     30 |     0 |
| distinct decline shapes                                 |     50 |    36 |

The verdicts themselves did not move: 156 declines before and after, and
`tests/test_planner_decline.py::TestAgainstTheRealLibrary` pins that the
reference profile still gets a plate on all four templates. This changed what a
decline says, not who is declined.

**Both columns above are re-measurable; the commands are in "Reproduce" below.**
Corrected 2026-08-08, after the entry was first written: as originally committed
the before column was **not** reproducible. `d4_declines.py` read
`Violation.blocking_slots` directly, and that field does not exist before D4a,
so the probe raised on the pre-D4a tree and only the after column could be taken
again. The numbers were real when taken and both reproduce unchanged now that
the probe runs on both trees — but "real when taken" is precisely the standard
`CLAUDE.md`'s process rule rejects, and a delta nobody can re-measure is not
evidence, whatever its provenance. The fix is one `getattr` with the reason
written at the call site; every other field the probe touches was checked to be
present in both trees rather than assumed. A probe that measures a change has to
run on both sides of it, and that is a property to check when the probe is
written, not after someone asks.

### Finding 24 — CLOSED

Two defects, opposite directions, one cause: `_blocking_violations` stopped at
the first thing it found.

**It stopped at the first cause.** The function returned the
structurally-unreachable bounds *or*, only if there were none, the nearest
plate's misses. From slice 4 onward a South Indian decline named the
quality-protein floor and nothing else, because an unreachable quality floor
made the first half non-empty and the second half never ran. Recorded at the
time as "a decline can now say less than it used to" (2026-08-07, OPEN); it is
this. Both halves now always run and merge, keyed by `(macro, kind)` so a bound
reported unreachable is not also reported jointly infeasible.

**When it did reach the second half, it picked the wrong plate.** The nearest
combination was chosen by the solver's deviation score. That score measures
distance from each macro's ideal *point*, and sodium and fibre have no
registered point at all (`core.nutrition.target.simple_target`), so a plate's
saltiness contributes exactly nothing to it. Measured, 110 kg fat-loss
vegetarian, `north_lunch`:

    BEFORE
      kind='above_ceiling' macro='fat_g'     actual=37.1   bound=34.1
      kind='above_ceiling' macro='sodium_mg' actual=1418.5 bound=1400.0

    AFTER
      kind='below_floor'   macro='protein_g' actual=54.9   bound=58.9
        reach='jointly_infeasible' relaxability='relaxed_to_limit'

A plate existed — phulka x3, soya_chunk_curry x2, paneer_masala x1 — that met
both named bounds and broke only the protein floor. The user was told to go
looking for leaner, less salty dishes to fix a protein shortfall. Ranking is now
**fewest bounds broken**, tie-broken by score.

### The structure a decline screen needs

Two token vocabularies on `Violation`, in the same style as
`core.nutrition.target.BOUND_SOURCES` and subject to the same rule — they are
`snake_case` identifiers, they cross the API, and they must never reach a
visible text node.

- `VIOLATION_REACH`: `unreachable` (no plate this library can build satisfies
  it, so no substitution helps) | `jointly_infeasible` (reachable alone, not
  alongside the rest) | `plate_miss` | `empty_pool`. Finding 24's actual
  complaint was that these were indistinguishable.
- `VIOLATION_RELAXABILITY`: `relaxable` | `relaxed_to_limit` | `hard_capped`
  (a rung fired and `_capped` clipped it — the sodium guard's shape) | `locked`
  (a disclosed condition; the one case where "we did not try" is the honest
  answer) | `never_relaxed` (no rung touches it at all — the quality floor).
  Derived from `RELAXATION_ORDER` itself, not a hand-kept table, so a rung
  added later cannot leave a stale classification behind.

`Violation.blocking_slots` carries the required courses that had no legal
selection. Sourced from `core.planner.combinations.unfillable_slots`, which
calls the enumerator's own `_slot_selections` rather than asking whether the
slot has candidates — a slot with two candidates and `min_selections=3` has
candidates *and* no legal selection, and the obvious implementation would name
nothing. Measured, vegan `south_lunch` (the one real-library pair that
enumerates zero combinations):

    BEFORE  no recipe combination survived filtering for this profile, so
            there was nothing to solve
    AFTER   1 required course of this meal cannot be filled from the recipe
            library for this profile, so there was nothing to solve
            blocking_slots=['curd_course']

### Finding 30 — a clinical-flag identifier was being written into user-facing prose — FIXED in the same commit

Found while carrying relaxable-vs-locked through. `Violation.describe` built
`f"(locked by disclosed condition: {names}...)"` from `ClinicalFlag.value`, so a
kidney-disease decline rendered the string `chronic_kidney_disease` into the
sentence `web/dashboard.js` displays verbatim. This is precisely the class
`tests/test_web_no_identifiers.py` exists to catch, and it missed it because no
web test renders a locked decline — the sweep is over static views, and a
decline disclosure is server-supplied.

Worse, `tests/test_planner_validator.py` **asserted the leak**:
`assert "hypertension" in outcome.result.disclosure`. It passed for months.
The prose now names no condition and the tuple travels as `locked_by`; that
assertion is inverted, and now also loops every `ClinicalFlag` value rather
than checking the one that happened to be in the test.

### Finding 31 — macro identifiers are still written into the same prose — **OPEN**

Noticed while fixing finding 30, logged and left per the queue's rule.
`Violation.describe` writes `f"{self.macro} is {actual}..."`, so a decline reads
`energy_kcal is 350.0kcal, above its ceiling of 300.0kcal`. Same defect class as
finding 30, same missed detection, and unfixed here because the remedy is a
macro-to-copy map, which is a decision about the screen and D4 says explicitly
not to design the screen. The structured fields a client needs to render it
properly (`macro`, `kind`, `actual`, `bound`, `bound_source`, `reach`,
`relaxability`) are all present and reach the API. Belongs with **D9**.

Related and also unfixed: `test_web_no_identifiers.py` cannot see either leak,
because it sweeps rendered static views and never exercises a decline. Whatever
D9 does about the copy, the sweep needs a decline in it or the third instance
of this class will be found the same way.

### Finding 26's discipline, applied to this change

Five mechanisms were introduced. Each was deleted, the suite re-run, and the
test that names it confirmed red before the mechanism was restored:

| defect injected                                                      | went red                                          |
| -------------------------------------------------------------------- | ------------------------------------------------- |
| rank nearest plate by `score` alone (`key = (0, plan.score)`)         | 4 tests, incl. `test_it_does_not_report_the_first_enumerated_plate_instead` |
| restore `if unreachable: return unreachable`                          | `test_an_unreachable_bound_no_longer_hides_the_reachable_ones` |
| `unfillable_slots` asks `not pool.for_slot(slot)`                     | `test_a_slot_with_candidates_but_no_legal_selection_still_counts` |
| `_relaxability` returns a constant                                    | 3 tests in `TestRelaxabilityIsDerivedFromTheLadderItself` |
| re-interpolate `ClinicalFlag.value` into `describe`                   | `test_with_hypertension_the_same_target_is_declined_instead` |

The joint-infeasibility fixture is built so its expected values are exact
rather than envelopes: `tests/factories.py`'s FEASIBILITY components pin
`min_count = max_count = 1`, so each of the four combinations is one point.
`TestTheLadderIsInertOnThisTarget` checks that all four rungs fire and move
nothing, so every hand-computed figure in that file stays valid if a rung
gains an effect later — the alternative was a comment asserting it.

### Reproduce

The **after** column of the table above, and every figure in this entry that is
not marked "before":

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py
python demo.py plan --region north_indian --meal-slot lunch --weight-kg 110 --goal lose_fat
python demo.py plan --region south_indian --meal-slot lunch --diet vegan
python -m pytest tests/test_planner_decline.py -q
```

The **before** column. The probe is copied into a worktree of the pre-D4a
commit rather than run from the old tree's own copy, so both columns come from
one probe implementation and a difference between them is a difference in
`core/`, not in how the two probes counted:

```bash
git worktree add /tmp/pre_d4a b72060e
cp docs/design/probes/d4_declines.py /tmp/pre_d4a/docs/design/probes/
cd /tmp/pre_d4a && PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d4_declines.py
git worktree remove /tmp/pre_d4a --force
```

`b72060e` is D5, the commit D4a was built on. Both runs, 2026-08-08:

```
before: 156 declines across the grid, 50 distinct shapes.
          72 decline with an empty pool, naming no slot
          12 omit a cause that is actually blocking
          30 name a bound as blocking that the nearest plate meets

after:  156 declines across the grid, 36 distinct shapes.
          0 decline with an empty pool, naming no slot
          0 omit a cause that is actually blocking
          0 name a bound as blocking that the nearest plate meets
```

**Disposition:** finding 24 CLOSED. The 2026-08-07 observation "a decline can
now say less than it used to" CLOSED — it was finding 24. Finding 30 FIXED.
Finding 31 OPEN, for D9. Finding 26's full sweep is D4b and remains OPEN.
Findings 22, 28, 29, 2, 15, 20 untouched.

---

## 2026-08-08 — D5: finding 22 re-scoped, and D5's own premise was wrong

Every figure below is from
`PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d5_margins.py`,
reference profile (70 kg / 175 cm / 28 / male / moderate / maintain /
vegetarian), today's `data/` library, `dev_mode=True`. Nothing was edited:
the guard sweep wraps `citations.value_of` in memory and restores it.

### D5's premise, restated and then contradicted

TASKS_2.MD's D5 says: "whether the app can plan a South Indian lunch currently
turns on half a percent of a number nobody derived." That reads the 8.9 mg
figure as the verdict's sensitivity to the guard. It is not. It is the chosen
**plate's** slack against the guard. Those are different quantities, and the
second one was never measured until now.

Measured — the guard moved, everything else held, pass/decline bisected over 40
iterations:

```
  Bisected pass/decline boundary per template (40 iterations):
    south_indian/breakfast: flips at 0.504835 =  1009.7 mg; registered 0.70 = 1400.0 mg is 390.3 mg (27.9%) above it
    south_indian/lunch: flips at 0.545743 =  1091.5 mg; registered 0.70 = 1400.0 mg is 308.5 mg (22.0%) above it
    north_indian/lunch: flips at 0.466169 =   932.3 mg; registered 0.70 = 1400.0 mg is 467.7 mg (33.4%) above it
    north_indian/dinner: flips at 0.436229 =   872.5 mg; registered 0.70 = 1400.0 mg is 527.5 mg (37.7%) above it
```

south_lunch does not stop passing at 1391 mg, or at 1300, or at 1200. It stops
passing at **1091.5 mg** — the guard would have to fall 22% before the verdict
moves. The verdict's margin on the guard is 308.5 mg, not 8.9 mg. **The goal as
written was wrong**, in the specific way TASKS_2.MD's "How to work this file"
anticipates, and this is the third time.

What actually happens as the guard falls is that the plate changes and the
ladder walks further, verdict intact:

```
  0.55 -> guard  1100.0 mg | south_break=pass(2r,1072mg)  south_lunch=pass(4r,1091mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(2r,872mg)
  0.60 -> guard  1200.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(4r,1091mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1148mg)
  0.65 -> guard  1300.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(4r,1246mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1148mg)
  0.70 -> guard  1400.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(3r,1391mg)  north_lunch=pass(0r,992mg)  north_dinne=pass(0r,1371mg)
  0.80 -> guard  1600.0 mg | south_break=pass(0r,1190mg)  south_lunch=pass(0r,1546mg)  north_lunch=pass(0r,1431mg)  north_dinne=pass(0r,1371mg)
```

The 4-rung south_lunch at 0.55–0.65 is worth noticing on its own: rung 4 is
protein tolerance, which carries mandatory disclosure. A tighter guard does not
turn south_lunch off, it turns it into a plate that has to apologise for its
protein.

### Finding 22, re-stated in its current form — still **OPEN**

The 2026-08-02 wording ("a multi-dish South Indian plate cannot get under the
sodium guard"; two of three south_lunch combinations unreachable at their
minimum counts) is **obsolete**: D3's `steamed_rice` and `soya_kuzhambu` changed
the enumerated set (3 -> 12 combinations), and all four templates now pass. The
finding survives in a narrower form:

> **Sodium is the only bound in the system whose ceiling is a project decision
> with no derivation, and it is simultaneously the bound closest to two of the
> four passing plates.** south_lunch sits 8.9 mg (0.6%) under it; north_dinner
> sits 28.7 mg (2.0%) under it. Both are hard-ceiling contacts — no relaxation
> rung may widen past 1400 mg, so a plate 9 mg over it is a decline with no
> recourse, however loose every other bound is.

Note the correction embedded there: the D5 task asked whether the other three
templates have comparable margins. **north_dinner does** — 28.7 mg, 2.0%, and
tighter still by the measure that matters (see below). Nobody had noticed it
either. south_breakfast (210.2 mg, 15.0%) and north_lunch (407.8 mg, 29.1%) do
not.

### Slack is the wrong unit; the smallest legal move is the right one

Portion space is integer unit counts, so a bound is not "nearly breached"
because slack is small in absolute terms — it is tight when slack is smaller
than the smallest legal one-unit move on that plate. By that measure the
sodium picture inverts:

| template | Na slack | smallest legal move raising Na | verdict |
|---|---|---|---|
| south_breakfast | 210.2 mg | 40.9 (chutney 2->3) | loose |
| south_lunch | **8.9 mg** | **2.0** (steamed_rice 1->2) | **loose** |
| north_lunch | 407.8 mg | 59.9 (phulka 5->6) | loose |
| north_dinner | **28.7 mg** | **59.9** (phulka 3->4) | **TIGHT** |

south_lunch's famous 8.9 mg is *not* a cliff edge in unit space: unsalted rice
is available in 2.0 mg increments, so the plate has room to move without
touching the guard. north_dinner's 28.7 mg **is** a cliff: every legal increment
on that plate costs at least 59.9 mg of sodium.

Both south plates and both north plates were also checked against every legal
single-unit neighbour, which is the honest version of the per-macro `step`
number because one unit move changes every macro at once:

```
south_lunch  -> 0 of the plate's single-unit neighbours are feasible
north_lunch  -> 0 of the plate's single-unit neighbours are feasible
north_dinner -> 0 of the plate's single-unit neighbours are feasible
south_breakfast -> 1 (coconut_chutney 2->3)
```

Three of the four passing plates are **point solutions**: not one adjacent
portion assignment is admissible. That is a property of a narrow library and
tight energy bands, not of sodium — the neighbours die on `energy_kcal` far
more often than on `sodium_mg`.

### What could change, and what each costs — **not picked, deliberately**

D5 says lay out the options and do not choose. Five, with the cost of each:

1. **Move the guard's value.** Cheapest to do, and now measured to buy nothing:
   the verdicts are stable from 0.55 to 1.00. Its real effect is on plate
   *choice* and rung count, not on pass/fail. Cost: re-registering a
   `PROJECT_DECISION` for an effect the sweep says is not the one anyone
   thought it had.
2. **Remove the guard.** The 2026-08-02 entry records why it exists: a bare
   remaining-budget check puts no limit at all on the first meal of a day, and
   a 1649.3 mg lunch passed one. Cost: that case returns.
3. **Let rule (ii) relax.** `core/nutrition/meal_target.py` states the reason it
   does not: rung 1 widens sodium by 0.50, so a widenable 0.70 guard permits a
   plate carrying 105% of a day's sodium. Cost: exactly that, and it is the
   outcome the guard was introduced to prevent.
4. **Re-derive the salt lines.** The sensitivity is measurable and is the axis
   D5's goal is actually about, since recipe work moves the plate and not the
   guard. Measured, every `sodium_mg` in the library scaled uniformly:
   ```
    south_indian/breakfast: still passes at x1.387 (+38.7% on every salt figure in the library)
    south_indian/lunch: still passes at x1.283 (+28.3% on every salt figure in the library)
    north_indian/lunch: still passes at x1.502 (+50.2% on every salt figure in the library)
    north_indian/dinner: still passes at x1.605 (+60.5% on every salt figure in the library)
   ```
   Every salt estimate in the library could be 28% low and all four templates
   would still pass. Cost: this is a *uniform* scaling and therefore an
   optimistic bound — a single dish being 30% under-salted is not covered by it.
5. **Nothing.** Defensible on this evidence, and it is what D5 forbids acting
   against anyway.

### What a reader should conclude about the four passing templates

They are a **result**, on the sodium axis, and something closer to a
**coincidence** on the energy axis.

Sodium: 22–38% of guard margin and 28–60% of salt-estimate margin behind every
verdict. Recipe work would have to be badly wrong, not slightly wrong, to flip
one. D5's fear does not survive measurement.

Energy: three of four plates have no feasible neighbour at all, and the
tightest bounds in the whole table are energy bounds — north_lunch's energy
ceiling has 13.6 kcal of slack against a 98.9 kcal smallest move (1.4%), and
south_lunch's *unrelaxed* energy floor is **missed by 6.7 kcal**, which is why
its third rung fires. One recipe's energy changing by a few percent moves those.
The honest reading: sodium is the bound everyone has been watching and is not
the fragile one; energy is fragile, on a band nobody has been watching, and no
task in the queue is about it.

### Finding 28 — the sodium guard is the only thing in the system that prefers less salt — **OPEN**

Raised by the sweep, not fixed here.

Nothing in the solver's objective penalises sodium: `NutritionTarget.points`
has no sodium entry, so any plate under the ceiling scores identically on that
macro. The consequence is visible as the guard rises:

```
  0.70 -> north_lunch=pass(0r, 992mg)   south_lunch=pass(3r,1391mg)
  0.80 -> north_lunch=pass(0r,1431mg)   south_lunch=pass(0r,1546mg)
  0.90 -> north_lunch=pass(0r,1733mg)   south_lunch=pass(0r,1546mg)
```

north_lunch's sodium **rises 741 mg (+75%) when the ceiling is loosened**, on
the same library and the same profile. Relaxing a limit made the plan worse in
the dimension the limit exists to protect. The guard is not acting as a
plausibility backstop here; it is acting as the sodium objective, because there
isn't one. A backstop and an objective are different mechanisms, and a system
where the only pressure toward less salt is a never-relaxing ceiling will always
serve the saltiest plate it is allowed to.

This is why option 1 above ("move the guard's value") is not the free
no-op the verdict sweep alone makes it look like: the verdicts do not move, but
the plates do, and they move in the wrong direction.

**Disposition.** OPEN. Not fixed here — D5 forbids tuning, and adding a sodium
term to the solver objective is a design decision about what the product
optimises for, not a defect fix.

### Finding 29 — relaxation rung 1 lets a *day* exceed its own sodium budget — **OPEN**

Raised while reconsidering the queue (slice 6 is about sequencing south meals
inside one day's sodium budget), not by the probe. Logged and left, per
TASKS_2.MD.

`core/nutrition/meal_target.py` sets two sodium bounds per plate:
`ceilings["sodium_mg"] = min(remaining, guard)` and
`hard_ceilings["sodium_mg"] = guard` — **the hard ceiling is always the
per-plate guard, never `remaining`.** So when the day's remaining budget is the
binding term, rung 1 of the ladder (`sodium_max_fibre_min`, ×1.5) is free to
widen it, and nothing catches the result at the day level.

Measured, south breakfast then south lunch for the reference profile:

```
$ python demo.py plan --region south_indian --meal-slot lunch --sodium-spent-mg 1189.8

      sodium_mg    floor         -   ceiling     810.2   [what the day has left]
  TARGET AS SOLVED (after 4 relaxation rung(s): ... ):
      sodium_mg    floor         -   ceiling    1215.3   [what the day has left]
  point        : 944.6 kcal, 35.0g protein, 24.3g fat, 144.8g carb, 1091.5mg sodium
```

The 1189.8 mg is the measured south_breakfast plate from the probe above.
2000 − 1189.8 = 810.2 remaining; 810.2 × 1.5 = 1215.3; the lunch plate takes
1091.5. Two meals, **2281.3 mg against a 2000 mg day budget — 14.1% over, with
one meal still to plan**, and no violation reported.

The 2026-08-02 entry that introduced the guard argued precisely this shape and
stopped one step short: it prevented *one plate* carrying 105% of a day, and
did not prevent *two plates* carrying 114% of one. `hard_ceilings` was made to
hold the guard still while tolerance moves around it; the day's remaining
budget was left with no such protection, and it is the bound that actually
encodes "a day".

Not a defect in rung 1 as such — the ladder is supposed to widen ceilings. The
question it raises is whether `day_remaining` is a tolerance at all, or a second
bound of the `hard_ceiling` kind that the ladder should skip. That is slice 6's
decision, not a fix to make here.

**Disposition.** OPEN. Blocks nothing today (nothing sequences a day yet); it
is the first thing slice 6 will hit.

### Reproduce

```bash
PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d5_margins.py
python demo.py plan --region south_indian --meal-slot lunch --sodium-spent-mg 1189.8
```

Full transcript is the probe's own output; the excerpts above are verbatim from
it. `docs/design/probes/README.md` lists it.

---

## 2026-08-07 — D3: making the south templates reachable

Three recipes (`idli`, `steamed_rice`, `soya_kuzhambu`) added so both South
Indian templates can satisfy the quality floor slice 4 introduced. Full account
in `docs/methodology.md`, "Making the south templates reachable". One new
finding, one prediction scorecard.

### The prediction, and it held completely

Written and stated before any file was created, from the per-unit table alone.
All six calls held, including both exact plates and both sodium figures:

| Prediction | Measured |
|---|---|
| south_breakfast passes, **0 rungs**, idli ×6 + soya_kuzhambu ×1 + coconut_chutney ×2 + thayir_plain ×1, 623.8 kcal, 1189.7 mg Na | passes, 0 rungs, that plate, 623.6 kcal, 1189.8 mg Na |
| south_lunch passes, **3 rungs**, ≈ steamed_rice ×1 + soya_kuzhambu ×2 + vegetable + thayir_plain ×1, ~848 kcal | passes, 3 rungs, steamed_rice ×1 + soya_kuzhambu ×2 + carrot_poriyal ×2 + thayir_plain ×1, 848.1 kcal, 1391.1 mg Na |
| sodium binds, and it is why two of the three recipes exist | held — see below |
| north verdicts do not move, because `candidates.py` filters on region | held, byte-identical, 24 and 12 combinations |
| combinations 2 → 8 and 3 → 12 | held |

Worth recording *why* it held, since the previous session's prediction did not:
this one was made from a measured per-unit table (`nutrition_of_recipe` over the
whole library) and hand arithmetic against the printed meal targets, not from
reasoning about what the rule "should" do. The one thing not predicted was
finding 27 below, which is a crash rather than a wrong answer.

**The sodium claim is backed by defect injection, not assertion.** Removing
`steamed_rice.yaml` alone puts south_lunch back into decline with
`Violation(macro='sodium_mg', kind='above_ceiling')`; removing `idli.yaml` alone
drops south_breakfast from 0 rungs to 3. Removing `soya_kuzhambu.yaml` is the
only one of the three that produces a *quality* decline.

### Finding 27 — a serving unit whose floor is above 1 crashed the candidate filter — FIXED in the same commit

`core/planner/candidates.py::_eligibility_flags` priced every candidate at a
hard-coded count of 1, while `nutrition_of_recipe` enforces the serving unit's
`[min_count, max_count]` bounds. Every recipe in the library happened to have
`min_count == 1`, so the two agreed by coincidence for the project's whole life
so far. `idli` is the first with a floor of 2 — nobody is served one idli — and
adding it made `build_candidate_pool` raise `ValueError: idli: count 1 outside
[2, 6]` before it could filter anything, for every template containing it.

The line's own comment already read *"any count in the unit's domain gives the
same fraction"* while the code used a count that need not be in that domain. The
comment was right and the code did not implement it — the same class of gap
CLAUDE.md's round-4 addendum is about, in miniature.

Three tests in `tests/test_nutrition_of.py::TestEligibilityConsequence` carried
the identical hard-coded 1 and crashed the same way.

**Disposition: FIXED.** `_eligibility_flags` and the three tests now use
`component.recipe.serving_unit.min_count`, which is in the domain by
construction. `tests/test_planner_candidates.py::TestServingUnitsWhoseFloorIsAboveOne`
pins it, with a second test proving the substitution is *safe* rather than
merely working: the eligibility fraction is identical at every count across
idli's whole 2–6 domain. Injection: reverting the line to `1` turns 9 tests red
across three files, including both new ones.

**What this says about coverage.** Nothing detected it because nothing exercised
it. `ServingUnit.min_count` has been a settable field since `core/foods/models.py`
was written and every recipe author independently chose 1. A field whose only
tested value is its default is not tested.

### Disposition of the older findings D3 touched

- **Finding 22** (south_lunch combinations unreachable at minimum counts) —
  still OPEN and untouched. The two offending combinations are still
  unreachable; D3 added a third rice_base/gravy pairing that is reachable. The
  passing south_lunch plate clears the 1400 mg guard by **8.9 mg**.
- **Finding 2** (a recipe with no `process:` lines reads as 0% process-uncertain)
  — still OPEN, now reachable with three real files rather than one:
  `thayir_plain`, `idli`, `steamed_rice`.
- **The "a decline can now say less" observation** from the slice-4 entry below
  — still OPEN. It is no longer visible on the south templates, because they
  pass, but it is a property of `_blocking_violations` and nothing about it
  changed.
- `tests/test_recipes.py::TestRecipeLoaderRules::test_declared_uncertainty_is_backed_by_registered_constants`
  was red before D3 (on `onion_raita`) and is red after (on `idli`, which sorts
  first). Same assertion, same defect class, deliberately not touched.

---

## 2026-08-07 — D2b-ii, slice 4: the quality-source rule

A per-meal floor on protein from ingredients clearing
`protein.quality_diaas_threshold` (0.75). Full description in
`docs/methodology.md`, "Protein quality is a rule about sources". Three
observations recorded here, one of them a defect in this session's own testing.

### The prediction, and where it was wrong

Written before any code was changed. Four of six calls held exactly:

- south_breakfast and south_lunch decline on quality — **held**, at exactly the
  predicted 8.99 g reachable against 11.2 g.
- north_lunch and north_dinner still pass with zero rungs, on plates containing
  soya or paneer instead of tofu — **held**, both.
- the three-katoris-of-dal plate is rejected on quality at 7.94 g — **held**
  (measured 7.936 g).
- `Profile.diet` still moves no target number — **held**.

**Wrong: the shape of the two south declines.** The prediction was that quality
would be named *alongside* energy, fat and sodium, since all four looked
individually unreachable. Measured, quality is named **instead of** them. The
cause is `_blocking_violations`' two-branch structure: energy/fat/sodium were
never in the unreachable branch at all — their reach spans the bound
(south_breakfast energy reaches 373.5–1326.8 kcal against a 707.0 ceiling), so
they were being reported by the later best-plate-probe branch. A genuinely
unreachable bound returns from the first branch and the probe never runs.

### Observation — a decline can now say less than it used to

Before: *"energy_kcal is 777.1kcal, above its ceiling of 707.0kcal; fat_g is
33.2g...; sodium_mg is 2273.4mg, above its ceiling of 1400.0mg"*.

After: *"only 9.0g of this plate's protein comes from a high-quality source,
against a floor of 11.2g"*.

The new sentence is the truest single thing — quality is unreachable at every
count, whereas the others were one probe plate's misses — but the user no longer
learns the plate is also 60% over the sodium guard. **Disposition: OPEN,
recorded, not fixed.** It is the same shape as finding 24 (a decline naming the
symptom rather than the cause), arriving from the other direction, and the
commissioning task ruled finding 24 out of scope.

### Finding 24 itself: checked, unmoved

`tests/test_planner_plan.py::TestPerMealProteinCeiling::
test_the_decline_names_energy_though_the_cause_is_the_protein_ceiling` still
passes unchanged. The quality rule does not fire on that synthetic case, so the
finding is neither fixed nor worsened.

### Finding 26 — a defect injection that the whole new test file survived — FIXED in the same commit

Deleting the quality check from `solver._within_target_point` — i.e. removing
the gate this slice exists to add — left **all 31 new tests green**.

Cause: `feasible_combinations` discards quality-failing combinations before the
solver runs, so on the real library the solver's own gate never decides
anything. Every test was reaching the pre-filter and stopping there. This is
exactly CLAUDE.md's "writing a test that cannot fail on the defect it names",
and it is the third instance in this repo's log.

Fixed by `TestTheSolverGateItself`, which isolates the gate on the synthetic
`SOUTH_LUNCH` pool: a combination the pre-filter must admit (`curd_b` reaches
5.0 g at its maximum count, above a 4.0 g floor) whose best-scoring assignment
falls short (2.5 g at one unit). With the gate present the solver returns
`curd_b ×2`; with it deleted, `curd_b ×1`. Both new tests were re-run against the
re-injected defect and go red.

Five further defects were injected and each turned the suite red: the protein
rung relaxing the quality floor (4 red), the floor scaled by the energy share
(9 red), a missing DIAAS reading as qualifying (15 red), the day floor taken off
the DIAAS-inflated figure instead of `base_g` (2 red), and `_widen_band`
rebuilding the target with an explicit constructor that drops the new field
(6 red). That last one is why the ladder's three target rebuilds were converted
to `dataclasses.replace`.

---

## 2026-08-02 — D2b-i, finding 25 closed

`SOUTH_BREAKFAST` gains an **optional** `curd_course` slot accepting
`curd`/`buttermilk`. `thayir_plain@curd` already fills it — no new recipe and no
new ingredient row were needed, and `curd_dahi` qualifies at DIAAS 1.09.

It follows `SOUTH_LUNCH.curd_course` in category but not in obligation: south
lunch's is required, because a South Indian lunch ends with thayir close to
obligatorily; breakfast's is optional, because idli or dosa with sambar and
chutney is a complete breakfast. That difference is the whole design of the
slot, and it is asserted rather than commented — a curd-less combination must
still enumerate.

Slot coverage and enumeration, before → after
(`PYTHONHASHSEED=0 python demo.py`):

```
south_breakfast  curd_course slot added, n=1 ['thayir_plain@curd']   1 -> 2
south_lunch      unchanged                                           3 -> 3
north_lunch      unchanged                                          24 -> 24
north_dinner     unchanged                                          12 -> 12
```

Both breakfast combinations enumerate: with and without the curd.

**A verdict reason moved, and it is worth stating.** `south_breakfast` still
declines for the reference profile, but on different numbers, because the
best-scoring combination is now the one carrying curd:

```
before  fat 24.7 > 24.6 | protein 18.4 < 23.8 | sodium 1790.4 > 1400.0
after   energy 777.1 > 707.0 | fat 33.2 > 24.6 | sodium 2273.4 > 1400.0
```

The protein violation is gone and the sodium one is worse — a katori of curd
carries its own salt line. Nothing was tuned; this is what adding a real option
to a slot does.

**Eggs are not in this.** They are the deferred non-vegetarian axis (onboarding,
filtering, schema and library all change), and nothing added here could be
served to a vegetarian profile that should not be.

*Disposition:* Finding 25 CLOSED. Pinned by
`tests/test_planner_plan.py::TestSouthBreakfastCanReachAQualitySource`, both
tests shown red against injected defects — the slot removed (KeyError, and no
curd-bearing combination), and the slot made required (no curd-less
combination).

---

## 2026-08-02 — D2a, the high-quality protein rows

Three ingredient rows (`paneer_fresh`, `tofu_firm`, `soya_chunks_dry`) and three
recipes (`paneer_masala@sabzi`, `tofu_bhurji@sabzi`,
`soya_chunk_curry@legume_curry`) were added so the quality-source rule has
something to select. Four things measured, one of them a finding.

### The reference profile now gets a plate, and it took no relaxation

This is the larger result and it was not the goal of the task. Before D2a all
four templates declined for the reference profile (see `docs/methodology.md`,
"Every template enumerates, and every template still declines"). After:

```
$ PYTHONHASHSEED=0 python demo.py plan --region north_indian --meal-slot lunch
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 4, 'dal_tadka@dal': 2, 'tofu_bhurji@sabzi': 1}
  point        : 929.8 kcal, 42.6g protein, 25.8g fat, 133.9g carb, 1209.0mg sodium

$ PYTHONHASHSEED=0 python demo.py plan --region north_indian --meal-slot dinner
passed         : True
relaxation     : ()
  unit counts  : {'phulka@roti': 4, 'dal_tadka@dal': 1, 'tofu_bhurji@sabzi': 1}
  point        : 756.8 kcal, 35.4g protein, 20.2g fat, 111.3g carb, 889.2mg sodium
```

Both north templates pass **with zero relaxation rungs fired** — the first
plates this library has served the reference profile without walking the ladder.
The mechanism is not protein: it is that a 150 g katori of tofu bhurji is a
low-sodium, moderate-energy way to fill the `sabzi` slot, so the solver can
reach the energy floor without the salt load that made every previous
combination breach the 1400 mg guard. The two south templates still decline, on
sodium among others; finding 22 is untouched.

### Finding 25 — no high-quality protein source can reach south_breakfast — **OPEN**

`SOUTH_BREAKFAST`'s four slots accept `tiffin`, `sambar`/`kuzhambu`,
`chutney`/`podi` and `beverage`. None of the three new components can be written
into any of them without either miscategorising the dish or inventing a category,
and the existing library has no qualifying ingredient in that template either
(`curd_dahi` reaches only `raita` and `curd`, which south_breakfast does not
accept).

So when the quality-source rule ships with a per-meal quality floor, **south
breakfast becomes structurally undeclinable-to-satisfy**: not "the library is
thin," but "the plate grammar has no slot a quality source could occupy." A
paneer/soya-stuffed dosa or a milk-based beverage would close it; both are new
recipes, and inventing one to make a rule pass is the shape of tuning this
project refuses.

*Disposition:* OPEN. Recorded before slice 4 rather than discovered by it.

### Nothing was upgraded to make the rows work

`dev_mode=False` still empties every pool — the new rows are `verified=false`
and carry the same 0.25 composition band as every other hand-entered row:

```
south_breakfast dev_mode True/False candidates: [3, 0]
south_lunch     dev_mode True/False candidates: [5, 0]
north_lunch     dev_mode True/False candidates: [8, 0]
north_dinner    dev_mode True/False candidates: [7, 0]
```

The three DIAAS figures are **authored, not sourced** — no primary source was
opened — and each was entered at the low end of its recalled range, because a
high DIAAS is what makes a row *qualify* and the cheapest authoring path must not
produce the most permissive output. The visible cost: `tofu_firm` at 0.65 sits
below the 0.75 threshold, so tofu will not qualify as a quality source. That is a
statement about this project's confidence, not about tofu.

### Unverified energy fraction: measured, not acted on

The two passing plates report 57.5% and 47.7% of plate energy as unverified,
against CLAUDE.md's ~15% shipping threshold. Both figures come from the
denominator finding 20 says is wrong in two directions at once, so they are
recorded and nothing is concluded from them. Nothing ships as validated either
way.

---

## 2026-08-02 — finding 24, raised by slice 3

### Finding 24 — a decline can name the symptom instead of the cause — **OPEN**

**What.** When the new per-meal protein ceiling excludes every energy-dense
plate, the decline reports **`energy_kcal below_floor`**. The protein ceiling is
never mentioned, because plates above it are removed before the validator sees
them, so the only thing left to report is that what survived cannot reach the
energy floor.

**Measured**, synthetic pool, day protein floor 40 g (meal ceiling 20.0 g),
energy 2400 kcal — the same target run twice, differing only in the registered
ceiling fraction:

```
ceiling 0.50 (real)  declines: energy_kcal below_floor 510.0 vs 756.0
ceiling 10.0 (off)   returns:  26.5 g protein, 800.0 kcal
```

The second run proves the first decline is caused by the protein ceiling. The
first run's message says energy.

**Why it matters.** A user told "energy is unreachable" would reasonably add an
energy-dense dish, which cannot help — every such dish is already excluded on
protein. The decline is truthful about what the validator saw and misleading
about what to do, which is a worse failure than a vague message: it points
somewhere specific and wrong. `docs/design/target_model_v2.md`'s decline-screen
work assumes the named macro is actionable.

**Scope.** Not specific to protein. Any bound that empties the feasible set
before the validator runs will surface as a violation of whatever the survivors
fail next. The pre-filter and the solver both discard silently.

**Not fixed here.** Slice 3's brief is the two bounds. A fix means the solver or
pre-filter reporting *why* it discarded, which is a different piece of work with
its own shape (`solve()` currently returns survivors and nothing about the
rejected). Pinned by
`tests/test_planner_plan.py::TestPerMealProteinCeiling::test_the_decline_names_energy_though_the_cause_is_the_protein_ceiling`,
so the current behaviour is visible and improving it is a deliberate change with
a red test attached rather than a silent one.

**Disposition.** OPEN.

---

## 2026-08-02 — finding 23, a form field with no effect

### Finding 23 — onboarding asks for diet and nothing reads it — **OPEN**

**What.** `web/onboarding.js` collects `diet`, `api/db.py` persists it on
`StoredProfile`, and as of slice 2 it changes no target value at all. Two
profiles identical but for diet receive identical energy, protein, fat, carb,
fibre and sodium targets. The wizard asks a question whose answer is stored and
then ignored.

**Why it is a finding and not just a gap.** The gap itself is deliberate and
documented (`docs/methodology.md`, "Protein quality no longer inflates the
target"): quality moved out of target-inflation and the quality-source rule that
replaces it is blocked on the ingredient set. What is not deliberate is that a
**shipped, user-facing surface still presents the question as consequential**. A
form that collects an answer it does not use is a claim to the user that it
matters. This project's entire premise is not overstating what it knows; an
inert form field is that failure on the most visible surface there is.

Distinct from the internal gap in one important way: the internal gap is fixed
by slice 4, and this is fixed by slice 4 *or* by saying so in the wizard. They
have different costs and either is defensible.

**Not fixed here.** Three options, none picked, all cheap: label the field in
the wizard as not yet affecting the plan; remove the step until slice 4; or
leave it and accept that the honest answer is "we collect this for later". The
first is the most in keeping with how the rest of this project handles a thing
it cannot yet do.

**Disposition.** OPEN. Reopens or closes with slice 4.

---

## 2026-08-02 — finding 22, raised by filling the library (T4)

### Finding 22 — a multi-dish South Indian plate cannot get under the sodium guard — **OPEN**

**What.** Now that every template enumerates, sodium blocks all four of them.
For `south_lunch` it is not a matter of a demanding profile: two of its three
combinations have a sodium **floor** above the per-plate guard with every
component at its minimum serving count, so no profile can ever be served them.

**Measured**, per-combination reach at min and max counts — the diagnosis is
built on the reach table this time, not read off a single blocking figure, which
is the mistake made in the other direction earlier the same day:

```
south_lunch
  Na  1437.0.. 3654.0   sambar_sadam + sambar + carrot_kootu + thayir_plain
  Na  1282.1.. 3344.2   sambar_sadam + sambar + carrot_poriyal + thayir_plain
  Na  1677.1.. 4134.2   sambar_sadam + sambar + carrot_kootu + carrot_poriyal + thayir_plain
south_breakfast
  Na  1006.6.. 3060.7   masala_dosa + sambar + coconut_chutney
```

Guard: 1400.0 mg (`day_budget.absurdity_fraction` 0.70 x 2000). Rows 1 and 3 are
above it before the solver picks a single unit count.

**Why it happens, and why it is not obviously a recipe defect.** A South Indian
lunch is four or five separate dishes, each independently salted at the ordinary
domestic proportion — the salt lines here run 0.33% to 0.67% of finished weight
and each carries a written reason. Four dishes at one katori each is roughly
3.3 g of salt before anyone eats a second helping. The arithmetic is not
disputed; what it means is:

- either the guard is wrong for multi-dish regional plates (it is a
  `PROJECT_DECISION` plausibility limit derived from meal-split fractions that
  are themselves project decisions, and it was never checked against a plate
  with four salt lines in it);
- or the salt proportions are wrong (but each was authored from how the dish is
  salted, and tuning them downward until plans pass is precisely the defect the
  salt notes exist to prevent);
- or a South Indian lunch genuinely carries this much sodium and the honest
  answer is to decline and say so.

**Not resolved here, deliberately.** TASKS.md forbids fixing things noticed in
passing, and each of the three readings above is a different decision with
different consequences. Lowering a salt line to clear a ceiling would be the
worst available option and is explicitly not on the table.

**Connects to finding 19/20's territory.** This is the sharpest available
illustration of `docs/design/recipe_quantity_uncertainty.md` §1: sodium is 77-99%
attributable to authored quantities, and it is now the single constraint blocking
every template in the library. The number that decides whether anything can be
served is one nobody measured.

**Disposition.** OPEN.

---

## 2026-08-02 — finding 21, and a correction to finding 19's own explanation

### Finding 21 — two constants in permanent contradiction, neither wrong alone — **OPEN**

**What.** `composition.verified_primary` (0.05) and `tolerance.energy_default`
(0.05) are the same number. The first is how wrong a verified composition value
is; the second is how far a plan's energy may sit from its target. One is checked
against the other every time a band is compared with the room a target leaves,
and they have never been compared with each other by anybody.

Neither is wrong on its own terms. `0.05` is a defensible estimate of analytical
spread; `±5%` is a defensible energy tolerance. Together they make the top
confidence state unreachable, and they do it permanently — no amount of
verification changes it, because verification changes who read the number, not
how variable the food is.

**Measured** (`docs/design/probes/t3b_propagation.py`), reference plate, process
term forced to zero so the composition term is isolated:

```
point     702.130   midpoint  691.445   point/midpoint 1.015454
h          35.106   room       34.572   h/room         1.015454
identical to 6 dp: True
```

When the two constants are equal the comparison collapses to **point versus
target midpoint**. So:

- With no process term, `confident` is granted exactly when the plate's energy
  lands at or below the centre of its own window — a fact about solver rounding
  over integer serving counts, carrying no nutritional meaning. A label decided
  that way is worse than one that never fires, because it looks like it means
  something.
- With the library's real process term (0.0689 on energy), the plate would need
  to sit 27% below centre, which is below its own energy floor. Unreachable.

**Scope, narrower than finding 19 stated.** This is energy-only.
`tolerance.fat_carb_default` is 0.15 against the same 0.05 band and has three
times the room it needs. Protein also exceeds its room on the reference plate
(h=1.46 vs 1.21) but that room is `point − floor`, a solver-slack fact about one
plate, not a constant-versus-constant contradiction.

**Same class as the salt-note defect.** A value that cannot do what its
neighbours assume it does, where every individual check passes. Nothing in the
registry can express "these two are compared against each other" — they sit four
entries apart in `citations.py` (positions 12 and 16 of 63) and no mechanism
noticed.

**Disposition.** OPEN, **deferred by decision 2026-08-02.** Options laid out in
`docs/design/tolerance_versus_band.md`; no constant moved and none chosen. The
contradiction is permanent but inert — the confidence label is not built, so
nothing reads either constant against the other today. **The label is not to be
built until this is settled**, because building it first would force the choice
from inside an implementation, which is exactly how the sodium ladder ambiguity
came to be resolved in `validator.py` rather than in a document. Reopen when the
label is scheduled, or when any user-facing surface states a "within 5% of your
energy target" claim.

Note for whoever picks: widening the tolerance to make the label move is the
perverse incentive CLAUDE.md documents, wearing a different hat, and 0.10 is
already the value rung 3 relaxes *to*, so it would make that rung a no-op.

### Correction — finding 19's explanation was wrong, its conclusion was not

Finding 19 (and `docs/design/recipe_quantity_uncertainty.md` §6) says a 5%
composition band "produces a ~7% band on plate energy". The figure is right. The
reason given — that errors accumulate across the components of a plate — is
wrong, and the wrong reason was load-bearing: it made this look like a scaling
problem that worsens with bigger plates, and it is what T3b was commissioned to
investigate ("at what component count does it stabilise?").

Composition uncertainty is applied per line and weighted by that line's share of
the macro, then summed, so a uniform `u` sums to exactly `u` at any component
count. Measured, process terms zeroed:

```
u = 0.05, 1 through 6 components: 0.0500 on every macro, every count
u = 0.25, 1 through 6 components: 0.2500 on every macro, every count
```

Flat. It never accumulates and there is no count at which it stabilises. The
extra 1.89 points on energy is the **process** term — dal_tadka's tempering oil —
which is per-recipe and does not scale with plate size either. Protein, carb and
sodium carry no process term at all, because oil has none of them.

Corrected in place in the design doc rather than silently edited. The correction
makes the problem smaller and sharper: not a scaling law, two equal numbers.

---

## 2026-08-02 — two findings from the T3 design measurement

Both found while designing `docs/design/recipe_quantity_uncertainty.md` against
the real library. Neither is caused by that design; both were already true and
were invisible because nothing had measured them. Design is not implemented, so
nothing here is fixed.

### Finding 19 — the confidence label saturates: `confident` is unreachable — **OPEN**

**What.** The plain-language confidence label specified in T3 (*confident* /
*rough* / *very rough*, derived from band half-width against the room a target
leaves) has one reachable bucket. Every plate the library can produce is already
*very rough* today, and stays *very rough* under a simulation of Task 6 in which
every ingredient is verified.

**Measured.** North Indian lunch for a 45 kg / 165 cm / 35 / female / active /
maintain profile — the nearest profile whose plate solves with **zero**
relaxation rungs, so the comparison is against the tightest bounds the system
ever applies. Plate `phulka ×1, dal_tadka ×3, onion_raita ×1`.

```
                              energy      protein     fat        carb
band half-width today          h=188.8     h=7.3      h=7.1      h=23.4
room the target leaves         room=34.6   room=1.2   room=3.2   room=14.6
                              -> very rough on all four

simulating Task 6 (composition.unverified_secondary 0.25 -> verified 0.05):
band half-width                h=48.4      h=1.5      h=2.6      (passes)
room                           room=34.6   room=1.2   room=3.2
                              -> still very rough on energy and protein
```

**Why it does not resolve itself.** Energy is the binding case and it is
structural, not a data problem: a 5% composition band on every ingredient
produces roughly a 7% band on plate energy, while `tolerance.energy_default` is
5%. `confident` cannot be reached from any composition data this project could
plausibly obtain, because the tolerance is narrower than the uncertainty of a
national food table. The two constants were registered independently and have
never been compared to each other.

**Why it matters.** The label was specified as counter-pressure against the
documented perverse incentive (wider bands are easier to satisfy). A label with
one reachable value exerts none. Separately, the counter-pressure that *does*
exist — the candidate eligibility filter, which removes a recipe whose band
exceeds 0.15 protein / 0.20 energy — is also saturated: all four north-lunch
recipes already breach both (protein 0.250 vs 0.15; energy 0.250–0.276 vs 0.20)
and survive only under `dev_mode=True`.

**Disposition.** OPEN. Recorded in the design doc §6 and §7 as a stated
limitation rather than smoothed over. Resolving it means revisiting either
`tolerance.energy_default` or `composition.verified_primary` **against each
other**, which is a target-model decision, not a recipe-data one. Do not resolve
it by widening the tolerance to make the label move — that is the perverse
incentive wearing a different hat.

### Finding 20 — the unverified-energy fraction is wrong in both directions, measured — **OPEN**

**What.** The round-4 addendum predicted that
`NutritionEstimate.unverified_energy_kcal` gets its denominator wrong in both
directions. It does, and the size is now measured rather than argued.

**Measured**, same plate: `unverified_energy_kcal = 519.0 of 702.1 = 73.9%`
against CLAUDE.md's ~15% shipping threshold.

```
dal_tadka      process_constants=['oil_uptake.vegetable_tempering']  -> whole 519 kcal charged
phulka         process_constants=[]                                  -> 0.0 charged
onion_raita    process_constants=[]                                  -> 0.0 charged
```

- **Over-charged:** `_depends_on_unverified` charges a recipe's *entire* energy
  when any process constant is unverified. dal_tadka's 519 kcal is charged
  because of a 5 g tempering-oil line.
- **Under-charged:** unverified *composition* never enters the calculation at
  all. phulka and onion_raita rest entirely on hand-entered, `verified=False`
  ingredient rows and contribute 0.0.

73.9% is therefore not the true figure. It is two large errors in opposite
directions that happen not to cancel, and the direction of the net error is
unknown.

**Disposition.** OPEN. The known over-attribution is already documented in
`core/foods/nutrition_of.py::_depends_on_unverified`, deliberately left because
correcting the smaller error alone would move the reported figure *away* from
the truth. This entry adds the measurement and the consequence: **the 15%
threshold cannot be trusted against real data until the denominator is fixed**,
and no work should be measured against it in the meantime. It does not change
what can ship — nothing can ship as validated for the independent reason that
every registered constant is `verified=False`.

---

## 2026-08-02 — finding 18 CLOSED, and the reproducibility pattern behind it

### Finding 18 — CLOSED

`CandidatePool.for_slot` now iterates `sorted(slot.accepted_categories)` and
returns candidates sorted by `component.id`. Sorted by **id, not by category
name**: the id is the identity of the thing actually offered, so the order
survives a category rename or a slot accepting more categories, and it is a
total order because `for_slot` already deduplicates on that key.

**Before fixing, the spread was measured.** `demo.py plan` for the north_lunch
reference profile, 12 hash seeds:

- **2 distinct enumeration orderings** (5 seeds gave rajma-first, 7 gave
  dal-first).
- **Verdict identical in all 12**: `passed: False`,
  `above_ceiling sodium_mg actual=1649.3 bound=1400.0`.

**The winner does not change with seed.** This was the serious question and the
answer is no. Checked on a target the real library *can* satisfy, and on
`tests/factories.py`'s 144-combination synthetic library where ties are far more
likely, across 12 seeds each:

```
REAL  plate={'phulka@roti':3,'rajma_chawal@combo_rice_legume':1,'onion_raita@raita':1}
      score=0.301389  top4=[0.301389, 0.372667, 0.9585, 1.039]
SYNTH n=144  plate={'rice_b@mixed_rice':2,'gravy_b@rasam':2,'veg_a@poriyal':2,
                    'veg_c@poriyal':2,'curd_b@buttermilk':1,'crisp_b@pickle':2}
      score=0.121429  top4=[0.121429, 0.142857, 0.214286, 0.271429]
```

Identical at every seed. **No tie was ever reached** — top-two scores differ by
24% (real) and 18% (synthetic) — so `solver.py`'s stable sort never had to break
one. The tie-break path is **latent, not realised**: published results did not
depend on a hash seed. Finding 18 is a reproducibility defect, not a correctness
one.

**After the fix**: one ordering across all 12 seeds; plate, score, verdict and
violation all unchanged. Note what that last clause is and is not — *nothing
changed* is a statement about **this library at this size**. With four
combinations and scores 24% apart there was no tie to resolve. It is not a
guarantee for a larger library, where the stable sort's input order is exactly
which plate a user is served.

**Other set-iteration sites, checked rather than assumed.** `candidates.py:110`
was the only one in the ordering-relevant path. Examined and deliberately not
changed:

- `core/foods/recipe_loader.py:218` and `ifct_loader.py:270` already
  `sorted(...)` their globs, so file order was never the problem.
- `combinations.py` uses `itertools.combinations` / `itertools.product`, both
  order-preserving given deterministic input — so the one fix propagates.
- `candidates.py` `recipe_allergens` returns a frozenset, but it is only ever
  membership-tested, never iterated for order.
- `len({f.recipe_id for f in flagged})` builds a set for a count only.
- **`solver.py:214`, `solved.sort(key=lambda p: p.score)` — left alone.**
  Python's sort is stable, so with deterministic input the winner is now
  deterministic; the defect is fully closed by the one fix. Adding a secondary
  sort key would additionally make the winner independent of *enumeration* order,
  which is a stronger and different property — a decision about tie-break
  semantics, not a determinism fix, and not made here.

**Disposition: CLOSED.** `tests/test_planner_determinism.py` (new).

### The pattern — second instance, and it should be named as one

This is the **second time a reproducibility rule in this project has been
satisfied literally while missing its purpose.**

1. **Task 9 (2026-07-31, finding 11).** CLAUDE.md requires a pasted command
   transcript backing any status claim. Every transcript in this log had one.
   None could be re-run, because the command lived in an untracked scratch
   script. The rule was met; its purpose — that anyone can check the claim —
   was not.
2. **Finding 18 (today).** `demo.py` was built to close that hole, and slice
   1a's acceptance criterion asserted byte-identical output against a captured
   baseline. Both were satisfied. Neither could be *reliably* true while
   enumeration order was seed-dependent: 1a's byte-diff passed because the
   baseline and the comparison run happened to draw the same ordering. The
   check was real, and it was a coin flip.

The shape is the same both times: **a reproducibility check that reproduces
itself.** A transcript that proves a transcript exists; a byte-diff run twice in
one shell against one seed. Neither compared across the axis the property was
actually about — a different machine, a different process.

What follows from it, stated as a rule rather than an intention: **a
determinism claim has to be checked across the thing it claims independence
from.** `tests/test_planner_determinism.py` does that by spawning subprocesses
under different `PYTHONHASHSEED` values, because nothing checkable inside one
process can.

That is not a hypothetical concern — it was demonstrated while writing the
tests. The first draft's three fast in-process tests **all passed against the
defect they were written to catch**, for two separate reasons: one picked
`north_lunch.grain_base`, which declares two categories but has candidates in
only one, so permuting it is a no-op; and the sortedness check compares
frozenset order against sorted order, which coincide often enough to pass under
many seeds. Both were found by injecting the defect and watching the tests not
fail. Under the corrected tests the defect fails 3 of 4 at every seed tried
(0, 1, 5), and the remaining one is documented in its own body as a statement of
contract rather than a detector.

### Does finding 11's closure claim now hold?

**Yes, and it did not before today.** The 2026-07-31 entry closed finding 11 on
the claim that the evidence chain is reproducible. As of that entry the
*substance* reproduced — verdicts, bounds and violations were stable across
every seed measured — but the artifact did not: two people running the
documented command got textually different transcripts, and a diff between them
showed changes that were not changes. With `for_slot` ordered, `demo.py` output
is byte-stable across 12 hash seeds, and the claim holds as written.

---

## 2026-08-02 — sodium became a day budget; two findings raised on the way

Build notes for target-model slices 1a and 1b, plus two things measured while
building them that neither the design doc nor this log had right.

### Finding 18 — combination enumeration order is not deterministic — **CLOSED 2026-08-02**, see the entry above

`TemplateSlot.accepted_categories` is a `frozenset[str]`, and
`core/planner/candidates.py:110` iterates it directly. Python randomises string
hashes per process, so **candidate order — and therefore the order
`enumerate_combinations` returns combinations in — varies between runs of
identical code on the same machine.**

Measured. Five runs of `demo.py plan`, hashing the enumeration block only, on
the unmodified pre-slice-1a code:

```
09071a2e79c2b59a8d1e1a4c0fe257da     f737693bb608d5fdd2e891852e804f5e
09071a2e79c2b59a8d1e1a4c0fe257da     09071a2e79c2b59a8d1e1a4c0fe257da
f737693bb608d5fdd2e891852e804f5e
```

Two distinct orderings. With `PYTHONHASHSEED=0` fixed, three runs produce one
ordering, which identifies hash randomisation as the cause. The two orderings
differ in whether `dal_tadka` or `rajma_chawal` is listed first for
`north_lunch.legume_curry`, whose `accepted_categories` is
`frozenset({"legume_curry", "dal", "combo_rice_legume"})`.

**Why this matters more than a cosmetic listing order.** `demo.py` exists so
that the transcripts in this file can be regenerated by anyone, and the
2026-07-31 entry closed finding 11 on exactly that basis. The verdict, the
bounds and the violations are stable — what varies is the enumeration listing —
so the *substance* of every transcript here reproduces. But two people running
the identical command get textually different transcripts, and a diff between
them shows changes that are not changes. Byte-reproducibility was the claim, and
it does not hold.

**The second-order risk, not observed today but structural.** `solve` returns
plans ordered by score, and ties are broken by input order. With today's
four-combination library no tie arises, so the plate served is stable. With a
richer library, *which plate a user is served* could depend on the hash seed of
the process that answered their request.

**Disposition: was OPEN when written; CLOSED the same day in its own commit —
see the 2026-08-02 entry above for the measured spread, the winner-stability
check, and the pattern this is the second instance of.** Deliberately not fixed
in the slice that found it: changing enumeration order changes `demo.py` output
and can change which plate the solver picks among equals, and that must not ride
inside a commit whose acceptance criterion is that no behaviour moved. Found
while diffing slice 1a's output against its baseline; not caused by it.

### Correction — the north_lunch decline was never a sodium wall

The 2026-07-31 entry, and `docs/design/target_model_v2.md` §2–3, both read the
`sodium_mg actual=1649.3` decline as sodium being unreachably high in this
library. It is not. Measured per-combination sodium reach (min..max over legal
unit counts):

```
   856.6 ..  1952.8   ['phulka@roti', 'rajma_chawal@combo_rice_legume']
  1111.8 ..  2463.2   [... + 'onion_raita@raita']
   379.6 ..  1318.5   ['phulka@roti', 'dal_tadka@dal']
   634.8 ..  1828.9   [... + 'onion_raita@raita']
```

The library can build a **379.6 mg** north lunch. 1649.3 mg is the sodium of the
plate that best fits *energy and protein*: `_blocking_violations` found every
bound individually reachable and fell through to its "no single assignment meets
them together" branch, which reports the best-scoring plate's own misses. So the
decline is a **joint energy-vs-sodium infeasibility** — the low-sodium plates
cannot reach the 809.9 kcal floor — not a sodium ceiling the library cannot get
under. Reading it as the latter is what made "does the decline survive?" look
like the important question about the day-budget design. It was not.

### Correction — the design doc's absurdity guard did not survive its own ladder

`docs/design/target_model_v2.md` §2 and §3 state that the 1649.3 mg plate "still
fails" the proposed 1400 mg guard, "which is the behaviour this design wants."
That compares the plate against the **unrelaxed** guard. Rung 1 widens the
sodium ceiling by `tolerance.sodium_relaxed_fraction` (0.50), so the guard
became 2100 mg and the plate passed:

```
--- sodium ceiling 1400 (0.70 x 2000), guard widenable
    passed: True | rungs: all four | final sodium ceiling: 2100.0
    plate: {'phulka@roti': 3, 'dal_tadka@dal': 3, 'onion_raita@raita': 2}
    point: 984.1 kcal, 40.4g pro, 1649.3mg Na
```

Generally: a widenable guard permits one plate to carry `fraction x 1.5` of a
day. At 0.70 that is **105% of a whole day's sodium on a single plate** — the
outcome the guard was introduced to prevent. Fixed in slice 1b by registering
the guard as a `NutritionTarget.hard_ceiling`, which no rung may widen past.

**Disposition: both corrections applied to `docs/design/target_model_v2.md` in
the same commit as slice 1b.**

---

## 2026-07-31 — the evidence chain was not reproducible (finding 11, enlarged and CLOSED)

Not an audit pass. Recorded because the defect is about this log's own
trustworthiness, which makes it the one thing that could not be left to a
commit message.

**What was wrong.** Finding 11 below recorded that `demo.py` was referenced by
CLAUDE.md's Commands block and by `docs/methodology.md` and did not exist. That
was the visible symptom of something larger: *every* result the recent work
rests on — the library's first end-to-end plan, the sodium decline, the
rung-by-rung ladder table, the per-line salt provenance breakdown, the four
ladder-target rows quoted in the 4b write-up — was produced by a scratch script
in a session working directory. `git ls-files` returned nothing for it. None of
it could be reproduced by anyone, on any other machine, or by us the following
day.

The process rule in CLAUDE.md requires a pasted command transcript in the same
artifact as any claim about the repo's state. Every transcript quoted here
satisfied that rule literally and none of them satisfied its purpose, because
the command could not be re-run. That gap is worse than a missing file: it means
this log recorded conclusions whose evidence had already evaporated.

**What was built.** `demo.py`, tracked, at the repo root, with `library` / `plan`
/ `all` subcommands and profile and template as flags rather than edits. It
loads the real `data/` library, reports counts/rejections/warnings, prints slot
coverage for all four templates, enumerates a named template, and runs
`plan_meal` for a named profile printing the plan-or-decline, rungs applied,
skipped-locked steps, violations with actuals and bounds, and the disclosure.

Two properties are deliberate:

* **It prints the unrelaxed target and the target the ladder stopped on, each
  labelled.** The scratch script printed only `LadderOutcome.target_used` under
  a bare "meal target" heading, and that is what miscalibrated the Task 4b
  prediction — the fully-relaxed bounds were read as the bounds the plate was
  first asked to meet, so every rung looked like it still had room to give. The
  prediction was wrong for that reason and not for an arithmetic one.
* **Output is ASCII only and carries `STATUS: DEV_MODE` at both ends**, read
  from `DerivedTarget.status` rather than hard-coded. Transcripts get pasted
  into commit messages and markdown from Windows terminals; a stray em-dash
  arrives as mojibake and corrupts the evidence it was meant to preserve.

`tests/test_demo.py` (13 tests) is a smoke suite only: it asserts the script
runs, that each subcommand works, that both targets are printed, and that the
status banner appears at both ends. It asserts no nutrition value — those are
pinned in the existing suite, where a failure names the quantity.

**Reproduction check.** The reference run (`python demo.py`, north_lunch,
70 kg / 175 cm / 28 / male / moderate / maintain / vegetarian) reproduces the
Task 4b result as amended by `2c4f30f` **exactly**: 4 recipes enumerated to 4
combinations, all four rungs applied, `skipped_locked=()`, one violation —
`above_ceiling sodium_mg actual=1649.3 bound=1050.0` — and the same disclosure
string. Every ladder-target row matches. No discrepancy.

**Severity:** HIGH in kind. Nothing computed was wrong, and the reproduction
confirms that. But for a project whose entire claim is evidentiary discipline,
an unreproducible evidence chain is a failure of the thesis rather than of an
implementation, and it survived four rounds of adversarial review because every
individual transcript looked correct.

**Disposition: FIXED.** Finding 11 CLOSED. From this entry forward, a
transcript in this file that cannot be regenerated by a documented `demo.py`
invocation should be treated as not having happened.

---

## 2026-07-31 — three open questions raised by the first end-to-end plate

Not an independent audit pass. All three were observed while adding
`data/recipes/phulka.yaml` (the library's first `roti`) and running the
north_lunch pipeline end to end for the first time. None is resolved here:
each is recorded as an open question with the evidence attached, per the
audit-workflow section's rule that a finding not written here did not happen.

### Finding 15 — a combo component filled a slot alongside the base it already contains — OPEN

`core/foods/templates.py` (`NORTH_LUNCH`, `SOUTH_LUNCH`),
`core/planner/combinations.py`

The north_lunch enumeration produced exactly one combination:

```
combinations surviving the O(1) feasibility pre-filter: 1
    ['phulka@roti', 'rajma_chawal@combo_rice_legume']
```

That is a roti served alongside a rice-and-legume dish — two grain bases on
one plate. It is why carb came in far over its ceiling for the 70 kg profile:

```
above_ceiling carb_g      actual=222.8  bound=149.4
above_ceiling energy_kcal actual=1240.2 bound=989.9
```

The decline is arithmetically correct. The combination should never have been
enumerated: it is not a plate anyone would serve, and the numbers it produces
are the numbers of a plate nobody would serve.

Nothing in the slot semantics prevented it. `TemplateSlot` declares
`accepted_categories` — what a component may *be* — and has no way to declare
what a filling component may not also *provide*. `rajma_chawal`'s category is
`combo_rice_legume`, which `NORTH_LUNCH.legume_curry` accepts; that the dish
also contains 183 g of `rice_cooked`, i.e. the thing `grain_base` was filled
with separately, is invisible to the enumerator.

**The open question, unanswered here:** should a slot be able to declare what
a filling component may **not** also provide (a "provides" / "excludes"
relation between slots), or should combo-type components instead be excluded
from templates that fill their constituents in separate slots? Both have
costs — the first adds a second axis to a grammar whose whole point is being
per-meal and readable; the second means `rajma_chawal` becomes unplannable in
the only template that currently accepts it, which would return north_lunch to
zero combinations. No decision is taken in this entry and none is implemented.

**It generalises — checked, not assumed.** The same shape exists in
`SOUTH_LUNCH` and is reachable with today's data plus one recipe:
`rice_base` accepts `mixed_rice`, and `sambar_sadam` (category `mixed_rice`)
is rice *with sambar already in it*, while `gravy` is a separate required slot
accepting `sambar`/`kuzhambu`/`rasam`. The instant a `sambar` recipe is
authored, south_lunch will enumerate sambar sadam + sambar. This is not a
north_lunch quirk; it is a property of every template that accepts a composed
category in one slot and one of that composition's constituents in another.
`SOUTH_BREAKFAST` and `NORTH_DINNER` accept no composed category in any slot
and are not exposed today.

**Severity:** MEDIUM. It does not produce a wrong number — the arithmetic on
the enumerated plate is right, and the validator correctly declined it. It
produces a *correct number about the wrong plate*, and in the current library
it is the only combination there is, so the whole template's behaviour rests
on it.

**Disposition: OPEN.** Not fixed in this task by instruction; no
slot/template semantics were changed.

### Finding 16 — the interval spans the bounds the point estimate passed against — OPEN

`core/foods/nutrition_of.py`, CLAUDE.md ("Uncertainty"),
findings 3, 4 and 6 above.

The first plan the real library has ever produced end to end (loose target,
2000 kcal/day, 10 g protein floor):

```
passed: True   relaxation: ()
unit_counts: {'phulka@roti': 2, 'rajma_chawal@combo_rice_legume': 1}
point   : 669.5 kcal
interval: 495.1 - 844.0 kcal
```

±26% around the point estimate. The meal's energy band under the loose target
is narrower than the interval on the estimate that cleared it: the plan passes
on a point estimate whose own honest error bar spans well outside the bounds
being gated against.

This is **not a new finding** — it is the first observation on real data of
the incentive problem CLAUDE.md's "Uncertainty" section already states in the
abstract ("a plan with worse underlying data passes more easily than one with
better data"), and it is the reason that section disqualifies interval-overlap
gating outright. Recorded here as evidence, cross-referencing rather than
duplicating: findings 3 (double-counted bands producing ±45%), 4 (a zero point
estimate printing with no band) and 6 (the low-end clamp biasing the reported
fraction narrow) are the mechanisms; this is what they look like on a plate.

The gate itself behaved as designed — it gated on the point estimate only, and
did not consult the interval. Nothing here suggests changing that. What it
documents is that "passed" and "±26%" can be true of the same plate at the
same time, which is a fact the user-facing display has to carry.

**Severity:** LOW as a defect (nothing is wrong), MEDIUM as a disclosure
question. The plate is `dev_mode` regardless: 471.7 kcal of its 669.5 kcal —
**70.5%** — comes from `verified=False` process constants, against the ~15%
shipping threshold.

**Disposition: OPEN**, as a question about display and about the existing
open interval findings, not as a new defect in the gate.

### Finding 17 — the fat floor was missed by 0.1 g, on precisely the known data gap — OPEN

`data/raw/ifct/fixture_ingredients.csv` (`sunflower_oil`, `gingelly_oil`),
`docs/methodology.md`

For the 70 kg profile, three of four violations missed their bound by a wide
margin. The fourth did not:

```
below_floor fat_g actual=20.5 bound=20.6
```

0.1 g, or 0.5% of the floor. A phulka is essentially fat-free (0.5 g per
roti, all of it from the atta), so the plate's entire fat load is
`rajma_chawal`'s 8 g tempering-oil line — and oils are the one category IFCT
2017 structurally cannot supply. Both oil rows in the fixture carry the
provenance note that IFCT's tabulated rows for oils report `energy_kcal=0`
and all micronutrients zero alongside `fatce=100`, i.e. no full nutrient
panel; both remain hand-entered approximations. The single constant governing
how much of that oil is retained, `oil_uptake.vegetable_tempering`, is a
`verified=False` project estimate with no matching primary source.

So the one macro that came down to a coin-flip is the one macro whose value
rests entirely on the library's least-supportable data. This is a
coincidence, not a causal finding — a 0.1 g miss on a 20.6 g floor is well
inside any reasonable band on that oil line, which is the point: the verdict
on this macro is not distinguishable from noise, and it happens to be the
verdict that decided a bound.

**Worth watching, explicitly:** whether this near-miss survives the task-4b
recipes (`dal_tadka`, `onion_raita`), both of which add fat — the dal
through its own tempering line, the raita through curd. If the fat floor
clears comfortably once they are in, the observation stands as a warning about
thin-library behaviour rather than a live problem. If it stays marginal, the
oil rows move up the verification queue.

**Severity:** LOW today. Recorded because a bound decided inside the noise
floor of the underlying data is the shape of thing this log exists to notice
before it decides something that matters.

**Disposition: OPEN.** No constant moved, no evidence grade changed.

### Cross-reference — `process_uncertainty` without `process_constants`, against finding 2

`tests/test_recipes.py::TestRecipeLoaderRules::
test_declared_uncertainty_is_backed_by_registered_constants` is **red as of
this entry, deliberately left unfixed.** `phulka` has a non-empty
`process_uncertainty` (0.2 bands on `fibre_g`/`iron_mg`/`calcium_mg`/`b12_ug`,
from `process_uncertainty_unassessed`) and an empty `process_constants`,
because it declares no `process:` line on any ingredient — a phulka is
dry-griddled, so no oil-uptake constant applies. The test asserts
`if recipe.process_uncertainty: assert recipe.process_constants`.

This meets **finding 2** at the same seam from the opposite direction.
Finding 2 is that a recipe with no `process:` lines reads as fully
process-*certain* — uncertainty wrongly absent. This is a recipe with no
`process:` lines whose uncertainty is correctly *present*, via the
`unassessed` path, and a check that looks for it in the wrong field. Both are
about what the absence of a `process:` line is allowed to mean. The
`unassessed` band *is* backed by a registered constant
(`process.unassessed_uncertainty`), just not one attached to any line, which
`process_constants` is derived from.

`phulka` is the first recipe in the library to use the unassessed path without
also using the per-line path, which is why the assumption held until now.

**Disposition: OPEN**, deliberately, and the test stays red. Fixing it means
deciding what finding 2 decides, and that decision is not taken here.

---

## 2026-07-22 — Phase 3 build notes: two self-caught defects

Not an independent audit pass. Both were caught while building
`core/planner/validator.py`, and both are recorded because they are instances
of failure modes CLAUDE.md names by name.

### Finding 13 — a hand-computed test expectation was wrong, and its own test agreed with it

`tests/factories.SOUTH_LUNCH_MAX_PROTEIN_G` was `33.6 g`, and
`tests/test_planner_solver.py::TestThinFeasibleSet::
test_the_synthetic_pool_cannot_reach_90g_protein_at_all` asserted exactly that
value against a comment restating the same derivation. The derivation summed
*both* crisp candidates (`crisp_a` 1.0 + `crisp_b` 0.3, doubled), but the
`crisp` slot has `max_selections=1`, so no combination ever contains two. The
true maximum is `33.0 g`.

The test passed throughout Phase 2 because the assertion and the comment were
the same mistake written twice. CLAUDE.md's testing convention ("expected
values are hand-computed, with the arithmetic shown in a comment") is
necessary but, as this shows, not sufficient: a hand-computed value is only
worth what its derivation is worth, and a comment cannot check itself.

**Severity:** LOW in consequence — the conclusion the test drew (33.6 < 90, so
the audit's thin case really is infeasible) is still true at 33.0, and nothing
in `core/` read the constant. MEDIUM in kind: it is precisely the
"code and docs agree with each other and neither survives a concrete input"
shape this log exists to catch, committed in a test rather than in a doc.

**Disposition: FIXED.** Value corrected to 33.0 with the per-slot arithmetic
shown, and a second test
(`test_the_hand_derived_max_matches_what_enumeration_actually_reaches`) now
cross-checks the hand-derived figure against what `enumerate_combinations` +
`macro_bounds` actually reach, so the arithmetic and the code must agree with
*each other*, not only with themselves. This is a cross-check, not a snapshot:
the hand-derived value is still stated and readable in `tests/factories.py`.

### Finding 14 — the relaxation ladder searched a set pre-filtered against the un-relaxed target

First implementation of `plan_within_ladder` took an already-pre-filtered
combination set and re-solved it after each rung. The O(1) feasibility
pre-filter is target-dependent, so the set handed in had already been pruned
to fit the *tight* target: every rung then widened a target and searched a
population selected to fit the target it was widening. Plans the ladder should
have found were unreachable, and the failure is silent — the system declines,
with a decline message that correctly names a constraint, and nothing
indicates the search space was wrong.

Measured on the Phase 2 synthetic pool: 17 of 144 combinations survive the
pre-filter under a 500 mg sodium ceiling; 141 survive once rung 1 drops it.
The plan the corrected ladder returns is *not* in the 17.

**Severity:** HIGH. It defeats the ladder for exactly the profiles the ladder
exists for, and presents as a legitimate decline.

**Disposition: FIXED.** `plan_within_ladder` now runs `feasible_combinations`
itself, once per rung, against that rung's target, and its docstring states
that callers must pass the enumerated set rather than a pre-filtered one.
Pinned by `tests/test_planner_validator.py::TestLadderFires::
test_relaxation_recovers_combinations_the_tight_pre_filter_discarded`, which
asserts the chosen plan is one the tight pre-filter discarded — a test that
fails if the pre-filter is ever hoisted back out.

---

## 2026-07-21 — Phase 2 build note: finding 1 closed, finding 2 status clarified

Not an independent audit pass (no fresh read-only subagent run against this
diff yet — that is still open work). Recorded here because building
`core/planner/candidates.py` directly resolves one open finding and bears on
another, and CLAUDE.md's audit-workflow section says a finding's disposition
belongs in this file, not only in a commit message.

**Finding 1 ("the protein eligibility ceiling is applied to a quantity that
is 0.0 for every recipe") — CLOSED.** `core/planner/candidates.py` gates on
`core.foods.nutrition_of.NutritionEstimate.uncertainty_fraction` — composition
uncertainty (mandatory per ingredient, never zero) plus process uncertainty —
computed via `nutrition_of_components` for each candidate recipe, not on
`Recipe.process_uncertainty` alone. `tests/test_planner_candidates.py::
TestUncertaintyEligibility::test_every_real_recipe_is_excluded_in_validated_mode`
asserts, per real recipe, that the combined protein fraction is pinned at
0.25 against a 0.15 ceiling (matching the figure already pinned in
`tests/test_nutrition_of.py::TestEligibilityConsequence`) and that all three
are excluded with `dev_mode=False`. CLAUDE.md's "Uncertainty" section wording
is corrected to say "combined composition-plus-process uncertainty" rather
than "process uncertainty."

`dev_mode` (named as a requirement in `docs/methodology.md`'s "dev_mode versus
validated" section, not previously implemented anywhere) is now a real
parameter on `build_candidate_pool`: `False` (default) excludes a recipe that
misses a ceiling; `True` keeps it and records the miss in
`CandidatePool.flagged` rather than silently treating it as validated. The
Phase 2 property test (200 random moderate profiles) runs against a synthetic,
tightly-verified fixture (`tests/factories.py`, not real recipe data) that
clears both ceilings even with `dev_mode=False` — it does not depend on
suspending the ceiling, and a separate test confirms the real library still
clears nothing.

**Finding 2 ("a recipe with no `process:` lines reads as fully
process-certain") — still OPEN, scope note added.** This finding is about
`core/foods/recipe_loader.py`'s `_derive_process_uncertainty` and
`core/foods/nutrition_of.py`'s `_depends_on_unverified`, neither of which
`core/planner` touches. It is not silently inherited by the eligibility filter
today: `Ingredient.composition_uncertainty` is mandatory per macro (construction
fails on an unpopulated entry — see `core/foods/models.py`), so the *combined*
figure `candidates.py` gates on can never be zero for a recipe built from
today's fixture, independent of whether that recipe declares any process at
all. The exposure finding 2 actually describes — a *verified*, tight-composition
ingredient combined with an undeclared process on a griddled or fried dish —
does not exist in the current fixture (every ingredient but `water` is
unverified) and so cannot presently slip through `candidates.py` either. It
would as soon as that combination exists. Closing finding 2 before that point
is still the right order of work; it just is not blocking today's `dev_mode`
eligibility behaviour the way finding 1 was.

---

## 2026-07-21 — audit of `7d9bc41` and `26e5ff4`

**Scope.** Composition uncertainty (`7d9bc41`) and the derive-process-uncertainty
/ pin-guards / restore-build-status pass (`26e5ff4`). Diff audited:
`git diff 116c765..HEAD`.

**Auditor.** Read-only subagent (Read/Grep/Glob + read-only Bash), no write
access to `core/`. `.claude/agents/auditor.md` and `.claude/commands/grill.md`
described in CLAUDE.md do not exist yet; this ran as an ad-hoc equivalent under
the same permission boundary. Building the persistent definitions is open work.

**Suite at time of audit:** `python -m pytest tests/ -q` -> `124 passed in 0.17s`.
**Suite after the fixes below:** `python -m pytest tests/ -q` -> `124 passed in 0.19s`.

**Summary:** 12 findings — 2 HIGH, 1 MEDIUM/HIGH, 3 MEDIUM, 6 LOW/doc-drift.
Six fixed in the follow-up commit (all of them statements that were simply
false); six left OPEN because they need a design decision rather than a
correction. Findings 1 and 2 are both in the permissive direction — they would
let the planner ship plans the project says it cannot — and should be closed
before `core/planner` starts.

### Cleared — checked and found sound

Recorded because knowing what was tested and cleared is as useful as the
findings, and because a later reader should not re-derive these.

- **`_composition_band` weighting is genuinely per-ingredient**, not an artifact
  of every row currently carrying 0.25. Flipping only `rajma_cooked` to verified
  moved `rajma_chawal`'s protein band 0.25 -> 0.12564, matching
  `(9.570/15.391)*0.05 + (5.821/15.391)*0.25` exactly.
- **Same ingredient on two lines with different process keys** (masala dosa's two
  `gingelly_oil` lines) derives correctly: 6.188 + 2.652 = 8.84 kcal.
- **Derived uncertainty cannot currently exceed 1.0** — the numerator sums a
  subset of the denominator's lines, all non-negative, so it is bounded by the
  largest constant uncertainty (0.20 today). No guard exists, but it is not
  reachable. See finding 6 for the related clamp issue.
- **The macro-share table in `docs/methodology.md` is arithmetically correct.**
  Independently recomputed: `rice_cooked` 39.34%/28.49%, `rajma_cooked`
  14.53%/34.71%, top eight = 93.04% energy / 91.90% protein.
- **`test_mutating_a_constant_moves_every_recipe_that_depends_on_it` is a real
  perturbation test**, not a self-consistency check.

### Findings

**1. The protein eligibility ceiling is applied to a quantity that is 0.0 for
every recipe — HIGH**
`core/foods/models.py:291-293`, `core/nutrition/citations.py` (`eligibility.max_protein_uncertainty`),
CLAUDE.md:136-137, `docs/methodology.md`

CLAUDE.md says the filter excludes "a recipe whose **process uncertainty** on a
given macro exceeds a stated ceiling", and `Recipe.process_uncertainty`'s
docstring says it is "Read later by the candidate eligibility filter". Measured
process protein uncertainty:

```
masala_dosa  0.0
rajma_chawal 0.0
sambar_sadam 0.0
```

Oil carries no protein, so no derived process term ever touches that macro. A
`core/planner` author implementing exactly what the docs instruct gets
`0.0 < 0.15` -> **every recipe eligible**, `dev_mode` never needed, all 124 tests
still green. Nothing in `core/` reads `eligibility.max_protein_uncertainty` —
only the tests. The `TestEligibilityConsequence` guards assert on
`NutritionEstimate.uncertainty_fraction`, a *different* quantity from the one the
ceiling is documented to gate.

This is the specific edit that makes the library "pass" with no test failing,
and it is the edit the docs tell you to make. `docs/methodology.md`'s "the
candidate pool is empty for every profile" is not enforced by anything.

*Disposition:* OPEN. Needs a decision: the ceiling must gate the **combined**
band (composition + process), and CLAUDE.md's wording must change to say so.

**2. A recipe with no `process:` lines reads as fully process-certain and 0%
unverified — HIGH**
`core/foods/recipe_loader.py` (`_derive_process_uncertainty`),
`core/foods/nutrition_of.py` (`_depends_on_unverified`)

A plain idli (rice + urad + water + salt, no oil line, no
`process_uncertainty_unassessed`) loads with all nine macros at 0.0 and
`unverified_energy_fraction() == 0.0` — against the 15% shipping threshold.

The loader docstring claims "the author cannot obtain [zero] by leaving the work
undone." The author obtains it precisely by leaving the work undone: omit
`process:` from every line. Nothing checks that a griddled, fried or boiled dish
declares any process at all. `Recipe.__post_init__`'s mandatory-per-macro rule is
satisfied by nine computed zeros.

This is the **permissive** direction of the attribution error, the opposite of
the over-attribution recorded as methodology limitation 8.

*Disposition:* OPEN. This is the same class as the defect `26e5ff4` fixed and
was introduced by the same change.

**3. `unassessed` + composition double-counts on cooked-basis rows, producing
±45% — MEDIUM/HIGH**
`core/foods/nutrition_of.py` (`_interval_for_recipe`), `core/nutrition/citations.py`

All three recipes display iron and calcium at **±45%** (0.25 composition + 0.20
unassessed process). `rajma_chawal` renders iron as `~3.2 mg (+/-45%)`, of which
87.8% comes from `rice_cooked` and `rajma_cooked` — **cooked-basis composition
records**.

The composition constant's registered `phenomenon` is dispersion in a value "as
eaten"; the unassessed constant's is change "during domestic cooking". On a
cooked-basis row those two phenomena describe the same span, and the code adds
them. Roughly half the widest band in the product is charged twice for a step the
recipe does not perform.

This is a `phenomenon`-mismatch of the exact kind CLAUDE.md's citation section
exists to catch — caught between two constants rather than between a constant and
a paper. Neither the docs nor any test mentions 0.45.

*Disposition:* OPEN.

**4. A macro with a zero point estimate displays with no band, including
declared-unassessed ones — MEDIUM**
`core/foods/nutrition_of.py` (`uncertainty_fraction`, `_interval_for_recipe`)

Masala dosa declares `b12_ug` unassessed (0.20 process band) yet renders
`"0 ug"` — no band, no qualifier. Both bands are multiplicative, so zero is an
absorbing state. The author's explicit "we have not assessed this" is
indistinguishable from a measured exact zero, on a vegan plan, for the one
nutrient where the distinction matters most.

Since composition uncertainty now floors everything else at 0.25, the *only*
figures that print without a band are exactly the ones the system knows nothing
about.

Same mechanism: a zero-protein component (chutney, rasam) reports
`uncertainty_fraction("protein_g") == 0.0` and clears the 0.15 ceiling.

*Disposition:* OPEN.

**5. No `max()` guard — declaring a macro unassessed can NARROW the band —
MEDIUM**
`core/foods/recipe_loader.py` (`_derive_process_uncertainty`),
`core/nutrition/citations.py` (`process.unassessed_uncertainty` note)

The constant's note claims it is "deliberately worse than any measured process
constant currently in this registry." It is not — `oil_uptake.dosa_griddled` is
also 0.20, i.e. equal, not worse. And there is no `max(derived, unassessed_band)`.
With `oil_uptake.vegetable_tempering` widened to 0.35, doing the work derives
0.35 while declaring the macro unassessed yields 0.20. Declaring unassessed
becomes the cheaper path to the tidier number — the exact inversion the constant
was registered to prevent.

`test_an_unassessed_macro_takes_the_registered_wide_band` does not test this
claim: it compares 0.20 against a dish-level derived *fraction* of 0.0395, not
against any constant.

*Disposition:* note text corrected 2026-07-21 (the "worse than any measured
constant" claim was false as written). The missing `max()` guard is OPEN.

**6. The low-end clamp silently understates the reported uncertainty fraction —
MEDIUM (latent)**
`core/foods/nutrition_of.py` (`_interval_for_recipe`, `uncertainty_fraction`)

`lows.append(max(0.0, v - half_width))`, but `uncertainty_fraction` recovers the
band as `(high - low) / (2p)`. Point 10 with half-width 12 clamps low to 0, high
22, reported fraction 1.1 against a true 1.2. The comment two lines above says "a
band wider than the point estimate is a legitimate statement about very poor
data" — the code makes that statement unreportable, and biases it narrow.

Not reachable today (max total band 0.45); reachable as soon as a wider constant
lands, and it fails in the false-precision direction.

*Disposition:* OPEN.

**7. CLAUDE.md's build-status test count is contradicted by the commit that
wrote it — MEDIUM**
`CLAUDE.md` build-status table

The table said "114 tests pass … at commit `7d9bc41`" and "(110 -> 114 tests)".
The commit that wrote those lines, `26e5ff4`, says "110 -> 124 tests" and
"124 passed in 0.17s". HEAD gives 124.

A status line whose transcript *in the same commit* refutes it — a direct
violation of CLAUDE.md's own "no unverified claims about the project's own
state". Cause: the table was written mid-session at 114 and not re-derived after
later tests landed in the same commit.

*Disposition:* FIXED 2026-07-21.

**8. `docs/methodology.md` still makes the "every ingredient row" claim the same
commit says it corrected — MEDIUM**

> "Consequently every ingredient row carries the 0.25 unverified-composition band"

`water` carries 0.05. `26e5ff4`'s message claims "Both documents corrected";
`data/raw/ifct/README.md` was, `docs/methodology.md` was not — and its own
limitation 1 correctly says "22 of 23", so the file contradicts itself.

The premise is also a non-sequitur: `Evidence.verified` and `Ingredient.verified`
are separate flags, and `water` is verified with no verified Evidence anywhere.

*Disposition:* FIXED 2026-07-21.

**9. The methodology worked example uses the superseded hand-rounded figure —
LOW**

Doc shows `process 223.65 x 0.040 = 8.9460`, half-width `64.8585`. Code and tests
give `8.8400` and `64.7525` (derived 0.03952604). The 0.040 is exactly the pasted
figure `26e5ff4` removed from the YAML; the doc's arithmetic block was not
re-derived with it.

*Disposition:* FIXED 2026-07-21.

**10. Two factual slips in the verification-priority section — LOW**

- "Wheat/atta, curd, coconut **and paneer**" — there is no paneer row in the
  fixture. Unused set is exactly `{coconut_fresh, curd_dahi, wheat_atta_raw}`.
- "verifying the **six** protein-dominant rows … changes `dev_mode` status."
  Five suffice, and per recipe far fewer: `rajma_cooked` alone drops
  `rajma_chawal` to 0.1256 < 0.15; `{rice_cooked, toor_dal_cooked}` clears
  `sambar_sadam`; `{urad_dal_raw, rice_milled_raw}` clears `masala_dosa`.
  `potato_boiled` is not needed. The doc's inference skips that the band is a
  weighted mix.
- `test_verification_alone_would_not_clear_the_ceiling_for_free` asserts the
  opposite of what its name says.

*Disposition:* FIXED 2026-07-21 (including the test rename).

**11. `demo.py` does not exist — LOW**
`CLAUDE.md` Commands block, `docs/methodology.md`

CLAUDE.md lists `python demo.py`; methodology requires "any `demo.py` stdout" to
carry the `dev_mode` label. There is no `demo.py` and no README in the repo. Same
class as the file's own "Things that have gone wrong before" entry about claiming
artifacts that are not in the repo.

*Disposition:* **CLOSED 2026-07-31** — see the entry at the top of this file
("the evidence chain was not reproducible"). `demo.py` now exists and is
tracked; CLAUDE.md's Commands block and `docs/methodology.md` both name a
command that runs. The finding turned out to be larger than a missing file:
every result this project's recent work rests on was produced by an untracked
scratch script.

**12. Two tests pass the pre-`26e5ff4` argument type — LOW**
`tests/test_recipes.py`

`load_recipe_file(Path(bad), frozenset(ingredients))` — the signature now
requires `Mapping[str, Ingredient]`. They pass only because both raise before
reaching `_derive_process_uncertainty`; moving where the loader validates would
turn them into confusing `TypeError`s rather than the assertions they claim.

*Disposition:* FIXED 2026-07-21.
