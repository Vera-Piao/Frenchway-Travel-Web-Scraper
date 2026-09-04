"""Build and optionally publish idempotent Google Sheets payloads."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials


DATA_PATH = Path("data/processed/scraped_data.json")
CONFIG_PATH = Path("credentials/google_config.json")
CREDENTIALS_PATH = Path("credentials/google_service_account.json")
PAYLOAD_PATH = Path("data/processed/sheets_payload.json")


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def flatten_link_field(records, field):
    rows = []
    for record in records:
        for item in record.get(field, []):
            rows.append({
                "site": record.get("site", ""),
                "category": record.get("category", ""),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
            })
    return rows


def flatten_text_field(records, field, output_name):
    rows = []
    for record in records:
        for text in record.get(field, []):
            rows.append({
                "site": record.get("site", ""),
                "category": record.get("category", ""),
                output_name: text,
            })
    return rows


def flatten_pricing(records):
    rows = []
    for record in records:
        for item in record.get("pricing_signals", []):
            rows.append({
                "site": record.get("site", ""),
                "text": item.get("text", ""),
                "kind": item.get("kind", ""),
                "url": item.get("url", ""),
            })
    return rows


def flatten_market_insights(records):
    rows = []
    for record in records:
        for insight in record.get("market_insights", []):
            rows.append({
                "site": record.get("site", ""),
                "category": record.get("category", ""),
                "title": insight.get("title", ""),
                "summary": insight.get("summary", ""),
                "author": insight.get("author", ""),
                "date": insight.get("date", ""),
                "url": insight.get("url", ""),
            })
    return rows


def build_payload(records):
    inventory = []
    for record in records:
        inventory.append({
            "site": record.get("site", ""),
            "category": record.get("category", ""),
            "source_url": record.get("source_url", ""),
            "page_title": record.get("page_title", ""),
            "services": len(record.get("service_offerings", [])),
            "case_studies": len(record.get("case_studies", [])),
            "testimonials": len(record.get("client_testimonials", [])),
            "thought_leadership": len(record.get("thought_leadership", [])),
            "industries": len(record.get("industries_served", [])),
            "pricing_signals": len(record.get("pricing_signals", [])),
            "market_insights": len(record.get("market_insights", [])),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "worksheets": {
            "Source Inventory": inventory,
            "Service Offerings": flatten_link_field(records, "service_offerings"),
            "Case Studies": flatten_link_field(records, "case_studies"),
            "Testimonials": flatten_text_field(records, "client_testimonials", "testimonial"),
            "Customer Reviews": flatten_text_field(records, "customer_reviews", "review"),
            "Thought Leadership": flatten_link_field(records, "thought_leadership"),
            "Industries Served": flatten_link_field(records, "industries_served"),
            "Pricing Signals": flatten_pricing(records),
            "Market Insights": flatten_market_insights(records),
        },
    }


def authenticate(credentials_path=CREDENTIALS_PATH):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    return gspread.authorize(credentials)


def spreadsheet_name(config):
    return config.get("spreadsheet_name", "Frenchway Market Research Data")


def get_or_create_worksheet(spreadsheet, name, rows, columns):
    try:
        worksheet = spreadsheet.worksheet(name)
        worksheet.resize(rows=max(rows, 2), cols=max(columns, 1))
        worksheet.clear()
        return worksheet
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=max(rows, 2), cols=max(columns, 1))


def worksheet_values(rows):
    headers = []
    for row in rows:
        for key in row:
            if key not in headers:
                headers.append(key)
    if not headers:
        return [["no_records"]]
    return [headers] + [[row.get(header, "") for header in headers] for row in rows]


def publish_payload(payload, config, credentials_path=CREDENTIALS_PATH):
    client = authenticate(credentials_path)
    spreadsheet = client.open(spreadsheet_name(config))
    for name, rows in payload["worksheets"].items():
        values = worksheet_values(rows)
        worksheet = get_or_create_worksheet(spreadsheet, name, len(values), len(values[0]))
        worksheet.update(values=values, range_name="A1")
        worksheet.freeze(rows=1)
        print(f"Published {len(rows)} rows to {name}")
    return spreadsheet.url


def check_remote(config, credentials_path=CREDENTIALS_PATH):
    client = authenticate(credentials_path)
    spreadsheet = client.open(spreadsheet_name(config))
    return {
        "title": spreadsheet.title,
        "url": spreadsheet.url,
        "worksheets": [worksheet.title for worksheet in spreadsheet.worksheets()],
    }


def write_payload(payload, output_path=PAYLOAD_PATH):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    return path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DATA_PATH))
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--credentials", default=str(CREDENTIALS_PATH))
    parser.add_argument("--output", default=str(PAYLOAD_PATH))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Publish the payload to Google Sheets.")
    mode.add_argument("--check", action="store_true", help="Read remote spreadsheet metadata without writing.")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_json(args.config) if Path(args.config).exists() else {}
    if args.check:
        print(json.dumps(check_remote(config, args.credentials), indent=2))
        return
    records = load_json(args.input)
    payload = build_payload(records)
    output = write_payload(payload, args.output)
    summary = {name: len(rows) for name, rows in payload["worksheets"].items()}
    print(json.dumps({"payload": str(output), "rows": summary}, indent=2))
    if args.apply:
        print(json.dumps({"spreadsheet_url": publish_payload(payload, config, args.credentials)}, indent=2))


if __name__ == "__main__":
    main()
