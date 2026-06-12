#!/usr/bin/env python3
"""Generate a local SEO readiness report without submitting listings."""

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

from citations import load_or_create_citation_opportunities, priority_counts  # noqa: E402


@dataclass
class LocalCheck:
    name: str
    status: str
    detail: str
    recommendation: str


@dataclass
class LocalSeoAudit:
    checks: list[LocalCheck] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str, recommendation: str) -> None:
        self.checks.append(LocalCheck(name, status, detail, recommendation))

    @property
    def pass_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "pass")

    @property
    def review_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "review")

    @property
    def needs_input_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "needs_owner_input")


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


def count_location_pages(inventory: list[dict[str, str]]) -> int:
    return sum(1 for row in inventory if row.get("page_type") == "local" or "/locations/" in row.get("url", ""))


def count_local_schema(inventory: list[dict[str, str]]) -> int:
    return sum(
        1
        for row in inventory
        if any(schema in row.get("schema_types", "") for schema in ("LocalBusiness", "Organization", "Service"))
    )


def unsupported_location_rows(keyword_rows: list[dict[str, str]], area_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    verified = set()
    for row in area_rows:
        if row.get("verified", "").lower() != "yes":
            continue
        for key in ("area", "city", "state_or_region", "country"):
            if row.get(key):
                verified.add(row[key].lower())
    unsupported = []
    for row in keyword_rows:
        location = row.get("location", "")
        if not location:
            continue
        parts = [part.strip().lower() for part in location.replace(",", ";").split(";") if part.strip()]
        if any(part not in verified for part in parts):
            unsupported.append(row)
    return unsupported


def real_review_status(brand_text: str) -> str:
    testimonials = field_value(brand_text, "Real testimonials")
    if not testimonials:
        return "needs_owner_input"
    return "needs_owner_input" if "No published testimonials" in testimonials or "NEEDS OWNER INPUT" in testimonials else "pass"


def build_local_audit(root: Path) -> tuple[LocalSeoAudit, list[dict[str, str]], list[dict[str, str]]]:
    root = root.resolve()
    brand_text = read_text(root / "seo-workspace" / "data" / "brand-profile.md")
    entity_text = read_text(root / "seo-workspace" / "data" / "entity-profile.md")
    area_rows = read_csv_rows(root / "seo-workspace" / "data" / "service-areas.csv")
    inventory = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    keyword_rows = read_csv_rows(root / "seo-workspace" / "data" / "keyword-map.csv")
    citations = load_or_create_citation_opportunities(root)
    unsupported = unsupported_location_rows(keyword_rows, area_rows)

    company = field_value(brand_text, "Company name")
    phone = field_value(brand_text, "Phone")
    email = field_value(brand_text, "Email")
    address = field_value(brand_text, "Address if public")
    gbp = field_value(brand_text, "Google Business Profile")

    audit = LocalSeoAudit()
    audit.add(
        "Google Business Profile data import",
        "needs_owner_input" if not gbp or "NEEDS OWNER INPUT" in gbp else "pass",
        f"GBP field: {gbp or 'missing'}",
        "Owner must provide GBP profile URL/access before GBP-specific optimization, review claims, hours, photos, or category changes.",
    )
    audit.add(
        "Baidu local/map data import if provided",
        "needs_owner_input",
        "No Baidu local/map listing export is present in seo-workspace/data/.",
        "Import only owner-provided Baidu listing details; do not invent map/listing data.",
    )
    nap_ready = bool(company and phone and email and address and company in entity_text and phone in entity_text)
    audit.add(
        "NAP consistency",
        "pass" if nap_ready else "needs_owner_input",
        f"Company={company or 'missing'}; phone={phone or 'missing'}; email={email or 'missing'}; address={address or 'missing'}.",
        "Use exactly the same company name, phone, email, address, and website across footer, schema, GBP, Baidu, and citations.",
    )
    verified_areas = [row for row in area_rows if row.get("verified", "").lower() == "yes"]
    audit.add(
        "service areas",
        "pass" if verified_areas else "needs_owner_input",
        f"Verified service areas: {len(verified_areas)}.",
        "Only use verified service areas; do not add unconfirmed cities for ranking.",
    )
    location_pages = count_location_pages(inventory)
    audit.add(
        "city pages",
        "review" if location_pages else "needs_owner_input",
        f"Location/city page URLs found in inventory: {location_pages}.",
        "Audit city pages for unique local context, service relevance, internal links, and no duplicate doorway patterns.",
    )
    local_schema = count_local_schema(inventory)
    audit.add(
        "local schema",
        "review" if local_schema else "needs_owner_input",
        f"Pages with Organization/LocalBusiness/Service schema signals: {local_schema}.",
        "Use LocalBusiness/Organization and Service schema only with confirmed NAP and service-area facts.",
    )
    audit.add(
        "local CTA",
        "review" if phone else "needs_owner_input",
        f"Phone/WhatsApp source found: {phone or 'missing'}; final WhatsApp CTA still requires owner confirmation before publishing new content.",
        "Keep CTA consistent across local pages; do not change phone/WhatsApp without owner approval.",
    )
    audit.add(
        "reviews only if real",
        real_review_status(brand_text),
        "Brand profile says no published testimonials were found, so reviews must not be used unless owner provides real proof.",
        "Do not create review schema, rating copy, or testimonial blocks without real owner-provided reviews.",
    )
    audit.add(
        "local photos only if real",
        "review",
        "Case-study rows include public project images, but before/after proof and local listing photos require owner review.",
        "Use real photos only when confirmed; otherwise use clearly labeled concept/rendering images outside real-listing proof contexts.",
    )
    audit.add(
        "concept images must be labeled",
        "pass" if "concept" in entity_text.lower() and "概念设计" in entity_text else "review",
        "Entity profile contains concept/rendering label policy.",
        "Label all generated planning visuals as concept/design/rendering material.",
    )
    counts = priority_counts(citations)
    audit.add(
        "citation opportunities",
        "review" if citations else "needs_owner_input",
        f"Citation opportunity rows: {len(citations)}; priority counts: {counts}.",
        "Use this as a review queue only; no automatic platform submissions.",
    )
    audit.add(
        "unsupported locations",
        "pass" if not unsupported else "review",
        f"Unsupported keyword-map locations found: {len(unsupported)}.",
        "Resolve unsupported locations before creating or optimizing location pages.",
    )
    return audit, citations, unsupported


def render_report(root: Path, audit: LocalSeoAudit, citations: list[dict[str, str]], unsupported: list[dict[str, str]]) -> str:
    today = dt.date.today().isoformat()
    lines = [
        "# Local SEO / Citation Readiness Report",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: draft-only / report-only",
        "- 输出文件: `seo-workspace/data/citation-opportunities.csv`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天做本地 SEO 与 citation readiness，而不是随机写文章。原因是装修业务的排名不仅取决于页面内容，还取决于 NAP 一致性、Google Business Profile、地图/目录资料、服务区域、城市页质量、真实评价/照片边界和本地 schema。先建立审计和机会清单，可以避免后续出现错误地址、虚假评价、伪造照片或重复城市 doorway 页面。",
        "",
        "## Local SEO Summary",
        "",
        f"- Pass: {audit.pass_count}",
        f"- Review: {audit.review_count}",
        f"- NEEDS OWNER INPUT: {audit.needs_input_count}",
        "",
        "## Checks",
        "",
    ]
    for check in audit.checks:
        lines.extend([
            f"### {check.name}",
            "",
            f"- Status: {check.status}",
            f"- Detail: {check.detail}",
            f"- Recommendation: {check.recommendation}",
            "",
        ])
    lines.extend([
        "## Citation Opportunities",
        "",
    ])
    for row in citations:
        lines.append(
            f"- {row.get('platform')} | priority={row.get('priority')} | status={row.get('status')} | input={row.get('required_owner_input')}"
        )
    lines.extend([
        "",
        "## Unsupported Locations",
        "",
    ])
    if unsupported:
        for row in unsupported:
            lines.append(f"- {row.get('keyword')} | location={row.get('location')} | url={row.get('target_url') or row.get('current_url')}")
    else:
        lines.append("- None found in keyword-map.csv")
    lines.extend([
        "",
        "## Owner Review Notes",
        "",
        "- NEEDS OWNER INPUT: Google Business Profile URL/access, category, hours, real GBP photos if owner wants GBP optimization.",
        "- NEEDS OWNER INPUT: Baidu local/map listing export or verified listing details if owner wants Baidu local work.",
        "- NEEDS OWNER INPUT: real reviews before using testimonials, star ratings, Review schema, or rating copy.",
        "- NEEDS OWNER INPUT: real local photos before using images as map/listing proof.",
        "- 不需要真实评论或真实照片才能继续页面级 SEO/GEO；但本地目录、地图和 review schema 不能使用虚假资料。",
        "",
        "## QA Checklist",
        "",
        "- [ ] NAP 在网站页脚、schema、GBP、Baidu、本地目录和 citation 表中完全一致。",
        "- [ ] 只使用 service-areas.csv 中 verified=yes 的服务区域。",
        "- [ ] 城市页必须有独特本地内容，不创建 city-swap doorway pages。",
        "- [ ] 不使用虚假评价、星级、客户截图、奖项、媒体引用或伪造照片。",
        "- [ ] 概念图只用于网页规划内容，并明确标注；不要上传为真实本地商家照片。",
        "- [ ] citation 提交前由业主确认平台、账号权限、NAP、营业时间、分类和照片资料。",
        "",
    ])
    return "\n".join(lines)


def run_local_seo_report(root: Path) -> Path:
    root = root.resolve()
    audit, citations, unsupported = build_local_audit(root)
    output = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-local-seo-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(root, audit, citations, unsupported), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a local SEO / citation readiness report.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(run_local_seo_report(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
