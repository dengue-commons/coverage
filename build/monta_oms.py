"""Camada de casos da OMS para os anos que o OpenDengue ainda não cobre (2025 e 2026).

Lê a API pública OData do xMart da OMS (V_DENGUE_GLOBAL_VALIDATED_PUBLIC), soma os casos por país e
ano e escreve dados/oms_casos.json. Esse arquivo é uma adaptação de dado da OMS e sai sob a licença
dela, CC BY-NC-SA 3.0 IGO, separado do resto do painel (CC BY 4.0). Nenhum dado bruto é guardado aqui.

    python3 monta_oms.py              # consulta a API
    python3 monta_oms.py --sem-rede   # usa a extração de 07/10/2026 em ../dados/oms_arbov/

Regras:
- um país-ano pode vir em mais de um tipo de período (epiweek, isoweek, month); fica o tipo com mais
  registros, e no empate o de maior total, para não somar a mesma semana duas vezes;
- só entram registros com casos informados e com início até a data da consulta;
- `ate` é o início do último período informado, para a tela dizer "até quando".
"""
import argparse
import datetime as dt
import io
import json
import pathlib
import sys

import pandas as pd

AQUI = pathlib.Path(__file__).resolve().parent
URL = "https://xmart-api-public.who.int/ARBOV/V_DENGUE_GLOBAL_VALIDATED_PUBLIC"
ANOS = (2025, 2026)
EXTRACAO_LOCAL = AQUI.parent / "dados" / "oms_arbov" / "registros_20261007.tsv"


def le_api() -> tuple[pd.DataFrame, str]:
    import requests

    r = requests.get(URL, timeout=180, headers={"Accept": "application/json"})
    r.raise_for_status()
    corpo = r.json()
    linhas = corpo.get("value", corpo)
    return pd.DataFrame(linhas), dt.date.today().isoformat()


def le_local() -> tuple[pd.DataFrame, str]:
    return pd.read_csv(EXTRACAO_LOCAL, sep="\t", comment="#", low_memory=False), "2026-10-07"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-rede", action="store_true")
    args = ap.parse_args()
    t, acesso = le_local() if args.sem_rede else le_api()

    for c in ("ISO3", "YEAR", "START_DATE", "DATE_TYPE", "CASES"):
        if c not in t.columns:
            print(f"campo {c} ausente na resposta da OMS: o esquema mudou", file=sys.stderr)
            return 1
    t["CASES"] = pd.to_numeric(t["CASES"], errors="coerce")
    t["YEAR"] = pd.to_numeric(t["YEAR"], errors="coerce")
    t["START_DATE"] = pd.to_datetime(t["START_DATE"], errors="coerce")
    t = t[t["YEAR"].isin(ANOS) & t["CASES"].notna() & (t["START_DATE"] <= pd.Timestamp(acesso))]

    paises: dict[str, dict] = {}
    for (iso, ano), g in t.groupby(["ISO3", "YEAR"]):
        por_tipo = g.groupby("DATE_TYPE").agg(n=("CASES", "size"), tot=("CASES", "sum"))
        tipo = por_tipo.sort_values(["n", "tot"], ascending=False).index[0]
        h = g[g["DATE_TYPE"] == tipo]
        paises.setdefault(iso, {})[str(int(ano))] = {
            "c": int(h["CASES"].sum()),
            "ate": h["START_DATE"].max().date().isoformat(),
        }

    saida = {
        "fonte": "WHO Global Dengue Surveillance, xMart public OData API, V_DENGUE_GLOBAL_VALIDATED_PUBLIC",
        "acesso": acesso,
        "anos": list(ANOS),
        "licenca": "CC BY-NC-SA 3.0 IGO",
        "atribuicao": (
            "Dengue cases 2025–2026: World Health Organization, Global Dengue Surveillance, "
            f"accessed {acesso}. Licence: CC BY-NC-SA 3.0 IGO. This is an adaptation of an original "
            "work by WHO (cases summed by country and year). The views expressed in this adaptation "
            "are the sole responsibility of the authors and do not necessarily represent the views, "
            "decisions or policies of WHO."
        ),
        "paises": paises,
    }
    (AQUI.parent / "dados" / "oms_casos.json").write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")))
    n = {a: sum(1 for p in paises.values() if str(a) in p) for a in ANOS}
    print("ok", n, "acesso", acesso)
    return 0


if __name__ == "__main__":
    sys.exit(main())
