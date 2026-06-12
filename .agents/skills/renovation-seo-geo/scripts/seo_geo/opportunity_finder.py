#!/usr/bin/env python3
"""Find the highest-value SEO/GEO opportunity for the next daily task."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path
from typing import Optional


SEO_GEO_DIR = Path(__file__).resolve().parent
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))

from scoring import (  # noqa: E402
    OpportunityScore,
    normalize_url,
    score_candidate,
    score_sort_key,
)
from hreflang import expected_pair_url  # noqa: E402


SCORE_FIELDS = [
    "url",
    "keyword",
    "language",
    "page_type",
    "service",
    "location",
    "total_score",
    "task_type",
    "positive_events",
    "penalty_events",
]


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


def brand_website(root: Path) -> str:
    path = root / "seo-workspace" / "data" / "brand-profile.md"
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("- Website:"):
            return line.split(":", 1)[1].strip()
    return ""


def rows_by_url(rows: list[dict[str, str]], field: str = "url", base_url: str = "") -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        url = normalize_url(row.get(field, ""), base_url)
        if url and url not in output:
            output[url] = row
    return output


def performance_by_page(rows: list[dict[str, str]], base_url: str = "") -> dict[str, dict[str, str]]:
    return rows_by_url(rows, "page", base_url)


def performance_by_query(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("query", "").lower(): row for row in rows if row.get("query")}


def keyword_url(row: dict[str, str], base_url: str) -> str:
    return normalize_url(row.get("target_url") or row.get("current_url", ""), base_url)


def combine_performance(
    *,
    keyword_row: dict[str, str],
    url: str,
    page_performance: dict[str, dict[str, str]],
    query_performance: dict[str, dict[str, str]],
) -> dict[str, str]:
    if url in page_performance:
        return page_performance[url]
    keyword = keyword_row.get("keyword", "").lower()
    return query_performance.get(keyword, {})


def score_to_row(score: OpportunityScore) -> dict[str, str]:
    return {
        "url": score.url,
        "keyword": score.keyword,
        "language": score.language,
        "page_type": score.page_type,
        "service": score.service,
        "location": score.location,
        "total_score": str(score.total_score),
        "task_type": score.task_type,
        "positive_events": "; ".join(f"{event.label} (+{event.points})" for event in score.positive_events),
        "penalty_events": "; ".join(f"{event.label} ({event.points})" for event in score.penalty_events),
    }


def build_opportunity_scores(root: Path) -> list[OpportunityScore]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    base_url = brand_website(root) or "https://flashcast.com.my/"

    keyword_rows = read_csv_rows(data_dir / "keyword-map.csv")
    inventory_rows = read_csv_rows(data_dir / "url-inventory.csv")
    internal_links = read_csv_rows(data_dir / "internal-links.csv")
    case_rows = read_csv_rows(data_dir / "case-studies.csv")
    service_areas = read_csv_rows(data_dir / "service-areas.csv")
    gsc_pages = read_csv_rows(data_dir / "gsc-pages.csv")
    gsc_queries = read_csv_rows(data_dir / "gsc-queries.csv")
    google_index_rows = read_csv_rows(data_dir / "google-index-status.csv")

    inventory_by_url = rows_by_url(inventory_rows, "url", base_url)
    google_index_by_url = rows_by_url(google_index_rows, "url", base_url)
    page_performance = performance_by_page(gsc_pages, base_url)
    query_performance = performance_by_query(gsc_queries)
    inventory_urls = set(inventory_by_url)

    scores: list[OpportunityScore] = []
    scored_urls: set[str] = set()
    for keyword_row in keyword_rows:
        url = keyword_url(keyword_row, base_url)
        if not url:
            continue
        inventory_row = inventory_by_url.get(url, {})
        score = score_candidate(
            url=url,
            keyword_row=keyword_row,
            inventory_row=inventory_row,
            performance_row=combine_performance(
                keyword_row=keyword_row,
                url=url,
                page_performance=page_performance,
                query_performance=query_performance,
            ),
            google_index_row=google_index_by_url.get(url, {}),
            inventory_urls=inventory_urls,
            internal_links=internal_links,
            case_rows=case_rows,
            service_areas=service_areas,
        )
        scores.append(score)
        scored_urls.add(url)

    for url, inventory_row in inventory_by_url.items():
        if url in scored_urls:
            continue
        scores.append(
            score_candidate(
                url=url,
                inventory_row=inventory_row,
                performance_row=page_performance.get(url, {}),
                google_index_row=google_index_by_url.get(url, {}),
                inventory_urls=inventory_urls,
                internal_links=internal_links,
                case_rows=case_rows,
                service_areas=service_areas,
            )
        )

    return sorted(scores, key=score_sort_key, reverse=True)


def event_lines(score: OpportunityScore) -> list[str]:
    lines: list[str] = []
    for event in score.events:
        sign = "+" if event.points > 0 else ""
        note = f" - {event.note}" if event.note else ""
        lines.append(f"- {event.label}: {sign}{event.points}{note}")
    return lines


def build_report(scores: list[OpportunityScore], root: Path, score_csv_path: Path) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    selected: Optional[OpportunityScore] = scores[0] if scores else None
    lines = [
        "# SEO Opportunity Score Report",
        "",
        f"- 生成时间: {now}",
        f"- 仓库: `{root}`",
        f"- 评分 CSV: `{score_csv_path}`",
        f"- 候选任务数: {len(scores)}",
        "",
        "## 今日决策",
        "",
    ]
    if selected:
        pair_url = expected_pair_url(selected.url)
        lines.extend(
            [
                f"- 今日最高价值任务: `{selected.url}`",
                f"- 配对页面: `{pair_url or 'N/A'}`",
                f"- 目标关键词: {selected.keyword or 'NEEDS OWNER INPUT: no keyword mapped'}",
                f"- 页面类型: {selected.page_type}",
                f"- 内容类型: {selected.task_type}",
                f"- 机会总分: {selected.total_score}",
                "- 为什么今天做这个: 该页面/关键词在当前评分中商业价值、页面类型和可优化信号组合最高；系统按分数选择，不随机写文章。",
                "",
                "## 最高分原因",
                "",
            ]
        )
        lines.extend(event_lines(selected))
    else:
        lines.append("- NEEDS OWNER INPUT: 没有可评分 URL。")

    lines.extend(
        [
            "",
            "## Top Opportunities",
            "",
        ]
    )
    for index, score in enumerate(scores[:20], start=1):
        lines.append(
            f"{index}. `{score.url}` | score={score.total_score} | type={score.task_type} | keyword={score.keyword or '-'}"
        )

    lines.extend(
        [
            "",
            "## 评分规则摘要",
            "",
            "- commercial intent +5; local commercial intent +5; service page +5; location page +4。",
            "- GSC position 2-3 +6; 4-10 +5; 11-20 +4; high impressions low CTR +4; indexed but low CTR +3。",
            "- missing FAQ +1; missing schema +1; weak CTA +2; weak internal links +2。",
            "- no case proof -1; unsupported location -10; duplicate city-swap risk -8; missing language pair -3。",
            "- not indexable -10; robots blocked -10; noindex -10; wrong canonical -8。",
            "",
            "## QA Checklist",
            "",
            "- [ ] 抽查最高分页面是否与业务高价值服务一致。",
            "- [ ] 如 GSC/百度/IndexNow 凭证未接入，不要把缺失 API 数据当作已排名或已收录事实。",
            "- [ ] 执行每日任务时优先选择最高分页面，不随机写文章。",
            "- [ ] 对 service/local 页面先做 FAQ、schema、CTA、内链和案例/概念证明增强。",
            "- [ ] 不创建重复城市门页，不伪造案例、评价、价格或服务区域。",
            "",
            "## 执行状态",
            "",
            "- 已生成 SEO 机会评分报告；未发布内容，未修改 live 网站，等待后续内容生成阶段或业主明确执行指令。",
            "",
        ]
    )
    return "\n".join(lines)


def run_opportunity_finder(root: Path) -> list[OpportunityScore]:
    root = root.resolve()
    scores = build_opportunity_scores(root)
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    score_csv_path = data_dir / "seo-opportunity-scores.csv"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-seo-opportunity-score.md"
    write_csv(score_csv_path, [score_to_row(score) for score in scores], SCORE_FIELDS)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(scores, root, score_csv_path), encoding="utf-8")
    return scores


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score SEO/GEO opportunities and select the next daily task.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scores = run_opportunity_finder(Path(args.root))
    print(f"Generated SEO opportunity scores: {len(scores)}")
    if scores:
        print(f"Top opportunity: {scores[0].url} score={scores[0].total_score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
