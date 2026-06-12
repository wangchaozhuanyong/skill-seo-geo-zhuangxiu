#!/usr/bin/env python3
"""Citation opportunity helpers for local SEO."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CitationOpportunity:
    platform: str
    market: str
    priority: str
    status: str
    required_owner_input: str
    nap_fields_to_match: str
    notes: str


DEFAULT_OPPORTUNITIES = [
    CitationOpportunity(
        platform="Google Business Profile",
        market="Malaysia / global local search",
        priority="high",
        status="needs_owner_input",
        required_owner_input="GBP profile URL, ownership/access, business categories, hours, real photos if used",
        nap_fields_to_match="company name; phone; address; website",
        notes="Do not claim ratings, reviews, photos, or opening hours until owner-provided.",
    ),
    CitationOpportunity(
        platform="Baidu Maps / Baidu local data",
        market="Chinese-language discovery",
        priority="medium",
        status="needs_owner_input",
        required_owner_input="Baidu local/map listing export or owner-approved listing details",
        nap_fields_to_match="company name; phone; address; website",
        notes="Import only if owner provides verified listing data; do not create unsupported China-local claims.",
    ),
    CitationOpportunity(
        platform="Bing Places",
        market="Bing / Microsoft local discovery",
        priority="medium",
        status="owner_review",
        required_owner_input="listing ownership/access if owner wants submission",
        nap_fields_to_match="company name; phone; address; website",
        notes="Useful after GBP/NAP facts are confirmed; no automatic submission.",
    ),
    CitationOpportunity(
        platform="Apple Business Connect / Maps",
        market="Apple Maps local discovery",
        priority="medium",
        status="owner_review",
        required_owner_input="business ownership/access if owner wants submission",
        nap_fields_to_match="company name; phone; address; website",
        notes="Use the same NAP and real photos only.",
    ),
    CitationOpportunity(
        platform="Malaysia business directories",
        market="Malaysia local citation ecosystem",
        priority="medium",
        status="owner_review",
        required_owner_input="owner-approved directory list and submission policy",
        nap_fields_to_match="company name; phone; address; website",
        notes="Prioritize reputable directories; avoid spam directories and duplicate inconsistent profiles.",
    ),
    CitationOpportunity(
        platform="Renovation / interior design industry directories",
        market="home improvement discovery",
        priority="low",
        status="owner_review",
        required_owner_input="approved portfolio facts and real photos if directory requires project proof",
        nap_fields_to_match="company name; phone; address; website",
        notes="Use only confirmed case studies and real owner-provided photos.",
    ),
]


CSV_FIELDS = [
    "platform",
    "market",
    "priority",
    "status",
    "required_owner_input",
    "nap_fields_to_match",
    "notes",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def opportunity_to_row(item: CitationOpportunity) -> dict[str, str]:
    return {
        "platform": item.platform,
        "market": item.market,
        "priority": item.priority,
        "status": item.status,
        "required_owner_input": item.required_owner_input,
        "nap_fields_to_match": item.nap_fields_to_match,
        "notes": item.notes,
    }


def write_citation_opportunities(root: Path, opportunities: list[CitationOpportunity] | None = None) -> Path:
    root = root.resolve()
    opportunities = opportunities or DEFAULT_OPPORTUNITIES
    output = root / "seo-workspace" / "data" / "citation-opportunities.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(opportunity_to_row(item) for item in opportunities)
    return output


def load_or_create_citation_opportunities(root: Path) -> list[dict[str, str]]:
    path = root / "seo-workspace" / "data" / "citation-opportunities.csv"
    if not path.exists():
        write_citation_opportunities(root)
    return read_csv_rows(path)


def priority_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        priority = row.get("priority", "unknown") or "unknown"
        counts[priority] = counts.get(priority, 0) + 1
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create citation opportunity CSV.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(write_citation_opportunities(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
