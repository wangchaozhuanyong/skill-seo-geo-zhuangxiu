#!/usr/bin/env python3
"""Create an uploaded URL map template for Content Studio concept media."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


DEFAULT_MEDIA_PLAN = "seo-workspace/data/media-upload-plan.json"
TEMPLATE_NAME = "uploaded-url-map.template.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def queue_rows(media_plan: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    raw_queue = media_plan.get("queue")
    if not isinstance(raw_queue, list):
        return rows
    for raw in raw_queue:
        if not isinstance(raw, dict) or not raw.get("placeholder_filename"):
            continue
        rows.append({key: str(value or "") for key, value in raw.items()})
    return rows


def prefilled_url(public_base_url: str, object_path: str) -> str:
    if not public_base_url:
        return ""
    return public_base_url.rstrip("/") + "/" + object_path.lstrip("/")


def build_template(media_plan: dict[str, Any], public_base_url: str = "") -> dict[str, Any]:
    files: list[dict[str, str]] = []
    for row in queue_rows(media_plan):
        object_path = row.get("object_path", "")
        files.append(
            {
                "placeholder_filename": row.get("placeholder_filename", ""),
                "filename": row.get("placeholder_filename", ""),
                "public_filename": row.get("public_filename", ""),
                "object_path": object_path,
                "bucket": row.get("bucket", ""),
                "local_path": row.get("local_path", ""),
                "file_url": prefilled_url(public_base_url, object_path),
                "alt_zh": row.get("alt_zh", ""),
                "alt_en": row.get("alt_en", ""),
                "claim_boundary": row.get("claim_boundary", ""),
                "note_zh": "请把 file_url 替换为已上传后的公开 HTTPS URL；不要使用 NEEDS_PUBLIC_URL 占位。",
            }
        )
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "uploaded_url_map_template_ready" if files else "blocked_missing_media_upload_plan",
        "source_media_plan_status": str(media_plan.get("status", "")),
        "public_base_url_prefilled": bool(public_base_url),
        "instructions_zh": [
            "上传或选择这些概念效果图后，把每个 file_url 填成真实公开 HTTPS URL。",
            "保留 placeholder_filename/public_filename/object_path 字段，media-upload-executor 会用它们匹配正文占位图。",
            "这些图片必须继续标注为 concept/rendering/design concept，不得写成真实完工案例或客户照片。",
        ],
        "files": files,
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_publish_executed": True,
        "owner_review_required": True,
    }


def render_report(template: dict[str, Any], output_path: Path) -> str:
    lines = [
        "# Content Studio Uploaded URL Map Template",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        "- 执行模式: template only / no upload / no publish",
        f"- 状态: {template['status']}",
        f"- Template: `{output_path}`",
        "- 执行状态: 等待业主审核、上传媒体并填写公开 URL",
        "",
        "## 今日决策",
        "",
        "今天把概念效果图上传队列转换成 uploaded URL map 模板，方便后续在已上传 URL 确认后生成 media-ready CMS payload。",
        "",
        "## Files To Fill",
        "",
    ]
    files = template.get("files") or []
    if files:
        for item in files:
            lines.append(f"- `{item.get('placeholder_filename')}` -> `{item.get('object_path')}` -> file_url `{item.get('file_url') or 'TO_FILL'}`")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 上传/选择概念效果图，并把公开 HTTPS URL 填入模板里的 `file_url`。",
            "- 将填写后的文件另存为 `seo-workspace/data/uploaded-url-map.json`。",
            "- 业主明确批准媒体上传结果后，再运行 `media-upload-executor --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --uploaded-confirmed ...`。",
            "",
            "## 安全边界",
            "",
            "- 本命令不上传媒体、不调用 CMS、不写源码、不发布、不部署。",
            "- 生成/上传的装修图片必须保持设计方案、效果图方案或 rendering concept 标签。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_media_url_template(
    root: Path,
    *,
    media_plan_path: str = "",
    output_path: str = "",
    public_base_url: str = "",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    media_file = resolve_path(root, media_plan_path or DEFAULT_MEDIA_PLAN)
    output_file = resolve_path(root, output_path or f"seo-workspace/data/{TEMPLATE_NAME}")
    report_file = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-media-url-template.md"
    media_plan = read_json(media_file)
    template = build_template(media_plan, public_base_url=public_base_url)
    template["media_plan_path"] = str(media_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_file.write_text(render_report(template, output_file), encoding="utf-8")
    return template, [output_file, report_file]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an uploaded URL map template for Content Studio concept media.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--media-plan-path", default="")
    parser.add_argument("--output-path", default="")
    parser.add_argument("--public-base-url", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    template, artifacts = run_content_studio_media_url_template(
        Path(args.root),
        media_plan_path=args.media_plan_path,
        output_path=args.output_path,
        public_base_url=args.public_base_url,
    )
    for output in artifacts:
        print(output)
    return 0 if template["status"] == "uploaded_url_map_template_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
