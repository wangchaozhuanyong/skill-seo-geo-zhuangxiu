#!/usr/bin/env python3
"""Build a local owner-review gallery for generated Content Studio media."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
from typing import Any


SUMMARY_NAME = "content-studio-media-review-package.json"
REPORT_NAME = "content-studio-media-review-package.md"
HTML_NAME = "content-studio-media-review-gallery.html"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_path(root: Path, value: str, default: str) -> Path:
    raw = value or default
    path = Path(raw)
    return path if path.is_absolute() else root / path


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def concept_by_placeholder(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for raw in safe_list(manifest.get("assets")):
        if isinstance(raw, dict) and raw.get("placeholder_filename"):
            rows[str(raw["placeholder_filename"])] = raw
    return rows


def build_items(media_plan: dict[str, Any], concept_manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    items: list[dict[str, Any]] = []
    blockers: list[str] = []
    concepts = concept_by_placeholder(concept_manifest)
    queue = safe_list(media_plan.get("queue"))
    if not queue:
        blockers.append("media-upload-plan.json has no queue items. Run media-upload-plan first.")
    for raw in queue:
        if not isinstance(raw, dict):
            continue
        placeholder = str(raw.get("placeholder_filename", ""))
        concept = concepts.get(placeholder, {})
        local_path = str(raw.get("local_path") or concept.get("local_path") or "")
        local_file = Path(local_path) if local_path else Path()
        exists = bool(local_path and local_file.is_file())
        if not exists:
            blockers.append(f"Local media file missing for {placeholder}: {local_path or 'missing'}")
        items.append(
            {
                "queue_id": raw.get("queue_id", ""),
                "placeholder_filename": placeholder,
                "public_filename": raw.get("public_filename") or concept.get("generated_filename", ""),
                "local_path": local_path,
                "local_file_exists": exists,
                "object_path": raw.get("object_path", ""),
                "bucket": raw.get("bucket", ""),
                "public_url_to_fill": raw.get("public_url", ""),
                "usage_type": raw.get("usage_type") or concept.get("usage_type", ""),
                "alt_zh": raw.get("alt_zh", ""),
                "alt_en": raw.get("alt_en", ""),
                "concept_label": concept.get("concept_label", "概念设计 / 效果图方案 / design concept / rendering concept"),
                "claim_boundary": raw.get("claim_boundary") or concept.get("claim_boundary", ""),
                "upload_helper": raw.get("upload_helper", "uploadAdminMediaObject"),
                "record_helper": raw.get("record_helper", "createAdminMediaAsset"),
            }
        )
    return items, blockers


def image_src(path_value: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    return path.as_uri() if path.is_absolute() else path_value


def render_html(summary: dict[str, Any]) -> str:
    cards: list[str] = []
    for item in safe_list(summary.get("items")):
        src = image_src(str(item.get("local_path", ""))) if item.get("local_file_exists") else ""
        img_html = (
            f'<img src="{html.escape(src)}" alt="{html.escape(str(item.get("alt_en") or item.get("alt_zh") or item.get("placeholder_filename")))}" />'
            if src
            else '<div class="missing">Local file missing</div>'
        )
        cards.append(
            f"""
      <article class="card">
        <div class="preview">{img_html}</div>
        <div class="body">
          <p class="eyebrow">{html.escape(str(item.get("usage_type", "")))} · {html.escape(str(item.get("concept_label", "")))}</p>
          <h2>{html.escape(str(item.get("public_filename", "")))}</h2>
          <label>Public HTTPS URL to fill</label>
          <input readonly value="{html.escape(str(item.get("public_url_to_fill", "")))}" />
          <dl>
            <dt>Placeholder</dt><dd>{html.escape(str(item.get("placeholder_filename", "")))}</dd>
            <dt>Local file</dt><dd>{html.escape(str(item.get("local_path", "")))}</dd>
            <dt>Upload object path</dt><dd>{html.escape(str(item.get("object_path", "")))}</dd>
            <dt>中文 alt</dt><dd>{html.escape(str(item.get("alt_zh", "")))}</dd>
            <dt>English alt</dt><dd>{html.escape(str(item.get("alt_en", "")))}</dd>
            <dt>Claim boundary</dt><dd>{html.escape(str(item.get("claim_boundary", "")))}</dd>
          </dl>
        </div>
      </article>
            """.strip()
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Content Studio Media Review Gallery</title>
  <style>
    :root {{
      --ink: #17201a;
      --paper: #f7f1e7;
      --line: #d7c8ad;
      --accent: #b45f2a;
      --muted: #685f52;
    }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Gill Sans", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(180,95,42,.18), transparent 32rem),
        linear-gradient(135deg, #fbf6ec, var(--paper));
    }}
    header {{
      padding: 42px min(7vw, 72px) 20px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(34px, 6vw, 72px);
      letter-spacing: -0.055em;
      line-height: .94;
      max-width: 980px;
    }}
    .meta {{
      color: var(--muted);
      max-width: 860px;
      line-height: 1.6;
      margin-top: 18px;
    }}
    main {{
      display: grid;
      gap: 22px;
      padding: 28px min(7vw, 72px) 56px;
    }}
    .card {{
      display: grid;
      grid-template-columns: minmax(220px, 34%) 1fr;
      gap: 22px;
      padding: 18px;
      background: rgba(255,255,255,.72);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: 0 18px 50px rgba(74, 58, 34, .08);
    }}
    .preview {{
      min-height: 240px;
      display: grid;
      place-items: center;
      background: #fffaf2;
      border-radius: 18px;
      overflow: hidden;
      border: 1px solid rgba(215,200,173,.7);
    }}
    img {{
      width: 100%;
      height: 100%;
      max-height: 360px;
      object-fit: contain;
    }}
    .missing {{
      color: #8a2b1b;
      font-weight: 700;
    }}
    .eyebrow {{
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: .11em;
      font-size: 12px;
      font-weight: 700;
      margin: 0 0 8px;
    }}
    h2 {{
      margin: 0 0 16px;
      font-size: clamp(22px, 3vw, 38px);
      letter-spacing: -.035em;
    }}
    label {{
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
      font-weight: 700;
    }}
    input {{
      width: 100%;
      box-sizing: border-box;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      margin-bottom: 16px;
    }}
    dl {{
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 8px 14px;
      margin: 0;
      font-size: 14px;
      line-height: 1.45;
    }}
    dt {{
      color: var(--muted);
      font-weight: 700;
    }}
    dd {{
      margin: 0;
      overflow-wrap: anywhere;
    }}
    @media (max-width: 760px) {{
      .card {{ grid-template-columns: 1fr; }}
      dl {{ grid-template-columns: 1fr; }}
      dt {{ margin-top: 8px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Content Studio Media Review Gallery</h1>
    <p class="meta">本页面用于审核装修设计效果图/概念图，并辅助填写公开 HTTPS 图片 URL。所有图片都必须继续标注为 design/rendering concept，不得作为真实完工案例、客户照片或评价证明。</p>
    <p class="meta">Status: <strong>{html.escape(str(summary.get("status", "")))}</strong> · Items: <strong>{len(safe_list(summary.get("items")))}</strong> · No upload / no CMS / no publish</p>
  </header>
  <main>
    {"".join(cards) if cards else '<p>No media items found.</p>'}
  </main>
</body>
</html>
"""


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Media Review Package",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{summary.get('status')}`",
        f"- Items: `{summary.get('item_count')}`",
        f"- Gallery: `{summary.get('artifacts', {}).get('gallery_html', '')}`",
        "- 执行状态: local owner review only；未上传媒体、未写 CMS、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把已生成的装修设计效果图/概念图整理成可审核 HTML gallery。业主或上传器可以在一个页面里核对图片、alt、图注边界、上传目标路径，并据此填写公开 HTTPS URL。",
        "",
        "## Media Items",
        "",
    ]
    items = safe_list(summary.get("items"))
    if items:
        for item in items:
            lines.append(f"- `{item.get('placeholder_filename')}` -> `{item.get('public_filename')}` -> exists `{item.get('local_file_exists')}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    blockers = safe_list(summary.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 打开 HTML gallery 审核每张效果图是否适合页面使用。",
            "- 上传或选择通过审核的图片，获得公开 HTTPS URL。",
            "- 把 URL 填入 `seo-workspace/data/uploaded-url-map.json` 的 `file_url`，并把 `owner_url_confirmed` 改为 `true`。",
            "- 然后运行 `content-studio-media-ready-handoff` 生成 media-ready CMS payload。",
            "",
            "## 安全边界",
            "",
            "- 本命令不上传文件、不调用 CMS/admin helper、不写源码、不发布、不部署。",
            "- 效果图只能作为设计方案、效果图方案、design/rendering concept 使用。",
            "- 不得把这些图片描述为真实完工案例、真实客户照片、前后对比证明或客户评价。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_media_review_package(
    root: Path,
    *,
    media_upload_plan_path: str = "",
    concept_manifest_path: str = "",
) -> tuple[dict[str, Any], tuple[Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    drafts_dir = root / "seo-workspace" / "drafts"
    media_plan_file = resolve_path(root, media_upload_plan_path, "seo-workspace/data/media-upload-plan.json")
    concept_manifest_file = resolve_path(root, concept_manifest_path, "seo-workspace/data/concept-asset-manifest.json")
    media_plan = read_json(media_plan_file)
    concept_manifest = read_json(concept_manifest_file)
    items, blockers = build_items(media_plan, concept_manifest)
    status = "media_review_package_ready" if items and not blockers else "blocked_missing_media_review_inputs"
    data_path = data_dir / SUMMARY_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    gallery_path = drafts_dir / f"{dt.date.today().isoformat()}-{HTML_NAME}"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "item_count": len(items),
        "media_upload_plan_path": str(media_plan_file),
        "concept_manifest_path": str(concept_manifest_file),
        "items": items,
        "blockers": blockers,
        "artifacts": {
            "summary_json": str(data_path),
            "report": str(report_path),
            "gallery_html": str(gallery_path),
        },
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(gallery_path, render_html(summary))
    write_text(report_path, render_report(summary))
    return summary, (data_path, gallery_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local owner-review gallery for generated Content Studio media.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--media-upload-plan-path", default="")
    parser.add_argument("--concept-manifest-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_media_review_package(
        Path(args.root),
        media_upload_plan_path=args.media_upload_plan_path,
        concept_manifest_path=args.concept_manifest_path,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if summary["status"] == "media_review_package_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
