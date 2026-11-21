"""Static configuration + enums mirrored from the backend (config/constants.py)."""

from __future__ import annotations

import os

API_URL = os.environ.get("NEWSMIND_API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.environ.get("NEWSMIND_TIMEOUT", "120"))
CACHE_TTL_SECONDS = int(os.environ.get("NEWSMIND_CACHE_TTL", "15"))

CONTENT_STATUSES = ["draft", "submitted", "approved", "rejected", "published", "rework"]
PITCH_STATUSES = ["submitted", "approved", "rejected", "hold", "closed"]
SEVERITIES = ["low", "medium", "high", "critical"]
ARTICLE_TYPES = ["feature", "analysis", "opinion", "profile", "explainer"]
PLATFORMS = ["SOCIAL_MEDIA", "PRINT_NEWSPAPER", "WEBSITE", "EMAIL_NEWSLETTER"]
ROLES = [
    "journalist",
    "editor",
    "publisher",
    "newsroom_manager",
    "audience_insight_analyst",
    "content_adaptation_editor",
    "administrator",
]

# Capability keys (same strings as backend ROLE_CAPABILITIES)
CAP_JOURNALIST = "journalist_tools"
CAP_ANALYTICS = "analytics"
CAP_PITCH_REVIEW = "pitch_review"
CAP_CONTENT_REVIEW = "content_review"
CAP_ASSIGN = "assign"
CAP_ADAPT = "adapt"
CAP_PUBLISH = "publish"
CAP_PIPELINE = "pipeline"
CAP_ADMIN = "admin"
CAP_MANAGE_USERS = "manage_users"
