from datetime import datetime
import unittest

from scripts.analytics import linear_forecast, sentiment_for_text


class AnalyticsTests(unittest.TestCase):
    def test_sentiment_is_explainable(self):
        result = sentiment_for_text("Personalized luxury service builds trust but disruption adds risk")
        self.assertEqual(result["evidence_terms"], 5)
        self.assertGreater(result["score"], 0)

    def test_forecast_is_withheld_for_sparse_data(self):
        result = linear_forecast([
            {"kind": "market_insight", "date": "2026-01-02"}
        ])
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["forecast"], [])

    def test_forecast_uses_dated_monthly_series(self):
        records = []
        for month in range(1, 7):
            for day in range(1, 5):
                records.append({
                    "kind": "market_insight",
                    "date": f"2026-{month:02d}-{day:02d}",
                })
        result = linear_forecast(records)
        self.assertEqual(result["status"], "modeled")
        self.assertEqual(len(result["forecast"]), 3)
        self.assertEqual(result["dated_records"], 24)


if __name__ == "__main__":
    unittest.main()
