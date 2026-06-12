#!/usr/bin/env python3
"""Create an owner-review rich text/image editor package from structured blocks."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from dataclasses import dataclass, field
from pathlib import Path


EDITOR_MANIFEST_NAME = "rich-content-editor-manifest.json"


@dataclass
class RichEditorResult:
    status: str
    block_count: int = 0
    media_count: int = 0
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


def media_plan_by_filename(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    for item in safe_list(payload.get("media_assets")):
        media = safe_dict(item)
        filename = str(media.get("filename", "")).strip()
        if filename:
            output[filename] = media
    return output


def concept_by_placeholder(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    for item in safe_list(payload.get("assets")):
        asset = safe_dict(item)
        filename = str(asset.get("placeholder_filename", "")).strip()
        if filename:
            output[filename] = asset
    return output


def media_from_block(block: dict[str, object], *, media_plan: dict[str, dict[str, object]], concepts: dict[str, dict[str, object]]) -> dict[str, object]:
    image = safe_dict(block.get("image"))
    filename = str(image.get("filename", "")).strip()
    if not filename:
        return {}
    plan = media_plan.get(filename, {})
    concept = concepts.get(filename, {})
    return {
        "filename": filename,
        "slot": image.get("slot", plan.get("usage_type", "")),
        "alt": image.get("alt", plan.get("alt_en") or plan.get("alt_zh", "")),
        "caption": image.get("caption", plan.get("caption_en") or plan.get("caption_zh", "")),
        "concept_label": image.get("concept_label", plan.get("concept_label", "design concept / rendering concept")),
        "claim_boundary": plan.get("claim_boundary", concept.get("claim_boundary", "Concept/rendering asset only; not real project proof.")),
        "file_url": plan.get("file_url", f"NEEDS_MEDIA_UPLOAD:{filename}"),
        "generated_local_path": concept.get("local_path", ""),
        "generated_filename": concept.get("generated_filename", ""),
        "status": image.get("status", plan.get("status", "needs_generation_or_owner_asset_selection")),
        "editable_fields": ["alt", "caption", "slot"],
    }


def editable_fields(block: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key in ("heading", "body", "href", "label"):
        if key in block:
            result[key] = block[key]
    if "items" in block:
        result["items"] = block["items"]
    return result


def build_editor_blocks(
    blocks: list[object],
    *,
    language: str,
    media_plan: dict[str, dict[str, object]],
    concepts: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for index, raw in enumerate(blocks):
        block = safe_dict(raw)
        source_id = str(block.get("id", f"block-{index + 1}"))
        editor_id = f"{language}-{source_id}"
        output.append(
            {
                "editor_id": editor_id,
                "source_id": source_id,
                "language": language,
                "type": block.get("type", "text"),
                "sort_order": index + 1,
                "can_drag": True,
                "editable_fields": editable_fields(block),
                "media": media_from_block(block, media_plan=media_plan, concepts=concepts),
                "publish_mapping": f"payload.content_{language}",
                "safety_rules": [
                    "Do not present generated images as real completed project photos.",
                    "Do not add prices, timelines, warranties, reviews, service areas, awards, or qualifications unless owner-confirmed.",
                    "Keep concept/rendering labels visible near generated visuals.",
                ],
            }
        )
    return output


def build_manifest(blocks_payload: dict[str, object], media_plan_payload: dict[str, object], concept_payload: dict[str, object], *, blocks_path: Path) -> dict[str, object]:
    media_plan = media_plan_by_filename(media_plan_payload)
    concepts = concept_by_placeholder(concept_payload)
    metadata = safe_dict(blocks_payload.get("metadata"))
    zh_blocks = build_editor_blocks(safe_list(blocks_payload.get("blocks_zh")), language="zh", media_plan=media_plan, concepts=concepts)
    en_blocks = build_editor_blocks(safe_list(blocks_payload.get("blocks_en")), language="en", media_plan=media_plan, concepts=concepts)
    media_items = []
    for filename, item in media_plan.items():
        media_items.append(
            {
                "filename": filename,
                "usage_type": item.get("usage_type", ""),
                "file_url": item.get("file_url", f"NEEDS_MEDIA_UPLOAD:{filename}"),
                "generated_local_path": concepts.get(filename, {}).get("local_path", ""),
                "concept_label": item.get("concept_label", "design concept / rendering concept"),
                "claim_boundary": item.get("claim_boundary", "Generated visual concept only; not real project proof."),
            }
        )
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "editable_rich_content_ready_for_owner_review",
        "source_blocks_path": str(blocks_path),
        "metadata": metadata,
        "target_url": metadata.get("target_url", ""),
        "paired_url": metadata.get("paired_url", ""),
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "editor_capabilities": [
            "reorder_blocks",
            "insert_new_heading_text_image_cta_blocks",
            "insert_multiple_inline_concept_images",
            "edit_heading_body_cta",
            "edit_image_alt_caption_slot",
            "review_generated_design_concept_assets",
            "export_json_for_later_approved_execution",
        ],
        "languages": {
            "zh": {"blocks": zh_blocks, "publish_mapping": "payload.content_zh"},
            "en": {"blocks": en_blocks, "publish_mapping": "payload.content_en"},
        },
        "media_library_handoff": media_items,
        "claim_boundary": "This editor package is draft/review only. Generated or concept visuals must stay labeled as design/rendering concepts, not real project proof.",
    }


def media_preview_src(media: dict[str, object]) -> str:
    local_path = str(media.get("generated_local_path", ""))
    if local_path and Path(local_path).exists():
        return local_path
    file_url = str(media.get("file_url", ""))
    if file_url and not file_url.startswith("NEEDS_MEDIA_UPLOAD:"):
        return file_url
    return ""


def render_editable_block(block: dict[str, object]) -> str:
    fields = safe_dict(block.get("editable_fields"))
    media = safe_dict(block.get("media"))
    heading = html.escape(str(fields.get("heading", "")))
    body = html.escape(str(fields.get("body", "")))
    block_type = html.escape(str(block.get("type", "")))
    editor_id = html.escape(str(block.get("editor_id", "")))
    parts = [
        f'<section class="editor-block" draggable="true" data-block-id="{editor_id}" data-type="{block_type}">',
        '<div class="block-toolbar"><span class="drag-handle">Drag</span><button type="button" data-move="up">Up</button><button type="button" data-move="down">Down</button></div>',
        f'<label>Heading</label><h2 contenteditable="true" data-field="heading">{heading}</h2>',
    ]
    if body:
        parts.append(f'<label>Body</label><p contenteditable="true" data-field="body">{body}</p>')
    if "items" in fields:
        parts.append(f'<label>Items / FAQ JSON</label><pre contenteditable="true" data-field="items">{html.escape(json.dumps(fields["items"], ensure_ascii=False, indent=2))}</pre>')
    if media:
        src = media_preview_src(media)
        alt = html.escape(str(media.get("alt", "")))
        caption = html.escape(str(media.get("caption", "")))
        label = html.escape(str(media.get("concept_label", "")))
        image = f'<img src="{html.escape(src)}" alt="{alt}" loading="lazy" />' if src else '<div class="image-placeholder">NEEDS MEDIA URL OR GENERATED ASSET</div>'
        parts.extend(
            [
                '<figure class="media-card">',
                image,
                f'<figcaption contenteditable="true" data-field="media.caption">{caption}</figcaption>',
                f'<p class="concept-label">{label}</p>',
                f'<label>Image alt</label><p contenteditable="true" data-field="media.alt">{alt}</p>',
                '</figure>',
            ]
        )
    if "href" in fields or "label" in fields:
        parts.append(f'<label>CTA URL</label><p contenteditable="true" data-field="href">{html.escape(str(fields.get("href", "")))}</p>')
        parts.append(f'<label>CTA Label</label><p contenteditable="true" data-field="label">{html.escape(str(fields.get("label", "")))}</p>')
    parts.append("</section>")
    return "\n".join(parts)


def render_language_panel(manifest: dict[str, object], language: str) -> str:
    language_payload = safe_dict(safe_dict(manifest.get("languages")).get(language))
    blocks = safe_list(language_payload.get("blocks"))
    title = "中文页面编辑" if language == "zh" else "English Page Editor"
    return "\n".join(
        [
            f'<section class="language-panel" data-language="{language}">',
            f"<h2>{title}</h2>",
            '<p class="panel-note">可拖拽排序、编辑标题/正文/图注/alt，也可新增文本、图片和 CTA 块。此页面只在本地导出 JSON，不写 CMS。</p>',
            '<div class="insert-toolbar">',
            f'<button type="button" data-add-block="text" data-language="{language}">Add Text Block</button>',
            f'<button type="button" data-add-block="image" data-language="{language}">Add Image Block</button>',
            f'<button type="button" data-add-block="cta" data-language="{language}">Add CTA Block</button>',
            "</div>",
            '<div class="block-list">',
            *(render_editable_block(safe_dict(block)) for block in blocks),
            "</div>",
            "</section>",
        ]
    )


def render_editor_html(manifest: dict[str, object]) -> str:
    title = "FLASH CAST Rich Text Image Editor Draft"
    manifest_json = html.escape(json.dumps(manifest, ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    :root {{ --ink:#1f2933; --muted:#64748b; --line:#d9e2ec; --paper:#f8fafc; --accent:#0f766e; --warn:#b45309; }}
    body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background:linear-gradient(135deg,#f8fafc,#e0f2fe); }}
    header, main {{ max-width:1180px; margin:0 auto; padding:24px; }}
    header {{ padding-top:36px; }}
    h1 {{ margin:0 0 10px; font-size:30px; }}
    .status {{ display:inline-block; padding:6px 10px; border:1px solid var(--line); border-radius:999px; background:white; color:var(--accent); font-weight:700; }}
    .safety {{ margin-top:14px; padding:14px; background:#fff7ed; border:1px solid #fed7aa; border-radius:14px; color:#7c2d12; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; align-items:start; }}
    .language-panel {{ background:rgba(255,255,255,.88); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 16px 40px rgba(15,23,42,.08); }}
    .panel-note {{ color:var(--muted); }}
    .insert-toolbar {{ display:flex; flex-wrap:wrap; gap:8px; padding:10px; border:1px dashed var(--line); border-radius:14px; background:#f0fdfa; }}
    .editor-block {{ border:1px solid var(--line); border-radius:16px; padding:14px; margin:14px 0; background:white; }}
    .editor-block.dragging {{ opacity:.55; outline:2px dashed var(--accent); }}
    .block-toolbar {{ display:flex; gap:8px; justify-content:flex-end; align-items:center; color:var(--muted); }}
    .drag-handle {{ margin-right:auto; cursor:grab; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
    button {{ border:0; border-radius:999px; padding:7px 11px; background:var(--accent); color:white; cursor:pointer; }}
    label {{ display:block; margin-top:12px; font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }}
    [contenteditable="true"] {{ outline:none; border-radius:10px; padding:7px; background:#f8fafc; border:1px dashed transparent; }}
    [contenteditable="true"]:focus {{ border-color:var(--accent); background:#ecfeff; }}
    .media-card {{ margin:14px 0; padding:12px; background:#f8fafc; border:1px solid var(--line); border-radius:14px; }}
    .media-card img {{ width:100%; max-height:260px; object-fit:cover; border-radius:12px; background:#e2e8f0; }}
    .image-placeholder {{ display:grid; place-items:center; min-height:170px; border:1px dashed var(--warn); border-radius:12px; color:var(--warn); background:#fffbeb; }}
    .concept-label {{ color:var(--warn); font-weight:700; }}
    .export {{ margin-top:24px; background:#0f172a; color:white; border-radius:18px; padding:18px; }}
    .export textarea {{ width:100%; min-height:240px; box-sizing:border-box; border-radius:12px; padding:12px; font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .export code {{ display:block; margin-top:10px; padding:12px; border-radius:12px; background:#020617; color:#d1fae5; overflow-wrap:anywhere; }}
    @media (max-width: 860px) {{ .grid {{ grid-template-columns:1fr; }} header, main {{ padding:18px; }} }}
  </style>
</head>
<body>
  <header>
    <span class="status">draft-only rich editor</span>
    <h1>{title}</h1>
    <p>Target: {html.escape(str(manifest.get("target_url", "")))} | Pair: {html.escape(str(manifest.get("paired_url", "")))}</p>
    <div class="safety">安全边界：本地编辑预览，不登录 CMS、不上传媒体、不写数据库、不发布。生成/概念图必须继续标注为设计效果图，不得说成真实完工案例。</div>
  </header>
  <main>
    <div class="grid">
      {render_language_panel(manifest, "zh")}
      {render_language_panel(manifest, "en")}
    </div>
    <section class="export">
      <h2>导出编辑 JSON / Export Edited JSON</h2>
      <p>点击按钮会把当前排序和可编辑文本导出到下方 textarea，也可以下载为 <strong>edited-export.json</strong>。后续仍需业主明确批准后，才能进入执行链。</p>
      <button type="button" id="export-json">Export JSON</button>
      <button type="button" id="download-json">Download edited-export.json</button>
      <code>python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json</code>
      <textarea id="export-output">{manifest_json}</textarea>
    </section>
  </main>
  <script id="editor-source" type="application/json">{manifest_json}</script>
  <script>
    const source = JSON.parse(document.getElementById('editor-source').textContent);
    let dragged = null;
    function bindBlock(block) {{
      block.addEventListener('dragstart', () => {{ dragged = block; block.classList.add('dragging'); }});
      block.addEventListener('dragend', () => {{ block.classList.remove('dragging'); dragged = null; }});
      block.addEventListener('dragover', (event) => {{
        event.preventDefault();
        if (!dragged || dragged === block) return;
        const rect = block.getBoundingClientRect();
        const after = event.clientY > rect.top + rect.height / 2;
        block.parentNode.insertBefore(dragged, after ? block.nextSibling : block);
      }});
    }}
    function bindMoveButton(button) {{
      button.addEventListener('click', () => {{
        const block = button.closest('.editor-block');
        if (button.dataset.move === 'up' && block.previousElementSibling) block.parentNode.insertBefore(block, block.previousElementSibling);
        if (button.dataset.move === 'down' && block.nextElementSibling) block.parentNode.insertBefore(block.nextElementSibling, block);
      }});
    }}
    document.querySelectorAll('.editor-block').forEach(bindBlock);
    document.querySelectorAll('[data-move]').forEach(bindMoveButton);
    function field(label, tag, dataField, text) {{
      const safe = (text || '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
      return `<label>${{label}}</label><${{tag}} contenteditable="true" data-field="${{dataField}}">${{safe}}</${{tag}}>`;
    }}
    function mediaFields() {{
      return [
        '<figure class="media-card">',
        '<div class="image-placeholder">NEW DESIGN / RENDERING CONCEPT IMAGE</div>',
        field('Suggested filename', 'p', 'media.filename', 'flash-cast-new-rendering-concept.webp'),
        field('Image URL or upload placeholder', 'p', 'media.file_url', 'NEEDS_MEDIA_UPLOAD:flash-cast-new-rendering-concept.webp'),
        field('Caption', 'figcaption', 'media.caption', '此图为新增设计效果图方案，不作为真实完工案例。'),
        field('Concept label', 'p', 'media.concept_label', '概念设计 / 效果图方案 / design concept / rendering concept'),
        field('Image alt', 'p', 'media.alt', 'FLASH CAST 新增装修效果图方案'),
        field('Claim boundary', 'p', 'media.claim_boundary', 'Concept/rendering asset only; not real project proof.'),
        '</figure>',
      ].join('');
    }}
    function createBlock(language, type) {{
      const id = `${{language}}-new-${{type}}-${{Date.now()}}`;
      const block = document.createElement('section');
      block.className = 'editor-block';
      block.draggable = true;
      block.dataset.blockId = id;
      block.dataset.type = type;
      block.dataset.newBlock = 'true';
      const heading = type === 'cta' ? '新增 CTA' : type === 'image' ? '新增效果图方案' : '新增图文段落';
      const body = type === 'cta' ? '补充咨询引导文案。' : type === 'image' ? '补充图片上下文说明。' : '补充新的正文段落。';
      block.innerHTML = [
        '<div class="block-toolbar"><span class="drag-handle">Drag</span><button type="button" data-move="up">Up</button><button type="button" data-move="down">Down</button></div>',
        field('Heading', 'h2', 'heading', heading),
        field('Body', 'p', 'body', body),
        type === 'image' ? mediaFields() : '',
        type === 'cta' ? field('CTA URL', 'p', 'href', language === 'zh' ? '/zh/quote' : '/en/quote') : '',
        type === 'cta' ? field('CTA Label', 'p', 'label', language === 'zh' ? '获取报价' : 'Request a Quote') : '',
      ].join('');
      bindBlock(block);
      block.querySelectorAll('[data-move]').forEach(bindMoveButton);
      return block;
    }}
    document.querySelectorAll('[data-add-block]').forEach((button) => {{
      button.addEventListener('click', () => {{
        const panel = button.closest('.language-panel');
        const list = panel.querySelector('.block-list');
        list.appendChild(createBlock(button.dataset.language, button.dataset.addBlock));
      }});
    }});
    function collectBlock(block, index) {{
      const fields = {{}};
      block.querySelectorAll('[data-field]').forEach((field) => {{ fields[field.dataset.field] = field.innerText.trim(); }});
      return {{ editor_id: block.dataset.blockId, type: block.dataset.type, sort_order: index + 1, is_new: block.dataset.newBlock === 'true', edited_fields: fields }};
    }}
    document.getElementById('export-json').addEventListener('click', () => {{
      const edited = JSON.parse(JSON.stringify(source));
      edited.status = 'owner_edited_export_pending_execution_approval';
      edited.exported_at = new Date().toISOString();
      edited.languages.zh.edited_blocks = Array.from(document.querySelectorAll('[data-language="zh"] .editor-block')).map(collectBlock);
      edited.languages.en.edited_blocks = Array.from(document.querySelectorAll('[data-language="en"] .editor-block')).map(collectBlock);
      document.getElementById('export-output').value = JSON.stringify(edited, null, 2);
    }});
    document.getElementById('download-json').addEventListener('click', () => {{
      document.getElementById('export-json').click();
      const blob = new Blob([document.getElementById('export-output').value + "\\n"], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'edited-export.json';
      link.click();
      URL.revokeObjectURL(url);
    }});
  </script>
</body>
</html>
"""


def render_report(result: RichEditorResult, manifest: dict[str, object]) -> str:
    lines = [
        "# Rich Text Image Editor Package Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Target URL: `{manifest.get('target_url', 'N/A')}`",
        f"- Paired URL: `{manifest.get('paired_url', 'N/A')}`",
        f"- Editable blocks: {result.block_count}",
        f"- Media items: {result.media_count}",
        "- 执行状态: draft/editor-only；未登录 CMS、未上传媒体、未写数据库、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天补齐图文内容编辑层：把结构化双语 blocks、图片占位和概念效果图资产汇总成可拖拽、可编辑、可新增文本/图片/CTA 块、可导出 JSON 的本地审核包。这样后续可以先审内容、图片顺序和新增图文混排，再进入业主批准后的发布 handoff。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Artifacts", ""])
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items())
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 编辑器包只用于本地审核和导出，不会写 CMS 或网站源码。",
            "- 生成图片、SVG 概念图、效果图方案必须继续标注为 design/rendering concept。",
            "- 任何真实案例、价格、工期、保修、评价、资质、服务区域或奖项仍需业主确认，不得在编辑器里凭空添加。",
            "- 后续执行仍需要 owner-approved、explicit execution、QA、media-ready payload 和 publish readiness。",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(root: Path, manifest: dict[str, object], result: RichEditorResult) -> tuple[Path, Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    drafts_dir = root / "seo-workspace" / "drafts"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    manifest_path = data_dir / EDITOR_MANIFEST_NAME
    html_path = drafts_dir / f"{today}-rich-content-editor.html"
    report_path = reports_dir / f"{today}-rich-content-editor-report.md"
    result.artifacts.update({"editor_manifest": str(manifest_path), "editor_html": str(html_path), "report": str(report_path)})
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_text(html_path, render_editor_html(manifest))
    write_text(report_path, render_report(result, manifest))
    return manifest_path, html_path, report_path


def run_rich_editor(
    root: Path,
    *,
    blocks_path: str = "",
    media_plan_path: str = "",
    concept_manifest_path: str = "",
) -> tuple[RichEditorResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    resolved_blocks = resolve_path(root, blocks_path) if blocks_path else data_dir / "rich-content-blocks.json"
    resolved_media_plan = resolve_path(root, media_plan_path) if media_plan_path else data_dir / "media-asset-plan.json"
    resolved_concepts = resolve_path(root, concept_manifest_path) if concept_manifest_path else data_dir / "concept-asset-manifest.json"

    blocks_payload = read_json(resolved_blocks)
    media_payload = read_json(resolved_media_plan)
    concept_payload = read_json(resolved_concepts)
    blockers: list[str] = []
    warnings: list[str] = []
    if not blocks_payload:
        blockers.append("Missing rich-content-blocks.json. Run rich-blocks first.")
    if not media_payload:
        warnings.append("Missing media-asset-plan.json; editor will still show block-level media placeholders.")
    if not concept_payload:
        warnings.append("Missing concept-asset-manifest.json; editor will not show generated local concept previews.")

    manifest = build_manifest(blocks_payload, media_payload, concept_payload, blocks_path=resolved_blocks) if blocks_payload else {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "rich_editor_blocked",
        "target_url": "",
        "paired_url": "",
        "no_live_actions_executed": True,
        "languages": {"zh": {"blocks": []}, "en": {"blocks": []}},
    }
    zh_count = len(safe_list(safe_dict(safe_dict(manifest.get("languages")).get("zh")).get("blocks")))
    en_count = len(safe_list(safe_dict(safe_dict(manifest.get("languages")).get("en")).get("blocks")))
    media_count = len(safe_list(manifest.get("media_library_handoff")))
    status = "editable_rich_content_ready_for_owner_review" if not blockers else "rich_editor_blocked"
    manifest["status"] = status
    result = RichEditorResult(status=status, block_count=zh_count + en_count, media_count=media_count, blockers=blockers, warnings=warnings)
    artifacts = write_outputs(root, manifest, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a draft-only rich text/image editor package.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--blocks-path", default="")
    parser.add_argument("--media-plan-path", default="")
    parser.add_argument("--concept-manifest-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, _ = run_rich_editor(
        Path(args.root),
        blocks_path=args.blocks_path,
        media_plan_path=args.media_plan_path,
        concept_manifest_path=args.concept_manifest_path,
    )
    for output in result.artifacts.values():
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
