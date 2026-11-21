from __future__ import annotations

import streamlit as st

from core import api, ui


def render() -> None:
    ui.header("Audience insight", "Engagement, interest, trends and story pitches.")
    scores, pitch, pitches, perf = st.tabs(["Scores", "Generate pitch", "Pitches", "Performance"])
    with scores:
        _scores()
    with pitch:
        _generate_pitch()
    with pitches:
        _pitch_list()
    with perf:
        _performance()


def _scores() -> None:
    c = st.columns(4)
    metrics = {
        "views": c[0].number_input("Views", 0.0, value=120.0),
        "likes": c[1].number_input("Likes", 0.0, value=25.0),
        "shares": c[2].number_input("Shares", 0.0, value=8.0),
        "comments": c[3].number_input("Comments", 0.0, value=4.0),
    }
    a, b = st.columns(2)
    if a.button("Analyze engagement", width="stretch"):
        res = api.post("/aia/analyze-engagement", metrics)
        if res:
            ui.metrics({"Engagement score": res.get("engagement_score"), "Source": res.get("source")})
    if b.button("Analyze interest", width="stretch"):
        res = api.post("/aia/analyze-interest", metrics)
        if res:
            ui.metrics({"Interest score": res.get("audience_interest_score"),
                        "Segment": res.get("segment")})

    st.divider()
    title = st.text_input("Title", key="a_t")
    summary = st.text_area("Summary", key="a_s", height=80)
    if st.button("Analyze trend"):
        res = api.post("/aia/analyze-trends", {"title": title, "summary": summary})
        if res:
            ui.metrics({"Trend score": res.get("trend_score"), "Category": res.get("category"),
                        "Confidence": res.get("category_confidence")})


def _generate_pitch() -> None:
    with st.form("pitch"):
        title = st.text_input("Title")
        summary = st.text_area("Summary", height=100)
        category = st.text_input("Category", "City")
        c = st.columns(3)
        trend = c[0].number_input("Trend score", 0.0, 100.0, 0.0)
        interest = c[1].number_input("Interest score", 0.0, 100.0, 0.0)
        gap = c[2].number_input("Coverage gap", 0.0, 100.0, 0.0)
        if st.form_submit_button("Generate pitch", type="primary"):
            res = api.post("/aia/generate-story-pitch", {
                "title": title, "summary": summary, "category": category,
                "trend_score": trend, "audience_interest_score": interest,
                "coverage_gap_score": gap})
            if res:
                st.success(f"Pitch **#{res['story_pitch_id']}** created.")
                ui.metrics({"Importance": res.get("pitch_importance"),
                            "Source": res.get("importance_source")})


def _pitch_list() -> None:
    which = st.radio("Show", ["All", "Top"], horizontal=True)
    res = api.get("/aia/story-pitches/top" if which == "Top" else "/aia/story-pitches")
    ui.table(ui.as_rows(res, "pitches"), key="a_pitches")


def _performance() -> None:
    res = api.get("/aia/performance")
    if not res:
        return
    for line in res.get("insights") or []:
        st.write("•", line)
    c1, c2 = st.columns(2)
    with c1:
        ui.bar(res.get("content_by_status"), caption="Content by status")
    with c2:
        ui.bar(res.get("publication_by_status"), caption="Publications by status")
    st.caption("Recently published")
    ui.table(res.get("recent_published"), key="a_recent")
    st.caption("Pitch outcomes")
    ui.table(res.get("pitch_outcomes"), key="a_outcomes")
