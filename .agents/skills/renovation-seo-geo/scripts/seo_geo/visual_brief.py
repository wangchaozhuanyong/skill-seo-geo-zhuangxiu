#!/usr/bin/env python3
"""Create visual asset briefs for SEO/GEO image opportunities."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


VISUAL_FIELDS = [
    "target_page",
    "page_type",
    "asset_type",
    "placement",
    "purpose",
    "concept_label_zh",
    "concept_label_en",
    "zh_alt_text",
    "en_alt_text",
    "file_name_suggestion",
    "caption_note",
    "owner_input_required",
]


@dataclass
class VisualBrief:
    target_page: str
    page_type: str
    asset_type: str
    placement: str
    purpose: str
    concept_label_zh: str
    concept_label_en: str
    zh_alt_text: str
    en_alt_text: str
    file_name_suggestion: str
    caption_note: str
    owner_input_required: str = ""

    def as_row(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in VISUAL_FIELDS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def infer_asset_type(page_type: str) -> str:
    if page_type == "service":
        return "service hero / section design concept"
    if page_type in {"case-study", "case-study-hub"}:
        return "case reference image / confirmed real photo if owner-approved"
    if page_type == "local":
        return "local service concept image"
    if page_type == "article":
        return "article explanatory graphic"
    return "page support image"


def slug_from_url(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1] or "home"
    return slug.replace("_", "-").lower()


def visual_brief_for_row(row: dict[str, str]) -> VisualBrief:
    url = row.get("url", "")
    page_type = row.get("page_type", "")
    slug = slug_from_url(url)
    is_zh = "/zh/" in url or url.endswith("/zh")
    service_label_zh = "装修服务视觉规划"
    service_label_en = "renovation service visual planning"
    if "kitchen" in slug:
        service_label_zh = "厨房装修概念设计"
        service_label_en = "kitchen renovation design concept"
    elif "bathroom" in slug:
        service_label_zh = "浴室装修效果图方案"
        service_label_en = "bathroom renovation rendering concept"
    elif "office" in slug:
        service_label_zh = "办公室装修空间规划"
        service_label_en = "office renovation space planning concept"
    elif "shop" in slug:
        service_label_zh = "店铺装修动线规划"
        service_label_en = "shop renovation layout concept"
    elif "renovation" in slug:
        service_label_zh = "住宅装修概念设计"
        service_label_en = "residential renovation design concept"
    alt_zh = f"{service_label_zh} - FLASH CAST 吉隆坡雪兰莪"
    alt_en = f"{service_label_en} by FLASH CAST in Kuala Lumpur and Selangor"
    return VisualBrief(
        target_page=url,
        page_type=page_type,
        asset_type=infer_asset_type(page_type),
        placement="hero or first supporting section",
        purpose="Improve page clarity, service understanding, image search relevance, and AI-search visual context.",
        concept_label_zh="概念设计 / 效果图方案 / 规划示例",
        concept_label_en="design concept / rendering concept / planning example",
        zh_alt_text=alt_zh if is_zh else f"{service_label_zh}参考图",
        en_alt_text=alt_en,
        file_name_suggestion=f"flash-cast-{slug}-design-concept.webp",
        caption_note="Use as clearly labeled planning material unless owner provides real completed-project photo proof.",
        owner_input_required="Real project photo proof required only if this will be presented as a completed project or listing photo.",
    )


def build_visual_briefs(root: Path, max_items: int = 20) -> list[VisualBrief]:
    rows = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    candidates = []
    for row in rows:
        page_type = row.get("page_type", "")
        try:
            image_count = int(float(row.get("image_count", "0") or 0))
        except ValueError:
            image_count = 0
        if page_type in {"service", "local", "article", "case-study", "case-study-hub"} and image_count == 0:
            candidates.append(visual_brief_for_row(row))
    return candidates[:max_items]


def write_visual_briefs(root: Path) -> Path:
    root = root.resolve()
    output = root / "seo-workspace" / "data" / "visual-asset-briefs.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=VISUAL_FIELDS)
        writer.writeheader()
        writer.writerows(item.as_row() for item in build_visual_briefs(root))
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create visual asset briefs for image SEO opportunities.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(write_visual_briefs(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
