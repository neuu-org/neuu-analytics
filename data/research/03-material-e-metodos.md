# Material e Métodos

## Visão geral do método experimental

Este trabalho adota uma abordagem experimental quantitativa, organizada em seis experimentos sequenciais, cada um isolando uma variável independente específica do pipeline de recuperação híbrida. O desenho progressivo permite atribuição causal: o Experimento 1 calibra parâmetros base, o Experimento 2 refina a curva de fusão léxico-semântica, o Experimento 3 avalia o impacto do modelo de embedding, o Experimento 4 testa fusão de embeddings multi-versão como experimento controlado negativo, o Experimento 5 introduz enriquecimento por conhecimento externo da literatura cristã clássica, e o Experimento 6 avalia o impacto de embeddings large (3.072 dimensões) no corpus CCEL em comparação pareada controlada com embeddings small.

A avaliação utiliza um padrão-ouro de 50 consultas com 445 referências graduadas, validadas contra seis datasets independentes e evidência patrística. Todas as métricas de recuperação de informação (Precision@K, Recall@K, MAP, NDCG@10, MRR) são calculadas por consulta e agregadas por nível de dificuldade, com testes estatísticos pareados (t de Student, Wilcoxon), intervalos de confiança bootstrap e correção de Bonferroni para comparações múltiplas.

## Construção do ecossistema de dados

A infraestrutura de dados deste trabalho foi construída integralmente do zero, compreendendo oito repositórios independentes de dados bíblicos, mais de cinquenta scripts de coleta, processamento e validação, e mais de um milhão de embeddings vetoriais gerados. Nenhum dataset pré-existente em formato computacional integrado estava disponível para a tarefa de recuperação bíblica com avaliação formal — toda a cadeia, da extração de dados brutos à validação do padrão-ouro, foi desenvolvida especificamente para esta pesquisa.

### Corpus bíblico multilíngue

O corpus de recuperação compreende 17 traduções bíblicas: oito em português brasileiro (NAA, ARA, NVI, AS21, ACF, NTLH, NVT, ARC) e nove em inglês (KJV, ASV, BSB, Darby, DRC, Geneva, AKJV, Webster, YLT). Cada tradução foi coletada de fontes de domínio público, normalizada para um esquema JSON hierárquico unificado (tradução > livro > capítulo > versículo > texto) e armazenada no repositório bible-text-dataset. O corpus totaliza 31.117 versículos canônicos multiplicados por 17 versões, resultando em 528.995 registros de versículos.

A escolha de múltiplas traduções não é redundância — é estratégia deliberada de recuperação. Cada tradução contribui vocabulário único: a NAA utiliza linguagem acadêmica moderna ("cordeiro"), a ARA preserva construções clássicas ("ovelha muda"), a KJV oferece terminologia teológica inglesa ("the Lamb of God"). Essa diversidade vocabular amplia o espaço de correspondência tanto para a busca léxica (BM25) quanto para a busca vetorial (embeddings), funcionando como uma forma implícita de expansão de consulta.

### Geração de embeddings vetoriais

Para cada um dos 528.995 versículos, foram gerados dois vetores de embedding utilizando os modelos text-embedding-3-small (1.536 dimensões) e text-embedding-3-large (3.072 dimensões) da OpenAI (OpenAI, 2024). Esses modelos utilizam a técnica Matryoshka Representation Learning (Kusupati et al., 2022), que produz representações vetoriais onde subconjuntos de dimensões preservam utilidade semântica. O total de embeddings gerados ultrapassa um milhão de vetores (528.995 versículos x 2 modelos).

Os embeddings foram armazenados em PostgreSQL com a extensão pgvector, utilizando índices IVFFlat para busca de similaridade por cosseno. A geração foi realizada via API OpenAI em lotes, com custo aproximado de USD 15 para o corpus completo. O processo levou aproximadamente 48 horas devido aos limites de taxa da API.

Adicionalmente, 2,2 milhões de parágrafos da CCEL (Christian Classics Ethereal Library) foram embedados com text-embedding-3-small (1.536 dimensões), armazenados em 222 arquivos Parquet (1,5 milhão de parágrafos com texto superior a 50 caracteres). Estes embeddings foram utilizados no Experimento 5 como camada de enriquecimento por conhecimento. Posteriormente, aproximadamente 1 milhão desses parágrafos foram também embedados com text-embedding-3-large (3.072 dimensões) para utilização no Experimento 6, permitindo comparação pareada controlada do impacto da dimensionalidade do embedding no enriquecimento por conhecimento.

### Comentários bíblicos

O corpus de comentários foi construído a partir de duas fontes complementares. A primeira, CatenaBible.com, foi coletada via scraping híbrido (Firecrawl + BeautifulSoup), resultando em 31.218 arquivos de versículos contendo 55.925 comentários individuais de mais de 100 Pais da Igreja e teólogos (período: 100 d.C. a 1700 d.C.). A segunda fonte, a CCEL, foi processada a partir de arquivos ThML/XML originais, incluindo os 45 volumes de Calvin (820 arquivos), os 260 arquivos de Barnes para o Novo Testamento, e os 1.189 arquivos de Jamieson, Fausset e Brown.

O pipeline de processamento seguiu quatro camadas: dados brutos (preservados intactos com checksums SHA-256), dados limpos (correção de encoding com ftfy, 14.906 correções, redução de 33% no tamanho), dados traduzidos (861 arquivos traduzidos para português via GPT-4o-mini) e dados enriquecidos (879 arquivos com análise teológica estruturada por IA). A separação rigorosa entre camadas garante que os dados originais nunca sejam contaminados por processamento posterior — princípio essencial para reprodutibilidade científica.

### Referências cruzadas bíblicas

O dataset de referências cruzadas consolida 1.117.491 arestas de conexão entre versículos bíblicos, cobrindo 31.060 versículos com média de 39,67 referências por versículo. As fontes são o OpenBible.info (343.610 pares com votos comunitários, licença CC-BY 2016) e o Treasury of Scripture Knowledge de Torrey (1897, domínio público, 500.000+ referências distribuídas em 32 fragmentos JSON).

O processo de consolidação envolveu normalização de mais de 86 aliases de nomes de livros para o padrão OSIS (Open Scripture Information Standard), merge com deduplicação, e cálculo de pontuação composta: score = votes + (number_of_sources × 2). A validação manual de uma amostra indicou taxa de aprovação de 97,3%, com cobertura bidirecional de 99,5%.

### Tópicos bíblicos e dicionários

O dataset de tópicos unifica 7.873 entradas de duas fontes enciclopédicas de domínio público: Nave's Topical Bible (5.320 tópicos, 1896) e Torrey's New Topical Textbook (622 tópicos, 1897), ambos parseados a partir de XML ThML da CCEL. Os tópicos foram enriquecidos com definições extraídas de cinco dicionários bíblicos: Easton (3.962 entradas, 1897), Smith (4.561 entradas, 1863), Hastings (5.033 entradas, 1898), Hitchcock (2.619 entradas, 1869) e Schaff (4.725 entradas), totalizando 20.900 entradas de dicionário. Dos tópicos, 75,6% possuem definições integradas e 48,7% receberam enriquecimento por IA.

### Gazetteers semânticos

O dataset de gazetteers contém 9.552 entidades e símbolos bíblicos organizados em 25 namespaces semânticos. As entidades (9.176 entradas) cobrem 13 categorias: PERSON (4.994), CONCEPT (1.811), PLACE (1.182), OBJECT (381), GROUP (321), EVENT (140), entre outras. Os símbolos (376 entradas) cobrem 12 categorias: OBJECT (213), NATURAL (103), ACTION (19), COLOR (9), entre outras. Cada entrada possui identificador canônico, aliases, descrição, referências bíblicas-chave e fontes de proveniência. O dataset foi construído a partir de seis fontes dicionárias, com classificação de namespace por IA e deduplicação automática.

### Corpus CCEL

A CCEL (Christian Classics Ethereal Library) é uma biblioteca digital que abrange toda a amplitude da literatura cristã clássica: comentários bíblicos (Barnes, Jamieson-Fausset-Brown, Matthew Henry, Calvin), teologia sistemática (Boyce, Aquinas, Hodge), sermões (Spurgeon, Finney, Wesley), obras patrísticas (Agostinho, Crisóstomo, Atanásio), enciclopédias topicais (Nave's Topical Bible, Torrey's New Topical Textbook, Schaff), devocionais, hinos e obras históricas. O corpus utilizado neste trabalho compreende 2.215.132 parágrafos distribuídos em 222 arquivos Parquet, dos quais 1.513.182 são parágrafos significativos (mais de 50 caracteres). Cada parágrafo possui metadados de autor, título, data de publicação e direitos, além de embedding pré-computado com text-embedding-3-small (1.536 dimensões).

### Resumo do ecossistema de dados

| Dataset | Fonte | Escala | Formato | Papel na pesquisa |
|---------|-------|--------|---------|-------------------|
| Texto bíblico | Múltiplas | 17 traduções, 528.995 versículos | JSON | Corpus de recuperação |
| Embeddings | OpenAI API | 1.057.990 vetores (small+large) | PostgreSQL pgvector | Busca semântica |
| Comentários | CatenaBible + CCEL | 55.925 comentários, 31.218 versículos | JSON (4 camadas) | Validação teológica |
| Referências cruzadas | OpenBible + TSK | 1.117.491 arestas, 31.060 versículos | JSON | Validação gold (estrutural) |
| Tópicos | Nave + Torrey | 7.873 tópicos unificados | JSON | Validação temática |
| Dicionários | 5 fontes | 20.900 entradas | JSON | Validação definicional |
| Gazetteers | 6 fontes | 9.552 entidades + símbolos | JSON | Classificação semântica |
| CCEL embeddings | CCEL + OpenAI | 1.513.182 parágrafos embedados (small + large) | Parquet | Enriquecimento (Exp5–6) |

## Construção do padrão-ouro

### Arquitetura de três fontes

O padrão-ouro (gold standard) para avaliação foi construído através de uma arquitetura de três fontes com rastreamento completo de proveniência, seguindo os princípios de avaliação de sistemas de recuperação de informação estabelecidos por Voorhees e Harman (2005).

A primeira fonte (curadoria por IA) produziu 50 consultas organizadas em cinco níveis de dificuldade operacional (10 consultas por nível), com 340 referências gold iniciais. Cada consulta inclui termos de busca bilíngues (português e inglês com sinônimos), livros bíblicos esperados e julgamentos de relevância em escala de 1 a 3 (1 = relacionado, 2 = relevante, 3 = essencial).

A segunda fonte (enriquecimento automatizado) validou cada referência gold contra seis datasets independentes através do script enrich_gold.py: referências cruzadas (1,2 milhão de links), tópicos (7.873 entradas), dicionário (5.998 entradas), comentários CCEL (30.990 entradas), símbolos (347 entradas) e entidades (2.474 entradas). O enriquecimento classifica cada referência em níveis de confiança: Gold-3 (curadoria manual + duas ou mais fontes independentes), Gold-2 (manual + uma fonte), Gold-1 (manual sem confirmação) e Silver (duas ou mais fontes sem curadoria manual).

A terceira fonte (validação humana) envolveu leitura do texto bíblico em tradução original (ARA), consulta a comentários patrísticos (CatenaBible, CCEL) e mapeamento de redes de referências cruzadas. A validação humana identificou lacunas que scripts não detectam: citações cruzadas entre comentários de diferentes autores (por exemplo, Gregório Magno em Jó 30:20 citando Salmo 22:2), inversões teológicas (Provérbios 1:28 como "silêncio invertido") e análise vocabular (por exemplo, "não te emudeças" em Salmo 28:1 como vocabulário explícito de silêncio divino). Cinco consultas foram validadas manualmente (uma por nível de dificuldade), resultando em 105 adições manuais e 289 confirmações humanas.

O processo de merge (merge_gold_set.py) combina as três fontes preservando proveniência: cada referência no arquivo final gold_set_final.json possui um array sources[] indicando exatamente quais fontes a sustentam (ai_curated, enrichment_confirmed, human_confirmed, manual).

### Classificação operacional de dificuldade

As 50 consultas foram classificadas em cinco níveis de dificuldade baseados em critérios operacionais que predizem o comportamento esperado dos componentes léxico e semântico do sistema:

**Extreme** (10 consultas): conceitos abstratos sem correspondência lexical direta no texto bíblico. Critérios: o conceito da consulta não aparece literalmente em nenhum versículo gold; as referências abrangem quatro ou mais livros em três ou mais gêneros literários; a conexão requer inferência teológica. Exemplos: "silêncio de Deus", "cegueira espiritual", "gemido da criação".

**Hard** (10 consultas): cadeias tipológicas entre Antigo e Novo Testamento. Critérios: referências gold abrangem AT e NT com conexão tipológica; vocabulário varia significativamente entre as referências; a conexão requer compreensão tipo-antítipo. Exemplos: "cordeiro de Deus", "pedra angular", "a serpente de bronze".

**Medium-hard** (10 consultas): frases específicas ou figuras raras com rede teológica mais ampla. Critérios: conceito tem versículo "primário" claro, mas compreensão completa requer conexão com rede mais ampla. Exemplos: "espinho na carne", "armadura de Deus", "a nuvem de testemunhas".

**Medium** (10 consultas): contrastes e paralelos indiretos. Critérios: conceito envolve contraste ou tensão entre AT e NT; vocabulário comum mas contextos teologicamente distintos. Exemplos: "olho por olho", "fruto do Espírito", "circuncisão do coração".

**Baseline** (10 consultas): narrativas conhecidas e frases diretas. Critérios: vocabulário da consulta aparece literalmente na maioria dos versículos gold; referências concentradas em livro ou passagens conhecidas. Exemplos: "a criação do mundo", "os dez mandamentos", "Noé e o dilúvio".

Um achado importante durante a validação humana foi que a dificuldade computacional difere da dificuldade cognitiva: "filho pródigo", inicialmente classificado como baseline, foi reclassificado para medium porque a expressão "pródigo" não aparece em nenhuma tradução bíblica portuguesa — o texto diz "um certo homem tinha dois filhos". Similarmente, "Melquisedeque" foi reclassificado de medium-hard para medium porque o nome próprio torna a busca léxica trivial.

### Princípios anti-circularidade

Para garantir a validade da avaliação, foram estabelecidos princípios explícitos anti-circularidade: (1) embeddings nunca são utilizados como fonte de validação — o mesmo mecanismo de busca não pode avaliar a si mesmo; (2) tópicos derivados do pipeline do projeto não são tratados como totalmente independentes; (3) fontes externas e manuais têm prioridade como gold; (4) cada fonte de validação tem sua proveniência registrada. A regra de ouro: quanto mais uma fonte foi derivada do corpus bíblico e do próprio pipeline do projeto, menor seu peso como verdade independente.

### Estatísticas finais do padrão-ouro

O padrão-ouro final contém 50 consultas e 445 referências graduadas. Das referências, 340 são provenientes de curadoria por IA, 105 são adições manuais, 339 foram confirmadas por enriquecimento automatizado e 289 receberam confirmação humana. A cobertura de validação humana abrange representantes de todos os cinco níveis de dificuldade.

## Pipeline de busca híbrida

### Arquitetura do sistema

O sistema de busca híbrida é implementado como uma API REST (Django/PostgreSQL) com seis estágios sequenciais:

**Estágio 1 — Busca léxica (BM25):** consulta ao índice tsvector do PostgreSQL com stemmer português/inglês, retornando os top-300 versículos por pontuação BM25. A indexação utiliza índices GIN (Generalized Inverted Index) para busca em tempo sublinear (~12ms após otimização, comparado a ~8.300ms sem índice).

**Estágio 2 — Busca semântica (embeddings):** o embedding da consulta é gerado via API OpenAI (text-embedding-3-small ou text-embedding-3-large) e comparado aos 528.995 embeddings de versículos por distância cosseno via pgvector, retornando os top-300 por similaridade.

**Estágio 3 — Fusão por Reciprocal Rank Fusion (RRF):** os rankings léxico e semântico são combinados pela fórmula de Cormack et al. (2009): score(d) = α × 1/(k + rank_bm25(d)) + (1-α) × 1/(k + rank_vector(d)), onde k=60 é a constante de suavização e α controla o peso relativo dos componentes (α=1.0 é puramente léxico, α=0.0 é puramente semântico).

**Estágio 4 — Expansão de consulta (opcional):** expansão por dicionário estático de sinônimos teológicos. O resultado do Experimento 2 demonstrou que esta expansão é neutra (sem impacto mensurável), pois o embedding da consulta é gerado antes da expansão — os sinônimos adicionados não enriquecem a representação vetorial.

**Estágio 5 — Reranking (opcional):** reordenação dos top-K candidatos utilizando o modelo text-embedding-3-large (3.072 dimensões) como cross-encoder, recalculando a similaridade cosseno entre o embedding large da consulta e os embeddings large de cada candidato.

**Estágio 6 — Diversificação MMR (opcional):** aplicação de Maximal Marginal Relevance (Carbonell e Goldstein, 1998): MMR(d) = λ × Sim(d,q) - (1-λ) × max(Sim(d, d_selecionado)), onde λ controla o equilíbrio entre relevância (λ=1.0) e diversidade (λ=0.0). O sistema utiliza λ=0.3 como padrão, priorizando diversidade de livros bíblicos nos resultados.

A deduplicação por versículo canônico é aplicada após a fusão: quando múltiplas versões do mesmo versículo aparecem nos resultados (por exemplo, João 1:29 na NAA, ARA e KJV), apenas a versão com maior pontuação é mantida.

### Correções pré-benchmark

Antes da execução dos experimentos, sete bugs foram identificados e corrigidos no pipeline para garantir a validade das medições:

1. O módulo de análise NLP (legado) substituía silenciosamente o parâmetro alpha fornecido pelo usuário — desativado completamente.
2. O alpha não respeitava o valor fornecido pelo usuário quando o NLP sugeria valor diferente — adicionada flag alpha_user_provided.
3. A deduplicação falhava quando MMR não estava ativo — adicionado caminho de deduplicação independente.
4. A busca BM25 utilizava proximity tsquery (17 resultados) ao invés de plainto_tsquery (154 resultados) — corrigido para plainto_tsquery.
5. O parâmetro top_k era aplicado antes da deduplicação, resultando em ~6 versículos únicos de 20 retornados — corrigido para aplicar após deduplicação.
6. A expansão de consulta poluía a busca BM25 com sinônimos genéricos (por exemplo, "Deus" expandido para "senhor" inundava resultados) — a expansão agora enriquece apenas o embedding, não o BM25.
7. O pool_size foi aumentado de 100 para 300 candidatos para garantir cobertura adequada antes da deduplicação.

### Pipeline de enriquecimento CCEL (Experimento 5)

Para o Experimento 5, foi desenvolvido um pipeline offline de enriquecimento por conhecimento que não modifica a API. O processo consiste em quatro etapas:

1. **Tradução de consultas:** as 50 consultas foram traduzidas de português para inglês via GPT-4o-mini, com validação manual dos termos teológicos-chave (por exemplo, "cordeiro de Deus" para "lamb of God", "bode expiatório" para "the scapegoat").

2. **Busca semântica no corpus CCEL:** para cada consulta traduzida, calcula-se a similaridade cosseno entre o embedding da consulta (text-embedding-3-small) e os 1.513.182 embeddings do corpus CCEL, utilizando NumPy em lotes para processamento eficiente em memória. Os 200 parágrafos mais similares são retidos por consulta.

3. **Extração de referências bíblicas:** expressões regulares extraem citações bíblicas dos textos dos parágrafos selecionados (por exemplo, "Matt. 13:15", "Gen. i. 26", "John 3:16"), com normalização para formato OSIS e conversão de números romanos.

4. **Injeção no ranking:** duas estratégias são testadas: (a) boost — versículos já presentes nos resultados da API recebem pontuação adicional proporcional à similaridade CCEL e ao número de citações independentes; (b) inject — versículos citados na CCEL mas ausentes nos top-30 da API são adicionados ao pool de candidatos.

A fórmula de pontuação CCEL é: score_ccel = max_similarity × (1 + 0,1 × min(citation_count, 5)), onde o fator 0,1 por citação adicional bonifica versículos mencionados por múltiplos autores independentes (até 50% de bônus para 5 ou mais citações), sob a premissa de que consenso entre fontes sinaliza relevância mais forte. A pontuação final combina: score_final = (1-w) × score_api + w × score_ccel, onde w é o peso CCEL.

## Desenho experimental

### Experimentos 1 e 2 — Calibração de parâmetros

O Experimento 1 testou 10 configurações cruzando quatro variáveis (alpha, expand, rerank, MMR) em 50 consultas, totalizando 500 chamadas à API. O Experimento 2 expandiu para 15 configurações com curva de alpha de 0,0 a 1,0 em passos de 0,1, mais quatro configurações de features (expand, rerank, MMR e pipeline completo), totalizando 750 chamadas. O Experimento 2 foi executado após a aplicação das sete correções no pipeline, constituindo o resultado definitivo para análise de parâmetros.

### Experimento 3 — Estratégias de embedding

O Experimento 3 testou 11 configurações comparando text-embedding-3-small (1.536 dimensões) e text-embedding-3-large (3.072 dimensões) como retriever primário, com variações de alpha (0,5 e 0,7), re-embedding após expansão e reranking cruzado (small como retriever + large como reranker). O total foi de 550 chamadas à API.

### Experimento 4 — Embeddings unificados (experimento controlado negativo)

O Experimento 4 testou se a fusão de embeddings de múltiplas versões bíblicas em um único embedding canônico por versículo (31.094 vetores unificados versus 528.995 vetores individuais) melhora a recuperação. Três estratégias de fusão foram testadas (média ponderada, média simples, max pooling) em 9 configurações, totalizando 450 chamadas. Este experimento foi desenhado como controle negativo — a hipótese era que a fusão poderia degradar a qualidade ao eliminar a diversidade vocabular entre versões.

### Experimento 5 — Recuperação aumentada por conhecimento (CCEL)

O Experimento 5 testou 11 configurações: um controle (reprodução do campeão do Experimento 3), quatro variações de peso CCEL (w=0,1, 0,3, 0,5, 1,0), um modo de injeção (w=0,3 com inject=true), três ablações (sem MMR, embedding small, alpha=0,5) e dois controles negativos (pontuações aleatórias e mapeamento embaralhado). O controle negativo com pontuações aleatórias substitui as similaridades CCEL reais por valores uniformes entre 0,3 e 0,8, verificando se qualquer boost numérico melhora os resultados independentemente do sinal semântico. O controle com mapeamento embaralhado permuta aleatoriamente a associação entre consultas e referências CCEL, verificando se o pareamento específico importa. As 11 configurações compartilham apenas 4 conjuntos únicos de parâmetros de API, resultando em 200 chamadas efetivas (as variações CCEL são aplicadas em pós-processamento offline).

### Experimento 6 — Embeddings large no corpus CCEL

O Experimento 6 avaliou o impacto de utilizar embeddings text-embedding-3-large (3.072 dimensões) no corpus CCEL, em substituição aos embeddings text-embedding-3-small (1.536 dimensões) utilizados no Experimento 5. O desenho experimental utiliza comparação pareada controlada: cada configuração do Experimento 5 é reproduzida com a única diferença sendo o modelo de embedding do corpus CCEL (small versus large), mantendo todos os demais parâmetros idênticos (alpha, peso CCEL, modo de injeção, MMR). Esse desenho permite atribuição causal direta ao modelo de embedding CCEL, isolando-o como única variável independente. Os embeddings large do corpus CCEL (3.072 dimensões) foram gerados para aproximadamente 1 milhão dos parágrafos CCEL, armazenados em formato Parquet.

## Métricas de avaliação

As métricas primárias seguem o framework de avaliação de recuperação de informação consolidado na literatura (Järvelin e Kekäläinen, 2002; Manning et al., 2008):

**Precision@K** (P@K): fração dos K primeiros resultados que são relevantes. Avaliado em K=5 e K=10.

**Recall@K** (R@K): fração das referências gold encontradas nos K primeiros resultados. Avaliado em K=10 e K=20.

**Mean Average Precision** (MAP): média das precisões calculadas em cada posição onde um documento relevante é encontrado, normalizada pelo total de documentos relevantes.

**Normalized Discounted Cumulative Gain** (NDCG@10): métrica que considera a relevância graduada (escala 1-3) e penaliza documentos relevantes em posições inferiores. Formulação: DCG = Σ rel_i / log2(i+1); NDCG = DCG / IDCG.

**Mean Reciprocal Rank** (MRR): inverso da posição do primeiro resultado relevante, indicando quão rapidamente o sistema apresenta um resultado útil.

**Diversidade@10**: número de livros bíblicos distintos representados nos 10 primeiros resultados.

### Testes estatísticos

Para comparação entre configurações, utilizaram-se testes pareados por consulta (n=50):

- **Teste t de Student pareado**: para cada métrica, calcula-se a diferença por consulta entre a configuração experimental e o controle, testando se a média das diferenças difere significativamente de zero.
- **Teste de Wilcoxon com sinais**: alternativa não-paramétrica quando a suposição de normalidade das diferenças não pode ser garantida.
- **d de Cohen**: tamanho do efeito, classificado como pequeno (d≈0,2), médio (d≈0,5) ou grande (d≈0,8).
- **Correção de Bonferroni**: para 7 métricas testadas simultaneamente, o nível de significância corrigido é α = 0,05/7 ≈ 0,0071.
- **Intervalos de confiança bootstrap**: 1.000 reamostras com reposição para estimar intervalos de 95% e 99% sem suposições distribucionais.

## Reprodutibilidade

Todos os repositórios de dados, scripts de processamento e resultados experimentais estão versionados em Git. Cada dataset possui rastreamento de proveniência (datas de extração, checksums SHA-256, versões de API utilizadas). Os arquivos de configuração de cada experimento (configs.json, configs_exp2.json, etc.) documentam os parâmetros exatos. Os resultados brutos de cada chamada à API são preservados em diretórios com timestamp (experiments/runs/{run_id}/raw/), permitindo verificação independente de qualquer resultado reportado. O padrão-ouro é regenerável a qualquer momento através do script merge_gold_set.py a partir das fontes imutáveis.
