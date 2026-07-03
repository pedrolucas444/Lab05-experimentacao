#!/usr/bin/env python3
"""
Análise estatística do experimento GraphQL vs REST (Sprint 2 - Passo 4).

Lê resultados.csv e responde:
  RQ1 - Respostas GraphQL são mais RÁPIDAS que REST? (tempo_ms)
  RQ2 - Respostas GraphQL têm TAMANHO menor que REST? (tamanho_bytes)

Projeto pareado (within-subject): para cada consulta e cada índice de
repetição comparamos o par (REST, GraphQL). Como não assumimos normalidade,
reportamos DOIS testes pareados unicaudais (H1: GraphQL < REST):
  - t de Student pareado
  - Wilcoxon dos postos sinalizados (não-paramétrico)
Além do p-valor, reportamos o tamanho de efeito (Cohen d e r).

As distribuições t e normal são implementadas aqui (sem scipy) para o script
rodar em qualquer ambiente. Saídas: analise_resumo.json + stdout.
"""
import json
import math
import numpy as np
import pandas as pd

ALFA = 0.05
CONSULTAS = ["simples", "filtrada", "por_id", "composta"]

# ---------- distribuições (sem scipy) ----------
def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 300, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS: break
    return h

def betai(a, b, x):
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    bt = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b

def t_two_sided(t, df):
    return betai(df / 2.0, 0.5, df / (df + t * t))

def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

# ---------- carga ----------
df = pd.read_csv("resultados.csv")

def pares(metrica):
    """Casa REST x GraphQL por (consulta, repeticao). Usa só pares completos,
    tolerando medições que tenham falhado em uma das abordagens."""
    rest = df[df.metodo == "REST"][["consulta", "repeticao", metrica]].rename(columns={metrica: "rest"})
    gql = df[df.metodo == "GraphQL"][["consulta", "repeticao", metrica]].rename(columns={metrica: "gql"})
    m = rest.merge(gql, on=["consulta", "repeticao"], how="inner")
    return m["rest"].to_numpy(dtype=float), m["gql"].to_numpy(dtype=float)

def t_pareado_unicaudal(rest, gql):
    dif = rest - gql
    n = len(dif)
    md, sd = dif.mean(), dif.std(ddof=1)
    t = md / (sd / math.sqrt(n))
    p_two = t_two_sided(t, n - 1)
    p_one = p_two / 2 if t > 0 else 1 - p_two / 2   # H1: dif>0 (GraphQL menor)
    return t, p_one, md / sd

def wilcoxon_unicaudal(rest, gql):
    dif = rest - gql
    dif = dif[dif != 0]
    n = len(dif)
    ordem = np.argsort(np.abs(dif))
    absd = np.abs(dif)[ordem]
    sinais = np.sign(dif)[ordem]
    postos = np.empty(n)
    ranks = np.arange(1, n + 1, dtype=float)
    i = 0
    while i < n:                                     # média de postos em empates
        j = i
        while j + 1 < n and absd[j + 1] == absd[i]:
            j += 1
        postos[i:j + 1] = ranks[i:j + 1].mean()
        i = j + 1
    w_pos = postos[sinais > 0].sum()
    mean_w = n * (n + 1) / 4.0
    var_w = n * (n + 1) * (2 * n + 1) / 24.0
    z = (w_pos - mean_w) / math.sqrt(var_w)
    zc = (w_pos - mean_w - 0.5) / math.sqrt(var_w)   # correção de continuidade
    p_one = 1 - norm_cdf(zc)                          # H1: mais postos positivos
    return w_pos, z, p_one, z / math.sqrt(n)

def interpreta_d(d):
    a = abs(d)
    return ("insignificante" if a < 0.2 else "pequeno" if a < 0.5
            else "médio" if a < 0.8 else "grande")

def analisar(metrica, rq):
    rest, gql = pares(metrica)
    dif = rest - gql
    t, p_t, d = t_pareado_unicaudal(rest, gql)
    w, z, p_w, r_eff = wilcoxon_unicaudal(rest, gql)
    return {
        "rq": rq, "metrica": metrica, "n_pares": int(len(rest)),
        "media_rest": round(float(rest.mean()), 2),
        "media_graphql": round(float(gql.mean()), 2),
        "mediana_rest": round(float(np.median(rest)), 2),
        "mediana_graphql": round(float(np.median(gql)), 2),
        "dp_rest": round(float(rest.std(ddof=1)), 2),
        "dp_graphql": round(float(gql.std(ddof=1)), 2),
        "reducao_pct": round(float((rest.mean() - gql.mean()) / rest.mean() * 100), 1),
        "skew_dif": round(float(pd.Series(dif).skew()), 3),
        "kurt_dif": round(float(pd.Series(dif).kurt()), 3),
        "t_stat": round(float(t), 3),
        "t_p": float(p_t), "t_p_fmt": (f"{p_t:.2e}" if p_t < 1e-4 else f"{p_t:.4f}"),
        "cohen_d": round(float(d), 3), "efeito_d": interpreta_d(d),
        "w_stat": round(float(w), 1), "w_z": round(float(z), 3),
        "w_p": float(p_w), "w_p_fmt": (f"{p_w:.2e}" if p_w < 1e-4 else f"{p_w:.4f}"),
        "r_efeito": round(float(r_eff), 3),
        "rejeita_h0": bool(p_t < ALFA and p_w < ALFA),
    }

def por_consulta(metrica):
    out = {}
    for c in CONSULTAS:
        sub = df[df.consulta == c]
        r = sub[sub.metodo == "REST"][metrica]
        g = sub[sub.metodo == "GraphQL"][metrica]
        out[c] = {
            "rest_media": round(float(r.mean()), 2),
            "graphql_media": round(float(g.mean()), 2),
            "rest_dp": round(float(r.std(ddof=1)), 2),
            "graphql_dp": round(float(g.std(ddof=1)), 2),
            "reducao_pct": round(float((r.mean() - g.mean()) / r.mean() * 100), 1),
        }
    return out

rq1 = analisar("tempo_ms", "RQ1")
rq2 = analisar("tamanho_bytes", "RQ2")

resumo = {
    "n_medicoes": int(len(df)), "n_pares": int(len(df) // 2), "alfa": ALFA,
    "rq1_tempo": rq1, "rq2_tamanho": rq2,
    "tempo_por_consulta": por_consulta("tempo_ms"),
    "tamanho_por_consulta": por_consulta("tamanho_bytes"),
}

with open("analise_resumo.json", "w", encoding="utf-8") as f:
    json.dump(resumo, f, indent=2, ensure_ascii=False)

def bloco(r, u):
    print(f"\n=== {r['rq']} ({r['metrica']}) ===")
    print(f"  Média  REST={r['media_rest']} {u} | GraphQL={r['media_graphql']} {u}  (redução {r['reducao_pct']}%)")
    print(f"  Mediana REST={r['mediana_rest']} | GraphQL={r['mediana_graphql']}")
    print(f"  t pareado : t={r['t_stat']}, p(uni)={r['t_p_fmt']}, Cohen d={r['cohen_d']} ({r['efeito_d']})")
    print(f"  Wilcoxon  : W={r['w_stat']}, z={r['w_z']}, p(uni)={r['w_p_fmt']}, r={r['r_efeito']}")
    print(f"  Rejeita H0? {'SIM' if r['rejeita_h0'] else 'NÃO'} (alfa={ALFA})")

print(f"N = {resumo['n_medicoes']} medições | {resumo['n_pares']} pares")
bloco(rq1, "ms")
bloco(rq2, "bytes")
print("\n[ok] analise_resumo.json salvo.")
