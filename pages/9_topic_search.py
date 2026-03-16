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
</style>
""", unsafe_allow_html=True)

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_topics(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{TOPICS_FILE}'").df()


def render_full_topic(row: pd.Series):
    """Render a full topic in study format."""
    import html as _html
    topic_name = row["topic"]

    src_labels = []
    if row["source_nav"]:
        src_labels.append("Nave's Topical Bible (1896)")
    if row["source_tor"]:
        src_labels.append("Torrey's Topical Textbook (1897)")

    st.markdown(f'<div class="topic-title">{_html.escape(topic_name)}</div>', unsafe_allow_html=True)
    st.caption(" · ".join(src_labels))

    # Stats row
    aspects = json.loads(row.get("aspects_json", "[]"))
    ot = int(row.get("ot_refs", 0))
    nt = int(row.get("nt_refs", 0))
    n_books = int(row.get("n_books", 0))

    st.markdown(
        f'<div class="stat-row">'
        f'<div class="stat-item"><strong>{int(row["n_biblical_refs"])}</strong> {"referencias" if is_pt else "references"}</div>'
        f'<div class="stat-item"><strong>{len(aspects)}</strong> aspects</div>'
        f'<div class="stat-item"><strong>{n_books}</strong> {"livros" if is_pt else "books"}</div>'
        f'<div class="stat-item"><strong>{ot}</strong> AT · <strong>{nt}</strong> NT</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Aspects
    if aspects:
        st.markdown('<div class="section-label">ASPECTS</div>', unsafe_allow_html=True)
        for asp in aspects:
            label = asp.get("label", "")
            refs = asp.get("references", [])
            source_tag = asp.get("source", "")

            tag_html = ""
            if source_tag == "NAV":
                tag_html = '<span class="tag-nav">NAV</span>'
            elif source_tag == "TOR":
                tag_html = '<span class="tag-tor">TOR</span>'

            refs_html = ""
            if refs:
                refs_html = f'<div class="aspect-refs">{", ".join(_html.escape(r) for r in refs)}</div>'

            st.markdown(
                f'<div class="aspect-card">'
                f'<span class="aspect-label">{_html.escape(label)}</span>{tag_html}'
                f'{refs_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Books mentioned
    books = json.loads(row.get("books_json", "[]"))
    if books:
        st.markdown(
            f'<div class="books-box">'
            f'<strong>{"Livros mencionados" if is_pt else "Books mentioned"}:</strong> '
            f'{", ".join(books)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # See also
    see_also = json.loads(row.get("see_also_json", "[]"))
    if see_also:
        st.markdown(
            f'<div class="see-also-box">'
            f'<strong>See also:</strong> {", ".join(see_also)}'
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
        f"{len(df):,} topicos de Nave (1896) + Torrey (1897)"
        if is_pt else
        f"{len(df):,} topics from Nave (1896) + Torrey (1897)"
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
            "Topicos presentes em ambas as fontes"
            if is_pt else
            "Topics present in both sources"
        )
        featured = df[df["n_sources"] == 2].nlargest(12, "n_biblical_refs")
        cols = st.columns(4)
        for i, (_, row) in enumerate(featured.iterrows()):
            with cols[i % 4]:
                render_card(row, "Nave + Torrey", "feat")

        st.markdown("---")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-label">NAVE HIGHLIGHTS</div>', unsafe_allow_html=True)
            nave_top = df[df["source_nav"] & ~df["source_tor"]].nlargest(8, "n_biblical_refs")
            for _, row in nave_top.iterrows():
                render_card(row, "Nave", "nave")

        with col_b:
            st.markdown('<div class="section-label">TORREY HIGHLIGHTS</div>', unsafe_allow_html=True)
            torrey_top = df[df["source_tor"] & ~df["source_nav"]].nlargest(8, "n_biblical_refs")
            for _, row in torrey_top.iterrows():
                render_card(row, "Torrey", "torrey")

    else:
        mask = df["topic"].str.contains(query.upper(), na=False)
        results = df[mask].sort_values("n_biblical_refs", ascending=False).head(20)

        if results.empty:
            st.warning("Nenhum resultado" if is_pt else "No results found")
        else:
            st.markdown(f"**{len(results)}** {'resultados' if is_pt else 'results'}")
            cols = st.columns(4)
            for i, (_, row) in enumerate(results.iterrows()):
                src_parts = []
                if row["source_nav"]:
                    src_parts.append("Nave")
                if row["source_tor"]:
                    src_parts.append("Torrey")
                with cols[i % 4]:
                    render_card(row, " + ".join(src_parts), "search")
