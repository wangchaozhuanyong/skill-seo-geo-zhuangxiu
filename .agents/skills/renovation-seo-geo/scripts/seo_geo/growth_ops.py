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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def brand_value(root: Path, label: str) -> str:
    text = read_text(data_path(root, "brand-profile.md"))
    pattern = re.compile(rf"^-\s*{re.escape(label)}:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def brand_website(root: Path) -> str:
    return brand_value(root, "Website") or "https://flashcast.com.my/"


def company_name(root: Path) -> str:
    return brand_value(root, "Company name") or "FLASH CAST"


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


def run_growth_ops_audit(root: Path) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    results: dict[str, Any] = {}
    artifacts: list[Path] = []
    for name, runner in [
        ("daily_performance_digest", run_daily_performance_digest),
        ("ai_search_monitor", run_ai_search_monitor),
        ("competitor_gap_audit", run_competitor_gap_audit),
        ("local_citation_tracker", run_local_citation_tracker),
        ("real_proof_asset_request", run_real_proof_asset_request),
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
        "- AI Search Monitor: 人工检查 ChatGPT/Gemini/Perplexity/Google AI 是否正确理解品牌与页面。",
        "- Competitor Gap Audit: 竞品差距检查框架，等待真实竞品名单后可执行。",
        "- Local Citation Tracker: 本地引用/NAP/地图平台跟踪。",
        "- Real Proof Asset Request: 真实项目证据素材请求，避免假案例和假评价。",
        "",
        "## 仍需要业主/平台输入",
        "",
        "- GSC/Bing/GBP 等平台权限或导出数据。",
        "- 3-5 个真实竞品 URL。",
        "- Google Business Profile / Bing Places / Apple Maps 等真实资料链接。",
        "- 真实项目照片、项目事实、客户授权和可公开证明。",
    ]
    report = write_report(root, "growth-ops-audit", lines)
    summary_path = write_json(data_path(root, "growth-ops-audit.json"), {"status": "growth_ops_audit_ready", "results": results, "report": str(report)})
    artifacts.extend([summary_path, report])
    return {"status": "growth_ops_audit_ready", "report": str(report), "json": str(summary_path), "results": results}, artifacts
