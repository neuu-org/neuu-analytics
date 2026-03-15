"""
Pagina de analise do dataset Bible Cross-References.
Placeholder — sera implementado quando o dataset tiver dados.
"""

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "data" / "crossrefs.parquet"

st.set_page_config(page_title="Cross-References | NEUU Analytics", page_icon="🔗", layout="wide")

st.title("🔗 Bible Cross-References — Analise")
st.caption("1.1M+ referencias cruzadas biblicas (OpenBible + TSK)")

if not PARQUET.exists():
    st.info(
        "Dataset ainda nao disponivel.\n\n"
        "O repositorio `neuu-org/bible-crossrefs-dataset` esta sendo preparado.\n\n"
        "Quando estiver pronto, habilite no `config.yaml` e execute `python sync.py`."
    )
else:
    st.success("Dados carregados! Analises em construcao.")
