#!/usr/bin/env python3
"""Google Search Console indexation reporting.

This script is safe by default. It does not call the Google Indexing API for
ordinary renovation pages and does not request indexing. URL Inspection and
sitemap submission only run when explicitly requested with configured GSC
credentials.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path
from typing import Optional


SEO_GEO_DIR = Path(__file__).resolve().parents[1]
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))

from integrations.google_search_console import (  # noqa: E402
    GoogleSearchConsoleConfig,
    URL_INSPECTION_FIELDS,
    build_search_console_service,
    inspect_url,
    query_search_analytics,
    submit_sitemap,
    write_csv,
    write_search_analytics_outputs,
)


GOOGLE_INDEX_STATUS_FIELDS = [
    "url",
    "language",
    "page_type",
    "status_code",
    "indexable",
    "robots_allowed",
    "canonical_self",
    "sitemap_included",
    "inspection_state",
    "verdict",
    "coverage_state",
    "indexing_state",
    "page_fetch_state",
    "robots_txt_state",
    "google_canonical",
    "user_canonical",
    "last_crawl_time",
    "referring_urls",
    "mobile_usability_verdict",
    "rich_results_verdict",
    "action",
    "notes",
]

GOOGLE_INDEXING_API_ALLOWED_SCHEMA = {"JobPosting"}


class GoogleIndexingApiBlocked(RuntimeError):
    """Raised when a page is not eligible for Google's Indexing API."""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def parse_schema_types(value: str) -> set[str]:
    return {part.strip() for part in (value or "").split(";") if part.strip()}


def is_google_indexing_api_allowed(row: dict[str, str]) -> bool:
    schema_types = parse_schema_types(row.get("schema_types", ""))
    if schema_types & GOOGLE_INDEXING_API_ALLOWED_SCHEMA:
        return True
    return "VideoObject" in schema_types and "BroadcastEvent" in schema_types


def assert_google_indexing_api_allowed(row: dict[str, str]) -> None:
    if is_google_indexing_api_allowed(row):
        return
    page_type = row.get("page_type", "unknown")
    url = row.get("url", "")
    raise GoogleIndexingApiBlocked(
        "Google Indexing API is blocked for this URL because it is not a "
        f"JobPosting page or a BroadcastEvent embedded in VideoObject: {page_type} {url}"
    )


def is_preflight_ready(row: dict[str, str]) -> bool:
    return (
        row.get("status_code") == "200"
        and row.get("indexable") == "yes"
        and row.get("robots_allowed") == "yes"
        and row.get("canonical_self") == "yes"
        and row.get("sitemap_included") == "yes"
    )


def inspection_placeholder(url: str, state: str, notes: str = "") -> dict[str, str]:
    row = {field: "" for field in URL_INSPECTION_FIELDS}
    row.update({"url": url, "inspection_state": state, "raw_error": notes})
    return row


def build_google_index_status_rows(
    inventory_rows: list[dict[str, str]],
    *,
    config: GoogleSearchConsoleConfig,
    inspection_rows: Optional[dict[str, dict[str, str]]] = None,
) -> list[dict[str, str]]:
    inspection_rows = inspection_rows or {}
    missing_config = ", ".join(config.missing_configuration())
    output: list[dict[str, str]] = []
    for inventory in inventory_rows:
        url = inventory.get("url", "")
        inspection = inspection_rows.get(url)
        if inspection is None:
            if not is_preflight_ready(inventory):
                inspection = inspection_placeholder(url, "not_checked", "Preflight failed; fix technical SEO first.")
                action = "fix_preflight_before_gsc_inspection"
            elif missing_config:
                inspection = inspection_placeholder(url, "not_checked", "Missing GSC configuration: " + missing_config)
                action = "needs_gsc_credentials"
            else:
                inspection = inspection_placeholder(url, "not_checked", "Run with --use-api to inspect in GSC.")
                action = "ready_for_url_inspection"
        else:
            action = "review_google_index_status" if inspection.get("inspection_state") == "checked" else "review_api_error"

        row = {
            "url": url,
            "language": inventory.get("language", ""),
            "page_type": inventory.get("page_type", ""),
            "status_code": inventory.get("status_code", ""),
            "indexable": inventory.get("indexable", ""),
            "robots_allowed": inventory.get("robots_allowed", ""),
            "canonical_self": inventory.get("canonical_self", ""),
            "sitemap_included": inventory.get("sitemap_included", ""),
            "inspection_state": inspection.get("inspection_state", ""),
            "verdict": inspection.get("verdict", ""),
            "coverage_state": inspection.get("coverage_state", ""),
            "indexing_state": inspection.get("indexing_state", ""),
            "page_fetch_state": inspection.get("page_fetch_state", ""),
            "robots_txt_state": inspection.get("robots_txt_state", ""),
            "google_canonical": inspection.get("google_canonical", ""),
            "user_canonical": inspection.get("user_canonical", ""),
            "last_crawl_time": inspection.get("last_crawl_time", ""),
            "referring_urls": inspection.get("referring_urls", ""),
            "mobile_usability_verdict": inspection.get("mobile_usability_verdict", ""),
            "rich_results_verdict": inspection.get("rich_results_verdict", ""),
            "action": action,
            "notes": inspection.get("raw_error", ""),
        }
        output.append(row)
    return output


def build_google_indexation_report(
    *,
    rows: list[dict[str, str]],
    root: Path,
    config: GoogleSearchConsoleConfig,
    used_api: bool,
    analytics_rows: int,
    sitemap_submit_result: Optional[dict[str, str]] = None,
) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    missing = config.missing_configuration()
    ready_count = sum(1 for row in rows if row.get("action") in {"ready_for_url_inspection", "needs_gsc_credentials"})
    checked_count = sum(1 for row in rows if row.get("inspection_state") == "checked")
    needs_config_count = sum(1 for row in rows if row.get("action") == "needs_gsc_credentials")
    preflight_blocked_count = sum(1 for row in rows if row.get("action") == "fix_preflight_before_gsc_inspection")

    lines = [
        "# Google Indexation Report",
        "",
        f"- 生成时间: {now}",
        f"- 仓库: `{root}`",
        f"- GSC property: `{config.site_url or 'NEEDS OWNER INPUT: GSC_SITE_URL'}`",
        f"- 凭证模式: {config.credential_mode()}",
        f"- 是否调用 GSC API: {'yes' if used_api else 'no'}",
        f"- Search Analytics rows: {analytics_rows}",
        "",
        "## 今日结论",
        "",
        "- 本报告只处理 Google Search Console 的数据读取、URL Inspection 状态检查和 sitemap 提交准备。",
        "- 没有调用 Google Indexing API，也没有请求 Google 立即索引普通装修页面。",
        "- Google Indexing API 已加硬规则：只允许 `JobPosting` 或 `VideoObject` 中的 `BroadcastEvent`，普通装修服务页会被拦截。",
        "",
        "## 配置状态",
        "",
    ]
    if missing:
        lines.append("- NEEDS OWNER INPUT: 缺少 " + ", ".join(missing))
    else:
        lines.append("- GSC 配置已满足 API 调用前置条件。")

    lines.extend(
        [
            "",
            "## URL Inspection 状态",
            "",
            f"- URL 总数: {len(rows)}",
            f"- 已通过技术预检但未查 GSC: {ready_count}",
            f"- 已从 GSC 检查: {checked_count}",
            f"- 等待 GSC 凭证: {needs_config_count}",
            f"- 技术预检阻塞: {preflight_blocked_count}",
            "",
            "## 输出文件",
            "",
            "- `seo-workspace/data/gsc-queries.csv`",
            "- `seo-workspace/data/gsc-pages.csv`",
            "- `seo-workspace/data/google-index-status.csv`",
            "",
        ]
    )
    if sitemap_submit_result:
        lines.extend(
            [
                "## Sitemap Submit",
                "",
                f"- 结果: {sitemap_submit_result.get('result', '')}",
                f"- Sitemap: `{sitemap_submit_result.get('sitemap_url', '')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## QA Checklist",
            "",
            "- [ ] 确认 GSC property 与网站实际 property 完全一致，例如 `https://flashcast.com.my/` 或 Search Console 中的 domain property。",
            "- [ ] 确认服务账号或 OAuth 用户已被加入对应 Search Console property。",
            "- [ ] 先查看 `google-index-status.csv`，只对 200、可索引、robots 允许、canonical self、sitemap included 的 URL 做 URL Inspection。",
            "- [ ] 不使用 Google Indexing API 推送普通装修服务页、文章页、案例页或城市页。",
            "- [ ] 如需提交 sitemap，只使用 Search Console Sitemaps API，不把它描述为 guaranteed indexing。",
            "",
            "## 执行状态",
            "",
            "- 已生成 Google 索引报告与 CSV 输出；未登录 CMS，未修改 live 网站，未请求 Google Indexing API。",
            "",
        ]
    )
    return "\n".join(lines)


def run_google_indexation_report(
    *,
    root: Path,
    site_url: str = "",
    use_api: bool = False,
    start_date: str = "",
    end_date: str = "",
    inspection_limit: int = 50,
    submit_sitemap_url: str = "",
) -> list[dict[str, str]]:
    root = root.resolve()
    config = GoogleSearchConsoleConfig.from_env(site_url=site_url)
    inventory_path = root / "seo-workspace" / "data" / "url-inventory.csv"
    inventory_rows = read_csv_rows(inventory_path)
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    index_status_path = data_dir / "google-index-status.csv"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-google-indexation-report.md"

    analytics_rows: list[dict[str, str]] = []
    inspection_rows: dict[str, dict[str, str]] = {}
    sitemap_submit_result: Optional[dict[str, str]] = None
    used_api = False

    if use_api and config.can_use_api():
        readonly = not bool(submit_sitemap_url)
        service = build_search_console_service(config, readonly=readonly)
        used_api = True
        if start_date and end_date:
            analytics_rows = query_search_analytics(
                service,
                config,
                start_date=start_date,
                end_date=end_date,
            )
        ready_urls = [row for row in inventory_rows if is_preflight_ready(row)]
        for row in ready_urls[:inspection_limit]:
            inspection_rows[row["url"]] = inspect_url(service, config, row["url"])
        if submit_sitemap_url:
            sitemap_submit_result = submit_sitemap(service, config, submit_sitemap_url)

    write_search_analytics_outputs(root, analytics_rows)
    status_rows = build_google_index_status_rows(
        inventory_rows,
        config=config,
        inspection_rows=inspection_rows,
    )
    write_csv(index_status_path, status_rows, GOOGLE_INDEX_STATUS_FIELDS)

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_google_indexation_report(
            rows=status_rows,
            root=root,
            config=config,
            used_api=used_api,
            analytics_rows=len(analytics_rows),
            sitemap_submit_result=sitemap_submit_result,
        ),
        encoding="utf-8",
    )
    return status_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Google Search Console indexation report.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--site-url", default="", help="Override GSC_SITE_URL for this run.")
    parser.add_argument("--use-api", action="store_true", help="Call GSC APIs when credentials are configured.")
    parser.add_argument("--start-date", default="", help="Search Analytics start date, YYYY-MM-DD.")
    parser.add_argument("--end-date", default="", help="Search Analytics end date, YYYY-MM-DD.")
    parser.add_argument("--inspection-limit", type=int, default=50, help="Maximum URL Inspection API calls.")
    parser.add_argument("--submit-sitemap", default="", help="Submit sitemap URL through Search Console Sitemaps API.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = run_google_indexation_report(
        root=Path(args.root),
        site_url=args.site_url,
        use_api=args.use_api,
        start_date=args.start_date,
        end_date=args.end_date,
        inspection_limit=args.inspection_limit,
        submit_sitemap_url=args.submit_sitemap,
    )
    print(f"Generated Google index status rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
