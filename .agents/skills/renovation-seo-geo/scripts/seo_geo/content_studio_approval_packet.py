#!/usr/bin/env python3
"""Create an owner approval packet from Content Studio publish-prep evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


DEFAULT_PREP = "seo-workspace/data/content-studio-publish-prep.json"
DEFAULT_CANDIDATE = "seo-workspace/data/content-studio-publish-candidate.json"
DEFAULT_MEDIA_PLAN = "seo-workspace/data/media-upload-plan.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def contains_any(texts: list[str], needles: tuple[str, ...]) -> bool:
    haystack = "\n".join(texts).lower()
    return any(needle.lower() in haystack for needle in needles)


def media_items(media_plan: dict[str, Any]) -> list[dict[str, str]]:
    queue = media_plan.get("queue")
    if not isinstance(queue, list):
        return []
    items: list[dict[str, str]] = []
    for row in queue:
        if not isinstance(row, dict):
            continue
        items.append(
            {
                "queue_id": str(row.get("queue_id", "")),
                "placeholder_filename": str(row.get("placeholder_filename", "")),
                "expected_object_path": str(row.get("expected_object_path") or row.get("object_path") or ""),
                "asset_kind": str(row.get("asset_kind", "")),
                "claim_boundary": str(row.get("claim_boundary", "")),
            }
        )
    return items


def build_action_items(prep: dict[str, Any], media_plan: dict[str, Any]) -> list[dict[str, Any]]:
    blockers = list(prep.get("blocker_summary") or prep.get("blockers") or [])
    actions: list[dict[str, Any]] = []
    if contains_any(blockers, ("owner-approved", "Owner approval")):
        actions.append(
            {
                "category": "owner_approval",
                "title_zh": "批准这个具体页面候选",
                "status": "needs_owner_decision",
                "details_zh": "请确认是否批准当前 kitchen 双语页面内容包进入后续执行准备；批准不等于真实发布。",
            }
        )
    if contains_any(blockers, ("explicit-execution", "explicit execution")):
        actions.append(
            {
                "category": "execution_instruction",
                "title_zh": "给出明确执行范围",
                "status": "needs_owner_decision",
                "details_zh": "请明确下一步只允许 dry-run / publish-prep，还是允许后续 approved execution。真实写入仍需单独指令。",
            }
        )
    if contains_any(blockers, ("qa-passed", "QA passed", "Pre-publish QA")):
        actions.append(
            {
                "category": "qa",
                "title_zh": "完成并确认发布前 QA",
                "status": "needs_qa_confirmation",
                "details_zh": "需要确认双语内容、链接、概念图标签、CTA、schema、移动端阅读和媒体占位。",
            }
        )
    if contains_any(blockers, ("media-url-map", "media-ready", "Media placeholders", "NEEDS_MEDIA_UPLOAD")):
        actions.append(
            {
                "category": "media",
                "title_zh": "处理概念效果图上传和 URL map",
                "status": "needs_media_urls",
                "details_zh": "当前图片是设计/效果图方案，可上传为概念图；必须保留 concept/rendering 标签，并提供公开 URL map 后才能生成 media-ready payload。",
                "media_items": media_items(media_plan),
            }
        )
    if contains_any(blockers, ("Storage readiness", "storage-ready")):
        actions.append(
            {
                "category": "storage",
                "title_zh": "确认媒体存储路径可用",
                "status": "needs_storage_confirmation",
                "details_zh": "需要确认 bucket、storage prefix、公开访问 URL 和上传权限。",
            }
        )
    if contains_any(blockers, ("execution receipt", "execution result", "receipt")):
        actions.append(
            {
                "category": "receipt",
                "title_zh": "真实执行后必须提供回执",
                "status": "future_gate",
                "details_zh": "只有真实写入后提供 CMS 记录、SEO 生成、QA、回滚和线上验证证据，才能验证发布完成。",
            }
        )
    return actions


def recommended_commands(target_url: str, paired_url: str) -> list[dict[str, str]]:
    base = "python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py"
    return [
        {
            "step": "refresh_candidate",
            "command": f"{base} content-studio-publish-candidate --target-url {target_url} --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main",
            "note_zh": "刷新候选和发布队列，不执行发布。",
        },
        {
            "step": "refresh_publish_prep",
            "command": f"{base} content-studio-publish-prep --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main",
            "note_zh": "重新生成本地发布准备证据。",
        },
        {
            "step": "create_uploaded_url_template",
            "command": f"{base} content-studio-media-url-template",
            "note_zh": "生成可填写的 uploaded URL map 模板；不上传媒体。",
        },
        {
            "step": "media_after_urls",
            "command": f"{base} media-upload-executor --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --uploaded-confirmed",
            "note_zh": "仅在媒体已上传并提供公开 URL map 后运行；命令本身仍不上传。",
        },
        {
            "step": "approved_dry_run_only",
            "command": f"{base} content-studio-publish-prep --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main --owner-approved --explicit-execution --qa-passed --media-ready --latest-research-verified",
            "note_zh": "业主批准后重新生成更接近 ready 的 dry-run handoff；仍不写 CMS。",
        },
        {
            "step": "receipt_after_real_execution",
            "command": f"{base} publish-execution-receipt",
            "note_zh": "未来真实执行完成后验证回执；不执行写入。",
        },
    ]


def owner_decision_template(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "owner_decision_template_waiting_owner_input",
        "target_url": packet.get("target_url", ""),
        "paired_url": packet.get("paired_url", ""),
        "instructions_zh": [
            "这是业主审核决定模板，不是执行命令。",
            "只有把 explicit_execution_requested 改为 true，并另外用自然语言明确要求 Codex 执行，才会进入后续执行门禁。",
            "真实发布仍需要后续 QA、媒体 URL、backup、changelog、rollback 和 live confirmation。",
        ],
        "decision": {
            "content_approved": False,
            "media_urls_confirmed": False,
            "qa_approved": False,
            "latest_research_verified": False,
            "explicit_execution_requested": False,
            "allowed_execution_scope": "owner_review_only",
            "allowed_execution_scope_options": [
                "owner_review_only",
                "media_ready_handoff_only",
                "approved_dry_run_only",
                "operator_ready_handoff_only",
                "live_publish_requires_separate_confirmation",
            ],
            "owner_notes": "",
        },
        "required_before_execution": [
            "content_approved=true",
            "qa_approved=true",
            "explicit_execution_requested=true",
            "media_urls_confirmed=true when image placeholders exist",
            "separate owner message requesting exact execution",
        ],
        "action_items_snapshot": packet.get("action_items", []),
        "approval_is_not_execution": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }


def merge_owner_decision_template(packet: dict[str, Any], existing_template: dict[str, Any]) -> dict[str, Any]:
    template = owner_decision_template(packet)
    existing_decision = existing_template.get("decision") if isinstance(existing_template.get("decision"), dict) else {}
    same_page = (
        bool(existing_decision)
        and str(existing_template.get("target_url", "")) == str(template.get("target_url", ""))
        and str(existing_template.get("paired_url", "")) == str(template.get("paired_url", ""))
    )
    if same_page:
        default_options = template["decision"]["allowed_execution_scope_options"]
        merged_decision = dict(template["decision"])
        for key in (
            "content_approved",
            "media_urls_confirmed",
            "qa_approved",
            "latest_research_verified",
            "explicit_execution_requested",
            "allowed_execution_scope",
            "owner_notes",
        ):
            if key in existing_decision:
                merged_decision[key] = existing_decision[key]
        merged_decision["allowed_execution_scope_options"] = default_options
        template["decision"] = merged_decision
        template["decision_preserved_from_previous_template"] = True
        template["previous_decision_generated_at"] = existing_template.get("generated_at", "")
    else:
        template["decision_preserved_from_previous_template"] = False
    return template


def render_report(packet: dict[str, Any]) -> str:
    lines = [
        "# Content Studio Owner Approval Packet",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        "- 执行模式: approval packet / owner review / no publish",
        f"- 状态: {packet['status']}",
        f"- 目标页面: `{packet.get('target_url') or 'not_found'}`",
        f"- 配对页面: `{packet.get('paired_url') or 'not_found'}`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天把发布准备包转成业主审批行动清单：只整理需要批准、确认、上传 URL 或未来验证的事项，不执行任何写入。",
        "",
        "## 业主需要决定",
        "",
    ]
    actions = packet.get("action_items") or []
    if actions:
        for action in actions:
            lines.append(f"- {action['title_zh']}: `{action['status']}`。{action['details_zh']}")
    else:
        lines.append("- None")
    media = next((action for action in actions if action.get("category") == "media"), {})
    media_rows = media.get("media_items") or []
    lines.extend(["", "## 媒体 URL 清单", ""])
    if media_rows:
        for row in media_rows:
            lines.append(f"- `{row.get('placeholder_filename')}` -> `{row.get('expected_object_path')}`；边界: {row.get('claim_boundary') or 'concept/rendering only'}")
    else:
        lines.append("- 当前审批包未检测到待上传媒体。")
    lines.extend(["", "## 推荐下一步命令", ""])
    for command in packet.get("recommended_commands") or []:
        lines.append(f"- {command['step']}: `{command['command']}`")
        lines.append(f"  说明: {command['note_zh']}")
    if packet.get("owner_decision_template_path"):
        lines.extend(
            [
                "",
                "## 业主决定模板",
                "",
                f"- `{packet['owner_decision_template_path']}`",
                "- 填写这个模板仍不等于执行；后续必须由业主另外明确要求执行具体范围。",
            ]
        )
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 未登录 CMS/admin。",
            "- 未调用网站 admin helper 或 Supabase。",
            "- 未修改源码、未上传媒体、未发布、未部署。",
            "- 概念图/效果图只能作为 design concept / rendering concept，不能写成真实完工照片或客户案例证明。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_approval_packet(
    root: Path,
    *,
    prep_path: str = "",
    candidate_path: str = "",
    media_plan_path: str = "",
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    prep_file = resolve_path(root, prep_path or DEFAULT_PREP)
    candidate_file = resolve_path(root, candidate_path or DEFAULT_CANDIDATE)
    media_file = resolve_path(root, media_plan_path or DEFAULT_MEDIA_PLAN)
    prep = read_json(prep_file)
    candidate = read_json(candidate_file)
    media_plan = read_json(media_file)
    target_url = str(prep.get("target_url") or candidate.get("target_url") or "")
    paired_url = str(prep.get("paired_url") or candidate.get("paired_url") or "")
    blockers: list[str] = []
    if not prep:
        blockers.append("Missing content-studio-publish-prep.json. Run content-studio-publish-prep first.")
    if not candidate:
        blockers.append("Missing content-studio-publish-candidate.json. Run content-studio-publish-candidate first.")
    action_items = build_action_items(prep, media_plan)
    decision_path = root / "seo-workspace" / "data" / "content-studio-owner-decision.template.json"
    packet = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "approval_packet_waiting_owner_review" if not blockers else "approval_packet_blocked_missing_inputs",
        "target_url": target_url,
        "paired_url": paired_url,
        "prep_path": str(prep_file),
        "candidate_path": str(candidate_file),
        "media_plan_path": str(media_file),
        "blockers": blockers,
        "action_items": action_items,
        "recommended_commands": recommended_commands(target_url or "<target-url>", paired_url or "<paired-url>"),
        "owner_decision_template_path": str(decision_path),
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    data_path = root / "seo-workspace" / "data" / "content-studio-approval-packet.json"
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-approval-packet.md"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    decision_template = merge_owner_decision_template(packet, read_json(decision_path))
    data_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    decision_path.write_text(json.dumps(decision_template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_report(packet), encoding="utf-8")
    return packet, [data_path, decision_path, report_path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an owner approval packet from Content Studio publish-prep evidence.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--prep-path", default="")
    parser.add_argument("--candidate-path", default="")
    parser.add_argument("--media-plan-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet, artifacts = run_content_studio_approval_packet(
        Path(args.root),
        prep_path=args.prep_path,
        candidate_path=args.candidate_path,
        media_plan_path=args.media_plan_path,
    )
    for output in artifacts:
        print(output)
    return 0 if packet["status"] == "approval_packet_waiting_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
