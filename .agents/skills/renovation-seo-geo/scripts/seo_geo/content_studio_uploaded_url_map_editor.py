#!/usr/bin/env python3
"""Create a local HTML editor for owner-filled uploaded media URLs."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = "seo-workspace/data/uploaded-url-map.json"
FALLBACK_SOURCE = "seo-workspace/data/uploaded-url-map.template.json"
SUMMARY_NAME = "content-studio-uploaded-url-map-editor.json"
REPORT_NAME = "content-studio-uploaded-url-map-editor.md"
HTML_NAME = "content-studio-uploaded-url-map-editor.html"
DOWNLOAD_NAME = "uploaded-url-map.filled.json"


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


def file_href(path_value: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    return path.as_uri() if path.is_absolute() and path.exists() else path_value


def normalize_files(payload: dict[str, Any]) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    for raw in safe_list(payload.get("files")):
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        item.setdefault("placeholder_filename", item.get("filename", ""))
        item.setdefault("filename", item.get("placeholder_filename", ""))
        item.setdefault("file_url", "")
        item.setdefault("owner_url_confirmed", False)
        item.setdefault("upload_status", "needs_public_url")
        item.setdefault("claim_boundary", "Concept/rendering asset only; not real project proof.")
        files.append(item)
    return files


def selected_source(root: Path, source_path: str = "") -> Path:
    if source_path:
        return resolve_path(root, source_path)
    default = resolve_path(root, DEFAULT_SOURCE)
    return default if default.exists() else resolve_path(root, FALLBACK_SOURCE)


def build_summary(source: dict[str, Any], source_path: Path, html_path: Path) -> dict[str, Any]:
    files = normalize_files(source)
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "uploaded_url_map_editor_ready" if files else "uploaded_url_map_editor_blocked",
        "source_path": str(source_path),
        "html_path": str(html_path),
        "file_count": len(files),
        "files": files,
        "download_filename": DOWNLOAD_NAME,
        "instructions_zh": [
            "逐张填写公开 HTTPS 图片 URL。",
            "确认图片与页面匹配后勾选 owner_url_confirmed。",
            "下载 uploaded-url-map.filled.json 后放到 seo-workspace/data/，再运行 content-studio-uploaded-url-map-import。",
            "所有图片仍是设计方案/效果图方案/rendering concept，不得写成真实完工案例或客户照片。",
        ],
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }


def render_file_card(item: dict[str, Any], index: int) -> str:
    local_href = file_href(str(item.get("local_path", "")))
    filename = html.escape(str(item.get("placeholder_filename") or item.get("filename") or f"file-{index}"))
    object_path = html.escape(str(item.get("object_path", "")))
    file_url = html.escape(str(item.get("file_url", "")))
    alt_zh = html.escape(str(item.get("alt_zh", "")))
    alt_en = html.escape(str(item.get("alt_en", "")))
    boundary = html.escape(str(item.get("claim_boundary", "")))
    checked = " checked" if item.get("owner_url_confirmed") is True else ""
    preview = (
        f'<img src="{html.escape(local_href)}" alt="{alt_en or alt_zh or filename}" loading="lazy" />'
        if local_href
        else '<div class="preview-empty">No local preview</div>'
    )
    return f"""
    <article class="file-card" data-index="{index}">
      <div class="preview">{preview}</div>
      <div class="fields">
        <h2>{filename}</h2>
        <p class="object-path">{object_path}</p>
        <label>Public HTTPS URL</label>
        <input data-field="file_url" value="{file_url}" placeholder="https://cdn.example.com/path/image.webp" />
        <label class="check">
          <input data-field="owner_url_confirmed" type="checkbox"{checked} />
          <span>owner_url_confirmed：我确认这个 URL 可公开访问，且图片只作为设计/效果图概念使用</span>
        </label>
        <div class="copy">
          <strong>Alt ZH</strong><span>{alt_zh or "未填写"}</span>
          <strong>Alt EN</strong><span>{alt_en or "Not filled"}</span>
          <strong>Claim Boundary</strong><span>{boundary}</span>
        </div>
      </div>
    </article>
    """.strip()


def render_html(summary: dict[str, Any]) -> str:
    files = safe_list(summary.get("files"))
    cards = "\n".join(render_file_card(item, index) for index, item in enumerate(files, start=1) if isinstance(item, dict))
    payload_raw_json = json.dumps({"files": files}, ensure_ascii=False).replace("</", "<\\/")
    payload_preview_json = html.escape(json.dumps({"files": files}, ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Uploaded URL Map Editor</title>
  <style>
    :root {{
      --ink: #17211d;
      --paper: #f4efe5;
      --card: #fffaf0;
      --line: #d5c3a7;
      --accent: #9a4f2c;
      --ok: #3f6f4f;
    }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Gill Sans", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 0%, rgba(154,79,44,.18), transparent 26rem),
        linear-gradient(135deg, #f8f1e5, #e9dfcb);
    }}
    header, main {{
      padding: 34px min(7vw, 76px);
    }}
    .kicker {{
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .14em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 10px 0;
      max-width: 920px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(36px, 6vw, 72px);
      line-height: .95;
      letter-spacing: -.055em;
    }}
    .note {{
      max-width: 900px;
      color: #61584b;
      line-height: 1.65;
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 2;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      padding: 14px min(7vw, 76px);
      background: rgba(244,239,229,.92);
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(10px);
    }}
    button {{
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      background: var(--ink);
      color: #fff8ec;
      font-weight: 800;
      cursor: pointer;
    }}
    button.secondary {{
      background: var(--ok);
    }}
    .status {{
      align-self: center;
      color: #61584b;
      font-weight: 700;
    }}
    .file-grid {{
      display: grid;
      gap: 18px;
    }}
    .file-card {{
      display: grid;
      grid-template-columns: minmax(180px, 320px) 1fr;
      gap: 18px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 26px;
      background: rgba(255,250,240,.82);
      box-shadow: 0 22px 60px rgba(34, 26, 14, .08);
    }}
    .preview {{
      min-height: 210px;
      border-radius: 20px;
      overflow: hidden;
      background: #ded2bb;
      display: grid;
      place-items: center;
    }}
    .preview img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .preview-empty {{
      color: #7c705d;
      font-weight: 800;
    }}
    h2 {{
      margin: 0 0 4px;
      font-size: 24px;
    }}
    .object-path {{
      margin: 0 0 14px;
      color: #756b5a;
      word-break: break-all;
    }}
    label {{
      display: block;
      margin: 12px 0 6px;
      font-size: 12px;
      font-weight: 900;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--accent);
    }}
    input[type="text"], input:not([type]) {{
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 13px 14px;
      font-size: 15px;
      background: #fffdf7;
      color: var(--ink);
    }}
    .check {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      color: var(--ink);
      text-transform: none;
      letter-spacing: 0;
      font-size: 14px;
      line-height: 1.45;
    }}
    .copy {{
      display: grid;
      grid-template-columns: 140px 1fr;
      gap: 8px 12px;
      margin-top: 16px;
      padding-top: 14px;
      border-top: 1px solid var(--line);
      color: #4f493f;
    }}
    .copy strong {{
      color: var(--accent);
    }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      padding: 16px;
      border-radius: 18px;
      background: #151f1b;
      color: #fff8ec;
    }}
    @media (max-width: 760px) {{
      .file-card {{
        grid-template-columns: 1fr;
      }}
      .toolbar {{
        position: static;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="kicker">FLASH CAST Content Studio</div>
    <h1>图片公开 URL 填写表单</h1>
    <p class="note">这一步只帮助你把已上传或已选择的设计效果图 URL 填进 JSON。不会上传图片、不会写 CMS、不会发布。生成图片必须继续标注为设计方案 / 效果图方案 / rendering concept。</p>
  </header>
  <div class="toolbar">
    <button type="button" id="download">Download {DOWNLOAD_NAME}</button>
    <button type="button" id="preview" class="secondary">Preview JSON</button>
    <span class="status" id="status">{len(files)} files loaded</span>
  </div>
  <main>
    <section class="file-grid" id="fileGrid">{cards or '<p>No files. Run content-studio-media-url-template first.</p>'}</section>
    <h2>JSON Preview</h2>
    <pre id="jsonPreview">{payload_preview_json}</pre>
  </main>
  <script type="application/json" id="initialPayload">{payload_raw_json}</script>
  <script>
    const initial = JSON.parse(document.getElementById('initialPayload').textContent);
    const files = initial.files || [];
    function collect() {{
      return {{
        generated_at: new Date().toISOString(),
        status: 'uploaded_url_map_owner_filled_from_editor',
        files: files.map((file, index) => {{
          const card = document.querySelector(`.file-card[data-index="${{index + 1}}"]`);
          const url = card?.querySelector('[data-field="file_url"]')?.value?.trim() || '';
          const confirmed = card?.querySelector('[data-field="owner_url_confirmed"]')?.checked || false;
          return {{ ...file, file_url: url, owner_url_confirmed: confirmed, upload_status: url ? 'owner_filled_public_url' : 'needs_public_url' }};
        }}),
        no_media_upload_executed: true,
        no_cms_write_executed: true,
        no_source_write_executed: true,
        no_publish_executed: true,
        owner_review_required: true
      }};
    }}
    function refreshPreview() {{
      const payload = collect();
      document.getElementById('jsonPreview').textContent = JSON.stringify(payload, null, 2);
      const ready = payload.files.filter(file => file.file_url.startsWith('https://') && file.owner_url_confirmed).length;
      document.getElementById('status').textContent = `${{ready}}/${{payload.files.length}} confirmed HTTPS URLs`;
      return payload;
    }}
    document.getElementById('preview').addEventListener('click', refreshPreview);
    document.getElementById('download').addEventListener('click', () => {{
      const payload = refreshPreview();
      const blob = new Blob([JSON.stringify(payload, null, 2) + '\\n'], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = '{DOWNLOAD_NAME}';
      link.click();
      URL.revokeObjectURL(url);
    }});
    document.querySelectorAll('input').forEach(input => input.addEventListener('input', refreshPreview));
    refreshPreview();
  </script>
</body>
</html>
"""


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Uploaded URL Map Editor",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{summary.get('status')}`",
        f"- Source: `{summary.get('source_path')}`",
        f"- HTML: `{summary.get('html_path')}`",
        f"- Files: `{summary.get('file_count')}`",
        "- 执行状态: local editor only / no upload / no CMS / no publish",
        "",
        "## 今日决策",
        "",
        "今天把图片 URL handoff 从手改 JSON 升级为本地可视化表单。业主或上传人员可以看着每张设计/效果图概念图填写公开 HTTPS URL，再下载 uploaded-url-map.filled.json。",
        "",
        "## 下一步",
        "",
        "- 打开 HTML 表单，逐张填写公开 HTTPS URL，并勾选 owner_url_confirmed。",
        "- 下载 `uploaded-url-map.filled.json` 后放到 `seo-workspace/data/`。",
        "- 运行 `content-studio-uploaded-url-map-import --filled-map-path seo-workspace/data/uploaded-url-map.filled.json`，导入成功后再运行 `content-studio-media-status`。",
        "",
        "## 安全边界",
        "",
        "- 本工具不上传图片、不调用 CMS、不写源码、不发布、不部署。",
        "- URL 填写只解决图片可访问问题，不允许把概念图写成真实客户案例或真实完工照片。",
    ]
    return "\n".join(lines) + "\n"


def run_content_studio_uploaded_url_map_editor(
    root: Path,
    *,
    source_path: str = "",
) -> tuple[dict[str, Any], tuple[Path, Path, Path]]:
    root = root.resolve()
    source_file = selected_source(root, source_path)
    html_path = root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-{HTML_NAME}"
    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    source = read_json(source_file)
    summary = build_summary(source, source_file, html_path)
    write_text(html_path, render_html(summary))
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, html_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local HTML editor for owner-filled uploaded media URLs.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_uploaded_url_map_editor(Path(args.root), source_path=args.source_path)
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "uploaded_url_map_editor_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
