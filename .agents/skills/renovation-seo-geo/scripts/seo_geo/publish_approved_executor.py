#!/usr/bin/env python3
"""Simulate an owner-approved publish executor without performing writes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


APPROVED_RECORD_JSON_NAME = "publish-approved-execution-record.json"
READY_BUNDLE_STATUS = "execution_bundle_ready_for_approved_executor"
EXPECTED_BUNDLE_ACTION = "sealed_execution_bundle_only_no_cms_write"
SIMULATION_ACTION = "approved_execution_simulation_only_no_write"
VALID_MODES = {"dry-run", "pr", "staging", "live"}
SAFETY_FLAGS = (
    "no_cms_write_executed",
    "no_source_page_write_executed",
    "no_media_upload_executed",
    "no_publish_executed",
    "no_deploy_executed",
    "no_live_actions_executed",
)


@dataclass
class ApprovedExecutorResult:
    status: str
    mode: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_record: dict[str, object] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def find_media_placeholders(value: object) -> list[str]:
    serialized = json.dumps(value, ensure_ascii=False)
    pattern = re.compile(r"NEEDS_MEDIA_UPLOAD:[^\"'\s<>]+")
    return sorted(set(pattern.findall(serialized)))


def validate_required_file(root: Path, label: str, value: str, blockers: list[str]) -> str:
    if not value:
        blockers.append(f"{label} path missing.")
        return ""
    path = resolve_path(root, value)
    if not path.exists():
        blockers.append(f"{label} path does not exist: {path}")
    return str(path)


def evaluate_approved_executor_gates(
    *,
    root: Path,
    bundle_payload: dict[str, object],
    mode: str,
    owner_approved: bool,
    explicit_execution: bool,
    qa_passed: bool,
    backup_path: str,
    changelog_path: str,
    rollback_plan_path: str,
    confirm_live: bool,
    allowed_target_urls: list[str],
) -> tuple[list[str], list[str], dict[str, str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    evidence_paths: dict[str, str] = {}
    bundle = safe_dict(bundle_payload.get("bundle"))
    helper_call = safe_dict(bundle.get("planned_helper_call"))

    if mode not in VALID_MODES:
        blockers.append(f"Unsupported approved executor mode: {mode}.")
    if not bundle_payload:
        blockers.append("Missing publish-execution-bundle.json. Run publish-bundle first.")
    elif str(bundle_payload.get("status", "")) != READY_BUNDLE_STATUS:
        blockers.append(
            f"Publish execution bundle top-level status is not {READY_BUNDLE_STATUS}: "
            f"{bundle_payload.get('status', 'missing')}."
        )
    if not bundle:
        blockers.append("Publish execution bundle has no bundle object.")
    elif str(bundle.get("status", "")) != READY_BUNDLE_STATUS:
        blockers.append(f"Publish execution bundle object is not ready: {bundle.get('status', 'missing')}.")

    for blocker in safe_list(bundle_payload.get("blockers")):
        blockers.append(f"Publish bundle blocker: {blocker}")
    for warning in safe_list(bundle_payload.get("warnings")):
        warnings.append(f"Publish bundle warning: {warning}")

    if not owner_approved:
        blockers.append("Owner approval flag missing (--owner-approved).")
    if not explicit_execution:
        blockers.append("Explicit execution flag missing (--explicit-execution).")
    if not qa_passed:
        blockers.append("QA passed flag missing (--qa-passed).")

    if str(bundle.get("action", "")) != EXPECTED_BUNDLE_ACTION:
        blockers.append("Publish bundle action is not the expected sealed no-write action.")
    if not helper_call:
        blockers.append("Publish bundle has no planned_helper_call.")
    elif not helper_call.get("function"):
        blockers.append("Publish bundle planned_helper_call has no function.")

    for flag in SAFETY_FLAGS:
        if bundle.get(flag) is not True:
            blockers.append(f"Publish bundle safety flag missing or false: {flag}.")

    if bundle.get("media_url_map_present") is not True:
        blockers.append("Media URL map evidence is missing from the bundle.")
    if bundle.get("media_ready_payload_present") is not True:
        blockers.append("Media-ready CMS payload evidence is missing from the bundle.")

    media_placeholders = find_media_placeholders(bundle_payload)
    if media_placeholders:
        blockers.append("Media placeholders remain in the execution bundle; do not execute until URLs are resolved.")

    target_url = str(bundle.get("target_url", "") or "")
    paired_url = str(bundle.get("paired_url", "") or "")
    if not target_url:
        blockers.append("Publish bundle target_url is missing.")
    if allowed_target_urls:
        allowed = {url.rstrip("/") for url in allowed_target_urls}
        if target_url.rstrip("/") not in allowed:
            blockers.append("Target URL is not in --allowed-target-url.")
        if paired_url and paired_url.rstrip("/") not in allowed:
            blockers.append("Paired URL is not in --allowed-target-url; bilingual scope would be incomplete.")

    if mode != "dry-run":
        evidence_paths["backup_path"] = validate_required_file(root, "Backup", backup_path, blockers)
        evidence_paths["changelog_path"] = validate_required_file(root, "Changelog", changelog_path, blockers)
        evidence_paths["rollback_plan_path"] = validate_required_file(root, "Rollback plan", rollback_plan_path, blockers)
    elif any([backup_path, changelog_path, rollback_plan_path]):
        for label, value in (
            ("backup_path", backup_path),
            ("changelog_path", changelog_path),
            ("rollback_plan_path", rollback_plan_path),
        ):
            if value:
                evidence_paths[label] = str(resolve_path(root, value))

    if mode == "live" and not confirm_live:
        blockers.append("Live mode confirmation missing (--confirm-live).")
    return blockers, warnings, evidence_paths


def build_execution_record(
    *,
    bundle_payload: dict[str, object],
    mode: str,
    blockers: list[str],
    warnings: list[str],
    evidence_paths: dict[str, str],
    owner_approved: bool,
    explicit_execution: bool,
    qa_passed: bool,
    confirm_live: bool,
    allowed_target_urls: list[str],
) -> dict[str, object]:
    bundle = safe_dict(bundle_payload.get("bundle"))
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "mode": mode,
        "action": SIMULATION_ACTION,
        "status": "approved_execution_simulation_ready" if not blockers else "blocked_before_approved_execution",
        "execution_allowed_for_future_executor": not blockers,
        "target_url": bundle.get("target_url", ""),
        "paired_url": bundle.get("paired_url", ""),
        "table": bundle.get("table", ""),
        "admin_helper": bundle.get("admin_helper", ""),
        "cms_payload_path": bundle.get("cms_payload_path", ""),
        "cms_payload_selection": bundle.get("cms_payload_selection", ""),
        "simulated_helper_call": safe_dict(bundle.get("planned_helper_call")),
        "payload_keys": safe_list(bundle.get("payload_keys")),
        "latest_research_sources": safe_list(bundle.get("latest_research_sources")),
        "post_write_tasks": safe_list(bundle.get("post_write_tasks")),
        "required_pre_execution_checks": safe_list(bundle.get("required_pre_execution_checks")),
        "approval_evidence": {
            "owner_approved": owner_approved,
            "explicit_execution": explicit_execution,
            "qa_passed": qa_passed,
            "confirm_live": confirm_live,
            "allowed_target_urls": allowed_target_urls,
        },
        "execution_evidence_paths": evidence_paths,
        "blockers": blockers,
        "warnings": warnings,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "safety_note": "This approved executor artifact is a simulation record only. It does not call CMS/admin helpers, write source files, upload media, publish, regenerate SEO assets, or deploy.",
    }


def render_report(result: ApprovedExecutorResult) -> str:
    record = result.execution_record
    helper = safe_dict(record.get("simulated_helper_call"))
    lines = [
        "# Publish Approved Executor Dry Run",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Mode: `{result.mode}`",
        f"- Status: `{result.status}`",
        f"- Target URL: `{record.get('target_url', 'N/A')}`",
        f"- Paired URL: `{record.get('paired_url', 'N/A')}`",
        f"- Table: `{record.get('table', 'N/A')}`",
        f"- Admin helper: `{record.get('admin_helper', 'N/A')}`",
        f"- CMS payload selection: `{record.get('cms_payload_selection', 'N/A')}`",
        "- 执行状态: approved-executor simulation only；未写 CMS、未改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天新增已批准执行器的最后门禁模拟层：它只验证 sealed bundle、业主批准、明确执行、QA、媒体、备份、变更日志和回滚证据是否齐全，并输出未来真实执行器可读取的本地记录。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Simulated Helper Call",
            "",
            f"- Function: `{helper.get('function', 'N/A')}`",
            f"- Payload keys: `{', '.join(str(item) for item in safe_list(record.get('payload_keys')))}`",
            f"- Future executor allowed: `{record.get('execution_allowed_for_future_executor', False)}`",
            "",
            "## Required Evidence",
            "",
            f"- Owner approved: `{safe_dict(record.get('approval_evidence')).get('owner_approved', False)}`",
            f"- Explicit execution: `{safe_dict(record.get('approval_evidence')).get('explicit_execution', False)}`",
            f"- QA passed: `{safe_dict(record.get('approval_evidence')).get('qa_passed', False)}`",
            f"- Confirm live: `{safe_dict(record.get('approval_evidence')).get('confirm_live', False)}`",
            f"- Evidence paths: `{json.dumps(record.get('execution_evidence_paths', {}), ensure_ascii=False)}`",
            "",
            "## Safety Notes",
            "",
            "- 该模块仍是本地 dry-run/simulation，不调用网站后台或 CMS helper。",
            "- 只有 `execution_allowed_for_future_executor=true` 时，后续真实执行器才可以进入独立的、明确授权的实施步骤。",
            "- 即使 mode 传入 `live`，本模块也不会发布；live 只用于验证上线前证据是否齐全。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, result: ApprovedExecutorResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    record_path = data_dir / APPROVED_RECORD_JSON_NAME
    report_path = reports_dir / f"{today}-publish-approved-executor-dry-run.md"
    result.artifacts.update({"execution_record": str(record_path), "dry_run_report": str(report_path)})
    write_text(
        record_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "mode": result.mode,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "execution_record": result.execution_record,
                "artifacts": result.artifacts,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return record_path, report_path


def run_publish_approved_executor(
    root: Path,
    *,
    bundle_path: str = "",
    mode: str = "dry-run",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    backup_path: str = "",
    changelog_path: str = "",
    rollback_plan_path: str = "",
    confirm_live: bool = False,
    allowed_target_urls: list[str] | None = None,
) -> tuple[ApprovedExecutorResult, tuple[Path, Path]]:
    root = root.resolve()
    bundle_file = resolve_path(root, bundle_path) if bundle_path else root / "seo-workspace" / "data" / "publish-execution-bundle.json"
    bundle_payload = read_json(bundle_file)
    normalized_allowed_urls = [url.rstrip("/") for url in (allowed_target_urls or []) if url]
    blockers, warnings, evidence_paths = evaluate_approved_executor_gates(
        root=root,
        bundle_payload=bundle_payload,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        backup_path=backup_path,
        changelog_path=changelog_path,
        rollback_plan_path=rollback_plan_path,
        confirm_live=confirm_live,
        allowed_target_urls=normalized_allowed_urls,
    )
    record = build_execution_record(
        bundle_payload=bundle_payload,
        mode=mode,
        blockers=blockers,
        warnings=warnings,
        evidence_paths=evidence_paths,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        confirm_live=confirm_live,
        allowed_target_urls=normalized_allowed_urls,
    )
    status = str(record.get("status", "blocked_before_approved_execution"))
    result = ApprovedExecutorResult(
        status=status,
        mode=mode,
        blockers=blockers,
        warnings=warnings,
        execution_record=record,
    )
    artifacts = write_outputs(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate a gated owner-approved publish executor without executing writes.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--bundle-path", default="")
    parser.add_argument("--mode", default="dry-run", choices=sorted(VALID_MODES))
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--backup-path", default="")
    parser.add_argument("--changelog-path", default="")
    parser.add_argument("--rollback-plan-path", default="")
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--allowed-target-url", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_approved_executor(
        Path(args.root),
        bundle_path=args.bundle_path,
        mode=args.mode,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        backup_path=args.backup_path,
        changelog_path=args.changelog_path,
        rollback_plan_path=args.rollback_plan_path,
        confirm_live=args.confirm_live,
        allowed_target_urls=args.allowed_target_url,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
