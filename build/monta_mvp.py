"""Reduz dados/painel.json do painel completo ao que a versão mínima usa.

Lê ../painel/dados/{painel,geo}.json e escreve dados/mvp.json e dados/geo.json.
Rodar depois de cada ../painel/reconstroi.sh.
"""
import json
import pathlib

AQUI = pathlib.Path(__file__).resolve().parent
ORIGEM = AQUI.parent / "painel" / "dados"
SOROTIPOS = ["DENV-1", "DENV-2", "DENV-3", "DENV-4"]
ANO_INICIO = 2001  # o SINAN por macrorregião começa em 2001; o painel inteiro começa junto

d = json.loads((ORIGEM / "painel.json").read_text())
k0 = d["anos"].index(ANO_INICIO)
corta = lambda v: v[k0:] if v is not None else None
geo = json.loads((ORIGEM / "geo.json").read_text())

paises = {}
for p in d["paises"]:
    iso = p["iso3"]
    s = d["serie"][iso]
    soro = d["sorotipo"].get(iso)
    paises[iso] = {
        "n": p["nome"],
        "g": corta(s["g"]),
        "c": corta(s.get("c")),
        "s": [corta(soro.get(k, [0] * len(d["anos"]))) for k in SOROTIPOS] if soro else None,
    }

br = d["brasil"]
b0 = br["anos"].index(ANO_INICIO)
brasil = {
    "anos": br["anos"][b0:],
    "macro": {m: {"g": br["macro"][m]["g"][b0:], "c": br["macro"][m]["c"][b0:],
                  "s": [br["macro"][m][k][b0:] for k in SOROTIPOS]}
              for m in br["macrorregioes"]},
}

# Máscara de circulação por macrorregião, do SINAN (casos prováveis com sorotipo identificado).
# O TabNet só tem sorotipo de 2014 em diante; antes disso o valor fica None e o painel cai na regra
# dos genomas. Um sorotipo circula na macrorregião-ano com pelo menos LIMIAR_SINAN casos tipados E
# pelo menos PARTE_SINAN dos casos tipados: o piso absoluto tira digitação esparsa (1 a 9 casos de
# DENV-3 entre 2014 e 2022), a fração tira ruído em ano de epidemia grande, e 1% mantém a volta real
# do DENV-3 no Sudeste em 2024 (1.307 casos, 1,2% dos tipados).
LIMIAR_SINAN, PARTE_SINAN = 10, 0.01
tab_sinan = sorted((AQUI.parent / "tabelas").glob("tab_br_sorotipo_sinan_macro_ano_*.tsv"))
if tab_sinan:
    import csv
    linhas = [l for l in open(tab_sinan[-1], encoding="utf-8") if not l.startswith("#")]
    circ = {m: [[None] * len(brasil["anos"]) for _ in SOROTIPOS] for m in brasil["macro"]}
    for r in csv.DictReader(linhas, delimiter="\t"):
        a = int(r["ano"])
        if r["macrorregiao"] not in circ or a not in brasil["anos"] or r["DENV1"] in ("", "NA"):
            continue
        j = brasil["anos"].index(a)
        # o ano em curso não vem na série de carga do painel completo; o total do SINAN entra aqui
        if not brasil["macro"][r["macrorregiao"]]["c"][j] and r["total"] not in ("", "NA"):
            brasil["macro"][r["macrorregiao"]]["c"][j] = int(float(r["total"]))
        n = [float(r[c]) for c in ("DENV1", "DENV2", "DENV3", "DENV4")]
        tip = sum(n)
        for k in range(4):
            circ[r["macrorregiao"]][k][brasil["anos"].index(a)] = bool(tip) and n[k] >= LIMIAR_SINAN and n[k] >= PARTE_SINAN * tip
    brasil["circ"] = circ
    brasil["circ_fonte"] = tab_sinan[-1].name

meta = d["meta"]
saida = {
    "anos": d["anos"][k0:],
    "sorotipos": SOROTIPOS,
    "alvo": meta["meta_d"],
    "dataVersion": meta["dataVersion"],
    "corte": next(f["corte"] for f in meta["fontes"] if f["automatica"]),
    "paises": paises,
    "brasil": brasil,
}
(AQUI / "dados" / "mvp.json").write_text(json.dumps(saida, separators=(",", ":")))
geo_min = {k: geo[k] for k in ("viewBox", "caminhos", "pontos", "nome_natural_earth")}
(AQUI / "dados" / "geo.json").write_text(json.dumps(geo_min, separators=(",", ":")))
print("ok", len(paises), "países")
