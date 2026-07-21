"""Cooking yield, oil uptake and the uncertainty that comes with them.

Every factor used here is a nutritional constant and therefore lives in
``core/nutrition/citations.py`` — this module holds no numbers of its own. It
holds the *mapping* from a named domestic process to the constant that
describes it, and each entry states the process in the same vocabulary as the
evidence's ``phenomenon`` field so a mismatch is visible side by side.

The specific trap this module is written against: deep-fat frying oil-uptake
literature is plentiful and does *not* describe a griddled dosa. Immersion
frying deposits oil into a crust during post-fry cooling; a dosa picks up oil
spooned around the rim of a tawa. Citing the former for the latter would pass
every automated check the registry runs. See ``REJECTED_CITATIONS`` in
``citations.py`` for the specific paper that was considered and refused.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.nutrition import citations

__all__ = [
    "Process",
    "PROCESSES",
    "process",
    "cooked_mass",
    "raw_mass_for_cooked",
    "retained_oil_mass",
    "process_uncertainty",
]


@dataclass(frozen=True)
class Process:
    """A named domestic cooking process and the constant that quantifies it."""

    key: str
    #: What physically happens. Compare against the backing evidence's
    #: ``phenomenon`` before trusting the constant here.
    description: str
    constant_key: str
    kind: str  # "yield" | "oil_uptake"

    @property
    def factor(self) -> float:
        return citations.value_of(self.constant_key)

    @property
    def uncertainty(self) -> float:
        return citations.uncertainty_of(self.constant_key)

    @property
    def verified(self) -> bool:
        return citations.evidence(
            citations.constant(self.constant_key).evidence_id
        ).verified


PROCESSES: dict[str, Process] = {
    p.key: p
    for p in (
        Process(
            key="boil_rice",
            description=(
                "milled rice boiled in excess water until fully gelatinised, then "
                "drained; mass increases through water absorption"
            ),
            constant_key="yield.rice_milled_boiled",
            kind="yield",
        ),
        Process(
            key="boil_toor_dal",
            description=(
                "dehusked toor dal pressure-cooked with water to a soft mash; mass "
                "increases through water absorption"
            ),
            constant_key="yield.toor_dal_boiled",
            kind="yield",
        ),
        Process(
            key="boil_rajma",
            description=(
                "dry rajma soaked overnight then pressure-cooked; mass increases "
                "through water absorption during both stages"
            ),
            constant_key="yield.rajma_soaked_boiled",
            kind="yield",
        ),
        Process(
            key="boil_potato",
            description=(
                "whole potato boiled in its skin then peeled; mass barely changes, "
                "and falls slightly on peeling"
            ),
            constant_key="yield.potato_boiled",
            kind="yield",
        ),
        Process(
            key="griddle_dosa",
            description=(
                "oil spooned onto a hot tawa around and under spreading dosa "
                "batter; part of it stays with the dosa and part smokes off or "
                "stays on the pan. Surface pickup — NOT immersion frying"
            ),
            constant_key="oil_uptake.dosa_griddled",
            kind="oil_uptake",
        ),
        Process(
            key="temper_vegetables",
            description=(
                "oil heated with mustard seed and curry leaf, then poured into a "
                "gravy or tossed through vegetables; essentially all of it is served"
            ),
            constant_key="oil_uptake.vegetable_tempering",
            kind="oil_uptake",
        ),
    )
}


def process(key: str) -> Process:
    try:
        return PROCESSES[key]
    except KeyError:
        raise KeyError(
            f"unknown process {key!r}. Add it here with a constant registered in "
            "citations.py — do not multiply by a yield factor inline."
        ) from None


def _require_kind(p: Process, kind: str) -> Process:
    if p.kind != kind:
        raise ValueError(
            f"process {p.key!r} is a {p.kind} factor, not a {kind} factor"
        )
    return p


def cooked_mass(raw_g: float, process_key: str) -> float:
    """Finished mass from raw dry mass. Rice roughly triples; see the constant."""

    if raw_g < 0:
        raise ValueError("raw mass cannot be negative")
    return raw_g * _require_kind(process(process_key), "yield").factor


def raw_mass_for_cooked(cooked_g: float, process_key: str) -> float:
    """Raw dry mass that yields ``cooked_g`` finished.

    Needed when only a raw-basis composition entry exists for a food that the
    recipe records on a cooked basis.
    """

    if cooked_g < 0:
        raise ValueError("cooked mass cannot be negative")
    return cooked_g / _require_kind(process(process_key), "yield").factor


def retained_oil_mass(applied_g: float, process_key: str) -> float:
    """Oil that ends up in the food, of the oil put in the pan."""

    if applied_g < 0:
        raise ValueError("applied oil cannot be negative")
    return applied_g * _require_kind(process(process_key), "oil_uptake").factor


def process_uncertainty(process_key: str) -> float:
    """Fractional uncertainty on the process factor itself.

    This is a property of the data. It never widens a validation tolerance —
    per CLAUDE.md, uncertainty makes a recipe less usable, it does not make a
    plan easier to pass.
    """

    return process(process_key).uncertainty


def unverified_processes() -> tuple[Process, ...]:
    return tuple(p for p in PROCESSES.values() if not p.verified)
