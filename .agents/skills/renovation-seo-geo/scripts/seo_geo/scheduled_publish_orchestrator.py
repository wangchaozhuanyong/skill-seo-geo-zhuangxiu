#!/usr/bin/env python3
"""Orchestrate a scheduled safe publish-prep run without live publishing."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from .daily_automation import run_daily_automation
    from .scheduled_publish_runner import READY_STATUS, run_scheduled_publish_runner
except ImportError:  # pragma: no cover - direct script execution
    from daily_automation import run_daily_automation
    from scheduled_publish_runner import READY_STATUS, run_scheduled_publish_runner


ORCHESTRATION_JSON_NAME = "scheduled-publish-orchestration.json"
ORCHESTRATION_REPORT_NAME = "scheduled-publish-orchestration.md"
ORCHESTRATION_ACTION = "scheduled_publish_orchestration_safe_prep_only"


@dataclass
class ScheduledPublishOrchestratorResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    orchestration: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def command_arg(command: list[object], flag: str) -> str:
    parts = [str(item) for item in command]
    if flag not in parts:
        return ""
    index = parts.index(flag)
    return parts[index + 1] if index + 1 < len(parts) else ""


def render_report(result: ScheduledPublishOrchestratorResult) -> str:
    orchestration = result.orchestration
    daily_summary = orchestration.get("daily_automation_summary", {})
    if not isinstance(daily_summary, dict):
        daily_summary = {}
    lines = [
        "# Scheduled Publish Orchestration",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{orchestration.get('target_url', 'N/A')}`",
        f"- Paired URL: `{orchestration.get('paired_url', 'N/A')}`",
        f"- Runner status: `{orchestration.get('runner_status', 'N/A')}`",
        f"- Daily automation status: `{daily_summary.get('status', 'not_executed')}`",
        f"- Research remote fetch: `{orchestration.get('research_fetch_remote', 'N/A')}`",
        f"- Research search provider: `{orchestration.get('research_search_provider', 'N/A')}`",
        f"- Research feeds config: `{orchestration.get('research_search_feeds_config', 'N/A')}`",
        "- 执行状态: safe orchestration only；未登录 CMS、未上传媒体、未写 live/source 页面、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天新增固定时间自动化的安全编排入口：它先验证 runner run request，只有 ready 时才触发 safe publish-prep 产物生成；整个流程仍停留在本地草稿/准备层。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Daily Automation Steps", ""])
    steps = safe_list(daily_summary.get("steps"))
    if steps:
        for step in steps:
            if isinstance(step, dict):
                lines.append(f"- `{step.get('name', 'unknown')}`: {step.get('status', 'unknown')}")
    else:
        lines.append("- Not executed")
    lines.extend(["", "## Handoff Blockers", ""])
    handoff_blockers = safe_list(daily_summary.get("handoff_blockers"))
    lines.extend(f"- {item}" for item in handoff_blockers) if handoff_blockers else lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 本入口最多执行 `daily-automation --pipeline publish-prep` 的本地准备流程。",
            "- publish-prep 仍只生成 queue、rich content、media plan、dry-run requests 和 readiness/bundle/implementation artifacts。",
            "- 本入口不会调用 CMS/admin helper，不上传媒体，不写 live/source 页面，不发布，不部署。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def run_scheduled_publish_orchestrator(
    root: Path,
    *,
    profile_path: str = "",
    target_url: str = "",
    now: str = "",
    window_minutes: int = 20,
    ignore_schedule_window: bool = False,
    allow_duplicate_run: bool = False,
    discover_research_sources: bool = True,
    research_fetch_remote: bool = True,
    research_search_provider: str = "hybrid-rss",
    research_search_feeds_config: str = "seo-workspace/config/research-search-feeds.example.yml",
    research_timeout: int = 10,
    research_per_seed_limit: int = 5,
    research_limit: int = 20,
    research_write_example: bool = True,
    auto_accept_research_sources: bool = True,
    research_intake_min_score: int = 60,
    research_intake_limit: int = 2,
    write_example: bool = True,
) -> tuple[ScheduledPublishOrchestratorResult, tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()

    runner_result, runner_artifacts = run_scheduled_publish_runner(
        root,
        profile_path=profile_path,
        target_url=target_url,
        now=now,
        window_minutes=window_minutes,
        ignore_schedule_window=ignore_schedule_window,
        allow_duplicate_run=allow_duplicate_run,
        write_example=write_example,
    )
    blockers = list(runner_result.blockers)
    warnings = list(runner_result.warnings)
    run_request = runner_result.run_request
    daily_summary: dict[str, Any] = {"status": "not_executed", "steps": [], "handoff_blockers": []}
    daily_artifacts: tuple[Path, Path] = ()
    daily_automation_executed = False

    if runner_result.status == READY_STATUS:
        daily_automation_executed = True
        command = safe_list(run_request.get("daily_automation_command"))
        selected_target_url = str_value(run_request.get("target_url"))
        website_root = command_arg(command, "--website-root")
        try:
            daily_result, daily_artifacts = run_daily_automation(
                root,
                pipeline="publish-prep",
                target_url=selected_target_url,
                website_root=website_root,
                discover_research_sources=discover_research_sources,
                research_fetch_remote=research_fetch_remote,
                research_search_provider=research_search_provider,
                research_search_feeds_config=research_search_feeds_config,
                research_timeout=research_timeout,
                research_per_seed_limit=research_per_seed_limit,
                research_limit=research_limit,
                research_write_example=research_write_example,
                auto_accept_research_sources=auto_accept_research_sources,
                research_intake_min_score=research_intake_min_score,
                research_intake_limit=research_intake_limit,
                authorization_profile_path=profile_path,
            )
        except Exception as exc:  # noqa: BLE001 - keep scheduler entrypoint auditable
            blockers.append(f"Safe daily publish-prep orchestration failed: {type(exc).__name__}: {exc}")
        else:
            if not daily_result.ok:
                blockers.extend(daily_result.blockers)
            daily_summary = {
                "status": daily_result.status,
                "pipeline": daily_result.pipeline,
                "selected_task": daily_result.selected_task,
                "steps": [step.as_dict() for step in daily_result.steps],
                "handoff_blockers": daily_result.handoff_blockers,
                "warnings": daily_result.warnings,
                "artifacts": [str(path) for path in daily_artifacts],
            }
            warnings.extend(daily_result.warnings)

    status = "scheduled_publish_safe_prep_completed" if not blockers and runner_result.status == READY_STATUS else "blocked_before_scheduled_publish_orchestration"
    orchestration = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": ORCHESTRATION_ACTION,
        "status": status,
        "runner_status": runner_result.status,
        "target_url": run_request.get("target_url", ""),
        "paired_url": run_request.get("paired_url", ""),
        "run_request": run_request,
        "daily_automation_executed": daily_automation_executed,
        "research_fetch_remote": research_fetch_remote,
        "research_search_provider": research_search_provider,
        "research_search_feeds_config": research_search_feeds_config,
        "daily_automation_summary": daily_summary,
        "runner_artifacts": [str(path) for path in runner_artifacts],
        "blockers": blockers,
        "warnings": warnings,
        "no_cms_login_executed": True,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "safety_note": "This orchestrator only runs the safe local publish-prep pipeline after a ready scheduled run request. It does not call CMS/admin helpers, upload media, write live/source pages, publish, regenerate SEO assets, or deploy.",
    }
    json_path = data_dir / ORCHESTRATION_JSON_NAME
    report_path = reports_dir / f"{today}-{ORCHESTRATION_REPORT_NAME}"
    result = ScheduledPublishOrchestratorResult(status=status, blockers=blockers, warnings=warnings, orchestration=orchestration)
    result.artifacts.update(
        {
            "orchestration_json": str(json_path),
            "report": str(report_path),
            "run_request_json": str(runner_artifacts[0]) if runner_artifacts else "",
            "run_log": str(runner_artifacts[1]) if len(runner_artifacts) > 1 else "",
            "run_request_report": str(runner_artifacts[2]) if len(runner_artifacts) > 2 else "",
        }
    )
    orchestration["artifacts"] = result.artifacts
    write_text(
        json_path,
        json.dumps(
            {
                "status": result.status,
                "orchestration": orchestration,
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
    return result, (json_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe scheduled publish-prep orchestration without live publishing.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--profile-path", default="", help="Optional scheduled publish authorization profile path.")
    parser.add_argument("--target-url", default="", help="Optional target URL override; must be allowed by authorization profile.")
    parser.add_argument("--now", default="", help="Optional ISO timestamp for deterministic scheduler checks.")
    parser.add_argument("--window-minutes", type=int, default=20)
    parser.add_argument("--ignore-schedule-window", action="store_true")
    parser.add_argument("--allow-duplicate-run", action="store_true")
    parser.add_argument("--skip-research-discovery", action="store_true")
    parser.add_argument("--no-fetch-research-remote", action="store_true")
    parser.add_argument("--research-search-provider", default="hybrid-rss")
    parser.add_argument("--research-search-feeds-config", default="seo-workspace/config/research-search-feeds.example.yml")
    parser.add_argument("--research-timeout", type=int, default=10)
    parser.add_argument("--research-per-seed-limit", type=int, default=5)
    parser.add_argument("--research-limit", type=int, default=20)
    parser.add_argument("--no-write-research-example", action="store_true")
    parser.add_argument("--no-auto-accept-research-sources", action="store_true")
    parser.add_argument("--research-intake-min-score", type=int, default=60)
    parser.add_argument("--research-intake-limit", type=int, default=2)
    parser.add_argument("--no-write-example", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_scheduled_publish_orchestrator(
        Path(args.root),
        profile_path=args.profile_path,
        target_url=args.target_url,
        now=args.now,
        window_minutes=args.window_minutes,
        ignore_schedule_window=args.ignore_schedule_window,
        allow_duplicate_run=args.allow_duplicate_run,
        discover_research_sources=not args.skip_research_discovery,
        research_fetch_remote=not args.no_fetch_research_remote,
        research_search_provider=args.research_search_provider,
        research_search_feeds_config=args.research_search_feeds_config,
        research_timeout=args.research_timeout,
        research_per_seed_limit=args.research_per_seed_limit,
        research_limit=args.research_limit,
        research_write_example=not args.no_write_research_example,
        auto_accept_research_sources=not args.no_auto_accept_research_sources,
        research_intake_min_score=args.research_intake_min_score,
        research_intake_limit=args.research_intake_limit,
        write_example=not args.no_write_example,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
