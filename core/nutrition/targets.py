"""Derive a nutritional target from a :class:`Profile`.

This is the first place the product does something *real*: it turns a user's
body and goal into an energy/protein/macro target, with every number traced to
a constant in :mod:`core.nutrition.citations`. The pipeline is entirely
deterministic — no LLM touches any quantity here (CLAUDE.md, "Central
invariant"):

    BMR (Mifflin-St Jeor)
      -> TDEE = BMR * activity PAL
        -> energy target = TDEE * goal factor
    protein g/kg (by goal) * weight    <- the floor, unadjusted for quality
    energy -> fat (AMDR midpoint) + carb (remainder) + fibre + sodium ceiling

``diet`` is still read here, but as of 2026-08-02 (slice 2) it changes no
target value: DIAAS is computed and reported, never applied. Protein quality
became a constraint on which sources fill the target rather than a multiplier
on it, and that constraint (slice 4) is not built. Between the two, ``diet``
moves nothing — see :class:`ProteinTarget` and ``docs/methodology.md``.

Two rules from CLAUDE.md shape the output:

* **Display the interval, never a false-precise point.** The energy target
  carries the Mifflin equation's own ~+/-10% prediction spread combined with
  activity-factor uncertainty, so callers show "~1,850 kcal (+/-14%)", not
  "1,847 kcal". :meth:`DerivedTarget.energy_interval` exposes it.
* **Nothing here can ship as validated.** Every backing constant rests on
  `verified=False` evidence (nobody has opened the source documents), so
  :attr:`DerivedTarget.status` is always ``"dev_mode"`` today and a one-line
  disclosure says so. ``dev_mode`` is kept distinct from ``validated`` exactly
  as CLAUDE.md's round-4 addendum requires; it is computed from the evidence,
  not hard-coded, so it will flip on its own when a human verifies the sources.

The target it produces is the canonical :class:`~core.nutrition.target.
NutritionTarget` (built via :func:`~core.nutrition.target.simple_target`), the
same shape ``core/planner`` consumes — not a parallel one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.nutrition import citations
from core.nutrition.target import NutritionTarget, simple_target
from core.schemas.profile import ActivityLevel, Goal, Profile, Sex

__all__ = [
    "DerivedTarget",
    "ProteinTarget",
    "bmr_mifflin_st_jeor",
    "tdee",
    "energy_target",
    "compute_protein",
    "derive_target",
]


# The enum values are the constant-key suffixes on purpose (activity.value ==
# "moderate" -> "activity.pal_moderate"), so the mapping is one line and a
# renamed enum member fails loudly at lookup rather than silently reading the
# wrong constant. Verified by tests/test_nutrition_targets.py.
def _pal_key(activity: ActivityLevel) -> str:
    return f"activity.pal_{activity.value}"


def _goal_energy_key(goal: Goal) -> str:
    return f"energy.goal_factor_{goal.value}"


def _protein_key(goal: Goal) -> str:
    return f"protein.g_per_kg_{goal.value}"


def _diaas_key(profile: Profile) -> str:
    return f"diaas.{profile.diet.value}"


def bmr_mifflin_st_jeor(profile: Profile) -> float:
    """Resting metabolic rate, kcal/day, from the Mifflin-St Jeor equation.

    BMR = 10*kg + 6.25*cm - 5*years + (male: +5, female: -161). Every
    coefficient is read from the registry, so this function contains no
    nutritional number of its own.
    """

    w = citations.value_of("bmr.mifflin.weight_coeff")
    h = citations.value_of("bmr.mifflin.height_coeff")
    a = citations.value_of("bmr.mifflin.age_coeff")
    sex_const = citations.value_of(
        "bmr.mifflin.sex_constant_male"
        if profile.sex is Sex.MALE
        else "bmr.mifflin.sex_constant_female"
    )
    return (
        w * profile.weight_kg
        + h * profile.height_cm
        - a * profile.age_years
        + sex_const
    )


def tdee(profile: Profile) -> float:
    """Total daily energy expenditure at maintenance: BMR * activity PAL."""

    return bmr_mifflin_st_jeor(profile) * citations.value_of(_pal_key(profile.activity))


def energy_target(profile: Profile) -> float:
    """The goal-adjusted energy target: maintenance TDEE * goal factor."""

    return tdee(profile) * citations.value_of(_goal_energy_key(profile.goal))


def _energy_uncertainty(profile: Profile) -> float:
    """Fractional 1-sigma-ish spread on the energy target, for display.

    Combines the equation's own RMR prediction spread with the activity-factor
    uncertainty in quadrature (independent sources multiply, so their fractional
    uncertainties add in quadrature). The goal factor is a chosen policy with
    zero uncertainty, so it does not widen the band.
    """

    rmr = citations.value_of("bmr.mifflin.rmr_prediction_uncertainty")
    pal = citations.uncertainty_of(_pal_key(profile.activity))
    return math.sqrt(rmr * rmr + pal * pal)


@dataclass(frozen=True)
class ProteinTarget:
    """The protein target. ``base_g`` is the one the planner gates on.

    **Changed 2026-08-02 (slice 2, the DIAAS reversal).** ``base_g`` used to be
    kept "only so the adjustment is inspectable" and ``quality_adjusted_g``
    (``base_g / diaas``) was the floor. That is now reversed, and the reasoning
    is worth keeping because the old shape looked obviously right:

    Inflating the gram target to compensate for a low-DIAAS diet answers a
    quality problem with volume. It tells a vegetarian to eat 12 g/day more
    protein of the same limiting-amino-acid profile, which does not supply the
    missing amino acid — it supplies more of what was already there. Protein
    quality is a constraint on *which sources* fill the target, not a multiplier
    on the target. That constraint is the quality-source rule (slice 4), which
    is blocked on the ingredient set having more than one qualifying row.

    So ``quality_adjusted_g`` survives as an inspectable figure and **nothing
    gates on it**. It is deliberately not deleted: the number is what makes the
    reversal legible to a reader, and a silent removal would leave the per-diet
    ``diaas.*`` constants in the registry with nothing explaining why they no
    longer move a target.

    Between this slice and slice 4, protein quality influences nothing at all.
    That is a real gap, stated rather than papered over — see
    ``docs/methodology.md``.
    """

    #: The floor the planner gates on: weight x g/kg, no quality adjustment.
    base_g: float
    #: ``base_g / diaas``. Display and inspection only; NOT gated on. Do not
    #: reintroduce this into ``simple_target`` — see the class docstring.
    quality_adjusted_g: float
    g_per_kg: float
    diaas: float


def compute_protein(profile: Profile) -> ProteinTarget:
    """Protein grams/day. ``diaas`` is reported, not applied to the target."""

    g_per_kg = citations.value_of(_protein_key(profile.goal))
    diaas = citations.value_of(_diaas_key(profile))
    base_g = profile.weight_kg * g_per_kg
    # Divide, not multiply: DIAAS < 1 would mean MORE grams to hit the same
    # utilisable-protein requirement. Computed so the figure stays inspectable
    # and the per-diet constants stay meaningful, but no longer used as the
    # target -- see ProteinTarget's docstring for why volume is the wrong
    # answer to a quality question.
    quality_adjusted_g = base_g / diaas
    return ProteinTarget(
        base_g=base_g,
        quality_adjusted_g=quality_adjusted_g,
        g_per_kg=g_per_kg,
        diaas=diaas,
    )


def _compute_macros(
    energy_kcal: float, protein_g: float
) -> tuple[float, float, tuple[str, ...]]:
    """Fat (AMDR midpoint) and carbohydrate (remainder) grams; plus warnings.

    Protein grams are already fixed by the (quality-adjusted) protein target, so
    only fat and carbohydrate are free. Fat takes the midpoint of the IOM AMDR
    range; carbohydrate absorbs the remaining energy — the least load-bearing
    macros, exactly as CLAUDE.md's relaxation ladder treats them.
    """

    kcal_p = citations.value_of("atwater.protein_kcal_per_g")
    kcal_f = citations.value_of("atwater.fat_kcal_per_g")
    kcal_c = citations.value_of("atwater.carb_kcal_per_g")
    fat_frac_lo = citations.value_of("macro.fat_energy_fraction_min")
    fat_frac_hi = citations.value_of("macro.fat_energy_fraction_max")

    fat_frac = (fat_frac_lo + fat_frac_hi) / 2.0  # AMDR midpoint (~27.5%)
    fat_energy = fat_frac * energy_kcal
    fat_g = fat_energy / kcal_f

    protein_energy = protein_g * kcal_p
    carb_energy = energy_kcal - protein_energy - fat_energy

    warnings: list[str] = []
    if carb_energy < 0:
        # Quality-adjusted protein plus fat already exceed the energy target —
        # real for a heavy person on a low-DIAAS diet in a deficit. Never
        # silently clamp: record it (CLAUDE.md, "Errors") and floor carbs at 0.
        warnings.append(
            f"protein ({protein_g:.0f} g) and fat together exceed the "
            f"{energy_kcal:.0f} kcal energy target; carbohydrate floored at 0 g. "
            "The quality-adjusted protein target is very demanding at this "
            "calorie level for this diet."
        )
        carb_energy = 0.0
    carb_g = carb_energy / kcal_c
    return fat_g, carb_g, tuple(warnings)


@dataclass(frozen=True)
class DerivedTarget:
    """A profile's full target: the planner shape plus everything to display it.

    ``nutrition_target`` is the canonical :class:`NutritionTarget` the solver and
    validator consume. The remaining fields are the honest presentation layer:
    the energy interval, the protein quality adjustment, the provenance, and the
    ``dev_mode`` status with its one-line disclosure.
    """

    nutrition_target: NutritionTarget
    bmr_kcal: float
    tdee_kcal: float
    energy_kcal: float
    energy_uncertainty: float
    protein: ProteinTarget
    fat_g: float
    carb_g: float
    fibre_g_min: float
    sodium_mg_max: float
    status: str
    disclosure: str
    warnings: tuple[str, ...]
    sources: tuple[str, ...]

    def energy_interval(self) -> tuple[float, float]:
        """(low, high) kcal for the display band, e.g. '~1,850 kcal (+/-14%)'."""

        u = self.energy_uncertainty
        return self.energy_kcal * (1 - u), self.energy_kcal * (1 + u)


# Every constant this derivation reads. Listed so DerivedTarget.sources can
# report provenance ("every number traceable to a paper") and so status can be
# computed from the verified-ness of exactly these, nothing more, nothing less.
_SOURCE_KEYS: tuple[str, ...] = (
    "bmr.mifflin.weight_coeff",
    "bmr.mifflin.height_coeff",
    "bmr.mifflin.age_coeff",
    "bmr.mifflin.sex_constant_male",
    "bmr.mifflin.sex_constant_female",
    "bmr.mifflin.rmr_prediction_uncertainty",
    "protein.g_per_kg_maintain",
    "protein.g_per_kg_lose_fat",
    "protein.g_per_kg_gain_muscle",
    "diaas.non_vegetarian",
    "diaas.eggetarian",
    "diaas.vegetarian",
    "diaas.jain",
    "diaas.vegan",
    "energy.goal_factor_lose_fat",
    "energy.goal_factor_maintain",
    "energy.goal_factor_gain_muscle",
    "activity.pal_sedentary",
    "activity.pal_light",
    "activity.pal_moderate",
    "activity.pal_active",
    "activity.pal_very_active",
    "atwater.protein_kcal_per_g",
    "atwater.fat_kcal_per_g",
    "atwater.carb_kcal_per_g",
    "macro.fat_energy_fraction_min",
    "macro.fat_energy_fraction_max",
    "nutrient.fibre_g_per_1000kcal",
    "nutrient.sodium_max_mg",
)


def _status_and_disclosure() -> tuple[str, str]:
    """``dev_mode`` unless every source constant rests on verified evidence.

    Computed, not hard-coded: this returns ``validated`` the day a human flips
    the last source's ``verified`` flag, and ``dev_mode`` until then. Today
    every source is unverified, so it is always ``dev_mode``.
    """

    all_verified = all(
        citations.evidence(citations.constant(k).evidence_id).verified
        for k in _SOURCE_KEYS
    )
    if all_verified:
        return "validated", ""
    disclosure = (
        "These targets are dev-mode, not validated: the equations behind them "
        "(Mifflin-St Jeor, the activity and protein factors, the macronutrient "
        "ranges) have not yet been checked against their primary sources, so "
        "treat the numbers as careful estimates carrying the stated uncertainty, "
        "not settled values."
    )
    return "dev_mode", disclosure


def _clinical_flag_warning(profile: Profile) -> tuple[str, ...]:
    """Disclose that clinical_flags do not adjust any number here.

    ``Profile.clinical_flags`` is read by ``core/planner/validator.py`` to
    *lock* a constraint out of the relaxation ladder later — it never *tightens*
    a target value here. `core/nutrition` cannot even see the flag->macro
    mapping that does that locking (`LOCKED_CONSTRAINTS` lives in
    `core/planner`, and `core/nutrition` must never import `core/planner`,
    CLAUDE.md "Architecture"). So a hypertensive profile gets the exact same
    `nutrient.sodium_max_mg` ceiling as anyone else at this stage: a deliberate
    scope boundary (docs/methodology.md, "Clinical flags do not tighten a
    target"), not a silent one. Disclosed here, structurally, rather than left
    for a caller to remember to mention next to a clinical-flags checkbox.
    """

    if not profile.clinical_flags:
        return ()
    flags = ", ".join(f.value for f in sorted(profile.clinical_flags, key=lambda f: f.value))
    return (
        f"You've disclosed: {flags}. These targets are general-population "
        "values — no number above is adjusted for a diagnosed condition. "
        "Disclosed flags currently only prevent the affected limit from being "
        "loosened later, during plan generation; they do not tighten it now. "
        "This is not a substitute for clinical dietary guidance.",
    )


def derive_target(profile: Profile) -> DerivedTarget:
    """Turn a Profile into a full, cited, dev-mode-labelled nutritional target."""

    bmr = bmr_mifflin_st_jeor(profile)
    tdee_kcal = tdee(profile)
    energy = energy_target(profile)
    energy_unc = _energy_uncertainty(profile)

    protein = compute_protein(profile)
    # base_g, not quality_adjusted_g. This feeds carbohydrate as well as the
    # protein floor -- _compute_macros derives carb as the energy remainder --
    # so dropping the inflation RAISES the carb target by the energy the
    # inflated protein was claiming. That side effect is real and intended-by-
    # implication rather than asked for; see the slice 2 commit and
    # docs/design/target_model_v2.md.
    fat_g, carb_g, macro_warnings = _compute_macros(energy, protein.base_g)

    fibre_per_1000 = citations.value_of("nutrient.fibre_g_per_1000kcal")
    fibre_g_min = fibre_per_1000 * energy / 1000.0
    sodium_mg_max = citations.value_of("nutrient.sodium_max_mg")

    # Delegate to simple_target so the floor/ceiling/point band math and the
    # default tolerances live in exactly one place (core.nutrition.target),
    # shared with the relaxation ladder. The protein FLOOR is base_g: quality
    # is a constraint on which sources fill it, not a multiplier on it, and
    # nothing gates on quality_adjusted_g any more (ProteinTarget's docstring).
    target = simple_target(
        energy_kcal=energy,
        protein_g_min=protein.base_g,
        fat_g=fat_g,
        carb_g=carb_g,
        sodium_mg_max=sodium_mg_max,
        fibre_g_min=fibre_g_min,
    )

    status, disclosure = _status_and_disclosure()

    return DerivedTarget(
        nutrition_target=target,
        bmr_kcal=bmr,
        tdee_kcal=tdee_kcal,
        energy_kcal=energy,
        energy_uncertainty=energy_unc,
        protein=protein,
        fat_g=fat_g,
        carb_g=carb_g,
        fibre_g_min=fibre_g_min,
        sodium_mg_max=sodium_mg_max,
        status=status,
        disclosure=disclosure,
        # profile.warnings (implausible body inputs) + macro warnings + the
        # clinical-flags disclosure, so the caller sees every caveat in one place.
        warnings=tuple(profile.warnings) + macro_warnings + _clinical_flag_warning(profile),
        sources=_SOURCE_KEYS,
    )
