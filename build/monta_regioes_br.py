"""Projeta as cinco macrorregiões do Brasil (malha do IBGE) na mesma Equal Earth do mapa-múndi.

Fonte: API de malhas do IBGE, v3, Brasil por região, qualidade mínima, baixada em 08/10/2026
para fontes/ibge_regioes_br_minima.geojson. Escreve dados/br_regioes.json.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("geo", AQUI.parent / "painel" / "monta_geografia.py")
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)

# códigos de região do IBGE
NOMES = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}

tela = geo.Tela()
fc = json.loads((AQUI / "fontes" / "ibge_regioes_br_minima.geojson").read_text())
saida = {}
for f in fc["features"]:
    nome = NOMES[f["properties"]["codarea"]]
    caminhos = []
    for anel in geo.geometria_para_aneis(f["geometry"]):
        pts = geo.douglas_peucker([tela(lon, lat) for lon, lat in anel], 0.25)
        if len(pts) >= 4 and geo.area(pts) > 0.3:
            caminhos.append(geo.anel_para_d(pts))
    saida[nome] = caminhos
(AQUI / "dados" / "br_regioes.json").write_text(json.dumps(saida, separators=(",", ":")))
print({k: len(v) for k, v in saida.items()})
