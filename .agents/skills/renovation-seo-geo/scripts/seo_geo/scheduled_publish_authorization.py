#!/usr/bin/env python3
"""Validate a scheduled publishing authorization profile without executing writes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from .config import parse_simple_yaml
except ImportError:  # pragma: no cover - direct script execution
    from config import parse_simple_yaml


AUTHORIZATION_JSON_NAME = "scheduled-publish-authorization.json"
AUTHORIZATION_REPORT_NAME = "scheduled-publish-authorization.md"
AUTHORIZATION_EXAMPLE_NAME = "scheduled-publish-authorization.example.yml"
DEFAULT_PROFILE_NAME = "scheduled-publish-authorization.yml"
VALID_PIPELINES = {"publish-prep"}
VALID_MODES = {"dry-run", "pr", "staging", "live"}
VALID_WEEKDAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
LIVE_CONFIRM_PHRASE = "CONFIRM LIVE SCHEDULED PUBLISH"
REQUIRED_TRUE_FLAGS = (
    "require_owner_approved",
    "require_explicit_execution",
    "require_qa_passed",
    "require_media_ready",
    "require_storage_ready",
    "require_backup",
    "require_changelog",
    "require_rollback",
)
SAFETY_GATES = (
    "no_cms_login_without_execution",
    "no_media_upload_without_execution",
    "no_source_write_without_execution",
    "no_publish_without_execution",
    "no_deploy_without_execution",
    "concept_labels_required",
)


@dataclass
class ScheduledPublishAuthorizationResult:
    status: str
    profile_path: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    authorization: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def bool_value(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"true", "yes", "1"}


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def is_placeholder(value: object) -> bool:
    text = str_value(value)
    return not text or text.startswith("NEEDS_OWNER_INPUT")


def parse_hour_minute(value: str) -> tuple[int, int]:
    hour_text, _, minute_text = value.partition(":")
    hour = int(hour_text or "9")
    minute = int(minute_text or "0")
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("local_time must be HH:MM in 24-hour format.")
    return hour, minute


def default_profile(root: Path) -> dict[str, Any]:
    return {
        "automation_id": "flash-cast-daily-seo-geo",
        "enabled": False,
        "authorization_profile_id": "NEEDS_OWNER_INPUT",
        "owner_authorization_id": "NEEDS_OWNER_INPUT",
        "authorized_pipeline": "publish-prep",
        "mode": "dry-run",
        "timezone": "Asia/Kuala_Lumpur",
        "local_time": "09:00",
        "allowed_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        "allowed_target_urls": [],
        "website_root": "/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main",
        "max_pages_per_run": 1,
        "language_scope": "bilingual_pair_required",
        "expires_at": "NEEDS_OWNER_INPUT",
        "require_owner_approved": True,
        "require_explicit_execution": True,
        "require_qa_passed": True,
        "require_media_ready": True,
        "require_storage_ready": True,
        "require_backup": True,
        "require_changelog": True,
        "require_rollback": True,
        "require_confirm_live": False,
        "confirm_live_phrase": "",
        "safety_gates": {
            "no_cms_login_without_execution": True,
            "no_media_upload_without_execution": True,
            "no_source_write_without_execution": True,
            "no_publish_without_execution": True,
            "no_deploy_without_execution": True,
            "concept_labels_required": True,
        },
        "command_root": str(root),
    }


def merge_profile(defaults: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    profile = dict(defaults)
    for key, value in raw.items():
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            profile[key] = safe_dict(profile[key]) | value
        else:
            profile[key] = value
    return profile


def load_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return parse_simple_yaml(path)


def render_example_profile(root: Path) -> str:
    profile = default_profile(root)
    return f"""# Scheduled publishing authorization profile example.
# Copy to {DEFAULT_PROFILE_NAME} only after the owner approves an exact recurring publish scope.
# This file is blocked by default and never publishes by itself.

automation_id: "{profile['automation_id']}"
enabled: false
authorization_profile_id: "NEEDS_OWNER_INPUT"
owner_authorization_id: "NEEDS_OWNER_INPUT"
authorized_pipeline: "publish-prep"
mode: "dry-run"
timezone: "Asia/Kuala_Lumpur"
local_time: "09:00"
allowed_weekdays:
  - "Mon"
  - "Tue"
  - "Wed"
  - "Thu"
  - "Fri"
allowed_target_urls:
  - "https://flashcast.com.my/en/services/kitchen"
  - "https://flashcast.com.my/zh/services/kitchen"
website_root: "{profile['website_root']}"
max_pages_per_run: 1
language_scope: "bilingual_pair_required"
expires_at: "NEEDS_OWNER_INPUT"

require_owner_approved: true
require_explicit_execution: true
require_qa_passed: true
require_media_ready: true
require_storage_ready: true
require_backup: true
require_changelog: true
require_rollback: true
require_confirm_live: false
confirm_live_phrase: ""

safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
"""


def has_bilingual_pair(urls: list[object]) -> bool:
    values = [str_value(url).rstrip("/") for url in urls]
    has_en = any("/en/" in value or value.endswith("/en") for value in values)
    has_zh = any("/zh/" in value or value.endswith("/zh") for value in values)
    return has_en and has_zh


def validate_expiry(value: object, blockers: list[str]) -> None:
    if is_placeholder(value):
        blockers.append("expires_at must be a real ISO date from the owner.")
        return
    try:
        expires_at = dt.date.fromisoformat(str_value(value))
    except ValueError:
        blockers.append("expires_at must use YYYY-MM-DD format.")
        return
    if expires_at < dt.date.today():
        blockers.append(f"expires_at is already past: {expires_at.isoformat()}.")


def validate_profile(profile: dict[str, Any], *, profile_present: bool, root: Path) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    if not profile_present:
        blockers.append(
            f"Scheduled publish authorization profile missing. Copy {AUTHORIZATION_EXAMPLE_NAME} to {DEFAULT_PROFILE_NAME} and fill owner-approved values."
        )
    if not bool_value(profile.get("enabled")):
        blockers.append("enabled must be true for scheduled publishing authorization.")
    if str_value(profile.get("automation_id")) != "flash-cast-daily-seo-geo":
        blockers.append("automation_id must be flash-cast-daily-seo-geo.")
    if is_placeholder(profile.get("authorization_profile_id")):
        blockers.append("authorization_profile_id must be a real owner-approved ID.")
    if is_placeholder(profile.get("owner_authorization_id")):
        blockers.append("owner_authorization_id must be a real owner authorization ID.")
    if str_value(profile.get("authorized_pipeline")) not in VALID_PIPELINES:
        blockers.append("authorized_pipeline must be publish-prep for scheduled publishing.")

    mode = str_value(profile.get("mode"), "dry-run")
    if mode not in VALID_MODES:
        blockers.append(f"Unsupported mode: {mode}.")
    try:
        max_pages_per_run = int(profile.get("max_pages_per_run") or 0)
    except (TypeError, ValueError):
        max_pages_per_run = 0
        blockers.append("max_pages_per_run must be a number.")
    if max_pages_per_run != 1:
        blockers.append("max_pages_per_run must be exactly 1.")

    if not str_value(profile.get("timezone")):
        blockers.append("timezone is required.")
    try:
        parse_hour_minute(str_value(profile.get("local_time"), ""))
    except Exception as exc:  # noqa: BLE001 - report config issues as blockers
        blockers.append(f"local_time is invalid: {exc}")

    weekdays = safe_list(profile.get("allowed_weekdays"))
    if not weekdays:
        blockers.append("allowed_weekdays must not be empty.")
    invalid_weekdays = [str_value(day) for day in weekdays if str_value(day) not in VALID_WEEKDAYS]
    if invalid_weekdays:
        blockers.append(f"allowed_weekdays contains unsupported values: {', '.join(invalid_weekdays)}.")

    target_urls = safe_list(profile.get("allowed_target_urls"))
    if not target_urls:
        blockers.append("allowed_target_urls must not be empty.")
    if str_value(profile.get("language_scope")) == "bilingual_pair_required" and target_urls and not has_bilingual_pair(target_urls):
        blockers.append("language_scope is bilingual_pair_required, so allowed_target_urls must include both /en and /zh page URLs.")
    if str_value(profile.get("language_scope")) != "bilingual_pair_required":
        warnings.append("language_scope is not bilingual_pair_required; single-language scheduled publishing needs explicit owner scope.")

    website_root = str_value(profile.get("website_root"))
    if not website_root:
        blockers.append("website_root is required for scheduled publish-prep authorization.")
    elif not resolve_path(root, website_root).exists():
        blockers.append(f"website_root does not exist: {resolve_path(root, website_root)}")

    validate_expiry(profile.get("expires_at"), blockers)

    for key in REQUIRED_TRUE_FLAGS:
        if not bool_value(profile.get(key)):
            blockers.append(f"{key} must be true.")

    if mode == "live":
        if not bool_value(profile.get("require_confirm_live")):
            blockers.append("live mode requires require_confirm_live=true.")
        if str_value(profile.get("confirm_live_phrase")) != LIVE_CONFIRM_PHRASE:
            blockers.append(f"live mode requires confirm_live_phrase to equal {LIVE_CONFIRM_PHRASE}.")
    elif bool_value(profile.get("require_confirm_live")):
        warnings.append("require_confirm_live is true for a non-live mode; this is safe but stricter than required.")

    safety = safe_dict(profile.get("safety_gates"))
    for key in SAFETY_GATES:
        if not bool_value(safety.get(key)):
            blockers.append(f"safety_gates.{key} must be true.")

    return blockers, warnings


def runtime_flags(profile: dict[str, Any]) -> list[str]:
    flags = [
        "--pipeline publish-prep",
        "--target-url <one of allowed_target_urls>",
        "--website-root <authorized website_root>",
        "--owner-approved",
        "--explicit-execution",
        "--qa-passed",
        "--media-ready",
        "--storage-ready",
        "--backup-path <verified backup>",
        "--changelog-path <reviewed changelog>",
        "--rollback-plan-path <reviewed rollback plan>",
    ]
    if str_value(profile.get("mode")) == "live":
        flags.append("--confirm-live")
    return flags


def allowed_daily_commands(profile: dict[str, Any]) -> list[str]:
    website_root = str_value(profile.get("website_root"))
    commands: list[str] = []
    for url in safe_list(profile.get("allowed_target_urls"))[:10]:
        target_url = str_value(url)
        if not target_url:
            continue
        command = [
            "python3",
            ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py",
            "daily-automation",
            "--pipeline",
            "publish-prep",
            "--target-url",
            target_url,
        ]
        if website_root:
            command.extend(["--website-root", website_root])
        commands.append(" ".join(command))
    return commands


def build_authorization(
    *,
    profile: dict[str, Any],
    profile_present: bool,
    profile_path: Path,
    blockers: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    status = "scheduled_publish_authorization_ready" if not blockers else "blocked_before_scheduled_publish_authorization"
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "authorization_ready_for_scheduled_publish": not blockers,
        "profile_present": profile_present,
        "profile_path": str(profile_path),
        "profile": profile,
        "required_runtime_flags": runtime_flags(profile),
        "allowed_daily_automation_commands": allowed_daily_commands(profile),
        "blockers": blockers,
        "warnings": warnings,
        "no_schedule_installed": True,
        "no_daily_automation_executed": True,
        "no_cms_login_executed": True,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "safety_note": "This authorization check writes local audit artifacts only. It does not run daily automation, install schedules, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy.",
    }


def render_report(result: ScheduledPublishAuthorizationResult) -> str:
    authorization = result.authorization
    profile = safe_dict(authorization.get("profile"))
    lines = [
        "# Scheduled Publish Authorization",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Profile path: `{result.profile_path}`",
        f"- Automation ID: `{profile.get('automation_id', 'N/A')}`",
        f"- Mode: `{profile.get('mode', 'N/A')}`",
        f"- Pipeline: `{profile.get('authorized_pipeline', 'N/A')}`",
        f"- Time: `{profile.get('local_time', 'N/A')}` `{profile.get('timezone', 'N/A')}`",
        f"- Max pages per run: `{profile.get('max_pages_per_run', 'N/A')}`",
        "- 执行状态: authorization-check-only；未安装定时任务、未运行 daily automation、未登录 CMS、未上传媒体、未写页面、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把固定时间发布升级为独立授权 profile 校验：只有业主给出精确授权 ID、目标 URL、双语范围、QA/媒体/备份/变更日志/回滚要求，并且 profile 未过期时，未来定时发布门禁才会放行。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Required Runtime Flags", ""])
    flags = safe_list(authorization.get("required_runtime_flags"))
    if flags:
        lines.extend(f"- `{item}`" for item in flags)
    else:
        lines.append("- None")
    lines.extend(["", "## Allowed Daily Automation Commands", ""])
    commands = safe_list(authorization.get("allowed_daily_automation_commands"))
    if commands:
        for command in commands:
            lines.append(f"- `{command}`")
    else:
        lines.append("- None until allowed_target_urls are authorized.")
    lines.extend(
        [
            "",
            "## Owner Review Notes",
            "",
            "- 此 profile 不是发布动作；它只决定未来固定时间发布准备流程是否可进入下一层门禁。",
            "- 即使 profile ready，真实写入仍必须经过 publish-readiness、publish-bundle、publish-approved-executor、publish-implementation-package、publish-operator-package、publish-execution-receipt 和网站 adapter。",
            "- `live` 模式必须额外提供精确 live confirmation、备份、变更日志和回滚证据。",
            "- 单次运行仍必须限制为一个页面任务，避免批量低质内容或 doorway 页面。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def run_scheduled_publish_authorization(
    root: Path,
    *,
    profile_path: str = "",
    write_example: bool = True,
) -> tuple[ScheduledPublishAuthorizationResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    config_dir = root / "seo-workspace" / "config"
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()

    example_path = config_dir / AUTHORIZATION_EXAMPLE_NAME
    resolved_profile_path = Path(profile_path) if profile_path else config_dir / DEFAULT_PROFILE_NAME
    if not resolved_profile_path.is_absolute():
        resolved_profile_path = root / resolved_profile_path
    if write_example:
        write_text(example_path, render_example_profile(root))

    profile_present = resolved_profile_path.exists()
    parse_blockers: list[str] = []
    parse_warnings: list[str] = []
    try:
        raw_profile = load_profile(resolved_profile_path)
    except Exception as exc:  # noqa: BLE001 - report malformed owner config as a validation blocker
        raw_profile = {}
        parse_blockers.append(f"Scheduled publish authorization profile parse failed: {type(exc).__name__}: {exc}")
    profile = merge_profile(default_profile(root), raw_profile) if profile_present else default_profile(root)
    try:
        blockers, warnings = validate_profile(profile, profile_present=profile_present, root=root)
    except Exception as exc:  # noqa: BLE001 - keep the CLI from crashing on malformed profile values
        blockers = [f"Scheduled publish authorization validation failed: {type(exc).__name__}: {exc}"]
        warnings = []
    blockers = parse_blockers + blockers
    warnings = parse_warnings + warnings
    authorization = build_authorization(
        profile=profile,
        profile_present=profile_present,
        profile_path=resolved_profile_path,
        blockers=blockers,
        warnings=warnings,
    )
    status = str_value(authorization.get("status"))
    result = ScheduledPublishAuthorizationResult(
        status=status,
        profile_path=str(resolved_profile_path),
        blockers=blockers,
        warnings=warnings,
        authorization=authorization,
    )

    json_path = data_dir / AUTHORIZATION_JSON_NAME
    report_path = reports_dir / f"{today}-{AUTHORIZATION_REPORT_NAME}"
    result.artifacts.update(
        {
            "example_profile": str(example_path),
            "authorization_json": str(json_path),
            "report": str(report_path),
        }
    )
    authorization["artifacts"] = result.artifacts
    write_text(
        json_path,
        json.dumps(
            {
                "status": result.status,
                "authorization": authorization,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "no_live_actions_executed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return result, (example_path, json_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate scheduled publish authorization profile without executing writes.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--profile-path", default="", help="Optional scheduled publish authorization profile path.")
    parser.add_argument("--no-write-example", action="store_true", help="Do not rewrite the example authorization profile.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_scheduled_publish_authorization(
        Path(args.root),
        profile_path=args.profile_path,
        write_example=not args.no_write_example,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
