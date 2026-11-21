from __future__ import annotations

import streamlit as st

from core import api, config, ui

_RECENT = "adapt_recent"


def render() -> None:
    ui.header("Content adaptation", "Adapt one story for several platforms and review the drafts.")
    new_tab, review_tab = st.tabs(["New adaptation", "Review drafts"])
    with new_tab:
        _create()
    with review_tab:
        _review()


def _create() -> None:
    with st.form("adapt"):
        title = st.text_input("Title", help="Minimum 5 characters.")
        content = st.text_area("Content", height=200, help="Minimum 20 characters.")
        platforms = st.multiselect("Platforms", config.PLATFORMS, default=config.PLATFORMS[:1])
        if st.form_submit_button("Generate drafts", type="primary"):
            res = api.post("/cae/adaptations", {
                "original_title": title, "original_content": content,
                "target_platforms": platforms})
            if res:
                st.session_state.setdefault(_RECENT, [])
                st.session_state[_RECENT] = [res["id"], *st.session_state[_RECENT]][:10]
                st.session_state["adapt_current"] = res["id"]
                st.success(f"Adaptation **#{res['id']}** created with {len(res['drafts'])} draft(s). "
                           "Open the *Review drafts* tab.")


def _review() -> None:
    recent = st.session_state.get(_RECENT, [])
    c1, c2 = st.columns([2, 1])
    manual = c2.number_input("Open request ID", 0, step=1, key="adapt_manual")
    if recent:
        current = st.session_state.get("adapt_current", recent[0])
        index = recent.index(current) if current in recent else 0
        picked = c1.selectbox("Recent requests (this session)", recent, index=index,
                              format_func=lambda i: f"#{i}")
    else:
        picked = None
        c1.caption("Requests you create appear here. Use the ID box to open an older one.")
    request_id = int(manual) or picked
    if not request_id:
        return

    res = api.get(f"/cae/adaptations/{request_id}")
    if not res:
        return
    st.subheader(f"Request #{res['id']} · {res['status']}")
    with st.expander("Original"):
        st.markdown(f"**{res['original_title']}**")
        st.write(res["original_content"])

    drafts = res.get("drafts") or []
    if not drafts:
        st.caption("No drafts.")
        return
    tabs = st.tabs([f"{d['platform'].replace('_', ' ').title()} · v{d['version_number']}" for d in drafts])
    for tab, draft in zip(tabs, drafts):
        with tab:
            _draft_panel(draft)


def _draft_panel(d: dict) -> None:
    did = d["id"]
    st.caption(f"Status: **{d['status']}** · model: {d['model_version']}")
    st.markdown(f"**{d['adapted_title']}**")
    st.write(d["adapted_content"])
    flags = {k: v for k, v in (d.get("validation_flags") or {}).items() if v}
    if flags:
        st.warning(f"Validation flags: {flags}")

    remarks = st.text_input("Remarks", key=f"rm{did}", help="Required for reject / regenerate.")
    a, b, c, e = st.columns(4)
    if a.button("Approve", key=f"ap{did}", type="primary", width="stretch"):
        api.post(f"/cae/adaptation-drafts/{did}/approve", {"remarks": remarks or None},
                 success="Draft approved.")
    if b.button("Reject", key=f"rj{did}", width="stretch"):
        api.post(f"/cae/adaptation-drafts/{did}/reject", {"remarks": remarks},
                 success="Draft rejected.")
    if c.button("Regenerate", key=f"rg{did}", width="stretch"):
        api.post(f"/cae/adaptation-drafts/{did}/regenerate", {"remarks": remarks},
                 success="New version generated.")
    if e.button("History", key=f"vs{did}", width="stretch"):
        ui.table(api.get(f"/cae/adaptation-drafts/{did}/versions"), key=f"vt{did}")

    with st.expander("Edit & finalize"):
        ft = st.text_input("Final title", d["adapted_title"], key=f"ft{did}")
        fc = st.text_area("Final content", d["adapted_content"], height=160, key=f"fc{did}")
        if st.button("Save final version", key=f"fn{did}"):
            api.put(f"/cae/adaptation-drafts/{did}/final",
                    {"final_title": ft, "final_content": fc, "remarks": remarks or None},
                    success="Final version saved.")
