"""
NEUU Analytics — Dashboard central dos datasets biblicos.
Entry point do Streamlit multi-page app.
"""

from pathlib import Path

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

st.title("📊 NEUU Analytics")
st.caption("Dashboard central de visibilidade dos datasets biblicos da org NEUU")

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

# Overview cards
st.header("Datasets Registrados")

cols = st.columns(len(config["datasets"]))
for col, (key, cfg) in zip(cols, config["datasets"].items()):
    with col:
        parquet = DATA_DIR / f"{key}.parquet"
        has_data = parquet.exists()

        if has_data:
            import duckdb

            count = duckdb.sql(f"SELECT COUNT(*) FROM '{parquet}'").fetchone()[0]
            st.metric(cfg["name"], f"{count:,} registros")
        else:
            st.metric(cfg["name"], "—")

        status = "Habilitado" if cfg.get("enabled") else "Desabilitado"
        st.caption(f"{cfg['description']}\n\nStatus: {status}")

        if has_data:
            size_mb = parquet.stat().st_size / 1024 / 1024
            st.caption(f"Parquet: {size_mb:.1f} MB")

st.divider()
st.markdown("Use o menu lateral para navegar entre as analises de cada dataset.")
st.caption(f"Org: `{config['org']}` · Datasets: {len(config['datasets'])}")
