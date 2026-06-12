#!/usr/bin/env python3
"""Create a gated media upload queue from generated concept assets."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path


MEDIA_UPLOAD_QUEUE_CSV = "media-upload-queue.csv"
MEDIA_UPLOAD_PLAN_JSON = "media-upload-plan.json"


@dataclass
class MediaUploadPlanResult:
    status: str
    queue_count: int
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def media_assets_from_plan(plan: dict[str, object]) -> dict[str, dict[str, object]]:
    assets: dict[str, dict[str, object]] = {}
    for raw in safe_list(plan.get("media_assets")):
        if isinstance(raw, dict) and raw.get("filename"):
            assets[str(raw["filename"])] = raw
    return assets


def concept_assets_from_manifest(manifest: dict[str, object]) -> dict[str, dict[str, str]]:
    assets: dict[str, dict[str, str]] = {}
    for raw in safe_list(manifest.get("assets")):
        if not isinstance(raw, dict):
            continue
        placeholder = str(raw.get("placeholder_filename", ""))
        if not placeholder:
            continue
        assets[placeholder] = {key: str(value or "") for key, value in raw.items()}
    return assets


def manifest_rows_by_placeholder(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("filename", ""): row for row in rows if row.get("filename")}


def safe_object_path(value: str) -> str:
    return value.replace(" ", "-").replace("\\", "/").lstrip("/")


def media_asset_record(row: dict[str, str], plan_item: dict[str, object], public_url: str) -> dict[str, object]:
    return {
        "file_url": public_url or f"NEEDS_PUBLIC_URL:{row['bucket']}/{row['object_path']}",
        "file_path": row["object_path"],
        "file_name": row["public_filename"],
        "mime_type": row["mime_type"],
        "size_bytes": None,
        "width": None,
        "height": None,
        "usage_type": row["usage_type"],
        "folder": row["folder"],
        "alt_zh": plan_item.get("alt_zh", ""),
        "alt_en": plan_item.get("alt_en", ""),
        "processing_status": "ready_after_upload",
    }


def build_queue_rows(
    *,
    media_plan: dict[str, object],
    concept_manifest: dict[str, object],
    file_manifest_rows: list[dict[str, str]],
    bucket: str,
    storage_prefix: str,
    public_base_url: str,
) -> tuple[list[dict[str, str]], list[str], list[str]]:
    plan_assets = media_assets_from_plan(media_plan)
    concept_assets = concept_assets_from_manifest(concept_manifest)
    file_rows = manifest_rows_by_placeholder(file_manifest_rows)
    blockers: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []
    if not plan_assets:
        blockers.append("No media assets found. Run media-assets first.")
    if not concept_assets:
        blockers.append("No concept assets found. Run concept-assets first.")

    today = dt.date.today().isoformat()
    for index, (placeholder, plan_item) in enumerate(plan_assets.items(), start=1):
        concept = concept_assets.get(placeholder, {})
        file_row = file_rows.get(placeholder, {})
        generated_filename = concept.get("generated_filename") or file_row.get("public_filename") or placeholder
        local_path = concept.get("local_path") or file_row.get("local_path") or ""
        path = Path(local_path) if local_path else Path()
        exists = "yes" if local_path and path.is_file() else "no"
        if exists != "yes":
            warnings.append(f"Local upload source missing for {placeholder}.")
        mime_type = concept.get("mime_type") or file_row.get("mime_type") or str(plan_item.get("mime_type", ""))
        object_path = safe_object_path(f"{storage_prefix.rstrip('/')}/{today}/{generated_filename}")
        public_url = f"{public_base_url.rstrip('/')}/{generated_filename}" if public_base_url else ""
        row = {
            "queue_id": f"media-upload-{index:03d}",
            "status": "owner_review_required",
            "target_url": str(plan_item.get("target_url", "")),
            "paired_url": str(plan_item.get("paired_url", "")),
            "placeholder_filename": placeholder,
            "public_filename": generated_filename,
            "local_path": local_path,
            "exists": exists,
            "bucket": bucket,
            "object_path": object_path,
            "public_url": public_url or f"NEEDS_PUBLIC_URL:{bucket}/{object_path}",
            "mime_type": mime_type,
            "folder": str(plan_item.get("folder", "media") or "media"),
            "usage_type": str(plan_item.get("usage_type", "general") or "general"),
            "alt_zh": str(plan_item.get("alt_zh", "")),
            "alt_en": str(plan_item.get("alt_en", "")),
            "claim_boundary": str(concept.get("claim_boundary") or plan_item.get("claim_boundary", "")),
            "upload_helper": "uploadAdminMediaObject",
            "record_helper": "createAdminMediaAsset",
            "execution_gate": "owner approval + explicit upload execution + storage credentials + QA + rollback note",
        }
        rows.append(row)

    return rows, blockers, warnings


def render_report(result: MediaUploadPlanResult, rows: list[dict[str, str]]) -> str:
    lines = [
        "# Media Upload Plan",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: {result.status}",
        f"- Queue items: {result.queue_count}",
        "- 执行状态: draft-only；未上传媒体、未写 media_assets、未发布",
        "",
        "## 今日决策",
        "",
        "今天把本地概念效果图文件转成可审核的媒体上传队列：明确 storage bucket/object path、媒体库字段、alt、用途分类、claim boundary 和执行门槛。",
        "",
        "## Queue",
        "",
    ]
    if rows:
        for row in rows:
            lines.append(f"- `{row['queue_id']}` | `{row['public_filename']}` | exists: `{row['exists']}` | helper: `{row['upload_helper']}` + `{row['record_helper']}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Execution Gate",
            "",
            "- Owner approves this exact media upload queue.",
            "- Owner explicitly asks to execute media upload.",
            "- Confirm Supabase storage credentials and allowed bucket.",
            "- Upload files through the website media service layer or equivalent approved helper.",
            "- Create `media_assets` records with matching alt, usage type, folder, and claim boundary.",
            "- Generate `media-url-map.json`, then regenerate media-ready CMS payload.",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
            "## Safety Notes",
            "",
            "- These assets are design/rendering concepts, not real completed project photos.",
            "- Do not use them as reviews, proof, price evidence, warranty evidence, or before/after proof.",
            "- This plan does not call CMS, Supabase, storage, or deployment.",
            "",
        ]
    )
    return "\n".join(lines)


def run_media_upload_plan(
    root: Path,
    *,
    media_plan_path: str = "",
    concept_manifest_path: str = "",
    media_file_manifest_path: str = "",
    bucket: str = "site-images",
    storage_prefix: str = "media/seo-generated",
    public_base_url: str = "",
) -> tuple[MediaUploadPlanResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()

    media_plan_file = Path(media_plan_path) if media_plan_path else data_dir / "media-asset-plan.json"
    concept_manifest_file = Path(concept_manifest_path) if concept_manifest_path else data_dir / "concept-asset-manifest.json"
    media_file_manifest_file = Path(media_file_manifest_path) if media_file_manifest_path else data_dir / "media-file-manifest.csv"
    if not media_plan_file.is_absolute():
        media_plan_file = root / media_plan_file
    if not concept_manifest_file.is_absolute():
        concept_manifest_file = root / concept_manifest_file
    if not media_file_manifest_file.is_absolute():
        media_file_manifest_file = root / media_file_manifest_file

    queue_path = data_dir / MEDIA_UPLOAD_QUEUE_CSV
    plan_path = data_dir / MEDIA_UPLOAD_PLAN_JSON
    report_path = reports_dir / f"{today}-media-upload-plan.md"
    rows, blockers, warnings = build_queue_rows(
        media_plan=read_json(media_plan_file),
        concept_manifest=read_json(concept_manifest_file),
        file_manifest_rows=read_csv_rows(media_file_manifest_file),
        bucket=bucket,
        storage_prefix=storage_prefix,
        public_base_url=public_base_url,
    )
    if any(row["exists"] != "yes" for row in rows):
        blockers.append("One or more local upload source files are missing.")
    status = "owner_review_required" if rows and not blockers else "blocked_missing_media_upload_inputs"
    result = MediaUploadPlanResult(status=status, queue_count=len(rows), blockers=blockers, warnings=warnings)
    result.artifacts.update({"upload_queue_csv": str(queue_path), "upload_plan_json": str(plan_path), "report": str(report_path)})

    fields = [
        "queue_id",
        "status",
        "target_url",
        "paired_url",
        "placeholder_filename",
        "public_filename",
        "local_path",
        "exists",
        "bucket",
        "object_path",
        "public_url",
        "mime_type",
        "folder",
        "usage_type",
        "alt_zh",
        "alt_en",
        "claim_boundary",
        "upload_helper",
        "record_helper",
        "execution_gate",
    ]
    write_csv(queue_path, rows, fields)
    records = []
    plan_assets = media_assets_from_plan(read_json(media_plan_file))
    for row in rows:
        public_url = "" if row["public_url"].startswith("NEEDS_PUBLIC_URL:") else row["public_url"]
        records.append(media_asset_record(row, plan_assets.get(row["placeholder_filename"], {}), public_url))
    write_text(
        plan_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "no_media_upload_executed": True,
                "bucket": bucket,
                "storage_prefix": storage_prefix,
                "queue": rows,
                "media_assets_record_drafts": records,
                "blockers": blockers,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result, rows))
    return result, (queue_path, plan_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a draft-only media upload queue from generated concept assets.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--media-plan-path", default="")
    parser.add_argument("--concept-manifest-path", default="")
    parser.add_argument("--media-file-manifest-path", default="")
    parser.add_argument("--bucket", default="site-images")
    parser.add_argument("--storage-prefix", default="media/seo-generated")
    parser.add_argument("--public-base-url", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, _ = run_media_upload_plan(
        Path(args.root),
        media_plan_path=args.media_plan_path,
        concept_manifest_path=args.concept_manifest_path,
        media_file_manifest_path=args.media_file_manifest_path,
        bucket=args.bucket,
        storage_prefix=args.storage_prefix,
        public_base_url=args.public_base_url,
    )
    for artifact in result.artifacts.values():
        print(artifact)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
