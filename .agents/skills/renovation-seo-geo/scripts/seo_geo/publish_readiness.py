#!/usr/bin/env python3
"""Summarize end-to-end publishing readiness without executing anything."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path


READINESS_JSON_NAME = "publish-readiness.json"


@dataclass
class PublishReadinessResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: dict[str, object] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def safe_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def valid_source_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def target_urls_from_plan(plan: dict[str, object], queue_rows: list[dict[str, str]]) -> set[str]:
    urls: set[str] = set()
    queue_item = safe_dict(plan.get("queue_item"))
    for key in ("target_url", "paired_url"):
        value = str(queue_item.get(key, ""))
        if value:
            urls.add(value)
    if not urls and len(queue_rows) == 1:
        for key in ("target_url", "paired_url"):
            value = queue_rows[0].get(key, "")
            if value:
                urls.add(value)
    return urls


def matching_research_sources(rows: list[dict[str, str]], targets: set[str]) -> list[dict[str, str]]:
    valid_rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        source_url = row.get("source_url", "")
        target_url = row.get("target_url", "")
        if targets and target_url not in targets:
            continue
        if not valid_source_url(source_url):
            continue
        key = (target_url, source_url)
        if key in seen:
            continue
        valid_rows.append(row)
        seen.add(key)
    return valid_rows


def artifact_exists(root: Path, value: str) -> bool:
    if not value:
        return False
    return resolve_path(root, value).exists()


def evaluate_readiness(
    *,
    root: Path,
    publish_plan: dict[str, object],
    cms_request: dict[str, object],
    media_request: dict[str, object],
    media_url_map: dict[str, object],
    media_ready_payload: dict[str, object],
    research_rows: list[dict[str, str]],
    queue_rows: list[dict[str, str]],
) -> tuple[list[str], list[str], dict[str, object]]:
    blockers: list[str] = []
    warnings: list[str] = []

    targets = target_urls_from_plan(publish_plan, queue_rows)
    matching_sources = matching_research_sources(research_rows, targets)
    plan_status = str(publish_plan.get("status", "missing") or "missing")
    cms_status = str(cms_request.get("status", "missing") or "missing")
    media_status = str(media_request.get("status", "missing") or "missing")
    media_ops = safe_list(media_request.get("operations"))
    media_queue = safe_list(read_json(root / "seo-workspace" / "data" / "media-upload-plan.json").get("queue"))
    plan_artifacts = safe_dict(publish_plan.get("artifacts"))
    cms_artifacts = safe_dict(cms_request.get("artifacts"))
    media_artifacts = safe_dict(media_request.get("artifacts"))
    editor_applied_payload = read_json(root / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json")
    editor_apply_summary = read_json(root / "seo-workspace" / "data" / "rich-content-editor-apply-summary.json")
    editor_apply_status = str(editor_apply_summary.get("status", "") if editor_apply_summary else "")
    cms_write_request = safe_dict(cms_request.get("write_request"))
    selected_cms_payload_path = str(cms_write_request.get("cms_payload_path", ""))

    if not publish_plan:
        blockers.append("Missing publish-execution-plan.json. Run publish-plan first.")
    elif plan_status != "ready_for_approved_execution_plan":
        blockers.append(f"Publish plan is not ready_for_approved_execution_plan: {plan_status}.")
    if not cms_request:
        blockers.append("Missing cms-write-request.json. Run publish-executor first.")
    elif cms_status != "dry_run_write_request_ready":
        blockers.append(f"CMS write request is not dry_run_write_request_ready: {cms_status}.")
    if not media_request:
        blockers.append("Missing media-upload-execution-request.json. Run media-upload-executor first.")
    elif media_status != "media_ready_payload_generated_from_uploaded_urls":
        blockers.append(f"Media upload execution is not media_ready_payload_generated_from_uploaded_urls: {media_status}.")
    if not media_url_map:
        blockers.append("Missing media-url-map.json. Upload/select media and provide confirmed public URLs first.")
    if not media_ready_payload:
        blockers.append("Missing rich-content-cms-payload.media-ready.json. Generate media-ready CMS payload before publish handoff.")
    if editor_applied_payload:
        if editor_apply_status and editor_apply_status != "editor_applied_payload_ready_for_owner_review":
            blockers.append(f"Editor-applied payload QA is not ready: {editor_apply_status}. Run rich-editor-apply and resolve blockers first.")
        if not safe_dict(editor_applied_payload.get("editor_applied")):
            blockers.append("Editor-applied payload is missing editor_applied safety metadata.")
        media_ready_uses_editor_payload = bool(safe_dict(media_ready_payload.get("editor_applied"))) if media_ready_payload else False
        if media_ready_payload and not media_ready_uses_editor_payload:
            warnings.append("Editor-applied payload exists, but the media-ready payload does not include editor_applied metadata; verify edited content was not lost.")
        if cms_request and selected_cms_payload_path:
            normalized_selected = resolve_path(root, selected_cms_payload_path)
            editor_path = root / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json"
            media_ready_path = root / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json"
            if normalized_selected not in {editor_path, media_ready_path}:
                warnings.append("Editor-applied payload exists, but the CMS write request is not using editor-applied or media-ready payload.")
    if not matching_sources:
        blockers.append("No matching valid latest-research sources found for the target page pair.")
    if not queue_rows:
        warnings.append("approved-publish-queue.csv is missing or empty; publish handoff evidence is incomplete.")

    for source_name, payload in (
        ("Publish plan", publish_plan),
        ("CMS write request", cms_request),
        ("Media upload execution request", media_request),
    ):
        for blocker in safe_list(payload.get("blockers")):
            blockers.append(f"{source_name} blocker: {blocker}")
        for warning in safe_list(payload.get("warnings")):
            warnings.append(f"{source_name} warning: {warning}")

    for name, path_value in (plan_artifacts | cms_artifacts | media_artifacts).items():
        path = str(path_value or "")
        if path and not artifact_exists(root, path):
            warnings.append(f"Referenced artifact is missing: {name} -> {path}")

    no_live_actions = {
        "publish_plan_no_publish_executed": publish_plan.get("no_publish_executed") is True,
        "cms_write_no_cms_write_executed": cms_write_request.get("no_cms_write_executed") is True,
        "media_upload_no_media_upload_executed": media_request.get("no_media_upload_executed") is True,
    }
    if not all(no_live_actions.values()):
        warnings.append("One or more dry-run safety flags are missing; verify no live action was executed before continuing.")

    evidence = {
        "target_urls": sorted(targets),
        "publish_plan_status": plan_status,
        "cms_write_request_status": cms_status,
        "media_upload_execution_status": media_status,
        "valid_latest_research_source_count": len(matching_sources),
        "latest_research_sources": [
            {
                "target_url": row.get("target_url", ""),
                "source_title": row.get("source_title", ""),
                "source_url": row.get("source_url", ""),
                "publisher": row.get("publisher", ""),
                "claim_boundary": row.get("claim_boundary", ""),
            }
            for row in matching_sources
        ],
        "approved_queue_count": len(queue_rows),
        "media_upload_queue_count": len(media_queue),
        "planned_media_operation_count": len(media_ops),
        "media_url_map_present": bool(media_url_map),
        "media_ready_payload_present": bool(media_ready_payload),
        "editor_applied_payload_present": bool(editor_applied_payload),
        "editor_applied_status": editor_apply_status,
        "editor_applied_used_edited_blocks": editor_apply_summary.get("used_edited_blocks", False) if editor_apply_summary else False,
        "media_ready_uses_editor_applied_payload": bool(safe_dict(media_ready_payload.get("editor_applied"))) if media_ready_payload else False,
        "cms_payload_path_used_by_write_request": selected_cms_payload_path,
        "cms_payload_selection": cms_write_request.get("cms_payload_selection", ""),
        "no_live_actions_executed_flags": no_live_actions,
    }
    return blockers, warnings, evidence


def render_report(result: PublishReadinessResult) -> str:
    evidence = result.evidence
    lines = [
        "# Publish Readiness Handoff Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: {result.status}",
        f"- Target URLs: `{', '.join(evidence.get('target_urls', [])) or 'N/A'}`",
        f"- Latest research sources: {evidence.get('valid_latest_research_source_count', 0)}",
        f"- Media upload queue items: {evidence.get('media_upload_queue_count', 0)}",
        f"- Planned media operations: {evidence.get('planned_media_operation_count', 0)}",
        "- 执行状态: readiness-only；未上传媒体、未写 CMS、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把最新研究、富文本内容包、媒体上传、媒体 URL、CMS payload、发布计划和 dry-run 写入请求汇总成统一发布 handoff 审核门。这个报告用于判断是否可以进入业主批准后的执行阶段，而不是执行发布。",
        "",
        "## Readiness Evidence",
        "",
        f"- Publish plan status: `{evidence.get('publish_plan_status', 'missing')}`",
        f"- CMS write request status: `{evidence.get('cms_write_request_status', 'missing')}`",
        f"- Media upload execution status: `{evidence.get('media_upload_execution_status', 'missing')}`",
        f"- Media URL map present: `{evidence.get('media_url_map_present', False)}`",
        f"- Media-ready CMS payload present: `{evidence.get('media_ready_payload_present', False)}`",
        f"- Editor-applied payload present: `{evidence.get('editor_applied_payload_present', False)}`",
        f"- Editor-applied used edited blocks: `{evidence.get('editor_applied_used_edited_blocks', False)}`",
        f"- Media-ready uses editor-applied payload: `{evidence.get('media_ready_uses_editor_applied_payload', False)}`",
        f"- CMS payload path used by write request: `{evidence.get('cms_payload_path_used_by_write_request', '')}`",
        f"- CMS payload selection: `{evidence.get('cms_payload_selection', '')}`",
        f"- No live actions executed flags: `{json.dumps(evidence.get('no_live_actions_executed_flags', {}), ensure_ascii=False)}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Latest Research Sources", ""])
    sources = safe_list(evidence.get("latest_research_sources"))
    if sources:
        for raw in sources:
            row = safe_dict(raw)
            lines.append(f"- {row.get('publisher', '')} | {row.get('source_title', '')} | {row.get('source_url', '')}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Owner Handoff Notes",
            "",
            "- 只有 Status 为 `ready_for_owner_approved_publish_handoff` 时，才适合进入业主批准后的发布执行。",
            "- 当前报告本身不代表授权；真实执行仍需要业主批准具体内容包、明确执行、QA 通过、媒体 URL 确认、备份、changelog 和 rollback plan。",
            "- 任何生成图片都必须继续标注为 design/rendering concept，不能描述为真实完工案例或客户照片。",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifacts(root: Path, result: PublishReadinessResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    json_path = data_dir / READINESS_JSON_NAME
    report_path = reports_dir / f"{today}-publish-readiness-report.md"
    result.artifacts.update({"readiness_json": str(json_path), "readiness_report": str(report_path)})
    write_text(
        json_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "evidence": result.evidence,
                "artifacts": result.artifacts,
                "safety_note": "Readiness-only artifact. No media upload, CMS write, source edit, publish, or deployment was executed.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return json_path, report_path


def run_publish_readiness(
    root: Path,
    *,
    publish_plan_path: str = "",
    cms_request_path: str = "",
    media_request_path: str = "",
    media_url_map_path: str = "",
    media_ready_payload_path: str = "",
    research_log_path: str = "",
    queue_path: str = "",
) -> tuple[PublishReadinessResult, tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    publish_plan_file = resolve_path(root, publish_plan_path) if publish_plan_path else data_dir / "publish-execution-plan.json"
    cms_request_file = resolve_path(root, cms_request_path) if cms_request_path else data_dir / "cms-write-request.json"
    media_request_file = resolve_path(root, media_request_path) if media_request_path else data_dir / "media-upload-execution-request.json"
    media_url_map_file = resolve_path(root, media_url_map_path) if media_url_map_path else data_dir / "media-url-map.json"
    media_ready_payload_file = (
        resolve_path(root, media_ready_payload_path)
        if media_ready_payload_path
        else data_dir / "rich-content-cms-payload.media-ready.json"
    )
    research_log_file = resolve_path(root, research_log_path) if research_log_path else data_dir / "research-source-log.csv"
    queue_file = resolve_path(root, queue_path) if queue_path else data_dir / "approved-publish-queue.csv"

    publish_plan = read_json(publish_plan_file)
    cms_request = read_json(cms_request_file)
    media_request = read_json(media_request_file)
    media_url_map = read_json(media_url_map_file)
    media_ready_payload = read_json(media_ready_payload_file)
    research_rows = read_csv_rows(research_log_file)
    queue_rows = read_csv_rows(queue_file)
    blockers, warnings, evidence = evaluate_readiness(
        root=root,
        publish_plan=publish_plan,
        cms_request=cms_request,
        media_request=media_request,
        media_url_map=media_url_map,
        media_ready_payload=media_ready_payload,
        research_rows=research_rows,
        queue_rows=queue_rows,
    )
    status = "ready_for_owner_approved_publish_handoff" if not blockers else "blocked_before_publish_handoff"
    result = PublishReadinessResult(status=status, blockers=blockers, warnings=warnings, evidence=evidence)
    artifacts = write_artifacts(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize publishing readiness; does not publish.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--publish-plan-path", default="")
    parser.add_argument("--cms-request-path", default="")
    parser.add_argument("--media-request-path", default="")
    parser.add_argument("--media-url-map-path", default="")
    parser.add_argument("--media-ready-payload-path", default="")
    parser.add_argument("--research-log-path", default="")
    parser.add_argument("--queue-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_readiness(
        Path(args.root),
        publish_plan_path=args.publish_plan_path,
        cms_request_path=args.cms_request_path,
        media_request_path=args.media_request_path,
        media_url_map_path=args.media_url_map_path,
        media_ready_payload_path=args.media_ready_payload_path,
        research_log_path=args.research_log_path,
        queue_path=args.queue_path,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
