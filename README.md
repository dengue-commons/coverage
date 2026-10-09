# Dengue genomic surveillance coverage

Open dengue virus sequences per country and year, against a minimum of 59 open sequences a year for each
circulating serotype, the smallest random sample that detects a lineage at 5% prevalence with 95%
confidence. Brazil is shown by macroregion and serotype.

**Draft, version 0.2.** Data frozen on 7–8 October 2026; map states revised on 9 October 2026. Methods, the derivation of the target and the
full data are in: Bermann T, et al. *Open genomic surveillance of dengue virus against reported and
modeled burden, worldwide, 2001–2026.* In preparation.

Live page: https://dengue-commons.github.io/coverage/

## Data

| layer | source | years |
|---|---|---|
| open sequences (≥505 bp) | [Pathoplexus](https://pathoplexus.org) open data, LAPIS API, dataVersion 1791217786 | 2001–2026 |
| reported cases | [OpenDengue](https://opendengue.org) National extract V1.3 (Clarke et al. 2024, Sci Data 11:296) | 2001–2024 |
| reported cases | WHO Global Dengue Surveillance, xMart public API | 2025–2026 |
| cases and serotyping, Brazil | SINAN, Ministry of Health of Brazil, via DATASUS TabNet | 2001–2026 |
| Brazil macroregions | IBGE malhas API | static |
| world map | Natural Earth, public domain | static |

The map has three states, and serotype circulation never comes from the sequences themselves. Where
no serotype reached 59, the place falls short whatever circulated and is colored by its
most-sequenced serotype. Where one did and no case typing is available, the cell is amber: the other
serotypes cannot be judged. Where case typing exists (Brazil from 2014 on, a serotype circulates in a
region when SINAN reports at least 10 typed cases of it and at least 1% of the typed cases there),
each circulating serotype must reach 59.

## Licence

- Code: MIT (`LICENSE`).
- Our derived data and text: CC BY 4.0 (`LICENSE-data`).
- `data/who_cases.json` is an adaptation of WHO data and keeps the WHO licence, CC BY-NC-SA 3.0 IGO
  (`data/who_cases.LICENSE.txt`).
- OpenDengue counts: CC BY 4.0, from OpenDengue; changes were made (aggregated by country and year).

## Links and data files

The page opens on a given year and country with `?year=2025&country=BRA` (ISO 3166-1 alpha-3).

`data/panel.json` holds, per country and per Brazilian region: `n` name, `g` open sequences per year,
`c` reported cases per year, `s` open sequences per year for DENV-1 to DENV-4. `data/who_cases.json`
holds WHO cases per country for 2025 and 2026 (`c`, and `until`, the start of the last reported
period). The CSV behind the "Download CSV" button is built from these files in the browser.

## Running locally

```bash
python3 -m http.server 8000
```

and open http://localhost:8000/. The page reads the JSON files in `data/`. The scripts in `build/`
are the ones that produced them; in this version they run inside the author's analysis tree, and
`build/build_who_cases.py` runs standalone against the WHO API.
