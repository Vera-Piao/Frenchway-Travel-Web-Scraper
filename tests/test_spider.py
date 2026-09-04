import unittest

from frenchway_scraper.frenchway_scraper.spiders.market_sites import MarketSitesSpider


class SpiderTests(unittest.TestCase):
    def test_catalog_covers_all_configured_sources(self):
        spider = MarketSitesSpider()
        self.assertEqual(sum(len(sites) for sites in spider.catalog.values()), 25)
        self.assertIn("www.egencia.com", spider.allowed_domains)
        self.assertIn("egencia.com", spider.allowed_domains)

    def test_relevant_link_filter(self):
        spider = MarketSitesSpider()
        self.assertTrue(spider.is_relevant_link("/insights/market-report"))
        self.assertFalse(spider.is_relevant_link("/privacy"))
        self.assertFalse(spider.is_relevant_link("/brochure.pdf"))


if __name__ == "__main__":
    unittest.main()
