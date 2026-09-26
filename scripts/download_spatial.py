"""Download site-context layers for London into data/raw/spatial/ (GeoParquet / CSV).

    python scripts/download_spatial.py              # everything (~15-30 min, flood zones is the slow one)
    python scripts/download_spatial.py --only ptal lsoa imd
    python scripts/download_spatial.py --list

Every layer is clipped to a London bounding box and stored in WGS84 (EPSG:4326).
Existing outputs are skipped; pass --force to re-download.
"""

import argparse
import csv
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
import shapely

OUT = Path("data/raw/spatial")
# Greater London plus a small margin (lon_min, lat_min, lon_max, lat_max).
LONDON_BBOX = (-0.52, 51.28, 0.34, 51.70)
UA = {"User-Agent": "house-london-hackathon/1.0"}

# planning.data.gov.uk national datasets (bulk CSV with WKT geometry).
PLANNING_DATA = [
    "conservation-area",
    "article-4-direction-area",
    "listed-building-outline",
    "green-belt",
    "brownfield-land",
    "tree-preservation-zone",
    "flood-risk-zone",  # 2.8 GB nationally; streamed and filtered, never saved whole
]

# Direct file downloads (London Datastore, gov.uk).
FILES = {
    "opportunity-areas": ("https://data.london.gov.uk/download/epr7z/7a2c2ec3-9b63-45d5-97a3-5b123c037687/Opportunity_Areas.gpkg", "gpkg"),
    "strategic-industrial-land": ("https://data.london.gov.uk/download/2y5xy/b0616b02-d392-4564-b45a-eeb2945e5df9/Strategic_Industrial_Land.gpkg", "gpkg"),
    "town-centres": ("https://data.london.gov.uk/download/e55z7/84b3939e-c301-48e5-85e0-31699b1cb751/Town_Centres_Boundaries.gpkg", "gpkg"),
    "imd-2025": ("https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv", "csv"),
    "mayor-referrals-2011-2024": ("https://data.london.gov.uk/download/2w1xz/47b49dde-d8ac-4229-b36f-900ca34c7490/Referable%20planning%20application%20data%202011-2024.xlsx", "xlsx"),
}

# ArcGIS feature services (paged queries).
ARCGIS = {
    "ptal-2023-grid": "https://services1.arcgis.com/YswvgzOodUvqkoCN/arcgis/rest/services/PTAL_2023_Grid_100m_100m/FeatureServer/33",
    "lsoa-2021": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0",
}

ALL = PLANNING_DATA + list(FILES) + list(ARCGIS)


def planning_data(name: str) -> None:
    """Stream a planning.data.gov.uk CSV, keeping rows whose geometry touches London."""
    out = OUT / f"{name}.parquet"
    url = f"https://files.planning.data.gov.uk/dataset/{name}.csv"
    csv.field_size_limit(sys.maxsize)
    rows, kept, scanned = [], [], 0
    box = shapely.box(*LONDON_BBOX)

    def flush():
        if not rows:
            return
        df = pd.DataFrame(rows).drop(columns=["geojson"], errors="ignore")
        geom_col = df["geometry"].fillna("").astype(str)
        point_col = df["point"].fillna("").astype(str) if "point" in df else ""
        wkt = geom_col.where(geom_col != "", point_col).to_numpy(dtype=object)
        wkt[wkt == ""] = None
        geom = shapely.from_wkt(wkt, on_invalid="ignore")
        mask = shapely.intersects(geom, box)
        if mask.any():
            kept.append(gpd.GeoDataFrame(df.loc[mask].drop(columns=["geometry", "point"], errors="ignore"),
                                         geometry=geom[mask], crs=4326))
        rows.clear()

    # Download to a temp file first (streaming the HTTP body into the csv reader is unreliable
    # for multi-GB files), filter it in chunks, then delete it.
    tmp = OUT / f"_tmp_{name}.csv"
    with requests.get(url, stream=True, timeout=120, headers=UA) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for i, chunk in enumerate(r.iter_content(1 << 20)):
                f.write(chunk)
                if i % 500 == 499:
                    print(f"    {name}: downloaded {(i + 1) / 1024:.1f} GB", flush=True)
    try:
        with open(tmp, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                rows.append(row)
                scanned += 1
                if len(rows) >= 20000:
                    flush()
                    print(f"    {name}: scanned {scanned:,}, kept {sum(map(len, kept)):,}", flush=True)
            flush()
    finally:
        tmp.unlink(missing_ok=True)
    gdf = pd.concat(kept, ignore_index=True) if kept else gpd.GeoDataFrame(geometry=[], crs=4326)
    gdf.to_parquet(out)
    print(f"  {name}: {len(gdf):,} of {scanned:,} features in London -> {out}")


def file_download(name: str) -> None:
    url, ext = FILES[name]
    raw = OUT / f"{name}.{ext}"
    with requests.get(url, stream=True, timeout=120, headers=UA) as r:
        r.raise_for_status()
        with open(raw, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    if ext == "gpkg":
        gdf = gpd.read_file(raw).to_crs(4326)
        gdf.to_parquet(OUT / f"{name}.parquet")
        raw.unlink()
        print(f"  {name}: {len(gdf):,} features -> {OUT / f'{name}.parquet'}")
    else:
        print(f"  {name}: saved {raw} ({raw.stat().st_size / 1e6:.1f} MB)")


def arcgis(name: str) -> None:
    """Page through an ArcGIS FeatureServer layer, clipped to the London bbox."""
    url = ARCGIS[name] + "/query"
    params = {
        "where": "1=1", "outFields": "*", "outSR": 4326, "f": "geojson",
        "geometry": ",".join(map(str, LONDON_BBOX)), "geometryType": "esriGeometryEnvelope",
        "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
        "orderByFields": "FID" if "ptal" in name else "LSOA21CD", "resultRecordCount": 2000,
    }
    parts, offset = [], 0
    while True:
        r = requests.get(url, params={**params, "resultOffset": offset}, timeout=120, headers=UA)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if not feats:
            break
        parts.append(gpd.GeoDataFrame.from_features(feats, crs=4326))
        offset += len(feats)
        print(f"    {name}: {offset:,}", flush=True)
    gdf = pd.concat(parts, ignore_index=True)
    if name == "lsoa-2021":
        gdf = gdf[gdf["LSOA21CD"].str.startswith("E01")]
    gdf.to_parquet(OUT / f"{name}.parquet")
    print(f"  {name}: {len(gdf):,} features -> {OUT / f'{name}.parquet'}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--only", nargs="+", choices=ALL, metavar="LAYER")
    p.add_argument("--force", action="store_true")
    p.add_argument("--list", action="store_true")
    args = p.parse_args()
    if args.list:
        print("\n".join(ALL))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for name in args.only or ALL:
        existing = list(OUT.glob(f"{name}.*"))
        if existing and not args.force:
            print(f"  {name}: exists ({existing[0].name}), skipping")
            continue
        print(f"Downloading {name} ...", flush=True)
        try:
            if name in PLANNING_DATA:
                planning_data(name)
            elif name in FILES:
                file_download(name)
            else:
                arcgis(name)
        except Exception as e:  # keep going so one broken source doesn't block the rest
            print(f"  {name}: FAILED - {e}")
            failed.append(name)
    if failed:
        raise SystemExit(f"Failed: {' '.join(failed)} (re-run with --only {' '.join(failed)})")


if __name__ == "__main__":
    main()
