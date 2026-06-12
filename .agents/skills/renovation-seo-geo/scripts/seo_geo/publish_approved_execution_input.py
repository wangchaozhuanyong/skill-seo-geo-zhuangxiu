#!/usr/bin/env python3
"""Create guarded future-execution inputs from the operator command package."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


INPUT_JSON_NAME = "publish-approved-execution-input.json"
RESULT_TEMPLATE_NAME = "publish-execution-result.template.json"
RUNNER_NAME = "publish-approved-execution-runner.mjs"
REPORT_NAME = "publish-approved-execution-input.md"
DEFAULT_OPERATOR_JSON_NAME = "publish-operator-command.json"
DEFAULT_HELPER_CALL_JSON_NAME = "publish-admin-helper-call.json"
DEFAULT_ADAPTER_JSON_NAME = "website-publish-adapter.json"
EXPECTED_OPERATOR_STATUS = "operator_command_ready_for_future_execution"
EXPECTED_OPERATOR_ACTION = "publish_operator_command_package_only_no_write"
EXECUTION_INPUT_ACTION = "publish_approved_execution_input_template_only_no_execute"
SAFETY_FLAGS = (
    "no_commands_executed",
    "no_cms_write_executed",
    "no_source_page_write_executed",
    "no_media_upload_executed",
    "no_publish_executed",
    "no_deploy_executed",
    "no_live_actions_executed",
)


@dataclass
class PublishApprovedExecutionInputResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_input: dict[str, Any] = field(default_factory=dict)
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


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            output.append(text)
            seen.add(text)
    return output


def find_helper_export(adapter_payload: dict[str, Any], helper_name: str) -> dict[str, Any]:
    adapter = safe_dict(adapter_payload.get("adapter"))
    for raw in safe_list(adapter.get("helpers")):
        item = safe_dict(raw)
        if item.get("helper") == helper_name and item.get("kind") == "export":
            return item
    for raw in safe_list(adapter.get("helpers")):
        item = safe_dict(raw)
        if item.get("helper") == helper_name:
            return item
    return {}


def find_media_placeholders(value: object) -> list[str]:
    serialized = json.dumps(value, ensure_ascii=False)
    return sorted(set(re.findall(r"NEEDS_MEDIA_UPLOAD:[^\"'\s<>]+", serialized)))


def evaluate_inputs(
    *,
    operator_payload: dict[str, Any],
    helper_payload: dict[str, Any],
    adapter_payload: dict[str, Any],
    allow_blocked_operator: bool,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    package = safe_dict(operator_payload.get("operator_package"))
    adapter = safe_dict(adapter_payload.get("adapter"))
    helper_call = safe_dict(package.get("admin_helper_call")) or helper_payload
    helper_name = str(helper_call.get("function", "") or package.get("admin_helper", "")).strip()

    if not operator_payload:
        blockers.append("Missing publish-operator-command.json. Run publish-operator-package first.")
    elif operator_payload.get("status") != EXPECTED_OPERATOR_STATUS:
        message = f"Operator package top-level status is not {EXPECTED_OPERATOR_STATUS}: {operator_payload.get('status', 'missing')}."
        if allow_blocked_operator:
            warnings.append(message)
        else:
            blockers.append(message)
    if package.get("action") != EXPECTED_OPERATOR_ACTION:
        blockers.append("Operator package action is not publish_operator_command_package_only_no_write.")
    if package.get("operator_allowed_for_future_executor") is not True:
        message = "Operator package does not allow future executor use."
        if allow_blocked_operator:
            warnings.append(message)
        else:
            blockers.append(message)
    for blocker in safe_list(operator_payload.get("blockers")) + safe_list(package.get("blockers")):
        message = f"Operator package blocker: {blocker}"
        if allow_blocked_operator:
            warnings.append(message)
        else:
            blockers.append(message)
    for warning in safe_list(operator_payload.get("warnings")) + safe_list(package.get("warnings")):
        warnings.append(f"Operator package warning: {warning}")

    if not helper_payload:
        blockers.append("Missing publish-admin-helper-call.json. Run publish-implementation-package first.")
    if not helper_name:
        blockers.append("Admin helper function is missing.")
    if helper_name and not find_helper_export(adapter_payload, helper_name):
        warnings.append(f"No exported helper evidence found in website adapter for {helper_name}; runner remains a guarded template.")
    if not adapter_payload:
        blockers.append("Missing website-publish-adapter.json. Run website-publish-adapter first.")
    elif adapter_payload.get("status") != "website_publish_adapter_ready":
        warnings.append(f"Website adapter is not ready: {adapter_payload.get('status', 'missing')}.")
    if not adapter.get("website_root"):
        blockers.append("Website root is missing from adapter evidence.")
    if find_media_placeholders(operator_payload) or find_media_placeholders(helper_payload):
        blockers.append("Media placeholders remain in operator/helper payload; do not create executable input.")
    for flag in SAFETY_FLAGS:
        if package.get(flag) is not True:
            warnings.append(f"Operator package safety flag missing or false: {flag}.")
    return unique_strings(blockers), unique_strings(warnings)


def build_execution_result_template(execution_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": "publish_execution_result_record",
        "status": "example_only_not_executed",
        "target_url": execution_input.get("target_url", ""),
        "paired_url": execution_input.get("paired_url", ""),
        "admin_helper": execution_input.get("admin_helper", ""),
        "publish_status": "draft",
        "cms_record_id": "NEEDS_REAL_EXECUTION_RESULT",
        "executed_operator_package_path": execution_input.get("operator_package_path", ""),
        "executed_helper_call_path": execution_input.get("helper_call_path", ""),
        "backup_completed_before_write": False,
        "cms_write_completed": False,
        "cms_write_result_recorded": False,
        "seo_assets_regenerated_after_write": False,
        "qa_passed_after_write": False,
        "rollback_evidence_retained": False,
        "explicit_publish_status_approval": False,
        "live_url_verified": False,
        "command_results": [
            {"phase": "backup", "command": command, "completed": False, "exit_code": None}
            for command in safe_list(execution_input.get("backup_commands"))
        ]
        + [{"phase": "cms_write", "command": f"call {execution_input.get('admin_helper', 'admin helper')}", "completed": False, "exit_code": None}]
        + [
            {"phase": "seo_generation", "command": command, "completed": False, "exit_code": None}
            for command in safe_list(execution_input.get("seo_generation_commands"))
        ]
        + [{"phase": "qa", "command": command, "completed": False, "exit_code": None} for command in safe_list(execution_input.get("qa_commands"))],
        "notes": "Copy to seo-workspace/data/publish-execution-result.json only after explicit owner-approved execution has actually completed.",
    }


def render_runner(execution_input: dict[str, Any]) -> str:
    helper_export = safe_dict(execution_input.get("helper_export"))
    helper_path = str(helper_export.get("path", ""))
    helper_name = str(execution_input.get("admin_helper", "admin helper"))
    return f"""#!/usr/bin/env node
/**
 * Guarded template for a future approved Flash Cast CMS write.
 *
 * This file is generated for review only. It refuses to run unless the operator
 * explicitly sets FLASHCAST_APPROVED_PUBLISH_RUN=I_UNDERSTAND_THIS_WRITES_CMS.
 * Codex must not run this unattended.
 */

import fs from "node:fs";

const REQUIRED_CONFIRMATION = "I_UNDERSTAND_THIS_WRITES_CMS";
if (process.env.FLASHCAST_APPROVED_PUBLISH_RUN !== REQUIRED_CONFIRMATION) {{
  console.error("Blocked: set FLASHCAST_APPROVED_PUBLISH_RUN=" + REQUIRED_CONFIRMATION + " only after explicit owner approval.");
  process.exit(1);
}}

const executionInputPath = process.argv[2] || "seo-workspace/data/publish-approved-execution-input.json";
const executionInput = JSON.parse(fs.readFileSync(executionInputPath, "utf8"));

if (executionInput.no_cms_write_executed !== true || executionInput.action !== "{EXECUTION_INPUT_ACTION}") {{
  throw new Error("Unexpected execution input safety/action fields.");
}}

console.log("Future CMS helper:", {json.dumps(helper_name)});
console.log("Helper export evidence:", {json.dumps(helper_path)});
console.log("Helper call payload path:", executionInput.helper_call_path);
console.log("Target URL:", executionInput.target_url);
console.log("Paired URL:", executionInput.paired_url);

// Implementation note:
// Import the helper from the website source after owner approval, then call it
// with executionInput.admin_helper_call.input. The exact import is intentionally
// left for the approved executor because TypeScript path aliases and runtime
// bootstrapping must match the website repo environment.
//
// Suggested helper: {helper_name}
// Source evidence: {helper_path or "not found in adapter"}
//
// After a real write, create seo-workspace/data/publish-execution-result.json
// from publish-execution-result.template.json and run publish-execution-receipt.
"""


def render_report(result: PublishApprovedExecutionInputResult) -> str:
    execution_input = result.execution_input
    lines = [
        "# Publish Approved Execution Input",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{execution_input.get('target_url', 'N/A')}`",
        f"- Paired URL: `{execution_input.get('paired_url', 'N/A')}`",
        f"- Admin helper: `{execution_input.get('admin_helper', 'N/A')}`",
        "- 执行状态: execution-input-template-only；未运行 runner、未调用 CMS、未改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把 operator command package 转成未来真实执行器可读取的输入文件、受保护 runner 模板和执行结果模板。这样批准后的发布步骤更确定，但当前仍不执行任何写入。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Runner Guard", ""])
    lines.extend(
        [
            "- Runner 默认拒绝执行。",
            "- 只有显式设置 `FLASHCAST_APPROVED_PUBLISH_RUN=I_UNDERSTAND_THIS_WRITES_CMS` 才会进入模板逻辑。",
            "- 本轮没有运行 runner，也没有写 CMS。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def run_publish_approved_execution_input(
    root: Path,
    *,
    operator_path: str = "",
    helper_call_path: str = "",
    adapter_path: str = "",
    allow_blocked_operator: bool = False,
) -> tuple[PublishApprovedExecutionInputResult, tuple[Path, Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    tools_dir = root / "seo-workspace" / "tools"
    reports_dir = root / "seo-workspace" / "reports"
    operator_file = resolve_path(root, operator_path or f"seo-workspace/data/{DEFAULT_OPERATOR_JSON_NAME}")
    helper_file = resolve_path(root, helper_call_path or f"seo-workspace/data/{DEFAULT_HELPER_CALL_JSON_NAME}")
    adapter_file = resolve_path(root, adapter_path or f"seo-workspace/data/{DEFAULT_ADAPTER_JSON_NAME}")

    operator_payload = read_json(operator_file)
    helper_payload = read_json(helper_file)
    adapter_payload = read_json(adapter_file)
    blockers, warnings = evaluate_inputs(
        operator_payload=operator_payload,
        helper_payload=helper_payload,
        adapter_payload=adapter_payload,
        allow_blocked_operator=allow_blocked_operator,
    )
    package = safe_dict(operator_payload.get("operator_package"))
    helper_call = safe_dict(package.get("admin_helper_call")) or helper_payload
    helper_name = str(helper_call.get("function", "") or package.get("admin_helper", "")).strip()
    execution_input = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": EXECUTION_INPUT_ACTION,
        "status": "execution_input_template_ready_for_approved_executor" if not blockers else "blocked_before_execution_input_template",
        "operator_package_path": str(operator_file),
        "helper_call_path": str(helper_file),
        "website_adapter_path": str(adapter_file),
        "target_url": package.get("target_url", ""),
        "paired_url": package.get("paired_url", ""),
        "admin_helper": helper_name,
        "admin_helper_call": helper_call,
        "helper_export": find_helper_export(adapter_payload, helper_name),
        "website_root": package.get("website_root") or safe_dict(adapter_payload.get("adapter")).get("website_root", ""),
        "backup_commands": safe_list(safe_dict(package.get("command_groups")).get("pre_execution")),
        "seo_generation_commands": safe_list(safe_dict(package.get("command_groups")).get("post_write_seo")),
        "qa_commands": safe_list(safe_dict(package.get("command_groups")).get("qa")),
        "build_commands": safe_list(safe_dict(package.get("command_groups")).get("build")),
        "blockers": blockers,
        "warnings": warnings,
        "no_runner_executed": True,
        "no_commands_executed": True,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
    }
    status = execution_input["status"]
    result = PublishApprovedExecutionInputResult(status=status, blockers=blockers, warnings=warnings, execution_input=execution_input)
    input_path = data_dir / INPUT_JSON_NAME
    result_template_path = data_dir / RESULT_TEMPLATE_NAME
    runner_path = tools_dir / RUNNER_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    result.artifacts.update(
        {
            "execution_input": str(input_path),
            "execution_result_template": str(result_template_path),
            "runner_template": str(runner_path),
            "report": str(report_path),
        }
    )
    write_text(input_path, json.dumps(execution_input, ensure_ascii=False, indent=2) + "\n")
    write_text(result_template_path, json.dumps(build_execution_result_template(execution_input), ensure_ascii=False, indent=2) + "\n")
    write_text(runner_path, render_runner(execution_input))
    write_text(report_path, render_report(result))
    return result, (input_path, result_template_path, runner_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create guarded future execution input templates; does not execute.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--operator-path", default="")
    parser.add_argument("--helper-call-path", default="")
    parser.add_argument("--adapter-path", default="")
    parser.add_argument("--allow-blocked-operator", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_approved_execution_input(
        Path(args.root),
        operator_path=args.operator_path,
        helper_call_path=args.helper_call_path,
        adapter_path=args.adapter_path,
        allow_blocked_operator=args.allow_blocked_operator,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if result.status == "execution_input_template_ready_for_approved_executor" else 1


if __name__ == "__main__":
    raise SystemExit(main())
