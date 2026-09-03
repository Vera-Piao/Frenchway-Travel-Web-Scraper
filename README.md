# Frenchway Travel Web Scraper

## Project Overview

This project was developed for Hasmo Consulting to support market research for Frenchway Travel.

The project collects and analyzes publicly available web data from competitor websites, travel industry news sources, and fashion industry news sources. The resulting data can be used to identify competitor offerings, market trends, and potential business opportunities for Frenchway Travel.

The workflow combines:

- Requests for HTTP data collection
- BeautifulSoup for HTML parsing and structured data extraction
- Scrapy for multi-page web crawling
- Google Sheets API for structured data export
- OpenAI API for market trend analysis
- Google Slides API for presentation generation

## Data Sources

The project collects data from three main categories.

### Competitors

Competitor websites are used to identify:

- Service offerings
- Case studies
- Client testimonials
- Business travel solutions
- Luxury and specialized travel services

Examples include BCD Travel, TravelPerk, FCM Travel, Navan, and France-based luxury travel providers.

### Travel Industry News

Travel industry sources are used to identify:

- Market trends
- Technology developments
- Tourism strategy
- Business travel developments
- Customer expectations

### Fashion Industry News

Fashion industry sources are used to identify:

- Luxury market trends
- Fashion events
- Retail and experiential trends
- Brand activations
- Consumer behavior relevant to travel

## Project Structure

```text
Project_1_Frenchway/
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── scraped_data.json
│   │   └── analysis_report.json
│   └── crawled/
│       ├── bcd_services.json
│       └── fashion_news.json
│
├── frenchway_scraper/
│   ├── scrapy.cfg
│   └── frenchway_scraper/
│       ├── settings.py
│       └── spiders/
│           ├── services.py
│           └── fashion_news.py
│
├── scripts/
│   ├── main.py
│   ├── targets.py
│   ├── utils.py
│   ├── parser.py
│   ├── export_sheets.py
│   ├── analysis.py
│   ├── slides.py
│   └── run_scrapers.sh
│
├── cron.example
├── requirements.txt
├── README.md
└── .gitignore
```

The local `frenchway/` virtual environment and `credentials/` directory are excluded from version control.

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone git@github.com:Vera-Piao/Frenchway-Travel-Web-Scraper.git
cd Frenchway-Travel-Web-Scraper
```

Create and activate a virtual environment:

```bash
python3 -m venv frenchway
source frenchway/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

### 1. Collect HTML with Requests

Run:

```bash
python scripts/main.py
```

This sends HTTP requests to the configured target websites and stores successful responses in:

```text
data/raw/
```

Some websites may return HTTP 403 responses or use client-side rendering. The scraper records accessible sources without attempting to bypass website protections.

### 2. Parse HTML with BeautifulSoup

Run:

```bash
python scripts/parser.py
```

The parser uses site-specific and generic extraction rules to identify structured information such as:

- Service offerings
- Case studies
- Testimonials
- Market insights

Processed data is stored in:

```text
data/processed/scraped_data.json
```

### 3. Export Data to Google Sheets

Run:

```bash
python scripts/export_sheets.py
```

The processed data is flattened into tables for:

- Service Offerings
- Case Studies
- Testimonials
- Thought Leadership
- Market Insights

Google API credentials are stored locally under `credentials/` and are not committed to the repository.

### 4. Analyze Market Data with AI

Set the OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key"
```

Then run:

```bash
python scripts/analysis.py
```

The analysis pipeline summarizes travel and fashion market insights and generates strategic recommendations.

Results are stored in:

```text
data/processed/analysis_report.json
```

API keys should never be stored directly in source code.

### 5. Generate Google Slides

Run:

```bash
python scripts/slides.py
```

The script generates presentation content including:

- Project overview
- Competitor analysis
- Service offering comparison
- Market insight comparison
- Key market trends
- Strategic recommendations

### 6. Crawl Multiple Pages with Scrapy

Two Scrapy spiders are included.

Run the BCD Travel services spider:

```bash
cd frenchway_scraper
scrapy crawl services -O ../data/crawled/bcd_services.json
```

Run the FashionUnited news spider:

```bash
scrapy crawl fashion_news -O ../data/crawled/fashion_news.json
```

The spiders use Scrapy selectors and `response.follow()` to navigate relevant internal pages and extract structured information.

The project respects `robots.txt` through:

```python
ROBOTSTXT_OBEY = True
```

## Automated Crawling

A reusable shell script runs both Scrapy spiders:

```bash
./scripts/run_scrapers.sh
```

An example cron configuration is provided in:

```text
cron.example
```

For example, the crawler can be scheduled to run every Monday at 9:00 AM:

```cron
0 9 * * 1 cd /path/to/Project_1_Frenchway && ./scripts/run_scrapers.sh >> data/crawled/scrapy.log 2>&1
```

The cron entry is provided as an example and should be configured for the deployment environment before use.

## Outputs

The main project outputs are:

| Output | Description |
|---|---|
| `data/processed/scraped_data.json` | Structured data extracted with BeautifulSoup |
| `data/processed/analysis_report.json` | AI-generated market analysis |
| `data/crawled/bcd_services.json` | Multi-page BCD Travel crawl results |
| `data/crawled/fashion_news.json` | FashionUnited news crawl results |
| Google Sheets | Structured tables for further analysis |
| Google Slides | Market research presentation |

## Limitations

Website structures can change over time, so selectors may require maintenance.

Some websites restrict automated HTTP access or rely heavily on client-side rendering. This project does not attempt to bypass access controls or anti-bot protections.

The extracted data represents publicly accessible information available at the time of collection.