"""HTTP client for the NewsMind FastAPI backend.

* ``request``  – raises ``ApiError`` (pure, testable).
* ``get/post/put`` – UI-friendly wrappers: show errors, return ``None`` on failure.
* GET requests are cached briefly; any successful write clears the cache.
"""

from __future__ import annotations

from typing import Any

import httpx
import streamlit as st

from core import config, session


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


@st.cache_resource(show_spinner=False)
def _http() -> httpx.Client:
    return httpx.Client(timeout=config.REQUEST_TIMEOUT)


def _clean(params: dict[str, Any] | None) -> dict[str, Any]:
    return {k: v for k, v in (params or {}).items() if v is not None}


def _error_detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except ValueError:
        return resp.text or resp.reason_phrase
    if isinstance(data, dict):
        if data.get("errors"):
            return "; ".join(f"{e.get('field')}: {e.get('message')}" for e in data["errors"])
        detail = data.get("detail", data)
        return detail if isinstance(detail, str) else str(detail)
    return str(data)


def _send(base: str, tok: str | None, method: str, path: str, json: Any, params: dict | None):
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    try:
        resp = _http().request(method, base + path, json=json, params=_clean(params), headers=headers)
    except httpx.HTTPError as exc:
        raise ApiError(0, f"Cannot reach API at {base} ({exc.__class__.__name__}).") from exc
    if resp.is_success:
        return resp.json() if resp.content else {}
    raise ApiError(resp.status_code, _error_detail(resp))


def _base() -> str:
    return str(st.session_state.get("api_url") or config.API_URL).rstrip("/")


def request(method: str, path: str, *, json: Any = None, params: dict | None = None):
    return _send(_base(), session.token(), method, path, json, params)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def _cached_get(base: str, tok: str | None, path: str, params: tuple):
    return _send(base, tok, "GET", path, None, dict(params))


# ── UI-friendly wrappers ─────────────────────────────────────────────────────


def _fail(exc: ApiError) -> None:
    if exc.status == 401 and session.token():
        session.sign_out("Your session expired. Please log in again.")
        st.rerun()
    st.error(f"{exc.detail}" + (f"  (HTTP {exc.status})" if exc.status else ""))


def get(path: str, *, _cache: bool = True, **params: Any):
    try:
        if _cache:
            return _cached_get(_base(), session.token(), path, tuple(sorted(_clean(params).items())))
        return request("GET", path, params=params)
    except ApiError as exc:
        _fail(exc)
        return None


def _write(method: str, path: str, json: Any, success: str | None):
    try:
        with st.spinner("Working…"):
            data = request(method, path, json=json)
    except ApiError as exc:
        _fail(exc)
        return None
    st.cache_data.clear()
    session.bump_revision()
    if success:
        st.toast(success, icon="✅")
    return data


def post(path: str, json: Any = None, *, success: str | None = None):
    return _write("POST", path, json, success)


def put(path: str, json: Any = None, *, success: str | None = None):
    return _write("PUT", path, json, success)
