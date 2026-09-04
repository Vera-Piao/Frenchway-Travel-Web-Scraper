"""Validate coverage, schema, freshness signals, and extraction quality."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

try:
    from .targets import TARGETS
except ImportError:
    from targets import TARGETS


DEFAULT_THRESHOLDS = Path("config/quality_thresholds.json")
DEFAULT_DATA = Path("data/processed/scraped_data.json")
DEFAULT_MANIFEST_DIR = Path("data/runs")
LINK_FIELDS = ("service_offerings", "case_studies", "thought_leadership", "industries_served")
LIST_FIELDS = LINK_FIELDS + ("client_testimonials", "customer_reviews", "pricing_signals", "market_insights")


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def configured_sites():
    return {
        site: category
        for category, sites in TARGETS.items()
        for site in sites
    }


def snapshot_sites(raw_dir="data/raw"):
    return {path.stem for path in Path(raw_dir).rglob("*.html")}


def parse_utc(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def latest_collection_evidence(manifest_dir=DEFAULT_MANIFEST_DIR):
    """Return the newest collection result for each site."""
    evidence = {}
    for path in sorted(Path(manifest_dir).glob("collection-*.json")):
        manifest = load_json(path, {})
        observed_at = manifest.get("finished_at") or manifest.get("started_at")
        observed_dt = parse_utc(observed_at)
        for result in manifest.get("results", []):
            site = result.get("site")
            if not site:
                continue
            previous = evidence.get(site)
            previous_dt = parse_utc(previous.get("observed_at")) if previous else None
            if previous is None or (observed_dt and (previous_dt is None or observed_dt >= previous_dt)):
                evidence[site] = {
                    "status": result.get("status"),
                    "status_code": result.get("status_code"),
                    "requested_url": result.get("requested_url", ""),
                    "observed_at": observed_at,
                    "manifest": str(path),
                }
    return evidence


def duplicate_rate(records):
    total = 0
    duplicates = 0
    for record in records:
        for field in LIST_FIELDS:
            seen = set()
            for item in record.get(field, []):
                total += 1
                if isinstance(item, dict):
                    key = (item.get("url", ""), item.get("title", item.get("text", ""))).__repr__()
                else:
                    key = str(item).casefold()
                if key in seen:
                    duplicates += 1
                seen.add(key)
    return 0.0 if total == 0 else duplicates / total


def empty_title_rate(records):
    items = [
        item
        for record in records
        for field in LINK_FIELDS + ("market_insights",)
        for item in record.get(field, [])
        if isinstance(item, dict)
    ]
    if not items:
        return 0.0
    return sum(not item.get("title") for item in items) / len(items)


def validate(records, thresholds, raw_dir="data/raw", manifest_dir=DEFAULT_MANIFEST_DIR, now=None):
    target_map = configured_sites()
    targets = set(target_map)
    snapshots = snapshot_sites(raw_dir)
    processed = {record.get("site", "") for record in records}
    evidence = latest_collection_evidence(manifest_dir)
    current_time = now or datetime.now(timezone.utc)
    allowed_statuses = set(thresholds.get("documented_unavailable_statuses", []))
    maximum_age_days = thresholds.get("maximum_unavailable_evidence_age_days", 30)
    documented_unavailable = {}
    expired_unavailable_evidence = {}
    for site in sorted(targets - snapshots):
        item = evidence.get(site)
        if not item or item.get("status") not in allowed_statuses:
            continue
        observed_at = parse_utc(item.get("observed_at"))
        age_days = None if observed_at is None else (current_time - observed_at).total_seconds() / 86400
        enriched = {**item, "age_days": None if age_days is None else round(age_days, 3)}
        if age_days is not None and 0 <= age_days <= maximum_age_days:
            documented_unavailable[site] = enriched
        else:
            expired_unavailable_evidence[site] = enriched

    accessible_targets = targets - set(documented_unavailable)
    accounted_targets = (snapshots & targets) | set(documented_unavailable)
    accessible_denominator = len(accessible_targets)
    accessible_snapshot_coverage = (
        1.0 if accessible_denominator == 0
        else len((snapshots & targets) & accessible_targets) / accessible_denominator
    )
    accessible_processed_coverage = (
        1.0 if accessible_denominator == 0
        else len((processed & targets) & accessible_targets) / accessible_denominator
    )
    missing_schema = []
    for record in records:
        for field in LIST_FIELDS:
            if not isinstance(record.get(field), list):
                missing_schema.append(f"{record.get('site', '<unknown>')}:{field}")

    insights = sum(len(record.get("market_insights", [])) for record in records)
    duplicate_value = duplicate_rate(records)
    empty_title_value = empty_title_rate(records)
    metrics = {
        "configured_targets": len(targets),
        "snapshot_count": len(snapshots & targets),
        "raw_snapshot_coverage": len(snapshots & targets) / len(targets),
        "processed_count": len(processed & targets),
        "raw_processed_coverage": len(processed & targets) / len(targets),
        "accounted_target_count": len(accounted_targets),
        "accounted_target_coverage": len(accounted_targets) / len(targets),
        "accessible_target_count": accessible_denominator,
        "accessible_snapshot_coverage": accessible_snapshot_coverage,
        "accessible_processed_coverage": accessible_processed_coverage,
        "missing_snapshots": sorted(targets - snapshots),
        "missing_processed_records": sorted(targets - processed),
        "documented_unavailable": documented_unavailable,
        "expired_unavailable_evidence": expired_unavailable_evidence,
        "unaccounted_targets": sorted(targets - accounted_targets),
        "unexpected_snapshots": sorted(snapshots - targets),
        "duplicate_rate": round(duplicate_value, 6),
        "empty_title_rate": round(empty_title_value, 6),
        "total_market_insights": insights,
        "schema_errors": missing_schema,
    }
    checks = {
        "accounted_target_coverage": metrics["accounted_target_coverage"] >= thresholds["minimum_accounted_target_coverage"],
        "accessible_snapshot_coverage": metrics["accessible_snapshot_coverage"] >= thresholds["minimum_accessible_snapshot_coverage"],
        "accessible_processed_coverage": metrics["accessible_processed_coverage"] >= thresholds["minimum_accessible_processed_coverage"],
        "duplicate_rate": duplicate_value <= thresholds["maximum_duplicate_rate"],
        "market_insight_volume": insights >= thresholds["minimum_total_market_insights"],
        "empty_title_rate": empty_title_value <= thresholds["maximum_empty_title_rate"],
        "schema": not missing_schema,
    }
    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "metrics": metrics,
    }


def write_report(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS))
    parser.add_argument("--manifest-dir", default=str(DEFAULT_MANIFEST_DIR))
    parser.add_argument("--write-report")
    parser.add_argument("--warn-only", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    records = load_json(args.data, [])
    thresholds = load_json(args.thresholds, {})
    report = validate(records, thresholds, args.raw_dir, args.manifest_dir)
    if args.write_report:
        write_report(report, args.write_report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] != "pass" and not args.warn_only:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
