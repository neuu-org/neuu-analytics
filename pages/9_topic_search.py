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

con = duckdb.connect()
is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_topics(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{TOPICS_FILE}'").df()


def render_full_topic(row: pd.Series):
    """Render a full topic in study format from parquet row."""
    topic_name = row["topic"]

    src_labels = []
    if row["source_nav"]:
        src_labels.append("Nave's Topical Bible (1896)")
    if row["source_tor"]:
        src_labels.append("Torrey's Topical Textbook (1897)")

    st.markdown(f"## {topic_name}")
    st.caption(" · ".join(src_labels))

    # Metrics
    mcols = st.columns(4)
    mcols[0].metric("Refs", int(row["n_biblical_refs"]))
    aspects = json.loads(row.get("aspects_json", "[]"))
    mcols[1].metric("Aspects", len(aspects))
    mcols[2].metric("Livros" if is_pt else "Books", int(row.get("n_books", 0)))
    mcols[3].metric("AT/NT" if is_pt else "OT/NT", f"{int(row.get('ot_refs', 0))}/{int(row.get('nt_refs', 0))}")

    st.markdown("---")

    # Aspects — the core content
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
    books = json.loads(row.get("books_json", "[]"))
    if books:
        st.markdown("---")
        st.markdown(f"**{'Livros mencionados' if is_pt else 'Books mentioned'}:** {', '.join(books)}")

    # See also
    see_also = json.loads(row.get("see_also_json", "[]"))
    if see_also:
        st.markdown(f"**See also:** {', '.join(see_also)}")


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
    title = "Explorar Topicos" if is_pt else "Explore Topics"
    st.title(f"📖 {title}")

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
        st.markdown("#### " + ("Topicos em Destaque" if is_pt else "Featured Topics"))
        st.caption(
            "Topicos presentes em ambas as fontes, ordenados por referencias"
            if is_pt else
            "Topics present in both sources, sorted by references"
        )
        featured = df[df["n_sources"] == 2].nlargest(12, "n_biblical_refs")
        cols = st.columns(4)
        for i, (_, row) in enumerate(featured.iterrows()):
            with cols[i % 4]:
                render_card(row, "Nave + Torrey", "feat")

        st.markdown("---")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### " + ("Destaques Nave" if is_pt else "Nave Highlights"))
            nave_top = df[df["source_nav"] & ~df["source_tor"]].nlargest(8, "n_biblical_refs")
            for _, row in nave_top.iterrows():
                render_card(row, "Nave", "nave")

        with col_b:
            st.markdown("#### " + ("Destaques Torrey" if is_pt else "Torrey Highlights"))
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
