"""
NEUU Analytics — Dashboard central dos datasets biblicos.
Entry point com st.navigation() para navegacao agrupada.
"""

import streamlit as st

st.set_page_config(
    page_title="NEUU Analytics",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Idioma global (session_state para persistir entre paginas)
# ---------------------------------------------------------------------------
if "language" not in st.session_state:
    st.session_state.language = "English"

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
from loading import show_loading
show_loading()

# ---------------------------------------------------------------------------
# Sidebar — Configuracoes globais
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="padding:1.2rem 0 1rem 0;border-bottom:1px solid #2A2D34;margin-bottom:0.5rem;">'
        '<div style="font-family:Inter,sans-serif;font-size:1.4rem;font-weight:700;letter-spacing:4px;color:#D4A853;">'
        'NEUU <span style="color:#5A5550;font-weight:300;font-size:1rem;">Analytics</span></div>'
        '<div style="font-size:0.6rem;color:#5A5550;letter-spacing:2px;text-transform:uppercase;margin-top:4px;">'
        'Nossa Essencia Uniao e Upgrade</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    is_pt = st.session_state.language == "Portugues"
    st.session_state.language = st.radio(
        "Idioma" if is_pt else "Language",
        ["English", "Portugues"],
        index=1 if is_pt else 0,
        horizontal=True,
        key="lang_radio",
    )
    is_pt = st.session_state.language == "Portugues"

    # Seletor de traducao biblica
    en_trans = ["KJV", "AKJV", "ASV", "BSB", "Darby", "DRC", "Geneva1599", "Webster", "YLT"]
    pt_trans = ["ACF", "ARA", "ARC", "AS21", "NAA", "NTLH", "NVI", "NVT"]
    filtered_trans = pt_trans if is_pt else en_trans
    default_trans = "ARA" if is_pt else "KJV"
    default_idx = filtered_trans.index(default_trans) if default_trans in filtered_trans else 0

    st.session_state.translation = st.selectbox(
        "Traducao" if is_pt else "Translation",
        filtered_trans,
        index=default_idx,
        key="translation_select",
        help="Versao usada para exibir texto dos versiculos" if is_pt else "Version used to display verse text",
    )

is_pt = st.session_state.language == "Portugues"

# ---------------------------------------------------------------------------
# Definir paginas com st.Page()
# ---------------------------------------------------------------------------
home = st.Page(
    "pages/home.py",
    title="Overview" if not is_pt else "Visao Geral",
    icon=":material/home:",
    default=True,
)

explorer = st.Page(
    "pages/0_explorer.py",
    title="Verse Explorer" if not is_pt else "Explorador de Versiculos",
    icon=":material/search:",
)

commentaries = st.Page(
    "pages/1_commentaries.py",
    title="Commentaries" if not is_pt else "Comentarios",
    icon=":material/menu_book:",
)

crossrefs = st.Page(
    "pages/2_crossrefs.py",
    title="Cross-References" if not is_pt else "Referencias Cruzadas",
    icon=":material/link:",
)

bibletext = st.Page(
    "pages/3_bibletext.py",
    title="Bible Text" if not is_pt else "Texto Biblico",
    icon=":material/auto_stories:",
)

gazetteers = st.Page(
    "pages/4_gazetteers.py",
    title="Gazetteers" if not is_pt else "Dicionario Biblico",
    icon=":material/library_books:",
)

# ---------------------------------------------------------------------------
# Navegacao agrupada
# ---------------------------------------------------------------------------
section_explorer = "Explorer" if not is_pt else "Explorador"
section_analytics = "Dataset Analytics" if not is_pt else "Analise de Datasets"

pg = st.navigation({
    "": [home],
    section_explorer: [explorer],
    section_analytics: [commentaries, crossrefs, bibletext, gazetteers],
})

pg.run()
