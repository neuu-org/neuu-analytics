"""
Estudos Tematicos — Investigacoes teologicas curadas com validacao humana,
redes de cross-refs, vozes patristicas e notas academicas.
"""

import html
import json
import math
import re
import unicodedata
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

from book_names import (
    CROSSREF_BOOK_NAMES,
    EN_TO_PT_BOOK,
    PT_TO_EN_BOOK,
    book_name_for_translation,
)
from loading import show_loading

show_loading()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG_PATH = ROOT / "config.yaml"
BIBLETEXT_PARQUET = DATA_DIR / "bibletext.parquet"

con = duckdb.connect()


def _resolve_experiments_path() -> Path:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    base = cfg.get("experiments", {}).get("base_path", "../../bible-hybrid-search/experiments")
    return (ROOT / base).resolve()


EXPERIMENTS = _resolve_experiments_path()

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap');

    .study-card {
        background: #1A1D24;
        border: 1px solid #2A2D34;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 8px;
        transition: border-color 0.3s ease;
    }
    .study-card:hover { border-color: rgba(212, 168, 83, 0.5); }

    .study-title {
        font-family: 'Crimson Pro', serif;
        font-size: 1.2rem;
        font-weight: 600;
        color: #D4A853;
        margin-bottom: 8px;
    }

    .diff-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .diff-baseline { background:rgba(76,175,80,0.15); color:#4CAF50; border:1px solid rgba(76,175,80,0.3); }
    .diff-medium { background:rgba(33,150,243,0.15); color:#2196F3; border:1px solid rgba(33,150,243,0.3); }
    .diff-medium_hard { background:rgba(255,152,0,0.15); color:#FF9800; border:1px solid rgba(255,152,0,0.3); }
    .diff-hard { background:rgba(239,85,59,0.15); color:#EF553B; border:1px solid rgba(239,85,59,0.3); }
    .diff-extreme { background:rgba(171,99,250,0.15); color:#AB63FA; border:1px solid rgba(171,99,250,0.3); }

    .type-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 500;
        background: rgba(99, 110, 250, 0.12);
        color: #636EFA;
        border: 1px solid rgba(99, 110, 250, 0.25);
        margin-right: 6px;
    }

    .validated-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #D4A853;
        margin-right: 6px;
        vertical-align: middle;
    }
    .validated-dot.pending {
        background: #5A5550;
    }

    .card-meta {
        font-size: 0.8rem;
        color: #8B8072;
        margin-top: 8px;
    }

    .verse-ref {
        font-family: 'Crimson Pro', serif;
        font-size: 1.6rem;
        font-weight: 600;
        color: #D4A853;
        margin-bottom: 4px;
    }
    .commentary-card {
        background: #1A1D24;
        border: 1px solid #2A2D34;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 12px;
    }
    .tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 500;
        margin: 2px 3px;
        background: rgba(212, 168, 83, 0.12);
        color: #D4A853;
        border: 1px solid rgba(212, 168, 83, 0.25);
    }
    .tag-human {
        background: rgba(0, 204, 150, 0.12);
        color: #00CC96;
        border-color: rgba(0, 204, 150, 0.25);
    }
    .tag-manual {
        background: rgba(99, 110, 250, 0.12);
        color: #636EFA;
        border-color: rgba(99, 110, 250, 0.25);
    }
    .tag-enrichment {
        background: rgba(255, 152, 0, 0.12);
        color: #FF9800;
        border-color: rgba(255, 152, 0, 0.25);
    }
    .insight-box {
        background: rgba(212, 168, 83, 0.08);
        border-left: 3px solid #D4A853;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin: 12px 0;
    }
    .insight-box .theme {
        font-family: 'Crimson Pro', serif;
        font-style: italic;
        font-size: 1.05rem;
        color: #E8E0D4;
    }
    .insight-box .reflection {
        font-size: 0.9rem;
        color: #8B8072;
        margin-top: 8px;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #5A5550;
        margin: 16px 0 8px 0;
    }
    .candidate-card {
        background: #1A1D24;
        border: 1px dashed #2A2D34;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }
    .relevance-dots {
        display: inline-flex;
        gap: 4px;
        vertical-align: middle;
        margin-right: 8px;
    }
    .rel-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .rel-dot.filled { background: #D4A853; }
    .rel-dot.empty { background: #2A2D34; border: 1px solid #5A5550; }

    .hero-stat {
        text-align: center;
    }
    .hero-stat .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #D4A853;
    }
    .hero-stat .label {
        font-size: 0.75rem;
        color: #8B8072;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .author-card {
        background: #1A1D24;
        border-left: 3px solid #D4A853;
        border-radius: 0 10px 10px 0;
        padding: 16px 20px;
        margin-bottom: 10px;
    }
    .author-card .name {
        font-weight: 600;
        color: #D4A853;
        font-size: 1rem;
    }
    .author-card .period {
        color: #8B8072;
        font-size: 0.8rem;
        margin-left: 8px;
    }
    .author-card .quote {
        font-family: 'Crimson Pro', serif;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #E8E0D4;
        margin-top: 8px;
        font-style: italic;
    }
    .info-tip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 16px; height: 16px;
        border-radius: 50%;
        background: rgba(212, 168, 83, 0.15);
        color: #D4A853;
        font-size: 0.6rem;
        font-weight: 700;
        cursor: help;
        margin-left: 6px;
        vertical-align: middle;
        position: relative;
    }
    .info-tip .tip-text {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        background: #1A1D24;
        border: 1px solid #2A2D34;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.75rem;
        font-weight: 400;
        color: #E8E0D4;
        width: 280px;
        line-height: 1.5;
        z-index: 100;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        transition: opacity 0.2s;
        text-align: left;
    }
    .info-tip:hover .tip-text {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Idioma
# ---------------------------------------------------------------------------
selected_language = st.session_state.get("language", "English")
selected_translation = st.session_state.get("translation", "KJV")
is_pt = selected_language == "Portugues"

# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
DIFF_LABELS = {
    "baseline": ("Basico", "Baseline"),
    "medium": ("Medio", "Medium"),
    "medium_hard": ("Medio-Dificil", "Medium-Hard"),
    "hard": ("Dificil", "Hard"),
    "extreme": ("Extremo", "Extreme"),
}

DIFF_COLORS = {
    "baseline": "#4CAF50",
    "medium": "#2196F3",
    "medium_hard": "#FF9800",
    "hard": "#EF553B",
    "extreme": "#AB63FA",
}

TYPE_LABELS = {
    "abstract_concept": ("Conceito Abstrato", "Abstract Concept"),
    "typology": ("Tipologia", "Typology"),
    "metaphor": ("Metafora", "Metaphor"),
    "figure": ("Figura", "Figure"),
    "narrative": ("Narrativa", "Narrative"),
    "direct_phrase": ("Frase Direta", "Direct Phrase"),
    "contrast": ("Contraste", "Contrast"),
    "phrase_expansion": ("Expansao de Frase", "Phrase Expansion"),
    "vocabulary_variation": ("Variacao de Vocabulario", "Vocabulary Variation"),
    "famous_narrative": ("Narrativa Famosa", "Famous Narrative"),
    "famous_teaching": ("Ensino Famoso", "Famous Teaching"),
    "famous_phrase": ("Frase Famosa", "Famous Phrase"),
}


@st.cache_data(ttl=3600)
def load_queries() -> list[dict]:
    path = EXPERIMENTS / "queries" / "pilot_queries_v2.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600)
def load_gold_set() -> dict:
    path = EXPERIMENTS / "gold_set" / "gold_set_final.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["query_id"]: item for item in data}


@st.cache_data(ttl=3600)
def load_additions(query_id: str) -> dict | None:
    path = EXPERIMENTS / "queries" / "validations" / query_id / "additions.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _strip_accents(s: str) -> str:
    """Remove accents for fuzzy book name matching."""
    nfkd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _pt_book_to_en(book_pt: str) -> str:
    """Map Portuguese book name to English, handling accent variations."""
    if book_pt in PT_TO_EN_BOOK:
        return PT_TO_EN_BOOK[book_pt]
    stripped = _strip_accents(book_pt).lower()
    for pt, en in PT_TO_EN_BOOK.items():
        if _strip_accents(pt).lower() == stripped:
            return en
    return book_pt


def parse_verse_ref(ref: str) -> tuple[str, int, int]:
    """Parse 'Salmos 22:1' or 'Isaias 53:5' into (book_pt, chapter, verse)."""
    match = re.match(r"^(.+?)\s+(\d+):(\d+)(?:-\d+)?$", ref.strip())
    if match:
        return match.group(1), int(match.group(2)), int(match.group(3))
    return ref, 0, 0


def get_verse_text(book_pt: str, chapter: int, verse: int) -> str | None:
    """Fetch verse text from bibletext parquet."""
    if not BIBLETEXT_PARQUET.exists() or chapter == 0:
        return None
    en_name = _pt_book_to_en(book_pt)
    book = book_name_for_translation(en_name, selected_translation)
    try:
        result = con.sql(
            f"""
            SELECT text FROM '{BIBLETEXT_PARQUET}'
            WHERE book = '{book}' AND chapter = {chapter} AND verse = {verse}
              AND translation = '{selected_translation}'
            LIMIT 1
            """
        ).df()
        return result["text"].iloc[0] if not result.empty else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Evidence parsing helpers
# ---------------------------------------------------------------------------
def parse_crossref_edges(evidence_list: list[str]) -> list[tuple[str, int]]:
    """Extract (target_osis, votes) from evidence strings."""
    edges = []
    for ev in evidence_list:
        if not ev.lower().startswith("crossrefs"):
            continue
        # Patterns: "15v→1PE.2.24" or "3v->HAB.1.2" or "15v←ACT.8.32"
        matches = re.findall(r"(\d+)v[→\->←]+([A-Z0-9]+\.\d+\.\d+)", ev)
        for votes, target in matches:
            edges.append((target, int(votes)))
    return edges


def osis_to_friendly(osis: str) -> str:
    """Convert ISA.53.5 to Isaias 53:5 (or English equivalent)."""
    parts = osis.split(".")
    if len(parts) != 3:
        return osis
    book_osis, ch, vs = parts[0], parts[1], parts[2]
    en_name = CROSSREF_BOOK_NAMES.get(book_osis, book_osis)
    if is_pt:
        name = EN_TO_PT_BOOK.get(en_name, en_name)
    else:
        name = en_name
    return f"{name} {ch}:{vs}"


# ---------------------------------------------------------------------------
# Patristic authors database
# ---------------------------------------------------------------------------
PATRISTIC_AUTHORS = {
    "Policarpo": {"date": 155, "en": "Polycarp", "tradition": "Apostolic Father"},
    "Polycarp": {"date": 155, "en": "Polycarp", "tradition": "Apostolic Father"},
    "Ireneu": {"date": 180, "en": "Irenaeus", "tradition": "Church Father"},
    "Irenaeus": {"date": 180, "en": "Irenaeus", "tradition": "Church Father"},
    "Eusébio": {"date": 330, "en": "Eusebius", "tradition": "Church Father"},
    "Eusebius": {"date": 330, "en": "Eusebius", "tradition": "Church Father"},
    "Atanásio": {"date": 350, "en": "Athanasius", "tradition": "Church Father"},
    "Athanasius": {"date": 350, "en": "Athanasius", "tradition": "Church Father"},
    "Efrém Sírio": {"date": 370, "en": "Ephrem the Syrian", "tradition": "Church Father"},
    "Efrem": {"date": 370, "en": "Ephrem the Syrian", "tradition": "Church Father"},
    "Basílio": {"date": 370, "en": "Basil the Great", "tradition": "Church Father"},
    "Basil": {"date": 370, "en": "Basil the Great", "tradition": "Church Father"},
    "Gregório": {"date": 390, "en": "Gregory the Theologian", "tradition": "Church Father"},
    "Gregory": {"date": 390, "en": "Gregory the Theologian", "tradition": "Church Father"},
    "Ambrósio": {"date": 397, "en": "Ambrose of Milan", "tradition": "Church Father"},
    "Ambrose": {"date": 397, "en": "Ambrose of Milan", "tradition": "Church Father"},
    "Crisóstomo": {"date": 407, "en": "John Chrysostom", "tradition": "Church Father"},
    "Chrysostom": {"date": 407, "en": "John Chrysostom", "tradition": "Church Father"},
    "Jerônimo": {"date": 420, "en": "Jerome", "tradition": "Church Father"},
    "Jerome": {"date": 420, "en": "Jerome", "tradition": "Church Father"},
    "Agostinho": {"date": 430, "en": "Augustine of Hippo", "tradition": "Church Father"},
    "Augustine": {"date": 430, "en": "Augustine of Hippo", "tradition": "Church Father"},
    "Cirilo": {"date": 444, "en": "Cyril", "tradition": "Church Father"},
    "Cyril": {"date": 444, "en": "Cyril", "tradition": "Church Father"},
    "Haydock": {"date": 1849, "en": "George Leo Haydock", "tradition": "Catholic"},
    "Calvino": {"date": 1560, "en": "John Calvin", "tradition": "Reformed"},
    "Calvin": {"date": 1560, "en": "John Calvin", "tradition": "Reformed"},
    "Henry": {"date": 1710, "en": "Matthew Henry", "tradition": "Protestant"},
    "Barnes": {"date": 1840, "en": "Albert Barnes", "tradition": "Protestant"},
    "JFB": {"date": 1871, "en": "Jamieson, Fausset & Brown", "tradition": "Protestant"},
    "Spurgeon": {"date": 1880, "en": "C.H. Spurgeon", "tradition": "Protestant"},
    "White": {"date": 1900, "en": "Ellen White", "tradition": "Adventist"},
    "Andrew Murray": {"date": 1900, "en": "Andrew Murray", "tradition": "Protestant"},
    "Salvian": {"date": 480, "en": "Salvian of Marseilles", "tradition": "Church Father"},
    "Hipólito": {"date": 235, "en": "Hippolytus of Rome", "tradition": "Church Father"},
    "Hippolytus": {"date": 235, "en": "Hippolytus of Rome", "tradition": "Church Father"},
    "Pseudo-Dionísio": {"date": 500, "en": "Pseudo-Dionysius", "tradition": "Church Father"},
    "Macário": {"date": 391, "en": "Macarius", "tradition": "Church Father"},
}


def extract_authors_from_evidence(evidence_list: list[str]) -> list[dict]:
    """Find patristic/commentary authors mentioned in evidence strings."""
    found = {}
    for ev in evidence_list:
        if "commentaries" in ev.lower() or "ccel" in ev.lower() or "catena" in ev.lower():
            for name, info in PATRISTIC_AUTHORS.items():
                if name in ev and info["en"] not in found:
                    found[info["en"]] = {
                        "name": info["en"],
                        "date": info["date"],
                        "tradition": info["tradition"],
                        "evidence": ev,
                    }
    return sorted(found.values(), key=lambda x: x["date"])


# ---------------------------------------------------------------------------
# Tooltip helper
# ---------------------------------------------------------------------------
_TIPS = {
    "votes": (
        "Votos indicam quantas fontes independentes de referencias cruzadas (OpenBible, TSK, e outras) "
        "concordam que esses dois versiculos estao conectados. Mais votos = maior consenso entre estudiosos.",
        "Votes indicate how many independent cross-reference sources (OpenBible, TSK, and others) "
        "agree these two verses are connected. More votes = stronger scholarly consensus.",
    ),
    "core": (
        "Conexoes entre versiculos que fazem parte do gold set deste estudo. "
        "Representam o nucleo tematico — as relacoes internas mais diretas.",
        "Connections between verses that are part of this study's gold set. "
        "These represent the thematic core — the most direct internal relationships.",
    ),
    "expansion": (
        "Conexoes de um gold ref para versiculos externos ao estudo. "
        "Expandem o tema para outros livros e contextos, mas nao sao o eixo central.",
        "Connections from a gold ref to verses outside this study. "
        "They expand the theme to other books and contexts, but are not the central axis.",
    ),
    "relevance": (
        "Relevancia 3 = Essencial (verso central do tema). "
        "Relevancia 2 = Importante (contribui significativamente). "
        "Relevancia 1 = Suporte (relacionado, mas periferico).",
        "Relevance 3 = Essential (central verse of the theme). "
        "Relevance 2 = Important (significant contribution). "
        "Relevance 1 = Supporting (related, but peripheral).",
    ),
    "sources": (
        "AI = curado por inteligencia artificial. "
        "Humano = confirmado por validacao humana. "
        "Manual = adicionado manualmente pelo pesquisador. "
        "Enrichment = confirmado por 2+ datasets independentes.",
        "AI = curated by artificial intelligence. "
        "Human = confirmed by human validation. "
        "Manual = manually added by the researcher. "
        "Enrichment = confirmed by 2+ independent datasets.",
    ),
    "patristic": (
        "Autores extraidos das evidencias de validacao. A timeline mostra quando cada comentarista viveu, "
        "revelando como a interpretacao deste tema evoluiu ao longo dos seculos.",
        "Authors extracted from validation evidence. The timeline shows when each commentator lived, "
        "revealing how the interpretation of this theme evolved across centuries.",
    ),
}


def tip(key: str) -> str:
    """Return an inline tooltip HTML span."""
    text = _TIPS.get(key, ("", ""))
    content = text[0] if is_pt else text[1]
    return f'<span class="info-tip">?<span class="tip-text">{content}</span></span>'


# ---------------------------------------------------------------------------
# Relevance dots helper
# ---------------------------------------------------------------------------
def relevance_html(score: int) -> str:
    dots = ""
    for i in range(3):
        cls = "filled" if i < score else "empty"
        dots += f'<span class="rel-dot {cls}"></span>'
    labels = {3: "Essencial", 2: "Importante", 1: "Suporte"} if is_pt else {3: "Essential", 2: "Important", 1: "Supporting"}
    label = labels.get(score, "")
    return f'<span class="relevance-dots">{dots}</span><span style="font-size:0.75rem;color:#8B8072;">{label}</span>'


# ---------------------------------------------------------------------------
# Source tag helper
# ---------------------------------------------------------------------------
def source_tags_html(sources: list[str]) -> str:
    tag_map = {
        "ai_curated": ("AI", "tag"),
        "human_confirmed": ("Humano" if is_pt else "Human", "tag tag-human"),
        "manual": ("Manual", "tag tag-manual"),
        "enrichment_confirmed": ("Enrichment", "tag tag-enrichment"),
    }
    tags = ""
    for src in sources:
        label, cls = tag_map.get(src, (src, "tag"))
        tags += f'<span class="{cls}">{label}</span>'
    return tags


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "selected_study" not in st.session_state:
    st.session_state.selected_study = None

queries = load_queries()
gold_set = load_gold_set()


# ═══════════════════════════════════════════════════════════════════════════
# STATE A: Library Overview
# ═══════════════════════════════════════════════════════════════════════════
def render_library():
    st.markdown(
        '<div class="verse-ref" style="font-size:1.8rem;">'
        + ("Estudos Tematicos" if is_pt else "Thematic Studies")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "50 investigacoes teologicas curadas com validacao humana e evidencias patristicas"
        if is_pt
        else "50 curated theological investigations with human validation and patristic evidence"
    )

    # --- Summary metrics ---
    total_refs = sum(len(gs.get("gold_references", [])) for gs in gold_set.values())
    validated = sum(1 for gs in gold_set.values() if gs.get("validation_available"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Estudos" if is_pt else "Studies", len(queries))
    c2.metric("Refs Gold" if is_pt else "Gold Refs", f"{total_refs:,}")
    c3.metric("Validados" if is_pt else "Validated", validated)
    c4.metric("Niveis" if is_pt else "Levels", 5)

    st.markdown('<hr style="border:none;border-top:1px solid #2A2D34;margin:16px 0 24px 0;">', unsafe_allow_html=True)

    # --- Filters ---
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    with fc1:
        diff_options = list(DIFF_LABELS.keys())
        diff_display = [DIFF_LABELS[d][0 if is_pt else 1] for d in diff_options]
        selected_diffs = st.multiselect(
            "Dificuldade" if is_pt else "Difficulty",
            options=diff_options,
            format_func=lambda d: DIFF_LABELS[d][0 if is_pt else 1],
            default=[],
            key="filter_diff",
        )
    with fc2:
        type_options = sorted({q.get("query_type", "") for q in queries})
        selected_types = st.multiselect(
            "Tipo" if is_pt else "Type",
            options=type_options,
            format_func=lambda t: TYPE_LABELS.get(t, (t, t))[0 if is_pt else 1],
            default=[],
            key="filter_type",
        )
    with fc3:
        search = st.text_input(
            "Buscar" if is_pt else "Search",
            placeholder="ex: servo sofredor, cordeiro, silencio..." if is_pt else "e.g. servant, lamb, silence...",
            key="filter_search",
        )

    # --- Filter queries ---
    filtered = queries
    if selected_diffs:
        filtered = [q for q in filtered if q.get("difficulty") in selected_diffs]
    if selected_types:
        filtered = [q for q in filtered if q.get("query_type") in selected_types]
    if search:
        search_lower = _strip_accents(search.lower())
        filtered = [q for q in filtered if search_lower in _strip_accents(q.get("query", "").lower())]

    if not filtered:
        st.info("Nenhum estudo encontrado." if is_pt else "No studies found.")
        return

    # --- Sort by difficulty ---
    diff_order = {"extreme": 0, "hard": 1, "medium_hard": 2, "medium": 3, "baseline": 4}
    filtered.sort(key=lambda q: (diff_order.get(q.get("difficulty", ""), 5), q.get("query", "")))

    # --- Render cards in 3-col grid ---
    for i in range(0, len(filtered), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(filtered):
                break
            q = filtered[idx]
            qid = q["id"]
            gs = gold_set.get(qid, {})
            ref_count = len(gs.get("gold_references", []))
            has_validation = gs.get("validation_available", False)
            diff = q.get("difficulty", "medium")
            qtype = q.get("query_type", "")
            diff_label = DIFF_LABELS.get(diff, (diff, diff))[0 if is_pt else 1]
            type_label = TYPE_LABELS.get(qtype, (qtype, qtype))[0 if is_pt else 1]
            notes_preview = (q.get("notes") or "")[:80]
            if len(q.get("notes", "") or "") > 80:
                notes_preview += "..."
            dot_cls = "" if has_validation else " pending"

            with col:
                st.markdown(
                    f"""<div class="study-card">
                        <div class="study-title">{html.escape(q["query"])}</div>
                        <div>
                            <span class="diff-badge diff-{diff}">{diff_label}</span>
                            <span class="type-badge">{type_label}</span>
                            <span class="validated-dot{dot_cls}" title="{'Validado' if has_validation else 'Pendente'}"></span>
                        </div>
                        <div class="card-meta">
                            {ref_count} refs gold{(' · ' + html.escape(notes_preview)) if notes_preview else ''}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Explorar →" if is_pt else "Explore →",
                    key=f"btn_{qid}",
                    use_container_width=True,
                ):
                    st.session_state.selected_study = qid
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# STATE B: Study Detail
# ═══════════════════════════════════════════════════════════════════════════
def render_study(query_id: str):
    gs = gold_set.get(query_id, {})
    additions = load_additions(query_id)
    query_obj = next((q for q in queries if q["id"] == query_id), None)

    if not gs and not query_obj:
        st.error("Estudo nao encontrado." if is_pt else "Study not found.")
        return

    query_name = gs.get("query") or (query_obj or {}).get("query", query_id)
    diff = gs.get("difficulty") or (query_obj or {}).get("difficulty", "medium")
    qtype = gs.get("query_type") or (query_obj or {}).get("query_type", "")
    diff_label = DIFF_LABELS.get(diff, (diff, diff))[0 if is_pt else 1]
    type_label = TYPE_LABELS.get(qtype, (qtype, qtype))[0 if is_pt else 1]

    # --- Back button ---
    if st.button("← " + ("Voltar" if is_pt else "Back"), key="back_btn"):
        st.session_state.selected_study = None
        st.rerun()

    # --- Hero ---
    st.markdown(
        f'<div class="verse-ref" style="font-size:2rem;">{html.escape(query_name)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="diff-badge diff-{diff}">{diff_label}</span>'
        f'<span class="type-badge">{type_label}</span>'
        + (f'<span class="tag tag-human">{"Validado" if is_pt else "Validated"}</span>' if gs.get("validation_available") else ""),
        unsafe_allow_html=True,
    )

    if additions and additions.get("methodology"):
        st.markdown(
            f'<div style="font-size:0.85rem;color:#8B8072;font-style:italic;margin:12px 0;line-height:1.6;">'
            f'{html.escape(additions["methodology"][:300])}{"..." if len(additions.get("methodology", "")) > 300 else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # --- Stats row ---
    refs = gs.get("gold_references", [])
    stats = gs.get("stats", {})
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.markdown(f'<div class="hero-stat"><div class="value">{len(refs)}</div><div class="label">Gold Refs</div></div>', unsafe_allow_html=True)
    sc2.markdown(f'<div class="hero-stat"><div class="value">{stats.get("human_confirmed", 0)}</div><div class="label">{"Confirmados" if is_pt else "Confirmed"}</div></div>', unsafe_allow_html=True)
    sc3.markdown(f'<div class="hero-stat"><div class="value">{stats.get("manual_added", 0)}</div><div class="label">{"Adicionados" if is_pt else "Added"}</div></div>', unsafe_allow_html=True)
    sc4.markdown(f'<div class="hero-stat"><div class="value">{stats.get("candidates", 0)}</div><div class="label">{"Candidatos" if is_pt else "Candidates"}</div></div>', unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid #2A2D34;margin:24px 0;">', unsafe_allow_html=True)

    # --- Tabs ---
    tab_labels = [
        "Referencias Gold" if is_pt else "Gold References",
        "Rede de Conexoes" if is_pt else "Connection Network",
        "Vozes Patristicas" if is_pt else "Patristic Voices",
        "Notas Academicas" if is_pt else "Scholarly Notes",
        "Candidatos" if is_pt else "Candidates",
    ]
    tab_gold, tab_network, tab_patristic, tab_notes, tab_candidates = st.tabs(tab_labels)

    # ==========================================================
    # TAB 1: Gold References
    # ==========================================================
    with tab_gold:
        _render_gold_refs(refs)

    # ==========================================================
    # TAB 2: Connection Network
    # ==========================================================
    with tab_network:
        _render_network(refs, additions)

    # ==========================================================
    # TAB 3: Patristic Voices
    # ==========================================================
    with tab_patristic:
        _render_patristic(refs, additions)

    # ==========================================================
    # TAB 4: Scholarly Notes
    # ==========================================================
    with tab_notes:
        _render_scholarly_notes(additions)

    # ==========================================================
    # TAB 5: Candidates
    # ==========================================================
    with tab_candidates:
        _render_candidates(additions)


# ---------------------------------------------------------------------------
# Tab renderers
# ---------------------------------------------------------------------------
def _render_gold_refs(refs: list[dict]):
    if not refs:
        st.info("Nenhuma referencia gold disponivel." if is_pt else "No gold references available.")
        return

    # Group by relevance
    for score in [3, 2, 1]:
        group = [r for r in refs if r.get("relevance") == score]
        if not group:
            continue
        label_map = {3: "Essenciais" if is_pt else "Essential", 2: "Importantes" if is_pt else "Important", 1: "Suporte" if is_pt else "Supporting"}
        st.markdown(f'<div class="section-label">{label_map[score]} ({len(group)}){tip("relevance") if score == 3 else ""}</div>', unsafe_allow_html=True)

        for ref in group:
            verse = ref.get("verse", "")
            book_pt, ch, vs = parse_verse_ref(verse)
            text = get_verse_text(book_pt, ch, vs)
            sources = ref.get("sources", [])
            evidence = ref.get("human_evidence", [])
            justification = ref.get("justification", "")

            card_html = f"""<div class="commentary-card">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    {relevance_html(score)}
                    <span style="font-family:Crimson Pro,serif;font-weight:600;color:#D4A853;font-size:1.15rem;">
                        {html.escape(verse)}
                    </span>
                </div>"""

            if text:
                card_html += f"""<div style="background:rgba(212,168,83,0.06);border-left:3px solid rgba(212,168,83,0.4);
                                     padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0;">
                    <div style="font-family:Crimson Pro,serif;font-size:1.05rem;line-height:1.8;color:#E8E0D4;font-style:italic;">
                        &ldquo;{html.escape(text)}&rdquo;
                    </div>
                    <div style="font-size:0.7rem;color:#5A5550;margin-top:6px;">{selected_translation}</div>
                </div>"""

            card_html += f'<div style="margin-top:8px;">{source_tags_html(sources)}{tip("sources")}</div>'

            if evidence:
                ev_html = "".join(
                    f'<div style="font-size:0.8rem;color:#8B8072;margin-top:4px;">• {html.escape(ev)}</div>'
                    for ev in evidence
                )
                card_html += ev_html

            if justification:
                card_html += f"""<div class="insight-box" style="margin-top:12px;">
                    <div class="reflection">{html.escape(justification)}</div>
                </div>"""

            card_html += "</div>"
            st.markdown(card_html, unsafe_allow_html=True)


def _render_network(refs: list[dict], additions: dict | None):
    """Render cross-reference network as a Plotly graph with core/expansion separation."""
    # Collect all edges from gold refs evidence
    all_edges = []
    verse_set = set()
    for ref in refs:
        verse = ref.get("verse", "")
        verse_set.add(verse)
        evidence = ref.get("human_evidence", [])
        for target_osis, votes in parse_crossref_edges(evidence):
            friendly_target = osis_to_friendly(target_osis)
            all_edges.append((verse, friendly_target, votes))

    # Also collect from additions confirmed refs
    if additions:
        for ref in additions.get("existing_refs_confirmed", []):
            verse = ref.get("verse", "")
            verse_set.add(verse)
            for target_osis, votes in parse_crossref_edges(ref.get("evidence", [])):
                friendly_target = osis_to_friendly(target_osis)
                all_edges.append((verse, friendly_target, votes))

    if not all_edges:
        st.info(
            "Dados de rede nao disponiveis para este estudo. Requer validacao humana."
            if is_pt
            else "Network data not available for this study. Requires human validation."
        )
        return

    # Deduplicate and keep max votes per edge
    edge_map: dict[tuple[str, str], int] = {}
    for src, tgt, votes in all_edges:
        key = (src, tgt) if src < tgt else (tgt, src)
        edge_map[key] = max(edge_map.get(key, 0), votes)

    # Classify edges: core (both vertices are gold refs) vs expansion (one is external)
    core_edges = {}
    expansion_edges = {}
    for (src, tgt), votes in edge_map.items():
        if src in verse_set and tgt in verse_set:
            core_edges[(src, tgt)] = votes
        else:
            expansion_edges[(src, tgt)] = votes

    sorted_core = sorted(core_edges.items(), key=lambda x: -x[1])[:20]
    sorted_expansion = sorted(expansion_edges.items(), key=lambda x: -x[1])[:15]
    sorted_edges = sorted_core + sorted_expansion

    if not sorted_edges:
        st.info("Sem conexoes suficientes." if is_pt else "Not enough connections.")
        return

    # Build node set
    nodes = set()
    for (src, tgt), _ in sorted_edges:
        nodes.add(src)
        nodes.add(tgt)
    node_list = sorted(nodes)
    node_idx = {n: i for i, n in enumerate(node_list)}

    # Circular layout
    n = len(node_list)
    angle_step = 2 * math.pi / max(n, 1)
    node_x = [math.cos(i * angle_step) for i in range(n)]
    node_y = [math.sin(i * angle_step) for i in range(n)]

    # Node properties — gold refs are gold+large, external are blue+small
    node_colors = []
    node_sizes = []
    for nd in node_list:
        if nd in verse_set:
            node_colors.append("#D4A853")
            node_sizes.append(18)
        else:
            node_colors.append("#636EFA")
            node_sizes.append(12)

    # Build edge traces — core=gold, expansion=blue/dashed
    edge_traces = []
    max_votes = max(v for _, v in sorted_edges) if sorted_edges else 1

    for (src, tgt), votes in sorted_edges:
        si, ti = node_idx[src], node_idx[tgt]
        is_core = (src, tgt) in core_edges or (tgt, src) in core_edges
        width = max(1, (votes / max_votes) * 5)
        opacity = max(0.3, min(1.0, votes / max_votes))

        if is_core:
            line_color = f"rgba(212,168,83,{opacity})"
            dash = None
        else:
            line_color = f"rgba(99,110,250,{opacity})"
            dash = "dot"

        edge_traces.append(
            go.Scatter(
                x=[node_x[si], node_x[ti], None],
                y=[node_y[si], node_y[ti], None],
                mode="lines",
                line=dict(width=width, color=line_color, dash=dash),
                hoverinfo="text",
                text=f"{src} ↔ {tgt}: {votes}v" + (" (nucleo)" if is_core else " (expansao)"),
                showlegend=False,
            )
        )

    # Node trace
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=1, color="#2A2D34")),
        text=[nd.split(" ")[-1] if len(nd) > 15 else nd for nd in node_list],
        textposition="top center",
        textfont=dict(size=9, color="#E8E0D4"),
        hovertext=node_list,
        hoverinfo="text",
        showlegend=False,
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#E8E0D4",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500,
        margin=dict(l=20, r=20, t=30, b=20),
    )

    # Legend hint
    st.markdown(
        '<div style="display:flex;gap:24px;margin-bottom:8px;font-size:0.75rem;">'
        '<span><span style="color:#D4A853;">━━</span> '
        + ("Nucleo (entre gold refs)" if is_pt else "Core (between gold refs)")
        + '</span>'
        '<span><span style="color:#636EFA;">┈┈</span> '
        + ("Expansao teologica" if is_pt else "Theological expansion")
        + '</span>'
        '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#D4A853;vertical-align:middle;"></span> Gold ref</span>'
        '<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#636EFA;vertical-align:middle;"></span> '
        + ("Externo" if is_pt else "External")
        + '</span>'
        + tip("votes")
        + '</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Core connections table ---
    if sorted_core:
        max_core = max(v for _, v in sorted_core) if sorted_core else 1
        st.markdown(
            f'<div class="section-label">'
            + ("Conexoes do Nucleo" if is_pt else "Core Connections")
            + f' ({len(sorted_core)}){tip("core")}</div>',
            unsafe_allow_html=True,
        )
        for (src, tgt), votes in sorted_core:
            bar_pct = int((votes / max_core) * 100)
            st.markdown(
                f"""<div style="display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid #1A1D24;">
                    <span style="color:#E8E0D4;font-size:0.85rem;min-width:200px;">{html.escape(src)}</span>
                    <span style="color:#D4A853;">↔</span>
                    <span style="color:#E8E0D4;font-size:0.85rem;min-width:200px;">{html.escape(tgt)}</span>
                    <div style="flex:1;background:#1A1D24;border-radius:4px;height:8px;">
                        <div style="width:{bar_pct}%;background:#D4A853;height:100%;border-radius:4px;"></div>
                    </div>
                    <span style="color:#D4A853;font-weight:600;font-size:0.85rem;">{votes}v</span>
                </div>""",
                unsafe_allow_html=True,
            )

    # --- Expansion connections table ---
    if sorted_expansion:
        max_exp = max(v for _, v in sorted_expansion) if sorted_expansion else 1
        st.markdown(
            f'<div class="section-label" style="margin-top:24px;">'
            + ("Expansao Teologica" if is_pt else "Theological Expansion")
            + f' ({len(sorted_expansion)}){tip("expansion")}</div>',
            unsafe_allow_html=True,
        )
        for (src, tgt), votes in sorted_expansion[:10]:
            bar_pct = int((votes / max_exp) * 100)
            # Identify which vertex is external
            ext = tgt if src in verse_set else src
            gold = src if src in verse_set else tgt
            st.markdown(
                f"""<div style="display:flex;align-items:center;gap:12px;padding:6px 0;border-bottom:1px solid #1A1D24;">
                    <span style="color:#D4A853;font-size:0.85rem;min-width:200px;">{html.escape(gold)}</span>
                    <span style="color:#636EFA;">→</span>
                    <span style="color:#636EFA;font-size:0.85rem;min-width:200px;">{html.escape(ext)}</span>
                    <div style="flex:1;background:#1A1D24;border-radius:4px;height:8px;">
                        <div style="width:{bar_pct}%;background:#636EFA;height:100%;border-radius:4px;"></div>
                    </div>
                    <span style="color:#636EFA;font-weight:600;font-size:0.85rem;">{votes}v</span>
                </div>""",
                unsafe_allow_html=True,
            )


def _render_patristic(refs: list[dict], additions: dict | None):
    """Render patristic authors timeline and commentary cards."""
    # Collect all authors from all refs
    all_authors = []
    seen = set()
    for ref in refs:
        for author in extract_authors_from_evidence(ref.get("human_evidence", [])):
            if author["name"] not in seen:
                seen.add(author["name"])
                author["verse"] = ref.get("verse", "")
                all_authors.append(author)

    # Also from additions
    if additions:
        for ref in additions.get("existing_refs_confirmed", []):
            for author in extract_authors_from_evidence(ref.get("evidence", [])):
                if author["name"] not in seen:
                    seen.add(author["name"])
                    author["verse"] = ref.get("verse", "")
                    all_authors.append(author)
        for ref in additions.get("new_refs_added", []):
            justification = ref.get("justification", "")
            # Check justification for author mentions
            for name, info in PATRISTIC_AUTHORS.items():
                if name in justification and info["en"] not in seen:
                    seen.add(info["en"])
                    all_authors.append({
                        "name": info["en"],
                        "date": info["date"],
                        "tradition": info["tradition"],
                        "evidence": justification[:150],
                        "verse": ref.get("verse", ""),
                    })

    if not all_authors:
        st.info(
            "Dados patristicos nao disponiveis. Requer validacao humana."
            if is_pt
            else "Patristic data not available. Requires human validation."
        )
        return

    all_authors.sort(key=lambda a: a["date"])

    # --- Timeline chart ---
    tradition_colors = {
        "Apostolic Father": "#EF553B",
        "Church Father": "#D4A853",
        "Catholic": "#AB63FA",
        "Reformed": "#2196F3",
        "Protestant": "#00CC96",
        "Adventist": "#FF9800",
    }

    fig = go.Figure()
    for i, author in enumerate(all_authors):
        color = tradition_colors.get(author["tradition"], "#8B8072")
        fig.add_trace(
            go.Scatter(
                x=[author["date"]],
                y=[0],
                mode="markers+text",
                marker=dict(size=14, color=color, line=dict(width=2, color="#0E1117")),
                text=[author["name"].split(" ")[0]],  # First name only
                textposition="top center",
                textfont=dict(size=10, color="#E8E0D4"),
                hovertext=f"{author['name']} (AD {author['date']})<br>{author['tradition']}<br>{author.get('verse', '')}",
                hoverinfo="text",
                showlegend=False,
            )
        )

    # Timeline line
    if all_authors:
        min_date = all_authors[0]["date"] - 50
        max_date = all_authors[-1]["date"] + 50
        fig.add_shape(
            type="line",
            x0=min_date, x1=max_date, y0=0, y1=0,
            line=dict(color="#2A2D34", width=2),
        )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#E8E0D4",
        xaxis=dict(
            title="AD" if not is_pt else "d.C.",
            showgrid=True,
            gridcolor="#1A1D24",
            tickfont=dict(color="#8B8072"),
        ),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 0.8]),
        height=200,
        margin=dict(l=20, r=20, t=10, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f'<div style="font-size:0.75rem;color:#5A5550;text-align:center;margin-bottom:16px;">'
        f'{len(all_authors)} {"autores ao longo de" if is_pt else "authors across"} '
        f'{all_authors[-1]["date"] - all_authors[0]["date"]} {"anos" if is_pt else "years"}'
        f'{tip("patristic")}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --- Author cards ---
    for author in all_authors:
        tradition_badge_color = tradition_colors.get(author["tradition"], "#8B8072")
        st.markdown(
            f"""<div class="author-card" style="border-left-color:{tradition_badge_color};">
                <span class="name">{html.escape(author['name'])}</span>
                <span class="period">AD {author['date']} · {author['tradition']}</span>
                <div style="margin-top:4px;">
                    <span class="tag" style="font-size:0.65rem;">{html.escape(author.get('verse', ''))}</span>
                </div>
                <div class="quote">{html.escape(author.get('evidence', '')[:200])}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_scholarly_notes(additions: dict | None):
    if not additions or not additions.get("scholarly_notes"):
        st.info(
            "Notas academicas nao disponiveis. Requer validacao humana."
            if is_pt
            else "Scholarly notes not available. Requires human validation."
        )
        return

    notes = additions["scholarly_notes"]
    for key, value in notes.items():
        # Format key: snake_case → Title Case
        title = key.replace("_", " ").title()
        st.markdown(f'<div class="section-label">{html.escape(title)}</div>', unsafe_allow_html=True)

        if isinstance(value, str):
            st.markdown(
                f"""<div class="insight-box">
                    <div class="theme">{html.escape(value)}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        elif isinstance(value, dict):
            parts = []
            for sub_key, sub_val in value.items():
                sub_title = sub_key.replace("_", " ").title()
                if isinstance(sub_val, str):
                    parts.append(f'<div style="margin-bottom:8px;"><strong style="color:#D4A853;font-size:0.85rem;">{html.escape(sub_title)}</strong>'
                                 f'<div style="font-family:Crimson Pro,serif;color:#E8E0D4;line-height:1.7;margin-top:4px;">{html.escape(sub_val)}</div></div>')
                elif isinstance(sub_val, list):
                    items = "".join(f"<li>{html.escape(str(item))}</li>" for item in sub_val)
                    parts.append(f'<div style="margin-bottom:8px;"><strong style="color:#D4A853;font-size:0.85rem;">{html.escape(sub_title)}</strong>'
                                 f'<ul style="color:#E8E0D4;margin-top:4px;">{items}</ul></div>')
                else:
                    parts.append(f'<div style="margin-bottom:8px;"><strong style="color:#D4A853;font-size:0.85rem;">{html.escape(sub_title)}</strong>'
                                 f'<div style="color:#E8E0D4;margin-top:4px;">{html.escape(str(sub_val))}</div></div>')

            st.markdown(
                f'<div class="insight-box">{"".join(parts)}</div>',
                unsafe_allow_html=True,
            )
        elif isinstance(value, list):
            items = "".join(f"<li style='color:#E8E0D4;'>{html.escape(str(item))}</li>" for item in value)
            st.markdown(
                f'<div class="insight-box"><ul style="margin:0;padding-left:20px;">{items}</ul></div>',
                unsafe_allow_html=True,
            )

    # Also show reclassification if present
    reclass = additions.get("reclassification")
    if reclass:
        st.markdown(f'<div class="section-label">{"Reclassificacao" if is_pt else "Reclassification"}</div>', unsafe_allow_html=True)
        from_d = DIFF_LABELS.get(reclass.get("from_difficulty", ""), ("", ""))[0 if is_pt else 1]
        to_d = DIFF_LABELS.get(reclass.get("proposed_difficulty", ""), ("", ""))[0 if is_pt else 1]
        st.markdown(
            f"""<div class="insight-box">
                <div style="font-size:0.9rem;color:#E8E0D4;">
                    <strong>{from_d}</strong> → <strong style="color:#D4A853;">{to_d}</strong>
                </div>
                <div class="reflection">{html.escape(reclass.get('reasoning', ''))}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_candidates(additions: dict | None):
    if not additions:
        st.info(
            "Dados de candidatos nao disponiveis. Requer validacao humana."
            if is_pt
            else "Candidate data not available. Requires human validation."
        )
        return

    # New refs added (human contributions)
    new_refs = additions.get("new_refs_added", [])
    if new_refs:
        st.markdown(
            f'<div class="section-label">{"Adicionados na Validacao" if is_pt else "Added During Validation"} ({len(new_refs)})</div>',
            unsafe_allow_html=True,
        )
        for ref in new_refs:
            verse = ref.get("verse", "")
            book_pt, ch, vs = parse_verse_ref(verse)
            text = get_verse_text(book_pt, ch, vs)
            relevance = ref.get("relevance", 1)
            justification = ref.get("justification", "")

            card_html = f"""<div class="commentary-card" style="border-left:3px solid #636EFA;">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    {relevance_html(relevance)}
                    <span style="font-family:Crimson Pro,serif;font-weight:600;color:#D4A853;font-size:1.1rem;">
                        {html.escape(verse)}
                    </span>
                    <span class="tag tag-manual">{"Adicionado" if is_pt else "Added"}</span>
                </div>"""

            if text:
                card_html += f"""<div style="background:rgba(99,110,250,0.06);border-left:3px solid rgba(99,110,250,0.4);
                                     padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0;">
                    <div style="font-family:Crimson Pro,serif;font-size:1.05rem;line-height:1.8;color:#E8E0D4;font-style:italic;">
                        &ldquo;{html.escape(text)}&rdquo;
                    </div>
                </div>"""

            if justification:
                card_html += f'<div style="font-size:0.85rem;color:#8B8072;margin-top:8px;line-height:1.6;">{html.escape(justification)}</div>'

            card_html += "</div>"
            st.markdown(card_html, unsafe_allow_html=True)

    # Candidates noted (for further study)
    candidates = additions.get("candidates_noted", [])
    if candidates:
        st.markdown(
            f'<div class="section-label">{"Candidatos para Estudo Futuro" if is_pt else "Candidates for Further Study"} ({len(candidates)})</div>',
            unsafe_allow_html=True,
        )
        for ref in candidates:
            verse = ref.get("verse", "")
            book_pt, ch, vs = parse_verse_ref(verse)
            text = get_verse_text(book_pt, ch, vs)
            relevance = ref.get("relevance", 1)
            justification = ref.get("justification", "")

            card_html = f"""<div class="candidate-card">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    {relevance_html(relevance)}
                    <span style="font-family:Crimson Pro,serif;font-weight:600;color:#E8E0D4;font-size:1.05rem;">
                        {html.escape(verse)}
                    </span>
                    <span style="font-size:0.65rem;color:#5A5550;padding:2px 8px;border:1px solid #2A2D34;border-radius:12px;">
                        {"Candidato" if is_pt else "Candidate"}
                    </span>
                </div>"""

            if text:
                card_html += f"""<div style="background:rgba(90,85,80,0.06);border-left:3px solid #2A2D34;
                                     padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0;">
                    <div style="font-family:Crimson Pro,serif;font-size:1rem;line-height:1.8;color:#E8E0D4;font-style:italic;">
                        &ldquo;{html.escape(text)}&rdquo;
                    </div>
                </div>"""

            if justification:
                card_html += f'<div style="font-size:0.85rem;color:#8B8072;margin-top:8px;line-height:1.6;">{html.escape(justification)}</div>'

            card_html += "</div>"
            st.markdown(card_html, unsafe_allow_html=True)

    if not new_refs and not candidates:
        st.info(
            "Nenhum candidato registrado para este estudo."
            if is_pt
            else "No candidates recorded for this study."
        )


# ═══════════════════════════════════════════════════════════════════════════
# Main routing
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.selected_study is None:
    render_library()
else:
    render_study(st.session_state.selected_study)
