"""
Pagina de analise do dataset Bible Dictionary.
20.900 entradas de 5 dicionarios biblicos classicos.
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    "EAS": "Easton's (1897)",
    "SMI": "Smith's (1863)",
    "HAS": "Hastings (1880)",
    "HIT": "Hitchcock (1869)",
    "SCH": "Schaff (1880)",
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
st.caption(
    "20.900 entradas de 5 dicionarios biblicos classicos (Easton, Smith, Hastings, Hitchcock, Schaff)"
    if is_pt else
    "20,900 entries from 5 classic Bible dictionaries (Easton, Smith, Hastings, Hitchcock, Schaff)"
)

# ============================================================
# 1. OVERVIEW
# ============================================================
st.header("1. " + ("Visao Geral" if is_pt else "Overview"))

total_defs = len(df)
unique_terms = df["term"].nunique()
sources = df["source"].nunique()
avg_words = int(df["word_count"].mean())
total_refs = int(df["refs_count"].sum())

cols = st.columns(5)
cols[0].metric("Definicoes" if is_pt else "Definitions", f"{total_defs:,}")
cols[1].metric("Termos" if is_pt else "Terms", f"{unique_terms:,}")
cols[2].metric("Fontes" if is_pt else "Sources", sources)
cols[3].metric("Media palavras" if is_pt else "Avg Words", f"{avg_words:,}")
cols[4].metric("Refs Biblicas" if is_pt else "Scripture Refs", f"{total_refs:,}")

# ============================================================
# 2. POR FONTE
# ============================================================
st.header("2. " + ("Por Fonte" if is_pt else "By Source"))

source_stats = df.groupby("source").agg(
    entries=("term", "nunique"),
    definitions=("term", "count"),
    avg_words=("word_count", "mean"),
    total_refs=("refs_count", "sum"),
).reset_index()
source_stats["source_name"] = source_stats["source"].map(SOURCE_LABELS)
source_stats["avg_words"] = source_stats["avg_words"].round(0).astype(int)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        source_stats.sort_values("entries", ascending=True),
        x="entries", y="source_name",
        orientation="h",
        color="source",
        color_discrete_map=SOURCE_COLORS,
        title="Entradas por Fonte" if is_pt else "Entries by Source",
        labels={"entries": "Entradas" if is_pt else "Entries", "source_name": ""},
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.pie(
        source_stats,
        values="definitions", names="source_name",
        title="Distribuicao de Definicoes" if is_pt else "Definition Distribution",
        color="source",
        color_discrete_map={v: SOURCE_COLORS[k] for k, v in SOURCE_LABELS.items()},
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=300)
    st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    source_stats[["source_name", "entries", "definitions", "avg_words", "total_refs"]].rename(
        columns={
            "source_name": "Fonte" if is_pt else "Source",
            "entries": "Termos" if is_pt else "Terms",
            "definitions": "Definicoes" if is_pt else "Definitions",
            "avg_words": "Media Palavras" if is_pt else "Avg Words",
            "total_refs": "Refs",
        }
    ),
    use_container_width=True, hide_index=True,
)

# ============================================================
# 3. COBERTURA ENTRE FONTES
# ============================================================
st.header("3. " + ("Cobertura entre Fontes" if is_pt else "Coverage Overlap"))

terms_by_source = df.groupby("term")["source"].apply(set).reset_index()
terms_by_source["num_sources"] = terms_by_source["source"].apply(len)

col1, col2 = st.columns(2)

with col1:
    source_dist = terms_by_source["num_sources"].value_counts().sort_index().reset_index()
    source_dist.columns = ["num_sources", "count"]
    fig = px.bar(
        source_dist, x="num_sources", y="count",
        title="Termos por Numero de Fontes" if is_pt else "Terms by Number of Sources",
        labels={"num_sources": "Fontes" if is_pt else "Sources", "count": "Termos" if is_pt else "Terms"},
        color="num_sources",
        color_continuous_scale=["#2A2D34", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Top termos com mais fontes — como treemap
    richest = terms_by_source.nlargest(30, "num_sources")
    richest["sources_label"] = richest["source"].apply(lambda s: ", ".join(sorted(s)))
    fig = px.treemap(
        richest, path=["num_sources", "term"],
        values="num_sources",
        title="Termos com Maior Cobertura" if is_pt else "Most Covered Terms",
        color="num_sources",
        color_continuous_scale=["#1A1D24", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 4. ANALISE TEXTUAL
# ============================================================
st.header("4. " + ("Analise Textual" if is_pt else "Text Analysis"))

col1, col2 = st.columns(2)

with col1:
    fig = px.box(
        df, x="source", y="word_count",
        color="source",
        color_discrete_map=SOURCE_COLORS,
        title="Distribuicao de Palavras por Fonte" if is_pt else "Word Count Distribution by Source",
        labels={"word_count": "Palavras" if is_pt else "Words", "source": ""},
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.histogram(
        df, x="word_count", nbins=50,
        title="Distribuicao Geral de Tamanho" if is_pt else "Overall Size Distribution",
        labels={"word_count": "Palavras" if is_pt else "Words"},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Frequencia" if is_pt else "Frequency", height=400)
    st.plotly_chart(fig, use_container_width=True)

# Top definicoes mais longas
st.subheader("Definicoes mais longas" if is_pt else "Longest Definitions")
longest = df.nlargest(10, "word_count")[["name", "source", "word_count", "refs_count"]]
longest["source_name"] = longest["source"].map(SOURCE_LABELS)
st.dataframe(
    longest[["name", "source_name", "word_count", "refs_count"]].rename(columns={
        "name": "Termo" if is_pt else "Term",
        "source_name": "Fonte" if is_pt else "Source",
        "word_count": "Palavras" if is_pt else "Words",
        "refs_count": "Refs",
    }),
    use_container_width=True, hide_index=True,
)

# ============================================================
# 5. DISTRIBUICAO ALFABETICA
# ============================================================
st.header("5. " + ("Distribuicao Alfabetica" if is_pt else "Alphabetical Distribution"))

letter_counts = df.groupby("letter")["term"].nunique().reset_index(name="count").sort_values("letter")

fig = px.bar(
    letter_counts, x="letter", y="count",
    title="Termos por Letra Inicial" if is_pt else "Terms by Initial Letter",
    labels={"letter": "Letra" if is_pt else "Letter", "count": "Termos" if is_pt else "Terms"},
    color="count",
    color_continuous_scale=["#2A2D34", "#D4A853"],
)
fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 6. CROSS-DATASET: Refs Biblicas
# ============================================================
st.header("6. " + ("Referencias Biblicas nos Dicionarios" if is_pt else "Scripture References in Dictionaries"))

refs_by_source = df.groupby("source").agg(
    total_refs=("refs_count", "sum"),
    terms_with_refs=("refs_count", lambda x: (x > 0).sum()),
    avg_refs=("refs_count", "mean"),
).reset_index()
refs_by_source["source_name"] = refs_by_source["source"].map(SOURCE_LABELS)
refs_by_source["avg_refs"] = refs_by_source["avg_refs"].round(1)

fig = px.scatter(
    refs_by_source,
    x="terms_with_refs", y="total_refs",
    size="total_refs", color="source",
    color_discrete_map=SOURCE_COLORS,
    text="source_name",
    title="Refs Biblicas: Volume vs Cobertura" if is_pt else "Scripture Refs: Volume vs Coverage",
    labels={
        "terms_with_refs": "Termos com Refs" if is_pt else "Terms with Refs",
        "total_refs": "Total Refs",
    },
)
fig.update_traces(textposition="top center", textfont_size=10)
fig.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
st.plotly_chart(fig, use_container_width=True)
