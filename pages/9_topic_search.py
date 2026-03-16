"""
Topic Explorer — Browse and study biblical topics.
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
TOPICS_REPO = ROOT / "datasets" / "bible-topics-dataset" / "data" / "01_parsed"

if not TOPICS_FILE.exists():
    st.info("Dados nao encontrados. Execute `python sync.py topics`.")
    st.stop()

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_topics(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{TOPICS_FILE}'").df()


def load_full_topic(slug: str) -> dict | None:
    """Load the full JSON for a topic from the repo."""
    letter = slug[0].upper() if slug else ""
    path = TOPICS_REPO / letter / f"{slug}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def render_full_topic(full: dict):
    """Render a full topic in study format."""
    topic_name = full.get("topic", "")
    sources = full.get("sources", [])
    stats = full.get("stats", {})

    src_labels = []
    for s in sources:
        if s == "NAV":
            src_labels.append("Nave's Topical Bible (1896)")
        elif s == "TOR":
            src_labels.append("Torrey's Topical Textbook (1897)")

    st.markdown(f"## {topic_name}")
    st.caption(" · ".join(src_labels))

    # Metrics
    mcols = st.columns(4)
    mcols[0].metric("Refs", stats.get("total_refs", 0))
    mcols[1].metric("Aspects", stats.get("total_aspects", 0))
    mcols[2].metric(
        "Livros" if is_pt else "Books",
        stats.get("books_count", 0),
    )
    ot = stats.get("ot_refs", 0)
    nt = stats.get("nt_refs", 0)
    mcols[3].metric("AT/NT" if is_pt else "OT/NT", f"{ot}/{nt}")

    st.markdown("---")

    # Aspects — the core content
    aspects = full.get("aspects", [])
    if aspects:
        for asp in aspects:
            label = asp.get("label", "")
            refs = asp.get("references", [])
            source_tag = asp.get("source", "")

            if source_tag == "NAV":
                badge = '<span style="background:#4CAF50;color:#fff;padding:1px 6px;border-radius:3px;font-size:0.6rem;margin-left:6px;">NAV</span>'
            elif source_tag == "TOR":
                badge = '<span style="background:#2196F3;color:#fff;padding:1px 6px;border-radius:3px;font-size:0.6rem;margin-left:6px;">TOR</span>'
            else:
                badge = ""

            if label and refs:
                refs_md = ", ".join(f"`{r}`" for r in refs)
                st.markdown(f"**{label}**{badge}", unsafe_allow_html=True)
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{refs_md}")
            elif label:
                st.markdown(f"**{label}**{badge}", unsafe_allow_html=True)
            elif refs:
                refs_md = ", ".join(f"`{r}`" for r in refs)
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{refs_md}")

    # Books mentioned
    books = full.get("books_mentioned", [])
    if books:
        st.markdown("---")
        st.markdown(f"**{'Livros mencionados' if is_pt else 'Books mentioned'}:** {', '.join(books)}")

    # See also
    see_also = full.get("see_also", [])
    if see_also:
        st.markdown(f"**See also:** {', '.join(see_also)}")


df = load_topics(TOPICS_FILE.stat().st_mtime)

# ---------------------------------------------------------------------------
# Check if a topic is selected
# ---------------------------------------------------------------------------
selected_slug = st.query_params.get("topic", "")

if selected_slug:
    # Back button
    if st.button("← " + ("Voltar" if is_pt else "Back")):
        st.query_params.clear()
        st.rerun()

    full = load_full_topic(selected_slug)
    if full:
        render_full_topic(full)
    else:
        st.error(f"Topic '{selected_slug}' not found")

else:
    # ---------------------------------------------------------------------------
    # Main page: search + featured cards
    # ---------------------------------------------------------------------------
    title = "Explorar Topicos" if is_pt else "Explore Topics"
    st.title(f"📖 {title}")

    query = st.text_input(
        "Buscar topico..." if is_pt else "Search topic...",
        placeholder="FAITH, GRACE, LOVE, ABRAHAM, SIN...",
        key="topic_query",
    )

    def render_card_grid(topics_df: pd.DataFrame, border_color: str, source_label: str):
        """Render a grid of topic cards as buttons."""
        cols = st.columns(4)
        for i, (_, row) in enumerate(topics_df.iterrows()):
            with cols[i % 4]:
                if st.button(
                    f"📖 {row['topic']}\n{row['n_biblical_refs']} refs",
                    key=f"card_{row['slug']}",
                    use_container_width=True,
                ):
                    st.query_params["topic"] = row["slug"]
                    st.rerun()

    if not query:
        # Featured: both sources
        st.markdown("#### " + ("Topicos em Destaque" if is_pt else "Featured Topics"))
        st.caption(
            "Topicos presentes em ambas as fontes, ordenados por referencias"
            if is_pt else
            "Topics present in both sources, sorted by references"
        )
        featured = df[df["n_sources"] == 2].nlargest(12, "n_biblical_refs")
        render_card_grid(featured, "#D4A853", "Nave + Torrey")

        st.markdown("---")

        # Nave only highlights
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### " + ("Destaques Nave" if is_pt else "Nave Highlights"))
            nave_top = df[df["source_nav"] & ~df["source_tor"]].nlargest(8, "n_biblical_refs")
            for _, row in nave_top.iterrows():
                if st.button(
                    f"📗 {row['topic']} — {row['n_biblical_refs']} refs",
                    key=f"nave_{row['slug']}",
                    use_container_width=True,
                ):
                    st.query_params["topic"] = row["slug"]
                    st.rerun()

        with col_b:
            st.markdown("#### " + ("Destaques Torrey" if is_pt else "Torrey Highlights"))
            torrey_top = df[df["source_tor"] & ~df["source_nav"]].nlargest(8, "n_biblical_refs")
            for _, row in torrey_top.iterrows():
                if st.button(
                    f"📘 {row['topic']} — {row['n_biblical_refs']} refs",
                    key=f"torrey_{row['slug']}",
                    use_container_width=True,
                ):
                    st.query_params["topic"] = row["slug"]
                    st.rerun()

    else:
        # Search results
        mask = df["topic"].str.contains(query.upper(), na=False)
        results = df[mask].sort_values("n_biblical_refs", ascending=False).head(20)

        if results.empty:
            st.warning("Nenhum resultado" if is_pt else "No results found")
        else:
            st.markdown(f"**{len(results)}** {'resultados' if is_pt else 'results'}")
            for _, row in results.iterrows():
                src_parts = []
                if row["source_nav"]:
                    src_parts.append("Nave")
                if row["source_tor"]:
                    src_parts.append("Torrey")
                src_text = " + ".join(src_parts)

                if st.button(
                    f"📖 {row['topic']}  —  {row['n_biblical_refs']} refs · {src_text}",
                    key=f"search_{row['slug']}",
                    use_container_width=True,
                ):
                    st.query_params["topic"] = row["slug"]
                    st.rerun()
