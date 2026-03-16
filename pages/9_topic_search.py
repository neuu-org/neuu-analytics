"""
Topic Search — Explorer tool for browsing biblical topics.
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from loading import show_loading

show_loading()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TOPICS_FILE = DATA_DIR / "topics.parquet"

if not TOPICS_FILE.exists():
    st.info("Dados nao encontrados. Execute `python sync.py topics`.")
    st.stop()

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_topics(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{TOPICS_FILE}'").df()


df = load_topics(TOPICS_FILE.stat().st_mtime)

title = "Buscar Topicos" if is_pt else "Topic Search"
st.title(f"🔎 {title}")
st.caption(
    f"{len(df):,} topicos de Nave's Topical Bible + Torrey's Topical Textbook"
    if is_pt else
    f"{len(df):,} topics from Nave's Topical Bible + Torrey's Topical Textbook"
)

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    query = st.text_input(
        "Buscar topico..." if is_pt else "Search topic...",
        placeholder="FAITH, GRACE, LOVE, ABRAHAM...",
    )

with col2:
    source_filter = st.selectbox(
        "Fonte" if is_pt else "Source",
        ["All", "Nave only", "Torrey only", "Both"],
    )

with col3:
    min_refs = st.number_input("Min refs", min_value=0, value=0, step=5)

# Apply filters
mask = pd.Series([True] * len(df))

if query:
    mask &= df["topic"].str.contains(query.upper(), na=False)

if source_filter == "Nave only":
    mask &= df["source_nav"] & ~df["source_tor"]
elif source_filter == "Torrey only":
    mask &= df["source_tor"] & ~df["source_nav"]
elif source_filter == "Both":
    mask &= df["source_nav"] & df["source_tor"]

if min_refs > 0:
    mask &= df["n_biblical_refs"] >= min_refs

results = df[mask].sort_values("n_biblical_refs", ascending=False)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
st.markdown(f"**{len(results):,}** {'resultados' if is_pt else 'results'}")

if not results.empty:
    # Show table
    display_cols = {
        "topic": "Topico" if is_pt else "Topic",
        "n_sources": "Fontes" if is_pt else "Sources",
        "n_biblical_refs": "Refs",
        "has_def_refs": "Def Refs",
        "n_see_also": "See Also",
    }

    st.dataframe(
        results[list(display_cols.keys())].head(50).rename(columns=display_cols),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    # Detail expander for top result
    if query and len(results) > 0:
        top = results.iloc[0]
        with st.expander(f"📖 {top['topic']}", expanded=True):
            cols = st.columns(4)
            cols[0].metric("Refs", top["n_biblical_refs"])
            cols[1].metric("Fontes" if is_pt else "Sources", top["n_sources"])
            cols[2].metric("Def Refs", top["n_def_refs"])
            cols[3].metric("See Also", top["n_see_also"])

            src_labels = []
            if top["source_nav"]:
                src_labels.append("Nave (1896)")
            if top["source_tor"]:
                src_labels.append("Torrey (1897)")
            st.markdown(f"**{'Fontes' if is_pt else 'Sources'}:** {', '.join(src_labels)}")
