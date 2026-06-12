#!/usr/bin/env python3
"""Build a safe entity profile for SEO/GEO and AI search readability."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BrandProfile:
    company_name: str = ""
    brand_name: str = ""
    website: str = ""
    main_service_area: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    google_business_profile: str = ""
    licenses: str = ""
    warranty: str = ""
    value_proposition: str = ""
    proof_items: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)


@dataclass
class ServiceSummary:
    name: str
    en_url: str = ""
    zh_url: str = ""
    description: str = ""
    customer_type: str = ""
    problems_solved: str = ""
    best_cta: str = ""
    case_references: str = ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def field_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^- {re.escape(label)}:\s*(.*)$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def bullet_block(text: str, heading: str) -> list[str]:
    pattern = re.compile(rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    if not match:
        return []
    return [
        line.strip()[2:].strip()
        for line in match.group("body").splitlines()
        if line.strip().startswith("- ")
    ]


def load_brand_profile(root: Path) -> BrandProfile:
    path = root / "seo-workspace" / "data" / "brand-profile.md"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    profile = BrandProfile(
        company_name=field_value(text, "Company name"),
        brand_name=field_value(text, "Brand name"),
        website=field_value(text, "Website"),
        main_service_area=field_value(text, "Main service area"),
        phone=field_value(text, "Phone"),
        email=field_value(text, "Email"),
        address=field_value(text, "Address if public"),
        google_business_profile=field_value(text, "Google Business Profile"),
        licenses=field_value(text, "Licenses/certifications"),
        warranty=field_value(text, "Insurance/warranty"),
        value_proposition=field_value(text, "Main value proposition"),
    )
    proof_lines = bullet_block(text, "Proof")
    profile.proof_items = [
        item for item in proof_lines
        if not item.lower().startswith(("real testimonials:", "awards:", "media mentions:"))
    ]
    for label, value in {
        "Google Business Profile": profile.google_business_profile,
        "Awards": field_value(text, "Awards"),
        "Media mentions": field_value(text, "Media mentions"),
    }.items():
        if "NEEDS OWNER INPUT" in value or not value:
            profile.missing_inputs.append(label)
    if "need owner confirmation" in profile.licenses.lower():
        profile.missing_inputs.append("SSM number / certifications")
    if "need owner confirmation" in profile.warranty.lower():
        profile.missing_inputs.append("Warranty scope and duration")
    return profile


def load_services(root: Path) -> list[ServiceSummary]:
    path = root / "seo-workspace" / "data" / "services.md"
    if not path.exists():
        return []
    services: list[ServiceSummary] = []
    current: ServiceSummary | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("### "):
            if current:
                services.append(current)
            current = ServiceSummary(name=line[4:].strip())
            continue
        if not current or not line.startswith("- "):
            continue
        key, _, value = line[2:].partition(":")
        value = value.strip()
        if key == "Existing URL":
            current.en_url = value
        elif key in {"Chinese URL", "Chinese URLs"}:
            current.zh_url = value
        elif key == "Description":
            current.description = value
        elif key == "Customer type":
            current.customer_type = value
        elif key == "Problems solved":
            current.problems_solved = value
        elif key == "Best CTA":
            current.best_cta = value
        elif key == "Real case study references":
            current.case_references = value
    if current:
        services.append(current)
    return services


def verified_service_areas(root: Path) -> list[dict[str, str]]:
    return [
        row for row in read_csv_rows(root / "seo-workspace" / "data" / "service-areas.csv")
        if row.get("verified", "").lower() == "yes"
    ]


def real_case_rows(root: Path) -> list[dict[str, str]]:
    return [
        row for row in read_csv_rows(root / "seo-workspace" / "data" / "case-studies.csv")
        if row.get("project_name") and "NEEDS OWNER INPUT" not in row.get("project_name", "")
    ]


def line_or_input(value: str, label: str) -> str:
    return value or f"NEEDS OWNER INPUT: {label}"


def build_entity_profile(root: Path) -> str:
    profile = load_brand_profile(root)
    services = load_services(root)
    areas = verified_service_areas(root)
    cases = real_case_rows(root)
    today = dt.date.today().isoformat()
    primary_areas = [row.get("area", "") for row in areas[:12] if row.get("area")]
    remaining_area_count = max(0, len(areas) - len(primary_areas))

    lines = [
        "# FLASH CAST Entity Profile for SEO/GEO",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: draft-only / report-only",
        "- 用途: 帮助搜索引擎和 AI 搜索系统清楚理解公司实体、服务、区域、证据边界和页面结构。",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## Entity Identity",
        "",
        f"- Company name: {line_or_input(profile.company_name, 'company name')}",
        f"- Brand name: {line_or_input(profile.brand_name, 'brand name')}",
        f"- Website: {line_or_input(profile.website, 'website')}",
        f"- Main service area: {line_or_input(profile.main_service_area, 'main service area')}",
        f"- Entity type: Renovation contractor / design-and-build renovation service provider",
        "",
        "## NAP",
        "",
        f"- Phone: {line_or_input(profile.phone, 'phone')}",
        f"- Email: {line_or_input(profile.email, 'email')}",
        f"- Address: {line_or_input(profile.address, 'public address')}",
        f"- Google Business Profile: {profile.google_business_profile or 'NEEDS OWNER INPUT'}",
        "",
        "## Service Taxonomy",
        "",
    ]
    for service in services:
        lines.extend([
            f"### {service.name}",
            "",
            f"- English URL: {service.en_url or 'NEEDS OWNER INPUT'}",
            f"- Chinese URL: {service.zh_url or 'NEEDS OWNER INPUT'}",
            f"- Description: {service.description or 'NEEDS OWNER INPUT'}",
            f"- Customer type: {service.customer_type or 'NEEDS OWNER INPUT'}",
            f"- Problems solved: {service.problems_solved or 'NEEDS OWNER INPUT'}",
            f"- Best CTA: {service.best_cta or 'NEEDS OWNER INPUT'}",
            f"- Evidence boundary: {service.case_references or 'NEEDS OWNER INPUT'}",
            "",
        ])
    lines.extend([
        "## Verified Area Coverage",
        "",
        f"- Verified area count: {len(areas)}",
        f"- Primary areas: {', '.join(primary_areas) if primary_areas else 'NEEDS OWNER INPUT'}",
        f"- Additional verified areas not listed above: {remaining_area_count}",
        "- Rule: do not create duplicate doorway pages by swapping city names. Use area pages only when content has local context, service fit, internal links, and useful user information.",
        "",
        "## Evidence Blocks",
        "",
    ])
    if cases:
        for row in cases:
            lines.append(f"- {row.get('project_name')} | {row.get('location')} | {row.get('service')} | photos_available={row.get('photos_available') or 'unknown'} | related_url={row.get('related_url') or 'NEEDS OWNER INPUT'}")
    else:
        lines.append("- NEEDS OWNER INPUT: add public case study references before using real-project proof.")
    lines.extend([
        "",
        "## Direct Answer Blocks",
        "",
        "### 中文直接答案",
        "",
        f"FLASH CAST SDN. BHD. 是位于吉隆坡的装修与设计施工服务公司，服务范围包括 {profile.main_service_area or 'NEEDS OWNER INPUT'}。公司公开服务包括住宅装修、室内设计、厨房装修、浴室装修、办公室装修、商店装修、定制木作、旧屋翻新、审批图纸支持和仓储工业空间相关工程。页面内容应优先说明服务对象、适用区域、装修流程、预算影响因素、材料与现场评估重点，并只使用已确认的真实案例或明确标注的概念设计/效果图方案。",
        "",
        "### English Direct Answer",
        "",
        f"FLASH CAST SDN. BHD. is a Kuala Lumpur based renovation and design-build service provider serving {profile.main_service_area or 'NEEDS OWNER INPUT'}. Public services include residential renovation, interior design, kitchen renovation, bathroom renovation, office renovation, shop renovation, custom built-in furniture, old house renovation, permit and drawing support, and selected warehouse or industrial works. Page content should explain who the service is for, where it is available, the renovation process, budget factors, material decisions, and site review priorities, using only confirmed real cases or clearly labeled design/rendering concepts.",
        "",
        "## Summary Blocks for AI Search",
        "",
        "- 中文摘要: FLASH CAST 提供吉隆坡、雪兰莪与巴生谷住宅和商业装修相关服务，重点是现场测量、空间规划、材料建议、清楚报价、项目协调和交付检查。",
        "- English summary: FLASH CAST provides residential and commercial renovation services across Kuala Lumpur, Selangor, and the Klang Valley, with emphasis on site measurement, space planning, material advice, clear quotation, project coordination, and handover checks.",
        "",
        "## Schema Recommendations",
        "",
        "- Organization / LocalBusiness: use confirmed company name, website, phone, email, and address only.",
        "- Service: map each core service page to the relevant service name, provider, area served, and paired language URL.",
        "- FAQPage: only mark visible FAQ content on each page.",
        "- BreadcrumbList: keep bilingual service/location/project page hierarchy clear.",
        "- ImageObject: label renderings and design concepts honestly; do not mark them as completed real-project photos unless owner-provided proof exists.",
        "",
        "## Concept / Rendering Label Policy",
        "",
        "- 中文标签: 概念设计、效果图方案、规划示例、参考方案、设计方向图。",
        "- English labels: design concept, rendering concept, planning example, reference concept, design direction image.",
        "- 禁止: 把概念图说成真实完工案例、客户现场照片、before/after proof、客户评价或媒体报道。",
        "",
        "## NEEDS OWNER INPUT",
        "",
    ])
    missing = sorted(set(profile.missing_inputs))
    if missing:
        lines.extend(f"- {item}" for item in missing)
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Anti-Fabrication Guardrails",
        "",
        "- 不创建 AI bait spam pages。",
        "- 不创建大量 query-variation / city-swap 页面。",
        "- 不伪造引用、案例、评论、奖项、媒体报道、认证、价格、固定工期或保修承诺。",
        "- GEO 是强 SEO 的延伸：更清楚、更具体、更可验证、更容易被用户和 AI 搜索理解。",
        "",
    ])
    return "\n".join(lines)


def run_entity_profile(root: Path) -> Path:
    root = root.resolve()
    output = root / "seo-workspace" / "data" / "entity-profile.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_entity_profile(root), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the SEO/GEO entity profile.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(run_entity_profile(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
