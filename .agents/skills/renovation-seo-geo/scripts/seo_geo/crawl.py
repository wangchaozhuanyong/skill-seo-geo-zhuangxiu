#!/usr/bin/env python3
"""Build a URL inventory and technical SEO audit report."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlsplit

try:
    from .canonical import extract_canonical_url, is_self_canonical
    from .hreflang import extract_hreflang_links, has_hreflang_pair
    from .http_checks import fetch_url, status_issue
    from .robots_sitemap import (
        SitemapEntry,
        find_local_sitemaps,
        parse_robots_txt,
        parse_sitemap_xml,
        read_sitemap_file,
        robots_allowed,
        robots_url_for,
    )
    from .url_inventory import (
        UrlCandidate,
        blank_inventory_row,
        collect_from_internal_links,
        collect_from_keyword_map,
        collect_from_seo_manifest,
        dedupe_candidates,
        normalize_url,
        priority_issue,
        write_inventory_csv,
    )
except ImportError:  # pragma: no cover - used when running as a script file
    from canonical import extract_canonical_url, is_self_canonical
    from hreflang import extract_hreflang_links, has_hreflang_pair
    from http_checks import fetch_url, status_issue
    from robots_sitemap import (
        SitemapEntry,
        find_local_sitemaps,
        parse_robots_txt,
        parse_sitemap_xml,
        read_sitemap_file,
        robots_allowed,
        robots_url_for,
    )
    from url_inventory import (
        UrlCandidate,
        blank_inventory_row,
        collect_from_internal_links,
        collect_from_keyword_map,
        collect_from_seo_manifest,
        dedupe_candidates,
        normalize_url,
        priority_issue,
        write_inventory_csv,
    )


@dataclass
class PageSignals:
    title: str = ""
    meta_description: str = ""
    meta_robots: str = ""
    h1: str = ""
    word_count: int = 0
    internal_outlinks: set[str] = field(default_factory=set)
    schema_types: set[str] = field(default_factory=set)
    image_count: int = 0
    missing_alt_count: int = 0


class _HtmlSignalsParser(HTMLParser):
    def __init__(self, page_url: str, base_url: str = "") -> None:
        super().__init__()
        self.page_url = page_url
        self.base_url = base_url
        self.signals = PageSignals()
        self._in_title = False
        self._in_h1 = False
        self._in_script_json_ld = False
        self._title_parts: list[str] = []
        self._h1_parts: list[str] = []
        self._text_parts: list[str] = []
        self._json_ld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        data = {key.lower(): value or "" for key, value in attrs}
        if tag_lower == "title":
            self._in_title = True
        elif tag_lower == "h1":
            self._in_h1 = True
        elif tag_lower == "meta":
            name = data.get("name", "").lower()
            if name == "description":
                self.signals.meta_description = data.get("content", "").strip()
            elif name == "robots":
                self.signals.meta_robots = data.get("content", "").strip()
        elif tag_lower == "a":
            href = data.get("href", "").strip()
            if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                self.signals.internal_outlinks.add(urljoin(self.page_url or self.base_url, href))
        elif tag_lower == "img":
            self.signals.image_count += 1
            if not data.get("alt", "").strip():
                self.signals.missing_alt_count += 1
        elif tag_lower == "script" and data.get("type", "").lower() == "application/ld+json":
            self._in_script_json_ld = True
            self._json_ld_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "title":
            self._in_title = False
            self.signals.title = _clean_text(" ".join(self._title_parts))
        elif tag_lower == "h1":
            self._in_h1 = False
            if not self.signals.h1:
                self.signals.h1 = _clean_text(" ".join(self._h1_parts))
        elif tag_lower == "script" and self._in_script_json_ld:
            self._in_script_json_ld = False
            self.signals.schema_types.update(_extract_schema_types("".join(self._json_ld_parts)))

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        elif self._in_h1:
            self._h1_parts.append(data)
        elif self._in_script_json_ld:
            self._json_ld_parts.append(data)
        else:
            self._text_parts.append(data)

    def close(self) -> None:
        super().close()
        visible_text = _clean_text(" ".join(self._text_parts))
        self.signals.word_count = len([word for word in re.split(r"\s+", visible_text) if len(word) > 1])


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _extract_schema_types(raw_json: str) -> set[str]:
    def walk(value: object) -> set[str]:
        found: set[str] = set()
        if isinstance(value, dict):
            item_type = value.get("@type")
            if isinstance(item_type, str):
                found.add(item_type)
            elif isinstance(item_type, list):
                found.update(str(item) for item in item_type if item)
            for child in value.values():
                found.update(walk(child))
        elif isinstance(value, list):
            for child in value:
                found.update(walk(child))
        return found

    try:
        return walk(json.loads(raw_json))
    except json.JSONDecodeError:
        return set()


def parse_html_signals(html: str, page_url: str, base_url: str = "") -> PageSignals:
    parser = _HtmlSignalsParser(page_url=page_url, base_url=base_url)
    parser.feed(html or "")
    parser.close()
    return parser.signals


def local_html_path_for_url(root: Path, url: str, base_url: str = "") -> Optional[Path]:
    parsed = urlsplit(url)
    if base_url and parsed.netloc and parsed.netloc != urlsplit(base_url).netloc:
        return None
    path = parsed.path.strip("/")
    candidates = []
    if not path:
        candidates.extend([root / "index.html", root / "dist" / "index.html", root / "public" / "index.html"])
    else:
        candidates.extend(
            [
                root / path,
                root / f"{path}.html",
                root / path / "index.html",
                root / "dist" / path / "index.html",
                root / "dist" / f"{path}.html",
                root / "public" / path / "index.html",
                root / "public" / f"{path}.html",
            ]
        )
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _is_remote_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def collect_url_candidates(root: Path, base_url: str = "", extra_urls: Optional[list[str]] = None) -> tuple[list[UrlCandidate], dict[str, SitemapEntry]]:
    candidates: list[UrlCandidate] = []
    sitemap_entries: dict[str, SitemapEntry] = {}

    for sitemap_path in find_local_sitemaps(root):
        for entry in read_sitemap_file(sitemap_path):
            normalized = normalize_url(entry.loc, base_url)
            if normalized:
                sitemap_entry = SitemapEntry(loc=normalized, lastmod=entry.lastmod)
                sitemap_entries[normalized] = sitemap_entry
                candidates.append(UrlCandidate(url=normalized, source="sitemap", lastmod=entry.lastmod))

    for manifest_path in (root / "public" / "seo-manifest.json", root / "dist" / "seo-manifest.json", root / "seo-manifest.json"):
        candidates.extend(collect_from_seo_manifest(manifest_path, base_url))

    data_dir = root / "seo-workspace" / "data"
    candidates.extend(collect_from_keyword_map(data_dir / "keyword-map.csv", base_url))
    candidates.extend(collect_from_internal_links(data_dir / "internal-links.csv", base_url))

    for url in extra_urls or []:
        normalized = normalize_url(url, base_url)
        if normalized:
            candidates.append(UrlCandidate(url=normalized, source="cli"))

    return dedupe_candidates(candidates), sitemap_entries


def _load_robots_text(
    root: Path,
    base_url: str = "",
    fetch_remote: bool = False,
    timeout: int = 8,
) -> str:
    for path in (root / "public" / "robots.txt", root / "dist" / "robots.txt", root / "robots.txt"):
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
    if fetch_remote and base_url:
        result = fetch_url(robots_url_for(base_url), read_body=True, timeout=timeout)
        if result.status_code == 200:
            return result.body
    return ""


def collect_remote_sitemap_entries(
    base_url: str,
    robots_text: str = "",
    timeout: int = 8,
) -> dict[str, SitemapEntry]:
    sitemap_urls = parse_robots_txt(robots_text).sitemaps if robots_text else []
    if not sitemap_urls and base_url:
        sitemap_urls = [urljoin(base_url.rstrip("/") + "/", "sitemap.xml")]

    entries: dict[str, SitemapEntry] = {}
    for sitemap_url in sitemap_urls:
        result = fetch_url(sitemap_url, read_body=True, timeout=timeout)
        if result.status_code != 200 or not result.body:
            continue
        try:
            parsed_entries = parse_sitemap_xml(result.body)
        except Exception:
            continue
        for entry in parsed_entries:
            normalized = normalize_url(entry.loc, base_url)
            if normalized:
                entries[normalized] = SitemapEntry(loc=normalized, lastmod=entry.lastmod)
    return entries


def build_inventory_rows(
    candidates: list[UrlCandidate],
    *,
    root: Path,
    base_url: str = "",
    robots_text: str = "",
    sitemap_entries: Optional[dict[str, SitemapEntry]] = None,
    fetch_remote: bool = False,
    timeout: int = 8,
) -> list[dict[str, str]]:
    sitemap_entries = sitemap_entries or {}
    rows: list[dict[str, str]] = []
    outlink_map: dict[str, set[str]] = {}

    for candidate in candidates:
        row = blank_inventory_row(candidate.url, page_type=candidate.page_type, lastmod=candidate.lastmod)
        if candidate.url in sitemap_entries:
            row["sitemap_included"] = "yes"
            row["lastmod"] = sitemap_entries[candidate.url].lastmod

        allowed = robots_allowed(candidate.url, robots_text)
        row["robots_allowed"] = "yes" if allowed else "no"

        html = ""
        status_code = ""
        if fetch_remote and _is_remote_url(candidate.url):
            result = fetch_url(candidate.url, timeout=timeout)
            status_code = str(result.status_code or 0)
            html = result.body if "html" in result.content_type.lower() else ""
            issue = status_issue(result.status_code)
            if issue:
                row["priority_issue"] = issue
        else:
            local_path = local_html_path_for_url(root, candidate.url, base_url)
            if local_path:
                status_code = "200"
                html = local_path.read_text(encoding="utf-8", errors="replace")

        row["status_code"] = status_code

        if html:
            signals = parse_html_signals(html, candidate.url, base_url)
            canonical_url = extract_canonical_url(html, candidate.url)
            hreflang_links = extract_hreflang_links(html, candidate.url)
            row.update(
                {
                    "meta_robots": signals.meta_robots,
                    "canonical_url": canonical_url,
                    "canonical_self": "yes" if is_self_canonical(candidate.url, canonical_url) else "no",
                    "hreflang_pair": "yes" if has_hreflang_pair(candidate.url, hreflang_links) else "no",
                    "title": signals.title,
                    "meta_description": signals.meta_description,
                    "h1": signals.h1,
                    "word_count": str(signals.word_count),
                    "internal_outlinks_count": str(len(signals.internal_outlinks)),
                    "schema_types": ";".join(sorted(signals.schema_types)),
                    "image_count": str(signals.image_count),
                    "missing_alt_count": str(signals.missing_alt_count),
                }
            )
            outlink_map[candidate.url] = signals.internal_outlinks

        noindex = "noindex" in row.get("meta_robots", "").lower()
        status_ok = row["status_code"] == "200"
        canonical_ok = row["canonical_self"] in {"unknown", "yes"}
        if not row["status_code"] and not html:
            row["indexable"] = "unknown"
            row["priority_issue"] = row["priority_issue"] or "html_not_available"
        else:
            row["indexable"] = "yes" if status_ok and allowed and not noindex and canonical_ok else "no"
        if not row["priority_issue"]:
            row["priority_issue"] = priority_issue(row)
        rows.append(row)

    row_urls = {row["url"] for row in rows}
    inlink_counts = {url: 0 for url in row_urls}
    for outlinks in outlink_map.values():
        for target in outlinks:
            if target in inlink_counts:
                inlink_counts[target] += 1
    for row in rows:
        row["internal_inlinks_count"] = str(inlink_counts.get(row["url"], 0))
    return rows


def build_technical_audit_report(rows: list[dict[str, str]], root: Path, inventory_path: Path) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    issue_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    indexable_counts: dict[str, int] = {}
    sitemap_counts: dict[str, int] = {}
    canonical_counts: dict[str, int] = {}
    hreflang_counts: dict[str, int] = {}
    for row in rows:
        issue = row.get("priority_issue") or "none"
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
        for counts, key in (
            (status_counts, "status_code"),
            (indexable_counts, "indexable"),
            (sitemap_counts, "sitemap_included"),
            (canonical_counts, "canonical_self"),
            (hreflang_counts, "hreflang_pair"),
        ):
            value = row.get(key) or "blank"
            counts[value] = counts.get(value, 0) + 1

    lines = [
        "# Technical SEO/GEO Audit",
        "",
        f"- 生成时间: {now}",
        f"- 仓库: `{root}`",
        f"- URL 清单: `{inventory_path}`",
        f"- URL 数量: {len(rows)}",
        "",
        "## 今日结论",
        "",
        "- 本报告是第三阶段 URL Inventory 与 Crawl 系统的技术审计输出。",
        "- 它不代表页面已经被 Google、百度或 Bing 收录；它只判断页面是否具备被抓取、被索引、被理解的基础条件。",
        "- 如果 `status_code` 为空，说明当前仓库没有可匹配的本地 HTML，且本次没有启用远程抓取。",
        "",
        "## 抓取覆盖率",
        "",
        f"- HTTP 状态码: {_format_counts(status_counts)}",
        f"- 可索引判断: {_format_counts(indexable_counts)}",
        f"- Sitemap 收录清单包含: {_format_counts(sitemap_counts)}",
        f"- Canonical self: {_format_counts(canonical_counts)}",
        f"- Hreflang pair: {_format_counts(hreflang_counts)}",
        "",
        "## 问题汇总",
        "",
    ]
    for issue, count in sorted(issue_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {issue}: {count}")

    lines.extend(
        [
            "",
            "## 高优先级 URL",
            "",
        ]
    )
    flagged = [row for row in rows if row.get("priority_issue")]
    for row in flagged[:30]:
        lines.append(f"- `{row['url']}`: {row.get('priority_issue')}")
    if not flagged:
        lines.append("- 暂无高优先级技术问题。")

    lines.extend(
        [
            "",
            "## QA Checklist",
            "",
            "- [ ] 抽查 `url-inventory.csv` 中的核心服务页 URL 是否完整。",
            "- [ ] 对核心 `/en` 与 `/zh` 页面检查 canonical 是否指向自身。",
            "- [ ] 对核心双语页面检查 hreflang 是否互相指向。",
            "- [ ] 对 sitemap 内 URL 检查是否返回 200 且没有 noindex。",
            "- [ ] 对图片较多页面检查缺失 alt 的图片。",
            "- [ ] 如要做 Google/Baidu/Bing 提交，先确认页面 200、可索引、robots 允许、canonical self、sitemap included。",
            "",
            "## 执行状态",
            "",
            "- 工具能力已生成本地报告；未提交搜索引擎索引，未登录 CMS，未修改 live 网站。",
            "",
        ]
    )
    return "\n".join(lines)


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def run_inventory_audit(
    *,
    root: Path,
    base_url: str = "",
    output_inventory: Optional[Path] = None,
    output_report: Optional[Path] = None,
    extra_urls: Optional[list[str]] = None,
    fetch_remote: bool = False,
    timeout: int = 8,
    add_remote_sitemap_urls: bool = True,
) -> list[dict[str, str]]:
    root = root.resolve()
    output_inventory = output_inventory or root / "seo-workspace" / "data" / "url-inventory.csv"
    output_report = output_report or root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-technical-seo-audit.md"
    candidates, sitemap_entries = collect_url_candidates(root, base_url, extra_urls)
    robots_text = _load_robots_text(root, base_url=base_url, fetch_remote=fetch_remote, timeout=timeout)
    if fetch_remote and base_url:
        remote_sitemap_entries = collect_remote_sitemap_entries(base_url, robots_text, timeout=timeout)
        sitemap_entries.update(remote_sitemap_entries)
        if add_remote_sitemap_urls:
            candidates = dedupe_candidates(
                candidates
                + [
                    UrlCandidate(url=entry.loc, source="remote-sitemap", lastmod=entry.lastmod)
                    for entry in remote_sitemap_entries.values()
                ]
            )
    rows = build_inventory_rows(
        candidates,
        root=root,
        base_url=base_url,
        robots_text=robots_text,
        sitemap_entries=sitemap_entries,
        fetch_remote=fetch_remote,
        timeout=timeout,
    )
    write_inventory_csv(rows, output_inventory)
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(build_technical_audit_report(rows, root, output_inventory), encoding="utf-8")
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SEO/GEO URL inventory and technical audit report.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--base-url", default="", help="Optional production base URL for relative paths.")
    parser.add_argument("--url", action="append", default=[], help="Extra URL to include. Can be passed multiple times.")
    parser.add_argument("--fetch-remote", action="store_true", help="Fetch remote HTTP URLs instead of local-only analysis.")
    parser.add_argument("--timeout", type=int, default=8, help="Per-request timeout in seconds for remote fetches.")
    parser.add_argument(
        "--no-add-remote-sitemap-urls",
        action="store_true",
        help="Use remote sitemap for inclusion checks without adding every sitemap URL to the crawl queue.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = run_inventory_audit(
        root=Path(args.root),
        base_url=args.base_url,
        extra_urls=args.url,
        fetch_remote=args.fetch_remote,
        timeout=args.timeout,
        add_remote_sitemap_urls=not args.no_add_remote_sitemap_urls,
    )
    print(f"Generated URL inventory rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
