# Checking food rows against their sources

For the project owner. Written 2026-10-17 (TASKS_3.md V2, `docs/audit_log.md`
"V2"). Each food row the planner uses came from a food table. Until a person
opens that table and sees the same numbers, the row stays **unchecked**
(`verified=false`), and no plate using it can be called validated. The
assistant is not allowed to mark a row checked: only you can.

V1 measured what checking every row would do: dishes that pass the
uncertainty check go from 0 of 55 to 50 of 55, and plates from 0 of 864 to
677. This list covers the 12 rows that already name a source and are used by
at least one dish. The other 25 rows name no source yet. Those need one found
first. Three more rows name a source but no dish uses them: raw rajma, raw
toor dal and raw potato. They are left off.

## How to check one row

1. Open the source and go to the page given.
2. Find the line with the code or food name given.
3. Compare the numbers in the "should say" column. All figures are per
   100 g of edible food. Small rounding (last digit) is fine.
4. Tell the assistant in chat, for example: "I opened IFCT 2017 page 58,
   M001 matches" or "M001: protein says 12.9, not 13.28". The assistant then
   marks the row checked in `data/raw/ifct/fixture_ingredients.csv` and
   quotes your message in the commit. If a number differs, nothing is
   marked. The row gets corrected first.

**Reading IFCT 2017 Table 1.** The columns go: moisture, protein, ash, total
fat, total fibre, insoluble fibre, soluble fibre, carbohydrate, energy. Some
rows leave out the fibre and carbohydrate columns (eggs, meat, fish have
none). Energy is in **kJ**, not kcal. The project stores kcal (kJ / 4.184)
and stores carbohydrate *plus* fibre as one figure. So the "should say"
column below gives the numbers exactly as the table prints them.

The IFCT 2017 PDF: https://www.nin.res.in/ebooks/IFCT2017.pdf (Longvah et
al., National Institute of Nutrition, Hyderabad). Page numbers below are the
PDF's page count, not the number printed on the page.

## The 12 rows, most important first

"Dishes" = how many dishes V1 found need this row checked to pass.

| # | Row | Dishes | Open | Find | Our numbers: the source should show the same (per 100 g) |
|---|---|---|---|---|---|
| 1 | Egg, whole, raw (`egg_whole_raw`) | 5 | IFCT 2017, PDF page 58 | M001 | protein 13.28 · fat 9.15 · energy 564 kJ |
| 2 | Egg, boiled (`egg_boiled`) | 4 | IFCT 2017, PDF page 58 | M004 | protein 13.43 · fat 10.54 · energy 618 kJ |
| 3 | Chicken breast, skinless (`chicken_breast_raw`) | 4 | IFCT 2017, PDF page 58 | N003 | protein 21.81 · fat 9.00 · energy 704 kJ |
| 4 | Moong dal, raw (`moong_dal_raw`) | 3 | https://fdc.nal.usda.gov/food-details/174256/nutrients | "Mung beans, mature seeds, raw" | energy 347 kcal · protein 23.86 · fat 1.15 · carbohydrate (by difference) 62.62 · fibre 16.3 · sodium 15 mg |
| 5 | Rice, raw, milled (`rice_milled_raw`) | 2 | IFCT 2017, PDF page 41 | A015 | protein 7.94 · fat 0.52 · total fibre 2.81 · carbohydrate 78.24 · energy 1491 kJ |
| 6 | Pomfret, white (`pomfret_white_raw`) | 2 | IFCT 2017, PDF page 65 | P057 | protein 19.02 · fat 5.12 · energy 513 kJ |
| 7 | Soy curd, plain (`soya_curd_plain`) | 2 | https://fdc.nal.usda.gov/food-details/175227/nutrients | "SILK Plain soy yogurt" | energy 66 kcal · protein 2.64 · fat 1.76 · carbohydrate 9.69 · fibre 0.4 · sodium 13 mg |
| 8 | Banana, ripe, robusta (`banana_ripe`) | 1 | IFCT 2017, PDF page 49 | E012 | protein 1.23 · fat 0.33 · total fibre 1.94 · carbohydrate 23.63 · energy 440 kJ |
| 9 | Soya flour, defatted (`soya_flour_defatted`) | 0 | https://fdc.nal.usda.gov/food-details/174275/nutrients | (FDC 174275) | energy 327 kcal · protein 51.46 · fat 1.22 · carbohydrate 33.92 · fibre 17.5 · sodium 20 mg |
| 10 | Chickpeas, boiled (`chickpea_boiled`) | 0 | https://fdc.nal.usda.gov/food-details/173757/nutrients | "Chickpeas ... cooked, boiled, without salt" | energy 164 kcal · protein 8.86 · fat 2.59 · carbohydrate 27.42 · fibre 7.6 · sodium 7 mg |
| 11 | Milk, whole, cow (`milk_cow_whole`) | 0 | IFCT 2017, PDF page 57 | L002 | protein 3.26 · fat 4.48 · carbohydrate 4.94 · energy 305 kJ |
| 12 | Black tea, brewed (`tea_black_brewed`) | 0 | https://fdc.nal.usda.gov/food-details/173227/nutrients | "Beverages, tea, black, brewed, prepared with tap water" | energy 1 kcal · protein 0 · fat 0 · carbohydrate 0.3 · sodium 3 mg |

Rows 9 to 12 move no dish past the protein check on their own (Dishes 0),
but every row that is checked lowers the share of unchecked energy on the
plates that use it.

## What the assistant already did, and why it does not count

The IFCT numbers above were read from the PDF by a program (text
extraction, 2026-10-17), and every one matches the row in the project. That
catches typing errors. It is not a check by a person, so it changes nothing.
The rule (CLAUDE.md invariant 4) exists because a program reading a table
can be wrong in ways it cannot see: a shifted column, the wrong food line.

## Not on this list yet

- The 25 rows with no named source, the most important being dry soya
  chunks (8 dishes), toor dal cooked, curd and urad dal (4, 4 and 3).
  Finding sources for them needs the IFCT 2017 PDF; a copy is already on
  this computer from an earlier task.
- The 18 sources behind the project's other numbers (energy equations,
  protein factors, the BMI-30 rule). A separate list will follow.
