"""WHO case layer for the years OpenDengue does not cover yet (2025 and 2026).

Reads the WHO xMart public OData API (V_DENGUE_GLOBAL_VALIDATED_PUBLIC), sums cases by country and
year and writes data/who_cases.json. That file is an adaptation of WHO data and keeps the WHO licence,
CC BY-NC-SA 3.0 IGO, separate from the rest of the page (CC BY 4.0). No raw data is stored here.

    python3 build_who_cases.py             # queries the API
    python3 build_who_cases.py --offline   # uses the 7 October 2026 extraction in the analysis tree

Rules:
- a country-year can come in more than one period type (epiweek, isoweek, month); the type with most
  records is kept, and on a tie the one with the larger total, so that no week is counted twice;
- only records with reported cases and a start date up to the query date enter;
- `until` is the start of the last reported period, so the page can say "up to when".
"""
import argparse
import datetime as dt
import io
import json
import pathlib
import sys

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
URL = "https://xmart-api-public.who.int/ARBOV/V_DENGUE_GLOBAL_VALIDATED_PUBLIC"
YEARS = (2025, 2026)
LOCAL_EXTRACTION = HERE.parent / "dados" / "oms_arbov" / "registros_20261007.tsv"


def read_api() -> tuple[pd.DataFrame, str]:
    import requests

    r = requests.get(URL, timeout=180, headers={"Accept": "application/json"})
    r.raise_for_status()
    corpo = r.json()
    linhas = corpo.get("value", corpo)
    return pd.DataFrame(linhas), dt.date.today().isoformat()


def read_local() -> tuple[pd.DataFrame, str]:
    return pd.read_csv(LOCAL_EXTRACTION, sep="\t", comment="#", low_memory=False), "2026-10-07"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    t, accessed = read_local() if args.offline else read_api()

    for c in ("ISO3", "YEAR", "START_DATE", "DATE_TYPE", "CASES"):
        if c not in t.columns:
            print(f"field {c} missing from the WHO response: the schema changed", file=sys.stderr)
            return 1
    t["CASES"] = pd.to_numeric(t["CASES"], errors="coerce")
    t["YEAR"] = pd.to_numeric(t["YEAR"], errors="coerce")
    t["START_DATE"] = pd.to_datetime(t["START_DATE"], errors="coerce")
    t = t[t["YEAR"].isin(YEARS) & t["CASES"].notna() & (t["START_DATE"] <= pd.Timestamp(accessed))]

    countries: dict[str, dict] = {}
    for (iso, year), g in t.groupby(["ISO3", "YEAR"]):
        by_type = g.groupby("DATE_TYPE").agg(n=("CASES", "size"), tot=("CASES", "sum"))
        kind = by_type.sort_values(["n", "tot"], ascending=False).index[0]
        h = g[g["DATE_TYPE"] == kind]
        countries.setdefault(iso, {})[str(int(year))] = {
            "c": int(h["CASES"].sum()),
            "until": h["START_DATE"].max().date().isoformat(),
        }

    out = {
        "source": "WHO Global Dengue Surveillance, xMart public OData API, V_DENGUE_GLOBAL_VALIDATED_PUBLIC",
        "accessed": accessed,
        "years": list(YEARS),
        "licence": "CC BY-NC-SA 3.0 IGO",
        "attribution": (
            "Dengue cases 2025–2026: World Health Organization, Global Dengue Surveillance, "
            f"accessed {accessed}. Licence: CC BY-NC-SA 3.0 IGO. This is an adaptation of an original "
            "work by WHO (cases summed by country and year). The views expressed in this adaptation "
            "are the sole responsibility of the authors and do not necessarily represent the views, "
            "decisions or policies of WHO."
        ),
        "countries": countries,
    }
    (HERE.parent / "data" / "who_cases.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    n = {a: sum(1 for p in countries.values() if str(a) in p) for a in YEARS}
    print("ok", n, "accessed", accessed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
