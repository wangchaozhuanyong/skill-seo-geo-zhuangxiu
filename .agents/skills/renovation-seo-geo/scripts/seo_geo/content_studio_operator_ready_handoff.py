#!/usr/bin/env python3
"""Refresh Content Studio media-ready through operator-ready handoff without live execution."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:  # pragma: no cover - package import path differs between CLI and tests
    from .content_studio_media_ready_handoff import run_content_studio_media_ready_handoff
    from .content_studio_media_status import run_content_studio_media_status
    from .publish_operator_ready_handoff import run_publish_operator_ready_handoff
except ImportError:  # pragma: no cover
    from content_studio_media_ready_handoff import run_content_studio_media_ready_handoff
    from content_studio_media_status import run_content_studio_media_status
    from publish_operator_ready_handoff import run_publish_operator_ready_handoff


SUMMARY_NAME = "content-studio-operator-ready-handoff.json"
REPORT_NAME = "content-studio-operator-ready-handoff.md"


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def step_summary(name: str, summary: dict[str, Any], artifacts: tuple[Path, ...] | list[Path]) -> dict[str, Any]:
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    return {
        "step": name,
        "status": str(summary.get("status", "")),
        "ok": not blockers and not str(summary.get("status", "")).endswith("_blocked"),
        "blockers": blockers,
        "warnings": warnings,
        "artifacts": [str(path) for path in artifacts if path],
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Operator Ready Handoff",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{summary.get('status')}`",
        f"- Media ready: `{summary.get('media_ready')}`",
        f"- Operator ready: `{summary.get('operator_ready')}`",
        "- 执行状态: no-write handoff only；未上传媒体、未调用 CMS、未写源码、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把图片 URL 确认后的本地发布准备链串成一个 Content Studio 入口：媒体状态复查、media-ready payload、publish-prep、readiness、bundle、operator command 和受保护执行输入模板。该命令只刷新证据，不执行发布。",
        "",
        "## Step Status",
        "",
    ]
    for step in summary.get("steps", []):
        if isinstance(step, dict):
            lines.append(f"- {step.get('step')}: `{step.get('status')}` / blockers `{len(step.get('blockers') or [])}` / artifacts `{len(step.get('artifacts') or [])}`")
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Artifacts", ""])
    artifacts = summary.get("artifacts") if isinstance(summary.get("artifacts"), dict) else {}
    for name, path in artifacts.items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本命令不上传图片，不调用 CMS/admin helper，不写源码，不发布，不部署。",
            "- 即使 operator-ready 证据生成成功，真实执行仍需要业主明确执行指令、备份、QA、回滚和执行回执。",
            "- 生成/上传图片仍必须作为设计方案、效果图方案或 rendering concept 使用，不能写成真实完工案例证明。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_operator_ready_handoff(
    root: Path,
    *,
    uploaded_url_map_path: str = "",
    cms_payload_path: str = "",
    website_root: str = "",
    mode: str = "dry-run",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    storage_ready: bool = False,
    uploaded_confirmed: bool = False,
    latest_research_verified: bool = False,
    allow_blocked_plan: bool = False,
    allow_blocked_operator: bool = False,
) -> tuple[dict[str, Any], tuple[Path, ...]]:
    root = root.resolve()
    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"

    media_status, media_status_artifacts = run_content_studio_media_status(root, uploaded_url_map_path=uploaded_url_map_path)
    media_ready, media_ready_artifacts = run_content_studio_media_ready_handoff(
        root,
        uploaded_url_map_path=uploaded_url_map_path,
        cms_payload_path=cms_payload_path,
        website_root=website_root,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        storage_ready=storage_ready,
        uploaded_confirmed=uploaded_confirmed,
        latest_research_verified=latest_research_verified,
        allow_blocked_plan=allow_blocked_plan,
    )
    operator_ready, operator_artifacts = run_publish_operator_ready_handoff(
        root,
        website_root=website_root,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        media_ready=bool(media_ready.get("media_ready")),
        latest_research_verified=latest_research_verified,
        allow_blocked_plan=allow_blocked_plan,
        allow_blocked_operator=allow_blocked_operator,
    )
    steps = [
        step_summary("content_studio_media_status", media_status, media_status_artifacts),
        step_summary("content_studio_media_ready_handoff", media_ready, media_ready_artifacts),
        step_summary("publish_operator_ready_handoff", operator_ready, operator_artifacts),
    ]
    blockers: list[str] = []
    warnings: list[str] = []
    for step in steps:
        blockers.extend(f"{step['step']}: {item}" for item in step.get("blockers", []))
        warnings.extend(f"{step['step']}: {item}" for item in step.get("warnings", []))
    media_is_ready = bool(media_ready.get("media_ready"))
    operator_is_ready = bool(operator_ready.get("operator_ready")) and bool(operator_ready.get("execution_input_ready"))
    status = "content_studio_operator_ready_handoff_waiting_owner_review" if media_is_ready and operator_is_ready else "content_studio_operator_ready_handoff_blocked"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "media_ready": media_is_ready,
        "operator_ready": operator_is_ready,
        "steps": steps,
        "blockers": blockers,
        "warnings": warnings,
        "artifacts": {
            "content_studio_operator_ready_handoff_json": str(data_path),
            "content_studio_operator_ready_handoff_report": str(report_path),
            "media_status_report": str(media_status_artifacts[-1]) if media_status_artifacts else "",
            "media_ready_handoff_report": str(media_ready_artifacts[1]) if len(media_ready_artifacts) > 1 else "",
            "operator_ready_handoff_report": str(operator_artifacts[1]) if len(operator_artifacts) > 1 else "",
            "operator_command": str(root / "seo-workspace" / "data" / "publish-operator-command.json"),
            "approved_execution_input": str(root / "seo-workspace" / "data" / "publish-approved-execution-input.json"),
        },
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
    }
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, report_path, *media_status_artifacts, *media_ready_artifacts, *operator_artifacts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Content Studio media-ready through operator-ready handoff without live execution.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--uploaded-url-map-path", default="")
    parser.add_argument("--cms-payload-path", default="")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--storage-ready", action="store_true")
    parser.add_argument("--uploaded-confirmed", action="store_true")
    parser.add_argument("--latest-research-verified", action="store_true")
    parser.add_argument("--allow-blocked-plan", action="store_true")
    parser.add_argument("--allow-blocked-operator", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_operator_ready_handoff(
        Path(args.root),
        uploaded_url_map_path=args.uploaded_url_map_path,
        cms_payload_path=args.cms_payload_path,
        website_root=args.website_root,
        mode=args.mode,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        storage_ready=args.storage_ready,
        uploaded_confirmed=args.uploaded_confirmed,
        latest_research_verified=args.latest_research_verified,
        allow_blocked_plan=args.allow_blocked_plan,
        allow_blocked_operator=args.allow_blocked_operator,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "content_studio_operator_ready_handoff_waiting_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
