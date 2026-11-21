"""NewsMind — Streamlit frontend entrypoint.

Run from the project root:   streamlit run frontend/app.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="NewsMind", page_icon="📰", layout="wide")

from core import api, config, session  # noqa: E402
from views import (  # noqa: E402
    account, adaptation, admin, audience, editor, journalist, login, manager, publisher,
)

st.session_state.setdefault("api_url", config.API_URL)


def _page(module, title: str, icon: str, path: str) -> st.Page:
    return st.Page(module.render, title=title, icon=icon, url_path=path)


def _build_menu(user: session.User) -> dict[str, list[st.Page]]:
    c = config
    menu: dict[str, list[tuple[bool, st.Page]]] = {
        "Desks": [
            (user.can(c.CAP_JOURNALIST), _page(journalist, "Journalist", "✍️", "journalist")),
            (user.can(c.CAP_ANALYTICS), _page(audience, "Audience insight", "📊", "audience")),
            (user.can(c.CAP_PITCH_REVIEW, c.CAP_CONTENT_REVIEW), _page(editor, "Editor", "🧐", "editor")),
            (user.can(c.CAP_ADAPT), _page(adaptation, "Adaptation", "🔁", "adaptation")),
            (user.can(c.CAP_PUBLISH), _page(publisher, "Publisher", "🚀", "publisher")),
        ],
        "Oversight": [
            (user.can(c.CAP_ANALYTICS) and user.can(c.CAP_PUBLISH, c.CAP_PITCH_REVIEW),
             _page(manager, "Manager", "🧭", "manager")),
            (user.can(c.CAP_ADMIN, c.CAP_MANAGE_USERS, c.CAP_PIPELINE),
             _page(admin, "Admin", "⚙️", "admin")),
        ],
        "Account": [(True, _page(account, "Account", "👤", "account"))],
    }
    visible = {s: [p for ok, p in pages if ok] for s, pages in menu.items()}
    return {s: p for s, p in visible.items() if p}


def main() -> None:
    user = session.user()
    if user is None:
        st.navigation([st.Page(login.render, title="Login", url_path="login")],
                      position="hidden").run()
        return

    pg = st.navigation(_build_menu(user))
    with st.sidebar:
        st.divider()
        st.markdown(f"**{user.username}**  \n{user.role_label}")
        if st.button("Log out", width="stretch"):
            try:
                api.request("POST", "/auth/logout")
            except api.ApiError:
                pass
            session.sign_out()
            st.rerun()
    pg.run()


main()
