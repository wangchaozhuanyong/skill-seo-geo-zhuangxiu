#!/usr/bin/env python3
"""Create a gated media upload execution request and consume uploaded URL results."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

from media_assets import replace_media_urls, select_cms_payload_file


MEDIA_UPLOAD_EXECUTION_REQUEST = "media-upload-execution-request.json"
MEDIA_URL_MAP_NAME = "media-url-map.json"


@dataclass
class MediaUploadExecutorResult:
    status: str
    planned_upload_count: int
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


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def queue_rows(plan: dict[str, object]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in safe_list(plan.get("queue")):
        if isinstance(raw, dict) and raw.get("placeholder_filename"):
            rows.append({key: str(value or "") for key, value in raw.items()})
    return rows


def normalize_uploaded_urls(data: dict[str, object]) -> dict[str, str]:
    if "files" in data and isinstance(data["files"], list):
        result: dict[str, str] = {}
        for raw in data["files"]:
            if not isinstance(raw, dict):
                continue
            file_url = str(raw.get("file_url", "") or raw.get("url", ""))
            if not file_url:
                continue
            for key in ("placeholder_filename", "filename", "public_filename", "object_path"):
                value = str(raw.get(key, ""))
                if value:
                    result[value] = file_url
        return result
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str) and value.startswith(("http://", "https://"))}


def uploaded_url_for(row: dict[str, str], uploaded_urls: dict[str, str]) -> str:
    candidates = [
        row.get("placeholder_filename", ""),
        row.get("public_filename", ""),
        row.get("object_path", ""),
        f"{row.get('bucket', '')}/{row.get('object_path', '')}".strip("/"),
    ]
    for candidate in candidates:
        if candidate and candidate in uploaded_urls:
            return uploaded_urls[candidate]
    return ""


def planned_operations(rows: list[dict[str, str]], uploaded_urls: dict[str, str]) -> list[dict[str, object]]:
    operations: list[dict[str, object]] = []
    for row in rows:
        file_url = uploaded_url_for(row, uploaded_urls)
        operations.append(
            {
                "queue_id": row.get("queue_id", ""),
                "status": "uploaded_url_supplied" if file_url else "needs_media_upload",
                "local_path": row.get("local_path", ""),
                "bucket": row.get("bucket", ""),
                "object_path": row.get("object_path", ""),
                "content_type": row.get("mime_type", ""),
                "file_url": file_url or row.get("public_url", ""),
                "upload_helper": row.get("upload_helper", "uploadAdminMediaObject"),
                "record_helper": row.get("record_helper", "createAdminMediaAsset"),
                "media_assets_record": {
                    "file_url": file_url or row.get("public_url", ""),
                    "file_path": row.get("object_path", ""),
                    "file_name": row.get("public_filename", ""),
                    "mime_type": row.get("mime_type", ""),
                    "usage_type": row.get("usage_type", ""),
                    "folder": row.get("folder", "media"),
                    "alt_zh": row.get("alt_zh", ""),
                    "alt_en": row.get("alt_en", ""),
                    "processing_status": "ready_after_upload",
                },
                "claim_boundary": row.get("claim_boundary", ""),
            }
        )
    return operations


def render_report(result: MediaUploadExecutorResult, operations: list[dict[str, object]]) -> str:
    lines = [
        "# Media Upload Executor Dry Run",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: {result.status}",
        f"- Planned uploads: {result.planned_upload_count}",
        "- 执行状态: gated dry-run；未上传媒体、未写 media_assets、未发布",
        "",
        "## 今日决策",
        "",
        "今天把媒体上传队列推进为 gated execution request：只有在业主批准、明确上传执行、QA、storage 准备就绪，并提供已上传 URL 结果后，才生成 media-url-map 和 media-ready CMS payload。",
        "",
        "## Planned Operations",
        "",
    ]
    if operations:
        for operation in operations:
            lines.append(f"- `{operation['queue_id']}` | `{operation['status']}` | `{operation['object_path']}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
            "## Safety Notes",
            "",
            "- This executor does not upload files or call Supabase by itself.",
            "- Uploaded URLs must come from an approved upload result, not from guessed paths.",
            "- Generated concept media must remain labeled as design/rendering concept material.",
            "",
        ]
    )
    return "\n".join(lines)


def run_media_upload_executor(
    root: Path,
    *,
    upload_plan_path: str = "",
    uploaded_url_map_path: str = "",
    cms_payload_path: str = "",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    storage_ready: bool = False,
    uploaded_confirmed: bool = False,
) -> tuple[MediaUploadExecutorResult, tuple[Path, Path, Path | None, Path | None]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    upload_plan_file = Path(upload_plan_path) if upload_plan_path else data_dir / "media-upload-plan.json"
    cms_payload_file, cms_payload_selection = select_cms_payload_file(root, cms_payload_path)
    uploaded_url_file = Path(uploaded_url_map_path) if uploaded_url_map_path else Path()
    if not upload_plan_file.is_absolute():
        upload_plan_file = root / upload_plan_file
    if uploaded_url_map_path and not uploaded_url_file.is_absolute():
        uploaded_url_file = root / uploaded_url_file

    request_path = data_dir / MEDIA_UPLOAD_EXECUTION_REQUEST
    url_map_path = data_dir / MEDIA_URL_MAP_NAME
    report_path = reports_dir / f"{today}-media-upload-executor-dry-run.md"
    ready_payload_path: Path | None = None
    final_url_map_path: Path | None = None

    upload_plan = read_json(upload_plan_file)
    cms_payload = read_json(cms_payload_file)
    rows = queue_rows(upload_plan)
    uploaded_urls = normalize_uploaded_urls(read_json(uploaded_url_file)) if uploaded_url_map_path else {}
    blockers: list[str] = []
    warnings: list[str] = []
    if not rows:
        blockers.append("No media upload queue found. Run media-upload-plan first.")
    if upload_plan.get("status") not in {"owner_review_required", "ready_for_media_upload_execution"}:
        warnings.append(f"Unexpected media upload plan status: {upload_plan.get('status', 'missing')}")
    if not owner_approved:
        blockers.append("Owner has not approved this exact media upload queue (--owner-approved missing).")
    if not explicit_execution:
        blockers.append("Owner has not explicitly asked to execute media upload (--explicit-execution missing).")
    if not qa_passed:
        blockers.append("Media/pre-publish QA is not marked passed (--qa-passed missing).")
    if not storage_ready:
        blockers.append("Storage readiness is not confirmed (--storage-ready missing).")
    if uploaded_url_map_path and not uploaded_confirmed:
        blockers.append("Uploaded URL map was provided but uploaded URLs are not confirmed (--uploaded-confirmed missing).")
    if uploaded_url_map_path and uploaded_confirmed and not cms_payload:
        blockers.append("CMS payload is missing. Run rich-blocks first or provide --cms-payload-path.")

    operations = planned_operations(rows, uploaded_urls)
    if uploaded_url_map_path and uploaded_confirmed:
        missing = [row.get("placeholder_filename", "") for row in rows if not uploaded_url_for(row, uploaded_urls)]
        if missing:
            blockers.append("Uploaded URL map is missing URLs for: " + ", ".join(missing))

    status = "blocked_before_media_upload"
    if rows and not blockers:
        status = "ready_for_media_upload_execution"
        if uploaded_url_map_path and uploaded_confirmed:
            url_map = {row["placeholder_filename"]: uploaded_url_for(row, uploaded_urls) for row in rows}
            write_text(url_map_path, json.dumps(url_map, ensure_ascii=False, indent=2) + "\n")
            ready_payload_path = data_dir / "rich-content-cms-payload.media-ready.json"
            write_text(ready_payload_path, json.dumps(replace_media_urls(cms_payload, url_map), ensure_ascii=False, indent=2) + "\n")
            final_url_map_path = url_map_path
            status = "media_ready_payload_generated_from_uploaded_urls"
    elif not uploaded_url_map_path:
        warnings.append("No uploaded URL map supplied; media-ready CMS payload was not generated.")

    result = MediaUploadExecutorResult(status=status, planned_upload_count=len(rows), blockers=blockers, warnings=warnings)
    result.artifacts.update({"execution_request": str(request_path), "report": str(report_path)})
    if final_url_map_path:
        result.artifacts["media_url_map"] = str(final_url_map_path)
    if ready_payload_path:
        result.artifacts["media_ready_cms_payload"] = str(ready_payload_path)
    write_text(
        request_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "no_media_upload_executed": True,
                "cms_payload_path": str(cms_payload_file),
                "cms_payload_selection": cms_payload_selection,
                "owner_approved": owner_approved,
                "explicit_execution": explicit_execution,
                "qa_passed": qa_passed,
                "storage_ready": storage_ready,
                "uploaded_confirmed": uploaded_confirmed,
                "blockers": blockers,
                "warnings": warnings,
                "operations": operations,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result, operations))
    return result, (request_path, report_path, final_url_map_path, ready_payload_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a gated media upload execution request; does not upload.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--upload-plan-path", default="")
    parser.add_argument("--uploaded-url-map-path", default="")
    parser.add_argument("--cms-payload-path", default="")
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--storage-ready", action="store_true")
    parser.add_argument("--uploaded-confirmed", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, _ = run_media_upload_executor(
        Path(args.root),
        upload_plan_path=args.upload_plan_path,
        uploaded_url_map_path=args.uploaded_url_map_path,
        cms_payload_path=args.cms_payload_path,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        storage_ready=args.storage_ready,
        uploaded_confirmed=args.uploaded_confirmed,
    )
    for artifact in result.artifacts.values():
        print(artifact)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
