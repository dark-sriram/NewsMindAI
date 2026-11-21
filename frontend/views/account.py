from __future__ import annotations

import streamlit as st

from core import api, session, ui


def render() -> None:
    user = session.user()
    ui.header("Account")
    st.markdown(f"**{user.username}** · {user.role_label}")
    with st.expander("Permissions"):
        st.write(", ".join(sorted(user.capabilities)) or "None")

    st.subheader("Change password")
    with st.form("pw", clear_on_submit=True):
        current = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password",
                            help="Min 10 characters with upper, lower, digit and special character.")
        confirm = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Update password", type="primary"):
            if new != confirm:
                st.error("New passwords do not match.")
            else:
                api.post("/auth/change-password",
                         {"current_password": current, "new_password": new},
                         success="Password changed.")
