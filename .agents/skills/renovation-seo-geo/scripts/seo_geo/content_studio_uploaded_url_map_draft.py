#!/usr/bin/env python3
"""Create and validate an owner-fillable uploaded URL map draft."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


DEFAULT_TEMPLATE = "seo-workspace/data/uploaded-url-map.template.json"
DEFAULT_OUTPUT = "seo-workspace/data/uploaded-url-map.json"
REPORT_NAME = "content-studio-uploaded-url-map-draft.md"


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


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def normalize_files(data: dict[str, Any]) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for raw in safe_list(data.get("files")):
        if isinstance(raw, dict):
            item = dict(raw)
            item.setdefault("file_url", "")
            item.setdefault("owner_url_confirmed", False)
            item.setdefault("upload_status", "needs_public_url")
            files.append(item)
    return files


def validate_files(files: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    ready: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(files, start=1):
        placeholder = str(item.get("placeholder_filename") or item.get("filename") or f"file_{index}")
        file_url = str(item.get("file_url", "")).strip()
        if placeholder in seen:
            blockers.append(f"Duplicate placeholder_filename: {placeholder}")
        seen.add(placeholder)
        if not file_url:
            blockers.append(f"Missing file_url for {placeholder}")
            continue
        if file_url.startswith("NEEDS_"):
            blockers.append(f"Placeholder file_url remains for {placeholder}: {file_url}")
            continue
        if not file_url.startswith("https://"):
            blockers.append(f"file_url must be public HTTPS for {placeholder}: {file_url}")
            continue
        if item.get("owner_url_confirmed") is not True:
            warnings.append(f"owner_url_confirmed is not true for {placeholder}; media-ready execution should still require --uploaded-confirmed.")
        ready.append(placeholder)
    if not files:
        blockers.append("No files found. Run content-studio-media-url-template first.")
    return blockers, warnings, ready


def merge_existing_public_urls(files: list[dict[str, Any]], existing: dict[str, Any]) -> list[dict[str, Any]]:
    existing_by_placeholder: dict[str, dict[str, Any]] = {}
    for raw in normalize_files(existing):
        placeholder = str(raw.get("placeholder_filename") or raw.get("filename") or "").strip()
        if placeholder:
            existing_by_placeholder[placeholder] = raw

    for item in files:
        placeholder = str(item.get("placeholder_filename") or item.get("filename") or "").strip()
        existing_item = existing_by_placeholder.get(placeholder)
        if not existing_item:
            continue
        current_url = str(item.get("file_url", "")).strip()
        existing_url = str(existing_item.get("file_url", "")).strip()
        if current_url and not current_url.startswith("NEEDS_"):
            continue
        if not existing_url.startswith("https://") or existing_url.startswith("NEEDS_"):
            continue
        item["file_url"] = existing_url
        item["owner_url_confirmed"] = existing_item.get("owner_url_confirmed", item.get("owner_url_confirmed", False))
        item["upload_status"] = existing_item.get("upload_status") or "existing_public_url_preserved"
    return files


def build_draft(template: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    files = normalize_files(template)
    if existing:
        files = merge_existing_public_urls(files, existing)
    blockers, warnings, ready = validate_files(files)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "uploaded_url_map_ready_for_confirmation" if files and not blockers else "uploaded_url_map_needs_owner_urls",
        "source_template_status": template.get("status", ""),
        "instructions_zh": [
            "把每个 file_url 填成真实、可公开访问的 HTTPS 图片 URL。",
            "不要填写 NEEDS_PUBLIC_URL、localhost、临时预览链接或需要登录才能访问的链接。",
            "每张图片仍然只能作为设计方案/效果图方案/concept rendering 使用，不得写成真实完工案例照片。",
            "填写完成后，将 owner_url_confirmed 改为 true，并让 Codex 运行 content-studio-media-ready-handoff。",
        ],
        "files": files,
        "validation": {
            "ready_file_count": len(ready),
            "total_file_count": len(files),
            "blockers": blockers,
            "warnings": warnings,
            "ready_placeholders": ready,
        },
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_publish_executed": True,
        "owner_review_required": True,
    }


def render_report(draft: dict[str, Any], output_path: Path) -> str:
    validation = draft.get("validation") if isinstance(draft.get("validation"), dict) else {}
    files = safe_list(draft.get("files"))
    lines = [
        "# Content Studio Uploaded URL Map Draft",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{draft.get('status')}`",
        f"- Output: `{output_path}`",
        f"- Ready URLs: `{validation.get('ready_file_count', 0)}/{validation.get('total_file_count', 0)}`",
        "- 执行状态: owner-fillable draft / no upload / no CMS / no publish",
        "",
        "## 今日决策",
        "",
        "今天把 uploaded URL map 模板转换成业主/上传器可填写草稿，并立即校验是否还有空 URL、非 HTTPS URL 或占位 URL。这样后续 media-ready handoff 不会因为字段填错而反复卡住。",
        "",
        "## 需要填写的图片 URL",
        "",
    ]
    if files:
        for item in files:
            url = str(item.get("file_url", "") or "TO_FILL")
            lines.append(f"- `{item.get('placeholder_filename')}` -> `{item.get('object_path')}` -> `{url}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    blockers = safe_list(validation.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = safe_list(validation.get("warnings"))
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 如果还有 `Missing file_url`，先上传/选择图片，然后把公开 HTTPS URL 填入 `file_url`。",
            "- 如果所有 URL 都已填好，把对应 `owner_url_confirmed` 改为 `true`。",
            "- 然后运行：`content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed`。",
            "",
            "## 安全边界",
            "",
            "- 本命令不上传图片、不调用 CMS、不写源码、不发布、不部署。",
            "- URL 只能证明图片可访问，不能把效果图描述成真实案例或真实客户照片。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_uploaded_url_map_draft(
    root: Path,
    *,
    template_path: str = "",
    output_path: str = "",
    validate_only: bool = False,
) -> tuple[dict[str, Any], tuple[Path, Path]]:
    root = root.resolve()
    template_file = resolve_path(root, template_path or DEFAULT_TEMPLATE)
    output_file = resolve_path(root, output_path or DEFAULT_OUTPUT)
    report_file = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    source = read_json(output_file if validate_only and output_file.exists() else template_file)
    existing = {} if validate_only else read_json(output_file)
    draft = build_draft(source, existing)
    draft["template_path"] = str(template_file)
    draft["output_path"] = str(output_file)
    if validate_only:
        draft["mode"] = "validate_only"
    else:
        draft["mode"] = "draft_written"
        write_text(output_file, json.dumps(draft, ensure_ascii=False, indent=2) + "\n")
    write_text(report_file, render_report(draft, output_file))
    return draft, (output_file, report_file)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or validate owner-fillable uploaded URL map draft.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--template-path", default="")
    parser.add_argument("--output-path", default="")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    draft, artifacts = run_content_studio_uploaded_url_map_draft(
        Path(args.root),
        template_path=args.template_path,
        output_path=args.output_path,
        validate_only=args.validate_only,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if draft["status"] == "uploaded_url_map_ready_for_confirmation" else 1


if __name__ == "__main__":
    raise SystemExit(main())
