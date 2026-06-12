"""Google Search Console integration helpers.

This module never stores secrets. Credentials must be supplied through
environment variables that point to files outside the repository.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


SEARCH_ANALYTICS_FIELDS = [
    "query",
    "page",
    "country",
    "device",
    "date",
    "clicks",
    "impressions",
    "ctr",
    "position",
]

GSC_QUERY_FIELDS = [
    "query",
    "clicks",
    "impressions",
    "ctr",
    "position",
]

GSC_PAGE_FIELDS = [
    "page",
    "clicks",
    "impressions",
    "ctr",
    "position",
]

URL_INSPECTION_FIELDS = [
    "url",
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
    "raw_error",
]

GSC_READONLY_SCOPES = ("https://www.googleapis.com/auth/webmasters.readonly",)
GSC_FULL_SCOPES = ("https://www.googleapis.com/auth/webmasters",)


@dataclass
class GoogleSearchConsoleConfig:
    site_url: str = ""
    google_application_credentials: str = ""
    oauth_client_config: str = ""
    oauth_token_json: str = ""

    @classmethod
    def from_env(cls, site_url: str = "") -> "GoogleSearchConsoleConfig":
        return cls(
            site_url=site_url or os.environ.get("GSC_SITE_URL", ""),
            google_application_credentials=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
            oauth_client_config=os.environ.get("GSC_OAUTH_CLIENT_CONFIG", ""),
            oauth_token_json=os.environ.get("GSC_OAUTH_TOKEN_JSON", ""),
        )

    def credential_mode(self) -> str:
        if self.google_application_credentials:
            return "service_account"
        if self.oauth_client_config or self.oauth_token_json:
            return "oauth"
        return "not_configured"

    def missing_configuration(self) -> list[str]:
        missing: list[str] = []
        if not self.site_url:
            missing.append("GSC_SITE_URL")
        if self.google_application_credentials:
            if not Path(self.google_application_credentials).expanduser().exists():
                missing.append("GOOGLE_APPLICATION_CREDENTIALS file")
        elif self.oauth_client_config or self.oauth_token_json:
            if not self.oauth_client_config:
                missing.append("GSC_OAUTH_CLIENT_CONFIG")
            elif not Path(self.oauth_client_config).expanduser().exists():
                missing.append("GSC_OAUTH_CLIENT_CONFIG file")
            if not self.oauth_token_json:
                missing.append("GSC_OAUTH_TOKEN_JSON")
            elif not Path(self.oauth_token_json).expanduser().exists():
                missing.append("GSC_OAUTH_TOKEN_JSON file")
        else:
            missing.append("GOOGLE_APPLICATION_CREDENTIALS or OAuth config")
        return missing

    def can_use_api(self) -> bool:
        return not self.missing_configuration()


def _load_credentials(config: GoogleSearchConsoleConfig, scopes: tuple[str, ...]) -> Any:
    if config.google_application_credentials:
        from google.oauth2 import service_account  # type: ignore

        return service_account.Credentials.from_service_account_file(
            str(Path(config.google_application_credentials).expanduser()),
            scopes=list(scopes),
        )

    if config.oauth_token_json:
        from google.oauth2.credentials import Credentials  # type: ignore

        return Credentials.from_authorized_user_file(
            str(Path(config.oauth_token_json).expanduser()),
            scopes=list(scopes),
        )

    raise RuntimeError("Google Search Console credentials are not configured")


def build_search_console_service(
    config: GoogleSearchConsoleConfig,
    *,
    readonly: bool = True,
) -> Any:
    if not config.can_use_api():
        raise RuntimeError("Google Search Console configuration missing: " + ", ".join(config.missing_configuration()))

    from googleapiclient.discovery import build  # type: ignore

    scopes = GSC_READONLY_SCOPES if readonly else GSC_FULL_SCOPES
    credentials = _load_credentials(config, scopes)
    return build("searchconsole", "v1", credentials=credentials, cache_discovery=False)


def normalize_search_analytics_response(
    response: dict[str, Any],
    dimensions: list[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in response.get("rows", []) or []:
        keys = item.get("keys", []) or []
        row = {field: "" for field in SEARCH_ANALYTICS_FIELDS}
        for index, dimension in enumerate(dimensions):
            if dimension in row and index < len(keys):
                row[dimension] = str(keys[index])
        row["clicks"] = str(item.get("clicks", 0))
        row["impressions"] = str(item.get("impressions", 0))
        row["ctr"] = str(item.get("ctr", 0))
        row["position"] = str(item.get("position", 0))
        rows.append(row)
    return rows


def query_search_analytics(
    service: Any,
    config: GoogleSearchConsoleConfig,
    *,
    start_date: str,
    end_date: str,
    dimensions: Optional[list[str]] = None,
    row_limit: int = 25000,
) -> list[dict[str, str]]:
    dimensions = dimensions or ["query", "page", "country", "device", "date"]
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    response = service.searchanalytics().query(siteUrl=config.site_url, body=body).execute()
    return normalize_search_analytics_response(response, dimensions)


def normalize_url_inspection_response(url: str, response: dict[str, Any]) -> dict[str, str]:
    result = response.get("inspectionResult", {}) or {}
    index_status = result.get("indexStatusResult", {}) or {}
    mobile = result.get("mobileUsabilityResult", {}) or {}
    rich = result.get("richResultsResult", {}) or {}
    return {
        "url": url,
        "inspection_state": "checked",
        "verdict": str(index_status.get("verdict", "")),
        "coverage_state": str(index_status.get("coverageState", "")),
        "indexing_state": str(index_status.get("indexingState", "")),
        "page_fetch_state": str(index_status.get("pageFetchState", "")),
        "robots_txt_state": str(index_status.get("robotsTxtState", "")),
        "google_canonical": str(index_status.get("googleCanonical", "")),
        "user_canonical": str(index_status.get("userCanonical", "")),
        "last_crawl_time": str(index_status.get("lastCrawlTime", "")),
        "referring_urls": ";".join(str(item) for item in index_status.get("referringUrls", []) or []),
        "mobile_usability_verdict": str(mobile.get("verdict", "")),
        "rich_results_verdict": str(rich.get("verdict", "")),
        "raw_error": "",
    }


def inspect_url(service: Any, config: GoogleSearchConsoleConfig, url: str) -> dict[str, str]:
    body = {"inspectionUrl": url, "siteUrl": config.site_url}
    try:
        response = service.urlInspection().index().inspect(body=body).execute()
    except Exception as exc:
        row = {field: "" for field in URL_INSPECTION_FIELDS}
        row.update({"url": url, "inspection_state": "error", "raw_error": str(exc)})
        return row
    return normalize_url_inspection_response(url, response)


def submit_sitemap(service: Any, config: GoogleSearchConsoleConfig, sitemap_url: str) -> dict[str, str]:
    response = service.sitemaps().submit(siteUrl=config.site_url, feedpath=sitemap_url).execute()
    return {
        "site_url": config.site_url,
        "sitemap_url": sitemap_url,
        "result": "submitted",
        "response": str(response or {}),
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def aggregate_search_rows(rows: list[dict[str, str]], key: str, fields: list[str]) -> list[dict[str, str]]:
    totals: dict[str, dict[str, float]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value:
            continue
        bucket = totals.setdefault(value, {"clicks": 0.0, "impressions": 0.0, "position_weight": 0.0})
        clicks = _to_float(row.get("clicks", "0"))
        impressions = _to_float(row.get("impressions", "0"))
        position = _to_float(row.get("position", "0"))
        bucket["clicks"] += clicks
        bucket["impressions"] += impressions
        bucket["position_weight"] += position * impressions

    output: list[dict[str, str]] = []
    for value, total in totals.items():
        impressions = total["impressions"]
        clicks = total["clicks"]
        ctr = clicks / impressions if impressions else 0.0
        position = total["position_weight"] / impressions if impressions else 0.0
        output.append(
            {
                key: value,
                "clicks": f"{clicks:.0f}",
                "impressions": f"{impressions:.0f}",
                "ctr": f"{ctr:.6f}",
                "position": f"{position:.2f}",
            }
        )
    return sorted(output, key=lambda item: _to_float(item.get("impressions", "0")), reverse=True)


def write_search_analytics_outputs(root: Path, rows: list[dict[str, str]]) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    queries_path = data_dir / "gsc-queries.csv"
    pages_path = data_dir / "gsc-pages.csv"
    query_rows = aggregate_search_rows(rows, "query", GSC_QUERY_FIELDS)
    page_rows = aggregate_search_rows(rows, "page", GSC_PAGE_FIELDS)
    write_csv(queries_path, query_rows, GSC_QUERY_FIELDS)
    write_csv(pages_path, page_rows, GSC_PAGE_FIELDS)
    return queries_path, pages_path
