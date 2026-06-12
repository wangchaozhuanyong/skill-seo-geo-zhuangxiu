#!/usr/bin/env python3
"""Validate an owner-filled Content Studio decision template without executing."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


DEFAULT_DECISION = "seo-workspace/data/content-studio-owner-decision.template.json"
DEFAULT_MEDIA_STATUS = "seo-workspace/data/content-studio-media-status.json"
DEFAULT_APPROVAL_PACKET = "seo-workspace/data/content-studio-approval-packet.json"
ALLOWED_SCOPES = {
    "owner_review_only",
    "media_ready_handoff_only",
    "approved_dry_run_only",
    "operator_ready_handoff_only",
    "live_publish_requires_separate_confirmation",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def bool_value(payload: dict[str, Any], key: str) -> bool:
    return payload.get(key) is True


def media_needs_confirmation(media_status: dict[str, Any]) -> bool:
    status = str(media_status.get("status", ""))
    counts = safe_dict(media_status.get("counts"))
    if status in {"media_urls_ready_for_handoff", "media_ready_payload_present"}:
        return False
    for key in ("missing_public_url", "invalid_public_url", "needs_owner_confirmation", "placeholder_url"):
        value = counts.get(key)
        if isinstance(value, int) and value > 0:
            return True
    return status in {"media_urls_need_owner_input", "media_status_missing_inputs"}


def build_commands(scope: str, target_url: str, website_root: str) -> list[dict[str, str]]:
    base = "python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py"
    owner_review = f"{base} content-studio-owner-review-package"
    prep = f"{base} content-studio-publish-prep"
    if website_root:
        owner_review += f" --website-root {website_root}"
        prep += f" --website-root {website_root}"
    if target_url:
        owner_review += f" --target-url {target_url}"
    commands = [
        {
            "step": "refresh_decision_status",
            "command": f"{base} content-studio-owner-decision-status",
            "note_zh": "重新读取业主决定模板，只判断状态，不执行任何写入。",
        },
        {
            "step": "import_filled_owner_decision",
            "command": f"{base} content-studio-owner-decision-import --filled-decision-path seo-workspace/data/content-studio-owner-decision.filled.json",
            "note_zh": "导入业主从 HTML 表单下载的 filled JSON；只更新本地 decision template，不执行发布。",
        },
        {
            "step": "orchestrate_next_safe_step",
            "command": f"{base} content-studio-decision-orchestrator",
            "note_zh": "按业主决定自动推进下一步安全准备；仍不上传、不写 CMS、不发布。",
        },
        {
            "step": "refresh_owner_review_package",
            "command": owner_review,
            "note_zh": "刷新 dashboard 和审核总包，仍然不发布。",
        },
    ]
    if scope == "media_ready_handoff_only":
        commands.append(
            {
                "step": "media_ready_handoff",
                "command": f"{base} content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed",
                "note_zh": "只在图片公开 URL 和 owner confirmation 都完成后运行；命令本身不上传、不发布。",
            }
        )
    if scope in {"approved_dry_run_only", "live_publish_requires_separate_confirmation"}:
        commands.append(
            {
                "step": "approved_dry_run_handoff",
                "command": f"{prep} --owner-approved --explicit-execution --qa-passed --media-ready --latest-research-verified",
                "note_zh": "生成更接近执行前的 dry-run handoff；仍不调用 CMS、不改源码、不发布。",
            }
        )
    if scope == "operator_ready_handoff_only":
        operator_command = (
            f"{base} content-studio-operator-ready-handoff "
            "--uploaded-url-map-path seo-workspace/data/uploaded-url-map.json "
            "--owner-approved --explicit-execution --qa-passed --storage-ready "
            "--uploaded-confirmed --latest-research-verified --allow-blocked-plan --allow-blocked-operator"
        )
        if website_root:
            operator_command += f" --website-root {website_root}"
        commands.append(
            {
                "step": "operator_ready_handoff",
                "command": operator_command,
                "note_zh": "刷新媒体、publish-prep、bundle 和 operator handoff 证据；仍不调用 CMS、不改源码、不发布。",
            }
        )
    if scope == "live_publish_requires_separate_confirmation":
        commands.append(
            {
                "step": "future_live_gate",
                "command": f"{base} publish-operator-ready-handoff --website-root {website_root or '/path/to/website'} --owner-approved --explicit-execution --qa-passed",
                "note_zh": "只准备未来执行输入；真实 live 发布仍需要业主另发明确执行指令和 live confirmation。",
            }
        )
    return commands


def evaluate_decision(
    decision_payload: dict[str, Any],
    media_status: dict[str, Any],
    approval_packet: dict[str, Any],
    *,
    website_root: str = "",
) -> dict[str, Any]:
    decision = safe_dict(decision_payload.get("decision"))
    target_url = str(decision_payload.get("target_url") or approval_packet.get("target_url") or "")
    paired_url = str(decision_payload.get("paired_url") or approval_packet.get("paired_url") or "")
    scope = str(decision.get("allowed_execution_scope", "owner_review_only"))
    blockers: list[str] = []
    warnings: list[str] = []

    if not decision_payload:
        blockers.append("Missing owner decision template. Run content-studio-approval-packet or content-studio-owner-review-package first.")
    if scope not in ALLOWED_SCOPES:
        blockers.append(f"Unsupported allowed_execution_scope: {scope or 'missing'}.")
    if decision_payload.get("approval_is_not_execution") is not True:
        warnings.append("approval_is_not_execution flag is missing or false; keep treating this as review-only.")

    media_required = media_needs_confirmation(media_status)
    content_approved = bool_value(decision, "content_approved")
    media_urls_confirmed = bool_value(decision, "media_urls_confirmed")
    qa_approved = bool_value(decision, "qa_approved")
    latest_research_verified = bool_value(decision, "latest_research_verified")
    explicit_execution_requested = bool_value(decision, "explicit_execution_requested")

    missing_decisions: list[str] = []
    if not content_approved:
        missing_decisions.append("content_approved=true")
    if not qa_approved:
        missing_decisions.append("qa_approved=true")
    if media_required and not media_urls_confirmed:
        missing_decisions.append("media_urls_confirmed=true")
    if scope in {"approved_dry_run_only", "operator_ready_handoff_only", "live_publish_requires_separate_confirmation"} and not latest_research_verified:
        missing_decisions.append("latest_research_verified=true")
    if scope != "owner_review_only" and not explicit_execution_requested:
        missing_decisions.append("explicit_execution_requested=true")

    if blockers:
        status = "owner_decision_status_blocked_missing_inputs"
    elif scope == "owner_review_only":
        status = "owner_decision_review_only"
    elif missing_decisions:
        status = "owner_decision_waiting_owner_input"
    elif media_required and scope in {"media_ready_handoff_only", "approved_dry_run_only", "operator_ready_handoff_only", "live_publish_requires_separate_confirmation"}:
        status = "owner_decision_ready_for_media_handoff"
    elif scope == "media_ready_handoff_only":
        status = "owner_decision_media_handoff_complete_or_not_required"
    elif scope == "approved_dry_run_only":
        status = "owner_decision_ready_for_approved_dry_run"
    elif scope == "operator_ready_handoff_only":
        status = "owner_decision_ready_for_operator_handoff"
    else:
        status = "owner_decision_live_requires_separate_confirmation"

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "target_url": target_url,
        "paired_url": paired_url,
        "decision": decision,
        "allowed_execution_scope": scope,
        "missing_decisions": missing_decisions,
        "media_required": media_required,
        "media_status": media_status.get("status", "not_found") if media_status else "not_found",
        "blockers": blockers,
        "warnings": warnings,
        "recommended_commands": build_commands(scope, target_url, website_root),
        "approval_is_not_execution": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Owner Decision Status",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- 目标页面: `{summary.get('target_url') or 'not_found'}`",
        f"- 配对页面: `{summary.get('paired_url') or 'not_found'}`",
        f"- 允许范围: `{summary.get('allowed_execution_scope')}`",
        "- 执行状态: 只读取业主决定；未执行上传、CMS 写入、源码修改、发布或部署",
        "",
        "## 今日决策",
        "",
        "今天新增业主决定状态检查：把业主填写的 approval template 转成机器可判断的下一步状态，但不会自动执行任何发布动作。",
        "",
        "## 缺少的业主确认",
        "",
    ]
    missing = safe_list(summary.get("missing_decisions"))
    if missing:
        lines.extend(f"- `{item}`" for item in missing)
    else:
        lines.append("- None")
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
    lines.extend(["", "## 推荐下一步命令", ""])
    for command in safe_list(summary.get("recommended_commands")):
        item = safe_dict(command)
        lines.append(f"- {item.get('step')}: `{item.get('command')}`")
        lines.append(f"  说明: {item.get('note_zh')}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- approval / decision 仍不等于 execution。",
            "- 真实发布必须由业主另外明确说执行哪个页面、哪个范围。",
            "- live 发布还需要 backup、changelog、rollback、QA、媒体证据和 live confirmation。",
            "- 设计图、效果图和生成图只能作为 design concept / rendering concept，不能写成真实完工案例证明。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_owner_decision_status(
    root: Path,
    *,
    decision_path: str = "",
    media_status_path: str = "",
    approval_packet_path: str = "",
    website_root: str = "",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    decision_file = resolve_path(root, decision_path or DEFAULT_DECISION)
    media_file = resolve_path(root, media_status_path or DEFAULT_MEDIA_STATUS)
    approval_file = resolve_path(root, approval_packet_path or DEFAULT_APPROVAL_PACKET)
    summary = evaluate_decision(
        read_json(decision_file),
        read_json(media_file),
        read_json(approval_file),
        website_root=website_root,
    )
    summary["decision_path"] = str(decision_file)
    summary["media_status_path"] = str(media_file)
    summary["approval_packet_path"] = str(approval_file)
    data_path = root / "seo-workspace" / "data" / "content-studio-owner-decision-status.json"
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-owner-decision-status.md"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary, [data_path, report_path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an owner-filled Content Studio decision template without executing.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--decision-path", default="")
    parser.add_argument("--media-status-path", default="")
    parser.add_argument("--approval-packet-path", default="")
    parser.add_argument("--website-root", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_owner_decision_status(
        Path(args.root),
        decision_path=args.decision_path,
        media_status_path=args.media_status_path,
        approval_packet_path=args.approval_packet_path,
        website_root=args.website_root,
    )
    for output in artifacts:
        print(output)
    return 0 if not summary.get("blockers") else 1


if __name__ == "__main__":
    raise SystemExit(main())
