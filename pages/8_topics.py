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

TYPE_COLORS = {
    "topic": "#4CAF50",
    "dictionary": "#2196F3",
    "both": "#FF9800",
}

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
    "7,873 topicos unificados de Nave's Topical Bible + Torrey's Topical Textbook"
    if is_pt else
    "7,873 unified topics from Nave's Topical Bible + Torrey's Topical Textbook"
)

# ============================================================
# 1. OVERVIEW
# ============================================================
st.header("1. " + ("Visao Geral" if is_pt else "Overview"))

total = len(df)
with_defs = int(df["has_definitions"].sum())
with_ai = int(df["has_ai"].sum())
with_def_refs = int(df["has_def_refs"].sum())
total_refs = int(df["n_biblical_refs"].sum())

cols = st.columns(5)
cols[0].metric("Topicos" if is_pt else "Topics", f"{total:,}")
cols[1].metric("Com Definicoes" if is_pt else "With Definitions", f"{with_defs:,}")
cols[2].metric("Com AI" if is_pt else "With AI", f"{with_ai:,}")
cols[3].metric("Com Def Refs" if is_pt else "With Def Refs", f"{with_def_refs:,}")
cols[4].metric("Refs Biblicas" if is_pt else "Biblical Refs", f"{total_refs:,}")

# ============================================================
# 2. POR TIPO
# ============================================================
st.header("2. " + ("Por Tipo" if is_pt else "By Type"))

col1, col2 = st.columns(2)

with col1:
    type_counts = df["type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]
    fig = px.pie(
        type_counts, values="count", names="type",
        title="Distribuicao por Tipo" if is_pt else "Distribution by Type",
        color="type",
        color_discrete_map=TYPE_COLORS,
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Sources coverage
    source_data = pd.DataFrame({
        "source": ["Nave (NAV)", "Torrey (TOR)", "Easton (EAS)", "Smith (SMI)"],
        "count": [
            int(df["source_nav"].sum()),
            int(df["source_tor"].sum()),
            int(df["source_eas"].sum()),
            int(df["source_smi"].sum()),
        ]
    })
    fig = px.bar(
        source_data.sort_values("count", ascending=True),
        x="count", y="source", orientation="h",
        title="Topicos por Fonte" if is_pt else "Topics by Source",
        labels={"count": "Topicos" if is_pt else "Topics", "source": ""},
        color="source",
        color_discrete_sequence=["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 3. COBERTURA DE CAMPOS
# ============================================================
st.header("3. " + ("Cobertura de Campos" if is_pt else "Field Coverage"))

coverage_data = pd.DataFrame({
    "field": [
        "definitions", "definition_refs", "ai_enrichment",
        "reference_groups", "biblical_references"
    ],
    "coverage": [
        df["has_definitions"].mean() * 100,
        df["has_def_refs"].mean() * 100,
        df["has_ai"].mean() * 100,
        (df["n_ref_groups"] > 0).mean() * 100,
        (df["n_biblical_refs"] > 0).mean() * 100,
    ]
})

fig = px.bar(
    coverage_data.sort_values("coverage", ascending=True),
    x="coverage", y="field", orientation="h",
    title="Cobertura por Campo (%)" if is_pt else "Field Coverage (%)",
    labels={"coverage": "%", "field": ""},
    color="coverage",
    color_continuous_scale=["#2A2D34", "#D4A853"],
)
fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=350)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 4. DISTRIBUICAO ALFABETICA
# ============================================================
st.header("4. " + ("Distribuicao Alfabetica" if is_pt else "Alphabetical Distribution"))

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
# 5. NUMERO DE FONTES
# ============================================================
st.header("5. " + ("Fontes por Topico" if is_pt else "Sources per Topic"))

col1, col2 = st.columns(2)

with col1:
    src_dist = df["n_sources"].value_counts().sort_index().reset_index()
    src_dist.columns = ["n_sources", "count"]
    fig = px.bar(
        src_dist, x="n_sources", y="count",
        title="Topicos por Numero de Fontes" if is_pt else "Topics by Number of Sources",
        labels={"n_sources": "Fontes" if is_pt else "Sources", "count": "Topicos" if is_pt else "Topics"},
        color="n_sources",
        color_continuous_scale=["#2A2D34", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Topics with most biblical refs
    top_refs = df.nlargest(15, "n_biblical_refs")[["topic", "n_biblical_refs", "type", "n_sources"]]
    fig = px.bar(
        top_refs.sort_values("n_biblical_refs", ascending=True),
        x="n_biblical_refs", y="topic", orientation="h",
        color="type",
        color_discrete_map=TYPE_COLORS,
        title="Topicos com Mais Refs" if is_pt else "Topics with Most Refs",
        labels={"n_biblical_refs": "Refs", "topic": ""},
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=350)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 6. BUSCA DE TOPICOS
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
            results[["topic", "type", "n_sources", "has_definitions", "has_ai", "n_biblical_refs"]].rename(columns={
                "topic": "Topico" if is_pt else "Topic",
                "type": "Tipo" if is_pt else "Type",
                "n_sources": "Fontes" if is_pt else "Sources",
                "has_definitions": "Defs",
                "has_ai": "AI",
                "n_biblical_refs": "Refs",
            }),
            use_container_width=True, hide_index=True,
        )

        # Show detail for first result
        selected = results.iloc[0]
        with st.expander(f"Detalhes: {selected['topic']}", expanded=True):
            if selected.get("first_definition"):
                st.markdown(f"**Definicao:** {selected['first_definition']}...")
            if selected.get("ai_summary"):
                st.markdown(f"**AI Summary:** {selected['ai_summary']}")
            st.markdown(f"**Tipo:** {selected['type']} | **Fontes:** {selected['n_sources']} | **Refs:** {selected['n_biblical_refs']} | **Def Refs:** {selected['n_def_refs']}")
