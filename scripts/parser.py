from pathlib import Path

from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin


def load_html(file_path):
    """Load a local HTML file and return a BeautifulSoup object."""
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    return soup

def find_html_files(raw_data_dir="data/raw"):
    """Find all HTML files inside the raw data directory."""
    raw_path = Path(raw_data_dir)

    return sorted(raw_path.rglob("*.html"))

def get_file_info(file_path):
    """Extract category and site name from an HTML file path."""
    path = Path(file_path)

    category = path.parent.name
    site = path.stem

    return {
        "category": category,
        "site": site,
        "file_path": str(path),
    }

def parse_html_file(file_path):
    """Parse one HTML file into a structured record."""
    file_info = get_file_info(file_path)
    soup = load_html(file_path)

    record = {
        "site": file_info["site"],
        "category": file_info["category"],
        "source_file": file_info["file_path"],
        "page_title": "",
        "service_offerings": [],
        "case_studies": [],
        "client_testimonials": [],
        "thought_leadership": [],
        "market_insights": [],
    }

    if soup.title:
        record["page_title"] = soup.title.get_text(" ", strip=True)

    # BCD Travel
    if file_info["site"] == "bcd_travel":
        business_data = extract_business_data(soup)

        record["service_offerings"] = business_data["service_offerings"]
        record["case_studies"] = business_data["case_studies"]
        record["client_testimonials"] = business_data["client_testimonials"]
        record["thought_leadership"] = business_data["thought_leadership"]
        record["market_insights"] = business_data["market_insights"]

    # TravelPerk
    elif file_info["site"] == "travelperk":
        travelperk_data = extract_travelperk_data(soup)
        competitor_data = extract_competitor_data(soup)

        record["service_offerings"] = travelperk_data["service_offerings"]
        record["case_studies"] = travelperk_data["case_studies"]
        record["client_testimonials"] = competitor_data["testimonials"]

    # AAV Luxury Travel
    elif file_info["site"] == "aav_luxury_travel":
        services = extract_links_by_patterns(
            soup,
            "https://www.aavluxurytravel.com",
            ["/experiences/"],
            excluded_texts={
                "experiences",
                "discover all",
                "discover more experiences",
            },
        )

        competitor_data = extract_competitor_data(soup)

        record["service_offerings"] = services
        record["client_testimonials"] = competitor_data["testimonials"]

    # FCM Travel
    elif file_info["site"] == "fcm_travel":
        fcm_data = extract_fcm_data(soup)
        competitor_data = extract_competitor_data(soup)

        record["service_offerings"] = fcm_data["service_offerings"]
        record["client_testimonials"] = competitor_data["testimonials"]

    # Navan
    elif file_info["site"] == "navan":
        services = extract_links_by_patterns(
            soup,
            "https://navan.com",
            ["/solutions/"],
        )

        case_studies = extract_links_by_patterns(
            soup,
            "https://navan.com",
            ["/resources/case-study/"],
            excluded_texts={
                "case studies",
            },
        )

        competitor_data = extract_competitor_data(soup)

        record["service_offerings"] = services
        record["case_studies"] = case_studies
        record["client_testimonials"] = competitor_data["testimonials"]

    # French Promise
    elif file_info["site"] == "french_promise":
        services = extract_links_by_patterns(
            soup,
            "https://www.frenchpromise.com",
            ["/experiences/"],
            excluded_texts={
                "experiences",
            },
        )

        competitor_data = extract_competitor_data(soup)

        record["service_offerings"] = services
        record["client_testimonials"] = competitor_data["testimonials"]

    # Other competitor websites
    elif file_info["category"] == "competitors":
        competitor_data = extract_competitor_data(soup)

        record["client_testimonials"] = competitor_data["testimonials"]

    # TTG
    elif file_info["site"] == "ttg":
        articles = extract_ttg_news(soup)
        record["market_insights"] = articles

    # Etourisme
    elif file_info["site"] == "etourisme":
        articles = extract_etourisme_news(soup)
        record["market_insights"] = articles

    # FashionUnited
    elif file_info["site"] == "fashion_united":
        articles = extract_fashion_united_news(soup)
        record["market_insights"] = articles

    # WWD
    elif file_info["site"] == "wwd":
        articles = extract_wwd_news(soup)
        record["market_insights"] = articles

    # Vogue Business
    elif file_info["site"] == "vogue_business":
        articles = extract_vogue_business_news(soup)
        record["market_insights"] = articles

    # Business of Fashion
    elif file_info["site"] == "business_of_fashion":
        articles = extract_business_of_fashion_news(soup)
        record["market_insights"] = articles

    return record

def extract_page_content(soup):
    """Extract general structured content from a parsed HTML page."""

    data = {
        "title": "",
        "headings": [],
        "paragraphs": [],
        "links": [],
    }

    # Extract page title
    if soup.title:
        data["title"] = soup.title.get_text(" ", strip=True)

    # Extract headings
    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(" ", strip=True)

        if text:
            data["headings"].append(text)

    # Extract paragraphs
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)

        if text:
            data["paragraphs"].append(text)

    # Extract links
    for link in soup.find_all("a"):
        text = link.get_text(" ", strip=True)
        href = link.get("href")

        if text and href:
            data["links"].append({
                "text": text,
                "href": href,
            })

    return data

def extract_business_data(soup, base_url="https://www.bcdtravel.com"):
    """Extract business-related information from the page."""

    data = {
        "service_offerings": [],
        "case_studies": [],
        "client_testimonials": [],
        "thought_leadership": [],
        "market_insights": [],
    }

    # Extract service offerings
    seen_services = set()

    for link in soup.find_all("a"):
        text = link.get_text(" ", strip=True)
        href = link.get("href", "")

        if not text or "/travel-management/" not in href:
            continue

        # Remove generic navigation text
        if text.lower() in {"learn more", "read more", "explore", "discover"}:
            continue

        # Avoid duplicate service names
        service_key = text.lower()

        if service_key in seen_services:
            continue

        seen_services.add(service_key)

        data["service_offerings"].append({
            "title": text,
            "url": urljoin(base_url, href),
        })

        # Extract case studies
    seen_case_studies = set()

    for h3 in soup.find_all("h3"):
        title = h3.get_text(" ", strip=True)

        if not title:
            continue

        # The case study link is located in the second parent container
        parent = h3.parent

        if parent is not None:
            parent = parent.parent

        if parent is None:
            continue

        link = parent.find("a", href=True)

        if link is None:
            continue

        href = link.get("href", "")

        # BCD case studies are stored under /resources/
        if "/resources/" not in href:
            continue

        if title.lower() in seen_case_studies:
            continue

        seen_case_studies.add(title.lower())

        data["case_studies"].append({
            "title": title,
            "url": urljoin(base_url, href),
        })

        # Extract client testimonials
    seen_testimonials = set()

    for quote in soup.find_all("blockquote"):
        text = quote.get_text(" ", strip=True)

        if not text:
            continue

        testimonial_key = text.lower()

        if testimonial_key in seen_testimonials:
            continue

        seen_testimonials.add(testimonial_key)

        data["client_testimonials"].append(text)
    
    return data

def extract_competitor_data(soup):
    """Extract general business information from a competitor page."""

    data = {
        "headings": [],
        "paragraphs": [],
        "links": [],
        "testimonials": [],
    }

    # Extract headings
    for heading in soup.find_all(["h1", "h2", "h3"]):
        text = heading.get_text(" ", strip=True)

        if text and text not in data["headings"]:
            data["headings"].append(text)

    # Extract paragraphs
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)

        if text and text not in data["paragraphs"]:
            data["paragraphs"].append(text)

    # Extract links
    seen_links = set()

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = link.get("href", "")

        if not text or not href:
            continue

        key = (text.lower(), href)

        if key in seen_links:
            continue

        seen_links.add(key)

        data["links"].append({
            "text": text,
            "url": href,
        })

    # Extract testimonials when blockquote is used
    for quote in soup.find_all("blockquote"):
        text = quote.get_text(" ", strip=True)

        if text and text not in data["testimonials"]:
            data["testimonials"].append(text)

    return data

def extract_ttg_news(soup):
    """Extract travel industry and luxury travel news from TTG."""

    articles = []
    seen_urls = set()

    article_patterns = [
        "/travel-industry-news/",
        "/luxury-travel-news/",
    ]

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        # Keep only relevant TTG article URLs
        if not any(pattern in href for pattern in article_patterns):
            continue

        # Skip duplicate article URLs
        if href in seen_urls:
            continue

        # Look for structured article title
        title_tag = link.select_one(".field--name-title")

        if title_tag is None:
            continue

        title = title_tag.get_text(" ", strip=True)

        if not title:
            continue

        # Summary may not exist for every article
        summary_tag = link.select_one(".field--name-body")

        summary = ""

        if summary_tag:
            summary = summary_tag.get_text(" ", strip=True)

        seen_urls.add(href)

        articles.append({
            "title": title,
            "summary": summary,
            "url": urljoin("https://www.ttgmedia.com", href),
        })

    return articles

def extract_etourisme_news(soup):
    """Extract tourism news articles from Etourisme."""

    articles = []

    for card in soup.select("a.listing_inner"):
        href = card.get("href", "")

        title_tag = card.find("h2")

        if title_tag is None or not href:
            continue

        title = title_tag.get_text(" ", strip=True)

        # Extract summary
        summary_tag = card.select_one(".listing_inner_excerpt")
        summary = ""

        if summary_tag:
            summary = summary_tag.get_text(" ", strip=True)

        # Extract author and publication information
        info_tag = card.select_one(".listing_inner_info")

        author = ""
        date = ""

        if info_tag:
            author_tag = info_tag.find("span")

            if author_tag:
                author = author_tag.get_text(" ", strip=True)

            info_text = info_tag.get_text(" ", strip=True)

            if " - " in info_text:
                date = info_text.split(" - ", 1)[1].strip()

        # Extract reading time
        duration_tag = card.select_one(".listing_inner_duree span")
        reading_time = ""

        if duration_tag:
            reading_time = duration_tag.get_text(" ", strip=True)

        articles.append({
            "title": title,
            "summary": summary,
            "author": author,
            "date": date,
            "reading_time": reading_time,
            "url": href,
        })

    return articles

def extract_fashion_united_news(soup):
    """Extract fashion news articles from FashionUnited."""

    articles = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        # Only keep FashionUnited news article links
        if not href.startswith("/news/"):
            continue

        if href in seen_urls:
            continue

        title_tag = link.find("h2")

        if title_tag is None:
            continue

        title = title_tag.get_text(" ", strip=True)

        if not title:
            continue

        # Extract article summary
        summary = ""

        for paragraph in link.find_all("p"):
            text = paragraph.get_text(" ", strip=True)

            if text and text.lower() != "loading...":
                summary = text
                break

        seen_urls.add(href)

        articles.append({
            "title": title,
            "summary": summary,
            "url": urljoin("https://fashionunited.com", href),
        })

    return articles

def extract_wwd_news(soup):
    """Extract fashion industry news articles from WWD."""

    articles = []
    seen_urls = set()

    for card in soup.select(".o-card__content"):
        title_link = card.select_one("a.c-title__link")

        if title_link is None:
            continue

        title = title_link.get_text(" ", strip=True)
        href = title_link.get("href", "")

        if not title or not href:
            continue

        # Only keep WWD article URLs
        if "wwd.com/" not in href:
            continue

        if href in seen_urls:
            continue

        summary_tag = card.select_one(".c-dek")
        summary = ""

        if summary_tag:
            summary = summary_tag.get_text(" ", strip=True)

        seen_urls.add(href)

        articles.append({
            "title": title,
            "summary": summary,
            "url": href,
        })

    return articles

def extract_vogue_business_news(soup):
    """Extract fashion industry articles from Vogue Business."""

    articles = []
    seen_urls = set()

    for card in soup.select(".summary-item"):
        title_link = card.select_one("a.summary-item__hed-link")

        if title_link is None:
            continue

        title_tag = title_link.find("h3")
        href = title_link.get("href", "")

        if title_tag is None or not href:
            continue

        title = title_tag.get_text(" ", strip=True)

        if not title:
            continue

        url = urljoin("https://www.vogue.com", href)

        if url in seen_urls:
            continue

        # Category
        category = ""
        category_tag = card.select_one(".rubric__name")

        if category_tag:
            category = category_tag.get_text(" ", strip=True)

        # Author
        author = ""
        author_tag = card.select_one('[data-testid="BylineName"]')

        if author_tag:
            author = author_tag.get_text(" ", strip=True)

            # Remove the "By" prefix
            if author.startswith("By "):
                author = author[3:].strip()

        # Publication date
        date = ""
        date_tag = card.select_one("time.summary-item__publish-date")

        if date_tag:
            date = date_tag.get_text(" ", strip=True)

        seen_urls.add(url)

        articles.append({
            "title": title,
            "category": category,
            "author": author,
            "date": date,
            "url": url,
        })

    return articles

def extract_business_of_fashion_news(soup):
    """Extract fashion industry articles from The Business of Fashion."""

    articles = []
    seen_urls = set()

    article_patterns = [
        "/articles/",
        "/briefings/",
        "/news/",
        "/opinions/",
        "/reviews/",
    ]

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        if not any(pattern in href for pattern in article_patterns):
            continue

        title_tag = link.find("h3")

        if title_tag is None:
            continue

        title = title_tag.get_text(" ", strip=True)

        if not title:
            continue

        url = urljoin(
            "https://www.businessoffashion.com",
            href,
        )

        if url in seen_urls:
            continue

        seen_urls.add(url)

        articles.append({
            "title": title,
            "url": url,
        })

    return articles

def extract_travelperk_data(soup):
    """Extract service offerings and case studies from TravelPerk."""

    data = {
        "service_offerings": [],
        "case_studies": [],
    }

    seen_services = set()
    seen_case_studies = set()

    service_patterns = [
        "/travel-solutions/",
        "/spend-solutions/",
        "/platform/",
        "/expense-management-nam/",
    ]

    excluded_service_patterns = [
        "/persona-",
    ]

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = link.get("href", "")

        if not text or not href:
            continue

        # -------------------------
        # Service offerings
        # -------------------------
        if (
            any(pattern in href for pattern in service_patterns)
            and not any(pattern in href for pattern in excluded_service_patterns)
        ):
            # Avoid generic CTA text
            if text.lower() in {
                "read more",
                "explore",
                "discover",
                "learn more",
                "explore integrations",
                "discover our product",
                "travel overview",
                "events overview",
                "explore travel",
                "explore events",
            }:
                continue

            url = urljoin("https://www.perk.com", href)

            if url not in seen_services:
                seen_services.add(url)

                data["service_offerings"].append({
                    "title": text,
                    "url": url,
                })

        # -------------------------
        # Case studies
        # -------------------------
        if "/case-studies/" in href:
            url = urljoin("https://www.perk.com", href)

            if url not in seen_case_studies:
                seen_case_studies.add(url)

                slug = href.rstrip("/").split("/")[-1]

                title = slug.replace("-", " ").title()

                data["case_studies"].append({
                    "title": title,
                    "url": url,
                })

    return data

def extract_links_by_patterns(
    soup,
    base_url,
    patterns,
    excluded_texts=None,
):
    """Extract unique structured links matching URL patterns."""

    items = []
    seen_urls = set()

    if excluded_texts is None:
        excluded_texts = set()

    excluded_texts = {
        text.lower()
        for text in excluded_texts
    }

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = link.get("href", "")

        if not text or not href:
            continue

        if not any(pattern in href for pattern in patterns):
            continue

        if text.lower() in excluded_texts:
            continue

        url = urljoin(base_url, href)

        if url in seen_urls:
            continue

        seen_urls.add(url)

        items.append({
            "title": text,
            "url": url,
        })

    return items

def extract_fcm_data(soup):
    """Extract service offerings from FCM Travel."""

    services = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")

        if "/en-us/solutions/" not in href:
            continue

        url = urljoin(
            "https://www.fcmtravel.com",
            href,
        )

        if url in seen_urls:
            continue

        # Prefer structured title elements
        title_tag = link.select_one(
            ".title, .menu-link-title"
        )

        if title_tag:
            title = title_tag.get_text(" ", strip=True)

        else:
            # Some links contain a description span.
            # Remove it before extracting the link text.
            link_copy = BeautifulSoup(
                str(link),
                "html.parser",
            )

            description = link_copy.select_one(
                ".description"
            )

            if description:
                description.decompose()

            title = link_copy.get_text(
                " ",
                strip=True,
            )

        if not title:
            continue

        if title.lower() in {
            "discover fcm platform",
            "discover travel services",
        }:
            continue

        seen_urls.add(url)

        services.append({
            "title": title,
            "url": url,
        })

    return {
        "service_offerings": services,
    }

def find_service_candidates(competitor_data):
    """Find links that may represent service offerings."""

    service_keywords = [
        "service",
        "services",
        "solution",
        "solutions",
        "travel management",
        "meetings",
        "events",
        "consulting",
        "technology",
        "platform",
        "vip",
        "corporate travel",
        "business travel",
    ]

    candidates = []

    for link in competitor_data["links"]:
        text = link["text"]
        url = link["url"]

        combined_text = f"{text} {url}".lower()

        if any(keyword in combined_text for keyword in service_keywords):
            candidates.append(link)

    return candidates

def save_processed_data(records, output_path="data/processed/scraped_data.json"):
    """Save structured records as JSON."""
    output_file = Path(output_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, ensure_ascii=False)

    print(f"Saved processed data to: {output_file}")

if __name__ == "__main__":
    html_files = find_html_files()

    records = []

    for file_path in html_files:
        record = parse_html_file(file_path)
        records.append(record)

    save_processed_data(records)

    print(f"Processed {len(records)} HTML files.")