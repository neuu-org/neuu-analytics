"""
Galeria de Imagens Biblicas — navegacao visual pelo dataset de pinturas.
Clique no artista para filtrar. Busca por titulo ou tag.
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from loading import show_loading

show_loading()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IMAGES_FILE = DATA_DIR / "images.parquet"

if not IMAGES_FILE.exists():
    st.info("Dados nao encontrados. Execute `python sync.py images`.")
    st.stop()

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_images(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{IMAGES_FILE}'").df()


df = load_images(IMAGES_FILE.stat().st_mtime)

# ---------------------------------------------------------------------------
# Artist filter via session state (set when user clicks an artist name)
# ---------------------------------------------------------------------------
if "gallery_artist" not in st.session_state:
    st.session_state.gallery_artist = None

active_artist = st.session_state.gallery_artist

# Header
title = "Galeria de Pinturas Biblicas" if is_pt else "Bible Paintings Gallery"
st.title(title)

if active_artist:
    count = len(df[df["artist"] == active_artist])
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.markdown(
            f'<div style="font-size:1.1rem;color:#D4A853;font-weight:600;">'
            f'{active_artist} <span style="color:#8B8072;font-weight:400;">'
            f'({count} {"pinturas" if is_pt else "paintings"})</span></div>',
            unsafe_allow_html=True,
        )
    with col_h2:
        if st.button("Mostrar todas" if is_pt else "Show all", type="secondary"):
            st.session_state.gallery_artist = None
            st.session_state.gallery_page = 1
            st.rerun()
else:
    st.caption(
        "16.914 pinturas religiosas — clique no artista para filtrar"
        if is_pt else
        "16,914 religious paintings — click an artist to filter"
    )

# ---------------------------------------------------------------------------
# Filters: Artist, Style, Search
# ---------------------------------------------------------------------------
ITEMS_PER_PAGE = 20

col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    artists_sorted = sorted(df["artist"].dropna().unique())
    default_idx = 0
    if active_artist and active_artist in artists_sorted:
        default_idx = artists_sorted.index(active_artist) + 1
    selected_artist = st.selectbox(
        "Artista" if is_pt else "Artist",
        options=[""] + artists_sorted,
        index=default_idx,
        format_func=lambda x: ("Todos" if is_pt else "All") if x == "" else x,
    )

with col_f2:
    all_styles = (
        df["styles"].dropna()
        .str.split("|").explode().str.strip()
        .replace("", pd.NA).dropna()
        .unique()
    )
    styles_sorted = sorted(all_styles)
    selected_styles = st.multiselect(
        "Estilos" if is_pt else "Styles",
        options=styles_sorted,
    )

with col_f3:
    tag_search = st.text_input(
        "Buscar" if is_pt else "Search",
        placeholder="Ex: Jesus, crucifixion, Doré...",
    )

# ---------------------------------------------------------------------------
# Apply filters + Sort by fame
# ---------------------------------------------------------------------------
filtered = df.copy()

# Artist: prefer clicked artist over selectbox
artist_filter = active_artist or selected_artist
if artist_filter:
    filtered = filtered[filtered["artist"] == artist_filter]

if selected_styles:
    mask = filtered["styles"].dropna().apply(
        lambda s: any(style in s.split("|") for style in selected_styles)
    )
    mask = mask.reindex(filtered.index, fill_value=False)
    filtered = filtered[mask]

if tag_search.strip():
    search_lower = tag_search.strip().lower()
    mask = (
        filtered["tags"].fillna("").str.lower().str.contains(search_lower, regex=False)
        | filtered["title"].fillna("").str.lower().str.contains(search_lower, regex=False)
        | filtered["artist"].fillna("").str.lower().str.contains(search_lower, regex=False)
    )
    filtered = filtered[mask]

# Always sort by fame score
if "fame_score" in filtered.columns:
    filtered = filtered.sort_values("fame_score", ascending=False)

total = len(filtered)
st.markdown(
    f"**{total:,}** {'pinturas encontradas' if is_pt else 'paintings found'}"
)

if total == 0:
    st.info(
        "Nenhuma pintura encontrada." if is_pt else "No paintings found."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
total_pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

if "gallery_page" not in st.session_state:
    st.session_state.gallery_page = 1

# Reset page when filters change
state_key = f"{artist_filter or ''}|{'|'.join(selected_styles)}|{tag_search}"
if st.session_state.get("_gallery_state") != state_key:
    st.session_state.gallery_page = 1
    st.session_state._gallery_state = state_key

page = st.session_state.gallery_page
if page > total_pages:
    page = total_pages
    st.session_state.gallery_page = page

start_idx = (page - 1) * ITEMS_PER_PAGE
end_idx = min(start_idx + ITEMS_PER_PAGE, total)
page_data = filtered.iloc[start_idx:end_idx]

# Page controls
nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
with nav_col1:
    if st.button("< " + ("Anterior" if is_pt else "Previous"), disabled=page <= 1):
        st.session_state.gallery_page = page - 1
        st.rerun()
with nav_col2:
    st.markdown(
        f'<div style="text-align:center;color:#8B8072;padding-top:8px;">'
        f'{"Pagina" if is_pt else "Page"} {page} / {total_pages}</div>',
        unsafe_allow_html=True,
    )
with nav_col3:
    if st.button(("Proxima" if is_pt else "Next") + " >", disabled=page >= total_pages):
        st.session_state.gallery_page = page + 1
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------------------------
# Image detail dialog
# ---------------------------------------------------------------------------
@st.dialog(" ", width="large")
def show_image_detail(key: str):
    """Show full-size image with metadata in a modal dialog."""
    img_row = df[df["key"] == key]
    if img_row.empty:
        st.error("Imagem nao encontrada." if is_pt else "Image not found.")
        return
    r = img_row.iloc[0]

    url = r.get("hf_image_url", "")
    t = r.get("title", "Untitled") or "Untitled"
    a = r.get("artist", "Unknown") or "Unknown"
    year = ""
    if pd.notna(r.get("completion")) and int(r["completion"]) >= 100:
        year = str(int(r["completion"]))
    styles = r.get("styles", "") or ""
    genres = r.get("genres", "") or ""
    tags = r.get("tags", "") or ""
    media = r.get("media", "") or ""

    # Title
    st.markdown(
        f'<div style="font-size:1.4rem;font-weight:700;color:#E8E0D4;">{t}</div>'
        f'<div style="font-size:1rem;color:#D4A853;margin-top:2px;">{a}'
        f'{" — " + year if year else ""}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Full image
    if url:
        st.image(url, width="stretch")

    # Metadata pills
    st.markdown("")
    meta_parts = []
    if styles:
        for s in styles.split("|"):
            if s.strip():
                meta_parts.append(("Estilo" if is_pt else "Style", s.strip()))
    if genres:
        for g in genres.split("|"):
            if g.strip():
                meta_parts.append(("Genero" if is_pt else "Genre", g.strip()))
    if media:
        for m in media.split("|"):
            if m.strip():
                meta_parts.append(("Material" if is_pt else "Media", m.strip()))

    if meta_parts:
        pills_html = " ".join(
            f'<span style="display:inline-block;padding:4px 12px;border-radius:20px;'
            f'font-size:0.75rem;margin:3px;background:rgba(212,168,83,0.12);'
            f'color:#D4A853;border:1px solid rgba(212,168,83,0.25);">'
            f'{val}</span>'
            for _, val in meta_parts
        )
        st.markdown(pills_html, unsafe_allow_html=True)

    if tags:
        tag_list = [t.strip() for t in tags.split("|") if t.strip()]
        if tag_list:
            tags_html = " ".join(
                f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;'
                f'font-size:0.7rem;margin:2px;background:rgba(139,128,114,0.15);'
                f'color:#8B8072;border:1px solid rgba(139,128,114,0.25);">'
                f'{t}</span>'
                for t in tag_list
            )
            st.markdown(tags_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Image Grid (4 columns)
# ---------------------------------------------------------------------------
grid_cols = st.columns(4)

for i, (_, row) in enumerate(page_data.iterrows()):
    col = grid_cols[i % 4]
    with col:
        image_url = row.get("hf_image_url", "")
        title_text = row.get("title", "Untitled") or "Untitled"
        artist_text = row.get("artist", "Unknown") or "Unknown"
        row_key = str(row.get("key", ""))
        year_text = ""
        completion = row.get("completion")
        if pd.notna(completion) and int(completion) >= 100:
            year_text = str(int(completion))

        # Image — click opens detail dialog
        if image_url:
            st.image(image_url, width="stretch")

        # Title — opens modal
        year_suffix = f" ({year_text})" if year_text else ""
        if st.button(
            title_text,
            key=f"detail_{row_key}_{i}",
            type="tertiary",
        ):
            show_image_detail(row_key)

        # Artist + year — filters by artist
        if st.button(
            artist_text + year_suffix,
            key=f"artist_{row_key}_{i}",
            type="tertiary",
        ):
            st.session_state.gallery_artist = artist_text
            st.session_state.gallery_page = 1
            st.rerun()

# Bottom pagination
st.markdown("---")
bot_col1, bot_col2, bot_col3 = st.columns([1, 2, 1])
with bot_col1:
    if st.button("< " + ("Anterior" if is_pt else "Previous"), key="prev_bot", disabled=page <= 1):
        st.session_state.gallery_page = page - 1
        st.rerun()
with bot_col2:
    st.markdown(
        f'<div style="text-align:center;color:#8B8072;padding-top:8px;">'
        f'{"Pagina" if is_pt else "Page"} {page} / {total_pages}</div>',
        unsafe_allow_html=True,
    )
with bot_col3:
    if st.button(("Proxima" if is_pt else "Next") + " >", key="next_bot", disabled=page >= total_pages):
        st.session_state.gallery_page = page + 1
        st.rerun()
