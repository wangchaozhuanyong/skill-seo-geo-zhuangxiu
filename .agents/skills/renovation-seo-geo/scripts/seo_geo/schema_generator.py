#!/usr/bin/env python3
"""Generate draft JSON-LD schema recommendations from approved SEO workspace data."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


SEO_GEO_DIR = Path(__file__).resolve().parent
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def field_value(text: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:\s*(.*)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def parse_services(root: Path) -> list[dict[str, str]]:
    text = read_text(root / "seo-workspace" / "data" / "services.md")
    services: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        if line.startswith("### "):
            if current:
                services.append(current)
            current = {"name": line[4:].strip()}
            continue
        if not current or not line.startswith("- "):
            continue
        key, _, value = line[2:].partition(":")
        current[key.strip()] = value.strip()
    if current:
        services.append(current)
    return services


def verified_areas(root: Path) -> list[dict[str, str]]:
    return [
        row for row in read_csv_rows(root / "seo-workspace" / "data" / "service-areas.csv")
        if row.get("verified", "").lower() == "yes"
    ]


def latest_content_brief(root: Path) -> Path | None:
    briefs = sorted((root / "seo-workspace" / "drafts").glob("*content-brief.md"))
    return briefs[-1] if briefs else None


def site_origin(website: str) -> str:
    parsed = urlparse(website)
    if not parsed.scheme or not parsed.netloc:
        return website.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}"


def organization_schema(brand_text: str) -> dict:
    website = field_value(brand_text, "Website")
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{website.rstrip('/')}/#organization" if website else "#organization",
        "name": field_value(brand_text, "Company name"),
        "alternateName": field_value(brand_text, "Brand name"),
        "url": website,
        "telephone": field_value(brand_text, "Phone"),
        "email": field_value(brand_text, "Email"),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": field_value(brand_text, "Address if public"),
            "addressCountry": "MY",
        },
    }


def local_business_schema(brand_text: str, areas: list[dict[str, str]]) -> dict:
    website = field_value(brand_text, "Website")
    area_names = [row.get("area") for row in areas if row.get("area")]
    schema = {
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": f"{website.rstrip('/')}/#localbusiness" if website else "#localbusiness",
        "name": field_value(brand_text, "Company name"),
        "url": website,
        "telephone": field_value(brand_text, "Phone"),
        "email": field_value(brand_text, "Email"),
        "address": {
            "@type": "PostalAddress",
            "streetAddress": field_value(brand_text, "Address if public"),
            "addressLocality": "Kuala Lumpur",
            "addressCountry": "MY",
        },
        "areaServed": [{"@type": "Place", "name": name} for name in area_names],
    }
    return schema


def service_schema(service: dict[str, str], brand_text: str, areas: list[dict[str, str]]) -> dict:
    website = field_value(brand_text, "Website")
    url = service.get("Existing URL") or service.get("English URL") or website
    return {
        "@context": "https://schema.org",
        "@type": "Service",
        "@id": f"{url.rstrip('/')}/#service",
        "name": service.get("name", ""),
        "description": service.get("Description", ""),
        "url": url,
        "provider": {
            "@type": "HomeAndConstructionBusiness",
            "name": field_value(brand_text, "Company name"),
            "url": website,
        },
        "areaServed": [{"@type": "Place", "name": row.get("area")} for row in areas if row.get("area")],
    }


def breadcrumb_schema(url: str, name: str) -> dict:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    items = []
    path = ""
    for index, part in enumerate(parts, start=1):
        path += f"/{part}"
        items.append(
            {
                "@type": "ListItem",
                "position": index,
                "name": name if index == len(parts) else part.replace("-", " ").title(),
                "item": f"{origin}{path}" if origin else path,
            }
        )
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def faq_schema_from_brief(brief_text: str, source_url: str) -> dict | None:
    if "Bilingual FAQ" not in brief_text:
        return None
    questions = [
        {
            "@type": "Question",
            "name": "住宅装修前要准备什么？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "建议先准备房屋照片、面积、位置、平面图、屋况问题、预算方向和希望完成的范围。",
            },
        },
        {
            "@type": "Question",
            "name": "What should I prepare before residential renovation?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Prepare photos, size, location, layout plan, current issues, budget direction, and the renovation scope you want to discuss.",
            },
        },
    ]
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": f"{source_url.rstrip('/')}/#faq",
        "mainEntity": questions,
    }


def image_object_schema(brand_text: str) -> dict:
    website = field_value(brand_text, "Website")
    return {
        "@context": "https://schema.org",
        "@type": "ImageObject",
        "name": "Residential renovation design concept / 住宅装修概念设计",
        "caption": "Design concept / rendering concept. This is planning material, not completed-project proof.",
        "representativeOfPage": False,
        "creator": {
            "@type": "Organization",
            "name": field_value(brand_text, "Company name"),
            "url": website,
        },
    }


def article_schema_from_brief(brief_path: Path | None, brand_text: str) -> dict | None:
    if not brief_path:
        return None
    website = field_value(brand_text, "Website")
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Residential Renovation Service Page Content Brief",
        "author": {
            "@type": "Organization",
            "name": field_value(brand_text, "Company name"),
            "url": website,
        },
        "dateCreated": dt.date.today().isoformat(),
        "isAccessibleForFree": True,
        "about": "Draft-only SEO/GEO content brief for owner review.",
    }


def video_object_placeholder() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "schemaStatus": "not_generated",
        "reason": "NEEDS OWNER INPUT: no owner-approved real video URL, thumbnail, upload date, or visible page video content was provided.",
    }


def build_schema_recommendations(root: Path) -> list[dict]:
    root = root.resolve()
    brand_text = read_text(root / "seo-workspace" / "data" / "brand-profile.md")
    areas = verified_areas(root)
    services = parse_services(root)
    website = field_value(brand_text, "Website")
    schemas: list[dict] = [
        organization_schema(brand_text),
        local_business_schema(brand_text, areas),
    ]
    for service in services:
        schemas.append(service_schema(service, brand_text, areas))
        url = service.get("Existing URL", "")
        if url:
            schemas.append(breadcrumb_schema(url, service.get("name", "")))
    brief_path = latest_content_brief(root)
    brief_text = read_text(brief_path) if brief_path else ""
    faq = faq_schema_from_brief(brief_text, f"{site_origin(website)}/en/services/renovation")
    if faq:
        schemas.append(faq)
    article = article_schema_from_brief(brief_path, brand_text)
    if article:
        schemas.append(article)
    schemas.append(image_object_schema(brand_text))
    schemas.append(video_object_placeholder())
    return schemas


def write_schema_recommendations(root: Path) -> Path:
    root = root.resolve()
    output = root / "seo-workspace" / "data" / "schema-recommendations.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_schema_recommendations(root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate draft JSON-LD schema recommendations.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(write_schema_recommendations(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
