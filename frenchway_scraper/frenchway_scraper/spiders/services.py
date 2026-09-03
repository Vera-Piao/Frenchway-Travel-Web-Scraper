import scrapy


class ServicesSpider(scrapy.Spider):
    name = "services"

    allowed_domains = ["www.bcdtravel.com"]

    start_urls = [
        "https://www.bcdtravel.com/",
    ]

    custom_settings = {
        "DEPTH_LIMIT": 2,
        "CLOSESPIDER_PAGECOUNT": 30,
        "DOWNLOAD_DELAY": 1,
    }

    def parse(self, response):
        """Extract page data and follow relevant internal links."""

        self.logger.info(
            "Crawling: %s",
            response.url,
        )

        title = response.css(
            "title::text"
        ).get()

        heading = response.css(
            "h1::text"
        ).get()

        headings = response.css(
            "h2::text, h3::text"
        ).getall()

        headings = [
            heading.strip()
            for heading in headings
            if heading.strip()
        ]

        yield {
            "url": response.url,
            "title": (
                title.strip()
                if title
                else ""
            ),
            "heading": (
                heading.strip()
                if heading
                else ""
            ),
            "section_headings": headings,
        }

        links = response.css(
            "a::attr(href)"
        ).getall()

        for href in links:
            if self.is_relevant_link(href):
                yield response.follow(
                    href,
                    callback=self.parse,
                )

    def is_relevant_link(self, href):
        """Return True for relevant English service links."""

        if not href:
            return False
        
        href_lower = href.lower()

        excluded_extensions = (
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".zip",
        )

        if href_lower.split("?")[0].endswith(
            excluded_extensions
        ):
            return False

        excluded_patterns = [
            "/pt/",
            "/nl/",
            "/it/",
            "/de/",
            "/fr/",
            "/es/",
            "/sv/",
            "/pl/",
            "/no/",
            "/da/",
            "/fi/",
            "login",
            "privacy",
            "cookie",
            "terms",
        ]

        if any(
            pattern in href_lower
            for pattern in excluded_patterns
        ):
            return False

        keywords = [
            "service",
            "solution",
            "meeting",
            "event",
        ]

        return any(
            keyword in href_lower
            for keyword in keywords
        )