#!/usr/bin/env python3
"""Prepare generated-design media assets and optional URL replacement maps."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


MEDIA_PLAN_JSON_NAME = "media-asset-plan.json"
MEDIA_URL_MAP_EXAMPLE_NAME = "media-url-map.example.json"
MEDIA_READY_PAYLOAD_NAME = "rich-content-cms-payload.media-ready.json"
BASE_CMS_PAYLOAD_NAME = "rich-content-cms-payload.json"
EDITOR_APPLIED_PAYLOAD_NAME = "rich-content-cms-payload.editor-applied.json"


@dataclass
class MediaPlanResult:
    status: str
    media_count: int
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


def safe_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def normalize_url_map(data: dict[str, object]) -> dict[str, str]:
    if "files" in data and isinstance(data["files"], list):
        result: dict[str, str] = {}
        for item in data["files"]:
            if isinstance(item, dict) and item.get("filename") and item.get("file_url"):
                result[str(item["filename"])] = str(item["file_url"])
        return result
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str)}


def select_cms_payload_file(root: Path, cms_payload_path: str = "") -> tuple[Path, str]:
    data_dir = root / "seo-workspace" / "data"
    if cms_payload_path:
        path = Path(cms_payload_path)
        return (path if path.is_absolute() else root / path), "explicit"
    editor_applied = data_dir / EDITOR_APPLIED_PAYLOAD_NAME
    if editor_applied.exists():
        return editor_applied, "auto_editor_applied"
    return data_dir / BASE_CMS_PAYLOAD_NAME, "auto_base"


def usage_type_for(index: int, item: dict[str, object]) -> str:
    slot = str(item.get("slot", "")).lower()
    filename = str(item.get("filename", "")).lower()
    if index == 0 or "hero" in slot or "hero" in filename:
        return "hero"
    if "material" in slot or "mood" in slot or "material" in filename:
        return "material"
    if "process" in slot or "step" in slot:
        return "general"
    return "general"


def build_media_plan(blocks_payload: dict[str, object]) -> list[dict[str, object]]:
    metadata = safe_dict(blocks_payload.get("metadata"))
    target_url = str(metadata.get("target_url", ""))
    paired_url = str(metadata.get("paired_url", ""))
    media = []
    for index, raw in enumerate(safe_list(blocks_payload.get("media_placeholders"))):
        item = safe_dict(raw)
        filename = str(item.get("filename", "")).strip()
        if not filename:
            continue
        media.append(
            {
                "filename": filename,
                "status": "needs_generation_or_owner_asset_selection",
                "asset_kind": "generated_design_rendering_concept",
                "target_url": target_url,
                "paired_url": paired_url,
                "folder": "media",
                "usage_type": usage_type_for(index, item),
                "mime_type": "image/webp",
                "recommended_width": 1600 if index == 0 else 1400,
                "recommended_height": 960 if index == 0 else 900,
                "file_url": f"NEEDS_MEDIA_UPLOAD:{filename}",
                "file_path": f"media/{filename}",
                "alt_zh": item.get("alt_zh", ""),
                "alt_en": item.get("alt_en", item.get("alt", "")),
                "caption_zh": item.get("caption_zh", ""),
                "caption_en": item.get("caption_en", item.get("caption", "")),
                "concept_label": item.get("concept_label", "design concept / rendering concept"),
                "prompt": item.get("prompt", ""),
                "negative_prompt": "Do not show real customers, addresses, reviews, price tags, awards, certificates, before-after proof, or completed-project evidence.",
                "claim_boundary": "Generated visual for design/rendering concept only; not a real project photo or customer case proof.",
                "media_assets_record": {
                    "file_url": f"NEEDS_MEDIA_UPLOAD:{filename}",
                    "file_path": f"media/{filename}",
                    "file_name": filename,
                    "mime_type": "image/webp",
                    "usage_type": usage_type_for(index, item),
                    "folder": "media",
                    "alt_zh": item.get("alt_zh", ""),
                    "alt_en": item.get("alt_en", item.get("alt", "")),
                    "processing_status": "ready_after_upload",
                },
            }
        )
    return media


def extract_attr(tag: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}=[\"']([^\"']*)[\"']", tag, flags=re.I)
    return match.group(1).strip() if match else ""


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def filename_from_src(src: str) -> str:
    if not src:
        return ""
    if src.startswith("NEEDS_MEDIA_UPLOAD:"):
        return src.split(":", 1)[1].strip()
    name = src.rsplit("/", 1)[-1].strip()
    return name if re.search(r"\.(webp|png|jpe?g|svg)$", name, flags=re.I) else ""


def editor_media_placeholders(cms_payload: dict[str, object]) -> list[dict[str, object]]:
    payload = safe_dict(cms_payload.get("payload"))
    target_url = str(safe_dict(cms_payload.get("editor_applied")).get("target_url", ""))
    paired_url = str(safe_dict(cms_payload.get("editor_applied")).get("paired_url", ""))
    discovered: dict[str, dict[str, object]] = {}
    for language, key in (("zh", "content_zh"), ("en", "content_en")):
        html_text = str(payload.get(key, ""))
        for figure_match in re.finditer(r"<figure\b[^>]*>(?P<body>.*?)</figure>", html_text, flags=re.I | re.S):
            body = figure_match.group("body")
            img_match = re.search(r"<img\b(?P<tag>[^>]*)>", body, flags=re.I | re.S)
            if not img_match:
                continue
            img_tag = img_match.group("tag")
            src = extract_attr(img_tag, "src")
            filename = filename_from_src(src)
            if not filename:
                continue
            item = discovered.setdefault(
                filename,
                {
                    "filename": filename,
                    "slot": "editor inserted concept image",
                    "target_url": target_url,
                    "paired_url": paired_url,
                    "concept_label": "design concept / rendering concept",
                    "prompt": "Create a renovation design/rendering concept that matches the edited page section. Do not show real customers, reviews, prices, addresses, awards, or completed-project proof.",
                    "claim_boundary": "Concept/rendering asset only; not real project proof.",
                },
            )
            alt = extract_attr(img_tag, "alt")
            caption_match = re.search(r"<figcaption\b[^>]*>(?P<caption>.*?)</figcaption>", body, flags=re.I | re.S)
            caption_body = re.sub(r"<strong\b[^>]*>.*?</strong>", "", caption_match.group("caption"), flags=re.I | re.S) if caption_match else ""
            caption = strip_tags(caption_body) if caption_body else ""
            label_match = re.search(r"<strong\b[^>]*>(?P<label>.*?)</strong>", body, flags=re.I | re.S)
            boundary_match = re.search(r"<p\b[^>]*class=[\"'][^\"']*claim-boundary[^\"']*[\"'][^>]*>(?P<boundary>.*?)</p>", body, flags=re.I | re.S)
            if label_match:
                item["concept_label"] = strip_tags(label_match.group("label"))
            if boundary_match:
                item["claim_boundary"] = strip_tags(boundary_match.group("boundary"))
            if language == "zh":
                item["alt_zh"] = alt
                item["caption_zh"] = caption
            else:
                item["alt_en"] = alt
                item["caption_en"] = caption
        for filename in sorted(set(re.findall(r"NEEDS_MEDIA_UPLOAD:([^\"'<>\s]+)", html_text))):
            discovered.setdefault(
                filename,
                {
                    "filename": filename,
                    "slot": "editor inserted concept image",
                    "target_url": target_url,
                    "paired_url": paired_url,
                    "concept_label": "design concept / rendering concept",
                    "prompt": "Create a renovation design/rendering concept that matches the edited page section. Do not show real customers, reviews, prices, addresses, awards, or completed-project proof.",
                    "claim_boundary": "Concept/rendering asset only; not real project proof.",
                },
            )
    return list(discovered.values())


def merge_media_placeholders(base_plan: list[dict[str, object]], editor_placeholders: list[dict[str, object]]) -> list[dict[str, object]]:
    merged = list(base_plan)
    by_filename = {str(item.get("filename", "")): item for item in merged if item.get("filename")}
    for raw in editor_placeholders:
        filename = str(raw.get("filename", "")).strip()
        if not filename:
            continue
        if filename in by_filename:
            existing = by_filename[filename]
            for key, value in raw.items():
                if value and not existing.get(key):
                    existing[key] = value
            continue
        index = len(merged)
        item = {
            "filename": filename,
            "status": "needs_generation_or_owner_asset_selection",
            "asset_kind": "generated_design_rendering_concept",
            "target_url": raw.get("target_url", ""),
            "paired_url": raw.get("paired_url", ""),
            "folder": "media",
            "usage_type": usage_type_for(index, raw),
            "mime_type": "image/webp",
            "recommended_width": 1400,
            "recommended_height": 900,
            "file_url": f"NEEDS_MEDIA_UPLOAD:{filename}",
            "file_path": f"media/{filename}",
            "alt_zh": raw.get("alt_zh", ""),
            "alt_en": raw.get("alt_en", ""),
            "caption_zh": raw.get("caption_zh", ""),
            "caption_en": raw.get("caption_en", ""),
            "concept_label": raw.get("concept_label", "design concept / rendering concept"),
            "prompt": raw.get("prompt", ""),
            "negative_prompt": "Do not show real customers, addresses, reviews, price tags, awards, certificates, before-after proof, or completed-project evidence.",
            "claim_boundary": raw.get("claim_boundary", "Generated visual for design/rendering concept only; not a real project photo or customer case proof."),
            "media_assets_record": {
                "file_url": f"NEEDS_MEDIA_UPLOAD:{filename}",
                "file_path": f"media/{filename}",
                "file_name": filename,
                "mime_type": "image/webp",
                "usage_type": usage_type_for(index, raw),
                "folder": "media",
                "alt_zh": raw.get("alt_zh", ""),
                "alt_en": raw.get("alt_en", ""),
                "processing_status": "ready_after_upload",
            },
        }
        merged.append(item)
        by_filename[filename] = item
    return merged


def replace_media_urls(cms_payload: dict[str, object], url_map: dict[str, str]) -> dict[str, object]:
    text = json.dumps(cms_payload, ensure_ascii=False)
    for filename, url in url_map.items():
        text = text.replace(f"NEEDS_MEDIA_UPLOAD:{filename}", url)
        text = re.sub(rf"(?<=src=\\\"){re.escape(filename)}(?=\\\")", url, text)
        text = re.sub(rf"(?<=src=\"){re.escape(filename)}(?=\")", url, text)
    return json.loads(text)


def missing_urls(media_plan: list[dict[str, object]], url_map: dict[str, str]) -> list[str]:
    return [str(item["filename"]) for item in media_plan if str(item["filename"]) not in url_map]


def render_prompt_markdown(media_plan: list[dict[str, object]]) -> str:
    lines = [
        "# Generated Design / Rendering Media Prompts",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        "- 执行状态: draft-only；未生成图片、未上传媒体、未发布",
        "",
    ]
    for index, item in enumerate(media_plan, start=1):
        lines.extend(
            [
                f"## {index}. {item['filename']}",
                "",
                f"- Usage type: `{item['usage_type']}`",
                f"- Recommended size: {item['recommended_width']}x{item['recommended_height']}",
                f"- 中文 alt: {item.get('alt_zh', '')}",
                f"- English alt: {item.get('alt_en', '')}",
                f"- Concept label: {item.get('concept_label', '')}",
                f"- Claim boundary: {item.get('claim_boundary', '')}",
                "",
                "### Prompt",
                "",
                str(item.get("prompt", "")),
                "",
                "### Negative Prompt",
                "",
                str(item.get("negative_prompt", "")),
                "",
            ]
        )
    return "\n".join(lines)


def render_report(result: MediaPlanResult, media_plan: list[dict[str, object]], url_map: dict[str, str]) -> str:
    lines = [
        "# Media Asset Preparation Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: {result.status}",
        f"- Media assets planned: {result.media_count}",
        "- 执行状态: draft-only；未生成图片、未上传媒体、未写 CMS、未发布",
        "",
        "## 今日决策",
        "",
        "今天把图文 blocks 中的媒体占位升级为可审核的效果图资产计划、生成提示词、媒体库字段草案和 URL 替换路径，解决后续 executor 的媒体准备 blocker。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Media Plan", ""])
    for item in media_plan:
        url = url_map.get(str(item["filename"]), "NEEDS_MEDIA_UPLOAD")
        lines.append(f"- `{item['filename']}` | usage: `{item['usage_type']}` | url: `{url}` | label: {item['concept_label']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
            "## Safety Notes",
            "",
            "- 所有图片必须作为概念设计/效果图方案使用，不得描述为真实完工照片。",
            "- 没有 URL map 时不会生成 media-ready CMS payload。",
            "- URL map 必须来自业主选择或后续已上传的媒体文件 URL。",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    root: Path,
    media_plan: list[dict[str, object]],
    cms_payload: dict[str, object],
    url_map: dict[str, str],
    cms_payload_file: Path,
    cms_payload_selection: str,
) -> tuple[MediaPlanResult, tuple[Path, Path, Path, Path | None]]:
    data_dir = root / "seo-workspace" / "data"
    drafts_dir = root / "seo-workspace" / "drafts"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    plan_path = data_dir / MEDIA_PLAN_JSON_NAME
    map_path = data_dir / MEDIA_URL_MAP_EXAMPLE_NAME
    prompts_path = drafts_dir / f"{today}-media-generation-prompts.md"
    report_path = reports_dir / f"{today}-media-asset-plan.md"
    ready_payload_path: Path | None = None

    blockers: list[str] = []
    warnings: list[str] = []
    if not media_plan:
        blockers.append("No media placeholders found. Run rich-blocks first.")
    if url_map:
        missing = missing_urls(media_plan, url_map)
        if missing:
            blockers.append("URL map is missing generated/uploaded URLs for: " + ", ".join(missing))
        else:
            ready_payload_path = data_dir / MEDIA_READY_PAYLOAD_NAME
            write_text(ready_payload_path, json.dumps(replace_media_urls(cms_payload, url_map), ensure_ascii=False, indent=2) + "\n")
    else:
        warnings.append("No URL map provided; media-ready CMS payload was not generated.")

    status = "media_ready_payload_generated" if ready_payload_path and not blockers else "needs_media_generation_or_upload"
    result = MediaPlanResult(status=status, media_count=len(media_plan), blockers=blockers, warnings=warnings)
    result.artifacts.update(
        {
            "media_plan": str(plan_path),
            "url_map_example": str(map_path),
            "prompt_pack": str(prompts_path),
            "report": str(report_path),
        }
    )
    if ready_payload_path:
        result.artifacts["media_ready_cms_payload"] = str(ready_payload_path)

    write_text(
        plan_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "no_media_upload_executed": True,
                "cms_payload_path": str(cms_payload_file),
                "cms_payload_selection": cms_payload_selection,
                "media_assets": media_plan,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        map_path,
        json.dumps({str(item["filename"]): f"https://example.com/uploads/{item['filename']}" for item in media_plan}, ensure_ascii=False, indent=2) + "\n",
    )
    write_text(prompts_path, render_prompt_markdown(media_plan))
    write_text(report_path, render_report(result, media_plan, url_map))
    return result, (plan_path, map_path, prompts_path, ready_payload_path)


def run_media_assets(
    root: Path,
    *,
    blocks_path: str = "",
    cms_payload_path: str = "",
    url_map_path: str = "",
) -> tuple[MediaPlanResult, tuple[Path, Path, Path, Path | None]]:
    root = root.resolve()
    blocks_file = Path(blocks_path) if blocks_path else root / "seo-workspace" / "data" / "rich-content-blocks.json"
    cms_file, cms_payload_selection = select_cms_payload_file(root, cms_payload_path)
    map_file = Path(url_map_path) if url_map_path else None
    if not blocks_file.is_absolute():
        blocks_file = root / blocks_file
    if map_file and not map_file.is_absolute():
        map_file = root / map_file
    blocks_payload = read_json(blocks_file)
    cms_payload = read_json(cms_file)
    url_map = normalize_url_map(read_json(map_file)) if map_file else {}
    media_plan = merge_media_placeholders(build_media_plan(blocks_payload), editor_media_placeholders(cms_payload))
    return write_outputs(root, media_plan, cms_payload, url_map, cms_file, cms_payload_selection)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare generated-design media assets and optional URL replacement maps.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--blocks-path", default="")
    parser.add_argument("--cms-payload-path", default="")
    parser.add_argument("--url-map-path", default="", help="Optional JSON mapping filename to uploaded/selected file_url.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_media_assets(
        Path(args.root),
        blocks_path=args.blocks_path,
        cms_payload_path=args.cms_payload_path,
        url_map_path=args.url_map_path,
    )
    for artifact in result.artifacts.values():
        print(artifact)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
