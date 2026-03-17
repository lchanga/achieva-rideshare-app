from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.db import get_engine
from server.models.user import User


def login_user(data: dict) -> dict:
    email = (data.get("email") or "").strip().lower()
    requested_role = data.get("role")
    if not email:
        return {"error": "Email is required.", "code": "invalid_request"}

    with Session(get_engine()) as session:
        user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            return {"error": "Invalid email.", "code": "invalid_credentials"}
        if requested_role and user.role != requested_role:
            return {"error": "Use the correct login page for your role.", "code": "invalid_credentials"}

        return {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
        }
