"""Pydantic request/response shapes for the HTTP boundary.

These exist only to validate JSON and serialise the core dataclasses; they carry
no logic. The enums are the same ``core.schemas`` string enums, so a JSON body
like ``{"sex": "male", "diet": "vegan"}`` maps straight through, and an
unrecognised value is rejected at the boundary rather than deep in core.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from core.schemas import ActivityLevel, ClinicalFlag, DietPattern, Goal, MealSlot, Region, Sex


class ProfileIn(BaseModel):
    """The onboarding form's payload."""

    weight_kg: float = Field(gt=0, description="Body weight in kilograms.")
    height_cm: float = Field(gt=0, description="Height in centimetres.")
    age_years: int = Field(gt=0, description="Age in whole years.")
    sex: Sex
    activity: ActivityLevel
    goal: Goal
    diet: DietPattern
    clinical_flags: list[ClinicalFlag] = Field(default_factory=list)


class EnergyOut(BaseModel):
    kcal: float
    low: float
    high: float
    uncertainty: float


class ProteinOut(BaseModel):
    base_g: float
    quality_adjusted_g: float
    g_per_kg: float
    diaas: float


class SourceOut(BaseModel):
    """One constant and where it comes from — 'every number traceable to a paper'."""

    key: str
    value: float
    unit: str
    source: str
    grade: str
    doi: str | None = None
    verified: bool


class TargetsOut(BaseModel):
    """The derived, cited, dev-mode-labelled target for one profile."""

    status: str
    disclosure: str
    bmr_kcal: float
    tdee_kcal: float
    energy: EnergyOut
    protein: ProteinOut
    fat_g: float
    carb_g: float
    fibre_g_min: float
    sodium_mg_max: float
    warnings: list[str]
    sources: list[SourceOut]


class PlanRequestIn(ProfileIn):
    """The onboarding profile plus which plate to generate."""

    region: Region
    meal_slot: MealSlot


class ComponentOut(BaseModel):
    """One recipe playing one role in the plate, at its solved unit count."""

    recipe_id: str
    recipe_name: str
    category: str
    unit_count: int
    unit_name: str


class PlanEstimateOut(BaseModel):
    """The solved plan's point estimate. Present only when a plan passed."""

    energy_kcal: float
    protein_g: float
    fat_g: float
    carb_g: float
    fibre_g: float
    sodium_mg: float


class EvidenceOut(BaseModel):
    """One registered source, exactly as ``core.nutrition.citations`` holds it.

    This is the ``GET /api/science`` payload's unit — the canonical home for
    citation text (DESIGN_SYSTEM.md, "Content redundancy rule"). No frontend
    page may hardcode a summary/phenomenon/source string of its own; it fetches
    this at request time and links back here instead of restating it.
    """

    id: str
    summary: str
    phenomenon: str
    source: str
    grade: str
    doi: str | None = None
    url: str | None = None
    verified: bool
    note: str


class RejectedCitationOut(BaseModel):
    """A real source that was found and deliberately not used, and why."""

    for_constant: str
    citation: str
    doi: str | None = None
    phenomenon_measured: str
    why_rejected: str


class ScienceOut(BaseModel):
    """The whole citation registry, for the "why these numbers?" expander.

    ``scope_statement`` lives here rather than in the frontend so the one
    sentence every page must show ("not a substitute for clinical nutrition
    guidance") has one canonical source too, not a copy pasted into every page
    that needs it.
    """

    scope_statement: str
    evidence: list[EvidenceOut]
    rejected_citations: list[RejectedCitationOut]
    unverified_count: int
    total_count: int


class ProfileOut(BaseModel):
    """A user's persisted profile, as stored — the ``GET``/``PUT /api/profile``
    shape. Same fields as ``ProfileIn``; kept as a separate model (rather than
    reusing ``ProfileIn`` for the response too) because a response also needs
    ``updated_at``, which a request body never supplies.
    """

    weight_kg: float
    height_cm: float
    age_years: int
    sex: Sex
    activity: ActivityLevel
    goal: Goal
    diet: DietPattern
    clinical_flags: list[ClinicalFlag]
    updated_at: str


class SignupIn(BaseModel):
    """Tier B, not Tier C: email + password only — no OAuth, no name field."""

    email: EmailStr
    password: str = Field(min_length=8, description="At least 8 characters.")
    #: If the signup happens at the onboarding-to-dashboard hinge, the
    #: just-completed profile is attached here so it is persisted in the same
    #: request as account creation — "don't lose the work someone already did
    #: filling out five steps" (this increment's brief).
    profile: ProfileIn | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    created_at: str


class AuthOut(BaseModel):
    """The response to signup and login alike: who's signed in, and their
    profile if one is already on file (present immediately after a signup
    that included one; present after login for any returning user)."""

    user: UserOut
    profile: ProfileOut | None = None


class PlanOut(BaseModel):
    """Either a solved, validated plate or an honest decline.

    ``passed=False`` is not an error — CLAUDE.md's relaxation ladder makes
    this the expected outcome whenever the recipe library cannot fill a
    template's required slots for the requested (region, meal_slot), and
    ``disclosure`` names the specific blocking reason rather than a generic
    failure.
    """

    passed: bool
    disclosure: str
    relaxation_applied: list[str]
    violations: list[str]
    components: list[ComponentOut] = Field(default_factory=list)
    estimate: PlanEstimateOut | None = None
