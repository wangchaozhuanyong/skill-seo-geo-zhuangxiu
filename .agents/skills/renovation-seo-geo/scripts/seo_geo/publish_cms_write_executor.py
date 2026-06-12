#!/usr/bin/env python3
"""Guarded admin publish handoff for approved Flash Cast content packages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_INPUT = "seo-workspace/data/publish-approved-execution-input.json"
RESULT_NAME = "publish-cms-write-result.json"
REPORT_NAME = "publish-cms-write-executor.md"
CONFIRM_ENV = "FLASHCAST_APPROVED_PUBLISH_RUN"
CONFIRM_VALUE = "I_UNDERSTAND_THIS_WRITES_CMS"
EXPECTED_INPUT_STATUS = "execution_input_template_ready_for_approved_executor"
EXPECTED_INPUT_ACTION = "publish_approved_execution_input_template_only_no_execute"
SUPPORTED_HELPERS = {"saveAdminService"}
PUBLISH_URL_ENV = "FLASHCAST_CONTENT_PUBLISH_URL"
ADMIN_TOKEN_ENV = "FLASHCAST_ADMIN_ACCESS_TOKEN"
PUBLISH_SECRET_ENV = "FLASHCAST_CONTENT_PUBLISH_SECRET"
PRIVATE_ENV_PATH = Path.home() / ".codex" / "automations" / "flash-cast-daily-seo-geo" / "publish.env"


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


def find_media_placeholders(value: object) -> list[str]:
    serialized = json.dumps(value, ensure_ascii=False)
    return sorted(set(re.findall(r"NEEDS_MEDIA_UPLOAD:[^\"'\s<>]+", serialized)))


def env_value(name: str) -> str:
    if not os.environ.get(name) and "PYTEST_CURRENT_TEST" not in os.environ and PRIVATE_ENV_PATH.exists():
        for line in PRIVATE_ENV_PATH.read_text(encoding="utf-8").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip("'\"")
    return str(os.environ.get(name, "") or "").strip()


def content_publish_request(execution_input: dict[str, Any], *, mode: str) -> dict[str, Any]:
    helper_call = safe_dict(execution_input.get("admin_helper_call"))
    helper_input = safe_dict(helper_call.get("input"))
    record = safe_dict(helper_input.get("record"))
    next_status = str(helper_input.get("nextStatus") or record.get("status") or "draft")
    return {
        "contentType": "service",
        "mode": "dry-run" if mode == "dry-run" else "publish",
        "nextStatus": next_status,
        "ownerApproved": mode != "dry-run",
        "explicitExecution": mode != "dry-run",
        "approvalId": f"codex-approved-{dt.date.today().isoformat()}",
        "source": "codex-seo-geo",
        "record": record,
    }


def call_content_publish_api(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    token = env_value(ADMIN_TOKEN_ENV)
    publish_secret = env_value(PUBLISH_SECRET_ENV)
    auth_headers = {"Authorization": f"Bearer {token}"} if token else {"x-cron-secret": publish_secret}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            **auth_headers,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - explicit owner-approved admin API URL
        raw = response.read().decode("utf-8")
        body = json.loads(raw) if raw else {}
        return {"status_code": response.status, "body": body}


def evaluate_gates(
    execution_input: dict[str, Any],
    *,
    mode: str,
    confirm_write: bool,
    allowed_target_urls: list[str],
    require_env: bool,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    helper = str(execution_input.get("admin_helper", "") or "").strip()
    target_url = str(execution_input.get("target_url", "") or "")
    paired_url = str(execution_input.get("paired_url", "") or "")

    if not execution_input:
        blockers.append("Missing publish-approved-execution-input.json. Run publish-approved-execution-input first.")
    if execution_input.get("status") != EXPECTED_INPUT_STATUS:
        blockers.append(f"Execution input is not ready: {execution_input.get('status', 'missing')}.")
    if execution_input.get("action") != EXPECTED_INPUT_ACTION:
        blockers.append("Execution input action is not the expected template action.")
    for blocker in safe_list(execution_input.get("blockers")):
        blockers.append(f"Execution input blocker: {blocker}")
    for warning in safe_list(execution_input.get("warnings")):
        warnings.append(f"Execution input warning: {warning}")
    if helper not in SUPPORTED_HELPERS:
        blockers.append(f"Unsupported CMS helper for live executor: {helper or 'missing'}.")
    if not target_url:
        blockers.append("Target URL is missing.")
    if not paired_url:
        blockers.append("Paired URL is missing; bilingual execution would be incomplete.")
    if allowed_target_urls:
        allowed = {url.rstrip("/") for url in allowed_target_urls}
        if target_url.rstrip("/") not in allowed:
            blockers.append("Target URL is not in --allowed-target-url.")
        if paired_url and paired_url.rstrip("/") not in allowed:
            blockers.append("Paired URL is not in --allowed-target-url.")
    else:
        blockers.append("At least one --allowed-target-url is required.")
    placeholders = find_media_placeholders(execution_input)
    if placeholders:
        blockers.append("Media placeholders remain; resolve uploaded URLs before CMS write: " + ", ".join(placeholders[:10]))
    if mode != "dry-run" and not confirm_write:
        blockers.append("--confirm-write is required for non-dry-run admin publishing.")
    if mode == "live" and env_value(CONFIRM_ENV) != CONFIRM_VALUE:
        blockers.append(f"{CONFIRM_ENV} must equal {CONFIRM_VALUE} for live admin publishing.")
    if require_env or mode != "dry-run":
        if not env_value(PUBLISH_URL_ENV):
            blockers.append(f"Missing {PUBLISH_URL_ENV}; set it to the protected content-publish Edge Function URL.")
        if not env_value(ADMIN_TOKEN_ENV) and not env_value(PUBLISH_SECRET_ENV):
            blockers.append(
                f"Missing {ADMIN_TOKEN_ENV} or {PUBLISH_SECRET_ENV}; set an admin access token or the approved content publish machine secret."
            )
    return unique_strings(blockers), unique_strings(warnings)


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Publish CMS Write Executor",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- Mode: `{summary.get('mode')}`",
        f"- Target URL: `{summary.get('target_url') or 'N/A'}`",
            f"- Paired URL: `{summary.get('paired_url') or 'N/A'}`",
            f"- Admin helper: `{summary.get('admin_helper') or 'N/A'}`",
            f"- CMS write executed: `{summary.get('cms_write_executed')}`",
        "- 执行状态: admin publish API；本工具不直接写数据库",
        "",
        "## 今日决策",
        "",
        "今天把最终发布门禁固定为管理后台发布 API：它读取 approved execution input，检查媒体 URL、业主授权、目标 URL 和确认 token，然后只调用受保护的 content-publish 后台接口。禁止直接写数据库。",
        "",
        "## Blockers",
        "",
    ]
    blockers = safe_list(summary.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = safe_list(summary.get("warnings"))
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## 写入结果",
            "",
            f"- Action: `{safe_dict(summary.get('write_result')).get('action', 'not_executed')}`",
            f"- Saved ID: `{safe_dict(summary.get('write_result')).get('savedId', '')}`",
            f"- Slug: `{safe_dict(summary.get('write_result')).get('slug', '')}`",
            f"- API status: `{safe_dict(summary.get('write_result')).get('status_code', '')}`",
            "",
            "## 安全边界",
            "",
            "- 本工具永远不直接写 Supabase/数据库表。",
            "- 真实发布必须通过网站管理后台 API `content-publish` 或现有 admin service layer，例如 `saveAdminService` / `saveAdminRecord`。",
            f"- live 发布仍必须设置 `{CONFIRM_ENV}={CONFIRM_VALUE}`，但该确认不能授权直接数据库写入。",
            f"- 非 dry-run 必须设置 `{PUBLISH_URL_ENV}`，并提供 `{ADMIN_TOKEN_ENV}` 或 `{PUBLISH_SECRET_ENV}`。",
            "- 媒体占位符未替换时阻断，避免把 NEEDS_MEDIA_UPLOAD 写进线上页面。",
            "- 后台发布后仍需要运行 SEO 生成、QA、receipt verification 和必要部署。",
            "",
            "## Artifacts",
            "",
        ]
    )
    for name, path in safe_dict(summary.get("artifacts")).items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines) + "\n"


def run_publish_cms_write_executor(
    root: Path,
    *,
    execution_input_path: str = "",
    mode: str = "dry-run",
    confirm_write: bool = False,
    allowed_target_urls: list[str] | None = None,
    require_env: bool = False,
) -> tuple[dict[str, Any], tuple[Path, Path]]:
    root = root.resolve()
    input_file = resolve_path(root, execution_input_path or DEFAULT_INPUT)
    execution_input = read_json(input_file)
    allowed = allowed_target_urls or []
    blockers, warnings = evaluate_gates(
        execution_input,
        mode=mode,
        confirm_write=confirm_write,
        allowed_target_urls=allowed,
        require_env=require_env,
    )
    cms_write_executed = False
    api_request = content_publish_request(execution_input, mode=mode) if execution_input else {}
    status = "cms_write_executor_ready_dry_run" if not blockers else "blocked_before_cms_write_execution"
    write_result: dict[str, Any] = {
        "action": "not_executed",
        "required_publish_path": "website_admin_backend",
        "admin_helper": execution_input.get("admin_helper", ""),
        "admin_helper_call": execution_input.get("admin_helper_call", {}),
        "api_request": api_request,
    }
    if mode != "dry-run" and not blockers:
        try:
            api_result = call_content_publish_api(env_value(PUBLISH_URL_ENV), api_request)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            blockers.append(f"Admin content-publish API failed: {type(exc).__name__}: {exc}")
            status = "admin_content_publish_api_failed"
        else:
            body = safe_dict(api_result.get("body"))
            cms_write_executed = bool(body.get("ok"))
            write_result = {
                "action": body.get("action", "publish"),
                "required_publish_path": "website_admin_backend",
                "status_code": api_result.get("status_code"),
                "body": body,
                "slug": body.get("slug", ""),
                "savedId": body.get("saved_id", ""),
            }
            status = "cms_write_executed_waiting_post_write_qa" if cms_write_executed else "admin_content_publish_api_rejected"
    result_path = root / "seo-workspace" / "data" / RESULT_NAME
    api_request_path = root / "seo-workspace" / "data" / "content-publish-api-request.json"
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "mode": mode,
        "execution_input_path": str(input_file),
        "target_url": execution_input.get("target_url", ""),
        "paired_url": execution_input.get("paired_url", ""),
        "admin_helper": execution_input.get("admin_helper", ""),
        "allowed_target_urls": allowed,
        "confirm_write": confirm_write,
        "cms_write_executed": cms_write_executed,
        "content_publish_api_request": api_request,
        "write_result": write_result,
        "blockers": unique_strings(blockers),
        "warnings": unique_strings(warnings),
        "artifacts": {
            "cms_write_result": str(result_path),
            "content_publish_api_request": str(api_request_path),
            "cms_write_report": str(report_path),
        },
        "direct_database_write_disabled": True,
        "required_publish_path": "website_admin_backend",
        "no_cms_write_executed": not cms_write_executed,
        "no_media_upload_executed": True,
        "no_deploy_executed": True,
    }
    write_text(result_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(api_request_path, json.dumps(api_request, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (result_path, api_request_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded CMS write executor for approved Flash Cast content packages.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--execution-input-path", default="")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "staging", "live"])
    parser.add_argument("--confirm-write", action="store_true")
    parser.add_argument("--allowed-target-url", action="append", default=[])
    parser.add_argument("--require-env", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_publish_cms_write_executor(
        Path(args.root),
        execution_input_path=args.execution_input_path,
        mode=args.mode,
        confirm_write=args.confirm_write,
        allowed_target_urls=args.allowed_target_url,
        require_env=args.require_env,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] in {"cms_write_executor_ready_dry_run", "cms_write_executed_waiting_post_write_qa"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
