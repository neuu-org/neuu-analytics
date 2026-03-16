"""
Pagina de analise do dataset Bible Topics.
5,745 topicos biblicos unificados de Nave + Torrey.
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
    "5,745 topicos unificados de Nave's Topical Bible (1896) + Torrey's Topical Textbook (1897)"
    if is_pt else
    "5,745 unified topics from Nave's Topical Bible (1896) + Torrey's Topical Textbook (1897)"
)

# ============================================================
# 1. OVERVIEW
# ============================================================
st.header("1. " + ("Visao Geral" if is_pt else "Overview"))

total = len(df)
from_nave = int(df["source_nav"].sum())
from_torrey = int(df["source_tor"].sum())
both = int((df["source_nav"] & df["source_tor"]).sum())
total_refs = int(df["n_biblical_refs"].sum())
with_refs = int((df["n_biblical_refs"] > 0).sum())
total_def_refs = int(df["n_def_refs"].sum())

cols = st.columns(6)
cols[0].metric("Topicos" if is_pt else "Topics", f"{total:,}")
cols[1].metric("Nave", f"{from_nave:,}")
cols[2].metric("Torrey", f"{from_torrey:,}")
cols[3].metric("Overlap", f"{both:,}")
cols[4].metric("Refs", f"{total_refs:,}")
cols[5].metric("Cobertura" if is_pt else "Coverage", f"{with_refs/total*100:.0f}%")

# ============================================================
# 2. SOURCES VENN
# ============================================================
st.header("2. " + ("Fontes" if is_pt else "Sources"))

col1, col2 = st.columns(2)

with col1:
    only_nave = from_nave - both
    only_torrey = from_torrey - both

    fig = go.Figure(go.Funnel(
        y=["Nave only", "Both", "Torrey only"],
        x=[only_nave, both, only_torrey],
        textinfo="value+percent total",
        marker=dict(color=["#4CAF50", "#D4A853", "#2196F3"]),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Distribuicao por Fonte" if is_pt else "Source Distribution",
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Refs per source
    nave_refs = int(df[df["source_nav"]]["n_biblical_refs"].sum())
    torrey_refs = int(df[df["source_tor"]]["n_biblical_refs"].sum())

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Nave", x=["Refs"], y=[nave_refs],
        marker_color="#4CAF50", text=[f"{nave_refs:,}"], textposition="auto",
    ))
    fig.add_trace(go.Bar(
        name="Torrey", x=["Refs"], y=[torrey_refs],
        marker_color="#2196F3", text=[f"{torrey_refs:,}"], textposition="auto",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Refs por Fonte" if is_pt else "Refs by Source",
        barmode="group", height=300, showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 3. REFERENCES ANALYSIS
# ============================================================
st.header("3. " + ("Analise de Referencias" if is_pt else "Reference Analysis"))

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        df[df["n_biblical_refs"] > 0], x="n_biblical_refs", nbins=60,
        title="Distribuicao de Refs por Topico" if is_pt else "Refs Distribution per Topic",
        labels={"n_biblical_refs": "Refs"},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Topicos" if is_pt else "Topics", height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    top_refs = df.nlargest(20, "n_biblical_refs")[["topic", "n_biblical_refs", "n_sources"]]
    fig = px.bar(
        top_refs.sort_values("n_biblical_refs", ascending=True),
        x="n_biblical_refs", y="topic", orientation="h",
        title="Top 20 Topicos com Mais Refs" if is_pt else "Top 20 Topics by Refs",
        labels={"n_biblical_refs": "Refs", "topic": ""},
        color="n_sources",
        color_continuous_scale=["#2A2D34", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 4. ALPHABETICAL DISTRIBUTION
# ============================================================
st.header("4. " + ("Distribuicao Alfabetica" if is_pt else "Alphabetical Distribution"))

letter_counts = df.groupby("letter").agg(
    topics=("topic", "count"),
    total_refs=("n_biblical_refs", "sum"),
).reset_index().sort_values("letter")

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Topicos" if is_pt else "Topics",
    x=letter_counts["letter"], y=letter_counts["topics"],
    marker_color="#4CAF50", yaxis="y",
))
fig.add_trace(go.Scatter(
    name="Refs",
    x=letter_counts["letter"], y=letter_counts["total_refs"],
    mode="lines+markers", marker_color="#D4A853", yaxis="y2",
))
fig.update_layout(
    **PLOTLY_LAYOUT,
    title="Topicos e Refs por Letra" if is_pt else "Topics and Refs by Letter",
    yaxis=dict(title="Topicos" if is_pt else "Topics", side="left"),
    yaxis2=dict(title="Refs", side="right", overlaying="y"),
    height=400,
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 5. DEFINITION REFS COVERAGE
# ============================================================
st.header("5. " + ("Cobertura de Definition Refs" if is_pt else "Definition Refs Coverage"))

with_def = int(df["has_def_refs"].sum())
without_def = total - with_def

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure(go.Pie(
        values=[with_def, without_def],
        labels=[
            "Com Def Refs" if is_pt else "With Def Refs",
            "Sem Def Refs" if is_pt else "Without Def Refs",
        ],
        marker=dict(colors=["#D4A853", "#2A2D34"]),
        hole=0.5,
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"Definition Refs: {with_def/total*100:.1f}%",
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    top_def = df[df["n_def_refs"] > 0].nlargest(10, "n_def_refs")[["topic", "n_def_refs"]]
    fig = px.bar(
        top_def.sort_values("n_def_refs", ascending=True),
        x="n_def_refs", y="topic", orientation="h",
        title="Top 10 por Definition Refs" if is_pt else "Top 10 by Definition Refs",
        labels={"n_def_refs": "Refs", "topic": ""},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=300)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 6. DATA QUALITY
# ============================================================
st.header("6. " + ("Qualidade dos Dados" if is_pt else "Data Quality"))

quality_data = pd.DataFrame({
    "metric": [
        "Com refs" if is_pt else "With refs",
        "Com def_refs" if is_pt else "With def_refs",
        "Com see_also" if is_pt else "With see_also",
        "2 fontes" if is_pt else "2 sources",
    ],
    "percent": [
        with_refs / total * 100,
        with_def / total * 100,
        (df["n_see_also"] > 0).sum() / total * 100,
        both / total * 100,
    ],
})

fig = px.bar(
    quality_data.sort_values("percent"),
    x="percent", y="metric", orientation="h",
    title="Cobertura por Campo" if is_pt else "Field Coverage",
    labels={"percent": "%", "metric": ""},
    color="percent",
    color_continuous_scale=["#2A2D34", "#4CAF50"],
)
fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=250)
st.plotly_chart(fig, use_container_width=True)
