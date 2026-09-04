"""Canonical target catalog shared by Requests and Scrapy collectors."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = PROJECT_ROOT / "config" / "targets.json"


def load_targets(path=TARGETS_PATH):
    with Path(path).open("r", encoding="utf-8") as file:
        targets = json.load(file)

    if not isinstance(targets, dict) or not targets:
        raise ValueError("Target catalog must be a non-empty object.")

    for category, sites in targets.items():
        if not isinstance(sites, dict) or not sites:
            raise ValueError(f"Target category '{category}' must not be empty.")
        for site, url in sites.items():
            if not site or not isinstance(url, str) or not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid target: {category}/{site}={url!r}")

    return targets


TARGETS = load_targets()
