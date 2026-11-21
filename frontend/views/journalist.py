from __future__ import annotations

import pandas as pd
import streamlit as st

from core import api, config, ui

ID_KEYS = ("content_id", "id")
EVIDENCE_TEMPLATE = pd.DataFrame(
    {"title": [""], "evidence_type": ["document"], "source_url": [""], "text": [""]}
)


def render() -> None:
    ui.header("Journalist desk", "Write stories, attach evidence, and run AI checks.")
    content_tab, new_tab, tools_tab = st.tabs(["My content", "New story", "AI tools"])
    with content_tab:
        _content_tab()
    with new_tab:
        _new_story_tab()
    with tools_tab:
        _tools_tab()


# ── My content ───────────────────────────────────────────────────────────────

def _content_tab() -> None:
    c1, c2 = st.columns([2, 1])
    status = c1.selectbox("Status", ["all", *config.CONTENT_STATUSES])
    limit = c2.number_input("Limit", 1, 500, 20)
    data = api.get("/journalist/content", limit=limit,
                   status=None if status == "all" else status)
    row = ui.table(ui.as_rows(data, "items"), key="j_content", selectable=True)
    cid = ui.target_id(row, ID_KEYS, "Content ID", "j_cid")
    if cid:
        _detail(cid)


def _detail(cid: int) -> None:
    st.divider()
    detail = api.get(f"/journalist/content/{cid}")
    content = (detail or {}).get("content") or {}
    st.subheader(content.get("title") or f"Content #{cid}")
    if content.get("status"):
        st.caption(f"Status: **{content['status']}**")
    body = content.get("body") or content.get("text")
    if body:
        with st.expander("Body", expanded=False):
            st.write(body)

    ev_tab, status_tab, cred_tab = st.tabs(["Evidence", "Status", "Credibility"])
    with ev_tab:
        ui.table(ui.as_rows(api.get(f"/journalist/content/{cid}/evidence"), "evidence", "items"),
                 key=f"j_ev_{cid}", empty="No evidence attached yet.")
        with st.expander("Add evidence"):
            with st.form(f"ev_{cid}", clear_on_submit=True):
                title = st.text_input("Title")
                c1, c2 = st.columns(2)
                etype = c1.text_input("Type", "document")
                url = c2.text_input("Source URL")
                text = st.text_area("Text", height=100)
                if st.form_submit_button("Attach"):
                    api.post("/journalist/evidence",
                             {"content_id": cid, "title": title, "evidence_type": etype,
                              "source_url": url, "text": text},
                             success="Evidence added.")
    with status_tab:
        current = content.get("status")
        options = config.CONTENT_STATUSES
        new_status = st.selectbox("Set status", options,
                                  index=options.index(current) if current in options else 0,
                                  key=f"j_st_{cid}")
        if st.button("Update status", key=f"j_stb_{cid}"):
            api.put(f"/journalist/content/{cid}/status", {"status": new_status},
                    success=f"Status set to {new_status}.")
    with cred_tab:
        if st.button("Assess credibility", key=f"j_cr_{cid}"):
            _credibility(cid)


def _credibility(cid: int) -> None:
    res = api.post("/journalist/credibility", {"content_id": cid})
    if res:
        ui.metrics({"Evidence items": res.get("evidence_count")})
        st.write(res.get("summary") or "")
        ui.table(res.get("claims"), key=f"j_claims_{cid}")


# ── New story ────────────────────────────────────────────────────────────────

def _new_story_tab() -> None:
    kind = st.radio("Type", ["News", "Article"], horizontal=True)
    with st.form("new_story"):
        title = st.text_input("Title")
        body = st.text_area("Body", height=200, help="Minimum 40 characters.")
        summary = st.text_area("Summary", height=70)

        extra: dict = {}
        if kind == "News":
            c1, c2, c3 = st.columns(3)
            extra["event_type"] = c1.text_input("Event type", "city")
            extra["event_location"] = c2.text_input("Location")
            extra["severity"] = c3.selectbox("Severity", config.SEVERITIES)
            extra["breaking"] = st.checkbox("Breaking news")
        else:
            c1, c2 = st.columns(2)
            extra["article_type"] = c1.selectbox("Article type", config.ARTICLE_TYPES)
            extra["read_time"] = c2.number_input("Read time (min)", 1, 120, 3)

        st.markdown("**Evidence** — at least one row with a title")
        evidence = st.data_editor(EVIDENCE_TEMPLATE, num_rows="dynamic", hide_index=True,
                                  key="j_new_evidence")
        status = st.radio("Save as", ["draft", "submitted"], horizontal=True)

        if st.form_submit_button("Create", type="primary"):
            items = [e for e in evidence.fillna("").to_dict("records") if e["title"].strip()]
            if not items:
                st.error("Add at least one evidence row with a title.")
                return
            payload = {"title": title, "body": body, "summary": summary,
                       "status": status, "evidence": items, **extra}
            res = api.post("/journalist/news" if kind == "News" else "/journalist/articles",
                           payload)
            if res:
                st.success(f"Created content **#{res['content_id']}**.")


# ── AI tools ─────────────────────────────────────────────────────────────────

def _tools_tab() -> None:
    val, rel, cred, dup = st.tabs(["Validate", "Related", "Credibility", "Duplicates"])

    with val:
        title = st.text_input("Title", key="v_t")
        text = st.text_area("Text", key="v_x", height=140)
        if st.button("Validate", key="v_b"):
            res = api.post("/journalist/validate", {"title": title, "text": text})
            if res:
                (st.success if res.get("ok") else st.error)("Valid" if res.get("ok") else "Issues found")
                for err in res.get("errors") or []:
                    st.write("•", err)
                ui.metrics({"Relevancy": res.get("relevancy"), "Score": res.get("relevancy_score")})
                ui.table(res.get("relevancy_matches"), key="v_m")

    with rel:
        title = st.text_input("Title", key="r_t")
        text = st.text_area("Text", key="r_x", height=140)
        if st.button("Find related", key="r_b"):
            res = api.post("/journalist/related-content", {"title": title, "text": text})
            if res:
                ui.metrics({"Relevancy": res.get("relevancy"),
                            "Best score": round(res.get("best_score", 0), 3),
                            "Corpus size": res.get("corpus_size")})
                ui.table(res.get("matches"), key="r_m")

    with cred:
        cid = st.number_input("Content ID", 0, step=1, key="c_id")
        if st.button("Assess", key="c_b", disabled=not cid):
            _credibility(int(cid))

    with dup:
        docs = st.data_editor(pd.DataFrame({"id": [1, 2], "title": ["", ""], "text": ["", ""]}),
                              num_rows="dynamic", hide_index=True, key="d_docs")
        c1, c2 = st.columns(2)
        threshold = c1.slider("Threshold", 0.0, 1.0, 0.5, 0.05)
        limit = c2.number_input("Max pairs", 1, 100, 20)
        if st.button("Find duplicates", key="d_b"):
            items = [{"id": int(r["id"]), "title": str(r["title"]), "text": str(r["text"])}
                     for r in docs.dropna(subset=["id"]).to_dict("records") if str(r["text"]).strip()]
            res = api.post("/journalist/duplicates",
                           {"documents": items, "threshold": threshold, "limit": int(limit)})
            if res:
                ui.table(res.get("pairs"), key="d_p", empty="No duplicate pairs found.")
