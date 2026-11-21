from __future__ import annotations

from datetime import datetime, time

import streamlit as st
import streamlit.components.v1 as components

from core import api, ui

ID_KEYS = ("content_id", "id")


def render() -> None:
    ui.header("Publisher", "Approve, template, schedule and publish.")
    queue_tab, stats_tab = st.tabs(["Publication queue", "Analytics"])
    with queue_tab:
        _queue()
    with stats_tab:
        _analytics()


def _queue() -> None:
    row = ui.table(ui.as_rows(api.get("/publisher/articles"), "articles"),
                   key="p_articles", selectable=True, empty="No articles are ready.")
    cid = ui.target_id(row, ID_KEYS, "Content ID", "p_cid")
    if not cid:
        return
    st.divider()
    st.subheader(f"Article #{cid}")

    step1, step2, step3 = st.tabs(["1 · Approve & template", "2 · Preview", "3 · Publish"])

    with step1:
        if st.button("Approve for publication", key="p_ap"):
            api.put(f"/publisher/articles/{cid}/approve", success="Approved for publication.")
        templates = ui.as_rows(api.get("/publisher/templates"), "templates")
        codes = {f"{t.get('name', t['code'])} ({t['code']})": t["code"] for t in templates}
        if codes:
            label = st.selectbox("Template", list(codes), key="p_tpl")
            if st.button("Assign template", key="p_tpl_b"):
                api.put(f"/publisher/articles/{cid}/template", {"template_code": codes[label]},
                        success="Template assigned.")

    with step2:
        preview = api.get(f"/publisher/articles/{cid}/preview")
        if preview:
            st.caption(f"Template: {preview.get('template', {}).get('name', '—')} · "
                       f"Status: {preview.get('publication_status') or '—'}")
            components.html(preview["preview_html"], height=420, scrolling=True)

    with step3:
        c1, c2, c3 = st.columns([2, 2, 1])
        day = c1.date_input("Date", key="p_day")
        hour = c2.time_input("Time", time(9, 0), key="p_time")
        c3.write("")
        if c3.button("Schedule", key="p_sch", width="stretch"):
            api.post(f"/publisher/articles/{cid}/schedule",
                     {"scheduled_at": datetime.combine(day, hour).isoformat()},
                     success="Publication scheduled.")
        st.divider()
        with st.popover("🚀 Publish now"):
            st.write(f"Publish article **#{cid}** immediately?")
            if st.button("Yes, publish", type="primary", key="p_pub"):
                api.post(f"/publisher/articles/{cid}/publish", success="Published.")


def _analytics() -> None:
    res = api.get("/publisher/analytics")
    if not res:
        return
    ui.metrics({"Approved": res.get("approved"), "Ready": res.get("ready"),
                "Scheduled": res.get("scheduled"), "Published": res.get("published")})
    ui.bar(res.get("publications_by_status"), caption="Publications by status")
