#!/usr/bin/env python3
"""Create a scheduled publish run request without executing automation or writes."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    from .scheduled_publish_authorization import run_scheduled_publish_authorization
except ImportError:  # pragma: no cover - direct script execution
    from scheduled_publish_authorization import run_scheduled_publish_authorization


RUN_REQUEST_JSON_NAME = "scheduled-publish-run-request.json"
RUN_LOG_CSV_NAME = "scheduled-publish-run-log.csv"
RUN_REPORT_NAME = "scheduled-publish-run-request.md"
RUN_ACTION = "scheduled_publish_run_request_only_no_execute"
READY_STATUS = "scheduled_publish_run_request_ready"
BLOCKED_STATUS = "blocked_before_scheduled_publish_run"


@dataclass
class ScheduledPublishRunnerResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    run_request: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def parse_hour_minute(value: str) -> tuple[int, int]:
    hour_text, _, minute_text = value.partition(":")
    hour = int(hour_text or "0")
    minute = int(minute_text or "0")
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("local_time must be HH:MM in 24-hour format.")
    return hour, minute


def parse_now(value: str) -> dt.datetime:
    if not value:
        return dt.datetime.now(dt.timezone.utc)
    normalized = value.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def expected_pair_url(url: str) -> str:
    if "/en/" in url:
        return url.replace("/en/", "/zh/", 1)
    if "/zh/" in url:
        return url.replace("/zh/", "/en/", 1)
    return ""


def choose_target_url(profile: dict[str, Any], requested_target_url: str, blockers: list[str]) -> tuple[str, str]:
    allowed_urls = [str_value(url).rstrip("/") for url in safe_list(profile.get("allowed_target_urls")) if str_value(url)]
    if not allowed_urls:
        blockers.append("No allowed target URLs in scheduled publish authorization profile.")
        return "", ""
    requested = requested_target_url.rstrip("/")
    if requested:
        if requested not in allowed_urls:
            blockers.append("Requested target URL is not included in allowed_target_urls.")
            return requested, expected_pair_url(requested)
        target_url = requested
    else:
        target_url = next((url for url in allowed_urls if "/en/" in url), allowed_urls[0])
    paired_url = expected_pair_url(target_url).rstrip("/")
    if str_value(profile.get("language_scope")) == "bilingual_pair_required" and paired_url not in allowed_urls:
        blockers.append("Selected target URL does not have its paired /en or /zh URL in allowed_target_urls.")
    return target_url, paired_url


def evaluate_schedule_window(
    *,
    profile: dict[str, Any],
    now_value: str,
    window_minutes: int,
    ignore_schedule_window: bool,
) -> tuple[list[str], list[str], dict[str, Any]]:
    blockers: list[str] = []
    warnings: list[str] = []
    timezone_name = str_value(profile.get("timezone"))
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        blockers.append(f"Unsupported timezone in authorization profile: {timezone_name}.")
        timezone = dt.timezone.utc
    try:
        now_utc = parse_now(now_value)
    except Exception as exc:  # noqa: BLE001 - invalid operator input should be a blocker
        blockers.append(f"Invalid --now value: {type(exc).__name__}: {exc}")
        now_utc = dt.datetime.now(dt.timezone.utc)
    local_now = now_utc.astimezone(timezone)
    weekday = local_now.strftime("%a")
    allowed_weekdays = [str_value(item) for item in safe_list(profile.get("allowed_weekdays")) if str_value(item)]
    if weekday not in allowed_weekdays:
        blockers.append(f"Current local weekday {weekday} is not allowed by scheduled publish authorization.")
    try:
        hour, minute = parse_hour_minute(str_value(profile.get("local_time")))
        scheduled_local = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        delta_minutes = abs((local_now - scheduled_local).total_seconds()) / 60
        inside_window = delta_minutes <= window_minutes
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"Unable to evaluate local_time window: {type(exc).__name__}: {exc}")
        scheduled_local = local_now
        delta_minutes = 0
        inside_window = False
    if not inside_window:
        message = (
            f"Current local time {local_now.strftime('%H:%M')} is outside the authorized "
            f"{window_minutes}-minute window around {str_value(profile.get('local_time'))}."
        )
        if ignore_schedule_window:
            warnings.append(message)
        else:
            blockers.append(message)
    return blockers, warnings, {
        "now_utc": now_utc.astimezone(dt.timezone.utc).isoformat(timespec="seconds"),
        "local_now": local_now.isoformat(timespec="seconds"),
        "local_date": local_now.date().isoformat(),
        "local_weekday": weekday,
        "scheduled_local": scheduled_local.isoformat(timespec="seconds"),
        "window_minutes": window_minutes,
        "inside_window": inside_window,
        "ignore_schedule_window": ignore_schedule_window,
    }


def read_run_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def append_run_log(path: Path, request: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    fields = ["generated_at", "local_date", "target_url", "paired_url", "status", "action"]
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({field: str_value(request.get(field)) for field in fields})


def duplicate_ready_run_exists(rows: list[dict[str, str]], *, local_date: str, target_url: str) -> bool:
    normalized_target = target_url.rstrip("/")
    for row in rows:
        if row.get("local_date") == local_date and row.get("target_url", "").rstrip("/") == normalized_target and row.get("status") == READY_STATUS:
            return True
    return False


def build_daily_automation_command(profile: dict[str, Any], target_url: str, profile_path: str) -> list[str]:
    command = [
        "python3",
        ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py",
        "daily-automation",
        "--pipeline",
        "publish-prep",
        "--target-url",
        target_url,
    ]
    website_root = str_value(profile.get("website_root"))
    if website_root:
        command.extend(["--website-root", website_root])
    if profile_path:
        command.extend(["--authorization-profile-path", profile_path])
    return command


def build_followup_commands(target_url: str, paired_url: str) -> list[list[str]]:
    commands = [
        [
            "python3",
            ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py",
            "qa",
            "--target-url",
            target_url,
        ]
    ]
    if paired_url:
        commands.append(
            [
                "python3",
                ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py",
                "qa",
                "--target-url",
                paired_url,
            ]
        )
    commands.extend(
        [
            ["python3", ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py", "publish-readiness"],
            ["python3", ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py", "publish-bundle"],
            ["python3", ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py", "publish-approved-executor", "--owner-approved", "--explicit-execution", "--qa-passed"],
            ["python3", ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py", "publish-implementation-package"],
            ["python3", ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py", "publish-operator-package"],
            ["python3", ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py", "publish-execution-receipt"],
        ]
    )
    return commands


def build_run_request(
    *,
    status: str,
    blockers: list[str],
    warnings: list[str],
    authorization_payload: dict[str, Any],
    target_url: str,
    paired_url: str,
    schedule_window: dict[str, Any],
    profile_path: str,
) -> dict[str, Any]:
    profile = safe_dict(authorization_payload.get("profile"))
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": RUN_ACTION,
        "status": status,
        "run_allowed_for_scheduler": status == READY_STATUS,
        "authorization_status": authorization_payload.get("status", ""),
        "authorization_ready_for_scheduled_publish": authorization_payload.get("authorization_ready_for_scheduled_publish", False),
        "target_url": target_url,
        "paired_url": paired_url,
        "local_date": schedule_window.get("local_date", ""),
        "local_weekday": schedule_window.get("local_weekday", ""),
        "schedule_window": schedule_window,
        "daily_automation_command": build_daily_automation_command(profile, target_url, profile_path) if target_url else [],
        "required_followup_commands": build_followup_commands(target_url, paired_url) if target_url else [],
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
        "safety_note": "This run request is a scheduler gate artifact only. It does not run daily automation, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy.",
    }


def command_string(parts: list[str]) -> str:
    return " ".join(parts)


def render_report(result: ScheduledPublishRunnerResult) -> str:
    request = result.run_request
    lines = [
        "# Scheduled Publish Run Request",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{request.get('target_url', 'N/A')}`",
        f"- Paired URL: `{request.get('paired_url', 'N/A')}`",
        f"- Local date: `{request.get('local_date', 'N/A')}`",
        f"- Authorization status: `{request.get('authorization_status', 'N/A')}`",
        "- 执行状态: run-request-only；未安装定时任务、未运行 daily automation、未登录 CMS、未上传媒体、未写页面、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天新增固定时间发布的运行请求层：它判断当前时间、授权 profile、目标 URL 和重复运行风险，只生成本次可执行请求或阻断原因，不触发真实发布。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Daily Automation Command Preview", ""])
    daily_command = request.get("daily_automation_command")
    if isinstance(daily_command, list) and daily_command:
        lines.append(f"```bash\n{command_string([str(item) for item in daily_command])}\n```")
    else:
        lines.append("- None")
    lines.extend(["", "## Required Follow-up Commands", ""])
    for command in safe_list(request.get("required_followup_commands")):
        if isinstance(command, list):
            lines.append(f"- `{command_string([str(item) for item in command])}`")
    if not safe_list(request.get("required_followup_commands")):
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 本产物只适合给 cron/launchd 或未来调度器读取，表示本次是否应该进入 daily publish-prep。",
            "- 即使 run request ready，后续仍必须经过 QA、publish-readiness、publish-bundle、approved executor 和 implementation package。",
            "- 本模块不调用 CMS、不上传媒体、不发布、不重生成 SEO assets、不部署。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def run_scheduled_publish_runner(
    root: Path,
    *,
    profile_path: str = "",
    target_url: str = "",
    now: str = "",
    window_minutes: int = 20,
    ignore_schedule_window: bool = False,
    allow_duplicate_run: bool = False,
    write_example: bool = True,
) -> tuple[ScheduledPublishRunnerResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()

    authorization_result, _ = run_scheduled_publish_authorization(root, profile_path=profile_path, write_example=write_example)
    authorization_payload = authorization_result.authorization
    profile = safe_dict(authorization_payload.get("profile"))
    blockers = list(authorization_result.blockers)
    warnings = list(authorization_result.warnings)
    selected_target_url, paired_url = choose_target_url(profile, target_url, blockers)
    schedule_blockers, schedule_warnings, schedule_window = evaluate_schedule_window(
        profile=profile,
        now_value=now,
        window_minutes=window_minutes,
        ignore_schedule_window=ignore_schedule_window,
    )
    blockers.extend(schedule_blockers)
    warnings.extend(schedule_warnings)

    log_path = data_dir / RUN_LOG_CSV_NAME
    if selected_target_url and not allow_duplicate_run:
        if duplicate_ready_run_exists(read_run_log(log_path), local_date=str_value(schedule_window.get("local_date")), target_url=selected_target_url):
            blockers.append("A ready scheduled publish run request already exists for this local date and target URL.")
    elif allow_duplicate_run:
        warnings.append("Duplicate scheduled publish run protection was bypassed by operator flag.")

    status = READY_STATUS if not blockers else BLOCKED_STATUS
    run_request = build_run_request(
        status=status,
        blockers=blockers,
        warnings=warnings,
        authorization_payload=authorization_payload,
        target_url=selected_target_url,
        paired_url=paired_url,
        schedule_window=schedule_window,
        profile_path=profile_path,
    )
    json_path = data_dir / RUN_REQUEST_JSON_NAME
    report_path = reports_dir / f"{today}-{RUN_REPORT_NAME}"
    result = ScheduledPublishRunnerResult(status=status, blockers=blockers, warnings=warnings, run_request=run_request)
    result.artifacts.update(
        {
            "run_request_json": str(json_path),
            "run_log": str(log_path),
            "report": str(report_path),
        }
    )
    run_request["artifacts"] = result.artifacts
    write_text(
        json_path,
        json.dumps(
            {
                "status": result.status,
                "run_request": run_request,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "no_live_actions_executed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    if result.ok:
        append_run_log(log_path, run_request)
    elif not log_path.exists():
        write_text(log_path, "generated_at,local_date,target_url,paired_url,status,action\n")
    write_text(report_path, render_report(result))
    return result, (json_path, log_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a scheduled publish run request without executing automation or writes.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--profile-path", default="", help="Optional scheduled publish authorization profile path.")
    parser.add_argument("--target-url", default="", help="Optional target URL override; must be allowed by authorization profile.")
    parser.add_argument("--now", default="", help="Optional ISO timestamp for deterministic scheduler checks.")
    parser.add_argument("--window-minutes", type=int, default=20, help="Allowed local-time window around configured local_time.")
    parser.add_argument("--ignore-schedule-window", action="store_true", help="Generate request even when current time is outside the window.")
    parser.add_argument("--allow-duplicate-run", action="store_true", help="Allow another ready request for the same local date and target URL.")
    parser.add_argument("--no-write-example", action="store_true", help="Do not rewrite authorization example profile.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_scheduled_publish_runner(
        Path(args.root),
        profile_path=args.profile_path,
        target_url=args.target_url,
        now=args.now,
        window_minutes=args.window_minutes,
        ignore_schedule_window=args.ignore_schedule_window,
        allow_duplicate_run=args.allow_duplicate_run,
        write_example=not args.no_write_example,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
