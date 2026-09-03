import json
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

def load_processed_data(
    file_path="data/processed/scraped_data.json"
):
    """Load processed scraped data from JSON."""
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data

def flatten_service_offerings(records):
    """Flatten service offerings into rows for Google Sheets."""

    rows = []

    for record in records:
        site = record["site"]

        for service in record["service_offerings"]:
            rows.append({
                "site": site,
                "title": service.get("title", ""),
                "url": service.get("url", ""),
            })

    return rows

def flatten_case_studies(records):
    """Flatten case studies into rows for Google Sheets."""

    rows = []

    for record in records:
        site = record["site"]

        for case_study in record["case_studies"]:
            rows.append({
                "site": site,
                "title": case_study.get("title", ""),
                "url": case_study.get("url", ""),
            })

    return rows


def flatten_testimonials(records):
    """Flatten client testimonials into rows for Google Sheets."""

    rows = []

    for record in records:
        site = record["site"]

        for testimonial in record["client_testimonials"]:
            rows.append({
                "site": site,
                "testimonial": testimonial,
            })

    return rows


def flatten_thought_leadership(records):
    """Flatten thought leadership articles into rows for Google Sheets."""

    rows = []

    for record in records:
        site = record["site"]

        for article in record["thought_leadership"]:
            rows.append({
                "site": site,
                "title": article.get("title", ""),
                "url": article.get("url", ""),
            })

    return rows


def flatten_market_insights(records):
    """Flatten market insights into rows for Google Sheets."""

    rows = []

    for record in records:
        site = record["site"]
        category = record["category"]

        for insight in record["market_insights"]:
            rows.append({
                "site": site,
                "category": category,
                "title": insight.get("title", ""),
                "summary": insight.get("summary", ""),
                "author": insight.get("author", ""),
                "date": insight.get("date", ""),
                "url": insight.get("url", ""),
            })

    return rows

def authenticate_google_sheets(
    credentials_path="credentials/google_service_account.json"
):
    """Authenticate with Google Sheets using a service account."""

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=scopes,
    )

    client = gspread.authorize(credentials)

    return client

def write_rows_to_worksheet(
    spreadsheet,
    worksheet_name,
    rows,
    headers,
):
    """Create a worksheet and upload structured rows."""

    worksheet = spreadsheet.add_worksheet(
        title=worksheet_name,
        rows=max(len(rows) + 1, 2),
        cols=len(headers),
    )

    values = [headers]

    for row in rows:
        values.append([
            row.get(header, "")
            for header in headers
        ])

    worksheet.update(values, "A1")

    print(
        f"Uploaded {len(rows)} rows "
        f"to '{worksheet_name}'."
    )


def export_to_google_sheets(
    service_rows,
    case_study_rows,
    testimonial_rows,
    thought_leadership_rows,
    market_insight_rows,
):
    """Export all structured data to Google Sheets."""

    client = authenticate_google_sheets()

    spreadsheet = client.open(
    "Frenchway Market Research Data"
    )

    default_sheet = spreadsheet.sheet1
    default_sheet.update_title("Service Offerings")

    service_values = [
        ["site", "title", "url"]
    ]

    for row in service_rows:
        service_values.append([
            row["site"],
            row["title"],
            row["url"],
        ])

    default_sheet.update(
        service_values,
        "A1",
    )

    print(
        f"Uploaded {len(service_rows)} rows "
        "to 'Service Offerings'."
    )

    write_rows_to_worksheet(
        spreadsheet,
        "Case Studies",
        case_study_rows,
        ["site", "title", "url"],
    )

    write_rows_to_worksheet(
        spreadsheet,
        "Testimonials",
        testimonial_rows,
        ["site", "testimonial"],
    )

    write_rows_to_worksheet(
        spreadsheet,
        "Thought Leadership",
        thought_leadership_rows,
        ["site", "title", "url"],
    )

    write_rows_to_worksheet(
        spreadsheet,
        "Market Insights",
        market_insight_rows,
        [
            "site",
            "category",
            "title",
            "summary",
            "author",
            "date",
            "url",
        ],
    )

    print("\nGoogle Sheets export completed successfully:")
    print(spreadsheet.url)

if __name__ == "__main__":
    records = load_processed_data()

    service_rows = flatten_service_offerings(records)
    case_study_rows = flatten_case_studies(records)
    testimonial_rows = flatten_testimonials(records)
    thought_leadership_rows = flatten_thought_leadership(records)
    market_insight_rows = flatten_market_insights(records)

    print(f"Service Offerings: {len(service_rows)} rows")
    print(f"Case Studies: {len(case_study_rows)} rows")
    print(f"Testimonials: {len(testimonial_rows)} rows")
    print(f"Thought Leadership: {len(thought_leadership_rows)} rows")
    print(f"Market Insights: {len(market_insight_rows)} rows")

    export_to_google_sheets(
        service_rows,
        case_study_rows,
        testimonial_rows,
        thought_leadership_rows,
        market_insight_rows,
    )