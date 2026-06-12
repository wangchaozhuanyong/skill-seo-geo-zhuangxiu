#!/usr/bin/env python3
"""Generate image SEO and visual asset readiness reports."""

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

from visual_brief import build_visual_briefs, write_visual_briefs  # noqa: E402


@dataclass
class ImageIssue:
    severity: str
    check: str
    url: str
    detail: str
    recommendation: str


@dataclass
class ImageSeoAudit:
    rows: list[dict[str, str]]
    issues: list[ImageIssue] = field(default_factory=list)

    def add(self, severity: str, check: str, url: str, detail: str, recommendation: str) -> None:
        self.issues.append(ImageIssue(severity, check, url, detail, recommendation))

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def review_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "review")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def as_int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def is_generic_alt(value: str) -> bool:
    generic = {"image", "photo", "picture", "renovation", "装修", "图片", "照片", "img"}
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", " ", value or "").strip().lower()
    return normalized in generic or len(normalized) < 8


def schema_has_image(row: dict[str, str]) -> bool:
    return "ImageObject" in {item.strip() for item in row.get("schema_types", "").split(";")}


def audit_images(root: Path) -> ImageSeoAudit:
    root = root.resolve()
    rows = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    entity_text = read_text(root / "seo-workspace" / "data" / "entity-profile.md")
    briefs = build_visual_briefs(root)
    audit = ImageSeoAudit(rows=rows)
    for row in rows:
        url = row.get("url", "")
        page_type = row.get("page_type", "")
        image_count = as_int(row.get("image_count", "0"))
        missing_alt = as_int(row.get("missing_alt_count", "0"))
        if missing_alt:
            audit.add("error", "missing alt", url, f"Missing alt count: {missing_alt}.", "Add specific bilingual alt text that describes the visible image and page context.")
        if image_count == 0 and page_type in {"service", "local", "article", "case-study", "case-study-hub"}:
            audit.add("review", "hero image / service image / case image", url, "No image detected in current inventory.", "Prepare a clearly labeled concept/rendering image or owner-approved real project photo.")
        if image_count > 0 and missing_alt == 0:
            audit.add("review", "generic alt", url, "Inventory confirms alt is not missing, but generic alt text cannot be verified from summary data.", "Run page-level image crawl before publishing image SEO changes.")
        if schema_has_image(row) and image_count == 0:
            audit.add("warning", "ImageObject schema", url, "ImageObject schema is present but inventory detected no page images.", "Confirm schema reflects visible page images before publishing.")
    audit.add(
        "review",
        "image size / width-height / lazy loading",
        "inventory",
        "Current url-inventory.csv does not contain image byte size, width, height, or loading attributes.",
        "Add a page-level image crawl/source inspection before execution to validate size, dimensions, and lazy loading.",
    )
    if "概念设计" not in entity_text or "rendering concept" not in entity_text:
        audit.add("warning", "concept/rendering label", "entity-profile", "Concept/rendering label policy not found.", "Add labels before using generated visual planning assets.")
    if not briefs:
        audit.add("review", "visual asset brief", "visual-asset-briefs.csv", "No visual asset briefs generated.", "Review whether existing pages already have sufficient images.")
    return audit


def render_image_report(root: Path, audit: ImageSeoAudit) -> str:
    today = dt.date.today().isoformat()
    total_pages = len(audit.rows)
    total_images = sum(as_int(row.get("image_count", "0")) for row in audit.rows)
    missing_alt = sum(as_int(row.get("missing_alt_count", "0")) for row in audit.rows)
    pages_without_images = sum(1 for row in audit.rows if as_int(row.get("image_count", "0")) == 0)
    visual_briefs = build_visual_briefs(root)
    lines = [
        "# Image SEO / Visual Asset Readiness Report",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: draft-only / report-only",
        "- 输出文件: `seo-workspace/data/visual-asset-briefs.csv`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天做图片 SEO 与视觉资产模块，而不是随机写文章。原因是装修网站的服务理解、图片搜索、AI 搜索引用和转化都依赖清楚的视觉资产、alt text、文件名、图片 schema、加载体验和真实/概念标签边界。先建立审计和视觉 brief，可以避免把概念图误当真实项目照，也能为后续服务页优化准备可执行图片清单。",
        "",
        "## Image SEO Summary",
        "",
        f"- Pages audited: {total_pages}",
        f"- Images detected by inventory: {total_images}",
        f"- Pages without detected images: {pages_without_images}",
        f"- Missing alt count: {missing_alt}",
        f"- Visual asset briefs generated: {len(visual_briefs)}",
        f"- Errors: {audit.error_count}",
        f"- Warnings: {audit.warning_count}",
        f"- Review items: {audit.review_count}",
        "",
        "## Checks Covered",
        "",
        "- missing alt",
        "- generic alt",
        "- image size",
        "- width/height",
        "- lazy loading",
        "- hero image",
        "- service image",
        "- case image",
        "- concept/rendering label",
        "- file names",
        "- image sitemap readiness",
        "",
        "## Issues",
        "",
    ]
    if audit.issues:
        for issue in audit.issues:
            lines.append(f"- [{issue.severity}] {issue.check} | {issue.url}: {issue.detail} 建议: {issue.recommendation}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Visual Asset Plan",
        "",
    ])
    for item in visual_briefs[:10]:
        lines.append(
            f"- `{item.target_page}` | {item.asset_type} | {item.concept_label_zh} / {item.concept_label_en} | file `{item.file_name_suggestion}`"
        )
    if len(visual_briefs) > 10:
        lines.append(f"- Additional briefs in CSV: {len(visual_briefs) - 10}")
    lines.extend([
        "",
        "## Owner Review Notes",
        "",
        "- NEEDS OWNER INPUT: 如果图片要作为真实完工案例、真实本地商家照片、before/after proof 或客户现场照片使用，必须由业主提供真实证明。",
        "- 不需要真实项目照片才能继续页面级 SEO/GEO；可以使用明确标注的概念设计、效果图方案、规划示例或 design concept。",
        "- 当前不生成图片文件，只生成图片 SEO 审计和视觉 brief。",
        "- 发布前需要页面级图片抓取或源码检查，确认尺寸、width/height、lazy loading、真实 alt 和图片 sitemap 状态。",
        "",
        "## QA Checklist",
        "",
        "- [ ] 每张非装饰图片都有具体、自然、不堆关键词的 alt text。",
        "- [ ] 中文页使用中文 alt，英文页使用英文 alt，含必要服务和区域上下文。",
        "- [ ] 文件名使用描述性英文小写短横线，不使用 IMG_1234 或 keyword stuffing。",
        "- [ ] Hero/service/case 图片和页面主题一致。",
        "- [ ] 概念图必须标注 概念设计 / 效果图方案 / design concept / rendering concept。",
        "- [ ] 真实案例图、地图商家图、评价截图、before/after proof 必须有业主真实资料。",
        "- [ ] 发布前确认图片尺寸、width/height、lazy loading、压缩格式和 image sitemap readiness。",
        "",
    ])
    return "\n".join(lines)


def run_image_seo_report(root: Path) -> Path:
    root = root.resolve()
    write_visual_briefs(root)
    audit = audit_images(root)
    output = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-image-seo-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_image_report(root, audit), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate image SEO and visual asset readiness report.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(run_image_seo_report(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
