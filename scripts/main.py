"""Collect configured source pages and write a complete run manifest."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

try:
    from .targets import TARGETS
    from .utils import content_sha256, create_http_session, fetch_url, save_html
except ImportError:
    from targets import TARGETS
    from utils import content_sha256, create_http_session, fetch_url, save_html


DEFAULT_MANIFEST_DIR = Path("data/runs")


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def classify_response(response):
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "").lower()
        return "success" if not content_type or "html" in content_type else "non_html"
    if response.status_code == 403:
        return "forbidden"
    if response.status_code == 404:
        return "not_found"
    if response.status_code in {429, 500, 502, 503, 504}:
        return "retryable_http_error"
    return "http_error"


def snapshot_path(category, site_name, raw_data_dir="data/raw"):
    return Path(raw_data_dir) / category / f"{site_name}.html"


def scrape_site(category, site_name, url, *, session, timeout, retries, raw_data_dir):
    print(f"Requesting {category}/{site_name}: {url}")
    result = fetch_url(url, timeout=timeout, retries=retries, session=session)
    existing = snapshot_path(category, site_name, raw_data_dir)
    record = {
        "category": category,
        "site": site_name,
        "requested_url": url,
        "final_url": "",
        "status": result.error_type or "unknown",
        "status_code": None,
        "elapsed_seconds": result.elapsed_seconds,
        "content_type": "",
        "bytes": 0,
        "sha256": "",
        "snapshot_path": str(existing),
        "snapshot_status": "stale" if existing.exists() else "missing",
        "error": result.error_message,
    }

    response = result.response
    if response is None:
        print(f"[{record['status'].upper()}] {site_name}")
        return record

    status = classify_response(response)
    record.update({
        "final_url": response.url,
        "status": status,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "bytes": len(response.content),
        "sha256": content_sha256(response.content),
    })

    if status == "success":
        output_file = save_html(response.content, category, site_name, raw_data_dir)
        record["snapshot_path"] = str(output_file)
        record["snapshot_status"] = "fresh"
        print(f"[200 OK] Saved to {output_file}")
    else:
        print(f"[{response.status_code}] {site_name}: {status}")

    return record


def selected_targets(only_sites=None):
    requested = set(only_sites or [])
    for category, sites in TARGETS.items():
        for site_name, url in sites.items():
            if not requested or site_name in requested:
                yield category, site_name, url


def write_manifest(manifest, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def run_collection(*, timeout=15, retries=2, raw_data_dir="data/raw", manifest_dir=DEFAULT_MANIFEST_DIR, only_sites=None):
    started_at = utc_now()
    started = perf_counter()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = []

    with create_http_session(retries=retries) as session:
        for category, site_name, url in selected_targets(only_sites):
            results.append(scrape_site(
                category,
                site_name,
                url,
                session=session,
                timeout=timeout,
                retries=retries,
                raw_data_dir=raw_data_dir,
            ))

    counts = Counter(item["status"] for item in results)
    snapshot_counts = Counter(item["snapshot_status"] for item in results)
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "duration_seconds": round(perf_counter() - started, 3),
        "targets_total": len(results),
        "status_counts": dict(sorted(counts.items())),
        "snapshot_counts": dict(sorted(snapshot_counts.items())),
        "fresh_collection_complete": bool(results) and all(item["status"] == "success" for item in results),
        "snapshot_coverage_complete": bool(results) and all(item["snapshot_status"] != "missing" for item in results),
        "results": results,
    }
    manifest_dir = Path(manifest_dir)
    manifest_path = manifest_dir / f"collection-{run_id}.json"
    write_manifest(manifest, manifest_path)
    write_manifest(manifest, manifest_dir / "latest-collection.json")
    print(json.dumps({
        "manifest": str(manifest_path),
        "status_counts": manifest["status_counts"],
        "snapshot_counts": manifest["snapshot_counts"],
    }, indent=2))
    return manifest


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--raw-data-dir", default="data/raw")
    parser.add_argument("--manifest-dir", default=str(DEFAULT_MANIFEST_DIR))
    parser.add_argument("--only", action="append", dest="only_sites", help="Collect one site id; repeatable.")
    parser.add_argument("--fail-on-incomplete", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    manifest = run_collection(
        timeout=args.timeout,
        retries=args.retries,
        raw_data_dir=args.raw_data_dir,
        manifest_dir=args.manifest_dir,
        only_sites=args.only_sites,
    )
    if args.fail_on_incomplete and not manifest["fresh_collection_complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
