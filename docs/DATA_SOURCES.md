# Data sources

Every dataset used by the pipeline, where it comes from, how to get it, and what it's used for. Snapshot dates are when the data in this project was downloaded; re-running the scripts fetches the current version.

Licences: check each publisher's dataset page before redistributing data. This repo contains **no data**, only the scripts that download it.

## Planning applications

| Dataset | Publisher | Access | Snapshot | Coverage | Used for |
|---|---|---|---|---|---|
| **Foundations** London housing applications | House London hackathon ([Foreman/Foundations](https://foreman.house-london.uk/)), built on [PlanIt](https://www.planit.org.uk/) council scrapes | Provided to participants; copy `foundations_london_housing_*.csv` into the project root | Fetched 2026-08-10 (in filename) | 181,929 applications, 35 London planning authorities, start dates 2022–2025. Rows filtered to `housing_relevance_score ≥ 0.9` by the publisher | **Labels**: outcome (`status`), S106 (`decision` text). Description text. Location |
| **Planning London Datahub (PLD)** | Greater London Authority ([about](https://www.london.gov.uk/programmes-strategies/planning/digital-planning/planning-london-datahub), [API guide](https://www.london.gov.uk/sites/default/files/planninglondondatahub_api_connection_technical_documentation_v1.pdf)) | `python scripts/download_pld.py` (Elasticsearch guest API) | 2026-09-26 | 447,502 applications validated 2022-01-01 to 2025-12-31, all 33 boroughs plus LLDC, OPDC, OSDC | **Proposal features**: units, tenure, bedrooms, storeys, height, site area and polygon, floorspace, use classes, parking, application type |

## Site constraints ([planning.data.gov.uk](https://www.planning.data.gov.uk/), MHCLG)

All via `python scripts/download_spatial.py`, streamed from `https://files.planning.data.gov.uk/dataset/<name>.csv` and clipped to a London bounding box. Snapshot 2026-09-26.

| Dataset | London features | Used for |
|---|---|---|
| `conservation-area` | 1,320 | `in_conservation_area` |
| `article-4-direction-area` | 2,532 | `in_article4_area` |
| `listed-building-outline` | 15,669 | `listed_building_within_25m` |
| `tree-preservation-zone` | 16,428 | `in_tpo_zone` |
| `green-belt` | 44 | `in_green_belt` |
| `brownfield-land` (points) | 7,216 | `brownfield_site_within_50m` |
| `flood-risk-zone` (Environment Agency flood zones 2 and 3) | 29,716 | `flood_zone` |

## London Plan designations ([London Datastore](https://data.london.gov.uk/), GLA)

| Dataset | Features | Used for |
|---|---|---|
| Opportunity Areas | 35 | `in_opportunity_area` |
| Strategic Industrial Land | 148 | `in_sil` |
| Town centre boundaries | 234 | `in_town_centre` |
| [Referable planning applications 2011–2024](https://data.london.gov.uk/dataset/referral-planning-applications-since-2011-2w1xz) | xlsx | Downloaded for reference; not yet joined (`mayor_referable` is currently derived from the 150-home / 30 m rule) |

## Transport and deprivation

| Dataset | Publisher | Used for |
|---|---|---|
| [PTAL 2023, 100 m grid](https://gis-tfl.opendata.arcgis.com/datasets/0646faf45243463aa04ca685e598f471) (159,451 cells) | Transport for London | `ptal_ai`, `ptal_level`, `ptal_ordinal` |
| LSOA December 2021 boundaries (generalised, 5,908 in London) | ONS Open Geography Portal | Point → LSOA lookup |
| [English Indices of Deprivation 2025](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025), File 7 | MHCLG | `imd_decile`, `imd_score` |

## Available but not used by the model

| Dataset | Notes |
|---|---|
| London domestic EPC certificates (`london-domestic-epc.csv`, 3.6M rows, 2012–2026) | Held locally. Describes existing homes; useful for completion tracking, not needed for approval prediction |
| planning.data.gov.uk `developer-agreement*` (S106 agreements and contributions) | Only Greenwich (370) and Islington (87) have London data, so not used as labels |
| Borough S106 registers ([Tower Hamlets](https://pfm.exacom.co.uk/towerhamlets/s106.php), [Southwark](https://pfm.exacom.co.uk/southwark/index.php)) | Possible gold-standard S106 labels for a subset; not downloaded |

## How the sources join

1. **Foundations ↔ PLD** on `(borough, normalised reference)`: upper-case, punctuation stripped (`23/AP/1312` → `23AP1312`). Foundations borough names are mapped to PLD's (`Kensington` → `Kensington & Chelsea`, etc.; see `BOROUGH_MAP` in `scripts/build_features.py`). Match rate on the final table: 96.8%.
2. **Location**: Foundations `lat`/`lng`, falling back to the PLD centroid, both checked against London bounds.
3. **Spatial layers**: all reprojected to British National Grid (EPSG:27700), then point-in-polygon (or a buffer for listed buildings and brownfield points; nearest cell within 150 m for PTAL).
4. **Deprivation**: point → LSOA 2021 code → IMD 2025 row.
