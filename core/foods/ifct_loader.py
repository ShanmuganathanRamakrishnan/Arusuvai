"""Load ingredient composition rows from ``data/raw/ifct/*.csv``.

The loader's job is not just parsing — it is refusing to let an incoherent
composition row into the system quietly. A row whose stated energy disagrees
with its own macros is either a transcription slip or a unit confusion, and
both propagate into every plan built on that ingredient.

Rejected rows are **logged individually and returned in the report**, never
silently dropped: a candidate pool that is quietly one ingredient short is much
harder to notice than a loud rejection at load time.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from core.foods.models import Ingredient
from core.nutrition.citations import value_of
from core.schemas import MACRO_KEYS, RawOrCooked

logger = logging.getLogger(__name__)

__all__ = ["LoadReport", "RejectedRow", "load_ingredients", "load_ingredient_file"]

REQUIRED_MACRO_COLUMNS: tuple[str, ...] = (
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carb_g",
)

_OPTIONAL_NUMERIC_COLUMNS: tuple[str, ...] = (
    "fibre_g",
    "sodium_mg",
    "iron_mg",
    "calcium_mg",
    "b12_ug",
)

#: Below this stated energy, a *relative* reconciliation check is meaningless
#: (salt and water state 0 kcal, and any relative difference from 0 is
#: infinite). Rows below it are checked on an absolute kcal difference instead.
_ZERO_ENERGY_FLOOR_KCAL = 5.0


@dataclass(frozen=True)
class RejectedRow:
    source: str
    line_number: int
    row_id: str
    reason: str

    def __str__(self) -> str:
        return f"{self.source}:{self.line_number} [{self.row_id or '?'}] {self.reason}"


@dataclass
class LoadReport:
    """What happened during a load. Inspect this; do not assume success."""

    loaded: dict[str, Ingredient] = field(default_factory=dict)
    rejected: list[RejectedRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.rejected

    def summary(self) -> str:
        return (
            f"{len(self.loaded)} ingredients loaded, {len(self.rejected)} rejected, "
            f"{len(self.warnings)} warnings"
        )


def _parse_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"true", "1", "yes", "y"}


def _parse_allergens(raw: str | None) -> frozenset[str]:
    if not raw or not raw.strip():
        return frozenset()
    return frozenset(part.strip() for part in raw.split("|") if part.strip())


def _energy_disagreement(
    stated_kcal: float, protein_g: float, fat_g: float, carb_g: float
) -> tuple[float, float]:
    """Return (recomputed kcal, fractional disagreement with the stated value).

    Uses the plain Atwater factors from the citation registry rather than
    literals, because a conversion factor is a nutritional constant like any
    other. ``carb_g`` here is total carbohydrate including fibre — see the
    convention note in ``data/raw/ifct/README.md``.
    """

    recomputed = (
        protein_g * value_of("atwater.protein_kcal_per_g")
        + fat_g * value_of("atwater.fat_kcal_per_g")
        + carb_g * value_of("atwater.carb_kcal_per_g")
    )
    if stated_kcal < _ZERO_ENERGY_FLOOR_KCAL:
        # Absolute check: a "0 kcal" row (salt, water) is fine as long as its
        # macros really are ~0, but must not smuggle in real macros.
        return recomputed, abs(recomputed - stated_kcal) / _ZERO_ENERGY_FLOOR_KCAL
    return recomputed, abs(recomputed - stated_kcal) / stated_kcal


def _row_to_ingredient(row: dict[str, str]) -> Ingredient:
    numbers: dict[str, float] = {}
    for col in REQUIRED_MACRO_COLUMNS + _OPTIONAL_NUMERIC_COLUMNS:
        parsed = _parse_float(row.get(col))
        if parsed is None:
            if col in REQUIRED_MACRO_COLUMNS:
                raise ValueError(f"missing or non-numeric required macro {col!r}")
            parsed = 0.0
        if parsed < 0:
            raise ValueError(f"{col} is negative ({parsed})")
        numbers[col] = parsed

    if numbers["fibre_g"] > numbers["carb_g"]:
        raise ValueError(
            f"fibre_g ({numbers['fibre_g']}) exceeds carb_g ({numbers['carb_g']}); "
            "carb_g is total carbohydrate and fibre is a subset of it"
        )

    state_raw = (row.get("state") or "").strip().lower()
    try:
        state = RawOrCooked(state_raw)
    except ValueError:
        raise ValueError(
            f"state {state_raw!r} is not one of "
            f"{[s.value for s in RawOrCooked]}"
        ) from None

    ifct_code = (row.get("ifct_code") or "").strip() or None
    diaas = _parse_float(row.get("diaas"))
    verified = _parse_bool(row.get("verified"), default=False)

    # Composition uncertainty is resolved here, from a registered constant keyed
    # on provenance, rather than read from a column. A per-row band in the CSV
    # would be a nutritional constant living in a data file — the thing the
    # registry exists to prevent — and would let an author quietly narrow the
    # band on their own unverified row.
    band = value_of(
        "composition.verified_primary" if verified else "composition.unverified_secondary"
    )
    composition_uncertainty = {macro: band for macro in MACRO_KEYS}

    return Ingredient(
        id=row["id"].strip(),
        name_en=(row.get("name_en") or "").strip(),
        name_ta=(row.get("name_ta") or "").strip(),
        name_hi=(row.get("name_hi") or "").strip(),
        ifct_code=ifct_code,
        state=state,
        diaas=diaas,
        is_animal_product=_parse_bool(row.get("is_animal_product"), default=False),
        jain_safe=_parse_bool(row.get("jain_safe"), default=True),
        allergens=_parse_allergens(row.get("allergens")),
        verified=verified,
        composition_uncertainty=composition_uncertainty,
        **numbers,
    )


def load_ingredient_file(path: Path, report: LoadReport | None = None) -> LoadReport:
    """Load one CSV into ``report`` (created if not supplied)."""

    report = report if report is not None else LoadReport()
    tolerance = value_of("qa.energy_reconciliation_tolerance")

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in ("id", "state", *REQUIRED_MACRO_COLUMNS) if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing required column(s) {missing}")

        for line_number, row in enumerate(reader, start=2):
            row_id = (row.get("id") or "").strip()
            if not row_id:
                _reject(report, path, line_number, row_id, "row has no id")
                continue
            try:
                ingredient = _row_to_ingredient(row)
            except (ValueError, KeyError, TypeError) as exc:
                _reject(report, path, line_number, row_id, str(exc))
                continue

            recomputed, disagreement = _energy_disagreement(
                ingredient.energy_kcal,
                ingredient.protein_g,
                ingredient.fat_g,
                ingredient.carb_g,
            )
            if disagreement > tolerance:
                _reject(
                    report,
                    path,
                    line_number,
                    row_id,
                    f"energy reconciliation failed: stated {ingredient.energy_kcal} kcal "
                    f"vs Atwater-recomputed {recomputed:.1f} kcal "
                    f"({disagreement:.1%} apart, tolerance {tolerance:.0%})",
                )
                continue

            if ingredient.id in report.loaded:
                _reject(report, path, line_number, row_id, "duplicate ingredient id")
                continue

            if not ingredient.verified:
                # Warned once per row rather than raised: the whole fixture set
                # is unverified by design at this stage, and the honest record
                # of that lives in the report, not in a crash.
                report.warnings.append(
                    f"{row_id}: composition values are unverified "
                    f"({(row.get('source_note') or 'no source note').strip()})"
                )
            report.loaded[ingredient.id] = ingredient

    return report


def load_ingredients(
    data_dir: Path | str = Path("data/raw/ifct"),
    *,
    strict: bool = False,
) -> LoadReport:
    """Load every ``*.csv`` under ``data_dir``.

    ``strict=True`` raises on the first rejection. The default is permissive so
    a single bad row does not take down the whole library — but it is only
    tolerable because the rejections are surfaced in the returned report and in
    the log, never swallowed.
    """

    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"ingredient data directory not found: {data_dir}")

    report = LoadReport()
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"no CSV files in {data_dir}")
    for path in files:
        load_ingredient_file(path, report)

    if strict and report.rejected:
        raise ValueError(
            "ingredient load rejected rows:\n"
            + "\n".join(f"  {r}" for r in report.rejected)
        )
    logger.info("ingredient load: %s", report.summary())
    return report


def _reject(
    report: LoadReport, path: Path, line_number: int, row_id: str, reason: str
) -> None:
    rejected = RejectedRow(
        source=path.name, line_number=line_number, row_id=row_id, reason=reason
    )
    report.rejected.append(rejected)
    logger.warning("rejected ingredient row — %s", rejected)
