"""The FastAPI app: one real endpoint, ``POST /api/targets``.

Run it with ``uvicorn api.main:app --reload``. The endpoint is deliberately
thin: it builds a ``core.schemas.Profile`` from the request (letting the frozen
dataclass do the validating), calls ``core.nutrition.targets.derive_target``,
and serialises the result. No number is computed here.
"""

from __future__ import annotations

import os
import secrets
import warnings

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from api.auth import current_user, hash_password, login_session, logout_session, verify_password
from api.db import StoredProfile, User, get_db
from api.models import (
    AuthOut,
    ComponentOut,
    EnergyOut,
    EvidenceOut,
    LoginIn,
    PlanEstimateOut,
    PlanOut,
    PlanRequestIn,
    ProfileIn,
    ProfileOut,
    ProteinOut,
    RejectedCitationOut,
    ScienceOut,
    SignupIn,
    SourceOut,
    TargetsOut,
    UserOut,
    ViolationOut,
)
from core.nutrition import citations
from core.nutrition.targets import DerivedTarget, derive_target
from core.planner.plan import default_library, plan_meal
from core.schemas import ClinicalFlag, Profile

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
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
    # Sessions ride a cookie, not a bearer header, so the browser must be
    # allowed to send/receive it cross-port — which requires an explicit
    # origin list above (already true) rather than "*", per the CORS spec.
    allow_credentials=True,
)

# Signed session cookie (Tier B auth): starlette's SessionMiddleware, backed by
# itsdangerous, not a heavier session framework or server-side session store —
# the cookie itself carries the (signed, not encrypted) session dict, so there
# is nothing to look up per request beyond `request.session`.
#
# secret_key: read from FOODAI_SESSION_SECRET in any deployment that sets it.
# An earlier version of this fell back to a fixed string CHECKED INTO SOURCE
# ("dev-only-insecure-secret-do-not-deploy") when the env var was unset — that
# is a real vulnerability, not a style nitpick, regardless of how the fallback
# was named: anyone who reads this file (which is public) could forge a valid
# session cookie for any user against a deployment that never set the env var.
# The fallback now generates a random secret with `secrets.token_hex` at
# process startup instead, which closes that hole at the cost of a real,
# disclosed tradeoff: every session invalidates on process restart, and
# running this API as multiple worker processes without setting the env var
# would give each worker a DIFFERENT random secret, so a session minted by one
# worker would fail to validate on another. `FOODAI_SESSION_SECRET` must be
# set for any deployment where either of those matters — see
# docs/methodology.md, "Accounts and persistence: scope".
_session_secret = os.environ.get("FOODAI_SESSION_SECRET")
if _session_secret is None:
    _session_secret = secrets.token_hex(32)
    warnings.warn(
        "FOODAI_SESSION_SECRET is not set. Using a random secret generated for "
        "this process only: existing sessions will stop validating on restart, "
        "and running multiple worker processes without this env var set will "
        "make their sessions mutually invalid. Fine for local, single-process "
        "dev; set FOODAI_SESSION_SECRET explicitly for anything else.",
        stacklevel=1,
    )

# same_site="lax", set deliberately, not left at whatever starlette defaults
# to: the real CSRF threat model here is a third-party site (attacker.com)
# submitting a state-changing request (POST /api/profile, POST /api/auth/
# logout) using a signed-in user's cookie. SameSite=Lax blocks the cookie on
# exactly that cross-SITE, non-GET request. It does NOT block the cookie
# between :3000 and :8000 -- browsers classify same-site by registrable
# domain, not port, so both localhost ports are "same-site" to each other --
# but that's the legitimate case this app's own frontend needs, not a hole:
# every state-changing endpoint here is POST/PUT, never GET, so there is no
# safe-method cross-site request that leaks state. https_only=False because
# local dev runs over plain HTTP; a real deployment over HTTPS should set it.
app.add_middleware(
    SessionMiddleware,
    secret_key=_session_secret,
    session_cookie="foodai_session",
    same_site="lax",
    https_only=False,
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# --------------------------------------------------------------------------
# Accounts + profile persistence (Tier B: session cookie, SQLite, bcrypt).
#
# No email verification, no password reset, no OAuth, nothing commerce-shaped
# — see docs/methodology.md's "Accounts and persistence: scope" for the
# named, deliberate limit. core/nutrition and core/planner are not imported
# by anything below except to build the same core.schemas.Profile the
# unauthenticated /api/targets and /api/plan endpoints already build; this
# section computes no nutritional number of its own.
# --------------------------------------------------------------------------


def _profile_out(sp: StoredProfile) -> ProfileOut:
    return ProfileOut(
        weight_kg=sp.weight_kg,
        height_cm=sp.height_cm,
        age_years=sp.age_years,
        sex=sp.sex,
        activity=sp.activity,
        goal=sp.goal,
        diet=sp.diet,
        clinical_flags=[ClinicalFlag(f) for f in sp.flags_list()],
        updated_at=sp.updated_at.isoformat(),
    )


def _validate_profile_in(body: ProfileIn) -> Profile:
    """Build a real core.schemas.Profile purely to let it validate the input.

    Not stored or returned — StoredProfile persists the raw fields, and the
    frozen dataclass's own __post_init__ (positive weight/height/age, and
    warnings for implausible-but-valid bodies) is the single source of truth
    for what a valid profile looks like, so this reuses it rather than
    re-deriving the same bounds checks in api/db.py.
    """

    try:
        return Profile(
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


def _upsert_profile(db: Session, user: User, body: ProfileIn) -> StoredProfile:
    _validate_profile_in(body)  # raises 422 on impossible input, discards the result
    sp = db.query(StoredProfile).filter(StoredProfile.user_id == user.id).one_or_none()
    if sp is None:
        sp = StoredProfile(user_id=user.id)
        db.add(sp)
    sp.weight_kg = body.weight_kg
    sp.height_cm = body.height_cm
    sp.age_years = body.age_years
    sp.sex = body.sex.value
    sp.activity = body.activity.value
    sp.goal = body.goal.value
    sp.diet = body.diet.value
    sp.clinical_flags = ",".join(f.value for f in body.clinical_flags)
    db.commit()
    db.refresh(sp)
    return sp


@app.post("/api/auth/signup", response_model=AuthOut, status_code=201)
def signup(body: SignupIn, request: Request, db: Session = Depends(get_db)) -> AuthOut:
    existing = db.query(User).filter(User.email == body.email).one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    login_session(request, user.id)

    profile_out: ProfileOut | None = None
    if body.profile is not None:
        sp = _upsert_profile(db, user, body.profile)
        profile_out = _profile_out(sp)

    return AuthOut(
        user=UserOut(id=user.id, email=user.email, created_at=user.created_at.isoformat()),
        profile=profile_out,
    )


@app.post("/api/auth/login", response_model=AuthOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)) -> AuthOut:
    user = db.query(User).filter(User.email == body.email).one_or_none()
    # Same 401 for "no such account" and "wrong password": distinguishing them
    # would tell an attacker which emails have accounts.
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    login_session(request, user.id)

    sp = db.query(StoredProfile).filter(StoredProfile.user_id == user.id).one_or_none()
    return AuthOut(
        user=UserOut(id=user.id, email=user.email, created_at=user.created_at.isoformat()),
        profile=_profile_out(sp) if sp is not None else None,
    )


@app.post("/api/auth/logout")
def logout(request: Request) -> dict[str, str]:
    logout_session(request)
    return {"status": "ok"}


@app.get("/api/auth/me", response_model=UserOut)
def me(request: Request, db: Session = Depends(get_db)) -> UserOut:
    user = current_user(request, db)
    return UserOut(id=user.id, email=user.email, created_at=user.created_at.isoformat())


@app.get("/api/profile", response_model=ProfileOut)
def get_profile(request: Request, db: Session = Depends(get_db)) -> ProfileOut:
    user = current_user(request, db)
    sp = db.query(StoredProfile).filter(StoredProfile.user_id == user.id).one_or_none()
    if sp is None:
        raise HTTPException(status_code=404, detail="No profile saved yet.")
    return _profile_out(sp)


@app.put("/api/profile", response_model=ProfileOut)
def put_profile(body: ProfileIn, request: Request, db: Session = Depends(get_db)) -> ProfileOut:
    user = current_user(request, db)
    sp = _upsert_profile(db, user, body)
    return _profile_out(sp)


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


@app.get("/api/science", response_model=ScienceOut)
def science() -> ScienceOut:
    """The whole citation registry: every ``Evidence`` this build has, verbatim.

    Not scoped to one profile's derivation (``/api/targets``'s own ``sources``
    already does that) — this is the canonical page a "why these numbers?"
    expander links to, so it returns everything, including the entries no
    single derivation happens to touch (e.g. rejected citations, oil-uptake
    and composition-uncertainty estimates that back ``core/foods`` rather than
    ``core/nutrition``). No number or citation string here is computed; this
    endpoint only serialises ``core.nutrition.citations``' own registries.
    """

    evidence_rows = [
        EvidenceOut(
            id=ev.id,
            summary=ev.summary,
            phenomenon=ev.phenomenon,
            source=ev.source,
            grade=ev.grade.value,
            doi=ev.doi,
            url=ev.url,
            verified=ev.verified,
            note=ev.note,
        )
        for ev in citations.all_evidence()
    ]
    rejected_rows = [
        RejectedCitationOut(
            for_constant=rc.for_constant,
            citation=rc.citation,
            doi=rc.doi,
            phenomenon_measured=rc.phenomenon_measured,
            why_rejected=rc.why_rejected,
        )
        for rc in citations.REJECTED_CITATIONS
    ]
    return ScienceOut(
        scope_statement=(
            "This is a portfolio project, not clinical nutrition guidance. "
            "Every number traces to a source below, graded by how strong that "
            "source is; project estimates are marked plainly, never dressed up "
            "as measured data. Nothing here is a substitute for advice from a "
            "dietitian or a doctor."
        ),
        evidence=evidence_rows,
        rejected_citations=rejected_rows,
        unverified_count=sum(1 for e in citations.all_evidence() if not e.verified),
        total_count=len(evidence_rows),
    )


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
            quality_source_day_g=dt.protein.quality_source_day_g,
        ),
        fat_g=dt.fat_g,
        carb_g=dt.carb_g,
        fibre_g_min=dt.fibre_g_min,
        sodium_mg_max=dt.sodium_mg_max,
        warnings=list(dt.warnings),
        sources=_sources_out(dt),
    )


@app.post("/api/plan", response_model=PlanOut)
def plan(body: PlanRequestIn) -> PlanOut:
    """Generate one meal's plate for a profile, or decline and say why.

    Thin wiring only: derive the profile's day-level target (same call
    ``/api/targets`` makes), hand it to ``core.planner.plan.plan_meal``
    (target -> per-meal split -> candidate pool -> combinations -> relaxation
    ladder), and serialise whatever ``LadderOutcome`` comes back. No number is
    computed here — the solved unit counts and the point estimate are read
    straight off ``outcome.plan``.
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
    # Passed explicitly rather than left to the default, so the value echoed
    # back in `PlanOut.dev_mode` is the one this call actually used. Reading it
    # off a default two modules away is how a label ends up describing a run
    # that did not happen.
    dev_mode = True
    outcome = plan_meal(
        default_library(),
        dt.nutrition_target,
        region=body.region,
        meal_slot=body.meal_slot,
        diet_pattern=body.diet,
        profile=profile,
        dev_mode=dev_mode,
    )

    components: list[ComponentOut] = []
    estimate: PlanEstimateOut | None = None
    if outcome.plan is not None:
        for component in outcome.plan.combination.components:
            components.append(
                ComponentOut(
                    recipe_id=component.recipe.id,
                    recipe_name=component.recipe.name,
                    category=component.category,
                    unit_count=outcome.plan.counts_for(component),
                    unit_name=component.recipe.serving_unit.name,
                )
            )
        point = outcome.plan.estimate.point
        estimate = PlanEstimateOut(
            energy_kcal=point.energy_kcal,
            protein_g=point.protein_g,
            fat_g=point.fat_g,
            carb_g=point.carb_g,
            fibre_g=point.fibre_g,
            sodium_mg=point.sodium_mg,
            # Read off the estimate `core/` already computed, not recomputed
            # here: this package computes no nutritional number, and a second
            # derivation could disagree with the one demo.py prints.
            unverified_energy_kcal=outcome.plan.estimate.unverified_energy_kcal,
            unverified_energy_fraction=outcome.plan.estimate.unverified_energy_fraction(),
        )

    return PlanOut(
        passed=outcome.result.passed,
        dev_mode=dev_mode,
        disclosure=outcome.result.disclosure or "",
        relaxation_applied=list(outcome.result.relaxation_applied),
        violations=[v.describe() for v in outcome.result.violations],
        violation_detail=[
            ViolationOut(
                macro=v.macro,
                kind=v.kind,
                bound_source=v.bound_source,
                reach=v.reach,
                relaxability=v.relaxability,
                blocking_slots=list(v.blocking_slots),
                locked_by=[f.value for f in v.locked_by],
                text=v.describe(),
            )
            for v in outcome.result.violations
        ],
        components=components,
        estimate=estimate,
    )
