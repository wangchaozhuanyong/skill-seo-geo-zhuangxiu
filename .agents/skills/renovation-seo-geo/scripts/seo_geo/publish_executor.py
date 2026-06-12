#!/usr/bin/env python3
"""Build a gated CMS/source write request without executing the publish."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


WRITE_REQUEST_JSON_NAME = "cms-write-request.json"
BASE_CMS_PAYLOAD_NAME = "rich-content-cms-payload.json"
EDITOR_APPLIED_PAYLOAD_NAME = "rich-content-cms-payload.editor-applied.json"
MEDIA_READY_PAYLOAD_NAME = "rich-content-cms-payload.media-ready.json"


@dataclass
class ExecutorResult:
    status: str
    mode: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    write_request: dict[str, object] = field(default_factory=dict)
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


def safe_get_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def select_cms_payload_file(root: Path, cms_payload_path: str = "") -> tuple[Path, str]:
    data_dir = root / "seo-workspace" / "data"
    if cms_payload_path:
        path = Path(cms_payload_path)
        return (path if path.is_absolute() else root / path), "explicit"
    media_ready = data_dir / MEDIA_READY_PAYLOAD_NAME
    if media_ready.exists():
        return media_ready, "auto_media_ready"
    editor_applied = data_dir / EDITOR_APPLIED_PAYLOAD_NAME
    if editor_applied.exists():
        return editor_applied, "auto_editor_applied"
    return data_dir / BASE_CMS_PAYLOAD_NAME, "auto_base"


def payload_has_media_placeholders(payload: dict[str, object]) -> list[str]:
    hits: list[str] = []
    pattern = re.compile(r"NEEDS_MEDIA_UPLOAD:[^\"'\s<>]+")
    for key, value in flatten(payload):
        if isinstance(value, str):
            for match in pattern.findall(value):
                hits.append(f"{key}={match}")
    return hits


def flatten(value: object, prefix: str = "") -> list[tuple[str, object]]:
    if isinstance(value, dict):
        rows: list[tuple[str, object]] = []
        for key, child in value.items():
            rows.extend(flatten(child, f"{prefix}.{key}" if prefix else str(key)))
        return rows
    if isinstance(value, list):
        rows = []
        for index, child in enumerate(value):
            rows.extend(flatten(child, f"{prefix}[{index}]"))
        return rows
    return [(prefix, value)]


def planned_helper_input(cms_payload: dict[str, object], *, next_status: str) -> dict[str, object]:
    payload = safe_get_dict(cms_payload.get("payload"))
    helper = str(cms_payload.get("admin_helper", ""))
    if helper == "saveAdminService":
        return {
            "function": "saveAdminService",
            "input": {
                "record": payload | {"status": next_status},
                "nextStatus": next_status,
            },
        }
    if helper == "saveAdminBlogPost":
        return {
            "function": "saveAdminBlogPost",
            "input": {
                "record": payload | {"status": next_status},
                "nextStatus": next_status,
            },
        }
    return {
        "function": helper or "saveAdminRecord",
        "input": {
            "table": cms_payload.get("table", "NEEDS_OWNER_INPUT"),
            "payload": payload | {"status": next_status},
            "action": "update_or_insert_after_record_id_confirmed",
        },
    }


def evaluate_executor_gates(
    *,
    plan: dict[str, object],
    cms_payload: dict[str, object],
    owner_approved: bool,
    explicit_execution: bool,
    qa_passed: bool,
    media_ready: bool,
    allow_blocked_plan: bool,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    plan_status = str(plan.get("status", ""))
    if plan_status != "ready_for_approved_execution_plan" and not allow_blocked_plan:
        blockers.append(f"Publish plan is not ready_for_approved_execution_plan: {plan_status or 'missing'}.")
    if not owner_approved:
        blockers.append("Owner approval flag missing (--owner-approved).")
    if not explicit_execution:
        blockers.append("Explicit execution flag missing (--explicit-execution).")
    if not qa_passed:
        blockers.append("QA passed flag missing (--qa-passed).")
    if not cms_payload:
        blockers.append("CMS payload draft is missing. Run rich-blocks first.")
    payload = safe_get_dict(cms_payload.get("payload"))
    if not payload:
        blockers.append("CMS payload draft has no payload object.")
    if str(cms_payload.get("admin_helper", "")) != str(safe_get_dict(plan.get("queue_item")).get("admin_helper", "")):
        warnings.append("CMS payload admin_helper does not match publish plan queue item.")
    if str(cms_payload.get("table", "")) != str(safe_get_dict(plan.get("queue_item")).get("table", "")):
        warnings.append("CMS payload table does not match publish plan queue item.")
    media_hits = payload_has_media_placeholders(cms_payload)
    if media_hits:
        blockers.append("Media placeholders remain in selected CMS payload. Generate/upload/select media and use a media-ready payload before execution.")
    elif media_ready:
        warnings.append("Media-ready flag supplied and selected CMS payload has no media placeholders.")
    if str(payload.get("status", "")) not in {"draft", "published"}:
        warnings.append("Payload status is not draft or published; website admin may reject it.")
    return blockers, warnings


def validate_editor_applied_selection(root: Path, *, cms_payload_file: Path, cms_payload_selection: str, cms_payload: dict[str, object]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    data_dir = root / "seo-workspace" / "data"
    editor_payload_path = data_dir / EDITOR_APPLIED_PAYLOAD_NAME
    media_ready_path = data_dir / MEDIA_READY_PAYLOAD_NAME
    summary_path = data_dir / "rich-content-editor-apply-summary.json"
    uses_editor_payload = cms_payload_selection == "auto_editor_applied" or cms_payload_file.resolve() == editor_payload_path.resolve()
    uses_media_ready_payload = cms_payload_selection == "auto_media_ready" or cms_payload_file.resolve() == media_ready_path.resolve()
    includes_editor_applied = bool(safe_get_dict(cms_payload.get("editor_applied")))
    if not (uses_editor_payload or (uses_media_ready_payload and includes_editor_applied)):
        return blockers, warnings
    if not safe_get_dict(cms_payload.get("editor_applied")):
        blockers.append("Selected editor-applied CMS payload is missing editor_applied safety metadata.")
    summary = read_json(summary_path)
    if summary:
        summary_status = str(summary.get("status", ""))
        if summary_status != "editor_applied_payload_ready_for_owner_review":
            blockers.append(f"Editor-applied payload QA is not ready: {summary_status or 'missing'}. Run rich-editor-apply and resolve blockers first.")
        if safe_get_dict(cms_payload.get("editor_applied")).get("no_cms_write_executed") is not True:
            blockers.append("Editor-applied payload safety flag no_cms_write_executed is missing or false.")
        if safe_get_dict(cms_payload.get("editor_applied")).get("no_live_actions_executed") is not True:
            blockers.append("Editor-applied payload safety flag no_live_actions_executed is missing or false.")
    else:
        warnings.append("Editor-applied payload selected but rich-content-editor-apply-summary.json is missing; verify rich-editor-apply QA before execution.")
    return blockers, warnings


def build_write_request(
    *,
    plan: dict[str, object],
    cms_payload: dict[str, object],
    mode: str,
    next_status: str,
    cms_payload_file: Path,
    cms_payload_selection: str,
) -> dict[str, object]:
    queue_item = safe_get_dict(plan.get("queue_item"))
    payload = safe_get_dict(cms_payload.get("payload"))
    media_placeholders = payload_has_media_placeholders(cms_payload)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "mode": mode,
        "action": "dry_run_only_no_cms_write",
        "no_cms_write_executed": True,
        "target_url": queue_item.get("target_url", ""),
        "paired_url": queue_item.get("paired_url", ""),
        "table": cms_payload.get("table", queue_item.get("table", "")),
        "admin_helper": cms_payload.get("admin_helper", queue_item.get("admin_helper", "")),
        "cms_payload_path": str(cms_payload_file),
        "cms_payload_selection": cms_payload_selection,
        "planned_helper_call": planned_helper_input(cms_payload, next_status=next_status),
        "payload_keys": sorted(payload.keys()),
        "media_placeholders": media_placeholders,
        "seo_assets_after_write": [
            "regenerate seo-manifest if the website uses generated SEO metadata",
            "regenerate sitemap.xml if URL/status/indexability changes",
            "regenerate llms.txt if public content changes",
            "run live smoke verification only after approved deployment",
        ],
        "safety_note": "This request is a local dry-run artifact. It does not import website code, call CMS, write Supabase, upload media, publish, or deploy.",
    }


def render_report(result: ExecutorResult) -> str:
    request = result.write_request
    lines = [
        "# CMS/Source Publish Executor Dry Run",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Mode: {result.mode}",
        f"- Status: {result.status}",
        f"- Target URL: `{request.get('target_url', 'N/A')}`",
        f"- Paired URL: `{request.get('paired_url', 'N/A')}`",
        f"- Table: `{request.get('table', 'N/A')}`",
        f"- Admin helper: `{request.get('admin_helper', 'N/A')}`",
        f"- CMS payload path: `{request.get('cms_payload_path', 'N/A')}`",
        f"- CMS payload selection: `{request.get('cms_payload_selection', 'N/A')}`",
        "- 执行状态: dry-run only；未写入 CMS、未调用 Supabase、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把发布计划和 CMS payload 草案转换成执行器 dry-run 写入请求，明确后续真实发布需要调用的 helper、字段、媒体占位和 SEO 生成步骤。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    helper_call = safe_get_dict(request.get("planned_helper_call"))
    lines.extend(
        [
            "",
            "## Planned Helper Call",
            "",
            f"- Function: `{helper_call.get('function', 'N/A')}`",
            f"- Payload keys: `{', '.join(request.get('payload_keys', []))}`",
            f"- Media placeholders: `{len(request.get('media_placeholders', []))}`",
            "",
            "## Safety Notes",
            "",
            "- 该 dry-run 不导入网站源码、不调用后台、不写数据库。",
            "- 只有没有 blockers 时，后续 executor 才能进入真实 CMS/source 执行阶段。",
            "- 真实执行仍需备份、回滚、变更日志、媒体上传/选择、双语同步、SEO manifest/sitemap/llms 更新和上线 smoke QA。",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifacts(root: Path, result: ExecutorResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    json_path = data_dir / WRITE_REQUEST_JSON_NAME
    report_path = reports_dir / f"{today}-publish-executor-dry-run.md"
    result.artifacts.update({"write_request": str(json_path), "dry_run_report": str(report_path)})
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": result.status,
        "mode": result.mode,
        "blockers": result.blockers,
        "warnings": result.warnings,
        "write_request": result.write_request,
        "artifacts": result.artifacts,
    }
    write_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(result))
    return json_path, report_path


def run_publish_executor(
    root: Path,
    *,
    mode: str = "dry-run",
    plan_path: str = "",
    cms_payload_path: str = "",
    next_status: str = "draft",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    media_ready: bool = False,
    allow_blocked_plan: bool = False,
) -> tuple[ExecutorResult, tuple[Path, Path]]:
    root = root.resolve()
    plan_file = Path(plan_path) if plan_path else root / "seo-workspace" / "data" / "publish-execution-plan.json"
    if not plan_file.is_absolute():
        plan_file = root / plan_file
    payload_file, payload_selection = select_cms_payload_file(root, cms_payload_path)
    plan = read_json(plan_file)
    cms_payload = read_json(payload_file)
    blockers, warnings = evaluate_executor_gates(
        plan=plan,
        cms_payload=cms_payload,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        media_ready=media_ready,
        allow_blocked_plan=allow_blocked_plan,
    )
    editor_blockers, editor_warnings = validate_editor_applied_selection(
        root,
        cms_payload_file=payload_file,
        cms_payload_selection=payload_selection,
        cms_payload=cms_payload,
    )
    blockers.extend(editor_blockers)
    warnings.extend(editor_warnings)
    request = build_write_request(
        plan=plan,
        cms_payload=cms_payload,
        mode=mode,
        next_status=next_status,
        cms_payload_file=payload_file,
        cms_payload_selection=payload_selection,
    )
    status = "dry_run_write_request_ready" if not blockers else "blocked_before_cms_write"
    result = ExecutorResult(status=status, mode=mode, blockers=blockers, warnings=warnings, write_request=request)
    artifacts = write_artifacts(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a gated CMS/source write request dry-run.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    parser.add_argument("--plan-path", default="")
    parser.add_argument("--cms-payload-path", default="")
    parser.add_argument("--next-status", default="draft", choices=["draft", "published"])
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--media-ready", action="store_true")
    parser.add_argument("--allow-blocked-plan", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_executor(
        Path(args.root),
        mode=args.mode,
        plan_path=args.plan_path,
        cms_payload_path=args.cms_payload_path,
        next_status=args.next_status,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        media_ready=args.media_ready,
        allow_blocked_plan=args.allow_blocked_plan,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
