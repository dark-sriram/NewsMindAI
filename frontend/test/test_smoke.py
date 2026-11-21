"""Render every view against a fake backend (no server / DB needed).

Run from the frontend folder:  pytest tests -q
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]

CAPS = {
    "journalist": ["journalist_tools", "pipeline", "ingest", "clean", "persist"],
    "editor": ["pitch_review", "content_review", "assign", "analytics"],
    "publisher": ["publish"],
    "manager": ["pitch_review", "content_review", "assign", "adapt", "publish",
                "analytics", "manage_users"],
    "admin": ["admin", "pipeline", "manage_users", "pitch_review", "content_review",
              "assign", "adapt", "publish", "analytics", "journalist_tools"],
}
CONTENT = [{"id": 1, "title": "Flood hits city", "status": "submitted"}]
DRAFT = {"id": 7, "platform": "WEBSITE", "version_number": 1, "adapted_title": "T",
         "adapted_content": "C", "model_version": "m", "status": "pending",
         "generation_parameters": {}, "validation_flags": {}}

GET_ROUTES = {
    "/journalist/content/1/evidence": [{"id": 1, "title": "Doc"}],
    "/journalist/content/1": {"actor": "a", "content": {"title": "Flood", "status": "draft", "body": "x"}},
    "/journalist/content": {"actor": "a", "items": CONTENT},
    "/aia/story-pitches/top": {"pitches": []},
    "/aia/story-pitches": {"pitches": [{"id": 1, "title": "P"}]},
    "/aia/performance": {"publication_by_status": {"published": 2}, "content_by_status": {"draft": 3},
                         "pitch_outcomes": [], "pitches_by_source": {}, "recent_published": [],
                         "insights": ["All good"]},
    "/editor/queue": {"tasks": [{"id": 1}], "pitch_count": 1, "content_count": 1},
    "/editor/pitches": {"pitches": [{"story_pitch_id": 3, "title": "P"}]},
    "/editor/content": {"items": CONTENT},
    "/cae/adaptations/5": {"id": 5, "original_title": "O", "original_content": "OC",
                           "status": "open", "drafts": [DRAFT]},
    "/publisher/articles": {"articles": [{"content_id": 1, "title": "A"}]},
    "/publisher/templates": {"templates": [{"code": "web_standard", "name": "Web"}]},
    "/publisher/articles/1/preview": {"content_id": 1, "template": {"name": "Web"},
                                      "preview_html": "<p>hi</p>", "publication_status": "ready"},
    "/publisher/analytics": {"approved_content": 1, "publications_by_status": {"ready": 1},
                             "published": 0, "scheduled": 0, "ready": 1, "approved": 1},
    "/manager/overview": {"submitted_pitches": 1, "submitted_content": 2, "approved_content": 3,
                          "publication": {"ready": 1}},
    "/manager/bottlenecks": {"content_stages": [{"stage": "submitted"}], "pitch_stages": [],
                             "publication_stages": [], "adaptation_stages": [], "hotspots": []},
    "/manager/workload": {"journalists": [{"name": "J", "open": 2}], "total_open_items": 2},
    "/manager/deadline-risk": {"thresholds_hours": {}, "content_at_risk": [], "pitches_at_risk": [],
                               "at_risk_count": 0},
    "/manager/resources": {"desks": [{"desk": "x"}], "utilization": {}, "overloaded": [],
                           "underutilized": []},
    "/manager/analytics": {"pipeline": {"a": 1}, "ops": {}, "bottleneck_hotspots": [],
                           "totals": {"content": 5}},
}


def fake_request(self, method, url, json=None, params=None, headers=None, **_):
    path = url.split("://", 1)[1].split("/", 1)[1]
    path = "/" + path
    req = httpx.Request(method, url)
    if path == "/auth/login":
        user = json["username"]
        if json["password"] != "pw" or user not in CAPS:
            return httpx.Response(401, json={"detail": "Invalid credentials"}, request=req)
        return httpx.Response(200, request=req, json={
            "session_token": "t", "user_id": 1, "username": user, "role_code": user,
            "capabilities": CAPS[user]})
    if method == "GET" and path in GET_ROUTES:
        return httpx.Response(200, json=GET_ROUTES[path], request=req)
    if method != "GET":
        return httpx.Response(200, json={"message": "ok", "result": {}}, request=req)
    return httpx.Response(404, json={"detail": f"no route {path}"}, request=req)


@pytest.fixture(autouse=True)
def _backend():
    with patch.object(httpx.Client, "request", fake_request):
        yield


def _view_script(module: str, role: str = "admin") -> str:
    return f"""
import sys
sys.path.insert(0, {str(ROOT)!r})
import streamlit as st
from core import session
st.session_state["api_url"] = "http://fake"
session.sign_in({{"session_token": "t", "user_id": 1, "username": "{role}",
                 "role_code": "{role}", "capabilities": {CAPS[role]!r}}})
from views import {module}
{module}.render()
"""


@pytest.mark.parametrize("module", [
    "journalist", "audience", "editor", "publisher", "manager", "admin", "account",
])
def test_view_renders(module):
    at = AppTest.from_string(_view_script(module), default_timeout=30).run()
    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]


def test_adaptation_review_renders_drafts():
    at = AppTest.from_string(_view_script("adaptation"), default_timeout=30).run()
    assert not at.exception
    at.number_input(key="adapt_manual").set_value(5).run()
    assert not at.exception, at.exception
    assert any("Request #5" in s.value for s in at.subheader)


@pytest.mark.parametrize("role,landing", [
    ("journalist", "Journalist desk"),
    ("publisher", "Publisher"),
    ("manager", "Audience insight"),
])
def test_login_lands_on_first_allowed_page(role, landing):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    at.text_input[0].set_value(role)
    at.text_input[1].set_value("pw")
    at.button[0].click().run()
    assert not at.exception, at.exception
    assert at.title[0].value == landing
    assert any(b.label == "Log out" for b in at.sidebar.button)


def test_bad_login_shows_error():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    at.text_input[0].set_value("nobody")
    at.text_input[1].set_value("bad")
    at.button[0].click().run()
    assert any("Invalid credentials" in e.value for e in at.error)
