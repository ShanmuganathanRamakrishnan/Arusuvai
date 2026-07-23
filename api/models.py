"""Pydantic request/response shapes for the HTTP boundary.

These exist only to validate JSON and serialise the core dataclasses; they carry
no logic. The enums are the same ``core.schemas`` string enums, so a JSON body
like ``{"sex": "male", "diet": "vegan"}`` maps straight through, and an
unrecognised value is rejected at the boundary rather than deep in core.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from core.schemas import ActivityLevel, ClinicalFlag, DietPattern, Goal, Sex


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
