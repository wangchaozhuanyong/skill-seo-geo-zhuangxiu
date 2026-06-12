#!/usr/bin/env python3
"""Create a local HTML form for owner decision review/export."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
from typing import Any


DEFAULT_DECISION = "seo-workspace/data/content-studio-owner-decision.template.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def render_editor_html(template: dict[str, Any], manifest: dict[str, Any]) -> str:
    decision = safe_dict(template.get("decision"))
    options = safe_list(decision.get("allowed_execution_scope_options")) or [
        "owner_review_only",
        "media_ready_handoff_only",
        "approved_dry_run_only",
        "operator_ready_handoff_only",
        "live_publish_requires_separate_confirmation",
    ]
    selected_scope = str(decision.get("allowed_execution_scope", "owner_review_only"))
    option_html = "\n".join(
        f'<option value="{html.escape(str(option))}" {"selected" if str(option) == selected_scope else ""}>{html.escape(str(option))}</option>'
        for option in options
    )
    action_items = safe_list(template.get("action_items_snapshot"))
    action_html = "\n".join(
        f"<li><strong>{html.escape(str(safe_dict(item).get('title_zh', '')))}</strong><span>{html.escape(str(safe_dict(item).get('details_zh', '')))}</span></li>"
        for item in action_items
    ) or "<li>当前模板没有行动项快照。</li>"
    template_json = json.dumps(template, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Content Studio Owner Decision Editor</title>
  <style>
    :root {{
      --ink: #17231f;
      --paper: #f4eadb;
      --card: rgba(255,255,255,.78);
      --line: #d7c6aa;
      --accent: #a6542d;
      --green: #53624f;
    }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Gill Sans", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 0%, rgba(166,84,45,.18), transparent 26rem),
        linear-gradient(135deg, rgba(83,98,79,.12), transparent 42%),
        var(--paper);
    }}
    header, main {{
      padding: 34px min(7vw, 76px);
    }}
    .kicker {{
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
    }}
    h1 {{
      max-width: 920px;
      margin: 12px 0 14px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(36px, 6vw, 72px);
      line-height: .95;
      letter-spacing: -.055em;
    }}
    .meta {{
      line-height: 1.65;
      color: #5d5549;
      overflow-wrap: anywhere;
    }}
    form, section {{
      max-width: 980px;
      margin: 0 0 22px;
      padding: 22px;
      border-radius: 26px;
      background: var(--card);
      border: 1px solid var(--line);
      box-shadow: 0 18px 46px rgba(75,55,30,.08);
    }}
    label {{
      display: flex;
      gap: 12px;
      align-items: flex-start;
      padding: 12px 0;
      line-height: 1.55;
      border-bottom: 1px solid rgba(215,198,170,.7);
      font-weight: 700;
    }}
    input[type="checkbox"] {{
      width: 22px;
      height: 22px;
      margin-top: 2px;
      accent-color: var(--green);
    }}
    select, textarea {{
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 12px 14px;
      margin-top: 10px;
      font: inherit;
      background: #fffaf1;
      color: var(--ink);
    }}
    textarea {{
      min-height: 110px;
    }}
    button {{
      border: 0;
      border-radius: 999px;
      padding: 14px 20px;
      margin: 14px 12px 0 0;
      background: var(--ink);
      color: #fff8ec;
      font-weight: 800;
      cursor: pointer;
    }}
    code, pre {{
      display: block;
      padding: 14px;
      border-radius: 16px;
      overflow: auto;
      background: #17231f;
      color: #fff8ec;
      font-size: 12px;
      line-height: 1.55;
    }}
    ul {{
      padding-left: 20px;
      line-height: 1.75;
    }}
    li span {{
      display: block;
      color: #5d5549;
    }}
  </style>
</head>
<body>
  <header>
    <div class="kicker">Local form · Export JSON · No publish</div>
    <h1>业主决定表单</h1>
    <p class="meta">目标页面：{html.escape(str(template.get("target_url", "not_found")))}<br />配对页面：{html.escape(str(template.get("paired_url", "not_found")))}<br />模板路径：{html.escape(str(manifest.get("decision_template_path", "")))}</p>
  </header>
  <main>
    <form id="decision-form">
      <label><input type="checkbox" id="content_approved" {"checked" if decision.get("content_approved") is True else ""} />内容已审核通过 content_approved</label>
      <label><input type="checkbox" id="media_urls_confirmed" {"checked" if decision.get("media_urls_confirmed") is True else ""} />图片公开 URL 已确认 media_urls_confirmed</label>
      <label><input type="checkbox" id="qa_approved" {"checked" if decision.get("qa_approved") is True else ""} />发布前 QA 已确认 qa_approved</label>
      <label><input type="checkbox" id="latest_research_verified" {"checked" if decision.get("latest_research_verified") is True else ""} />最新资料/引用已确认 latest_research_verified</label>
      <label><input type="checkbox" id="explicit_execution_requested" {"checked" if decision.get("explicit_execution_requested") is True else ""} />我明确请求进入下一步执行门禁 explicit_execution_requested</label>
      <label>允许范围 allowed_execution_scope
        <select id="allowed_execution_scope">{option_html}</select>
      </label>
      <label>业主备注 owner_notes
        <textarea id="owner_notes">{html.escape(str(decision.get("owner_notes", "")))}</textarea>
      </label>
      <button type="button" id="preview">预览 JSON</button>
      <button type="button" id="download">下载 filled JSON</button>
    </form>
    <section>
      <h2>需要确认的事项</h2>
      <ul>{action_html}</ul>
    </section>
    <section>
      <h2>安全提醒</h2>
      <ul>
        <li>这个页面只导出 JSON，不会上传图片、不会写 CMS、不会发布、不会部署。</li>
        <li>勾选批准不等于真实发布；真实执行仍需要你另外明确说执行哪个页面和哪个范围。</li>
        <li>生成图、效果图、概念图只能作为设计方案/效果图方案，不能写成真实完工案例照片。</li>
      </ul>
    </section>
    <section>
      <h2>JSON 预览</h2>
      <pre id="output"></pre>
    </section>
  </main>
  <script>
    const template = {template_json};
    function currentPayload() {{
      const payload = JSON.parse(JSON.stringify(template));
      payload.status = "owner_decision_filled_waiting_codex_review";
      payload.filled_at = new Date().toISOString();
      payload.decision = {{
        ...payload.decision,
        content_approved: document.getElementById("content_approved").checked,
        media_urls_confirmed: document.getElementById("media_urls_confirmed").checked,
        qa_approved: document.getElementById("qa_approved").checked,
        latest_research_verified: document.getElementById("latest_research_verified").checked,
        explicit_execution_requested: document.getElementById("explicit_execution_requested").checked,
        allowed_execution_scope: document.getElementById("allowed_execution_scope").value,
        owner_notes: document.getElementById("owner_notes").value
      }};
      payload.exported_from_owner_decision_editor = true;
      payload.approval_is_not_execution = true;
      payload.no_cms_write_executed = true;
      payload.no_source_write_executed = true;
      payload.no_media_upload_executed = true;
      payload.no_publish_executed = true;
      payload.no_deploy_executed = true;
      return payload;
    }}
    function renderPreview() {{
      document.getElementById("output").textContent = JSON.stringify(currentPayload(), null, 2);
    }}
    document.getElementById("preview").addEventListener("click", renderPreview);
    document.getElementById("download").addEventListener("click", () => {{
      const blob = new Blob([JSON.stringify(currentPayload(), null, 2) + "\\n"], {{ type: "application/json" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "content-studio-owner-decision.filled.json";
      a.click();
      URL.revokeObjectURL(url);
    }});
    renderPreview();
  </script>
</body>
</html>
"""


def render_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Content Studio Owner Decision Editor",
            "",
            f"- 生成日期: {dt.date.today().isoformat()}",
            f"- 状态: `{summary['status']}`",
            f"- 目标页面: `{summary.get('target_url') or 'not_found'}`",
            f"- 配对页面: `{summary.get('paired_url') or 'not_found'}`",
            f"- HTML editor: `{summary.get('html_path')}`",
            "- 执行状态: local decision editor only；未上传媒体、未写 CMS、未改源码、未发布、未部署",
            "",
            "## 使用方式",
            "",
            "- 打开 HTML editor。",
            "- 勾选内容审核、媒体 URL、QA、资料确认和允许范围。",
            "- 点击下载 filled JSON。",
            "- 后续运行 `content-studio-owner-decision-import --filled-decision-path <downloaded-json>` 导入，再跑状态检查。",
            "",
            "## 安全边界",
            "",
            "- 这个 editor 只导出 JSON。",
            "- approval 仍不等于 execution。",
            "- 真实发布仍需要业主另行明确执行指令和发布门禁。",
        ]
    ) + "\n"


def run_content_studio_owner_decision_editor(
    root: Path,
    *,
    decision_path: str = "",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    decision_file = resolve_path(root, decision_path or DEFAULT_DECISION)
    template = read_json(decision_file)
    blockers: list[str] = []
    if not template:
        blockers.append("Missing owner decision template. Run content-studio-approval-packet first.")
    html_path = root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-content-studio-owner-decision-editor.html"
    manifest_path = root / "seo-workspace" / "data" / "content-studio-owner-decision-editor.json"
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-owner-decision-editor.md"
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "owner_decision_editor_ready" if not blockers else "owner_decision_editor_blocked",
        "target_url": template.get("target_url", ""),
        "paired_url": template.get("paired_url", ""),
        "decision_template_path": str(decision_file),
        "html_path": str(html_path),
        "report_path": str(report_path),
        "blockers": blockers,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_editor_html(template, summary), encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return summary, [manifest_path, html_path, report_path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local HTML owner decision form; does not execute.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--decision-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_owner_decision_editor(Path(args.root), decision_path=args.decision_path)
    for output in artifacts:
        print(output)
    return 0 if summary["status"] == "owner_decision_editor_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
