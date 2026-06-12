#!/usr/bin/env python3
"""Generate image-rich content packages with source logs and publishing gates."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

try:
    from .content_system import build_rows, write_content_system_map
except ImportError:  # pragma: no cover
    from content_system import build_rows, write_content_system_map


SOURCE_LOG_FIELDS = [
    "date_added",
    "target_url",
    "source_type",
    "source_title",
    "source_url",
    "publisher",
    "published_or_accessed_date",
    "usage_note",
    "claim_boundary",
]


@dataclass
class ResearchSource:
    source_type: str
    source_title: str
    source_url: str
    publisher: str
    published_or_accessed_date: str
    usage_note: str
    claim_boundary: str = "general guidance only; not a FLASH CAST business claim"

    @classmethod
    def from_cli(cls, value: str) -> "ResearchSource":
        parts = [part.strip() for part in value.split("|")]
        parts += [""] * (6 - len(parts))
        return cls(
            source_type=parts[0] or "external",
            source_title=parts[1] or "NEEDS LIVE SEARCH TITLE",
            source_url=parts[2] or "NEEDS LIVE SEARCH URL",
            publisher=parts[3] or "NEEDS LIVE SEARCH PUBLISHER",
            published_or_accessed_date=parts[4] or dt.date.today().isoformat(),
            usage_note=parts[5] or "Use for current general guidance only.",
        )

    @classmethod
    def from_log_row(cls, row: dict[str, str]) -> "ResearchSource":
        return cls(
            source_type=row.get("source_type", "") or "external",
            source_title=row.get("source_title", "") or row.get("source_url", "") or "NEEDS LIVE SEARCH TITLE",
            source_url=row.get("source_url", "") or "NEEDS LIVE SEARCH URL",
            publisher=row.get("publisher", "") or "NEEDS LIVE SEARCH PUBLISHER",
            published_or_accessed_date=row.get("published_or_accessed_date", "") or dt.date.today().isoformat(),
            usage_note=row.get("usage_note", "") or "Use for current general guidance only.",
            claim_boundary=row.get("claim_boundary", "") or "general guidance only; not a FLASH CAST business claim",
        )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def append_source_log(root: Path, target_url: str, sources: list[ResearchSource]) -> Path:
    output = root / "seo-workspace" / "data" / "research-source-log.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = read_csv_rows(output)
    today = dt.date.today().isoformat()
    rows = list(existing)
    seen = {(row.get("target_url", ""), row.get("source_url", "")) for row in existing}
    for source in sources:
        key = (target_url, source.source_url)
        if key in seen:
            continue
        rows.append(
            {
                "date_added": today,
                "target_url": target_url,
                "source_type": source.source_type,
                "source_title": source.source_title,
                "source_url": source.source_url,
                "publisher": source.publisher,
                "published_or_accessed_date": source.published_or_accessed_date,
                "usage_note": source.usage_note,
                "claim_boundary": source.claim_boundary,
            }
        )
        seen.add(key)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SOURCE_LOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def valid_source_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def source_log_sources(root: Path, target_urls: set[str]) -> list[ResearchSource]:
    rows = read_csv_rows(root / "seo-workspace" / "data" / "research-source-log.csv")
    sources: list[ResearchSource] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if row.get("target_url", "") not in target_urls:
            continue
        source_url = row.get("source_url", "")
        if not valid_source_url(source_url):
            continue
        key = (row.get("target_url", ""), source_url)
        if key in seen:
            continue
        sources.append(ResearchSource.from_log_row(row))
        seen.add(key)
    return sources


def target_row(root: Path, target_url: str = ""):
    rows = build_rows(root)
    if not rows:
        write_content_system_map(root)
        rows = build_rows(root)
    if target_url:
        for row in rows:
            if row.target_url == target_url or urlsplit(row.target_url).path == target_url:
                return row
    scores = read_csv_rows(root / "seo-workspace" / "data" / "seo-opportunity-scores.csv")
    if scores:
        top_url = scores[0].get("url", "")
        for row in rows:
            if row.target_url == top_url:
                return row
    return rows[0] if rows else None


def slug_from_url(url: str) -> str:
    path = urlsplit(url).path or url
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return slug or "rich-content-package"


def keyword_for_url(root: Path, url: str) -> str:
    path = urlsplit(url).path
    for row in read_csv_rows(root / "seo-workspace" / "data" / "keyword-map.csv"):
        if row.get("target_url") in {url, path} or row.get("current_url") in {url, path}:
            return row.get("keyword", "")
    for row in read_csv_rows(root / "seo-workspace" / "data" / "seo-opportunity-scores.csv"):
        if row.get("url") == url:
            return row.get("keyword", "")
    return ""


def brand_fact(root: Path, label: str, fallback: str = "") -> str:
    path = root / "seo-workspace" / "data" / "brand-profile.md"
    prefix = f"- {label}:"
    if not path.exists():
        return fallback
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip() or fallback
    return fallback


def research_status(page_type: str, sources: list[ResearchSource]) -> str:
    if sources:
        return f"source_log_attached ({len(sources)} source rows)"
    if page_type == "article":
        return "NEEDS LIVE SEARCH: article pages require recent authoritative sources before publish."
    return "optional: use live search only for current design, material, authority, or search policy facts."


def zh_sections(page_type: str) -> list[str]:
    if page_type == "article":
        return ["文章导语", "最新资料摘要", "装修决策要点", "图文步骤", "常见误区", "服务页 CTA", "FAQ"]
    if page_type == "case-study":
        return ["案例事实或概念边界", "空间目标", "设计方案", "材料与视觉方向", "效果图位", "施工/规划说明", "CTA"]
    if page_type == "local":
        return ["区域服务说明", "适合项目类型", "本地规划要点", "服务入口", "概念图位", "FAQ", "CTA"]
    return ["Hero", "快速答案", "服务范围", "规划示例", "流程", "图文内容位", "FAQ", "CTA"]


def en_sections(page_type: str) -> list[str]:
    if page_type == "article":
        return ["Article intro", "Latest-source summary", "Decision factors", "Image-rich steps", "Common mistakes", "Service CTA", "FAQ"]
    if page_type == "case-study":
        return ["Case facts or concept boundary", "Space goals", "Design concept", "Materials and visual direction", "Rendering slots", "Planning notes", "CTA"]
    if page_type == "local":
        return ["Area service context", "Suitable project types", "Local planning notes", "Service entry points", "Concept image slots", "FAQ", "CTA"]
    return ["Hero", "Quick answer", "Service scope", "Planning examples", "Process", "Image-rich blocks", "FAQ", "CTA"]


def image_blocks(page_type: str) -> list[tuple[str, str, str]]:
    if page_type == "article":
        return [
            ("hero explanatory graphic", "文章主题说明图", "article explanatory design concept"),
            ("step diagram", "步骤图 / 检查清单图", "step-by-step planning graphic"),
            ("service CTA visual", "服务咨询 CTA 图", "service consultation CTA visual"),
        ]
    if page_type == "case-study":
        return [
            ("design concept hero", "概念设计主图", "case design concept hero"),
            ("material board", "材料与饰面参考图", "material and finish mood board"),
            ("layout/rendering support", "布局或效果图方案", "layout or rendering concept"),
        ]
    if page_type == "local":
        return [
            ("local service concept", "区域装修服务概念图", "local renovation service concept"),
            ("service type thumbnails", "服务类型缩略图", "service type thumbnails"),
            ("CTA visual", "咨询 CTA 图", "consultation CTA visual"),
        ]
    return [
        ("hero rendering concept", "服务页效果图方案主图", "service page rendering concept"),
        ("section concept image", "分区规划示例图", "section planning example"),
        ("material mood board", "材料 mood board", "material mood board"),
        ("process graphic", "流程说明图", "process graphic"),
    ]


def render_sources(sources: list[ResearchSource], page_type: str) -> str:
    if not sources:
        if page_type == "article":
            return "- NEEDS LIVE SEARCH: 发布前必须补充 2-5 条近期权威来源，并写入 `seo-workspace/data/research-source-log.csv`。"
        return "- 暂无外部来源；当前内容包只使用业主/网站/工作区数据。发布前如加入行业趋势、材料参数、政策或搜索引擎规则，必须联网核查并补 source log。"
    lines = []
    for source in sources:
        lines.append(f"- {source.source_title} | {source.publisher} | {source.source_url} | {source.usage_note}")
    return "\n".join(lines)


def render_image_blocks(page_type: str) -> str:
    lines: list[str] = []
    for index, (slot, zh_name, en_name) in enumerate(image_blocks(page_type), start=1):
        lines.extend(
            [
                f"### Image Block {index}: {slot}",
                "",
                f"- 中文图位：{zh_name}",
                f"- English slot: {en_name}",
                "- 标签：`概念设计 / 效果图方案 / 规划示例` + `design concept / rendering concept / planning example`",
                f"- 中文 alt：FLASH CAST {zh_name}，用于装修内容规划说明",
                f"- English alt: FLASH CAST {en_name} for renovation planning content",
                f"- 图注：此图为规划/效果图方案，不作为真实完工案例或客户照片。",
                f"- Suggested filename: `flash-cast-{slot.replace(' ', '-')}.webp`",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def render_section_plan(page_type: str) -> str:
    zh = "\n".join(f"- {section}" for section in zh_sections(page_type))
    en = "\n".join(f"- {section}" for section in en_sections(page_type))
    return f"""### 中文富文本结构

{zh}

### English Rich-Text Structure

{en}
"""


def render_package(root: Path, row, topic: str, sources: list[ResearchSource]) -> str:
    today = dt.date.today().isoformat()
    brand = brand_fact(root, "Brand name", "FLASH CAST")
    company = brand_fact(root, "Company name", "FLASH CAST SDN. BHD.")
    keyword = keyword_for_url(root, row.target_url)
    title_topic = topic or keyword or row.target_url
    return f"""# Rich Content Publishing Package

- 生成日期: {today}
- 执行模式: draft-only / publishing package
- 品牌: {brand}
- 公司: {company}
- 目标页面: `{row.target_url}`
- 配对页面: `{row.paired_url}`
- 页面类型: {row.page_type}
- 内容优先级: {row.content_priority}
- 目标关键词: {keyword or 'NEEDS OWNER INPUT / infer from page intent'}
- 主题: {title_topic}
- 研究状态: {research_status(row.page_type, sources)}
- 执行状态: 等待业主审核和明确执行指令

## 今日决策

本包用于把页面内容升级为可审核的图文富文本发布包：包含最新资料 source log、双语正文结构、图片/效果图位、alt、图注、CTA、schema 和发布门槛。它不是 live 发布，不登录 CMS，不修改网站源码。

## 最新资料 / Source Log

{render_sources(sources, row.page_type)}

## 中文页面建议文案

页面应围绕 `{title_topic}` 组织为清晰的图文内容。中文正文要先回答用户最关心的问题，再说明服务范围、规划思路、图文示例、FAQ 和咨询路径。涉及效果图、概念图、材料图或案例替代图时，必须写明 `概念设计 / 效果图方案 / 规划示例`。

## 英文页面建议文案

The page should be structured as an image-rich publishing package for `{title_topic}`. English copy should answer the main user question early, then explain scope, planning logic, visual examples, FAQ, and consultation path. Generated visuals must be labeled as `design concept / rendering concept / planning example`.

## 富文本结构 / Rich-Text Structure

{render_section_plan(row.page_type)}

## 图文内容块 / Image-Rich Blocks

{render_image_blocks(row.page_type)}

## Bilingual SEO Fields

- 中文 SEO title：{brand} | {title_topic} | 装修设计与规划
- English SEO title: {brand} | {title_topic} | Renovation Design and Planning
- 中文 meta description：围绕 {title_topic} 的装修内容包，包含服务说明、规划示例、效果图方案、FAQ、内链和咨询 CTA。
- English meta description: Image-rich renovation content package for {title_topic}, including service copy, planning examples, rendering concepts, FAQ, internal links, and CTA.
- 中文 slug：`{urlsplit(row.paired_url).path if '/zh/' in row.paired_url else urlsplit(row.target_url).path}`
- English slug：`{urlsplit(row.target_url).path if '/en/' in row.target_url else urlsplit(row.paired_url).path}`

## Schema 建议

- Page type schema: use `Service`, `Article`, `CollectionPage`, `FAQPage`, `ImageObject`, or `BreadcrumbList` only when matching visible content exists.
- ImageObject: generated images must include concept/rendering labels.
- FAQPage: only mark questions visible on the page.
- Do not add Review, AggregateRating, price, openingHours, award, certification, or warranty schema unless owner-confirmed and visible on page.

## Publishing Field Map

- title
- slug
- excerpt / summary
- rich_text_body
- image_blocks[]: file, alt_zh, alt_en, caption_zh, caption_en, concept_label
- seo_title_zh / seo_title_en
- meta_description_zh / meta_description_en
- faq[]
- internal_links[]
- schema_json
- cta_label / cta_url
- source_log_refs[]

If the website CMS only supports cover image + body + media library, preserve this package as the source of truth and map image blocks into the closest supported fields.

## Owner Review Notes

- NEEDS OWNER INPUT only for factual business claims, final CTA/contact display, exact publishing target, or true case/project proof if the page will say `真实案例`.
- Missing real photos, fixed budgets, fixed timelines, warranties, or reviews do not block this package; use labeled design/rendering concepts.
- External sources support general guidance only. They do not prove FLASH CAST-specific claims.

## QA Checklist

- [ ] Source log exists if latest/current external facts are used.
- [ ] No fake case, fake review, fake price, fake timeline, fake warranty, fake certification, fake award, or fake service area.
- [ ] Generated images are labeled as concept/rendering/planning material.
- [ ] 中文 and English page pair considered.
- [ ] Internal links and CTA point to real site URLs.
- [ ] Schema matches visible page content.
- [ ] Backup, changelog, rollback plan, and pre-publish QA are ready before any live execution.
"""


def write_rich_content_package(
    root: Path,
    *,
    target_url: str = "",
    topic: str = "",
    sources: list[ResearchSource] | None = None,
    use_research_log: bool = True,
) -> Path:
    root = root.resolve()
    sources = sources or []
    row = target_row(root, target_url)
    if row is None:
        raise RuntimeError("No target URL found. Run content-system or provide url-inventory/keyword-map data.")
    if not sources and use_research_log:
        sources = source_log_sources(root, {row.target_url, row.paired_url})
    append_source_log(root, row.target_url, sources)
    output = root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-{slug_from_url(row.target_url)}-rich-content-package.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_package(root, row, topic, sources), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an image-rich content publishing package.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="", help="Target URL or path. Defaults to top opportunity.")
    parser.add_argument("--topic", default="", help="Optional content topic override.")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source row as type|title|url|publisher|date|usage note. Repeatable.",
    )
    parser.add_argument("--no-use-research-log", action="store_true", help="Do not auto-attach existing research-source-log rows for the target page.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = [ResearchSource.from_cli(value) for value in args.source]
    print(write_rich_content_package(Path(args.root), target_url=args.target_url, topic=args.topic, sources=sources, use_research_log=not args.no_use_research_log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
