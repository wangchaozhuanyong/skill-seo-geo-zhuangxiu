#!/usr/bin/env python3
"""Apply a rich-editor JSON export to a CMS payload draft without publishing."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from dataclasses import dataclass, field
from pathlib import Path


EDITOR_APPLIED_PAYLOAD_NAME = "rich-content-cms-payload.editor-applied.json"
EDITOR_APPLY_SUMMARY_NAME = "rich-content-editor-apply-summary.json"


@dataclass
class RichEditorApplyResult:
    status: str
    zh_block_count: int = 0
    en_block_count: int = 0
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


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def parse_items(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [line.strip() for line in value.splitlines() if line.strip()]
        return parsed if isinstance(parsed, list) else [parsed]
    return []


def original_blocks_by_id(blocks: list[object]) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    for raw in blocks:
        block = safe_dict(raw)
        editor_id = str(block.get("editor_id", "")).strip()
        if editor_id:
            output[editor_id] = block
    return output


def new_block_base(raw: dict[str, object], *, language: str) -> dict[str, object]:
    editor_id = str(raw.get("editor_id", "")).strip() or f"{language}-new-block"
    block_type = str(raw.get("type", "text") or "text")
    return {
        "editor_id": editor_id,
        "source_id": editor_id,
        "language": language,
        "type": block_type,
        "sort_order": raw.get("sort_order", 0),
        "can_drag": True,
        "editable_fields": {},
        "media": {},
        "publish_mapping": f"payload.content_{language}",
        "safety_rules": [
            "New editor block remains draft-only until owner-approved execution.",
            "Generated images must stay labeled as design/rendering concepts.",
        ],
    }


def merged_blocks(language_payload: dict[str, object], warnings: list[str], *, language: str) -> list[dict[str, object]]:
    original = sorted(
        [safe_dict(item) for item in safe_list(language_payload.get("blocks"))],
        key=lambda item: int(item.get("sort_order", 0) or 0),
    )
    edited = safe_list(language_payload.get("edited_blocks"))
    if not edited:
        warnings.append(f"No edited_blocks found for {language}; using current editor blocks.")
        return original
    originals = original_blocks_by_id(original)
    merged: list[dict[str, object]] = []
    for raw in sorted([safe_dict(item) for item in edited], key=lambda item: int(item.get("sort_order", 0) or 0)):
        editor_id = str(raw.get("editor_id", "")).strip()
        base = json.loads(json.dumps(originals.get(editor_id, {}), ensure_ascii=False))
        if not base:
            if raw.get("is_new") is True or editor_id.startswith(f"{language}-new-"):
                base = new_block_base(raw, language=language)
            else:
                warnings.append(f"Edited block {editor_id or 'unknown'} has no matching original block; skipped.")
                continue
        fields = safe_dict(base.get("editable_fields")).copy()
        media = safe_dict(base.get("media")).copy()
        for key, value in safe_dict(raw.get("edited_fields")).items():
            if key == "items":
                fields["items"] = parse_items(value)
            elif key.startswith("media."):
                media[key.split(".", 1)[1]] = value
            else:
                fields[key] = value
        base["sort_order"] = raw.get("sort_order", base.get("sort_order", len(merged) + 1))
        base["editable_fields"] = fields
        base["media"] = media
        merged.append(base)
    if not merged:
        warnings.append(f"Edited blocks for {language} were empty after merge; using current editor blocks.")
        return original
    return merged


def media_src(media: dict[str, object]) -> str:
    file_url = str(media.get("file_url", "")).strip()
    if file_url:
        return file_url
    filename = str(media.get("filename", "")).strip()
    return f"NEEDS_MEDIA_UPLOAD:{filename}" if filename else ""


def render_figure(media: dict[str, object]) -> str:
    if not media:
        return ""
    src = html.escape(media_src(media))
    alt = html.escape(str(media.get("alt", "")))
    caption = html.escape(str(media.get("caption", "")))
    label = html.escape(str(media.get("concept_label", "design concept / rendering concept")))
    boundary = html.escape(str(media.get("claim_boundary", "Concept/rendering image only; not real project proof.")))
    return (
        "<figure class=\"seo-rich-editor-media\">"
        f"<img src=\"{src}\" alt=\"{alt}\" loading=\"lazy\" />"
        f"<figcaption>{caption} <strong>{label}</strong></figcaption>"
        f"<p class=\"seo-rich-claim-boundary\">{boundary}</p>"
        "</figure>"
    )


def render_items(items: list[object]) -> str:
    output = []
    for item in items:
        if isinstance(item, dict) and ("question" in item or "answer" in item):
            output.append(
                "<details>"
                f"<summary>{html.escape(str(item.get('question', '')))}</summary>"
                f"<p>{html.escape(str(item.get('answer', '')))}</p>"
                "</details>"
            )
        else:
            output.append(f"<li>{html.escape(str(item))}</li>")
    return "\n".join(output)


def render_block(block: dict[str, object], *, language: str) -> str:
    block_type = str(block.get("type", "text"))
    fields = safe_dict(block.get("editable_fields"))
    media = safe_dict(block.get("media"))
    heading = html.escape(str(fields.get("heading", "")))
    body = html.escape(str(fields.get("body", "")))
    if block_type == "hero":
        return f"<section class=\"seo-rich-block seo-rich-hero\"><h1>{heading}</h1><p>{body}</p>{render_figure(media)}</section>"
    if block_type == "image":
        return f"<section class=\"seo-rich-block seo-rich-image\"><h2>{heading}</h2><p>{body}</p>{render_figure(media)}</section>"
    if block_type == "steps":
        return f"<section class=\"seo-rich-block seo-rich-steps\"><h2>{heading}</h2><ol>{render_items(parse_items(fields.get('items', [])))}</ol></section>"
    if block_type == "faq":
        return f"<section class=\"seo-rich-block seo-rich-faq\"><h2>{heading}</h2>{render_items(parse_items(fields.get('items', [])))}</section>"
    if block_type == "cta":
        href = html.escape(str(fields.get("href", "")))
        label = html.escape(str(fields.get("label", "")))
        return f"<section class=\"seo-rich-block seo-rich-cta\"><h2>{heading}</h2><p>{body}</p><a href=\"{href}\">{label}</a></section>"
    tag = "h2" if language == "en" else "h2"
    return f"<section class=\"seo-rich-block\"><{tag}>{heading}</{tag}><p>{body}</p></section>"


def render_html(blocks: list[dict[str, object]], *, language: str) -> str:
    disclaimer = (
        "以上图片为概念设计/效果图方案，不代表真实完工案例。"
        if language == "zh"
        else "Images above are design/rendering concepts, not completed real project proof."
    )
    parts = [render_block(block, language=language) for block in blocks]
    parts.append(f"<p class=\"seo-rich-disclaimer\">{html.escape(disclaimer)}</p>")
    return "\n".join(parts)


def first_heading(blocks: list[dict[str, object]]) -> str:
    for block in blocks:
        if str(block.get("type", "")) == "hero":
            heading = str(safe_dict(block.get("editable_fields")).get("heading", "")).strip()
            if heading:
                return heading
    for block in blocks:
        heading = str(safe_dict(block.get("editable_fields")).get("heading", "")).strip()
        if heading:
            return heading
    return ""


def first_media_url(blocks: list[dict[str, object]]) -> str:
    for block in blocks:
        media = safe_dict(block.get("media"))
        if media:
            return media_src(media)
    return ""


def media_placeholders(html_text: str) -> list[str]:
    return sorted({part.split("\"", 1)[0] for part in html_text.split("NEEDS_MEDIA_UPLOAD:")[1:]})


CONCEPT_BOUNDARY_TOKENS = (
    "concept",
    "rendering",
    "not real",
    "not a real",
    "not completed",
    "效果图",
    "概念",
    "不作为",
    "不代表",
    "非真实",
)

UNSUPPORTED_CLAIM_PATTERNS = (
    "real customer case",
    "real project photo",
    "completed real project",
    "customer review",
    "fixed price",
    "fixed timeline",
    "guaranteed timeline",
    "warranty",
    "真实客户案例",
    "真实客户照片",
    "客户评价",
    "固定价格",
    "固定工期",
    "保证工期",
    "保修",
    "质保",
    "已完工案例",
)

NEGATION_OR_RULE_TOKENS = (
    "do not",
    "don't",
    "must not",
    "should not",
    "not a",
    "not real",
    "不要",
    "不得",
    "不能",
    "不可",
    "不作为",
    "不代表",
)


def text_has_safe_boundary(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in CONCEPT_BOUNDARY_TOKENS)


def text_has_unsupported_claim(text: str) -> bool:
    lowered = text.lower()
    if text_has_safe_boundary(lowered) or any(token in lowered for token in NEGATION_OR_RULE_TOKENS):
        return False
    return any(pattern in lowered for pattern in UNSUPPORTED_CLAIM_PATTERNS)


def block_text_values(block: dict[str, object]) -> list[str]:
    values: list[str] = []
    fields = safe_dict(block.get("editable_fields"))
    media = safe_dict(block.get("media"))
    for value in fields.values():
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(json.dumps(item, ensure_ascii=False) for item in value)
    for key in ("alt", "caption", "concept_label"):
        value = str(media.get(key, "") or "").strip()
        if value:
            values.append(value)
    return values


def validate_media_block(block: dict[str, object], *, language: str) -> list[str]:
    media = safe_dict(block.get("media"))
    if not media:
        return []
    editor_id = str(block.get("editor_id", "unknown"))
    blockers: list[str] = []
    for field in ("alt", "caption", "concept_label", "claim_boundary"):
        if not str(media.get(field, "") or "").strip():
            blockers.append(f"{language} block {editor_id} image is missing media.{field}.")
    boundary_text = " ".join(str(media.get(field, "") or "") for field in ("caption", "concept_label", "claim_boundary"))
    if boundary_text and not text_has_safe_boundary(boundary_text):
        blockers.append(f"{language} block {editor_id} image must keep a design/rendering concept boundary.")
    return blockers


def validate_merged_blocks(blocks: list[dict[str, object]], *, language: str) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    for block in blocks:
        editor_id = str(block.get("editor_id", "unknown"))
        blockers.extend(validate_media_block(block, language=language))
        for text in block_text_values(block):
            if text_has_unsupported_claim(text):
                blockers.append(f"{language} block {editor_id} contains unsupported factual claim text: {text[:120]}")
    if not blocks:
        warnings.append(f"No merged blocks found for {language}.")
    return blockers, warnings


def validate_editor_export(editor_export: dict[str, object], warnings: list[str]) -> tuple[list[str], dict[str, object]]:
    languages = safe_dict(editor_export.get("languages"))
    zh_blocks = merged_blocks(safe_dict(languages.get("zh")), warnings, language="zh")
    en_blocks = merged_blocks(safe_dict(languages.get("en")), warnings, language="en")
    zh_blockers, zh_warnings = validate_merged_blocks(zh_blocks, language="zh")
    en_blockers, en_warnings = validate_merged_blocks(en_blocks, language="en")
    warnings.extend(zh_warnings + en_warnings)
    summary = {
        "qa_checked": True,
        "qa_zh_block_count": len(zh_blocks),
        "qa_en_block_count": len(en_blocks),
        "qa_media_block_count": len([block for block in zh_blocks + en_blocks if safe_dict(block.get("media"))]),
    }
    return zh_blockers + en_blockers, summary


def dedupe_strings(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output


def build_applied_payload(editor_export: dict[str, object], cms_payload: dict[str, object], warnings: list[str]) -> tuple[dict[str, object], dict[str, object]]:
    languages = safe_dict(editor_export.get("languages"))
    zh_blocks = merged_blocks(safe_dict(languages.get("zh")), warnings, language="zh")
    en_blocks = merged_blocks(safe_dict(languages.get("en")), warnings, language="en")
    content_zh = render_html(zh_blocks, language="zh")
    content_en = render_html(en_blocks, language="en")
    output = json.loads(json.dumps(cms_payload, ensure_ascii=False))
    payload = safe_dict(output.get("payload")).copy()
    payload["content_zh"] = content_zh
    payload["content_en"] = content_en
    if first_heading(zh_blocks):
        payload["title_zh"] = first_heading(zh_blocks)
    if first_heading(en_blocks):
        payload["title_en"] = first_heading(en_blocks)
    if first_media_url(en_blocks) or first_media_url(zh_blocks):
        payload["image_url"] = first_media_url(en_blocks) or first_media_url(zh_blocks)
    payload["status"] = str(payload.get("status", "draft") or "draft")
    output["payload"] = payload
    output["editor_applied"] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source_editor_status": editor_export.get("status", ""),
        "target_url": editor_export.get("target_url", ""),
        "paired_url": editor_export.get("paired_url", ""),
        "zh_block_count": len(zh_blocks),
        "en_block_count": len(en_blocks),
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "claim_boundary": "Editor-applied payload is still a draft artifact. It is not approved for live CMS/source execution.",
    }
    summary = {
        "target_url": editor_export.get("target_url", ""),
        "paired_url": editor_export.get("paired_url", ""),
        "zh_block_count": len(zh_blocks),
        "en_block_count": len(en_blocks),
        "media_placeholders": sorted(set(media_placeholders(content_zh) + media_placeholders(content_en))),
        "used_edited_blocks": bool(safe_list(safe_dict(languages.get("zh")).get("edited_blocks")) or safe_list(safe_dict(languages.get("en")).get("edited_blocks"))),
    }
    return output, summary


def render_report(result: RichEditorApplyResult, summary: dict[str, object]) -> str:
    lines = [
        "# Rich Editor Apply Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{summary.get('target_url', 'N/A')}`",
        f"- Paired URL: `{summary.get('paired_url', 'N/A')}`",
        f"- 中文 blocks: {result.zh_block_count}",
        f"- English blocks: {result.en_block_count}",
        f"- Used edited blocks: `{summary.get('used_edited_blocks', False)}`",
        "- 执行状态: draft payload only；未登录 CMS、未上传媒体、未写数据库、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把本地富文本图文编辑器导出的 JSON 回写成新的 CMS payload 草稿，让拖拽排序、正文、CTA、图片 alt 和图注可以进入后续 publish handoff。该文件仍不是发布动作。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Media Placeholders", ""])
    placeholders = [str(item) for item in safe_list(summary.get("media_placeholders"))]
    lines.extend(f"- NEEDS_MEDIA_UPLOAD:{item}" for item in placeholders) if placeholders else lines.append("- None")
    lines.extend(["", "## Artifacts", ""])
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items())
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 输出文件是新的 editor-applied CMS payload 草稿，不覆盖原始 payload。",
            "- 后续 publish-executor 会在没有 media-ready payload 或显式 `--cms-payload-path` 时默认选用该 payload，并仍需 owner-approved、explicit execution、QA、media-ready 和 readiness gate。",
            "- 任何概念图、效果图、生成图必须继续保留 design/rendering concept 边界。",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, applied_payload: dict[str, object], summary: dict[str, object], result: RichEditorApplyResult) -> tuple[Path, Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    payload_path = data_dir / EDITOR_APPLIED_PAYLOAD_NAME
    summary_path = data_dir / EDITOR_APPLY_SUMMARY_NAME
    report_path = reports_dir / f"{today}-rich-editor-apply-report.md"
    result.artifacts.update({"editor_applied_payload": str(payload_path), "summary": str(summary_path), "report": str(report_path)})
    write_text(payload_path, json.dumps(applied_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(summary_path, json.dumps({"status": result.status, "blockers": result.blockers, "warnings": result.warnings, **summary}, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(result, summary))
    return payload_path, summary_path, report_path


def run_rich_editor_apply(
    root: Path,
    *,
    editor_export_path: str = "",
    cms_payload_path: str = "",
) -> tuple[RichEditorApplyResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    editor_file = resolve_path(root, editor_export_path) if editor_export_path else data_dir / "rich-content-editor-manifest.json"
    cms_file = resolve_path(root, cms_payload_path) if cms_payload_path else data_dir / "rich-content-cms-payload.json"
    editor_export = read_json(editor_file)
    cms_payload = read_json(cms_file)
    blockers: list[str] = []
    warnings: list[str] = []
    if not editor_export:
        blockers.append("Missing rich editor export/manifest. Run rich-editor first or pass --editor-export-path.")
    if not cms_payload:
        blockers.append("Missing CMS payload draft. Run rich-blocks first or pass --cms-payload-path.")
    if not safe_dict(editor_export.get("languages")):
        blockers.append("Editor export has no languages object.")
    if not safe_dict(cms_payload.get("payload")):
        blockers.append("CMS payload draft has no payload object.")

    qa_summary: dict[str, object] = {}
    if not blockers:
        qa_blockers, qa_summary = validate_editor_export(editor_export, warnings)
        blockers.extend(qa_blockers)

    if blockers:
        applied_payload: dict[str, object] = {}
        summary: dict[str, object] = {"target_url": editor_export.get("target_url", ""), "paired_url": editor_export.get("paired_url", ""), "zh_block_count": 0, "en_block_count": 0, "media_placeholders": [], "used_edited_blocks": False, **qa_summary}
    else:
        applied_payload, summary = build_applied_payload(editor_export, cms_payload, warnings)
        summary.update(qa_summary)

    status = "editor_applied_payload_ready_for_owner_review" if not blockers else "rich_editor_apply_blocked"
    warnings = dedupe_strings(warnings)
    result = RichEditorApplyResult(
        status=status,
        zh_block_count=int(summary.get("zh_block_count", 0) or 0),
        en_block_count=int(summary.get("en_block_count", 0) or 0),
        blockers=blockers,
        warnings=warnings,
    )
    artifacts = write_outputs(root, applied_payload, summary, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply rich-editor JSON export to a CMS payload draft without publishing.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--editor-export-path", default="")
    parser.add_argument("--cms-payload-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, _ = run_rich_editor_apply(Path(args.root), editor_export_path=args.editor_export_path, cms_payload_path=args.cms_payload_path)
    for output in result.artifacts.values():
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
