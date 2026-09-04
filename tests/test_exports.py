import unittest

from scripts.export_sheets import build_payload, worksheet_values
from scripts.slides import build_slide_plan


RECORD = {
    "site": "example",
    "category": "competitors",
    "source_url": "https://example.com",
    "page_title": "Example",
    "service_offerings": [{"title": "Concierge", "url": "https://example.com/service"}],
    "case_studies": [],
    "client_testimonials": ["Excellent specialist service."],
    "customer_reviews": ["Excellent specialist service."],
    "thought_leadership": [],
    "industries_served": [{"title": "Fashion", "url": "https://example.com/fashion"}],
    "pricing_signals": [{"text": "Request pricing", "kind": "quote_or_pricing_cta", "url": ""}],
    "market_insights": [{"title": "Luxury travel outlook", "summary": "", "url": "https://example.com/news"}],
}


class ExportTests(unittest.TestCase):
    def test_sheet_payload_contains_all_required_tables(self):
        payload = build_payload([RECORD])
        expected = {
            "Source Inventory", "Service Offerings", "Case Studies", "Testimonials",
            "Customer Reviews", "Thought Leadership", "Industries Served",
            "Pricing Signals", "Market Insights",
        }
        self.assertEqual(set(payload["worksheets"]), expected)
        self.assertEqual(worksheet_values([]), [["no_records"]])

    def test_slide_plan_uses_analysis_report(self):
        analysis = {
            "schema_version": 2,
            "travel_analysis": "Travel evidence text",
            "fashion_analysis": "Fashion evidence text",
            "strategic_recommendations": [{
                "title": "Use evidence",
                "rationale": "Because it is traceable.",
                "suggested_action": "Review sources.",
            }],
        }
        plan = build_slide_plan([RECORD], analysis)
        bodies = {slide["id"]: slide.get("body", "") for slide in plan["slides"]}
        self.assertIn("Travel evidence text", bodies["market_trends"])
        self.assertIn("Use evidence", bodies["strategic_recommendations"])


if __name__ == "__main__":
    unittest.main()
