"""The FastAPI app: one real endpoint, ``POST /api/targets``.

Run it with ``uvicorn api.main:app --reload``. The endpoint is deliberately
thin: it builds a ``core.schemas.Profile`` from the request (letting the frozen
dataclass do the validating), calls ``core.nutrition.targets.derive_target``,
and serialises the result. No number is computed here.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import (
    EnergyOut,
    ProfileIn,
    ProteinOut,
    SourceOut,
    TargetsOut,
)
from core.nutrition import citations
from core.nutrition.targets import DerivedTarget, derive_target
from core.schemas import Profile

app = FastAPI(
    title="Arusuvai targets API",
    version="0.1.0",
    summary="Turns a body/goal profile into a cited, dev-mode nutritional target.",
)

# Dev-only: the static onboarding page (a later increment) will fetch this from
# a different localhost port. Scoped to localhost so it is not a blanket opener.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _sources_out(dt: DerivedTarget) -> list[SourceOut]:
    """Provenance for every constant the derivation read."""

    out: list[SourceOut] = []
    for key in dt.sources:
        c = citations.constant(key)
        ev = citations.evidence(c.evidence_id)
        out.append(
            SourceOut(
                key=key,
                value=c.value,
                unit=c.unit,
                source=ev.source,
                grade=ev.grade.value,
                doi=ev.doi,
                verified=ev.verified,
            )
        )
    return out


@app.post("/api/targets", response_model=TargetsOut)
def targets(body: ProfileIn) -> TargetsOut:
    """Derive the nutritional target for a profile.

    Impossible input (non-positive weight/height/age) raises in ``Profile`` and
    becomes a 422. Implausible-but-valid input (e.g. a 300 kg weight) is accepted
    and surfaced in ``warnings`` rather than rejected — the same warn-don't-clamp
    contract the core schema uses.
    """

    try:
        profile = Profile(
            weight_kg=body.weight_kg,
            height_cm=body.height_cm,
            age_years=body.age_years,
            sex=body.sex,
            activity=body.activity,
            goal=body.goal,
            diet=body.diet,
            clinical_flags=frozenset(body.clinical_flags),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    dt = derive_target(profile)
    lo, hi = dt.energy_interval()

    return TargetsOut(
        status=dt.status,
        disclosure=dt.disclosure,
        bmr_kcal=dt.bmr_kcal,
        tdee_kcal=dt.tdee_kcal,
        energy=EnergyOut(
            kcal=dt.energy_kcal, low=lo, high=hi, uncertainty=dt.energy_uncertainty
        ),
        protein=ProteinOut(
            base_g=dt.protein.base_g,
            quality_adjusted_g=dt.protein.quality_adjusted_g,
            g_per_kg=dt.protein.g_per_kg,
            diaas=dt.protein.diaas,
        ),
        fat_g=dt.fat_g,
        carb_g=dt.carb_g,
        fibre_g_min=dt.fibre_g_min,
        sodium_mg_max=dt.sodium_mg_max,
        warnings=list(dt.warnings),
        sources=_sources_out(dt),
    )
