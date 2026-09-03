import json
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


CREDENTIALS_PATH = "credentials/google_service_account.json"
CONFIG_PATH = "credentials/google_config.json"
ANALYSIS_PATH = "data/processed/analysis_report.json"

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive",
]

DATA_PATH = "data/processed/scraped_data.json"

def load_analysis_report():
    """Load AI-generated market analysis."""

    path = Path(ANALYSIS_PATH)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)

def create_analysis_slides(
    service,
    presentation_id,
):
    """Create concise market analysis slides."""

    trends_body = (
        "Travel Market\n"
        "• AI-assisted trip planning is becoming mainstream\n"
        "• Personalized, experiential travel is growing\n"
        "• Crisis communication and resilience matter\n"
        "• Trust and professional expertise remain critical\n\n"

        "Fashion & Luxury Market\n"
        "• Consumers increasingly seek memorable experiences\n"
        "• Fashion, culture, wellness, and travel increasingly overlap\n"
        "• Authenticity and local identity drive differentiation\n"
        "• Luxury consumers are more selective and value-conscious"
    )

    recommendations_body = (
        "1. Curate fashion & luxury travel experiences\n"
        "Combine shopping, events, culture, and local discovery.\n\n"

        "2. Use AI for personalized itinerary planning\n"
        "Pair automation with human expertise and quality control.\n\n"

        "3. Strengthen experiential France offerings\n"
        "Prioritize distinctive, hard-to-replicate experiences.\n\n"

        "4. Lead with trust and expert service\n"
        "Emphasize credibility, responsiveness, and international support.\n\n"

        "5. Strengthen digital customer acquisition\n"
        "Use distinctive, experience-led content to reach global travelers."
    )

    create_slide(
        service,
        presentation_id,
        "market_trends",
        "Key Market Trends",
        trends_body,
    )

    create_slide(
        service,
        presentation_id,
        "strategic_recommendations",
        "Strategic Recommendations",
        recommendations_body,
    )
    
def authenticate_google_slides():
    """Authenticate with Google Slides using a service account."""

    credentials = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
    )

    slides_service = build(
        "slides",
        "v1",
        credentials=credentials,
    )

    return slides_service


def load_presentation_id():
    """Load the Google Slides presentation ID."""

    path = Path(CONFIG_PATH)

    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    return config["presentation_id"]

def load_processed_data():
    """Load processed market research data."""

    path = Path(DATA_PATH)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def calculate_summary(records):
    """Calculate summary statistics for the presentation."""

    competitor_sites = 0
    travel_news_sites = 0
    fashion_news_sites = 0

    service_count = 0
    case_study_count = 0
    testimonial_count = 0
    market_insight_count = 0

    for record in records:
        category = record["category"]

        if category == "competitors":
            competitor_sites += 1
        elif category == "travel_news":
            travel_news_sites += 1
        elif category == "fashion_news":
            fashion_news_sites += 1

        service_count += len(record["service_offerings"])
        case_study_count += len(record["case_studies"])
        testimonial_count += len(
            record["client_testimonials"]
        )
        market_insight_count += len(
            record["market_insights"]
        )

    return {
        "total_sites": len(records),
        "competitor_sites": competitor_sites,
        "travel_news_sites": travel_news_sites,
        "fashion_news_sites": fashion_news_sites,
        "service_count": service_count,
        "case_study_count": case_study_count,
        "testimonial_count": testimonial_count,
        "market_insight_count": market_insight_count,
    }

def calculate_competitor_service_counts(records):
    """Count extracted service offerings for each competitor."""

    counts = []

    for record in records:
        if record["category"] != "competitors":
            continue

        count = len(record["service_offerings"])

        if count > 0:
            counts.append({
                "site": record["site"],
                "count": count,
            })

    counts.sort(
        key=lambda item: item["count"],
        reverse=True,
    )

    return counts

def calculate_market_insight_counts(records):
    """Count extracted market insights by source."""

    counts = []

    for record in records:
        if record["category"] not in {
            "travel_news",
            "fashion_news",
        }:
            continue

        count = len(record["market_insights"])

        if count > 0:
            counts.append({
                "site": record["site"],
                "category": record["category"],
                "count": count,
            })

    counts.sort(
        key=lambda item: item["count"],
        reverse=True,
    )

    return counts

def format_site_name(site):
    """Convert internal site identifiers to display names."""

    display_names = {
        "travelperk": "TravelPerk",
        "fcm_travel": "FCM Travel",
        "bcd_travel": "BCD Travel",
        "aav_luxury_travel": "AAV Luxury Travel",
        "french_promise": "French Promise",
        "navan": "Navan",
        "vogue_business": "Vogue Business",
        "business_of_fashion": "Business of Fashion",
        "wwd": "WWD",
        "ttg": "TTG",
        "etourisme": "Etourisme",
        "fashion_united": "Fashion United",
    }

    return display_names.get(
        site,
        site.replace("_", " ").title(),
    )

def delete_generated_slides(
    service,
    presentation_id,
    presentation,
):
    """Delete previously generated slides while keeping the title slide."""

    slides = presentation.get("slides", [])

    if len(slides) <= 1:
        return

    requests = []

    for slide in slides[1:]:
        requests.append({
            "deleteObject": {
                "objectId": slide["objectId"],
            }
        })

    service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests},
    ).execute()

    print(
        f"Deleted {len(slides) - 1} "
        "previously generated slides."
    )

def create_slide(
    service,
    presentation_id,
    slide_id,
    title,
    body,
):
    """Create a title-and-body slide."""

    title_id = f"{slide_id}_title"
    body_id = f"{slide_id}_body"

    requests = [
        {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {
                    "predefinedLayout": "TITLE_AND_BODY"
                },
                "placeholderIdMappings": [
                    {
                        "layoutPlaceholder": {
                            "type": "TITLE",
                            "index": 0,
                        },
                        "objectId": title_id,
                    },
                    {
                        "layoutPlaceholder": {
                            "type": "BODY",
                            "index": 0,
                        },
                        "objectId": body_id,
                    },
                ],
            }
        },
        {
            "insertText": {
                "objectId": title_id,
                "text": title,
            }
        },
        {
            "insertText": {
                "objectId": body_id,
                "text": body,
            }
        },
        {
            "updateTextStyle": {
                "objectId": body_id,
                "textRange": {
                    "type": "ALL"
                },
                "style": {
                    "fontSize": {
                        "magnitude": 14,
                        "unit": "PT"
                    }
                },
                "fields": "fontSize",
            }
        },
    ]

    service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests},
    ).execute()

def create_initial_slides(
    service,
    presentation_id,
    summary,
):
    """Create the initial market research slides."""

    overview_body = (
        f"Websites analyzed: {summary['total_sites']}\n"
        f"• Competitor websites: "
        f"{summary['competitor_sites']}\n"
        f"• Travel news sources: "
        f"{summary['travel_news_sites']}\n"
        f"• Fashion news sources: "
        f"{summary['fashion_news_sites']}\n\n"
        "Research Focus\n"
        "• Competitive positioning and services\n"
        "• Travel industry developments\n"
        "• Fashion and luxury travel trends"
    )

    competitor_body = (
        "Structured competitor data extracted:\n\n"
        f"• {summary['service_count']} "
        "service offerings\n"
        f"• {summary['case_study_count']} "
        "case studies\n"
        f"• {summary['testimonial_count']} "
        "client testimonials\n\n"
        "The dataset supports comparison of service "
        "portfolios, market positioning, client evidence, "
        "and potential differentiation opportunities."
    )

    create_slide(
        service,
        presentation_id,
        "project_overview",
        "Project Overview",
        overview_body,
    )

    create_slide(
        service,
        presentation_id,
        "competitor_analysis",
        "Competitor Analysis",
        competitor_body,
    )

def create_bar_chart_slide(
    service,
    presentation_id,
    slide_id,
    title,
    data,
):
    """Create a reusable horizontal bar chart slide."""

    requests = [
        {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {
                    "predefinedLayout": "BLANK"
                },
            }
        }
    ]

    title_id = f"{slide_id}_title"

    requests.append({
        "createShape": {
            "objectId": title_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": slide_id,
                "size": {
                    "width": {
                        "magnitude": 620,
                        "unit": "PT",
                    },
                    "height": {
                        "magnitude": 40,
                        "unit": "PT",
                    },
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": 40,
                    "translateY": 25,
                    "unit": "PT",
                },
            },
        }
    })

    requests.append({
        "insertText": {
            "objectId": title_id,
            "text": title,
        }
    })

    max_count = max(
        item["count"]
        for item in data
    )

    start_y = 90
    row_height = 48
    max_bar_width = 340

    for index, item in enumerate(data):
        y = start_y + index * row_height

        label_id = f"{slide_id}_label_{index}"
        bar_id = f"{slide_id}_bar_{index}"
        value_id = f"{slide_id}_value_{index}"

        bar_width = (
            item["count"] / max_count
        ) * max_bar_width

        # Source/company label
        requests.append({
            "createShape": {
                "objectId": label_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {
                            "magnitude": 160,
                            "unit": "PT",
                        },
                        "height": {
                            "magnitude": 32,
                            "unit": "PT",
                        },
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 35,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        })

        requests.append({
            "insertText": {
                "objectId": label_id,
                "text": format_site_name(
                    item["site"]
                ),
            }
        })

        # Horizontal bar
        requests.append({
            "createShape": {
                "objectId": bar_id,
                "shapeType": "RECTANGLE",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {
                            "magnitude": bar_width,
                            "unit": "PT",
                        },
                        "height": {
                            "magnitude": 22,
                            "unit": "PT",
                        },
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 205,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        })

        # Numeric value
        requests.append({
            "createShape": {
                "objectId": value_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {
                            "magnitude": 50,
                            "unit": "PT",
                        },
                        "height": {
                            "magnitude": 25,
                            "unit": "PT",
                        },
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 565,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        })

        requests.append({
            "insertText": {
                "objectId": value_id,
                "text": str(item["count"]),
            }
        })

    service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests},
    ).execute()

def populate_title_slide(
    service,
    presentation_id,
    presentation,
):
    """Populate the existing first slide."""

    first_slide = presentation["slides"][0]

    placeholders = []

    for element in first_slide.get("pageElements", []):
        shape = element.get("shape", {})
        placeholder = shape.get("placeholder", {})

        if placeholder:
            placeholders.append({
                "object_id": element["objectId"],
                "type": placeholder.get("type"),
            })

    requests = []

    for placeholder in placeholders:
        if placeholder["type"] in {
            "CENTERED_TITLE",
            "TITLE",
        }:
            requests.append({
                "deleteText": {
                    "objectId": placeholder["object_id"],
                    "textRange": {
                        "type": "ALL",
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": placeholder["object_id"],
                    "text": "Frenchway Market Research",
                }
            })

        elif placeholder["type"] == "SUBTITLE":
            requests.append({
                "deleteText": {
                    "objectId": placeholder["object_id"],
                    "textRange": {
                        "type": "ALL",
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": placeholder["object_id"],
                    "text": (
                        "Competitive, Travel, and "
                        "Fashion Industry Analysis"
                    ),
                }
            })

    if requests:
        service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()

def get_presentation(service, presentation_id):
    """Retrieve presentation metadata."""

    presentation = (
        service.presentations()
        .get(presentationId=presentation_id)
        .execute()
    )

    return presentation


if __name__ == "__main__":
    service = authenticate_google_slides()
    presentation_id = load_presentation_id()

    presentation = get_presentation(
        service,
        presentation_id,
    )

    records = load_processed_data()
    analysis_report = load_analysis_report()
    print(
        "AI analysis loaded:",
        analysis_report["dataset_summary"][
            "total_market_insights"
        ],
        "market insights",
    )
    summary = calculate_summary(records)
    service_counts = calculate_competitor_service_counts(
        records
    )
    market_insight_counts = calculate_market_insight_counts(
        records
    )

    print("Google Slides connection successful.")
    print(f"Title: {presentation['title']}")
    print(f"Websites analyzed: {summary['total_sites']}")
    print(f"Service offerings: {summary['service_count']}")
    print(f"Market insights: {summary['market_insight_count']}")
    print("\nMarket insights by source:")

    for item in market_insight_counts:
        print(
            f"- {format_site_name(item['site'])}: "
            f"{item['count']}"
        )

    populate_title_slide(
        service,
        presentation_id,
        presentation,
    )

    delete_generated_slides(
        service,
        presentation_id,
        presentation,
    )

    create_initial_slides(
        service,
        presentation_id,
        summary,
    )

    create_bar_chart_slide(
        service,
        presentation_id,
        "service_chart",
        "Extracted Service Offerings by Competitor",
        service_counts,
    )

    create_bar_chart_slide(
        service,
        presentation_id,
        "market_insights_chart",
        "Market Insights by Source",
        market_insight_counts,
    )

    create_analysis_slides(
        service,
        presentation_id,
    )

    print("Presentation slides created successfully.")