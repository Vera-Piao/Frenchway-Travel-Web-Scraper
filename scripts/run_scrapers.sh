#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRAPY_DIR="$PROJECT_ROOT/frenchway_scraper"
OUTPUT_DIR="$PROJECT_ROOT/data/crawled"
RUN_DIR="$PROJECT_ROOT/data/runs"
SCRAPY_BIN="${SCRAPY_BIN:-$PROJECT_ROOT/frenchway/bin/scrapy}"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_ROOT/frenchway/bin/python}"

mkdir -p "$OUTPUT_DIR" "$RUN_DIR"

if [ ! -x "$SCRAPY_BIN" ]; then
    SCRAPY_BIN="$(command -v scrapy)"
fi

if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(command -v python3)"
fi

cd "$SCRAPY_DIR"

echo "Starting Frenchway scheduled crawl..."
echo "Run time: $(date)"

"$SCRAPY_BIN" crawl services \
    -O "$OUTPUT_DIR/bcd_services.json"

"$SCRAPY_BIN" crawl fashion_news \
    -O "$OUTPUT_DIR/fashion_news.json"

"$SCRAPY_BIN" crawl market_sites \
    -O "$OUTPUT_DIR/market_sites.json"

"$PYTHON_BIN" "$PROJECT_ROOT/scripts/validate_outputs.py" \
    --write-report "$RUN_DIR/latest-quality.json"

echo "Frenchway scheduled crawl completed."
