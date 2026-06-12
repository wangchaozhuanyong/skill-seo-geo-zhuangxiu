#!/usr/bin/env python3
"""Validate multilingual SEO signals for paired /zh and /en pages."""

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

from language_pairs import build_language_pairs, write_language_pairs  # noqa: E402


@dataclass
class MultilingualIssue:
    severity: str
    check: str
    url: str
    message: str
    recommendation: str


@dataclass
class MultilingualValidation:
    pair_rows: list[dict[str, str]]
    issues: list[MultilingualIssue] = field(default_factory=list)

    def add(self, severity: str, check: str, url: str, message: str, recommendation: str) -> None:
        self.issues.append(MultilingualIssue(severity, check, url, message, recommendation))

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def ok(self) -> bool:
        return self.error_count == 0


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def as_rows(pairs) -> list[dict[str, str]]:
    return [pair.as_row() for pair in pairs]


def contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def contains_english_words(text: str) -> bool:
    return bool(re.search(r"\b(renovation|service|design|kitchen|bathroom|quote|planning)\b", text, flags=re.I))


def latest_content_brief_text(root: Path) -> str:
    briefs = sorted((root / "seo-workspace" / "drafts").glob("*content-brief.md"))
    return read_text(briefs[-1]) if briefs else ""


def validate_multilingual(root: Path) -> MultilingualValidation:
    root = root.resolve()
    pairs_path = root / "seo-workspace" / "data" / "language-pairs.csv"
    if not pairs_path.exists():
        write_language_pairs(root)
    pair_rows = read_csv_rows(pairs_path)
    validation = MultilingualValidation(pair_rows=pair_rows)
    inventory = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    brief_text = latest_content_brief_text(root)

    for row in pair_rows:
        url = row.get("source_url", "")
        if row.get("pair_exists") != "yes":
            validation.add("error", "/zh and /en URL pair", url, "Missing paired language URL.", "Create or map the paired URL before publishing language-specific optimization.")
        if row.get("source_hreflang_pair") != "yes":
            validation.add("warning", "hreflang alternate reference", url, "Source page does not show confirmed hreflang alternate pair in inventory.", "Add reciprocal hreflang alternates.")
        if row.get("paired_hreflang_pair") and row.get("paired_hreflang_pair") != "yes":
            validation.add("warning", "hreflang alternate reference", row.get("paired_url", ""), "Paired page does not show confirmed hreflang alternate pair in inventory.", "Add reciprocal hreflang alternates.")
        if row.get("source_canonical_self") == "no":
            validation.add("error", "canonical cross-language", url, "Source canonical is not self-referencing.", "Do not canonicalize /zh pages to /en pages or the reverse.")
        if row.get("paired_canonical_self") == "no":
            validation.add("error", "canonical cross-language", row.get("paired_url", ""), "Paired canonical is not self-referencing.", "Do not canonicalize /zh pages to /en pages or the reverse.")
        if row.get("source_in_sitemap") == "no" or row.get("paired_in_sitemap") == "no":
            validation.add("warning", "sitemap bilingual coverage", url, "One side of the language pair is not confirmed in sitemap.", "Include both /zh and /en URLs in sitemap when indexable.")
        if row.get("service_slug_pair_consistent") == "no":
            validation.add("warning", "service slug pair consistency", url, "Service slug differs between /zh and /en pair.", "Keep service slug pair consistent unless an intentional legacy alias is redirected/canonicalized.")

    zh_rows = [row for row in inventory if row.get("language") == "zh" or "/zh/" in row.get("url", "")]
    en_rows = [row for row in inventory if row.get("language") == "en" or "/en/" in row.get("url", "")]
    if zh_rows and not contains_chinese(brief_text):
        validation.add("warning", "Chinese page language", "latest content brief", "No Chinese copy detected in latest brief.", "Chinese page drafts should include Chinese visible copy.")
    if en_rows and not contains_english_words(brief_text):
        validation.add("warning", "English page language", "latest content brief", "No English renovation/service copy detected in latest brief.", "English page drafts should include English visible copy.")
    if "Bilingual SEO Title" not in brief_text or "Bilingual Meta Description" not in brief_text:
        validation.add("warning", "bilingual meta matching", "latest content brief", "Latest brief does not include bilingual title/meta sections.", "Prepare title/meta for both /zh and /en pages together.")
    return validation


def render_multilingual_report(root: Path, validation: MultilingualValidation) -> str:
    today = dt.date.today().isoformat()
    pair_count = len(validation.pair_rows)
    complete_pairs = sum(1 for row in validation.pair_rows if row.get("pair_exists") == "yes")
    zh_count = sum(1 for row in validation.pair_rows if row.get("source_language") == "zh")
    en_count = sum(1 for row in validation.pair_rows if row.get("source_language") == "en")
    lines = [
        "# Multilingual SEO / Hreflang Report",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: draft-only / report-only",
        "- 输出文件: `seo-workspace/data/language-pairs.csv`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天做多语言 SEO 模块，而不是随机写文章。原因是 Flash Cast 网站有 `/zh` 和 `/en` 双语结构，搜索引擎需要清楚理解语言配对、hreflang、canonical、sitemap 和双语 meta。先建立自动校验，可以避免中文页和英文页互相抢索引、canonical 跨语言错误、sitemap 漏收录和服务 slug 配对混乱。",
        "",
        "## Multilingual Summary",
        "",
        f"- Language-pair rows: {pair_count}",
        f"- Complete pairs: {complete_pairs}",
        f"- Source zh rows: {zh_count}",
        f"- Source en rows: {en_count}",
        f"- Errors: {validation.error_count}",
        f"- Warnings: {validation.warning_count}",
        f"- Status: {'PASS' if validation.ok else 'REVIEW REQUIRED'}",
        "",
        "## Checks Covered",
        "",
        "- /zh 和 /en URL pair",
        "- hreflang self reference / inventory-level language signal",
        "- hreflang alternate reference",
        "- canonical 不跨语言错误",
        "- sitemap 是否包含双语 URL",
        "- 中文页面是否中文",
        "- 英文页面是否英文",
        "- meta 是否双语匹配",
        "- service slug pair 是否一致",
        "",
        "## Issues",
        "",
    ]
    if validation.issues:
        for issue in validation.issues:
            lines.append(f"- [{issue.severity}] {issue.check} | {issue.url}: {issue.message} 建议: {issue.recommendation}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Owner Review Notes",
        "",
        "- 如果某个 `/zh` 或 `/en` 页面未来只做单语，必须由业主明确确认；默认继续双语配对。",
        "- 如果存在历史别名 URL，应使用 redirect/canonical 策略，不要让多语言别名互相竞争。",
        "- 双语 meta 不需要逐字翻译，但必须匹配同一个服务意图、区域和 CTA。",
        "",
        "## QA Checklist",
        "",
        "- [ ] 每个 indexable `/zh` 页面都有对应 `/en` 页面。",
        "- [ ] 每个 indexable `/en` 页面都有对应 `/zh` 页面。",
        "- [ ] hreflang 至少包含 self 和 alternate，并保持互相指向。",
        "- [ ] canonical 指向自身，不跨语言 canonical。",
        "- [ ] sitemap 同时包含双语 URL。",
        "- [ ] 中文页主要内容为中文，英文页主要内容为英文。",
        "- [ ] 中文和英文 SEO title/meta 对应同一页面意图。",
        "- [ ] 服务页 slug 配对一致；历史别名需明确 redirect/canonical。",
        "",
    ])
    return "\n".join(lines)


def run_multilingual_report(root: Path) -> Path:
    root = root.resolve()
    write_language_pairs(root)
    validation = validate_multilingual(root)
    output = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-multilingual-seo-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_multilingual_report(root, validation), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate multilingual SEO and hreflang signals.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(run_multilingual_report(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
