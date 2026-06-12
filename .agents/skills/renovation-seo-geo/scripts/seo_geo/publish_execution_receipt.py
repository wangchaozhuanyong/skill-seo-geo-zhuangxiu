#!/usr/bin/env python3
"""Verify a no-write receipt for a future publish execution result."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


RECEIPT_JSON_NAME = "publish-execution-receipt.json"
RECEIPT_REPORT_NAME = "publish-execution-receipt.md"
RESULT_JSON_NAME = "publish-execution-result.json"
RESULT_EXAMPLE_NAME = "publish-execution-result.example.json"
DEFAULT_OPERATOR_JSON_NAME = "publish-operator-command.json"
EXPECTED_OPERATOR_STATUS = "operator_command_ready_for_future_execution"
EXPECTED_OPERATOR_ACTION = "publish_operator_command_package_only_no_write"
EXPECTED_RESULT_STATUS = "publish_execution_completed"
EXPECTED_RESULT_ACTION = "publish_execution_result_record"
RECEIPT_ACTION = "publish_execution_receipt_verification_only_no_execute"
REQUIRED_RESULT_FLAGS = (
    "backup_completed_before_write",
    "cms_write_completed",
    "cms_write_result_recorded",
    "seo_assets_regenerated_after_write",
    "qa_passed_after_write",
    "rollback_evidence_retained",
)


@dataclass
class PublishExecutionReceiptResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    receipt: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_json(path: Path) -> dict[str, Any]:
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


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def bool_value(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"true", "yes", "1"}


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def find_media_placeholders(value: object) -> list[str]:
    serialized = json.dumps(value, ensure_ascii=False)
    pattern = re.compile(r"NEEDS_MEDIA_UPLOAD:[^\"'\s<>]+")
    return sorted(set(pattern.findall(serialized)))


def example_result(operator_payload: dict[str, Any]) -> dict[str, Any]:
    package = safe_dict(operator_payload.get("operator_package"))
    helper_call = safe_dict(package.get("admin_helper_call"))
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": EXPECTED_RESULT_ACTION,
        "status": "example_only_not_executed",
        "target_url": package.get("target_url", "https://example.com/en/services/kitchen"),
        "paired_url": package.get("paired_url", "https://example.com/zh/services/kitchen"),
        "admin_helper": helper_call.get("function") or package.get("admin_helper", "saveAdminService"),
        "publish_status": "draft",
        "cms_record_id": "NEEDS_REAL_EXECUTION_RESULT",
        "executed_operator_package_path": "seo-workspace/data/publish-operator-command.json",
        "executed_helper_call_path": "seo-workspace/data/publish-admin-helper-call.json",
        "backup_completed_before_write": False,
        "cms_write_completed": False,
        "cms_write_result_recorded": False,
        "seo_assets_regenerated_after_write": False,
        "qa_passed_after_write": False,
        "rollback_evidence_retained": False,
        "explicit_publish_status_approval": False,
        "live_url_verified": False,
        "command_results": [
            {"command": "npm run backup:supabase", "exit_code": None, "completed": False},
            {"command": "admin helper call", "exit_code": None, "completed": False},
            {"command": "npm run generate:sitemap", "exit_code": None, "completed": False},
            {"command": "python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url <target>", "exit_code": None, "completed": False},
        ],
        "notes": "Copy this example to seo-workspace/data/publish-execution-result.json only after an explicitly approved execution has actually completed.",
    }


def evaluate_receipt_inputs(
    *,
    operator_payload: dict[str, Any],
    result_payload: dict[str, Any],
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    package = safe_dict(operator_payload.get("operator_package"))
    helper_call = safe_dict(package.get("admin_helper_call"))

    if not operator_payload:
        blockers.append("Missing publish-operator-command.json. Run publish-operator-package first.")
    elif str_value(operator_payload.get("status")) != EXPECTED_OPERATOR_STATUS:
        blockers.append(
            f"Operator package top-level status is not {EXPECTED_OPERATOR_STATUS}: "
            f"{operator_payload.get('status', 'missing')}."
        )
    if not package:
        blockers.append("Operator payload has no operator_package object.")
    elif str_value(package.get("status")) != EXPECTED_OPERATOR_STATUS:
        blockers.append(f"Operator package object is not ready: {package.get('status', 'missing')}.")
    if str_value(package.get("action")) != EXPECTED_OPERATOR_ACTION:
        blockers.append("Operator package action is not the expected no-write command package action.")
    if package.get("operator_allowed_for_future_executor") is not True:
        blockers.append("Operator package does not allow future executor use.")

    for blocker in safe_list(operator_payload.get("blockers")):
        blockers.append(f"Operator package blocker: {blocker}")
    for blocker in safe_list(package.get("blockers")):
        blockers.append(f"Operator package blocker: {blocker}")
    for warning in safe_list(operator_payload.get("warnings")) + safe_list(package.get("warnings")):
        warnings.append(f"Operator package warning: {warning}")

    if not result_payload:
        blockers.append("Missing publish-execution-result.json. Record the actual approved execution result before verifying receipt.")
    else:
        if str_value(result_payload.get("status")) != EXPECTED_RESULT_STATUS:
            blockers.append(f"Publish execution result status is not {EXPECTED_RESULT_STATUS}: {result_payload.get('status', 'missing')}.")
        if str_value(result_payload.get("action")) != EXPECTED_RESULT_ACTION:
            blockers.append("Publish execution result action is not publish_execution_result_record.")

    target_url = str_value(package.get("target_url"))
    paired_url = str_value(package.get("paired_url"))
    result_target = str_value(result_payload.get("target_url"))
    result_pair = str_value(result_payload.get("paired_url"))
    if target_url and result_target and target_url.rstrip("/") != result_target.rstrip("/"):
        blockers.append("Publish execution result target_url does not match operator package target_url.")
    if paired_url and result_pair and paired_url.rstrip("/") != result_pair.rstrip("/"):
        blockers.append("Publish execution result paired_url does not match operator package paired_url.")

    expected_helper = str_value(helper_call.get("function") or package.get("admin_helper"))
    actual_helper = str_value(result_payload.get("admin_helper") or result_payload.get("helper_function"))
    if expected_helper and actual_helper and expected_helper != actual_helper:
        blockers.append("Publish execution result admin_helper does not match operator package helper function.")

    if result_payload:
        for flag in REQUIRED_RESULT_FLAGS:
            if not bool_value(result_payload.get(flag)):
                blockers.append(f"Publish execution result required flag missing or false: {flag}.")

        if not str_value(result_payload.get("cms_record_id")):
            blockers.append("Publish execution result cms_record_id is missing.")
        if not str_value(result_payload.get("executed_operator_package_path")):
            blockers.append("Publish execution result executed_operator_package_path is missing.")
        if not str_value(result_payload.get("executed_helper_call_path")):
            blockers.append("Publish execution result executed_helper_call_path is missing.")

        publish_status = str_value(result_payload.get("publish_status"), "draft")
        if publish_status not in {"draft", "published"}:
            blockers.append("Publish execution result publish_status must be draft or published.")
        if publish_status == "published":
            if not bool_value(result_payload.get("explicit_publish_status_approval")):
                blockers.append("Published status requires explicit_publish_status_approval=true.")
            if not bool_value(result_payload.get("live_url_verified")):
                blockers.append("Published status requires live_url_verified=true.")
        elif bool_value(result_payload.get("live_url_verified")):
            warnings.append("live_url_verified=true but publish_status is not published; verify the receipt scope.")

        command_results = safe_list(result_payload.get("command_results"))
        for command in command_results:
            if isinstance(command, dict) and command.get("completed") is False:
                blockers.append(f"Publish execution command not completed: {command.get('command', 'unknown command')}.")
            if isinstance(command, dict) and command.get("exit_code") not in {0, "0", None}:
                blockers.append(f"Publish execution command failed: {command.get('command', 'unknown command')}.")

    if find_media_placeholders(operator_payload) or find_media_placeholders(result_payload):
        blockers.append("Media placeholders remain in operator/result payload; receipt cannot be verified.")
    return unique_strings(blockers), unique_strings(warnings)


def build_receipt(
    *,
    operator_payload: dict[str, Any],
    result_payload: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
    operator_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    package = safe_dict(operator_payload.get("operator_package"))
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": RECEIPT_ACTION,
        "status": "publish_execution_receipt_verified" if not blockers else "blocked_before_publish_execution_receipt",
        "receipt_verified_for_post_publish_qa": not blockers,
        "operator_package_path": str(operator_path),
        "execution_result_path": str(result_path),
        "target_url": package.get("target_url", result_payload.get("target_url", "")),
        "paired_url": package.get("paired_url", result_payload.get("paired_url", "")),
        "admin_helper": safe_dict(package.get("admin_helper_call")).get("function") or package.get("admin_helper", ""),
        "publish_status": result_payload.get("publish_status", ""),
        "cms_record_id": result_payload.get("cms_record_id", ""),
        "result_flags": {flag: bool_value(result_payload.get(flag)) for flag in REQUIRED_RESULT_FLAGS},
        "command_results": safe_list(result_payload.get("command_results")),
        "blockers": blockers,
        "warnings": warnings,
        "no_commands_executed_by_receipt_verifier": True,
        "no_cms_write_executed_by_receipt_verifier": True,
        "no_source_page_write_executed_by_receipt_verifier": True,
        "no_media_upload_executed_by_receipt_verifier": True,
        "no_publish_executed_by_receipt_verifier": True,
        "no_deploy_executed_by_receipt_verifier": True,
        "no_live_actions_executed_by_receipt_verifier": True,
        "safety_note": "This receipt verifier reads local artifacts only. It does not run commands, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.",
    }


def render_report(result: PublishExecutionReceiptResult) -> str:
    receipt = result.receipt
    lines = [
        "# Publish Execution Receipt",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{receipt.get('target_url', 'N/A')}`",
        f"- Paired URL: `{receipt.get('paired_url', 'N/A')}`",
        f"- Admin helper: `{receipt.get('admin_helper', 'N/A')}`",
        f"- Publish status: `{receipt.get('publish_status', 'N/A')}`",
        "- 执行状态: receipt verification only；未运行命令、未调用 CMS、未改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天新增发布执行回执验证层：未来只有真实 approved execution 写入完成，并提供 CMS 记录、备份、SEO 生成、QA 和回滚证据后，才允许把发布结果标记为已验证。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Result Flags", ""])
    flags = safe_dict(receipt.get("result_flags"))
    lines.extend(f"- {key}: `{value}`" for key, value in flags.items()) if flags else lines.append("- None")
    lines.extend(["", "## Command Results", ""])
    commands = safe_list(receipt.get("command_results"))
    if commands:
        for command in commands:
            if isinstance(command, dict):
                lines.append(f"- `{command.get('command', '')}`: completed=`{command.get('completed', '')}`, exit_code=`{command.get('exit_code', '')}`")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 本模块不会执行发布，只验证未来执行器或人工 operator 留下的执行结果。",
            "- 没有真实 `publish-execution-result.json` 时，不允许声称页面已经发布或写入完成。",
            "- 若 publish_status 为 `published`，必须同时提供明确发布状态批准和 live URL 验证。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, result: PublishExecutionReceiptResult, *, example_payload: dict[str, Any], write_example: bool) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    config_dir = root / "seo-workspace" / "config"
    today = dt.date.today().isoformat()
    receipt_path = data_dir / RECEIPT_JSON_NAME
    report_path = reports_dir / f"{today}-{RECEIPT_REPORT_NAME}"
    result.artifacts.update({"receipt_json": str(receipt_path), "report": str(report_path)})
    if write_example:
        example_path = config_dir / RESULT_EXAMPLE_NAME
        result.artifacts["execution_result_example"] = str(example_path)
        write_text(example_path, json.dumps(example_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(
        receipt_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "receipt": result.receipt,
                "artifacts": result.artifacts,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return receipt_path, report_path


def run_publish_execution_receipt(
    root: Path,
    *,
    operator_path: str = "",
    execution_result_path: str = "",
    write_example: bool = True,
) -> tuple[PublishExecutionReceiptResult, tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    operator_file = resolve_path(root, operator_path) if operator_path else data_dir / DEFAULT_OPERATOR_JSON_NAME
    result_file = resolve_path(root, execution_result_path) if execution_result_path else data_dir / RESULT_JSON_NAME
    operator_payload = read_json(operator_file)
    result_payload = read_json(result_file)
    blockers, warnings = evaluate_receipt_inputs(operator_payload=operator_payload, result_payload=result_payload)
    receipt = build_receipt(
        operator_payload=operator_payload,
        result_payload=result_payload,
        blockers=blockers,
        warnings=warnings,
        operator_path=operator_file,
        result_path=result_file,
    )
    status = str_value(receipt.get("status"), "blocked_before_publish_execution_receipt")
    result = PublishExecutionReceiptResult(status=status, blockers=blockers, warnings=warnings, receipt=receipt)
    artifacts = write_outputs(root, result, example_payload=example_result(operator_payload), write_example=write_example)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify publish execution receipt artifacts without executing writes.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--operator-path", default="")
    parser.add_argument("--execution-result-path", default="")
    parser.add_argument("--no-write-example", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_execution_receipt(
        Path(args.root),
        operator_path=args.operator_path,
        execution_result_path=args.execution_result_path,
        write_example=not args.no_write_example,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
