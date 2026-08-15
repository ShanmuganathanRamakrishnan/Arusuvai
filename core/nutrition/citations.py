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

Scope note: this module registers the constants. Energy/protein/macro target
computation reads them in ``core/nutrition/targets.py``; the target-derivation
constants (Mifflin-St Jeor, activity/PAL, protein g/kg, per-diet DIAAS, goal
energy factors, macro AMDR, fibre, sodium) live at the end of this file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
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
    #: How this source is NAMED when another registry entry cites it in prose
    #: — "Morton et al. (2018)", not ``morton_2018_protein``. ``id`` is a
    #: lookup key and is not reader-facing; ``summary``/``phenomenon``/
    #: ``source``/``note`` are all served to the browser by ``GET
    #: /api/science`` and rendered verbatim. Write a cross-reference as a
    #: ``{other_evidence_id}`` slot and let ``register_evidence`` substitute
    #: that entry's label — see RENDERED_FIELDS and _resolve_refs.
    display_ref: str = ""

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


#: The Evidence fields that reach a human reader verbatim. ``GET /api/science``
#: serialises all four and web/onboarding.js prints them into the "Why these
#: numbers?" panel, so anything written into one of these is copy, not code.
#: ``id``, by contrast, is a lookup key and must never appear in them — see
#: _resolve_refs.
RENDERED_FIELDS = ("summary", "phenomenon", "source", "note")

_REF_SLOT = re.compile(r"\{([a-z0-9_]+)\}")


def _resolve_refs(ev: Evidence) -> Evidence:
    """Substitute ``{evidence_id}`` slots with the referenced entry's label.

    An entry that cites another entry used to do it by writing the other's id
    into its prose, which put ``morton_2018_protein`` on screen inside a
    sentence otherwise addressed to a reader. Barring the id by convention did
    not hold — it was reported closed three times — so the id is barred
    structurally here instead: a cross-reference can only be written as a slot,
    the slot can only resolve through the registry, and a raw id left in a
    rendered field fails registration. The shape is deliberately the same one
    CLAUDE.md mandates for LLM narration: prose from the author, the identifier
    substituted by the layer that owns it.
    """

    patched: dict[str, str] = {}
    for field_name in RENDERED_FIELDS:
        text = getattr(ev, field_name)
        for ref_id in _REF_SLOT.findall(text):
            target = _EVIDENCE.get(ref_id)
            if target is None:
                raise ValueError(
                    f"Evidence {ev.id!r} field {field_name!r} cites {ref_id!r}, "
                    "which is not registered (register the cited entry first)"
                )
            if not target.display_ref:
                raise ValueError(
                    f"Evidence {ev.id!r} cites {ref_id!r}, which has no "
                    "display_ref to render in its place"
                )
            text = text.replace("{" + ref_id + "}", target.display_ref)
        # After substitution nothing reader-facing may still name an id. This
        # catches the case the slot syntax cannot: an id simply typed into the
        # sentence, which is exactly how every escape of this class happened.
        for known_id in _EVIDENCE:
            if known_id in text:
                raise ValueError(
                    f"Evidence {ev.id!r} field {field_name!r} contains the raw "
                    f"evidence id {known_id!r}. This field is rendered to the "
                    f"reader; cite it as {{{known_id}}} instead."
                )
        if text != getattr(ev, field_name):
            patched[field_name] = text
    return replace(ev, **patched) if patched else ev


def register_evidence(ev: Evidence) -> Evidence:
    if ev.id in _EVIDENCE:
        raise ValueError(f"duplicate evidence id {ev.id!r}")
    ev = _resolve_refs(ev)
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
    "atwater.fibre_kcal_per_g": "reviewed: IFCT's own stated fibre energy factor, applied to the fibre portion of the energy reconciliation check",
    "yield.rice_milled_boiled": "reviewed: water absorption on boiling, applied to boiled rice",
    "yield.toor_dal_boiled": "reviewed: water absorption on boiling, applied to boiled toor dal",
    "yield.rajma_soaked_boiled": "reviewed: soak plus boil water uptake, applied to boiled rajma",
    "yield.potato_boiled": "reviewed: near-unity mass change on boiling whole potato, applied to boiled potato",
    "oil_uptake.dosa_griddled": "reviewed: NO matching primary source; project estimate, mechanism stated honestly",
    "oil_uptake.vegetable_tempering": "reviewed: NO matching primary source; project estimate",
    "process.unassessed_uncertainty": "reviewed: NO matching primary source; project estimate standing in for an unmeasured process",
    "composition.unverified_secondary": "reviewed: NO matching primary source; project estimate of transcription-plus-analytical error",
    "composition.verified_primary": "reviewed: NO matching primary source; project estimate of analytical spread",
    "eligibility.max_protein_uncertainty": "reviewed: project decision, no physical process claimed",
    "eligibility.max_energy_uncertainty": "reviewed: project decision, no physical process claimed",
    "tolerance.energy_default": "reviewed: project decision, no physical process claimed",
    "tolerance.energy_relaxed": "reviewed: project decision, no physical process claimed",
    "tolerance.fat_carb_default": "reviewed: project decision, no physical process claimed",
    "tolerance.fat_carb_relaxed": "reviewed: project decision, no physical process claimed",
    "tolerance.protein_relaxed_fraction": "reviewed: project decision, no physical process claimed",
    "tolerance.sodium_relaxed_fraction": "reviewed: project decision, no physical process claimed",
    "day_budget.absurdity_fraction": "reviewed: project decision, no physical process claimed -- a plausibility guard on one plate's share of a day, explicitly not a nutritional bound",
    "tolerance.fibre_relaxed_fraction": "reviewed: project decision, no physical process claimed",
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

IFCT_2017_ENERGY_FACTORS = register_evidence(
    Evidence(
        id="ifct_2017_energy_factors",
        summary=(
            "IFCT 2017's own component-specific energy conversion factors: "
            "protein 4, fat 9, available carbohydrate 4, fibre 2 kcal/g."
        ),
        phenomenon=(
            "the metabolisable-energy conversion factors IFCT 2017 itself uses "
            "to compute the tabulated 'energy' value of a food from its stated "
            "protein, fat, available carbohydrate and dietary fibre content — "
            "notably crediting fibre at ~2 kcal/g, distinct from and lower than "
            "the general 4 kcal/g factor applied to available carbohydrate"
        ),
        source=(
            "Longvah, T., Ananthan, R., Bhaskarachary, K., Venkaiah, K. (2017). "
            "Indian Food Composition Tables. National Institute of Nutrition, "
            "Hyderabad — energy calculation methodology, as re-published in "
            "machine-readable form by Sahu, S. & Sahu, A. (2022), "
            "ifct2017/ifct2017 v2.0.10, Zenodo, energies/index.csv."
        ),
        grade=Grade.NATIONAL_TABLE,
        doi="10.5281/zenodo.7088653",
        url="https://github.com/ifct2017/compositions",
        verified=False,
        note=(
            "This project has not opened the primary IFCT2017.pdf (it exceeds "
            "this tool's fetch size limit); the four-factor table above was "
            "read from the Sahu & Sahu machine-readable re-publication's "
            "energies/index.csv, cross-checked structurally against several "
            "IFCT food-code rows in the same dataset (see the fibre-energy "
            "factor's own entry). A human should confirm this table "
            "against the primary PDF's own methodology section before flipping "
            "verified."
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
            "literature; the rejected sources are listed alongside this "
            "registry. Oil uptake on a dosa varies "
            "with the cook and the pan, so the band here is wide and the "
            "estimate is on the high side rather than optimistic."
        ),
    )
)

PROJECT_COMPOSITION_UNCERTAINTY = register_evidence(
    Evidence(
        id="project_composition_uncertainty",
        summary="How wrong a composition value is likely to be, by where it came from.",
        phenomenon=(
            "dispersion between a stated per-100 g nutrient value and the true "
            "content of the food as eaten, arising from analytical variation, "
            "cultivar and seasonal spread, and — for values not read out of a "
            "primary table — transcription error"
        ),
        source="This project's own estimate.",
        doi=None,
        grade=Grade.PROJECT_ESTIMATE,
        verified=False,
        note=(
            "Registered because the alternative was worse: before this existed, "
            "composition error contributed exactly zero to every displayed band, "
            "so a dosa whose ingredient values were transcribed from memory "
            "rendered as '~220 kcal (+/-4%)' — a band narrower than the "
            "acknowledged error of its own inputs, which asserts the error is "
            "small rather than merely failing to mention it."
        ),
    )
)

PROJECT_UNASSESSED_PROCESS = register_evidence(
    Evidence(
        id="project_unassessed_process",
        summary="Stand-in band for a macro whose process sensitivity nobody has quantified.",
        phenomenon=(
            "change in a nutrient's content during domestic cooking where the "
            "retention or loss has not been measured for this preparation at all "
            "— e.g. mineral and vitamin retention through boiling, steaming and "
            "griddling of Indian dishes"
        ),
        source="This project's own estimate.",
        doi=None,
        grade=Grade.PROJECT_ESTIMATE,
        verified=False,
        note=(
            "Exists so that 'we have not assessed this' is representable as "
            "something other than zero. Before it, a macro absent from a "
            "recipe's uncertainty map read as perfectly certain, which made "
            "skipping the work produce the most confident-looking output."
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
        # Named by role, not by filename. This Evidence's `source` is rendered
        # verbatim to end users in the onboarding flow's citation panel
        # (GET /api/science), where two repo filenames identified nothing a
        # reader outside the codebase could open or check. The provenance
        # claim is unchanged and no less specific: this constant's authority
        # is a decision recorded in the project's own design documents, which
        # is exactly what Grade.PROJECT_DECISION already asserts. Nothing
        # numeric, no grade and no verified flag was touched.
        source="This project's own design documents.",
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
        applied_to=(
            "estimating metabolisable energy at 4 kcal/g per gram of "
            "carbohydrate. Two call sites, two different aggregates: "
            "core/foods/ifct_loader.py applies it to AVAILABLE carbohydrate "
            "only (carb_g minus fibre_g) when reconciling one ingredient row's "
            "stated energy, with fibre charged separately at "
            "atwater.fibre_kcal_per_g; core/nutrition/targets.py applies it to "
            "the day-level target's whole carbohydrate remainder (protein and "
            "fat energy subtracted out), which does not yet budget fibre "
            "separately at that level. The rate is the same 4 kcal/g in both "
            "places; what differs is which grams it is multiplied against."
        ),
        uncertainty=0.10,
        note=(
            "Until 2026-07-24 the ifct_loader call site applied this to total "
            "carbohydrate including fibre, which over-charges high-fibre foods "
            "(fibre yields well under 4 kcal/g). Corrected after real IFCT 2017 "
            "data for rajma (B020) failed the energy reconciliation gate at 19% "
            "under the old, fibre-inclusive formula: IFCT's own energy "
            "methodology (see ifct_2017_energy_factors below) separates "
            "available carbohydrate from fibre and charges them at different "
            "rates. The targets.py call site was not touched by this fix — see "
            "its own applied_to note above for why it's a different aggregate."
        ),
    )
)
ATWATER_FIBRE = register_constant(
    Constant(
        key="atwater.fibre_kcal_per_g",
        value=2.0,
        unit="kcal/g",
        evidence_id="ifct_2017_energy_factors",
        applied_to=(
            "estimating metabolisable energy from stated dietary fibre content, "
            "distinct from and lower than the available-carbohydrate rate above"
        ),
        uncertainty=0.10,
        note=(
            "Added 2026-07-24. Without this, the loader's energy-reconciliation "
            "check charged fibre at the same 4 kcal/g as starch, which is wrong "
            "and specifically punished high-fibre legumes: rajma's real IFCT "
            "figures (16.57g fibre/100g) failed the 15% reconciliation gate at "
            "19% under the flat formula but reconcile at 8% once fibre is "
            "charged at its own rate, matching IFCT's own stated methodology."
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

# Composition uncertainty, by provenance of the value. Applied per ingredient
# and weighted by that ingredient's share of the macro — a dish that is 96%
# rice and 4% griddle oil must not display a band that reflects only the oil.
COMPOSITION_UNVERIFIED = register_constant(
    Constant(
        key="composition.unverified_secondary",
        value=0.25,
        unit="fraction",
        evidence_id="project_composition_uncertainty",
        applied_to=(
            "a per-100 g nutrient value that was not read out of a primary "
            "composition table — transcribed from memory or a secondary source"
        ),
        uncertainty=0.0,
        note=(
            "Wide on purpose. Deliberately larger than the analytical spread "
            "alone, because the dominant error in an unread value is "
            "transcription, not cultivar variation."
        ),
    )
)
COMPOSITION_VERIFIED = register_constant(
    Constant(
        key="composition.verified_primary",
        value=0.05,
        unit="fraction",
        evidence_id="project_composition_uncertainty",
        applied_to=(
            "a per-100 g nutrient value read out of a primary national "
            "composition table by a human"
        ),
        uncertainty=0.0,
        note=(
            "Nothing in the library currently qualifies: every ingredient row is "
            "verified=False. Registered now so the number exists before the data "
            "does, rather than being chosen later to fit whatever passes."
        ),
    )
)

PROCESS_UNASSESSED = register_constant(
    Constant(
        key="process.unassessed_uncertainty",
        value=0.20,
        unit="fraction",
        evidence_id="project_unassessed_process",
        applied_to=(
            "a macro a recipe author has declared process-sensitive but for "
            "which no retention or loss constant is registered"
        ),
        uncertainty=0.0,
        note=(
            "Wide enough to be uncomfortable, on purpose: declaring a macro "
            "unassessed must never be the cheapest way to make a band look "
            "good. NOTE — it does not currently achieve that. It is equal to, "
            "not worse than, oil_uptake.dosa_griddled (also 0.20), and the "
            "loader applies it in place of the derived figure rather than "
            "taking max(derived, this). A recipe whose derived band exceeds "
            "0.20 can therefore narrow it by declaring the macro unassessed. "
            "See docs/audit_log.md finding 5; the missing max() is open."
        ),
    )
)

# Candidate eligibility ceilings. Per CLAUDE.md, uncertainty never widens a
# tolerance — it makes a recipe ineligible where the macro is target-critical.
# Registered here rather than left as prose so core/planner reads a constant
# instead of inventing one.
ELIGIBILITY_PROTEIN = register_constant(
    Constant(
        key="eligibility.max_protein_uncertainty",
        value=0.15,
        unit="fraction",
        evidence_id="project_decision",
        applied_to=(
            "excluding a recipe from a candidate pool where protein is "
            "target-critical, because its protein estimate is too uncertain"
        ),
        uncertainty=0.0,
        note=(
            "No recipe in the library currently clears this — see the test in "
            "tests/test_nutrition_of.py. That is the honest consequence of "
            "unverified composition data, not a bug in the ceiling."
        ),
    )
)
ELIGIBILITY_ENERGY = register_constant(
    Constant(
        key="eligibility.max_energy_uncertainty",
        value=0.20,
        unit="fraction",
        evidence_id="project_decision",
        applied_to=(
            "excluding a recipe from a candidate pool on energy uncertainty; "
            "looser than protein per CLAUDE.md's 'wider tolerance on energy'"
        ),
        uncertainty=0.0,
    )
)

# Tolerance bands, default and relaxed. These are the *tolerance* axis, which
# CLAUDE.md keeps strictly separate from the uncertainty axis above: a
# tolerance is a product decision about how far a plan may sit from its target,
# an uncertainty is a measured property of the data. They are neighbours in
# this file only because both are numbers that must not be written inline —
# nothing here may ever be read as an uncertainty, and the relaxation ladder in
# core/planner/validator.py only ever widens values from this block, never one
# from the eligibility or composition blocks.
#
# The default/relaxed pairs are transcribed from CLAUDE.md's "Relaxation
# ladder" section, which states the ranges (fat/carb 15% -> up to 25%, energy
# 5% -> up to 10%) as a design decision rather than deriving them from
# literature. Registering them here rather than leaving them as literals in
# target.py means the ladder and the default target constructor cannot drift
# apart, which they otherwise would the first time one of them was edited.
TOLERANCE_ENERGY_DEFAULT = register_constant(
    Constant(
        key="tolerance.energy_default",
        value=0.05,
        unit="fraction",
        evidence_id="project_decision",
        applied_to="the +/- band around a plan's energy target before any relaxation",
        uncertainty=0.0,
    )
)
TOLERANCE_ENERGY_RELAXED = register_constant(
    Constant(
        key="tolerance.energy_relaxed",
        value=0.10,
        unit="fraction",
        evidence_id="project_decision",
        applied_to="the widened energy band at relaxation ladder step 3",
        uncertainty=0.0,
    )
)
TOLERANCE_FAT_CARB_DEFAULT = register_constant(
    Constant(
        key="tolerance.fat_carb_default",
        value=0.15,
        unit="fraction",
        evidence_id="project_decision",
        applied_to="the +/- band around fat and carb targets before any relaxation",
        uncertainty=0.0,
    )
)
TOLERANCE_FAT_CARB_RELAXED = register_constant(
    Constant(
        key="tolerance.fat_carb_relaxed",
        value=0.25,
        unit="fraction",
        evidence_id="project_decision",
        applied_to="the widened fat/carb band at relaxation ladder step 2",
        uncertainty=0.0,
    )
)
TOLERANCE_PROTEIN_RELAXED_FRACTION = register_constant(
    Constant(
        key="tolerance.protein_relaxed_fraction",
        value=0.15,
        unit="fraction",
        evidence_id="project_decision",
        applied_to=(
            "how far below its floor the protein target may fall at the last "
            "relaxation ladder step; CLAUDE.md says protein relaxes 'partially', "
            "and this is the number that makes 'partially' checkable"
        ),
        uncertainty=0.0,
        note=(
            "Deliberately the tightest relaxation on the ladder. Widening this "
            "makes plans pass that should have been declined with a disclosure, "
            "which is the failure the ladder's ordering exists to prevent."
        ),
    )
)
TOLERANCE_SODIUM_RELAXED_FRACTION = register_constant(
    Constant(
        key="tolerance.sodium_relaxed_fraction",
        value=0.50,
        unit="fraction",
        evidence_id="project_decision",
        applied_to=(
            "how far the sodium ceiling widens at relaxation ladder step 1, for "
            "a profile with no clinical_flags locking sodium. CLAUDE.md's Round-4 "
            "clarification: this rung widens rather than drops the ceiling, so an "
            "unflagged profile is never solved against zero sodium ceiling at all"
        ),
        uncertainty=0.0,
        note=(
            "Deliberately the widest fraction on the ladder, not zero: this rung "
            "is CLAUDE.md's 'general health guidance, not the product's core "
            "nutritional claim', so it is the one place a large widening is "
            "appropriate -- but 'least load-bearing' is not the same claim as "
            "'unbounded', and dropping the ceiling entirely conflated the two."
        ),
    )
)
DAY_BUDGET_ABSURDITY_FRACTION = register_constant(
    Constant(
        key="day_budget.absurdity_fraction",
        value=0.70,
        unit="fraction of a day's budgeted ceiling",
        evidence_id="project_decision",
        applied_to=(
            "the largest share of a day's sodium budget any single plate may "
            "take, whatever the day has left. A plausibility guard on one "
            "eating occasion -- NOT a nutritional claim, and not a bound any "
            "guideline states. It exists because a remaining-budget check alone "
            "puts no limit at all on the first meal of a day"
        ),
        uncertainty=0.0,
        note=(
            "Three things about this number, all of which have to stay written "
            "down for it to be read honestly. (1) It was CHOSEN AFTER seeing "
            "which plate it excludes: the 1649.3 mg reference plate was already "
            "known when 0.70 was picked, and a multiplier chosen before would "
            "have produced a different answer. (2) Its derivation -- twice the "
            "largest meal split (lunch, 0.35) -- sounds principled and is not, "
            "because those splits are themselves project decisions this file "
            "calls 'the customary big lunch shape of an Indian day, nothing "
            "more'. A guard derived from an arbitrary constant is arbitrary. "
            "(3) It NEVER RELAXES: it is a hard ceiling the relaxation ladder "
            "may not widen past, which makes it stricter than the per-meal "
            "share it replaces, since that share did relax. That was accepted "
            "deliberately -- unclamped, rung 1's 0.50 widening would let one "
            "plate carry 0.70 x 1.5 = 105% of a whole day's sodium, which is "
            "the outcome the guard exists to prevent."
        ),
    )
)
TOLERANCE_FIBRE_RELAXED_FRACTION = register_constant(
    Constant(
        key="tolerance.fibre_relaxed_fraction",
        value=0.50,
        unit="fraction",
        evidence_id="project_decision",
        applied_to="how far the fibre floor lowers at relaxation ladder step 1",
        uncertainty=0.0,
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


# ==========================================================================
# Target-derivation constants (core/nutrition/targets.py)
# ==========================================================================
#
# Everything below turns a Profile into an energy/protein/macro target. Per
# CLAUDE.md's "no magic numbers" rule, the Mifflin-St Jeor coefficients, the
# activity multipliers, the protein g/kg figures, the per-diet DIAAS factors,
# the goal energy factors and the macro-distribution bounds all live here, not
# inline in targets.py — each one changes the number a user is shown.
#
# Grades are honest: the two real equations (Mifflin 1990, Morton 2018) and the
# two national/international tables (IOM DRI, WHO) are graded as such but remain
# verified=False, because nobody has opened the source documents in this build.
# The mappings this project *chose* — the exact activity point within a PAL
# range, the deficit/surplus size, the per-diet DIAAS rollup — are PROJECT_
# ESTIMATE or PROJECT_DECISION, so nothing here can ship as validated (see
# docs/methodology.md). targets.py labels every derived target dev_mode for
# exactly this reason.

MIFFLIN_ST_JEOR_1990 = register_evidence(
    Evidence(
        id="mifflin_st_jeor_1990",
        summary="The Mifflin-St Jeor resting metabolic rate equation.",
        phenomenon=(
            "resting metabolic rate measured by indirect calorimetry in 498 "
            "healthy adults, regressed on weight, height, age and sex; the paper "
            "reports the equation predicts measured RMR within about +/-10% for "
            "most individuals"
        ),
        source=(
            "Mifflin, M.D., St Jeor, S.T., Hill, L.A., Scott, B.J., Daugherty, "
            "S.A., Koh, Y.O. (1990). A new predictive equation for resting energy "
            "expenditure in healthy individuals. Am J Clin Nutr 51(2):241-247."
        ),
        grade=Grade.PRIMARY_MEASUREMENT,
        doi="10.1093/ajcn/51.2.241",
        verified=False,
        note=(
            "Coefficients transcribed from memory of the published equation; the "
            "paper has not been opened in this build. Chosen over Harris-Benedict "
            "because it was fitted on a more modern population and reports a "
            "tighter prediction error."
        ),
    )
)

MORTON_2018_PROTEIN = register_evidence(
    Evidence(
        id="morton_2018_protein",
        summary="Meta-analysis of protein intake and resistance-training gains.",
        phenomenon=(
            "the dietary protein intake, in g per kg body weight per day, above "
            "which resistance-trained adults saw no further gain in fat-free mass "
            "in a meta-regression of 49 randomised trials (breakpoint ~1.6 g/kg)"
        ),
        source=(
            "Morton, R.W. et al. (2018). A systematic review, meta-analysis and "
            "meta-regression of the effect of protein supplementation on "
            "resistance training-induced gains in muscle mass and strength in "
            "healthy adults. Br J Sports Med 52(6):376-384."
        ),
        grade=Grade.PRIMARY_MEASUREMENT,
        doi="10.1136/bjsports-2017-097608",
        verified=False,
        display_ref="Morton et al. (2018)",
        note=(
            "The 1.6 g/kg breakpoint is the maintenance/anchor figure. It is the "
            "same source the landing-page calculator cites; the paper has not "
            "been opened here."
        ),
    )
)

IOM_DRI_2005 = register_evidence(
    Evidence(
        id="iom_dri_2005",
        summary="US Institute of Medicine Dietary Reference Intakes (macros).",
        phenomenon=(
            "population acceptable macronutrient distribution ranges (fat as a "
            "percentage of energy) and adequate fibre intake per 1000 kcal, set "
            "from balance and observational data across healthy adults"
        ),
        source=(
            "Institute of Medicine (2005). Dietary Reference Intakes for Energy, "
            "Carbohydrate, Fiber, Fat, Fatty Acids, Cholesterol, Protein, and "
            "Amino Acids. National Academies Press."
        ),
        grade=Grade.NATIONAL_TABLE,
        doi="10.17226/10490",
        verified=False,
        note=(
            "AMDR fat range (20-35% of energy) and fibre (14 g/1000 kcal) "
            "transcribed from memory; not opened here. US, not Indian — ICMR-NIN "
            "2020 would be the preferred source and is a known substitution to "
            "make once a human opens either document."
        ),
    )
)

WHO_SODIUM_2012 = register_evidence(
    Evidence(
        id="who_sodium_2012",
        summary="WHO guideline ceiling on adult sodium intake.",
        phenomenon=(
            "the daily sodium intake below which population blood-pressure and "
            "cardiovascular risk benefits were observed in the WHO evidence "
            "review; a guideline maximum, not a physiological requirement"
        ),
        source="World Health Organization (2012). Guideline: Sodium intake for adults and children.",
        grade=Grade.NATIONAL_TABLE,
        doi=None,
        url="https://www.who.int/publications/i/item/9789241504836",
        verified=False,
        note="2000 mg/day (< 5 g salt) transcribed from memory; not opened here.",
    )
)

PROJECT_ACTIVITY_FACTOR_ESTIMATE = register_evidence(
    Evidence(
        id="project_activity_factor_estimate",
        summary="The multiplier from RMR to total energy, per activity level. Project estimate.",
        phenomenon=(
            "physical activity level as the ratio of total daily energy "
            "expenditure to basal metabolic rate; the specific factor assigned to "
            "each of this project's five activity levels is a project mapping onto "
            "the customary 1.2-1.9 PAL range, not a measured value for any person"
        ),
        source="This project's own estimate, over the conventional activity-factor range.",
        doi=None,
        grade=Grade.PROJECT_ESTIMATE,
        verified=False,
        note=(
            "The WHO/FAO/UNU 2004 report tabulates PAL bands; picking a single "
            "point per enum level is this project's choice, so the honest grade is "
            "estimate, with a wide band feeding the displayed energy interval."
        ),
    )
)

PROJECT_GOAL_ENERGY_POLICY = register_evidence(
    Evidence(
        id="project_goal_energy_policy",
        summary="How far above/below maintenance each body-composition goal sits. Project decision.",
        phenomenon=(
            "no physical process; the size of the energy deficit or surplus this "
            "project applies for a fat-loss or muscle-gain goal, chosen as a "
            "moderate, widely-used policy (a 20% deficit, a 10% surplus)"
        ),
        source="This project's decision.",
        doi=None,
        grade=Grade.PROJECT_DECISION,
        verified=False,
    )
)

PROJECT_DIET_DIAAS_ESTIMATE = register_evidence(
    Evidence(
        id="project_diet_diaas_estimate",
        summary="Representative protein quality (DIAAS) of a day's protein, per diet pattern. Estimate.",
        phenomenon=(
            "the digestible indispensable amino acid score (DIAAS, FAO 2013 "
            "method) of the limiting amino acid in a representative day's protein "
            "for each diet pattern; a single per-diet rollup is a project estimate "
            "and is not the measured DIAAS of any individual food"
        ),
        source="This project's own estimate, informed by published single-food DIAAS values.",
        doi=None,
        grade=Grade.PROJECT_ESTIMATE,
        verified=False,
        note=(
            "Animal proteins (milk, egg) score near or above 1.0; mixed plant "
            "proteins are lower and lysine-limited. A vegan day is scored well "
            "below a non-vegetarian one, so the protein GRAM target is inflated "
            "for lower-quality diets — a plant-forward plate must actually deliver "
            "the utilisable protein, not just hit a gram number. Wide band."
        ),
    )
)

PROJECT_PROTEIN_TARGET_POLICY = register_evidence(
    Evidence(
        id="project_protein_target_policy",
        summary="Protein g/kg for fat-loss and muscle-gain goals. Project decision above the Morton anchor.",
        phenomenon=(
            "no single measured breakpoint; the protein intake this project "
            "targets in an energy deficit (to spare lean mass) or a building "
            "phase, set above the Morton maintenance figure — direction supported "
            "by the deficit-protein literature, exact value a project decision"
        ),
        source="This project's decision, anchored on {morton_2018_protein}.",
        doi=None,
        grade=Grade.PROJECT_DECISION,
        verified=False,
    )
)

# --- BMR: Mifflin-St Jeor coefficients ------------------------------------
# BMR = weight_coeff*kg + height_coeff*cm - age_coeff*years + sex_constant.
# The coefficients are exact regression outputs (uncertainty 0); the equation's
# ~+/-10% individual prediction spread is carried separately below and is what
# feeds the displayed energy interval.
register_constant(Constant(
    key="bmr.mifflin.weight_coeff", value=10.0, unit="kcal/day per kg",
    evidence_id="mifflin_st_jeor_1990",
    applied_to="the body-weight term of the Mifflin-St Jeor RMR equation",
    uncertainty=0.0,
))
register_constant(Constant(
    key="bmr.mifflin.height_coeff", value=6.25, unit="kcal/day per cm",
    evidence_id="mifflin_st_jeor_1990",
    applied_to="the height term of the Mifflin-St Jeor RMR equation",
    uncertainty=0.0,
))
register_constant(Constant(
    key="bmr.mifflin.age_coeff", value=5.0, unit="kcal/day per year",
    evidence_id="mifflin_st_jeor_1990",
    applied_to="the age term (subtracted) of the Mifflin-St Jeor RMR equation",
    uncertainty=0.0,
))
register_constant(Constant(
    key="bmr.mifflin.sex_constant_male", value=5.0, unit="kcal/day",
    evidence_id="mifflin_st_jeor_1990",
    applied_to="the constant term of the Mifflin-St Jeor RMR equation for male bodies",
    uncertainty=0.0,
))
register_constant(Constant(
    key="bmr.mifflin.sex_constant_female", value=-161.0, unit="kcal/day",
    evidence_id="mifflin_st_jeor_1990",
    applied_to="the constant term of the Mifflin-St Jeor RMR equation for female bodies",
    uncertainty=0.0,
))
register_constant(Constant(
    key="bmr.mifflin.rmr_prediction_uncertainty", value=0.10, unit="fraction",
    evidence_id="mifflin_st_jeor_1990",
    applied_to=(
        "the fractional spread between the equation's predicted RMR and an "
        "individual's measured RMR; carried into the displayed energy interval"
    ),
    uncertainty=0.0,
    note="The equation predicts within ~10% for most people, not all; a point RMR is false-precise.",
))

# --- Activity: PAL multipliers (RMR -> total energy) ----------------------
_PAL: tuple[tuple[str, float, str], ...] = (
    ("activity.pal_sedentary", 1.2, "little or no exercise, desk-bound day"),
    ("activity.pal_light", 1.375, "light exercise 1-3 days/week"),
    ("activity.pal_moderate", 1.55, "moderate exercise 3-5 days/week"),
    ("activity.pal_active", 1.725, "hard exercise 6-7 days/week"),
    ("activity.pal_very_active", 1.9, "very hard exercise or a physical job"),
)
for _k, _v, _desc in _PAL:
    register_constant(Constant(
        key=_k, value=_v, unit="ratio (total energy / RMR)",
        evidence_id="project_activity_factor_estimate",
        applied_to=f"multiplying RMR to total daily energy for: {_desc}",
        uncertainty=0.10,
    ))

# --- Protein: g/kg body weight per day, by goal ---------------------------
register_constant(Constant(
    key="protein.g_per_kg_maintain", value=1.6, unit="g/kg/day",
    evidence_id="morton_2018_protein",
    applied_to="the protein intake target for a maintenance goal (Morton breakpoint)",
    uncertainty=0.15,
))
register_constant(Constant(
    key="protein.g_per_kg_lose_fat", value=1.8, unit="g/kg/day",
    evidence_id="project_protein_target_policy",
    applied_to="the protein intake target in an energy deficit, raised to spare lean mass",
    uncertainty=0.15,
))
register_constant(Constant(
    key="protein.g_per_kg_gain_muscle", value=1.8, unit="g/kg/day",
    evidence_id="project_protein_target_policy",
    applied_to="the protein intake target in a building phase",
    uncertainty=0.15,
))

# --- Diet: representative DIAAS by pattern (divides the protein target) ----
# quality_adjusted_grams = base_grams / diaas: a lower score => more grams.
#
# diaas.pescatarian added 2026-08-14 (TASKS_3.md R1a) alongside
# DietPattern.PESCATARIAN: compute_protein and derive_target read this key for
# every DietPattern member (core/nutrition/targets.py's `_diaas_key`), so
# adding the enum member without a matching constant here would leave a
# reachable KeyError rather than an authored estimate -- the same silence the
# module docstring on Ingredient.composition_uncertainty warns against
# elsewhere. 0.97, between eggetarian's 0.95 and non_vegetarian's 1.0: fish
# adds a third complete animal-protein source beyond dairy and egg, closer in
# diversity to unrestricted non-vegetarian than to eggetarian alone. Like its
# four neighbours this is a project estimate, not a per-diet rollup anyone has
# published -- see the REVIEWED_MECHANISM_MATCHES note below.
_DIAAS: tuple[tuple[str, float, str], ...] = (
    ("diaas.non_vegetarian", 1.0, "mixed animal and plant protein across the day"),
    ("diaas.pescatarian", 0.97, "dairy, egg, fish and plant protein"),
    ("diaas.eggetarian", 0.95, "dairy, egg and plant protein"),
    ("diaas.vegetarian", 0.90, "dairy and plant protein, no egg"),
    ("diaas.jain", 0.85, "dairy and plant protein, no root vegetables"),
    ("diaas.vegan", 0.75, "plant protein only, typically lysine-limited"),
)
for _k, _v, _desc in _DIAAS:
    register_constant(Constant(
        key=_k, value=_v, unit="DIAAS (fraction of high-quality protein)",
        evidence_id="project_diet_diaas_estimate",
        applied_to=f"quality-adjusting the protein gram target for: {_desc}",
        uncertainty=0.15,
    ))

# --- Goal: energy multiplier on maintenance TDEE --------------------------
_GOAL_ENERGY: tuple[tuple[str, float, str], ...] = (
    ("energy.goal_factor_lose_fat", 0.80, "a fat-loss goal: a 20% energy deficit"),
    ("energy.goal_factor_maintain", 1.00, "a maintenance goal: no adjustment"),
    ("energy.goal_factor_gain_muscle", 1.10, "a muscle-gain goal: a 10% energy surplus"),
)
for _k, _v, _desc in _GOAL_ENERGY:
    register_constant(Constant(
        key=_k, value=_v, unit="multiplier",
        evidence_id="project_goal_energy_policy",
        applied_to=f"scaling maintenance TDEE to the energy target for {_desc}",
        uncertainty=0.0,
    ))

# --- Macro distribution, fibre, sodium ------------------------------------
register_constant(Constant(
    key="macro.fat_energy_fraction_min", value=0.20, unit="fraction of energy",
    evidence_id="iom_dri_2005",
    applied_to="the lower bound of the fat acceptable macronutrient distribution range",
    uncertainty=0.0,
))
register_constant(Constant(
    key="macro.fat_energy_fraction_max", value=0.35, unit="fraction of energy",
    evidence_id="iom_dri_2005",
    applied_to="the upper bound of the fat acceptable macronutrient distribution range",
    uncertainty=0.0,
))
register_constant(Constant(
    key="nutrient.fibre_g_per_1000kcal", value=14.0, unit="g per 1000 kcal",
    evidence_id="iom_dri_2005",
    applied_to="the adequate dietary fibre intake scaled to a plan's energy target",
    uncertainty=0.10,
))
register_constant(Constant(
    key="nutrient.sodium_max_mg", value=2000.0, unit="mg/day",
    evidence_id="who_sodium_2012",
    applied_to="the daily sodium ceiling applied to a plan (relaxable unless hypertension is flagged)",
    uncertainty=0.0,
))

# --- Meal split: dividing a day's target across meal slots ----------------
# core/nutrition/targets.py derives a whole-DAY target; core/planner/plan.py
# solves ONE meal at a time (one template call = one plate). Comparing a
# single meal's combination against the unscaled day target would make every
# meal fail on energy alone (no breakfast plate is meant to hit a whole day's
# 1800 kcal), which is a modelling error, not evidence about the recipe
# library. These four fractions split the day proportionally by meal_slot,
# named the same as core.schemas.common.MealSlot values so a renamed slot
# fails the lookup loudly rather than falling back to a wrong default. A
# project decision (there is no physical process to measure), not a claim
# from any source — the customary "big lunch" shape of an Indian day, nothing
# more.
_MEAL_SPLIT: tuple[tuple[str, float, str], ...] = (
    ("meal_split.energy_fraction_breakfast", 0.25, "breakfast"),
    ("meal_split.energy_fraction_lunch", 0.35, "lunch"),
    ("meal_split.energy_fraction_dinner", 0.30, "dinner"),
    ("meal_split.energy_fraction_snack", 0.10, "snack"),
)
for _k, _v, _slot in _MEAL_SPLIT:
    register_constant(Constant(
        key=_k, value=_v, unit="fraction of the day's target",
        evidence_id="project_decision",
        applied_to=(
            f"scaling every floor/ceiling/point of a day-level NutritionTarget "
            f"down to a single-meal target for the {_slot} slot"
        ),
        uncertainty=0.0,
    ))

# Per-meal protein bounds (slice 3). Both are fractions of the DAY protein
# floor, so they move with the profile instead of being absolute grams.
#
# Both are PROJECT_DECISION and there is no source for either. The per-meal
# protein-distribution literature that exists (leucine-threshold and per-meal
# dose work) measures the muscle-protein-synthesis response to a bolus, which
# is not what this product optimises; citing it here would be the
# mechanism-mismatch failure the `phenomenon` field exists to prevent. So no
# citation is attached rather than a real-but-wrong one.
#
# 0.15 is chosen below the smallest meal split (snack, 0.10 -- see below for
# why that ordering matters) so the floor cannot on its own make an ordinary
# light meal infeasible. 0.50 is "no single meal carries more than half the
# day's protein".
PROTEIN_MEAL_FLOOR_FRACTION = register_constant(
    Constant(
        key="protein.meal_floor_fraction",
        value=0.15,
        unit="fraction of the day protein floor",
        evidence_id="project_decision",
        applied_to=(
            "the minimum protein one meal must carry, as a floor beneath the "
            "proportional energy-fraction share -- it raises a meal's floor, "
            "never lowers it, so no meal is empty of protein"
        ),
        uncertainty=0.0,
        note=(
            "Applied as max(energy share, this), NOT as a replacement for the "
            "share. Taken literally as a replacement it would LOWER the "
            "reference lunch floor from 39.2 g to 16.8 g, which is a large "
            "loosening nobody asked for; the stated purpose of the bound is to "
            "stop a meal being empty of protein, which is a guard. In practice "
            "it therefore binds only on the snack slot, whose 0.10 energy share "
            "is the only one below it -- that is the case it exists for."
        ),
    )
)
PROTEIN_MEAL_CEILING_FRACTION = register_constant(
    Constant(
        key="protein.meal_ceiling_fraction",
        value=0.50,
        unit="fraction of the day protein floor",
        evidence_id="project_decision",
        applied_to=(
            "the most protein one meal may carry -- what stops the solver "
            "answering a protein floor by piling three katoris of dal onto one "
            "plate"
        ),
        uncertainty=0.0,
        note=(
            "Derived from the day FLOOR, because protein has no day ceiling: "
            "the day target states a minimum and nothing above it. So this is "
            "not half of a ceiling, it is half of the floor, and a day whose "
            "floor is met exactly could in principle be carried by two meals. "
            "No relaxation rung widens it, but it is deliberately NOT "
            "registered as a hard_ceiling: nothing in RELAXATION_ORDER touches "
            "a protein ceiling at all (_relax_protein only lowers the floor), "
            "so the machinery would be a concept with no mechanism behind it."
        ),
    )
)

# The quality-source rule (slice 4). Three PROJECT_DECISION constants that,
# between them, decide which foods a person is told to eat. Read this block
# before touching any of the three values.
#
# WHAT THE RULE IS NOT. It is not a nutritional finding. DIAAS is
# limiting-amino-acid based, so a mixed grain-plus-legume plate scores higher
# than the weighted mean of its parts -- roti and dal complement each other,
# each supplying the amino acid the other is short of. This rule aggregates
# per ingredient line and therefore gives that plate credit for NEITHER part.
# It declines a roti-and-dal plate that complementarity would call adequate.
# **It understates mixed Indian plates specifically, which is the exact food
# this product plans.** That sentence is the honest description of the rule's
# error direction and must not be softened in a later pass.
#
# WHAT IT RESTS ON. `Ingredient.diaas` on the fixture rows, every one of which
# was authored from a recalled range rather than read out of a source
# (docs/methodology.md, "DIAAS values are authored"). Three rows clear 0.75
# today: curd_dahi 1.09, paneer_fresh 1.00, soya_chunks_dry 0.85. tofu_firm at
# 0.65 does not, and 17 of 29 rows carry no DIAAS at all, which this rule reads
# as "does not qualify" -- missing and low are indistinguishable to it. So the
# rule's whole behaviour turns on a dozen invented numbers. That is the most
# load-bearing unsourced field in the project.
PROTEIN_QUALITY_DIAAS_THRESHOLD = register_constant(
    Constant(
        key="protein.quality_diaas_threshold",
        value=0.75,
        unit="DIAAS score",
        evidence_id="project_decision",
        applied_to=(
            "the DIAAS at or above which an ingredient's protein counts toward "
            "a meal's high-quality protein floor -- a cutoff on a score, not a "
            "measurement of anything"
        ),
        uncertainty=0.0,
        note=(
            "0.75 is the boundary of the band FAO's 2013 DIAAS report is "
            "recalled as calling 'good quality' protein, but nobody here has "
            "opened that report, so it is registered as a project decision and "
            "NOT as a citation -- attaching the FAO reference to a number "
            "transcribed from memory is the mismatched-but-real citation "
            "failure this registry exists to prevent. The value was fixed in "
            "the D2a recipe headers before any plan was measured against it, "
            "and it has not been moved since: tofu_firm at an authored 0.65 "
            "fails its own threshold rather than being quietly admitted, which "
            "is the failure direction to keep. Raising it to 0.65 to make tofu "
            "qualify, or to 0.80 to make anything decline, would be tuning a "
            "threshold until plans pass."
        ),
    )
)
PROTEIN_QUALITY_DAY_FRACTION = register_constant(
    Constant(
        key="protein.quality_day_fraction",
        value=0.33,
        unit="fraction of the day protein floor",
        evidence_id="project_decision",
        applied_to=(
            "how much of a day's protein should come from qualifying sources -- "
            "computed and displayed on the day target, gated on by nothing"
        ),
        uncertainty=0.0,
        note=(
            "'Roughly a third from quality sources' is a judgement about what a "
            "plant-forward Indian diet can plausibly reach, not a finding. "
            "NOTHING ENFORCES IT TODAY: enforcing a day FLOOR against a "
            "one-meal-at-a-time planner is a reachability question (can the "
            "remaining slots still close the gap?), not a remaining-budget "
            "subtraction, and that is its own slice -- see "
            "docs/design/target_model_v2.md section 2. Registered now because "
            "the per-meal floor below is stated as a fraction of the same day "
            "protein floor and the two are meant to be read together."
        ),
    )
)
PROTEIN_QUALITY_MEAL_FLOOR_FRACTION = register_constant(
    Constant(
        key="protein.quality_meal_floor_fraction",
        value=0.10,
        unit="fraction of the day protein floor",
        evidence_id="project_decision",
        applied_to=(
            "the minimum qualifying protein one plate must carry -- what makes "
            "'no meal is pure lentil' a bound rather than an intention"
        ),
        uncertainty=0.0,
        note=(
            "Deliberately low, and low for a stated reason: the design wants "
            "most of a day's quality protein to be free to land in one or two "
            "meals, so this is a floor under every plate rather than an even "
            "share of the day. At the reference profile it is 11.2 g, which one "
            "katori of paneer masala (12.8 g) or soya chunk curry (14.6 g) "
            "clears on its own and two katoris of curd (8.9 g) cannot. "
            "Applied FLAT, not scaled by the meal's energy share, unlike "
            "protein.meal_floor_fraction which is a max() guard beneath a "
            "share: quality protein has no day-level share to be a guard "
            "beneath, because nothing apportions the day quality floor across "
            "slots. The cost of flat is real and is not hidden -- a snack slot "
            "gets the same 11.2 g floor as a lunch, on a quarter of the "
            "energy. No template exists for the snack slot today, so that "
            "case is unexercised rather than resolved."
        ),
    )
)

# Mechanism review for every constant registered above. Kept next to the
# registrations (rather than in the literal near the top) so a reviewer sees
# the applied_to and its review verdict together. Single-author mechanism
# review only — it records that phenomenon and applied_to describe the same
# mechanism, never that a source was opened (that is `verified`, still False).
REVIEWED_MECHANISM_MATCHES.update({
    "bmr.mifflin.weight_coeff": "reviewed: RMR regression coefficient, applied to the same RMR equation term",
    "bmr.mifflin.height_coeff": "reviewed: as above",
    "bmr.mifflin.age_coeff": "reviewed: as above",
    "bmr.mifflin.sex_constant_male": "reviewed: as above",
    "bmr.mifflin.sex_constant_female": "reviewed: as above",
    "bmr.mifflin.rmr_prediction_uncertainty": "reviewed: the equation's own reported prediction spread, applied as the RMR interval",
    "activity.pal_sedentary": "reviewed: NO matching primary source; project point within the conventional PAL range",
    "activity.pal_light": "reviewed: NO matching primary source; project point within the conventional PAL range",
    "activity.pal_moderate": "reviewed: NO matching primary source; project point within the conventional PAL range",
    "activity.pal_active": "reviewed: NO matching primary source; project point within the conventional PAL range",
    "activity.pal_very_active": "reviewed: NO matching primary source; project point within the conventional PAL range",
    "protein.g_per_kg_maintain": "reviewed: meta-regression protein breakpoint, applied to the protein intake target",
    "protein.g_per_kg_lose_fat": "reviewed: project decision above the Morton anchor; no single measured breakpoint claimed",
    "protein.g_per_kg_gain_muscle": "reviewed: project decision above the Morton anchor; no single measured breakpoint claimed",
    "diaas.non_vegetarian": "reviewed: NO matching primary source for a per-diet rollup; project estimate of protein quality",
    "diaas.pescatarian": "reviewed: NO matching primary source for a per-diet rollup; project estimate of protein quality",
    "diaas.eggetarian": "reviewed: NO matching primary source for a per-diet rollup; project estimate of protein quality",
    "diaas.vegetarian": "reviewed: NO matching primary source for a per-diet rollup; project estimate of protein quality",
    "diaas.jain": "reviewed: NO matching primary source for a per-diet rollup; project estimate of protein quality",
    "diaas.vegan": "reviewed: NO matching primary source for a per-diet rollup; project estimate of protein quality",
    "energy.goal_factor_lose_fat": "reviewed: project decision, a chosen deficit size, no physical process claimed",
    "energy.goal_factor_maintain": "reviewed: project decision, no adjustment, no physical process claimed",
    "energy.goal_factor_gain_muscle": "reviewed: project decision, a chosen surplus size, no physical process claimed",
    "macro.fat_energy_fraction_min": "reviewed: AMDR fat lower bound, applied to the fat distribution bound",
    "macro.fat_energy_fraction_max": "reviewed: AMDR fat upper bound, applied to the fat distribution bound",
    "nutrient.fibre_g_per_1000kcal": "reviewed: adequate fibre intake per energy, applied to the fibre floor",
    "nutrient.sodium_max_mg": "reviewed: guideline sodium ceiling, applied to the sodium ceiling",
    "meal_split.energy_fraction_breakfast": "reviewed: project decision, no physical process claimed",
    "meal_split.energy_fraction_lunch": "reviewed: project decision, no physical process claimed",
    "meal_split.energy_fraction_dinner": "reviewed: project decision, no physical process claimed",
    "meal_split.energy_fraction_snack": "reviewed: project decision, no physical process claimed",
    "protein.meal_floor_fraction": "reviewed: project decision, no physical process claimed -- deliberately NOT matched to per-meal dose literature, which measures a different phenomenon",
    "protein.meal_ceiling_fraction": "reviewed: project decision, no physical process claimed -- a plausibility bound on one plate, not a nutritional maximum",
    "protein.quality_diaas_threshold": "reviewed: project decision, a cutoff on a score; NO matching primary source -- the FAO band it echoes has not been opened, so it is deliberately not cited",
    "protein.quality_day_fraction": "reviewed: project decision, no physical process claimed -- a judgement about a reachable diet composition, and gated on by nothing today",
    "protein.quality_meal_floor_fraction": "reviewed: project decision, no physical process claimed -- deliberately NOT matched to amino-acid complementarity literature, which describes the opposite effect to the one this bound assumes",
})
