"""Reduce the full panel data to what this page uses.

Data dictionary of data/panel.json, per country (and per Brazilian region): n = name, g = open
sequences per year, c = reported cases per year, s = open sequences per year for DENV-1 to DENV-4.
`brazil.circ[region][serotype][year]` is true, false or null (no SINAN serotyping that year).

Reads ../painel/dados/{painel,geo}.json from the author's analysis tree and writes data/panel.json and
data/geo.json. Run after each rebuild of the full panel.
"""
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parent / "painel" / "dados"
TABLES = HERE.parent / "tabelas"
SEROTYPES = ["DENV-1", "DENV-2", "DENV-3", "DENV-4"]
REGION_EN = {"Norte": "North", "Nordeste": "Northeast", "Centro-Oeste": "Central-West", "Sudeste": "Southeast", "Sul": "South"}
FIRST_YEAR = 2001  # SINAN by macroregion starts in 2001; the whole page starts with it

d = json.loads((SOURCE / "painel.json").read_text())
k0 = d["anos"].index(FIRST_YEAR)
cut = lambda v: v[k0:] if v is not None else None
geo = json.loads((SOURCE / "geo.json").read_text())

countries = {}
for p in d["paises"]:
    iso = p["iso3"]
    s = d["serie"][iso]
    sero = d["sorotipo"].get(iso)
    countries[iso] = {
        "n": p["nome"],
        "g": cut(s["g"]),
        "c": cut(s.get("c")),
        "s": [cut(sero.get(k, [0] * len(d["anos"]))) for k in SEROTYPES] if sero else None,
    }

br = d["brasil"]
b0 = br["anos"].index(FIRST_YEAR)
brazil = {
    "years": br["anos"][b0:],
    "regions": {REGION_EN[m]: {"g": br["macro"][m]["g"][b0:], "c": br["macro"][m]["c"][b0:],
                               "s": [br["macro"][m][k][b0:] for k in SEROTYPES]}
                for m in br["macrorregioes"]},
}

# Serotype circulation by macroregion, from SINAN (probable cases with an identified serotype).
# TabNet only has serotype from 2014 on; before that the value stays None and the page falls back on
# the sequence rule. A serotype circulates in a macroregion-year with at least SINAN_MIN typed cases
# AND at least SINAN_SHARE of the typed cases: the absolute floor removes sparse entries (a median of
# 1 typed DENV-3 case per macroregion-year in 2014-2022), the share removes noise in large epidemic
# years, and 1% keeps the real return of DENV-3 to the Southeast in 2024 (1,307 cases, 1.2%).
SINAN_MIN, SINAN_SHARE = 10, 0.01
sinan = sorted(TABLES.glob("tab_br_sorotipo_sinan_macro_ano_*.tsv"))
if sinan:
    rows = [l for l in open(sinan[-1], encoding="utf-8") if not l.startswith("#")]
    circ = {m: [[None] * len(brazil["years"]) for _ in SEROTYPES] for m in brazil["regions"]}
    for r in csv.DictReader(rows, delimiter="\t"):
        y, reg = int(r["ano"]), REGION_EN.get(r["macrorregiao"])
        if reg not in circ or y not in brazil["years"] or r["DENV1"] in ("", "NA"):
            continue
        j = brazil["years"].index(y)
        # the current year is not in the full panel's case series; the SINAN total enters here
        if not brazil["regions"][reg]["c"][j] and r["total"] not in ("", "NA"):
            brazil["regions"][reg]["c"][j] = int(float(r["total"]))
        n = [float(r[c]) for c in ("DENV1", "DENV2", "DENV3", "DENV4")]
        typed = sum(n)
        for k in range(4):
            circ[reg][k][j] = bool(typed) and n[k] >= SINAN_MIN and n[k] >= SINAN_SHARE * typed
    brazil["circ"] = circ
    brazil["circ_source"] = sinan[-1].name

meta = d["meta"]
out = {
    "years": d["anos"][k0:],
    "serotypes": SEROTYPES,
    "target": meta["meta_d"],
    "dataVersion": meta["dataVersion"],
    "cutoff": next(f["corte"] for f in meta["fontes"] if f["automatica"]),
    "countries": countries,
    "brazil": brazil,
}
(HERE / "data" / "panel.json").write_text(json.dumps(out, separators=(",", ":")))
geo_min = {"viewBox": geo["viewBox"], "paths": geo["caminhos"], "points": geo["pontos"], "names": geo["nome_natural_earth"]}
(HERE / "data" / "geo.json").write_text(json.dumps(geo_min, separators=(",", ":")))
print("ok", len(countries), "countries")
