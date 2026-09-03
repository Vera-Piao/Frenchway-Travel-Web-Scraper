import json
from pathlib import Path
from openai import OpenAI


DATA_PATH = "data/processed/scraped_data.json"
OUTPUT_PATH = "data/processed/analysis_report.json"

def test_openai_connection():
    """Test the OpenAI API connection."""

    client = OpenAI()

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=(
            "Reply with exactly: "
            "OpenAI connection successful."
        ),
    )

    return response.output_text

def load_processed_data():
    """Load processed scraped data."""

    path = Path(DATA_PATH)

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def collect_market_insights(records):
    """Collect market insights for AI analysis."""

    insights = []

    for record in records:
        if record["category"] not in {
            "travel_news",
            "fashion_news",
        }:
            continue

        for article in record["market_insights"]:
            insights.append({
                "source": record["site"],
                "category": record["category"],
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "date": article.get("date", ""),
                "url": article.get("url", ""),
            })

    return insights


def split_insights_by_category(insights):
    """Split insights into travel and fashion datasets."""

    travel = []
    fashion = []

    for insight in insights:
        if insight["category"] == "travel_news":
            travel.append(insight)

        elif insight["category"] == "fashion_news":
            fashion.append(insight)

    return travel, fashion

def format_insights_for_ai(insights):
    """Format market insights as compact text for AI analysis."""

    sections = []

    for index, insight in enumerate(insights, start=1):
        parts = [
            f"[{index}]",
            f"Source: {insight['source']}",
            f"Title: {insight['title']}",
        ]

        if insight["summary"]:
            parts.append(
                f"Summary: {insight['summary']}"
            )

        if insight["date"]:
            parts.append(
                f"Date: {insight['date']}"
            )

        sections.append("\n".join(parts))

    return "\n\n".join(sections)

def analyze_market_category(
    client,
    category_name,
    insights,
):
    """Analyze one category of market insights."""

    formatted_data = format_insights_for_ai(
        insights
    )

    prompt = f"""
You are analyzing market research data for
Frenchway Travel, a travel company seeking to
attract more international customers.

Analyze the following {category_name} news data.

Identify:
1. Five major market themes or trends.
2. Important customer expectations or behaviors.
3. Relevant opportunities for a travel company.
4. Potential risks or challenges.

Base your conclusions only on the supplied data.
Do not invent statistics, companies, or trends
that are not supported by the input.

For each major theme, briefly explain the evidence
visible in the supplied article titles or summaries.

DATA:
{formatted_data}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt,
    )

    return response.output_text

def group_insights_by_source(insights):
    """Group market insights by source."""

    groups = {}

    for insight in insights:
        source = insight["source"]

        if source not in groups:
            groups[source] = []

        groups[source].append(insight)

    return groups

def analyze_fashion_sources(
    client,
    fashion_insights,
):
    """Analyze fashion news source by source."""

    source_groups = group_insights_by_source(
        fashion_insights
    )

    analyses = {}

    for source, insights in source_groups.items():
        print(
            f"Analyzing {source}: "
            f"{len(insights)} insights..."
        )

        analyses[source] = analyze_market_category(
            client,
            f"fashion and luxury industry "
            f"news from {source}",
            insights,
        )

    return analyses

def synthesize_fashion_analysis(
    client,
    source_analyses,
):
    """Synthesize fashion analyses across sources."""

    combined = []

    for source, analysis in source_analyses.items():
        combined.append(
            f"SOURCE: {source}\n"
            f"{analysis}"
        )

    combined_text = "\n\n".join(combined)

    prompt = f"""
You are preparing market research for Frenchway
Travel, a travel company seeking to attract more
international customers.

Below are separate analyses of fashion and luxury
industry news sources.

Synthesize them into a concise cross-source report.

Identify:
1. Five strongest fashion/luxury market trends.
2. Customer expectations relevant to luxury travel.
3. Connections between fashion and travel.
4. Opportunities for Frenchway Travel.
5. Risks or challenges.

Prioritize patterns supported across the supplied
analyses. Do not invent facts or statistics.

SOURCE ANALYSES:

{combined_text}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt,
    )

    return response.output_text

def synthesize_strategic_recommendations(
    client,
    travel_analysis,
    fashion_analysis,
):
    """Create final strategic recommendations for Frenchway Travel."""

    prompt = f"""
You are preparing the final strategic market
research summary for Frenchway Travel.

Frenchway Travel wants to attract more
international customers.

Below are two analyses derived from scraped
travel and fashion industry data.

TRAVEL INDUSTRY ANALYSIS:
{travel_analysis}

FASHION AND LUXURY ANALYSIS:
{fashion_analysis}

Based only on these analyses, identify the five
most actionable strategic recommendations for
Frenchway Travel.

Each recommendation must include:
- title
- rationale
- suggested action

Focus on recommendations that connect directly
to international customer acquisition, travel
experience design, digital capabilities, or
competitive differentiation.

Keep the recommendations concise and suitable
for a consulting presentation.

Do not invent statistics or unsupported facts.
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt,
    )

    return response.output_text

def save_analysis_report(
    travel_analysis,
    fashion_analysis,
    strategic_recommendations,
    total_count,
    travel_count,
    fashion_count,
):
    """Save AI market analysis as structured JSON."""

    report = {
        "dataset_summary": {
            "total_market_insights": total_count,
            "travel_insights": travel_count,
            "fashion_insights": fashion_count,
        },
        "travel_analysis": travel_analysis,
        "fashion_analysis": fashion_analysis,
        "strategic_recommendations": (
            strategic_recommendations
        ),
    }
    
    path = Path(OUTPUT_PATH)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\nAnalysis report saved to: {path}")

if __name__ == "__main__":
    records = load_processed_data()

    insights = collect_market_insights(records)

    travel_insights, fashion_insights = (
        split_insights_by_category(insights)
    )

    print(f"Total market insights: {len(insights)}")
    print(f"Travel insights: {len(travel_insights)}")
    print(f"Fashion insights: {len(fashion_insights)}")
    client = OpenAI()

    print("\nAnalyzing travel industry data...")

    travel_analysis = analyze_market_category(
        client,
        "travel industry",
        travel_insights,
    )

    print("\nTRAVEL INDUSTRY ANALYSIS")
    print("=" * 60)
    print(travel_analysis)

    print("\nAnalyzing fashion industry data...")

    fashion_source_analyses = (
        analyze_fashion_sources(
            client,
            fashion_insights,
        )
    )

    print("\nSynthesizing fashion analysis...")

    fashion_analysis = (
        synthesize_fashion_analysis(
            client,
            fashion_source_analyses,
        )
    )

    print("\nFASHION INDUSTRY ANALYSIS")
    print("=" * 60)
    print(fashion_analysis)

    print("\nGenerating strategic recommendations...")

    strategic_recommendations = (
        synthesize_strategic_recommendations(
            client,
            travel_analysis,
            fashion_analysis,
        )
    )

    print("\nSTRATEGIC RECOMMENDATIONS")
    print("=" * 60)
    print(strategic_recommendations)

    save_analysis_report(
        travel_analysis,
        fashion_analysis,
        strategic_recommendations,
        len(insights),
        len(travel_insights),
        len(fashion_insights),
    )
