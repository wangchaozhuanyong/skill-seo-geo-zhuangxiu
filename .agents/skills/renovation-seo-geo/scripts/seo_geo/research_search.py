#!/usr/bin/env python3
"""Generate and optionally fetch current internet search candidates for research."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

try:
    from .config import parse_simple_yaml
    from .research_discovery import (
        CANDIDATE_FIELDS,
        ResearchCandidate,
        build_queries,
        dedupe_sort,
        shell_quote,
        target_context,
        token_set,
    )
except ImportError:  # pragma: no cover - direct script execution
    from config import parse_simple_yaml
    from research_discovery import CANDIDATE_FIELDS, ResearchCandidate, build_queries, dedupe_sort, shell_quote, target_context, token_set


SEARCH_JSON_NAME = "research-search-candidates.json"
SEARCH_CSV_NAME = "research-search-candidates.csv"
SEARCH_REPORT_NAME = "research-search-report.md"
SEARCH_HANDOFF_NAME = "research-search-handoff.md"
DEFAULT_PROVIDER = "google-news-rss"
SUPPORTED_PROVIDERS = {"google-news-rss", "trusted-rss", "hybrid-rss"}
DEFAULT_FEEDS_CONFIG = "seo-workspace/config/research-search-feeds.example.yml"


@dataclass
class SearchResult:
    query: str
    url: str
    title: str
    publisher: str
    published_date: str
    snippet: str
    provider: str
    source_type: str = "industry"
    usage_note: str = "Use only for current industry/news context before drafting; verify source details with latest-research."
    claim_boundary: str = "Search result context only; not a FLASH CAST business claim, customer claim, price, timeline, warranty, or completed project proof."


@dataclass
class TrustedFeed:
    feed_id: str
    feed_url: str
    source_type: str = "industry"
    publisher: str = ""
    authority_score: int = 20
    usage_note: str = "Use only for current general guidance before drafting."
    claim_boundary: str = "External source context only; not a FLASH CAST business claim."


@dataclass
class ResearchSearchResult:
    status: str
    target_url: str
    provider: str
    queries: list[str] = field(default_factory=list)
    candidates: list[ResearchCandidate] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def search_queries(context: dict[str, str]) -> list[str]:
    base = build_queries(context)
    keyword = context.get("keyword", "")
    service = context.get("service", "")
    location = context.get("location", "")
    additions = [
        f"{keyword} latest".strip(),
        f"{service} Malaysia renovation trends".strip(),
        f"{service} {location} renovation guide".strip(),
        "Google Search Central structured data service page latest",
        "renovation material planning Malaysia latest",
    ]
    output: list[str] = []
    for query in [*base, *additions]:
        query = re.sub(r"\s+", " ", query).strip()
        if query and query not in output:
            output.append(query)
    return output


def fetch_google_news_rss(query: str, *, timeout: int, market: str = "MY", language: str = "en") -> list[SearchResult]:
    encoded = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl={language}-{market}&gl={market}&ceid={market}:{language}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; RenovationSeoGeoBot/1.0; +https://flashcast.com.my/)"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - public RSS search endpoint
        content = response.read(600_000)
    root = ET.fromstring(content)
    results: list[SearchResult] = []
    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title", ""))
        link = clean_text(item.findtext("link", ""))
        published = normalize_pub_date(clean_text(item.findtext("pubDate", "")))
        source = item.find("{*}source")
        publisher = clean_text(source.text if source is not None and source.text else "") or publisher_from_url(link)
        snippet = clean_text(item.findtext("description", ""))
        if link:
            results.append(
                SearchResult(
                    query=query,
                    url=link,
                    title=title or link,
                    publisher=publisher,
                    published_date=published or dt.date.today().isoformat(),
                    snippet=snippet,
                    provider="google-news-rss",
                )
            )
    return results


def render_feeds_example_config() -> str:
    return """# Trusted RSS/Atom feeds for current internet research candidates.
# These feeds provide external context only. They are not FLASH CAST claims.

feeds:
  google_search_central_blog:
    source_type: "search_engine"
    publisher: "Google Search Central"
    feed_url: "https://feeds.feedburner.com/blogspot/amDG"
    authority_score: 45
    usage_note: "Use only for current Google Search guidance and updates."
    claim_boundary: "Search-engine guidance only; not a FLASH CAST business claim."
  cidb_news:
    source_type: "government"
    publisher: "CIDB Malaysia"
    feed_url: "https://www.cidb.gov.my/feed/"
    authority_score: 35
    usage_note: "Use only for general Malaysia construction or renovation context when relevant."
    claim_boundary: "Government/industry context only; not a FLASH CAST business claim."
  design_material_inspiration:
    source_type: "industry"
    publisher: "Design and material planning source"
    feed_url: "https://example.com/feed.xml"
    authority_score: 15
    usage_note: "Replace this placeholder with a real trusted renovation/design/material feed before production use."
    claim_boundary: "General design inspiration only; not a FLASH CAST case, claim, price, or proof."
"""


def read_trusted_feeds(root: Path, feeds_config: str = "", write_example: bool = True) -> tuple[list[TrustedFeed], Path]:
    example_path = root / DEFAULT_FEEDS_CONFIG
    if write_example:
        write_text(example_path, render_feeds_example_config())
    config_file = Path(feeds_config) if feeds_config else example_path
    if not config_file.is_absolute():
        config_file = root / config_file
    raw = parse_simple_yaml(config_file)
    feeds_raw = raw.get("feeds", {}) if isinstance(raw.get("feeds"), dict) else {}
    feeds: list[TrustedFeed] = []
    for feed_id, value in feeds_raw.items():
        item = value if isinstance(value, dict) else {}
        feed_url = str(item.get("feed_url", "")).strip()
        if not feed_url or urlparse(feed_url).netloc == "example.com":
            continue
        feeds.append(
            TrustedFeed(
                feed_id=str(feed_id),
                feed_url=feed_url,
                source_type=str(item.get("source_type", "industry") or "industry"),
                publisher=str(item.get("publisher", "") or publisher_from_url(feed_url)),
                authority_score=int(item.get("authority_score", 20) or 20),
                usage_note=str(item.get("usage_note", "") or "Use only for current general guidance before drafting."),
                claim_boundary=str(item.get("claim_boundary", "") or "External source context only; not a FLASH CAST business claim."),
            )
        )
    return feeds, example_path


def fetch_url_text(url: str, *, timeout: int) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; RenovationSeoGeoBot/1.0; +https://flashcast.com.my/)"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - owner-configured trusted feed URL
        raw = response.read(800_000)
        encoding = response.headers.get_content_charset() or "utf-8"
        return raw.decode(encoding, errors="replace")


def find_xml_text(element: ET.Element, *names: str) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return clean_text(found.text)
    return ""


def find_atom_link(element: ET.Element) -> str:
    for link in element.findall("{*}link"):
        href = link.attrib.get("href", "")
        rel = link.attrib.get("rel", "alternate")
        if href and rel in {"alternate", ""}:
            return href
    return ""


def parse_rss_or_atom(content: str, feed: TrustedFeed, *, queries: list[str]) -> list[SearchResult]:
    root = ET.fromstring(content)
    items = root.findall(".//item")
    entries = root.findall(".//{*}entry")
    results: list[SearchResult] = []
    for item in items:
        title = find_xml_text(item, "title")
        link = find_xml_text(item, "link", "guid")
        published = normalize_pub_date(find_xml_text(item, "pubDate", "published", "updated"))
        snippet = find_xml_text(item, "description", "summary")
        if link:
            results.append(
                SearchResult(
                    query=queries[0] if queries else "",
                    url=link,
                    title=title or link,
                    publisher=feed.publisher or publisher_from_url(link),
                    published_date=published or dt.date.today().isoformat(),
                    snippet=snippet,
                    provider="trusted-rss",
                    source_type=feed.source_type,
                    usage_note=feed.usage_note,
                    claim_boundary=feed.claim_boundary,
                )
            )
    for entry in entries:
        title = find_xml_text(entry, "{*}title")
        link = find_atom_link(entry) or find_xml_text(entry, "{*}id")
        published = normalize_pub_date(find_xml_text(entry, "{*}published", "{*}updated"))
        snippet = find_xml_text(entry, "{*}summary", "{*}content")
        if link:
            results.append(
                SearchResult(
                    query=queries[0] if queries else "",
                    url=link,
                    title=title or link,
                    publisher=feed.publisher or publisher_from_url(link),
                    published_date=published or dt.date.today().isoformat(),
                    snippet=snippet,
                    provider="trusted-rss",
                    source_type=feed.source_type,
                    usage_note=feed.usage_note,
                    claim_boundary=feed.claim_boundary,
                )
            )
    return results


def fetch_trusted_feed(feed: TrustedFeed, *, timeout: int, queries: list[str]) -> list[SearchResult]:
    return parse_rss_or_atom(fetch_url_text(feed.feed_url, timeout=timeout), feed, queries=queries)


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_pub_date(value: str) -> str:
    if not value:
        return ""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return dt.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    match = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", value)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return ""


def publisher_from_url(url: str) -> str:
    host = urlparse(url).netloc
    return host.removeprefix("www.") if host else "external"


def score_search_result(result: SearchResult, queries: list[str]) -> int:
    query_tokens = token_set(*queries)
    result_tokens = token_set(result.url, result.title, result.snippet, result.publisher)
    relevance = len(query_tokens & result_tokens) * 5
    freshness = 0
    try:
        days_old = (dt.date.today() - dt.date.fromisoformat(result.published_date[:10])).days
        if days_old <= 14:
            freshness = 20
        elif days_old <= 60:
            freshness = 12
        elif days_old <= 180:
            freshness = 6
    except ValueError:
        freshness = 0
    provider_score = 25 if result.provider == "google-news-rss" else 35 if result.provider == "trusted-rss" else 5
    return provider_score + freshness + relevance


def to_candidate(result: SearchResult, *, target_url: str, all_queries: list[str]) -> ResearchCandidate:
    return ResearchCandidate(
        target_url=target_url,
        query=result.query,
        candidate_url=result.url,
        source_type=result.source_type,
        publisher=result.publisher or publisher_from_url(result.url),
        source_title=result.title or result.url,
        published_or_accessed_date=result.published_date or dt.date.today().isoformat(),
        score=score_search_result(result, all_queries),
        discovery_status=f"search_result:{result.provider}",
        usage_note=result.usage_note,
        claim_boundary=result.claim_boundary,
    )


def render_report(result: ResearchSearchResult) -> str:
    lines = [
        "# Current Internet Research Search Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Provider: `{result.provider}`",
        f"- Target URL: `{result.target_url or 'NEEDS OWNER INPUT'}`",
        f"- Candidate sources: {len(result.candidates)}",
        "- 执行状态: search-candidates only；未写入 source log、未发布、未写 CMS、未修改网站源码",
        "",
        "## 今日决策",
        "",
        "今天补上外部搜索候选层：按目标页面自动生成当前互联网查询，抓取或整理搜索候选，再交给 `research-intake` / `latest-research` 做正式抓取和 source log。这样比直接写文章更安全，因为搜索结果不会被直接当成公司事实或页面证明。",
        "",
        "## Queries",
        "",
    ]
    lines.extend(f"- {query}" for query in result.queries) if result.queries else lines.append("- None")
    lines.extend(["", "## Top Candidates", ""])
    if result.candidates:
        for candidate in result.candidates[:20]:
            lines.append(
                f"- score={candidate.score} | `{candidate.source_type}` | {candidate.publisher} | {candidate.source_title} | {candidate.candidate_url}"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Research Intake Handoff", ""])
    if result.candidates:
        lines.extend(
            [
                "```bash",
                "python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-intake \\",
                "  --candidates-path seo-workspace/data/research-search-candidates.json \\",
                f"  --target-url {shell_quote(result.target_url)} \\",
                "  --min-score 60",
                "```",
            ]
        )
    else:
        lines.append("- No candidate handoff available.")
    lines.extend(["", "## latest-research Handoff", ""])
    if result.candidates:
        top = result.candidates[0]
        lines.extend(
            [
                "```bash",
                "python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py latest-research \\",
                f"  --target-url {shell_quote(result.target_url)} \\",
                f"  --query {shell_quote(top.query)} \\",
                f"  --source {shell_quote(top.latest_research_arg())}",
                "```",
            ]
        )
    else:
        lines.append("- No latest-research handoff available.")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 搜索候选不等于已验证来源；发布前必须通过 latest-research 抓取并进入 source log。",
            "- 外部搜索结果只支持一般行业、材料、设计趋势、搜索规则或政策背景。",
            "- 不得把外部搜索结果写成 FLASH CAST 的价格、资质、奖项、服务区域、真实案例、客户评价、保修、工期或完工证明。",
            "- 不复制竞争对手页面文案，不自动发布，不自动修改 CMS/source。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, result: ResearchSearchResult) -> tuple[Path, Path, Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    drafts_dir = root / "seo-workspace" / "drafts"
    today = dt.date.today().isoformat()
    csv_path = data_dir / SEARCH_CSV_NAME
    json_path = data_dir / SEARCH_JSON_NAME
    report_path = reports_dir / f"{today}-{SEARCH_REPORT_NAME}"
    handoff_path = drafts_dir / f"{today}-{SEARCH_HANDOFF_NAME}"
    rows = [candidate.as_row() for candidate in result.candidates]
    result.artifacts.update(
        {
            "candidates_csv": str(csv_path),
            "candidates_json": str(json_path),
            "report": str(report_path),
            "handoff": str(handoff_path),
        }
    )
    write_csv(csv_path, rows)
    write_text(
        json_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "provider": result.provider,
                "target_url": result.target_url,
                "queries": result.queries,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "candidates": rows,
                "no_source_log_write": True,
                "no_live_actions_executed": True,
                "safety_note": "Search candidates are not verified claims. Use research-intake/latest-research before drafting or publishing.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    report = render_report(result)
    write_text(report_path, report)
    write_text(handoff_path, report)
    return csv_path, json_path, report_path, handoff_path


def run_research_search(
    root: Path,
    *,
    target_url: str = "",
    provider: str = DEFAULT_PROVIDER,
    fetch_remote: bool = True,
    timeout: int = 10,
    limit: int = 20,
    market: str = "MY",
    language: str = "en",
    feeds_config: str = "",
    write_feeds_example: bool = True,
) -> tuple[ResearchSearchResult, tuple[Path, Path, Path, Path]]:
    root = root.resolve()
    context = target_context(root, target_url)
    selected_target = context.get("url", "")
    queries = search_queries(context)
    blockers: list[str] = []
    warnings: list[str] = []
    if not selected_target:
        blockers.append("No target URL selected. Provide --target-url or seed keyword/opportunity data.")
    if provider not in SUPPORTED_PROVIDERS:
        blockers.append(f"Unsupported search provider: {provider}. Currently supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}.")
    results: list[SearchResult] = []
    if not blockers and fetch_remote:
        if provider in {"google-news-rss", "hybrid-rss"}:
            for query in queries:
                try:
                    results.extend(fetch_google_news_rss(query, timeout=timeout, market=market, language=language))
                except Exception as exc:  # noqa: BLE001 - search fetch failure must be visible, not fatal per query
                    warnings.append(f"Search fetch failed for `{query}`: {type(exc).__name__}: {exc}")
        if provider in {"trusted-rss", "hybrid-rss"}:
            feeds, feeds_example = read_trusted_feeds(root, feeds_config=feeds_config, write_example=write_feeds_example)
            warnings.append(f"Trusted RSS config example: {feeds_example}")
            if not feeds:
                warnings.append("No trusted RSS feeds configured; add real feed_url values to research-search-feeds.example.yml or pass --feeds-config.")
            for feed in feeds:
                try:
                    results.extend(fetch_trusted_feed(feed, timeout=timeout, queries=queries))
                except Exception as exc:  # noqa: BLE001 - per-feed failures should not hide other feed candidates
                    warnings.append(f"Trusted RSS fetch failed for `{feed.feed_id}`: {type(exc).__name__}: {exc}")
    elif not fetch_remote:
        warnings.append("Remote search fetching disabled; output contains query plan only.")
    candidates = dedupe_sort([to_candidate(item, target_url=selected_target, all_queries=queries) for item in results], limit)
    if not candidates and not blockers and fetch_remote:
        blockers.append("No search candidates found from current internet provider.")
    status = "research_search_candidates_ready_for_intake" if candidates and not blockers else "research_search_queries_ready" if not blockers else "research_search_blocked"
    result = ResearchSearchResult(
        status=status,
        target_url=selected_target,
        provider=provider,
        queries=queries,
        candidates=candidates,
        blockers=blockers,
        warnings=warnings,
    )
    artifacts = write_outputs(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and optionally fetch current internet search candidates for research.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--no-fetch-remote", action="store_true")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--market", default="MY")
    parser.add_argument("--language", default="en")
    parser.add_argument("--feeds-config", default="")
    parser.add_argument("--no-write-feeds-example", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_research_search(
        Path(args.root),
        target_url=args.target_url,
        provider=args.provider,
        fetch_remote=not args.no_fetch_remote,
        timeout=args.timeout,
        limit=args.limit,
        market=args.market,
        language=args.language,
        feeds_config=args.feeds_config,
        write_feeds_example=not args.no_write_feeds_example,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
