from __future__ import annotations

import streamlit as st

from core import api, session


def render() -> None:
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.title("📰 NewsMind")
        st.caption("Newsroom workflow console")

        if flash := session.pop_flash():
            st.warning(flash)

        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary", width="stretch")

        with st.expander("Connection"):
            st.text_input("API URL", key="api_url")

        if submitted:
            if not username or not password:
                st.error("Enter your username and password.")
                return
            payload = api.post("/auth/login", {"username": username, "password": password})
            if payload:
                session.sign_in(payload)
                st.rerun()
