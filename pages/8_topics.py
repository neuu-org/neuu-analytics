"""
Pagina de analise do dataset Bible Topics.
7,873 topicos biblicos unificados de Nave + Torrey.
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from loading import show_loading

show_loading()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TOPICS_FILE = DATA_DIR / "topics.parquet"

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E8E0D4",
)

if not TOPICS_FILE.exists():
    st.info("Dados nao encontrados. Execute `python sync.py topics`.")
    st.stop()

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_topics(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{TOPICS_FILE}'").df()


df = load_topics(TOPICS_FILE.stat().st_mtime)

title = "Topicos Biblicos — Analise" if is_pt else "Bible Topics — Analysis"
st.title(f"📚 {title}")
st.caption(
    "7,873 topicos unificados de Nave's Topical Bible (1896) + Torrey's Topical Textbook (1897)"
    if is_pt else
    "7,873 unified topics from Nave's Topical Bible (1896) + Torrey's Topical Textbook (1897)"
)

# ============================================================
# 1. OVERVIEW
# ============================================================
st.header("1. " + ("Visao Geral" if is_pt else "Overview"))

total = len(df)
from_nave = int(df["source_nav"].sum())
from_torrey = int(df["source_tor"].sum())
with_def_refs = int(df["has_def_refs"].sum())
total_refs = int(df["n_biblical_refs"].sum())
total_def_refs = int(df["n_def_refs"].sum())

cols = st.columns(5)
cols[0].metric("Topicos" if is_pt else "Topics", f"{total:,}")
cols[1].metric("Nave", f"{from_nave:,}")
cols[2].metric("Torrey", f"{from_torrey:,}")
cols[3].metric("Refs Biblicas" if is_pt else "Biblical Refs", f"{total_refs:,}")
cols[4].metric("Definition Refs", f"{total_def_refs:,}")

# ============================================================
# 2. FONTES
# ============================================================
st.header("2. " + ("Fontes" if is_pt else "Sources"))

col1, col2 = st.columns(2)

with col1:
    source_data = pd.DataFrame({
        "source": ["Nave (NAV)", "Torrey (TOR)"],
        "count": [from_nave, from_torrey],
    })
    fig = px.pie(
        source_data, values="count", names="source",
        title="Topicos por Fonte" if is_pt else "Topics by Source",
        color="source",
        color_discrete_sequence=["#4CAF50", "#2196F3"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    src_dist = df["n_sources"].value_counts().sort_index().reset_index()
    src_dist.columns = ["n_sources", "count"]
    labels_map = {1: "1 fonte", 2: "2 fontes"} if is_pt else {1: "1 source", 2: "2 sources"}
    src_dist["label"] = src_dist["n_sources"].map(labels_map)
    fig = px.bar(
        src_dist, x="label", y="count",
        title="Topicos por Numero de Fontes" if is_pt else "Topics by Number of Sources",
        labels={"label": "", "count": "Topicos" if is_pt else "Topics"},
        color="n_sources",
        color_continuous_scale=["#2A2D34", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

# Overlap
both = int((df["source_nav"] & df["source_tor"]).sum())
only_nave = from_nave - both
only_torrey = from_torrey - both
st.markdown(
    f"**Overlap:** {both:,} topicos em ambas as fontes | "
    f"**Apenas Nave:** {only_nave:,} | **Apenas Torrey:** {only_torrey:,}"
    if is_pt else
    f"**Overlap:** {both:,} topics in both sources | "
    f"**Nave only:** {only_nave:,} | **Torrey only:** {only_torrey:,}"
)

# ============================================================
# 3. DISTRIBUICAO ALFABETICA
# ============================================================
st.header("3. " + ("Distribuicao Alfabetica" if is_pt else "Alphabetical Distribution"))

letter_counts = df.groupby("letter").size().reset_index(name="count").sort_values("letter")

fig = px.bar(
    letter_counts, x="letter", y="count",
    title="Topicos por Letra Inicial" if is_pt else "Topics by Initial Letter",
    labels={"letter": "Letra" if is_pt else "Letter", "count": "Topicos" if is_pt else "Topics"},
    color="count",
    color_continuous_scale=["#2A2D34", "#D4A853"],
)
fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 4. REFERENCIAS BIBLICAS
# ============================================================
st.header("4. " + ("Referencias Biblicas" if is_pt else "Biblical References"))

col1, col2 = st.columns(2)

with col1:
    # Distribution of refs per topic
    fig = px.histogram(
        df, x="n_biblical_refs", nbins=50,
        title="Refs por Topico" if is_pt else "Refs per Topic",
        labels={"n_biblical_refs": "Refs"},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Topicos" if is_pt else "Topics", height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Top topics by refs
    top_refs = df.nlargest(15, "n_biblical_refs")[["topic", "n_biblical_refs", "n_sources"]]
    fig = px.bar(
        top_refs.sort_values("n_biblical_refs", ascending=True),
        x="n_biblical_refs", y="topic", orientation="h",
        title="Topicos com Mais Refs" if is_pt else "Topics with Most Refs",
        labels={"n_biblical_refs": "Refs", "topic": ""},
        color_discrete_sequence=["#4CAF50"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 5. DEFINITION REFS
# ============================================================
st.header("5. " + ("Definition Refs" if is_pt else "Definition References"))

col1, col2 = st.columns(2)
pct_with = with_def_refs / total * 100

with col1:
    st.metric(
        "Cobertura" if is_pt else "Coverage",
        f"{pct_with:.1f}%",
        f"{with_def_refs:,} de {total:,}" if is_pt else f"{with_def_refs:,} of {total:,}",
    )

with col2:
    top_def_refs = df[df["n_def_refs"] > 0].nlargest(10, "n_def_refs")[["topic", "n_def_refs"]]
    st.dataframe(
        top_def_refs.rename(columns={
            "topic": "Topico" if is_pt else "Topic",
            "n_def_refs": "Refs",
        }),
        use_container_width=True, hide_index=True,
    )

# ============================================================
# 6. BUSCA
# ============================================================
st.header("6. " + ("Buscar Topico" if is_pt else "Search Topic"))

query = st.text_input("Buscar..." if is_pt else "Search...", placeholder="FAITH, GRACE, LOVE...")
if query:
    mask = df["topic"].str.contains(query.upper(), na=False)
    results = df[mask].head(20)
    if results.empty:
        st.warning("Nenhum resultado" if is_pt else "No results")
    else:
        st.dataframe(
            results[["topic", "n_sources", "n_biblical_refs", "n_def_refs", "n_see_also"]].rename(columns={
                "topic": "Topico" if is_pt else "Topic",
                "n_sources": "Fontes" if is_pt else "Sources",
                "n_biblical_refs": "Refs",
                "n_def_refs": "Def Refs",
                "n_see_also": "See Also",
            }),
            use_container_width=True, hide_index=True,
        )
