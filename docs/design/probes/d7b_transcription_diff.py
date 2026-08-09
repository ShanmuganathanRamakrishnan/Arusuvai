"""D7b: diff a filled-in IFCT transcription worksheet against the fixture.

The worksheet (`docs/design/ifct_transcription_worksheet.csv`) is filled **blind**
-- from IFCT 2017 alone, without reading the current fixture values first. This
script is what closes the loop afterwards. It reads nothing but the two CSVs and
writes nothing at all: flipping `verified` is a human edit to
`fixture_ingredients.csv`, per `CLAUDE.md`'s second invariant, and a script that
did it automatically would be exactly the self-attestation that invariant exists
to prevent.

Why blind, and why a diff rather than a direct edit: every one of these rows is
a hand-entered approximation. Transcribing with the guess visible anchors the
transcription to the guess, and a transcription that agrees with an
approximation because it was copied from it looks identical, in the file, to one
that agrees because the approximation was good. The diff distinguishes them --
but only if the transcription could have disagreed.

What the output means:

  MATCH      transcribed value is within tolerance of the fixture. The
             approximation was good. Take the IFCT value anyway -- it has a
             source and the approximation does not.
  DIFFERS    the approximation was wrong by more than tolerance. This is the
             case the whole exercise is for. Note the size: a >3x gap is a
             raw/cooked-basis error, not a data-quality one (`CLAUDE.md`,
             "Raw versus cooked weight").
  NOT FOUND  left empty: IFCT does not tabulate this. A recorded negative.
             The row stays verified=False, and its source_note should say so
             with the date, the way sunflower_oil's already does.

Run from the repo root:

    PYTHONHASHSEED=0 PYTHONPATH=. python docs/design/probes/d7b_transcription_diff.py
"""
from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FIXTURE = REPO / "data/raw/ifct/fixture_ingredients.csv"
WORKSHEET = REPO / "docs/design/ifct_transcription_worksheet.csv"

#: Relative tolerance for calling two figures the same number. 2% is tighter
#: than any uncertainty band in the registry on purpose: this is a
#: transcription check, not a nutritional one. Two people reading the same
#: table cell should agree to the printed precision.
TOLERANCE = 0.02

MACROS = ("energy_kcal", "protein_g", "fat_g", "carb_g", "fibre_g",
          "sodium_mg", "iron_mg", "calcium_mg", "b12_ug")


def _rows(path: Path) -> dict[str, dict[str, str]]:
    text = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.startswith("##")
    )
    return {r["id"]: r for r in csv.DictReader(text.splitlines())}


def main() -> None:
    fixture = _rows(FIXTURE)
    worksheet = _rows(WORKSHEET)

    filled = [i for i, r in worksheet.items()
              if any(r.get(m, "").strip() for m in MACROS)]
    if not filled:
        print(f"{WORKSHEET.relative_to(REPO)} has no transcribed values yet.")
        print(f"{len(worksheet)} rows are waiting. Nothing to diff.")
        return

    differs: list[tuple[str, str, float, float]] = []
    print("=" * 92)
    print(f"{len(filled)} of {len(worksheet)} worksheet rows transcribed")
    print("=" * 92)

    for row_id in worksheet:
        sheet = worksheet[row_id]
        if row_id not in fixture:
            print(f"\n  {row_id}: NOT IN FIXTURE -- worksheet id does not match any "
                  "ingredient row.")
            continue
        if row_id not in filled:
            continue
        current = fixture[row_id]
        code = sheet.get("ifct_code", "").strip() or "-"
        page = sheet.get("ifct_page", "").strip() or "-"
        print(f"\n  {row_id}   ifct_code={code}  page={page}  "
              f"state: worksheet={sheet.get('state','')} fixture={current.get('state','')}")
        if sheet.get("state", "").strip() != current.get("state", "").strip():
            print("      !! STATE MISMATCH -- the two rows describe the food in "
                  "different states. Values are not comparable; resolve this first.")
        for macro in MACROS:
            raw = sheet.get(macro, "").strip()
            if not raw:
                print(f"      {macro:<12} NOT FOUND    (fixture holds "
                      f"{current[macro]})")
                continue
            new, old = float(raw), float(current[macro])
            if old == 0 and new == 0:
                verdict, ratio = "MATCH", 1.0
            elif old == 0:
                verdict, ratio = "DIFFERS", float("inf")
            else:
                ratio = new / old
                verdict = "MATCH" if abs(ratio - 1) <= TOLERANCE else "DIFFERS"
            if verdict == "DIFFERS":
                differs.append((row_id, macro, old, new))
                flag = "  <-- BASIS ERROR?" if ratio > 2.5 or ratio < 0.4 else ""
                print(f"      {macro:<12} DIFFERS      {old:>10.2f} -> "
                      f"{new:>10.2f}  ({ratio:.2f}x){flag}")
            else:
                print(f"      {macro:<12} match        {old:>10.2f}")

    print()
    print("=" * 92)
    print(f"{len(differs)} value(s) differ by more than {TOLERANCE:.0%}")
    print("=" * 92)
    for row_id, macro, old, new in differs:
        print(f"  {row_id:<22} {macro:<12} {old:>10.2f} -> {new:>10.2f}")
    print("\n  Next steps, none of which this script performs:")
    print("   1. Copy the transcribed values into fixture_ingredients.csv by hand.")
    print("   2. Set ifct_code, and rewrite source_note to name IFCT 2017 and the")
    print("      page -- replacing 'Hand-entered approximation', which will be false.")
    print("   3. Flip verified to true ONLY for rows you personally read in the")
    print("      source document. CLAUDE.md, second invariant.")
    print("   4. DIAAS is NOT in this worksheet and is not verified by this sitting:")
    print("      IFCT 2017 is a composition table and does not tabulate DIAAS. The")
    print("      authored 1.00 on paneer_fresh and 0.85 on soya_chunks_dry stay")
    print("      authored, and the quality-source rule still turns on them.")
    print("   5. Re-run: python -m pytest tests/ -q  and  python demo.py")
    print("      Verifying a row changes its composition band 0.25 -> 0.05, which")
    print("      moves displayed intervals. Point estimates change only where a")
    print("      transcribed value DIFFERS, and those can move a verdict.")


if __name__ == "__main__":
    main()
