"""
Pagina de analise do dataset Bible Cross-References.
1.1M+ referencias cruzadas de OpenBible + Treasury of Scripture Knowledge.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from book_names import CROSSREF_BOOK_NAMES, friendly_name

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PARQUET = DATA_DIR / "crossrefs.parquet"
COMM_PARQUET = DATA_DIR / "commentaries.parquet"

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


df = load_data()
df["from_book_name"] = df["from_book"].apply(friendly_name)
df["to_book_name"] = df["to_book"].apply(friendly_name)

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
median_refs = df.groupby(["from_book", "from_chapter", "from_verse"]).size().median()
max_refs = df.groupby(["from_book", "from_chapter", "from_verse"]).size().max()
both_sources = df[df["source_openbible"] & df["source_tsk"]].shape[0]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Referencias", f"{total_edges:,}")
c2.metric("Versiculos", f"{unique_from:,}")
c3.metric("Livros", unique_books)
c4.metric("Media/Versiculo", f"{avg_refs:.1f}")
c5.metric("Mediana", f"{median_refs:.0f}")
c6.metric("Max (hub)", f"{max_refs:,}")

col1, col2, col3 = st.columns(3)

with col1:
    testament_counts = df.groupby("from_testament").size().reset_index(name="count")
    testament_counts["from_testament"] = testament_counts["from_testament"].map(
        {"old_testament": "Old Testament", "new_testament": "New Testament"}
    )
    fig = px.pie(
        testament_counts, values="count", names="from_testament",
        title="Por Testamento (origem)",
        color_discrete_sequence=["#636EFA", "#EF553B"],
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    strength_counts = df["connection_strength"].value_counts().reset_index()
    strength_counts.columns = ["Forca", "Contagem"]
    fig = px.pie(
        strength_counts, values="Contagem", names="Forca",
        title="Forca das Conexoes",
        color_discrete_map={"strong": "#D4A853", "moderate": "#636EFA", "weak": "#5A5550"},
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col3:
    only_openbible = df[df["source_openbible"] & ~df["source_tsk"]].shape[0]
    only_tsk = df[~df["source_openbible"] & df["source_tsk"]].shape[0]
    both = df[df["source_openbible"] & df["source_tsk"]].shape[0]
    source_df = pd.DataFrame({
        "Fonte": ["OpenBible", "TSK", "Ambas"],
        "Contagem": [only_openbible, only_tsk, both],
    })
    fig = px.pie(
        source_df, values="Contagem", names="Fonte",
        title="Cobertura por Fonte",
        color_discrete_sequence=["#636EFA", "#00CC96", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 2. Top Versiculos Hub
# ---------------------------------------------------------------------------
st.header("2. Versiculos Hub (Mais Conectados)")
st.caption("Versiculos que funcionam como nos centrais na rede de referencias biblicas")

top_n = st.slider("Top N versiculos", 10, 50, 20, key="top_hubs")

hub_df = (
    df.groupby(["from_book", "from_chapter", "from_verse", "from_book_name"])
    .agg(
        ref_count=("to_book", "size"),
        total_votes=("votes", "sum"),
        avg_score=("score", "mean"),
        strong_count=("connection_strength", lambda x: (x == "strong").sum()),
    )
    .reset_index()
    .sort_values("ref_count", ascending=False)
)
hub_df["verse_label"] = hub_df.apply(
    lambda r: f"{r['from_book_name']} {r['from_chapter']}:{r['from_verse']}", axis=1
)

col1, col2 = st.columns([3, 1])

with col1:
    fig = px.bar(
        hub_df.head(top_n),
        x="verse_label", y="ref_count",
        title=f"Top {top_n} Versiculos Hub",
        color="avg_score",
        color_continuous_scale=["#2A2D34", "#D4A853"],
        labels={"ref_count": "Referencias", "verse_label": "Versiculo", "avg_score": "Score medio"},
    )
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Destaques")
    for _, row in hub_df.head(5).iterrows():
        st.markdown(
            f"**{row['verse_label']}**  \n"
            f"{row['ref_count']} refs · {row['strong_count']} fortes · {row['total_votes']} votos"
        )
        st.markdown("---")

# ---------------------------------------------------------------------------
# 3. Distribuicao de Referencias por Versiculo
# ---------------------------------------------------------------------------
st.header("3. Distribuicao de Referencias")

col1, col2 = st.columns(2)

refs_per_verse = df.groupby(["from_book", "from_chapter", "from_verse"]).size().reset_index(name="refs")

with col1:
    fig = px.histogram(
        refs_per_verse, x="refs", nbins=60,
        title="Quantas Referencias Cada Versiculo Tem",
        labels={"refs": "Referencias por versiculo"},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Frequencia")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    voted = df[df["votes"] > 0]
    fig = px.histogram(
        voted, x="votes", nbins=50,
        title="Distribuicao de Votos (OpenBible Community)",
        labels={"votes": "Votos"},
        color_discrete_sequence=["#636EFA"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Frequencia")
    st.plotly_chart(fig, use_container_width=True)

# Top votados
st.subheader("Referencias Mais Votadas pela Comunidade")
top_voted = df.nlargest(10, "votes").copy()
top_voted["from_label"] = top_voted.apply(
    lambda r: f"{friendly_name(r['from_book'])} {r['from_chapter']}:{r['from_verse']}", axis=1
)
top_voted["to_label"] = top_voted.apply(
    lambda r: f"{friendly_name(r['to_book'])} {r['to_chapter']}:{r['to_verse']}", axis=1
)
st.dataframe(
    top_voted[["from_label", "to_label", "votes", "score", "connection_strength"]].rename(
        columns={"from_label": "De", "to_label": "Para", "votes": "Votos",
                 "score": "Score", "connection_strength": "Forca"}
    ),
    hide_index=True, use_container_width=True,
)

# ---------------------------------------------------------------------------
# 4. Mapa de Conexoes entre Livros
# ---------------------------------------------------------------------------
st.header("4. Mapa de Conexoes entre Livros")

# Heatmap interativo com seletor de livros
all_books = sorted(df["from_book_name"].unique())

view_mode = st.radio(
    "Visualizacao",
    ["Top 20 livros", "Selecionar livros", "Todos os livros"],
    horizontal=True,
    key="heatmap_mode",
)

if view_mode == "Top 20 livros":
    top_books = df["from_book_name"].value_counts().head(20).index.tolist()
elif view_mode == "Selecionar livros":
    top_books = st.multiselect(
        "Livros", all_books,
        default=[friendly_name(b) for b in ["PSA", "ISA", "GEN", "MAT", "JHN", "ROM", "HEB", "REV"]
                 if friendly_name(b) in all_books],
    )
else:
    top_books = all_books

if top_books:
    book_matrix = (
        df[df["from_book_name"].isin(top_books) & df["to_book_name"].isin(top_books)]
        .groupby(["from_book_name", "to_book_name"])
        .size()
        .reset_index(name="count")
    )
    pivot = book_matrix.pivot(index="from_book_name", columns="to_book_name", values="count").fillna(0)

    fig = px.imshow(
        pivot,
        title="Mapa de Conexoes Livro → Livro",
        labels=dict(x="Para", y="De", color="Refs"),
        aspect="auto",
        color_continuous_scale="YlOrRd",
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=max(400, len(top_books) * 28))
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 5. Heatmap de Densidade por Capitulo
# ---------------------------------------------------------------------------
st.header("5. Densidade por Capitulo")
st.caption("Quantas referencias cruzadas partem de cada capitulo")

selected_book_heat = st.selectbox(
    "Livro para heatmap de capitulos",
    all_books,
    index=all_books.index("Psalms") if "Psalms" in all_books else 0,
    key="heat_book",
)

book_filter = df[df["from_book_name"] == selected_book_heat]

if not book_filter.empty:
    chapter_density = (
        book_filter.groupby(["from_chapter", "from_verse"])
        .size()
        .reset_index(name="refs")
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        # Scatter: cada ponto e um versiculo, tamanho = refs
        fig = px.scatter(
            chapter_density,
            x="from_chapter", y="from_verse",
            size="refs", color="refs",
            color_continuous_scale=["#1A1D24", "#D4A853"],
            title=f"Densidade de Referencias — {selected_book_heat}",
            labels={"from_chapter": "Capitulo", "from_verse": "Versiculo", "refs": "Refs"},
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        chapter_totals = (
            book_filter.groupby("from_chapter").size().reset_index(name="total")
            .sort_values("total", ascending=False)
        )
        st.subheader(f"Capitulos de {selected_book_heat}")
        st.dataframe(
            chapter_totals.head(10).rename(columns={"from_chapter": "Cap", "total": "Refs"}),
            hide_index=True,
        )

# ---------------------------------------------------------------------------
# 6. Ponte AT ↔ NT
# ---------------------------------------------------------------------------
st.header("6. Ponte AT ↔ NT")
st.caption("Como os dois testamentos se conectam atraves de referencias cruzadas")

at_to_nt = df[(df["from_testament"] == "old_testament") & (df["to_testament"] == "new_testament")]
nt_to_at = df[(df["from_testament"] == "new_testament") & (df["to_testament"] == "old_testament")]
total_bridge = len(at_to_nt) + len(nt_to_at)

bc1, bc2, bc3 = st.columns(3)
bc1.metric("AT → NT", f"{len(at_to_nt):,}")
bc2.metric("NT → AT", f"{len(nt_to_at):,}")
bc3.metric("Total entre Testamentos", f"{total_bridge:,}",
           delta=f"{total_bridge / total_edges * 100:.1f}% do total")

col1, col2 = st.columns(2)

with col1:
    at_nt_books = (
        at_to_nt.groupby("from_book_name").size()
        .reset_index(name="refs_to_nt")
        .sort_values("refs_to_nt", ascending=True)
    )
    fig = px.bar(
        at_nt_books.tail(15), x="refs_to_nt", y="from_book_name",
        orientation="h",
        title="AT → NT: Livros que Mais Referenciam o NT",
        color="refs_to_nt",
        color_continuous_scale=["#2A2D34", "#636EFA"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    nt_at_books = (
        nt_to_at.groupby("from_book_name").size()
        .reset_index(name="refs_to_at")
        .sort_values("refs_to_at", ascending=True)
    )
    fig = px.bar(
        nt_at_books.tail(15), x="refs_to_at", y="from_book_name",
        orientation="h",
        title="NT → AT: Livros que Mais Referenciam o AT",
        color="refs_to_at",
        color_continuous_scale=["#2A2D34", "#EF553B"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# Top versiculos ponte
st.subheader("Versiculos Ponte Mais Conectados")
bridge_verses = pd.concat([
    at_to_nt.assign(direction="AT→NT"),
    nt_to_at.assign(direction="NT→AT"),
])
bridge_hub = (
    bridge_verses.groupby(["from_book_name", "from_chapter", "from_verse", "direction"])
    .agg(bridge_refs=("to_book", "size"), total_votes=("votes", "sum"))
    .reset_index()
    .sort_values("bridge_refs", ascending=False)
)
bridge_hub["verse_label"] = bridge_hub.apply(
    lambda r: f"{r['from_book_name']} {r['from_chapter']}:{r['from_verse']}", axis=1
)
st.dataframe(
    bridge_hub.head(10)[["verse_label", "direction", "bridge_refs", "total_votes"]].rename(
        columns={"verse_label": "Versiculo", "direction": "Direcao",
                 "bridge_refs": "Refs entre Testamentos", "total_votes": "Votos"}
    ),
    hide_index=True, use_container_width=True,
)

# ---------------------------------------------------------------------------
# 7. Livros como "Pontes" (Network Degree)
# ---------------------------------------------------------------------------
st.header("7. Livros como Pontes na Rede")
st.caption("Quais livros se conectam com mais livros diferentes (grau de rede)")

book_degree = (
    df.groupby("from_book_name")["to_book_name"]
    .nunique()
    .reset_index(name="livros_conectados")
    .sort_values("livros_conectados", ascending=False)
)
book_degree["total_refs"] = book_degree["from_book_name"].map(
    df["from_book_name"].value_counts()
)

fig = px.scatter(
    book_degree,
    x="livros_conectados", y="total_refs",
    size="total_refs", color="livros_conectados",
    text="from_book_name",
    color_continuous_scale=["#2A2D34", "#D4A853"],
    title="Grau de Rede vs Volume de Referencias",
    labels={"livros_conectados": "Livros Conectados (grau)", "total_refs": "Total de Referencias",
            "from_book_name": "Livro"},
)
fig.update_traces(textposition="top center", textfont_size=10)
fig.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 8. Referencias por Livro (ranking completo)
# ---------------------------------------------------------------------------
st.header("8. Referencias por Livro")

book_ref_counts = (
    df.groupby("from_book_name")
    .agg(
        total_refs=("to_book", "size"),
        avg_per_verse=("to_book", lambda x: len(x) / max(x.groupby([
            df.loc[x.index, "from_chapter"], df.loc[x.index, "from_verse"]
        ]).ngroups, 1) if len(x) > 0 else 0),
    )
    .reset_index()
    .sort_values("total_refs", ascending=False)
)

fig = px.bar(
    book_ref_counts,
    x="from_book_name", y="total_refs",
    title="Total de Referencias Cruzadas por Livro",
    color="total_refs",
    color_continuous_scale="Viridis",
    labels={"from_book_name": "Livro", "total_refs": "Total Refs"},
)
fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 9. Cross-Dataset: Riqueza dos Versiculos (se commentaries disponivel)
# ---------------------------------------------------------------------------
if COMM_PARQUET.exists():
    st.header("9. Cross-Dataset: Riqueza Biblica")
    st.caption("Cruzamento entre comentarios patristicos e referencias cruzadas por livro")

    @st.cache_data(ttl=3600)
    def load_comm_stats():
        return con.sql(f"""
            SELECT book, COUNT(*) as commentaries
            FROM '{COMM_PARQUET}'
            WHERE author IS NOT NULL
            GROUP BY book
        """).df()

    comm_stats = load_comm_stats()

    # Crossrefs por livro (usando abreviacao do commentaries via CROSSREF_TO_COMM)
    from book_names import CROSSREF_TO_COMM
    crossref_by_book = df.groupby("from_book").size().reset_index(name="crossrefs")
    crossref_by_book["comm_book"] = crossref_by_book["from_book"].map(CROSSREF_TO_COMM)

    merged = crossref_by_book.merge(
        comm_stats, left_on="comm_book", right_on="book", how="inner"
    )
    merged["book_name"] = merged["from_book"].apply(friendly_name)

    if not merged.empty:
        fig = px.scatter(
            merged,
            x="crossrefs", y="commentaries",
            size="crossrefs", color="commentaries",
            text="book_name",
            color_continuous_scale=["#2A2D34", "#D4A853"],
            title="Comentarios vs Referencias Cruzadas por Livro",
            labels={"crossrefs": "Referencias Cruzadas", "commentaries": "Comentarios"},
        )
        fig.update_traces(textposition="top center", textfont_size=9)
        fig.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Livros mais ricos (alto em ambos)
        merged["richness_score"] = (
            merged["crossrefs"] / merged["crossrefs"].max()
            + merged["commentaries"] / merged["commentaries"].max()
        )
        richest = merged.nlargest(10, "richness_score")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Livros Mais Ricos")
            st.caption("Maior combinacao de comentarios + referencias")
            st.dataframe(
                richest[["book_name", "commentaries", "crossrefs"]].rename(
                    columns={"book_name": "Livro", "commentaries": "Comentarios",
                             "crossrefs": "Cross-Refs"}
                ),
                hide_index=True,
            )

        with col2:
            # Lacunas: muitas crossrefs mas poucos comentarios
            merged["gap_score"] = (
                merged["crossrefs"] / merged["crossrefs"].max()
                - merged["commentaries"] / merged["commentaries"].max()
            )
            gaps = merged.nlargest(10, "gap_score")
            st.subheader("Lacunas de Pesquisa")
            st.caption("Muitas referencias mas poucos comentarios — oportunidade de estudo")
            st.dataframe(
                gaps[["book_name", "commentaries", "crossrefs"]].rename(
                    columns={"book_name": "Livro", "commentaries": "Comentarios",
                             "crossrefs": "Cross-Refs"}
                ),
                hide_index=True,
            )
