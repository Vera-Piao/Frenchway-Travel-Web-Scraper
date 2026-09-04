import json
from pathlib import Path
import tempfile
import unittest

from bs4 import BeautifulSoup

from scripts.parser import (
    extract_customer_reviews,
    extract_generic_news,
    extract_industries_served,
    extract_pricing_signals,
    extract_thought_leadership,
    parse_html_file,
)


HTML = """
<html><head><title>Direct Travel Test</title></head><body>
  <a href="/services/vip">VIP Concierge Service</a>
  <a href="/case-studies/client-a">How Client A Improved Travel</a>
  <a href="/industries/fashion">Fashion and Luxury</a>
  <a href="/insights/market-report">2026 Business Travel Market Report</a>
  <a href="/pricing">Request a quote</a>
  <p>Plans start at $250 per traveler.</p>
  <blockquote>The team provided exceptional support and a truly personalized itinerary.</blockquote>
</body></html>
"""


class ParserTests(unittest.TestCase):
    def test_generic_competitor_extractors(self):
        soup = BeautifulSoup(HTML, "html.parser")
        base = "https://example.com"
        self.assertTrue(extract_customer_reviews(soup))
        self.assertTrue(extract_pricing_signals(soup, base))
        self.assertTrue(extract_industries_served(soup, base))
        self.assertTrue(extract_thought_leadership(soup, base))

    def test_full_record_schema_and_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "competitors" / "direct_travel.html"
            path.parent.mkdir()
            path.write_text(HTML, encoding="utf-8")
            record = parse_html_file(path)
        self.assertEqual(record["site"], "direct_travel")
        self.assertEqual(record["page_title"], "Direct Travel Test")
        self.assertTrue(record["service_offerings"])
        self.assertTrue(record["case_studies"])
        self.assertTrue(record["pricing_signals"])
        self.assertTrue(record["customer_reviews"])
        self.assertTrue(record["industries_served"])
        self.assertTrue(record["thought_leadership"])
        json.dumps(record)

    def test_generic_news_deduplicates_urls(self):
        soup = BeautifulSoup(
            '<a href="/news/story"><h2>A sufficiently detailed travel headline</h2></a>'
            '<a href="/news/story#top"><h2>A sufficiently detailed travel headline</h2></a>',
            "html.parser",
        )
        items = extract_generic_news(soup, "https://news.example")
        self.assertEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
