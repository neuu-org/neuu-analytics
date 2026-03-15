"""
Pagina de analise do dataset Bible Text.
17 traducoes biblicas (9 EN + 8 PT) em formato estruturado.
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PARQUET = DATA_DIR / "bibletext.parquet"

st.set_page_config(page_title="Bible Text | NEUU Analytics", page_icon="📜", layout="wide")

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E8E0D4",
)

if not PARQUET.exists():
    st.info("Dados nao encontrados. Execute `python sync.py bibletext`.")
    st.stop()

con = duckdb.connect()


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{PARQUET}'").df()


df = load_data()
df["word_count"] = df["text"].str.split().str.len()

st.title("📜 Bible Text — Analise")
st.caption("17 traducoes biblicas em formato estruturado (9 EN + 8 PT)")

# ---------------------------------------------------------------------------
# 1. Visao Geral
# ---------------------------------------------------------------------------
st.header("1. Visao Geral")

total_verses = len(df)
translations = df["translation"].nunique()
languages = df["language"].nunique()
books = df["book"].nunique()
avg_words = df["word_count"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Versiculos", f"{total_verses:,}")
c2.metric("Traducoes", translations)
c3.metric("Idiomas", languages)
c4.metric("Livros (unicos)", books)
c5.metric("Media palavras/verso", f"{avg_words:.0f}")

col1, col2 = st.columns(2)

with col1:
    lang_counts = df.groupby("language")["translation"].nunique().reset_index(name="count")
    lang_counts["language"] = lang_counts["language"].map(
        {"english": "English", "portuguese": "Portuguese"}
    ).fillna(lang_counts["language"])
    fig = px.pie(
        lang_counts, values="count", names="language",
        title="Traducoes por Idioma",
        color_discrete_sequence=["#636EFA", "#00CC96"],
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    trans_counts = (
        df.groupby(["translation", "language"])
        .size()
        .reset_index(name="verses")
        .sort_values("verses", ascending=True)
    )
    fig = px.bar(
        trans_counts, x="verses", y="translation",
        orientation="h", color="language",
        title="Versiculos por Traducao",
        color_discrete_map={"english": "#636EFA", "portuguese": "#00CC96"},
        labels={"verses": "Versiculos", "translation": "Traducao", "language": "Idioma"},
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 2. Cobertura por Traducao
# ---------------------------------------------------------------------------
st.header("2. Cobertura por Traducao")
st.caption("Quais livros cada traducao cobre")

coverage = df.groupby(["translation", "book"]).size().reset_index(name="verses")
coverage_pivot = coverage.pivot(index="translation", columns="book", values="verses").fillna(0)

# Mostrar como heatmap simplificado (books com mais cobertura)
top_books = coverage.groupby("book")["verses"].sum().nlargest(20).index.tolist()
coverage_small = coverage_pivot[top_books] if all(b in coverage_pivot.columns for b in top_books) else coverage_pivot.iloc[:, :20]

fig = px.imshow(
    (coverage_small > 0).astype(int),
    title="Cobertura de Livros por Traducao (Top 20 livros)",
    labels=dict(x="Livro", y="Traducao", color="Presente"),
    aspect="auto",
    color_continuous_scale=["#1A1D24", "#D4A853"],
)
fig.update_layout(**PLOTLY_LAYOUT, height=500)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Analise Textual Comparativa
# ---------------------------------------------------------------------------
st.header("3. Analise Textual Comparativa")

col1, col2 = st.columns(2)

with col1:
    wc_by_trans = (
        df.groupby("translation")["word_count"]
        .mean()
        .reset_index(name="avg_words")
        .sort_values("avg_words", ascending=True)
    )
    fig = px.bar(
        wc_by_trans, x="avg_words", y="translation",
        orientation="h",
        title="Media de Palavras por Versiculo (por Traducao)",
        color="avg_words",
        color_continuous_scale=["#2A2D34", "#D4A853"],
        labels={"avg_words": "Palavras (media)", "translation": "Traducao"},
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.histogram(
        df, x="word_count", nbins=50,
        title="Distribuicao do Tamanho dos Versiculos",
        labels={"word_count": "Palavras"},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Frequencia")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 4. Comparador de Versiculos
# ---------------------------------------------------------------------------
st.header("4. Comparador de Versiculos")
st.caption("Compare o mesmo versiculo em diferentes traducoes")

# Pegar livros em ingles para o seletor
en_books = sorted(df[df["language"] == "english"]["book"].unique())

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    comp_book = st.selectbox("Livro", en_books, index=en_books.index("John") if "John" in en_books else 0, key="comp_book")
with col2:
    comp_chapters = sorted(df[(df["book"] == comp_book)]["chapter"].unique())
    comp_chapter = st.selectbox("Capitulo", comp_chapters, key="comp_ch")
with col3:
    comp_verses = sorted(df[(df["book"] == comp_book) & (df["chapter"] == comp_chapter)]["verse"].unique())
    comp_verse = st.selectbox("Versiculo", comp_verses, key="comp_v")

# Buscar em todas as traducoes
verse_texts = df[
    (df["book"] == comp_book) & (df["chapter"] == comp_chapter) & (df["verse"] == comp_verse)
].sort_values(["language", "translation"])

if not verse_texts.empty:
    st.markdown(
        f'<div style="font-family:Crimson Pro,serif;font-size:1.4rem;color:#D4A853;'
        f'margin:16px 0 8px 0;">{comp_book} {comp_chapter}:{comp_verse}</div>',
        unsafe_allow_html=True,
    )

    for _, row in verse_texts.iterrows():
        lang_icon = "🇬🇧" if row["language"] == "english" else "🇧🇷"
        st.markdown(
            f'<div style="background:#1A1D24;border:1px solid #2A2D34;border-radius:8px;'
            f'padding:14px 18px;margin-bottom:8px;">'
            f'<span style="font-weight:600;color:#D4A853;">{lang_icon} {row["translation"]}</span>'
            f'<div style="font-family:Crimson Pro,serif;font-size:1.05rem;line-height:1.7;'
            f'color:#E8E0D4;margin-top:8px;">'
            f'&ldquo;{row["text"]}&rdquo;</div></div>',
            unsafe_allow_html=True,
        )
else:
    st.info("Versiculo nao encontrado nesta traducao.")

# ---------------------------------------------------------------------------
# 5. Livros por Tamanho
# ---------------------------------------------------------------------------
st.header("5. Livros por Tamanho")

# Usar KJV como referencia
kjv_books = df[df["translation"] == "KJV"].groupby("book").agg(
    chapters=("chapter", "nunique"),
    verses=("verse", "count"),
    words=("word_count", "sum"),
).reset_index().sort_values("verses", ascending=False)

if not kjv_books.empty:
    fig = px.bar(
        kjv_books, x="book", y="verses",
        title="Versiculos por Livro (KJV como referencia)",
        color="words",
        color_continuous_scale="Viridis",
        labels={"book": "Livro", "verses": "Versiculos", "words": "Total palavras"},
    )
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
