#!/usr/bin/env python3
"""Convert confirmed media URLs into a refreshed Content Studio publish handoff."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from content_studio_approval_packet import run_content_studio_approval_packet
from content_studio_publish_prep import run_content_studio_publish_prep
from media_upload_executor import run_media_upload_executor


SUMMARY_NAME = "content-studio-media-ready-handoff.json"
REPORT_NAME = "content-studio-media-ready-handoff.md"


def result_summary(name: str, result: Any, artifacts: list[Path] | tuple[Path | None, ...]) -> dict[str, Any]:
    clean_artifacts = [str(path) for path in artifacts if path]
    return {
        "step": name,
        "status": str(getattr(result, "status", "")) if not isinstance(result, dict) else str(result.get("status", "")),
        "ok": bool(getattr(result, "ok", False)) if not isinstance(result, dict) else not bool(result.get("blockers")),
        "blockers": list(getattr(result, "blockers", []) or []) if not isinstance(result, dict) else list(result.get("blockers", []) or []),
        "warnings": list(getattr(result, "warnings", []) or []) if not isinstance(result, dict) else list(result.get("warnings", []) or []),
        "artifacts": clean_artifacts,
    }


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def normalize_blocker(blocker: str) -> str:
    text = blocker.strip()
    while " blocker: " in text:
        text = text.split(" blocker: ", 1)[1].strip()
    for prefix in ("content_studio_publish_prep: ", "media_upload_executor: ", "content_studio_approval_packet: "):
        if text.startswith(prefix):
            text = text[len(prefix) :].strip()
    return text


def summarize_blockers(blockers: list[str], limit: int = 14) -> list[str]:
    seen: set[str] = set()
    summary: list[str] = []
    for blocker in blockers:
        normalized = normalize_blocker(blocker)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if len(summary) < limit:
            summary.append(normalized)
    remaining = len(seen) - len(summary)
    if remaining > 0:
        summary.append(f"... plus {remaining} more unique blocker categories in JSON evidence.")
    return summary


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Media Ready Handoff",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{summary.get('status')}`",
        f"- Media ready: `{summary.get('media_ready')}`",
        f"- Uploaded URL map: `{summary.get('uploaded_url_map_path')}`",
        "- 执行状态: media-ready handoff only；未上传媒体、未写 CMS、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把业主/上传器确认过的图片公开 URL 转成 media-ready CMS payload，并刷新 Content Studio 发布准备证据。这样图文审核包可以进入更接近执行的 handoff 阶段，但仍不会自动写入网站。",
        "",
        "## Step Status",
        "",
    ]
    for step in summary.get("steps", []):
        lines.append(f"- {step['step']}: `{step['status']}` / blockers `{len(step.get('blockers') or [])}` / artifacts `{len(step.get('artifacts') or [])}`")
    lines.extend(["", "## Blockers", ""])
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    blocker_summary = summary.get("blocker_summary") if isinstance(summary.get("blocker_summary"), list) else summarize_blockers(blockers)
    if blockers:
        lines.append(f"- 完整阻断证据数量: `{len(blockers)}`，详见 `content-studio-media-ready-handoff.json`。")
    lines.extend(f"- {item}" for item in blocker_summary) if blocker_summary else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Artifacts", ""])
    artifacts = summary.get("artifacts") if isinstance(summary.get("artifacts"), dict) else {}
    for name, path in artifacts.items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本命令只消费已确认的公开 URL；不会上传文件。",
            "- 本命令只刷新本地 CMS payload / publish-prep / approval packet；不会登录 CMS、不会调用 admin helper。",
            "- 概念图仍必须标注为 design/rendering concept，不能写成真实完工案例照片。",
            "- 真实发布仍需要业主明确执行指令、QA、backup、changelog、rollback 和对应发布门禁。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_media_ready_handoff(
    root: Path,
    *,
    upload_plan_path: str = "",
    uploaded_url_map_path: str = "",
    cms_payload_path: str = "",
    candidate_path: str = "",
    website_root: str = "",
    mode: str = "dry-run",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    storage_ready: bool = False,
    uploaded_confirmed: bool = False,
    latest_research_verified: bool = False,
    allow_blocked_plan: bool = False,
) -> tuple[dict[str, Any], tuple[Path, ...]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    uploaded_map = uploaded_url_map_path or "seo-workspace/data/uploaded-url-map.json"

    media_result, media_artifacts = run_media_upload_executor(
        root,
        upload_plan_path=upload_plan_path,
        uploaded_url_map_path=uploaded_map,
        cms_payload_path=cms_payload_path,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        storage_ready=storage_ready,
        uploaded_confirmed=uploaded_confirmed,
    )
    media_ready = media_result.status == "media_ready_payload_generated_from_uploaded_urls" and media_result.ok

    prep_summary, prep_artifacts = run_content_studio_publish_prep(
        root,
        candidate_path=candidate_path,
        website_root=website_root,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        media_ready=media_ready,
        latest_research_verified=latest_research_verified,
        allow_blocked_plan=allow_blocked_plan,
    )
    packet_summary, packet_artifacts = run_content_studio_approval_packet(root)

    steps = [
        result_summary("media_upload_executor", media_result, media_artifacts),
        result_summary("content_studio_publish_prep", prep_summary, prep_artifacts),
        result_summary("content_studio_approval_packet", packet_summary, packet_artifacts),
    ]
    blockers: list[str] = []
    warnings: list[str] = []
    for step in steps:
        blockers.extend(f"{step['step']}: {blocker}" for blocker in step.get("blockers", []))
        warnings.extend(f"{step['step']}: {warning}" for warning in step.get("warnings", []))

    status = "media_ready_handoff_waiting_owner_review" if media_ready else "media_ready_handoff_blocked"
    data_path = data_dir / SUMMARY_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "media_ready": media_ready,
        "uploaded_url_map_path": str((root / uploaded_map).resolve()) if not Path(uploaded_map).is_absolute() else uploaded_map,
        "steps": steps,
        "blockers": blockers,
        "blocker_summary": summarize_blockers(blockers),
        "warnings": warnings,
        "artifacts": {
            "media_ready_handoff_json": str(data_path),
            "media_ready_handoff_report": str(report_path),
            "media_url_map": str(media_artifacts[2]) if len(media_artifacts) > 2 and media_artifacts[2] else "",
            "media_ready_cms_payload": str(media_artifacts[3]) if len(media_artifacts) > 3 and media_artifacts[3] else "",
            "content_studio_publish_prep_json": str(prep_artifacts[-2]) if len(prep_artifacts) >= 2 else "",
            "content_studio_publish_prep_report": str(prep_artifacts[-1]) if prep_artifacts else "",
            "approval_packet_json": str(packet_artifacts[0]) if packet_artifacts else "",
            "approval_packet_report": str(packet_artifacts[1]) if len(packet_artifacts) > 1 else "",
        },
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, report_path, *[path for path in media_artifacts if path], *prep_artifacts, *packet_artifacts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a media-ready Content Studio handoff from confirmed uploaded URLs; does not upload or publish.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--upload-plan-path", default="")
    parser.add_argument("--uploaded-url-map-path", default="")
    parser.add_argument("--cms-payload-path", default="")
    parser.add_argument("--candidate-path", default="")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--storage-ready", action="store_true")
    parser.add_argument("--uploaded-confirmed", action="store_true")
    parser.add_argument("--latest-research-verified", action="store_true")
    parser.add_argument("--allow-blocked-plan", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_media_ready_handoff(
        Path(args.root),
        upload_plan_path=args.upload_plan_path,
        uploaded_url_map_path=args.uploaded_url_map_path,
        cms_payload_path=args.cms_payload_path,
        candidate_path=args.candidate_path,
        website_root=args.website_root,
        mode=args.mode,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        storage_ready=args.storage_ready,
        uploaded_confirmed=args.uploaded_confirmed,
        latest_research_verified=args.latest_research_verified,
        allow_blocked_plan=args.allow_blocked_plan,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "media_ready_handoff_waiting_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
