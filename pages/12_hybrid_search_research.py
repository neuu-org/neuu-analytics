"""
NEUU Analytics — Hybrid Search Research (TCC)
Pagina dedicada aos resultados da pesquisa de busca hibrida biblica.
"""

import json
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Paths (relative to repo root for Streamlit Cloud compatibility)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "research"
WRITING_DIR = DATA_DIR
FIGURES_DIR = DATA_DIR / "figures"
EXP5_DIR = DATA_DIR / "exp5"
CCEL_DIR = DATA_DIR / "ccel_bridge"

is_pt = st.session_state.get("language", "Portugues") == "Portugues"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div style="font-size:1.8rem;font-weight:700;color:#D4A853;letter-spacing:2px;">'
    + ("Pesquisa: Busca Hibrida Biblica" if is_pt else "Research: Bible Hybrid Search")
    + "</div>"
    + '<div style="font-size:0.8rem;color:#8B8072;margin-bottom:1.5rem;">'
    + ("TCC — MBA Data Science and Analytics, USP/ESALQ" if is_pt else "Thesis — MBA Data Science and Analytics, USP/ESALQ")
    + "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_names = (
    ["Resumo", "Resultados", "Figuras", "Texto Completo", "Dados"]
    if is_pt
    else ["Summary", "Results", "Figures", "Full Text", "Data"]
)

tab_summary, tab_results, tab_figures, tab_text, tab_data = st.tabs(tab_names)

# ===== TAB: RESUMO =====
with tab_summary:
    st.markdown("### " + ("Resumo da Pesquisa" if is_pt else "Research Summary"))

    col1, col2, col3 = st.columns(3)
    col1.metric("Experimentos", "5")
    col2.metric("Configuracoes" if is_pt else "Configurations", "46+")
    col3.metric("Queries", "50")

    col4, col5, col6 = st.columns(3)
    col4.metric("Gold Refs", "445")
    col5.metric("Datasets", "8")
    col6.metric("Embeddings", "1M+")

    st.markdown("---")

    st.markdown(
        "#### " + ("Evolucao dos Resultados" if is_pt else "Results Evolution")
    )

    evolution_data = {
        "Experiment": ["Exp1", "Exp2", "Exp3", "Exp4 (unified)", "Exp5 (CCEL)"],
        "P@10": [0.202, 0.216, 0.284, 0.178, 0.338],
        "R@20": [0.326, 0.310, 0.419, 0.243, 0.513],
        "MAP": [0.196, 0.203, 0.282, 0.175, 0.334],
    }
    st.dataframe(evolution_data, use_container_width=True)

    st.markdown("---")
    st.markdown("#### " + ("Achados Principais" if is_pt else "Key Findings"))

    findings = [
        ("BM25 competitivo" if is_pt else "BM25 competitive",
         "17 traducoes funcionam como expansao implicita de consulta" if is_pt
         else "17 translations act as implicit query expansion"),
        ("Embedding large +27%" if is_pt else "Large embedding +27%",
         "Maior ganho individual: trocar 1536d por 3072d" if is_pt
         else "Largest single gain: switching from 1536d to 3072d"),
        ("Multi-versao > Unified" if is_pt else "Multi-version > Unified",
         "Fusao degrada qualidade em 37% — redundancia eh feature" if is_pt
         else "Fusion degrades quality by 37% — redundancy is a feature"),
        ("CCEL +21% P@10, +23% R@20",
         "Ganho inversamente proporcional a dificuldade: extreme +41%, baseline ~0%" if is_pt
         else "Gains inversely proportional to difficulty: extreme +41%, baseline ~0%"),
        ("p<0.001 (Bonferroni)" if is_pt else "p<0.001 (Bonferroni)",
         "5/7 metricas estatisticamente significativas apos correcao" if is_pt
         else "5/7 metrics statistically significant after correction"),
    ]

    for title, desc in findings:
        st.markdown(f"**{title}** — {desc}")

# ===== TAB: RESULTADOS =====
with tab_results:
    st.markdown("### " + ("Resultados do Experimento 5" if is_pt else "Experiment 5 Results"))

    # Load exp5 summary
    summary_path = EXP5_DIR / "summary.json"
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as f:
            exp5 = json.load(f)

        # Aggregate table
        st.markdown("#### " + ("Metricas Globais" if is_pt else "Global Metrics"))
        agg = exp5.get("aggregate", {})
        rows = []
        for cfg_id, metrics in agg.items():
            rows.append({
                "Config": cfg_id,
                "P@5": round(metrics.get("p@5", 0), 3),
                "P@10": round(metrics.get("p@10", 0), 3),
                "R@10": round(metrics.get("r@10", 0), 3),
                "R@20": round(metrics.get("r@20", 0), 3),
                "MAP": round(metrics.get("map", 0), 3),
                "NDCG@10": round(metrics.get("ndcg@10", 0), 3),
                "MRR": round(metrics.get("mrr", 0), 3),
            })
        st.dataframe(rows, use_container_width=True)

        # Statistical significance
        st.markdown("#### " + ("Significancia Estatistica" if is_pt else "Statistical Significance"))
        st.markdown(
            ("E5_ccel_inject vs E5_ctrl (n=50, Bonferroni α=0,0071):" if is_pt
             else "E5_ccel_inject vs E5_ctrl (n=50, Bonferroni α=0.0071):")
        )

        stat_data = [
            {"Metrica": "P@10", "Delta": "+0.058 (+21%)", "p-value": "0.001", "Cohen d": "0.50", "Sig": "***"},
            {"Metrica": "R@10", "Delta": "+0.072 (+22%)", "p-value": "<0.001", "Cohen d": "0.53", "Sig": "***"},
            {"Metrica": "R@20", "Delta": "+0.095 (+23%)", "p-value": "0.001", "Cohen d": "0.50", "Sig": "***"},
            {"Metrica": "MAP", "Delta": "+0.057 (+20%)", "p-value": "0.002", "Cohen d": "0.45", "Sig": "**"},
            {"Metrica": "NDCG@10", "Delta": "+0.072 (+19%)", "p-value": "<0.001", "Cohen d": "0.59", "Sig": "***"},
            {"Metrica": "MRR", "Delta": "+0.074 (+11%)", "p-value": "0.010", "Cohen d": "0.38", "Sig": "*"},
        ]
        st.dataframe(stat_data, use_container_width=True)

        # Per-difficulty
        st.markdown("#### " + ("Ganho por Dificuldade (R@20)" if is_pt else "Gain by Difficulty (R@20)"))
        diff_data = [
            {"Dificuldade": "Extreme", "Ctrl": 0.357, "CCEL Inject": 0.505, "Delta": "+41%"},
            {"Dificuldade": "Hard", "Ctrl": 0.370, "CCEL Inject": 0.510, "Delta": "+38%"},
            {"Dificuldade": "Medium", "Ctrl": 0.524, "CCEL Inject": 0.660, "Delta": "+26%"},
            {"Dificuldade": "Medium-hard", "Ctrl": 0.427, "CCEL Inject": 0.447, "Delta": "+5%"},
            {"Dificuldade": "Baseline", "Ctrl": 0.394, "CCEL Inject": 0.389, "Delta": "-1%"},
        ]
        st.dataframe(diff_data, use_container_width=True)
    else:
        st.warning("Dados do Exp5 nao encontrados" if is_pt else "Exp5 data not found")

    # CCEL Coverage
    st.markdown("#### " + ("Cobertura CCEL" if is_pt else "CCEL Coverage"))
    coverage_path = CCEL_DIR / "coverage_analysis.json"
    if coverage_path.exists():
        with open(coverage_path, encoding="utf-8") as f:
            coverage = json.load(f)
        per_diff = coverage.get("per_difficulty", {})
        cov_rows = []
        for diff, stats in sorted(per_diff.items()):
            cov_rows.append({
                "Dificuldade": diff,
                "Gold Refs": stats.get("gold_refs", 0),
                "CCEL Found": stats.get("ccel_covered", 0),
                "Cobertura": f"{stats.get('coverage_pct', 0)}%",
            })
        glob = coverage.get("global", {})
        cov_rows.append({
            "Dificuldade": "GLOBAL",
            "Gold Refs": glob.get("total_gold", 0),
            "CCEL Found": glob.get("covered", 0),
            "Cobertura": f"{glob.get('coverage_pct', 0)}%",
        })
        st.dataframe(cov_rows, use_container_width=True)

# ===== TAB: FIGURAS =====
with tab_figures:
    st.markdown("### " + ("Figuras da Pesquisa" if is_pt else "Research Figures"))

    figures = [
        ("fig1_evolution_exp1_to_exp5.png",
         "Figura 1. Evolucao Exp1 a Exp5 — Precision e Recall" if is_pt
         else "Figure 1. Evolution Exp1 to Exp5 — Precision and Recall"),
        ("fig4_difficulty_gain.png",
         "Figura 4. Ganho R@20 por dificuldade — CCEL vs Controle" if is_pt
         else "Figure 4. R@20 Gain by Difficulty — CCEL vs Control"),
        ("fig2_heatmap_difficulty_config.png",
         "Figura 2. Heatmap Config x Dificuldade (P@10 e R@20)" if is_pt
         else "Figure 2. Heatmap Config x Difficulty (P@10 and R@20)"),
        ("fig3_ccel_weight_sweep.png",
         "Figura 3. Curva de peso CCEL — Reranking vs Injecao" if is_pt
         else "Figure 3. CCEL Weight Sweep — Reranking vs Injection"),
        ("fig5_boxplot_ctrl_vs_inject.png",
         "Figura 5. Box plots — Ctrl vs CCEL Inject (n=50)" if is_pt
         else "Figure 5. Box plots — Ctrl vs CCEL Inject (n=50)"),
        ("fig6_scatter_precision_recall.png",
         "Figura 6. Precision x Recall — Todas configuracoes Exp5" if is_pt
         else "Figure 6. Precision x Recall — All Exp5 configurations"),
        ("fig7_negative_controls.png",
         "Figura 7. Controles negativos — Random e Shuffled vs CCEL real" if is_pt
         else "Figure 7. Negative controls — Random and Shuffled vs Real CCEL"),
    ]

    for filename, caption in figures:
        fig_path = FIGURES_DIR / filename
        if fig_path.exists():
            st.image(str(fig_path), caption=caption, use_container_width=True)
            st.markdown("---")
        else:
            st.warning(f"Figura nao encontrada: {filename}")

# ===== TAB: TEXTO COMPLETO =====
with tab_text:
    st.markdown("### " + ("Texto Completo do TCC" if is_pt else "Full Thesis Text"))

    chapters = [
        ("00-resumo.md", "Resumo / Abstract"),
        ("01-introducao.md", "Introducao" if is_pt else "Introduction"),
        ("02-referencial-teorico.md", "Referencial Teorico" if is_pt else "Theoretical Framework"),
        ("03-material-e-metodos.md", "Material e Metodos" if is_pt else "Material and Methods"),
        ("04-resultados-e-discussao.md", "Resultados e Discussao" if is_pt else "Results and Discussion"),
        ("05-conclusao.md", "Conclusao" if is_pt else "Conclusion"),
        ("06-referencias.md", "Referencias" if is_pt else "References"),
    ]

    selected_chapter = st.selectbox(
        "Capitulo" if is_pt else "Chapter",
        [name for _, name in chapters],
    )

    for filename, name in chapters:
        if name == selected_chapter:
            chapter_path = WRITING_DIR / filename
            if chapter_path.exists():
                content = chapter_path.read_text(encoding="utf-8")
                st.markdown(content)
            else:
                st.warning(f"Arquivo nao encontrado: {filename}")
            break

# ===== TAB: DADOS =====
with tab_data:
    st.markdown("### " + ("Dados da Pesquisa" if is_pt else "Research Data"))

    st.markdown(
        "#### " + ("Ecossistema de Datasets" if is_pt else "Dataset Ecosystem")
    )

    datasets = [
        {"Dataset": "Texto Biblico" if is_pt else "Bible Text", "Escala": "17 traducoes, 528.995 versiculos", "Formato": "JSON", "Papel": "Corpus de recuperacao"},
        {"Dataset": "Embeddings", "Escala": "1.057.990 vetores (small+large)", "Formato": "PostgreSQL pgvector", "Papel": "Busca semantica"},
        {"Dataset": "Comentarios" if is_pt else "Commentaries", "Escala": "55.925 comentarios, 31.218 versiculos", "Formato": "JSON (4 camadas)", "Papel": "Validacao teologica"},
        {"Dataset": "Refs Cruzadas" if is_pt else "Cross-refs", "Escala": "1.117.491 arestas", "Formato": "JSON", "Papel": "Validacao gold"},
        {"Dataset": "Topicos" if is_pt else "Topics", "Escala": "7.873 unificados", "Formato": "JSON", "Papel": "Validacao tematica"},
        {"Dataset": "Dicionarios" if is_pt else "Dictionaries", "Escala": "20.900 entradas", "Formato": "JSON", "Papel": "Validacao definicional"},
        {"Dataset": "Gazetteers", "Escala": "9.552 entidades + simbolos", "Formato": "JSON", "Papel": "Classificacao semantica"},
        {"Dataset": "CCEL Embeddings", "Escala": "1.513.182 paragrafos embedados", "Formato": "Parquet", "Papel": "Enriquecimento (Exp5)"},
    ]
    st.dataframe(datasets, use_container_width=True)

    st.markdown("---")
    st.markdown(
        "#### " + ("Arquivos de Resultados" if is_pt else "Result Files")
    )

    result_files = {
        "Gold Set": str(RESEARCH_ROOT / "experiments" / "gold_set" / "gold_set_final.json"),
        "Exp5 Summary": str(EXP5_DIR / "summary.json"),
        "CCEL Bridge Index": str(CCEL_DIR / "query_commentary_index.json"),
        "CCEL Coverage": str(CCEL_DIR / "coverage_analysis.json"),
        "Query Translations": str(CCEL_DIR / "query_translations.json"),
    }

    for name, path in result_files.items():
        p = Path(path)
        status = "Found" if p.exists() else "Missing"
        size = f"{p.stat().st_size / 1024:.1f} KB" if p.exists() else "—"
        st.markdown(f"- **{name}**: `{p.name}` ({size}) — {status}")
