#!/usr/bin/env python3
"""Review renovation content quality, claim safety, and GEO readiness."""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit


QUALITY_FIELDS = [
    "metric",
    "score",
    "max_score",
    "status",
    "evidence",
    "recommendation",
]

RISK_PATTERNS = [
    (r"\b#\s*1\b|第一名|排名第一|best renovation|best contractor", "unsupported best/#1 claim"),
    (r"guarantee(?:d)? ranking|保证排名|保证首页|保证收录", "ranking/indexing guarantee"),
    (r"cheapest|最便宜|lowest price|最低价", "unsupported cheapest claim"),
    (r"limited time|限时优惠|只剩|马上结束", "fake urgency risk"),
    (r"真实客户评价|real customer review|testimonial", "testimonial/customer review requires owner proof"),
    (r"保修|warranty|guarantee", "warranty claim requires owner confirmation"),
]


@dataclass(frozen=True)
class QualityMetric:
    metric: str
    score: int
    max_score: int
    status: str
    evidence: str
    recommendation: str


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
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return path


def write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def metric_to_row(metric: QualityMetric) -> dict[str, str]:
    return {
        "metric": metric.metric,
        "score": str(metric.score),
        "max_score": str(metric.max_score),
        "status": metric.status,
        "evidence": metric.evidence,
        "recommendation": metric.recommendation,
    }


def resolve_draft_path(root: Path, draft_path: str = "", target_url: str = "") -> Path:
    if draft_path:
        path = Path(draft_path)
        return path if path.is_absolute() else root / path
    candidates = [
        path
        for path in (root / "seo-workspace" / "drafts").glob("*.md")
        if "rich-content-package" in path.name or "content-brief" in path.name or "service-page-optimization" in path.name
    ]
    if target_url:
        target_path = urlsplit(target_url).path
        matching = []
        for path in candidates:
            text = path.read_text(encoding="utf-8", errors="replace")
            if target_url in text or (target_path and target_path in text):
                matching.append(path)
        if matching:
            candidates = matching
    if not candidates:
        return root / "seo-workspace" / "drafts" / "NEEDS_DRAFT_PATH.md"
    return max(candidates, key=lambda path: path.stat().st_mtime)


def target_url_from_text(text: str, fallback: str = "") -> str:
    patterns = [
        r"目标页面:\s*`([^`]+)`",
        r"Target URL:\s*`?([^\s`]+)",
        r"target_url[\"']?\s*[:=]\s*[\"']([^\"']+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return fallback


def count_urls(text: str) -> int:
    return len(set(re.findall(r"https?://[^\s)>\"]+", text)))


def contains_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def risk_hits(text: str) -> list[str]:
    hits: list[str] = []
    guardrail_markers = [
        "do not",
        "unless owner-confirmed",
        "owner-confirmed",
        "requires owner",
        "owner confirmation",
        "needs owner",
        "missing real",
        "no fake",
        "不作为",
        "不能",
        "不得",
        "不要",
        "不承诺",
        "除非",
        "需要业主",
        "业主确认",
        "未经确认",
    ]
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(marker in lower for marker in guardrail_markers):
            continue
        for pattern, label in RISK_PATTERNS:
            if re.search(pattern, stripped, flags=re.IGNORECASE):
                hits.append(label)
    return sorted(set(hits))


def metric(status: str, score: int, max_score: int, name: str, evidence: str, recommendation: str) -> QualityMetric:
    return QualityMetric(metric=name, score=score, max_score=max_score, status=status, evidence=evidence, recommendation=recommendation)


def build_quality_metrics(text: str) -> list[QualityMetric]:
    metrics: list[QualityMetric] = []
    if not text.strip():
        return [
            metric(
                "blocked",
                0,
                100,
                "draft_available",
                "draft text is empty or missing",
                "先生成 content brief 或 rich-content package，再运行 content-quality-review。",
            )
        ]

    url_count = count_urls(text)
    has_source_log = "Source Log" in text or "最新资料" in text or "research-source-log" in text
    metrics.append(
        metric(
            "pass" if has_source_log and url_count >= 2 else "review",
            12 if has_source_log and url_count >= 2 else 6 if url_count else 0,
            12,
            "source_evidence",
            f"url_count={url_count}; source_log={'yes' if has_source_log else 'no'}",
            "当前事实、搜索政策、材料或权威指导应进入 source log；外部资料只作 general guidance，不变成 FLASH CAST claim。",
        )
    )

    bilingual = "中文页面建议文案" in text and "英文页面建议文案" in text
    metrics.append(
        metric(
            "pass" if bilingual else "review",
            10 if bilingual else 4,
            10,
            "bilingual_pair",
            "中文/英文建议文案 present" if bilingual else "missing bilingual section marker",
            "服务页和可发布页面默认保持 `/zh` 与 `/en` 双语规划。",
        )
    )

    customer_terms = ["问题", "customer problem", "pain point", "需求", "storage", "leakage", "workflow", "空间", "材料"]
    process_terms = ["流程", "process", "planning", "施工", "quotation", "site visit", "材料", "material"]
    service_terms = ["服务范围", "service scope", "renovation", "装修", "fit-out", "built-in", "contractor"]
    specificity_score = sum(
        [
            1 if contains_any(text, service_terms) else 0,
            1 if contains_any(text, customer_terms) else 0,
            1 if contains_any(text, process_terms) else 0,
        ]
    )
    metrics.append(
        metric(
            "pass" if specificity_score == 3 else "review",
            specificity_score * 6,
            18,
            "renovation_usefulness",
            f"service/customer/process signals={specificity_score}/3",
            "内容应回答真实装修客户关心的问题：服务范围、痛点、流程、材料取舍、报价准备和 CTA。",
        )
    )

    has_faq = "FAQ" in text or "常见" in text
    has_cta = "CTA" in text or "quote" in text.lower() or "contact" in text.lower() or "咨询" in text
    has_schema = "schema" in text.lower() or "结构化" in text
    metrics.append(
        metric(
            "pass" if has_faq and has_cta and has_schema else "review",
            (5 if has_faq else 0) + (5 if has_cta else 0) + (5 if has_schema else 0),
            15,
            "search_structure",
            f"faq={'yes' if has_faq else 'no'}; cta={'yes' if has_cta else 'no'}; schema={'yes' if has_schema else 'no'}",
            "补齐可见 FAQ、明确咨询路径和匹配可见内容的 schema 建议。",
        )
    )

    concept_terms = ["概念设计", "效果图方案", "规划示例", "design concept", "rendering concept", "planning example"]
    image_terms = ["Image Block", "图文", "image", "alt", "caption", "图注"]
    has_media = contains_any(text, image_terms)
    has_concept_label = contains_any(text, concept_terms)
    metrics.append(
        metric(
            "pass" if not has_media or has_concept_label else "blocked",
            15 if has_media and has_concept_label else 8 if not has_media else 0,
            15,
            "media_claim_boundary",
            f"media={'yes' if has_media else 'no'}; concept_label={'yes' if has_concept_label else 'no'}",
            "所有效果图/概念图/规划图必须明确标注，不能当真实完工案例或客户照片。",
        )
    )

    local_geo_terms = ["Kuala Lumpur", "Selangor", "Klang Valley", "Malaysia", "吉隆坡", "雪兰莪", "马来西亚"]
    direct_answer_terms = ["快速答案", "Quick answer", "answer", "直接回答"]
    metrics.append(
        metric(
            "pass" if contains_any(text, local_geo_terms) and contains_any(text, direct_answer_terms) else "review",
            (7 if contains_any(text, local_geo_terms) else 0) + (7 if contains_any(text, direct_answer_terms) else 0),
            14,
            "geo_ai_readiness",
            f"local_context={'yes' if contains_any(text, local_geo_terms) else 'no'}; direct_answer={'yes' if contains_any(text, direct_answer_terms) else 'no'}",
            "GEO 内容要有本地语境、直接答案、实体清晰度和可引用段落。",
        )
    )

    risks = risk_hits(text)
    metrics.append(
        metric(
            "blocked" if risks else "pass",
            0 if risks else 16,
            16,
            "claim_safety",
            "; ".join(risks) if risks else "no risky claim patterns detected",
            "删除或标记所有未经确认的排名、价格、评价、奖项、保修、紧迫感和真实案例类声明。",
        )
    )
    return metrics


def overall_status(metrics: list[QualityMetric]) -> str:
    if any(item.status == "blocked" for item in metrics):
        return "blocked_before_owner_review"
    total = sum(item.score for item in metrics)
    maximum = sum(item.max_score for item in metrics) or 1
    ratio = total / maximum
    if ratio >= 0.8:
        return "content_quality_ready_for_owner_review"
    return "content_quality_needs_revision"


def render_report(
    *,
    root: Path,
    draft_path: Path,
    target_url: str,
    csv_path: Path,
    json_path: Path,
    metrics: list[QualityMetric],
    status: str,
) -> str:
    total = sum(item.score for item in metrics)
    maximum = sum(item.max_score for item in metrics)
    lines = [
        "# Content Quality / GEO Readiness Review",
        "",
        f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
        f"- 仓库: `{root}`",
        f"- 草稿: `{draft_path}`",
        f"- 目标页面: `{target_url or 'N/A'}`",
        f"- CSV: `{csv_path}`",
        f"- JSON: `{json_path}`",
        f"- 总分: {total}/{maximum}",
        f"- 状态: {status}",
        "",
        "## 结论",
        "",
    ]
    if status == "content_quality_ready_for_owner_review":
        lines.append("- 草稿质量和声明边界达到 owner-review 标准；仍需业主确认事实和发布执行。")
    elif status == "blocked_before_owner_review":
        lines.append("- 草稿存在声明或媒体边界阻塞，进入发布准备前必须修正。")
    else:
        lines.append("- 草稿可继续优化，优先补足得分较低的内容质量/GEO 信号。")
    lines.extend(["", "## Metrics", ""])
    for item in metrics:
        lines.append(f"- [{item.status}] {item.metric}: {item.score}/{item.max_score} | {item.evidence} -> {item.recommendation}")
    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 本报告只审查本地草稿，不代表内容已经批准、发布、收录或排名。",
            "- 缺少真实案例/真实图片不自动阻塞；但效果图、概念图和规划示例必须清楚标注。",
            "- 所有价格、工期、保修、评价、奖项、资质和真实项目证明仍需业主确认。",
            "",
        ]
    )
    return "\n".join(lines)


def run_content_quality_review(root: Path, *, draft_path: str = "", target_url: str = "") -> tuple[dict[str, object], list[Path]]:
    root = root.resolve()
    selected_draft_path = resolve_draft_path(root, draft_path, target_url)
    text = selected_draft_path.read_text(encoding="utf-8", errors="replace") if selected_draft_path.exists() else ""
    resolved_target_url = target_url_from_text(text, target_url)
    metrics = build_quality_metrics(text)
    status = overall_status(metrics)
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    csv_path = data_dir / "content-quality-review.csv"
    json_path = data_dir / "content-quality-review.json"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-content-quality-review.md"
    rows = [metric_to_row(item) for item in metrics]
    write_csv(csv_path, rows, QUALITY_FIELDS)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "draft_path": str(selected_draft_path),
        "target_url": resolved_target_url,
        "slug": re.sub(r"[^a-z0-9]+", "-", urlsplit(resolved_target_url).path.lower()).strip("-") if resolved_target_url else "",
        "total_score": sum(item.score for item in metrics),
        "max_score": sum(item.max_score for item in metrics),
        "metrics": [asdict(item) for item in metrics],
        "no_publish_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
    }
    write_json(json_path, payload)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(
            root=root,
            draft_path=selected_draft_path,
            target_url=resolved_target_url,
            csv_path=csv_path,
            json_path=json_path,
            metrics=metrics,
            status=status,
        ),
        encoding="utf-8",
    )
    return payload, [csv_path, json_path, report_path]
