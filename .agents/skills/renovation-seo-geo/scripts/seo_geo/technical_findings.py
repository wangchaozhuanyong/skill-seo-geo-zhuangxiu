"""Structured technical SEO/GEO findings from URL inventory rows."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

try:
    from .seo_findings import (
        SeoFinding,
        count_by_severity,
        dedupe_findings,
        format_counts,
        write_findings_csv,
        write_findings_json,
    )
    from .url_inventory import read_inventory_csv
except ImportError:  # pragma: no cover
    from seo_findings import (
        SeoFinding,
        count_by_severity,
        dedupe_findings,
        format_counts,
        write_findings_csv,
        write_findings_json,
    )
    from url_inventory import read_inventory_csv


def _parse_int(value: str) -> int:
    try:
        return int(float(value or "0"))
    except ValueError:
        return 0


def _row_url(row: dict[str, str]) -> str:
    return row.get("url", "").strip()


def _is_core_page(row: dict[str, str]) -> bool:
    return row.get("page_type", "") in {"service", "local", "service-hub", "home", "conversion"}


def _add(
    findings: list[SeoFinding],
    *,
    severity: str,
    category: str,
    row: dict[str, str],
    evidence: str,
    recommendation: str,
    publish_blocker: bool = False,
    owner_input_required: bool = False,
) -> None:
    findings.append(
        SeoFinding(
            severity=severity,
            category=category,
            url=_row_url(row),
            evidence=evidence,
            recommendation=recommendation,
            publish_blocker=publish_blocker,
            owner_input_required=owner_input_required,
            source="url-inventory.csv",
        )
    )


def build_technical_findings(rows: list[dict[str, str]]) -> list[SeoFinding]:
    findings: list[SeoFinding] = []
    if not rows:
        return [
            SeoFinding(
                severity="warning",
                category="inventory",
                url="",
                evidence="url-inventory.csv is missing or empty",
                recommendation="先运行 crawl 或 technical-audit 生成 URL 清单，再做技术 findings。",
                owner_input_required=False,
                source="technical-findings",
            )
        ]

    for row in rows:
        status = row.get("status_code", "").strip()
        indexable = row.get("indexable", "").strip().lower()
        robots_allowed = row.get("robots_allowed", "").strip().lower()
        meta_robots = row.get("meta_robots", "").strip().lower()
        canonical_self = row.get("canonical_self", "").strip().lower()
        hreflang_pair = row.get("hreflang_pair", "").strip().lower()
        schema_types = row.get("schema_types", "").strip()
        page_type = row.get("page_type", "").strip()
        language = row.get("language", "").strip()

        if status and status != "200":
            _add(
                findings,
                severity="error",
                category="http_status",
                row=row,
                evidence=f"status_code={status}",
                recommendation="修复页面返回状态；核心页面发布前应返回 200。",
                publish_blocker=True,
            )
        elif not status:
            _add(
                findings,
                severity="info",
                category="crawl_coverage",
                row=row,
                evidence="status_code is blank",
                recommendation="当前未匹配到本地 HTML，且未启用远程抓取；需要发布前用真实 URL 复核 HTTP 状态。",
            )

        if robots_allowed == "no":
            _add(
                findings,
                severity="error",
                category="crawlability",
                row=row,
                evidence="robots_allowed=no",
                recommendation="调整 robots.txt 或页面路径，确保应收录页面允许搜索引擎抓取。",
                publish_blocker=True,
            )

        if indexable == "no":
            _add(
                findings,
                severity="error",
                category="indexability",
                row=row,
                evidence="indexable=no",
                recommendation="先修复阻塞索引的状态、robots、noindex 或 canonical 问题，再进入发布/提交阶段。",
                publish_blocker=True,
            )

        if "noindex" in meta_robots:
            _add(
                findings,
                severity="error",
                category="indexability",
                row=row,
                evidence=f"meta_robots={row.get('meta_robots', '')}",
                recommendation="移除不该存在的 noindex；只有明确不希望收录的页面才保留 noindex。",
                publish_blocker=True,
            )

        if canonical_self == "no":
            _add(
                findings,
                severity="error",
                category="canonical",
                row=row,
                evidence=f"canonical_url={row.get('canonical_url', '') or 'blank'}",
                recommendation="核心页面 canonical 应指向自身 URL，避免搜索引擎把价值合并到错误页面。",
                publish_blocker=True,
            )

        if hreflang_pair == "no" and language in {"en", "zh"}:
            _add(
                findings,
                severity="warning",
                category="multilingual",
                row=row,
                evidence="hreflang_pair=no",
                recommendation="补齐 `/zh` 与 `/en` 配对页面互指，避免双语页面关系不清。",
            )

        if _is_core_page(row) and not row.get("title", "").strip():
            _add(
                findings,
                severity="error",
                category="on_page",
                row=row,
                evidence="title is blank",
                recommendation="为核心页面补充唯一、可点击、符合搜索意图的 title。",
                publish_blocker=True,
            )

        if _is_core_page(row) and not row.get("h1", "").strip():
            _add(
                findings,
                severity="error",
                category="on_page",
                row=row,
                evidence="h1 is blank",
                recommendation="为核心页面补充清晰 H1，保持页面主题和主关键词一致。",
                publish_blocker=True,
            )

        if _is_core_page(row) and not row.get("meta_description", "").strip():
            _add(
                findings,
                severity="warning",
                category="on_page",
                row=row,
                evidence="meta_description is blank",
                recommendation="补充面向真实用户的 description，优先说明服务、地区和 CTA。",
            )

        if page_type in {"service", "local", "home"} and not schema_types:
            _add(
                findings,
                severity="warning",
                category="schema",
                row=row,
                evidence="schema_types is blank",
                recommendation="补充合适的 LocalBusiness/Service/WebPage/FAQPage 结构化数据；不要写未经确认的奖项、价格或评价。",
            )
        elif page_type in {"service", "local"} and "FAQPage" not in {item.strip() for item in schema_types.split(";")}:
            _add(
                findings,
                severity="info",
                category="geo_readiness",
                row=row,
                evidence=f"schema_types={schema_types}",
                recommendation="如页面已有真实 FAQ，可补充 FAQPage schema；没有真实问答时先写草稿等待确认。",
            )

        missing_alt_count = _parse_int(row.get("missing_alt_count", ""))
        if missing_alt_count > 0:
            _add(
                findings,
                severity="warning",
                category="image_seo",
                row=row,
                evidence=f"missing_alt_count={missing_alt_count}",
                recommendation="为装修/设计图片补充具体 alt，并标注 concept/rendering，不能冒充真实完工案例。",
            )

        word_count = _parse_int(row.get("word_count", ""))
        if page_type in {"service", "local", "article"} and word_count and word_count < 250:
            _add(
                findings,
                severity="warning",
                category="content_depth",
                row=row,
                evidence=f"word_count={word_count}",
                recommendation="补充服务范围、流程、材料/空间要点、FAQ、内部链接和合规 CTA，避免薄内容。",
            )

        if page_type in {"service", "local"}:
            inlinks = _parse_int(row.get("internal_inlinks_count", ""))
            outlinks = _parse_int(row.get("internal_outlinks_count", ""))
            if inlinks < 2 or outlinks < 2:
                _add(
                    findings,
                    severity="warning",
                    category="internal_links",
                    row=row,
                    evidence=f"internal_inlinks_count={inlinks}; internal_outlinks_count={outlinks}",
                    recommendation="补充相关服务页、地区页、案例/概念证明页和 CTA 的内部链接。",
                )

        if row.get("sitemap_included", "").strip().lower() == "no" and indexable == "yes":
            _add(
                findings,
                severity="warning",
                category="sitemap",
                row=row,
                evidence="sitemap_included=no",
                recommendation="确认应收录页面进入 sitemap；不要把 noindex 或重复页面强行提交。",
            )

    return dedupe_findings(findings)


def build_findings_report(
    *,
    root: Path,
    inventory_path: Path,
    csv_path: Path,
    json_path: Path,
    findings: list[SeoFinding],
) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    blocker_count = sum(1 for finding in findings if finding.publish_blocker)
    counts = count_by_severity(findings)
    lines = [
        "# Technical SEO Findings",
        "",
        f"- 生成时间: {now}",
        f"- 仓库: `{root}`",
        f"- 输入清单: `{inventory_path}`",
        f"- Findings CSV: `{csv_path}`",
        f"- Findings JSON: `{json_path}`",
        f"- Findings 数量: {len(findings)}",
        f"- 发布阻塞项: {blocker_count}",
        f"- 严重级别: {format_counts(counts)}",
        "",
        "## 结论",
        "",
    ]
    if blocker_count:
        lines.append("- 当前存在发布前必须修复的技术阻塞项；不要把这些 URL 直接提交搜索引擎或进入 live 发布。")
    elif findings:
        lines.append("- 当前没有结构化发布阻塞项，但仍有可优化的技术/内容证据。")
    else:
        lines.append("- 当前没有发现结构化技术问题。")

    lines.extend(
        [
            "",
            "## Top Findings",
            "",
        ]
    )
    for finding in findings[:30]:
        blocker = " blocker=yes" if finding.publish_blocker else ""
        lines.append(f"- [{finding.severity}] {finding.category}{blocker} `{finding.url or 'N/A'}`: {finding.evidence} -> {finding.recommendation}")
    if not findings:
        lines.append("- 暂无 findings。")

    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 本报告是本地证据汇总，不代表页面已经被搜索引擎收录或排名。",
            "- `info` 项通常是复核提醒；`warning` 项适合进入优化队列；`error` 项若 publish_blocker=yes，发布前必须处理。",
            "- 不要用本报告生成虚假案例、评价、价格、奖项、证书或未经确认的服务区域。",
            "",
            "## 执行状态",
            "",
            "- 已生成本地 findings；未发布、未提交索引、未登录 CMS、未修改 live 网站。",
            "",
        ]
    )
    return "\n".join(lines)


def run_technical_findings_report(root: Path, inventory_path: str = "") -> tuple[dict[str, object], list[Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    selected_inventory_path = Path(inventory_path) if inventory_path else data_dir / "url-inventory.csv"
    if not selected_inventory_path.is_absolute():
        selected_inventory_path = root / selected_inventory_path
    rows = read_inventory_csv(selected_inventory_path)
    findings = build_technical_findings(rows)

    csv_path = data_dir / "technical-audit-findings.csv"
    json_path = data_dir / "technical-audit-findings.json"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-technical-audit-findings.md"
    write_findings_csv(csv_path, findings)
    write_findings_json(json_path, findings)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_findings_report(
            root=root,
            inventory_path=selected_inventory_path,
            csv_path=csv_path,
            json_path=json_path,
            findings=findings,
        ),
        encoding="utf-8",
    )
    summary = {
        "finding_count": len(findings),
        "publish_blocker_count": sum(1 for finding in findings if finding.publish_blocker),
        "severity_counts": count_by_severity(findings),
    }
    return summary, [csv_path, json_path, report_path]
