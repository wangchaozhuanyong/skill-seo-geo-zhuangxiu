#!/usr/bin/env python3
"""Create a safe owner-review publish candidate from the latest Content Studio run."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

from publish_queue import run_publish_queue


DEFAULT_POSTRUN = "seo-workspace/data/content-studio-postrun-summary.json"
DEFAULT_RUN = "seo-workspace/data/content-studio-run.json"
SUMMARY_PATH = "seo-workspace/data/content-studio-publish-candidate.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def latest_target(postrun: dict[str, Any], run: dict[str, Any], explicit_target_url: str = "") -> tuple[str, str]:
    if explicit_target_url:
        target_url = explicit_target_url
    else:
        target_url = str(postrun.get("latest_run", {}).get("target_url") or run.get("requested_target_url") or "")
    paired_url = str(postrun.get("latest_run", {}).get("paired_url") or "")
    if not paired_url:
        selected_task = run.get("selected_task", {})
        if isinstance(selected_task, dict):
            paired_url = str(selected_task.get("paired_url") or "")
    return target_url, paired_url


def find_rich_content_draft(root: Path, run: dict[str, Any], target_url: str) -> str:
    outputs = run.get("content_outputs") or []
    if not isinstance(outputs, list):
        return ""
    for value in outputs:
        if not isinstance(value, str) or not value.endswith("-rich-content-package.md"):
            continue
        path = resolve_path(root, value)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not target_url or target_url in text:
            return relative_to_root(root, path)
    return ""


def read_queue_rows(queue_path: Path) -> list[dict[str, str]]:
    if not queue_path.exists():
        return []
    with queue_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_queue_row(rows: list[dict[str, str]], target_url: str, draft_path: str) -> dict[str, str]:
    for row in rows:
        if draft_path and row.get("draft_path") == draft_path:
            return row
    for row in rows:
        if target_url and target_url in {row.get("target_url"), row.get("paired_url")}:
            return row
    return {}


def render_report(summary: dict[str, Any]) -> str:
    candidate = summary.get("candidate_row") or {}
    blockers = summary.get("blockers") or []
    lines = [
        "# Content Studio Publish Candidate",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        "- 执行模式: candidate-only / owner-review / no publish",
        f"- 状态: {summary['status']}",
        f"- 目标页面: `{summary.get('target_url') or 'not_found'}`",
        f"- 配对页面: `{summary.get('paired_url') or 'not_found'}`",
        f"- 匹配草稿: `{summary.get('matched_draft_path') or 'not_found'}`",
        f"- Queue: `{summary.get('queue_path')}`",
        f"- Publish queue report: `{summary.get('publish_queue_report_path')}`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天把最近一次 Content Studio 图文内容包整理成发布候选，而不是直接执行发布。这样可以让业主先审核目标页面、双语范围、CMS 字段路径、图片策略和发布闸门。",
        "",
        "## 候选发布路径",
        "",
        f"- 页面类型: `{candidate.get('page_type') or 'not_found'}`",
        f"- Target kind: `{candidate.get('target_kind') or 'not_found'}`",
        f"- CMS/source table: `{candidate.get('table') or 'not_found'}`",
        f"- Admin helper: `{candidate.get('admin_helper') or 'not_found'}`",
        f"- Queue status: `{candidate.get('status') or 'not_found'}`",
        f"- Language scope: `{candidate.get('language_scope') or 'not_found'}`",
        f"- Rich text ready: `{candidate.get('rich_text_ready') or 'not_found'}`",
        f"- Image strategy: `{candidate.get('image_strategy') or 'not_found'}`",
        "",
        "## 安全边界",
        "",
        "- 未调用 CMS / Supabase / admin helper。",
        "- 未修改网站源码或线上页面。",
        "- 未上传媒体、未发布、未部署。",
        "- 后续即使生成 publish-plan，也必须先有业主批准、明确执行指令、QA、备份、changelog 和 rollback plan。",
    ]
    if blockers:
        lines.extend(["", "## 阻断项"])
        lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(
        [
            "",
            "## 业主审核备注",
            "",
            "- 请确认是否批准这个具体页面候选进入后续 publish-plan 阶段。",
            "- 如果页面包含生成效果图或设计概念，发布时必须继续保留 concept/rendering 标签，不能写成真实完工案例或客户照片。",
            "- 若 CTA、服务区域、联系方式或业务承诺需要新增事实，请先提供确认信息。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_artifacts(root: Path, summary: dict[str, Any]) -> tuple[Path, Path]:
    data_path = root / SUMMARY_PATH
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-publish-candidate.md"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return data_path, report_path


def run_content_studio_publish_candidate(
    root: Path,
    *,
    postrun_path: str = "",
    content_studio_run_path: str = "",
    website_root: str = "",
    target_url: str = "",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    postrun_file = resolve_path(root, postrun_path or DEFAULT_POSTRUN)
    run_file = resolve_path(root, content_studio_run_path or DEFAULT_RUN)
    postrun = read_json(postrun_file)
    run = read_json(run_file)
    selected_target_url, paired_url = latest_target(postrun, run, target_url)
    matched_draft = find_rich_content_draft(root, run, selected_target_url)

    field_map_path, queue_path, publish_queue_report_path = run_publish_queue(root, website_root=website_root)
    rows = read_queue_rows(queue_path)
    candidate_row = find_queue_row(rows, selected_target_url, matched_draft)
    if candidate_row:
        # The publish queue is the canonical source for bilingual execution scope.
        # This prevents stale postrun paired_url values from leaking into handoff packages.
        selected_target_url = candidate_row.get("target_url") or selected_target_url
        paired_url = candidate_row.get("paired_url") or paired_url

    blockers: list[str] = []
    if not selected_target_url:
        blockers.append("Missing latest Content Studio target URL.")
    if not matched_draft:
        blockers.append("No matching rich-content package found for the latest Content Studio target.")
    if not candidate_row:
        blockers.append("No matching owner-review publish queue row found.")

    status = "content_studio_publish_candidate_waiting_owner_review" if not blockers else "content_studio_publish_candidate_blocked"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "target_url": selected_target_url,
        "paired_url": paired_url,
        "matched_draft_path": matched_draft,
        "candidate_row": candidate_row,
        "blockers": blockers,
        "field_map_path": str(field_map_path),
        "queue_path": str(queue_path),
        "publish_queue_report_path": str(publish_queue_report_path),
        "postrun_path": str(postrun_file),
        "content_studio_run_path": str(run_file),
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
    }
    data_path, report_path = write_artifacts(root, summary)
    return summary, [field_map_path, queue_path, publish_queue_report_path, data_path, report_path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a safe owner-review publish candidate from Content Studio output.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--postrun-path", default="", help="Optional content-studio-postrun-summary.json path.")
    parser.add_argument("--content-studio-run-path", default="", help="Optional content-studio-run.json path.")
    parser.add_argument("--website-root", default="", help="Optional website source root for publish-queue evidence.")
    parser.add_argument("--target-url", default="", help="Override target URL selection.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_publish_candidate(
        Path(args.root),
        postrun_path=args.postrun_path,
        content_studio_run_path=args.content_studio_run_path,
        website_root=args.website_root,
        target_url=args.target_url,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] == "content_studio_publish_candidate_waiting_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
