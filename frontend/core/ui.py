"""Small reusable UI building blocks."""

from __future__ import annotations

from typing import Any, Iterable

import pandas as pd
import streamlit as st

from core import session


def header(title: str, caption: str | None = None) -> None:
    st.title(title)
    if caption:
        st.caption(caption)


def as_rows(data: Any, *keys: str) -> list[dict]:
    """Extract a list of records from the many response shapes the API returns."""
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return [r for r in data[key] if isinstance(r, dict)]
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
    return []


def _display_frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, (dict, list))).any():
            df[col] = df[col].map(lambda v: str(v) if isinstance(v, (dict, list)) else v)
    return df


def table(rows: Iterable[dict] | None, *, key: str, selectable: bool = False,
          empty: str = "Nothing to show.") -> dict | None:
    """Render records. With ``selectable`` returns the clicked row (or None)."""
    rows = list(rows or [])
    if not rows:
        st.caption(empty)
        return None
    df = _display_frame(rows)
    if not selectable:
        st.dataframe(df, hide_index=True, key=f"{key}:{session.revision()}")
        return None
    event = st.dataframe(
        df, hide_index=True, on_select="rerun", selection_mode="single-row",
        key=f"{key}:{session.revision()}",
    )
    picked = event.selection.rows
    return rows[picked[0]] if picked else None


def pick_id(row: dict | None, keys: tuple[str, ...]) -> int | None:
    for k in keys:
        if row and row.get(k) is not None:
            return int(row[k])
    return None


def target_id(row: dict | None, keys: tuple[str, ...], label: str, key: str) -> int | None:
    """ID of the selected row, or a manual ID box. Returns None when nothing is chosen."""
    chosen = pick_id(row, keys)
    if chosen is not None:
        st.caption(f"Selected **#{chosen}**")
        return chosen
    manual = int(st.number_input(f"{label} (or select a row above)", min_value=0, step=1,
                                 value=0, key=key))
    return manual or None


def metrics(items: dict[str, Any]) -> None:
    cols = st.columns(max(len(items), 1))
    for col, (label, value) in zip(cols, items.items()):
        col.metric(label, "—" if value is None else value)


def bar(data: dict[str, Any] | None, *, caption: str | None = None) -> None:
    """Bar chart from a {label: number} dict; silently skips non-numeric values."""
    numeric = {str(k): v for k, v in (data or {}).items() if isinstance(v, (int, float))}
    if not numeric:
        return
    if caption:
        st.caption(caption)
    st.bar_chart(pd.Series(numeric), height=200)


def raw(data: Any, label: str = "Raw response") -> None:
    if data is not None:
        with st.expander(label):
            st.json(data, expanded=2)
