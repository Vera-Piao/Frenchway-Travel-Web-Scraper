"""Create an evidence-bounded market analysis with optional OpenAI synthesis."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from openai import OpenAI

try:
    from .analytics import build_quantitative_analysis, offline_recommendations
except ImportError:
    from analytics import build_quantitative_analysis, offline_recommendations


DATA_PATH = Path("data/processed/scraped_data.json")
OUTPUT_PATH = Path("data/processed/analysis_report.json")


def load_processed_data(file_path=DATA_PATH):
    with Path(file_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def collect_market_insights(records):
    insights = []
    for record in records:
        if record.get("category") not in {"travel_news", "fashion_news"}:
            continue
        for article in record.get("market_insights", []):
            insights.append({
                "source": record.get("site", ""),
                "category": record.get("category", ""),
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "date": article.get("date", ""),
                "url": article.get("url", ""),
            })
    return insights


def format_insights_for_ai(insights, limit=120):
    sections = []
    for index, insight in enumerate(insights[:limit], start=1):
        sections.append("\n".join(filter(None, [
            f"[{index}] Source: {insight['source']}",
            f"Title: {insight['title']}",
            f"Summary: {insight['summary']}" if insight["summary"] else "",
            f"Date: {insight['date']}" if insight["date"] else "",
            f"URL: {insight['url']}" if insight["url"] else "",
        ])))
    return "\n\n".join(sections)


def api_synthesis(client, model, label, insights):
    prompt = f"""
You are preparing market research for Frenchway Travel.
Analyze the supplied {label} article records. Identify five supported themes,
customer expectations, opportunities, and risks. Cite record numbers in the
analysis. Do not invent statistics, dates, sources, or causal claims. Explicitly
state when evidence is title-only or sparse.

DATA:
{format_insights_for_ai(insights)}
"""
    response = client.responses.create(model=model, input=prompt)
    return response.output_text


def api_recommendations(client, model, travel_analysis, fashion_analysis):
    prompt = f"""
Create five concise, evidence-bounded recommendations for Frenchway Travel.
For each, include title, rationale, action, and success measure. Base every item
only on the analyses below and avoid unsupported forecasts.

TRAVEL ANALYSIS:
{travel_analysis}

FASHION/LUXURY ANALYSIS:
{fashion_analysis}
"""
    response = client.responses.create(model=model, input=prompt)
    return response.output_text


def offline_analysis_text(category, quantitative):
    category_metrics = quantitative.get("by_category", {}).get(category, quantitative)
    themes = category_metrics["themes"][:5]
    theme_text = ", ".join(
        f"{item['theme'].replace('_', ' ')} ({item['record_count']} records)"
        for item in themes
    ) or "no repeated themes detected"
    sentiment = category_metrics["sentiment"]
    forecast = category_metrics["predictive_model"]
    display_category = category.replace("_news", "").replace("_", " ")
    return (
        f"Deterministic {display_category} summary. Leading category themes: {theme_text}. "
        f"Keyword sentiment mean is {sentiment['mean_score']}; this is descriptive and not a customer-satisfaction measure. "
        f"Predictive model status: {forecast['status']}. {forecast.get('reason', forecast.get('limitations', ''))}"
    )


def dataset_summary(records, insights):
    return {
        "total_sources": len(records),
        "competitor_sources": sum(record.get("category") == "competitors" for record in records),
        "travel_news_sources": sum(record.get("category") == "travel_news" for record in records),
        "fashion_news_sources": sum(record.get("category") == "fashion_news" for record in records),
        "total_market_insights": len(insights),
        "travel_insights": sum(item["category"] == "travel_news" for item in insights),
        "fashion_insights": sum(item["category"] == "fashion_news" for item in insights),
    }


def build_report(records, *, use_ai=False, model=None):
    insights = collect_market_insights(records)
    travel = [item for item in insights if item["category"] == "travel_news"]
    fashion = [item for item in insights if item["category"] == "fashion_news"]
    quantitative = build_quantitative_analysis(records)

    if use_ai:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required with --ai.")
        model = model or os.environ.get("OPENAI_MODEL", "gpt-5-mini")
        client = OpenAI()
        travel_analysis = api_synthesis(client, model, "travel", travel)
        fashion_analysis = api_synthesis(client, model, "fashion and luxury", fashion)
        recommendations = api_recommendations(client, model, travel_analysis, fashion_analysis)
        mode = "openai_plus_deterministic_metrics"
    else:
        model = None
        travel_analysis = offline_analysis_text("travel_news", quantitative)
        fashion_analysis = offline_analysis_text("fashion_news", quantitative)
        recommendations = offline_recommendations(quantitative)
        mode = "deterministic_offline"

    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "analysis_mode": mode,
        "model": model,
        "dataset_summary": dataset_summary(records, insights),
        "quantitative_analysis": quantitative,
        "travel_analysis": travel_analysis,
        "fashion_analysis": fashion_analysis,
        "strategic_recommendations": recommendations,
        "guardrails": [
            "Record counts are extraction outputs, not market share or demand.",
            "Keyword sentiment is descriptive and can miss context.",
            "Forecasts are withheld unless the dated time series meets minimum sufficiency thresholds.",
            "OpenAI synthesis, when enabled, must be reviewed against source records before external use.",
        ],
    }


def save_analysis_report(report, output_path=OUTPUT_PATH):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DATA_PATH))
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    parser.add_argument("--ai", action="store_true", help="Use the OpenAI Responses API for narrative synthesis.")
    parser.add_argument("--model", help="OpenAI model id; defaults to OPENAI_MODEL or gpt-5-mini.")
    return parser.parse_args()


def main():
    args = parse_args()
    records = load_processed_data(args.input)
    report = build_report(records, use_ai=args.ai, model=args.model)
    path = save_analysis_report(report, args.output)
    print(json.dumps({
        "output": str(path),
        "analysis_mode": report["analysis_mode"],
        "dataset_summary": report["dataset_summary"],
        "predictive_model_status": report["quantitative_analysis"]["predictive_model"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
