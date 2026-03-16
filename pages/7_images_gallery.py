"""
Galeria de Imagens Biblicas — navegacao visual pelo dataset de pinturas.
Ordenado por fama, estetica ou periodo. Clique no artista para filtrar.
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
    # Show active artist filter with clear button
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
        "16.914 pinturas religiosas ordenadas por relevancia"
        if is_pt else
        "16,914 religious paintings sorted by relevance"
    )

# ---------------------------------------------------------------------------
# Sort control
# ---------------------------------------------------------------------------
ITEMS_PER_PAGE = 20

sort_options = {
    "fame": "Mais Famosas" if is_pt else "Most Famous",
    "aesthetic": "Mais Belas" if is_pt else "Most Beautiful",
    "recent": "Mais Recentes" if is_pt else "Most Recent",
    "oldest": "Mais Antigas" if is_pt else "Oldest First",
}

sort_by = st.radio(
    "Ordenar por" if is_pt else "Sort by",
    options=list(sort_options.keys()),
    format_func=lambda x: sort_options[x],
    horizontal=True,
)

# ---------------------------------------------------------------------------
# Filter by artist + Sort
# ---------------------------------------------------------------------------
sorted_df = df.copy()

if active_artist:
    sorted_df = sorted_df[sorted_df["artist"] == active_artist]

if sort_by == "fame" and "fame_score" in sorted_df.columns:
    sorted_df = sorted_df.sort_values("fame_score", ascending=False)
elif sort_by == "aesthetic":
    sorted_df = sorted_df.sort_values("aesthetic", ascending=False)
elif sort_by == "recent":
    sorted_df = sorted_df.sort_values("completion", ascending=False, na_position="last")
elif sort_by == "oldest":
    sorted_df = sorted_df.sort_values("completion", ascending=True, na_position="last")

total = len(sorted_df)
if not active_artist:
    st.markdown(
        f"**{total:,}** {'pinturas' if is_pt else 'paintings'}"
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

# Reset page when sort changes
state_key = f"{sort_by}|{active_artist or ''}"
if st.session_state.get("_gallery_state") != state_key:
    st.session_state.gallery_page = 1
    st.session_state._gallery_state = state_key

page = st.session_state.gallery_page
if page > total_pages:
    page = total_pages
    st.session_state.gallery_page = page

start_idx = (page - 1) * ITEMS_PER_PAGE
end_idx = min(start_idx + ITEMS_PER_PAGE, total)
page_data = sorted_df.iloc[start_idx:end_idx]

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
# Image Grid (4 columns)
# ---------------------------------------------------------------------------
grid_cols = st.columns(4)

for i, (_, row) in enumerate(page_data.iterrows()):
    col = grid_cols[i % 4]
    with col:
        image_url = row.get("hf_image_url", "")
        title_text = row.get("title", "Untitled") or "Untitled"
        artist_text = row.get("artist", "Unknown") or "Unknown"
        year_text = ""
        completion = row.get("completion")
        if pd.notna(completion) and int(completion) >= 100:
            year_text = str(int(completion))

        if image_url:
            st.markdown(
                f'<div style="border-radius:8px;overflow:hidden;background:#1A1D24;'
                f'border:1px solid #2A2D34;min-height:180px;">'
                f'<img src="{image_url}" style="width:100%;display:block;border-radius:8px;"'
                f' onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
                f'<div style="display:none;height:180px;align-items:center;justify-content:center;'
                f'color:#5A5550;font-size:0.8rem;">Uploading...</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Title
        st.markdown(
            f'<div style="font-weight:600;color:#E8E0D4;font-size:0.85rem;'
            f'line-height:1.3;margin-top:4px;">{title_text}</div>',
            unsafe_allow_html=True,
        )

        # Artist name as clickable button
        if st.button(
            artist_text,
            key=f"artist_{row.get('key', i)}",
            type="tertiary",
        ):
            st.session_state.gallery_artist = artist_text
            st.session_state.gallery_page = 1
            st.rerun()

        # Year
        if year_text:
            st.markdown(
                f'<div style="color:#8B8072;font-size:0.7rem;margin-top:-8px;">{year_text}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("")  # spacer

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
