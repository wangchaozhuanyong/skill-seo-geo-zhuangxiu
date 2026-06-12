#!/usr/bin/env python3
"""Summarize Content Studio media URL readiness without uploading or publishing."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from content_studio_uploaded_url_map_draft import normalize_files, validate_files


SUMMARY_NAME = "content-studio-media-status.json"
REPORT_NAME = "content-studio-media-status.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_path(root: Path, value: str, default: str) -> Path:
    raw = value or default
    path = Path(raw)
    return path if path.is_absolute() else root / path


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def file_status_rows(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(files, start=1):
        placeholder = str(item.get("placeholder_filename") or item.get("filename") or f"file_{index}")
        file_url = str(item.get("file_url", "")).strip()
        owner_confirmed = item.get("owner_url_confirmed") is True
        if not file_url:
            status = "missing_public_url"
        elif file_url.startswith("NEEDS_"):
            status = "placeholder_url_remaining"
        elif not file_url.startswith("https://"):
            status = "non_https_url"
        elif not owner_confirmed:
            status = "needs_owner_confirmation"
        else:
            status = "ready"
        rows.append(
            {
                "placeholder_filename": placeholder,
                "object_path": item.get("object_path", ""),
                "file_url": file_url,
                "owner_url_confirmed": owner_confirmed,
                "status": status,
                "concept_label": item.get("concept_label", ""),
                "claim_boundary": item.get("claim_boundary", ""),
            }
        )
    return rows


def derive_next_actions(*, files: list[dict[str, Any]], blockers: list[str], media_ready_payload: dict[str, Any]) -> list[str]:
    if media_ready_payload:
        return [
            "媒体 URL 和 media-ready CMS payload 已存在；下一步刷新 publish-readiness / publish-bundle，并等待业主明确执行指令。",
        ]
    if not files:
        return [
            "先运行 content-studio-media-url-template 生成 uploaded-url-map.template.json。",
            "如果还没有媒体计划，先运行 media-assets / concept-assets / media-upload-plan。",
        ]
    missing = [row for row in file_status_rows(files) if row["status"] in {"missing_public_url", "placeholder_url_remaining", "non_https_url"}]
    unconfirmed = [row for row in file_status_rows(files) if row["status"] == "needs_owner_confirmation"]
    if missing:
        return [
            "先上传或选择效果图/概念图，把每个 file_url 填成真实公开 HTTPS URL。",
            "不要使用 localhost、临时预览链接、NEEDS_PUBLIC_URL 或需要登录才能访问的链接。",
            "填完后重新运行 content-studio-media-status 或 content-studio-uploaded-url-map-draft --validate-only。",
        ]
    if unconfirmed:
        return [
            "所有 URL 已是 HTTPS，但还有 owner_url_confirmed 不是 true；确认图片可公开使用后把它们改成 true。",
            "确认后运行 content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed。",
        ]
    if blockers:
        return [
            "先处理 blockers 列表，再运行 content-studio-media-ready-handoff。",
        ]
    return [
        "URL 和确认标记已就绪；运行 content-studio-media-ready-handoff 生成 media-ready CMS payload 和发布前 handoff 证据。",
    ]


def render_report(summary: dict[str, Any]) -> str:
    counts = summary.get("counts") if isinstance(summary.get("counts"), dict) else {}
    lines = [
        "# Content Studio Media Status",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{summary.get('status')}`",
        f"- Uploaded URL map: `{summary.get('uploaded_url_map_path')}`",
        f"- Media-ready payload present: `{summary.get('media_ready_payload_present')}`",
        f"- URLs ready: `{counts.get('ready', 0)}/{counts.get('total', 0)}`",
        "- 执行状态: status/report only；未上传媒体、未写 CMS、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把图文内容发布链路中的媒体状态单独汇总：哪些效果图 URL 还没填、哪些 URL 还没确认、media-ready payload 是否已经生成。这样后续自动化可以明确停在正确步骤，而不是反复猜卡点。",
        "",
        "## 图片 URL 状态",
        "",
    ]
    rows = safe_list(summary.get("files"))
    if rows:
        for row in rows:
            lines.append(
                f"- `{row.get('placeholder_filename')}`: `{row.get('status')}` -> `{row.get('file_url') or 'TO_FILL'}`"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    blockers = safe_list(summary.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## 下一步", ""])
    for action in safe_list(summary.get("next_actions")):
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 本命令只读现有媒体/发布证据并写本地状态报告。",
            "- 不上传图片、不调用 CMS/admin helper、不写源码、不发布、不部署。",
            "- 生成或选择的装修图片只能作为设计方案、效果图方案、design/rendering concept 使用，不能描述成真实完工案例或真实客户照片。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_media_status(
    root: Path,
    *,
    uploaded_url_map_path: str = "",
    template_path: str = "",
    media_url_map_path: str = "",
    media_ready_payload_path: str = "",
    publish_readiness_path: str = "",
) -> tuple[dict[str, Any], tuple[Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    uploaded_file = resolve_path(root, uploaded_url_map_path, "seo-workspace/data/uploaded-url-map.json")
    template_file = resolve_path(root, template_path, "seo-workspace/data/uploaded-url-map.template.json")
    media_url_map_file = resolve_path(root, media_url_map_path, "seo-workspace/data/media-url-map.json")
    media_ready_file = resolve_path(root, media_ready_payload_path, "seo-workspace/data/rich-content-cms-payload.media-ready.json")
    readiness_file = resolve_path(root, publish_readiness_path, "seo-workspace/data/publish-readiness.json")

    uploaded_data = read_json(uploaded_file)
    template_data = read_json(template_file)
    source_data = uploaded_data or template_data
    files = normalize_files(source_data)
    blockers, warnings, ready = validate_files(files)
    rows = file_status_rows(files)
    media_url_map = read_json(media_url_map_file)
    media_ready_payload = read_json(media_ready_file)
    readiness = read_json(readiness_file)

    if media_ready_payload and media_url_map:
        status = "media_ready_payload_present"
    elif files and not blockers and len(ready) == len(files):
        status = "media_urls_ready_for_handoff"
    elif files:
        status = "media_urls_need_owner_input"
    else:
        status = "blocked_missing_media_url_template"

    counts = {
        "total": len(rows),
        "ready": sum(1 for row in rows if row["status"] == "ready"),
        "missing_public_url": sum(1 for row in rows if row["status"] == "missing_public_url"),
        "placeholder_url_remaining": sum(1 for row in rows if row["status"] == "placeholder_url_remaining"),
        "non_https_url": sum(1 for row in rows if row["status"] == "non_https_url"),
        "needs_owner_confirmation": sum(1 for row in rows if row["status"] == "needs_owner_confirmation"),
    }
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "uploaded_url_map_path": str(uploaded_file),
        "template_path": str(template_file),
        "source": "uploaded_url_map" if uploaded_data else "template" if template_data else "missing",
        "files": rows,
        "counts": counts,
        "blockers": blockers,
        "warnings": warnings,
        "ready_placeholders": ready,
        "media_url_map_present": bool(media_url_map),
        "media_ready_payload_present": bool(media_ready_payload),
        "publish_readiness_status": readiness.get("status", "") if readiness else "",
        "next_actions": derive_next_actions(files=files, blockers=blockers, media_ready_payload=media_ready_payload),
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    data_path = data_dir / SUMMARY_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize Content Studio media URL readiness without uploading or publishing.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--uploaded-url-map-path", default="")
    parser.add_argument("--template-path", default="")
    parser.add_argument("--media-url-map-path", default="")
    parser.add_argument("--media-ready-payload-path", default="")
    parser.add_argument("--publish-readiness-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_media_status(
        Path(args.root),
        uploaded_url_map_path=args.uploaded_url_map_path,
        template_path=args.template_path,
        media_url_map_path=args.media_url_map_path,
        media_ready_payload_path=args.media_ready_payload_path,
        publish_readiness_path=args.publish_readiness_path,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] in {"media_urls_ready_for_handoff", "media_ready_payload_present"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
