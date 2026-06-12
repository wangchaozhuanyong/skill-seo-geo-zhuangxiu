#!/usr/bin/env python3
"""Run the next safe no-write Content Studio step from an owner decision."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from content_studio_media_ready_handoff import run_content_studio_media_ready_handoff
from content_studio_operator_ready_handoff import run_content_studio_operator_ready_handoff
from content_studio_owner_decision_status import run_content_studio_owner_decision_status
from content_studio_publish_prep import run_content_studio_publish_prep


SUMMARY_NAME = "content-studio-decision-orchestration.json"
REPORT_NAME = "content-studio-decision-orchestration.md"


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def step_summary(name: str, payload: dict[str, Any], artifacts: list[Path] | tuple[Path, ...]) -> dict[str, Any]:
    return {
        "step": name,
        "status": str(payload.get("status", "")),
        "blockers": safe_list(payload.get("blockers")),
        "warnings": safe_list(payload.get("warnings")),
        "artifacts": [str(path) for path in artifacts],
    }


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Decision Orchestration",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- 决策动作: `{summary.get('orchestrated_action')}`",
        f"- 目标页面: `{summary.get('target_url') or 'not_found'}`",
        f"- 配对页面: `{summary.get('paired_url') or 'not_found'}`",
        "- 执行状态: owner-decision no-write orchestration；未上传媒体、未写 CMS、未改源码、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把业主决定状态接到安全编排器：系统会根据业主填写的模板自动推进下一步本地准备，或在缺少确认时停住。它只生成本地证据，不执行真实发布。",
        "",
        "## Step Status",
        "",
    ]
    for step in safe_list(summary.get("steps")):
        item = safe_dict(step)
        lines.append(f"- {item.get('step')}: `{item.get('status')}` / blockers `{len(safe_list(item.get('blockers')))}` / artifacts `{len(safe_list(item.get('artifacts')))}`")
    lines.extend(["", "## Blockers", ""])
    blockers = safe_list(summary.get("blockers"))
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = safe_list(summary.get("warnings"))
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- `owner_review_only` 或缺少确认时只刷新状态并停住。",
            "- `media_ready_handoff_only` 只会消费已确认 URL map，命令本身不上传图片。",
            "- `approved_dry_run_only` 只会刷新本地 publish-prep / dry-run 证据，不调用 CMS/admin helper。",
            "- `operator_ready_handoff_only` 只会刷新本地 operator-ready 交接证据，不调用 CMS/admin helper。",
            "- `live_publish_requires_separate_confirmation` 不会自动 live；必须业主另发明确执行指令并满足 live 门禁。",
            "- 生成图片仍必须作为 design/rendering concept，不能描述为真实完工项目证明。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_decision_orchestrator(
    root: Path,
    *,
    decision_path: str = "",
    media_status_path: str = "",
    approval_packet_path: str = "",
    uploaded_url_map_path: str = "",
    candidate_path: str = "",
    website_root: str = "",
    mode: str = "dry-run",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    artifacts: list[Path] = []
    steps: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []

    decision_status, decision_artifacts = run_content_studio_owner_decision_status(
        root,
        decision_path=decision_path,
        media_status_path=media_status_path,
        approval_packet_path=approval_packet_path,
        website_root=website_root,
    )
    artifacts.extend(decision_artifacts)
    steps.append(step_summary("content_studio_owner_decision_status", decision_status, decision_artifacts))
    blockers.extend(f"content_studio_owner_decision_status: {item}" for item in safe_list(decision_status.get("blockers")))
    warnings.extend(f"content_studio_owner_decision_status: {item}" for item in safe_list(decision_status.get("warnings")))

    status = str(decision_status.get("status", ""))
    decision = safe_dict(decision_status.get("decision"))
    orchestrated_action = "status_only"

    if status in {"owner_decision_review_only", "owner_decision_waiting_owner_input", "owner_decision_status_blocked_missing_inputs"}:
        orchestrated_action = "no_action_waiting_owner_input"
        if safe_list(decision_status.get("missing_decisions")):
            blockers.extend(f"Missing owner decision: {item}" for item in safe_list(decision_status.get("missing_decisions")))
    elif status == "owner_decision_ready_for_media_handoff":
        orchestrated_action = "run_media_ready_handoff_no_write"
        media_summary, media_artifacts = run_content_studio_media_ready_handoff(
            root,
            uploaded_url_map_path=uploaded_url_map_path,
            candidate_path=candidate_path,
            website_root=website_root,
            mode=mode,
            owner_approved=True,
            explicit_execution=True,
            qa_passed=True,
            storage_ready=True,
            uploaded_confirmed=True,
            latest_research_verified=decision.get("latest_research_verified") is True,
            allow_blocked_plan=True,
        )
        artifacts.extend(media_artifacts)
        steps.append(step_summary("content_studio_media_ready_handoff", media_summary, media_artifacts))
        blockers.extend(f"content_studio_media_ready_handoff: {item}" for item in safe_list(media_summary.get("blockers")))
        warnings.extend(f"content_studio_media_ready_handoff: {item}" for item in safe_list(media_summary.get("warnings")))
    elif status in {"owner_decision_ready_for_approved_dry_run", "owner_decision_media_handoff_complete_or_not_required"}:
        orchestrated_action = "run_approved_dry_run_no_write"
        prep_summary, prep_artifacts = run_content_studio_publish_prep(
            root,
            candidate_path=candidate_path,
            website_root=website_root,
            mode=mode,
            owner_approved=True,
            explicit_execution=True,
            qa_passed=True,
            media_ready=True,
            latest_research_verified=decision.get("latest_research_verified") is True,
            allow_blocked_plan=True,
        )
        artifacts.extend(prep_artifacts)
        steps.append(step_summary("content_studio_publish_prep", prep_summary, prep_artifacts))
        blockers.extend(f"content_studio_publish_prep: {item}" for item in safe_list(prep_summary.get("blockers")))
        warnings.extend(f"content_studio_publish_prep: {item}" for item in safe_list(prep_summary.get("warnings")))
    elif status == "owner_decision_ready_for_operator_handoff":
        orchestrated_action = "run_operator_ready_handoff_no_write"
        operator_summary, operator_artifacts = run_content_studio_operator_ready_handoff(
            root,
            uploaded_url_map_path=uploaded_url_map_path,
            website_root=website_root,
            mode=mode,
            owner_approved=True,
            explicit_execution=True,
            qa_passed=True,
            storage_ready=True,
            uploaded_confirmed=True,
            latest_research_verified=decision.get("latest_research_verified") is True,
            allow_blocked_plan=True,
            allow_blocked_operator=True,
        )
        artifacts.extend(operator_artifacts)
        steps.append(step_summary("content_studio_operator_ready_handoff", operator_summary, operator_artifacts))
        blockers.extend(f"content_studio_operator_ready_handoff: {item}" for item in safe_list(operator_summary.get("blockers")))
        warnings.extend(f"content_studio_operator_ready_handoff: {item}" for item in safe_list(operator_summary.get("warnings")))
    elif status == "owner_decision_live_requires_separate_confirmation":
        orchestrated_action = "live_confirmation_required_no_action"
        blockers.append("Live publish scope requires a separate natural-language owner execution instruction plus live confirmation; no live action was run.")
    else:
        orchestrated_action = "unknown_decision_status_no_action"
        blockers.append(f"Unsupported decision status for orchestration: {status}")

    ok_actions = {
        "no_action_waiting_owner_input",
        "run_media_ready_handoff_no_write",
        "run_approved_dry_run_no_write",
        "run_operator_ready_handoff_no_write",
    }
    summary_status = "decision_orchestration_waiting_owner_input" if orchestrated_action == "no_action_waiting_owner_input" else "decision_orchestration_waiting_owner_review"
    if orchestrated_action not in ok_actions or any("Unsupported" in blocker for blocker in blockers):
        summary_status = "decision_orchestration_blocked"

    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": summary_status,
        "orchestrated_action": orchestrated_action,
        "target_url": decision_status.get("target_url", ""),
        "paired_url": decision_status.get("paired_url", ""),
        "owner_decision_status": status,
        "steps": steps,
        "blockers": blockers,
        "warnings": warnings,
        "artifacts": {
            "decision_orchestration_json": str(data_path),
            "decision_orchestration_report": str(report_path),
        },
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    artifacts.extend([data_path, report_path])
    return summary, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the next safe no-write Content Studio step from an owner decision.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--decision-path", default="")
    parser.add_argument("--media-status-path", default="")
    parser.add_argument("--approval-packet-path", default="")
    parser.add_argument("--uploaded-url-map-path", default="")
    parser.add_argument("--candidate-path", default="")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_decision_orchestrator(
        Path(args.root),
        decision_path=args.decision_path,
        media_status_path=args.media_status_path,
        approval_packet_path=args.approval_packet_path,
        uploaded_url_map_path=args.uploaded_url_map_path,
        candidate_path=args.candidate_path,
        website_root=args.website_root,
        mode=args.mode,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] != "decision_orchestration_blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
