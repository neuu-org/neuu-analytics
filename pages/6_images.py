"""
Pagina de analise do dataset Bible Images.
16,914 pinturas religiosas de 1,892 artistas (WikiArt).
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
IMAGES_FILE = DATA_DIR / "images.parquet"

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E8E0D4",
)

if not IMAGES_FILE.exists():
    st.info("Dados nao encontrados. Execute `python sync.py images`.")
    st.stop()

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_images(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{IMAGES_FILE}'").df()


df = load_images(IMAGES_FILE.stat().st_mtime)

title = "Pinturas Biblicas -- Analise" if is_pt else "Bible Paintings -- Analysis"
st.title(title)
st.caption(
    "16.914 pinturas religiosas de 1.892 artistas extraidas do WikiArt"
    if is_pt else
    "16,914 religious paintings from 1,892 artists extracted from WikiArt"
)


# ============================================================
# Helper: explode pipe-separated columns
# ============================================================
def explode_col(series: pd.Series) -> pd.Series:
    """Split pipe-separated strings and explode into individual rows."""
    return series.dropna().str.split("|").explode().str.strip().replace("", pd.NA).dropna()


# ============================================================
# 1. OVERVIEW
# ============================================================
st.header("1. " + ("Visao Geral" if is_pt else "Overview"))

total_images = len(df)
unique_artists = df["artist"].nunique()
all_styles = explode_col(df["styles"])
unique_styles = all_styles.nunique()
avg_aesthetic = df["aesthetic"].mean()

# Time span from completion year
df_with_year = df.dropna(subset=["completion"])
df_with_year = df_with_year[df_with_year["completion"] >= 100]  # filter out invalid years
if not df_with_year.empty:
    min_year = int(df_with_year["completion"].min())
    max_year = int(df_with_year["completion"].max())
    time_span = f"{min_year} - {max_year}"
else:
    time_span = "N/A"

cols = st.columns(5)
cols[0].metric("Imagens" if is_pt else "Images", f"{total_images:,}")
cols[1].metric("Artistas" if is_pt else "Artists", f"{unique_artists:,}")
cols[2].metric("Estilos" if is_pt else "Styles", f"{unique_styles:,}")
cols[3].metric("Estetica Media" if is_pt else "Avg Aesthetic", f"{avg_aesthetic:.2f}")
cols[4].metric("Periodo" if is_pt else "Time Span", time_span)

# ============================================================
# 2. BY ARTIST
# ============================================================
st.header("2. " + ("Por Artista" if is_pt else "By Artist"))

artist_stats = df.groupby("artist").agg(
    count=("key", "count"),
    avg_aesthetic=("aesthetic", "mean"),
    primary_style=("styles", lambda x: x.dropna().str.split("|").explode().str.strip().mode().iloc[0] if not x.dropna().empty and len(x.dropna().str.split("|").explode().str.strip().mode()) > 0 else ""),
).reset_index()
artist_stats["avg_aesthetic"] = artist_stats["avg_aesthetic"].round(2)

top20_artists = artist_stats.nlargest(20, "count")

col1, col2 = st.columns([1, 1])

with col1:
    fig = px.bar(
        top20_artists.sort_values("count", ascending=True),
        x="count", y="artist",
        orientation="h",
        title="Top 20 Artistas por Quantidade" if is_pt else "Top 20 Artists by Count",
        labels={"count": "Pinturas" if is_pt else "Paintings", "artist": ""},
        color_discrete_sequence=["#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=550)
    st.plotly_chart(fig, width="stretch")

with col2:
    st.dataframe(
        top20_artists[["artist", "count", "avg_aesthetic", "primary_style"]].rename(
            columns={
                "artist": "Artista" if is_pt else "Artist",
                "count": "Pinturas" if is_pt else "Paintings",
                "avg_aesthetic": "Estetica Media" if is_pt else "Avg Aesthetic",
                "primary_style": "Estilo Principal" if is_pt else "Primary Style",
            }
        ),
        width="stretch", hide_index=True, height=550,
    )

# ============================================================
# 3. BY STYLE
# ============================================================
st.header("3. " + ("Por Estilo" if is_pt else "By Style"))

style_counts = all_styles.value_counts().reset_index()
style_counts.columns = ["style", "count"]

# Top 15 + Other for pie
top15_styles = style_counts.head(15).copy()
other_count = style_counts.iloc[15:]["count"].sum() if len(style_counts) > 15 else 0
if other_count > 0:
    top15_styles = pd.concat([
        top15_styles,
        pd.DataFrame([{"style": "Other" if not is_pt else "Outros", "count": other_count}]),
    ], ignore_index=True)

col1, col2 = st.columns(2)

with col1:
    fig = px.pie(
        top15_styles,
        values="count", names="style",
        title="Distribuicao de Estilos" if is_pt else "Style Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=450)
    st.plotly_chart(fig, width="stretch")

with col2:
    top20_styles = style_counts.head(20)
    fig = px.bar(
        top20_styles.sort_values("count", ascending=True),
        x="count", y="style",
        orientation="h",
        title="Top 20 Estilos" if is_pt else "Top 20 Styles",
        labels={"count": "Pinturas" if is_pt else "Paintings", "style": ""},
        color="count",
        color_continuous_scale=["#2A2D34", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=450)
    st.plotly_chart(fig, width="stretch")

# ============================================================
# 4. BY GENRE
# ============================================================
st.header("4. " + ("Por Genero" if is_pt else "By Genre"))

all_genres = explode_col(df["genres"])
genre_counts = all_genres.value_counts().reset_index()
genre_counts.columns = ["genre", "count"]
top20_genres = genre_counts.head(20)

fig = px.bar(
    top20_genres.sort_values("count", ascending=True),
    x="count", y="genre",
    orientation="h",
    title="Generos mais Frequentes" if is_pt else "Most Frequent Genres",
    labels={"count": "Pinturas" if is_pt else "Paintings", "genre": ""},
    color="count",
    color_continuous_scale=["#2A2D34", "#D4A853"],
)
fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=500)
st.plotly_chart(fig, width="stretch")

# ============================================================
# 5. TIMELINE
# ============================================================
st.header("5. " + ("Linha do Tempo" if is_pt else "Timeline"))

if not df_with_year.empty:
    # Group by century
    df_century = df_with_year.copy()
    df_century["century"] = (df_century["completion"] // 100) * 100
    century_counts = df_century.groupby("century").size().reset_index(name="count")
    century_counts["century_label"] = century_counts["century"].apply(
        lambda c: f"{int(c)}s"
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            century_counts,
            x="century", y="count",
            title="Pinturas por Seculo" if is_pt else "Paintings by Century",
            labels={"century": "Seculo" if is_pt else "Century", "count": "Pinturas" if is_pt else "Paintings"},
            markers=True,
            color_discrete_sequence=["#D4A853"],
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=400)
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = px.histogram(
            df_with_year, x="completion", nbins=60,
            title="Distribuicao por Ano de Conclusao" if is_pt else "Distribution by Completion Year",
            labels={"completion": "Ano" if is_pt else "Year"},
            color_discrete_sequence=["#D4A853"],
        )
        fig.update_layout(
            **PLOTLY_LAYOUT,
            yaxis_title="Frequencia" if is_pt else "Frequency",
            height=400,
        )
        st.plotly_chart(fig, width="stretch")
else:
    st.info("Dados de ano de conclusao nao disponiveis." if is_pt else "Completion year data not available.")

# ============================================================
# 6. TAGS
# ============================================================
st.header("6. Tags")

all_tags = explode_col(df["tags"])
tag_counts = all_tags.value_counts()

# Tag pills (top 30)
st.subheader("Top 30 Tags")
top30_tags = tag_counts.head(30)
tags_html = " ".join(
    f'<span class="tag" style="display:inline-block;padding:4px 12px;border-radius:20px;'
    f'font-size:0.8rem;font-weight:500;margin:3px;'
    f'background:rgba(212,168,83,0.12);color:#D4A853;'
    f'border:1px solid rgba(212,168,83,0.25);">'
    f'{tag} <span style="color:#8B8072;font-size:0.7rem;">({count:,})</span></span>'
    for tag, count in top30_tags.items()
)
st.markdown(tags_html, unsafe_allow_html=True)

st.markdown("")  # spacer

# Bar chart top 20 tags
top20_tags = tag_counts.head(20).reset_index()
top20_tags.columns = ["tag", "count"]

fig = px.bar(
    top20_tags.sort_values("count", ascending=True),
    x="count", y="tag",
    orientation="h",
    title="Top 20 Tags",
    labels={"count": "Pinturas" if is_pt else "Paintings", "tag": ""},
    color="count",
    color_continuous_scale=["#2A2D34", "#D4A853"],
)
fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=500)
st.plotly_chart(fig, width="stretch")
