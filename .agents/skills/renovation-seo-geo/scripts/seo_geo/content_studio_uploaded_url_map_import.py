#!/usr/bin/env python3
"""Import an owner-filled uploaded URL map after validating it against the current template."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:  # pragma: no cover - package import path differs between CLI and tests
    from .content_studio_uploaded_url_map_draft import DEFAULT_OUTPUT, DEFAULT_TEMPLATE, normalize_files, safe_list, validate_files
except ImportError:  # pragma: no cover
    from content_studio_uploaded_url_map_draft import DEFAULT_OUTPUT, DEFAULT_TEMPLATE, normalize_files, safe_list, validate_files


DEFAULT_FILLED = "seo-workspace/data/uploaded-url-map.filled.json"
SUMMARY_NAME = "content-studio-uploaded-url-map-import.json"
REPORT_NAME = "content-studio-uploaded-url-map-import.md"


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


def placeholder_set(files: list[dict[str, Any]]) -> set[str]:
    return {
        str(item.get("placeholder_filename") or item.get("filename") or "").strip()
        for item in files
        if str(item.get("placeholder_filename") or item.get("filename") or "").strip()
    }


def compare_template(filled_files: list[dict[str, Any]], template_files: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    filled = placeholder_set(filled_files)
    template = placeholder_set(template_files)
    if not template:
        warnings.append("Missing or empty uploaded-url-map.template.json; import validates URL shape but cannot compare current media queue.")
        return blockers, warnings
    missing = sorted(template - filled)
    extra = sorted(filled - template)
    if missing:
        blockers.append("Filled uploaded URL map is missing current placeholders: " + ", ".join(missing))
    if extra:
        blockers.append("Filled uploaded URL map contains placeholders not in the current template: " + ", ".join(extra))
    return blockers, warnings


def build_import_summary(
    *,
    filled_path: Path,
    template_path: Path,
    output_path: Path,
    filled_payload: dict[str, Any],
    template_payload: dict[str, Any],
) -> dict[str, Any]:
    files = normalize_files(filled_payload)
    template_files = normalize_files(template_payload)
    file_blockers, file_warnings, ready = validate_files(files)
    template_blockers, template_warnings = compare_template(files, template_files)
    blockers = file_blockers + template_blockers
    warnings = file_warnings + template_warnings
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "uploaded_url_map_imported_waiting_media_status" if not blockers else "uploaded_url_map_import_blocked",
        "filled_map_path": str(filled_path),
        "template_path": str(template_path),
        "output_path": str(output_path),
        "ready_file_count": len(ready),
        "total_file_count": len(files),
        "files": files,
        "validation": {
            "blockers": blockers,
            "warnings": warnings,
            "ready_placeholders": ready,
            "template_placeholders": sorted(placeholder_set(template_files)),
            "filled_placeholders": sorted(placeholder_set(files)),
        },
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }


def render_report(summary: dict[str, Any]) -> str:
    validation = summary.get("validation") if isinstance(summary.get("validation"), dict) else {}
    lines = [
        "# Content Studio Uploaded URL Map Import",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{summary.get('status')}`",
        f"- Filled map: `{summary.get('filled_map_path')}`",
        f"- Output: `{summary.get('output_path')}`",
        f"- Ready URLs: `{summary.get('ready_file_count')}/{summary.get('total_file_count')}`",
        "- 执行状态: import/validation only；未上传媒体、未写 CMS、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把浏览器表单导出的 uploaded-url-map.json 增加安全导入步骤：先校验公开 HTTPS URL、owner confirmation 和当前模板占位符匹配，再写入工作区供 media-status / media-ready handoff 使用。",
        "",
        "## Blockers",
        "",
    ]
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
            "- 如果状态是 `uploaded_url_map_imported_waiting_media_status`，运行 `content-studio-media-status` 复查媒体 URL 状态。",
            "- 如果 URL 和确认都齐全，再按业主决定进入 `content-studio-media-ready-handoff`。",
            "- 如果有 blockers，回到图片 URL 填写表单修正后重新导入。",
            "",
            "## 安全边界",
            "",
            "- 本命令只导入本地 JSON，不上传文件、不调用 CMS、不写源码、不发布、不部署。",
            "- 导入成功也不代表允许发布；仍需要业主审核、明确执行、QA、media-ready、backup、changelog 和 rollback gates。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_uploaded_url_map_import(
    root: Path,
    *,
    filled_map_path: str = "",
    template_path: str = "",
    output_path: str = "",
) -> tuple[dict[str, Any], tuple[Path, Path, Path]]:
    root = root.resolve()
    filled_file = resolve_path(root, filled_map_path or DEFAULT_FILLED)
    template_file = resolve_path(root, template_path or DEFAULT_TEMPLATE)
    output_file = resolve_path(root, output_path or DEFAULT_OUTPUT)
    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    filled_payload = read_json(filled_file)
    template_payload = read_json(template_file)
    summary = build_import_summary(
        filled_path=filled_file,
        template_path=template_file,
        output_path=output_file,
        filled_payload=filled_payload,
        template_payload=template_payload,
    )
    if summary["status"] != "uploaded_url_map_import_blocked":
        imported_payload = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "status": "uploaded_url_map_imported_from_owner_editor",
            "source_filled_map_path": str(filled_file),
            "template_path": str(template_file),
            "files": summary["files"],
            "validation": summary["validation"],
            "no_media_upload_executed": True,
            "no_cms_write_executed": True,
            "no_source_write_executed": True,
            "no_publish_executed": True,
            "owner_review_required": True,
        }
        write_text(output_file, json.dumps(imported_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, output_file, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import and validate an owner-filled uploaded URL map.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--filled-map-path", default="")
    parser.add_argument("--template-path", default="")
    parser.add_argument("--output-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_uploaded_url_map_import(
        Path(args.root),
        filled_map_path=args.filled_map_path,
        template_path=args.template_path,
        output_path=args.output_path,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "uploaded_url_map_imported_waiting_media_status" else 1


if __name__ == "__main__":
    raise SystemExit(main())
