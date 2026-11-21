from __future__ import annotations

import streamlit as st

from core import api, config, session, ui


def render() -> None:
    user = session.user()
    ui.header("Admin")
    sections = [
        ("Pipeline", user.can(config.CAP_PIPELINE), _pipeline),
        ("Users", user.can(config.CAP_MANAGE_USERS), _users),
        ("Categories", user.can(config.CAP_ANALYTICS), _categories),
    ]
    allowed = [(name, fn) for name, ok, fn in sections if ok]
    if not allowed:
        st.info("Your role has no admin tools.")
        return
    for tab, (_, fn) in zip(st.tabs([n for n, _ in allowed]), allowed):
        with tab:
            fn()


def _report(res: dict | None) -> None:
    if res:
        st.success(res.get("message") or "Done.")
        ui.raw(res.get("result"), "Details")


def _pipeline() -> None:
    st.caption("Ingest CSVs from data/raw → clean → persist to the content desk.")
    only_new = st.checkbox("Only new files", help="Skip files already ingested.")
    c = st.columns(4)
    if c[0].button("Ingest", width="stretch"):
        _report(api.post("/admin/ingest", {"only_new": only_new}))
    if c[1].button("Clean", width="stretch"):
        _report(api.post("/admin/clean", {}))
    if c[2].button("Persist", width="stretch"):
        _report(api.post("/admin/persist", {}))
    if c[3].button("Run full pipeline", type="primary", width="stretch"):
        _report(api.post("/admin/pipeline", {"only_new": only_new}))

    with st.expander("Inspect data"):
        if st.button("List CSV files"):
            _report(api.get("/admin/csv-files", _cache=False))
        limit = st.number_input("Raw rows", 1, 500, 20)
        if st.button("Show raw ingest rows"):
            res = api.get("/admin/raw-ingest", limit=limit, _cache=False)
            if res:
                ui.metrics(res.get("counts") or {})
                ui.table(res.get("items"), key="ad_raw")


def _users() -> None:
    st.subheader("Create user")
    with st.form("add_user", clear_on_submit=True):
        c1, c2 = st.columns(2)
        username = c1.text_input("Username")
        password = c2.text_input("Password", type="password",
                                 help="Min 10 chars with upper, lower, digit, special.")
        first = c1.text_input("First name")
        last = c2.text_input("Last name")
        email = c1.text_input("Email")
        role = c2.selectbox("Role", config.ROLES)
        if st.form_submit_button("Create user", type="primary"):
            _report(api.post("/admin/users", {
                "username": username, "password": password, "first_name": first,
                "last_name": last, "email": email, "role_code": role}))

    st.subheader("Reset password")
    with st.form("reset", clear_on_submit=True):
        c1, c2 = st.columns(2)
        who = c1.text_input("Username")
        pw = c2.text_input("New password", type="password")
        if st.form_submit_button("Reset"):
            _report(api.post("/admin/users/reset-password", {"username": who, "new_password": pw}))

    st.subheader("Look up user")
    name = st.text_input("Username", key="ad_find")
    if name and st.button("Find"):
        res = api.get(f"/admin/users/{name}", _cache=False)
        if res:
            st.json(res.get("result"))


def _categories() -> None:
    with st.form("cat", clear_on_submit=True):
        name = st.text_input("Category name")
        desc = st.text_input("Description")
        if st.form_submit_button("Add category", type="primary"):
            _report(api.post("/admin/categories", {"name": name, "description": desc}))
