"""
NEUU Analytics — Dashboard central dos datasets biblicos.
Entry point do Streamlit multi-page app.
"""

from pathlib import Path

import duckdb
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"
DATA_DIR = ROOT / "data"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


st.set_page_config(
    page_title="NEUU Analytics",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS — identidade visual NEUU
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header brand */
    .neuu-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 8px 0 24px 0;
    }
    .neuu-logo {
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: 4px;
        color: #D4A853;
    }
    .neuu-logo span {
        color: #E8E0D4;
        font-weight: 300;
    }
    .neuu-tagline {
        font-size: 0.85rem;
        color: #8B8072;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* Dataset cards */
    .dataset-card {
        background: #1A1D24;
        border: 1px solid #2A2D34;
        border-radius: 12px;
        padding: 24px;
        transition: border-color 0.2s;
    }
    .dataset-card:hover {
        border-color: #D4A853;
    }
    .dataset-card h3 {
        color: #E8E0D4;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .dataset-card .metric {
        font-size: 2rem;
        font-weight: 700;
        color: #D4A853;
    }
    .dataset-card .desc {
        font-size: 0.85rem;
        color: #8B8072;
        margin-top: 8px;
    }
    .dataset-card .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .badge-active {
        background: rgba(212, 168, 83, 0.15);
        color: #D4A853;
        border: 1px solid rgba(212, 168, 83, 0.3);
    }
    .badge-pending {
        background: rgba(139, 128, 114, 0.15);
        color: #8B8072;
        border: 1px solid rgba(139, 128, 114, 0.3);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        border-right: 1px solid #2A2D34;
    }

    /* Divider */
    .neuu-divider {
        border: none;
        border-top: 1px solid #2A2D34;
        margin: 32px 0;
    }

    /* Footer */
    .neuu-footer {
        text-align: center;
        font-size: 0.75rem;
        color: #5A5550;
        padding: 24px 0;
        letter-spacing: 1px;
    }

    /* Hide default streamlit header */
    header[data-testid="stHeader"] {
        background: #0E1117;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="neuu-header">
        <div>
            <div class="neuu-logo">NEUU <span>Analytics</span></div>
            <div class="neuu-tagline">Nossa Essencia Uniao e Upgrade</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

config = load_config()

# Verificar se os dados foram sincronizados
parquet_files = list(DATA_DIR.glob("*.parquet"))

if not parquet_files:
    st.warning(
        "Nenhum dado encontrado. Execute o sync primeiro:\n\n"
        "```bash\n"
        "pip install -r requirements.txt\n"
        "python sync.py\n"
        "```"
    )
    st.stop()

# ---------------------------------------------------------------------------
# Dataset cards
# ---------------------------------------------------------------------------
st.markdown('<hr class="neuu-divider">', unsafe_allow_html=True)

cols = st.columns(len(config["datasets"]))
for col, (key, cfg) in zip(cols, config["datasets"].items()):
    with col:
        parquet = DATA_DIR / f"{key}.parquet"
        has_data = parquet.exists()
        enabled = cfg.get("enabled", False)

        if has_data:
            count = duckdb.sql(f"SELECT COUNT(*) FROM '{parquet}'").fetchone()[0]
            size_mb = parquet.stat().st_size / 1024 / 1024
            badge = '<span class="badge badge-active">Ativo</span>'
            metric_html = f'<div class="metric">{count:,}</div>'
            detail = f"registros &middot; {size_mb:.1f} MB"
        else:
            badge = '<span class="badge badge-pending">Em breve</span>'
            metric_html = '<div class="metric" style="color:#5A5550;">—</div>'
            detail = "aguardando dados"

        st.markdown(
            f"""
            <div class="dataset-card">
                <h3>{cfg['name']} {badge}</h3>
                {metric_html}
                <div class="desc">{detail}</div>
                <div class="desc" style="margin-top:12px;">{cfg['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="neuu-divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Quick stats
# ---------------------------------------------------------------------------
if (DATA_DIR / "commentaries.parquet").exists():
    parquet = DATA_DIR / "commentaries.parquet"
    stats = duckdb.sql(
        f"""
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT book) as books,
            COUNT(DISTINCT author) FILTER (WHERE author IS NOT NULL) as authors,
            COUNT(*) FILTER (WHERE author IS NOT NULL) as commentaries,
            COUNT(*) FILTER (WHERE author IS NULL) as empty_verses
        FROM '{parquet}'
        """
    ).fetchone()

    st.markdown("### Panorama Geral")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Livros Biblicos", stats[1])
    c2.metric("Autores", f"{stats[2]:,}")
    c3.metric("Comentarios", f"{stats[3]:,}")
    c4.metric("Versiculos Vazios", f"{stats[4]:,}")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="neuu-footer">
        NEUU &middot; Open datasets & AI tools for biblical scholarship
    </div>
    """,
    unsafe_allow_html=True,
)
