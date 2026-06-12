#!/usr/bin/env python3
"""Build the full content production and publishing automation map."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path

try:
    from .hreflang import expected_pair_url
except ImportError:  # pragma: no cover
    from hreflang import expected_pair_url


CONTENT_SYSTEM_FIELDS = [
    "target_url",
    "paired_url",
    "language",
    "page_type",
    "content_priority",
    "content_package",
    "latest_research_policy",
    "rich_media_slots",
    "concept_label_required",
    "allowed_source_types",
    "publish_mode",
    "live_publish_gate",
    "automation_cadence",
    "owner_input_required",
]


@dataclass
class ContentSystemRow:
    target_url: str
    paired_url: str
    language: str
    page_type: str
    content_priority: str
    content_package: str
    latest_research_policy: str
    rich_media_slots: str
    concept_label_required: str
    allowed_source_types: str
    publish_mode: str
    live_publish_gate: str
    automation_cadence: str
    owner_input_required: str

    def as_dict(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in CONTENT_SYSTEM_FIELDS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def language_from_url(url: str) -> str:
    if "/zh/" in url or url.rstrip("/").endswith("/zh"):
        return "zh"
    if "/en/" in url or url.rstrip("/").endswith("/en"):
        return "en"
    return ""


def priority_for_page(page_type: str) -> str:
    if page_type in {"service", "service-hub", "home", "conversion"}:
        return "high"
    if page_type in {"local", "case-study-hub", "case-study"}:
        return "medium-high"
    if page_type == "article":
        return "medium"
    return "review"


def content_package_for_page(page_type: str) -> str:
    packages = {
        "home": "brand positioning, service entry points, proof-safe trust blocks, bilingual CTA, FAQ, schema",
        "service-hub": "service selector, service groups, comparison copy, FAQ, internal links, CTA, ItemList schema",
        "service": "bilingual service copy, scope blocks, process, FAQ, internal links, CTA, Service schema, image prompts",
        "local": "verified area context, service availability, local internal links, FAQ, CTA, no city-swap doorway copy",
        "article": "latest-source research brief, educational article, FAQ, service CTA, citations/source log, concept graphics",
        "case-study-hub": "case index, project filters, proof boundaries, concept placeholders when proof is unavailable",
        "case-study": "owner-approved case facts or clearly labeled design concept, scope, materials, image captions, CTA",
        "conversion": "quote/contact copy, form guidance, trust notes, privacy-safe CTA, no invented offers",
    }
    return packages.get(page_type, "page copy, FAQ, internal links, image alt text, CTA, schema review")


def latest_research_policy_for_page(page_type: str) -> str:
    if page_type == "article":
        return "required before drafting; use research-search/research-discovery, then research-intake or latest-research source log"
    if page_type in {"service", "service-hub", "home"}:
        return "optional for current design/material guidance; use research-search/research-discovery when current facts are needed; do not copy competitors"
    if page_type == "local":
        return "use only to verify official area or authority facts; search candidates must be checked with official sources; avoid unsupported location claims"
    if page_type == "case-study":
        return "not a substitute for project proof; use only for general material or design context"
    return "optional; cite sources when external facts are used"


def rich_media_slots_for_page(page_type: str) -> str:
    if page_type in {"home", "service-hub"}:
        return "hero concept image; service category thumbnails; process diagram; CTA visual"
    if page_type == "service":
        return "hero rendering concept; section concept image; material mood board; process graphic; FAQ support graphic"
    if page_type == "article":
        return "hero explanatory graphic; step-by-step diagram; checklist image; service CTA image"
    if page_type == "case-study":
        return "real owner-approved photos if available; otherwise labeled design concept/rendering concept; material board"
    if page_type == "local":
        return "local service concept image; service area map-style graphic; project-type thumbnails"
    if page_type == "conversion":
        return "quote process graphic; contact CTA image; trust/scope checklist visual"
    return "hero image; support image; alt text; caption"


def source_types_for_page(page_type: str) -> str:
    base = "owner facts; website data; services.md; service-areas.csv; keyword-map.csv; internal-links.csv"
    if page_type == "article":
        return f"{base}; authoritative external sources; official guidance; manufacturer documentation"
    if page_type in {"local", "approval"}:
        return f"{base}; official authority pages only for approval or area facts"
    return f"{base}; external sources only for general education or current design/material context"


def owner_input_for_page(page_type: str) -> str:
    common = "final CTA/contact display; unsupported factual claims before publish"
    if page_type == "case-study":
        return f"{common}; real project proof only if presented as completed case"
    if page_type == "local":
        return f"{common}; any unverified service area or local office claim"
    if page_type == "article":
        return f"{common}; no owner input needed for general educational draft unless business claims are added"
    if page_type == "conversion":
        return f"{common}; form fields, offer wording, privacy/contact handling"
    return f"{common}; warranty, price, timeline, certifications, awards, reviews if mentioned"


def build_rows(root: Path) -> list[ContentSystemRow]:
    inventory = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    if not inventory:
        inventory = [
            {
                "url": row.get("target_url") or row.get("current_url", ""),
                "language": language_from_url(row.get("target_url") or row.get("current_url", "")),
                "page_type": row.get("page_type", ""),
            }
            for row in read_csv_rows(root / "seo-workspace" / "data" / "keyword-map.csv")
        ]

    rows: list[ContentSystemRow] = []
    for item in inventory:
        url = item.get("url", "")
        if not url:
            continue
        page_type = item.get("page_type", "")
        rows.append(
            ContentSystemRow(
                target_url=url,
                paired_url=expected_pair_url(url),
                language=item.get("language") or language_from_url(url),
                page_type=page_type,
                content_priority=priority_for_page(page_type),
                content_package=content_package_for_page(page_type),
                latest_research_policy=latest_research_policy_for_page(page_type),
                rich_media_slots=rich_media_slots_for_page(page_type),
                concept_label_required="yes for generated renderings, concepts, planning examples, and placeholder visuals",
                allowed_source_types=source_types_for_page(page_type),
                publish_mode="draft by default; pr/staging/live only after owner-approved execution",
                live_publish_gate="scheduled-publish-authorization + scheduled-publish-runner + scheduled-publish-orchestrator + scheduled-publish-postrun + website-publish-adapter + publish-approved-executor simulation + publish-implementation-package + publish-operator-package + publish-execution-receipt + backup + QA pass + changelog + rollback plan + explicit live confirmation",
                automation_cadence="daily draft generation; scheduled publish-prep only through validated authorization profile, ready per-window run request, safe orchestrator, and postrun review",
                owner_input_required=owner_input_for_page(page_type),
            )
        )
    return rows


def write_content_system_map(root: Path) -> Path:
    root = root.resolve()
    rows = build_rows(root)
    output = root / "seo-workspace" / "data" / "content-publishing-system-map.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONTENT_SYSTEM_FIELDS)
        writer.writeheader()
        writer.writerows(row.as_dict() for row in rows)
    return output


def render_report(rows: list[ContentSystemRow]) -> str:
    today = dt.date.today().isoformat()
    page_type_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    for row in rows:
        page_type_counts[row.page_type or "unknown"] = page_type_counts.get(row.page_type or "unknown", 0) + 1
        priority_counts[row.content_priority] = priority_counts.get(row.content_priority, 0) + 1

    lines = [
        "# Content Production and Publishing Automation System",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: planning / draft-only",
        "- 输出状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天把 skill 升级为可规划全站内容生产、最新资料研究、图文/效果图内容包、发布前 QA 和定时自动化的工作流，而不是只生成单篇文章。",
        "",
        "## Coverage",
        "",
        f"- URL rows mapped: {len(rows)}",
    ]
    for page_type, count in sorted(page_type_counts.items()):
        lines.append(f"- {page_type}: {count}")
    lines.extend(["", "## Priority Mix", ""])
    for priority, count in sorted(priority_counts.items()):
        lines.append(f"- {priority}: {count}")
    lines.extend(
        [
            "",
            "## What The Skill Can Produce",
            "",
            "- 最新资料研究：对文章、材料趋势、官方政策、行业新闻或搜索引擎规则，先用 `research-search` / `research-discovery` 生成候选，再用 `research-intake` / `latest-research` 保存 source log；不得复制竞品内容。",
            "- 图文内容：为服务页、文章、案例、区域页、首页、报价页生成正文、FAQ、内链、CTA、schema、图片 alt、图注和富文本结构。",
            "- 单页内容工作室：用 `content-studio --target-url <url> --pipeline rich-content|publish-prep` 一次生成指定页面的研究候选、富文本图文包、本地编辑器、媒体/效果图计划、service-pattern 包和发布准备交接。",
            "- 效果图方案：可为装修页面生成 design concept / rendering concept / planning example，用作设计效果图和规划说明。",
            "- 真实案例编辑：只有业主提供真实项目事实时才写成 completed project；缺少真实证明时可转为清楚标注的设计概念或效果图方案。",
            "- 发布执行：默认 draft；执行前必须有业主批准、QA、备份、changelog、rollback plan、允许的 CMS/source 路径，并通过 `scheduled-publish-authorization`、`scheduled-publish-runner`、`scheduled-publish-orchestrator`、`scheduled-publish-postrun`、`website-publish-adapter`、`publish-approved-executor`、`publish-implementation-package`、`publish-operator-package` 和 `publish-execution-receipt` 本地门禁。",
            "- 定时自动化：每天可自动生成一个最高价值 SEO/GEO 草案；固定时间 publish-prep 只允许在精确授权 profile 存在、校验通过、本次 run request ready、safe orchestrator 放行且 postrun 复盘完成时执行下一步。",
            "",
            "## Publishing Boundaries",
            "",
            "- 不自动编造真实案例、客户评价、价格、固定工期、保修期限、资质、奖项或服务区域。",
            "- 不把 AI 生成效果图、概念图或规划示例写成真实完工照片。",
            "- 不在无人值守自动化里登录 CMS、修改生产页面或提交搜索平台，除非授权 profile 明确允许该 exact action。",
            "- 普通装修页面不得使用 Google Indexing API；索引提交只能按搜索引擎政策执行。",
            "",
            "## Next Implementation Step",
            "",
            "1. 配置 CMS/admin 发布路径和授权 profile。",
            "2. 为富文本页面确认网站实际字段：正文 HTML/Markdown、图片数组、图注、alt、SEO 字段、schema 字段。",
            "3. 把 daily automation 从 draft-only 升级为可选的 approved queue：先生成，后审核，再执行。",
            "4. 对每次 live 执行跑 QA、生成备份、changelog 和 rollback plan。",
            "",
            "## 执行状态",
            "",
            "等待业主审核和明确执行指令。本报告只生成系统地图，不发布、不登录 CMS、不修改 live/source 页面。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_content_system_report(root: Path) -> Path:
    root = root.resolve()
    rows = build_rows(root)
    output = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-publishing-system-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(rows), encoding="utf-8")
    return output


def run_content_system(root: Path) -> tuple[Path, Path]:
    return write_content_system_map(root), write_content_system_report(root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the content production and publishing automation map.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_path, report_path = run_content_system(Path(args.root))
    print(data_path)
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
