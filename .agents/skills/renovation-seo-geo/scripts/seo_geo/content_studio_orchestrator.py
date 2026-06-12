#!/usr/bin/env python3
"""Safe fixed-time orchestrator for content-studio queue consumption."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:  # pragma: no cover - package import path differs between CLI and tests
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]

try:  # pragma: no cover
    from .automation_schedule import bool_value, parse_hour_minute, schedule_from_config, str_value, validate_schedule
    from .content_studio_next import run_content_studio_next
except ImportError:  # pragma: no cover
    from automation_schedule import bool_value, parse_hour_minute, schedule_from_config, str_value, validate_schedule
    from content_studio_next import run_content_studio_next


ORCHESTRATION_JSON_NAME = "content-studio-orchestration.json"
ORCHESTRATION_LOG_NAME = "content-studio-orchestration-log.csv"
LOG_FIELDS = ["run_at", "local_date", "status", "target_url", "pipeline", "next_run_json", "report"]


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def append_log(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in LOG_FIELDS})


def config_path_for(root: Path, config_path: str) -> Path:
    if config_path:
        path = Path(config_path)
        return path if path.is_absolute() else root / path
    candidate = root / "seo-workspace" / "config" / "daily-automation.yml"
    if candidate.exists():
        return candidate
    return root / "seo-workspace" / "config" / "daily-automation.example.yml"


def timezone_for(name: str) -> dt.tzinfo:
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception:  # noqa: BLE001 - fall back to UTC in report
            return dt.timezone.utc
    return dt.timezone.utc


def parse_now(value: str, timezone_name: str) -> dt.datetime:
    tz = timezone_for(timezone_name)
    if not value:
        return dt.datetime.now(tz)
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def within_window(now: dt.datetime, time_local: str, window_minutes: int) -> tuple[bool, int]:
    hour, minute = parse_hour_minute(time_local)
    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    delta = abs(int((now - scheduled).total_seconds() // 60))
    return delta <= window_minutes, delta


def already_ran_today(log_path: Path, local_date: str) -> bool:
    for row in read_csv_rows(log_path):
        if row.get("local_date") == local_date and row.get("status") == "content_studio_orchestration_completed":
            return True
    return False


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Orchestration",
        "",
        f"- 生成时间: {summary.get('generated_at')}",
        f"- Status: `{summary.get('status')}`",
        f"- Executor: `{summary.get('executor')}`",
        f"- Local date: `{summary.get('local_date')}`",
        f"- Schedule delta minutes: {summary.get('schedule_delta_minutes')}",
        f"- Owner review package: `{summary.get('owner_review_package_enabled')}`",
        "- 执行状态: schedule-gated draft/prep-only；未安装 cron/launchd，未登录 CMS，未上传媒体，未发布，未部署",
        "",
        "## 今日决策",
        "",
        "今天通过 Content Studio Orchestrator 检查固定时间计划，并且只在时间窗口、executor 和重复运行门禁通过时消费一个队列页面。这样定时 SEO/GEO 可以稳定覆盖整站，同时避免无人值守发布或批量内容。",
        "",
        "## Blockers",
        "",
    ]
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Artifacts", ""])
    artifacts = summary.get("artifacts") if isinstance(summary.get("artifacts"), dict) else {}
    for name, path in artifacts.items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本 orchestrator 不安装系统定时任务；只供 cron/launchd 在未来调用。",
            "- 每次最多消费一个 content-studio queue item。",
            "- 不发布、不上传媒体、不写 CMS/source；发布仍需业主审核和明确执行指令。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_orchestrator(
    root: Path,
    *,
    config_path: str = "",
    now: str = "",
    window_minutes: int = 20,
    ignore_schedule_window: bool = False,
    allow_duplicate_run: bool = False,
) -> tuple[dict[str, Any], tuple[Path, Path, Path]]:
    root = root.resolve()
    cfg_path = config_path_for(root, config_path)
    schedule = schedule_from_config(root, cfg_path)
    blockers, warnings = validate_schedule(schedule)
    timezone_name = str_value(schedule.get("timezone"), "UTC")
    now_local = parse_now(now, timezone_name)
    ok_window, delta_minutes = within_window(now_local, str_value(schedule.get("time_local"), "09:00"), window_minutes)
    log_path = root / "seo-workspace" / "data" / ORCHESTRATION_LOG_NAME
    data_path = root / "seo-workspace" / "data" / ORCHESTRATION_JSON_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-orchestration.md"
    local_date = now_local.date().isoformat()

    if not bool_value(schedule.get("enabled")):
        blockers.append("Schedule is disabled.")
    if str_value(schedule.get("executor"), "daily-automation") != "content-studio-next":
        blockers.append("Content Studio Orchestrator requires executor: content-studio-next.")
    if bool_value(schedule.get("publish_enabled")):
        blockers.append("Content Studio Orchestrator requires publish_enabled=false.")
    if not ignore_schedule_window and not ok_window:
        blockers.append(f"Current time is outside the schedule window by {delta_minutes} minutes.")
    if not allow_duplicate_run and already_ran_today(log_path, local_date):
        blockers.append("Content Studio Orchestrator already completed a run for this local date.")

    next_summary: dict[str, Any] = {}
    owner_review_package_enabled = bool_value(schedule.get("owner_review_package"))
    next_artifacts: tuple[Path, ...] = ()
    if not blockers:
        next_summary, next_artifacts = run_content_studio_next(
            root,
            target_url=str_value(schedule.get("target_url")),
            pipeline=str_value(schedule.get("pipeline")),
            website_root=str_value(schedule.get("website_root")),
            rebuild_queue=True,
            research_fetch_remote=bool_value(schedule.get("fetch_research_remote")),
            research_search_provider=str_value(schedule.get("research_search_provider"), "hybrid-rss"),
            research_search_feeds_config=str_value(
                schedule.get("research_search_feeds_config"),
                "seo-workspace/config/research-search-feeds.example.yml",
            ),
            owner_review_package=owner_review_package_enabled,
        )

    status = "content_studio_orchestration_completed" if not blockers else "content_studio_orchestration_blocked"
    selected = next_summary.get("selected_queue_item") if isinstance(next_summary.get("selected_queue_item"), dict) else {}
    artifacts = {
        "orchestration_json": str(data_path),
        "orchestration_log": str(log_path),
        "orchestration_report": str(report_path),
    }
    if next_artifacts:
        artifacts.update(
            {
                "content_studio_next_json": str(next_artifacts[0]),
                "content_studio_history": str(next_artifacts[1]),
                "content_studio_next_report": str(next_artifacts[2]),
            }
        )
        if len(next_artifacts) >= 5:
            artifacts.update(
                {
                    "owner_review_package_json": str(next_artifacts[-2]),
                    "owner_review_package_report": str(next_artifacts[-1]),
                }
            )
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "executor": str_value(schedule.get("executor"), "daily-automation"),
        "owner_review_package_enabled": owner_review_package_enabled,
        "local_date": local_date,
        "schedule_delta_minutes": delta_minutes,
        "schedule": schedule,
        "blockers": blockers,
        "warnings": warnings,
        "next_summary": next_summary,
        "artifacts": artifacts,
        "no_schedule_installed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
    }
    append_log(
        log_path,
        {
            "run_at": summary["generated_at"],
            "local_date": local_date,
            "status": status,
            "target_url": str(selected.get("target_url", "")),
            "pipeline": str_value(schedule.get("pipeline")),
            "next_run_json": artifacts.get("content_studio_next_json", ""),
            "report": str(report_path),
        },
    )
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, log_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe fixed-time content-studio queue orchestration.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--config-path", default="")
    parser.add_argument("--now", default="")
    parser.add_argument("--window-minutes", type=int, default=20)
    parser.add_argument("--ignore-schedule-window", action="store_true")
    parser.add_argument("--allow-duplicate-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_orchestrator(
        Path(args.root),
        config_path=args.config_path,
        now=args.now,
        window_minutes=args.window_minutes,
        ignore_schedule_window=args.ignore_schedule_window,
        allow_duplicate_run=args.allow_duplicate_run,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "content_studio_orchestration_completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
