#!/usr/bin/env python3
"""Create a safe post-publish SEO/GEO feedback watchlist."""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    from .hreflang import expected_pair_url
except ImportError:  # pragma: no cover
    from hreflang import expected_pair_url


WATCHLIST_FIELDS = [
    "target_url",
    "paired_url",
    "checkpoint",
    "due_date",
    "current_status",
    "evidence_sources",
    "metrics_to_check",
    "owner_input_needed",
    "recommended_action",
    "blocked_actions",
]

OPPORTUNITY_FEEDBACK_FIELDS = [
    "url",
    "target_url",
    "paired_url",
    "score_delta",
    "feedback_status",
    "feedback_events",
    "recommended_daily_action",
    "owner_input_needed",
    "evidence",
]


HIGH_QUALITY_LEAD_TERMS = {"high", "qualified", "won", "converted", "good", "keep", "成交", "高质量", "有效"}
LOW_QUALITY_LEAD_TERMS = {
    "low",
    "spam",
    "unqualified",
    "irrelevant",
    "poor",
    "pause",
    "negative",
    "无效",
    "垃圾",
    "低质量",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


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


def _normalize_url(value: str) -> str:
    value = (value or "").strip()
    if value.endswith("/") and value.count("/") > 2:
        return value.rstrip("/")
    return value


def _receipt_payload(root: Path) -> dict[str, Any]:
    payload = read_json(root / "seo-workspace" / "data" / "publish-execution-receipt.json")
    receipt = payload.get("receipt")
    return receipt if isinstance(receipt, dict) else payload


def _result_payload(root: Path) -> dict[str, Any]:
    return read_json(root / "seo-workspace" / "data" / "publish-execution-result.json")


def _top_opportunity(root: Path) -> dict[str, str]:
    rows = read_csv_rows(root / "seo-workspace" / "data" / "seo-opportunity-scores.csv")
    return rows[0] if rows else {}


def resolve_target(root: Path, target_url: str = "") -> tuple[str, str, str]:
    if target_url:
        return target_url, expected_pair_url(target_url) or "", "cli_target_url"
    receipt = _receipt_payload(root)
    if receipt.get("target_url"):
        return str(receipt.get("target_url", "")), str(receipt.get("paired_url", "")), "publish-execution-receipt.json"
    result = _result_payload(root)
    if result.get("target_url"):
        return str(result.get("target_url", "")), str(result.get("paired_url", "")), "publish-execution-result.json"
    top = _top_opportunity(root)
    if top.get("url"):
        url = top.get("url", "")
        return url, expected_pair_url(url) or "", "seo-opportunity-scores.csv"
    return "", "", "missing"


def _page_metrics(root: Path, urls: set[str]) -> tuple[str, str]:
    rows = [row for row in read_csv_rows(root / "seo-workspace" / "data" / "gsc-pages.csv") if _normalize_url(row.get("page", "")) in urls]
    if not rows:
        return "missing_or_empty", "GSC page rows unavailable for target/pair"
    evidence = []
    for row in rows:
        evidence.append(
            f"{row.get('page')}: clicks={row.get('clicks','0')}, impressions={row.get('impressions','0')}, ctr={row.get('ctr','')}, position={row.get('position','')}"
        )
    return "ready", "; ".join(evidence)


def _index_metrics(root: Path, urls: set[str]) -> tuple[str, str]:
    rows = [row for row in read_csv_rows(root / "seo-workspace" / "data" / "google-index-status.csv") if _normalize_url(row.get("url", "")) in urls]
    if not rows:
        return "missing_or_empty", "Google index inspection rows unavailable for target/pair"
    return "ready", "; ".join(f"{row.get('url')}: {row.get('inspection_state','')} {row.get('verdict','')} {row.get('coverage_state','')}" for row in rows)


def _lead_metrics(root: Path, urls: set[str]) -> tuple[str, str]:
    rows = [row for row in read_csv_rows(root / "seo-workspace" / "data" / "lead-quality-log.csv") if _normalize_url(row.get("landing_page", "")) in urls]
    if not rows:
        return "missing_or_empty", "Owner-confirmed lead quality rows unavailable for target/pair"
    labels = [row.get("lead_quality", "") or row.get("decision_label", "") or "logged" for row in rows]
    return "ready", f"lead_rows={len(rows)}; labels={', '.join(labels[:8])}"


def _lead_quality_terms(root: Path, urls: set[str]) -> set[str]:
    rows = [row for row in read_csv_rows(root / "seo-workspace" / "data" / "lead-quality-log.csv") if _normalize_url(row.get("landing_page", "")) in urls]
    terms: set[str] = set()
    for row in rows:
        for field in ("lead_quality", "decision_label", "quoted", "won"):
            value = (row.get(field, "") or "").strip().lower()
            if value:
                terms.add(value)
            if field == "won" and value in {"yes", "y", "true", "1", "成交"}:
                terms.add("won")
            if field == "quoted" and value in {"yes", "y", "true", "1", "已报价"}:
                terms.add("qualified")
        if (row.get("owner_notes", "") or "").strip():
            terms.add(row.get("owner_notes", "").strip().lower())
    return terms


def _terms_contain(terms: set[str], needles: set[str]) -> bool:
    haystack = " ".join(sorted(terms))
    return any(needle in haystack for needle in needles)


def build_opportunity_feedback_rows(
    root: Path,
    summary: dict[str, Any],
    watchlist_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    target = _normalize_url(str(summary.get("target_url") or ""))
    paired = _normalize_url(str(summary.get("paired_url") or ""))
    if not target:
        return []

    urls = {_normalize_url(url) for url in (target, paired) if url}
    events: list[tuple[str, int]] = []
    lead_terms = _lead_quality_terms(root, urls)
    if summary.get("gsc_status") != "ready":
        events.append(("post-publish GSC data gap", 1))
    if summary.get("index_status") != "ready":
        events.append(("post-publish index status gap", 1))
    if summary.get("lead_quality_status") != "ready":
        events.append(("post-publish lead-quality data gap", 2))
    elif _terms_contain(lead_terms, HIGH_QUALITY_LEAD_TERMS):
        events.append(("post-publish high-quality lead signal", 6))
    elif _terms_contain(lead_terms, LOW_QUALITY_LEAD_TERMS):
        events.append(("post-publish low-quality lead cleanup signal", 5))
    else:
        events.append(("post-publish lead-quality data ready", 3))

    if summary.get("receipt_verified"):
        events.append(("verified publish receipt for feedback loop", 1))

    score_delta = min(10, sum(points for _label, points in events))
    owner_input_needed = "; ".join(summary.get("owner_input_needed") or []) or "none"
    feedback_events = "; ".join(f"{label} (+{points})" for label, points in events)
    evidence = " | ".join(row.get("evidence_sources", "") for row in watchlist_rows[:1])
    recommended_action = (
        "Use this page/pair as a post-publish follow-up candidate in daily opportunity scoring; "
        "review GSC/index/owner-confirmed lead quality before content, internal-link, CTA, or schema decisions."
    )
    rows: list[dict[str, str]] = []
    for url in sorted(urls):
        rows.append(
            {
                "url": url,
                "target_url": target,
                "paired_url": paired,
                "score_delta": str(score_delta),
                "feedback_status": str(summary.get("status") or ""),
                "feedback_events": feedback_events,
                "recommended_daily_action": recommended_action,
                "owner_input_needed": owner_input_needed,
                "evidence": evidence,
            }
        )
    return rows


def build_watchlist(root: Path, *, target_url: str = "") -> tuple[dict[str, Any], list[dict[str, str]]]:
    target, paired, target_source = resolve_target(root, target_url)
    today = dt.date.today()
    urls = {_normalize_url(url) for url in (target, paired) if url}
    gsc_status, gsc_evidence = _page_metrics(root, urls)
    index_status, index_evidence = _index_metrics(root, urls)
    lead_status, lead_evidence = _lead_metrics(root, urls)
    receipt = _receipt_payload(root)
    receipt_verified = receipt.get("receipt_verified_for_post_publish_qa") is True or receipt.get("status") == "publish_execution_receipt_verified"

    owner_inputs = []
    if gsc_status != "ready":
        owner_inputs.append("GSC page/query export or API access")
    if index_status != "ready":
        owner_inputs.append("Google URL inspection/status export")
    if lead_status != "ready":
        owner_inputs.append("owner-confirmed WhatsApp/phone/form lead quality")
    if not receipt_verified:
        owner_inputs.append("verified publish execution receipt")
    owner_input_needed = "; ".join(owner_inputs) if owner_inputs else "none"

    rows: list[dict[str, str]] = []
    checkpoint_specs = [
        (
            "7_day_index_and_quality_check",
            today + dt.timedelta(days=7),
            "Check index status, crawl/index blockers, title/meta visibility, early impressions, and whether any leads mention the updated page.",
            "Fix technical blockers or owner-input gaps; do not judge ROI from 7-day clicks alone.",
        ),
        (
            "30_day_performance_and_lead_quality_review",
            today + dt.timedelta(days=30),
            "Compare GSC impressions/clicks/CTR/position, query mix, page engagement proxies, and owner-confirmed lead quality.",
            "Keep, refresh, internally link, add FAQ/schema, tighten paid terms, or queue another page based on verified data.",
        ),
    ]
    evidence_sources = [
        f"target_source={target_source}",
        f"gsc={gsc_status}: {gsc_evidence}",
        f"index={index_status}: {index_evidence}",
        f"lead_quality={lead_status}: {lead_evidence}",
    ]
    current_status = "watch_ready" if target and owner_input_needed == "none" else "watch_waiting_for_data"
    if not target:
        current_status = "blocked_missing_target_url"
    for checkpoint, due_date, metrics, action in checkpoint_specs:
        rows.append(
            {
                "target_url": target,
                "paired_url": paired,
                "checkpoint": checkpoint,
                "due_date": due_date.isoformat(),
                "current_status": current_status,
                "evidence_sources": " | ".join(evidence_sources),
                "metrics_to_check": metrics,
                "owner_input_needed": owner_input_needed,
                "recommended_action": action,
                "blocked_actions": "No ranking/ROI/lead-quality claims; no budget increases; no publish/submit/deploy from this review.",
            }
        )
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": current_status,
        "target_url": target,
        "paired_url": paired,
        "target_source": target_source,
        "receipt_verified": receipt_verified,
        "gsc_status": gsc_status,
        "index_status": index_status,
        "lead_quality_status": lead_status,
        "owner_input_needed": owner_inputs,
        "watchlist_count": len(rows),
    }
    return summary, rows


def render_report(root: Path, summary: dict[str, Any], csv_path: Path, json_path: Path, rows: list[dict[str, str]]) -> str:
    lines = [
        "# Post-Publish Feedback Watchlist",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        f"- 仓库: `{root}`",
        f"- 目标页面: `{summary.get('target_url') or 'N/A'}`",
        f"- 配对页面: `{summary.get('paired_url') or 'N/A'}`",
        f"- 状态: {summary.get('status')}",
        f"- CSV: `{csv_path}`",
        f"- JSON: `{json_path}`",
        "",
        "## 结论",
        "",
    ]
    if summary.get("status") == "watch_ready":
        lines.append("- 复盘 watchlist 已准备好；7 天看索引与早期信号，30 天看 GSC 与业主确认线索质量。")
    elif summary.get("status") == "blocked_missing_target_url":
        lines.append("- 缺少目标 URL，无法建立复盘清单。")
    else:
        lines.append("- 已建立复盘清单，但缺少部分真实数据；不要用缺失数据推断效果。")
    lines.extend(["", "## Checkpoints", ""])
    for row in rows:
        lines.append(
            f"- {row['checkpoint']} due={row['due_date']} status={row['current_status']} owner_input={row['owner_input_needed']}"
        )
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 本报告只创建复盘计划和本地数据检查，不登录平台、不发布、不提交索引、不修改广告预算。",
            "- 线索质量必须以业主确认的 WhatsApp、电话、表单或 CRM 结果为准。",
            "- 点击、展示、排名和 AI 搜索想法不能单独证明 ROI。",
            "",
        ]
    )
    return "\n".join(lines)


def run_post_publish_feedback(root: Path, *, target_url: str = "") -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    summary, rows = build_watchlist(root, target_url=target_url)
    opportunity_feedback_rows = build_opportunity_feedback_rows(root, summary, rows)
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    csv_path = data_dir / "post-publish-watchlist.csv"
    feedback_csv_path = data_dir / "post-publish-opportunity-feedback.csv"
    json_path = data_dir / "post-publish-feedback.json"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-post-publish-feedback.md"
    write_csv(csv_path, rows, WATCHLIST_FIELDS)
    write_csv(feedback_csv_path, opportunity_feedback_rows, OPPORTUNITY_FEEDBACK_FIELDS)
    summary = {
        **summary,
        "watchlist_csv": str(csv_path),
        "opportunity_feedback_csv": str(feedback_csv_path),
        "json": str(json_path),
        "report": str(report_path),
        "opportunity_feedback_count": len(opportunity_feedback_rows),
    }
    write_json(json_path, {**summary, "watchlist": rows, "opportunity_feedback": opportunity_feedback_rows})
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(root, summary, csv_path, json_path, rows), encoding="utf-8")
    return summary, [csv_path, feedback_csv_path, json_path, report_path]
