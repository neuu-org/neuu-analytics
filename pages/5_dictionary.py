"""
Pagina de analise do dataset Bible Dictionary.
20.900 entradas de 5 dicionarios biblicos classicos.
"""

import json
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from loading import show_loading

show_loading()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DICT_FILE = DATA_DIR / "dictionary.parquet"

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E8E0D4",
)

SOURCE_LABELS = {
    "EAS": "Easton's Bible Dictionary (1897)",
    "SMI": "Smith's Bible Dictionary (1863)",
    "HAS": "Hastings Dictionary of the Bible (1880)",
    "HIT": "Hitchcock's Bible Names (1869)",
    "SCH": "Schaff's Dictionary of the Bible (1880)",
}

SOURCE_COLORS = {
    "EAS": "#4CAF50",
    "SMI": "#2196F3",
    "HAS": "#FF9800",
    "HIT": "#9C27B0",
    "SCH": "#F44336",
}

if not DICT_FILE.exists():
    st.info("Dados nao encontrados. Execute `python sync.py dictionary`.")
    st.stop()

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_dict(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{DICT_FILE}'").df()


df = load_dict(DICT_FILE.stat().st_mtime)

title = "Dicionarios Biblicos — Analise" if is_pt else "Bible Dictionaries — Analysis"
st.title(f"📖 {title}")

# ============================================================
# OVERVIEW
# ============================================================
st.header("Visao Geral" if is_pt else "Overview")

total_defs = len(df)
unique_terms = df["term"].nunique()
sources = df["source"].nunique()
avg_words = int(df["word_count"].mean())
total_refs = int(df["refs_count"].sum())

cols = st.columns(5)
cols[0].metric("Definicoes" if is_pt else "Definitions", f"{total_defs:,}")
cols[1].metric("Termos Unicos" if is_pt else "Unique Terms", f"{unique_terms:,}")
cols[2].metric("Fontes" if is_pt else "Sources", sources)
cols[3].metric("Media palavras" if is_pt else "Avg Words", f"{avg_words:,}")
cols[4].metric("Refs Biblicas" if is_pt else "Scripture Refs", f"{total_refs:,}")

# ============================================================
# BY SOURCE
# ============================================================
st.header("Por Fonte" if is_pt else "By Source")

source_stats = df.groupby("source").agg(
    entries=("term", "nunique"),
    definitions=("term", "count"),
    avg_words=("word_count", "mean"),
    total_refs=("refs_count", "sum"),
).reset_index()
source_stats["source_name"] = source_stats["source"].map(SOURCE_LABELS)
source_stats["avg_words"] = source_stats["avg_words"].round(0).astype(int)

fig = px.bar(
    source_stats.sort_values("entries", ascending=True),
    x="entries",
    y="source_name",
    orientation="h",
    color="source",
    color_discrete_map=SOURCE_COLORS,
    title="Entradas por Fonte" if is_pt else "Entries by Source",
    labels={"entries": "Entradas" if is_pt else "Entries", "source_name": ""},
)
fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=300)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    source_stats[["source_name", "entries", "definitions", "avg_words", "total_refs"]].rename(
        columns={
            "source_name": "Fonte" if is_pt else "Source",
            "entries": "Termos" if is_pt else "Terms",
            "definitions": "Definicoes" if is_pt else "Definitions",
            "avg_words": "Media Palavras" if is_pt else "Avg Words",
            "total_refs": "Refs" if is_pt else "Refs",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

# ============================================================
# COVERAGE OVERLAP
# ============================================================
st.header("Cobertura entre Fontes" if is_pt else "Coverage Overlap")

terms_by_source = df.groupby("term")["source"].apply(set).reset_index()
terms_by_source["num_sources"] = terms_by_source["source"].apply(len)

source_dist = terms_by_source["num_sources"].value_counts().sort_index().reset_index()
source_dist.columns = ["num_sources", "count"]

fig2 = px.bar(
    source_dist,
    x="num_sources",
    y="count",
    title="Termos por Numero de Fontes" if is_pt else "Terms by Number of Sources",
    labels={
        "num_sources": "Fontes" if is_pt else "Sources",
        "count": "Termos" if is_pt else "Terms",
    },
    color_discrete_sequence=["#D4A853"],
)
fig2.update_layout(**PLOTLY_LAYOUT, height=300)
st.plotly_chart(fig2, use_container_width=True)

# Show terms with most sources
richest = terms_by_source.sort_values("num_sources", ascending=False).head(20)
st.subheader("Termos com mais fontes" if is_pt else "Terms with Most Sources")
for _, row in richest.iterrows():
    sources_list = ", ".join(sorted(row["source"]))
    st.write(f"**{row['term']}** — {row['num_sources']} fontes ({sources_list})")

# ============================================================
# WORD COUNT ANALYSIS
# ============================================================
st.header("Analise de Tamanho" if is_pt else "Size Analysis")

fig3 = px.box(
    df,
    x="source",
    y="word_count",
    color="source",
    color_discrete_map=SOURCE_COLORS,
    title="Distribuicao de Palavras por Fonte" if is_pt else "Word Count Distribution by Source",
    labels={"word_count": "Palavras" if is_pt else "Words", "source": "Fonte" if is_pt else "Source"},
)
fig3.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=400)
st.plotly_chart(fig3, use_container_width=True)

# Longest definitions
st.subheader("Definicoes mais longas" if is_pt else "Longest Definitions")
longest = df.nlargest(10, "word_count")[["term", "source", "word_count", "refs_count"]]
st.dataframe(
    longest.rename(columns={
        "term": "Termo" if is_pt else "Term",
        "source": "Fonte" if is_pt else "Source",
        "word_count": "Palavras" if is_pt else "Words",
        "refs_count": "Refs",
    }),
    use_container_width=True,
    hide_index=True,
)

# ============================================================
# SEARCH
# ============================================================
st.header("🔍 Buscar Termo" if is_pt else "🔍 Search Term")

search = st.text_input("Termo" if is_pt else "Term", placeholder="AARON, MOSES, JERUSALEM...")

if search:
    search_upper = search.strip().upper()
    results = df[df["term"].str.contains(search_upper, na=False)]

    if results.empty:
        st.warning("Nenhum resultado" if is_pt else "No results")
    else:
        matched_terms = results["term"].unique()
        st.success(f"{len(matched_terms)} termo(s) encontrado(s)" if is_pt else f"{len(matched_terms)} term(s) found")

        for term in matched_terms[:5]:
            term_rows = results[results["term"] == term]
            name = term_rows.iloc[0]["name"]

            with st.expander(f"📖 {name} ({len(term_rows)} definicoes)" if is_pt else f"📖 {name} ({len(term_rows)} definitions)"):
                for _, row in term_rows.iterrows():
                    source_label = SOURCE_LABELS.get(row["source"], row["source"])
                    st.markdown(f"**{source_label}** ({row['word_count']} palavras)")
                    st.write(row["definition"][:500] + ("..." if len(row["definition"]) > 500 else ""))
                    st.divider()
