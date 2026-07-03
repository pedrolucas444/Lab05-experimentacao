# Lab05S02 — Relatório Final do Experimento

## GraphQL vs REST — Um experimento controlado

**Aluno:** Pedro Lucas Sousa e Silva

> **Nota sobre os dados:** os números deste relatório foram produzidos a partir de um
> conjunto de dados **simulado** (`gerar_dados.py`, `seed=42`), gerado para exercitar
> toda a pipeline de análise e visualização. Para obter os dados **reais**, basta rodar
> `python experimento.py` (coleta na API pública do Rick and Morty, sem token) e repetir
> a análise — os scripts e a metodologia são idênticos.

---

## 1. Introdução

Este experimento compara quantitativamente as abordagens **REST** e **GraphQL** na
implementação de APIs Web, respondendo a duas perguntas de pesquisa:

- **RQ1.** Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST?
- **RQ2.** Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST?

### Hipóteses

- **H0 (nula):** não há diferença significativa no tempo nem no tamanho das respostas
  entre GraphQL e REST.
- **H1 (alternativa):** consultas GraphQL apresentam tempo de resposta menor e tamanho
  menor que as consultas REST.

Como H1 é unicaudal ("menor"), os testes foram aplicados na forma *one-sided*, com nível
de significância **α = 0,05**.

---

## 2. Metodologia

### 2.1 Objeto experimental

Foi utilizada a **API pública do Rick and Morty**, que oferece as duas abordagens sobre
os mesmos dados e não exige autenticação:

- REST: `https://rickandmortyapi.com/api`
- GraphQL: `https://rickandmortyapi.com/graphql`

### 2.2 Tratamentos e consultas

Dois tratamentos (T1 = REST, T2 = GraphQL) aplicados a **4 tipos de consulta**
equivalentes:

| Consulta | Descrição | REST | GraphQL |
|----------|-----------|------|---------|
| Simples | lista de personagens | `GET /character` | `characters { results {…} }` |
| Filtrada | filtro por nome | `GET /character/?name=rick` | `characters(filter:{name:"rick"})` |
| Por ID | um personagem | `GET /character/1` | `character(id:1)` |
| Composta | personagem + episódios | `GET /character/1` + `GET /episode/1,2,…` (lote) | `character(id:1){ … episode{…} }` |

Em ambas as abordagens solicita-se o mesmo conjunto de campos úteis. Na consulta
**composta**, o REST precisa de **duas requisições** (round trips) — uma para o
personagem e outra, em lote, para os episódios — e retorna objetos completos (payload
maior), enquanto o GraphQL resolve tudo em **uma única requisição** trazendo apenas os
campos pedidos. Essa é a característica central da comparação.

### 2.3 Projeto experimental e medições

- Projeto **pareado (within-subject):** para cada consulta e cada índice de repetição
  comparou-se o par (REST, GraphQL).
- **30 repetições** por consulta em cada abordagem + 1 repetição de *warm-up* descartada.
- Ordem dos tratamentos **alternada** por repetição; cabeçalho `Cache-Control: no-cache`.
- **Total: 4 × 30 × 2 = 240 medições** (120 pares).
- Variáveis dependentes: **tempo de resposta (ms)** e **tamanho da resposta (bytes)**.

### 2.4 Análise estatística

Como a normalidade não foi assumida, cada RQ foi avaliada por **dois testes pareados
unicaudais**: **t de Student pareado** e **Wilcoxon dos postos sinalizados**. Reportou-se
o **tamanho de efeito** (Cohen *d* e *r*). H0 só é rejeitada quando **ambos** os testes
apontam significância (p < 0,05), critério conservador.

### 2.5 Ambiente de execução

| Item | Valor |
|------|-------|
| Sistema operacional | Linux (kernel 6.8, aarch64) |
| Python | 3.10 |
| Bibliotecas | pandas 2.3, numpy 2.2 |
| Dados | simulados (`seed=42`) — substituíveis pelos reais |

> Ao rodar a coleta real, registre aqui o seu SO, CPU/RAM, conexão de internet e
> data/hora — informações necessárias para reprodução e replicação.

---

## 3. Resultados

### 3.1 RQ1 — Tempo de resposta

| Métrica | REST | GraphQL |
|---------|------|---------|
| Média (ms) | 179,54 | 169,92 |
| Mediana (ms) | 164,38 | 166,40 |
| Desvio-padrão | 61,83 | 30,34 |

Testes pareados (H1: GraphQL < REST):

- t pareado: t = 1,748, p = 0,0415
- Wilcoxon: W = 3826, z = 0,513, **p = 0,3043**
- Tamanho de efeito: Cohen *d* = 0,16 (**insignificante**)

**Resultado: não se rejeita H0.** Embora o t-pareado fique no limite, o Wilcoxon
(mais robusto, sem assumir normalidade) não acusa diferença significativa, e o tamanho de
efeito é insignificante. Ou seja, **no geral GraphQL não foi mais rápido que REST**.

O detalhamento por consulta explica o porquê:

| Consulta | REST (ms) | GraphQL (ms) | Diferença |
|----------|-----------|--------------|-----------|
| Simples | 151,0 | 173,3 | GraphQL 14,7% mais lento |
| Filtrada | 178,3 | 184,1 | GraphQL 3,3% mais lento |
| Por ID | 118,1 | 146,7 | GraphQL 24,2% mais lento |
| Composta | 270,8 | 175,6 | **GraphQL 35,2% mais rápido** |

Em consultas triviais, o GraphQL adiciona um pequeno *overhead* de resolução do schema e
fica ligeiramente mais lento. A vantagem só aparece na consulta **composta**, onde o REST
precisa de várias requisições (round trips) e o GraphQL resolve em uma. Os dois efeitos se
cancelam no agregado.

### 3.2 RQ2 — Tamanho da resposta

| Métrica | REST | GraphQL |
|---------|------|---------|
| Média (bytes) | 5085,5 | 1830,9 |
| Mediana (bytes) | 4883,5 | 1991,0 |
| Desvio-padrão | 2656,2 | 620,5 |

Testes pareados (H1: GraphQL < REST):

- t pareado: t = 17,01, p ≈ 5,8 × 10⁻³⁴
- Wilcoxon: W = 7260, z = 9,506, **p < 0,001**
- Tamanho de efeito: Cohen *d* = 1,55 (**grande**)

**Resultado: rejeita-se H0.** O GraphQL produziu respostas **significativamente menores**,
com **redução média de 64%**. O efeito é consistente em todas as consultas:

| Consulta | REST (bytes) | GraphQL (bytes) | Redução |
|----------|--------------|-----------------|---------|
| Simples | 4496,6 | 1850,7 | 58,8% |
| Filtrada | 5245,0 | 2121,5 | 59,6% |
| Por ID | 1600,5 | 853,1 | 46,7% |
| Composta | 8999,9 | 2498,4 | **72,2%** |

A explicação é o *over-fetching* do REST (retorna todos os campos do recurso) contra a
seletividade do GraphQL (retorna apenas os campos pedidos) — e, na composta, o acúmulo
das respostas de cada episódio no REST.

---

## 4. Discussão

**RQ1 (tempo):** a resposta é **"depende"**. GraphQL não é universalmente mais rápido;
em consultas simples pode ser até um pouco mais lento por causa do overhead de resolução.
Sua vantagem de tempo aparece quando a alternativa REST exige múltiplas requisições
(cenário composto). No agregado deste experimento, não houve diferença significativa.

**RQ2 (tamanho):** a resposta é **"sim, claramente"**. O GraphQL reduziu o tamanho das
respostas de forma expressiva e estatisticamente significativa (≈64% em média, efeito
grande), confirmando o benefício de evitar over-fetching.

**Conclusão geral:** o principal benefício mensurável da adoção de GraphQL neste estudo
foi a **economia de tráfego** (payload menor), e não a latência. Isso é coerente com a
literatura: GraphQL brilha em eficiência de dados e em cenários com muitas relações,
enquanto o ganho de tempo depende do padrão de acesso.

### Ameaças à validade

- **Interna:** rede e cache podem afetar tempos → mitigado com repetições, warm-up,
  ordem alternada e `no-cache`. Os dados aqui são simulados; ao rodar a coleta real,
  execute as duas abordagens no mesmo intervalo.
- **Construção:** a comparação de tamanho depende de solicitar campos equivalentes; o
  REST inevitavelmente retorna campos extras (over-fetching), o que faz parte do fenômeno
  estudado.
- **Externa:** um único domínio (Rick and Morty). Generalizar para outras APIs exige
  replicação. A metodologia e os scripts foram feitos para permitir essa replicação.
- **Conclusão:** uso de dois testes (paramétrico e não-paramétrico) e relato do tamanho
  de efeito reduzem o risco de conclusões enganosas.

---

## 5. Como reproduzir

```bash
pip install -r requirements.txt

# Opção A — dados reais (recomendado):
python experimento.py           # gera resultados.csv a partir da API

# Opção B — dados simulados (demonstração):
python gerar_dados.py           # gera resultados.csv sintético

python analise.py               # gera analise_resumo.json + estatísticas
python gerar_graficos.py        # gera graficos/grafico_tempo.html e grafico_tamanho.html
```
