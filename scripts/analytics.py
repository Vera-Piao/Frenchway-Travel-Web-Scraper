"""Deterministic, explainable metrics for the Frenchway research dataset."""

from collections import Counter, defaultdict
from datetime import datetime
import math
import re


POSITIVE_TERMS = {
    "authentic", "benefit", "confidence", "creative", "demand", "experience",
    "growth", "improve", "innovation", "luxury", "opportunity", "personalized",
    "premium", "resilient", "safe", "sustainable", "trust", "unique", "value",
}
NEGATIVE_TERMS = {
    "cancel", "cost", "crisis", "decline", "delay", "disruption", "downturn",
    "fraud", "inflation", "risk", "shortage", "threat", "uncertain", "warning",
    "wildfire", "weak",
}
THEME_TERMS = {
    "ai_and_technology": (" ai ", "artificial intelligence", "digital", "technology", "automation"),
    "experiential_travel": ("experience", "experiential", "culture", "event", "festival"),
    "fashion_and_retail": ("fashion", "luxury", "retail", "shopping", "vintage"),
    "sustainability": ("sustainab", "climate", "carbon", "responsible"),
    "risk_and_resilience": ("risk", "crisis", "disruption", "delay", "security", "wildfire"),
    "trust_and_service": ("trust", "expert", "advisor", "service", "concierge", "support"),
}


def tokenize(text):
    return re.findall(r"[a-z][a-z'-]+", (text or "").casefold())


def sentiment_for_text(text):
    tokens = tokenize(text)
    positive = sum(token in POSITIVE_TERMS for token in tokens)
    negative = sum(token in NEGATIVE_TERMS for token in tokens)
    evidence = positive + negative
    score = 0.0 if evidence == 0 else (positive - negative) / evidence
    label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    return {
        "label": label,
        "score": round(score, 4),
        "positive_terms": positive,
        "negative_terms": negative,
        "evidence_terms": evidence,
    }


def collect_text_records(records):
    items = []
    for record in records:
        for insight in record.get("market_insights", []):
            items.append({
                "site": record.get("site", ""),
                "category": record.get("category", ""),
                "kind": "market_insight",
                "title": insight.get("title", ""),
                "text": " ".join(filter(None, [insight.get("title", ""), insight.get("summary", "")])),
                "date": insight.get("date", ""),
                "url": insight.get("url", ""),
            })
        for testimonial in record.get("client_testimonials", []):
            items.append({
                "site": record.get("site", ""),
                "category": record.get("category", ""),
                "kind": "testimonial",
                "title": "",
                "text": testimonial,
                "date": "",
                "url": "",
            })
    return items


def sentiment_summary(text_records):
    distribution = Counter()
    scores = []
    evidence_records = 0
    for item in text_records:
        result = sentiment_for_text(item["text"])
        distribution[result["label"]] += 1
        scores.append(result["score"])
        evidence_records += result["evidence_terms"] > 0
    return {
        "method": "transparent keyword polarity; descriptive, not customer satisfaction",
        "records_analyzed": len(text_records),
        "records_with_lexicon_evidence": evidence_records,
        "distribution": dict(sorted(distribution.items())),
        "mean_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "limitations": "Titles and short summaries can omit context, irony, and negation.",
    }


def theme_summary(text_records):
    counts = Counter()
    for item in text_records:
        haystack = f" {(item['text'] or '').casefold()} "
        for theme, terms in THEME_TERMS.items():
            if any(term in haystack for term in terms):
                counts[theme] += 1
    return [
        {"theme": theme, "record_count": count}
        for theme, count in counts.most_common()
    ]


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return None
    cleaned = re.sub(r"^(published|updated)\s*:?\s*", "", value, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned)
    iso_candidate = cleaned.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate).replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    match = re.search(r"(20\d{2})[-/.](\d{1,2})", cleaned)
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), 1)
    return None


def month_index(dt):
    return dt.year * 12 + dt.month - 1


def month_label(index):
    year, month_zero = divmod(index, 12)
    return f"{year:04d}-{month_zero + 1:02d}"


def linear_forecast(text_records, minimum_records=20, minimum_months=6, horizon=3):
    monthly = Counter()
    dated_records = 0
    for item in text_records:
        if item["kind"] != "market_insight":
            continue
        parsed = parse_date(item.get("date", ""))
        if parsed:
            dated_records += 1
            monthly[month_index(parsed)] += 1

    if len(monthly) < minimum_months or dated_records < minimum_records:
        return {
            "status": "insufficient_data",
            "method": "ordinary least-squares trend on monthly dated article counts",
            "dated_records": dated_records,
            "distinct_months": len(monthly),
            "minimum_records": minimum_records,
            "minimum_months": minimum_months,
            "forecast": [],
            "reason": "Forecast withheld because the dated time series is too short or sparse.",
        }

    start = min(monthly)
    end = max(monthly)
    x_values = list(range(end - start + 1))
    y_values = [monthly[start + x] for x in x_values]
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    slope = 0.0 if denominator == 0 else sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / denominator
    intercept = y_mean - slope * x_mean
    predictions = []
    for offset in range(1, horizon + 1):
        x = x_values[-1] + offset
        predictions.append({
            "month": month_label(end + offset),
            "predicted_article_count": round(max(0.0, intercept + slope * x), 2),
        })
    residuals = [y - (intercept + slope * x) for x, y in zip(x_values, y_values)]
    rmse = math.sqrt(sum(value ** 2 for value in residuals) / len(residuals))
    return {
        "status": "modeled",
        "method": "ordinary least-squares trend on monthly dated article counts",
        "dated_records": dated_records,
        "distinct_months": len(monthly),
        "slope_per_month": round(slope, 4),
        "training_rmse": round(rmse, 4),
        "observed_monthly_counts": [
            {"month": month_label(index), "count": monthly.get(index, 0)}
            for index in range(start, end + 1)
        ],
        "forecast": predictions,
        "limitations": "Article volume measures source publishing/capture activity, not market demand or revenue.",
    }


def extraction_coverage(records):
    fields = (
        "service_offerings", "case_studies", "client_testimonials", "thought_leadership",
        "industries_served", "pricing_signals", "market_insights",
    )
    return {
        field: {
            "records": sum(len(record.get(field, [])) for record in records),
            "sites_with_data": sum(bool(record.get(field)) for record in records),
        }
        for field in fields
    }


def build_quantitative_analysis(records):
    text_records = collect_text_records(records)
    result = {
        "sentiment": sentiment_summary(text_records),
        "themes": theme_summary(text_records),
        "predictive_model": linear_forecast(text_records),
        "extraction_coverage": extraction_coverage(records),
    }
    result["by_category"] = {}
    for category in ("travel_news", "fashion_news"):
        category_records = [item for item in text_records if item["category"] == category]
        result["by_category"][category] = {
            "sentiment": sentiment_summary(category_records),
            "themes": theme_summary(category_records),
            "predictive_model": linear_forecast(category_records),
        }
    return result


def offline_recommendations(quantitative):
    coverage = quantitative["extraction_coverage"]
    return [
        {
            "title": "Lead with signature fashion-and-culture journeys",
            "rationale": "Fashion, luxury, retail, and experiential themes recur in the captured evidence.",
            "suggested_action": "Pilot one Paris itinerary with explicit access, service, and conversion measures.",
        },
        {
            "title": "Use AI for drafts with human approval",
            "rationale": "Technology signals coexist with trust, expertise, and risk themes.",
            "suggested_action": "Require specialist review and a source checklist before sending itineraries.",
        },
        {
            "title": "Make resilience part of the offer",
            "rationale": "Risk and disruption signals appear in travel coverage.",
            "suggested_action": "Publish escalation, rebooking, traveler-alert, and data-protection commitments.",
        },
        {
            "title": "Improve evidence depth",
            "rationale": f"Pricing signals appear on {coverage['pricing_signals']['sites_with_data']} sites and industries on {coverage['industries_served']['sites_with_data']} sites.",
            "suggested_action": "Review low-yield sources monthly and maintain selectors with fixtures.",
        },
        {
            "title": "Operate a monitored monthly scan",
            "rationale": "Recurring decisions require freshness and source-level quality metrics.",
            "suggested_action": "Schedule the pipeline, retain manifests, and alert on coverage or yield regressions.",
        },
    ]
