"""Password hashing and session helpers.

Hashing goes through ``bcrypt`` directly (the maintained C-backed library, not
``passlib`` — whose bcrypt backend has had version-detection breakage against
recent ``bcrypt`` releases — and not a homemade scheme). ``bcrypt.hashpw``
salts internally, so no separate salt column exists on ``User``.

Session identity is a single integer, ``request.session["user_id"]``, read
and written through the two small helpers below rather than scattered
``request.session[...]`` accesses across ``api/main.py`` — so "what does an
authenticated session actually store" has one place to answer from.
"""

from __future__ import annotations

import bcrypt
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from api.db import User

__all__ = ["hash_password", "verify_password", "login_session", "logout_session", "current_user"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def login_session(request: Request, user_id: int) -> None:
    request.session["user_id"] = user_id


def logout_session(request: Request) -> None:
    request.session.pop("user_id", None)


def current_user(request: Request, db: Session) -> User:
    """The signed-in ``User``, or a 401.

    Not a FastAPI ``Depends``-only function because it needs ``db``, which is
    itself a ``Depends`` — every route composes this explicitly
    (``current_user(request, db)``) rather than nesting dependencies, so the
    401 path is one straight line to read, not two levels of indirection.
    """

    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    user = db.get(User, user_id)
    if user is None:
        # The session cookie outlived the account it named (e.g. a dev DB
        # reset). Treat it as signed-out rather than a 500.
        request.session.pop("user_id", None)
        raise HTTPException(status_code=401, detail="Session is no longer valid.")
    return user
