#!/usr/bin/env python3
"""Import an owner-filled decision JSON into the current decision template."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


DEFAULT_TEMPLATE = "seo-workspace/data/content-studio-owner-decision.template.json"
DEFAULT_OUTPUT = "seo-workspace/data/content-studio-owner-decision.template.json"
ALLOWED_SCOPES = {
    "owner_review_only",
    "media_ready_handoff_only",
    "approved_dry_run_only",
    "operator_ready_handoff_only",
    "live_publish_requires_separate_confirmation",
}
DECISION_KEYS = (
    "content_approved",
    "media_urls_confirmed",
    "qa_approved",
    "latest_research_verified",
    "explicit_execution_requested",
    "allowed_execution_scope",
    "owner_notes",
)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def validate_import(current_template: dict[str, Any], filled: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not current_template:
        blockers.append("Missing current owner decision template. Run content-studio-approval-packet first.")
    if not filled:
        blockers.append("Missing filled owner decision JSON.")
        return blockers
    if safe_dict(filled.get("decision")) == {}:
        blockers.append("Filled JSON is missing decision object.")
    if str(filled.get("target_url", "")) != str(current_template.get("target_url", "")):
        blockers.append("Filled decision target_url does not match current template.")
    if str(filled.get("paired_url", "")) != str(current_template.get("paired_url", "")):
        blockers.append("Filled decision paired_url does not match current template.")
    scope = str(safe_dict(filled.get("decision")).get("allowed_execution_scope", ""))
    if scope not in ALLOWED_SCOPES:
        blockers.append(f"Unsupported allowed_execution_scope: {scope or 'missing'}.")
    if filled.get("approval_is_not_execution") is not True:
        blockers.append("Filled JSON must keep approval_is_not_execution=true.")
    return blockers


def imported_template(current_template: dict[str, Any], filled: dict[str, Any]) -> dict[str, Any]:
    current_decision = safe_dict(current_template.get("decision"))
    filled_decision = safe_dict(filled.get("decision"))
    merged_decision = dict(current_decision)
    for key in DECISION_KEYS:
        if key in filled_decision:
            merged_decision[key] = filled_decision[key]
    merged_decision["allowed_execution_scope_options"] = current_decision.get(
        "allowed_execution_scope_options",
        [
            "owner_review_only",
            "media_ready_handoff_only",
            "approved_dry_run_only",
            "operator_ready_handoff_only",
            "live_publish_requires_separate_confirmation",
        ],
    )
    output = dict(current_template)
    output["decision"] = merged_decision
    output["status"] = "owner_decision_imported_waiting_status_check"
    output["imported_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    output["imported_from_owner_decision_editor"] = filled.get("exported_from_owner_decision_editor") is True
    output["decision_preserved_from_previous_template"] = True
    output["approval_is_not_execution"] = True
    output["no_cms_write_executed"] = True
    output["no_source_write_executed"] = True
    output["no_media_upload_executed"] = True
    output["no_publish_executed"] = True
    output["no_deploy_executed"] = True
    return output


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Owner Decision Import",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- 目标页面: `{summary.get('target_url') or 'not_found'}`",
        f"- 配对页面: `{summary.get('paired_url') or 'not_found'}`",
        f"- Filled JSON: `{summary.get('filled_decision_path')}`",
        f"- Output template: `{summary.get('output_path')}`",
        "- 执行状态: decision import only；未上传媒体、未写 CMS、未改源码、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把业主表单导出的 filled JSON 安全导入当前 owner decision template，后续仍需要运行 decision status / decision orchestrator 才能判断下一步。",
        "",
        "## Blockers",
        "",
    ]
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 运行 `content-studio-owner-decision-status` 复查导入后的决定。",
            "- 如果状态允许，再运行 `content-studio-decision-orchestrator` 进入下一步 no-write 准备。",
            "- 真实发布仍必须另有业主明确执行指令。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_owner_decision_import(
    root: Path,
    *,
    filled_decision_path: str,
    template_path: str = "",
    output_path: str = "",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    filled_file = resolve_path(root, filled_decision_path) if filled_decision_path else root / "MISSING_FILLED_DECISION_JSON"
    template_file = resolve_path(root, template_path or DEFAULT_TEMPLATE)
    output_file = resolve_path(root, output_path or DEFAULT_OUTPUT)
    current_template = read_json(template_file)
    filled = read_json(filled_file)
    blockers = validate_import(current_template, filled)
    status = "owner_decision_imported_waiting_status_check" if not blockers else "owner_decision_import_blocked"
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-owner-decision-import.md"
    summary_path = root / "seo-workspace" / "data" / "content-studio-owner-decision-import.json"
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "target_url": current_template.get("target_url", ""),
        "paired_url": current_template.get("paired_url", ""),
        "filled_decision_path": str(filled_file),
        "template_path": str(template_file),
        "output_path": str(output_file),
        "blockers": blockers,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
    }
    if not blockers:
        write_text(output_file, json.dumps(imported_template(current_template, filled), ensure_ascii=False, indent=2) + "\n")
    write_text(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, [summary_path, report_path, output_file]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import an owner-filled decision JSON; does not execute.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--filled-decision-path", required=True)
    parser.add_argument("--template-path", default="")
    parser.add_argument("--output-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_owner_decision_import(
        Path(args.root),
        filled_decision_path=args.filled_decision_path,
        template_path=args.template_path,
        output_path=args.output_path,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] == "owner_decision_imported_waiting_status_check" else 1


if __name__ == "__main__":
    raise SystemExit(main())
