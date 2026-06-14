#!/usr/bin/env python3
"""Build the full no-write owner review package for the latest Content Studio page."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

from content_studio_approval_packet import run_content_studio_approval_packet
from content_studio_media_review_package import run_content_studio_media_review_package
from content_studio_media_status import run_content_studio_media_status
from content_studio_media_url_template import run_content_studio_media_url_template
from content_studio_owner_decision_editor import run_content_studio_owner_decision_editor
from content_studio_owner_decision_status import run_content_studio_owner_decision_status
from content_studio_publish_candidate import run_content_studio_publish_candidate
from content_studio_publish_prep import run_content_studio_publish_prep
from content_studio_uploaded_url_map_draft import run_content_studio_uploaded_url_map_draft
from content_studio_uploaded_url_map_editor import run_content_studio_uploaded_url_map_editor


def step_summary(name: str, payload: dict[str, Any], artifacts: list[Path]) -> dict[str, Any]:
    return {
        "step": name,
        "status": str(payload.get("status", "")),
        "target_url": str(payload.get("target_url", "")),
        "paired_url": str(payload.get("paired_url", "")),
        "artifact_count": len(artifacts),
        "artifacts": [str(path) for path in artifacts],
    }


def file_href(path_value: str) -> str:
    if not path_value:
        return "#"
    path = Path(path_value)
    return path.as_uri() if path.is_absolute() else path_value


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def build_recommended_commands(website_root: str = "", target_url: str = "") -> list[dict[str, str]]:
    base = "python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py"
    owner_review = f"{base} content-studio-owner-review-package"
    if target_url:
        owner_review += f" --target-url {target_url}"
    if website_root:
        owner_review += f" --website-root {website_root}"
    return [
        {
            "label": "应用富文本编辑导出",
            "when": "从 rich editor 下载 edited-export.json 并放到 seo-workspace/data/ 后运行。",
            "command": f"{base} rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json",
        },
        {
            "label": "刷新图文媒体资产计划",
            "when": "应用 edited-export 后运行，让新增图片块进入媒体上传/URL 计划。",
            "command": f"{base} media-assets",
        },
        {
            "label": "导入业主决定 JSON",
            "when": "从业主决定表单下载 filled JSON 后运行。",
            "command": f"{base} content-studio-owner-decision-import --filled-decision-path seo-workspace/data/content-studio-owner-decision.filled.json",
        },
        {
            "label": "复查业主决定状态",
            "when": "导入 filled JSON 后运行，确认现在允许到哪一步。",
            "command": f"{base} content-studio-owner-decision-status",
        },
        {
            "label": "按决定推进下一步",
            "when": "状态允许 media-ready 或 approved dry-run 时运行；仍不发布。",
            "command": f"{base} content-studio-decision-orchestrator",
        },
        {
            "label": "复查媒体 URL 状态",
            "when": "填写或修改 uploaded-url-map.json 后运行。",
            "command": f"{base} content-studio-media-status",
        },
        {
            "label": "打开图片 URL 填写表单",
            "when": "不想手改 JSON 时，打开 HTML 表单填写公开 HTTPS URL 并下载 uploaded-url-map.filled.json。",
            "command": f"{base} content-studio-uploaded-url-map-editor",
        },
        {
            "label": "导入已填写图片 URL JSON",
            "when": "从 HTML 表单下载 uploaded-url-map.filled.json 后运行；会先校验再写入工作区 uploaded-url-map.json。",
            "command": f"{base} content-studio-uploaded-url-map-import --filled-map-path seo-workspace/data/uploaded-url-map.filled.json",
        },
        {
            "label": "生成 media-ready handoff",
            "when": "所有 file_url 都是公开 HTTPS URL 且 owner_url_confirmed=true 后运行。",
            "command": f"{base} content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed",
        },
        {
            "label": "刷新到 operator-ready 本地发布包",
            "when": "media-ready URL 已确认，且需要一次性刷新 publish readiness / bundle / operator command 时运行；仍不发布。",
            "command": f"{base} content-studio-operator-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed --latest-research-verified --allow-blocked-plan --allow-blocked-operator",
        },
        {
            "label": "刷新完整业主审核总包",
            "when": "媒体 URL 或审核结论变化后运行，重新生成 dashboard。",
            "command": owner_review,
        },
        {
            "label": "最终发布前就绪检查",
            "when": "media-ready payload 已生成，并且业主明确要求继续执行前运行。",
            "command": f"{base} publish-readiness",
        },
    ]


def render_dashboard(summary: dict[str, Any]) -> str:
    artifacts = summary.get("key_artifacts") if isinstance(summary.get("key_artifacts"), dict) else {}
    media_summary = safe_dict(summary.get("media_status_summary"))
    decision_summary = safe_dict(summary.get("owner_decision_status_summary"))
    media_counts = safe_dict(media_summary.get("counts"))
    media_next_actions = safe_list(media_summary.get("next_actions"))
    media_next_html = "\n".join(f"<li>{html.escape(str(item))}</li>" for item in media_next_actions) if media_next_actions else "<li>None</li>"
    recommended_commands = safe_list(summary.get("recommended_commands"))
    command_html = "\n".join(
        f"""
        <li>
          <span>{html.escape(str(item.get("label", "")))}</span>
          <small>{html.escape(str(item.get("when", "")))}</small>
          <code>{html.escape(str(item.get("command", "")))}</code>
        </li>
        """.strip()
        for item in recommended_commands
        if isinstance(item, dict)
    ) or "<li>None</li>"
    cards = [
        ("审批行动包", "先看这里：内容批准、QA、媒体 URL、执行范围需要业主确认。", artifacts.get("approval_packet", "")),
        ("富文本图文编辑器", "拖拽编辑中英文图文、添加图片/CTA，并下载 edited-export.json。", artifacts.get("rich_editor", "")),
        ("已应用图文 Payload", "查看 rich-editor-apply 后的 CMS payload 草稿；仍不发布。", artifacts.get("editor_applied_payload", "")),
        ("业主决定表单", "不用手写 JSON：打开本地表单勾选审批项并导出 filled JSON。", artifacts.get("owner_decision_editor", "")),
        ("业主决定模板", "填写内容批准、媒体 URL、QA 和是否请求执行；填写不等于自动执行。", artifacts.get("owner_decision_template", "")),
        ("业主决定状态", "读取已填写决定模板，判断现在只能审核、media-ready，还是进入 approved dry-run。", artifacts.get("owner_decision_status", "")),
        ("图文发布准备", "查看 publish-prep 证据、发布门禁、执行前阻断项。", artifacts.get("publish_prep", "")),
        ("效果图审核 Gallery", "逐张查看设计效果图/概念图，确认是否适合页面使用。", artifacts.get("media_review_gallery", "")),
        ("图片 URL 填写表单", "看着每张概念图填写公开 HTTPS URL，下载 uploaded-url-map.filled.json。", artifacts.get("uploaded_url_map_editor", "")),
        ("可填写 URL 草稿", "上传或选择图片后，把公开 HTTPS URL 填入这个 JSON。", artifacts.get("uploaded_url_map_draft", "")),
        ("媒体状态报告", "复查还缺哪些图片 URL、哪些还没有 owner confirmation。", artifacts.get("media_status", "")),
        ("候选发布项", "查看本次 owner-review 对应的目标页面和配对页面。", artifacts.get("publish_candidate", "")),
    ]
    card_html = []
    for title, desc, path_value in cards:
        card_html.append(
            f"""
      <a class="card" href="{html.escape(file_href(str(path_value)))}">
        <span>{html.escape(title)}</span>
        <strong>{html.escape(str(path_value or 'not generated'))}</strong>
        <p>{html.escape(desc)}</p>
      </a>
            """.strip()
        )
    steps_html = "\n".join(
        f"<li><span>{html.escape(str(step.get('step', '')))}</span><strong>{html.escape(str(step.get('status', '')))}</strong></li>"
        for step in summary.get("steps", [])
    )
    blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
    blocker_html = "\n".join(f"<li>{html.escape(str(item))}</li>" for item in blockers) if blockers else "<li>None</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Content Studio Owner Review Dashboard</title>
  <style>
    :root {{
      --ink: #18231f;
      --paper: #f5efe4;
      --card: rgba(255,255,255,.76);
      --line: #d8c8ad;
      --accent: #9d4f2c;
      --sage: #68735b;
    }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Gill Sans", sans-serif;
      color: var(--ink);
      background:
        linear-gradient(120deg, rgba(157,79,44,.16), transparent 34%),
        radial-gradient(circle at right top, rgba(104,115,91,.16), transparent 28rem),
        var(--paper);
    }}
    header {{
      padding: 48px min(7vw, 78px) 28px;
      border-bottom: 1px solid var(--line);
    }}
    .kicker {{
      color: var(--accent);
      font-weight: 800;
      letter-spacing: .12em;
      text-transform: uppercase;
      font-size: 12px;
    }}
    h1 {{
      margin: 12px 0 16px;
      max-width: 920px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(36px, 6vw, 76px);
      line-height: .94;
      letter-spacing: -.055em;
    }}
    .meta {{
      color: #5f594d;
      line-height: 1.65;
      max-width: 980px;
    }}
    main {{
      padding: 28px min(7vw, 78px) 64px;
    }}
    .actions {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      margin: 22px 0 34px;
    }}
    .action {{
      padding: 18px;
      border-radius: 22px;
      background: #17231f;
      color: #fff8ec;
      min-height: 110px;
    }}
    .action strong {{
      display: block;
      font-size: 20px;
      margin-bottom: 8px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .status-band {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 0 0 24px;
    }}
    .metric {{
      padding: 16px;
      border-radius: 20px;
      background: rgba(255,255,255,.72);
      border: 1px solid var(--line);
    }}
    .metric span {{
      display: block;
      color: var(--sage);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .metric strong {{
      display: block;
      margin-top: 6px;
      font-size: clamp(24px, 4vw, 44px);
      line-height: 1;
    }}
    .card {{
      display: block;
      padding: 18px;
      min-height: 138px;
      border-radius: 24px;
      background: var(--card);
      border: 1px solid var(--line);
      color: inherit;
      text-decoration: none;
      box-shadow: 0 18px 50px rgba(69, 52, 31, .08);
    }}
    .card span {{
      display: block;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -.03em;
    }}
    .card strong {{
      display: block;
      margin: 10px 0;
      color: var(--sage);
      font-size: 12px;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
    .card p {{
      margin: 0;
      line-height: 1.55;
      color: #60594d;
    }}
    section {{
      margin-top: 30px;
      padding: 20px;
      border-radius: 24px;
      background: rgba(255,255,255,.52);
      border: 1px solid var(--line);
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 24px;
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
      line-height: 1.8;
    }}
    li span {{
      font-weight: 700;
    }}
    li strong {{
      color: var(--sage);
      margin-left: 10px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
    }}
    code {{
      display: block;
      margin: 8px 0 14px;
      padding: 12px 14px;
      border-radius: 14px;
      background: #17231f;
      color: #fff8ec;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      line-height: 1.55;
    }}
    small {{
      display: block;
      margin: 4px 0 0;
      color: #5f594d;
    }}
    @media (max-width: 820px) {{
      .actions, .grid, .status-band {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="kicker">No upload · No CMS write · No publish</div>
    <h1>Content Studio Owner Review Dashboard</h1>
    <p class="meta">目标页面：{html.escape(str(summary.get("target_url") or "not_found"))}<br />配对页面：{html.escape(str(summary.get("paired_url") or "not_found"))}<br />状态：<strong>{html.escape(str(summary.get("status", "")))}</strong></p>
  </header>
  <main>
    <div class="actions">
      <div class="action"><strong>1. 审核内容</strong>先看审批行动包和 publish-prep，确认页面、双语范围和执行门禁。</div>
      <div class="action"><strong>2. 审核图片</strong>打开效果图 gallery，确认图片只能作为设计方案/效果图方案使用。</div>
      <div class="action"><strong>3. 填写 URL</strong>上传/选择图片后，用表单下载 uploaded-url-map.filled.json，再安全导入。</div>
    </div>
    <div class="status-band">
      <div class="metric"><span>Media status</span><strong>{html.escape(str(media_summary.get("status", "missing")))}</strong></div>
      <div class="metric"><span>URLs ready</span><strong>{html.escape(str(media_counts.get("ready", 0)))}/{html.escape(str(media_counts.get("total", 0)))}</strong></div>
      <div class="metric"><span>Missing URLs</span><strong>{html.escape(str(media_counts.get("missing_public_url", 0)))}</strong></div>
      <div class="metric"><span>Owner decision</span><strong>{html.escape(str(decision_summary.get("status", "missing")))}</strong></div>
    </div>
    <div class="grid">
      {"".join(card_html)}
    </div>
    <section>
      <h2>媒体下一步</h2>
      <ul>{media_next_html}</ul>
    </section>
    <section>
      <h2>可复制命令</h2>
      <ul>{command_html}</ul>
    </section>
    <section>
      <h2>Package Steps</h2>
      <ul>{steps_html}</ul>
    </section>
    <section>
      <h2>Blockers</h2>
      <ul>{blocker_html}</ul>
    </section>
    <section>
      <h2>安全边界</h2>
      <ul>
        <li>本 dashboard 只是本地审核入口。</li>
        <li>没有上传媒体、没有调用 CMS/admin helper、没有写源码、没有发布、没有部署。</li>
        <li>生成图片只能描述为设计方案、效果图方案、design/rendering concept，不能写成真实完工案例或客户照片。</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Owner Review Package",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        "- 执行模式: full owner-review package / no live write",
        f"- 状态: {summary['status']}",
        f"- 目标页面: `{summary.get('target_url') or 'not_found'}`",
        f"- 配对页面: `{summary.get('paired_url') or 'not_found'}`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天把最新 Content Studio 页面打包成完整业主审核包：候选页、发布准备、审批行动清单、媒体审核 gallery、可填写 URL 草稿和媒体状态报告一次生成，仍不发布。",
        "",
        "## Package Steps",
        "",
    ]
    for step in summary.get("steps", []):
        lines.append(f"- {step['step']}: `{step['status']}` / artifacts `{step['artifact_count']}`")
    lines.extend(["", "## Key Artifacts", ""])
    for key, value in (summary.get("key_artifacts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    media_summary = safe_dict(summary.get("media_status_summary"))
    media_counts = safe_dict(media_summary.get("counts"))
    decision_summary = safe_dict(summary.get("owner_decision_status_summary"))
    lines.extend(
        [
            "",
            "## Media Status Summary",
            "",
            f"- Status: `{media_summary.get('status', 'missing')}`",
            f"- URLs ready: `{media_counts.get('ready', 0)}/{media_counts.get('total', 0)}`",
            f"- Missing public URLs: `{media_counts.get('missing_public_url', 0)}`",
            f"- Needs owner confirmation: `{media_counts.get('needs_owner_confirmation', 0)}`",
            "",
            "## Owner Decision Status",
            "",
            f"- Status: `{decision_summary.get('status', 'missing')}`",
            f"- Allowed scope: `{decision_summary.get('allowed_execution_scope', 'missing')}`",
            f"- Missing decisions: `{', '.join(str(item) for item in safe_list(decision_summary.get('missing_decisions'))) or 'None'}`",
        ]
    )
    media_next_actions = safe_list(media_summary.get("next_actions"))
    if media_next_actions:
        lines.append("- Next actions:")
        lines.extend(f"- {item}" for item in media_next_actions)
    recommended_commands = safe_list(summary.get("recommended_commands"))
    if recommended_commands:
        lines.extend(["", "## Recommended Commands", ""])
        for item in recommended_commands:
            if isinstance(item, dict):
                lines.append(f"- {item.get('label', '')}: `{item.get('command', '')}`")
    lines.extend(["", "## 下一步", ""])
    lines.extend(
        [
            "- 业主先打开 `owner_review_dashboard`，再看 `content-studio-approval-packet.md`。",
            "- 业主或上传器打开媒体审核 gallery，确认效果图可用。",
            "- 媒体上传/选择完成后，用图片 URL 表单下载 `uploaded-url-map.filled.json`，再运行 `content-studio-uploaded-url-map-import`。",
            "- 再运行 `content-studio-media-status` 复查 URL 是否完整，然后进入 `content-studio-media-ready-handoff`。",
            "- 只有业主明确批准具体候选、QA、媒体 URL 和执行范围后，才能进入后续 approved dry-run；真实发布仍需单独指令。",
            "",
            "## 安全边界",
            "",
            "- 未登录 CMS/admin。",
            "- 未调用 Supabase 或网站 admin helper。",
            "- 未修改网站源码或线上页面。",
            "- 未上传媒体、未发布、未部署。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_owner_review_package(
    root: Path,
    *,
    website_root: str = "",
    target_url: str = "",
    postrun_path: str = "",
    content_studio_run_path: str = "",
    public_base_url: str = "",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    all_artifacts: list[Path] = []
    steps: list[dict[str, Any]] = []

    candidate, candidate_artifacts = run_content_studio_publish_candidate(
        root,
        postrun_path=postrun_path,
        content_studio_run_path=content_studio_run_path,
        website_root=website_root,
        target_url=target_url,
    )
    all_artifacts.extend(candidate_artifacts)
    steps.append(step_summary("content_studio_publish_candidate", candidate, list(candidate_artifacts)))

    prep, prep_artifacts = run_content_studio_publish_prep(root, website_root=website_root)
    all_artifacts.extend(prep_artifacts)
    steps.append(step_summary("content_studio_publish_prep", prep, list(prep_artifacts)))

    approval, approval_artifacts = run_content_studio_approval_packet(root)
    all_artifacts.extend(approval_artifacts)
    steps.append(step_summary("content_studio_approval_packet", approval, list(approval_artifacts)))

    owner_decision_editor, owner_decision_editor_artifacts = run_content_studio_owner_decision_editor(root)
    all_artifacts.extend(owner_decision_editor_artifacts)
    steps.append(step_summary("content_studio_owner_decision_editor", owner_decision_editor, list(owner_decision_editor_artifacts)))

    media_review, media_review_artifacts = run_content_studio_media_review_package(root)
    all_artifacts.extend(media_review_artifacts)
    steps.append(step_summary("content_studio_media_review_package", media_review, list(media_review_artifacts)))

    media_template, media_artifacts = run_content_studio_media_url_template(root, public_base_url=public_base_url)
    all_artifacts.extend(media_artifacts)
    steps.append(step_summary("content_studio_media_url_template", media_template, list(media_artifacts)))

    uploaded_url_draft, uploaded_url_artifacts = run_content_studio_uploaded_url_map_draft(root)
    all_artifacts.extend(uploaded_url_artifacts)
    steps.append(step_summary("content_studio_uploaded_url_map_draft", uploaded_url_draft, list(uploaded_url_artifacts)))

    uploaded_url_editor, uploaded_url_editor_artifacts = run_content_studio_uploaded_url_map_editor(root)
    all_artifacts.extend(uploaded_url_editor_artifacts)
    steps.append(step_summary("content_studio_uploaded_url_map_editor", uploaded_url_editor, list(uploaded_url_editor_artifacts)))

    media_status, media_status_artifacts = run_content_studio_media_status(root)
    all_artifacts.extend(media_status_artifacts)
    steps.append(step_summary("content_studio_media_status", media_status, list(media_status_artifacts)))

    owner_decision_status, owner_decision_artifacts = run_content_studio_owner_decision_status(root, website_root=website_root)
    all_artifacts.extend(owner_decision_artifacts)
    steps.append(step_summary("content_studio_owner_decision_status", owner_decision_status, list(owner_decision_artifacts)))

    blockers = []
    for name, payload in (
        ("content_studio_publish_candidate", candidate),
        ("content_studio_publish_prep", prep),
        ("content_studio_approval_packet", approval),
        ("content_studio_owner_decision_editor", owner_decision_editor),
        ("content_studio_media_review_package", media_review),
        ("content_studio_media_url_template", media_template),
        ("content_studio_uploaded_url_map_draft", uploaded_url_draft),
        ("content_studio_uploaded_url_map_editor", uploaded_url_editor),
        ("content_studio_media_status", media_status),
        ("content_studio_owner_decision_status", owner_decision_status),
    ):
        status = str(payload.get("status", ""))
        if status.startswith("blocked"):
            blockers.append(f"{name}: {status}")
    target = str(candidate.get("target_url") or prep.get("target_url") or approval.get("target_url") or "")
    paired = str(candidate.get("paired_url") or prep.get("paired_url") or approval.get("paired_url") or "")
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "owner_review_package_ready" if not blockers else "owner_review_package_blocked",
        "target_url": target,
        "paired_url": paired,
        "steps": steps,
        "blockers": blockers,
        "media_status_summary": {
            "status": media_status.get("status", ""),
            "counts": media_status.get("counts", {}),
            "next_actions": media_status.get("next_actions", []),
            "blockers": media_status.get("blockers", []),
        },
        "owner_decision_status_summary": {
            "status": owner_decision_status.get("status", ""),
            "allowed_execution_scope": owner_decision_status.get("allowed_execution_scope", ""),
            "missing_decisions": owner_decision_status.get("missing_decisions", []),
            "blockers": owner_decision_status.get("blockers", []),
        },
        "recommended_commands": build_recommended_commands(website_root, target),
        "key_artifacts": {
            "approval_packet": str(root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-approval-packet.md"),
            "rich_editor": str(root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-rich-content-editor.html"),
            "editor_applied_payload": str(root / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json"),
            "editor_apply_report": str(root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-rich-editor-apply-report.md"),
            "owner_decision_editor": str(root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-content-studio-owner-decision-editor.html"),
            "owner_decision_template": str(root / "seo-workspace" / "data" / "content-studio-owner-decision.template.json"),
            "owner_decision_status": str(root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-owner-decision-status.md"),
            "owner_review_dashboard": str(root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-content-studio-owner-review-dashboard.html"),
            "publish_prep": str(root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-publish-prep.md"),
            "media_review_gallery": str(root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-content-studio-media-review-gallery.html"),
            "uploaded_url_map_editor": str(root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-content-studio-uploaded-url-map-editor.html"),
            "uploaded_url_template": str(root / "seo-workspace" / "data" / "uploaded-url-map.template.json"),
            "uploaded_url_map_draft": str(root / "seo-workspace" / "data" / "uploaded-url-map.json"),
            "media_status": str(root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-media-status.md"),
            "publish_candidate": str(root / "seo-workspace" / "data" / "content-studio-publish-candidate.json"),
        },
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    data_path = root / "seo-workspace" / "data" / "content-studio-owner-review-package.json"
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-owner-review-package.md"
    dashboard_path = root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-content-studio-owner-review-dashboard.html"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dashboard_path.write_text(render_dashboard(summary), encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    all_artifacts.extend([data_path, dashboard_path, report_path])
    return summary, all_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the full no-write owner review package for the latest Content Studio page.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--target-url", default="")
    parser.add_argument("--postrun-path", default="")
    parser.add_argument("--content-studio-run-path", default="")
    parser.add_argument("--public-base-url", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_owner_review_package(
        Path(args.root),
        website_root=args.website_root,
        target_url=args.target_url,
        postrun_path=args.postrun_path,
        content_studio_run_path=args.content_studio_run_path,
        public_base_url=args.public_base_url,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] == "owner_review_package_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
