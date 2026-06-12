#!/usr/bin/env python3
"""Run the safe daily SEO/GEO automation orchestrator."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

try:
    from .concept_assets import run_concept_assets
    from .content_brief import run_content_brief
    from .media_assets import run_media_assets
    from .media_upload_executor import run_media_upload_executor
    from .media_upload_plan import run_media_upload_plan
    from .hreflang import expected_pair_url
    from .opportunity_finder import OpportunityScore, run_opportunity_finder
    from .publish_approved_executor import run_publish_approved_executor
    from .publish_bundle import run_publish_bundle
    from .publish_executor import run_publish_executor
    from .publish_implementation_package import run_publish_implementation_package
    from .publish_operator_package import run_publish_operator_package
    from .publish_plan import run_publish_plan
    from .publish_queue import run_publish_queue
    from .publish_readiness import run_publish_readiness
    from .research_discovery import run_research_discovery
    from .research_intake import run_research_intake
    from .research_search import run_research_search
    from .rich_blocks import run_rich_blocks
    from .rich_content import write_rich_content_package
    from .rich_editor import run_rich_editor
    from .rich_editor_apply import run_rich_editor_apply
    from .scheduled_publish_authorization import run_scheduled_publish_authorization
    from .service_pattern_content_package import run_service_pattern_content_package
    from .website_publish_adapter import run_website_publish_adapter
except ImportError:  # pragma: no cover - direct script execution
    from concept_assets import run_concept_assets
    from content_brief import run_content_brief
    from media_assets import run_media_assets
    from media_upload_executor import run_media_upload_executor
    from media_upload_plan import run_media_upload_plan
    from hreflang import expected_pair_url
    from opportunity_finder import OpportunityScore, run_opportunity_finder
    from publish_approved_executor import run_publish_approved_executor
    from publish_bundle import run_publish_bundle
    from publish_executor import run_publish_executor
    from publish_implementation_package import run_publish_implementation_package
    from publish_operator_package import run_publish_operator_package
    from publish_plan import run_publish_plan
    from publish_queue import run_publish_queue
    from publish_readiness import run_publish_readiness
    from research_discovery import run_research_discovery
    from research_intake import run_research_intake
    from research_search import run_research_search
    from rich_blocks import run_rich_blocks
    from rich_content import write_rich_content_package
    from rich_editor import run_rich_editor
    from rich_editor_apply import run_rich_editor_apply
    from scheduled_publish_authorization import run_scheduled_publish_authorization
    from service_pattern_content_package import run_service_pattern_content_package
    from website_publish_adapter import run_website_publish_adapter


RUN_JSON_NAME = "daily-automation-run.json"
CONTENT_CALENDAR_JSON_NAME = "daily-content-calendar.json"
PIPELINES = {"brief", "rich-content", "publish-prep"}


@dataclass
class DailyAutomationStep:
    name: str
    status: str
    artifacts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "artifacts": self.artifacts,
            "notes": self.notes,
        }


@dataclass
class DailyAutomationResult:
    status: str
    pipeline: str
    selected_task: dict[str, object] = field(default_factory=dict)
    steps: list[DailyAutomationStep] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    handoff_blockers: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def score_to_task(score: OpportunityScore) -> dict[str, object]:
    return {
        "target_url": score.url,
        "keyword": score.keyword,
        "language": score.language,
        "page_type": score.page_type,
        "service": score.service,
        "location": score.location,
        "total_score": score.total_score,
        "task_type": score.task_type,
        "positive_events": [{"label": event.label, "points": event.points, "note": event.note} for event in score.positive_events],
        "penalty_events": [{"label": event.label, "points": event.points, "note": event.note} for event in score.penalty_events],
    }


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")


def url_matches(candidate_url: str, target_url: str) -> bool:
    candidate = normalize_url(candidate_url)
    target = normalize_url(target_url)
    if not candidate or not target:
        return False
    return candidate == target or normalize_url(expected_pair_url(candidate)) == target


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def content_calendar_row(root: Path) -> dict[str, str]:
    payload = read_json(root / "seo-workspace" / "data" / CONTENT_CALENDAR_JSON_NAME)
    if payload.get("status") != "content_calendar_ready_for_owner_review":
        return {}
    rows = payload.get("calendar", [])
    if not isinstance(rows, list):
        return {}
    today = dt.date.today()
    future_rows: list[tuple[dt.date, dict[str, str]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        target_url = str(row.get("target_url") or "").strip()
        date_value = str(row.get("date") or "").strip()
        if not target_url or not date_value:
            continue
        try:
            row_date = dt.date.fromisoformat(date_value)
        except ValueError:
            continue
        typed_row = {str(key): str(value or "") for key, value in row.items()}
        if row_date == today:
            return typed_row
        if row_date > today:
            future_rows.append((row_date, typed_row))
    if future_rows:
        return sorted(future_rows, key=lambda item: item[0])[0][1]
    return {}


def select_score(scores: list[OpportunityScore], target_url: str = "") -> OpportunityScore | None:
    if target_url:
        normalized_target = normalize_url(target_url)
        for score in scores:
            if normalize_url(score.url) == normalized_target:
                return score
        for score in scores:
            if url_matches(score.url, target_url):
                return score
    return scores[0] if scores else None


def add_step(result: DailyAutomationResult, name: str, status: str, artifacts: list[Path | str] | None = None, notes: list[str] | None = None) -> None:
    result.steps.append(
        DailyAutomationStep(
            name=name,
            status=status,
            artifacts=[str(path) for path in artifacts or [] if path],
            notes=notes or [],
        )
    )


def pipeline_status(result: DailyAutomationResult, readiness_status: str = "") -> str:
    if result.blockers:
        return "automation_failed_before_output"
    if result.pipeline == "brief":
        return "daily_brief_waiting_owner_review"
    if result.pipeline == "rich-content":
        return "rich_content_package_waiting_owner_review"
    if readiness_status == "ready_for_owner_approved_publish_handoff":
        return "ready_for_owner_approved_publish_handoff"
    return "publish_prep_blocked_before_owner_authorization"


def render_report(result: DailyAutomationResult) -> str:
    task = result.selected_task
    lines = [
        "# Daily SEO/GEO Automation Run",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Pipeline: `{result.pipeline}`",
        f"- Status: `{result.status}`",
        f"- Target URL: `{task.get('target_url', 'N/A')}`",
        f"- Keyword: {task.get('keyword', 'N/A')}",
        f"- Content type: {task.get('task_type', 'N/A')}",
        "- 执行状态: draft/prep-only；未登录 CMS、未上传媒体、未写数据库、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天使用自动化 orchestrator 只选择一个最高价值 SEO/GEO 任务，并按安全 pipeline 生成可审核产物。这样比随机写文章更有价值，因为它优先处理商业意图、服务页转化、图文内容、媒体准备和发布门槛。",
        "",
        "## Selected Task",
        "",
        f"- 目标页面: `{task.get('target_url', 'N/A')}`",
        f"- 目标关键词: {task.get('keyword', 'N/A')}",
        f"- 页面类型: {task.get('page_type', 'N/A')}",
        f"- 服务: {task.get('service', 'N/A')}",
        f"- 地区: {task.get('location', 'N/A')}",
        f"- 机会分: {task.get('total_score', 'N/A')}",
        "",
        "## Automation Steps",
        "",
    ]
    for step in result.steps:
        lines.append(f"- `{step.name}`: {step.status}")
        for artifact in step.artifacts:
            lines.append(f"  - artifact: `{artifact}`")
        for note in step.notes:
            lines.append(f"  - note: {note}")
    lines.extend(["", "## Handoff Blockers", ""])
    lines.extend(f"- {item}" for item in result.handoff_blockers) if result.handoff_blockers else lines.append("- None")
    lines.extend(["", "## Automation Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Owner Review Notes",
            "",
            "- 本次自动化不代表发布授权；真实执行仍需要业主批准具体内容包并明确要求执行。",
            "- research-search / research-discovery 只输出候选来源；正式引用仍需通过 `research-intake` 或 `latest-research --source` 写入 source log。",
            "- 生成图片、效果图和概念图必须继续标注为 design/rendering concept，不能说成真实完工案例。",
            "- 如果选择 `publish-prep` pipeline，handoff blockers 是发布前必须处理的授权和媒体准备事项。",
            "",
            "## QA Checklist",
            "",
            "- [ ] 只选择了一个最高价值任务，没有批量生成随机文章。",
            "- [ ] 输出仍停留在 draft/prep-only，没有 CMS 写入或 live 发布。",
            "- [ ] 中文和英文页面配对已纳入后续执行范围。",
            "- [ ] 候选来源未被当作正式引用，source log 仍需要明确选择和 latest-research 抓取。",
            "- [ ] 未编造案例、评价、价格、工期、保修、资质、服务区域或排名承诺。",
            "- [ ] 图文/效果图内容有概念标签和 claim boundary。",
            "",
            "- 已完成：每日 SEO/GEO 自动化 orchestrator 已生成本次安全运行产物",
            f"- 目标关键词/页面：{task.get('keyword', 'N/A')} / {task.get('target_url', 'N/A')}",
            "- 预期收益：把 daily SEO/GEO 从人工串命令升级为可重复、可审计、可扩展的单任务自动化流程",
            "- 需要业主补充：发布前仍需批准具体内容包、明确执行、确认 CTA/媒体 URL/QA/storage",
            "- 建议下一步：审核本次自动化报告，选择是否允许下一阶段生成完整图文发布准备包",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifacts(root: Path, result: DailyAutomationResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    json_path = data_dir / RUN_JSON_NAME
    report_path = reports_dir / f"{today}-daily-automation-run.md"
    result.artifacts.update({"run_json": str(json_path), "run_report": str(report_path)})
    write_text(
        json_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "pipeline": result.pipeline,
                "selected_task": result.selected_task,
                "steps": [step.as_dict() for step in result.steps],
                "blockers": result.blockers,
                "warnings": result.warnings,
                "handoff_blockers": result.handoff_blockers,
                "artifacts": result.artifacts,
                "no_live_actions_executed": True,
                "safety_note": "Daily automation is draft/prep-only unless a separate owner-approved execution path is used.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return json_path, report_path


def run_daily_automation(
    root: Path,
    *,
    pipeline: str = "brief",
    target_url: str = "",
    topic: str = "",
    website_root: str = "",
    discover_research_sources: bool = True,
    research_config_path: str = "",
    research_fetch_remote: bool = True,
    research_search_provider: str = "hybrid-rss",
    research_search_feeds_config: str = "seo-workspace/config/research-search-feeds.example.yml",
    research_timeout: int = 10,
    research_per_seed_limit: int = 5,
    research_limit: int = 20,
    research_write_example: bool = True,
    auto_accept_research_sources: bool = True,
    research_intake_min_score: int = 60,
    research_intake_limit: int = 2,
    authorization_profile_path: str = "",
) -> tuple[DailyAutomationResult, tuple[Path, Path]]:
    if pipeline not in PIPELINES:
        raise ValueError(f"Unsupported pipeline: {pipeline}")
    root = root.resolve()
    result = DailyAutomationResult(status="running", pipeline=pipeline)
    rich_package_draft_path = ""

    try:
        scores = run_opportunity_finder(root)
    except Exception as exc:  # noqa: BLE001 - surface automation failure in report
        result.blockers.append(f"Opportunity scoring failed: {type(exc).__name__}: {exc}")
        result.status = pipeline_status(result)
        return result, write_artifacts(root, result)
    add_step(result, "opportunity_finder", "completed", [root / "seo-workspace" / "data" / "seo-opportunity-scores.csv"])

    calendar_row = {} if target_url else content_calendar_row(root)
    selection_target = target_url or calendar_row.get("target_url", "")
    selected = select_score(scores, selection_target)
    if selected is None:
        result.blockers.append("No SEO/GEO opportunity could be selected from workspace data.")
        result.status = pipeline_status(result)
        return result, write_artifacts(root, result)
    result.selected_task = score_to_task(selected)
    if calendar_row:
        result.selected_task.update(
            {
                "selection_source": "content-calendar",
                "calendar_date": calendar_row.get("date", ""),
                "calendar_target_url": calendar_row.get("target_url", ""),
                "paired_url": calendar_row.get("paired_url", ""),
                "calendar_score": calendar_row.get("calendar_score", ""),
            }
        )
        add_step(
            result,
            "content_calendar",
            "selected",
            [root / "seo-workspace" / "data" / CONTENT_CALENDAR_JSON_NAME],
            [f"selected scheduled target: {calendar_row.get('target_url', '')}"],
        )

    try:
        brief_path = run_content_brief(root, target_url=selected.url)
    except Exception as exc:  # noqa: BLE001
        result.blockers.append(f"Content brief generation failed: {type(exc).__name__}: {exc}")
        result.status = pipeline_status(result)
        return result, write_artifacts(root, result)
    add_step(result, "content_brief", "completed", [brief_path], ["owner review required before execution"])

    if pipeline in {"rich-content", "publish-prep"}:
        if discover_research_sources:
            try:
                search_result, search_artifacts = run_research_search(
                    root,
                    target_url=selected.url,
                    provider=research_search_provider,
                    fetch_remote=research_fetch_remote,
                    timeout=research_timeout,
                    limit=research_limit,
                    feeds_config=research_search_feeds_config,
                    write_feeds_example=research_write_example,
                )
            except Exception as exc:  # noqa: BLE001 - current internet search is useful but not a drafting gate
                warning = f"Research search failed non-blocking: {type(exc).__name__}: {exc}"
                result.warnings.append(warning)
                add_step(
                    result,
                    "research_search",
                    "failed_non_blocking",
                    notes=[
                        warning,
                        "rich-content continues with trusted seed discovery and existing research-source-log rows",
                    ],
                )
            else:
                search_notes = [
                    f"candidate sources: {len(search_result.candidates)}",
                    "search-candidate only; did not write research-source-log.csv",
                    "use research-intake or latest-research before source-dependent publishing",
                ]
                if not research_fetch_remote:
                    search_notes.append("remote search fetching disabled; query plan only")
                search_notes.extend(search_result.blockers)
                search_notes.extend(search_result.warnings)
                add_step(result, "research_search", search_result.status, list(search_artifacts), search_notes)
                result.warnings.extend(search_result.warnings)
                result.warnings.extend(f"Research search handoff note: {item}" for item in search_result.blockers)
                if auto_accept_research_sources and research_fetch_remote and search_result.ok and search_result.candidates:
                    try:
                        search_intake_result, search_intake_artifacts = run_research_intake(
                            root,
                            candidates_path=str(search_artifacts[1]),
                            target_url=selected.url,
                            limit=research_intake_limit,
                            min_score=research_intake_min_score,
                            timeout=research_timeout,
                        )
                    except Exception as exc:  # noqa: BLE001 - search intake should not block content drafting
                        warning = f"Research search intake failed non-blocking: {type(exc).__name__}: {exc}"
                        result.warnings.append(warning)
                        add_step(result, "research_search_intake", "failed_non_blocking", notes=[warning])
                    else:
                        add_step(
                            result,
                            "research_search_intake",
                            search_intake_result.status,
                            list(search_intake_artifacts),
                            search_intake_result.warnings + search_intake_result.blockers,
                        )
                        result.warnings.extend(search_intake_result.warnings)
                        result.warnings.extend(f"Research search intake handoff note: {item}" for item in search_intake_result.blockers)
                elif auto_accept_research_sources:
                    add_step(
                        result,
                        "research_search_intake",
                        "skipped",
                        notes=["remote search disabled, no candidates, or search candidates were not ready"],
                    )
                else:
                    add_step(result, "research_search_intake", "skipped", notes=["auto source intake disabled by operator flag"])
            try:
                discovery_result, discovery_artifacts = run_research_discovery(
                    root,
                    target_url=selected.url,
                    config_path=research_config_path,
                    fetch_remote=research_fetch_remote,
                    timeout=research_timeout,
                    per_seed_limit=research_per_seed_limit,
                    limit=research_limit,
                    write_example=research_write_example,
                )
            except Exception as exc:  # noqa: BLE001 - discovery is useful but not a publishing gate
                warning = f"Research discovery failed non-blocking: {type(exc).__name__}: {exc}"
                result.warnings.append(warning)
                add_step(
                    result,
                    "research_discovery",
                    "failed_non_blocking",
                    notes=[
                        warning,
                        "rich-content continues with existing research-source-log rows only",
                        "use research-intake or latest-research before source-dependent publishing",
                    ],
                )
            else:
                discovery_notes = [
                    f"candidate sources: {len(discovery_result.candidates)}",
                    "candidate-only; did not write research-source-log.csv",
                    "use research-intake or latest-research before source-dependent publishing",
                ]
                if not research_fetch_remote:
                    discovery_notes.append("remote fetching disabled; seed URLs only")
                discovery_notes.extend(discovery_result.blockers)
                discovery_notes.extend(discovery_result.warnings)
                add_step(result, "research_discovery", discovery_result.status, list(discovery_artifacts), discovery_notes)
                result.warnings.extend(discovery_result.warnings)
                result.warnings.extend(f"Research discovery handoff note: {item}" for item in discovery_result.blockers)
                if auto_accept_research_sources:
                    if not research_fetch_remote:
                        add_step(
                            result,
                            "research_intake",
                            "skipped",
                            notes=[
                                "remote fetching disabled; source log auto-intake skipped",
                                "run research-intake after selecting/fetching sources when network is allowed",
                            ],
                        )
                    elif discovery_result.ok:
                        try:
                            intake_result, intake_artifacts = run_research_intake(
                                root,
                                target_url=selected.url,
                                limit=research_intake_limit,
                                min_score=research_intake_min_score,
                                timeout=research_timeout,
                            )
                        except Exception as exc:  # noqa: BLE001 - research intake should not block content drafting
                            warning = f"Research intake failed non-blocking: {type(exc).__name__}: {exc}"
                            result.warnings.append(warning)
                            add_step(result, "research_intake", "failed_non_blocking", notes=[warning])
                        else:
                            add_step(
                                result,
                                "research_intake",
                                intake_result.status,
                                list(intake_artifacts),
                                intake_result.warnings + intake_result.blockers,
                            )
                            result.warnings.extend(intake_result.warnings)
                            result.warnings.extend(f"Research intake handoff note: {item}" for item in intake_result.blockers)
                    else:
                        add_step(
                            result,
                            "research_intake",
                            "skipped",
                            notes=["research discovery did not produce trusted candidates"],
                        )
                else:
                    add_step(
                        result,
                        "research_intake",
                        "skipped",
                        notes=["auto source intake disabled by operator flag"],
                    )
        else:
            add_step(
                result,
                "research_discovery",
                "skipped",
                notes=[
                    "skipped by operator flag",
                    "rich-content continues with existing research-source-log rows only",
                ],
            )
            add_step(
                result,
                "research_intake",
                "skipped",
                notes=["research discovery skipped; no candidates available for auto source intake"],
            )

        try:
            package_path = write_rich_content_package(root, target_url=selected.url, topic=topic)
            rich_package_draft_path = package_path.relative_to(root).as_posix()
            blocks_artifacts = run_rich_blocks(root, target_url=selected.url, draft_path=str(package_path))
            media_result, media_artifacts = run_media_assets(root)
            concept_result, concept_artifacts = run_concept_assets(root)
            upload_result, upload_artifacts = run_media_upload_plan(root)
            editor_result, editor_artifacts = run_rich_editor(root)
            editor_apply_result, editor_apply_artifacts = run_rich_editor_apply(root)
        except Exception as exc:  # noqa: BLE001
            result.blockers.append(f"Rich-content pipeline failed: {type(exc).__name__}: {exc}")
            result.status = pipeline_status(result)
            return result, write_artifacts(root, result)
        add_step(result, "rich_content", "completed", [package_path])
        add_step(result, "rich_blocks", "completed", list(blocks_artifacts))
        add_step(result, "media_assets", media_result.status, list(media_artifacts), media_result.warnings)
        add_step(result, "concept_assets", concept_result.status, list(concept_artifacts), concept_result.warnings)
        add_step(result, "media_upload_plan", upload_result.status, list(upload_artifacts), upload_result.warnings)
        add_step(result, "rich_editor", editor_result.status, list(editor_artifacts), editor_result.warnings + editor_result.blockers)
        add_step(result, "rich_editor_apply", editor_apply_result.status, list(editor_apply_artifacts), editor_apply_result.warnings + editor_apply_result.blockers)
        try:
            service_pattern_summary, service_pattern_artifacts = run_service_pattern_content_package(root, target_url=selected.url)
        except Exception as exc:  # noqa: BLE001 - not every rich-content target is a service-pattern page
            warning = f"Service-pattern package skipped non-blocking: {type(exc).__name__}: {exc}"
            result.warnings.append(warning)
            add_step(result, "service_pattern_package", "skipped_non_blocking", notes=[warning])
        else:
            add_step(
                result,
                "service_pattern_package",
                str(service_pattern_summary.get("status", "owner_review_package_ready")),
                list(service_pattern_artifacts),
                [f"package_count: {service_pattern_summary.get('package_count', 0)}"],
            )
        result.warnings.extend(media_result.warnings + concept_result.warnings + upload_result.warnings + editor_result.warnings + editor_apply_result.warnings)
        result.warnings.extend(f"Rich editor handoff note: {item}" for item in editor_result.blockers)
        result.warnings.extend(f"Rich editor apply handoff note: {item}" for item in editor_apply_result.blockers)

    readiness_status = ""
    if pipeline == "publish-prep":
        try:
            queue_artifacts = run_publish_queue(root, website_root=website_root)
            authorization_result, authorization_artifacts = run_scheduled_publish_authorization(root, profile_path=authorization_profile_path)
            adapter_result, adapter_artifacts = run_website_publish_adapter(root, website_root=website_root)
            plan_result, plan_artifacts = run_publish_plan(root, target_url=selected.url, draft_path=rich_package_draft_path, mode="pr")
            media_exec_result, _ = run_media_upload_executor(root)
            publish_exec_result, publish_exec_artifacts = run_publish_executor(root)
            readiness_result, readiness_artifacts = run_publish_readiness(root)
            bundle_result, bundle_artifacts = run_publish_bundle(root)
            approved_executor_result, approved_executor_artifacts = run_publish_approved_executor(root)
            implementation_result, implementation_artifacts = run_publish_implementation_package(root, website_root=website_root)
            operator_result, operator_artifacts = run_publish_operator_package(root)
        except Exception as exc:  # noqa: BLE001
            result.blockers.append(f"Publish-prep pipeline failed: {type(exc).__name__}: {exc}")
            result.status = pipeline_status(result)
            return result, write_artifacts(root, result)
        readiness_status = readiness_result.status
        add_step(result, "publish_queue", "completed", list(queue_artifacts))
        add_step(result, "scheduled_publish_authorization", authorization_result.status, list(authorization_artifacts), authorization_result.blockers)
        add_step(result, "website_publish_adapter", adapter_result.status, list(adapter_artifacts), adapter_result.blockers)
        add_step(result, "publish_plan", plan_result.status, list(plan_artifacts), plan_result.blockers)
        add_step(result, "media_upload_executor", media_exec_result.status, list(media_exec_result.artifacts.values()), media_exec_result.blockers)
        add_step(result, "publish_executor", publish_exec_result.status, list(publish_exec_artifacts), publish_exec_result.blockers)
        add_step(result, "publish_readiness", readiness_result.status, list(readiness_artifacts), readiness_result.blockers)
        add_step(result, "publish_bundle", bundle_result.status, list(bundle_artifacts), bundle_result.blockers)
        approved_executor_notes = []
        if approved_executor_result.blockers:
            approved_executor_notes.append(
                f"approved executor blockers: {len(approved_executor_result.blockers)}; see publish-approved-execution-record.json"
            )
        add_step(
            result,
            "publish_approved_executor",
            approved_executor_result.status,
            list(approved_executor_artifacts),
            approved_executor_notes,
        )
        implementation_notes = []
        if implementation_result.blockers:
            implementation_notes.append(
                f"implementation package blockers: {len(implementation_result.blockers)}; see publish-implementation-package.json"
            )
        add_step(
            result,
            "publish_implementation_package",
            implementation_result.status,
            list(implementation_artifacts),
            implementation_notes,
        )
        operator_notes = []
        if operator_result.blockers:
            operator_notes.append(
                f"operator command blockers: {len(operator_result.blockers)}; see publish-operator-command.json"
            )
        add_step(
            result,
            "publish_operator_package",
            operator_result.status,
            list(operator_artifacts),
            operator_notes,
        )
        result.handoff_blockers.extend(readiness_result.blockers)
        if authorization_result.blockers:
            result.handoff_blockers.append(
                f"Scheduled publish authorization is not ready: {authorization_result.status}. See scheduled-publish-authorization.json for details."
            )
        if adapter_result.blockers:
            result.handoff_blockers.append(f"Website publish adapter is not ready: {adapter_result.status}. See website-publish-adapter.json for details.")
        if bundle_result.blockers:
            result.handoff_blockers.append(f"Publish bundle is not ready: {bundle_result.status}. See publish-execution-bundle.json for details.")
        if approved_executor_result.blockers:
            result.handoff_blockers.append(
                f"Approved executor simulation is not ready: {approved_executor_result.status}. See publish-approved-execution-record.json for details."
            )
        if implementation_result.blockers:
            result.handoff_blockers.append(
                f"Implementation package is not ready: {implementation_result.status}. See publish-implementation-package.json for details."
            )
        if operator_result.blockers:
            result.handoff_blockers.append(
                f"Operator command package is not ready: {operator_result.status}. See publish-operator-command.json for details."
            )
        result.warnings.extend(
            plan_result.warnings
            + authorization_result.warnings
            + adapter_result.warnings
            + media_exec_result.warnings
            + publish_exec_result.warnings
            + readiness_result.warnings
            + bundle_result.warnings
            + approved_executor_result.warnings
            + implementation_result.warnings
            + operator_result.warnings
        )

    result.status = pipeline_status(result, readiness_status)
    return result, write_artifacts(root, result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the safe daily SEO/GEO automation orchestrator.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--pipeline", default="brief", choices=sorted(PIPELINES))
    parser.add_argument("--target-url", default="", help="Optional target URL override from scored opportunities.")
    parser.add_argument("--topic", default="", help="Optional rich-content topic override.")
    parser.add_argument("--website-root", default="", help="Optional website source root for publish-prep evidence checks.")
    parser.add_argument("--skip-research-discovery", action="store_true", help="Skip candidate source discovery before rich-content/publish-prep.")
    parser.add_argument("--research-config-path", default="", help="Trusted research source config path.")
    parser.add_argument("--no-fetch-research-remote", action="store_true", help="Do not fetch remote research seed pages.")
    parser.add_argument("--research-search-provider", default="hybrid-rss", help="research-search provider: google-news-rss, trusted-rss, or hybrid-rss.")
    parser.add_argument("--research-search-feeds-config", default="seo-workspace/config/research-search-feeds.example.yml", help="Optional trusted RSS/Atom feed config for research-search.")
    parser.add_argument("--research-timeout", type=int, default=10, help="Research seed fetch timeout in seconds.")
    parser.add_argument("--research-per-seed-limit", type=int, default=5, help="Maximum candidates per trusted seed.")
    parser.add_argument("--research-limit", type=int, default=20, help="Maximum discovered research candidates.")
    parser.add_argument("--no-write-research-example", action="store_true", help="Do not rewrite the trusted source example config.")
    parser.add_argument("--no-auto-accept-research-sources", action="store_true", help="Do not auto-record high-trust discovery candidates into research-source-log.csv.")
    parser.add_argument("--research-intake-min-score", type=int, default=60, help="Minimum discovery score for automatic source intake.")
    parser.add_argument("--research-intake-limit", type=int, default=2, help="Maximum trusted candidate sources to auto-intake per run.")
    parser.add_argument("--authorization-profile-path", default="", help="Optional scheduled publish authorization profile path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_daily_automation(
        Path(args.root),
        pipeline=args.pipeline,
        target_url=args.target_url,
        topic=args.topic,
        website_root=args.website_root,
        discover_research_sources=not args.skip_research_discovery,
        research_config_path=args.research_config_path,
        research_fetch_remote=not args.no_fetch_research_remote,
        research_search_provider=args.research_search_provider,
        research_search_feeds_config=args.research_search_feeds_config,
        research_timeout=args.research_timeout,
        research_per_seed_limit=args.research_per_seed_limit,
        research_limit=args.research_limit,
        research_write_example=not args.no_write_research_example,
        auto_accept_research_sources=not args.no_auto_accept_research_sources,
        research_intake_min_score=args.research_intake_min_score,
        research_intake_limit=args.research_intake_limit,
        authorization_profile_path=args.authorization_profile_path,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
