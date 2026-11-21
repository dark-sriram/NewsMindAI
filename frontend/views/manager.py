from __future__ import annotations

import streamlit as st

from core import api, ui


def render() -> None:
    ui.header("Newsroom manager", "Pipeline health, workload and risk.")
    tabs = st.tabs(["Overview", "Bottlenecks", "Workload", "Deadline risk", "Resources", "Analytics"])
    for tab, fn in zip(tabs, (_overview, _bottlenecks, _workload, _deadline, _resources, _analytics)):
        with tab:
            fn()


def _overview() -> None:
    res = api.get("/manager/overview")
    if not res:
        return
    ui.metrics({"Submitted pitches": res.get("submitted_pitches"),
                "Submitted content": res.get("submitted_content"),
                "Approved content": res.get("approved_content")})
    ui.bar(res.get("publication"), caption="Publication pipeline")


def _bottlenecks() -> None:
    res = api.get("/manager/bottlenecks")
    if not res:
        return
    st.caption("Hotspots")
    ui.table(res.get("hotspots"), key="m_hot", empty="No hotspots detected.")
    for key in ("content_stages", "pitch_stages", "publication_stages", "adaptation_stages"):
        with st.expander(key.replace("_", " ").title()):
            ui.table(res.get(key), key=f"m_{key}")


def _workload() -> None:
    res = api.get("/manager/workload")
    if res:
        ui.metrics({"Open items": res.get("total_open_items")})
        ui.table(res.get("journalists"), key="m_work")


def _deadline() -> None:
    c1, c2 = st.columns(2)
    submitted = c1.number_input("Submitted stuck after (hours)", 1.0, 720.0, 48.0)
    rework = c2.number_input("Rework stuck after (hours)", 1.0, 720.0, 24.0)
    res = api.get("/manager/deadline-risk", submitted_hours=submitted, rework_hours=rework)
    if res:
        ui.metrics({"At risk": res.get("at_risk_count")})
        st.caption("Content")
        ui.table(res.get("content_at_risk"), key="m_dl_c", empty="None at risk.")
        st.caption("Pitches")
        ui.table(res.get("pitches_at_risk"), key="m_dl_p", empty="None at risk.")


def _resources() -> None:
    res = api.get("/manager/resources")
    if not res:
        return
    ui.table(res.get("desks"), key="m_res")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Overloaded")
        ui.table(res.get("overloaded"), key="m_over", empty="None.")
    with c2:
        st.caption("Underutilized")
        ui.table(res.get("underutilized"), key="m_under", empty="None.")


def _analytics() -> None:
    res = api.get("/manager/analytics")
    if not res:
        return
    ui.metrics({k.replace("_", " ").title(): v for k, v in (res.get("totals") or {}).items()
                if isinstance(v, (int, float))})
    ui.bar(res.get("pipeline"), caption="Pipeline")
    ui.raw(res, "Full analytics payload")
