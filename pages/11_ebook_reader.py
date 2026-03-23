"""
Biblioteca — Leitor de ebooks para classicos cristaos traduzidos.
Interface otimizada para leitura de textos longos com tipografia editorial.
"""

import json
import re
from pathlib import Path

import streamlit as st

from loading import show_loading

show_loading()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CLASSICS_DIR = DATA_DIR / "classics"
META_PATH = CLASSICS_DIR / "_meta.json"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def load_catalog(_mtime: float = 0) -> dict:
    if META_PATH.exists():
        with open(META_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"works": {}}


@st.cache_data(ttl=300)
def load_work(author: str, filename: str) -> dict | None:
    path = CLASSICS_DIR / "02_translated" / "pt" / author / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


# ---------------------------------------------------------------------------
# CSS — Reading experience
# ---------------------------------------------------------------------------
EBOOK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500;600&display=swap');

.ebook-container {
    max-width: 720px;
    margin: 0 auto;
    padding: 0 1rem;
}

/* Book header */
.ebook-header {
    text-align: center;
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid #2A2D34;
    margin-bottom: 2rem;
}
.ebook-book-title {
    font-family: 'Crimson Pro', serif;
    font-size: 2rem;
    font-weight: 600;
    color: #D4A853;
    letter-spacing: 2px;
    margin: 0;
}
.ebook-book-author {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #8B8072;
    letter-spacing: 1px;
    margin-top: 0.5rem;
}

/* Progress bar */
.ebook-progress-wrap {
    max-width: 720px;
    margin: 0 auto 1.5rem;
    display: flex;
    align-items: center;
    gap: 12px;
}
.ebook-progress-bar {
    flex: 1;
    height: 3px;
    background: #2A2D34;
    border-radius: 2px;
    overflow: hidden;
}
.ebook-progress-fill {
    height: 100%;
    background: #D4A853;
    border-radius: 2px;
    transition: width 0.3s ease;
}
.ebook-progress-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #5A5550;
    white-space: nowrap;
}

/* Chapter title */
.ebook-chapter-title {
    font-family: 'Crimson Pro', serif;
    font-size: 1.6rem;
    font-weight: 600;
    color: #D4A853;
    text-align: center;
    letter-spacing: 1px;
    margin: 1rem 0 0.3rem;
}
.ebook-chapter-subtitle {
    font-family: 'Crimson Pro', serif;
    font-size: 1.1rem;
    font-weight: 400;
    font-style: italic;
    color: #8B8072;
    text-align: center;
    margin: 0 0 2rem;
}

/* Body text */
.ebook-body {
    font-family: 'Crimson Pro', serif;
    font-size: 1.15rem;
    line-height: 1.85;
    color: #E8E0D4;
    text-align: justify;
    hyphens: auto;
}
.ebook-body p {
    margin: 0 0 1.3em;
    text-indent: 1.5em;
}
.ebook-body p:first-child {
    text-indent: 0;
}

/* Drop cap */
.ebook-body p:first-child::first-letter {
    float: left;
    font-family: 'Crimson Pro', serif;
    font-size: 3.8rem;
    line-height: 0.8;
    font-weight: 600;
    color: #D4A853;
    padding-right: 8px;
    padding-top: 6px;
}

/* Section markers like **(1)** */
.ebook-body .section-marker {
    color: #D4A853;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
}

/* Scripture references */
.ebook-body .scripture-ref {
    color: #D4A853;
    border-bottom: 1px dotted rgba(212, 168, 83, 0.4);
    cursor: default;
}

/* Footnote markers (superscript) */
.ebook-body .fn-marker {
    color: #D4A853;
    font-size: 0.75em;
    vertical-align: super;
    cursor: help;
    position: relative;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
}
.ebook-body .fn-marker:hover::after {
    content: attr(data-note);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: #1A1D24;
    border: 1px solid #D4A853;
    color: #E8E0D4;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 0.78rem;
    line-height: 1.5;
    font-weight: 400;
    white-space: normal;
    width: 280px;
    z-index: 100;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5);
}

/* Footnotes section */
.ebook-footnotes {
    border-top: 1px solid #2A2D34;
    margin-top: 2rem;
    padding-top: 1rem;
}
.ebook-footnotes-title {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: #5A5550;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.ebook-footnote {
    font-family: 'Crimson Pro', serif;
    font-size: 0.95rem;
    color: #8B8072;
    line-height: 1.6;
    margin-bottom: 0.4rem;
    padding-left: 1.5em;
    text-indent: -1.5em;
}
.ebook-footnote .fn-num {
    color: #D4A853;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Chapter divider */
.ebook-divider {
    text-align: center;
    color: #2A2D34;
    margin: 3rem 0;
    font-size: 1.2rem;
    letter-spacing: 12px;
}

/* Navigation */
.ebook-nav {
    max-width: 720px;
    margin: 2rem auto 3rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 1.5rem;
    border-top: 1px solid #2A2D34;
}
.ebook-nav-btn {
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #8B8072;
    text-decoration: none;
    padding: 8px 16px;
    border: 1px solid #2A2D34;
    border-radius: 6px;
    transition: all 0.2s;
    cursor: pointer;
    background: transparent;
}
.ebook-nav-btn:hover {
    border-color: #D4A853;
    color: #D4A853;
}
.ebook-nav-btn.disabled {
    opacity: 0.3;
    pointer-events: none;
}

/* Untranslated notice */
.ebook-untranslated {
    background: rgba(212, 168, 83, 0.08);
    border: 1px solid rgba(212, 168, 83, 0.2);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 1.5rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #D4A853;
    text-align: center;
}

/* Catalog cards */
.catalog-card {
    background: #1A1D24;
    border: 1px solid #2A2D34;
    border-radius: 12px;
    padding: 24px;
    transition: border-color 0.3s ease;
    cursor: pointer;
    height: 100%;
}
.catalog-card:hover {
    border-color: rgba(212, 168, 83, 0.5);
}
.catalog-title {
    font-family: 'Crimson Pro', serif;
    font-size: 1.3rem;
    font-weight: 600;
    color: #D4A853;
    margin-bottom: 4px;
}
.catalog-author {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #8B8072;
    margin-bottom: 12px;
}
.catalog-meta {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    color: #5A5550;
}
.catalog-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.65rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
}
.badge-complete {
    background: rgba(76, 175, 80, 0.15);
    color: #4CAF50;
}
.badge-partial {
    background: rgba(255, 193, 7, 0.15);
    color: #FFC107;
}

/* Hide streamlit chrome for reading */
.ebook-container .stMarkdown { margin: 0; padding: 0; }

@media print {
    body { background: white !important; color: black !important; }
    .ebook-body { color: #1a1a1a; font-size: 11pt; }
    .ebook-chapter-title { color: #333; }
    .ebook-nav, .ebook-progress-wrap { display: none !important; }
}
</style>
"""

# ---------------------------------------------------------------------------
# Text processing helpers
# ---------------------------------------------------------------------------
def process_text_to_html(text: str, notes: list[dict]) -> str:
    """Convert chapter text to HTML with footnote tooltips and formatting."""
    if not text:
        return ""

    # Build notes lookup
    notes_map = {}
    for n in notes:
        num = n.get("number", "") or n.get("text", "").split(":")[0] if isinstance(n, dict) else ""
        note_text = n.get("text", "") if isinstance(n, dict) else str(n)
        if num:
            notes_map[str(num)] = note_text

    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Process footnote markers [N] → superscript with tooltip
    def replace_fn(m):
        num = m.group(1)
        note_text = notes_map.get(num, "")
        note_text_escaped = note_text.replace('"', '&quot;').replace("'", "&#39;")
        if note_text:
            return f'<span class="fn-marker" data-note="{note_text_escaped}">{num}</span>'
        return f'<span class="fn-marker">{num}</span>'

    text = re.sub(r"\[(\d+)\]", replace_fn, text)

    # Process section markers **(N)** → styled span
    text = re.sub(
        r"\*\*\((\d+)\)\*\*",
        r'<span class="section-marker">(\1)</span>',
        text,
    )

    # Process bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # Process italic *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    html_parts = []
    for p in paragraphs:
        # Replace single newlines within paragraph with spaces
        p = re.sub(r"\n", " ", p)
        html_parts.append(f"<p>{p}</p>")

    return "\n".join(html_parts)


def render_footnotes_html(notes: list[dict]) -> str:
    """Render footnotes section at bottom of chapter."""
    if not notes:
        return ""

    items = []
    for n in notes:
        if isinstance(n, dict):
            num = n.get("number", "")
            text = n.get("text", "")
        else:
            num = ""
            text = str(n)
        if text:
            text_escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            items.append(
                f'<div class="ebook-footnote"><span class="fn-num">[{num}]</span> {text_escaped}</div>'
            )

    if not items:
        return ""

    return (
        '<div class="ebook-footnotes">'
        '<div class="ebook-footnotes-title">Notas</div>'
        + "\n".join(items)
        + "</div>"
    )


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------
def render_catalog(catalog: dict, is_pt: bool):
    """Render the book catalog (library view)."""
    works = catalog.get("works", {})

    st.markdown(
        '<div class="ebook-container">'
        '<div class="ebook-header">'
        '<div class="ebook-book-title">Biblioteca</div>'
        '<div class="ebook-book-author">'
        + ("Classicos cristaos em edicao bilingue" if is_pt else "Christian classics in bilingual edition")
        + "</div></div></div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(works))
    for i, (work_id, work) in enumerate(works.items()):
        with cols[i]:
            title = work.get("title_pt", work.get("title_en", ""))
            author = work.get("author_pt", work.get("author_en", ""))
            status = work.get("status", "unknown")
            badge_class = "badge-complete" if status == "complete" else "badge-partial"
            badge_text = "Completo" if status == "complete" else "Parcial"
            stats = work.get("stats", {})
            chapters = stats.get("chapters", "?")

            st.markdown(
                f'<div class="catalog-card">'
                f'<div class="catalog-title">{title}</div>'
                f'<div class="catalog-author">{author} ({work.get("author_dates", "")})</div>'
                f'<div class="catalog-meta">'
                f'<span class="catalog-badge {badge_class}">{badge_text}</span>'
                f' &nbsp; {chapters} capitulos &nbsp; {work.get("work_date", "")}'
                f"</div></div>",
                unsafe_allow_html=True,
            )

            if st.button(
                f"{'Ler' if is_pt else 'Read'} →",
                key=f"read_{work_id}",
                use_container_width=True,
            ):
                st.session_state.ebook_work_id = work_id
                st.session_state.ebook_chapter_idx = 0
                st.rerun()


def render_reader(work_data: dict, catalog_work: dict, is_pt: bool):
    """Render the ebook reading experience."""
    chapters = work_data.get("chapters", [])
    meta = work_data.get("metadata", {})

    # Filter chapters with content
    content_chapters = [
        (i, ch) for i, ch in enumerate(chapters)
        if ch.get("text_en") or ch.get("text_pt")
    ]

    if not content_chapters:
        st.warning("No chapters with content found.")
        return

    # Current chapter index — start at first translated chapter when PT
    if "ebook_chapter_idx" not in st.session_state:
        first_translated = 0
        if is_pt:
            for ci, (_, ch) in enumerate(content_chapters):
                if ch.get("has_translation"):
                    first_translated = ci
                    break
        st.session_state.ebook_chapter_idx = first_translated

    idx = st.session_state.ebook_chapter_idx
    if idx >= len(content_chapters):
        idx = 0
        st.session_state.ebook_chapter_idx = 0

    real_idx, chapter = content_chapters[idx]

    # --- Book header ---
    title = meta.get("title_pt", meta.get("title_en", "")) if is_pt else meta.get("title_en", "")
    author = meta.get("author_pt", meta.get("author_en", "")) if is_pt else meta.get("author_en", "")

    st.markdown(
        '<div class="ebook-container">'
        f'<div class="ebook-header">'
        f'<div class="ebook-book-title">{title}</div>'
        f'<div class="ebook-book-author">{author}</div>'
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # --- Progress bar ---
    progress = (idx + 1) / len(content_chapters) * 100
    st.markdown(
        f'<div class="ebook-progress-wrap">'
        f'<div class="ebook-progress-bar"><div class="ebook-progress-fill" style="width:{progress:.0f}%"></div></div>'
        f'<div class="ebook-progress-text">{idx+1}/{len(content_chapters)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- Chapter selector ---
    chapter_options = []
    for ci, (_, ch) in enumerate(content_chapters):
        if is_pt:
            ch_title = ch.get("title_pt") or ch.get("title_en") or f"Capitulo {ch.get('number', ci+1)}"
        else:
            ch_title = ch.get("title_en") or f"Chapter {ch.get('number', ci+1)}"
        has_pt = ch.get("has_translation", False)
        marker = "" if has_pt or not is_pt else " [EN]"
        chapter_options.append(f"{ci+1}. {ch_title}{marker}")

    def _on_chapter_change():
        sel = st.session_state._chapter_sel
        new_i = chapter_options.index(sel)
        st.session_state.ebook_chapter_idx = new_i

    col_sel, col_back = st.columns([4, 1])
    with col_sel:
        st.selectbox(
            "Capitulo" if is_pt else "Chapter",
            chapter_options,
            index=idx,
            key="_chapter_sel",
            label_visibility="collapsed",
            on_change=_on_chapter_change,
        )

    with col_back:
        if st.button("← " + ("Catalogo" if is_pt else "Catalog"), key="back_catalog"):
            del st.session_state["ebook_work_id"]
            st.rerun()

    # --- Chapter content ---
    has_translation = chapter.get("has_translation", False)
    if is_pt and has_translation:
        ch_title_display = chapter.get("title_pt") or chapter.get("title_en") or ""
    else:
        ch_title_display = chapter.get("title_en") or ""
    ch_subtitle = chapter.get("subtitle_en", "")

    # Select text based on language
    if is_pt and has_translation:
        text = chapter.get("text_pt", "")
        notes = chapter.get("notes_pt", [])
    else:
        text = chapter.get("text_en", "")
        notes = chapter.get("notes_en", [])

    # Untranslated notice
    untranslated_html = ""
    if is_pt and not has_translation:
        untranslated_html = (
            '<div class="ebook-untranslated">'
            "Traducao ainda nao disponivel para este capitulo. Exibindo texto original em ingles."
            "</div>"
        )

    body_html = process_text_to_html(text, notes)
    footnotes_html = render_footnotes_html(notes)

    st.markdown(
        f'<div class="ebook-container">'
        f'{untranslated_html}'
        f'<div class="ebook-chapter-title">{ch_title_display}</div>'
        + (f'<div class="ebook-chapter-subtitle">{ch_subtitle}</div>' if ch_subtitle else "")
        + f'<div class="ebook-body">{body_html}</div>'
        f"{footnotes_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- Navigation buttons ---
    col_prev, col_next = st.columns(2)
    with col_prev:
        if idx > 0:
            if st.button("← " + ("Anterior" if is_pt else "Previous"), key="prev_ch", use_container_width=True):
                st.session_state.ebook_chapter_idx = idx - 1
                if "_chapter_sel" in st.session_state:
                    del st.session_state["_chapter_sel"]
                st.rerun()
    with col_next:
        if idx < len(content_chapters) - 1:
            if st.button(("Próximo" if is_pt else "Next") + " →", key="next_ch", use_container_width=True):
                st.session_state.ebook_chapter_idx = idx + 1
                if "_chapter_sel" in st.session_state:
                    del st.session_state["_chapter_sel"]
                st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
st.markdown(EBOOK_CSS, unsafe_allow_html=True)

is_pt = st.session_state.get("language", "Portugues") == "Portugues"

_meta_mtime = META_PATH.stat().st_mtime if META_PATH.exists() else 0
catalog = load_catalog(_mtime=_meta_mtime)

# Determine if we're viewing catalog or reading a book
if "ebook_work_id" in st.session_state:
    work_id = st.session_state.ebook_work_id
    # Resolve work file
    work_files = {
        "athanasius:incarnation": ("athanasius", "incarnation.json"),
        "kempis:imitation": ("kempis", "imitation_book1.json"),
        "lawrence:practice": ("lawrence", "practice.json"),
    }

    if work_id in work_files:
        author_dir, filename = work_files[work_id]
        work_data = load_work(author_dir, filename)

        if work_data:
            catalog_work = catalog.get("works", {}).get(work_id, {})
            render_reader(work_data, catalog_work, is_pt)
        else:
            st.error(f"Could not load work data for {work_id}")
            if st.button("Back to catalog"):
                del st.session_state["ebook_work_id"]
                st.rerun()
    else:
        st.error(f"Unknown work: {work_id}")
        if st.button("Back to catalog"):
            del st.session_state["ebook_work_id"]
            st.rerun()
else:
    render_catalog(catalog, is_pt)
