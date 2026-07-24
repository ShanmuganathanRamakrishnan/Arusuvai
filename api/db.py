"""SQLite persistence for accounts and profiles — Tier B, not Tier C.

Two tables, no ORM cleverness: ``User`` (id, email, hashed_password,
created_at) and ``StoredProfile`` (one row per user, upserted whenever the
onboarding flow or the dashboard's "edit profile" link saves). Nothing here
computes a nutritional number — ``StoredProfile`` is a dumb row of the same
fields ``core.schemas.Profile`` already validates; ``api/main.py`` builds a
real ``Profile`` from it the same way it builds one from a fresh request body.

The engine is created via ``make_sessionmaker`` rather than at import time
against a fixed path, so tests can point it at an isolated in-memory database
instead of ``data/app.db`` — the same "don't let production and test state
share a file" concern ``tests/conftest.py`` already handles for the recipe
library by loading fixtures explicitly rather than importing a module-level
default.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    #: A real bcrypt hash (see ``api/auth.py``) — never the plaintext password,
    #: never a homemade hash.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    profile: Mapped["StoredProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StoredProfile(Base):
    """One user's most recently saved onboarding profile.

    One row per user (``user_id`` unique) — saving again replaces it rather
    than accumulating history, matching the scope statement in
    ``docs/methodology.md``: this increment persists the current profile, not
    a plan history or account changelog. ``clinical_flags`` is stored as a
    comma-joined string of ``ClinicalFlag`` values rather than a second table,
    since the set is always small and fixed by the enum (CLAUDE.md's
    "no magic numbers" concern is about nutritional constants, not this).
    """

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    age_years: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(16), nullable=False)
    activity: Mapped[str] = mapped_column(String(32), nullable=False)
    goal: Mapped[str] = mapped_column(String(32), nullable=False)
    diet: Mapped[str] = mapped_column(String(32), nullable=False)
    clinical_flags: Mapped[str] = mapped_column(Text, nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship(back_populates="profile")

    def flags_list(self) -> list[str]:
        return [f for f in self.clinical_flags.split(",") if f]


def make_sessionmaker(database_url: str) -> tuple[sessionmaker[Session], "object"]:
    """Build an isolated engine + sessionmaker and create its tables.

    ``StaticPool`` for ``sqlite:///:memory:`` specifically: SQLite's default
    pooling opens a fresh connection (and therefore a fresh, empty, in-memory
    database) per checkout, which would make every request in a test see a
    different, empty database. A file-backed URL doesn't have this problem and
    uses the normal pool.
    """

    connect_args = {"check_same_thread": False}
    if database_url == "sqlite:///:memory:":
        engine = create_engine(database_url, connect_args=connect_args, poolclass=StaticPool)
    else:
        engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False), engine


#: The real, process-lifetime database. ``FOODAI_DB_PATH`` lets a deployment
#: relocate it; the default keeps it next to the other ``data/`` fixtures this
#: project already ships, though unlike those it is real, mutable, per-user
#: state, not a checked-in fixture.
_DB_PATH = Path(os.environ.get("FOODAI_DB_PATH", "data/app.db"))
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
SessionLocal, _engine = make_sessionmaker(f"sqlite:///{_DB_PATH}")


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
