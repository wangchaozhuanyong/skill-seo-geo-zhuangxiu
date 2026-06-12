"""Baidu Search Resource Platform integration helpers.

This module does not store secrets. Baidu tokens must be supplied through
environment variables or an owner-managed config file outside source control.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BAIDU_SUBMIT_LOG_FIELDS = [
    "submitted_at",
    "batch_id",
    "url",
    "submission_type",
    "status",
    "http_status",
    "success_count",
    "remain",
    "message",
    "error",
]

BAIDU_INDEX_STATUS_IMPORT_FIELDS = [
    "date",
    "indexed_count",
    "source_file",
    "notes",
]

BAIDU_TRAFFIC_KEYWORD_FIELDS = [
    "date",
    "keyword",
    "url",
    "clicks",
    "impressions",
    "position",
    "source_file",
]

BAIDU_CRAWL_ERROR_FIELDS = [
    "date",
    "url",
    "error_type",
    "http_status",
    "source_file",
    "notes",
]


@dataclass
class BaiduConfig:
    site: str = ""
    push_token: str = ""
    submit_endpoint: str = ""
    sitemap_url: str = ""
    daily_quota: int = 200
    batch_size: int = 100

    @classmethod
    def from_env(cls) -> "BaiduConfig":
        return cls(
            site=os.environ.get("BAIDU_SITE", ""),
            push_token=os.environ.get("BAIDU_PUSH_TOKEN", ""),
            submit_endpoint=os.environ.get("BAIDU_SUBMIT_ENDPOINT", ""),
            sitemap_url=os.environ.get("BAIDU_SITEMAP_URL", ""),
            daily_quota=int(os.environ.get("BAIDU_DAILY_QUOTA", "200") or "200"),
            batch_size=int(os.environ.get("BAIDU_BATCH_SIZE", "100") or "100"),
        )

    def missing_configuration(self) -> list[str]:
        missing: list[str] = []
        if not self.site:
            missing.append("BAIDU_SITE")
        if not self.push_token and not self.submit_endpoint:
            missing.append("BAIDU_PUSH_TOKEN or BAIDU_SUBMIT_ENDPOINT")
        return missing

    def can_submit(self) -> bool:
        return not self.missing_configuration()


def read_simple_yaml(path: Path) -> dict[str, str]:
    """Read a small key:value YAML file without adding a YAML dependency."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def config_from_file(path: Path) -> BaiduConfig:
    values = read_simple_yaml(path)
    return BaiduConfig(
        site=values.get("site", ""),
        push_token=values.get("push_token", ""),
        submit_endpoint=values.get("submit_endpoint", ""),
        sitemap_url=values.get("sitemap_url", ""),
        daily_quota=int(values.get("daily_quota", "200") or "200"),
        batch_size=int(values.get("batch_size", "100") or "100"),
    )


def merge_config(primary: BaiduConfig, fallback: BaiduConfig) -> BaiduConfig:
    return BaiduConfig(
        site=primary.site or fallback.site,
        push_token=primary.push_token or fallback.push_token,
        submit_endpoint=primary.submit_endpoint or fallback.submit_endpoint,
        sitemap_url=primary.sitemap_url or fallback.sitemap_url,
        daily_quota=primary.daily_quota or fallback.daily_quota,
        batch_size=primary.batch_size or fallback.batch_size,
    )


def build_submit_endpoint(config: BaiduConfig) -> str:
    if config.submit_endpoint:
        return config.submit_endpoint
    params = urlencode({"site": config.site, "token": config.push_token})
    return f"http://data.zz.baidu.com/urls?{params}"


def chunk_urls(urls: list[str], batch_size: int) -> list[list[str]]:
    size = max(1, batch_size)
    return [urls[index : index + size] for index in range(0, len(urls), size)]


def submit_urls(
    urls: list[str],
    config: BaiduConfig,
    *,
    timeout: int = 15,
    submission_type: str = "normal",
) -> dict[str, object]:
    if not urls:
        return {"status": "skipped", "message": "No URLs to submit."}
    if not config.can_submit():
        return {"status": "needs-owner-input", "message": ", ".join(config.missing_configuration())}

    endpoint = build_submit_endpoint(config)
    body = "\n".join(urls).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "text/plain",
            "User-Agent": "SEO-GEO-Baidu-Submit/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw.strip() else {}
            payload["http_status"] = response.getcode()
            payload["status"] = "accepted" if "success" in payload else "failed"
            payload["submission_type"] = submission_type
            return payload
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return {
            "status": "failed",
            "http_status": exc.code,
            "message": raw,
            "submission_type": submission_type,
        }
    except (URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "status": "failed",
            "http_status": "",
            "message": str(exc),
            "submission_type": submission_type,
        }


def classify_submitted_urls(urls: list[str], response: dict[str, object]) -> dict[str, str]:
    status = str(response.get("status", "failed"))
    not_valid = {str(item) for item in response.get("not_valid", []) or []}
    not_same_site = {str(item) for item in response.get("not_same_site", []) or []}
    error_message = str(response.get("message", "") or response.get("error", ""))
    output: dict[str, str] = {}
    for url in urls:
        if status == "needs-owner-input":
            output[url] = "needs-owner-input"
        elif url in not_valid:
            output[url] = "failed:not_valid"
        elif url in not_same_site:
            output[url] = "failed:not_same_site"
        elif status == "accepted":
            output[url] = "accepted"
        elif error_message:
            output[url] = "failed"
        else:
            output[url] = status
    return output


def append_submit_log(
    path: Path,
    *,
    submitted_at: str,
    batch_id: str,
    urls: list[str],
    response: dict[str, object],
    submission_type: str = "normal",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    status_by_url = classify_submitted_urls(urls, response)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BAIDU_SUBMIT_LOG_FIELDS)
        if not exists:
            writer.writeheader()
        for url in urls:
            writer.writerow(
                {
                    "submitted_at": submitted_at,
                    "batch_id": batch_id,
                    "url": url,
                    "submission_type": submission_type,
                    "status": status_by_url.get(url, str(response.get("status", ""))),
                    "http_status": str(response.get("http_status", "")),
                    "success_count": str(response.get("success", "")),
                    "remain": str(response.get("remain", "")),
                    "message": str(response.get("message", "")),
                    "error": str(response.get("error", "")),
                }
            )


def read_submit_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def recently_submitted_urls(rows: list[dict[str, str]]) -> set[str]:
    return {
        row.get("url", "")
        for row in rows
        if row.get("status") in {"accepted", "submitted", "received"}
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_optional_import_csv(path: Path, expected_fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = read_submit_log(path)
    normalized: list[dict[str, str]] = []
    for row in rows:
        normalized.append({field: row.get(field, "") for field in expected_fields})
    return normalized
