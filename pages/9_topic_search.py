"""
Topic Explorer — Browse and study biblical topics.
All data loaded from parquet (no JSON repo dependency).
"""

from pathlib import Path

import duckdb
import json
import pandas as pd
import streamlit as st

from loading import show_loading

show_loading()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TOPICS_FILE = DATA_DIR / "topics.parquet"
BIBLETEXT_FILE = DATA_DIR / "bibletext.parquet"

if not TOPICS_FILE.exists():
    st.info("Dados nao encontrados. Execute `python sync.py topics`.")
    st.stop()

# ---------------------------------------------------------------------------
# CSS — aligned with Verse Explorer design system
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap');

.topic-title {
    font-family: 'Crimson Pro', serif;
    font-size: 1.6rem;
    font-weight: 600;
    color: #D4A853;
    margin-bottom: 4px;
}
.aspect-card {
    background: #1A1D24;
    border: 1px solid #2A2D34;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.aspect-label {
    font-weight: 600;
    color: #E8E0D4;
    font-size: 0.95rem;
}
.aspect-refs {
    font-family: 'Crimson Pro', serif;
    font-size: 0.95rem;
    line-height: 1.7;
    color: #D4A853;
    margin-top: 6px;
}
.tag-nav {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 20px;
    font-size: 0.65rem;
    font-weight: 500;
    background: rgba(76, 175, 80, 0.15);
    color: #4CAF50;
    border: 1px solid rgba(76, 175, 80, 0.3);
    margin-left: 6px;
}
.tag-tor {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 20px;
    font-size: 0.65rem;
    font-weight: 500;
    background: rgba(33, 150, 243, 0.15);
    color: #2196F3;
    border: 1px solid rgba(33, 150, 243, 0.3);
    margin-left: 6px;
}
.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #5A5550;
    margin: 16px 0 8px 0;
}
.stat-row {
    display: flex;
    gap: 24px;
    margin: 8px 0;
}
.stat-item {
    font-size: 0.85rem;
    color: #8B8072;
}
.stat-item strong {
    color: #E8E0D4;
}
.books-box {
    background: rgba(212, 168, 83, 0.08);
    border-left: 3px solid #D4A853;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin-top: 12px;
    font-size: 0.9rem;
    color: #E8E0D4;
}
.see-also-box {
    background: rgba(99, 110, 250, 0.08);
    border-left: 3px solid #636EFA;
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
    margin-top: 8px;
    font-size: 0.9rem;
    color: #E8E0D4;
}
.verse-inline {
    background: rgba(212, 168, 83, 0.06);
    border-left: 2px solid rgba(212, 168, 83, 0.3);
    padding: 8px 12px;
    margin: 4px 0 4px 8px;
    font-family: 'Crimson Pro', serif;
    font-style: italic;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #E8E0D4;
    border-radius: 0 6px 6px 0;
}
.verse-inline .verse-ref-small {
    font-style: normal;
    font-size: 0.8rem;
    color: #D4A853;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"
import re as _re


@st.cache_data(ttl=3600)
def load_topics(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{TOPICS_FILE}'").df()


@st.cache_data(ttl=3600)
def load_bible_text(mtime: float) -> pd.DataFrame:
    if not BIBLETEXT_FILE.exists():
        return pd.DataFrame()
    return con.sql(f"SELECT * FROM '{BIBLETEXT_FILE}'").df()


def parse_ref(ref_str: str):
    """Parse 'Genesis 1:2' or '1 Chronicles 2:10' into (book, chapter, verse)."""
    m = _re.match(r"^(\d?\s?[A-Za-z ]+?)\s+(\d+):(\d+)", ref_str.strip())
    if m:
        return m.group(1).strip(), int(m.group(2)), int(m.group(3))
    return None, None, None


# Canonical book order (matches Torrey/standard English names)
_CANONICAL_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
]


@st.cache_data(ttl=3600)
def build_book_map(bible_mtime: float) -> dict[str, dict[str, str]]:
    """Build canonical→translation book name map for each translation.

    Returns {translation: {canonical_lower: actual_book_name}}
    """
    bible_df = load_bible_text(bible_mtime)
    if bible_df.empty:
        return {}
    book_map: dict[str, dict[str, str]] = {}
    for tr in bible_df["translation"].unique():
        tr_books = []
        seen = set()
        for b in bible_df[bible_df["translation"] == tr]["book"]:
            if b not in seen:
                seen.add(b)
                tr_books.append(b)
        # Map by position: canonical[i] → translation[i]
        mapping = {}
        for i, canon in enumerate(_CANONICAL_BOOKS):
            if i < len(tr_books):
                mapping[canon.lower()] = tr_books[i]
        book_map[tr] = mapping
    return book_map


def lookup_verse(bible_df: pd.DataFrame, ref_str: str, translation: str,
                 book_map: dict[str, dict[str, str]] | None = None) -> str | None:
    """Look up verse text from bibletext dataframe."""
    book, ch, vs = parse_ref(ref_str)
    if not book:
        return None
    # Resolve book name for this translation
    tr_map = book_map.get(translation, {}) if book_map else {}
    resolved = tr_map.get(book.lower(), book)
    mask = (
        (bible_df["translation"] == translation)
        & (bible_df["book"] == resolved)
        & (bible_df["chapter"] == ch)
        & (bible_df["verse"] == vs)
    )
    matches = bible_df[mask]
    if not matches.empty:
        return matches.iloc[0]["text"]
    return None


def render_full_topic(row: pd.Series):
    """Render a full topic in study format with tabs like Verse Explorer."""
    import html as _html
    import plotly.graph_objects as go
    topic_name = row["topic"]

    # Load bible text for verse lookups
    bible_df = pd.DataFrame()
    bk_map: dict[str, dict[str, str]] = {}
    if BIBLETEXT_FILE.exists():
        mtime = BIBLETEXT_FILE.stat().st_mtime
        bible_df = load_bible_text(mtime)
        bk_map = build_book_map(mtime)

    selected_translation = st.session_state.get("translation", "KJV")

    st.markdown(f'<div class="topic-title">{_html.escape(topic_name)}</div>', unsafe_allow_html=True)
    st.caption("Torrey's Topical Textbook (1897)")

    aspects = json.loads(row.get("aspects_json", "[]"))
    ot = int(row.get("ot_refs", 0))
    nt = int(row.get("nt_refs", 0))
    n_books = int(row.get("n_books", 0))
    all_refs = []
    for asp in aspects:
        all_refs.extend(asp.get("references", []))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Refs", int(row["n_biblical_refs"]))
    c2.metric("Aspects", len(aspects))
    c3.metric("Books" if not is_pt else "Livros", n_books)
    c4.metric("OT/NT" if not is_pt else "AT/NT", f"{ot}/{nt}")

    st.markdown("---")

    # ── TABS ──
    tab_aspects, tab_refs, tab_books, tab_overview = st.tabs([
        "Aspectos" if is_pt else "Aspects",
        f"{'Referencias' if is_pt else 'References'} ({len(all_refs)})",
        f"{'Livros' if is_pt else 'Books'} ({n_books})",
        "Visao Geral" if is_pt else "Overview",
    ])

    # ── TAB: ASPECTS ──
    with tab_aspects:
        if aspects:
            for asp in aspects:
                label = asp.get("label", "")
                refs = asp.get("references", [])

                refs_html = ""
                if refs:
                    refs_html = f'<div class="aspect-refs">{" · ".join(_html.escape(r) for r in refs)}</div>'

                st.markdown(
                    f'<div class="aspect-card">'
                    f'<span class="aspect-label">{_html.escape(label)}</span>'
                    f'{refs_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Verse text expander
                if refs and not bible_df.empty:
                    show_limit = 20
                    with st.expander(f"{'Ver versiculos' if is_pt else 'Show verses'} ({len(refs)})", expanded=False):
                        for ref in refs[:show_limit]:
                            text = lookup_verse(bible_df, ref, selected_translation, bk_map)
                            if text:
                                st.markdown(
                                    f'<div class="verse-inline">'
                                    f'<span class="verse-ref-small">{_html.escape(ref)}</span><br/>'
                                    f'{_html.escape(text)}'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                        if len(refs) > show_limit:
                            st.caption(f"... {'e mais' if is_pt else 'and'} {len(refs) - show_limit} {'versiculos' if is_pt else 'more verses'}")
        else:
            st.info("Nenhum aspecto encontrado" if is_pt else "No aspects found")

    # ── TAB: REFERENCES ──
    with tab_refs:
        if all_refs and not bible_df.empty:
            for ref in all_refs:
                text = lookup_verse(bible_df, ref, selected_translation, bk_map)
                if text:
                    st.markdown(
                        f'<div class="verse-inline">'
                        f'<span class="verse-ref-small">{_html.escape(ref)}</span><br/>'
                        f'{_html.escape(text)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="aspect-refs" style="margin:4px 0;">{_html.escape(ref)}</div>',
                        unsafe_allow_html=True,
                    )
        elif all_refs:
            for ref in all_refs:
                st.markdown(
                    f'<div class="aspect-refs" style="margin:4px 0;">{_html.escape(ref)}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Nenhuma referencia encontrada" if is_pt else "No references found")

    # ── TAB: BOOKS ──
    with tab_books:
        books = json.loads(row.get("books_json", "[]"))
        if books:
            # Count refs per book
            from collections import Counter
            book_counts = Counter()
            for ref in all_refs:
                book, _, _ = parse_ref(ref)
                if book:
                    book_counts[book] += 1

            if book_counts:
                bk_df = pd.DataFrame(
                    sorted(book_counts.items(), key=lambda x: -x[1]),
                    columns=["Book", "Refs"],
                )
                fig = go.Figure(go.Bar(
                    x=bk_df["Refs"], y=bk_df["Book"],
                    orientation="h",
                    marker_color="#D4A853",
                    text=bk_df["Refs"], textposition="auto",
                ))
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E8E0D4",
                    height=max(250, len(bk_df) * 28),
                    margin=dict(l=0, r=0, t=10, b=10),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig, use_container_width=True)

            # OT/NT pie
            if ot > 0 or nt > 0:
                col1, col2 = st.columns([1, 2])
                with col1:
                    fig = go.Figure(go.Pie(
                        labels=["AT" if is_pt else "OT", "NT"],
                        values=[ot, nt],
                        marker_colors=["#4CAF50", "#2196F3"],
                        hole=0.45,
                        textinfo="percent+value",
                    ))
                    fig.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#E8E0D4",
                        height=250,
                        margin=dict(l=0, r=0, t=10, b=10),
                        showlegend=True,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown(
                        f'<div class="books-box">'
                        f'<strong>{"Livros mencionados" if is_pt else "Books mentioned"}:</strong><br/>'
                        f'{", ".join(books)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Nenhum livro encontrado" if is_pt else "No books found")

    # ── TAB: OVERVIEW ──
    with tab_overview:
        st.markdown('<div class="section-label">METADATA</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div class="aspect-card">'
            f'<div class="stat-row">'
            f'<div class="stat-item"><strong>{"Fonte" if is_pt else "Source"}:</strong> Torrey\'s Topical Textbook (1897)</div>'
            f'</div>'
            f'<div class="stat-row">'
            f'<div class="stat-item"><strong>Aspects:</strong> {len(aspects)}</div>'
            f'<div class="stat-item"><strong>Refs:</strong> {len(all_refs)}</div>'
            f'<div class="stat-item"><strong>Books:</strong> {n_books}</div>'
            f'<div class="stat-item"><strong>OT:</strong> {ot} · <strong>NT:</strong> {nt}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # See also — clicáveis
        see_also = json.loads(row.get("see_also_json", "[]"))
        if see_also:
            see_links = []
            for sa in see_also:
                slug = sa.lower().replace(" ", "_").replace(",", "").replace("'", "")
                see_links.append(f'<a href="?topic={slug}" style="color:#636EFA;text-decoration:none;">{_html.escape(sa)}</a>')
            st.markdown(
                f'<div class="see-also-box">'
                f'<strong>See also:</strong> {" · ".join(see_links)}'
                f'</div>',
                unsafe_allow_html=True,
            )


df = load_topics(TOPICS_FILE.stat().st_mtime)

# ---------------------------------------------------------------------------
# Check if a topic is selected
# ---------------------------------------------------------------------------
selected_slug = st.query_params.get("topic", "")

if selected_slug:
    if st.button("← " + ("Voltar" if is_pt else "Back")):
        st.query_params.clear()
        st.rerun()

    match = df[df["slug"] == selected_slug]
    if not match.empty:
        render_full_topic(match.iloc[0])
    else:
        st.error(f"Topic '{selected_slug}' not found")

else:
    st.markdown(
        '<div class="topic-title" style="font-size:1.8rem;">Explorador de Topicos</div>'
        if is_pt else
        '<div class="topic-title" style="font-size:1.8rem;">Topic Explorer</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        f"{len(df):,} topicos de Torrey's New Topical Textbook (1897)"
        if is_pt else
        f"{len(df):,} topics from Torrey's New Topical Textbook (1897)"
    )
    st.info(
        "Nave's Topical Bible esta temporariamente indisponivel enquanto o parser de referencias e aprimorado."
        if is_pt else
        "Nave's Topical Bible is temporarily unavailable while the reference parser is being improved."
    )

    query = st.text_input(
        "Buscar topico..." if is_pt else "Search topic...",
        placeholder="FAITH, GRACE, LOVE, ABRAHAM, SIN...",
        key="topic_query",
    )

    def render_card(row, src_label: str, key_prefix: str):
        if st.button(
            f"{row['topic']}\n{row['n_biblical_refs']} refs · {src_label}",
            key=f"{key_prefix}_{row['slug']}",
            use_container_width=True,
        ):
            st.query_params["topic"] = row["slug"]
            st.rerun()

    if not query:
        st.markdown('<div class="section-label">FEATURED TOPICS</div>', unsafe_allow_html=True)
        st.caption(
            "Topicos com mais referencias biblicas"
            if is_pt else
            "Topics with most biblical references"
        )
        featured = df.nlargest(12, "n_biblical_refs")
        cols = st.columns(4)
        for i, (_, row) in enumerate(featured.iterrows()):
            with cols[i % 4]:
                render_card(row, "Torrey", "feat")

    else:
        mask = df["topic"].str.contains(query.upper(), na=False)
        results = df[mask].sort_values("n_biblical_refs", ascending=False).head(20)

        if results.empty:
            st.warning("Nenhum resultado" if is_pt else "No results found")
        else:
            st.markdown(f"**{len(results)}** {'resultados' if is_pt else 'results'}")
            cols = st.columns(4)
            for i, (_, row) in enumerate(results.iterrows()):
                with cols[i % 4]:
                    render_card(row, "Torrey", "search")
