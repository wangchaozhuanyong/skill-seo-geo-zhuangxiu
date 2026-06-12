#!/usr/bin/env python3
"""Build a media URL map from local generated/selected files."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

from media_assets import run_media_assets


MEDIA_FILE_MANIFEST_NAME = "media-file-manifest.csv"
MEDIA_URL_MAP_NAME = "media-url-map.json"


@dataclass
class MediaUrlMapResult:
    status: str
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


def media_assets_from_plan(plan: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in safe_list(plan.get("media_assets")):
        if isinstance(raw, dict) and raw.get("filename"):
            rows.append(raw)
    return rows


def join_url(base_url: str, filename: str) -> str:
    return f"{base_url.rstrip('/')}/{filename.lstrip('/')}"


def candidate_asset_paths(asset_dir: Path, filename: str) -> list[Path]:
    original = asset_dir / filename
    stem = Path(filename).stem
    candidates = [original]
    for suffix in (".svg", ".webp", ".png", ".jpg", ".jpeg"):
        candidate = asset_dir / f"{stem}{suffix}"
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def resolve_asset_path(asset_dir: Path, filename: str) -> Path:
    for candidate in candidate_asset_paths(asset_dir, filename):
        if candidate.is_file():
            return candidate
    return asset_dir / filename


def mime_type_for(path: Path, fallback: str) -> str:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return "image/svg+xml"
    if suffix == ".webp":
        return "image/webp"
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return fallback


def build_manifest_rows(media_assets: list[dict[str, object]], asset_dir: Path, public_base_url: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in media_assets:
        filename = str(item.get("filename", ""))
        local_path = resolve_asset_path(asset_dir, filename)
        public_filename = local_path.name if local_path.is_file() else filename
        rows.append(
            {
                "filename": filename,
                "public_filename": public_filename,
                "local_path": str(local_path),
                "exists": "yes" if local_path.is_file() else "no",
                "file_url": join_url(public_base_url, public_filename) if public_base_url else "",
                "usage_type": str(item.get("usage_type", "")),
                "mime_type": mime_type_for(local_path, str(item.get("mime_type", ""))),
                "placeholder_mime_type": str(item.get("mime_type", "")),
                "alt_zh": str(item.get("alt_zh", "")),
                "alt_en": str(item.get("alt_en", "")),
                "claim_boundary": str(item.get("claim_boundary", "")),
            }
        )
    return rows


def write_manifest(path: Path, rows: list[dict[str, str]]) -> Path:
    fields = ["filename", "public_filename", "local_path", "exists", "file_url", "usage_type", "mime_type", "placeholder_mime_type", "alt_zh", "alt_en", "claim_boundary"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def render_report(result: MediaUrlMapResult, rows: list[dict[str, str]], asset_dir: Path, public_base_url: str) -> str:
    lines = [
        "# Media URL Map Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: {result.status}",
        f"- Asset dir: `{asset_dir}`",
        f"- Public base URL: `{public_base_url or 'NEEDS OWNER INPUT'}`",
        "- 执行状态: dry-run / manifest-only；未上传媒体、未写 CMS、未发布",
        "",
        "## 今日决策",
        "",
        "今天把已生成/已选择的本地效果图文件映射为媒体 URL map；只有文件齐全且 URL 前缀明确时，才会产出 media-ready CMS payload。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## File Manifest", ""])
    for row in rows:
        lines.append(f"- `{row['filename']}` | exists: `{row['exists']}` | url: `{row['file_url'] or 'N/A'}`")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
            "## Safety Notes",
            "",
            "- 本命令不上传媒体，也不验证 CDN/线上 URL 是否已公开可访问。",
            "- URL map 只应使用已生成、已选择、已上传并可用于网站的概念设计/效果图文件。",
            "- 生成图仍不能作为真实完工案例、客户照片、评价或 before/after proof。",
            "",
        ]
    )
    return "\n".join(lines)


def run_media_url_map(
    root: Path,
    *,
    asset_dir: str = "",
    public_base_url: str = "",
    media_plan_path: str = "",
) -> tuple[MediaUrlMapResult, tuple[Path, Path | None, Path]]:
    root = root.resolve()
    media_plan_file = Path(media_plan_path) if media_plan_path else root / "seo-workspace" / "data" / "media-asset-plan.json"
    if not media_plan_file.is_absolute():
        media_plan_file = root / media_plan_file
    output_dir = root / "seo-workspace" / "data"
    report_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    manifest_path = output_dir / MEDIA_FILE_MANIFEST_NAME
    url_map_path = output_dir / MEDIA_URL_MAP_NAME
    report_path = report_dir / f"{today}-media-url-map-report.md"

    media_assets = media_assets_from_plan(read_json(media_plan_file))
    asset_root = Path(asset_dir) if asset_dir else root / "seo-workspace" / "media" / "generated"
    if not asset_root.is_absolute():
        asset_root = root / asset_root
    rows = build_manifest_rows(media_assets, asset_root, public_base_url)
    blockers: list[str] = []
    warnings: list[str] = []
    if not media_assets:
        blockers.append("No media assets found. Run media-assets first.")
    if not public_base_url:
        blockers.append("Public base URL missing. Provide --public-base-url after media files are uploaded/served.")
    missing = [row["filename"] for row in rows if row["exists"] != "yes"]
    if missing:
        blockers.append("Missing local media files: " + ", ".join(missing))

    ready_map_path: Path | None = None
    status = "blocked_missing_media_files_or_url"
    if not blockers:
        url_map = {row["filename"]: row["file_url"] for row in rows}
        write_text(url_map_path, json.dumps(url_map, ensure_ascii=False, indent=2) + "\n")
        media_result, _ = run_media_assets(root, url_map_path=str(url_map_path))
        if media_result.ok:
            ready_map_path = url_map_path
            status = "media_url_map_ready"
        else:
            blockers.extend(media_result.blockers)
            warnings.extend(media_result.warnings)

    result = MediaUrlMapResult(status=status, blockers=blockers, warnings=warnings)
    result.artifacts.update({"file_manifest": str(manifest_path), "report": str(report_path)})
    if ready_map_path:
        result.artifacts["media_url_map"] = str(ready_map_path)
        result.artifacts["media_ready_cms_payload"] = str(root / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json")
    write_manifest(manifest_path, rows)
    write_text(report_path, render_report(result, rows, asset_root, public_base_url))
    return result, (manifest_path, ready_map_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a media URL map from local generated/selected files.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--asset-dir", default="", help="Directory containing generated/selected media files.")
    parser.add_argument("--public-base-url", default="", help="Public URL prefix where files are served after upload.")
    parser.add_argument("--media-plan-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, _ = run_media_url_map(
        Path(args.root),
        asset_dir=args.asset_dir,
        public_base_url=args.public_base_url,
        media_plan_path=args.media_plan_path,
    )
    for output in result.artifacts.values():
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
