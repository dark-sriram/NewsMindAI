"""Authentication state kept in st.session_state (no API calls here)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import streamlit as st

_TOKEN = "_token"
_USER = "_user"
_FLASH = "_flash"
_REV = "_rev"


@dataclass(frozen=True)
class User:
    user_id: int
    username: str
    role_code: str
    capabilities: frozenset[str] = field(default_factory=frozenset)

    def can(self, *caps: str) -> bool:
        """True if the user holds at least one of the given capabilities."""
        return any(c in self.capabilities for c in caps)

    @property
    def role_label(self) -> str:
        return self.role_code.replace("_", " ").title()


def sign_in(payload: dict[str, Any]) -> None:
    st.session_state[_TOKEN] = payload["session_token"]
    st.session_state[_USER] = User(
        user_id=int(payload["user_id"]),
        username=str(payload["username"]),
        role_code=str(payload["role_code"]),
        capabilities=frozenset(payload.get("capabilities") or []),
    )


def sign_out(reason: str | None = None) -> None:
    for key in list(st.session_state.keys()):
        if key != "api_url":
            del st.session_state[key]
    if reason:
        st.session_state[_FLASH] = reason


def token() -> str | None:
    return st.session_state.get(_TOKEN)


def user() -> User | None:
    return st.session_state.get(_USER) if token() else None


def pop_flash() -> str | None:
    return st.session_state.pop(_FLASH, None)


def revision() -> int:
    """Bumped after every successful write; used to reset table selections."""
    return int(st.session_state.get(_REV, 0))


def bump_revision() -> None:
    st.session_state[_REV] = revision() + 1
