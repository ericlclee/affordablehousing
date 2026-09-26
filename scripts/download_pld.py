"""Download Planning London Datahub (PLD) applications to gzipped JSON Lines.

Pages through the GLA's public Elasticsearch guest API with search_after on _id,
so it is resumable: re-running continues from the last saved record.

    python scripts/download_pld.py                      # valid_date 2022-01-01..2025-12-31
    python scripts/download_pld.py --start 2020-01-01   # wider window (new output file)

Output: data/raw/pld/pld_applications_<start>_<end>.jsonl.gz (one application per line)
"""

import argparse
import gzip
import json
import time
from pathlib import Path

import requests

API = "https://planningdata.london.gov.uk/api-guest/applications/_search"
# Public guest token from the GLA's API connection guide:
# https://www.london.gov.uk/sites/default/files/planninglondondatahub_api_connection_technical_documentation_v1.pdf
HEADERS = {"Content-Type": "application/json", "X-API-AllowRequest": "be2rmRnt&"}
PAGE_SIZE = 5000
# Raw projected polygon duplicates wgs84_polygon and is large, so skip it.
EXCLUDE = ["polygon"]


def to_pld_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def last_id(path: Path) -> str | None:
    """Return the _id of the last complete line, truncating any partial final line."""
    if not path.exists():
        return None
    last = None
    good = []
    with gzip.open(path, "rt") as f:
        try:
            for line in f:
                rec = json.loads(line)
                last = rec["_id"]
                good.append(line)
        except (EOFError, json.JSONDecodeError, gzip.BadGzipFile):
            # Interrupted mid-write: rewrite only the complete lines.
            with gzip.open(path, "wt") as out:
                out.writelines(good)
    return last


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2022-01-01")
    p.add_argument("--end", default="2025-12-31")
    p.add_argument("--out-dir", default="data/raw/pld")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"pld_applications_{args.start}_{args.end}.jsonl.gz"

    query = {"range": {"valid_date": {"gte": to_pld_date(args.start), "lte": to_pld_date(args.end)}}}
    total = requests.post(API.replace("_search", "_count"), headers=HEADERS,
                          json={"query": query}, timeout=60).json()["count"]

    after = last_id(out)
    done = 0
    if after:
        with gzip.open(out, "rt") as f:
            done = sum(1 for _ in f)
        print(f"Resuming after {after} ({done:,} already saved)")
    print(f"{total:,} applications with valid_date {args.start}..{args.end} -> {out}")

    with gzip.open(out, "at") as f:
        while True:
            body = {"size": PAGE_SIZE, "sort": [{"_id": "asc"}], "query": query,
                    "_source": {"excludes": EXCLUDE}}
            if after:
                body["search_after"] = [after]
            for attempt in range(5):
                try:
                    r = requests.post(API, headers=HEADERS, json=body, timeout=180)
                    r.raise_for_status()
                    hits = r.json()["hits"]["hits"]
                    break
                except (requests.RequestException, KeyError, ValueError) as e:
                    wait = 5 * 2**attempt
                    print(f"  retry {attempt + 1} in {wait}s: {e}")
                    time.sleep(wait)
            else:
                raise SystemExit("PLD API kept failing; re-run to resume.")
            if not hits:
                break
            for h in hits:
                rec = h["_source"]
                rec["_id"] = h["_id"]
                f.write(json.dumps(rec, separators=(",", ":")) + "\n")
            f.flush()
            after = hits[-1]["_id"]
            done += len(hits)
            print(f"  {done:,}/{total:,}  last={after}", flush=True)

    print(f"Done: {done:,} records in {out}")


if __name__ == "__main__":
    main()
