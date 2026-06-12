#!/usr/bin/env python3
"""Baidu indexation reporting and URL-submit preflight checks."""

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

from integrations.baidu import (  # noqa: E402
    BAIDU_CRAWL_ERROR_FIELDS,
    BAIDU_INDEX_STATUS_IMPORT_FIELDS,
    BAIDU_SUBMIT_LOG_FIELDS,
    BAIDU_TRAFFIC_KEYWORD_FIELDS,
    BaiduConfig,
    append_submit_log,
    chunk_urls,
    config_from_file,
    load_optional_import_csv,
    merge_config,
    read_submit_log,
    recently_submitted_urls,
    submit_urls,
    write_csv,
)


BAIDU_INDEX_STATUS_FIELDS = [
    "url",
    "language",
    "page_type",
    "status_code",
    "indexable",
    "robots_allowed",
    "canonical_self",
    "sitemap_included",
    "baidu_submit_ready",
    "baidu_submit_status",
    "action",
    "notes",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def is_preflight_ready(row: dict[str, str]) -> bool:
    return (
        row.get("status_code") == "200"
        and row.get("indexable") == "yes"
        and row.get("robots_allowed") == "yes"
        and row.get("canonical_self") == "yes"
        and row.get("sitemap_included") == "yes"
    )


def preflight_block_reason(row: dict[str, str]) -> str:
    checks = [
        ("status_code", "200", "URL is not HTTP 200"),
        ("indexable", "yes", "URL is not indexable"),
        ("robots_allowed", "yes", "URL is blocked by robots"),
        ("canonical_self", "yes", "URL canonical is not self"),
        ("sitemap_included", "yes", "URL is not included in sitemap"),
    ]
    for field, expected, message in checks:
        if row.get(field) != expected:
            return message
    return ""


def build_baidu_index_status_rows(
    inventory_rows: list[dict[str, str]],
    *,
    config: BaiduConfig,
    submit_log_rows: Optional[list[dict[str, str]]] = None,
) -> list[dict[str, str]]:
    submit_log_rows = submit_log_rows or []
    submitted = recently_submitted_urls(submit_log_rows)
    missing_config = ", ".join(config.missing_configuration())
    output: list[dict[str, str]] = []
    for row in inventory_rows:
        url = row.get("url", "")
        ready = is_preflight_ready(row)
        if not ready:
            status = "blocked"
            action = "fix_preflight_before_baidu_submit"
            notes = preflight_block_reason(row)
        elif url in submitted:
            status = "already_submitted"
            action = "do_not_resubmit_without_change"
            notes = "URL already appears in Baidu submit log."
        elif missing_config:
            status = "needs-owner-input"
            action = "needs_baidu_credentials"
            notes = "Missing Baidu configuration: " + missing_config
        else:
            status = "ready"
            action = "ready_for_baidu_submit"
            notes = "Ready for Baidu normal inclusion API submit if owner approves."

        output.append(
            {
                "url": url,
                "language": row.get("language", ""),
                "page_type": row.get("page_type", ""),
                "status_code": row.get("status_code", ""),
                "indexable": row.get("indexable", ""),
                "robots_allowed": row.get("robots_allowed", ""),
                "canonical_self": row.get("canonical_self", ""),
                "sitemap_included": row.get("sitemap_included", ""),
                "baidu_submit_ready": "yes" if ready else "no",
                "baidu_submit_status": status,
                "action": action,
                "notes": notes,
            }
        )
    return output


def eligible_submit_urls(status_rows: list[dict[str, str]], limit: int) -> list[str]:
    urls = [
        row["url"]
        for row in status_rows
        if row.get("baidu_submit_status") == "ready" and row.get("url")
    ]
    return urls[: max(0, limit)]


def generate_deadlink_file(rows: list[dict[str, str]], path: Path) -> list[str]:
    deadlinks = [
        row.get("url", "")
        for row in rows
        if row.get("url") and row.get("status_code") in {"404", "410"}
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(deadlinks) + ("\n" if deadlinks else ""), encoding="utf-8")
    return deadlinks


def build_baidu_report(
    *,
    rows: list[dict[str, str]],
    root: Path,
    config: BaiduConfig,
    used_api: bool,
    submitted_count: int,
    deadlink_count: int,
    imported_index_rows: int,
    imported_keyword_rows: int,
    imported_crawl_error_rows: int,
) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    technical_ready_count = sum(1 for row in rows if row.get("baidu_submit_ready") == "yes")
    configured_ready_count = sum(1 for row in rows if row.get("baidu_submit_status") == "ready")
    needs_config_count = sum(1 for row in rows if row.get("baidu_submit_status") == "needs-owner-input")
    blocked_count = sum(1 for row in rows if row.get("baidu_submit_status") == "blocked")
    already_submitted_count = sum(1 for row in rows if row.get("baidu_submit_status") == "already_submitted")

    lines = [
        "# Baidu Indexation Report",
        "",
        f"- 生成时间: {now}",
        f"- 仓库: `{root}`",
        f"- 百度站点: `{config.site or 'NEEDS OWNER INPUT: BAIDU_SITE'}`",
        f"- 是否调用百度提交 API: {'yes' if used_api else 'no'}",
        f"- 本次提交 URL 数: {submitted_count}",
        f"- 死链文件 URL 数: {deadlink_count}",
        "",
        "## 今日结论",
        "",
        "- 本报告用于百度普通收录 API、sitemap 记录、死链文件和百度数据导入的安全预检。",
        "- 百度提交只能加快发现和抓取处理，不代表 guaranteed indexing、guaranteed ranking 或 guaranteed traffic。",
        "- 真实提交前必须满足：200、可索引、robots 允许、canonical self、在 sitemap 中，并且不能重复疯狂提交未变化 URL。",
        "",
        "## 配置状态",
        "",
    ]
    missing = config.missing_configuration()
    if missing:
        lines.append("- NEEDS OWNER INPUT: 缺少 " + ", ".join(missing))
    else:
        lines.append("- 百度提交配置已满足 API 调用前置条件。")
    if config.sitemap_url:
        lines.append(f"- Sitemap URL: `{config.sitemap_url}`")

    lines.extend(
        [
            "",
            "## URL 提交预检",
            "",
            f"- URL 总数: {len(rows)}",
            f"- 技术预检通过: {technical_ready_count}",
            f"- 配置齐全可提交: {configured_ready_count}",
            f"- 等待百度配置: {needs_config_count}",
            f"- 技术预检阻塞: {blocked_count}",
            f"- 已提交过不建议重复提交: {already_submitted_count}",
            "",
            "## 百度数据导入",
            "",
            f"- 索引量导入行数: {imported_index_rows}",
            f"- 流量关键词导入行数: {imported_keyword_rows}",
            f"- 抓取异常导入行数: {imported_crawl_error_rows}",
            "",
            "## 输出文件",
            "",
            "- `seo-workspace/data/baidu-submit-log.csv`",
            "- `seo-workspace/data/baidu-index-status.csv`",
            "- `seo-workspace/data/baidu-deadlinks.txt`",
            "",
            "## QA Checklist",
            "",
            "- [ ] 确认 `BAIDU_SITE` 与百度搜索资源平台验证站点完全一致。",
            "- [ ] 确认 `BAIDU_PUSH_TOKEN` 或 `BAIDU_SUBMIT_ENDPOINT` 来自百度搜索资源平台普通收录 API。",
            "- [ ] 只提交 200、可索引、robots 允许、canonical self、sitemap included 的 URL。",
            "- [ ] 不重复提交未修改 URL，不批量提交垃圾页、门页或重复城市页。",
            "- [ ] 死链提交文件只放 404/410 URL，不能放仍然 200 的正常页面。",
            "- [ ] 报告里只能写 submitted/accepted/failed/needs-owner-input，不能写 guaranteed indexed。",
            "",
            "## 执行状态",
            "",
            (
                f"- 已调用百度普通收录 API；本次提交 URL 数: {submitted_count}。未登录 CMS，未修改 live 网站。"
                if used_api
                else "- 已生成百度收录报告与 CSV 输出；默认未提交百度 API，未登录 CMS，未修改 live 网站。"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def load_config(root: Path, config_path: str = "") -> BaiduConfig:
    env_config = BaiduConfig.from_env()
    if config_path:
        return merge_config(env_config, config_from_file(Path(config_path)))
    default_config = root / "seo-workspace" / "config" / "baidu.yml"
    if default_config.exists():
        return merge_config(env_config, config_from_file(default_config))
    return env_config


def run_baidu_indexation_report(
    *,
    root: Path,
    config_path: str = "",
    use_api: bool = False,
    submit_limit: int = 50,
) -> list[dict[str, str]]:
    root = root.resolve()
    config = load_config(root, config_path)
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    inventory_rows = read_csv_rows(data_dir / "url-inventory.csv")
    submit_log_path = data_dir / "baidu-submit-log.csv"
    status_path = data_dir / "baidu-index-status.csv"
    deadlink_path = data_dir / "baidu-deadlinks.txt"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-baidu-indexation-report.md"

    existing_log_rows = read_submit_log(submit_log_path)
    status_rows = build_baidu_index_status_rows(
        inventory_rows,
        config=config,
        submit_log_rows=existing_log_rows,
    )

    submitted_count = 0
    used_api = False
    if use_api and config.can_submit():
        urls = eligible_submit_urls(status_rows, min(submit_limit, config.daily_quota))
        submitted_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
        for batch_number, batch in enumerate(chunk_urls(urls, config.batch_size), start=1):
            response = submit_urls(batch, config, submission_type="normal")
            append_submit_log(
                submit_log_path,
                submitted_at=submitted_at,
                batch_id=f"{submitted_at}-batch-{batch_number}",
                urls=batch,
                response=response,
                submission_type="normal",
            )
            submitted_count += len(batch)
            used_api = True
        status_rows = build_baidu_index_status_rows(
            inventory_rows,
            config=config,
            submit_log_rows=read_submit_log(submit_log_path),
        )
    elif not submit_log_path.exists():
        write_csv(submit_log_path, [], BAIDU_SUBMIT_LOG_FIELDS)

    write_csv(status_path, status_rows, BAIDU_INDEX_STATUS_FIELDS)
    deadlinks = generate_deadlink_file(inventory_rows, deadlink_path)

    imported_index_rows = len(load_optional_import_csv(data_dir / "baidu-index-import.csv", BAIDU_INDEX_STATUS_IMPORT_FIELDS))
    imported_keyword_rows = len(load_optional_import_csv(data_dir / "baidu-traffic-keywords-import.csv", BAIDU_TRAFFIC_KEYWORD_FIELDS))
    imported_crawl_error_rows = len(load_optional_import_csv(data_dir / "baidu-crawl-errors-import.csv", BAIDU_CRAWL_ERROR_FIELDS))

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_baidu_report(
            rows=status_rows,
            root=root,
            config=config,
            used_api=used_api,
            submitted_count=submitted_count,
            deadlink_count=len(deadlinks),
            imported_index_rows=imported_index_rows,
            imported_keyword_rows=imported_keyword_rows,
            imported_crawl_error_rows=imported_crawl_error_rows,
        ),
        encoding="utf-8",
    )
    return status_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Baidu indexation report.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--config", default="", help="Optional baidu.yml config path.")
    parser.add_argument("--use-api", action="store_true", help="Submit eligible URLs to Baidu API when configured.")
    parser.add_argument("--submit-limit", type=int, default=50, help="Maximum URLs to submit in this run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = run_baidu_indexation_report(
        root=Path(args.root),
        config_path=args.config,
        use_api=args.use_api,
        submit_limit=args.submit_limit,
    )
    print(f"Generated Baidu index status rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
