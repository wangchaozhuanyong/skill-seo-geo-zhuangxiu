#!/usr/bin/env python3
"""Run a target-page content studio package without live execution."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

try:  # pragma: no cover - package import path differs between CLI and tests
    from .daily_automation import DailyAutomationResult, run_daily_automation
except ImportError:  # pragma: no cover
    from daily_automation import DailyAutomationResult, run_daily_automation


CONTENT_STUDIO_JSON_NAME = "content-studio-run.json"
CONTENT_STUDIO_PIPELINES = {"brief", "rich-content", "publish-prep"}
DEFAULT_RESEARCH_SEARCH_PROVIDER = "hybrid-rss"
DEFAULT_RESEARCH_SEARCH_FEEDS_CONFIG = "seo-workspace/config/research-search-feeds.example.yml"


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def step_dicts(result: DailyAutomationResult) -> list[dict[str, object]]:
    return [step.as_dict() for step in result.steps]


def build_summary(
    result: DailyAutomationResult,
    *,
    target_url: str,
    website_root: str,
    research_fetch_remote: bool,
    research_search_provider: str,
    research_search_feeds_config: str,
) -> dict[str, object]:
    steps = step_dicts(result)
    research_artifacts = [
        artifact
        for step in steps
        if str(step.get("name", "")).startswith("research_")
        for artifact in step.get("artifacts", [])
    ]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": result.status,
        "pipeline": result.pipeline,
        "requested_target_url": target_url,
        "selected_task": result.selected_task,
        "website_root": website_root,
        "steps": steps,
        "step_count": len(steps),
        "content_outputs": [artifact for step in steps for artifact in step.get("artifacts", [])],
        "research_fetch_remote": research_fetch_remote,
        "research_search_provider": research_search_provider,
        "research_search_feeds_config": research_search_feeds_config,
        "research_artifacts": research_artifacts,
        "handoff_blockers": result.handoff_blockers,
        "automation_blockers": result.blockers,
        "warnings": result.warnings,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
        "execution_status": "waiting_owner_review_and_explicit_execution_instruction",
    }


def render_report(summary: dict[str, object]) -> str:
    task = summary.get("selected_task") if isinstance(summary.get("selected_task"), dict) else {}
    steps = summary.get("steps") if isinstance(summary.get("steps"), list) else []
    blockers = summary.get("handoff_blockers") if isinstance(summary.get("handoff_blockers"), list) else []
    automation_blockers = summary.get("automation_blockers") if isinstance(summary.get("automation_blockers"), list) else []
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    outputs = summary.get("content_outputs") if isinstance(summary.get("content_outputs"), list) else []

    lines = [
        "# Content Studio Run",
        "",
        f"- 生成时间: {summary.get('generated_at')}",
        f"- Pipeline: `{summary.get('pipeline')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Requested target URL: `{summary.get('requested_target_url')}`",
        f"- Selected target URL: `{task.get('target_url', '')}`",
        f"- Keyword: {task.get('keyword', '')}",
        f"- Research remote fetch: `{summary.get('research_fetch_remote')}`",
        f"- Research search provider: `{summary.get('research_search_provider')}`",
        f"- Research feeds config: `{summary.get('research_search_feeds_config')}`",
        "- 执行状态: draft/prep-only；未登录 CMS、未上传媒体、未写源码或数据库、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "本次使用 Content Studio 针对一个目标页面生成可审核的 SEO/GEO 图文内容生产包，而不是随机写文章。它把最新资料候选、富文本内容、图文编辑、概念效果图和发布准备门禁收进一个入口，方便后续固定化自动化。",
        "",
        "## 内容能力覆盖",
        "",
        "- 最新资料: 默认通过 `hybrid-rss` 同时生成 Google News RSS 与可信 RSS/Atom 候选，可信来源需经 `research-intake` 或 `latest-research` 进入 source log。",
        "- 富文本图文: 通过 `rich-blocks`、`rich-editor`、`rich-editor-apply` 生成可拖拽、可新增文本/图片/CTA 的本地审核编辑器与 CMS payload 草稿。",
        "- 装修效果图: 通过 `media-assets`、`concept-assets`、`media-upload-plan` 准备清晰标注的 design/rendering concept，不作为真实完工案例证明。",
        "- 服务页模式: 如果目标命中 `service-content-patterns.json`，会额外生成 service-pattern owner-review 内容包。",
        "- 发布准备: `publish-prep` pipeline 只生成授权、adapter、readiness、bundle、implementation、operator 等本地门禁产物，不执行发布。",
        "",
        "## Steps",
        "",
    ]
    for step in steps:
        if not isinstance(step, dict):
            continue
        lines.append(f"- `{step.get('name')}`: {step.get('status')}")
    lines.extend(["", "## 主要产物", ""])
    if outputs:
        for output in outputs:
            lines.append(f"- `{output}`")
    else:
        lines.append("- None")
    lines.extend(["", "## 最新来源候选产物", ""])
    research_artifacts = summary.get("research_artifacts") if isinstance(summary.get("research_artifacts"), list) else []
    if research_artifacts:
        for output in research_artifacts:
            lines.append(f"- `{output}`")
    else:
        lines.append("- None")
    lines.extend(["", "## 发布前阻断项", ""])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None")
    lines.extend(["", "## 自动化阻断项", ""])
    if automation_blockers:
        lines.extend(f"- {item}" for item in automation_blockers)
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## 业主审核备注",
            "",
            "- 本报告只表示内容生产包已生成或发布准备已检查，不代表允许发布。",
            "- 业主需要先审核具体页面文案、图文结构、图片概念标签、CTA 和事实性声明。",
            "- 真实发布必须另行明确指定已批准草稿/计划，并要求 Codex 执行。",
            "",
            "## QA checklist",
            "",
            "- [ ] 中文和英文页面成对审核。",
            "- [ ] 没有伪造案例、评价、价格、工期、保修、资质、奖项或排名承诺。",
            "- [ ] 生成图片均标注为设计方案、效果图方案或 rendering concept。",
            "- [ ] 外部资料只作为通用参考，不变成未经支持的 FLASH CAST 业务 claim。",
            "- [ ] 发布前完成 owner approval、explicit execution、QA、媒体 URL、备份、changelog、rollback gates。",
            "",
            "## 执行状态：等待业主审核和明确执行指令",
        ]
    )
    return "\n".join(lines) + "\n"


def write_artifacts(root: Path, summary: dict[str, object]) -> tuple[Path, Path]:
    data_path = root / "seo-workspace" / "data" / CONTENT_STUDIO_JSON_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-content-studio-run.md"
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return data_path, report_path


def run_content_studio(
    root: Path,
    *,
    target_url: str = "",
    pipeline: str = "rich-content",
    topic: str = "",
    website_root: str = "",
    research_fetch_remote: bool = True,
    skip_research_discovery: bool = False,
    research_config_path: str = "",
    research_timeout: int = 10,
    research_search_provider: str = DEFAULT_RESEARCH_SEARCH_PROVIDER,
    research_search_feeds_config: str = DEFAULT_RESEARCH_SEARCH_FEEDS_CONFIG,
    research_per_seed_limit: int = 5,
    research_limit: int = 20,
    write_research_example: bool = True,
    auto_accept_research_sources: bool = True,
    research_intake_min_score: int = 60,
    research_intake_limit: int = 2,
    authorization_profile_path: str = "",
) -> tuple[dict[str, object], tuple[Path, Path]]:
    if pipeline not in CONTENT_STUDIO_PIPELINES:
        raise ValueError(f"Unsupported content-studio pipeline: {pipeline}")
    root = root.resolve()
    result, _ = run_daily_automation(
        root,
        pipeline=pipeline,
        target_url=target_url,
        topic=topic,
        website_root=website_root,
        discover_research_sources=not skip_research_discovery,
        research_config_path=research_config_path,
        research_fetch_remote=research_fetch_remote,
        research_search_provider=research_search_provider,
        research_search_feeds_config=research_search_feeds_config,
        research_timeout=research_timeout,
        research_per_seed_limit=research_per_seed_limit,
        research_limit=research_limit,
        research_write_example=write_research_example,
        auto_accept_research_sources=auto_accept_research_sources,
        research_intake_min_score=research_intake_min_score,
        research_intake_limit=research_intake_limit,
        authorization_profile_path=authorization_profile_path,
    )
    summary = build_summary(
        result,
        target_url=target_url,
        website_root=website_root,
        research_fetch_remote=research_fetch_remote,
        research_search_provider=research_search_provider,
        research_search_feeds_config=research_search_feeds_config,
    )
    artifacts = write_artifacts(root, summary)
    return summary, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a draft-only target-page content studio package.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--target-url", default="", help="Target URL. If omitted, daily content selection is used.")
    parser.add_argument("--pipeline", default="rich-content", choices=sorted(CONTENT_STUDIO_PIPELINES))
    parser.add_argument("--topic", default="", help="Optional topic override for rich-content generation.")
    parser.add_argument("--website-root", default="", help="Optional website source root for publish-prep evidence checks.")
    parser.add_argument("--skip-research-discovery", action="store_true")
    parser.add_argument("--research-config-path", default="")
    parser.add_argument("--no-fetch-research-remote", action="store_true")
    parser.add_argument("--research-search-provider", default=DEFAULT_RESEARCH_SEARCH_PROVIDER)
    parser.add_argument("--research-search-feeds-config", default=DEFAULT_RESEARCH_SEARCH_FEEDS_CONFIG)
    parser.add_argument("--research-timeout", type=int, default=10)
    parser.add_argument("--research-per-seed-limit", type=int, default=5)
    parser.add_argument("--research-limit", type=int, default=20)
    parser.add_argument("--no-write-research-example", action="store_true")
    parser.add_argument("--no-auto-accept-research-sources", action="store_true")
    parser.add_argument("--research-intake-min-score", type=int, default=60)
    parser.add_argument("--research-intake-limit", type=int, default=2)
    parser.add_argument("--authorization-profile-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_content_studio(
        Path(args.root),
        target_url=args.target_url,
        pipeline=args.pipeline,
        topic=args.topic,
        website_root=args.website_root,
        skip_research_discovery=args.skip_research_discovery,
        research_config_path=args.research_config_path,
        research_fetch_remote=not args.no_fetch_research_remote,
        research_search_provider=args.research_search_provider,
        research_search_feeds_config=args.research_search_feeds_config,
        research_timeout=args.research_timeout,
        research_per_seed_limit=args.research_per_seed_limit,
        research_limit=args.research_limit,
        write_research_example=not args.no_write_research_example,
        auto_accept_research_sources=not args.no_auto_accept_research_sources,
        research_intake_min_score=args.research_intake_min_score,
        research_intake_limit=args.research_intake_limit,
        authorization_profile_path=args.authorization_profile_path,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if not summary.get("automation_blockers") else 1


if __name__ == "__main__":
    raise SystemExit(main())
