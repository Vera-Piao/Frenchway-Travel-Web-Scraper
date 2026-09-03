#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRAPY_DIR="$PROJECT_ROOT/frenchway_scraper"
OUTPUT_DIR="$PROJECT_ROOT/data/crawled"

mkdir -p "$OUTPUT_DIR"

cd "$SCRAPY_DIR"

echo "Starting Frenchway scheduled crawl..."
echo "Run time: $(date)"

scrapy crawl services \
    -O "$OUTPUT_DIR/bcd_services.json"

scrapy crawl fashion_news \
    -O "$OUTPUT_DIR/fashion_news.json"

echo "Frenchway scheduled crawl completed."