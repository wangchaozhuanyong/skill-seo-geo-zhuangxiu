#!/usr/bin/env python3
"""Run safe publish-prep handoff steps for a Content Studio publish candidate."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from publish_approved_executor import run_publish_approved_executor
from publish_bundle import run_publish_bundle
from publish_execution_receipt import run_publish_execution_receipt
from publish_executor import run_publish_executor
from publish_implementation_package import run_publish_implementation_package
from publish_operator_package import run_publish_operator_package
from publish_plan import run_publish_plan
from publish_readiness import run_publish_readiness
from website_publish_adapter import run_website_publish_adapter


DEFAULT_CANDIDATE = "seo-workspace/data/content-studio-publish-candidate.json"
SUMMARY_NAME = "content-studio-publish-prep.json"
REPORT_NAME = "content-studio-publish-prep.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def result_summary(name: str, result: Any, artifacts: list[Path] | tuple[Path, ...]) -> dict[str, Any]:
    return {
        "step": name,
        "status": str(getattr(result, "status", "")),
        "ok": bool(getattr(result, "ok", False)),
        "blockers": list(getattr(result, "blockers", []) or []),
        "warnings": list(getattr(result, "warnings", []) or []),
        "artifacts": [str(path) for path in artifacts],
    }


def normalize_blocker(blocker: str) -> str:
    text = blocker.strip()
    known_prefixes = (
        "website_publish_adapter",
        "publish_plan",
        "publish_executor",
        "publish_readiness",
        "publish_bundle",
        "publish_approved_executor",
        "publish_implementation_package",
        "publish_operator_package",
        "publish_execution_receipt",
    )
    for prefix in known_prefixes:
        marker = f"{prefix}: "
        if text.startswith(marker):
            text = text[len(marker) :].strip()
            break
    while " blocker: " in text:
        text = text.split(" blocker: ", 1)[1].strip()
    return text


def summarize_blockers(blockers: list[str], limit: int = 20) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    unique_count = 0
    for blocker in blockers:
        normalized = normalize_blocker(blocker)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_count += 1
        if len(items) < limit:
            items.append(normalized)
    remaining = unique_count - len(items)
    if remaining > 0:
        items.append(f"... plus {remaining} more unique blocker categories in JSON evidence.")
    return items


def render_report(summary: dict[str, Any]) -> str:
    steps = summary.get("steps") or []
    blockers = summary.get("blockers") or []
    key_blockers = summary.get("blocker_summary") or summarize_blockers(list(blockers))
    lines = [
        "# Content Studio Publish Prep",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        "- 执行模式: publish-prep / local handoff only / no live write",
        f"- 状态: {summary['status']}",
        f"- 目标页面: `{summary.get('target_url') or 'not_found'}`",
        f"- 配对页面: `{summary.get('paired_url') or 'not_found'}`",
        f"- 候选文件: `{summary.get('candidate_path')}`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天把 Content Studio 候选页面推进到完整发布准备包：生成执行计划、CMS dry-run 请求、readiness、bundle、approved executor 模拟、implementation runbook、operator 命令清单和 execution receipt 验证模板。所有步骤只写本地证据，不发布。",
        "",
        "## Step Status",
        "",
    ]
    for step in steps:
        lines.append(f"- {step['step']}: `{step['status']}` / blockers `{len(step.get('blockers') or [])}` / artifacts `{len(step.get('artifacts') or [])}`")
    lines.extend(["", "## 阻断项汇总", ""])
    if blockers:
        lines.append(f"- 完整阻断证据数量: `{len(blockers)}`，详见 `content-studio-publish-prep.json`。")
    lines.extend(f"- {item}" for item in key_blockers) if key_blockers else lines.append("- None")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 未登录 CMS/admin。",
            "- 未调用 Supabase 或网站 admin helper。",
            "- 未修改网站源码或线上页面。",
            "- 未上传媒体、未发布、未部署。",
            "- 如果业主之后批准执行，仍必须逐项确认 owner approval、explicit execution、QA、media readiness、backup、changelog、rollback 和 live confirmation。",
            "",
            "## 业主审核备注",
            "",
            "- 请先审核 Content Studio 内容包、概念效果图标签、双语页面范围和发布路径。",
            "- 如果批准继续，下一步应明确指定目标候选，并说明是否允许进入 approved execution dry-run；真实写入仍需单独执行指令。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_artifacts(root: Path, summary: dict[str, Any]) -> tuple[Path, Path]:
    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_report(summary), encoding="utf-8")
    return data_path, report_path


def run_content_studio_publish_prep(
    root: Path,
    *,
    candidate_path: str = "",
    website_root: str = "",
    mode: str = "dry-run",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    media_ready: bool = False,
    latest_research_verified: bool = False,
    allow_blocked_plan: bool = False,
) -> tuple[dict[str, Any], list[Path]]:
    root = root.resolve()
    candidate_file = resolve_path(root, candidate_path or DEFAULT_CANDIDATE)
    candidate = read_json(candidate_file)
    candidate_row = candidate.get("candidate_row") if isinstance(candidate.get("candidate_row"), dict) else {}
    target_url = str(candidate.get("target_url") or candidate_row.get("target_url") or "")
    paired_url = str(candidate.get("paired_url") or candidate_row.get("paired_url") or "")
    draft_path = str(candidate.get("matched_draft_path") or candidate_row.get("draft_path") or "")

    initial_blockers: list[str] = []
    if not candidate:
        initial_blockers.append("Missing content-studio-publish-candidate.json. Run content-studio-publish-candidate first.")
    if candidate and candidate.get("status") != "content_studio_publish_candidate_waiting_owner_review":
        initial_blockers.append(f"Candidate is not ready for owner review: {candidate.get('status')}")
    if not target_url:
        initial_blockers.append("Missing target URL in Content Studio publish candidate.")

    steps: list[dict[str, Any]] = []
    artifacts: list[Path] = []

    adapter_result, adapter_artifacts = run_website_publish_adapter(root, website_root=website_root)
    steps.append(result_summary("website_publish_adapter", adapter_result, list(adapter_artifacts)))
    artifacts.extend(adapter_artifacts)

    plan_result, plan_artifacts = run_publish_plan(
        root,
        target_url=target_url,
        draft_path=draft_path,
        mode="pr",
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        latest_research_verified=latest_research_verified,
    )
    steps.append(result_summary("publish_plan", plan_result, list(plan_artifacts)))
    artifacts.extend(plan_artifacts)

    executor_result, executor_artifacts = run_publish_executor(
        root,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        media_ready=media_ready,
        allow_blocked_plan=allow_blocked_plan,
    )
    steps.append(result_summary("publish_executor", executor_result, list(executor_artifacts)))
    artifacts.extend(executor_artifacts)

    readiness_result, readiness_artifacts = run_publish_readiness(root)
    steps.append(result_summary("publish_readiness", readiness_result, list(readiness_artifacts)))
    artifacts.extend(readiness_artifacts)

    bundle_result, bundle_artifacts = run_publish_bundle(root)
    steps.append(result_summary("publish_bundle", bundle_result, list(bundle_artifacts)))
    artifacts.extend(bundle_artifacts)

    approved_result, approved_artifacts = run_publish_approved_executor(
        root,
        mode=mode,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        allowed_target_urls=[target_url, paired_url],
    )
    steps.append(result_summary("publish_approved_executor", approved_result, list(approved_artifacts)))
    artifacts.extend(approved_artifacts)

    implementation_result, implementation_artifacts = run_publish_implementation_package(root, website_root=website_root)
    steps.append(result_summary("publish_implementation_package", implementation_result, list(implementation_artifacts)))
    artifacts.extend(implementation_artifacts)

    operator_result, operator_artifacts = run_publish_operator_package(root)
    steps.append(result_summary("publish_operator_package", operator_result, list(operator_artifacts)))
    artifacts.extend(operator_artifacts)

    receipt_result, receipt_artifacts = run_publish_execution_receipt(root)
    steps.append(result_summary("publish_execution_receipt", receipt_result, list(receipt_artifacts)))
    artifacts.extend(receipt_artifacts)

    blockers = list(initial_blockers)
    for step in steps:
        blockers.extend(f"{step['step']}: {blocker}" for blocker in step.get("blockers", []))
    status = "publish_prep_ready_for_owner_review" if candidate and target_url else "publish_prep_blocked_missing_candidate"
    summary: dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "target_url": target_url,
        "paired_url": paired_url,
        "draft_path": draft_path,
        "candidate_path": str(candidate_file),
        "steps": steps,
        "blockers": blockers,
        "blocker_summary": summarize_blockers(blockers),
        "owner_approved": owner_approved,
        "explicit_execution": explicit_execution,
        "qa_passed": qa_passed,
        "media_ready": media_ready,
        "latest_research_verified": latest_research_verified,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    summary_path, report_path = write_artifacts(root, summary)
    artifacts.extend([summary_path, report_path])
    return summary, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe publish-prep handoff steps for a Content Studio candidate.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--candidate-path", default="")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--media-ready", action="store_true")
    parser.add_argument("--latest-research-verified", action="store_true")
    parser.add_argument("--allow-blocked-plan", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio_publish_prep(
        Path(args.root),
        candidate_path=args.candidate_path,
        website_root=args.website_root,
        mode=args.mode,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        media_ready=args.media_ready,
        latest_research_verified=args.latest_research_verified,
        allow_blocked_plan=args.allow_blocked_plan,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] == "publish_prep_ready_for_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
