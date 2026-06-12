#!/usr/bin/env python3
"""Discover candidate latest-research sources from trusted seeds."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit
from urllib.request import Request, urlopen

try:
    from .config import parse_simple_yaml
except ImportError:  # pragma: no cover - direct script execution
    from config import parse_simple_yaml


CANDIDATE_FIELDS = [
    "target_url",
    "query",
    "candidate_url",
    "source_type",
    "publisher",
    "source_title",
    "published_or_accessed_date",
    "score",
    "discovery_status",
    "usage_note",
    "claim_boundary",
    "latest_research_source_arg",
]


@dataclass
class TrustedSeed:
    seed_id: str
    seed_url: str
    source_type: str = "external"
    publisher: str = ""
    discovery_mode: str = "page"
    usage_note: str = "Use for current general guidance only."
    claim_boundary: str = "general guidance only; not a FLASH CAST business claim"
    authority_score: int = 10


@dataclass
class ResearchCandidate:
    target_url: str
    query: str
    candidate_url: str
    source_type: str
    publisher: str
    source_title: str
    published_or_accessed_date: str
    score: int
    discovery_status: str
    usage_note: str
    claim_boundary: str

    def as_row(self) -> dict[str, str]:
        return {
            "target_url": self.target_url,
            "query": self.query,
            "candidate_url": self.candidate_url,
            "source_type": self.source_type,
            "publisher": self.publisher,
            "source_title": self.source_title,
            "published_or_accessed_date": self.published_or_accessed_date,
            "score": str(self.score),
            "discovery_status": self.discovery_status,
            "usage_note": self.usage_note,
            "claim_boundary": self.claim_boundary,
            "latest_research_source_arg": self.latest_research_arg(),
        }

    def latest_research_arg(self) -> str:
        return "|".join(
            [
                self.source_type,
                self.candidate_url,
                self.usage_note,
                self.claim_boundary,
                self.query,
            ]
        )


@dataclass
class ResearchDiscoveryResult:
    status: str
    target_url: str
    queries: list[str] = field(default_factory=list)
    candidates: list[ResearchCandidate] = field(default_factory=list)
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


def brand_website(root: Path) -> str:
    path = root / "seo-workspace" / "data" / "brand-profile.md"
    if not path.exists():
        return "https://flashcast.com.my/"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("- Website:"):
            return line.split(":", 1)[1].strip() or "https://flashcast.com.my/"
    return "https://flashcast.com.my/"


def normalize_url(value: str, base_url: str) -> str:
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value.rstrip("/")
    if value.startswith("/"):
        return base_url.rstrip("/") + value
    return value.rstrip("/")


def target_context(root: Path, target_url: str = "") -> dict[str, str]:
    base_url = brand_website(root)
    scores = read_csv_rows(root / "seo-workspace" / "data" / "seo-opportunity-scores.csv")
    keyword_rows = read_csv_rows(root / "seo-workspace" / "data" / "keyword-map.csv")
    selected: dict[str, str] = {}
    normalized_target = normalize_url(target_url, base_url)
    if normalized_target:
        for row in scores:
            if normalize_url(row.get("url", ""), base_url) == normalized_target:
                selected = row
                break
        if not selected:
            path = urlsplit(normalized_target).path
            for row in keyword_rows:
                if row.get("target_url") == path or row.get("current_url") == path:
                    selected = {
                        "url": normalized_target,
                        "keyword": row.get("keyword", ""),
                        "page_type": row.get("page_type", ""),
                        "service": row.get("service", ""),
                        "location": row.get("location", ""),
                    }
                    break
    if not selected and scores:
        selected = scores[0]
    if not selected and keyword_rows:
        row = keyword_rows[0]
        selected = {
            "url": normalize_url(row.get("target_url") or row.get("current_url", ""), base_url),
            "keyword": row.get("keyword", ""),
            "page_type": row.get("page_type", ""),
            "service": row.get("service", ""),
            "location": row.get("location", ""),
        }
    selected.setdefault("url", normalized_target)
    selected.setdefault("keyword", "")
    selected.setdefault("page_type", "")
    selected.setdefault("service", "")
    selected.setdefault("location", "")
    return selected


def build_queries(context: dict[str, str]) -> list[str]:
    keyword = context.get("keyword", "")
    service = context.get("service", "")
    location = context.get("location", "")
    page_type = context.get("page_type", "")
    queries = []
    for value in (
        keyword,
        f"{service} {location} renovation planning".strip(),
        f"{service} material planning guidance".strip(),
    ):
        if value and value not in queries:
            queries.append(value)
    if page_type == "service":
        queries.append("renovation service page FAQ schema guidance")
    if page_type == "article":
        queries.append(f"{keyword} latest guide".strip())
    if not queries:
        queries.append("renovation planning guidance")
    return queries


def source_type_score(source_type: str) -> int:
    return {
        "official": 45,
        "government": 45,
        "search_engine": 40,
        "manufacturer": 30,
        "standards": 30,
        "industry": 20,
        "external": 10,
    }.get(source_type, 10)


def token_set(*values: str) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for token in re.findall(r"[a-z0-9\u4e00-\u9fff]{2,}", value.lower()):
            if token not in {"https", "http", "www", "com", "html"}:
                tokens.add(token)
    return tokens


def score_candidate(seed: TrustedSeed, *, url: str, title: str, description: str, queries: list[str]) -> int:
    query_tokens = token_set(*queries)
    candidate_tokens = token_set(url, title, description)
    relevance = len(query_tokens & candidate_tokens) * 5
    exact = 10 if any(query.lower() in f"{title} {url}".lower() for query in queries if query) else 0
    return seed.authority_score + source_type_score(seed.source_type) + relevance + exact


def read_trusted_seeds(root: Path, config_path: str = "", write_example: bool = True) -> tuple[list[TrustedSeed], Path]:
    config_dir = root / "seo-workspace" / "config"
    example_path = config_dir / "research-sources.example.yml"
    if write_example:
        write_text(example_path, render_example_config())
    config_file = Path(config_path) if config_path else example_path
    if not config_file.is_absolute():
        config_file = root / config_file
    raw = parse_simple_yaml(config_file)
    sources = raw.get("sources", {}) if isinstance(raw.get("sources"), dict) else {}
    seeds: list[TrustedSeed] = []
    for seed_id, value in sources.items():
        item = value if isinstance(value, dict) else {}
        seed_url = str(item.get("seed_url", "")).strip()
        if not seed_url:
            continue
        seeds.append(
            TrustedSeed(
                seed_id=str(seed_id),
                seed_url=seed_url,
                source_type=str(item.get("source_type", "external") or "external"),
                publisher=str(item.get("publisher", "") or publisher_from_url(seed_url)),
                discovery_mode=str(item.get("discovery_mode", "page") or "page"),
                usage_note=str(item.get("usage_note", "") or "Use for current general guidance only."),
                claim_boundary=str(item.get("claim_boundary", "") or "general guidance only; not a FLASH CAST business claim"),
                authority_score=int(item.get("authority_score", 10) or 10),
            )
        )
    return seeds, example_path


def render_example_config() -> str:
    return """# Trusted latest-research source discovery seeds.
# These are not FLASH CAST business claims. They only help find general guidance sources.

sources:
  google_search_central_structured_data:
    source_type: "search_engine"
    publisher: "Google Search Central"
    seed_url: "https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data"
    discovery_mode: "page"
    authority_score: 50
    usage_note: "Use only for search visibility, structured data, and schema guidance."
    claim_boundary: "Search-engine guidance only; not a FLASH CAST business claim."
  google_search_central_blog:
    source_type: "search_engine"
    publisher: "Google Search Central"
    seed_url: "https://developers.google.com/search/blog"
    discovery_mode: "page"
    authority_score: 45
    usage_note: "Use only for current Google Search guidance and updates."
    claim_boundary: "Search-engine guidance only; not a FLASH CAST business claim."
  schema_org_service:
    source_type: "standards"
    publisher: "Schema.org"
    seed_url: "https://schema.org/Service"
    discovery_mode: "page"
    authority_score: 35
    usage_note: "Use only for schema type and property planning."
    claim_boundary: "Schema vocabulary guidance only; not a FLASH CAST business claim."
  malaysia_home_renovation_general:
    source_type: "industry"
    publisher: "General renovation planning source"
    seed_url: "https://www.cidb.gov.my/"
    discovery_mode: "page"
    authority_score: 20
    usage_note: "Use only for general Malaysia construction or renovation context when relevant."
    claim_boundary: "General external context only; not a FLASH CAST business claim."
"""


def publisher_from_url(url: str) -> str:
    host = urlparse(url).netloc
    return host.removeprefix("www.") if host else "external"


def fetch_url(url: str, *, timeout: int) -> tuple[str, str, str]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; RenovationSeoGeoBot/1.0; +https://flashcast.com.my/)"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - trusted owner-configured source seeds
        raw = response.read(800_000)
        encoding = response.headers.get_content_charset() or "utf-8"
        return raw.decode(encoding, errors="replace"), str(response.getcode() or ""), response.geturl()


def extract_title(content: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", content, flags=re.I | re.S)
    if not match:
        return ""
    return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def extract_meta_description(content: str) -> str:
    patterns = [
        r"<meta[^>]+(?:name|property)=[\"']description[\"'][^>]+content=[\"']([^\"']+)[\"'][^>]*>",
        r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+(?:name|property)=[\"']description[\"'][^>]*>",
        r"<meta[^>]+(?:property)=[\"']og:description[\"'][^>]+content=[\"']([^\"']+)[\"'][^>]*>",
    ]
    for pattern in patterns:
        match = re.search(pattern, content, flags=re.I | re.S)
        if match:
            return html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())
    return ""


def extract_date(content: str) -> str:
    for pattern in (
        r"<meta[^>]+(?:property|name)=[\"']article:published_time[\"'][^>]+content=[\"']([^\"']+)[\"']",
        r"<meta[^>]+(?:property|name)=[\"']datePublished[\"'][^>]+content=[\"']([^\"']+)[\"']",
        r'"datePublished"\s*:\s*"([^"]+)"',
        r"<lastmod>([^<]+)</lastmod>",
        r"<pubDate>([^<]+)</pubDate>",
    ):
        match = re.search(pattern, content, flags=re.I | re.S)
        if match:
            return match.group(1).strip()[:10]
    return dt.date.today().isoformat()


def extract_links(content: str, base_url: str) -> list[str]:
    links: list[str] = []
    for match in re.finditer(r"href=[\"']([^\"'#]+)[\"']", content, flags=re.I):
        value = urljoin(base_url, html.unescape(match.group(1).strip()))
        if is_reference_page_url(value) and value not in links:
            links.append(value)
    for match in re.finditer(r"<loc>([^<]+)</loc>", content, flags=re.I):
        value = html.unescape(match.group(1).strip())
        if is_reference_page_url(value) and value not in links:
            links.append(value)
    return links


def is_reference_page_url(url: str) -> bool:
    if not url.startswith(("http://", "https://")):
        return False
    parsed = urlsplit(url)
    lowered_path = parsed.path.lower()
    if any(part in lowered_path for part in ("/feed", "/comments/feed", "/wp-json/", "/oembed/")):
        return False
    if lowered_path.endswith("/xmlrpc.php"):
        return False
    if re.search(r"\.(css|js|json|xml|ico|png|jpg|jpeg|gif|svg|webp|pdf|zip|gz|txt)$", lowered_path):
        return False
    if parsed.query.startswith("hl="):
        return False
    return True


def discover_from_seed(
    seed: TrustedSeed,
    *,
    target_url: str,
    queries: list[str],
    fetch_remote: bool,
    timeout: int,
    per_seed_limit: int,
) -> tuple[list[ResearchCandidate], list[str]]:
    warnings: list[str] = []
    today = dt.date.today().isoformat()
    candidates: list[ResearchCandidate] = []
    content = ""
    final_url = seed.seed_url
    status = "seed_not_fetched"
    if fetch_remote:
        try:
            content, http_status, final_url = fetch_url(seed.seed_url, timeout=timeout)
            status = f"fetched:{http_status}"
        except Exception as exc:  # noqa: BLE001 - report and keep seed as candidate
            status = f"fetch_failed:{type(exc).__name__}"
            warnings.append(f"{seed.seed_id} fetch failed: {type(exc).__name__}")
    title = extract_title(content) if content else seed.publisher or seed.seed_url
    description = extract_meta_description(content) if content else ""
    date_value = extract_date(content) if content else today
    best_query = queries[0] if queries else ""
    candidates.append(
        ResearchCandidate(
            target_url=target_url,
            query=best_query,
            candidate_url=final_url,
            source_type=seed.source_type,
            publisher=seed.publisher or publisher_from_url(final_url),
            source_title=title or final_url,
            published_or_accessed_date=date_value,
            score=score_candidate(seed, url=final_url, title=title, description=description, queries=queries),
            discovery_status=status,
            usage_note=seed.usage_note,
            claim_boundary=seed.claim_boundary,
        )
    )
    if content and seed.discovery_mode in {"page", "rss", "sitemap"}:
        for link in extract_links(content, final_url)[: per_seed_limit * 4]:
            if len(candidates) >= per_seed_limit:
                break
            if not same_or_known_host(final_url, link):
                continue
            link_title = title_from_url(link)
            score = score_candidate(seed, url=link, title=link_title, description="", queries=queries)
            if score <= seed.authority_score + source_type_score(seed.source_type):
                continue
            candidates.append(
                ResearchCandidate(
                    target_url=target_url,
                    query=best_query,
                    candidate_url=link,
                    source_type=seed.source_type,
                    publisher=seed.publisher or publisher_from_url(link),
                    source_title=link_title,
                    published_or_accessed_date=today,
                    score=score,
                    discovery_status=f"discovered_from:{seed.seed_id}",
                    usage_note=seed.usage_note,
                    claim_boundary=seed.claim_boundary,
                )
            )
    return candidates, warnings


def same_or_known_host(seed_url: str, candidate_url: str) -> bool:
    seed_host = urlparse(seed_url).netloc
    candidate_host = urlparse(candidate_url).netloc
    return bool(seed_host and candidate_host and (candidate_host == seed_host or candidate_host.endswith("." + seed_host)))


def title_from_url(url: str) -> str:
    path = urlsplit(url).path.strip("/")
    if not path:
        return publisher_from_url(url)
    slug = path.rsplit("/", 1)[-1]
    return re.sub(r"[-_]+", " ", slug).strip().title() or url


def dedupe_sort(candidates: list[ResearchCandidate], limit: int) -> list[ResearchCandidate]:
    seen: set[str] = set()
    output: list[ResearchCandidate] = []
    for candidate in sorted(candidates, key=lambda item: (item.score, item.source_type), reverse=True):
        key = candidate.candidate_url.rstrip("/")
        if key in seen:
            continue
        output.append(candidate)
        seen.add(key)
        if len(output) >= limit:
            break
    return output


def render_report(result: ResearchDiscoveryResult) -> str:
    lines = [
        "# Research Source Discovery Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{result.target_url or 'NEEDS OWNER INPUT'}`",
        f"- Candidate sources: {len(result.candidates)}",
        "- 执行状态: discovery-only；未写入 source log、未发布、未写 CMS、未修改网站源码",
        "",
        "## 今日决策",
        "",
        "今天补上最新资料自动发现层：从可信来源种子抓取候选 URL，按权威性和相关性评分，输出给 `latest-research` 进一步抓取/入库。候选来源不等于已采用事实来源。",
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
        lines.append("- No candidate handoff available.")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 候选来源只支持一般行业、搜索规则、材料、设计或政策背景，不证明 FLASH CAST 的业务事实。",
            "- 不自动复制竞争对手内容，不自动发布，不自动把候选 URL 写入页面。",
            "- 只有通过 `research-intake` 或显式 `latest-research --source` 抓取并进入 `research-source-log.csv` 后，才可作为后续内容包 source log 输入。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def write_outputs(root: Path, result: ResearchDiscoveryResult, example_path: Path) -> tuple[Path, Path, Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    drafts_dir = root / "seo-workspace" / "drafts"
    today = dt.date.today().isoformat()
    csv_path = data_dir / "research-discovery-candidates.csv"
    json_path = data_dir / "research-discovery-candidates.json"
    report_path = reports_dir / f"{today}-research-discovery-report.md"
    handoff_path = drafts_dir / f"{today}-research-source-selection.md"
    result.artifacts.update(
        {
            "trusted_sources_example": str(example_path),
            "candidates_csv": str(csv_path),
            "candidates_json": str(json_path),
            "report": str(report_path),
            "selection_handoff": str(handoff_path),
        }
    )
    rows = [candidate.as_row() for candidate in result.candidates]
    write_csv(csv_path, rows, CANDIDATE_FIELDS)
    write_text(
        json_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "target_url": result.target_url,
                "queries": result.queries,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "candidates": rows,
                "no_source_log_write": True,
                "no_live_actions_executed": True,
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


def run_research_discovery(
    root: Path,
    *,
    target_url: str = "",
    config_path: str = "",
    fetch_remote: bool = True,
    timeout: int = 10,
    per_seed_limit: int = 5,
    limit: int = 20,
    write_example: bool = True,
) -> tuple[ResearchDiscoveryResult, tuple[Path, Path, Path, Path]]:
    root = root.resolve()
    context = target_context(root, target_url)
    selected_target = context.get("url", "")
    queries = build_queries(context)
    seeds, example_path = read_trusted_seeds(root, config_path=config_path, write_example=write_example)
    blockers: list[str] = []
    warnings: list[str] = []
    if not selected_target:
        blockers.append("No target URL selected. Provide --target-url or seed keyword/opportunity data.")
    if not seeds:
        blockers.append("No trusted research seeds configured.")
    candidates: list[ResearchCandidate] = []
    if not blockers:
        for seed in seeds:
            seed_candidates, seed_warnings = discover_from_seed(
                seed,
                target_url=selected_target,
                queries=queries,
                fetch_remote=fetch_remote,
                timeout=timeout,
                per_seed_limit=per_seed_limit,
            )
            candidates.extend(seed_candidates)
            warnings.extend(seed_warnings)
    candidates = dedupe_sort(candidates, limit)
    if not candidates and not blockers:
        blockers.append("No research source candidates found from trusted seeds.")
    status = "research_candidates_ready_for_selection" if not blockers else "research_discovery_blocked"
    result = ResearchDiscoveryResult(status=status, target_url=selected_target, queries=queries, candidates=candidates, blockers=blockers, warnings=warnings)
    artifacts = write_outputs(root, result, example_path)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover candidate latest-research sources from trusted seeds.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="")
    parser.add_argument("--config-path", default="")
    parser.add_argument("--no-fetch-remote", action="store_true")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--per-seed-limit", type=int, default=5)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--no-write-example", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_research_discovery(
        Path(args.root),
        target_url=args.target_url,
        config_path=args.config_path,
        fetch_remote=not args.no_fetch_remote,
        timeout=args.timeout,
        per_seed_limit=args.per_seed_limit,
        limit=args.limit,
        write_example=not args.no_write_example,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
