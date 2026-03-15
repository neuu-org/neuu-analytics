"""
Pagina de analise do dataset Bible Cross-References.
1.1M+ referencias cruzadas de OpenBible + Treasury of Scripture Knowledge.
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from book_names import CROSSREF_BOOK_NAMES, friendly_name

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PARQUET = DATA_DIR / "crossrefs.parquet"

st.set_page_config(page_title="Cross-References | NEUU Analytics", page_icon="🔗", layout="wide")

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E8E0D4",
)

# ---------------------------------------------------------------------------
# Verificar dados
# ---------------------------------------------------------------------------
if not PARQUET.exists():
    st.info(
        "Dados de cross-references nao encontrados.\n\n"
        "Execute `python sync.py crossrefs` para sincronizar."
    )
    st.stop()

con = duckdb.connect()


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{PARQUET}'").df()


@st.cache_data(ttl=3600)
def query(sql: str):
    return con.sql(sql.replace("PARQUET", f"'{PARQUET}'")).df()


df = load_data()

st.title("🔗 Bible Cross-References — Analise")
st.caption("1.1M+ referencias cruzadas biblicas (OpenBible + Treasury of Scripture Knowledge)")

# ---------------------------------------------------------------------------
# 1. Visao Geral
# ---------------------------------------------------------------------------
st.header("1. Visao Geral")

total_edges = len(df)
unique_from = df.groupby(["from_book", "from_chapter", "from_verse"]).ngroups
unique_books = df["from_book"].nunique()
avg_refs = total_edges / unique_from if unique_from else 0
both_sources = df[df["source_openbible"] & df["source_tsk"]].shape[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Referencias Cruzadas", f"{total_edges:,}")
c2.metric("Versiculos com Refs", f"{unique_from:,}")
c3.metric("Livros", unique_books)
c4.metric("Media por Versiculo", f"{avg_refs:.1f}")
c5.metric("Em Ambas Fontes", f"{both_sources:,}", delta=f"{both_sources/total_edges*100:.0f}%")

col1, col2 = st.columns(2)

with col1:
    # Distribuicao por testamento
    testament_counts = df.groupby("from_testament").size().reset_index(name="count")
    testament_counts["from_testament"] = testament_counts["from_testament"].map(
        {"old_testament": "Old Testament", "new_testament": "New Testament"}
    )
    fig = px.pie(
        testament_counts,
        values="count",
        names="from_testament",
        title="Referencias por Testamento (origem)",
        color_discrete_sequence=["#636EFA", "#EF553B"],
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Connection strength
    strength_counts = df["connection_strength"].value_counts().reset_index()
    strength_counts.columns = ["Forca", "Contagem"]
    fig = px.pie(
        strength_counts,
        values="Contagem",
        names="Forca",
        title="Forca das Conexoes",
        color_discrete_sequence=["#D4A853", "#636EFA", "#00CC96"],
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 2. Top Versiculos Hub
# ---------------------------------------------------------------------------
st.header("2. Versiculos Hub (Mais Conectados)")

top_n = st.slider("Top N versiculos", 10, 50, 20, key="top_hubs")

hub_df = (
    df.groupby(["from_book", "from_chapter", "from_verse"])
    .agg(ref_count=("to_book", "size"), total_votes=("votes", "sum"))
    .reset_index()
    .sort_values("ref_count", ascending=False)
)
hub_df["verse_label"] = hub_df.apply(
    lambda r: f"{friendly_name(r['from_book'])} {r['from_chapter']}:{r['from_verse']}", axis=1
)

fig = px.bar(
    hub_df.head(top_n),
    x="verse_label",
    y="ref_count",
    title=f"Top {top_n} Versiculos com Mais Referencias Cruzadas",
    color="total_votes",
    color_continuous_scale=["#2A2D34", "#D4A853"],
    labels={"ref_count": "Referencias", "verse_label": "Versiculo", "total_votes": "Votos"},
)
fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Mapa de Conexoes entre Livros
# ---------------------------------------------------------------------------
st.header("3. Mapa de Conexoes entre Livros")

df["from_book_name"] = df["from_book"].apply(friendly_name)
df["to_book_name"] = df["to_book"].apply(friendly_name)

book_matrix = (
    df.groupby(["from_book_name", "to_book_name"])
    .size()
    .reset_index(name="count")
)

# Pegar top livros para nao sobrecarregar o heatmap
top_books_from = df["from_book_name"].value_counts().head(20).index.tolist()
top_books_to = df["to_book_name"].value_counts().head(20).index.tolist()
top_books_all = list(dict.fromkeys(top_books_from + top_books_to))[:20]

matrix_filtered = book_matrix[
    book_matrix["from_book_name"].isin(top_books_all)
    & book_matrix["to_book_name"].isin(top_books_all)
]

pivot = matrix_filtered.pivot(index="from_book_name", columns="to_book_name", values="count").fillna(0)

fig = px.imshow(
    pivot,
    title="Conexoes entre Livros (Top 20)",
    labels=dict(x="Para", y="De", color="Refs"),
    aspect="auto",
    color_continuous_scale="YlOrRd",
)
fig.update_layout(**PLOTLY_LAYOUT, height=600)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 4. Ponte AT ↔ NT
# ---------------------------------------------------------------------------
st.header("4. Ponte AT ↔ NT")
st.caption("Versiculos que mais conectam os dois testamentos")

col1, col2 = st.columns(2)

with col1:
    # AT → NT
    at_to_nt = df[
        (df["from_testament"] == "old_testament") & (df["to_testament"] == "new_testament")
    ]
    at_nt_books = (
        at_to_nt.groupby("from_book")
        .size()
        .reset_index(name="refs_to_nt")
        .sort_values("refs_to_nt", ascending=False)
    )
    at_nt_books["book_name"] = at_nt_books["from_book"].apply(friendly_name)

    fig = px.bar(
        at_nt_books.head(15),
        x="book_name",
        y="refs_to_nt",
        title="AT → NT: Livros que Mais Referenciam o NT",
        color="refs_to_nt",
        color_continuous_scale=["#2A2D34", "#636EFA"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # NT → AT
    nt_to_at = df[
        (df["from_testament"] == "new_testament") & (df["to_testament"] == "old_testament")
    ]
    nt_at_books = (
        nt_to_at.groupby("from_book")
        .size()
        .reset_index(name="refs_to_at")
        .sort_values("refs_to_at", ascending=False)
    )
    nt_at_books["book_name"] = nt_at_books["from_book"].apply(friendly_name)

    fig = px.bar(
        nt_at_books.head(15),
        x="book_name",
        y="refs_to_at",
        title="NT → AT: Livros que Mais Referenciam o AT",
        color="refs_to_at",
        color_continuous_scale=["#2A2D34", "#EF553B"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# Total de ponte
total_at_nt = len(at_to_nt)
total_nt_at = len(nt_to_at)
st.metric(
    "Total de Referencias entre Testamentos",
    f"{total_at_nt + total_nt_at:,}",
    delta=f"{(total_at_nt + total_nt_at) / total_edges * 100:.1f}% do total",
)

# ---------------------------------------------------------------------------
# 5. Distribuicao de Votos e Score
# ---------------------------------------------------------------------------
st.header("5. Distribuicao de Votos")

col1, col2 = st.columns(2)

with col1:
    voted = df[df["votes"] > 0]
    fig = px.histogram(
        voted,
        x="votes",
        nbins=50,
        title="Distribuicao de Votos (OpenBible)",
        labels={"votes": "Votos"},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Frequencia")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Fontes
    only_openbible = df[df["source_openbible"] & ~df["source_tsk"]].shape[0]
    only_tsk = df[~df["source_openbible"] & df["source_tsk"]].shape[0]
    both = df[df["source_openbible"] & df["source_tsk"]].shape[0]

    source_df = pd.DataFrame({
        "Fonte": ["Apenas OpenBible", "Apenas TSK", "Ambas"],
        "Contagem": [only_openbible, only_tsk, both],
    })
    fig = px.bar(
        source_df,
        x="Fonte",
        y="Contagem",
        title="Cobertura por Fonte",
        color="Fonte",
        color_discrete_sequence=["#636EFA", "#00CC96", "#D4A853"],
        text="Contagem",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 6. Refs por Livro
# ---------------------------------------------------------------------------
st.header("6. Referencias por Livro")

book_ref_counts = (
    df.groupby("from_book")
    .size()
    .reset_index(name="total_refs")
    .sort_values("total_refs", ascending=False)
)
book_ref_counts["book_name"] = book_ref_counts["from_book"].apply(friendly_name)

fig = px.bar(
    book_ref_counts,
    x="book_name",
    y="total_refs",
    title="Total de Referencias Cruzadas por Livro",
    color="total_refs",
    color_continuous_scale="Viridis",
)
fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)
