"""Responsible, bounded crawler for every configured Frenchway source."""

import json
from pathlib import Path
from urllib.parse import urlparse

import scrapy


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TARGETS_PATH = PROJECT_ROOT / "config" / "targets.json"


def load_catalog(path=TARGETS_PATH):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


class MarketSitesSpider(scrapy.Spider):
    name = "market_sites"
    custom_settings = {
        "DEPTH_LIMIT": 1,
        "CLOSESPIDER_PAGECOUNT": 150,
        "DOWNLOAD_DELAY": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "HTTPERROR_ALLOW_ALL": True,
    }
    follow_keywords = (
        "service", "solution", "experience", "industry", "insight", "research",
        "report", "article", "news", "case-stud", "customer-stor", "pricing",
    )
    excluded_suffixes = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip")
    max_pages_per_site = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog = load_catalog()
        hostnames = {
            urlparse(url).hostname
            for sites in self.catalog.values()
            for url in sites.values()
            if urlparse(url).hostname
        }
        self.allowed_domains = sorted(
            hostnames
            | {hostname.removeprefix("www.") for hostname in hostnames}
            | {f"www.{hostname}" for hostname in hostnames if not hostname.startswith("www.")}
        )
        self.site_page_counts = {}

    async def start(self):
        for category, sites in self.catalog.items():
            for site, url in sites.items():
                yield scrapy.Request(
                    url,
                    callback=self.parse,
                    errback=self.errback_source,
                    meta={"category": category, "site": site},
                    dont_filter=True,
                )

    def parse(self, response):
        site = response.meta["site"]
        category = response.meta["category"]
        self.site_page_counts[site] = self.site_page_counts.get(site, 0) + 1
        headings = [
            text.strip()
            for text in response.css("h1::text, h2::text, h3::text").getall()
            if text.strip()
        ]
        paragraphs = [
            text.strip()
            for text in response.css("main p::text, article p::text").getall()
            if text.strip()
        ]
        yield {
            "site": site,
            "category": category,
            "url": response.url,
            "status_code": response.status,
            "title": (response.css("title::text").get() or "").strip(),
            "heading": headings[0] if headings else "",
            "section_headings": headings[1:30],
            "summary": " ".join(paragraphs[:2]),
        }

        if response.status != 200 or self.site_page_counts[site] >= self.max_pages_per_site:
            return
        for href in set(response.css("a::attr(href)").getall()):
            if not self.is_relevant_link(href):
                continue
            yield response.follow(
                href,
                callback=self.parse,
                errback=self.errback_source,
                meta={"category": category, "site": site},
            )

    def errback_source(self, failure):
        request = failure.request
        yield {
            "site": request.meta.get("site", ""),
            "category": request.meta.get("category", ""),
            "url": request.url,
            "status_code": None,
            "error": failure.value.__class__.__name__ if failure.value else "request_error",
            "title": "",
            "heading": "",
            "section_headings": [],
            "summary": "",
        }

    def is_relevant_link(self, href):
        if not href:
            return False
        normalized = href.casefold().split("#", 1)[0]
        if normalized.endswith(self.excluded_suffixes):
            return False
        if any(value in normalized for value in ("login", "privacy", "cookie", "terms", "javascript:", "mailto:")):
            return False
        return any(keyword in normalized for keyword in self.follow_keywords)
