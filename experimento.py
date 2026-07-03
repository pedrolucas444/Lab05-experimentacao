#!/usr/bin/env python3
"""
Coleta do experimento controlado GraphQL vs REST (Sprint 2 - Passo 3).
======================================================================

Objeto experimental: API pública do Rick and Morty
  REST    -> https://rickandmortyapi.com/api
  GraphQL -> https://rickandmortyapi.com/graphql
Nenhuma autenticação/token é necessária.

Mede, para cada uma das 4 consultas do desenho, o TEMPO de resposta (ms) e o
TAMANHO da resposta (bytes) em REST e em GraphQL, repetindo N vezes.

As 4 consultas (equivalentes nas duas abordagens):
  1. simples  - lista de personagens (primeira página)
  2. filtrada - personagens com name="rick"
  3. por_id   - um personagem específico (id=1)
  4. composta - personagem + seus episódios relacionados
                (em REST exige várias requisições; em GraphQL, uma só)

Projeto pareado: a ordem dos tratamentos é alternada por repetição e a
primeira repetição é descartada como warm-up.

Saída: resultados.csv  (metodo, consulta, repeticao, tempo_ms, tamanho_bytes)

Uso:
    pip install -r requirements.txt
    python experimento.py                      # 30 repetições (padrão)
    python experimento.py --repeticoes 30 --pausa 0.3
    python experimento.py --dry-run            # valida sem requisitar
"""
import argparse
import csv
import sys
import time

try:
    import requests
except ImportError:
    requests = None

REST_BASE = "https://rickandmortyapi.com/api"
GRAPHQL_URL = "https://rickandmortyapi.com/graphql"

# Campos que a "aplicação precisa" — usados para manter equivalência semântica.
GQL_CHAR_FIELDS = "id name status species type gender image"

# Sessão reutilizada (keep-alive) — mais rápida e estável que requisições soltas.
SESSION = requests.Session() if requests else None
if SESSION is not None:
    SESSION.headers.update({
        "User-Agent": "lab05-experimento-graphql-rest",
        "Cache-Control": "no-cache",
    })

def _espera(r, i):
    """Backoff: espera mais quando toma 429 (rate limit)."""
    if r is not None and r.status_code == 429:
        retry_after = r.headers.get("Retry-After")
        time.sleep(float(retry_after) if retry_after else 3.0 * (i + 1))
    else:
        time.sleep(0.6 * (i + 1))

def _timed_get(url, tentativas=6):
    """GET com retentativas. Mede APENAS a requisição bem-sucedida (exclui as
    esperas de backoff). Retorna (tempo_ms, response)."""
    ultimo, r = None, None
    for i in range(tentativas):
        try:
            t0 = time.perf_counter()
            r = SESSION.get(url, timeout=30)
            dt = (time.perf_counter() - t0) * 1000.0
            if r.status_code == 200 and r.content:
                return dt, r
            ultimo = f"HTTP {r.status_code}"
        except Exception as e:
            r, ultimo = None, str(e)
        _espera(r, i)
    raise RuntimeError(f"falha ao buscar {url}: {ultimo}")

def _timed_post(url, payload, tentativas=6):
    ultimo, r = None, None
    for i in range(tentativas):
        try:
            t0 = time.perf_counter()
            r = SESSION.post(url, json=payload, timeout=30)
            dt = (time.perf_counter() - t0) * 1000.0
            if r.status_code == 200 and r.content:
                return dt, r
            ultimo = f"HTTP {r.status_code}"
        except Exception as e:
            r, ultimo = None, str(e)
        _espera(r, i)
    raise RuntimeError(f"falha ao consultar {url}: {ultimo}")

# ---------------------------------------------------------------------------
# Consultas REST — cada função retorna (tempo_ms, tamanho_bytes)
# ---------------------------------------------------------------------------
def rest_simples():
    t, r = _timed_get(f"{REST_BASE}/character")
    return t, len(r.content)

def rest_filtrada():
    t, r = _timed_get(f"{REST_BASE}/character/?name=rick")
    return t, len(r.content)

def rest_por_id():
    t, r = _timed_get(f"{REST_BASE}/character/1")
    return t, len(r.content)

def rest_composta():
    # Personagem + episódios relacionados. Em REST são 2 requisições (round
    # trips): uma para o personagem e outra em lote para os episódios. Em
    # GraphQL, tudo em 1 requisição. O REST ainda retorna objetos completos
    # (payload maior); o GraphQL, só os campos pedidos. Somamos o tempo e o
    # tamanho das duas requisições REST.
    t_total, tam = 0.0, 0
    t1, r = _timed_get(f"{REST_BASE}/character/1")
    t_total += t1
    tam += len(r.content)
    ids = [u.rsplit("/", 1)[-1] for u in r.json().get("episode", [])]
    if ids:
        t2, er = _timed_get(f"{REST_BASE}/episode/{','.join(ids)}")
        t_total += t2
        tam += len(er.content)
    return t_total, tam

# ---------------------------------------------------------------------------
# Consultas GraphQL (mesma informação, uma única requisição)
# ---------------------------------------------------------------------------
GQL = {
    "simples":  f'{{ characters {{ results {{ {GQL_CHAR_FIELDS} }} }} }}',
    "filtrada": f'{{ characters(filter: {{ name: "rick" }}) {{ results {{ {GQL_CHAR_FIELDS} }} }} }}',
    "por_id":   f'{{ character(id: 1) {{ {GQL_CHAR_FIELDS} }} }}',
    "composta": f'{{ character(id: 1) {{ {GQL_CHAR_FIELDS} episode {{ id name air_date }} }} }}',
}

def graphql(consulta):
    t, r = _timed_post(GRAPHQL_URL, {"query": GQL[consulta]})
    return t, len(r.content)

REST_FUNCS = {
    "simples": rest_simples,
    "filtrada": rest_filtrada,
    "por_id": rest_por_id,
    "composta": rest_composta,
}
CONSULTAS = ["simples", "filtrada", "por_id", "composta"]

def main():
    ap = argparse.ArgumentParser(description="Coleta GraphQL vs REST (Rick and Morty API)")
    ap.add_argument("--repeticoes", type=int, default=30)
    ap.add_argument("--saida", default="resultados.csv")
    ap.add_argument("--pausa", type=float, default=0.5, help="pausa (s) entre requisições")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = len(CONSULTAS) * 2 * args.repeticoes
    print(f"[info] {len(CONSULTAS)} consultas x 2 abordagens x {args.repeticoes} reps = {total} medições")
    print("[info] 1 repetição extra de warm-up por consulta será descartada")

    if args.dry_run:
        print("[dry-run] Consultas GraphQL montadas:")
        for k, v in GQL.items():
            print(f"   {k}: {v}")
        print("[dry-run] OK — nada foi requisitado.")
        return

    if requests is None:
        sys.exit("[erro] instale 'requests': pip install -r requirements.txt")

    linhas = []
    for consulta in CONSULTAS:
        extra = " (esta é a mais demorada — REST faz várias requisições)" if consulta == "composta" else ""
        print(f"[coleta] {consulta} ...{extra}", flush=True)
        for rep in range(args.repeticoes + 1):     # +1 = warm-up
            eh_warmup = rep == 0
            if not eh_warmup:
                print(f"   {consulta}: repetição {rep}/{args.repeticoes}", flush=True)
            ordem = ["REST", "GraphQL"] if rep % 2 == 0 else ["GraphQL", "REST"]
            for metodo in ordem:
                try:
                    if metodo == "REST":
                        t, tam = REST_FUNCS[consulta]()
                    else:
                        t, tam = graphql(consulta)
                except Exception as e:
                    print(f"   [erro] {metodo}/{consulta}: {e}")
                    t, tam = None, None
                if not eh_warmup and t is not None:
                    linhas.append({
                        "metodo": metodo,
                        "consulta": consulta,
                        "repeticao": rep,
                        "tempo_ms": round(t, 2),
                        "tamanho_bytes": tam,
                    })
                time.sleep(args.pausa)

    with open(args.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metodo", "consulta", "repeticao", "tempo_ms", "tamanho_bytes"])
        w.writeheader()
        w.writerows(linhas)
    print(f"[ok] {len(linhas)} medições salvas em {args.saida}", flush=True)

if __name__ == "__main__":
    main()
