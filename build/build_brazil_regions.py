"""Project Brazil's five macroregions (IBGE boundaries) onto the same Equal Earth map as the world.

Source: IBGE malhas API v3, Brazil by region, minimal quality, downloaded on 8 October 2026 to
sources/ibge_brazil_regions_minimal.geojson. Writes data/brazil_regions.json. Uses the projection
helpers of the full panel (../painel/monta_geografia.py).
"""
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("geo", HERE.parent / "painel" / "monta_geografia.py")
geo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geo)

# IBGE region codes; names stay in Portuguese because the panel data key the regions by them
NAMES = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}

screen = geo.Tela()
fc = json.loads((HERE / "sources" / "ibge_brazil_regions_minimal.geojson").read_text())
out = {}
for f in fc["features"]:
    name = NAMES[f["properties"]["codarea"]]
    paths = []
    for ring in geo.geometria_para_aneis(f["geometry"]):
        pts = geo.douglas_peucker([screen(lon, lat) for lon, lat in ring], 0.25)
        if len(pts) >= 4 and geo.area(pts) > 0.3:
            paths.append(geo.anel_para_d(pts))
    out[name] = paths
(HERE / "data" / "brazil_regions.json").write_text(json.dumps(out, separators=(",", ":")))
print({k: len(v) for k, v in out.items()})
