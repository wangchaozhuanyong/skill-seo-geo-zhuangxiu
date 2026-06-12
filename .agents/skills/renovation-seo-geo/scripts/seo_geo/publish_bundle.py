#!/usr/bin/env python3
"""Create a sealed publish execution bundle without executing it."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path


BUNDLE_JSON_NAME = "publish-execution-bundle.json"


@dataclass
class PublishBundleResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    bundle: dict[str, object] = field(default_factory=dict)
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


def evaluate_bundle_inputs(readiness: dict[str, object], cms_request: dict[str, object]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    readiness_status = str(readiness.get("status", "") or "")
    cms_status = str(cms_request.get("status", "") or "")
    write_request = safe_dict(cms_request.get("write_request"))
    helper_call = safe_dict(write_request.get("planned_helper_call"))

    if not readiness:
        blockers.append("Missing publish-readiness.json. Run publish-readiness first.")
    elif readiness_status != "ready_for_owner_approved_publish_handoff":
        blockers.append(f"Publish readiness is not ready_for_owner_approved_publish_handoff: {readiness_status or 'missing'}.")
    for blocker in safe_list(readiness.get("blockers")):
        blockers.append(f"Publish readiness blocker: {blocker}")
    for warning in safe_list(readiness.get("warnings")):
        warnings.append(f"Publish readiness warning: {warning}")

    if not cms_request:
        blockers.append("Missing cms-write-request.json. Run publish-executor first.")
    elif cms_status != "dry_run_write_request_ready":
        blockers.append(f"CMS write request is not dry_run_write_request_ready: {cms_status or 'missing'}.")
    for blocker in safe_list(cms_request.get("blockers")):
        blockers.append(f"CMS write request blocker: {blocker}")
    for warning in safe_list(cms_request.get("warnings")):
        warnings.append(f"CMS write request warning: {warning}")

    if not write_request:
        blockers.append("CMS write request has no write_request object.")
    elif write_request.get("no_cms_write_executed") is not True:
        warnings.append("CMS write request safety flag no_cms_write_executed is missing or false.")
    if not helper_call:
        blockers.append("CMS write request has no planned_helper_call.")
    if safe_list(write_request.get("media_placeholders")):
        blockers.append("CMS write request still contains media placeholders; generate a media-ready payload before bundling.")
    if str(write_request.get("action", "")) != "dry_run_only_no_cms_write":
        warnings.append("CMS write request action is not the expected dry-run action.")
    return blockers, warnings


def build_bundle(readiness: dict[str, object], cms_request: dict[str, object]) -> dict[str, object]:
    evidence = safe_dict(readiness.get("evidence"))
    write_request = safe_dict(cms_request.get("write_request"))
    helper_call = safe_dict(write_request.get("planned_helper_call"))
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": "sealed_execution_bundle_only_no_cms_write",
        "status": "execution_bundle_ready_for_approved_executor",
        "target_url": write_request.get("target_url", ""),
        "paired_url": write_request.get("paired_url", ""),
        "table": write_request.get("table", ""),
        "admin_helper": write_request.get("admin_helper", ""),
        "cms_payload_path": write_request.get("cms_payload_path", ""),
        "cms_payload_selection": write_request.get("cms_payload_selection", ""),
        "planned_helper_call": helper_call,
        "payload_keys": safe_list(write_request.get("payload_keys")),
        "latest_research_sources": safe_list(evidence.get("latest_research_sources")),
        "media_url_map_present": evidence.get("media_url_map_present", False),
        "media_ready_payload_present": evidence.get("media_ready_payload_present", False),
        "editor_applied_payload_present": evidence.get("editor_applied_payload_present", False),
        "editor_applied_used_edited_blocks": evidence.get("editor_applied_used_edited_blocks", False),
        "post_write_tasks": safe_list(write_request.get("seo_assets_after_write")),
        "required_pre_execution_checks": [
            "owner approval is recorded for this exact bundle",
            "explicit execution instruction references this bundle",
            "pre-publish QA is still passing",
            "CMS/source backup exists",
            "rollback plan and change log are ready",
            "media URLs are public and stable",
            "language pair scope is correct",
        ],
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "safety_note": "This is a sealed local execution bundle for a later approved executor. It does not call CMS, write source, upload media, publish, or deploy.",
    }


def render_report(result: PublishBundleResult) -> str:
    bundle = result.bundle
    helper = safe_dict(bundle.get("planned_helper_call"))
    lines = [
        "# Publish Execution Bundle",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{bundle.get('target_url', 'N/A')}`",
        f"- Paired URL: `{bundle.get('paired_url', 'N/A')}`",
        f"- Table: `{bundle.get('table', 'N/A')}`",
        f"- Admin helper: `{bundle.get('admin_helper', 'N/A')}`",
        f"- CMS payload selection: `{bundle.get('cms_payload_selection', 'N/A')}`",
        "- 执行状态: sealed bundle only；未写 CMS、未修改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把 readiness 证据和 CMS dry-run 写入请求封装成最终执行包。这个包用于后续已批准执行器读取，避免真实发布时重新拼字段或误用旧 payload。",
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
            "## Execution Payload",
            "",
            f"- Function: `{helper.get('function', 'N/A')}`",
            f"- Payload keys: `{', '.join(str(item) for item in safe_list(bundle.get('payload_keys')) )}`",
            f"- Latest research sources: `{len(safe_list(bundle.get('latest_research_sources')))}`",
            f"- Media URL map present: `{bundle.get('media_url_map_present', False)}`",
            f"- Media-ready payload present: `{bundle.get('media_ready_payload_present', False)}`",
            f"- Editor-applied payload present: `{bundle.get('editor_applied_payload_present', False)}`",
            f"- Editor-applied used edited blocks: `{bundle.get('editor_applied_used_edited_blocks', False)}`",
            "",
            "## Safety Notes",
            "",
            "- 该文件不是发布动作，只是后续 approved executor 的输入包。",
            "- 若存在 blockers，不允许进入 CMS/source 执行。",
            "- 真实执行仍必须通过网站既有 admin/backend helper，并保留 backup、changelog、rollback 和上线 smoke QA。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, result: PublishBundleResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    bundle_path = data_dir / BUNDLE_JSON_NAME
    report_path = reports_dir / f"{today}-publish-execution-bundle.md"
    result.artifacts.update({"bundle_json": str(bundle_path), "report": str(report_path)})
    write_text(
        bundle_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "bundle": result.bundle,
                "artifacts": result.artifacts,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return bundle_path, report_path


def run_publish_bundle(
    root: Path,
    *,
    readiness_path: str = "",
    cms_request_path: str = "",
) -> tuple[PublishBundleResult, tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    readiness_file = resolve_path(root, readiness_path) if readiness_path else data_dir / "publish-readiness.json"
    cms_request_file = resolve_path(root, cms_request_path) if cms_request_path else data_dir / "cms-write-request.json"
    readiness = read_json(readiness_file)
    cms_request = read_json(cms_request_file)
    blockers, warnings = evaluate_bundle_inputs(readiness, cms_request)
    bundle = build_bundle(readiness, cms_request) if cms_request else {"safety_note": "No CMS write request was available; no execution bundle can be used."}
    status = "execution_bundle_ready_for_approved_executor" if not blockers else "blocked_before_execution_bundle"
    if blockers:
        bundle["status"] = "blocked_before_execution_bundle"
    result = PublishBundleResult(status=status, blockers=blockers, warnings=warnings, bundle=bundle)
    artifacts = write_outputs(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a sealed publish execution bundle without executing it.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--readiness-path", default="")
    parser.add_argument("--cms-request-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_bundle(Path(args.root), readiness_path=args.readiness_path, cms_request_path=args.cms_request_path)
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
