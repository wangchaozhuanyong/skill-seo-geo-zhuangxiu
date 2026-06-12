#!/usr/bin/env python3
"""Refresh the no-write operator-ready publishing handoff chain."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from publish_approved_execution_input import run_publish_approved_execution_input
from publish_approved_executor import run_publish_approved_executor
from publish_bundle import run_publish_bundle
from publish_executor import run_publish_executor
from publish_implementation_package import run_publish_implementation_package
from publish_operator_package import run_publish_operator_package
from publish_readiness import run_publish_readiness
from website_publish_adapter import run_website_publish_adapter


SUMMARY_NAME = "publish-operator-ready-handoff.json"
REPORT_NAME = "publish-operator-ready-handoff.md"


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def result_summary(name: str, result: Any, artifacts: list[Path] | tuple[Path, ...]) -> dict[str, Any]:
    return {
        "step": name,
        "status": str(getattr(result, "status", "")),
        "ok": bool(getattr(result, "ok", False)),
        "blockers": list(getattr(result, "blockers", []) or []),
        "warnings": list(getattr(result, "warnings", []) or []),
        "artifacts": [str(path) for path in artifacts],
    }


def normalize_blocker(blocker: str) -> str:
    text = blocker.strip()
    while " blocker: " in text:
        text = text.split(" blocker: ", 1)[1].strip()
    for prefix in (
        "publish_executor: ",
        "publish_readiness: ",
        "publish_bundle: ",
        "publish_approved_executor: ",
        "publish_implementation_package: ",
        "publish_operator_package: ",
        "publish_approved_execution_input: ",
        "website_publish_adapter: ",
    ):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
    return text


def normalize_warning(warning: str) -> str:
    text = normalize_blocker(warning)
    while " warning: " in text:
        text = text.split(" warning: ", 1)[1].strip()
    return text


def summarize_blockers(blockers: list[str], limit: int = 18) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for blocker in blockers:
        normalized = normalize_blocker(blocker)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if len(output) < limit:
            output.append(normalized)
    remaining = len(seen) - len(output)
    if remaining > 0:
        output.append(f"... plus {remaining} more unique blocker categories in JSON evidence.")
    return output


def summarize_warnings(warnings: list[str], limit: int = 12) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for warning in warnings:
        normalized = normalize_warning(warning)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if len(output) < limit:
            output.append(normalized)
    remaining = len(seen) - len(output)
    if remaining > 0:
        output.append(f"... plus {remaining} more unique warning categories in JSON evidence.")
    return output


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Publish Operator Ready Handoff",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{summary.get('status')}`",
        f"- Operator ready: `{summary.get('operator_ready')}`",
        f"- Execution input ready: `{summary.get('execution_input_ready')}`",
        "- 执行状态: operator-ready handoff only；未运行命令、未调用 CMS、未改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把 media-ready 之后的发布门禁一次性刷新到 operator/input 阶段：CMS dry-run 请求、readiness、bundle、approved executor 模拟、implementation package、operator command 和受保护执行输入模板。该流程只刷新本地证据，不执行发布。",
        "",
        "## Step Status",
        "",
    ]
    for step in summary.get("steps", []):
        lines.append(f"- {step['step']}: `{step['status']}` / blockers `{len(step.get('blockers') or [])}` / artifacts `{len(step.get('artifacts') or [])}`")
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    blocker_summary = summary.get("blocker_summary") if isinstance(summary.get("blocker_summary"), list) else summarize_blockers(blockers)
    lines.extend(["", "## Blockers", ""])
    if blockers:
        lines.append(f"- 完整阻断证据数量: `{len(blockers)}`，详见 `publish-operator-ready-handoff.json`。")
    lines.extend(f"- {item}" for item in blocker_summary) if blocker_summary else lines.append("- None")
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    warning_summary = summary.get("warning_summary") if isinstance(summary.get("warning_summary"), list) else summarize_warnings(warnings)
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.append(f"- 完整 warning 证据数量: `{len(warnings)}`，详见 `publish-operator-ready-handoff.json`。")
    lines.extend(f"- {item}" for item in warning_summary) if warning_summary else lines.append("- None")
    lines.extend(["", "## Artifacts", ""])
    artifacts = summary.get("artifacts") if isinstance(summary.get("artifacts"), dict) else {}
    for name, path in artifacts.items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本命令不运行 npm，不调用 CMS/admin helper，不上传媒体，不写源码，不发布，不部署。",
            "- 即使所有本地 handoff ready，真实执行仍需业主明确指定执行、备份、QA、回滚和执行回执。",
            "- 概念图仍必须保持 design/rendering concept 标注。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def run_publish_operator_ready_handoff(
    root: Path,
    *,
    website_root: str = "",
    mode: str = "dry-run",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    media_ready: bool = False,
    latest_research_verified: bool = False,
    allow_blocked_plan: bool = False,
    allow_blocked_operator: bool = False,
    backup_path: str = "",
    changelog_path: str = "",
    rollback_plan_path: str = "",
    confirm_live: bool = False,
    allowed_target_urls: list[str] | None = None,
) -> tuple[dict[str, Any], tuple[Path, ...]]:
    root = root.resolve()
    allowed_target_urls = allowed_target_urls or []
    steps: list[dict[str, Any]] = []
    artifacts: list[Path] = []

    adapter_result, adapter_artifacts = run_website_publish_adapter(root, website_root=website_root)
    steps.append(result_summary("website_publish_adapter", adapter_result, adapter_artifacts))
    artifacts.extend(adapter_artifacts)

    executor_result, executor_artifacts = run_publish_executor(
        root,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        media_ready=media_ready,
        allow_blocked_plan=allow_blocked_plan,
    )
    steps.append(result_summary("publish_executor", executor_result, executor_artifacts))
    artifacts.extend(executor_artifacts)

    readiness_result, readiness_artifacts = run_publish_readiness(root)
    steps.append(result_summary("publish_readiness", readiness_result, readiness_artifacts))
    artifacts.extend(readiness_artifacts)

    bundle_result, bundle_artifacts = run_publish_bundle(root)
    steps.append(result_summary("publish_bundle", bundle_result, bundle_artifacts))
    artifacts.extend(bundle_artifacts)

    approved_result, approved_artifacts = run_publish_approved_executor(
        root,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        backup_path=backup_path,
        changelog_path=changelog_path,
        rollback_plan_path=rollback_plan_path,
        confirm_live=confirm_live,
        allowed_target_urls=allowed_target_urls,
    )
    steps.append(result_summary("publish_approved_executor", approved_result, approved_artifacts))
    artifacts.extend(approved_artifacts)

    implementation_result, implementation_artifacts = run_publish_implementation_package(root, website_root=website_root)
    steps.append(result_summary("publish_implementation_package", implementation_result, implementation_artifacts))
    artifacts.extend(implementation_artifacts)

    operator_result, operator_artifacts = run_publish_operator_package(root)
    steps.append(result_summary("publish_operator_package", operator_result, operator_artifacts))
    artifacts.extend(operator_artifacts)

    execution_input_result, execution_input_artifacts = run_publish_approved_execution_input(root, allow_blocked_operator=allow_blocked_operator)
    steps.append(result_summary("publish_approved_execution_input", execution_input_result, execution_input_artifacts))
    artifacts.extend(execution_input_artifacts)

    blockers: list[str] = []
    warnings: list[str] = []
    for step in steps:
        blockers.extend(f"{step['step']}: {blocker}" for blocker in step.get("blockers", []))
        warnings.extend(f"{step['step']}: {warning}" for warning in step.get("warnings", []))
    operator_ready = operator_result.ok
    execution_input_ready = execution_input_result.ok
    status = "operator_ready_handoff_waiting_owner_review" if operator_ready and execution_input_ready else "operator_ready_handoff_blocked"

    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "operator_ready": operator_ready,
        "execution_input_ready": execution_input_ready,
        "steps": steps,
        "blockers": blockers,
        "blocker_summary": summarize_blockers(blockers),
        "warnings": warnings,
        "warning_summary": summarize_warnings(warnings),
        "artifacts": {
            "operator_ready_handoff_json": str(data_path),
            "operator_ready_handoff_report": str(report_path),
            "operator_command": str(root / "seo-workspace" / "data" / "publish-operator-command.json"),
            "approved_execution_input": str(root / "seo-workspace" / "data" / "publish-approved-execution-input.json"),
            "execution_runner_template": str(root / "seo-workspace" / "tools" / "publish-approved-execution-runner.mjs"),
            "execution_result_template": str(root / "seo-workspace" / "data" / "publish-execution-result.template.json"),
        },
        "no_commands_executed": True,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
    }
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, tuple([data_path, report_path, *artifacts])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh no-write operator-ready handoff chain.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--media-ready", action="store_true")
    parser.add_argument("--latest-research-verified", action="store_true")
    parser.add_argument("--allow-blocked-plan", action="store_true")
    parser.add_argument("--allow-blocked-operator", action="store_true")
    parser.add_argument("--backup-path", default="")
    parser.add_argument("--changelog-path", default="")
    parser.add_argument("--rollback-plan-path", default="")
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--allowed-target-url", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_publish_operator_ready_handoff(
        Path(args.root),
        website_root=args.website_root,
        mode=args.mode,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        media_ready=args.media_ready,
        latest_research_verified=args.latest_research_verified,
        allow_blocked_plan=args.allow_blocked_plan,
        allow_blocked_operator=args.allow_blocked_operator,
        backup_path=args.backup_path,
        changelog_path=args.changelog_path,
        rollback_plan_path=args.rollback_plan_path,
        confirm_live=args.confirm_live,
        allowed_target_urls=args.allowed_target_url,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "operator_ready_handoff_waiting_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
