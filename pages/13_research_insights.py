"""
NEUU Analytics — Research Insights & Discoveries
Storytelling page showing real theological discoveries from the CCEL bridge.
"""

import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "research"
FIGURES_DIR = DATA_DIR / "figures"

is_pt = st.session_state.get("language", "Portugues") == "Portugues"

# ---------------------------------------------------------------------------
# Custom CSS for storytelling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .insight-card {
        background: linear-gradient(135deg, #1A1D24 0%, #2A2D34 100%);
        border-left: 4px solid #D4A853;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .insight-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #D4A853;
        margin-bottom: 0.5rem;
    }
    .insight-subtitle {
        font-size: 0.85rem;
        color: #8B8072;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .quote-box {
        background: #0E1117;
        border-left: 3px solid #5A9BD5;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        font-style: italic;
        color: #C8C0B8;
        border-radius: 0 6px 6px 0;
    }
    .author-tag {
        background: #2A2D34;
        color: #D4A853;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .metric-highlight {
        font-size: 2rem;
        font-weight: 800;
        color: #D4A853;
    }
    .chain-arrow {
        color: #5A9BD5;
        font-size: 1.2rem;
    }
    .discovery-tag {
        background: #1B3A26;
        color: #66BB6A;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem 0;">
    <div style="font-size:0.8rem;color:#8B8072;letter-spacing:3px;text-transform:uppercase;">
        Bible Hybrid Search Research
    </div>
    <div style="font-size:2.2rem;font-weight:700;color:#E8E0D4;margin:0.5rem 0;">
        {}
    </div>
    <div style="font-size:1rem;color:#8B8072;max-width:600px;margin:0 auto;">
        {}
    </div>
</div>
""".format(
    "Descobertas e Insights" if is_pt else "Discoveries & Insights",
    "Quando 2.000 anos de erudição cristã encontram inteligência artificial — histórias reais de conexões teológicas que nenhum embedding moderno consegue fazer sozinho."
    if is_pt else
    "When 2,000 years of Christian scholarship meets artificial intelligence — real stories of theological connections no modern embedding can make alone."
), unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.markdown('<div style="text-align:center"><div class="metric-highlight">1.5M</div><div style="color:#8B8072;font-size:0.8rem">paragrafos CCEL</div></div>', unsafe_allow_html=True)
c2.markdown('<div style="text-align:center"><div class="metric-highlight">62%</div><div style="color:#8B8072;font-size:0.8rem">gold refs cobertas</div></div>', unsafe_allow_html=True)
c3.markdown('<div style="text-align:center"><div class="metric-highlight">+41%</div><div style="color:#8B8072;font-size:0.8rem">ganho queries extremas</div></div>', unsafe_allow_html=True)
c4.markdown('<div style="text-align:center"><div class="metric-highlight">p<0.001</div><div style="color:#8B8072;font-size:0.8rem">significancia estatistica</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# INSIGHT 1: Cordeiro de Deus
# ---------------------------------------------------------------------------
st.markdown("""
<div class="insight-card">
    <div class="insight-subtitle">Insight 1 — Cadeia tipologica</div>
    <div class="insight-title">🐑 O Cordeiro de Deus: uma cadeia de 4.000 anos</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 2])

with col1:
    if is_pt:
        st.markdown("""
O embedding de **"cordeiro de Deus"** encontra facilmente João 1:29 — o versículo contém a expressão literal. Mas a cadeia tipológica completa cruza **5 livros e 4 gêneros literários**:
""")
    else:
        st.markdown("""
The embedding of **"lamb of God"** easily finds John 1:29 — the verse contains the literal expression. But the complete typological chain crosses **5 books and 4 literary genres**:
""")

    st.markdown("""
<div style="text-align:center;padding:1rem;font-size:1.1rem;">
    <span style="color:#D4A853">Gênesis 22:8</span>
    <span class="chain-arrow"> → </span>
    <span style="color:#D4A853">Êxodo 12:3</span>
    <span class="chain-arrow"> → </span>
    <span style="color:#D4A853">Isaías 53:7</span>
    <span class="chain-arrow"> → </span>
    <span style="color:#D4A853">João 1:29</span>
    <span class="chain-arrow"> → </span>
    <span style="color:#D4A853">Apocalipse 5:6</span>
</div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div class="quote-box">
"Every morning and every evening there had been a lamb sacrificed in the Tabernacle
as the type and emblem of this Lamb of God who was yet to come."
<br><br>— <span class="author-tag">Spurgeon, 1881</span>
</div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div class="quote-box">
"THE LAMB OF GOD — Ge. 22.8. Is. 53.7. Jno. 1.29. Ac. 8.32-35. 1 Pe. 1.19. Re. 5.6; 13.8; 15.3; 21.22; 22.1."
<br><br>— <span class="author-tag">Smith, Old Testament Types and Teachings</span>
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
<div style="background:#1A1D24;padding:1.2rem;border-radius:8px;">
    <div style="font-size:0.75rem;color:#8B8072;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.8rem;">O que aconteceu</div>
    <div style="margin-bottom:0.6rem;">
        <span style="color:#EF5350">✗</span> <span style="color:#C8C0B8">Embedding sozinho:</span><br>
        <span style="color:#8B8072;font-size:0.85rem;padding-left:1.2rem;">Encontra Jo 1:29, Ap 5:6 (texto literal)</span>
    </div>
    <div style="margin-bottom:0.6rem;">
        <span style="color:#EF5350">✗</span> <span style="color:#C8C0B8">Não alcança:</span><br>
        <span style="color:#8B8072;font-size:0.85rem;padding-left:1.2rem;">Gn 22:8 ("proverá o cordeiro")</span><br>
        <span style="color:#8B8072;font-size:0.85rem;padding-left:1.2rem;">Is 53:7 ("ovelha muda")</span><br>
        <span style="color:#8B8072;font-size:0.85rem;padding-left:1.2rem;">1 Pe 1:19 ("sangue precioso")</span>
    </div>
    <div style="margin-top:1rem;">
        <span class="discovery-tag">CCEL BRIDGE</span><br>
        <span style="color:#66BB6A;font-size:0.85rem;padding-left:0.5rem;">
        Spurgeon + Smith conectam a cadeia completa de 4.000 anos</span>
    </div>
</div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# INSIGHT 2: Cegueira Espiritual
# ---------------------------------------------------------------------------
st.markdown("""
<div class="insight-card">
    <div class="insight-subtitle">Insight 2 — O mapa que ja existia</div>
    <div class="insight-title">👁️ Cegueira espiritual: Boyce e Manton ja sabiam ha 300 anos</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("""
<div style="background:#1A1D24;padding:1.2rem;border-radius:8px;">
    <div style="font-size:0.75rem;color:#8B8072;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.8rem;">Antes vs Depois</div>
    <div style="font-size:2.5rem;font-weight:800;color:#EF5350;text-align:center;">5/11</div>
    <div style="text-align:center;color:#8B8072;font-size:0.85rem;margin-bottom:1rem;">sem CCEL</div>
    <div style="font-size:2.5rem;font-weight:800;color:#66BB6A;text-align:center;">8/11</div>
    <div style="text-align:center;color:#8B8072;font-size:0.85rem;margin-bottom:1rem;">com CCEL (+60%)</div>
    <div style="text-align:center;margin-top:1rem;">
        <span class="discovery-tag">3 versículos resgatados</span>
    </div>
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
<div class="quote-box">
"Spiritual blindness. Matt. 13:15; 1 Cor. 2:14."
<br><br>— <span class="author-tag">James P. Boyce, Abstract of Systematic Theology, 1887</span>
<br><span style="font-size:0.8rem;color:#5A9BD5;">Similaridade: 0.78 — o match mais forte de todo o Exp5</span>
</div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div class="quote-box">
"Spiritual blindness is natural to us, as that man that was blind
from his birth, John ix. 1."
<br><br>— <span class="author-tag">Thomas Manton, Works, 1680</span>
<br><span style="font-size:0.8rem;color:#5A9BD5;">Conecta Jo 9:1 → Ap 3:17 — ponte que nenhum embedding faz</span>
</div>
    """, unsafe_allow_html=True)

    if is_pt:
        st.markdown("**Versículos resgatados pelo CCEL:** Apocalipse 3:17 (via Manton), João 9:39 (via Spurgeon e Owen), Mateus 13:15 (via Boyce). Conexões documentadas há séculos — agora computacionalmente acessíveis.")
    else:
        st.markdown("**Verses rescued by CCEL:** Revelation 3:17 (via Manton), John 9:39 (via Spurgeon & Owen), Matthew 13:15 (via Boyce). Connections documented centuries ago — now computationally accessible.")

st.markdown("---")

# ---------------------------------------------------------------------------
# INSIGHT 3: Kenosis
# ---------------------------------------------------------------------------
st.markdown("""
<div class="insight-card">
    <div class="insight-subtitle">Insight 3 — Exegese grega sem saber grego</div>
    <div class="insight-title">⬇️ Esvaziamento de Cristo: Calvin faz exegese em 1548</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="quote-box">
"Emptied himself (ἑαυτὸν ἐκένωσε). This emptying is the same as the abasement...
Christ, indeed, could not divest himself of Godhead; but he kept it concealed for a time."
<br><br>— <span class="author-tag">João Calvino, Commentary on Philippians, 1548</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="quote-box">
"First aorist active indicative of κενόω, old verb from κενός, empty.
Of what did Christ empty himself? Not of his divine nature. That was impossible."
<br><br>— <span class="author-tag">A.T. Robertson, Word Pictures in the New Testament, 1930</span>
</div>
""", unsafe_allow_html=True)

if is_pt:
    st.markdown("""
O sistema consegue acessar **exegese grega do século XVI** sem saber grego — porque Calvin e Robertson já fizeram a tradução conceitual, conectando o termo técnico (*kenosis*, κένωσις) aos versículos Filipenses 2:6-8 e João 1:14. O embedding moderno sabe que "esvaziamento" e "humilhação" são relacionados. A tradição interpretativa sabe *exatamente* qual verbo grego Paulo usou e o que ele significa doutrinalmente.
""")
else:
    st.markdown("""
The system accesses **16th-century Greek exegesis** without knowing Greek — because Calvin and Robertson already translated the concept, connecting the technical term (*kenosis*, κένωσις) to Philippians 2:6-8 and John 1:14.
""")

st.markdown("---")

# ---------------------------------------------------------------------------
# INSIGHT 4: Gemido da criação
# ---------------------------------------------------------------------------
st.markdown("""
<div class="insight-card">
    <div class="insight-subtitle">Insight 4 — Consenso entre tradicoes opostas</div>
    <div class="insight-title">🌍 Gemido da criação: 100% de cobertura — Pink, Wesley e Spurgeon concordam</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
<div style="text-align:center;padding:1rem;background:#1A1D24;border-radius:8px;">
    <div style="font-size:0.7rem;color:#8B8072;text-transform:uppercase;letter-spacing:1px;">Calvinista dispensacionalista</div>
    <div style="font-size:1.1rem;color:#D4A853;font-weight:700;margin:0.5rem 0;">A.W. Pink</div>
    <div style="font-size:0.85rem;color:#C8C0B8;font-style:italic;">"The world groans beneath an accumulating load of sin"</div>
    <div style="font-size:0.75rem;color:#5A9BD5;margin-top:0.5rem;">sim = 0.69</div>
</div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
<div style="text-align:center;padding:1rem;background:#1A1D24;border-radius:8px;">
    <div style="font-size:0.7rem;color:#8B8072;text-transform:uppercase;letter-spacing:1px;">Arminiano metodista</div>
    <div style="font-size:1.1rem;color:#D4A853;font-weight:700;margin:0.5rem 0;">John Wesley</div>
    <div style="font-size:0.85rem;color:#C8C0B8;font-style:italic;">"The whole creation groaneth together — as it were with one voice"</div>
    <div style="font-size:0.75rem;color:#5A9BD5;margin-top:0.5rem;">sim = 0.65</div>
</div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
<div style="text-align:center;padding:1rem;background:#1A1D24;border-radius:8px;">
    <div style="font-size:0.7rem;color:#8B8072;text-transform:uppercase;letter-spacing:1px;">Calvinista batista</div>
    <div style="font-size:1.1rem;color:#D4A853;font-weight:700;margin:0.5rem 0;">C.H. Spurgeon</div>
    <div style="font-size:0.85rem;color:#C8C0B8;font-style:italic;">"The birth pangs of the Creation are on it"</div>
    <div style="font-size:0.75rem;color:#5A9BD5;margin-top:0.5rem;">sim = 0.64</div>
</div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if is_pt:
    st.markdown("""
Três teólogos de **tradições opostas** — separados por séculos — convergem nas mesmas referências para Romanos 8:19-26. Quando múltiplos autores independentes concordam, isso é um **sinal forte de relevância**. O sistema operacionaliza esse conceito acadêmico como métrica: versículos citados por 3+ autores recebem pontuação mais alta. **Resultado: 8/8 gold refs encontradas (100%).**
""")
else:
    st.markdown("""
Three theologians from **opposing traditions** — separated by centuries — converge on the same references for Romans 8:19-26. **Result: 8/8 gold refs found (100%).**
""")

st.markdown("---")

# ---------------------------------------------------------------------------
# INSIGHT 5: Filho Pródigo
# ---------------------------------------------------------------------------
st.markdown("""
<div class="insight-card">
    <div class="insight-subtitle">Insight 5 — A parabola que nao existe</div>
    <div class="insight-title">🏠 Filho pródigo: um nome inventado pela tradição</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 2])

with col1:
    if is_pt:
        st.markdown("""
A expressão **"filho pródigo"** não aparece em **nenhuma tradução bíblica portuguesa**. O texto de Lucas 15:11 diz:

> *"Um certo homem tinha dois filhos."*

O nome "pródigo" é uma **invenção da tradição interpretativa** — não texto bíblico. Isso torna a busca léxica por "pródigo" impossível (zero resultados) e foi um dos motivos para reclassificar esta query de *baseline* para *medium* durante a validação humana.

O CCEL preserva essa nomenclatura convencional: **Tillotson** (similaridade 0,78) indexa "Prodigal son, the parable of the"; **Maclaren** e **Fosdick** citam Lucas 15:11; **Spurgeon** cita Lucas 15:20 ("o pai correu ao seu encontro").
""")
    else:
        st.markdown("""
The expression **"prodigal son"** does not appear in **any Portuguese Bible translation**. Luke 15:11 says:

> *"A certain man had two sons."*

The name "prodigal" is an **invention of the interpretive tradition** — not biblical text.
""")

with col2:
    st.markdown("""
<div style="background:#1A1D24;padding:1.2rem;border-radius:8px;text-align:center;">
    <div style="font-size:0.75rem;color:#8B8072;text-transform:uppercase;letter-spacing:1px;margin-bottom:1rem;">Busca por "pródigo" na Bíblia</div>
    <div style="font-size:3rem;font-weight:800;color:#EF5350;">0</div>
    <div style="color:#8B8072;font-size:0.9rem;">resultados</div>
    <div style="margin-top:1.5rem;font-size:0.75rem;color:#8B8072;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.5rem;">Busca na CCEL</div>
    <div style="font-size:3rem;font-weight:800;color:#66BB6A;">4/8</div>
    <div style="color:#8B8072;font-size:0.9rem;">gold refs encontradas</div>
</div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Closing
# ---------------------------------------------------------------------------
st.markdown("""
<div style="text-align:center;padding:2rem 1rem;max-width:700px;margin:0 auto;">
    <div style="font-size:1.3rem;color:#E8E0D4;font-style:italic;line-height:1.8;">
        {}
    </div>
    <div style="margin-top:1.5rem;font-size:0.85rem;color:#8B8072;">
        {}
    </div>
</div>
""".format(
    "O embedding moderno sabe que 'cordeiro' e 'ovelha' são animais similares. A tradição interpretativa sabe que o cordeiro de Gênesis 22 prefigura o Cordeiro de João 1, que cumpre o cordeiro pascal de Êxodo 12, que se consuma no Cordeiro do Apocalipse 5."
    if is_pt else
    "The modern embedding knows that 'lamb' and 'sheep' are similar animals. The interpretive tradition knows that the lamb of Genesis 22 prefigures the Lamb of John 1, which fulfills the paschal lamb of Exodus 12, which is consummated in the Lamb of Revelation 5.",
    "Essa cadeia tipológica — invisível para qualquer modelo de linguagem — é o que a CCEL torna computacionalmente acessível."
    if is_pt else
    "This typological chain — invisible to any language model — is what the CCEL makes computationally accessible."
), unsafe_allow_html=True)
