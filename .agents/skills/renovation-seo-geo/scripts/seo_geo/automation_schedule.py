#!/usr/bin/env python3
"""Generate and validate safe daily SEO/GEO automation schedule plans."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from .config import parse_simple_yaml
    from .scheduled_publish_authorization import run_scheduled_publish_authorization
except ImportError:  # pragma: no cover - direct script execution
    from config import parse_simple_yaml
    from scheduled_publish_authorization import run_scheduled_publish_authorization


SCHEDULE_PLAN_JSON = "daily-automation-schedule-plan.json"
SCHEDULE_REPORT_NAME = "daily-automation-schedule.md"
CRON_EXAMPLE_NAME = "daily-automation.cron.example"
LAUNCHD_EXAMPLE_NAME = "com.flashcast.daily-seo-geo.plist.example"
VALID_PIPELINES = {"brief", "rich-content", "publish-prep"}
VALID_EXECUTORS = {"daily-automation", "content-studio-next"}


@dataclass
class AutomationScheduleResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schedule: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def bool_value(value: object) -> bool:
    return value is True or str(value).strip().lower() == "true"


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def default_schedule(root: Path) -> dict[str, Any]:
    return {
        "automation_id": "flash-cast-daily-seo-geo",
        "enabled": True,
        "timezone": "Asia/Kuala_Lumpur",
        "time_local": "09:00",
        "executor": "daily-automation",
        "pipeline": "brief",
        "owner_review_package": False,
        "target_url": "",
        "topic": "",
        "website_root": "/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main",
        "fetch_research_remote": False,
        "research_search_provider": "hybrid-rss",
        "research_search_feeds_config": "seo-workspace/config/research-search-feeds.example.yml",
        "command_root": str(root),
        "log_path": "seo-workspace/reports/daily-automation.log",
        "publish_enabled": False,
        "max_tasks_per_run": 1,
        "language_scope": "bilingual_pair_required",
        "owner_authorization": {
            "exact_authorization_id": "NEEDS_OWNER_INPUT",
            "owner_approved": False,
            "explicit_execution": False,
            "allowed_pipeline": "brief",
            "allowed_target_paths": [],
            "qa_required": True,
            "backup_required": True,
            "rollback_required": True,
            "media_url_confirmation_required": True,
            "live_confirmation_required": True,
        },
        "safety_gates": {
            "no_cms_login_without_execution": True,
            "no_media_upload_without_execution": True,
            "no_source_write_without_execution": True,
            "no_publish_without_execution": True,
            "no_deploy_without_execution": True,
            "concept_labels_required": True,
            "source_log_required_for_current_facts": True,
        },
    }


def schedule_from_config(root: Path, config_path: Path) -> dict[str, Any]:
    parsed = parse_simple_yaml(config_path)
    schedule = default_schedule(root)
    for key, value in parsed.items():
        if isinstance(value, dict) and isinstance(schedule.get(key), dict):
            schedule[key] = safe_dict(schedule[key]) | value
        else:
            schedule[key] = value
    return schedule


def validate_schedule(schedule: dict[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    pipeline = str_value(schedule.get("pipeline"), "brief")
    executor = str_value(schedule.get("executor"), "daily-automation")
    publish_enabled = bool_value(schedule.get("publish_enabled"))
    authorization = safe_dict(schedule.get("owner_authorization"))
    safety = safe_dict(schedule.get("safety_gates"))

    if executor not in VALID_EXECUTORS:
        blockers.append(f"Unsupported automation executor: {executor}.")
    if pipeline not in VALID_PIPELINES:
        blockers.append(f"Unsupported daily automation pipeline: {pipeline}.")
    if executor == "content-studio-next" and publish_enabled:
        blockers.append("content-studio-next schedules must keep publish_enabled=false; use scheduled-publish gates for publish-prep handoff.")
    if executor == "content-studio-next" and not bool_value(schedule.get("owner_review_package")):
        warnings.append("content-studio-next schedules should set owner_review_package=true to create a complete owner-review handoff after each queued page.")
    if int(schedule.get("max_tasks_per_run") or 0) != 1:
        blockers.append("max_tasks_per_run must be exactly 1 to avoid bulk/spam publishing.")
    if not str_value(schedule.get("timezone")):
        blockers.append("timezone is required.")
    if not str_value(schedule.get("time_local")):
        blockers.append("time_local is required.")
    if str_value(schedule.get("language_scope")) != "bilingual_pair_required":
        warnings.append("language_scope is not bilingual_pair_required; owner must explicitly approve single-language execution.")

    for key in (
        "no_cms_login_without_execution",
        "no_media_upload_without_execution",
        "no_source_write_without_execution",
        "no_publish_without_execution",
        "no_deploy_without_execution",
        "concept_labels_required",
    ):
        if not bool_value(safety.get(key)):
            blockers.append(f"Safety gate must be true: {key}.")

    if publish_enabled:
        if pipeline != "publish-prep":
            blockers.append("publish_enabled schedules must use pipeline publish-prep before any execution handoff.")
        if str_value(authorization.get("exact_authorization_id")).startswith("NEEDS_OWNER_INPUT"):
            blockers.append("publish_enabled requires a real exact_authorization_id from the owner.")
        for key in (
            "owner_approved",
            "explicit_execution",
            "qa_required",
            "backup_required",
            "rollback_required",
            "media_url_confirmation_required",
            "live_confirmation_required",
        ):
            if not bool_value(authorization.get(key)):
                blockers.append(f"publish_enabled requires owner_authorization.{key}=true.")
        if not safe_list(authorization.get("allowed_target_paths")):
            blockers.append("publish_enabled requires non-empty owner_authorization.allowed_target_paths.")
    else:
        if pipeline == "publish-prep":
            warnings.append("publish-prep is handoff-only because publish_enabled is false.")
        if bool_value(authorization.get("owner_approved")) or bool_value(authorization.get("explicit_execution")):
            warnings.append("Owner approval flags are present but publish_enabled is false; this schedule will still not publish.")

    return blockers, warnings


def command_args(schedule: dict[str, Any]) -> list[str]:
    executor = str_value(schedule.get("executor"), "daily-automation")
    if executor == "content-studio-next":
        args = [
            "python3",
            ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py",
            "content-studio-orchestrator",
        ]
        config_path = str_value(schedule.get("_config_path"))
        if config_path:
            args.extend(["--config-path", config_path])
        return args
    args = [
        "python3",
        ".agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py",
        "daily-automation",
        "--pipeline",
        str_value(schedule.get("pipeline"), "brief"),
    ]
    for flag, key in (("--target-url", "target_url"), ("--topic", "topic"), ("--website-root", "website_root")):
        value = str_value(schedule.get(key))
        if value:
            args.extend([flag, value])
    if not bool_value(schedule.get("fetch_research_remote")):
        args.append("--no-fetch-research-remote")
    provider = str_value(schedule.get("research_search_provider"), "google-news-rss")
    if provider:
        args.extend(["--research-search-provider", provider])
    feeds_config = str_value(schedule.get("research_search_feeds_config"))
    if feeds_config:
        args.extend(["--research-search-feeds-config", feeds_config])
    return args


def cron_line(root: Path, schedule: dict[str, Any]) -> str:
    hour, minute = parse_hour_minute(str_value(schedule.get("time_local"), "09:00"))
    log_path = str_value(schedule.get("log_path"), "seo-workspace/reports/daily-automation.log")
    command = " ".join(shell_quote(part) for part in command_args(schedule))
    return f"{minute} {hour} * * * cd {shell_quote(str(root))} && {command} >> {shell_quote(log_path)} 2>&1"


def launchd_plist(root: Path, schedule: dict[str, Any]) -> str:
    hour, minute = parse_hour_minute(str_value(schedule.get("time_local"), "09:00"))
    args = command_args(schedule)
    log_path = root / str_value(schedule.get("log_path"), "seo-workspace/reports/daily-automation.log")
    escaped_args = "\n".join(f"    <string>{xml_escape(arg)}</string>" for arg in args)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.flashcast.daily-seo-geo</string>
  <key>WorkingDirectory</key>
  <string>{xml_escape(str(root))}</string>
  <key>ProgramArguments</key>
  <array>
{escaped_args}
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>{hour}</integer>
    <key>Minute</key>
    <integer>{minute}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{xml_escape(str(log_path))}</string>
  <key>StandardErrorPath</key>
  <string>{xml_escape(str(log_path))}</string>
</dict>
</plist>
"""


def parse_hour_minute(value: str) -> tuple[int, int]:
    hour_text, _, minute_text = value.partition(":")
    hour = int(hour_text or "9")
    minute = int(minute_text or "0")
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError("time_local must be HH:MM in 24-hour format.")
    return hour, minute


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_example_config(root: Path) -> str:
    schedule = default_schedule(root)
    return f"""# Daily SEO/GEO automation schedule example.
# Copy to daily-automation.yml for local owner-approved use.
# This file is safe by default: it schedules draft/prep output only.

automation_id: "{schedule['automation_id']}"
enabled: true
timezone: "Asia/Kuala_Lumpur"
time_local: "09:00"
executor: "daily-automation"
pipeline: "brief"
owner_review_package: false
fetch_research_remote: false
research_search_provider: "hybrid-rss"
research_search_feeds_config: "seo-workspace/config/research-search-feeds.example.yml"
target_url: ""
topic: ""
website_root: "{schedule['website_root']}"
command_root: "{schedule['command_root']}"
log_path: "seo-workspace/reports/daily-automation.log"
publish_enabled: false
max_tasks_per_run: 1
language_scope: "bilingual_pair_required"

owner_authorization:
  exact_authorization_id: "NEEDS_OWNER_INPUT"
  owner_approved: false
  explicit_execution: false
  allowed_pipeline: "brief"
  allowed_target_paths:
  qa_required: true
  backup_required: true
  rollback_required: true
  media_url_confirmation_required: true
  live_confirmation_required: true

safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
  source_log_required_for_current_facts: true
"""


def render_report(result: AutomationScheduleResult) -> str:
    schedule = result.schedule
    lines = [
        "# Daily SEO/GEO Automation Schedule Plan",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Automation ID: `{schedule.get('automation_id', 'N/A')}`",
        f"- Executor: `{schedule.get('executor', 'daily-automation')}`",
        f"- Pipeline: `{schedule.get('pipeline', 'N/A')}`",
        f"- Time: `{schedule.get('time_local', 'N/A')}` `{schedule.get('timezone', 'N/A')}`",
        f"- Publish enabled: `{schedule.get('publish_enabled', False)}`",
        "- 执行状态: schedule-plan-only；未安装 cron/launchd，未执行自动化，未发布",
        "",
        "## 今日决策",
        "",
        "今天把 daily SEO/GEO 自动化升级为可审核的固定时间调度计划：生成安全配置、cron 示例、launchd 示例和授权校验。默认只允许 draft/prep-only，不允许无人值守发布。",
        "",
        "## Command Preview",
        "",
        f"```bash\ncd {shell_quote(str(schedule.get('command_root', '')))} && {' '.join(shell_quote(part) for part in command_args(schedule))}\n```",
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
            "## Safety Notes",
            "",
            "- 本计划不会安装系统定时任务；业主需要审核后自行或明确要求 Codex 安装。",
            "- `executor: content-studio-next` 可用于每天固定消费一个整站内容队列项，并写入 history。",
            "- `owner_review_package: true` 会让 content-studio-next 定时运行后继续生成候选发布队列、publish-prep、审批包和媒体 URL 模板，仍然不发布。",
            "- `publish_enabled: false` 时，任何 pipeline 都不会自动发布。",
            "- 若未来启用发布，必须补齐 exact authorization、QA、backup、rollback、media URL confirmation、allowed target paths 和 live confirmation。",
            "- 每次运行仍限制 `max_tasks_per_run: 1`，避免批量低质内容或 doorway 页面。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def run_automation_schedule(
    root: Path,
    *,
    config_path: str = "",
    authorization_profile_path: str = "",
    write_example: bool = True,
) -> tuple[AutomationScheduleResult, tuple[Path, Path, Path, Path, Path]]:
    root = root.resolve()
    config_dir = root / "seo-workspace" / "config"
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    example_path = config_dir / "daily-automation.example.yml"
    schedule_path = Path(config_path) if config_path else example_path
    if not schedule_path.is_absolute():
        schedule_path = root / schedule_path
    if write_example:
        write_text(example_path, render_example_config(root))

    schedule = schedule_from_config(root, schedule_path)
    schedule["_config_path"] = str(schedule_path)
    blockers: list[str] = []
    warnings: list[str] = []
    authorization_result = None
    authorization_artifacts: tuple[Path, Path, Path] = ()
    try:
        blockers, warnings = validate_schedule(schedule)
        cron = cron_line(root, schedule)
        plist = launchd_plist(root, schedule)
    except Exception as exc:  # noqa: BLE001 - report config errors as blockers
        blockers = [f"Schedule config parse/validation failed: {type(exc).__name__}: {exc}"]
        cron = ""
        plist = ""
    try:
        authorization_result, authorization_artifacts = run_scheduled_publish_authorization(
            root,
            profile_path=authorization_profile_path,
            write_example=write_example,
        )
    except Exception as exc:  # noqa: BLE001 - authorization gate should be visible in the schedule report
        blockers.append(f"Scheduled publish authorization check failed: {type(exc).__name__}: {exc}")
    else:
        publish_enabled = bool_value(schedule.get("publish_enabled"))
        if publish_enabled and not authorization_result.ok:
            blockers.append(
                "publish_enabled is true, but scheduled publish authorization is not ready. "
                "See scheduled-publish-authorization.json."
            )
        elif not authorization_result.ok:
            warnings.append("Scheduled publishing remains blocked until scheduled-publish-authorization.yml is completed.")
        if authorization_result.warnings:
            warnings.extend(f"Scheduled publish authorization warning: {item}" for item in authorization_result.warnings)
    status = "schedule_plan_ready_for_owner_review" if not blockers else "schedule_plan_blocked"
    result = AutomationScheduleResult(status=status, blockers=blockers, warnings=warnings, schedule=schedule)

    plan_path = data_dir / SCHEDULE_PLAN_JSON
    cron_path = config_dir / CRON_EXAMPLE_NAME
    launchd_path = config_dir / LAUNCHD_EXAMPLE_NAME
    report_path = reports_dir / f"{today}-{SCHEDULE_REPORT_NAME}"
    result.artifacts.update(
        {
            "example_config": str(example_path),
            "schedule_plan": str(plan_path),
            "cron_example": str(cron_path),
            "launchd_example": str(launchd_path),
            "report": str(report_path),
        }
    )
    if authorization_artifacts:
        authorization_example_path, authorization_json_path, authorization_report_path = authorization_artifacts
        result.artifacts.update(
            {
                "scheduled_publish_authorization_example": str(authorization_example_path),
                "scheduled_publish_authorization_json": str(authorization_json_path),
                "scheduled_publish_authorization_report": str(authorization_report_path),
            }
        )
    write_text(cron_path, cron + "\n")
    write_text(launchd_path, plist)
    write_text(
        plan_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "schedule": result.schedule,
                "command_args": command_args(schedule),
                "cron_example": cron,
                "launchd_example_path": str(launchd_path),
                "scheduled_publish_authorization_status": authorization_result.status if authorization_result else "not_checked",
                "no_schedule_installed": True,
                "no_live_actions_executed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return result, (example_path, plan_path, cron_path, launchd_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate/validate daily SEO/GEO automation schedule plan.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--config-path", default="", help="Optional schedule config path.")
    parser.add_argument("--authorization-profile-path", default="", help="Optional scheduled publish authorization profile path.")
    parser.add_argument("--no-write-example", action="store_true", help="Do not rewrite daily-automation.example.yml.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_automation_schedule(
        Path(args.root),
        config_path=args.config_path,
        authorization_profile_path=args.authorization_profile_path,
        write_example=not args.no_write_example,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
