#!/usr/bin/env python3
"""Create a no-install handoff package for fixed-time SEO/GEO automation."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:  # pragma: no cover - direct CLI imports differ from tests
    from .automation_schedule import command_args, parse_hour_minute, shell_quote, xml_escape
except ImportError:  # pragma: no cover
    from automation_schedule import command_args, parse_hour_minute, shell_quote, xml_escape


DEFAULT_SCHEDULE_PLAN = "seo-workspace/data/daily-automation-schedule-plan.json"
SUMMARY_NAME = "automation-install-plan.json"
REPORT_NAME = "automation-install-plan.md"
WRAPPER_NAME = "run-daily-seo-geo.sh"
PLIST_NAME = "com.flashcast.daily-seo-geo.plist"
CRON_NAME = "daily-automation.install.cron"
LAUNCHD_LOG_PATH = Path.home() / ".codex" / "automations" / "flash-cast-daily-seo-geo" / "daily-automation.log"


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


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def shell_join(parts: list[str]) -> str:
    return " ".join(shell_quote(part) for part in parts)


def wrapper_script(root: Path, schedule: dict[str, Any], log_path: Path) -> str:
    args = [str(part) for part in command_args(schedule)]
    if args and args[0] == "python3":
        args[0] = shutil.which("python3") or "python3"
    command = shell_join(args)
    return f"""#!/usr/bin/env bash
set -euo pipefail

cd {shell_quote(str(root))}
mkdir -p {shell_quote(str(log_path.parent))}

echo "[flash-cast-daily-seo-geo] started $(date -Iseconds)" >> {shell_quote(str(log_path))}
{command} >> {shell_quote(str(log_path))} 2>&1
echo "[flash-cast-daily-seo-geo] finished $(date -Iseconds)" >> {shell_quote(str(log_path))}
"""


def cron_line(schedule: dict[str, Any], wrapper_path: Path, log_path: Path) -> str:
    time_local = str_value(schedule.get("time_local"), "09:00")
    hour, minute = parse_hour_minute(time_local)
    return f"{minute} {hour} * * * {shell_quote(str(wrapper_path))} >> {shell_quote(str(log_path))} 2>&1"


def local_launchd_time(schedule: dict[str, Any], now: dt.datetime | None = None) -> tuple[int, int, str]:
    """Convert the schedule timezone into the Mac's local launchd clock."""
    target_hour, target_minute = parse_hour_minute(str_value(schedule.get("time_local"), "09:00"))
    timezone_name = str_value(schedule.get("timezone"), "")
    local_now = now or dt.datetime.now().astimezone()
    local_tz = local_now.tzinfo
    if not timezone_name or local_tz is None:
        return target_hour, target_minute, ""
    try:
        target_tz = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return target_hour, target_minute, f"Unsupported timezone for launchd conversion: {timezone_name}."
    target_time = local_now.astimezone(target_tz).replace(
        hour=target_hour,
        minute=target_minute,
        second=0,
        microsecond=0,
    )
    local_time = target_time.astimezone(local_tz)
    return local_time.hour, local_time.minute, (
        f"launchd runs in the Mac local timezone; converted {target_hour:02d}:{target_minute:02d} "
        f"{timezone_name} to {local_time.hour:02d}:{local_time.minute:02d} local time for this host."
    )


def wrapper_launchd_plist(root: Path, schedule: dict[str, Any], wrapper_path: Path, log_path: Path) -> str:
    hour, minute, _ = local_launchd_time(schedule)
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
    <string>/bin/bash</string>
    <string>{xml_escape(str(wrapper_path))}</string>
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


def install_commands(root: Path, plist_path: Path, cron_path: Path, wrapper_path: Path, log_path: Path) -> list[dict[str, str]]:
    launch_agents_path = "~/Library/LaunchAgents/com.flashcast.daily-seo-geo.plist"
    return [
        {
            "step": "review_wrapper",
            "command": f"bash -n {shell_quote(str(wrapper_path))}",
            "note_zh": "检查 wrapper 脚本语法；不会运行自动化。",
        },
        {
            "step": "test_run_once",
            "command": shell_quote(str(wrapper_path)),
            "note_zh": "人工测试运行一次；仍遵守 schedule 的 no-publish 门禁。",
        },
        {
            "step": "install_launchd_macos",
            "command": f"mkdir -p ~/Library/LaunchAgents && cp {shell_quote(str(plist_path))} {launch_agents_path} && launchctl bootstrap gui/$(id -u) {launch_agents_path}",
            "note_zh": "macOS 安装 launchd 定时任务；需要业主明确批准后再执行。",
        },
        {
            "step": "uninstall_launchd_macos",
            "command": f"launchctl bootout gui/$(id -u) {launch_agents_path}; rm -f {launch_agents_path}",
            "note_zh": "禁用并删除 macOS launchd 定时任务。",
        },
        {
            "step": "install_cron_server",
            "command": f"(crontab -l 2>/dev/null; cat {shell_quote(str(cron_path))}) | crontab -",
            "note_zh": "Linux/服务器 cron 安装示例；需要确认运行用户和路径。",
        },
        {
            "step": "view_log",
            "command": f"tail -n 200 {shell_quote(str(log_path))}",
            "note_zh": "查看最近自动化日志。",
        },
        {
            "step": "open_workspace",
            "command": f"cd {shell_quote(str(root))}",
            "note_zh": "进入 skill 工作区查看 daily reports / owner review package。",
        },
    ]


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Automation Install Plan",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- Executor: `{summary.get('executor')}`",
        f"- Pipeline: `{summary.get('pipeline')}`",
        f"- Time: `{summary.get('time_local')}` `{summary.get('timezone')}`",
        "- 执行状态: install-plan-only；未安装 launchd/cron，未运行自动化，未发布",
        "",
        "## 今日决策",
        "",
        "今天把固定时间 SEO/GEO 自动化补到安装准备层：生成 wrapper、launchd plist、cron 行、安装/禁用/查看日志命令。当前仍只做本地计划，不安装系统任务。",
        "",
        "## 安装前 Blockers",
        "",
    ]
    blockers = safe_list(summary.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## 安装前 Warnings", ""])
    warnings = safe_list(summary.get("warnings"))
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## 人工审核命令", ""])
    for command in safe_list(summary.get("install_commands")):
        item = safe_dict(command)
        lines.append(f"- {item.get('step')}: `{item.get('command')}`")
        lines.append(f"  说明: {item.get('note_zh')}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本命令不会安装 launchd 或 cron；只生成可审核文件和命令。",
            "- schedule 仍必须保持 `max_tasks_per_run=1`，避免批量低质内容。",
            "- 如果 `publish_enabled=false`，定时任务只会生成内容/审核/准备产物，不会发布。",
            "- 真实 CMS 写入、图片上传或 live 发布仍需要业主另发明确执行指令。",
            "",
            "## Artifacts",
            "",
        ]
    )
    for name, path in safe_dict(summary.get("artifacts")).items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines) + "\n"


def run_automation_install_plan(
    root: Path,
    *,
    schedule_plan_path: str = "",
    install_kind: str = "launchd",
) -> tuple[dict[str, Any], tuple[Path, Path, Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    tools_dir = root / "seo-workspace" / "tools"
    config_dir = root / "seo-workspace" / "config"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    plan_file = resolve_path(root, schedule_plan_path or DEFAULT_SCHEDULE_PLAN)
    plan = read_json(plan_file)
    schedule = safe_dict(plan.get("schedule"))
    blockers = list(str(item) for item in safe_list(plan.get("blockers")))
    warnings = list(str(item) for item in safe_list(plan.get("warnings")))

    if not plan:
        blockers.append("Missing daily automation schedule plan. Run automation-schedule first.")
    if not schedule:
        blockers.append("Schedule plan has no schedule object.")
    if install_kind not in {"launchd", "cron", "both"}:
        blockers.append(f"Unsupported install kind: {install_kind}.")
    if plan.get("no_schedule_installed") is not True:
        warnings.append("Schedule plan does not explicitly say no_schedule_installed=true.")
    if schedule and str_value(schedule.get("automation_id")) != "flash-cast-daily-seo-geo":
        warnings.append("Automation ID is not flash-cast-daily-seo-geo; verify before installing.")
    launchd_hour, launchd_minute, launchd_note = local_launchd_time(schedule) if schedule else (9, 0, "")
    if launchd_note:
        warnings.append(launchd_note)

    workspace_log_path = root / str_value(schedule.get("log_path"), "seo-workspace/reports/daily-automation.log")
    log_path = LAUNCHD_LOG_PATH if install_kind in {"launchd", "both"} else workspace_log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path = tools_dir / WRAPPER_NAME
    plist_path = config_dir / PLIST_NAME
    cron_path = config_dir / CRON_NAME
    summary_path = data_dir / SUMMARY_NAME
    report_path = reports_dir / f"{today}-{REPORT_NAME}"

    if schedule:
        write_text(wrapper_path, wrapper_script(root, schedule, log_path))
        wrapper_path.chmod(0o755)
        write_text(plist_path, wrapper_launchd_plist(root, schedule, wrapper_path, log_path))
        write_text(cron_path, cron_line(schedule, wrapper_path, log_path) + "\n")
    else:
        write_text(wrapper_path, "#!/usr/bin/env bash\nexit 1\n")
        write_text(plist_path, "")
        write_text(cron_path, "")

    commands = install_commands(root, plist_path, cron_path, wrapper_path, log_path)
    status = "automation_install_plan_ready_for_owner_review" if not blockers else "automation_install_plan_blocked"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "install_kind": install_kind,
        "schedule_plan_path": str(plan_file),
        "automation_id": schedule.get("automation_id", ""),
        "executor": schedule.get("executor", ""),
        "pipeline": schedule.get("pipeline", ""),
        "time_local": schedule.get("time_local", ""),
        "timezone": schedule.get("timezone", ""),
        "launchd_local_time": f"{launchd_hour:02d}:{launchd_minute:02d}",
        "publish_enabled": schedule.get("publish_enabled", False),
        "install_commands": commands,
        "blockers": blockers,
        "warnings": warnings,
        "artifacts": {
            "wrapper_script": str(wrapper_path),
            "launchd_plist_candidate": str(plist_path),
            "cron_line_candidate": str(cron_path),
            "runtime_log": str(log_path),
            "install_plan_json": str(summary_path),
            "install_plan_report": str(report_path),
        },
        "no_schedule_installed": True,
        "no_automation_run_executed": True,
        "no_cms_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
    }
    write_text(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (wrapper_path, plist_path, cron_path, summary_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a no-install handoff package for fixed-time SEO/GEO automation.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--schedule-plan-path", default="")
    parser.add_argument("--install-kind", default="launchd", choices=["launchd", "cron", "both"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_automation_install_plan(
        Path(args.root),
        schedule_plan_path=args.schedule_plan_path,
        install_kind=args.install_kind,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] == "automation_install_plan_ready_for_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
