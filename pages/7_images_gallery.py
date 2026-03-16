"""
Galeria de Imagens Biblicas — navegacao visual pelo dataset de pinturas.
Filtros por artista, estilo e tag com grid de imagens do HuggingFace.
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

title = "Galeria de Pinturas Biblicas" if is_pt else "Bible Paintings Gallery"
st.title(title)
st.caption(
    "Navegue pelas 16.914 pinturas religiosas do WikiArt"
    if is_pt else
    "Browse 16,914 religious paintings from WikiArt"
)

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
ITEMS_PER_PAGE = 20

col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])

with col_f1:
    artists_sorted = sorted(df["artist"].dropna().unique())
    selected_artist = st.selectbox(
        "Artista" if is_pt else "Artist",
        options=[""] + artists_sorted,
        index=0,
        format_func=lambda x: ("Todos" if is_pt else "All") if x == "" else x,
    )

with col_f2:
    # Collect unique styles
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
        "Buscar tag" if is_pt else "Search tag",
        placeholder="Ex: Jesus, Mary, crucifixion...",
    )

with col_f4:
    sort_options = {
        "fame": "Mais Famosas" if is_pt else "Most Famous",
        "aesthetic": "Mais Belas" if is_pt else "Most Beautiful",
        "recent": "Mais Recentes" if is_pt else "Most Recent",
        "oldest": "Mais Antigas" if is_pt else "Oldest First",
    }
    sort_by = st.selectbox(
        "Ordenar" if is_pt else "Sort by",
        options=list(sort_options.keys()),
        format_func=lambda x: sort_options[x],
    )

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
filtered = df.copy()

if selected_artist:
    filtered = filtered[filtered["artist"] == selected_artist]

if selected_styles:
    mask = filtered["styles"].dropna().apply(
        lambda s: any(style in s.split("|") for style in selected_styles)
    )
    # Reindex mask to align with filtered, filling missing with False
    mask = mask.reindex(filtered.index, fill_value=False)
    filtered = filtered[mask]

if tag_search.strip():
    search_lower = tag_search.strip().lower()
    mask = filtered["tags"].fillna("").str.lower().str.contains(search_lower, regex=False)
    filtered = filtered[mask]

# Sort
if sort_by == "fame" and "fame_score" in filtered.columns:
    filtered = filtered.sort_values("fame_score", ascending=False)
elif sort_by == "aesthetic":
    filtered = filtered.sort_values("aesthetic", ascending=False)
elif sort_by == "recent":
    filtered = filtered.sort_values("completion", ascending=False, na_position="last")
elif sort_by == "oldest":
    filtered = filtered.sort_values("completion", ascending=True, na_position="last")

total_filtered = len(filtered)
st.markdown(
    f"**{total_filtered:,}** {'pinturas encontradas' if is_pt else 'paintings found'}"
)

if total_filtered == 0:
    st.info(
        "Nenhuma pintura corresponde aos filtros selecionados."
        if is_pt else
        "No paintings match the selected filters."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
total_pages = max(1, (total_filtered + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

if "gallery_page" not in st.session_state:
    st.session_state.gallery_page = 1

# Reset page when filters change
filter_key = f"{selected_artist}|{'|'.join(selected_styles)}|{tag_search}|{sort_by}"
if st.session_state.get("_gallery_filter_key") != filter_key:
    st.session_state.gallery_page = 1
    st.session_state._gallery_filter_key = filter_key

page = st.session_state.gallery_page
if page > total_pages:
    page = total_pages
    st.session_state.gallery_page = page

start_idx = (page - 1) * ITEMS_PER_PAGE
end_idx = min(start_idx + ITEMS_PER_PAGE, total_filtered)
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

        # Caption with title, artist, year
        caption_parts = [
            f'<div style="font-weight:600;color:#E8E0D4;font-size:0.85rem;'
            f'line-height:1.3;margin-top:4px;">{title_text}</div>',
            f'<div style="color:#D4A853;font-size:0.75rem;">{artist_text}</div>',
        ]
        if year_text:
            caption_parts.append(
                f'<div style="color:#8B8072;font-size:0.7rem;">{year_text}</div>'
            )
        st.markdown("".join(caption_parts), unsafe_allow_html=True)
        st.markdown("")  # spacer between rows

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
