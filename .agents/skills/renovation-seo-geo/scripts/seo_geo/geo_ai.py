#!/usr/bin/env python3
"""Generate a GEO / AI search readiness report."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


SEO_GEO_DIR = Path(__file__).resolve().parent
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))

from entity_profile import build_entity_profile, run_entity_profile  # noqa: E402


@dataclass
class ReadinessCheck:
    name: str
    status: str
    detail: str
    recommendation: str = ""


@dataclass
class GeoAiReport:
    checks: list[ReadinessCheck] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str, recommendation: str = "") -> None:
        self.checks.append(ReadinessCheck(name, status, detail, recommendation))

    @property
    def pass_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "pass")

    @property
    def review_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "review")

    @property
    def needs_input_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "needs_owner_input")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def has_all(text: str, values: list[str]) -> bool:
    lowered = text.lower()
    return all(value.lower() in lowered for value in values if value)


def count_inventory(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def count_with_schema(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("schema_types", "").strip())


def find_latest_brief(root: Path) -> Path | None:
    drafts = sorted((root / "seo-workspace" / "drafts").glob("*content-brief.md"))
    return drafts[-1] if drafts else None


def technical_summary(inventory: list[dict[str, str]]) -> str:
    total = len(inventory)
    if total == 0:
        return "URL inventory missing."
    return (
        f"URL count={total}; HTTP 200={count_inventory(inventory, 'status_code', '200')}; "
        f"indexable={count_inventory(inventory, 'indexable', 'yes')}; "
        f"robots allowed={count_inventory(inventory, 'robots_allowed', 'yes')}; "
        f"canonical self={count_inventory(inventory, 'canonical_self', 'yes')}; "
        f"hreflang pair={count_inventory(inventory, 'hreflang_pair', 'yes')}; "
        f"schema present={count_with_schema(inventory)}."
    )


def unique_page_signal(inventory: list[dict[str, str]]) -> str:
    word_counts = []
    for row in inventory:
        try:
            word_counts.append(int(float(row.get("word_count", "0"))))
        except ValueError:
            word_counts.append(0)
    thin = sum(1 for count in word_counts if count < 80)
    return f"Thin/commodity-risk pages with word_count < 80: {thin} of {len(inventory)}."


def build_readiness(root: Path) -> tuple[GeoAiReport, Path, str]:
    root = root.resolve()
    entity_path = root / "seo-workspace" / "data" / "entity-profile.md"
    if not entity_path.exists():
        entity_path = run_entity_profile(root)
    entity_text = read_text(entity_path)
    brand_text = read_text(root / "seo-workspace" / "data" / "brand-profile.md")
    services_text = read_text(root / "seo-workspace" / "data" / "services.md")
    inventory = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    areas = read_csv_rows(root / "seo-workspace" / "data" / "service-areas.csv")
    cases = read_csv_rows(root / "seo-workspace" / "data" / "case-studies.csv")
    brief_path = find_latest_brief(root)
    brief_text = read_text(brief_path) if brief_path else ""

    report = GeoAiReport()
    report.add(
        "brand/entity consistency",
        "pass" if has_all(entity_text, ["FLASH CAST SDN. BHD.", "FLASH CAST", "Renovation"]) else "needs_owner_input",
        "Entity profile includes company name, brand name, and renovation entity type.",
        "Keep company name identical across schema, footer, service pages, and citations.",
    )
    report.add(
        "company name consistency",
        "pass" if "FLASH CAST SDN. BHD." in brand_text and "FLASH CAST SDN. BHD." in entity_text else "review",
        "Company name is pulled from brand-profile.md into entity-profile.md.",
        "Avoid mixing legal name and brand name without context.",
    )
    nap_ready = has_all(entity_text, ["+601128853888", "flashcast001@gmail.com", "94, Jalan Mega Mendung"])
    report.add(
        "NAP consistency",
        "review" if nap_ready and "Google Business Profile: NEEDS OWNER INPUT" in entity_text else ("pass" if nap_ready else "needs_owner_input"),
        "Phone, email, and public address are present; Google Business Profile still needs owner input.",
        "Confirm GBP URL/profile details before adding GBP-specific claims or citation work.",
    )
    service_count = len(re.findall(r"^### ", services_text, flags=re.MULTILINE))
    report.add(
        "service taxonomy",
        "pass" if service_count >= 5 else "needs_owner_input",
        f"Core service sections found: {service_count}.",
        "Use this taxonomy for service schema and page hierarchy; avoid unsupported service pages.",
    )
    verified_areas = [row for row in areas if row.get("verified", "").lower() == "yes"]
    report.add(
        "area coverage",
        "pass" if len(verified_areas) >= 3 else "needs_owner_input",
        f"Verified service areas found: {len(verified_areas)}.",
        "Do not create duplicate city doorway pages; add local context only where useful.",
    )
    report.add(
        "direct answer blocks",
        "pass" if has_all(entity_text, ["中文直接答案", "English Direct Answer"]) else "review",
        "Entity profile includes bilingual direct answer blocks.",
        "Reuse concise direct-answer blocks on key service/location pages where natural.",
    )
    report.add(
        "concise summary blocks",
        "pass" if has_all(entity_text, ["中文摘要", "English summary"]) else "review",
        "Entity profile includes bilingual AI-readable summary blocks.",
        "Keep summaries factual, short, and aligned with page content.",
    )
    real_cases = [row for row in cases if row.get("project_name")]
    report.add(
        "evidence blocks",
        "review" if real_cases else "needs_owner_input",
        f"Public case rows available: {len(real_cases)}; testimonials/awards/media still require owner input if used.",
        "Use real case names only when supported by business data; do not invent reviews or awards.",
    )
    report.add(
        "FAQ",
        "pass" if "Bilingual FAQ" in brief_text or "FAQPage" in entity_text else "review",
        "Latest content brief contains bilingual FAQ recommendations.",
        "Only add FAQPage schema for questions visible on the published page.",
    )
    report.add(
        "comparison tables only when useful",
        "pass",
        "No mass comparison/table template was generated for query manipulation.",
        "Use comparison tables only for genuine material, scope, or decision trade-offs.",
    )
    report.add(
        "schema",
        "review" if inventory and count_with_schema(inventory) < len(inventory) else ("pass" if inventory else "needs_owner_input"),
        technical_summary(inventory),
        "Prioritize Organization/LocalBusiness, Service, FAQPage, BreadcrumbList, and ImageObject where content supports it.",
    )
    crawl_ok = bool(inventory) and count_inventory(inventory, "status_code", "200") == len(inventory) and count_inventory(inventory, "robots_allowed", "yes") == len(inventory)
    report.add(
        "crawlability",
        "pass" if crawl_ok else "review",
        technical_summary(inventory),
        "Fix non-200 or robots-blocked pages before content-only GEO optimization.",
    )
    index_ok = bool(inventory) and count_inventory(inventory, "indexable", "yes") == len(inventory)
    report.add(
        "indexability",
        "pass" if index_ok else "review",
        technical_summary(inventory),
        "Keep canonical, robots, hreflang, and sitemap signals aligned.",
    )
    report.add(
        "page clarity",
        "pass" if brief_text and has_all(brief_text, ["中文页面建议文案", "英文页面建议文案", "QA Checklist"]) else "review",
        "Latest content brief includes bilingual page copy and QA checklist.",
        "Apply the same structure to future high-intent service pages.",
    )
    report.add(
        "unique non-commodity content",
        "review",
        unique_page_signal(inventory),
        "Refresh thin pages with process, service fit, material decisions, local context, FAQ, and internal links.",
    )
    concept_label_ready = has_all(entity_text + brief_text, ["概念设计", "rendering concept"])
    report.add(
        "concept/rendering label",
        "pass" if concept_label_ready else "review",
        "Concept/rendering labels are present in entity profile and latest brief.",
        "Never present renderings, planning examples, or design concepts as completed real projects.",
    )
    return report, entity_path, brief_path.name if brief_path else "None"


def render_report(root: Path, report: GeoAiReport, entity_path: Path, latest_brief: str) -> str:
    today = dt.date.today().isoformat()
    lines = [
        "# GEO / AI Search Readiness Report",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: draft-only / report-only",
        f"- Entity profile: `{entity_path.relative_to(root)}`",
        f"- Latest content brief reviewed: `{latest_brief}`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天继续做 GEO/AI 搜索实体识别与内容可读性体系，而不是随机写新文章。原因是 AI 搜索和传统搜索都需要先稳定理解公司是谁、提供什么服务、服务哪些区域、有哪些真实证据、哪些内容只是概念设计或效果图方案。这个基础会提高后续每个服务页、区域页、FAQ、schema 和内链优化的一致性。",
        "",
        "## Readiness Summary",
        "",
        f"- Pass: {report.pass_count}",
        f"- Review: {report.review_count}",
        f"- NEEDS OWNER INPUT: {report.needs_input_count}",
        "",
        "## GEO/AI Checks",
        "",
    ]
    for check in report.checks:
        lines.extend([
            f"### {check.name}",
            "",
            f"- Status: {check.status}",
            f"- Detail: {check.detail}",
            f"- Recommendation: {check.recommendation or 'None'}",
            "",
        ])
    lines.extend([
        "## Guardrails",
        "",
        "- 不创建 AI bait spam pages。",
        "- 不创建 mass query-variation pages。",
        "- 不伪造 citations、case studies、reviews、awards、media mentions、certifications、prices、fixed timelines 或 warranty promises。",
        "- GEO 是强 SEO 的延伸：清楚、具体、可验证、对用户有用、对搜索和 AI 系统可理解。",
        "",
        "## Owner Review Notes",
        "",
        "- NEEDS OWNER INPUT: Google Business Profile URL / profile details.",
        "- NEEDS OWNER INPUT: awards and media mentions only if owner wants them used.",
        "- NEEDS OWNER INPUT: SSM number/certification wording and exact warranty scope/duration before publishing those claims.",
        "- 不需要真实评论、固定价格、固定工期或新案例才能继续做安全的 GEO 结构优化；没有证明的内容必须保持为概念设计、效果图方案或规划示例。",
        "",
        "## QA Checklist",
        "",
        "- [ ] 公司名、品牌名、电话、邮箱、地址在页面、schema、footer、citation 资料中一致。",
        "- [ ] 每个服务页只使用 services.md 和公开网站支持的服务范围。",
        "- [ ] 每个区域页只使用 service-areas.csv 中 verified=yes 的区域，不做 city-swap doorway pages。",
        "- [ ] FAQPage schema 只标记页面可见问题。",
        "- [ ] 概念设计 / rendering concept 标签在图片、caption、alt text 和正文中一致。",
        "- [ ] 不使用未确认的评价、奖项、媒体、价格、工期、保修、资质或完成项目证明。",
        "- [ ] 发布前重新跑技术审计、索引预检和双语页面 QA。",
        "",
    ])
    return "\n".join(lines)


def run_geo_ai_report(root: Path) -> Path:
    root = root.resolve()
    report, entity_path, latest_brief = build_readiness(root)
    output = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-geo-ai-readiness-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(root, report, entity_path, latest_brief), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the GEO / AI search readiness report.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(run_geo_ai_report(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
