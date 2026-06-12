#!/usr/bin/env python3
"""Audit whether the SEO/GEO automation system has all major capability gates."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


SUMMARY_NAME = "automation-completion-audit.json"
REPORT_NAME = "automation-completion-audit.md"

REQUIRED_MODULES = {
    "latest internet research": "research_search.py",
    "trusted research intake": "research_intake.py",
    "rich text image editor": "rich_editor.py",
    "editor export apply": "rich_editor_apply.py",
    "concept rendering assets": "concept_assets.py",
    "owner review package": "content_studio_owner_review_package.py",
    "fixed time install plan": "automation_install_plan.py",
    "media upload executor": "publish_media_upload_executor.py",
    "post media handoff": "publish_post_media_handoff.py",
    "admin publish handoff": "publish_cms_write_executor.py",
}

REQUIRED_ARTIFACTS = {
    "owner review dashboard": "seo-workspace/drafts/2026-06-11-content-studio-owner-review-dashboard.html",
    "automation install plan": "seo-workspace/data/automation-install-plan.json",
    "media upload result": "seo-workspace/data/publish-media-upload-result.json",
    "post media handoff": "seo-workspace/data/publish-post-media-handoff.json",
    "admin publish gate": "seo-workspace/data/publish-cms-write-result.json",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def status_of(root: Path, relative_path: str) -> str:
    payload = read_json(root / relative_path)
    return str(payload.get("status", "missing")) if payload else "missing"


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Automation Completion Audit",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- Capability ready: `{summary.get('capability_ready')}`",
        f"- Execution ready now: `{summary.get('execution_ready_now')}`",
        "- 执行状态: audit/report only；未上传、未写数据库、未发布、未部署",
        "",
        "## 结论",
        "",
        summary.get("conclusion_zh", ""),
        "",
        "## Capability Checks",
        "",
    ]
    for item in safe_list(summary.get("capability_checks")):
        lines.append(f"- {item.get('name')}: `{item.get('status')}` -> `{item.get('path')}`")
    lines.extend(["", "## Artifact Checks", ""])
    for item in safe_list(summary.get("artifact_checks")):
        lines.append(f"- {item.get('name')}: `{item.get('status')}` -> `{item.get('path')}`")
    lines.extend(["", "## Remaining Owner/Runtime Inputs", ""])
    remaining = safe_list(summary.get("remaining_owner_inputs"))
    lines.extend(f"- {item}" for item in remaining) if remaining else lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    blockers = safe_list(summary.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 这个审计只判断系统能力和当前门禁状态，不执行任何发布动作。",
            "- 如果 capability ready 但 execution ready now 为 false，表示代码链路已具备，剩余是业主授权、真实 URL 或环境凭证。",
            "- 真实发布仍必须按媒体准备、post-media handoff、管理后台发布、QA、receipt、部署的顺序执行。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_automation_completion_audit(root: Path) -> tuple[dict[str, Any], tuple[Path, Path]]:
    root = root.resolve()
    scripts_dir = root / ".agents" / "skills" / "renovation-seo-geo" / "scripts" / "seo_geo"
    capability_checks = []
    blockers: list[str] = []
    for name, filename in REQUIRED_MODULES.items():
        path = scripts_dir / filename
        exists = path.exists()
        capability_checks.append({"name": name, "status": "present" if exists else "missing", "path": str(path)})
        if not exists:
            blockers.append(f"Missing capability module: {filename}")

    artifact_checks = []
    for name, relative_path in REQUIRED_ARTIFACTS.items():
        path = root / relative_path
        artifact_checks.append({"name": name, "status": "present" if path.exists() else "missing", "path": str(path)})

    media_upload_status = status_of(root, "seo-workspace/data/publish-media-upload-result.json")
    post_media_status = status_of(root, "seo-workspace/data/publish-post-media-handoff.json")
    cms_write_status = status_of(root, "seo-workspace/data/publish-cms-write-result.json")
    install_status = status_of(root, "seo-workspace/data/automation-install-plan.json")

    remaining_owner_inputs = []
    if media_upload_status != "media_uploaded_waiting_media_ready_handoff":
        remaining_owner_inputs.append("真实媒体 URL 尚未就绪；需要 owner approval、后台媒体上传/媒体库路径，或手工填写公开 HTTPS 图片 URL。")
    if post_media_status != "post_media_handoff_ready_for_owner_review":
        remaining_owner_inputs.append("post-media handoff 尚未 ready；通常因为 uploaded-url-map 缺公开 HTTPS URL 或 owner confirmation。")
    if cms_write_status != "cms_write_executed_waiting_post_write_qa":
        remaining_owner_inputs.append("内容尚未通过管理后台发布；需要媒体 URL 全部就绪、明确执行、允许 URL、confirm token 和网站管理后台/后台服务发布权限。")
    if install_status != "automation_install_plan_ready_for_owner_review":
        remaining_owner_inputs.append("固定时间安装包未 ready；需要先运行 automation-schedule 和 automation-install-plan。")

    capability_ready = not blockers
    execution_ready_now = not remaining_owner_inputs
    status = "automation_capability_complete_waiting_owner_runtime_inputs" if capability_ready and not execution_ready_now else "automation_fully_execution_ready"
    if blockers:
        status = "automation_completion_audit_blocked_missing_capabilities"
    conclusion = (
        "代码能力链路已经补齐；当前不应该继续写新功能，剩余是业主授权、真实图片 URL/后台媒体上传、管理后台发布权限和明确发布执行。"
        if capability_ready and not execution_ready_now
        else "当前已具备完整能力且运行输入也齐全，可以按批准范围进入真实执行。"
    )
    if blockers:
        conclusion = "仍有能力模块缺失，需要继续补代码。"

    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "capability_ready": capability_ready,
        "execution_ready_now": execution_ready_now,
        "conclusion_zh": conclusion,
        "capability_checks": capability_checks,
        "artifact_checks": artifact_checks,
        "runtime_status": {
            "media_upload": media_upload_status,
            "post_media_handoff": post_media_status,
            "cms_write": cms_write_status,
            "automation_install": install_status,
        },
        "remaining_owner_inputs": remaining_owner_inputs,
        "blockers": blockers,
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
    }
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit SEO/GEO automation capability completion.")
    parser.add_argument("--root", default=".")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_automation_completion_audit(Path(args.root))
    for output in artifacts:
        print(output)
    return 0 if summary["capability_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
