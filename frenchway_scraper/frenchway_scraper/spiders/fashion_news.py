import scrapy


class FashionNewsSpider(scrapy.Spider):
    name = "fashion_news"

    allowed_domains = ["fashionunited.com"]

    start_urls = [
        "https://fashionunited.com/news",
    ]

    custom_settings = {
        "DEPTH_LIMIT": 3,
        "CLOSESPIDER_PAGECOUNT": 30,
        "DOWNLOAD_DELAY": 1,
    }

    def parse(self, response):
        """Parse a news listing page."""

        self.logger.info(
            "Parsing listing page: %s",
            response.url,
        )

        article_links = response.css(
            'a[href*="/news/"]::attr(href)'
        ).getall()

        for href in set(article_links):
            if href == response.url:
                continue

            yield response.follow(
                href,
                callback=self.parse_article,
            )

        # Follow pagination when a next-page link exists.
        next_page = response.css(
            'a[rel="next"]::attr(href)'
        ).get()

        if not next_page:
            next_page = response.css(
                'a[aria-label*="Next"]::attr(href)'
            ).get()

        if next_page:
            self.logger.info(
                "Following next page: %s",
                next_page,
            )

            yield response.follow(
                next_page,
                callback=self.parse,
            )

    def parse_article(self, response):
        """Extract structured data from a news article."""

        title = response.css(
            "h1::text"
        ).get()

        paragraphs = response.css(
            "article p::text"
        ).getall()

        if not paragraphs:
            paragraphs = response.css(
                "main p::text"
            ).getall()

        paragraphs = [
            text.strip()
            for text in paragraphs
            if text.strip()
        ]

        yield {
            "url": response.url,
            "title": (
                title.strip()
                if title
                else ""
            ),
            "summary": " ".join(
                paragraphs[:2]
            ),
        }