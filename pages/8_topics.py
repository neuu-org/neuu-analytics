"""
Pagina de analise do dataset Bible Topics.
620 topicos biblicos de Torrey's Topical Textbook (Nave temporariamente indisponivel).
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
    f"{len(df):,} topicos de Torrey's New Topical Textbook (1897)"
    if is_pt else
    f"{len(df):,} topics from Torrey's New Topical Textbook (1897)"
)
st.info(
    "Nave's Topical Bible esta temporariamente indisponivel enquanto o parser de referencias e aprimorado."
    if is_pt else
    "Nave's Topical Bible is temporarily unavailable while the reference parser is being improved."
)

# ============================================================
# 1. OVERVIEW
# ============================================================
st.header("1. " + ("Visao Geral" if is_pt else "Overview"))

total = len(df)
total_refs = int(df["n_biblical_refs"].sum())
with_refs = int((df["n_biblical_refs"] > 0).sum())
avg_refs = total_refs / total if total > 0 else 0
with_see_also = int((df["n_see_also"] > 0).sum())

cols = st.columns(5)
cols[0].metric("Topicos" if is_pt else "Topics", f"{total:,}")
cols[1].metric("Refs", f"{total_refs:,}")
cols[2].metric("Media" if is_pt else "Average", f"{avg_refs:.1f} refs/topic")
cols[3].metric("Cobertura" if is_pt else "Coverage", f"{with_refs/total*100:.0f}%")
cols[4].metric("See Also", f"{with_see_also:,}")

# ============================================================
# 2. REFERENCES ANALYSIS
# ============================================================
st.header("2. " + ("Analise de Referencias" if is_pt else "Reference Analysis"))

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
    top_refs = df.nlargest(20, "n_biblical_refs")[["topic", "n_biblical_refs"]]
    fig = px.bar(
        top_refs.sort_values("n_biblical_refs", ascending=True),
        x="n_biblical_refs", y="topic", orientation="h",
        title="Top 20 Topicos com Mais Refs" if is_pt else "Top 20 Topics by Refs",
        labels={"n_biblical_refs": "Refs", "topic": ""},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 3. ALPHABETICAL DISTRIBUTION
# ============================================================
st.header("3. " + ("Distribuicao Alfabetica" if is_pt else "Alphabetical Distribution"))

letter_counts = df.groupby("letter").agg(
    topics=("topic", "count"),
    total_refs=("n_biblical_refs", "sum"),
).reset_index().sort_values("letter")

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Topicos" if is_pt else "Topics",
    x=letter_counts["letter"], y=letter_counts["topics"],
    marker_color="#2196F3", yaxis="y",
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
# 4. OT/NT DISTRIBUTION
# ============================================================
st.header("4. " + ("AT/NT" if is_pt else "OT/NT Distribution"))

col1, col2 = st.columns(2)
with col1:
    ot_total = int(df["ot_refs"].sum())
    nt_total = int(df["nt_refs"].sum())
    fig = go.Figure(go.Pie(
        labels=["AT" if is_pt else "OT", "NT"],
        values=[ot_total, nt_total],
        marker_colors=["#4CAF50", "#2196F3"],
        hole=0.4,
        textinfo="percent+value",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Refs AT vs NT" if is_pt else "OT vs NT Refs",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    quality_data = pd.DataFrame({
        "metric": [
            "Com refs" if is_pt else "With refs",
            "Com see_also" if is_pt else "With see_also",
            "OT + NT" if is_pt else "OT + NT",
        ],
        "percent": [
            with_refs / total * 100,
            with_see_also / total * 100,
            ((df["ot_refs"] > 0) & (df["nt_refs"] > 0)).sum() / total * 100,
        ],
    })
    fig = px.bar(
        quality_data.sort_values("percent"),
        x="percent", y="metric", orientation="h",
        title="Cobertura por Campo" if is_pt else "Field Coverage",
        labels={"percent": "%", "metric": ""},
        color="percent",
        color_continuous_scale=["#2A2D34", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)
