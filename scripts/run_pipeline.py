"""Run the collection, parsing, analysis, payload, crawl, and QA stages."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = PROJECT_ROOT / "data" / "runs"


def run_command(name, command, log_dir):
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True)
    log_path = log_dir / f"{name}.log"
    log_path.write_text(result.stdout + ("\nSTDERR\n" + result.stderr if result.stderr else ""), encoding="utf-8")
    return {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "log": str(log_path.relative_to(PROJECT_ROOT)),
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--skip-crawl", action="store_true")
    parser.add_argument("--ai", action="store_true")
    parser.add_argument("--publish-google", action="store_true")
    parser.add_argument("--warn-only", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_dir = RUN_DIR / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    python = sys.executable
    stages = []

    if not args.skip_collect:
        stages.append(("collect", [python, "scripts/main.py"]))
    stages.append(("parse", [python, "scripts/parser.py"]))
    analysis_command = [python, "scripts/analysis.py"] + (["--ai"] if args.ai else [])
    stages.append(("analysis", analysis_command))
    stages.append(("sheets_payload", [python, "scripts/export_sheets.py"] + (["--apply"] if args.publish_google else [])))
    stages.append(("slides_payload", [python, "scripts/slides.py"] + (["--apply"] if args.publish_google else [])))
    if not args.skip_crawl:
        stages.append(("scrapy", [str(PROJECT_ROOT / "scripts" / "run_scrapers.sh")]))
    stages.append(("quality", [python, "scripts/validate_outputs.py", "--write-report", str(log_dir / "quality.json")] + (["--warn-only"] if args.warn_only else [])))

    results = []
    for name, command in stages:
        result = run_command(name, command, log_dir)
        results.append(result)
        if result["returncode"] != 0 and not args.warn_only:
            break

    report = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "pass" if results and all(item["returncode"] == 0 for item in results) else "fail",
        "stages": results,
    }
    report_path = log_dir / "pipeline.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest = RUN_DIR / "latest-pipeline.json"
    latest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "pass" and not args.warn_only:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
