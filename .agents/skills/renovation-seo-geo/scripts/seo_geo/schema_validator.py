#!/usr/bin/env python3
"""Validate draft schema recommendations against anti-fabrication rules."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SEO_GEO_DIR = Path(__file__).resolve().parent
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))

from schema_generator import build_schema_recommendations, write_schema_recommendations  # noqa: E402


SUPPORTED_TYPES = {
    "Organization",
    "LocalBusiness",
    "HomeAndConstructionBusiness",
    "Service",
    "Article",
    "FAQPage",
    "BreadcrumbList",
    "ImageObject",
    "VideoObject",
}
FORBIDDEN_WITHOUT_REAL_DATA = {"Review", "AggregateRating", "Offer", "PriceSpecification"}
FORBIDDEN_FIELDS_WITHOUT_OWNER_INPUT = {"review", "aggregateRating", "price", "priceRange", "openingHours", "openingHoursSpecification"}


@dataclass
class SchemaIssue:
    severity: str
    schema_type: str
    field: str
    message: str
    recommendation: str


@dataclass
class SchemaValidation:
    schemas: list[dict[str, Any]]
    issues: list[SchemaIssue] = field(default_factory=list)

    def add(self, severity: str, schema_type: str, field: str, message: str, recommendation: str) -> None:
        self.issues.append(SchemaIssue(severity, schema_type, field, message, recommendation))

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def ok(self) -> bool:
        return self.error_count == 0


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def schema_types(schema: dict[str, Any]) -> set[str]:
    value = schema.get("@type", "")
    if isinstance(value, list):
        return {str(item) for item in value}
    return {str(value)} if value else set()


def walk_json(value: Any) -> list[tuple[str, Any]]:
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.append((key, child))
            found.extend(walk_json(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(walk_json(child))
    return found


def verified_area_names(root: Path) -> set[str]:
    names: set[str] = set()
    for row in read_csv_rows(root / "seo-workspace" / "data" / "service-areas.csv"):
        if row.get("verified", "").lower() != "yes":
            continue
        for key in ("area", "city", "state_or_region", "country"):
            if row.get(key):
                names.add(row[key])
    return names


def service_names(root: Path) -> set[str]:
    text = read_text(root / "seo-workspace" / "data" / "services.md")
    return {line[4:].strip() for line in text.splitlines() if line.startswith("### ")}


def real_review_available(root: Path) -> bool:
    brand = read_text(root / "seo-workspace" / "data" / "brand-profile.md")
    cases = read_csv_rows(root / "seo-workspace" / "data" / "case-studies.csv")
    if "Real testimonials: No published testimonials" in brand:
        return False
    return any(row.get("testimonial") and "NEEDS OWNER INPUT" not in row.get("testimonial", "") for row in cases)


def validate_schemas(root: Path, schemas: list[dict[str, Any]] | None = None) -> SchemaValidation:
    root = root.resolve()
    if schemas is None:
        schema_path = root / "seo-workspace" / "data" / "schema-recommendations.json"
        if not schema_path.exists():
            schema_path = write_schema_recommendations(root)
        schemas = json.loads(read_text(schema_path))
    validation = SchemaValidation(schemas=schemas)
    areas = verified_area_names(root)
    services = service_names(root)
    has_real_reviews = real_review_available(root)

    for schema in schemas:
        types = schema_types(schema)
        type_label = ";".join(sorted(types)) or "unknown"
        unsupported = types - SUPPORTED_TYPES - FORBIDDEN_WITHOUT_REAL_DATA
        if unsupported:
            validation.add("warning", type_label, "@type", f"Unsupported schema type(s): {', '.join(sorted(unsupported))}.", "Review manually before publishing.")
        if types & FORBIDDEN_WITHOUT_REAL_DATA and not has_real_reviews:
            validation.add("error", type_label, "@type", "Review/AggregateRating/price-like schema requires real owner-provided data.", "Remove unless real reviews, ratings, or pricing are provided and visible on page.")
        for field, value in walk_json(schema):
            if field in FORBIDDEN_FIELDS_WITHOUT_OWNER_INPUT:
                validation.add("error", type_label, field, f"Forbidden or owner-input field present: {field}.", "Do not use fake rating, fake review, fake price, or fake opening hours.")
            if field == "areaServed":
                places = value if isinstance(value, list) else [value]
                for place in places:
                    if isinstance(place, dict):
                        name = place.get("name", "")
                        if name and name not in areas:
                            validation.add("error", type_label, "areaServed", f"Unsupported service area in schema: {name}.", "Use only verified service areas.")
        if "Service" in types:
            name = str(schema.get("name", ""))
            if name not in services:
                validation.add("warning", type_label, "name", f"Service schema name is not an exact services.md heading: {name}.", "Use service taxonomy from services.md.")
        if "FAQPage" in types and not schema.get("mainEntity"):
            validation.add("error", type_label, "mainEntity", "FAQPage has no visible FAQ entities.", "Only add FAQPage for visible page FAQ.")
        if "ImageObject" in types:
            caption = str(schema.get("caption", "")).lower()
            if "concept" not in caption and "rendering" not in caption:
                validation.add("warning", type_label, "caption", "ImageObject does not clearly label concept/rendering material.", "Label concept images clearly unless real project photo proof exists.")
        if "VideoObject" in types and schema.get("schemaStatus") == "not_generated":
            validation.add("warning", type_label, "VideoObject", "VideoObject placeholder is not publishable.", "Generate VideoObject only when real visible video data exists.")
    return validation


def render_schema_report(root: Path, validation: SchemaValidation) -> str:
    today = dt.date.today().isoformat()
    type_counts: dict[str, int] = {}
    for schema in validation.schemas:
        for item in schema_types(schema):
            type_counts[item] = type_counts.get(item, 0) + 1
    lines = [
        "# Schema Generator / Validator Report",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: draft-only / report-only",
        "- 输出文件: `seo-workspace/data/schema-recommendations.json`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天做 Schema 系统，而不是随机写文章。原因是搜索引擎和 AI 搜索需要用结构化数据理解公司实体、服务、区域、FAQ、面包屑和图片，但 schema 一旦包含虚假评价、价格、营业时间或服务区域，会直接损害可信度。本阶段先生成可审核 schema 建议并用规则拦截不支持的声明。",
        "",
        "## Schema Types Covered",
        "",
    ]
    for schema_type in sorted(type_counts):
        lines.append(f"- {schema_type}: {type_counts[schema_type]}")
    lines.extend([
        "",
        "## Validation Summary",
        "",
        f"- Schema objects: {len(validation.schemas)}",
        f"- Errors: {validation.error_count}",
        f"- Warnings: {validation.warning_count}",
        f"- Status: {'PASS' if validation.ok else 'REVIEW REQUIRED'}",
        "",
        "## Issues",
        "",
    ])
    if validation.issues:
        for issue in validation.issues:
            lines.append(f"- [{issue.severity}] {issue.schema_type} / {issue.field}: {issue.message} 建议: {issue.recommendation}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Hard Rules",
        "",
        "- schema 内容必须在页面可见内容中出现。",
        "- 不允许 fake rating。",
        "- 不允许 fake review。",
        "- 不允许 fake price。",
        "- 不允许 fake opening hours。",
        "- 不允许 fake service area。",
        "- Review 只能在真实评价数据存在且页面可见时使用。",
        "- AggregateRating 只能在真实汇总评分存在且页面可见时使用。",
        "",
        "## Owner Review Notes",
        "",
        "- NEEDS OWNER INPUT: 如需 Review / AggregateRating schema，必须先提供真实评价和汇总评分证明。",
        "- NEEDS OWNER INPUT: 如需营业时间 schema，必须确认真实营业时间。",
        "- NEEDS OWNER INPUT: 如需价格或报价 schema，必须确认页面可见的真实价格信息；当前不建议添加价格 schema。",
        "- VideoObject 当前只生成 not_generated 占位说明，不可发布为真实视频 schema。",
        "",
        "## QA Checklist",
        "",
        "- [ ] 每个 schema 字段都能在对应页面可见内容中找到。",
        "- [ ] Organization / LocalBusiness 使用确认过的公司名、电话、邮箱、地址和网站。",
        "- [ ] Service schema 只使用 services.md 中真实服务。",
        "- [ ] areaServed 只使用 service-areas.csv 中 verified=yes 的区域。",
        "- [ ] FAQPage 只标记页面可见 FAQ。",
        "- [ ] ImageObject 的概念图必须标注 design concept / rendering concept。",
        "- [ ] 不发布 Review、AggregateRating、price、openingHours，除非业主提供真实资料并页面可见。",
        "",
    ])
    return "\n".join(lines)


def run_schema_validation_report(root: Path) -> Path:
    root = root.resolve()
    schema_path = root / "seo-workspace" / "data" / "schema-recommendations.json"
    if not schema_path.exists():
        write_schema_recommendations(root)
    validation = validate_schemas(root)
    output = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-schema-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_schema_report(root, validation), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate draft schema recommendations.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(run_schema_validation_report(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
