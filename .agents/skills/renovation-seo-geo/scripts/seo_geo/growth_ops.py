#!/usr/bin/env python3
"""Professional SEO/GEO growth operations reports.

These commands fill the non-publishing daily operating gaps: performance
review, AI-search monitoring prompts, competitor gap tracking, local citation
readiness, and real proof asset requests. They only write local artifacts.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

try:
    from .post_publish_feedback import run_post_publish_feedback
except ImportError:  # pragma: no cover
    from post_publish_feedback import run_post_publish_feedback


DATA_DIR = Path("seo-workspace") / "data"
REPORTS_DIR = Path("seo-workspace") / "reports"
CONFIG_DIR = Path("seo-workspace") / "config"

PERFORMANCE_FIELDS = [
    "priority",
    "url",
    "keyword",
    "language",
    "task_type",
    "total_score",
    "clicks",
    "impressions",
    "ctr",
    "position",
    "recommended_action",
    "notes",
]

AI_SEARCH_FIELDS = [
    "query",
    "language",
    "surface",
    "expected_entity",
    "expected_canonical_url",
    "pass_criteria",
    "notes",
]

COMPETITOR_FIELDS = [
    "competitor",
    "competitor_url",
    "check_area",
    "current_flash_cast_status",
    "manual_check_status",
    "recommended_action",
    "priority",
]

CITATION_FIELDS = [
    "platform",
    "profile_url",
    "nap_status",
    "owner_action",
    "priority",
    "notes",
]

PROOF_FIELDS = [
    "asset_type",
    "related_service",
    "related_url",
    "needed_from_owner",
    "why_it_matters",
    "claim_boundary",
    "priority",
]

DATA_HEALTH_FIELDS = [
    "source",
    "required_for",
    "status",
    "rows",
    "decision_use",
    "owner_action",
    "notes",
]

LEAD_QUALITY_FIELDS = [
    "date",
    "source",
    "campaign",
    "ad_group",
    "keyword",
    "search_term",
    "landing_page",
    "contact_channel",
    "service_type",
    "service_area",
    "lead_quality",
    "quoted",
    "won",
    "revenue_myr",
    "cost_myr",
    "owner_notes",
    "decision_label",
]

ADS_DECISION_FIELDS = [
    "priority",
    "scope",
    "entity",
    "observed_signal",
    "decision",
    "recommended_action",
    "owner_approval_required",
    "reason",
    "safety_guardrail",
]

COMPETITOR_MONITOR_FIELDS = [
    "competitor",
    "competitor_url",
    "weekly_check_area",
    "last_checked",
    "change_status",
    "recommended_action",
    "priority",
    "notes",
]

LOCAL_VERIFICATION_FIELDS = [
    "asset",
    "official_url",
    "ownership_status",
    "nap_status",
    "category_status",
    "photo_status",
    "review_status",
    "service_area_status",
    "next_action",
    "priority",
]

WEEKLY_CONTROL_FIELDS = [
    "priority",
    "area",
    "finding",
    "recommended_action",
    "owner_input_needed",
    "blocked_actions",
    "evidence",
]

INVALID_SEARCH_INTENT_TERMS = [
    "job",
    "vacancy",
    "salary",
    "course",
    "training",
    "diy",
    "template",
    "pdf",
    "software",
    "second hand",
    "招聘",
    "找工",
    "工作",
    "空缺",
    "薪水",
    "课程",
    "培训",
    "教学",
    "教程",
    "自己做",
    "模板",
    "软件",
    "二手",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows: list[dict[str, str]] = []
        for row in csv.DictReader(handle):
            cleaned: dict[str, str] = {}
            for key, value in row.items():
                if key is None:
                    continue
                if isinstance(value, list):
                    cleaned[key] = ",".join(value).strip()
                else:
                    cleaned[key] = (value or "").strip()
            rows.append(cleaned)
        return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_report(root: Path, slug: str, lines: list[str]) -> Path:
    path = root / REPORTS_DIR / f"{dt.date.today().isoformat()}-{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def data_path(root: Path, filename: str) -> Path:
    return root / DATA_DIR / filename


def config_path(root: Path, filename: str) -> Path:
    return root / CONFIG_DIR / filename


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def file_status(path: Path) -> tuple[str, int, str]:
    if not path.exists():
        return "missing", 0, ""
    if path.suffix.lower() == ".csv":
        rows = read_csv_rows(path)
        status = "ready" if rows else "empty"
        mtime = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).astimezone().isoformat(timespec="seconds")
        return status, len(rows), mtime
    text = read_text(path).strip()
    status = "ready" if text else "empty"
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    return status, 1 if text else 0, mtime


def parse_number(value: str) -> float:
    try:
        return float((value or "").replace(",", "").replace("MYR", "").replace("RM", "").replace("%", "").strip())
    except ValueError:
        return 0.0


def parse_int_like(value: str) -> int:
    try:
        return int(float((value or "").replace(",", "").strip()))
    except ValueError:
        return 0


def truthy(value: str) -> bool:
    return (value or "").strip().lower() in {"yes", "y", "true", "1", "won", "converted", "成交", "是"}


def contains_invalid_intent(text: str) -> bool:
    haystack = (text or "").lower()
    return any(term.lower() in haystack for term in INVALID_SEARCH_INTENT_TERMS)


def brand_value(root: Path, label: str) -> str:
    text = read_text(data_path(root, "brand-profile.md"))
    pattern = re.compile(rf"^-\s*{re.escape(label)}:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def brand_website(root: Path) -> str:
    return brand_value(root, "Website") or "https://flashcast.com.my/"


def company_name(root: Path) -> str:
    return brand_value(root, "Company name") or "FLASH CAST"


def write_lead_quality_example(root: Path) -> Path:
    path = config_path(root, "lead-quality-log.example.csv")
    if path.exists():
        return path
    sample = [
        {
            "date": "2026-06-13",
            "source": "Google Ads",
            "campaign": "Search - Renovation Leads - KL Selangor",
            "ad_group": "广告组 1",
            "keyword": "附近装修公司",
            "search_term": "附近装修公司",
            "landing_page": "https://flashcast.com.my/zh/services/renovation",
            "contact_channel": "WhatsApp",
            "service_type": "住宅装修",
            "service_area": "Kuala Lumpur",
            "lead_quality": "high|medium|low|spam|unknown",
            "quoted": "yes|no|unknown",
            "won": "yes|no|unknown",
            "revenue_myr": "",
            "cost_myr": "",
            "owner_notes": "Only write real owner-confirmed lead outcome here.",
            "decision_label": "keep|add_negative|pause_candidate|landing_page_issue|needs_owner_review",
        }
    ]
    return write_csv(path, sample, LEAD_QUALITY_FIELDS)


def write_google_ads_performance_examples(root: Path) -> list[Path]:
    search_terms_path = config_path(root, "google-ads-search-terms.example.csv")
    keyword_path = config_path(root, "google-ads-keyword-performance.example.csv")
    if not search_terms_path.exists():
        write_csv(
            search_terms_path,
            [
                {
                    "date": "2026-06-13",
                    "campaign": "Search - Renovation Leads - KL Selangor",
                    "ad_group": "广告组 1",
                    "keyword": "附近装修公司",
                    "match_type": "phrase",
                    "search_term": "附近装修公司",
                    "clicks": "0",
                    "impressions": "0",
                    "cost_myr": "0",
                    "conversions": "0",
                    "status": "under_review",
                }
            ],
            [
                "date",
                "campaign",
                "ad_group",
                "keyword",
                "match_type",
                "search_term",
                "clicks",
                "impressions",
                "cost_myr",
                "conversions",
                "status",
            ],
        )
    if not keyword_path.exists():
        write_csv(
            keyword_path,
            [
                {
                    "date": "2026-06-13",
                    "campaign": "Search - Renovation Leads - KL Selangor",
                    "ad_group": "广告组 1",
                    "keyword": "附近装修公司",
                    "match_type": "phrase",
                    "clicks": "0",
                    "impressions": "0",
                    "cost_myr": "0",
                    "conversions": "0",
                    "avg_cpc_myr": "0",
                    "status": "eligible|under_review|low_search_volume|paused",
                }
            ],
            [
                "date",
                "campaign",
                "ad_group",
                "keyword",
                "match_type",
                "clicks",
                "impressions",
                "cost_myr",
                "conversions",
                "avg_cpc_myr",
                "status",
            ],
        )
    return [search_terms_path, keyword_path]


def write_growth_intelligence_example(root: Path) -> Path:
    path = config_path(root, "growth-intelligence.example.yml")
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Growth intelligence loop example.",
                "# Copy to growth-intelligence.yml for local use. Do not store secrets.",
                "data_sources:",
                "  gsc_pages_csv: seo-workspace/data/gsc-pages.csv",
                "  gsc_queries_csv: seo-workspace/data/gsc-queries.csv",
                "  google_ads_search_terms_csv: seo-workspace/data/google-ads-search-terms.csv",
                "  google_ads_keyword_performance_csv: seo-workspace/data/google-ads-keyword-performance.csv",
                "  lead_quality_log_csv: seo-workspace/data/lead-quality-log.csv",
                "  local_seo_verification_csv: seo-workspace/data/local-seo-verification.csv",
                "decision_thresholds:",
                "  wasted_clicks_without_lead: 5",
                "  wasted_cost_myr_without_lead: 10",
                "  high_intent_keep_signal: owner_confirmed_high_quality_lead",
                "blocked_without_owner_approval:",
                "  - increase_budget",
                "  - broaden_locations",
                "  - enable_performance_max",
                "  - enable_ai_max",
                "  - enable_display",
                "  - enable_search_partners",
                "  - switch_to_broad_match",
                "  - change_bidding",
                "  - change_billing",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def to_float(value: str) -> float:
    try:
        if value.endswith("%"):
            return float(value.rstrip("%")) / 100
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def score_int(row: dict[str, str]) -> int:
    try:
        return int(float(row.get("total_score", "0")))
    except ValueError:
        return 0


def top_opportunity_rows(root: Path, limit: int = 5) -> list[dict[str, str]]:
    rows = read_csv_rows(data_path(root, "seo-opportunity-scores.csv"))
    return sorted(rows, key=score_int, reverse=True)[:limit]


def top_performance_pages(root: Path, limit: int = 10) -> list[dict[str, str]]:
    rows = read_csv_rows(data_path(root, "gsc-pages.csv"))
    return sorted(rows, key=lambda row: (to_float(row.get("impressions", "")), to_float(row.get("clicks", ""))), reverse=True)[:limit]


def top_performance_queries(root: Path, limit: int = 10) -> list[dict[str, str]]:
    rows = read_csv_rows(data_path(root, "gsc-queries.csv"))
    return sorted(rows, key=lambda row: (to_float(row.get("impressions", "")), to_float(row.get("clicks", ""))), reverse=True)[:limit]


def recommend_action(row: dict[str, str]) -> str:
    task_type = row.get("task_type") or "page optimization"
    url = row.get("url") or row.get("page") or "NEEDS OWNER INPUT"
    return f"优先优化 {task_type}: {url}"


def run_daily_performance_digest(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    opportunities = top_opportunity_rows(root)
    pages = top_performance_pages(root)
    queries = top_performance_queries(root)
    selected = opportunities[0] if opportunities else {}
    digest_rows: list[dict[str, str]] = []
    for index, row in enumerate(opportunities, start=1):
        page_match = next((page for page in pages if page.get("page") == row.get("url")), {})
        digest_rows.append(
            {
                "priority": str(index),
                "url": row.get("url", ""),
                "keyword": row.get("keyword", ""),
                "language": row.get("language", ""),
                "task_type": row.get("task_type", ""),
                "total_score": row.get("total_score", ""),
                "clicks": page_match.get("clicks", ""),
                "impressions": page_match.get("impressions", ""),
                "ctr": page_match.get("ctr", ""),
                "position": page_match.get("position", ""),
                "recommended_action": recommend_action(row),
                "notes": "selected from seo-opportunity-scores; enrich with fresh GSC export when available",
            }
        )

    if not digest_rows:
        digest_rows.append(
            {
                "priority": "1",
                "recommended_action": "NEEDS OWNER INPUT: add GSC/opportunity data before data-led daily prioritization",
                "notes": "gsc-pages.csv or seo-opportunity-scores.csv is empty",
            }
        )

    csv_path = write_csv(data_path(root, "daily-performance-digest.csv"), digest_rows, PERFORMANCE_FIELDS)
    json_path = write_json(
        data_path(root, "daily-performance-digest.json"),
        {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "status": "draft_only_local_report",
            "selected_next_action": digest_rows[0],
            "gsc_pages_rows": len(read_csv_rows(data_path(root, "gsc-pages.csv"))),
            "gsc_queries_rows": len(read_csv_rows(data_path(root, "gsc-queries.csv"))),
            "opportunity_rows": len(opportunities),
            "top_pages": pages,
            "top_queries": queries,
            "artifacts": [str(csv_path)],
        },
    )
    lines = [
        "# Daily Performance Digest",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地报告；未登录 GSC，未提交搜索引擎，未发布。",
        f"- 今日建议动作: {digest_rows[0].get('recommended_action', '')}",
        f"- 机会数据行: {len(opportunities)}",
        f"- GSC 页面行: {len(read_csv_rows(data_path(root, 'gsc-pages.csv')))}",
        f"- GSC 查询行: {len(read_csv_rows(data_path(root, 'gsc-queries.csv')))}",
        "",
        "## 专业 SEO 日常判断",
        "",
        "- 看曝光/点击/CTR/平均排名，找有需求但没吃满点击的页面。",
        "- 结合商业意图和页面类型，每天只选一个最高价值动作。",
        "- 如果 GSC 数据为空，先补导出或配置同步，避免凭感觉排期。",
        "",
        "## 今日优先列表",
        "",
    ]
    for row in digest_rows[:5]:
        lines.append(f"- P{row.get('priority')}: {row.get('recommended_action')} | keyword={row.get('keyword', '')} | score={row.get('total_score', '')}")
    report = write_report(root, "daily-performance-digest", lines)
    return {"status": "daily_performance_digest_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [csv_path, json_path, report]


def service_urls(root: Path) -> list[str]:
    text = read_text(data_path(root, "services.md"))
    urls: list[str] = []
    for line in text.splitlines():
        if "URL:" not in line:
            continue
        value = line.split("URL:", 1)[1].strip()
        if value and value not in urls:
            urls.append(value)
    if not urls:
        urls = [row.get("url", "") for row in top_opportunity_rows(root, limit=6) if row.get("url")]
    return urls[:8]


def run_ai_search_monitor(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    company = company_name(root)
    website = brand_website(root).rstrip("/")
    urls = service_urls(root)
    base_queries = [
        ("en", f"best renovation contractor in Kuala Lumpur for homeowners"),
        ("en", f"who is {company} and what renovation services do they provide"),
        ("en", "kitchen cabinet renovation company Malaysia comparison"),
        ("zh", "吉隆坡 装修 公司 推荐"),
        ("zh", f"{company} 装修 服务 靠谱吗"),
        ("zh", "马来西亚 厨房橱柜 装修 公司 对比"),
    ]
    rows: list[dict[str, str]] = []
    for language, query in base_queries:
        rows.append(
            {
                "query": query,
                "language": language,
                "surface": "ChatGPT / Gemini / Perplexity / Google AI overview manual check",
                "expected_entity": company,
                "expected_canonical_url": website,
                "pass_criteria": "AI answer names the brand accurately, links/cites the canonical site when relevant, and does not invent reviews/prices/certifications.",
                "notes": "manual check queue; no automated scraping in this command",
            }
        )
    for url in urls[:4]:
        language = "zh" if "/zh/" in url else "en"
        rows.append(
            {
                "query": f"Summarize the renovation service page {url}",
                "language": language,
                "surface": "ChatGPT / Gemini / Perplexity manual page understanding test",
                "expected_entity": company,
                "expected_canonical_url": url if url.startswith("http") else website + "/" + url.lstrip("/"),
                "pass_criteria": "AI can identify service, location context, CTA, and concept-vs-real proof boundaries from the page.",
                "notes": "use after page/content update to check AI-readable clarity",
            }
        )
    csv_path = write_csv(data_path(root, "ai-search-monitor-queries.csv"), rows, AI_SEARCH_FIELDS)
    lines = [
        "# AI Search Monitor",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 人工监控队列；未自动查询 AI 平台，未抓取第三方回答。",
        f"- 品牌实体: {company}",
        f"- Canonical: {website}",
        f"- 待测问题数: {len(rows)}",
        "",
        "## 专业 GEO 每天要看什么",
        "",
        "- AI 是否正确识别品牌、服务、地区和页面事实。",
        "- AI 是否引用或推荐了正确 canonical 页面。",
        "- AI 是否产生错误价格、假评价、假资质或不存在的案例。",
        "- 哪些页面缺少清晰实体说明、FAQ、结构化内容或真实证明。",
        "",
        "## 今日抽查问题",
        "",
    ]
    for row in rows[:8]:
        lines.append(f"- [{row['language']}] {row['query']}")
    report = write_report(root, "ai-search-monitor", lines)
    json_path = write_json(data_path(root, "ai-search-monitor.json"), {"status": "manual_monitor_queue_ready", "queries": rows, "report": str(report)})
    return {"status": "ai_search_monitor_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [csv_path, json_path, report]


def write_competitor_example(root: Path) -> Path:
    path = root / CONFIG_DIR / "competitors.example.yml"
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Owner-fillable competitor list for manual SEO/GEO gap checks.",
                "# This skill does not fetch competitors unless a future approved workflow adds that capability.",
                "competitors:",
                "  - name: NEEDS OWNER INPUT",
                "    url: https://example-competitor.com",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def parse_competitors(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    competitors: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            if current:
                competitors.append(current)
            current = {"name": stripped.split(":", 1)[1].strip().strip('"')}
        elif stripped.startswith("url:") and current:
            current["url"] = stripped.split(":", 1)[1].strip().strip('"')
    if current:
        competitors.append(current)
    return [row for row in competitors if row.get("name") and "NEEDS OWNER INPUT" not in row.get("name", "")]


def run_competitor_gap_audit(root: Path, competitors_config: str = "") -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    example_path = write_competitor_example(root)
    config_path = Path(competitors_config) if competitors_config else example_path
    if not config_path.is_absolute():
        config_path = root / config_path
    competitors = parse_competitors(config_path)
    checks = [
        ("service_page_depth", "Service page depth, FAQ, CTA, and proof signals"),
        ("schema_and_entity", "Schema, entity clarity, and AI-readable summary"),
        ("local_relevance", "Local areas, NAP consistency, and map/citation signals"),
        ("media_and_proof", "Real photos, project facts, before/after, testimonials"),
        ("technical_quality", "Indexability, page speed, internal links, sitemap/canonical"),
    ]
    rows: list[dict[str, str]] = []
    if competitors:
        for competitor in competitors:
            for check_key, check_label in checks:
                rows.append(
                    {
                        "competitor": competitor.get("name", ""),
                        "competitor_url": competitor.get("url", ""),
                        "check_area": check_key,
                        "current_flash_cast_status": "compare manually using latest reports and page inventory",
                        "manual_check_status": "not_checked",
                        "recommended_action": check_label,
                        "priority": "high" if check_key in {"service_page_depth", "media_and_proof"} else "medium",
                    }
                )
    else:
        rows.append(
            {
                "competitor": "NEEDS OWNER INPUT",
                "competitor_url": "",
                "check_area": "competitor_list",
                "current_flash_cast_status": "workspace can audit once owner supplies competitor names/URLs",
                "manual_check_status": "blocked_waiting_owner_input",
                "recommended_action": "Fill seo-workspace/config/competitors.example.yml with 3-5 real competitors.",
                "priority": "high",
            }
        )
    csv_path = write_csv(data_path(root, "competitor-gap-audit.csv"), rows, COMPETITOR_FIELDS)
    lines = [
        "# Competitor Gap Audit",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地手工审计清单；未抓取竞品网站，未编造竞品结论。",
        f"- 竞品配置: `{config_path}`",
        f"- 竞品数量: {len(competitors)}",
        f"- 输出 CSV: `{csv_path}`",
        "",
        "## 专业 SEO/GEO 每天/每周要看什么",
        "",
        "- 对比竞品服务页深度、FAQ、Schema、内链、真实证明、地图/引用和页面速度。",
        "- 找出我们能用真实资料补强的差距，不做 doorway page 或关键词堆砌。",
        "- 没有真实竞品名单时，只能生成检查框架，不能假装已完成竞品分析。",
    ]
    if not competitors:
        lines.extend(["", "## 当前缺口", "", "- NEEDS OWNER INPUT: 请补 3-5 个真实竞品名称和 URL。"])
    report = write_report(root, "competitor-gap-audit", lines)
    json_path = write_json(data_path(root, "competitor-gap-audit.json"), {"status": "competitor_gap_audit_ready", "competitors": competitors, "rows": rows, "report": str(report)})
    return {"status": "competitor_gap_audit_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [csv_path, json_path, report, example_path]


def brand_profile_mentions(root: Path, needle: str) -> str:
    text = read_text(data_path(root, "brand-profile.md"))
    for line in text.splitlines():
        if needle.lower() in line.lower():
            return line.strip()
    return ""


def run_local_citation_tracker(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    platforms = [
        ("Google Business Profile", brand_profile_mentions(root, "Google Business Profile"), "critical"),
        ("Bing Places", "", "high"),
        ("Apple Business Connect / Apple Maps", "", "high"),
        ("Facebook Page", "", "medium"),
        ("LinkedIn Company Page", "", "medium"),
        ("Yelp or local directory", "", "medium"),
        ("Malaysia business directory / chamber listing", "", "medium"),
        ("Industry partner / supplier directory", "", "medium"),
    ]
    rows = []
    for platform, evidence, priority in platforms:
        needs_input = not evidence or "NEEDS OWNER INPUT" in evidence
        url_match = re.search(r"https?://\S+", evidence)
        rows.append(
            {
                "platform": platform,
                "profile_url": "" if needs_input else (url_match.group(0).rstrip("`") if url_match else evidence),
                "nap_status": "needs_owner_input" if needs_input else "needs_manual_consistency_check",
                "owner_action": "Provide/verify profile URL, exact NAP, category, service areas, photos, and access owner." if needs_input else "Manually confirm NAP/category/service-area consistency.",
                "priority": priority,
                "notes": evidence,
            }
        )
    csv_path = write_csv(data_path(root, "local-citation-tracker.csv"), rows, CITATION_FIELDS)
    lines = [
        "# Local Citation Tracker",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地引用/NAP 跟踪表；未登录任何平台，未提交目录。",
        f"- 待核对平台: {len(rows)}",
        "",
        "## 专业 Local SEO 每天/每周要做什么",
        "",
        "- 核对 NAP: 公司名、地址、电话、网站是否一致。",
        "- 核对 Google Business Profile / Bing Places / Apple Maps 的类别、服务区域、图片和评价响应。",
        "- 记录新增引用机会，不伪造评价，不创建虚假地址或虚假服务区。",
    ]
    report = write_report(root, "local-citation-tracker", lines)
    json_path = write_json(data_path(root, "local-citation-tracker.json"), {"status": "local_citation_tracker_ready", "rows": rows, "report": str(report)})
    return {"status": "local_citation_tracker_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [csv_path, json_path, report]


def run_real_proof_asset_request(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    case_rows = read_csv_rows(data_path(root, "case-studies.csv"))
    opportunities = top_opportunity_rows(root, limit=6)
    rows: list[dict[str, str]] = []
    for row in opportunities:
        rows.extend(
            [
                {
                    "asset_type": "real_project_photos_or_before_after",
                    "related_service": row.get("service", ""),
                    "related_url": row.get("url", ""),
                    "needed_from_owner": "真实项目照片、拍摄地点可公开范围、是否可展示前后对比",
                    "why_it_matters": "提升 E-E-A-T、转化率和 AI/搜索对真实经验的识别。",
                    "claim_boundary": "No photo can be described as a completed real project unless owner confirms it.",
                    "priority": "high",
                },
                {
                    "asset_type": "project_fact_sheet",
                    "related_service": row.get("service", ""),
                    "related_url": row.get("url", ""),
                    "needed_from_owner": "项目类型、城市、范围、材料、挑战、解决方案、年份；预算/工期只在业主确认后写。",
                    "why_it_matters": "把概念内容升级成可验证案例/经验内容。",
                    "claim_boundary": "Do not invent budget, timeline, warranty, client quotes, awards, or credentials.",
                    "priority": "high",
                },
            ]
        )
    if not rows and case_rows:
        for case in case_rows[:5]:
            rows.append(
                {
                    "asset_type": "case_study_proof_pack",
                    "related_service": case.get("service", ""),
                    "related_url": case.get("related_url", ""),
                    "needed_from_owner": "补真实照片、客户授权、可公开地点、评价授权和项目事实核对。",
                    "why_it_matters": "让现有 case study 更接近专业 SEO/GEO 的证据标准。",
                    "claim_boundary": "Only owner-confirmed facts can become real case proof.",
                    "priority": "high",
                }
            )
    if not rows:
        rows.append(
            {
                "asset_type": "owner_fact_pack",
                "needed_from_owner": "至少提供 3 个真实项目资料包或确认继续使用 concept/rendering 内容。",
                "why_it_matters": "真实经验和证据是专业 SEO/GEO 与普通 AI 内容的核心差距。",
                "claim_boundary": "Concept/rendering material remains allowed but must be labeled as planning/design concept.",
                "priority": "high",
            }
        )
    csv_path = write_csv(data_path(root, "real-proof-asset-request.csv"), rows, PROOF_FIELDS)
    lines = [
        "# Real Proof Asset Request",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 业主素材请求清单；未把概念图写成真实案例，未编造评价/价格/工期。",
        f"- 请求项: {len(rows)}",
        "",
        "## 为什么这是专业 SEO/GEO 缺口",
        "",
        "- 专业 SEO 需要真实经验、真实照片、项目事实和可验证证据。",
        "- GEO 需要 AI 能从页面中读到清楚、可信、边界明确的实体和经验信号。",
        "- 缺真实素材时仍可做 concept/rendering 内容，但必须明确标注，不冒充完工案例。",
    ]
    report = write_report(root, "real-proof-asset-request", lines)
    json_path = write_json(data_path(root, "real-proof-asset-request.json"), {"status": "real_proof_asset_request_ready", "rows": rows, "report": str(report)})
    return {"status": "real_proof_asset_request_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [csv_path, json_path, report]


def run_data_health_center(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    examples = [write_growth_intelligence_example(root), write_lead_quality_example(root), *write_google_ads_performance_examples(root)]
    checks = [
        ("GSC pages", "organic_page_prioritization", data_path(root, "gsc-pages.csv"), "Connect GSC or export page performance."),
        ("GSC queries", "organic_query_prioritization", data_path(root, "gsc-queries.csv"), "Connect GSC or export query performance."),
        ("Google Ads search terms", "paid_search_waste_control", data_path(root, "google-ads-search-terms.csv"), "Export search terms from Google Ads."),
        ("Google Ads keyword performance", "paid_keyword_decisions", data_path(root, "google-ads-keyword-performance.csv"), "Export keyword performance from Google Ads."),
        ("Lead quality log", "roi_and_lead_quality", data_path(root, "lead-quality-log.csv"), "Fill real lead outcomes from WhatsApp, phone, form, or CRM."),
        ("Local SEO verification", "local_seo_truth_check", data_path(root, "local-seo-verification.csv"), "Confirm GBP, Bing Places, NAP, photos, and reviews."),
        ("Competitor config", "weekly_competitor_monitoring", root / CONFIG_DIR / "competitors.yml", "Fill real Malaysia renovation competitors."),
        ("Search engine integrations", "indexation_and_platform_status", data_path(root, "search-engine-integrations.md"), "Keep GSC/Bing/Baidu/IndexNow status current."),
    ]
    rows: list[dict[str, str]] = []
    ready_count = 0
    for source, required_for, path, owner_action in checks:
        status, count, updated = file_status(path)
        if status == "ready":
            ready_count += 1
        decision_use = "can_drive_decisions" if status == "ready" else "not_enough_for_automatic_optimization"
        if source in {"Google Ads search terms", "Google Ads keyword performance", "Lead quality log"} and status != "ready":
            decision_use = "paid_ads_can_only_be_guarded_by_basic_safety_rules"
        rows.append(
            {
                "source": source,
                "required_for": required_for,
                "status": status,
                "rows": str(count),
                "decision_use": decision_use,
                "owner_action": "" if status == "ready" else owner_action,
                "notes": f"path={path}; last_updated={updated or 'not_available'}",
            }
        )
    csv_path = write_csv(data_path(root, "growth-data-health.csv"), rows, DATA_HEALTH_FIELDS)
    json_path = write_json(
        data_path(root, "growth-data-health.json"),
        {
            "status": "growth_data_health_ready",
            "ready_sources": ready_count,
            "total_sources": len(rows),
            "rows": rows,
            "examples": [str(path) for path in examples],
        },
    )
    lines = [
        "# Growth Data Health Center",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地数据健康报告；未登录平台，未读取密码/cookie/token，未修改广告或网站。",
        f"- 可用于决策的数据源: {ready_count}/{len(rows)}",
        "",
        "## 判断原则",
        "",
        "- GSC/GA/Google Ads/询盘质量没有形成闭环前，不自动扩大预算或放宽匹配。",
        "- 点击和展示只能说明流量，不等于有效装修客户。",
        "- 真实询盘质量表是判断 ROI 的最高优先级输入。",
        "",
        "## 数据源状态",
        "",
    ]
    for row in rows:
        lines.append(f"- {row['source']}: {row['status']} | rows={row['rows']} | {row['decision_use']}")
    report = write_report(root, "growth-data-health", lines)
    return {"status": "growth_data_health_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [*examples, csv_path, json_path, report]


def run_lead_quality_tracker(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    example_path = write_lead_quality_example(root)
    path = data_path(root, "lead-quality-log.csv")
    if not path.exists():
        write_csv(path, [], LEAD_QUALITY_FIELDS)
    rows = read_csv_rows(path)
    counts = {"high": 0, "medium": 0, "low": 0, "spam": 0, "unknown": 0, "won": 0, "quoted": 0}
    decision_rows: list[dict[str, str]] = []
    for row in rows:
        quality = (row.get("lead_quality") or "unknown").strip().lower()
        if quality not in counts:
            quality = "unknown"
        counts[quality] += 1
        if truthy(row.get("won", "")):
            counts["won"] += 1
        if truthy(row.get("quoted", "")):
            counts["quoted"] += 1
        label = row.get("decision_label", "")
        if not label:
            if quality in {"high", "medium"}:
                label = "keep_or_expand_after_owner_review"
            elif quality in {"low", "spam"}:
                label = "tighten_or_negative_candidate"
            else:
                label = "needs_owner_review"
        decision_rows.append({**row, "decision_label": label})
    write_csv(path, decision_rows, LEAD_QUALITY_FIELDS)
    json_path = write_json(
        data_path(root, "lead-quality-summary.json"),
        {
            "status": "lead_quality_tracker_ready",
            "lead_rows": len(rows),
            "counts": counts,
            "lead_quality_log": str(path),
            "example": str(example_path),
        },
    )
    lines = [
        "# Lead Quality Tracker",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地询盘质量表；只使用业主确认或后台导出的真实线索，不编造成交/评价/客户反馈。",
        f"- 询盘记录数: {len(rows)}",
        f"- 高质量: {counts['high']} | 中等: {counts['medium']} | 低质量: {counts['low']} | 垃圾: {counts['spam']} | 未知: {counts['unknown']}",
        f"- 已报价: {counts['quoted']} | 已成交: {counts['won']}",
        "",
        "## 使用规则",
        "",
        "- 只有真实询盘质量能决定关键词是否值得保留、拆组或申请加预算。",
        "- 没有询盘质量记录时，Google Ads 只能做止损和搜索词清理，不能判断 ROI。",
        "- 低质量或垃圾询盘要回填来源、关键词和搜索词，方便后续加否定词或暂停。",
    ]
    if not rows:
        lines.extend(["", "## 当前缺口", "", f"- 请按模板填写 `{path}`；模板参考 `{example_path}`。"])
    report = write_report(root, "lead-quality-tracker", lines)
    return {"status": "lead_quality_tracker_ready", "report": str(report), "csv": str(path), "json": str(json_path)}, [example_path, path, json_path, report]


def lead_quality_by_term(root: Path) -> dict[str, list[dict[str, str]]]:
    mapping: dict[str, list[dict[str, str]]] = {}
    for row in read_csv_rows(data_path(root, "lead-quality-log.csv")):
        for key in [row.get("search_term", ""), row.get("keyword", "")]:
            normalized = key.strip().lower()
            if normalized:
                mapping.setdefault(normalized, []).append(row)
    return mapping


def decision_from_paid_row(row: dict[str, str], lead_map: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    search_term = row.get("search_term", "") or row.get("keyword", "")
    keyword = row.get("keyword", "")
    entity = search_term or keyword or row.get("campaign", "")
    clicks = parse_int_like(row.get("clicks", ""))
    cost = parse_number(row.get("cost_myr", "") or row.get("cost", ""))
    conversions = parse_number(row.get("conversions", ""))
    status = (row.get("status", "") or "").lower()
    match_type = (row.get("match_type", "") or "").lower()
    leads = lead_map.get(search_term.strip().lower(), []) + lead_map.get(keyword.strip().lower(), [])
    high_quality = any((lead.get("lead_quality", "").lower() in {"high", "medium"} or truthy(lead.get("won", ""))) for lead in leads)
    low_quality = any(lead.get("lead_quality", "").lower() in {"low", "spam"} for lead in leads)

    if contains_invalid_intent(search_term):
        return {
            "priority": "P0",
            "scope": "search_term",
            "entity": entity,
            "observed_signal": f"irrelevant intent detected; clicks={clicks}; cost_myr={cost:g}",
            "decision": "negative_keyword_candidate",
            "recommended_action": "Add as negative keyword or pause the triggering keyword after review.",
            "owner_approval_required": "recommended_before_non_emergency_change",
            "reason": "Search intent matches job/course/DIY/software/template/second-hand waste patterns.",
            "safety_guardrail": "Do not broaden targeting to recover volume.",
        }
    if "broad" in match_type:
        return {
            "priority": "P0",
            "scope": "keyword",
            "entity": entity,
            "observed_signal": f"broad match detected; clicks={clicks}; cost_myr={cost:g}",
            "decision": "tighten_match_type",
            "recommended_action": "Switch back to phrase/exact only after owner approval.",
            "owner_approval_required": "yes",
            "reason": "Chinese launch baseline forbids broad match until conversion and search-term quality are proven.",
            "safety_guardrail": "Do not accept Google broad match recommendations automatically.",
        }
    if high_quality:
        return {
            "priority": "P1",
            "scope": "keyword_or_search_term",
            "entity": entity,
            "observed_signal": "owner-confirmed high/medium quality lead or won lead exists",
            "decision": "keep_and_consider_isolation",
            "recommended_action": "Keep; consider a tighter ad group, stronger landing-page alignment, or owner-reviewed budget shift.",
            "owner_approval_required": "yes_for_budget_or_bidding_changes",
            "reason": "Real lead quality outranks raw CTR/CPC.",
            "safety_guardrail": "Do not promise future lead volume or ROI.",
        }
    if low_quality:
        return {
            "priority": "P1",
            "scope": "keyword_or_search_term",
            "entity": entity,
            "observed_signal": "owner-confirmed low quality or spam lead",
            "decision": "tighten_or_pause_candidate",
            "recommended_action": "Review search term, add negative where appropriate, or pause if repeated.",
            "owner_approval_required": "recommended_before_non_emergency_change",
            "reason": "The term produced poor lead quality.",
            "safety_guardrail": "Use evidence; do not block broad Chinese terms without checking examples.",
        }
    if conversions > 0:
        return {
            "priority": "P2",
            "scope": "keyword_or_search_term",
            "entity": entity,
            "observed_signal": f"conversions={conversions:g}; lead quality not confirmed",
            "decision": "verify_lead_quality",
            "recommended_action": "Match conversion to WhatsApp/phone/form outcome before scaling.",
            "owner_approval_required": "yes_for_scaling",
            "reason": "Conversion count alone may be page visit or unqualified lead.",
            "safety_guardrail": "Do not optimize only to page views.",
        }
    if clicks >= 5 and cost >= 10:
        return {
            "priority": "P2",
            "scope": "keyword_or_search_term",
            "entity": entity,
            "observed_signal": f"clicks={clicks}; cost_myr={cost:g}; no confirmed lead",
            "decision": "waste_review_candidate",
            "recommended_action": "Inspect search term and landing page; add negative or pause if irrelevant.",
            "owner_approval_required": "recommended_before_non_emergency_change",
            "reason": "Spend is accumulating without owner-confirmed lead value.",
            "safety_guardrail": "Emergency pause only when traffic is clearly irrelevant or spend is abnormal.",
        }
    if "low" in status and "volume" in status:
        return {
            "priority": "P3",
            "scope": "keyword",
            "entity": entity,
            "observed_signal": status,
            "decision": "hold_low_volume_keyword",
            "recommended_action": "Keep if tightly relevant and not spending; do not broaden just for volume.",
            "owner_approval_required": "no_for_observation",
            "reason": "Chinese local long-tail near-me terms can be low volume but still valuable.",
            "safety_guardrail": "No broad match expansion without clean data.",
        }
    return {
        "priority": "P4",
        "scope": "keyword_or_search_term",
        "entity": entity,
        "observed_signal": f"clicks={clicks}; cost_myr={cost:g}; conversions={conversions:g}; status={status}",
        "decision": "observe",
        "recommended_action": "Continue monitoring until enough search-term and lead-quality data exists.",
        "owner_approval_required": "no_for_read_only_monitoring",
        "reason": "Insufficient evidence for action.",
        "safety_guardrail": "No budget, location, bidding, or match-type expansion.",
    }


def run_ads_decision_review(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    examples = write_google_ads_performance_examples(root)
    lead_example = write_lead_quality_example(root)
    search_terms = read_csv_rows(data_path(root, "google-ads-search-terms.csv"))
    keyword_rows = read_csv_rows(data_path(root, "google-ads-keyword-performance.csv"))
    lead_map = lead_quality_by_term(root)
    input_rows = search_terms + keyword_rows
    decisions = [decision_from_paid_row(row, lead_map) for row in input_rows]
    if not decisions:
        decisions.append(
            {
                "priority": "P0",
                "scope": "data",
                "entity": "Google Ads exports",
                "observed_signal": "missing google-ads-search-terms.csv and google-ads-keyword-performance.csv",
                "decision": "needs_data_before_optimization",
                "recommended_action": "Export Google Ads search terms and keyword performance, then rerun ads-decision-review.",
                "owner_approval_required": "no_for_export_review",
                "reason": "The skill cannot decide which terms to cut or scale without spend/search-term data.",
                "safety_guardrail": "Keep budget/location/match-type guarded; do not scale.",
            }
        )
    decisions = sorted(decisions, key=lambda row: row.get("priority", "P9"))
    csv_path = write_csv(data_path(root, "google-ads-decision-review.csv"), decisions, ADS_DECISION_FIELDS)
    json_path = write_json(
        data_path(root, "google-ads-decision-review.json"),
        {
            "status": "google_ads_decision_review_ready",
            "search_term_rows": len(search_terms),
            "keyword_rows": len(keyword_rows),
            "lead_quality_terms": len(lead_map),
            "decisions": decisions,
            "examples": [str(path) for path in [*examples, lead_example]],
        },
    )
    lines = [
        "# Google Ads Decision Review",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地广告决策建议；未登录 Google Ads，未改预算/地区/出价/匹配方式。",
        f"- 搜索词行: {len(search_terms)}",
        f"- 关键词表现行: {len(keyword_rows)}",
        f"- 可匹配询盘质量词: {len(lead_map)}",
        "",
        "## 决策规则",
        "",
        "- 真实高质量询盘优先级高于 CTR/CPC。",
        "- 明显无效搜索意图优先加否定词或暂停候选。",
        "- 有花费无询盘时先检查搜索词和落地页，不直接加预算。",
        "- 附近/中文长尾低搜索量可以保留观察，不为了放量改 broad match。",
        "- 加预算、扩地区、PMax、AI Max、Search partners、Display、broad match、出价策略变化都需要业主确认。",
        "",
        "## 本次建议",
        "",
    ]
    for row in decisions[:12]:
        lines.append(f"- {row['priority']} {row['decision']}: {row['entity']} -> {row['recommended_action']}")
    report = write_report(root, "google-ads-decision-review", lines)
    return {"status": "google_ads_decision_review_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [*examples, lead_example, csv_path, json_path, report]


def run_competitor_weekly_monitor(root: Path, competitors_config: str = "") -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    example_path = write_competitor_example(root)
    config_candidate = Path(competitors_config) if competitors_config else root / CONFIG_DIR / "competitors.yml"
    if not config_candidate.is_absolute():
        config_candidate = root / config_candidate
    competitors = parse_competitors(config_candidate) or parse_competitors(example_path)
    check_areas = [
        ("new_or_changed_service_pages", "Check whether competitor added/changed high-intent renovation, kitchen, bathroom, cabinet, office, or shop pages."),
        ("title_meta_faq_schema", "Compare title, meta, FAQ, schema, and internal linking depth."),
        ("local_seo_and_maps", "Compare GBP categories, services, photos, review count, and NAP consistency."),
        ("proof_and_media", "Compare real project proof, before/after, testimonials, and concept-vs-real labeling."),
        ("chinese_search_coverage", "Check Chinese pages, Chinese keywords, and local hybrid terms such as KL装修公司."),
    ]
    rows: list[dict[str, str]] = []
    if competitors:
        for competitor in competitors:
            for area, note in check_areas:
                rows.append(
                    {
                        "competitor": competitor.get("name", ""),
                        "competitor_url": competitor.get("url", ""),
                        "weekly_check_area": area,
                        "last_checked": "",
                        "change_status": "not_checked",
                        "recommended_action": "Manual public-page check; convert confirmed gap into one owner-review task.",
                        "priority": "high" if area in {"chinese_search_coverage", "local_seo_and_maps"} else "medium",
                        "notes": note,
                    }
                )
    else:
        rows.append(
            {
                "competitor": "NEEDS OWNER INPUT",
                "competitor_url": "",
                "weekly_check_area": "competitor_list",
                "last_checked": "",
                "change_status": "blocked_waiting_competitor_urls",
                "recommended_action": "Fill seo-workspace/config/competitors.yml with real Malaysia renovation competitors.",
                "priority": "high",
                "notes": "The monitor is ready but needs real competitor URLs.",
            }
        )
    csv_path = write_csv(data_path(root, "competitor-weekly-monitor.csv"), rows, COMPETITOR_MONITOR_FIELDS)
    json_path = write_json(data_path(root, "competitor-weekly-monitor.json"), {"status": "competitor_weekly_monitor_ready", "competitors": competitors, "rows": rows})
    lines = [
        "# Competitor Weekly Monitor",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地周监控清单；未抓取竞品网站，未复制竞品内容。",
        f"- 竞品数: {len(competitors)}",
        "",
        "## 每周判断方式",
        "",
        "- 只记录公开可见差距，不把竞品内容当作可复制文案。",
        "- 每周把确认差距转成 1-3 个最高价值页面/本地 SEO/广告动作。",
        "- 竞品商标词广告和竞品名称文案必须另行做政策/风险审查。",
    ]
    report = write_report(root, "competitor-weekly-monitor", lines)
    return {"status": "competitor_weekly_monitor_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [example_path, csv_path, json_path, report]


def run_local_seo_verification(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    brand_text = read_text(data_path(root, "brand-profile.md"))
    integrations = read_text(data_path(root, "search-engine-integrations.md"))
    assets = [
        ("Google Business Profile", brand_profile_mentions(root, "Google Business Profile"), "critical"),
        ("Bing Places", "Bing Places imported and pending publication" if "Bing Places" in integrations else "", "high"),
        ("Google Ads location asset", "Use Google Ads asset report/account evidence when available", "high"),
        ("Phone/NAP on website", brand_profile_mentions(root, "Phone") or brand_profile_mentions(root, "WhatsApp"), "critical"),
        ("Apple Maps", "out_of_scope_by_owner_decision", "none"),
        ("Directory citations", "", "medium"),
    ]
    rows: list[dict[str, str]] = []
    for asset, evidence, priority in assets:
        if evidence == "out_of_scope_by_owner_decision":
            rows.append(
                {
                    "asset": asset,
                    "official_url": "",
                    "ownership_status": "out_of_scope",
                    "nap_status": "out_of_scope",
                    "category_status": "out_of_scope",
                    "photo_status": "out_of_scope",
                    "review_status": "out_of_scope",
                    "service_area_status": "out_of_scope",
                    "next_action": "Do not continue Apple Maps unless owner reopens it.",
                    "priority": priority,
                }
            )
            continue
        url_match = re.search(r"https?://\S+", evidence or brand_text)
        verified = bool(evidence and "NEEDS OWNER INPUT" not in evidence)
        rows.append(
            {
                "asset": asset,
                "official_url": url_match.group(0).rstrip("`") if url_match and verified else "",
                "ownership_status": "needs_owner_confirmation" if not verified else "needs_manual_verification",
                "nap_status": "needs_manual_verification",
                "category_status": "needs_manual_verification",
                "photo_status": "concept_or_real_must_be_labeled",
                "review_status": "real_reviews_only",
                "service_area_status": "needs_owner_confirmation",
                "next_action": "Confirm official URL/access, exact NAP, category, service areas, hours, and media boundaries." if not verified else "Compare with website/footer/schema and record differences.",
                "priority": priority,
            }
        )
    csv_path = write_csv(data_path(root, "local-seo-verification.csv"), rows, LOCAL_VERIFICATION_FIELDS)
    json_path = write_json(data_path(root, "local-seo-verification.json"), {"status": "local_seo_verification_ready", "rows": rows})
    lines = [
        "# Local SEO Verification",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地真实性验证表；未登录 GBP/Bing/目录，未修改第三方平台。",
        "",
        "## 验证原则",
        "",
        "- 公司名、电话、网站、地址/服务区域必须在网站、schema、GBP、Bing Places 和目录中一致。",
        "- 真实评价、真实照片、真实项目证明只能用业主确认资料。",
        "- Apple Maps 已按业主决定保持 out of scope。",
    ]
    report = write_report(root, "local-seo-verification", lines)
    return {"status": "local_seo_verification_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, [csv_path, json_path, report]


def run_weekly_growth_control(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    data_health, data_artifacts = run_data_health_center(root)
    lead_quality, lead_artifacts = run_lead_quality_tracker(root)
    post_publish_feedback, post_publish_artifacts = run_post_publish_feedback(root)
    ads_decisions, ads_artifacts = run_ads_decision_review(root)
    competitor_monitor, competitor_artifacts = run_competitor_weekly_monitor(root)
    local_verification, local_artifacts = run_local_seo_verification(root)
    rows = [
        {
            "priority": "P0",
            "area": "Data health",
            "finding": f"Data health report ready: {data_health.get('report')}",
            "recommended_action": "Fix missing data sources before scaling ads or making ROI claims.",
            "owner_input_needed": "GSC/GA/Google Ads exports and lead quality outcomes when missing.",
            "blocked_actions": "budget increase, broad match, PMax, ROI claims",
            "evidence": data_health.get("json", ""),
        },
        {
            "priority": "P0",
            "area": "Lead quality",
            "finding": f"Lead quality tracker ready: {lead_quality.get('report')}",
            "recommended_action": "Record every WhatsApp/phone/form lead outcome weekly.",
            "owner_input_needed": "Real lead quality and sale outcome.",
            "blocked_actions": "keyword scaling without qualified lead evidence",
            "evidence": lead_quality.get("json", ""),
        },
        {
            "priority": "P1",
            "area": "Post-publish feedback",
            "finding": f"Post-publish feedback ready: {post_publish_feedback.get('report')}",
            "recommended_action": "Use post-publish feedback adjustments in the next daily opportunity scoring run.",
            "owner_input_needed": "; ".join(post_publish_feedback.get("owner_input_needed") or []) or "none",
            "blocked_actions": "ranking/ROI guarantees, budget increases, publish/submit/deploy from feedback review",
            "evidence": post_publish_feedback.get("opportunity_feedback_csv", ""),
        },
        {
            "priority": "P1",
            "area": "Google Ads decisions",
            "finding": f"Ads decision review ready: {ads_decisions.get('report')}",
            "recommended_action": "Use search-term and lead-quality evidence to add negatives, pause waste, or keep winners.",
            "owner_input_needed": "Approval for non-emergency account changes.",
            "blocked_actions": "budget, bidding, broad match, PMax, AI Max, Display, Search partners",
            "evidence": ads_decisions.get("json", ""),
        },
        {
            "priority": "P2",
            "area": "Competitors",
            "finding": f"Competitor weekly monitor ready: {competitor_monitor.get('report')}",
            "recommended_action": "Review fixed competitors weekly and turn confirmed gaps into tasks.",
            "owner_input_needed": "True competitor URLs if not configured.",
            "blocked_actions": "copying competitor content or using competitor trademarks in ads",
            "evidence": competitor_monitor.get("json", ""),
        },
        {
            "priority": "P2",
            "area": "Local SEO",
            "finding": f"Local verification ready: {local_verification.get('report')}",
            "recommended_action": "Verify GBP/Bing/NAP/photos/reviews before using them as trust signals.",
            "owner_input_needed": "Official ownership/access and real media/review confirmation.",
            "blocked_actions": "fake reviews, fake locations, unsupported service areas",
            "evidence": local_verification.get("json", ""),
        },
    ]
    csv_path = write_csv(data_path(root, "weekly-growth-control.csv"), rows, WEEKLY_CONTROL_FIELDS)
    json_path = write_json(
        data_path(root, "weekly-growth-control.json"),
        {
            "status": "weekly_growth_control_ready",
            "data_health": data_health,
            "lead_quality": lead_quality,
            "post_publish_feedback": post_publish_feedback,
            "ads_decisions": ads_decisions,
            "competitor_monitor": competitor_monitor,
            "local_verification": local_verification,
            "rows": rows,
        },
    )
    lines = [
        "# Weekly Growth Control",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地周增长总控；未发布、未登录平台、未修改广告或网站。",
        "",
        "## 本周总控原则",
        "",
        "- 先看真实数据，再决定内容、广告和本地 SEO 动作。",
        "- 广告优化以真实询盘质量为最高优先级。",
        "- 每周最多推进 1-3 个最高价值动作，避免随机发文章或盲目扩量。",
        "",
        "## 本周动作队列",
        "",
    ]
    for row in rows:
        lines.append(f"- {row['priority']} {row['area']}: {row['recommended_action']}")
    report = write_report(root, "weekly-growth-control", lines)
    artifacts = [
        *data_artifacts,
        *lead_artifacts,
        *post_publish_artifacts,
        *ads_artifacts,
        *competitor_artifacts,
        *local_artifacts,
        csv_path,
        json_path,
        report,
    ]
    return {"status": "weekly_growth_control_ready", "report": str(report), "csv": str(csv_path), "json": str(json_path)}, artifacts


def run_growth_ops_audit(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    results: dict[str, Any] = {}
    artifacts: list[Path] = []
    for name, runner in [
        ("daily_performance_digest", run_daily_performance_digest),
        ("growth_data_health", run_data_health_center),
        ("lead_quality_tracker", run_lead_quality_tracker),
        ("google_ads_decision_review", run_ads_decision_review),
        ("ai_search_monitor", run_ai_search_monitor),
        ("competitor_gap_audit", run_competitor_gap_audit),
        ("competitor_weekly_monitor", run_competitor_weekly_monitor),
        ("local_citation_tracker", run_local_citation_tracker),
        ("local_seo_verification", run_local_seo_verification),
        ("real_proof_asset_request", run_real_proof_asset_request),
        ("weekly_growth_control", run_weekly_growth_control),
    ]:
        result, paths = runner(root)
        results[name] = result
        artifacts.extend(paths)
    lines = [
        "# Growth Ops Audit",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        "- 状态: 本地专业 SEO/GEO 运营闭环报告；未发布、未提交搜索引擎、未登录第三方平台。",
        "",
        "## 已补齐的专业日常模块",
        "",
        "- Daily Performance Digest: 每天看数据与最高价值动作。",
        "- Growth Data Health Center: 检查 GSC/GA/Ads/询盘/本地 SEO 数据是否可用于决策。",
        "- Lead Quality Tracker: 把 WhatsApp、电话和表单询盘质量回填为 ROI 判断依据。",
        "- Google Ads Decision Review: 用搜索词、花费和询盘质量生成加否词/暂停/保留建议。",
        "- AI Search Monitor: 人工检查 ChatGPT/Gemini/Perplexity/Google AI 是否正确理解品牌与页面。",
        "- Competitor Gap Audit: 竞品差距检查框架，等待真实竞品名单后可执行。",
        "- Competitor Weekly Monitor: 固定竞品库每周检查页面、FAQ、Schema、地图和中文覆盖差距。",
        "- Local Citation Tracker: 本地引用/NAP/地图平台跟踪。",
        "- Local SEO Verification: 验证 GBP/Bing/NAP/照片/评价/服务区域真实性。",
        "- Real Proof Asset Request: 真实项目证据素材请求，避免假案例和假评价。",
        "- Weekly Growth Control: 每周把数据、广告、竞品和本地 SEO 汇总成最高价值动作队列。",
        "",
        "## 仍需要业主/平台输入",
        "",
        "- GSC/Bing/GBP 等平台权限或导出数据。",
        "- Google Ads 搜索词/关键词表现导出。",
        "- WhatsApp、电话、表单或 CRM 的真实询盘质量回填。",
        "- 3-5 个真实竞品 URL。",
        "- Google Business Profile / Bing Places / Apple Maps 等真实资料链接。",
        "- 真实项目照片、项目事实、客户授权和可公开证明。",
    ]
    report = write_report(root, "growth-ops-audit", lines)
    summary_path = write_json(data_path(root, "growth-ops-audit.json"), {"status": "growth_ops_audit_ready", "results": results, "report": str(report)})
    artifacts.extend([summary_path, report])
    return {"status": "growth_ops_audit_ready", "report": str(report), "json": str(summary_path), "results": results}, artifacts
