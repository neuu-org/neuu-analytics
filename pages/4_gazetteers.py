"""
Pagina de analise do dataset Bible Gazetteers.
2.474 entidades, 347 simbolos e 436 relacionamentos biblicos.
"""

import html
import json
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from loading import show_loading

show_loading()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ENTITIES = DATA_DIR / "gazetteers_entities.parquet"
SYMBOLS = DATA_DIR / "gazetteers_symbols.parquet"
RELS = DATA_DIR / "gazetteers_relationships.parquet"

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E8E0D4",
)

if not ENTITIES.exists():
    st.info("Dados nao encontrados. Execute `python sync.py gazetteers`.")
    st.stop()

con = duckdb.connect()

is_pt = st.session_state.get("language", "English") == "Portugues"


@st.cache_data(ttl=3600)
def load_entities(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{ENTITIES}'").df()


@st.cache_data(ttl=3600)
def load_symbols(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{SYMBOLS}'").df()


@st.cache_data(ttl=3600)
def load_rels(mtime: float) -> pd.DataFrame:
    return con.sql(f"SELECT * FROM '{RELS}'").df()


df_ent = load_entities(ENTITIES.stat().st_mtime)
df_sym = load_symbols(SYMBOLS.stat().st_mtime)
df_rel = load_rels(RELS.stat().st_mtime)

title = "Dicionario Biblico — Analise" if is_pt else "Bible Gazetteers — Analysis"
st.title(f"📚 {title}")
st.caption(
    "2.474 entidades, 347 simbolos e 436 relacionamentos biblicos"
    if is_pt else
    "2,474 entities, 347 symbols and 436 biblical relationships"
)

# ---------------------------------------------------------------------------
# 1. Visao Geral
# ---------------------------------------------------------------------------
st.header("1. Visao Geral" if is_pt else "1. Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Entidades" if is_pt else "Entities", f"{len(df_ent):,}")
c2.metric("Simbolos" if is_pt else "Symbols", f"{len(df_sym):,}")
c3.metric("Relacionamentos" if is_pt else "Relationships", f"{len(df_rel):,}")
c4.metric("Tipos" if is_pt else "Types", df_ent["type"].nunique())

col1, col2 = st.columns(2)

with col1:
    # Distribuicao de entidades por tipo
    ent_types = df_ent["type"].value_counts().reset_index()
    ent_types.columns = ["Tipo", "Contagem"]
    fig = px.pie(
        ent_types, values="Contagem", names="Tipo",
        title="Entidades por Tipo" if is_pt else "Entities by Type",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Distribuicao de simbolos por tipo
    sym_types = df_sym["type"].value_counts().reset_index()
    sym_types.columns = ["Tipo", "Contagem"]
    fig = px.pie(
        sym_types, values="Contagem", names="Tipo",
        title="Simbolos por Tipo" if is_pt else "Symbols by Type",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 2. Entidades Mais Importantes
# ---------------------------------------------------------------------------
st.header("2. Entidades Mais Importantes" if is_pt else "2. Most Important Entities")

# Filtro por tipo
all_types = sorted(df_ent["type"].unique())
selected_type = st.selectbox(
    "Filtrar por tipo" if is_pt else "Filter by type",
    ["Todos" if is_pt else "All"] + all_types,
    key="ent_type_filter",
)

df_ent_filtered = df_ent if selected_type in ["Todos", "All"] else df_ent[df_ent["type"] == selected_type]

col1, col2 = st.columns([3, 2])

with col1:
    top_n = st.slider("Top N", 10, 50, 20, key="top_ent")
    top_ent = df_ent_filtered.nlargest(top_n, "boost")
    fig = px.bar(
        top_ent, x="name", y="boost",
        color="type",
        title=f"Top {top_n} Entidades por Importancia" if is_pt else f"Top {top_n} Entities by Importance",
        labels={"name": "Entidade" if is_pt else "Entity", "boost": "Boost", "type": "Tipo" if is_pt else "Type"},
    )
    fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.scatter(
        df_ent_filtered, x="boost", y="priority",
        color="type", hover_name="name",
        title="Boost vs Priority",
        labels={"boost": "Boost", "priority": "Priority", "type": "Tipo" if is_pt else "Type"},
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# 3. Simbolos Biblicos
# ---------------------------------------------------------------------------
st.header("3. Simbolos Biblicos" if is_pt else "3. Biblical Symbols")

top_sym = df_sym.nlargest(15, "boost")
fig = px.bar(
    top_sym, x="name", y="boost",
    color="type",
    title="Top 15 Simbolos por Importancia" if is_pt else "Top 15 Symbols by Importance",
    color_discrete_sequence=["#D4A853", "#636EFA", "#00CC96"],
)
fig.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# Cards de simbolos
st.subheader("Detalhe dos Simbolos" if is_pt else "Symbol Details")
sym_search = st.text_input(
    "Buscar simbolo" if is_pt else "Search symbol",
    key="sym_search",
)

display_syms = df_sym[df_sym["name"].str.contains(sym_search, case=False, na=False)] if sym_search else top_sym.head(5)

for _, sym in display_syms.iterrows():
    literal = sym.get("literal_meaning", "")
    symbolic_raw = sym.get("symbolic_meaning", "[]")
    try:
        symbolic = json.loads(symbolic_raw) if isinstance(symbolic_raw, str) else symbolic_raw
    except (json.JSONDecodeError, TypeError):
        symbolic = []

    examples_raw = sym.get("bible_examples", "[]")
    try:
        examples = json.loads(examples_raw) if isinstance(examples_raw, str) else examples_raw
    except (json.JSONDecodeError, TypeError):
        examples = []

    with st.expander(f"**{sym['name']}** · {sym['type']} · boost {sym['boost']:.2f}"):
        if literal:
            st.markdown(f"**{'Significado literal' if is_pt else 'Literal meaning'}:** {html.escape(str(literal))}")
        if symbolic:
            meanings = ", ".join(str(s) for s in symbolic[:8])
            st.markdown(f"**{'Significado simbolico' if is_pt else 'Symbolic meaning'}:** {meanings}")
        if examples:
            st.markdown(f"**{'Exemplos biblicos' if is_pt else 'Bible examples'}:**")
            for ex in examples[:5]:
                if isinstance(ex, dict):
                    st.markdown(f"- **{ex.get('ref', '')}**: {html.escape(str(ex.get('context', '')))}")

# ---------------------------------------------------------------------------
# 4. Rede de Relacionamentos
# ---------------------------------------------------------------------------
st.header("4. Relacionamentos" if is_pt else "4. Relationships")

col1, col2 = st.columns(2)

with col1:
    rel_types = df_rel["type"].value_counts().reset_index()
    rel_types.columns = ["Tipo", "Contagem"]
    fig = px.bar(
        rel_types.head(15), x="Contagem", y="Tipo",
        orientation="h",
        title="Top 15 Tipos de Relacionamento" if is_pt else "Top 15 Relationship Types",
        color="Contagem",
        color_continuous_scale=["#2A2D34", "#D4A853"],
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Target types
    target_types = df_rel["target_type"].value_counts().reset_index()
    target_types.columns = ["Tipo", "Contagem"]
    fig = px.pie(
        target_types, values="Contagem", names="Tipo",
        title="Alvos por Tipo" if is_pt else "Targets by Type",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

# Tabela interativa
rel_filter = st.selectbox(
    "Filtrar por tipo de relacionamento" if is_pt else "Filter by relationship type",
    ["Todos" if is_pt else "All"] + sorted(df_rel["type"].unique()),
    key="rel_type_filter",
)
df_rel_display = df_rel if rel_filter in ["Todos", "All"] else df_rel[df_rel["type"] == rel_filter]
st.dataframe(
    df_rel_display[["source", "type", "target", "target_type", "description"]].rename(
        columns={"source": "Origem" if is_pt else "Source",
                 "type": "Tipo" if is_pt else "Type",
                 "target": "Alvo" if is_pt else "Target",
                 "target_type": "Tipo Alvo" if is_pt else "Target Type",
                 "description": "Descricao" if is_pt else "Description"}
    ),
    hide_index=True, use_container_width=True,
)

# ---------------------------------------------------------------------------
# 5. Explorador de Entidades
# ---------------------------------------------------------------------------
st.header("5. Explorador de Entidades" if is_pt else "5. Entity Explorer")

ent_search = st.text_input(
    "Buscar entidade por nome" if is_pt else "Search entity by name",
    key="ent_search",
)

if ent_search:
    matches = df_ent[df_ent["name"].str.contains(ent_search, case=False, na=False)]
    if matches.empty:
        st.info("Nenhuma entidade encontrada." if is_pt else "No entity found.")
    else:
        for _, ent in matches.head(10).iterrows():
            aliases_raw = ent.get("aliases", "[]")
            try:
                aliases = json.loads(aliases_raw) if isinstance(aliases_raw, str) else aliases_raw
            except (json.JSONDecodeError, TypeError):
                aliases = []

            categories_raw = ent.get("categories", "[]")
            try:
                categories = json.loads(categories_raw) if isinstance(categories_raw, str) else categories_raw
            except (json.JSONDecodeError, TypeError):
                categories = []

            with st.expander(f"**{ent['name']}** · {ent['type']} · boost {ent['boost']:.2f}"):
                st.markdown(f"**ID:** `{ent.get('canonical_id', '')}`")
                if ent.get("description"):
                    st.markdown(f"**{'Descricao' if is_pt else 'Description'}:** {html.escape(str(ent['description']))}")
                if aliases:
                    st.markdown(f"**Aliases:** {', '.join(str(a) for a in aliases[:10])}")
                if categories:
                    st.markdown(f"**{'Categorias' if is_pt else 'Categories'}:** {', '.join(str(c) for c in categories)}")

                # Relacionamentos desta entidade
                ent_rels = df_rel[(df_rel["source"] == ent["name"]) | (df_rel["target"] == ent["name"])]
                if not ent_rels.empty:
                    st.markdown(f"**{'Relacionamentos' if is_pt else 'Relationships'}:** ({len(ent_rels)})")
                    for _, rel in ent_rels.head(10).iterrows():
                        direction = "→" if rel["source"] == ent["name"] else "←"
                        other = rel["target"] if rel["source"] == ent["name"] else rel["source"]
                        st.markdown(f"- {direction} **{rel['type']}** {other}")
else:
    st.caption("Digite um nome para buscar." if is_pt else "Type a name to search.")

# ---------------------------------------------------------------------------
# 6. Cross-Dataset
# ---------------------------------------------------------------------------
COMM_PARQUET = DATA_DIR / "commentaries.parquet"
if COMM_PARQUET.exists():
    st.header("6. Cross-Dataset: Entidades nos Comentarios" if is_pt else "6. Cross-Dataset: Entities in Commentaries")
    st.caption(
        "Quais entidades do dicionario mais aparecem nos comentarios patristicos"
        if is_pt else
        "Which gazetteer entities appear most in patristic commentaries"
    )

    @st.cache_data(ttl=3600)
    def count_entity_mentions():
        """Conta quantas vezes cada entidade aparece nos comentarios."""
        comm_df = con.sql(f"SELECT content FROM '{COMM_PARQUET}' WHERE content IS NOT NULL").df()
        all_text = " ".join(comm_df["content"].tolist()).lower()

        counts = []
        for _, ent in df_ent.iterrows():
            name = str(ent["name"]).lower()
            if len(name) > 2:  # Ignorar nomes muito curtos
                count = all_text.count(name)
                if count > 0:
                    counts.append({
                        "name": ent["name"],
                        "type": ent["type"],
                        "boost": ent["boost"],
                        "mentions": count,
                    })
        return pd.DataFrame(counts).sort_values("mentions", ascending=False)

    with st.spinner("Analisando mencoes..." if is_pt else "Analyzing mentions..."):
        mentions_df = count_entity_mentions()

    if not mentions_df.empty:
        fig = px.scatter(
            mentions_df.head(50),
            x="mentions", y="boost",
            size="mentions", color="type",
            hover_name="name",
            title="Entidades: Mencoes nos Comentarios vs Importancia" if is_pt else "Entities: Commentary Mentions vs Importance",
            labels={"mentions": "Mencoes" if is_pt else "Mentions", "boost": "Boost"},
        )
        fig.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            mentions_df.head(20).rename(
                columns={"name": "Entidade" if is_pt else "Entity",
                         "type": "Tipo" if is_pt else "Type",
                         "mentions": "Mencoes" if is_pt else "Mentions"}
            ),
            hide_index=True, use_container_width=True,
        )
