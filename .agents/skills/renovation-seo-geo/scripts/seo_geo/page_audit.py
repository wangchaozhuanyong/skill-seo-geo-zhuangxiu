"""Page-level SEO/GEO audit helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

try:
    from .hreflang import expected_pair_url
except ImportError:  # pragma: no cover
    from hreflang import expected_pair_url


@dataclass
class AuditFinding:
    field: str
    severity: str
    finding: str
    recommendation: str


@dataclass
class PageAudit:
    url: str
    paired_url: str = ""
    page_type: str = ""
    language: str = ""
    keyword: str = ""
    score: int = 0
    findings: list[AuditFinding] = field(default_factory=list)

    @property
    def priority_findings(self) -> list[AuditFinding]:
        return [finding for finding in self.findings if finding.severity in {"high", "medium"}]

    def add(self, field: str, severity: str, finding: str, recommendation: str) -> None:
        self.findings.append(
            AuditFinding(
                field=field,
                severity=severity,
                finding=finding,
                recommendation=recommendation,
            )
        )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def row_by_url(rows: list[dict[str, str]], url: str) -> dict[str, str]:
    for row in rows:
        if row.get("url") == url:
            return row
    return {}


def keyword_for_url(rows: list[dict[str, str]], url: str) -> dict[str, str]:
    path = url.replace("https://flashcast.com.my", "")
    for row in rows:
        if row.get("target_url") in {url, path} or row.get("current_url") in {url, path}:
            return row
    return {}


def score_for_url(rows: list[dict[str, str]], url: str) -> dict[str, str]:
    return row_by_url(rows, url)


def as_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def has_schema(row: dict[str, str], schema_type: str) -> bool:
    return schema_type in {item.strip() for item in row.get("schema_types", "").split(";")}


def audit_page(
    *,
    url: str,
    inventory_row: dict[str, str],
    keyword_row: dict[str, str],
    score_row: dict[str, str],
) -> PageAudit:
    audit = PageAudit(
        url=url,
        paired_url=expected_pair_url(url),
        page_type=inventory_row.get("page_type", keyword_row.get("page_type", "")),
        language=inventory_row.get("language", ""),
        keyword=keyword_row.get("keyword", score_row.get("keyword", "")),
        score=as_int(score_row.get("total_score", "0")),
    )

    if inventory_row.get("status_code") and inventory_row.get("status_code") != "200":
        audit.add("status_code", "high", "页面不是 200 状态。", "先修复 HTTP 状态，再做内容优化。")
    if inventory_row.get("indexable") == "no":
        audit.add("indexable", "high", "页面当前不可索引。", "移除 noindex、错误 canonical 或其他索引阻塞。")
    if inventory_row.get("robots_allowed") == "no":
        audit.add("robots", "high", "robots 阻止抓取。", "调整 robots.txt，允许搜索引擎抓取目标页面。")
    if inventory_row.get("canonical_self") == "no":
        audit.add("canonical", "high", "canonical 没有指向自身。", "修正 canonical，避免权重和索引信号被转移。")
    if inventory_row.get("hreflang_pair") == "no":
        audit.add("hreflang", "medium", "双语 hreflang 配对不完整。", "补充 `/zh` 与 `/en` 互相指向。")
    if not has_schema(inventory_row, "FAQPage"):
        audit.add("FAQ", "medium", "缺少 FAQPage schema。", "添加真实有用的 FAQ，并用 FAQPage schema 标记。")
    if as_int(inventory_row.get("internal_outlinks_count", "0")) < 2:
        audit.add("CTA/internal links", "medium", "页面出站内链或 CTA 路径偏弱。", "增加报价页、服务页、案例/概念方案页等相关内链。")
    if as_int(inventory_row.get("internal_inlinks_count", "0")) < 2:
        audit.add("internal inlinks", "medium", "页面获得的站内入口偏少。", "从首页、服务 hub、相关文章和案例页增加指向该页面的内链。")
    if as_int(inventory_row.get("word_count", "0")) < 250:
        audit.add("content depth", "medium", "页面正文深度偏薄。", "补充流程、适合人群、材料选择、预算因素、常见问题和设计规划示例。")
    if not audit.findings:
        audit.add("review", "low", "没有发现高优先级技术阻塞。", "可进入内容增强、转化优化和内链优化。")
    return audit


def load_page_audit(root: Path, url: str) -> PageAudit:
    data_dir = root / "seo-workspace" / "data"
    inventory_rows = read_csv_rows(data_dir / "url-inventory.csv")
    keyword_rows = read_csv_rows(data_dir / "keyword-map.csv")
    score_rows = read_csv_rows(data_dir / "seo-opportunity-scores.csv")
    return audit_page(
        url=url,
        inventory_row=row_by_url(inventory_rows, url),
        keyword_row=keyword_for_url(keyword_rows, url),
        score_row=score_for_url(score_rows, url),
    )


def audit_to_markdown(audit: PageAudit) -> str:
    lines = [
        f"- URL: `{audit.url}`",
        f"- 配对页面: `{audit.paired_url or 'N/A'}`",
        f"- 页面类型: {audit.page_type}",
        f"- 目标关键词: {audit.keyword}",
        f"- 机会分: {audit.score}",
        "",
        "### Page Audit Findings",
        "",
    ]
    for finding in audit.findings:
        lines.append(
            f"- [{finding.severity}] {finding.field}: {finding.finding} 建议: {finding.recommendation}"
        )
    return "\n".join(lines)
