#!/usr/bin/env python3
"""Fetch and log latest-source research for SEO/GEO content packages."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SOURCE_LOG_FIELDS = [
    "date_added",
    "target_url",
    "source_type",
    "source_title",
    "source_url",
    "publisher",
    "published_or_accessed_date",
    "usage_note",
    "claim_boundary",
]

LATEST_SOURCE_FIELDS = SOURCE_LOG_FIELDS + [
    "query",
    "final_url",
    "http_status",
    "fetch_status",
    "fetched_at",
    "meta_description",
]


@dataclass
class ResearchFetch:
    source_url: str
    target_url: str
    query: str = ""
    source_type: str = "external"
    source_title: str = ""
    publisher: str = ""
    published_or_accessed_date: str = ""
    usage_note: str = "Use for current general guidance only."
    claim_boundary: str = "general guidance only; not a FLASH CAST business claim"
    final_url: str = ""
    http_status: str = ""
    fetch_status: str = "not_checked"
    fetched_at: str = ""
    meta_description: str = ""

    def source_log_row(self) -> dict[str, str]:
        today = dt.date.today().isoformat()
        return {
            "date_added": today,
            "target_url": self.target_url,
            "source_type": self.source_type,
            "source_title": self.source_title or self.source_url,
            "source_url": self.source_url,
            "publisher": self.publisher or publisher_from_url(self.source_url),
            "published_or_accessed_date": self.published_or_accessed_date or today,
            "usage_note": self.usage_note,
            "claim_boundary": self.claim_boundary,
        }

    def latest_row(self) -> dict[str, str]:
        row = self.source_log_row()
        row.update(
            {
                "query": self.query,
                "final_url": self.final_url,
                "http_status": self.http_status,
                "fetch_status": self.fetch_status,
                "fetched_at": self.fetched_at,
                "meta_description": self.meta_description,
            }
        )
        return row


@dataclass
class LatestResearchResult:
    target_url: str
    queries: list[str]
    sources: list[ResearchFetch] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def publisher_from_url(url: str) -> str:
    host = urlparse(url).netloc or urlparse(url).path
    return host.removeprefix("www.") or "external"


def extract_tag(content: str, pattern: str) -> str:
    match = re.search(pattern, content, flags=re.I | re.S)
    if not match:
        return ""
    return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def extract_title(content: str) -> str:
    return extract_tag(content, r"<title[^>]*>(.*?)</title>") or extract_meta(content, "og:title") or extract_meta(content, "twitter:title")


def extract_meta(content: str, name: str) -> str:
    escaped = re.escape(name)
    patterns = [
        rf"<meta[^>]+(?:name|property)=[\"']{escaped}[\"'][^>]+content=[\"']([^\"']+)[\"'][^>]*>",
        rf"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+(?:name|property)=[\"']{escaped}[\"'][^>]*>",
    ]
    for pattern in patterns:
        value = extract_tag(content, pattern)
        if value:
            return value
    return ""


def extract_date(content: str) -> str:
    for key in ("article:published_time", "datePublished", "pubdate", "publishdate", "date"):
        value = extract_meta(content, key)
        if value:
            return value[:10]
    match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', content, flags=re.I)
    return match.group(1)[:10] if match else ""


def fetch_url(url: str, *, timeout: int = 10) -> tuple[str, str, str, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; RenovationSeoGeoBot/1.0; +https://flashcast.com.my/)"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-provided research URLs are expected
        raw = response.read(600_000)
        content_type = response.headers.get_content_charset() or "utf-8"
        text = raw.decode(content_type, errors="replace")
        status = str(response.getcode() or "")
        final_url = response.geturl()
        return text, status, final_url, "fetched"


def fetch_source(
    url: str,
    *,
    target_url: str,
    query: str = "",
    source_type: str = "external",
    usage_note: str = "Use for current general guidance only.",
    claim_boundary: str = "general guidance only; not a FLASH CAST business claim",
    timeout: int = 10,
) -> ResearchFetch:
    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    result = ResearchFetch(
        source_url=url,
        target_url=target_url,
        query=query,
        source_type=source_type,
        usage_note=usage_note,
        claim_boundary=claim_boundary,
        fetched_at=fetched_at,
    )
    try:
        content, status, final_url, fetch_status = fetch_url(url, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - report fetch failure as research status
        result.fetch_status = f"failed: {type(exc).__name__}"
        result.publisher = publisher_from_url(url)
        result.published_or_accessed_date = dt.date.today().isoformat()
        return result
    result.http_status = status
    result.final_url = final_url
    result.fetch_status = fetch_status
    result.source_title = extract_title(content) or final_url
    result.publisher = extract_meta(content, "og:site_name") or publisher_from_url(final_url)
    result.published_or_accessed_date = extract_date(content) or dt.date.today().isoformat()
    result.meta_description = extract_meta(content, "description") or extract_meta(content, "og:description")
    return result


def parse_source_arg(value: str) -> dict[str, str]:
    # type|url|usage note|claim boundary|query
    parts = [part.strip() for part in value.split("|")]
    parts += [""] * (5 - len(parts))
    return {
        "source_type": parts[0] or "external",
        "source_url": parts[1],
        "usage_note": parts[2] or "Use for current general guidance only.",
        "claim_boundary": parts[3] or "general guidance only; not a FLASH CAST business claim",
        "query": parts[4],
    }


def append_unique_source_log(root: Path, rows: Iterable[dict[str, str]]) -> Path:
    path = root / "seo-workspace" / "data" / "research-source-log.csv"
    existing = read_csv_rows(path)
    seen = {(row.get("target_url", ""), row.get("source_url", "")) for row in existing}
    next_rows = list(existing)
    for row in rows:
        key = (row.get("target_url", ""), row.get("source_url", ""))
        if key not in seen:
            next_rows.append(row)
            seen.add(key)
    return write_csv(path, next_rows, SOURCE_LOG_FIELDS)


def render_report(result: LatestResearchResult) -> str:
    lines = [
        "# Latest Source Research Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Target URL: `{result.target_url or 'NEEDS OWNER INPUT'}`",
        f"- Sources checked: {len(result.sources)}",
        "- 执行状态: research-only；未发布、未写 CMS、未修改网站源码",
        "",
        "## 今日决策",
        "",
        "今天补齐最新资料研究入口：把联网搜索/抓取到的来源转成可追踪 source log、研究报告和内容包输入，避免后续文章或服务页引用没有出处的最新事实。",
        "",
        "## Queries",
        "",
    ]
    lines.extend(f"- {query}" for query in result.queries) if result.queries else lines.append("- None provided")
    lines.extend(["", "## Sources", ""])
    if result.sources:
        for source in result.sources:
            lines.append(f"- `{source.fetch_status}` | {source.source_title or source.source_url} | {source.publisher} | {source.source_url}")
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Claim Boundaries",
            "",
            "- 外部来源只支持一般行业、材料、设计趋势、搜索规则或政策解释。",
            "- 外部来源不能证明 FLASH CAST 的价格、资质、奖项、服务区域、真实案例、客户评价、保修或工期。",
            "- 发布前如使用当前事实，必须保留 source log，并在页面文案中避免把第三方资料写成公司承诺。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def run_latest_research(
    root: Path,
    *,
    target_url: str = "",
    queries: list[str] | None = None,
    sources: list[str] | None = None,
    timeout: int = 10,
) -> tuple[LatestResearchResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    queries = queries or []
    sources = sources or []
    parsed_sources = [parse_source_arg(value) for value in sources]
    valid_sources = [item for item in parsed_sources if item["source_url"]]
    fetched = [
        fetch_source(
            item["source_url"],
            target_url=target_url,
            query=item["query"],
            source_type=item["source_type"],
            usage_note=item["usage_note"],
            claim_boundary=item["claim_boundary"],
            timeout=timeout,
        )
        for item in valid_sources
    ]
    blockers: list[str] = []
    warnings: list[str] = []
    if not target_url:
        warnings.append("Target URL missing; source log rows will not be tied to a publish target.")
    if queries and not sources:
        blockers.append("Queries were provided but no source URLs were supplied. Use Codex/web search, then pass selected URLs with --source.")
    if sources and not valid_sources:
        blockers.append("Source arguments were provided, but none contained a valid URL.")
    if not queries and not sources:
        blockers.append("No queries or source URLs provided.")
    failed = [source.source_url for source in fetched if source.fetch_status.startswith("failed")]
    if failed:
        warnings.append("Some sources could not be fetched: " + ", ".join(failed))

    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    drafts_dir = root / "seo-workspace" / "drafts"
    today = dt.date.today().isoformat()
    latest_path = data_dir / "latest-research-sources.csv"
    source_log_path = append_unique_source_log(root, [source.source_log_row() for source in fetched if not source.fetch_status.startswith("failed")])
    existing_latest = read_csv_rows(latest_path)
    write_csv(latest_path, existing_latest + [source.latest_row() for source in fetched], LATEST_SOURCE_FIELDS)
    report_path = reports_dir / f"{today}-latest-research-report.md"
    brief_path = drafts_dir / f"{today}-latest-research-brief.md"
    result = LatestResearchResult(target_url=target_url, queries=queries, sources=fetched, blockers=blockers, warnings=warnings)
    result.artifacts.update({"latest_sources": str(latest_path), "source_log": str(source_log_path), "report": str(report_path), "brief": str(brief_path)})
    write_text(report_path, render_report(result))
    write_text(brief_path, render_report(result))
    return result, (latest_path, report_path, brief_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and log latest-source research for SEO/GEO content.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="")
    parser.add_argument("--query", action="append", default=[], help="Research query to document. Repeatable.")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source as type|url|usage note|claim boundary|query. Repeatable.",
    )
    parser.add_argument("--timeout", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_latest_research(
        Path(args.root),
        target_url=args.target_url,
        queries=args.query,
        sources=args.source,
        timeout=args.timeout,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
