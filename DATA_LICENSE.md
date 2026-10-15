# Data sources and licences

The MIT licence in `LICENSE` covers the Python code only. The files in `data/` and `fonts/` keep their own licences:

| File | Derived from | Licence |
|---|---|---|
| `data/app_data.json` (road geometry) | © OpenStreetMap contributors, `highway=motorway` ways, extracted 2026 | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) – this file is a derivative database and is shared under ODbL |
| `data/app_data.json` (opening years), `data/autoroute_sections_opening_years.csv` | French Wikipedia articles "Autoroute Axx (France)", plus OSM `start_date` tags | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| `data/bg.jpg` (relief) | AWS Terrain Tiles (SRTM, GMTED, ETOPO and others), Natural Earth country outlines; path-traced with forge3d | Open data; attribution: Mapzen / AWS Terrain Tiles, Natural Earth |
| `fonts/*.ttf` | Source Serif 4, Inter, Oswald (Google Fonts) | SIL Open Font License 1.1 (see `fonts/OFL-*.txt`) |

Opening years: about two thirds come from Wikipedia text; the rest were filled from general knowledge where no date was given
(`confidence` column in the CSV). Corrections are welcome.
