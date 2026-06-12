#!/usr/bin/env python3
"""Pre-publish QA checks for SEO/GEO content and page changes."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

try:
    from .hreflang import expected_pair_url
except ImportError:  # pragma: no cover
    from hreflang import expected_pair_url


@dataclass
class QaIssue:
    severity: str
    check: str
    target: str
    detail: str
    recommendation: str


@dataclass
class QaResult:
    target_url: str
    paired_url: str = ""
    mode: str = "draft"
    issues: list[QaIssue] = field(default_factory=list)

    def add(self, severity: str, check: str, target: str, detail: str, recommendation: str) -> None:
        self.issues.append(QaIssue(severity, check, target, detail, recommendation))

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")

    @property
    def owner_input_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "owner_input")

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


def row_by_url(rows: list[dict[str, str]], url: str) -> dict[str, str]:
    for row in rows:
        if row.get("url") == url:
            return row
    return {}


def latest_content_text(root: Path, target_url: str = "", paired_url: str = "") -> tuple[Path | None, str]:
    candidates = sorted((root / "seo-workspace" / "drafts").glob("*.md"))
    if not candidates:
        return None, ""
    target_path = urlsplit(target_url).path if target_url else ""
    paired_path = urlsplit(paired_url).path if paired_url else ""
    for path in reversed(candidates):
        text = read_text(path)
        if any(value and value in text for value in (target_url, paired_url, target_path, paired_path)):
            return path, text
    path = candidates[-1]
    return path, read_text(path)


def top_target_url(root: Path) -> str:
    rows = read_csv_rows(root / "seo-workspace" / "data" / "seo-opportunity-scores.csv")
    return rows[0].get("url", "") if rows else ""


def as_int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def verified_locations(root: Path) -> set[str]:
    names: set[str] = set()
    for row in read_csv_rows(root / "seo-workspace" / "data" / "service-areas.csv"):
        if row.get("verified", "").lower() != "yes":
            continue
        for key in ("area", "city", "state_or_region", "country"):
            if row.get(key):
                names.add(row[key].lower())
    return names


def keyword_row_for_url(root: Path, url: str) -> dict[str, str]:
    path = urlsplit(url).path
    for row in read_csv_rows(root / "seo-workspace" / "data" / "keyword-map.csv"):
        if row.get("target_url") in {url, path} or row.get("current_url") in {url, path}:
            return row
    return {}


def scan_forbidden_claims(text: str) -> list[tuple[str, str]]:
    checks = [
        ("no fake ranking promise", r"\b(guaranteed\s+(first|top)|rank\s*#?1|排名第一保证|保证排名|首页保证)\b"),
        ("no fake reviews", r"\b(5[- ]?star|five[- ]?star|五星好评|客户评价[:：]|testimonial[:：])\b"),
        ("no fake price", r"\b(RM\s*\d{2,}|MYR\s*\d{2,}|fixed price|固定价格|保证最低价)\b"),
        ("no fake cases", r"\b(completed real project proof|真实完工证明|before/after proof|客户现场照片)\b"),
    ]
    found: list[tuple[str, str]] = []
    masked = "\n".join(line for line in text.splitlines() if "NEEDS OWNER INPUT" not in line)
    for label, pattern in checks:
        if re.search(pattern, masked, flags=re.I):
            found.append((label, pattern))
    return found


def keyword_stuffing_detected(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    normalized = keyword.lower().strip()
    if len(normalized) < 4:
        return False
    return text.lower().count(normalized) > 8


def cta_present(text: str) -> bool:
    return bool(re.search(r"\b(CTA|quote|quotation|WhatsApp|咨询|报价|获取免费报价)\b", text, flags=re.I))


def internal_links_present(text: str) -> bool:
    return bool(re.search(r"`?/(zh|en)/", text))


def concept_label_present(text: str) -> bool:
    return all(label in text for label in ("概念设计", "rendering concept"))


def schema_valid(root: Path) -> bool:
    report = read_text(root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-schema-report.md")
    return "Errors: 0" in report or "Status: PASS" in report


def file_exists(path: str) -> bool:
    return bool(path and Path(path).exists())


def run_qa(
    root: Path,
    *,
    target_url: str = "",
    mode: str = "draft",
    backup_path: str = "",
    rollback_plan_path: str = "",
) -> QaResult:
    root = root.resolve()
    target_url = target_url or top_target_url(root)
    paired_url = expected_pair_url(target_url)
    result = QaResult(target_url=target_url, paired_url=paired_url, mode=mode)
    inventory = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    target_row = row_by_url(inventory, target_url)
    pair_row = row_by_url(inventory, paired_url) if paired_url else {}
    draft_path, content = latest_content_text(root, target_url, paired_url)
    keyword_row = keyword_row_for_url(root, target_url)

    if not target_row:
        result.add("error", "target page exists", target_url, "Target URL is not in url-inventory.csv.", "Run URL inventory or confirm the target page before execution.")
    else:
        if target_row.get("canonical_self") == "no":
            result.add("error", "no wrong canonical", target_url, "Target canonical is not self-referencing.", "Fix canonical before publishing.")
        if "noindex" in target_row.get("meta_robots", "").lower() or target_row.get("indexable") == "no":
            result.add("error", "no noindex on target page", target_url, "Target page is noindex or not indexable.", "Remove noindex before publishing indexable SEO content.")
        if target_row.get("robots_allowed") == "no":
            result.add("error", "robots allowed", target_url, "robots.txt blocks target page.", "Allow crawling before publishing.")
        if target_row.get("sitemap_included", target_row.get("in_sitemap", "")) == "no":
            result.add("warning", "sitemap included", target_url, "Target page is not confirmed in sitemap.", "Include indexable target page in sitemap.")
        for field, label in (("title", "title present"), ("meta_description", "meta present"), ("h1", "H1 present")):
            if not target_row.get(field):
                result.add("error", label, target_url, f"Missing {field}.", "Add title/meta/H1 before publishing.")
        if as_int(target_row.get("internal_outlinks_count", "0")) < 1:
            result.add("error", "internal links present", target_url, "No internal outlinks detected.", "Add relevant internal links/CTA path.")
        if target_row.get("page_type") == "local" and as_int(target_row.get("word_count", "0")) < 80:
            result.add("error", "no doorway page / no duplicate city swap", target_url, "Local page is very thin.", "Add unique local context or do not publish city page.")

    if paired_url and not pair_row:
        result.add("error", "/zh and /en pair considered", paired_url, "Paired language URL is missing from inventory.", "Update both language versions or explicitly approve single-language scope.")
    elif pair_row and pair_row.get("canonical_self") == "no":
        result.add("error", "/zh and /en pair considered", paired_url, "Paired language canonical is not self-referencing.", "Fix paired page canonical.")

    if not content:
        result.add("error", "content draft present", str(draft_path or "seo-workspace/drafts"), "No draft content found.", "Create or select an approved draft before execution.")
    else:
        for check, pattern in scan_forbidden_claims(content):
            result.add("error", check, str(draft_path), f"Potential unsupported claim matched pattern: {pattern}", "Remove or mark as NEEDS OWNER INPUT with proof before publishing.")
        if keyword_stuffing_detected(content, keyword_row.get("keyword", "")):
            result.add("error", "no keyword stuffing", str(draft_path), "Target keyword appears excessively.", "Rewrite naturally and reduce repetition.")
        if not cta_present(content):
            result.add("error", "CTA present", str(draft_path), "CTA not found in draft.", "Add a clear consultation/quote CTA.")
        if not internal_links_present(content):
            result.add("error", "internal links present", str(draft_path), "No bilingual internal links found in draft.", "Add relevant internal links.")
        if not concept_label_present(content):
            result.add("owner_input", "concept/rendering clearly labeled", str(draft_path), "Concept/rendering labels are incomplete in latest draft.", "Confirm labels before using concept images.")
        if "NEEDS OWNER INPUT" in content:
            result.add("owner_input", "owner input missing", str(draft_path), "Draft contains NEEDS OWNER INPUT items.", "Owner must review these factual claims before publishing.")

    locations = verified_locations(root)
    location = keyword_row.get("location", "")
    if location:
        parts = [part.strip().lower() for part in location.replace(",", ";").split(";") if part.strip()]
        unsupported = [part for part in parts if part not in locations]
        if unsupported:
            result.add("error", "no unsupported service area", target_url, f"Unsupported locations: {', '.join(unsupported)}.", "Use only verified service areas.")

    if not schema_valid(root):
        result.add("error", "schema valid", "schema-report", "Schema report is missing or has validation errors.", "Run schema validator and resolve errors before publishing.")

    if mode == "live":
        if not file_exists(backup_path):
            result.add("error", "backup exists before live", backup_path or "backup_path", "Live mode requires an existing backup.", "Create backup before live execution.")
        if not file_exists(rollback_plan_path):
            result.add("error", "rollback plan exists before live", rollback_plan_path or "rollback_plan_path", "Live mode requires an existing rollback plan.", "Create rollback plan before live execution.")
    else:
        result.add("owner_input", "backup exists before live", "draft mode", "Backup is required only before live execution.", "Create backup after owner approves execution and before live change.")
        result.add("owner_input", "rollback plan exists before live", "draft mode", "Rollback plan is required only before live execution.", "Create rollback plan after owner approves execution and before live change.")
    return result


def render_qa_report(result: QaResult) -> str:
    today = dt.date.today().isoformat()
    lines = [
        "# Pre-Publish SEO/GEO QA Report",
        "",
        f"- 生成日期: {today}",
        f"- 执行模式: {result.mode}",
        f"- Target URL: `{result.target_url}`",
        f"- Paired URL: `{result.paired_url or 'N/A'}`",
        f"- Status: {'PASS' if result.ok else 'FAIL'}",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天做发布前 QA 系统，而不是随机写文章。原因是后续任何批准执行都必须先阻止虚假声明、错误 canonical、noindex、robots 阻塞、schema 错误、未验证区域、关键词堆砌、doorway 页面和缺少回滚方案等高风险问题。",
        "",
        "## QA Summary",
        "",
        f"- Errors: {result.error_count}",
        f"- Warnings: {result.warning_count}",
        f"- NEEDS OWNER INPUT / live-prep notes: {result.owner_input_count}",
        "",
        "## Checks Covered",
        "",
        "- no fake claims",
        "- no fake reviews",
        "- no fake cases",
        "- no fake price",
        "- no fake ranking promise",
        "- no unsupported service area",
        "- no keyword stuffing",
        "- no doorway page",
        "- no duplicate city swap",
        "- no wrong canonical",
        "- no noindex on target page",
        "- robots allowed",
        "- sitemap included",
        "- title/meta/H1 present",
        "- CTA present",
        "- internal links present",
        "- schema valid",
        "- /zh and /en pair considered",
        "- concept/rendering clearly labeled",
        "- backup exists before live",
        "- rollback plan exists before live",
        "",
        "## Issues",
        "",
    ]
    if result.issues:
        for issue in result.issues:
            lines.append(f"- [{issue.severity}] {issue.check} | {issue.target}: {issue.detail} 建议: {issue.recommendation}")
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Exit-Code Policy",
        "",
        "- 严重问题 exit code = 1。",
        "- 只有 owner input 缺失或 live 前准备项提示时 exit code = 0，但必须报告。",
        "",
        "## Owner Review Notes",
        "",
        "- 当前 QA 是预发布检查，不代表已经发布。",
        "- 如果业主批准执行，正式执行前仍需重新跑此 QA，并在 live mode 准备 backup 和 rollback plan。",
        "",
    ])
    return "\n".join(lines)


def write_qa_report(root: Path, result: QaResult) -> Path:
    output = root.resolve() / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-prepublish-qa-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_qa_report(result), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pre-publish SEO/GEO QA.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="", help="Target URL. Defaults to top opportunity.")
    parser.add_argument("--mode", default="draft", choices=["draft", "live"], help="QA mode.")
    parser.add_argument("--backup-path", default="", help="Required in live mode.")
    parser.add_argument("--rollback-plan-path", default="", help="Required in live mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    result = run_qa(
        root,
        target_url=args.target_url,
        mode=args.mode,
        backup_path=args.backup_path,
        rollback_plan_path=args.rollback_plan_path,
    )
    print(write_qa_report(root, result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
