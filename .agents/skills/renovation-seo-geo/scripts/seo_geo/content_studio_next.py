#!/usr/bin/env python3
"""Run the next content-studio queue item without live execution."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path

try:  # pragma: no cover - package import path differs between CLI and tests
    from .content_studio import DEFAULT_RESEARCH_SEARCH_FEEDS_CONFIG, DEFAULT_RESEARCH_SEARCH_PROVIDER, run_content_studio
    from .content_studio_owner_review_package import run_content_studio_owner_review_package
    from .content_studio_queue import run_content_studio_queue
except ImportError:  # pragma: no cover
    from content_studio import DEFAULT_RESEARCH_SEARCH_FEEDS_CONFIG, DEFAULT_RESEARCH_SEARCH_PROVIDER, run_content_studio
    from content_studio_owner_review_package import run_content_studio_owner_review_package
    from content_studio_queue import run_content_studio_queue


NEXT_RUN_JSON_NAME = "content-studio-next-run.json"
HISTORY_CSV_NAME = "content-studio-history.csv"
HISTORY_FIELDS = [
    "run_at",
    "target_url",
    "paired_url",
    "pipeline",
    "status",
    "queue_slot",
    "content_studio_json",
    "content_studio_report",
]


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def append_history(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in HISTORY_FIELDS})


def pair_key(url: str) -> str:
    return url.rstrip("/").replace("/en/", "/{lang}/").replace("/zh/", "/{lang}/")


def used_keys(root: Path, history_path: str = "") -> set[str]:
    path = Path(history_path) if history_path else root / "seo-workspace" / "data" / HISTORY_CSV_NAME
    if not path.is_absolute():
        path = root / path
    keys: set[str] = set()
    for row in read_csv_rows(path):
        url = row.get("target_url", "")
        if url:
            keys.add(pair_key(url))
    return keys


def select_next(queue: list[dict[str, str]], used: set[str], target_url: str = "") -> dict[str, str]:
    if target_url:
        normalized = target_url.rstrip("/")
        for row in queue:
            if row.get("target_url", "").rstrip("/") == normalized or row.get("paired_url", "").rstrip("/") == normalized:
                return row
        raise RuntimeError(f"Target URL not found in content-studio queue: {target_url}")
    for row in queue:
        if pair_key(row.get("target_url", "")) not in used:
            return row
    return queue[0] if queue else {}


def render_report(summary: dict[str, object]) -> str:
    selected = summary.get("selected_queue_item") if isinstance(summary.get("selected_queue_item"), dict) else {}
    artifacts = summary.get("artifacts") if isinstance(summary.get("artifacts"), dict) else {}
    lines = [
        "# Content Studio Next Run",
        "",
        f"- 生成时间: {summary.get('generated_at')}",
        f"- Status: `{summary.get('status')}`",
        f"- Target URL: `{selected.get('target_url', '')}`",
        f"- Paired URL: `{selected.get('paired_url', '')}`",
        f"- Pipeline: `{selected.get('recommended_pipeline', '')}`",
        f"- Research remote fetch: `{summary.get('research_fetch_remote')}`",
        f"- Research search provider: `{summary.get('research_search_provider')}`",
        f"- Research feeds config: `{summary.get('research_search_feeds_config')}`",
        "- 执行状态: draft/prep-only；未登录 CMS、未上传媒体、未写源码或数据库、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天从 Content Studio 队列中选择下一个页面并生成图文内容生产包。默认带 `hybrid-rss` 最新来源候选，这样固定时间自动化可以按队列逐步覆盖整站，而不是重复同一页或随机写文章。",
        "",
        "## 产物",
        "",
        f"- Content Studio JSON: `{artifacts.get('content_studio_json', '')}`",
        f"- Content Studio report: `{artifacts.get('content_studio_report', '')}`",
        f"- Owner review package: `{artifacts.get('owner_review_package_report', '')}`",
        f"- Next run JSON: `{artifacts.get('next_run_json', '')}`",
        f"- History CSV: `{artifacts.get('history_csv', '')}`",
        "",
        "## 安全边界",
        "",
        "- 本命令只取队列中的一个页面生成本地审核包。",
        "- 不批量生成全站正文，不登录 CMS，不上传媒体，不写源站，不发布，不部署。",
        "- 后续发布仍需要业主审核、明确执行、QA、media-ready、backup、changelog 和 rollback gates。",
        "",
        "## 执行状态：等待业主审核和明确执行指令",
    ]
    return "\n".join(lines) + "\n"


def run_content_studio_next(
    root: Path,
    *,
    target_url: str = "",
    pipeline: str = "",
    website_root: str = "",
    history_path: str = "",
    rebuild_queue: bool = False,
    research_fetch_remote: bool = True,
    research_search_provider: str = DEFAULT_RESEARCH_SEARCH_PROVIDER,
    research_search_feeds_config: str = DEFAULT_RESEARCH_SEARCH_FEEDS_CONFIG,
    owner_review_package: bool = False,
) -> tuple[dict[str, object], tuple[Path, ...]]:
    root = root.resolve()
    queue_path = root / "seo-workspace" / "data" / "content-studio-queue.json"
    if rebuild_queue or not queue_path.exists():
        run_content_studio_queue(root)
    payload = read_json(queue_path)
    queue = payload.get("queue") if isinstance(payload.get("queue"), list) else []
    typed_queue = [row for row in queue if isinstance(row, dict)]
    selected = select_next([{str(k): str(v or "") for k, v in row.items()} for row in typed_queue], used_keys(root, history_path), target_url)
    if not selected:
        raise RuntimeError("Content Studio queue is empty. Run content-studio-queue first.")
    selected_pipeline = pipeline or selected.get("recommended_pipeline", "rich-content") or "rich-content"
    studio_summary, studio_artifacts = run_content_studio(
        root,
        target_url=selected["target_url"],
        pipeline=selected_pipeline,
        website_root=website_root,
        research_fetch_remote=research_fetch_remote,
        research_search_provider=research_search_provider,
        research_search_feeds_config=research_search_feeds_config,
    )
    owner_summary: dict[str, object] = {}
    owner_artifacts: list[Path] = []
    if owner_review_package:
        owner_summary, package_artifacts = run_content_studio_owner_review_package(
            root,
            website_root=website_root,
            target_url=selected["target_url"],
        )
        owner_artifacts = list(package_artifacts)
    run_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    history_csv = Path(history_path) if history_path else data_dir / HISTORY_CSV_NAME
    if not history_csv.is_absolute():
        history_csv = root / history_csv
    next_json = data_dir / NEXT_RUN_JSON_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-content-studio-next-run.md"
    summary = {
        "generated_at": run_at,
        "status": "content_studio_next_waiting_owner_review",
        "selected_queue_item": selected,
        "content_studio_status": studio_summary.get("status", ""),
        "research_fetch_remote": research_fetch_remote,
        "research_search_provider": research_search_provider,
        "research_search_feeds_config": research_search_feeds_config,
        "research_artifacts": studio_summary.get("research_artifacts", []),
        "artifacts": {
            "content_studio_json": str(studio_artifacts[0]),
            "content_studio_report": str(studio_artifacts[1]),
            "owner_review_package_json": str(owner_artifacts[-2]) if owner_artifacts else "",
            "owner_review_package_report": str(owner_artifacts[-1]) if owner_artifacts else "",
            "next_run_json": str(next_json),
            "history_csv": str(history_csv),
            "next_run_report": str(report_path),
        },
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
    }
    if owner_summary:
        summary["owner_review_package_status"] = owner_summary.get("status", "")
    append_history(
        history_csv,
        {
            "run_at": run_at,
            "target_url": selected.get("target_url", ""),
            "paired_url": selected.get("paired_url", ""),
            "pipeline": selected_pipeline,
            "status": str(studio_summary.get("status", "")),
            "queue_slot": selected.get("slot", ""),
            "content_studio_json": str(studio_artifacts[0]),
            "content_studio_report": str(studio_artifacts[1]),
        },
    )
    write_text(next_json, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, tuple([next_json, history_csv, report_path, *owner_artifacts])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the next draft-only content-studio queue item.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--target-url", default="", help="Optional explicit queue target URL.")
    parser.add_argument("--pipeline", default="", choices=["", "brief", "rich-content", "publish-prep"])
    parser.add_argument("--website-root", default="")
    parser.add_argument("--history-path", default="")
    parser.add_argument("--rebuild-queue", action="store_true")
    parser.add_argument("--no-fetch-research-remote", action="store_true")
    parser.add_argument("--research-search-provider", default=DEFAULT_RESEARCH_SEARCH_PROVIDER)
    parser.add_argument("--research-search-feeds-config", default=DEFAULT_RESEARCH_SEARCH_FEEDS_CONFIG)
    parser.add_argument("--owner-review-package", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _, artifacts = run_content_studio_next(
        Path(args.root),
        target_url=args.target_url,
        pipeline=args.pipeline,
        website_root=args.website_root,
        history_path=args.history_path,
        rebuild_queue=args.rebuild_queue,
        research_fetch_remote=not args.no_fetch_research_remote,
        research_search_provider=args.research_search_provider,
        research_search_feeds_config=args.research_search_feeds_config,
        owner_review_package=args.owner_review_package,
    )
    for artifact in artifacts:
        print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
