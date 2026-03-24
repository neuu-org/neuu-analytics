# Referencial Teórico

## Fundamentos de recuperação de informação

### Modelo probabilístico e BM25

O BM25 (Best Matching 25) é uma função de ranking baseada no modelo probabilístico de recuperação de informação, originalmente proposta por Robertson et al. (1994) e formalizada como framework por Robertson e Zaragoza (2009). A função calcula a relevância de um documento para uma consulta com base na frequência dos termos da consulta no documento (TF), na frequência inversa dos documentos que contêm cada termo (IDF) e no comprimento do documento, controlados pelos parâmetros k1 (saturação de frequência) e b (normalização por comprimento).

O BM25 apresenta três características que o tornam particularmente adequado para busca em texto bíblico: (1) operação puramente léxica, sem necessidade de treinamento ou GPU; (2) interpretabilidade — cada correspondência é rastreável a termos específicos; e (3) robustez fora do domínio, confirmada pelo benchmark BEIR (Thakur et al., 2021), que demonstrou que o BM25 frequentemente supera modelos neurais em domínios especializados sem fine-tuning.

Neste trabalho, o BM25 é implementado via PostgreSQL utilizando tsvector com stemmers para português e inglês, acelerado por índices GIN (Generalized Inverted Index). A indexação adequada reduziu a latência de ~8.300ms para ~12ms por consulta.

### Recuperação densa com embeddings

A recuperação densa utiliza redes neurais para representar consultas e documentos como vetores em um espaço semântico contínuo, onde a similaridade é computada por distância cosseno. O paradigma de dual-encoder, formalizado por Karpukhin et al. (2020) no Dense Passage Retrieval (DPR), codifica consulta e documento independentemente, permitindo pré-computação dos vetores de documentos e busca eficiente em tempo sublinear.

Reimers e Gurevych (2019) demonstraram com o Sentence-BERT que redes siamesas baseadas em BERT produzem embeddings de sentenças semanticamente significativos, reduzindo o tempo de busca por similaridade de 65 horas para ~5 segundos em comparação com cross-encoders. Essa eficiência viabiliza a busca semântica em corpora com centenas de milhares de documentos.

Os modelos text-embedding-3-small (1.536 dimensões) e text-embedding-3-large (3.072 dimensões) da OpenAI (OpenAI, 2024) utilizam a técnica Matryoshka Representation Learning (Kusupati et al., 2022), que produz representações onde subconjuntos de dimensões preservam utilidade semântica. O benchmark MTEB (Muennighoff et al., 2023) demonstra que modelos de maior dimensionalidade capturam nuances semânticas superiores, achado confirmado pelos resultados do Experimento 3 deste trabalho (+27% P@10 ao substituir small por large).

A principal limitação da recuperação densa é a dependência do domínio de treinamento: modelos treinados em corpus geral podem não capturar nuances semânticas de domínios especializados como teologia, exigindo fine-tuning ou estratégias complementares de enriquecimento.

### Recuperação híbrida e fusão de rankings

A recuperação híbrida combina os pontos fortes complementares dos componentes léxico e semântico. Luan et al. (2021) demonstraram formalmente que recuperadores esparsos e densos recuperam conjuntos de resultados complementares: o componente esparso (BM25) destaca-se em correspondência de tokens, entidades e frases exatas, enquanto o componente denso (embeddings) captura paráfrases e lacunas vocabulares. Lee et al. (2023) propuseram treinar os dois componentes para maximizar complementaridade explícita, obtendo ganhos significativos quando os sistemas cobrem mutuamente as fraquezas um do outro.

A técnica de fusão utilizada neste trabalho é o Reciprocal Rank Fusion (RRF), proposta por Cormack et al. (2009). A fórmula combina rankings sem necessidade de normalização de scores: score(d) = Σ 1/(k + rank_i(d)), onde k=60 é a constante de suavização e os rankings podem ser ponderados por um parâmetro alpha. O RRF é simples, sem parâmetros de aprendizado, e consistentemente supera métodos mais complexos como Condorcet e learning-to-rank.

Alternativas ao paradigma BM25+dual-encoder incluem o ColBERT (Khattab e Zaharia, 2020), que utiliza interação tardia com correspondência MaxSim sobre representações contextualizadas por BERT, e o SPLADE (Formal et al., 2021), que aprende representações esparsas via o cabeçalho MLM do BERT com regularização de esparsidade. Ambos alcançam desempenho competitivo com melhor generalização fora do domínio, mas requerem treinamento especializado e infraestrutura de GPU — requisitos que o pipeline BM25+dual-encoder deste trabalho evita intencionalmente para maximizar acessibilidade e reprodutibilidade.

## Pipeline multi-estágio de recuperação

### Expansão de consulta

A expansão de consulta adiciona termos semanticamente relacionados à consulta original para melhorar a cobertura vocabular. Kuzi et al. (2016) demonstraram que embeddings CBOW podem ser utilizados para seleção semântica de termos de expansão, complementando feedback de pseudo-relevância. Neste trabalho, a expansão utiliza um dicionário estático de sinônimos teológicos, abordagem que se mostrou neutra nos Experimentos 1-2 porque os sinônimos são adicionados após a geração do embedding da consulta — não enriquecendo a representação vetorial. A literatura sugere que expansão baseada em embeddings (gerando novo embedding após adição dos termos) seria mais eficaz.

### Reranking de segundo estágio

A arquitetura de recuperação em dois estágios — primeiro estágio rápido (BM25 ou dual-encoder) seguido de reranking preciso — é formalizada por Lin et al. (2021) em seu levantamento sobre transformers para ranking. Nogueira e Cho (2019) demonstraram que cross-encoders BERT aplicados como rerankers alcançam ganhos de 27% em MRR@10 no MS MARCO, com a atenção cruzada completa entre consulta e documento proporcionando qualidade de ranking drasticamente superior à dos dual-encoders.

Neste trabalho, o reranking utiliza o model text-embedding-3-large como segundo estágio: os top-K candidatos do primeiro estágio (small ou BM25+small) são recomputados com embeddings large de 3.072 dimensões. O Experimento 3 revelou que o reranking beneficia apenas quando o retriever é de qualidade inferior ao reranker (small → large melhora; large → large degrada), estabelecendo uma regra prática para pipelines multi-estágio.

### Diversificação com MMR

A Maximal Marginal Relevance (MMR), proposta por Carbonell e Goldstein (1998), equilibra relevância e diversidade nos resultados de busca: MMR(d) = λ × Sim(d, q) - (1-λ) × max(Sim(d, d_selecionado)). Com λ próximo de 1, a seleção prioriza relevância; com λ próximo de 0, prioriza diversidade. Santos et al. (2015) formalizaram o campo da diversificação de resultados de busca, demonstrando que a diversidade melhora a satisfação do usuário em consultas ambíguas ou multi-aspecto.

Para busca bíblica, a diversificação é particularmente relevante porque consultas teológicas frequentemente abrangem múltiplos livros, gêneros e períodos. Uma consulta sobre "cordeiro de Deus" deve retornar resultados de Êxodo (lei ritual), Isaías (profecia), João (narrativa evangélica) e Apocalipse (visão), não apenas múltiplos versículos de um único livro. O MMR com λ=0,3 demonstrou ser a feature mais consistentemente benéfica nos Experimentos 1-2: +16% R@20 e aumento de 4,3 para 5,9 livros bíblicos distintos nos top-10 resultados (Diversidade@10).

## Recuperação aumentada por conhecimento

### Fundamentos do RAG e integração de conhecimento

O paradigma de Retrieval-Augmented Generation (RAG), proposto por Lewis et al. (2020), combina recuperação de informação com geração de linguagem: dado uma consulta, recupera documentos relevantes de um corpus externo e utiliza esses documentos como contexto para um modelo de linguagem gerar a resposta. Guu et al. (2020) propuseram o REALM, que integra a recuperação diretamente no pré-treinamento do modelo de linguagem. Gao et al. (2024) apresentaram um levantamento abrangente que categoriza as variantes de RAG em três gerações: naive RAG (recuperação + geração simples), advanced RAG (com otimização de consulta, indexação e pós-processamento) e modular RAG (com componentes intercambiáveis).

A abordagem deste trabalho é análoga ao RAG, mas com uma diferença fundamental: a etapa de "geração" é substituída por extração de referências de um corpus curado. Enquanto o RAG utiliza um LLM para sintetizar respostas a partir de passagens recuperadas, nosso pipeline utiliza a CCEL como índice pré-existente de conexões teológicas, extraindo citações bíblicas explícitas dos parágrafos mais similares à consulta. Essa abordagem de "knowledge injection" evita os problemas de alucinação do RAG e garante rastreabilidade total — cada versículo injetado é rastreável a uma citação específica em uma obra identificada da tradição cristã clássica.

### A CCEL como corpus de conhecimento

A Christian Classics Ethereal Library (CCEL) é uma biblioteca digital que disponibiliza textos cristãos clássicos de domínio público, abrangendo toda a amplitude da tradição literária cristã desde os Pais da Igreja (século II d.C.) até o início do século XX. Diferentemente de um corpus de comentários bíblicos stricto sensu, a CCEL inclui: comentários verso-a-verso (Barnes, Jamieson-Fausset-Brown, Matthew Henry, Calvin), teologia sistemática (Boyce, Aquinas, Hodge), sermões (Spurgeon, Finney, Wesley), obras patrísticas (Agostinho, Crisóstomo, Atanásio, Gregório de Nissa), enciclopédias topicais (Nave's Topical Bible, Torrey's New Topical Textbook), dicionários bíblicos (Schaff) e obras devocionais, hinos e história eclesiástica.

A hipótese de que essa literatura funciona como "ponte semântica" baseia-se na observação de que conceitos teológicos abstratos (por exemplo, "cegueira espiritual", "silêncio de Deus") são amplamente discutidos na tradição interpretativa cristã, mas não aparecem literalmente no texto bíblico. Os comentários, sermões e enciclopédias contêm tanto o vocabulário conceitual da consulta ("spiritual blindness") quanto as referências bíblicas específicas associadas a esse conceito (Mateus 13:15, 2 Coríntios 4:4). Ao conectar consulta e versículo através de um intermediário textual curado por séculos de erudição, o sistema supera a limitação dos embeddings genéricos, que não foram treinados para reconhecer essas associações teológicas.

O trabalho de Mellerin (2014) com o BiblIndex — um índice online de citações bíblicas na literatura cristã primitiva — representa a iniciativa mais próxima: o BiblIndex cataloga referências bíblicas em textos patrísticos, mas como ferramenta de consulta acadêmica, não como componente de um sistema de recuperação automática. O presente trabalho é o primeiro a integrar embeddings de literatura cristã clássica como camada de enriquecimento em um pipeline de recuperação de versículos bíblicos.

## Avaliação de sistemas de recuperação de informação

### Métricas com relevância graduada

Järvelin e Kekäläinen (2002) propuseram o NDCG (Normalized Discounted Cumulative Gain), que estende as métricas binárias (relevante/não relevante) para relevância graduada, penalizando documentos relevantes em posições inferiores via desconto logarítmico. O NDCG tornou-se a métrica padrão para avaliação com julgamentos graduados. Kekäläinen e Järvelin (2002) demonstraram que julgamentos graduados proporcionam avaliação mais informativa que julgamentos binários, especialmente quando a diferença entre "essencial" e "tangencialmente relacionado" é significativa — como no caso de referências bíblicas com relevância 3 (essencial para a doutrina) versus 1 (menção tangencial).

Manning et al. (2008) formalizam as métricas complementares: Precision@K (fração de relevantes nos top-K), Recall@K (fração das referências gold encontradas nos top-K), MAP (média das precisões em cada posição relevante) e MRR (inverso da posição do primeiro relevante). A combinação dessas métricas proporciona uma visão multidimensional do desempenho do sistema.

### Construção de coleções de teste

O framework TREC (Text REtrieval Conference), consolidado por Voorhees e Harman (2005), estabelece o paradigma de Cranfield para avaliação de sistemas de recuperação: uma coleção de teste consiste em um corpus de documentos, um conjunto de tópicos (consultas) e julgamentos de relevância por assessores humanos. Zobel (1998) analisou a confiabilidade de experimentos em larga escala, demonstrando que julgamentos incompletos (quando nem todos os documentos são avaliados) podem subestimar o recall, mas permanecem viáveis para comparação entre sistemas quando o pool de avaliação é bem construído.

O benchmark BEIR (Thakur et al., 2021) estendeu essa abordagem para avaliação zero-shot heterogênea: 18 datasets de domínios diversos, incluindo domínios especializados onde modelos treinados em MS MARCO (Nguyen et al., 2016) podem falhar. O benchmark MIRACL (Zhang et al., 2023) expandiu para 18 idiomas incluindo português, com 726 mil julgamentos de relevância anotados por falantes nativos.

Este trabalho segue o paradigma TREC adaptado ao domínio bíblico: um corpus de 528.995 versículos, 50 consultas em 5 níveis de dificuldade, 445 julgamentos de relevância graduada (escala 1-3) e validação multi-fonte com rastreamento de proveniência. A escala é comparável ao QSST (Alqahtani et al., 2022) e inferior ao Loci Similes (545 paralelos, Schelb et al., 2025), mas é o primeiro benchmark formal para recuperação bíblica com relevância graduada.

## Processamento de linguagem natural em textos sagrados

### NLP aplicado a textos bíblicos

A aplicação de técnicas computacionais a textos bíblicos tem uma história que precede o aprendizado profundo. Resnik et al. (1999) e Christodouloupoulos e Steedman (2015) utilizaram a Bíblia como corpus paralelo para projeção de anotações e alinhamento entre idiomas, explorando a disponibilidade de traduções em centenas de línguas. Akerman et al. (2023) estenderam essa abordagem com o eBible Corpus, cobrindo 1.009 traduções em 833 idiomas para benchmarks de tradução automática.

Na interseção entre NLP e estudos bíblicos, Zhao e Liu (2018) criaram o BibleQA, um dataset de 1.001 perguntas com transferência de aprendizado do SQuAD para perguntas-e-respostas bíblicas. Embora seja a primeira aplicação formal de NLP para acesso ao conteúdo bíblico, o BibleQA é restrito a perguntas factuais em inglês, sem avaliação de recuperação aberta ou relevância graduada. McGovern et al. (2025) utilizaram embeddings neurais para detectar quiasmos — estrutura literária de inversão temática — em textos bíblicos, alcançando Precision@K de 0,80 em nível de versículo e identificando mais de 2.700 quiasmos. Smiley (2025) avaliou transformers (E5, AlephBERT, MPNet, LaBSE) para detecção de paralelos intertextuais em hebraico bíblico entre Samuel/Reis e Crônicas.

A revisão sistemática de MDPI Analytics (2025) cataloga o campo de IA aplicada a escrituras bíblicas, identificando lacunas significativas em avaliação formal de sistemas de recuperação. Swanson (2024) aborda considerações éticas e metodológicas no uso de textos religiosos em NLP, alertando para riscos de instrumentalização e perda de contexto litúrgico.

### NLP em outros textos sagrados

A busca semântica em textos sagrados não se limita à tradição cristã. Alqahtani et al. (2022) desenvolveram o QSST para busca semântica no Alcorão, treinando embeddings CBOW no corpus corânico com árabe clássico e alcançando 76,9% de precisão e 72,2% de recall com validação por três especialistas. Pesquisas mais recentes têm explorado embeddings baseados em LLMs para busca semântica em textos corânicos.

Miller et al. (2025) propuseram o pipeline ACT para detecção automática de padrões de citação em literatura rabínica (Bereshit Rabba, Vayikra Rabba), alcançando F1=0,91 na identificação de estilos de citação (simples, onda, eco, composto). Embora a tarefa seja diferente (detecção de citações versus recuperação de versículos), o trabalho valida o uso de referências cruzadas de textos sagrados como verdade fundamental para avaliação.

### Intertextualidade computacional

O campo de detecção computacional de intertextualidade, embora desenvolvido principalmente para literatura clássica, fornece os precedentes metodológicos mais relevantes. O projeto Tesserae (Coffee et al., 2012) estabeleceu a detecção automatizada de intertextualidade em poesia latina, utilizando correspondência de formas e lemas para identificar ~3.000 paralelos validados contra comentários acadêmicos, com precisão semântica de ~80%.

Schelb et al. (2025) propuseram o Loci Similes, o benchmark mais metodologicamente próximo a este trabalho: ~172.000 segmentos de literatura tardo-antiga, 545 paralelos verificados por especialistas entre autores como Jerônimo, Lactâncio e Virgílio, avaliados com pipeline de recuperação e reranking usando E5-large (R@10 ≈ 61%). O presente trabalho difere em cinco dimensões: corpus de texto sagrado (não literário), consultas conceituais abertas (não paralelos textuais), multi-versão em dois idiomas, enriquecimento por conhecimento externo e análise estratificada por dificuldade.

## Lacuna na literatura e posicionamento

A análise da literatura revela que nenhum trabalho publicado combina simultaneamente: (a) recuperação híbrida (léxica + densa) com métricas formais de recuperação de informação, (b) padrão-ouro graduado com proveniência multi-fonte e validação patrística, (c) estratégia multi-versão (17 traduções em dois idiomas) como mecanismo de recuperação, (d) enriquecimento por conhecimento de literatura cristã clássica como ponte semântica, e (e) análise estratificada por dificuldade com validação estatística formal incluindo controles negativos.

Os trabalhos mais próximos — QSST para o Alcorão, Loci Similes para intertextualidade latina, BibleQA para perguntas bíblicas e Smiley para paralelos hebraicos — abordam aspectos parciais do problema mas não a integração completa. Este trabalho posiciona-se como a primeira avaliação formal de recuperação híbrida aumentada por conhecimento para texto bíblico, com o objetivo de contribuir tanto para o campo de recuperação de informação em domínios especializados quanto para as humanidades digitais aplicadas a textos sagrados.
