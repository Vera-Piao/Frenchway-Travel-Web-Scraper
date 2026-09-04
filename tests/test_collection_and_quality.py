from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from scripts.main import classify_response, snapshot_path
from scripts.validate_outputs import validate


class FakeResponse:
    def __init__(self, status_code, content_type="text/html"):
        self.status_code = status_code
        self.headers = {"content-type": content_type}


def empty_record(site, category):
    return {
        "site": site,
        "category": category,
        "service_offerings": [],
        "case_studies": [],
        "client_testimonials": [],
        "customer_reviews": [],
        "thought_leadership": [],
        "industries_served": [],
        "pricing_signals": [],
        "market_insights": [],
    }


class CollectionAndQualityTests(unittest.TestCase):
    def test_response_classification(self):
        self.assertEqual(classify_response(FakeResponse(200)), "success")
        self.assertEqual(classify_response(FakeResponse(200, "application/pdf")), "non_html")
        self.assertEqual(classify_response(FakeResponse(403)), "forbidden")
        self.assertEqual(classify_response(FakeResponse(503)), "retryable_http_error")

    def test_snapshot_path_is_category_scoped(self):
        self.assertEqual(snapshot_path("competitors", "example", "raw"), Path("raw/competitors/example.html"))

    def test_documented_unavailable_source_is_accounted_not_fabricated(self):
        from scripts.validate_outputs import configured_sites

        configured = configured_sites()
        unavailable_site = sorted(configured)[0]
        available_sites = set(configured) - {unavailable_site}
        records = [empty_record(site, configured[site]) for site in available_sites]
        records[0]["market_insights"] = [
            {"title": f"Insight {index}", "url": f"https://example.com/{index}"}
            for index in range(20)
        ]
        thresholds = {
            "minimum_accounted_target_coverage": 1.0,
            "minimum_accessible_snapshot_coverage": 1.0,
            "minimum_accessible_processed_coverage": 1.0,
            "documented_unavailable_statuses": ["forbidden"],
            "maximum_unavailable_evidence_age_days": 30,
            "maximum_duplicate_rate": 0.05,
            "minimum_total_market_insights": 20,
            "maximum_empty_title_rate": 0.1,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw"
            manifests = root / "runs"
            manifests.mkdir()
            for site in available_sites:
                category = configured[site]
                path = raw / category / f"{site}.html"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("<html></html>", encoding="utf-8")
            observed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            manifest = {
                "finished_at": observed,
                "results": [{
                    "site": unavailable_site,
                    "status": "forbidden",
                    "status_code": 403,
                    "requested_url": "https://example.com",
                }],
            }
            (manifests / "collection-test.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = validate(records, thresholds, raw, manifests)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["metrics"]["raw_snapshot_coverage"], 24 / 25)
        self.assertEqual(report["metrics"]["accounted_target_coverage"], 1.0)
        self.assertIn(unavailable_site, report["metrics"]["documented_unavailable"])


if __name__ == "__main__":
    unittest.main()
