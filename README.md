# Lab05S01 — Desenho e Preparação do Experimento
 
## GraphQL vs REST — Um experimento controlado
 
**Aluno:** Pedro Lucas Sousa e Silva
 
---
 
## 1. Desenho do Experimento
 
### A. Hipóteses
 
**Hipótese nula (H0):** Não existe diferença significativa no tempo de resposta nem no tamanho das respostas entre consultas GraphQL e REST.
 
**Hipótese alternativa (H1):** Consultas GraphQL apresentam tempo de resposta menor e tamanho das respostas menor quando comparadas às consultas REST.
 
> Observação: por H1 ser unicaudal ("menor"), os testes estatísticos da Sprint 2 serão aplicados na forma *one-sided* (t pareado ou Wilcoxon unicaudal).
 
### B. Variáveis Dependentes
 
São as métricas que serão medidas:
 
- Tempo de resposta (ms)
- Tamanho da resposta (bytes ou KB)
### C. Variáveis Independentes
 
São os fatores manipulados no experimento:
 
- Tipo de API: REST vs GraphQL
- Tipo de consulta: simples, filtrada, por ID e composta
### D. Tratamentos
 
- **T1 — REST:** consultas executadas usando endpoints REST tradicionais.
- **T2 — GraphQL:** as mesmas consultas executadas usando sintaxe GraphQL equivalente.
### E. Objetos Experimentais
 
Serão utilizadas:
 
- Uma API REST pública (ou construída pelo grupo).
- Uma API GraphQL equivalente, retornando os mesmos dados.
Sobre elas, serão feitas consultas do mesmo tipo:
 
- consulta simples — lista de itens;
- consulta filtrada — com parâmetro;
- consulta por ID;
- consulta composta — item + atributos relacionados.
### F. Tipo de Projeto Experimental
 
O experimento será um projeto controlado com **medidas repetidas (within-subject / pareado)**, pois:
 
- os mesmos objetos são testados em REST e em GraphQL;
- o mesmo ambiente será usado para evitar ruído externo;
- a comparação é direta entre tratamentos.
### G. Quantidade de Medições
 
Para cada consulta serão realizadas:
 
- 30 medições em REST;
- 30 medições em GraphQL.
**Total:** 4 consultas × 30 repetições × 2 tratamentos = **240 medições**.
 
### H. Ameaças à Validade
 
**Validade interna**
 
- Oscilações de rede podem afetar tempos → usar o mesmo computador e a mesma rede; aplicar repetições e usar a mediana.
- Cache pode interferir → usar cabeçalhos *no-cache* e descartar a primeira execução (warm-up).
**Validade externa**
 
- Resultados podem não representar todas as APIs → uso de apenas um domínio (limitação assumida e discutida no relatório final).
**Validade de construção**
 
- Implementações REST e GraphQL devem retornar exatamente os mesmos dados, para que a comparação de tamanho seja justa.
**Validade estatística / de conclusão**
 
- Poucas medições poderiam gerar ruído → 30 repetições por consulta mitigam o problema; além do p-valor, será relatado o tamanho de efeito.
---
 
## 2. Preparação do Experimento
 
### 2.1 Ambiente
 
O experimento será executado utilizando:
 
- Computador pessoal.
- Sistema operacional: Windows / macOS / Linux.
- **Python 3.11+** como linguagem principal (alinha com a análise da Sprint 2).
- Bibliotecas:
  - `requests` — para chamadas REST e POST GraphQL (única lib HTTP, evita dependências extras);
  - `csv` (biblioteca padrão) — para gravar os resultados;
  - `time.perf_counter` (padrão) — para medição de tempo de alta precisão.
- **Ferramentas da Sprint 2:** `pandas` (manipulação), `scipy` (testes estatísticos) e `matplotlib`/`seaborn` (visualizações).
> Decisão de ferramenta: optou-se por **Python + `requests`** em vez de Node.js/Axios por integração direta com Pandas, SciPy e Matplotlib na fase de análise, mantendo todo o pipeline (coleta → análise → dashboard) em uma só linguagem.
 
### 2.2 Scripts Necessários
 
**Script de coleta (REST e GraphQL unificado)**
 
- Executa cada uma das 4 consultas 30 vezes em cada abordagem.
- Mede tempo de resposta (ms) e tamanho da resposta (bytes).
- Alterna a ordem dos tratamentos e descarta o warm-up.
- Salva todos os resultados em um único CSV padronizado.
### 2.3 Consultas
 
As consultas escolhidas serão equivalentes em REST e GraphQL:
 
| # | Consulta | Descrição |
|---|----------|-----------|
| 1 | Simples | lista de itens |
| 2 | Filtrada | lista com parâmetro/filtro |
| 3 | Por ID | um item específico |
| 4 | Composta | item + atributos relacionados |
 
### 2.4 Estrutura do CSV
 
Cada linha registrada seguirá o formato:
 
| metodo | consulta | repeticao | tempo_ms | tamanho_bytes |
|--------|----------|-----------|----------|---------------|
| REST | simples | 1 | 123 | 4210 |
| GraphQL | simples | 1 | 98 | 1870 |
 
Isso permitirá análises diretas para RQ1 (tempo) e RQ2 (tamanho) na Sprint 2.
