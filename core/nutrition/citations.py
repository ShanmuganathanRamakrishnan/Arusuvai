"""The single home for every nutritional constant in the system.

Two rules from CLAUDE.md are enforced structurally here rather than by
convention:

1. **No magic numbers outside this file, including inside ``data/``.** Yield
   factors, oil uptake, household-measure gram weights and Atwater factors are
   nutritional constants exactly as much as an RDA figure is, because each one
   changes the number a user is shown. They are registered here and referenced
   by key elsewhere.

2. **Citation-presence is not citation-relevance.** Every :class:`Evidence`
   carries a ``phenomenon`` describing precisely what physical process the
   source measured, and every :class:`Constant` carries an ``applied_to``
   describing the process it is used for. :func:`mechanism_mismatches` compares
   the two, and :data:`REJECTED_CITATIONS` records sources that were real,
   findable and correctly formatted but described the wrong mechanism — the
   dangerous case, because a fabricated citation is falsifiable by anyone who
   looks it up and a mismatched-but-real one is not.

Scope note: this module is the Phase 1 subset of ``core/nutrition``. Energy,
protein, macro and target computation are not built yet — see the build-status
table in CLAUDE.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Grade(str, Enum):
    """How much weight a piece of evidence carries.

    Ordered strongest to weakest. ``PROJECT_ESTIMATE`` is not evidence in the
    literature sense at all; it exists so an honest "we had to pick a number
    and no primary source matched" is representable, which is the alternative
    to attaching a plausible-but-wrong citation.
    """

    PRIMARY_MEASUREMENT = "primary_measurement"
    NATIONAL_TABLE = "national_table"
    TEXTBOOK = "textbook"
    PROJECT_ESTIMATE = "project_estimate"
    PROJECT_DECISION = "project_decision"


@dataclass(frozen=True)
class Evidence:
    """A source. ``phenomenon`` is what it actually measured."""

    id: str
    summary: str
    #: Precisely what physical process the source measured, stated so that a
    #: reader can tell whether it is the same mechanism as the place the
    #: constant is applied. Deliberately distinct from ``summary``.
    phenomenon: str
    source: str
    grade: Grade
    doi: str | None = None
    url: str | None = None
    #: Only a human who has opened the source document may set this True.
    verified: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        if not self.phenomenon.strip():
            raise ValueError(f"Evidence {self.id!r} has an empty phenomenon")
        if self.verified and self.grade is Grade.PROJECT_ESTIMATE:
            raise ValueError(
                f"Evidence {self.id!r}: a project estimate has no source document "
                "to open, so it can never be marked verified"
            )


@dataclass(frozen=True)
class Constant:
    """A number, its uncertainty, and the process it is licensed to describe."""

    key: str
    value: float
    unit: str
    evidence_id: str
    #: The process this constant is used for, in the same vocabulary as
    #: ``Evidence.phenomenon``. If these two do not plausibly describe the same
    #: mechanism, the registration is the defect — not the usage site.
    applied_to: str
    #: Fractional 1-sigma-ish band on the value (0.20 == +/-20%). This is a
    #: property of the data, never a lever anyone adjusts to make a plan pass;
    #: see CLAUDE.md "Uncertainty".
    uncertainty: float
    note: str = ""

    def __post_init__(self) -> None:
        if self.uncertainty < 0:
            raise ValueError(f"Constant {self.key!r}: negative uncertainty")
        if not self.applied_to.strip():
            raise ValueError(f"Constant {self.key!r} has an empty applied_to")


@dataclass(frozen=True)
class RejectedCitation:
    """A real source that was considered and deliberately not used.

    Kept in the repo because the failure mode this guards against is invisible
    otherwise: the next person to look for oil-uptake literature will find the
    same deep-frying papers and, without this record, has no way to know they
    were already examined and ruled out on mechanism.
    """

    for_constant: str
    citation: str
    doi: str | None
    phenomenon_measured: str
    why_rejected: str


_EVIDENCE: dict[str, Evidence] = {}
_CONSTANTS: dict[str, Constant] = {}


def register_evidence(ev: Evidence) -> Evidence:
    if ev.id in _EVIDENCE:
        raise ValueError(f"duplicate evidence id {ev.id!r}")
    _EVIDENCE[ev.id] = ev
    return ev


def register_constant(c: Constant) -> Constant:
    if c.key in _CONSTANTS:
        raise ValueError(f"duplicate constant key {c.key!r}")
    if c.evidence_id not in _EVIDENCE:
        raise ValueError(
            f"constant {c.key!r} references unregistered evidence {c.evidence_id!r}"
        )
    _CONSTANTS[c.key] = c
    return c


def evidence(evidence_id: str) -> Evidence:
    try:
        return _EVIDENCE[evidence_id]
    except KeyError:
        raise KeyError(f"no evidence registered under {evidence_id!r}") from None


def constant(key: str) -> Constant:
    try:
        return _CONSTANTS[key]
    except KeyError:
        raise KeyError(
            f"no constant registered under {key!r}. Nutritional constants may not "
            "be written inline; register one here first."
        ) from None


def value_of(key: str) -> float:
    return constant(key).value


def uncertainty_of(key: str) -> float:
    return constant(key).uncertainty


def all_evidence() -> tuple[Evidence, ...]:
    return tuple(_EVIDENCE.values())


def all_constants() -> tuple[Constant, ...]:
    return tuple(_CONSTANTS.values())


def unverified() -> tuple[Constant, ...]:
    """Constants whose backing evidence has not been opened by a human."""

    return tuple(c for c in _CONSTANTS.values() if not evidence(c.evidence_id).verified)


def unverified_report() -> str:
    lines = ["Constants resting on unverified evidence:"]
    for c in unverified():
        ev = evidence(c.evidence_id)
        lines.append(
            f"  {c.key} = {c.value} {c.unit} (+/-{c.uncertainty:.0%})  "
            f"[{ev.grade.value}] {ev.source}"
        )
    if len(lines) == 1:
        lines.append("  (none)")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Mechanism-match review
# --------------------------------------------------------------------------
#
# Automating "does this phenomenon describe this application?" would need
# domain judgement we do not have in code, so this starts as a human-reviewed
# checklist, per the Phase 1 acceptance criteria. Each entry records that a
# person read the evidence's `phenomenon` next to the constant's `applied_to`
# and judged them to be the same mechanism. A constant missing from this map is
# not a silent pass: `mechanism_mismatches` reports it.

REVIEWED_MECHANISM_MATCHES: dict[str, str] = {
    "atwater.protein_kcal_per_g": "reviewed: metabolisable-energy factor applied to estimate metabolisable energy",
    "atwater.fat_kcal_per_g": "reviewed: same mechanism as above",
    "atwater.carb_kcal_per_g": "reviewed: same mechanism as above",
    "qa.energy_reconciliation_tolerance": "reviewed: project decision, no physical process claimed",
    "yield.rice_milled_boiled": "reviewed: water absorption on boiling, applied to boiled rice",
    "yield.toor_dal_boiled": "reviewed: water absorption on boiling, applied to boiled toor dal",
    "yield.rajma_soaked_boiled": "reviewed: soak plus boil water uptake, applied to boiled rajma",
    "yield.potato_boiled": "reviewed: near-unity mass change on boiling whole potato, applied to boiled potato",
    "oil_uptake.dosa_griddled": "reviewed: NO matching primary source; project estimate, mechanism stated honestly",
    "oil_uptake.vegetable_tempering": "reviewed: NO matching primary source; project estimate",
    "measure.katori_gravy_g": "reviewed: household volume-to-mass measure, applied to serving-unit gram weight",
    "measure.cup_cooked_rice_g": "reviewed: as above",
    "measure.idli_g": "reviewed: as above",
    "measure.dosa_g": "reviewed: as above",
    "measure.roti_g": "reviewed: as above",
    "measure.vada_g": "reviewed: as above",
    "measure.ladle_g": "reviewed: as above",
    "measure.tablespoon_g": "reviewed: as above",
    "measure.teaspoon_g": "reviewed: as above",
}


def mechanism_mismatches() -> tuple[str, ...]:
    """Constant keys that have not been through mechanism review."""

    return tuple(k for k in _CONSTANTS if k not in REVIEWED_MECHANISM_MATCHES)


REJECTED_CITATIONS: tuple[RejectedCitation, ...] = (
    RejectedCitation(
        for_constant="oil_uptake.dosa_griddled",
        citation=(
            "Bouchon, P. & Pyle, D.L. (2005). Modelling oil absorption during "
            "post-frying cooling: I & II. Food and Bioproducts Processing."
        ),
        doi=None,
        phenomenon_measured=(
            "oil ingress into the crust of a deep-fat-fried potato product during "
            "post-fry cooling, driven by capillary suction as steam condenses"
        ),
        why_rejected=(
            "A griddled dosa is not immersed in oil and forms no fried crust; its "
            "oil pickup is surface application onto a hot tawa, controlled by how "
            "much the cook spoons around the rim. Different mechanism entirely. "
            "Citing this would pass every automated check the registry performs "
            "while describing food that is not the food in question."
        ),
    ),
)


# --------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------

IFCT_2017 = register_evidence(
    Evidence(
        id="ifct_2017",
        summary="Indian Food Composition Tables, the national reference for Indian foods.",
        phenomenon=(
            "laboratory-analysed nutrient content per 100 g edible portion of "
            "Indian foods, predominantly raw/as-purchased, with a smaller set of "
            "cooked-state entries"
        ),
        source=(
            "Longvah, T., Ananthan, R., Bhaskarachary, K., Venkaiah, K. (2017). "
            "Indian Food Composition Tables. National Institute of Nutrition, "
            "Hyderabad."
        ),
        grade=Grade.NATIONAL_TABLE,
        doi=None,
        url="https://www.nin.res.in/ebooks/IFCT2017.pdf",
        verified=False,
        note=(
            "Values currently in data/raw/ifct/ were transcribed from memory of "
            "commonly published figures, not read out of this document. Nobody "
            "has opened IFCT 2017 in the course of this build. Do not flip "
            "verified until someone has."
        ),
    )
)

FAO_FNP_77 = register_evidence(
    Evidence(
        id="fao_fnp_77",
        summary="FAO's reference on food energy conversion factors (the Atwater system).",
        phenomenon=(
            "conversion of measured protein, fat and carbohydrate content into "
            "metabolisable energy for mixed human diets, i.e. gross combustion "
            "energy less faecal and urinary losses averaged across foods"
        ),
        source=(
            "FAO (2003). Food energy - methods of analysis and conversion factors. "
            "FAO Food and Nutrition Paper 77."
        ),
        grade=Grade.TEXTBOOK,
        doi=None,
        url="https://www.fao.org/4/y5022e/y5022e00.htm",
        verified=False,
        note="4/9/4 transcribed from memory; the paper has not been opened here.",
    )
)

NIN_HOUSEHOLD_MEASURES = register_evidence(
    Evidence(
        id="nin_household_measures",
        summary="Standardised Indian household measures (katori, cup, ladle) in grams.",
        phenomenon=(
            "mass of a named Indian household serving vessel or item when filled "
            "or portioned in the customary way, measured by weighing"
        ),
        source=(
            "National Institute of Nutrition (ICMR), Dietary Guidelines for "
            "Indians - A Manual, standardised household measures section."
        ),
        grade=Grade.NATIONAL_TABLE,
        doi=None,
        verified=False,
        note=(
            "Transcribed from memory. Household measures vary by household more "
            "than most nutritional constants do, which is why every one below "
            "carries a double-digit uncertainty band."
        ),
    )
)

PROJECT_YIELD_ESTIMATE = register_evidence(
    Evidence(
        id="project_yield_estimate",
        summary="Cooking yield factors estimated by this project, no primary source.",
        phenomenon=(
            "change in mass of a staple during domestic wet cooking (water "
            "absorption during boiling), expressed as finished mass divided by "
            "raw dry mass"
        ),
        source="This project's own estimate.",
        doi=None,
        grade=Grade.PROJECT_ESTIMATE,
        verified=False,
        note=(
            "Indian-specific process literature for these staples is thin. A "
            "conservative estimate with a wide band is registered rather than "
            "borrowing a figure from an unrelated food-science paper."
        ),
    )
)

PROJECT_OIL_UPTAKE_ESTIMATE = register_evidence(
    Evidence(
        id="project_oil_uptake_estimate",
        summary="Oil retained by griddled and tempered Indian preparations. No primary source found.",
        phenomenon=(
            "fraction of the oil applied to a hot flat griddle (tawa) or tempering "
            "pan that remains in the finished item, as opposed to smoking off or "
            "staying on the pan; a surface-application mechanism, NOT deep-fat "
            "frying absorption"
        ),
        source="This project's own estimate.",
        doi=None,
        grade=Grade.PROJECT_ESTIMATE,
        verified=False,
        note=(
            "Searched for and deliberately rejected deep-fry absorption "
            "literature; see REJECTED_CITATIONS. Oil uptake on a dosa varies "
            "with the cook and the pan, so the band here is wide and the "
            "estimate is on the high side rather than optimistic."
        ),
    )
)

PROJECT_DECISION = register_evidence(
    Evidence(
        id="project_decision",
        summary="A threshold this project chose. Not a claim about the world.",
        phenomenon=(
            "no physical process; a data-quality threshold or policy value "
            "decided by the authors"
        ),
        source="CLAUDE.md and BUILD_PROMPTS.md.",
        doi=None,
        grade=Grade.PROJECT_DECISION,
        verified=False,
    )
)


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

# Atwater general factors. Used only to sanity-check the internal consistency
# of composition data on load, never to overwrite a stated energy value.
ATWATER_PROTEIN = register_constant(
    Constant(
        key="atwater.protein_kcal_per_g",
        value=4.0,
        unit="kcal/g",
        evidence_id="fao_fnp_77",
        applied_to="estimating metabolisable energy from stated protein content",
        uncertainty=0.05,
    )
)
ATWATER_FAT = register_constant(
    Constant(
        key="atwater.fat_kcal_per_g",
        value=9.0,
        unit="kcal/g",
        evidence_id="fao_fnp_77",
        applied_to="estimating metabolisable energy from stated fat content",
        uncertainty=0.05,
    )
)
ATWATER_CARB = register_constant(
    Constant(
        key="atwater.carb_kcal_per_g",
        value=4.0,
        unit="kcal/g",
        evidence_id="fao_fnp_77",
        applied_to="estimating metabolisable energy from stated carbohydrate content",
        uncertainty=0.10,
        note=(
            "Widest of the three in practice: carbohydrate here is total "
            "carbohydrate including dietary fibre, and fibre yields well under "
            "4 kcal/g, so high-fibre foods reconcile worse than starchy ones."
        ),
    )
)

ENERGY_RECONCILIATION_TOLERANCE = register_constant(
    Constant(
        key="qa.energy_reconciliation_tolerance",
        value=0.15,
        unit="fraction",
        evidence_id="project_decision",
        applied_to=(
            "rejecting a composition row whose Atwater-recomputed energy differs "
            "from its stated energy by more than this fraction"
        ),
        uncertainty=0.0,
        note="Specified in BUILD_PROMPTS.md Phase 1.",
    )
)

# Cooking yields: finished mass / raw dry mass.
YIELD_RICE = register_constant(
    Constant(
        key="yield.rice_milled_boiled",
        value=3.0,
        unit="g finished per g raw",
        evidence_id="project_yield_estimate",
        applied_to="milled white rice boiled in excess water and drained",
        uncertainty=0.15,
        note=(
            "The classic 'rice triples' figure. Real range is roughly 2.6-3.2 "
            "depending on variety and how much water is left in the pot."
        ),
    )
)
YIELD_TOOR_DAL = register_constant(
    Constant(
        key="yield.toor_dal_boiled",
        value=2.5,
        unit="g finished per g raw",
        evidence_id="project_yield_estimate",
        applied_to="dehusked toor dal pressure-cooked to a soft mash",
        uncertainty=0.20,
        note="Wider band than rice: final consistency is a cook's preference.",
    )
)
YIELD_RAJMA = register_constant(
    Constant(
        key="yield.rajma_soaked_boiled",
        value=2.4,
        unit="g finished per g raw",
        evidence_id="project_yield_estimate",
        applied_to="dry rajma soaked overnight then pressure-cooked",
        uncertainty=0.15,
    )
)
YIELD_POTATO = register_constant(
    Constant(
        key="yield.potato_boiled",
        value=0.98,
        unit="g finished per g raw",
        evidence_id="project_yield_estimate",
        applied_to="whole potato boiled in skin, then peeled",
        uncertainty=0.05,
        note=(
            "Near unity, and slightly under: a boiled-in-skin potato loses a "
            "little mass to peeling, and gains almost no water."
        ),
    )
)

# Oil uptake: fraction of applied oil that ends up in the finished item.
OIL_UPTAKE_DOSA = register_constant(
    Constant(
        key="oil_uptake.dosa_griddled",
        value=0.70,
        unit="fraction of applied oil retained",
        evidence_id="project_oil_uptake_estimate",
        applied_to=(
            "oil spooned onto a tawa around and under a spreading dosa batter, "
            "griddled to crisp - surface pickup, not immersion frying"
        ),
        uncertainty=0.20,
        note=(
            "Drives the +/-20% energy uncertainty declared on the masala dosa "
            "recipe. Estimated on the high side per CLAUDE.md: uncertain data "
            "must make a recipe harder to use, never easier to pass."
        ),
    )
)
OIL_UPTAKE_TEMPERING = register_constant(
    Constant(
        key="oil_uptake.vegetable_tempering",
        value=0.95,
        unit="fraction of applied oil retained",
        evidence_id="project_oil_uptake_estimate",
        applied_to=(
            "oil heated with mustard seed and curry leaf then poured into a "
            "gravy or tossed with vegetables; nearly all of it is served"
        ),
        uncertainty=0.10,
    )
)

# Household measures. These determine how many grams a user actually eats, so
# they are nutritional constants and live here, not inline in portions.py.
_MEASURES: tuple[tuple[str, float, str, float], ...] = (
    ("measure.katori_gravy_g", 150.0, "a standard katori filled with a pourable gravy such as sambar or dal", 0.15),
    ("measure.cup_cooked_rice_g", 200.0, "a standard cup levelled with cooked rice", 0.12),
    ("measure.idli_g", 40.0, "one steamed idli from a standard idli-plate mould", 0.15),
    ("measure.dosa_g", 90.0, "one plain dosa spread to about 25 cm on a tawa", 0.20),
    ("measure.roti_g", 45.0, "one wheat roti/chapati about 15 cm across", 0.15),
    ("measure.vada_g", 45.0, "one medium medu vada", 0.15),
    ("measure.ladle_g", 60.0, "one serving ladle of a pourable gravy", 0.20),
    ("measure.tablespoon_g", 15.0, "one level tablespoon of a semi-solid such as chutney", 0.20),
    ("measure.teaspoon_g", 5.0, "one level teaspoon of oil or a spice powder", 0.20),
)

for _key, _grams, _applied, _unc in _MEASURES:
    register_constant(
        Constant(
            key=_key,
            value=_grams,
            unit="g",
            evidence_id="nin_household_measures",
            applied_to=_applied,
            uncertainty=_unc,
        )
    )
