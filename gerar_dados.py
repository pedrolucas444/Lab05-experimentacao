#!/usr/bin/env python3
"""
Gera um dataset SIMULADO (fallback) para exercitar a análise e os gráficos
sem precisar rodar a coleta real (experimento.py).

>>> Use os dados REAIS sempre que possível: rode `python experimento.py`.
    Este script existe apenas para demonstrar a pipeline de ponta a ponta.

Estrutura idêntica à saída real: 4 consultas x 30 reps x 2 métodos = 240 linhas.
Colunas: metodo, consulta, repeticao, tempo_ms, tamanho_bytes
"""
import csv
import random

random.seed(42)  # reprodutibilidade

CONSULTAS = ["simples", "filtrada", "por_id", "composta"]
REPS = 30

# Perfis (média, desvio) por consulta e método, inspirados no comportamento
# esperado da API do Rick and Morty:
#  - Tamanho: REST sofre over/under-fetching -> maior que GraphQL, sobretudo na
#    consulta composta (várias respostas de episódios somadas).
#  - Tempo: GraphQL tem leve overhead em consultas triviais, mas vence na
#    composta, onde REST faz múltiplas requisições (round trips).
PERFIS = {
    "simples":  {"tempo": {"REST": (150, 22), "GraphQL": (168, 26)},
                 "tam":   {"REST": (4500, 180), "GraphQL": (1850, 90)}},
    "filtrada": {"tempo": {"REST": (172, 25), "GraphQL": (185, 28)},
                 "tam":   {"REST": (5200, 210), "GraphQL": (2100, 110)}},
    "por_id":   {"tempo": {"REST": (118, 18), "GraphQL": (138, 22)},
                 "tam":   {"REST": (1600, 70), "GraphQL": (860, 45)}},
    "composta": {"tempo": {"REST": (275, 34), "GraphQL": (182, 27)},
                 "tam":   {"REST": (9000, 320), "GraphQL": (2500, 130)}},
}

def amostra(media, desvio, minimo):
    return max(minimo, random.gauss(media, desvio))

linhas = []
for consulta in CONSULTAS:
    for metodo in ["REST", "GraphQL"]:
        tmu, tsd = PERFIS[consulta]["tempo"][metodo]
        smu, ssd = PERFIS[consulta]["tam"][metodo]
        for rep in range(1, REPS + 1):
            linhas.append({
                "metodo": metodo,
                "consulta": consulta,
                "repeticao": rep,
                "tempo_ms": round(amostra(tmu, tsd, 20), 2),
                "tamanho_bytes": int(round(amostra(smu, ssd, 100))),
            })

with open("resultados.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["metodo", "consulta", "repeticao", "tempo_ms", "tamanho_bytes"])
    w.writeheader()
    w.writerows(linhas)

print(f"resultados.csv gerado com {len(linhas)} linhas (SIMULADO, seed=42)")
