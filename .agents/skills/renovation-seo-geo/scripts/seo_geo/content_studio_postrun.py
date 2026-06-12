#!/usr/bin/env python3
"""Summarize content-studio orchestration results without executing anything."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any


POSTRUN_JSON_NAME = "content-studio-postrun-summary.json"
POSTRUN_REPORT_NAME = "content-studio-postrun-report.md"


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def pair_key(url: str) -> str:
    return url.rstrip("/").replace("/en/", "/{lang}/").replace("/zh/", "/{lang}/")


def resolve_path(root: Path, value: str, fallback: Path) -> Path:
    if not value:
        return fallback
    path = Path(value)
    return path if path.is_absolute() else root / path


def next_queue_item(queue: list[dict[str, str]], history: list[dict[str, str]]) -> dict[str, str]:
    used = {pair_key(row.get("target_url", "")) for row in history if row.get("target_url")}
    for row in queue:
        if pair_key(row.get("target_url", "")) not in used:
            return row
    return queue[0] if queue else {}


def render_report(summary: dict[str, Any]) -> str:
    latest = summary.get("latest_run") if isinstance(summary.get("latest_run"), dict) else {}
    next_item = summary.get("next_queue_item") if isinstance(summary.get("next_queue_item"), dict) else {}
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    artifacts = summary.get("artifacts") if isinstance(summary.get("artifacts"), dict) else {}
    lines = [
        "# Content Studio Postrun Report",
        "",
        f"- 生成时间: {summary.get('generated_at')}",
        f"- Status: `{summary.get('status')}`",
        f"- Latest target URL: `{latest.get('target_url', '')}`",
        f"- Latest pipeline: `{latest.get('pipeline', '')}`",
        f"- Latest content status: `{latest.get('status', '')}`",
        f"- Next queue target: `{next_item.get('target_url', '')}`",
        "- 执行状态: postrun-report-only；未运行自动化、未登录 CMS、未上传媒体、未写源码或数据库、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天生成 Content Studio 固定时间运行后的复盘报告，用来告诉业主本次是否完成、产物在哪里、下一个队列页面是谁，以及发布前还需要哪些审核动作。",
        "",
        "## Latest Run",
        "",
        f"- Target URL: `{latest.get('target_url', '')}`",
        f"- Paired URL: `{latest.get('paired_url', '')}`",
        f"- Pipeline: `{latest.get('pipeline', '')}`",
        f"- Status: `{latest.get('status', '')}`",
        f"- Content Studio report: `{latest.get('content_studio_report', '')}`",
        "",
        "## Next Queue Item",
        "",
        f"- Target URL: `{next_item.get('target_url', '')}`",
        f"- Paired URL: `{next_item.get('paired_url', '')}`",
        f"- Pipeline: `{next_item.get('recommended_pipeline', '')}`",
        f"- Command: `{next_item.get('content_studio_command', '')}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Artifacts", ""])
    for name, path in artifacts.items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(
        [
            "",
            "## 业主审核备注",
            "",
            "- 本报告只复盘本地内容生产结果，不代表发布授权。",
            "- 业主需要审核最新 Content Studio report、富文本编辑器、图片概念标签、CTA 和事实性声明。",
            "- 如要发布，仍需明确批准具体草稿并要求执行，通过 QA、media-ready、backup、changelog、rollback gates。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_postrun(
    root: Path,
    *,
    orchestration_path: str = "",
    next_run_path: str = "",
    queue_path: str = "",
    history_path: str = "",
) -> tuple[dict[str, Any], tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    orchestration_file = resolve_path(root, orchestration_path, data_dir / "content-studio-orchestration.json")
    next_file = resolve_path(root, next_run_path, data_dir / "content-studio-next-run.json")
    queue_file = resolve_path(root, queue_path, data_dir / "content-studio-queue.json")
    history_file = resolve_path(root, history_path, data_dir / "content-studio-history.csv")
    orchestration = read_json(orchestration_file)
    next_run = read_json(next_file)
    queue_payload = read_json(queue_file)
    history = read_csv_rows(history_file)
    blockers: list[str] = []
    if not orchestration:
        blockers.append("Missing content-studio-orchestration.json.")
    if not next_run:
        blockers.append("Missing content-studio-next-run.json.")
    if not queue_payload:
        blockers.append("Missing content-studio-queue.json.")
    if orchestration and orchestration.get("status") != "content_studio_orchestration_completed":
        blockers.extend(str(item) for item in orchestration.get("blockers", []) if item)
        if not blockers:
            blockers.append(f"Latest orchestration status is {orchestration.get('status')}.")

    selected = next_run.get("selected_queue_item") if isinstance(next_run.get("selected_queue_item"), dict) else {}
    latest_history = history[-1] if history else {}
    queue_rows = queue_payload.get("queue") if isinstance(queue_payload.get("queue"), list) else []
    typed_queue = [{str(k): str(v or "") for k, v in row.items()} for row in queue_rows if isinstance(row, dict)]
    next_item = next_queue_item(typed_queue, history)
    latest_run = {
        "target_url": str(selected.get("target_url") or latest_history.get("target_url", "")),
        "paired_url": str(selected.get("paired_url") or latest_history.get("paired_url", "")),
        "pipeline": str(selected.get("recommended_pipeline") or latest_history.get("pipeline", "")),
        "status": str(next_run.get("content_studio_status") or latest_history.get("status", "")),
        "content_studio_report": str(next_run.get("artifacts", {}).get("content_studio_report", "") if isinstance(next_run.get("artifacts"), dict) else latest_history.get("content_studio_report", "")),
    }
    status = "content_studio_postrun_ready_for_owner_review" if not blockers else "content_studio_postrun_blocked"
    json_path = data_dir / POSTRUN_JSON_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-{POSTRUN_REPORT_NAME}"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "latest_run": latest_run,
        "next_queue_item": next_item,
        "blockers": blockers,
        "history_count": len(history),
        "queue_count": len(typed_queue),
        "artifacts": {
            "postrun_json": str(json_path),
            "postrun_report": str(report_path),
            "orchestration_json": str(orchestration_file),
            "next_run_json": str(next_file),
            "queue_json": str(queue_file),
            "history_csv": str(history_file),
        },
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
    }
    write_text(json_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (json_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize content-studio orchestration outputs without executing.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--orchestration-path", default="")
    parser.add_argument("--next-run-path", default="")
    parser.add_argument("--queue-path", default="")
    parser.add_argument("--history-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_postrun(
        Path(args.root),
        orchestration_path=args.orchestration_path,
        next_run_path=args.next_run_path,
        queue_path=args.queue_path,
        history_path=args.history_path,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "content_studio_postrun_ready_for_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
