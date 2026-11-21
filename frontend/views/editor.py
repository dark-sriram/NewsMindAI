from __future__ import annotations

import streamlit as st

from core import api, config, ui


def render() -> None:
    ui.header("Editor desk", "Review pitches and content, assign work.")
    queue, pitches, content, tools = st.tabs(["Queue", "Pitches", "Content", "Tools"])
    with queue:
        _queue()
    with pitches:
        _pitches()
    with content:
        _content()
    with tools:
        _tools()


def _queue() -> None:
    res = api.get("/editor/queue")
    if res:
        ui.metrics({"Pitches": res.get("pitch_count"), "Content": res.get("content_count")})
        ui.table(res.get("tasks"), key="e_queue", empty="The queue is empty.")


def _pitches() -> None:
    status = st.selectbox("Status", config.PITCH_STATUSES, key="e_pst")
    row = ui.table(ui.as_rows(api.get("/editor/pitches", status=status), "pitches"),
                   key="e_pitches", selectable=True)
    pid = ui.target_id(row, ("story_pitch_id", "id"), "Pitch ID", "e_pid")
    remarks = st.text_input("Remarks (used when rejecting)", key="e_prem")
    a, b = st.columns(2)
    if a.button("Approve", key="e_pa", disabled=pid is None, type="primary", width="stretch"):
        api.put(f"/editor/pitches/{pid}/approve", success=f"Pitch #{pid} approved.")
    if b.button("Reject", key="e_pr", disabled=pid is None, width="stretch"):
        api.put(f"/editor/pitches/{pid}/reject", {"remarks": remarks},
                success=f"Pitch #{pid} rejected.")


def _content() -> None:
    status = st.selectbox("Status", config.CONTENT_STATUSES, index=1, key="e_cst")
    row = ui.table(ui.as_rows(api.get("/editor/content", status=status), "items"),
                   key="e_content", selectable=True)
    cid = ui.target_id(row, ("content_id", "id"), "Content ID", "e_cid")
    remarks = st.text_input("Remarks (used when rejecting / sending to rework)", key="e_crem")
    a, b, c = st.columns(3)
    if a.button("Approve", key="e_ca", disabled=cid is None, type="primary", width="stretch"):
        api.put(f"/editor/content/{cid}/approve", success=f"Content #{cid} approved.")
    if b.button("Rework", key="e_cw", disabled=cid is None, width="stretch"):
        api.put(f"/editor/content/{cid}/rework", {"remarks": remarks},
                success=f"Content #{cid} sent for rework.")
    if c.button("Reject", key="e_cr", disabled=cid is None, width="stretch"):
        api.put(f"/editor/content/{cid}/reject", {"remarks": remarks},
                success=f"Content #{cid} rejected.")

    with st.expander("Assign to a journalist"):
        c1, c2 = st.columns([1, 2])
        uid = c1.number_input("Assignee user ID", 0, step=1, key="e_uid")
        note = c2.text_input("Note", key="e_note")
        if st.button("Assign", key="e_as", disabled=cid is None or not uid):
            api.put(f"/editor/content/{cid}/assign",
                    {"assignee_user_id": int(uid), "note": note},
                    success=f"Content #{cid} assigned.")


def _tools() -> None:
    st.subheader("Urgency score")
    title = st.text_input("Title", key="e_ut")
    summary = st.text_area("Summary", key="e_us", height=80)
    if st.button("Score urgency"):
        res = api.post("/editor/queue/score", {"title": title, "summary": summary})
        if res:
            ui.metrics({"Urgency": res.get("urgency"), "Confidence": res.get("confidence")})
            ui.bar(res.get("probabilities"), caption="Class probabilities")

    st.divider()
    st.subheader("Suggest a journalist")
    c1, c2 = st.columns([3, 1])
    topic = c1.text_input("Topic", key="e_topic")
    if c2.button("Suggest", width="stretch"):
        res = api.post("/editor/assign/suggest", {"topic": topic})
        if res:
            ui.table(res.get("suggestions"), key="e_sugg")

    st.divider()
    st.subheader("Duplicate pitches")
    if st.button("Scan submitted pitches"):
        res = api.post("/editor/pitches/duplicates", {})
        if res:
            ui.table(res.get("pairs") or res.get("matches"), key="e_dups",
                     empty="No duplicates found.")
