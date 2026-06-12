#!/usr/bin/env python3
"""IndexNow reporting and optional URL submission.

Safe by default: report generation does not submit URLs. HTTP 200/202 responses
are recorded as received/accepted, never as indexed.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


INDEXNOW_DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_LOG_FIELDS = [
    "submitted_at",
    "batch_id",
    "url",
    "action_type",
    "status",
    "http_status",
    "endpoint",
    "key_location",
    "message",
]

INDEXNOW_STATUS_FIELDS = [
    "url",
    "language",
    "page_type",
    "status_code",
    "indexable",
    "robots_allowed",
    "canonical_self",
    "sitemap_included",
    "indexnow_ready",
    "indexnow_status",
    "action",
    "notes",
]

INDEXNOW_KEY_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,128}$")


@dataclass
class IndexNowConfig:
    key: str = ""
    key_location: str = ""
    endpoint: str = INDEXNOW_DEFAULT_ENDPOINT
    host: str = ""
    batch_size: int = 10000

    @classmethod
    def from_env(cls) -> "IndexNowConfig":
        return cls(
            key=os.environ.get("INDEXNOW_KEY", ""),
            key_location=os.environ.get("INDEXNOW_KEY_LOCATION", ""),
            endpoint=os.environ.get("INDEXNOW_ENDPOINT", INDEXNOW_DEFAULT_ENDPOINT),
            host=os.environ.get("INDEXNOW_HOST", ""),
            batch_size=int(os.environ.get("INDEXNOW_BATCH_SIZE", "10000") or "10000"),
        )

    def missing_configuration(self) -> list[str]:
        missing: list[str] = []
        if not self.key:
            missing.append("INDEXNOW_KEY")
        elif not is_valid_key(self.key):
            missing.append("valid INDEXNOW_KEY")
        if not self.host:
            missing.append("INDEXNOW_HOST")
        if not self.endpoint:
            missing.append("INDEXNOW_ENDPOINT")
        return missing

    def can_submit(self) -> bool:
        return not self.missing_configuration()


def is_valid_key(key: str) -> bool:
    return bool(INDEXNOW_KEY_PATTERN.match(key or ""))


def host_from_url(url: str) -> str:
    return urlsplit(url).netloc.lower()


def suggested_key_file_url(config: IndexNowConfig, site_url: str = "") -> str:
    host_url = site_url.rstrip("/") if site_url else f"https://{config.host}".rstrip("/")
    if not config.key:
        return ""
    return f"{host_url}/{config.key}.txt"


def key_file_recommendation(config: IndexNowConfig, site_url: str = "") -> str:
    url = config.key_location or suggested_key_file_url(config, site_url)
    if not config.key:
        return "NEEDS OWNER INPUT: generate INDEXNOW_KEY and host a UTF-8 text file containing exactly the key."
    return f"Host a UTF-8 text key file at `{url}` containing exactly `{config.key}`."


def verify_key_file(config: IndexNowConfig, *, timeout: int = 10) -> dict[str, str]:
    key_location = config.key_location or suggested_key_file_url(config)
    if not key_location:
        return {"status": "needs-owner-input", "message": "INDEXNOW_KEY_LOCATION or host/key is missing"}
    request = Request(key_location, headers={"User-Agent": "SEO-GEO-IndexNow/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(2048).decode("utf-8", errors="replace").strip()
            if response.getcode() == 200 and body == config.key:
                return {"status": "verified", "http_status": "200", "message": "Key file is accessible and matches."}
            return {
                "status": "mismatch",
                "http_status": str(response.getcode()),
                "message": "Key file is accessible but content does not exactly match INDEXNOW_KEY.",
            }
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        http_status = str(exc.code) if isinstance(exc, HTTPError) else ""
        return {"status": "failed", "http_status": http_status, "message": str(exc)}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_submit_log(
    path: Path,
    *,
    submitted_at: str,
    batch_id: str,
    urls: list[str],
    action_type: str,
    response: dict[str, str],
    config: IndexNowConfig,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEXNOW_LOG_FIELDS)
        if not exists:
            writer.writeheader()
        for url in urls:
            writer.writerow(
                {
                    "submitted_at": submitted_at,
                    "batch_id": batch_id,
                    "url": url,
                    "action_type": action_type,
                    "status": response.get("status", ""),
                    "http_status": response.get("http_status", ""),
                    "endpoint": config.endpoint,
                    "key_location": config.key_location,
                    "message": response.get("message", ""),
                }
            )


def read_submit_log(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def previously_received_urls(rows: list[dict[str, str]]) -> set[str]:
    return {
        row.get("url", "")
        for row in rows
        if row.get("status") in {"received", "accepted"}
    }


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


def validate_host_ownership(urls: list[str], config: IndexNowConfig) -> list[str]:
    if not config.host:
        return urls
    return [url for url in urls if host_from_url(url) == config.host.lower()]


def build_payload(urls: list[str], config: IndexNowConfig) -> dict[str, object]:
    payload: dict[str, object] = {
        "host": config.host,
        "key": config.key,
        "urlList": urls,
    }
    if config.key_location:
        payload["keyLocation"] = config.key_location
    return payload


def classify_response(status_code: int, body: str = "") -> dict[str, str]:
    if status_code == 200:
        return {"status": "received", "http_status": "200", "message": "Received by IndexNow endpoint; not an indexing guarantee."}
    if status_code == 202:
        return {"status": "accepted", "http_status": "202", "message": "Accepted; key validation may still be pending."}
    if status_code == 400:
        return {"status": "failed", "http_status": "400", "message": "Bad request: invalid format."}
    if status_code == 403:
        return {"status": "failed", "http_status": "403", "message": "Forbidden: key not valid or key file not found."}
    if status_code == 422:
        return {"status": "failed", "http_status": "422", "message": "URLs do not belong to host or key location scope."}
    if status_code == 429:
        return {"status": "failed", "http_status": "429", "message": "Too many requests; possible spam/rate limit."}
    return {"status": "failed", "http_status": str(status_code), "message": body or "Unexpected response."}


def submit_urls(
    urls: list[str],
    config: IndexNowConfig,
    *,
    action_type: str = "updated",
    timeout: int = 15,
) -> dict[str, str]:
    if action_type not in {"added", "updated", "deleted"}:
        return {"status": "failed", "http_status": "", "message": "action_type must be added, updated, or deleted"}
    if not urls:
        return {"status": "skipped", "http_status": "", "message": "No URLs to submit."}
    if not config.can_submit():
        return {"status": "needs-owner-input", "http_status": "", "message": ", ".join(config.missing_configuration())}

    valid_host_urls = validate_host_ownership(urls, config)
    if len(valid_host_urls) != len(urls):
        return {"status": "failed", "http_status": "", "message": "One or more URLs do not belong to INDEXNOW_HOST."}

    request = Request(
        config.endpoint,
        data=json.dumps(build_payload(urls, config)).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "SEO-GEO-IndexNow/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return classify_response(response.getcode(), body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return classify_response(exc.code, body)
    except (URLError, OSError, TimeoutError) as exc:
        return {"status": "failed", "http_status": "", "message": str(exc)}


def chunk_urls(urls: list[str], batch_size: int) -> list[list[str]]:
    size = min(max(1, batch_size), 10000)
    return [urls[index : index + size] for index in range(0, len(urls), size)]


def build_indexnow_status_rows(
    inventory_rows: list[dict[str, str]],
    *,
    config: IndexNowConfig,
    submit_log_rows: Optional[list[dict[str, str]]] = None,
) -> list[dict[str, str]]:
    submit_log_rows = submit_log_rows or []
    received = previously_received_urls(submit_log_rows)
    missing_config = ", ".join(config.missing_configuration())
    output: list[dict[str, str]] = []
    for row in inventory_rows:
        url = row.get("url", "")
        ready = is_preflight_ready(row)
        if not ready:
            status = "blocked"
            action = "fix_preflight_before_indexnow"
            notes = preflight_block_reason(row)
        elif url in received:
            status = "already_received"
            action = "do_not_resubmit_without_change"
            notes = "URL already appears in IndexNow submit log as received/accepted."
        elif missing_config:
            status = "needs-owner-input"
            action = "needs_indexnow_key"
            notes = "Missing IndexNow configuration: " + missing_config
        else:
            status = "ready"
            action = "ready_for_indexnow_submit"
            notes = "Ready for IndexNow submit if owner approves and key file is verified."

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
                "indexnow_ready": "yes" if ready else "no",
                "indexnow_status": status,
                "action": action,
                "notes": notes,
            }
        )
    return output


def eligible_submit_urls(status_rows: list[dict[str, str]], limit: int) -> list[str]:
    urls = [row["url"] for row in status_rows if row.get("indexnow_status") == "ready" and row.get("url")]
    return urls[: max(0, limit)]


def build_report(
    *,
    rows: list[dict[str, str]],
    root: Path,
    config: IndexNowConfig,
    used_api: bool,
    submitted_count: int,
    key_check: dict[str, str],
) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    technical_ready_count = sum(1 for row in rows if row.get("indexnow_ready") == "yes")
    configured_ready_count = sum(1 for row in rows if row.get("indexnow_status") == "ready")
    needs_key_count = sum(1 for row in rows if row.get("indexnow_status") == "needs-owner-input")
    blocked_count = sum(1 for row in rows if row.get("indexnow_status") == "blocked")
    already_received_count = sum(1 for row in rows if row.get("indexnow_status") == "already_received")
    missing = config.missing_configuration()

    lines = [
        "# IndexNow Report",
        "",
        f"- 生成时间: {now}",
        f"- 仓库: `{root}`",
        f"- Endpoint: `{config.endpoint}`",
        f"- Host: `{config.host or 'NEEDS OWNER INPUT: INDEXNOW_HOST'}`",
        f"- 是否调用 IndexNow API: {'yes' if used_api else 'no'}",
        f"- 本次提交 URL 数: {submitted_count}",
        "",
        "## 今日结论",
        "",
        "- 本报告用于 Bing / IndexNow 的 URL 变更通知、key 文件验证和批量提交预检。",
        "- IndexNow 的 200/202 响应只能记录为 received/accepted，不能写成 indexed 或 guaranteed indexed。",
        "- 不重复提交未修改 URL；只有新增、更新或删除 URL 才应提交。",
        "",
        "## 配置状态",
        "",
    ]
    if missing:
        lines.append("- NEEDS OWNER INPUT: 缺少 " + ", ".join(missing))
    else:
        lines.append("- IndexNow 配置已满足 API 调用前置条件。")
    lines.extend(
        [
            f"- Key 文件建议: {key_file_recommendation(config)}",
            f"- Key 文件验证: {key_check.get('status', 'not_checked')} {key_check.get('message', '')}",
            "",
            "## URL 提交预检",
            "",
            f"- URL 总数: {len(rows)}",
            f"- 技术预检通过: {technical_ready_count}",
            f"- 配置齐全可提交: {configured_ready_count}",
            f"- 等待 IndexNow key: {needs_key_count}",
            f"- 技术预检阻塞: {blocked_count}",
            f"- 已 received/accepted 不建议重复提交: {already_received_count}",
            "",
            "## 输出文件",
            "",
            "- `seo-workspace/data/indexnow-submit-log.csv`",
            "- `seo-workspace/data/indexnow-status.csv`",
            "",
            "## QA Checklist",
            "",
            "- [ ] 生成 8-128 位合法 IndexNow key，只包含字母、数字或 dash。",
            "- [ ] 将 UTF-8 key 文件放在网站根目录或配置 `INDEXNOW_KEY_LOCATION`。",
            "- [ ] 验证 key 文件可公网访问且内容与 key 完全一致。",
            "- [ ] 只提交新增、更新或删除 URL，不重复提交未变化 URL。",
            "- [ ] 报告中 200/202 只能写 received/accepted，不能写 indexed。",
            "- [ ] 真实提交前确认 URL 200、可索引、robots 允许、canonical self、sitemap included。",
            "",
            "## 执行状态",
            "",
            "- 已生成 IndexNow 报告与 CSV 输出；默认未提交 API，未登录 CMS，未修改 live 网站。",
            "",
        ]
    )
    return "\n".join(lines)


def run_indexnow_report(
    *,
    root: Path,
    use_api: bool = False,
    submit_limit: int = 50,
    action_type: str = "updated",
    verify_key: bool = False,
) -> list[dict[str, str]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    inventory_rows = read_csv_rows(data_dir / "url-inventory.csv")
    submit_log_path = data_dir / "indexnow-submit-log.csv"
    status_path = data_dir / "indexnow-status.csv"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-indexnow-report.md"
    config = IndexNowConfig.from_env()
    submit_log_rows = read_submit_log(submit_log_path)
    status_rows = build_indexnow_status_rows(
        inventory_rows,
        config=config,
        submit_log_rows=submit_log_rows,
    )
    key_check = verify_key_file(config) if verify_key else {"status": "not_checked", "message": "Run with --verify-key after hosting the key file."}

    submitted_count = 0
    used_api = False
    if use_api and config.can_submit():
        urls = eligible_submit_urls(status_rows, submit_limit)
        submitted_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
        for batch_number, batch in enumerate(chunk_urls(urls, config.batch_size), start=1):
            response = submit_urls(batch, config, action_type=action_type)
            append_submit_log(
                submit_log_path,
                submitted_at=submitted_at,
                batch_id=f"{submitted_at}-batch-{batch_number}",
                urls=batch,
                action_type=action_type,
                response=response,
                config=config,
            )
            submitted_count += len(batch)
            used_api = True
        status_rows = build_indexnow_status_rows(
            inventory_rows,
            config=config,
            submit_log_rows=read_submit_log(submit_log_path),
        )
    elif not submit_log_path.exists():
        write_csv(submit_log_path, [], INDEXNOW_LOG_FIELDS)

    write_csv(status_path, status_rows, INDEXNOW_STATUS_FIELDS)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_report(
            rows=status_rows,
            root=root,
            config=config,
            used_api=used_api,
            submitted_count=submitted_count,
            key_check=key_check,
        ),
        encoding="utf-8",
    )
    return status_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate IndexNow report and optionally submit URLs.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--use-api", action="store_true", help="Submit eligible URLs when IndexNow config is present.")
    parser.add_argument("--submit-limit", type=int, default=50, help="Maximum URLs to submit in this run.")
    parser.add_argument("--action-type", default="updated", choices=["added", "updated", "deleted"], help="URL change type.")
    parser.add_argument("--verify-key", action="store_true", help="Verify hosted IndexNow key file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = run_indexnow_report(
        root=Path(args.root),
        use_api=args.use_api,
        submit_limit=args.submit_limit,
        action_type=args.action_type,
        verify_key=args.verify_key,
    )
    print(f"Generated IndexNow status rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
