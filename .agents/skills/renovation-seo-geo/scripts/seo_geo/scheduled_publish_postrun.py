#!/usr/bin/env python3
"""Summarize scheduled publish automation outcomes without executing actions."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


POSTRUN_JSON_NAME = "scheduled-publish-postrun-summary.json"
POSTRUN_REPORT_NAME = "scheduled-publish-postrun-report.md"
POSTRUN_ACTION = "scheduled_publish_postrun_summary_only_no_execute"


@dataclass
class ScheduledPublishPostrunResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str, default_relative: str) -> Path:
    path = Path(value) if value else root / default_relative
    return path if path.is_absolute() else root / path


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def unique_strings(values: list[object]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str_value(value)
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def categorize_blockers(blockers: list[str]) -> dict[str, list[str]]:
    categories: dict[str, list[str]] = {
        "authorization": [],
        "schedule_window": [],
        "owner_approval": [],
        "qa": [],
        "media": [],
        "source_research": [],
        "implementation": [],
        "operator": [],
        "receipt": [],
        "other": [],
    }
    for blocker in blockers:
        if contains_any(blocker, ("authorization", "owner authorization", "profile missing", "enabled must be true", "allowed_target_urls", "expires_at")):
            categories["authorization"].append(blocker)
        elif contains_any(blocker, ("local time", "local weekday", "scheduled", "window")):
            categories["schedule_window"].append(blocker)
        elif contains_any(blocker, ("owner has not approved", "--owner-approved", "explicit execution", "--explicit-execution")):
            categories["owner_approval"].append(blocker)
        elif contains_any(blocker, ("qa", "--qa-passed")):
            categories["qa"].append(blocker)
        elif contains_any(blocker, ("media", "upload", "storage", "placeholder", "url map")):
            categories["media"].append(blocker)
        elif contains_any(blocker, ("research", "source log", "latest")):
            categories["source_research"].append(blocker)
        elif contains_any(blocker, ("operator command", "operator package", "publish-operator")):
            categories["operator"].append(blocker)
        elif contains_any(blocker, ("execution receipt", "publish-execution-receipt", "execution result", "receipt verifier")):
            categories["receipt"].append(blocker)
        elif contains_any(blocker, ("bundle", "implementation", "executor", "cms write", "website adapter", "backup", "rollback", "changelog")):
            categories["implementation"].append(blocker)
        else:
            categories["other"].append(blocker)
    return {key: value for key, value in categories.items() if value}


def recommended_next_actions(categories: dict[str, list[str]], *, runner_status: str, daily_status: str) -> list[str]:
    actions: list[str] = []
    if "authorization" in categories:
        actions.append("填写并审核 `seo-workspace/config/scheduled-publish-authorization.yml`，包括授权 ID、双语 URL、过期日期和 website_root。")
    if "schedule_window" in categories:
        actions.append("在授权本地时间窗口内运行 scheduler，或仅在人工测试时使用 `--ignore-schedule-window`。")
    if runner_status != "scheduled_publish_run_request_ready":
        actions.append("先让 `scheduled-publish-runner` 达到 ready，再允许 orchestrator 触发 publish-prep。")
    if daily_status == "not_executed":
        actions.append("runner ready 后重新运行 `scheduled-publish-orchestrator --no-fetch-research-remote` 做安全 publish-prep dry-run。")
    if "media" in categories:
        actions.append("完成概念图/效果图生成、上传或 URL map，确保 payload 不再含 `NEEDS_MEDIA_UPLOAD:*`。")
    if "qa" in categories:
        actions.append("对目标 `/en` 与 `/zh` 页面分别运行 QA，并只把真实通过结果作为后续执行证据。")
    if "owner_approval" in categories:
        actions.append("业主需要批准 exact 内容包，并明确发出执行指令；普通批准不能替代执行授权。")
    if "source_research" in categories:
        actions.append("为依赖最新资料的页面补齐 `research-source-log.csv`，避免把 query 或未验证来源当引用。")
    if "implementation" in categories:
        actions.append("待 readiness/bundle/approved executor 全部 ready 后，再生成或复核 implementation package。")
    if "operator" in categories:
        actions.append("待 implementation package ready 后，重新生成并复核 `publish-operator-command.json`，不要直接调用 CMS helper。")
    if "receipt" in categories:
        actions.append("真实执行后必须生成并验证 `publish-execution-result.json` / `publish-execution-receipt.json`，否则不要声称已发布。")
    if not actions:
        actions.append("当前 postrun 未发现阻断；下一步应由业主确认是否进入 approved execution gate。")
    return actions


def build_summary(
    *,
    orchestration_payload: dict[str, Any],
    run_request_payload: dict[str, Any],
    daily_payload: dict[str, Any],
    readiness_payload: dict[str, Any],
    implementation_payload: dict[str, Any],
    operator_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
    source_paths: dict[str, str],
) -> tuple[dict[str, Any], list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    orchestration = safe_dict(orchestration_payload.get("orchestration"))
    run_request = safe_dict(run_request_payload.get("run_request"))
    daily_status = str_value(daily_payload.get("status"), "not_executed")
    readiness_status = str_value(readiness_payload.get("status"), "not_checked")
    implementation_status = str_value(implementation_payload.get("status"), "not_checked")
    operator_status = str_value(operator_payload.get("status"), "not_checked")
    receipt_status = str_value(receipt_payload.get("status"), "not_checked")
    runner_status = str_value(orchestration.get("runner_status") or run_request.get("status"), "not_checked")

    if not orchestration_payload:
        blockers.append("Missing scheduled-publish-orchestration.json. Run scheduled-publish-orchestrator first.")
    if not run_request_payload:
        warnings.append("Missing scheduled-publish-run-request.json; postrun summary cannot inspect scheduler gate details.")
    if not daily_payload:
        warnings.append("Missing daily-automation-run.json; daily publish-prep may not have executed.")
    if not operator_payload:
        warnings.append("Missing publish-operator-command.json; postrun summary cannot inspect the final operator gate.")
    if operator_status == "operator_command_ready_for_future_execution" and not receipt_payload:
        blockers.append("Missing publish-execution-receipt.json after operator package ready; verify execution result before claiming publish completion.")

    operator_package = safe_dict(operator_payload.get("operator_package"))
    receipt = safe_dict(receipt_payload.get("receipt"))

    all_blockers = unique_strings(
        safe_list(orchestration_payload.get("blockers"))
        + safe_list(orchestration.get("blockers"))
        + safe_list(run_request_payload.get("blockers"))
        + safe_list(run_request.get("blockers"))
        + safe_list(daily_payload.get("blockers"))
        + safe_list(daily_payload.get("handoff_blockers"))
        + safe_list(readiness_payload.get("blockers"))
        + safe_list(implementation_payload.get("blockers"))
        + safe_list(operator_payload.get("blockers"))
        + safe_list(operator_package.get("blockers"))
        + safe_list(receipt_payload.get("blockers"))
        + safe_list(receipt.get("blockers"))
    )
    all_warnings = unique_strings(
        safe_list(orchestration_payload.get("warnings"))
        + safe_list(orchestration.get("warnings"))
        + safe_list(run_request_payload.get("warnings"))
        + safe_list(run_request.get("warnings"))
        + safe_list(daily_payload.get("warnings"))
        + safe_list(readiness_payload.get("warnings"))
        + safe_list(implementation_payload.get("warnings"))
        + safe_list(operator_payload.get("warnings"))
        + safe_list(operator_package.get("warnings"))
        + safe_list(receipt_payload.get("warnings"))
        + safe_list(receipt.get("warnings"))
    )
    categories = categorize_blockers(all_blockers)
    next_actions = recommended_next_actions(categories, runner_status=runner_status, daily_status=daily_status)
    if all_blockers:
        blockers.extend(all_blockers)
    warnings.extend(all_warnings)

    daily_steps = []
    for step in safe_list(daily_payload.get("steps")):
        if isinstance(step, dict):
            daily_steps.append({"name": step.get("name", ""), "status": step.get("status", "")})

    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": POSTRUN_ACTION,
        "status": "scheduled_publish_postrun_blocked" if blockers else "scheduled_publish_postrun_ready",
        "target_url": orchestration.get("target_url") or run_request.get("target_url") or safe_dict(daily_payload.get("selected_task")).get("target_url", ""),
        "paired_url": orchestration.get("paired_url") or run_request.get("paired_url", ""),
        "runner_status": runner_status,
        "orchestration_status": str_value(orchestration_payload.get("status") or orchestration.get("status"), "not_checked"),
        "daily_automation_status": daily_status,
        "readiness_status": readiness_status,
        "implementation_status": implementation_status,
        "operator_status": operator_status,
        "receipt_status": receipt_status,
        "daily_steps": daily_steps,
        "blocker_categories": categories,
        "next_actions": next_actions,
        "source_paths": source_paths,
        "blockers": blockers,
        "warnings": warnings,
        "no_cms_login_executed": True,
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
        "safety_note": "This postrun report summarizes local artifacts only. It does not fetch research, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy.",
    }
    return summary, blockers, warnings


def render_report(result: ScheduledPublishPostrunResult) -> str:
    summary = result.summary
    lines = [
        "# Scheduled Publish Postrun Summary",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{summary.get('target_url', 'N/A')}`",
        f"- Paired URL: `{summary.get('paired_url', 'N/A')}`",
        f"- Runner status: `{summary.get('runner_status', 'N/A')}`",
        f"- Orchestration status: `{summary.get('orchestration_status', 'N/A')}`",
        f"- Daily automation status: `{summary.get('daily_automation_status', 'N/A')}`",
        f"- Operator package status: `{summary.get('operator_status', 'N/A')}`",
        f"- Execution receipt status: `{summary.get('receipt_status', 'N/A')}`",
        "- 执行状态: postrun-summary-only；未联网抓取、未登录 CMS、未上传媒体、未写页面、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天新增固定时间 SEO/GEO 自动化的运行后复盘层：它把 scheduler、orchestrator、daily publish-prep 和发布门禁阻断统一整理成业主可读的下一步清单。",
        "",
        "## Blocker Categories",
        "",
    ]
    categories = safe_dict(summary.get("blocker_categories"))
    if categories:
        for category, items in categories.items():
            lines.append(f"### {category}")
            for item in safe_list(items):
                lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.extend(["", "## Recommended Next Actions", ""])
    for action in safe_list(summary.get("next_actions")):
        lines.append(f"- {action}")
    lines.extend(["", "## Daily Automation Steps", ""])
    steps = safe_list(summary.get("daily_steps"))
    if steps:
        for step in steps:
            if isinstance(step, dict):
                lines.append(f"- `{step.get('name', 'unknown')}`: {step.get('status', 'unknown')}")
    else:
        lines.append("- Not executed")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 本报告只复盘本地产物，不会再次执行 research、daily automation 或发布链路。",
            "- 若需要继续，应优先处理 Recommended Next Actions，再重新运行相应 dry-run。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def run_scheduled_publish_postrun(
    root: Path,
    *,
    orchestration_path: str = "",
    run_request_path: str = "",
    daily_run_path: str = "",
    readiness_path: str = "",
    implementation_path: str = "",
    operator_path: str = "",
    receipt_path: str = "",
) -> tuple[ScheduledPublishPostrunResult, tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    paths = {
        "orchestration": resolve_path(root, orchestration_path, "seo-workspace/data/scheduled-publish-orchestration.json"),
        "run_request": resolve_path(root, run_request_path, "seo-workspace/data/scheduled-publish-run-request.json"),
        "daily_run": resolve_path(root, daily_run_path, "seo-workspace/data/daily-automation-run.json"),
        "readiness": resolve_path(root, readiness_path, "seo-workspace/data/publish-readiness.json"),
        "implementation": resolve_path(root, implementation_path, "seo-workspace/data/publish-implementation-package.json"),
        "operator": resolve_path(root, operator_path, "seo-workspace/data/publish-operator-command.json"),
        "receipt": resolve_path(root, receipt_path, "seo-workspace/data/publish-execution-receipt.json"),
    }
    summary, blockers, warnings = build_summary(
        orchestration_payload=read_json(paths["orchestration"]),
        run_request_payload=read_json(paths["run_request"]),
        daily_payload=read_json(paths["daily_run"]),
        readiness_payload=read_json(paths["readiness"]),
        implementation_payload=read_json(paths["implementation"]),
        operator_payload=read_json(paths["operator"]),
        receipt_payload=read_json(paths["receipt"]),
        source_paths={key: str(path) for key, path in paths.items()},
    )
    status = str_value(summary.get("status"))
    result = ScheduledPublishPostrunResult(status=status, blockers=blockers, warnings=warnings, summary=summary)
    json_path = data_dir / POSTRUN_JSON_NAME
    report_path = reports_dir / f"{today}-{POSTRUN_REPORT_NAME}"
    result.artifacts.update(
        {
            "postrun_json": str(json_path),
            "report": str(report_path),
            **{f"source_{key}": str(path) for key, path in paths.items()},
        }
    )
    summary["artifacts"] = result.artifacts
    write_text(
        json_path,
        json.dumps(
            {
                "status": result.status,
                "summary": summary,
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
    parser = argparse.ArgumentParser(description="Summarize scheduled publish automation artifacts without executing actions.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--orchestration-path", default="")
    parser.add_argument("--run-request-path", default="")
    parser.add_argument("--daily-run-path", default="")
    parser.add_argument("--readiness-path", default="")
    parser.add_argument("--implementation-path", default="")
    parser.add_argument("--operator-path", default="")
    parser.add_argument("--receipt-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_scheduled_publish_postrun(
        Path(args.root),
        orchestration_path=args.orchestration_path,
        run_request_path=args.run_request_path,
        daily_run_path=args.daily_run_path,
        readiness_path=args.readiness_path,
        implementation_path=args.implementation_path,
        operator_path=args.operator_path,
        receipt_path=args.receipt_path,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
