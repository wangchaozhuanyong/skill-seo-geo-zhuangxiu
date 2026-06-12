#!/usr/bin/env python3
"""Guarded media upload handoff for generated renovation concept assets."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_UPLOAD_PLAN = "seo-workspace/data/media-upload-plan.json"
RESULT_NAME = "publish-media-upload-result.json"
REPORT_NAME = "publish-media-upload-executor.md"
UPLOADED_URL_MAP = "uploaded-url-map.json"
CONFIRM_ENV = "FLASHCAST_APPROVED_MEDIA_UPLOAD_RUN"
CONFIRM_VALUE = "I_UNDERSTAND_THIS_UPLOADS_MEDIA"
ADMIN_MEDIA_REQUIRED = (
    "Direct Supabase storage/media_assets writes are disabled. Upload media through the website management "
    "media library or existing admin media service layer so uploaded files, media records, public URLs, "
    "validation, cache behavior, and audit logs stay synchronized."
)


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
            seen.add(text)
            output.append(text)
    return output


def env_value(name: str) -> str:
    return str(os.environ.get(name, "") or "").strip()


def upload_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for raw in safe_list(plan.get("queue")):
        row = safe_dict(raw)
        if row.get("placeholder_filename"):
            rows.append(row)
    return rows


def evaluate_gates(
    plan: dict[str, Any],
    *,
    mode: str,
    confirm_upload: bool,
    allowed_bucket: str,
    require_env: bool,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    rows = upload_rows(plan)
    if not plan:
        blockers.append("Missing media-upload-plan.json. Run media-upload-plan first.")
    if plan.get("status") != "owner_review_required":
        warnings.append(f"Unexpected media upload plan status: {plan.get('status', 'missing')}.")
    if not rows:
        blockers.append("Media upload queue is empty.")
    for row in rows:
        local_path = Path(str(row.get("local_path", "")))
        if not local_path.is_file():
            blockers.append(f"Local media file missing: {local_path}")
        if row.get("bucket") != allowed_bucket:
            blockers.append(f"Queue item bucket is not allowed: {row.get('bucket', '')}")
        if "Generated" not in str(row.get("claim_boundary", "")) and "concept" not in str(row.get("claim_boundary", "")).lower():
            warnings.append(f"Claim boundary may be missing concept label for {row.get('placeholder_filename', '')}.")
    if mode != "dry-run":
        blockers.append(ADMIN_MEDIA_REQUIRED)
    if mode != "dry-run" and not confirm_upload:
        blockers.append("--confirm-upload is required for non-dry-run media handoff.")
    if mode == "live" and env_value(CONFIRM_ENV) != CONFIRM_VALUE:
        blockers.append(f"{CONFIRM_ENV} must equal {CONFIRM_VALUE} for live media handoff.")
    if require_env or mode != "dry-run":
        warnings.append("Runtime media credentials must belong to the website admin/media-library path, not direct Supabase storage or table writes.")
    return unique_strings(blockers), unique_strings(warnings)


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Publish Media Upload Executor",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- Mode: `{summary.get('mode')}`",
        f"- Queue items: `{summary.get('queue_count')}`",
        f"- Media upload executed: `{summary.get('media_upload_executed')}`",
        "- 执行状态: guarded media upload handoff；本工具不直接上传媒体",
        "",
        "## 今日决策",
        "",
        "今天把真实媒体上传门禁固定为管理后台媒体库路径：它读取 media-upload-plan，验证本地文件、bucket、概念图边界和确认 token，并生成后台媒体上传交接材料。禁止直接写 Supabase Storage 或 media_assets 表。",
        "",
        "## Blockers",
        "",
    ]
    blockers = safe_list(summary.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = safe_list(summary.get("warnings"))
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Uploaded Files", ""])
    uploaded = safe_list(summary.get("uploaded_files"))
    if uploaded:
        for item in uploaded:
            row = safe_dict(item)
            lines.append(f"- `{row.get('placeholder_filename')}` -> `{row.get('file_url')}`")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本工具永远不直接上传媒体或写 media_assets 表。",
            "- 真实媒体上传必须通过网站管理后台媒体库或既有 admin media helper。",
            f"- live 媒体交接仍必须设置 `{CONFIRM_ENV}={CONFIRM_VALUE}`，但该确认不能授权直接 Supabase 写入。",
            "- 只允许上传到配置的 allowed bucket。",
            "- 生成图片必须保持设计方案/效果图方案/rendering concept 边界。",
            "- 上传后仍需运行 media-ready handoff、CMS dry-run、QA 和发布门禁。",
            "",
            "## Artifacts",
            "",
        ]
    )
    for name, path in safe_dict(summary.get("artifacts")).items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines) + "\n"


def run_publish_media_upload_executor(
    root: Path,
    *,
    upload_plan_path: str = "",
    mode: str = "dry-run",
    confirm_upload: bool = False,
    allowed_bucket: str = "site-images",
    require_env: bool = False,
    create_media_records: bool = True,
) -> tuple[dict[str, Any], tuple[Path, Path, Path]]:
    root = root.resolve()
    plan_file = resolve_path(root, upload_plan_path or DEFAULT_UPLOAD_PLAN)
    plan = read_json(plan_file)
    rows = upload_rows(plan)
    blockers, warnings = evaluate_gates(
        plan,
        mode=mode,
        confirm_upload=confirm_upload,
        allowed_bucket=allowed_bucket,
        require_env=require_env,
    )
    uploaded_files: list[dict[str, Any]] = []
    media_upload_executed = False
    status = "media_upload_executor_ready_dry_run" if not blockers else "blocked_before_media_upload_execution"
    data_dir = root / "seo-workspace" / "data"
    result_path = data_dir / RESULT_NAME
    uploaded_map_path = data_dir / UPLOADED_URL_MAP
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    uploaded_url_map = {"files": uploaded_files} if uploaded_files else {"files": []}
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "mode": mode,
        "upload_plan_path": str(plan_file),
        "queue_count": len(rows),
        "allowed_bucket": allowed_bucket,
        "confirm_upload": confirm_upload,
        "create_media_records": create_media_records,
        "direct_storage_write_disabled": True,
        "required_upload_path": "website_admin_media_library",
        "media_upload_executed": media_upload_executed,
        "uploaded_files": uploaded_files,
        "blockers": unique_strings(blockers),
        "warnings": unique_strings(warnings),
        "artifacts": {
            "media_upload_result": str(result_path),
            "uploaded_url_map": str(uploaded_map_path),
            "media_upload_report": str(report_path),
        },
        "no_media_upload_executed": not media_upload_executed,
        "no_cms_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
    }
    write_text(result_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    if uploaded_files:
        write_text(uploaded_map_path, json.dumps(uploaded_url_map, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (result_path, uploaded_map_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded media upload executor for generated renovation concept assets.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--upload-plan-path", default="")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "staging", "live"])
    parser.add_argument("--confirm-upload", action="store_true")
    parser.add_argument("--allowed-bucket", default="site-images")
    parser.add_argument("--require-env", action="store_true")
    parser.add_argument("--no-create-media-records", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_publish_media_upload_executor(
        Path(args.root),
        upload_plan_path=args.upload_plan_path,
        mode=args.mode,
        confirm_upload=args.confirm_upload,
        allowed_bucket=args.allowed_bucket,
        require_env=args.require_env,
        create_media_records=not args.no_create_media_records,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] in {"media_upload_executor_ready_dry_run", "media_uploaded_waiting_media_ready_handoff"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
