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


df = load_topics(TOPICS_FILE.stat().st_mtime)

title = "Explorar Topicos" if is_pt else "Explore Topics"
st.title(f"📖 {title}")

# ---------------------------------------------------------------------------
# Search bar
# ---------------------------------------------------------------------------
query = st.text_input(
    "Buscar topico..." if is_pt else "Search topic...",
    placeholder="FAITH, GRACE, LOVE, ABRAHAM, SIN...",
    key="topic_query",
)

# ---------------------------------------------------------------------------
# Featured topics (when no search)
# ---------------------------------------------------------------------------
if not query:
    st.markdown(
        "#### " + ("Topicos em Destaque" if is_pt else "Featured Topics")
    )
    st.caption(
        "Topicos com mais referencias biblicas nas duas fontes (Nave + Torrey)"
        if is_pt else
        "Topics with the most biblical references across both sources (Nave + Torrey)"
    )

    # Top topics by refs that have 2 sources
    featured = df[df["n_sources"] == 2].nlargest(12, "n_biblical_refs")

    cols = st.columns(4)
    for i, (_, row) in enumerate(featured.iterrows()):
        with cols[i % 4]:
            refs_label = f"{row['n_biblical_refs']} refs"
            src = "Nave + Torrey"
            st.markdown(
                f"""<div style="
                    background: linear-gradient(135deg, #1A1D24 0%, #2A2D34 100%);
                    border: 1px solid #3A3D44;
                    border-left: 3px solid #D4A853;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-bottom: 8px;
                    cursor: pointer;
                ">
                    <div style="font-weight:600;color:#E8E0D4;font-size:0.9rem;">{row['topic']}</div>
                    <div style="color:#D4A853;font-size:0.75rem;margin-top:4px;">{refs_label}</div>
                    <div style="color:#5A5550;font-size:0.65rem;margin-top:2px;">{src}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Also show some single-source highlights
    st.markdown(
        "#### " + ("Apenas Nave" if is_pt else "Nave Only — Highlights")
    )
    nave_top = df[df["source_nav"] & ~df["source_tor"]].nlargest(8, "n_biblical_refs")
    cols = st.columns(4)
    for i, (_, row) in enumerate(nave_top.iterrows()):
        with cols[i % 4]:
            st.markdown(
                f"""<div style="
                    background: #1A1D24;
                    border: 1px solid #2A2D34;
                    border-left: 3px solid #4CAF50;
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 8px;
                ">
                    <div style="font-weight:600;color:#E8E0D4;font-size:0.85rem;">{row['topic']}</div>
                    <div style="color:#4CAF50;font-size:0.7rem;margin-top:3px;">{row['n_biblical_refs']} refs · Nave</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown(
        "#### " + ("Apenas Torrey" if is_pt else "Torrey Only — Highlights")
    )
    torrey_top = df[df["source_tor"] & ~df["source_nav"]].nlargest(8, "n_biblical_refs")
    cols = st.columns(4)
    for i, (_, row) in enumerate(torrey_top.iterrows()):
        with cols[i % 4]:
            st.markdown(
                f"""<div style="
                    background: #1A1D24;
                    border: 1px solid #2A2D34;
                    border-left: 3px solid #2196F3;
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 8px;
                ">
                    <div style="font-weight:600;color:#E8E0D4;font-size:0.85rem;">{row['topic']}</div>
                    <div style="color:#2196F3;font-size:0.7rem;margin-top:3px;">{row['n_biblical_refs']} refs · Torrey</div>
                </div>""",
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# Search results
# ---------------------------------------------------------------------------
if query:
    mask = df["topic"].str.contains(query.upper(), na=False)
    results = df[mask].sort_values("n_biblical_refs", ascending=False).head(20)

    if results.empty:
        st.warning("Nenhum resultado" if is_pt else "No results found")
    else:
        st.markdown(f"**{len(results)}** {'resultados' if is_pt else 'results'}")

        # Show as clickable cards
        for _, row in results.iterrows():
            src_parts = []
            if row["source_nav"]:
                src_parts.append("Nave")
            if row["source_tor"]:
                src_parts.append("Torrey")
            src_text = " + ".join(src_parts)
            border_color = "#D4A853" if len(src_parts) > 1 else ("#4CAF50" if "Nave" in src_parts else "#2196F3")

            with st.expander(f"📖 {row['topic']}  —  {row['n_biblical_refs']} refs · {src_text}"):
                # Load full topic data
                full = load_full_topic(row["slug"])
                if full:
                    # Metrics row
                    mcols = st.columns(4)
                    mcols[0].metric("Refs", full["stats"]["total_refs"])
                    mcols[1].metric("Aspects", full["stats"]["total_aspects"])
                    mcols[2].metric("Books", full["stats"]["books_count"])
                    mcols[3].metric("Sources", len(full["sources"]))

                    # Aspects
                    aspects = full.get("aspects", [])
                    if aspects:
                        st.markdown("**Aspects:**")
                        for asp in aspects:
                            label = asp.get("label", "")
                            refs = asp.get("references", [])
                            source_tag = asp.get("source", "")
                            source_badge = f' `{source_tag}`' if source_tag else ""

                            if refs:
                                refs_str = ", ".join(refs[:5])
                                if len(refs) > 5:
                                    refs_str += f" (+{len(refs)-5})"
                                st.markdown(f"- **{label}**{source_badge} — {refs_str}")
                            elif label:
                                st.markdown(f"- **{label}**{source_badge}")

                    # Books mentioned
                    books = full.get("books_mentioned", [])
                    if books:
                        st.markdown(f"**Books:** {', '.join(books)}")

                    # See also
                    see_also = full.get("see_also", [])
                    if see_also:
                        st.markdown(f"**See also:** {', '.join(see_also)}")
                else:
                    st.caption("Full topic data not available (run sync first)")
