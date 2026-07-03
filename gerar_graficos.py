#!/usr/bin/env python3
"""
Gera os 2 gráficos HTML interativos (Sprint 3 - Passo 6, adiantado).

Lê analise_resumo.json e produz, na pasta ./graficos:
  - grafico_tempo.html    -> RQ1 (tempo de resposta, ms)
  - grafico_tamanho.html  -> RQ2 (tamanho da resposta, bytes)

Cada gráfico é um arquivo autocontido (Chart.js via CDN): barras REST vs
GraphQL por tipo de consulta, com card de resumo estatístico e tooltip.
Basta abrir o .html no navegador.
"""
import json
import os

CONSULTAS = ["simples", "filtrada", "por_id", "composta"]
ROTULOS = {"simples": "Simples", "filtrada": "Filtrada", "por_id": "Por ID", "composta": "Composta"}
COR_REST, COR_GQL = "#378ADD", "#1D9E75"

with open("analise_resumo.json", encoding="utf-8") as f:
    resumo = json.load(f)

os.makedirs("graficos", exist_ok=True)

def pagina(titulo, subtitulo, unidade, por_consulta, rq, canvas_id):
    rest = [por_consulta[c]["rest_media"] for c in CONSULTAS]
    gql = [por_consulta[c]["graphql_media"] for c in CONSULTAS]
    labels = [ROTULOS[c] for c in CONSULTAS]
    dec = "0" if unidade == "bytes" else "1"
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titulo}</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; max-width: 820px; margin: 24px auto; padding: 0 16px; color: #1f1f1f; }}
  h1 {{ font-size: 22px; margin-bottom: 2px; }}
  .sub {{ color: #666; margin-top: 0; }}
  .cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 18px 0; }}
  .card {{ background: #f4f6f8; border-radius: 10px; padding: 12px 16px; min-width: 150px; }}
  .card .lbl {{ font-size: 12px; color: #666; }}
  .card .val {{ font-size: 22px; font-weight: bold; }}
  .legenda {{ display: flex; gap: 16px; margin: 10px 0 6px; font-size: 13px; color: #555; }}
  .legenda span {{ display: flex; align-items: center; gap: 5px; }}
  .dot {{ width: 11px; height: 11px; border-radius: 2px; display: inline-block; }}
  .wrap {{ position: relative; width: 100%; height: 380px; }}
  .nota {{ font-size: 12px; color: #999; margin-top: 12px; }}
  .concl {{ background: #eef6f2; border-left: 4px solid {COR_GQL}; padding: 10px 14px; border-radius: 0 8px 8px 0; margin-top: 16px; font-size: 14px; }}
</style>
</head>
<body>
  <h1>{titulo}</h1>
  <p class="sub">{subtitulo}</p>

  <div class="cards">
    <div class="card"><div class="lbl">Média REST</div><div class="val" style="color:{COR_REST}">{rq['media_rest']:.{dec}f} {unidade}</div></div>
    <div class="card"><div class="lbl">Média GraphQL</div><div class="val" style="color:{COR_GQL}">{rq['media_graphql']:.{dec}f} {unidade}</div></div>
    <div class="card"><div class="lbl">Redução com GraphQL</div><div class="val">{rq['reducao_pct']:.1f}%</div></div>
    <div class="card"><div class="lbl">p-valor (Wilcoxon)</div><div class="val">{rq['w_p_fmt']}</div></div>
  </div>

  <div class="legenda">
    <span><span class="dot" style="background:{COR_REST}"></span>REST</span>
    <span><span class="dot" style="background:{COR_GQL}"></span>GraphQL</span>
  </div>
  <div class="wrap">
    <canvas id="{canvas_id}" role="img" aria-label="Barras comparando REST e GraphQL por tipo de consulta"></canvas>
  </div>

  <div class="concl">
    <b>{rq['rq']}:</b> {
        "GraphQL apresentou " + unidade + " significativamente MENOR que REST (rejeita H0, confirma a hipótese)."
        if rq['rejeita_h0'] else
        ("GraphQL apresentou " + unidade + " significativamente MAIOR que REST — resultado contrário à hipótese (H1 rejeitada)."
         if rq['media_graphql'] > rq['media_rest'] else
         "não houve diferença estatisticamente significativa entre GraphQL e REST.")
    }
    &nbsp;Tamanho de efeito: Cohen d = {abs(rq['cohen_d'])} ({rq['efeito_d']}).
  </div>
  <p class="nota">N = {resumo['n_medicoes']} medições ({resumo['n_pares']} pares) · teste pareado unicaudal, α = {resumo['alfa']}. Gerado a partir de analise_resumo.json.</p>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
  <script>
    new Chart(document.getElementById('{canvas_id}'), {{
      type: 'bar',
      data: {{ labels: {json.dumps(labels, ensure_ascii=False)}, datasets: [
        {{ label: 'REST',    data: {json.dumps(rest)},  backgroundColor: '{COR_REST}' }},
        {{ label: 'GraphQL', data: {json.dumps(gql)}, backgroundColor: '{COR_GQL}' }}
      ]}},
      options: {{ responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: (c) => c.dataset.label + ': ' + c.parsed.y.toLocaleString('pt-BR') + ' {unidade}' }} }} }},
        scales: {{ x: {{ ticks: {{ autoSkip: false }} }},
                  y: {{ beginAtZero: true, title: {{ display: true, text: '{subtitulo}' }} }} }} }}
    }});
  </script>
</body>
</html>"""

# RQ1 - tempo
html_tempo = pagina(
    "REST vs GraphQL — Tempo de resposta (RQ1)",
    "Tempo médio de resposta (ms) por tipo de consulta",
    "ms", resumo["tempo_por_consulta"], resumo["rq1_tempo"], "graf_tempo")
with open(os.path.join("graficos", "grafico_tempo.html"), "w", encoding="utf-8") as f:
    f.write(html_tempo)

# RQ2 - tamanho
html_tam = pagina(
    "REST vs GraphQL — Tamanho da resposta (RQ2)",
    "Tamanho médio da resposta (bytes) por tipo de consulta",
    "bytes", resumo["tamanho_por_consulta"], resumo["rq2_tamanho"], "graf_tam")
with open(os.path.join("graficos", "grafico_tamanho.html"), "w", encoding="utf-8") as f:
    f.write(html_tam)

print("[ok] graficos/grafico_tempo.html e graficos/grafico_tamanho.html gerados.")
