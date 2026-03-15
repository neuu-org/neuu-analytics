"""
Explorador de Versiculos — busca qualquer versiculo e ve todos os dados disponíveis.
Comentarios, autores, enriquecimento teologico, tudo num lugar so.
"""

import html
from collections import Counter
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from book_names import (
    BOOK_NAMES, BOOK_ORDER, COMM_TO_CROSSREF, EN_TO_PT_BOOK,
    friendly_name, abbrev_from_name, book_name_for_translation,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PARQUET = DATA_DIR / "commentaries.parquet"
ENRICHED_PARQUET = DATA_DIR / "commentaries_enriched.parquet"
CROSSREFS_PARQUET = DATA_DIR / "crossrefs.parquet"
BIBLETEXT_PARQUET = DATA_DIR / "bibletext.parquet"

from loading import show_loading
show_loading()

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap');

    .verse-ref {
        font-family: 'Crimson Pro', serif;
        font-size: 1.6rem;
        font-weight: 600;
        color: #D4A853;
        margin-bottom: 4px;
    }
    .commentary-card {
        background: #1A1D24;
        border: 1px solid #2A2D34;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 12px;
    }
    .commentary-card .author-name {
        font-weight: 600;
        color: #D4A853;
        font-size: 1rem;
    }
    .commentary-card .period {
        color: #8B8072;
        font-size: 0.8rem;
        margin-left: 8px;
    }
    .commentary-card .content {
        font-family: 'Crimson Pro', serif;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #E8E0D4;
        margin-top: 12px;
    }
    .tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 500;
        margin: 2px 3px;
        background: rgba(212, 168, 83, 0.12);
        color: #D4A853;
        border: 1px solid rgba(212, 168, 83, 0.25);
    }
    .tag-method {
        background: rgba(99, 110, 250, 0.12);
        color: #636EFA;
        border-color: rgba(99, 110, 250, 0.25);
    }
    .tag-tradition {
        background: rgba(0, 204, 150, 0.12);
        color: #00CC96;
        border-color: rgba(0, 204, 150, 0.25);
    }
    .insight-box {
        background: rgba(212, 168, 83, 0.08);
        border-left: 3px solid #D4A853;
        padding: 16px 20px;
        border-radius: 0 8px 8px 0;
        margin-top: 12px;
    }
    .insight-box .theme {
        font-family: 'Crimson Pro', serif;
        font-style: italic;
        font-size: 1.05rem;
        color: #E8E0D4;
    }
    .insight-box .reflection {
        font-size: 0.9rem;
        color: #8B8072;
        margin-top: 8px;
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
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Verificar dados
# ---------------------------------------------------------------------------
if not PARQUET.exists():
    st.error("Dados nao encontrados. Execute `python sync.py` primeiro.")
    st.stop()

con = duckdb.connect()

# ---------------------------------------------------------------------------
# Carregar lista de livros e capitulos
# ---------------------------------------------------------------------------


@st.cache_data(ttl=3600)
def get_books() -> list[str]:
    return con.sql(
        f"SELECT DISTINCT book FROM '{PARQUET}' WHERE book != '' ORDER BY book"
    ).df()["book"].tolist()


@st.cache_data(ttl=3600)
def get_chapters(book: str) -> list[int]:
    return sorted(
        con.sql(
            f"SELECT DISTINCT chapter FROM '{PARQUET}' WHERE book = '{book}' ORDER BY chapter"
        ).df()["chapter"].tolist()
    )


@st.cache_data(ttl=3600)
def get_verses(book: str, chapter: int) -> list[int]:
    return sorted(
        con.sql(
            f"SELECT DISTINCT verse FROM '{PARQUET}' WHERE book = '{book}' AND chapter = {chapter} ORDER BY verse"
        ).df()["verse"].tolist()
    )


@st.cache_data(ttl=3600)
def get_verse_data(book: str, chapter: int, verse: int) -> pd.DataFrame:
    return con.sql(
        f"""
        SELECT * FROM '{PARQUET}'
        WHERE book = '{book}' AND chapter = {chapter} AND verse = {verse}
          AND author IS NOT NULL
        ORDER BY period
        """
    ).df()


@st.cache_data(ttl=3600)
def get_enriched_data(verse_ref: str) -> pd.DataFrame | None:
    if not ENRICHED_PARQUET.exists():
        return None
    df = con.sql(
        f"SELECT * FROM '{ENRICHED_PARQUET}' WHERE verse_reference = '{verse_ref}'"
    ).df()
    return df if not df.empty else None


@st.cache_data(ttl=3600)
def get_crossrefs(book_abbrev: str, chapter: int, verse: int) -> pd.DataFrame | None:
    """Busca referencias cruzadas para um versiculo."""
    if not CROSSREFS_PARQUET.exists():
        return None
    crossref_book = COMM_TO_CROSSREF.get(book_abbrev, book_abbrev.upper())
    df = con.sql(
        f"""
        SELECT * FROM '{CROSSREFS_PARQUET}'
        WHERE from_book = '{crossref_book}'
          AND from_chapter = {chapter}
          AND from_verse = {verse}
        ORDER BY score DESC
        """
    ).df()
    return df if not df.empty else None


@st.cache_data(ttl=3600)
def get_available_translations() -> list[str]:
    """Lista traducoes disponiveis no dataset de texto biblico."""
    if not BIBLETEXT_PARQUET.exists():
        return []
    return con.sql(
        f"SELECT DISTINCT translation FROM '{BIBLETEXT_PARQUET}' ORDER BY translation"
    ).df()["translation"].tolist()


@st.cache_data(ttl=3600)
def get_verse_text(book_name_en: str, chapter: int, verse: int, translation: str) -> str | None:
    """Busca o texto de um versiculo, traduzindo o nome do livro conforme a traducao."""
    if not BIBLETEXT_PARQUET.exists():
        return None
    book = book_name_for_translation(book_name_en, translation)
    result = con.sql(
        f"""
        SELECT text FROM '{BIBLETEXT_PARQUET}'
        WHERE book = '{book}'
          AND chapter = {chapter}
          AND verse = {verse}
          AND translation = '{translation}'
        LIMIT 1
        """
    ).df()
    return result["text"].iloc[0] if not result.empty else None


@st.cache_data(ttl=3600)
def get_crossref_verse_text(crossref_book: str, chapter: int, verse: int, translation: str) -> str | None:
    """Busca texto de um versiculo referenciado (formato crossref OSIS)."""
    if not BIBLETEXT_PARQUET.exists():
        return None
    en_name = friendly_name(crossref_book)
    book = book_name_for_translation(en_name, translation)
    result = con.sql(
        f"""
        SELECT text FROM '{BIBLETEXT_PARQUET}'
        WHERE book = '{book}'
          AND chapter = {chapter}
          AND verse = {verse}
          AND translation = '{translation}'
        LIMIT 1
        """
    ).df()
    return result["text"].iloc[0] if not result.empty else None


# ---------------------------------------------------------------------------
# Idioma e traducao (lidos do session_state, definidos no streamlit_app.py)
# ---------------------------------------------------------------------------
selected_language = st.session_state.get("language", "English")
selected_translation = st.session_state.get("translation", "KJV")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="verse-ref" style="font-size:1.8rem;">Explorador de Versiculos</div>',
    unsafe_allow_html=True,
)
st.caption("Texto, comentarios patristicos, referencias cruzadas e traducoes — tudo num lugar so")

# ---------------------------------------------------------------------------
# Seletores
# ---------------------------------------------------------------------------
books = get_books()

col1, col2, col3 = st.columns([2, 1, 1])

# Ordenar livros na ordem canonica, com nomes amigaveis
books_sorted = [b for b in BOOK_ORDER if b in books]
books_sorted += [b for b in books if b not in books_sorted]

# Nomes em PT ou EN conforme idioma selecionado
is_pt = selected_language == "Portugues"
if is_pt:
    book_display = [EN_TO_PT_BOOK.get(friendly_name(b), friendly_name(b)) for b in books_sorted]
else:
    book_display = [friendly_name(b) for b in books_sorted]

# Mapa reverso para encontrar a abreviacao a partir do display name
_display_to_abbrev = dict(zip(book_display, books_sorted))

with col1:
    default_idx = books_sorted.index("mt") if "mt" in books_sorted else 0
    selected_display = st.selectbox("Livro", book_display, index=default_idx)
    selected_book = _display_to_abbrev.get(selected_display, abbrev_from_name(selected_display))

with col2:
    chapters = get_chapters(selected_book)
    selected_chapter = st.selectbox("Capitulo", chapters)

with col3:
    verses = get_verses(selected_book, selected_chapter)
    selected_verse = st.selectbox("Versiculo", verses)

st.markdown("---")

# ---------------------------------------------------------------------------
# Dados do versiculo
# ---------------------------------------------------------------------------
df_verse = get_verse_data(selected_book, selected_chapter, selected_verse)

verse_ref = f"{selected_book.upper()} {selected_chapter}:{selected_verse}"
_en_book_name = friendly_name(selected_book)
if is_pt:
    _display_book = EN_TO_PT_BOOK.get(_en_book_name, _en_book_name)
else:
    _display_book = _en_book_name
verse_display = f"{_display_book} {selected_chapter}:{selected_verse}"

st.markdown(f'<div class="verse-ref">{html.escape(verse_display)}</div>', unsafe_allow_html=True)

# Mostrar texto do versiculo selecionado (se disponivel)
main_verse_text = get_verse_text(friendly_name(selected_book), selected_chapter, selected_verse, selected_translation)
if main_verse_text:
    st.markdown(
        f'<div style="background:rgba(212,168,83,0.08);border-left:3px solid #D4A853;'
        f'padding:16px 20px;border-radius:0 8px 8px 0;margin:8px 0 16px 0;">'
        f'<div style="font-family:Crimson Pro,serif;font-size:1.15rem;line-height:1.8;'
        f'color:#E8E0D4;font-style:italic;">'
        f'&ldquo;{html.escape(main_verse_text)}&rdquo;</div>'
        f'<div style="font-size:0.75rem;color:#8B8072;margin-top:8px;">{html.escape(selected_translation)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

if df_verse.empty:
    st.info("Nenhum comentario disponivel para este versiculo.")
    st.stop()

# Stats rapidos
total = len(df_verse)
authors = df_verse["author"].nunique()
avg_words = df_verse["word_count"].mean()

st.markdown(
    f"""
    <div class="stat-row">
        <div class="stat-item"><strong>{total}</strong> comentarios</div>
        <div class="stat-item"><strong>{authors}</strong> autores</div>
        <div class="stat-item"><strong>{avg_words:.0f}</strong> palavras em media</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Enriched data (se disponivel)
# ---------------------------------------------------------------------------
df_enriched = get_enriched_data(verse_ref)

# ---------------------------------------------------------------------------
# Tabs: Comentarios | Analise | Visao Geral
# ---------------------------------------------------------------------------
tab_comm, tab_crossrefs, tab_translations, tab_analysis, tab_overview = st.tabs(
    ["Comentarios", "Referencias Cruzadas", "Traducoes", "Analise Teologica", "Visao Geral"]
)

# --- Tab 1: Comentarios ---
with tab_comm:
    # Filtro de autor
    all_authors = sorted(df_verse["author"].unique())
    selected_authors = st.multiselect(
        "Filtrar por autor",
        options=all_authors,
        default=all_authors,
        key="author_filter",
    )

    df_filtered = df_verse[df_verse["author"].isin(selected_authors)]

    for _, row in df_filtered.iterrows():
        content_raw = row["content"] or ""
        if len(content_raw) > 1500:
            content_raw = content_raw[:1500] + "..."
        content_preview = html.escape(content_raw).replace("\n", "<br>")

        author_safe = html.escape(row["author"] or "")
        period_safe = html.escape(row["period"] or "")

        # Construir bloco enriched (se disponivel)
        enriched_html = ""
        if df_enriched is not None:
            author_enriched = df_enriched[df_enriched["author"] == row["author"]]
            if not author_enriched.empty:
                e = author_enriched.iloc[0]

                doctrines = [html.escape(d.strip()) for d in str(e.get("doctrines", "")).split("|") if d.strip()]
                traditions = [html.escape(t.strip()) for t in str(e.get("traditions", "")).split("|") if t.strip()]
                method = html.escape(str(e.get("theological_method", "")))
                theme = html.escape(str(e.get("theme", "")))
                one_sentence = html.escape(str(e.get("one_sentence", "")))

                tags_parts = []
                for d in doctrines[:5]:
                    tags_parts.append(f'<span class="tag">{d}</span>')
                for t in traditions[:3]:
                    tags_parts.append(f'<span class="tag tag-tradition">{t}</span>')
                if method:
                    tags_parts.append(f'<span class="tag tag-method">{method}</span>')

                tags_html = " ".join(tags_parts)

                insight_html = ""
                if theme or one_sentence:
                    insight_html = (
                        '<div class="insight-box">'
                        f'<div class="theme">&ldquo;{theme}&rdquo;</div>'
                        f'<div class="reflection">{one_sentence}</div>'
                        '</div>'
                    )

                if tags_html or insight_html:
                    enriched_html = (
                        '<div class="section-label">Analise Teologica</div>'
                        f'{tags_html}'
                        f'{insight_html}'
                    )

        card_html = (
            '<div class="commentary-card">'
            f'<span class="author-name">{author_safe}</span>'
            f'<span class="period">{period_safe}</span>'
            f'<div class="content">{content_preview}</div>'
            f'{enriched_html}'
            '</div>'
        )

        st.markdown(card_html, unsafe_allow_html=True)

# --- Tab 2: Referencias Cruzadas ---
with tab_crossrefs:
    df_crossrefs = get_crossrefs(selected_book, selected_chapter, selected_verse)

    if df_crossrefs is not None and not df_crossrefs.empty:
        total_refs = len(df_crossrefs)
        strong = len(df_crossrefs[df_crossrefs["connection_strength"] == "strong"])
        moderate = len(df_crossrefs[df_crossrefs["connection_strength"] == "moderate"])

        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Referencias", total_refs)
        rc2.metric("Fortes", strong)
        rc3.metric("Moderadas", moderate)

        # Lista de referencias (design original com bolinhas + collapse para texto)
        st.markdown(
            '<div class="section-label">Referencias Cruzadas (por relevancia)</div>',
            unsafe_allow_html=True,
        )

        for idx, (_, ref) in enumerate(df_crossrefs.iterrows()):
            to_name_en = friendly_name(ref["to_book"])
            to_name = EN_TO_PT_BOOK.get(to_name_en, to_name_en) if is_pt else to_name_en
            strength = ref["connection_strength"]
            votes = ref["votes"]
            score = ref["score"]

            strength_color = {
                "strong": "#D4A853", "primary": "#D4A853",
                "moderate": "#636EFA", "weak": "#5A5550",
            }.get(strength, "#5A5550")
            vote_text = f" · {votes} votos" if votes > 0 else ""

            # Linha visual com bolinha + tag + toggle na mesma linha
            ref_col1, ref_col2 = st.columns([20, 1])
            with ref_col1:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0;">'
                    f'<span style="color:{strength_color};font-size:1.5rem;">●</span>'
                    f'<span style="color:#E8E0D4;font-weight:500;">'
                    f'{html.escape(to_name)} {ref["to_chapter"]}:{ref["to_verse"]}</span>'
                    f'<span style="color:#8B8072;font-size:0.8rem;">score {score}{vote_text}</span>'
                    f'<span class="tag" style="font-size:0.65rem;">{html.escape(strength)}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with ref_col2:
                show_text = st.toggle("", key=f"ref_{idx}", label_visibility="collapsed")

            if show_text:
                ref_text = get_crossref_verse_text(
                    ref["to_book"], int(ref["to_chapter"]), int(ref["to_verse"]),
                    selected_translation,
                )
                if ref_text:
                    st.markdown(
                        f'<div style="font-family:Crimson Pro,serif;font-size:1.1rem;'
                        f'line-height:1.8;color:#E8E0D4;font-style:italic;'
                        f'padding:4px 16px 12px 40px;background:rgba(212,168,83,0.06);'
                        f'border-left:3px solid #D4A853;border-radius:0 8px 8px 0;'
                        f'margin:-8px 0 4px 0;">'
                        f'&ldquo;{html.escape(ref_text)}&rdquo;'
                        f'<div style="font-size:0.75rem;color:#8B8072;margin-top:6px;font-style:normal;">'
                        f'{html.escape(selected_translation)}'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption(f"Texto nao disponivel em {selected_translation}")

        # Grafo por livro
        st.markdown("---")
        book_targets = (
            df_crossrefs.groupby("to_book")
            .agg(count=("to_book", "size"), avg_score=("score", "mean"))
            .reset_index()
            .sort_values("count", ascending=False)
            .head(15)
        )
        book_targets["to_book_name"] = book_targets["to_book"].apply(friendly_name)

        fig = px.bar(
            book_targets,
            x="to_book_name", y="count",
            color="avg_score",
            color_continuous_scale=["#2A2D34", "#D4A853"],
            title=f"Livros mais referenciados por {verse_display}",
            labels={"count": "Referencias", "to_book_name": "Livro", "avg_score": "Score medio"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E8E0D4",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma referencia cruzada encontrada para este versiculo.")

# --- Tab 3: Traducoes (Comparador) ---
with tab_translations:
    if BIBLETEXT_PARQUET.exists():
        @st.cache_data(ttl=3600)
        def get_all_translations(book_en: str, chapter: int, verse: int) -> pd.DataFrame:
            return con.sql(
                f"""
                SELECT translation, language, text
                FROM '{BIBLETEXT_PARQUET}'
                WHERE chapter = {chapter} AND verse = {verse}
                ORDER BY language, translation
                """
            ).df()

        _book_en = friendly_name(selected_book)
        _book_pt = EN_TO_PT_BOOK.get(_book_en, _book_en)
        _lang_filter = "portuguese" if is_pt else "english"

        verse_texts = con.sql(
            f"""
            SELECT translation, language, text
            FROM '{BIBLETEXT_PARQUET}'
            WHERE (book = '{_book_en}' OR book = '{_book_pt}')
              AND chapter = {selected_chapter}
              AND verse = {selected_verse}
              AND language = '{_lang_filter}'
            ORDER BY translation
            """
        ).df()

        if not verse_texts.empty:
            lang_label = "Portugues" if is_pt else "English"
            st.caption(f"{len(verse_texts)} traducoes em {lang_label}")

            for _, row in verse_texts.iterrows():
                st.markdown(
                    f'<div style="background:#1A1D24;border:1px solid #2A2D34;border-radius:8px;'
                    f'padding:14px 18px;margin-bottom:8px;">'
                    f'<span style="font-weight:600;color:#D4A853;">{html.escape(row["translation"])}</span>'
                    f'<div style="font-family:Crimson Pro,serif;font-size:1.05rem;line-height:1.7;'
                    f'color:#E8E0D4;margin-top:8px;">'
                    f'&ldquo;{html.escape(str(row["text"]))}&rdquo;</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Nenhuma traducao encontrada para este versiculo.")
    else:
        st.info("Dataset de texto biblico nao disponivel. Execute `python sync.py bibletext`.")

# --- Tab 4: Analise Teologica ---
with tab_analysis:
    if df_enriched is not None and not df_enriched.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Doutrinas neste versiculo
            all_doctrines = []
            for docs in df_enriched["doctrines"]:
                if isinstance(docs, str) and docs:
                    all_doctrines.extend([d.strip() for d in docs.split("|") if d.strip()])

            if all_doctrines:
                doc_counts = Counter(all_doctrines).most_common(10)
                doc_df = pd.DataFrame(doc_counts, columns=["Doutrina", "Frequencia"])
                fig = px.bar(
                    doc_df,
                    x="Frequencia",
                    y="Doutrina",
                    orientation="h",
                    title="Doutrinas neste Versiculo",
                    color_discrete_sequence=["#D4A853"],
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E8E0D4",
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Metodos teologicos
            methods = df_enriched["theological_method"].value_counts().reset_index()
            methods.columns = ["Metodo", "Contagem"]
            if not methods.empty:
                fig = px.pie(
                    methods,
                    values="Contagem",
                    names="Metodo",
                    title="Metodos Interpretativos",
                    color_discrete_sequence=["#D4A853", "#636EFA", "#00CC96", "#EF553B"],
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E8E0D4",
                )
                st.plotly_chart(fig, use_container_width=True)

        # Key points
        all_points = []
        for kp in df_enriched["key_points"]:
            if isinstance(kp, str) and kp:
                all_points.extend([p.strip() for p in kp.split("|") if p.strip()])

        if all_points:
            st.markdown('<div class="section-label">Pontos-Chave dos Comentaristas</div>', unsafe_allow_html=True)
            for point in all_points[:10]:
                st.markdown(f"- {point}")
    else:
        st.info(
            "Dados enriquecidos nao disponiveis para este versiculo.\n\n"
            "A camada de enriquecimento cobre atualmente apenas Acts e John."
        )

# --- Tab 3: Visao Geral ---
with tab_overview:
    col1, col2 = st.columns(2)

    with col1:
        # Word count por autor
        fig = px.bar(
            df_verse.sort_values("word_count", ascending=False),
            x="author",
            y="word_count",
            title="Tamanho do Comentario por Autor",
            color="word_count",
            color_continuous_scale=["#2A2D34", "#D4A853"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E8E0D4",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Timeline dos autores
        df_with_year = df_verse.copy()
        df_with_year["year"] = df_with_year["period"].apply(
            lambda p: int(m.group(1)) if p and (m := __import__("re").search(r"(\d{3,4})", str(p))) else None
        )
        df_with_year = df_with_year.dropna(subset=["year"])

        if not df_with_year.empty:
            fig = px.scatter(
                df_with_year,
                x="year",
                y="author",
                size="word_count",
                title="Autores ao Longo do Tempo",
                color_discrete_sequence=["#D4A853"],
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E8E0D4",
                xaxis_title="Ano (AD)",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Dados brutos
    with st.expander("Ver dados brutos"):
        st.dataframe(
            df_verse[["author", "period", "word_count", "category", "testament"]],
            hide_index=True,
            use_container_width=True,
        )
