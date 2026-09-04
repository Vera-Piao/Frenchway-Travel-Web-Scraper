# Frenchway Travel Market Research Pipeline

This repository collects and analyzes public competitor, travel-industry, and fashion-industry web content for Frenchway Travel. It produces auditable local datasets, deterministic analysis, Google-ready payloads, crawl outputs, run manifests, and quality reports.

The implementation is deliberately evidence-bounded: it records access failures and stale snapshots, does not bypass anti-bot controls, withholds forecasts when the dated series is too sparse, and requires explicit flags before changing Google Sheets or Google Slides.

## What is covered

The canonical catalog in `config/targets.json` contains 25 sources:

- 17 competitors
- 4 travel-news sources
- 4 fashion-news sources

For competitor pages, the parser extracts service offerings, case studies, testimonials, customer reviews, thought leadership, industries served, and pricing signals. News pages produce structured market-insight records. The analysis stage adds theme counts, transparent keyword polarity, extraction coverage, and a guarded monthly publishing-volume trend model.

## Project layout

```text
Project_1_Frenchway/
├── config/
│   ├── targets.json
│   └── quality_thresholds.json
├── data/
│   ├── raw/                  # HTML snapshots
│   ├── crawled/              # Scrapy JSON outputs
│   ├── processed/            # Parsed data, analysis, export payloads
│   └── runs/                 # Collection, pipeline, and QA manifests
├── frenchway_scraper/
│   └── frenchway_scraper/spiders/
│       ├── services.py
│       ├── fashion_news.py
│       └── market_sites.py   # Bounded multi-domain crawler
├── scripts/
│   ├── main.py               # Retry-aware snapshot collector
│   ├── parser.py
│   ├── analytics.py
│   ├── analysis.py
│   ├── export_sheets.py
│   ├── slides.py
│   ├── validate_outputs.py
│   ├── run_pipeline.py
│   └── run_scrapers.sh
├── tests/
├── cron.example
└── requirements.txt
```

The local `frenchway/` virtual environment and `credentials/` directory are excluded from version control.

## Installation

```bash
python3 -m venv frenchway
source frenchway/bin/activate
python -m pip install -r requirements.txt
```

## Recommended run

Run the complete workflow from the repository root:

```bash
python scripts/run_pipeline.py
```

The orchestrator stops on the first failed stage and writes stage logs plus `pipeline.json` under a timestamped `data/runs/` directory. Useful options are:

```bash
python scripts/run_pipeline.py --skip-collect --skip-crawl
python scripts/run_pipeline.py --ai
python scripts/run_pipeline.py --publish-google
python scripts/run_pipeline.py --warn-only
```

`--ai` requires `OPENAI_API_KEY` and uses `OPENAI_MODEL` or `gpt-5-mini`. Without it, the analysis is deterministic and offline. `--publish-google` is the only pipeline option that writes to the configured Google spreadsheet and presentation.

## Run stages separately

### 1. Collect snapshots

```bash
python scripts/main.py
python scripts/main.py --only egencia --only travel_weekly
python scripts/main.py --fail-on-incomplete
```

Successful HTML is atomically saved under `data/raw/`. Every attempt writes a manifest containing HTTP status, final URL, timing, byte count, hash, and snapshot freshness. Failed requests never overwrite a valid older snapshot.

### 2. Parse and analyze

```bash
python scripts/parser.py
python scripts/analysis.py
python scripts/analysis.py --ai
```

Outputs:

- `data/processed/scraped_data.json`
- `data/processed/analysis_report.json`

Sentiment is a transparent keyword indicator, not a customer-satisfaction score. The predictive result is publishing/capture volume, not demand or revenue. The model is withheld unless it has at least 20 dated records spanning six months.

### 3. Build or publish Google outputs

The default commands only generate local, reviewable payloads:

```bash
python scripts/export_sheets.py
python scripts/slides.py
```

Read-only remote checks:

```bash
python scripts/export_sheets.py --check
python scripts/slides.py --check
```

Explicit remote publication:

```bash
python scripts/export_sheets.py --apply
python scripts/slides.py --apply
```

The Sheets publisher updates named worksheets idempotently instead of creating duplicates. Credentials remain under `credentials/` and must not be committed.

### 4. Run Scrapy

```bash
./scripts/run_scrapers.sh
```

The script runs the two focused spiders and the bounded `market_sites` spider, then executes the quality gate. The multi-domain spider obeys `robots.txt`, uses auto-throttling, limits crawl depth to one, and caps pages per site.

### 5. Validate outputs

```bash
python scripts/validate_outputs.py --write-report data/runs/latest-quality.json
```

The quality report checks:

- all 25 configured targets are accounted for;
- every currently accessible target has a snapshot and processed record;
- inaccessible sources have recent, explicit `403`/`404` collection evidence;
- structured list fields follow the schema;
- duplicate and empty-title rates remain below thresholds;
- enough market-insight records exist for useful analysis.

Raw coverage remains visible in the report. A documented unavailable source is never converted into a fabricated record.

## Automated tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts frenchway_scraper/frenchway_scraper tests
python -m pip check
```

Tests cover parsing, quantitative-analysis gates, source catalog coverage, crawler link filtering, Google payload construction, Slides data binding, HTTP status classification, and unavailable-source accountability.

## Scheduling

`cron.example` is an installable template for a Monday 09:00 run. Replace `PROJECT_ROOT` with the deployment path, review the command, and only then install it with `crontab cron.example`. This repository does not silently change the host's scheduler.

## Known external constraints

At the latest checked run, Amex GBT, Egencia, and Travel Weekly returned HTTP 403 to the responsible Requests client, including tested official subpages. The quality manifest records this evidence and expires it after 30 days so the sources are retried rather than permanently excluded. Google remote state and scheduler activation depend on the deployment account and host; use the explicit check/apply and cron steps above.
