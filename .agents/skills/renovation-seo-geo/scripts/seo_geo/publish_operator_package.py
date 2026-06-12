#!/usr/bin/env python3
"""Create a no-write operator command package from an implementation package."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


OPERATOR_PACKAGE_JSON_NAME = "publish-operator-command.json"
OPERATOR_REPORT_NAME = "publish-operator-command.md"
DEFAULT_IMPLEMENTATION_JSON_NAME = "publish-implementation-package.json"
DEFAULT_HELPER_CALL_JSON_NAME = "publish-admin-helper-call.json"
EXPECTED_IMPLEMENTATION_STATUS = "implementation_package_ready_for_future_executor"
EXPECTED_IMPLEMENTATION_ACTION = "implementation_package_only_no_write"
EXPECTED_ADAPTER_STATUS = "website_publish_adapter_ready"
OPERATOR_ACTION = "publish_operator_command_package_only_no_write"
SAFETY_FLAGS = (
    "no_cms_write_executed",
    "no_source_page_write_executed",
    "no_media_upload_executed",
    "no_publish_executed",
    "no_deploy_executed",
    "no_live_actions_executed",
)


@dataclass
class PublishOperatorPackageResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    operator_package: dict[str, object] = field(default_factory=dict)
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


def string_list(value: object) -> list[str]:
    return [str(item) for item in safe_list(value) if str(item).strip()]


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


def evaluate_operator_inputs(
    *,
    implementation_payload: dict[str, object],
    helper_payload: dict[str, object],
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    package = safe_dict(implementation_payload.get("package"))

    if not implementation_payload:
        blockers.append("Missing publish-implementation-package.json. Run publish-implementation-package first.")
    elif str(implementation_payload.get("status", "")) != EXPECTED_IMPLEMENTATION_STATUS:
        blockers.append(
            f"Implementation package top-level status is not {EXPECTED_IMPLEMENTATION_STATUS}: "
            f"{implementation_payload.get('status', 'missing')}."
        )

    if not package:
        blockers.append("Implementation payload has no package object.")
    elif str(package.get("status", "")) != EXPECTED_IMPLEMENTATION_STATUS:
        blockers.append(f"Implementation package object is not ready: {package.get('status', 'missing')}.")

    if str(package.get("action", "")) != EXPECTED_IMPLEMENTATION_ACTION:
        blockers.append("Implementation package action is not the expected no-write implementation action.")
    if package.get("implementation_allowed_for_future_executor") is not True:
        blockers.append("Implementation package does not allow future executor use.")

    for blocker in safe_list(implementation_payload.get("blockers")):
        blockers.append(f"Implementation package blocker: {blocker}")
    for warning in safe_list(implementation_payload.get("warnings")):
        warnings.append(f"Implementation package warning: {warning}")
    for blocker in safe_list(package.get("blockers")):
        blockers.append(f"Implementation package blocker: {blocker}")
    for warning in safe_list(package.get("warnings")):
        warnings.append(f"Implementation package warning: {warning}")

    helper_call = safe_dict(package.get("admin_helper_call"))
    if not helper_call:
        blockers.append("Implementation package has no admin_helper_call.")
    elif not helper_call.get("function"):
        blockers.append("Implementation admin_helper_call has no function.")

    if not helper_payload:
        blockers.append("Missing publish-admin-helper-call.json. Run publish-implementation-package first.")
    elif helper_payload.get("function") != helper_call.get("function"):
        blockers.append("publish-admin-helper-call.json function does not match implementation package admin_helper_call.")

    if not package.get("target_url"):
        blockers.append("Implementation package target_url is missing.")
    if not package.get("paired_url"):
        blockers.append("Implementation package paired_url is missing; bilingual execution scope is incomplete.")
    if str(package.get("website_adapter_status", "")) != EXPECTED_ADAPTER_STATUS:
        blockers.append(
            f"Website publish adapter is required for operator command package: "
            f"{package.get('website_adapter_status', 'missing')}."
        )

    if not string_list(package.get("backup_commands")):
        blockers.append("No backup command found in implementation package.")
    if not string_list(package.get("seo_generation_commands")):
        blockers.append("No SEO generation command found in implementation package.")
    if not string_list(package.get("qa_commands")):
        blockers.append("No QA command found in implementation package.")

    for flag in SAFETY_FLAGS:
        if package.get(flag) is not True:
            blockers.append(f"Implementation package safety flag missing or false: {flag}.")

    if find_media_placeholders(implementation_payload) or find_media_placeholders(helper_payload):
        blockers.append("Media placeholders remain in implementation/helper payload; operator package cannot be used.")
    return unique_strings(blockers), unique_strings(warnings)


def build_operator_package(
    *,
    implementation_payload: dict[str, object],
    helper_payload: dict[str, object],
    blockers: list[str],
    warnings: list[str],
    implementation_path: Path,
    helper_call_path: Path,
) -> dict[str, object]:
    package = safe_dict(implementation_payload.get("package"))
    website_evidence = safe_dict(package.get("website_evidence"))
    admin_helper_call = safe_dict(package.get("admin_helper_call"))
    command_groups = {
        "pre_execution": string_list(package.get("backup_commands")),
        "cms_write": [
            {
                "type": "admin_helper_call",
                "function": admin_helper_call.get("function", ""),
                "source_artifact": str(helper_call_path),
                "input": safe_dict(admin_helper_call.get("input")),
            }
        ],
        "post_write_seo": string_list(package.get("seo_generation_commands")),
        "qa": string_list(package.get("qa_commands")),
        "build": string_list(package.get("build_commands")),
        "rollback": string_list(package.get("rollback_plan")),
    }
    website_root = str(website_evidence.get("website_root", "") or "")
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": OPERATOR_ACTION,
        "status": "operator_command_ready_for_future_execution" if not blockers else "blocked_before_operator_command",
        "operator_allowed_for_future_executor": not blockers,
        "implementation_package_path": str(implementation_path),
        "helper_call_path": str(helper_call_path),
        "target_url": package.get("target_url", ""),
        "paired_url": package.get("paired_url", ""),
        "table": package.get("table", ""),
        "admin_helper": package.get("admin_helper", ""),
        "cms_payload_path": package.get("cms_payload_path", ""),
        "cms_payload_selection": package.get("cms_payload_selection", ""),
        "payload_keys": safe_list(package.get("payload_keys")),
        "latest_research_sources": safe_list(package.get("latest_research_sources")),
        "website_root": website_root,
        "package_manager": website_evidence.get("package_manager", ""),
        "node_engine": website_evidence.get("node_engine", ""),
        "website_adapter_status": package.get("website_adapter_status", "missing"),
        "website_adapter_contract": safe_dict(package.get("website_adapter_contract")),
        "admin_helper_call": admin_helper_call or helper_payload,
        "command_groups": command_groups,
        "dry_run_command_preview": [
            "verify owner-approved execution record and current implementation package",
            *(f"cd {website_root} && {command}" if website_root else command for command in command_groups["pre_execution"]),
            f"call {admin_helper_call.get('function', 'admin helper')} with {helper_call_path}",
            *(f"cd {website_root} && {command}" if website_root else command for command in command_groups["post_write_seo"]),
            *(f"cd {website_root} && {command}" if website_root else command for command in command_groups["qa"]),
            *(f"cd {website_root} && {command}" if website_root else command for command in command_groups["build"]),
        ],
        "required_operator_confirmations": {
            "owner_approved_specific_implementation_package": False,
            "explicit_execution_instruction": False,
            "backup_completed_before_write": False,
            "cms_write_result_recorded": False,
            "seo_assets_regenerated_after_write": False,
            "qa_passed_after_write": False,
            "rollback_evidence_retained": False,
        },
        "blockers": blockers,
        "warnings": warnings,
        "no_commands_executed": True,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "safety_note": "This operator package is a deterministic command manifest only. It does not run npm, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.",
    }


def render_report(result: PublishOperatorPackageResult) -> str:
    package = result.operator_package
    command_groups = safe_dict(package.get("command_groups"))
    helper_call = safe_dict(package.get("admin_helper_call"))
    lines = [
        "# Publish Operator Command Package",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{package.get('target_url', 'N/A')}`",
        f"- Paired URL: `{package.get('paired_url', 'N/A')}`",
        f"- Admin helper: `{helper_call.get('function', package.get('admin_helper', 'N/A'))}`",
        f"- Website adapter status: `{package.get('website_adapter_status', 'missing')}`",
        "- 执行状态: operator command package only；未运行命令、未调用 CMS、未改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把 implementation package 进一步封装成未来执行器可读取的操作命令包：包含备份、CMS helper call、SEO 生成、QA、build 和 rollback 的确定性顺序，但仍停在 no-write 审核状态。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Command Groups", ""])
    for name in ("pre_execution", "cms_write", "post_write_seo", "qa", "build", "rollback"):
        items = safe_list(command_groups.get(name))
        lines.append(f"### {name}")
        if not items:
            lines.append("- None")
        else:
            for item in items:
                if isinstance(item, dict):
                    lines.append(f"- `{item.get('type', 'step')}`: `{item.get('function', '')}` from `{item.get('source_artifact', '')}`")
                else:
                    lines.append(f"- `{item}`")
        lines.append("")
    confirmations = safe_dict(package.get("required_operator_confirmations"))
    lines.extend(["## Required Operator Confirmations", ""])
    lines.extend(f"- {key}: `{value}`" for key, value in confirmations.items()) if confirmations else lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 该文件不是执行结果，只是未来执行器/人工 operator 的命令清单。",
            "- 若存在 blockers，不允许调用 CMS/admin helper。",
            "- 即使本包 ready，真实执行仍需要业主再次明确指定执行该 implementation package。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, result: PublishOperatorPackageResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    package_path = data_dir / OPERATOR_PACKAGE_JSON_NAME
    report_path = reports_dir / f"{today}-{OPERATOR_REPORT_NAME}"
    result.artifacts.update({"operator_package": str(package_path), "report": str(report_path)})
    write_text(
        package_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "operator_package": result.operator_package,
                "artifacts": result.artifacts,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return package_path, report_path


def run_publish_operator_package(
    root: Path,
    *,
    implementation_path: str = "",
    helper_call_path: str = "",
) -> tuple[PublishOperatorPackageResult, tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    implementation_file = resolve_path(root, implementation_path) if implementation_path else data_dir / DEFAULT_IMPLEMENTATION_JSON_NAME
    helper_file = resolve_path(root, helper_call_path) if helper_call_path else data_dir / DEFAULT_HELPER_CALL_JSON_NAME
    implementation_payload = read_json(implementation_file)
    helper_payload = read_json(helper_file)
    blockers, warnings = evaluate_operator_inputs(implementation_payload=implementation_payload, helper_payload=helper_payload)
    operator_package = build_operator_package(
        implementation_payload=implementation_payload,
        helper_payload=helper_payload,
        blockers=blockers,
        warnings=warnings,
        implementation_path=implementation_file,
        helper_call_path=helper_file,
    )
    status = str(operator_package.get("status", "blocked_before_operator_command"))
    result = PublishOperatorPackageResult(status=status, blockers=blockers, warnings=warnings, operator_package=operator_package)
    artifacts = write_outputs(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a no-write publish operator command package.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--implementation-path", default="")
    parser.add_argument("--helper-call-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_operator_package(
        Path(args.root),
        implementation_path=args.implementation_path,
        helper_call_path=args.helper_call_path,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
