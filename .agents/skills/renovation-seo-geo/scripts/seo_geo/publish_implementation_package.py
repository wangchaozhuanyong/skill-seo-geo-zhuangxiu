#!/usr/bin/env python3
"""Create a no-write implementation package from an approved execution record."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


IMPLEMENTATION_PACKAGE_JSON_NAME = "publish-implementation-package.json"
HELPER_CALL_JSON_NAME = "publish-admin-helper-call.json"
DEFAULT_ADAPTER_JSON_NAME = "website-publish-adapter.json"
EXPECTED_RECORD_STATUS = "approved_execution_simulation_ready"
EXPECTED_RECORD_ACTION = "approved_execution_simulation_only_no_write"
PACKAGE_ACTION = "implementation_package_only_no_write"
SAFETY_FLAGS = (
    "no_cms_write_executed",
    "no_source_page_write_executed",
    "no_media_upload_executed",
    "no_publish_executed",
    "no_deploy_executed",
    "no_live_actions_executed",
)
SCAN_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py"}


@dataclass
class PublishImplementationPackageResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    package: dict[str, object] = field(default_factory=dict)
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


def iter_source_files(root: Path, *, limit: int = 1200) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    files: list[Path] = []
    ignored_dirs = {"node_modules", ".git", "dist", "build", ".next", "coverage", ".turbo"}
    for current_raw, dirs, names in os.walk(root):
        current = Path(current_raw)
        dirs[:] = [item for item in dirs if item not in ignored_dirs and not item.startswith(".cache")]
        for name in names:
            path = current / name
            if path.suffix in SCAN_EXTENSIONS:
                files.append(path)
                if len(files) >= limit:
                    return files
    return files


def discover_website_evidence(website_root: Path, helper_names: list[str]) -> dict[str, object]:
    evidence: dict[str, object] = {
        "website_root": str(website_root),
        "provided": bool(str(website_root)),
        "exists": website_root.exists() if str(website_root) else False,
        "helper_matches": [],
        "seo_script_matches": [],
        "scanned_file_count": 0,
    }
    if not str(website_root) or not website_root.exists() or not website_root.is_dir():
        return evidence
    files = iter_source_files(website_root)
    evidence["scanned_file_count"] = len(files)
    helper_patterns = [name for name in helper_names if name]
    seo_patterns = ["generate-seo-manifest", "generate-sitemap", "llms", "sitemap.xml", "seo-manifest"]
    helper_matches: list[dict[str, str]] = []
    seo_matches: list[dict[str, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        relative = path.relative_to(website_root).as_posix()
        for pattern in helper_patterns:
            if pattern in text:
                helper_matches.append({"helper": pattern, "path": relative})
        for pattern in seo_patterns:
            if pattern in text or pattern in path.name:
                seo_matches.append({"pattern": pattern, "path": relative})
    evidence["helper_matches"] = helper_matches[:50]
    evidence["seo_script_matches"] = seo_matches[:50]
    return evidence


def empty_website_evidence() -> dict[str, object]:
    return {
        "website_root": "",
        "provided": False,
        "exists": False,
        "helper_matches": [],
        "seo_script_matches": [],
        "scanned_file_count": 0,
    }


def evaluate_package_inputs(
    *,
    record_payload: dict[str, object],
    website_evidence: dict[str, object],
    adapter_payload: dict[str, object],
    website_root_provided: bool,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    record = safe_dict(record_payload.get("execution_record"))

    if not record_payload:
        blockers.append("Missing publish-approved-execution-record.json. Run publish-approved-executor first.")
    elif str(record_payload.get("status", "")) != EXPECTED_RECORD_STATUS:
        blockers.append(
            f"Approved execution record top-level status is not {EXPECTED_RECORD_STATUS}: "
            f"{record_payload.get('status', 'missing')}."
        )
    if not record:
        blockers.append("Approved execution record has no execution_record object.")
    elif str(record.get("status", "")) != EXPECTED_RECORD_STATUS:
        blockers.append(f"Execution record is not ready: {record.get('status', 'missing')}.")
    if str(record.get("action", "")) != EXPECTED_RECORD_ACTION:
        blockers.append("Execution record action is not the expected approved simulation no-write action.")
    if record.get("execution_allowed_for_future_executor") is not True:
        blockers.append("Execution record does not allow future executor implementation.")

    for blocker in safe_list(record_payload.get("blockers")):
        blockers.append(f"Approved execution blocker: {blocker}")
    for warning in safe_list(record_payload.get("warnings")):
        warnings.append(f"Approved execution warning: {warning}")

    helper_call = safe_dict(record.get("simulated_helper_call"))
    if not helper_call:
        blockers.append("Execution record has no simulated_helper_call.")
    elif not helper_call.get("function"):
        blockers.append("Execution record simulated_helper_call has no function.")

    if not record.get("target_url"):
        blockers.append("Execution record target_url is missing.")
    if not record.get("paired_url"):
        warnings.append("Execution record paired_url is missing; bilingual implementation scope may be incomplete.")

    for flag in SAFETY_FLAGS:
        if record.get(flag) is not True:
            blockers.append(f"Execution record safety flag missing or false: {flag}.")

    if find_media_placeholders(record_payload):
        blockers.append("Media placeholders remain in the execution record; implementation package cannot be used.")

    if adapter_payload:
        adapter_status = str(adapter_payload.get("status", ""))
        if adapter_status != "website_publish_adapter_ready":
            blockers.append(f"Website publish adapter is not ready: {adapter_status or 'missing'}.")
        for blocker in safe_list(adapter_payload.get("blockers")):
            blockers.append(f"Website adapter blocker: {blocker}")
        for warning in safe_list(adapter_payload.get("warnings")):
            warnings.append(f"Website adapter warning: {warning}")
    else:
        warnings.append("Missing website-publish-adapter.json; implementation package falls back to direct helper scan only.")

    if website_root_provided:
        if website_evidence.get("exists") is not True:
            blockers.append(f"Website root does not exist: {website_evidence.get('website_root', '')}")
        elif not safe_list(website_evidence.get("helper_matches")):
            warnings.append("No matching admin helper references were found in the provided website root.")
    else:
        warnings.append("No website root supplied; implementation package cannot verify helper source paths.")
    return blockers, warnings


def adapter_object(adapter_payload: dict[str, object]) -> dict[str, object]:
    return safe_dict(adapter_payload.get("adapter"))


def adapter_commands(adapter_payload: dict[str, object]) -> dict[str, object]:
    return safe_dict(adapter_object(adapter_payload).get("commands"))


def command_list(adapter_payload: dict[str, object], key: str) -> list[object]:
    return safe_list(adapter_commands(adapter_payload).get(key))


def adapter_website_evidence(adapter_payload: dict[str, object], fallback: dict[str, object]) -> dict[str, object]:
    adapter = adapter_object(adapter_payload)
    if not adapter:
        return fallback
    return {
        "website_root": adapter.get("website_root", fallback.get("website_root", "")),
        "provided": True,
        "exists": True,
        "package_manager": adapter.get("package_manager", ""),
        "node_engine": adapter.get("node_engine", ""),
        "scanned_file_count": adapter.get("scanned_file_count", 0),
        "helper_matches": safe_list(adapter.get("helpers")),
        "helper_summary": safe_dict(adapter.get("helper_summary")),
        "seo_assets": safe_list(adapter.get("seo_assets")),
        "docs": safe_list(adapter.get("docs")),
        "env_keys_from_example": safe_list(adapter.get("env_keys_from_example")),
        "future_executor_contract": safe_dict(adapter.get("future_executor_contract")),
    }


def build_package(
    *,
    record_payload: dict[str, object],
    blockers: list[str],
    warnings: list[str],
    website_evidence: dict[str, object],
    adapter_payload: dict[str, object],
) -> dict[str, object]:
    record = safe_dict(record_payload.get("execution_record"))
    helper_call = safe_dict(record.get("simulated_helper_call"))
    target_url = str(record.get("target_url", "") or "")
    paired_url = str(record.get("paired_url", "") or "")
    backup_commands = command_list(adapter_payload, "backup_commands")
    seo_generation_commands = command_list(adapter_payload, "seo_generation_commands")
    website_qa_commands = command_list(adapter_payload, "qa_commands")
    build_commands = command_list(adapter_payload, "build_commands")
    adapter = adapter_object(adapter_payload)
    combined_qa_commands = [
        f"python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url {target_url}".strip(),
        f"python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url {paired_url}".strip(),
        *(str(command) for command in website_qa_commands),
    ]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": PACKAGE_ACTION,
        "status": "implementation_package_ready_for_future_executor" if not blockers else "blocked_before_implementation_package",
        "implementation_allowed_for_future_executor": not blockers,
        "target_url": target_url,
        "paired_url": paired_url,
        "table": record.get("table", ""),
        "admin_helper": record.get("admin_helper", ""),
        "cms_payload_path": record.get("cms_payload_path", ""),
        "cms_payload_selection": record.get("cms_payload_selection", ""),
        "admin_helper_call": helper_call,
        "payload_keys": safe_list(record.get("payload_keys")),
        "latest_research_sources": safe_list(record.get("latest_research_sources")),
        "website_evidence": adapter_website_evidence(adapter_payload, website_evidence),
        "website_adapter_status": adapter_payload.get("status", "missing") if adapter_payload else "missing",
        "website_adapter_artifacts": safe_dict(adapter_payload.get("artifacts")) if adapter_payload else {},
        "website_adapter_contract": safe_dict(adapter.get("future_executor_contract")),
        "backup_commands": backup_commands,
        "seo_generation_commands": seo_generation_commands,
        "website_qa_commands": website_qa_commands,
        "build_commands": build_commands,
        "execution_order": [
            "confirm owner-approved execution record is current",
            "run or verify backup command before any CMS/source write",
            "call the website admin helper with admin_helper_call",
            "keep resulting record status as draft unless owner explicitly approved publish status",
            "run website SEO generation commands for sitemap, seo-manifest, and llms assets",
            "run skill pre-publish QA for target and paired URLs",
            "run website QA commands from the adapter",
            "run website build command when source/generated assets changed",
            "run live smoke verification only after a separate approved deployment/publish step",
            "write changelog and retain rollback evidence",
        ],
        "post_write_tasks": safe_list(record.get("post_write_tasks")),
        "qa_commands": combined_qa_commands,
        "rollback_plan": [
            "restore backed-up CMS/source record for both language versions",
            "remove or revert uploaded concept media only if it was created solely for this package",
            "regenerate SEO manifest, sitemap, and llms assets after rollback if those files changed",
            "run QA and smoke checks again after rollback",
        ],
        "blockers": blockers,
        "warnings": warnings,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "safety_note": "This package is an implementation runbook and machine-readable helper-call artifact only. It does not call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.",
    }


def render_report(result: PublishImplementationPackageResult) -> str:
    package = result.package
    helper_call = safe_dict(package.get("admin_helper_call"))
    website_evidence = safe_dict(package.get("website_evidence"))
    lines = [
        "# Publish Implementation Package",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{package.get('target_url', 'N/A')}`",
            f"- Paired URL: `{package.get('paired_url', 'N/A')}`",
            f"- Admin helper: `{package.get('admin_helper', 'N/A')}`",
            f"- CMS payload selection: `{package.get('cms_payload_selection', 'N/A')}`",
            f"- Website adapter status: `{package.get('website_adapter_status', 'missing')}`",
            "- 执行状态: implementation package only；未调用 CMS、未改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把 approved execution record 转换成未来真实执行器可读取的本地实施包：包括 admin helper call、执行顺序、SEO 后置任务、QA 命令、回滚步骤和网站 helper 证据。",
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
            "## Admin Helper Call",
            "",
            f"- Function: `{helper_call.get('function', 'N/A')}`",
            f"- Payload keys: `{', '.join(str(item) for item in safe_list(package.get('payload_keys')))}`",
            "",
            "## Website Evidence",
            "",
            f"- Website root: `{website_evidence.get('website_root', '')}`",
            f"- Exists: `{website_evidence.get('exists', False)}`",
            f"- Package manager: `{website_evidence.get('package_manager', '')}`",
            f"- Node engine: `{website_evidence.get('node_engine', '')}`",
            f"- Scanned files: `{website_evidence.get('scanned_file_count', 0)}`",
            f"- Helper matches: `{len(safe_list(website_evidence.get('helper_matches')))}`",
            f"- SEO script matches: `{len(safe_list(website_evidence.get('seo_script_matches')))}`",
            f"- Adapter SEO assets: `{len(safe_list(website_evidence.get('seo_assets')))}`",
            "",
            "## Website Commands",
            "",
            f"- Backup: `{', '.join(str(item) for item in safe_list(package.get('backup_commands'))) or 'None'}`",
            f"- SEO generation: `{', '.join(str(item) for item in safe_list(package.get('seo_generation_commands'))) or 'None'}`",
            f"- Website QA: `{', '.join(str(item) for item in safe_list(package.get('website_qa_commands'))) or 'None'}`",
            f"- Build: `{', '.join(str(item) for item in safe_list(package.get('build_commands'))) or 'None'}`",
            "",
            "## Execution Order",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in safe_list(package.get("execution_order")))
    lines.extend(["", "## QA Commands", ""])
    lines.extend(f"- `{item}`" for item in safe_list(package.get("qa_commands")) if item)
    lines.extend(["", "## Rollback Plan", ""])
    lines.extend(f"- {item}" for item in safe_list(package.get("rollback_plan")))
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 该实施包不是执行器，只是未来执行器和人工复核的输入。",
            "- 若存在 blockers，不允许进入 CMS/source 执行。",
            "- 图文和效果图内容继续按 design/rendering concept 处理，不能伪装成真实完工项目证明。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, result: PublishImplementationPackageResult) -> tuple[Path, Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    package_path = data_dir / IMPLEMENTATION_PACKAGE_JSON_NAME
    helper_call_path = data_dir / HELPER_CALL_JSON_NAME
    report_path = reports_dir / f"{today}-publish-implementation-package.md"
    result.artifacts.update(
        {
            "implementation_package": str(package_path),
            "admin_helper_call": str(helper_call_path),
            "report": str(report_path),
        }
    )
    write_text(
        package_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "package": result.package,
                "artifacts": result.artifacts,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(helper_call_path, json.dumps(result.package.get("admin_helper_call", {}), ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(result))
    return package_path, helper_call_path, report_path


def run_publish_implementation_package(
    root: Path,
    *,
    execution_record_path: str = "",
    website_root: str = "",
    adapter_path: str = "",
) -> tuple[PublishImplementationPackageResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    record_file = resolve_path(root, execution_record_path) if execution_record_path else data_dir / "publish-approved-execution-record.json"
    adapter_file = resolve_path(root, adapter_path) if adapter_path else data_dir / DEFAULT_ADAPTER_JSON_NAME
    record_payload = read_json(record_file)
    adapter_payload = read_json(adapter_file)
    record = safe_dict(record_payload.get("execution_record"))
    helper_call = safe_dict(record.get("simulated_helper_call"))
    helper_names = [str(record.get("admin_helper", "") or ""), str(helper_call.get("function", "") or "")]
    website_evidence = discover_website_evidence(resolve_path(root, website_root), helper_names) if website_root else empty_website_evidence()
    blockers, warnings = evaluate_package_inputs(
        record_payload=record_payload,
        website_evidence=website_evidence,
        adapter_payload=adapter_payload,
        website_root_provided=bool(website_root),
    )
    package = build_package(
        record_payload=record_payload,
        blockers=blockers,
        warnings=warnings,
        website_evidence=website_evidence,
        adapter_payload=adapter_payload,
    )
    status = str(package.get("status", "blocked_before_implementation_package"))
    result = PublishImplementationPackageResult(status=status, blockers=blockers, warnings=warnings, package=package)
    artifacts = write_outputs(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a no-write publish implementation package from an approved execution record.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--execution-record-path", default="")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--adapter-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_implementation_package(
        Path(args.root),
        execution_record_path=args.execution_record_path,
        website_root=args.website_root,
        adapter_path=args.adapter_path,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
