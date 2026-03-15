"""
Pagina de analise do dataset Bible Commentaries.
"""

import re
from collections import Counter
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from book_names import friendly_name

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PARQUET = DATA_DIR / "commentaries.parquet"
ENRICHED_PARQUET = DATA_DIR / "commentaries_enriched.parquet"

st.set_page_config(page_title="Commentaries | NEUU Analytics", page_icon="📖", layout="wide")

# Plotly template dark consistente com o tema NEUU
PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E8E0D4",
)


def parse_period_year(period: str) -> int | None:
    if not period:
        return None
    match = re.search(r"(\d{3,4})", str(period))
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# Verificar dados
# ---------------------------------------------------------------------------
if not PARQUET.exists():
    st.error("Dados de commentaries nao encontrados. Execute `python sync.py` primeiro.")
    st.stop()

# ---------------------------------------------------------------------------
# Carregar com DuckDB (rapido, sem carregar tudo em memoria)
# ---------------------------------------------------------------------------
con = duckdb.connect()


@st.cache_data(ttl=3600)
def load_data(_parquet_mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{PARQUET}'").df()


@st.cache_data(ttl=3600)
def load_enriched() -> pd.DataFrame | None:
    if ENRICHED_PARQUET.exists():
        return con.sql(f"SELECT * FROM '{ENRICHED_PARQUET}'").df()
    return None


df = load_data(PARQUET.stat().st_mtime)
if "book" in df.columns:
    df["book_name"] = df["book"].apply(friendly_name)
else:
    df["book_name"] = "Unknown"
df_with = df[df["author"].notna()]
df_empty = df[df["author"].isna()]

st.title("📖 Bible Commentaries — Analise")
st.caption("Dataset de comentarios patristicos e historicos (AD 100-1700)")

# ---------------------------------------------------------------------------
# 1. Visao Geral
# ---------------------------------------------------------------------------
st.header("1. Visao Geral")

total_verses = len(df)
total_commentaries = len(df_with)
unique_authors = df_with["author"].nunique()
unique_books = df["book"].nunique()
empty_verses = len(df_empty)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Versiculos", f"{total_verses:,}")
c2.metric("Comentarios", f"{total_commentaries:,}")
c3.metric("Autores", unique_authors)
c4.metric("Livros", unique_books)
c5.metric(
    "Sem comentarios",
    f"{empty_verses:,}",
    delta=f"{empty_verses / total_verses * 100:.1f}%",
    delta_color="inverse",
)

col1, col2 = st.columns(2)

with col1:
    testament_counts = df_with.groupby("testament").size().reset_index(name="count")
    fig = px.pie(
        testament_counts,
        values="count",
        names="testament",
        title="Comentarios por Testamento",
        color_discrete_sequence=["#636EFA", "#EF553B"],
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    cat_counts = (
        df_with.groupby("category")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )
    fig = px.bar(
        cat_counts,
        x="count",
        y="category",
        orientation="h",
        title="Comentarios por Categoria",
        color="category",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 2. Analise por Livro
# ---------------------------------------------------------------------------
st.header("2. Analise por Livro")

book_counts = (
    df_with.groupby("book_name")
    .size()
    .reset_index(name="total")
    .sort_values("total", ascending=False)
)

top_n = st.slider("Top N livros", 10, 50, 20, key="top_books")

fig = px.bar(
    book_counts.head(top_n),
    x="book_name",
    y="total",
    title=f"Top {top_n} Livros por Quantidade de Comentarios",
    color="total",
    color_continuous_scale="Viridis",
)
st.plotly_chart(fig, use_container_width=True)

# Heatmap
st.subheader("Densidade de Comentarios por Capitulo")

available_books = sorted(df_with["book_name"].unique())
default_books = [friendly_name(b) for b in ["mt", "gn", "ps", "rom"] if friendly_name(b) in available_books]
if not default_books:
    default_books = available_books[:4]

books_for_heatmap = st.multiselect(
    "Selecione livros para o heatmap",
    options=available_books,
    default=default_books,
)

if books_for_heatmap:
    heat_df = (
        df_with[df_with["book_name"].isin(books_for_heatmap)]
        .groupby(["book_name", "chapter"])
        .size()
        .reset_index(name="count")
    )
    heat_pivot = heat_df.pivot(index="book_name", columns="chapter", values="count").fillna(0)
    fig = px.imshow(
        heat_pivot,
        title="Comentarios por Capitulo",
        labels=dict(x="Capitulo", y="Livro", color="Qtd"),
        aspect="auto",
        color_continuous_scale="YlOrRd",
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Autores
# ---------------------------------------------------------------------------
st.header("3. Autores")

col1, col2 = st.columns(2)

with col1:
    author_counts = (
        df_with.groupby("author")
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )
    fig = px.bar(
        author_counts.head(20),
        x="total",
        y="author",
        orientation="h",
        title="Top 20 Autores Mais Prolificos",
        color="total",
        color_continuous_scale="Blues",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    author_diversity = (
        df_with.groupby("author")["book_name"]
        .nunique()
        .reset_index(name="books_covered")
        .sort_values("books_covered", ascending=False)
    )
    fig = px.bar(
        author_diversity.head(20),
        x="books_covered",
        y="author",
        orientation="h",
        title="Top 20 Autores por Diversidade (Livros Cobertos)",
        color="books_covered",
        color_continuous_scale="Greens",
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

# Timeline
st.subheader("Timeline dos Autores")
df_timeline = df_with.copy()
df_timeline["year"] = df_timeline["period"].apply(parse_period_year)
df_timeline = df_timeline.dropna(subset=["year"])

if not df_timeline.empty:
    author_periods = (
        df_timeline.groupby("author")
        .agg(year_min=("year", "min"), year_max=("year", "max"), count=("year", "size"))
        .reset_index()
        .sort_values("year_min")
    )
    top_authors = author_periods.nlargest(30, "count")

    fig = go.Figure()
    for _, row in top_authors.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["year_min"], row["year_max"]],
                y=[row["author"], row["author"]],
                mode="lines+markers",
                name=row["author"],
                line=dict(width=3),
                hovertemplate=(
                    f"{row['author']}: AD{row['year_min']:.0f}-{row['year_max']:.0f}"
                    f" ({row['count']} comentarios)"
                ),
            )
        )
    fig.update_layout(
        title="Periodos dos 30 Autores Mais Prolificos",
        xaxis_title="Ano (AD)",
        showlegend=False,
        height=700,
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 4. Analise Textual
# ---------------------------------------------------------------------------
st.header("4. Analise Textual")

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        df_with,
        x="word_count",
        nbins=50,
        title="Distribuicao do Tamanho dos Comentarios (palavras)",
        labels={"word_count": "Palavras"},
    )
    fig.update_layout(yaxis_title="Frequencia")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    wc_stats = df_with["word_count"].describe()
    st.dataframe(
        pd.DataFrame(
            {
                "Estatistica": ["Media", "Mediana", "Desvio Padrao", "Min", "Max"],
                "Palavras": [
                    f"{wc_stats['mean']:.0f}",
                    f"{wc_stats['50%']:.0f}",
                    f"{wc_stats['std']:.0f}",
                    f"{wc_stats['min']:.0f}",
                    f"{wc_stats['max']:.0f}",
                ],
            }
        ),
        hide_index=True,
    )

    st.subheader("Comentarios Mais Longos")
    longest = df_with.nlargest(5, "word_count")[
        ["author", "book_name", "chapter", "verse", "word_count"]
    ]
    longest.columns = ["Autor", "Livro", "Cap", "Vers", "Palavras"]
    st.dataframe(longest, hide_index=True)

# ---------------------------------------------------------------------------
# 5. Analise Teologica (Enriched)
# ---------------------------------------------------------------------------
df_enriched = load_enriched()

if df_enriched is not None and not df_enriched.empty:
    st.header("5. Analise Teologica (Dados Enriquecidos)")
    st.caption("Baseado na camada 03_enriched — atualmente cobre Acts e John (PT-BR)")

    col1, col2 = st.columns(2)

    with col1:
        all_doctrines = []
        for docs in df_enriched["doctrines"]:
            if isinstance(docs, str) and docs:
                all_doctrines.extend(docs.split("|"))
        doctrine_counts = Counter(all_doctrines).most_common(15)
        if doctrine_counts:
            doc_df = pd.DataFrame(doctrine_counts, columns=["Doutrina", "Frequencia"])
            fig = px.bar(
                doc_df,
                x="Frequencia",
                y="Doutrina",
                orientation="h",
                title="Top 15 Doutrinas Teologicas",
                color="Frequencia",
                color_continuous_scale="Purples",
            )
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        methods = df_enriched["theological_method"].value_counts().reset_index()
        methods.columns = ["Metodo", "Contagem"]
        if not methods.empty:
            fig = px.pie(
                methods,
                values="Contagem",
                names="Metodo",
                title="Metodos Teologicos",
            )
            st.plotly_chart(fig, use_container_width=True)

    all_traditions = []
    for trads in df_enriched["traditions"]:
        if isinstance(trads, str) and trads:
            all_traditions.extend(trads.split("|"))
    trad_counts = Counter(all_traditions).most_common(10)
    if trad_counts:
        trad_df = pd.DataFrame(trad_counts, columns=["Tradicao", "Frequencia"])
        fig = px.bar(
            trad_df,
            x="Tradicao",
            y="Frequencia",
            title="Tradicoes Teologicas",
            color="Frequencia",
            color_continuous_scale="Oranges",
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 6. Cobertura do Pipeline
# ---------------------------------------------------------------------------
st.header("6. Cobertura do Pipeline")

datasets_dir = ROOT / "datasets" / "bible-commentaries-dataset"
if datasets_dir.exists():
    layers = {
        "00_raw": datasets_dir / "data" / "00_raw",
        "01_cleaned": datasets_dir / "data" / "01_cleaned",
        "02_translated": datasets_dir / "data" / "02_translated",
        "03_enriched": datasets_dir / "data" / "03_enriched",
    }

    layer_counts = {}
    for name, path in layers.items():
        if path.exists():
            count = len(list(path.rglob("*.json")))
            # Descontar manifests e configs
            count -= len(list(path.glob("*.json")))
            layer_counts[name] = max(count, 0)
        else:
            layer_counts[name] = 0

    col1, col2 = st.columns(2)

    with col1:
        pipeline_df = pd.DataFrame(
            [{"Camada": k, "Arquivos": v} for k, v in layer_counts.items()]
        )
        fig = px.bar(
            pipeline_df,
            x="Camada",
            y="Arquivos",
            title="Arquivos por Camada do Pipeline",
            color="Camada",
            text="Arquivos",
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        total_cleaned = layer_counts.get("01_cleaned", 1) or 1
        translated = layer_counts.get("02_translated", 0)
        enriched = layer_counts.get("03_enriched", 0)

        st.subheader("Progresso")
        st.progress(
            min(translated / total_cleaned, 1.0),
            text=f"Traducao: {translated}/{total_cleaned} ({translated / total_cleaned * 100:.1f}%)",
        )
        st.progress(
            min(enriched / total_cleaned, 1.0),
            text=f"Enriquecimento: {enriched}/{total_cleaned} ({enriched / total_cleaned * 100:.1f}%)",
        )

        remaining_translate = total_cleaned - translated
        remaining_enrich = total_cleaned - enriched
        cost_translate = remaining_translate * 0.001
        cost_enrich = remaining_enrich * 0.01

        st.subheader("Estimativa para Completar")
        st.write(f"- Traducao: ~{remaining_translate:,} restantes · ~US$ {cost_translate:.2f}")
        st.write(f"- Enriquecimento: ~{remaining_enrich:,} restantes · ~US$ {cost_enrich:.2f}")
        st.write(f"- **Total estimado: ~US$ {cost_translate + cost_enrich:.2f}**")
else:
    st.info("Execute `python sync.py` para ver a cobertura do pipeline.")
