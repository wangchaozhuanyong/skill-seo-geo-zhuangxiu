#!/usr/bin/env python3
"""Unified CLI entrypoint for the renovation SEO/GEO operating system."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SEO_GEO_DIR = SCRIPT_DIR / "seo_geo"
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))

from ai_crawler_policy import run_ai_crawler_owner_review_draft, run_ai_crawler_policy_report  # noqa: E402
from content_brief import run_content_brief  # noqa: E402
from content_calendar import run_content_calendar  # noqa: E402
from content_quality_review import run_content_quality_review  # noqa: E402
from config import validate_config  # noqa: E402
from concept_assets import run_concept_assets  # noqa: E402
from content_studio_decision_orchestrator import run_content_studio_decision_orchestrator  # noqa: E402
from content_studio import run_content_studio  # noqa: E402
from content_studio_next import run_content_studio_next  # noqa: E402
from content_studio_operator_ready_handoff import run_content_studio_operator_ready_handoff  # noqa: E402
from content_studio_orchestrator import run_content_studio_orchestrator  # noqa: E402
from content_studio_owner_decision_editor import run_content_studio_owner_decision_editor  # noqa: E402
from content_studio_owner_decision_import import run_content_studio_owner_decision_import  # noqa: E402
from content_studio_owner_decision_status import run_content_studio_owner_decision_status  # noqa: E402
from content_studio_owner_review_package import run_content_studio_owner_review_package  # noqa: E402
from content_studio_postrun import run_content_studio_postrun  # noqa: E402
from content_studio_approval_packet import run_content_studio_approval_packet  # noqa: E402
from content_studio_media_url_template import run_content_studio_media_url_template  # noqa: E402
from content_studio_media_ready_handoff import run_content_studio_media_ready_handoff  # noqa: E402
from content_studio_media_review_package import run_content_studio_media_review_package  # noqa: E402
from content_studio_media_status import run_content_studio_media_status  # noqa: E402
from content_studio_uploaded_url_map_draft import run_content_studio_uploaded_url_map_draft  # noqa: E402
from content_studio_uploaded_url_map_editor import run_content_studio_uploaded_url_map_editor  # noqa: E402
from content_studio_uploaded_url_map_import import run_content_studio_uploaded_url_map_import  # noqa: E402
from content_studio_publish_prep import run_content_studio_publish_prep  # noqa: E402
from content_studio_publish_candidate import run_content_studio_publish_candidate  # noqa: E402
from content_studio_queue import run_content_studio_queue  # noqa: E402
from content_system import run_content_system  # noqa: E402
from crawl import run_inventory_audit  # noqa: E402
from automation_completion_audit import run_automation_completion_audit  # noqa: E402
from automation_install_plan import run_automation_install_plan  # noqa: E402
from automation_schedule import run_automation_schedule  # noqa: E402
from daily_automation import run_daily_automation  # noqa: E402
from entity_profile import run_entity_profile  # noqa: E402
from geo_ai import run_geo_ai_report  # noqa: E402
from growth_ops import (  # noqa: E402
    run_ai_search_monitor,
    run_ads_asset_status_tracker,
    run_ads_decision_review,
    run_competitor_gap_audit,
    run_competitor_weekly_monitor,
    run_daily_performance_digest,
    run_data_health_center,
    run_growth_ops_audit,
    run_growth_action_queue,
    run_growth_learning_memory,
    run_lead_quality_editor,
    run_lead_quality_tracker,
    run_local_citation_tracker,
    run_local_seo_verification,
    run_real_proof_asset_request,
    run_weekly_growth_control,
)
from hreflang_validator import run_multilingual_report  # noqa: E402
from image_seo import run_image_seo_report  # noqa: E402
from indexation.baidu import run_baidu_indexation_report  # noqa: E402
from indexation.google import run_google_indexation_report  # noqa: E402
from indexation.indexnow import run_indexnow_report  # noqa: E402
from language_pairs import write_language_pairs  # noqa: E402
from latest_research import run_latest_research  # noqa: E402
from local_seo import run_local_seo_report  # noqa: E402
from media_assets import run_media_assets  # noqa: E402
from media_upload_executor import run_media_upload_executor  # noqa: E402
from media_upload_plan import run_media_upload_plan  # noqa: E402
from media_url_map import run_media_url_map  # noqa: E402
from opportunity_finder import run_opportunity_finder  # noqa: E402
from permissions import PermissionContext, SeoGeoMode, validate_live_preconditions  # noqa: E402
from post_publish_feedback import run_post_publish_feedback  # noqa: E402
from publish_approved_executor import run_publish_approved_executor  # noqa: E402
from publish_approved_execution_input import run_publish_approved_execution_input  # noqa: E402
from publish_bundle import run_publish_bundle  # noqa: E402
from publish_cms_write_executor import run_publish_cms_write_executor  # noqa: E402
from publish_executor import run_publish_executor  # noqa: E402
from publish_execution_receipt import run_publish_execution_receipt  # noqa: E402
from publish_implementation_package import run_publish_implementation_package  # noqa: E402
from publish_media_upload_executor import run_publish_media_upload_executor  # noqa: E402
from publish_operator_package import run_publish_operator_package  # noqa: E402
from publish_operator_ready_handoff import run_publish_operator_ready_handoff  # noqa: E402
from publish_post_media_handoff import run_publish_post_media_handoff  # noqa: E402
from publish_plan import run_publish_plan  # noqa: E402
from publish_queue import run_publish_queue  # noqa: E402
from publish_readiness import run_publish_readiness  # noqa: E402
from qa import run_qa, write_qa_report  # noqa: E402
from research_discovery import run_research_discovery  # noqa: E402
from research_intake import run_research_intake  # noqa: E402
from research_search import run_research_search  # noqa: E402
from rich_blocks import run_rich_blocks  # noqa: E402
from rich_content import ResearchSource, write_rich_content_package  # noqa: E402
from rich_editor import run_rich_editor  # noqa: E402
from rich_editor_apply import run_rich_editor_apply  # noqa: E402
from schema_generator import write_schema_recommendations  # noqa: E402
from schema_validator import run_schema_validation_report  # noqa: E402
from scheduled_publish_authorization import run_scheduled_publish_authorization  # noqa: E402
from scheduled_publish_orchestrator import run_scheduled_publish_orchestrator  # noqa: E402
from scheduled_publish_postrun import run_scheduled_publish_postrun  # noqa: E402
from scheduled_publish_runner import run_scheduled_publish_runner  # noqa: E402
from service_pattern_brief import run_service_pattern_brief  # noqa: E402
from service_pattern_content_package import run_service_pattern_content_package  # noqa: E402
from service_pattern_media_assets import run_service_pattern_media_assets  # noqa: E402
from service_pattern_publish_payload import run_service_pattern_publish_payload  # noqa: E402
from service_pattern_rich_editor import run_service_pattern_rich_editor  # noqa: E402
from technical_findings import run_technical_findings_report  # noqa: E402
from visual_brief import write_visual_briefs  # noqa: E402
from website_publish_adapter import run_website_publish_adapter  # noqa: E402


def report_path(root: Path, name: str) -> Path:
    return root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{name}.md"


def run_validate(root: Path) -> int:
    validate_path = root / "validate_workspace.py"
    if not validate_path.exists():
        print("Missing validate_workspace.py", file=sys.stderr)
        return 1
    import importlib.util

    spec = importlib.util.spec_from_file_location("seo_geo_validate_workspace", validate_path)
    if spec is None or spec.loader is None:
        print("Unable to load validate_workspace.py", file=sys.stderr)
        return 1
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.run_validation(write_report=True)
    print("PASS" if result.ok else "FAIL")
    return 0 if result.ok else 1


def run_daily(root: Path) -> list[Path]:
    outputs: list[Path] = []
    run_opportunity_finder(root)
    outputs.append(run_content_brief(root))
    outputs.append(run_entity_profile(root))
    outputs.append(run_geo_ai_report(root))
    outputs.append(run_local_seo_report(root))
    outputs.append(run_schema_validation_report(root))
    outputs.append(run_multilingual_report(root))
    outputs.append(run_image_seo_report(root))
    qa_result = run_qa(root)
    outputs.append(write_qa_report(root, qa_result))
    return outputs


def run_technical_audit(root: Path, args: argparse.Namespace, *, include_findings: bool = True) -> int:
    rows = run_inventory_audit(
        root=root,
        base_url=args.site or args.base_url,
        fetch_remote=args.fetch_remote,
        timeout=args.timeout,
        add_remote_sitemap_urls=not args.no_add_remote_sitemap_urls,
    )
    print(f"Generated URL inventory rows: {len(rows)}")
    if include_findings:
        summary, artifacts = run_technical_findings_report(root)
        print(f"Generated technical findings: {summary['finding_count']} blockers={summary['publish_blocker_count']}")
        for output in artifacts:
            print(output)
    return 0


def run_apply(root: Path, args: argparse.Namespace) -> int:
    plan = Path(args.plan)
    plan_path = plan if plan.is_absolute() else root / plan
    output = report_path(root, "apply-preflight-report")
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SEO/GEO Apply Preflight Report",
        "",
        f"- Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
        f"- Plan: `{plan_path}`",
        f"- Mode: {args.mode}",
        "- Status: preflight only; no CMS/source/live changes executed",
        "",
    ]
    exit_code = 0
    if not plan_path.exists():
        lines.append("- [error] Plan file does not exist.")
        exit_code = 1
    if args.mode == "live":
        context = PermissionContext.from_env(
            SeoGeoMode.LIVE,
            root=root,
            confirm_live=args.confirm_live,
            qa_passed=args.qa_passed,
            backup_path=args.backup_path,
            rollback_plan_path=args.rollback_plan_path,
            changelog_path=args.changelog_path,
        )
        try:
            validate_live_preconditions(context)
        except Exception as exc:  # noqa: BLE001 - report all live preflight blockers
            lines.append(f"- [error] Live mode blocked: {exc}")
            exit_code = 1
        else:
            lines.append("- Live preconditions passed. This CLI still does not publish by itself.")
    else:
        lines.append("- PR/staging preflight only. Use an explicit implementation path after owner approval.")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Renovation SEO/GEO unified CLI.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--config", default="", help="Optional main SEO/GEO config path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Run workspace validation.")
    subparsers.add_parser("config", help="Validate SEO/GEO configuration examples.")

    crawl_parser = subparsers.add_parser("crawl", help="Run URL inventory crawl/audit.")
    crawl_parser.add_argument("--site", default="", help="Production base URL.")
    crawl_parser.add_argument("--base-url", default="", help="Alias for --site.")
    crawl_parser.add_argument("--fetch-remote", action="store_true", help="Fetch remote pages.")
    crawl_parser.add_argument("--timeout", type=int, default=8)
    crawl_parser.add_argument("--no-add-remote-sitemap-urls", action="store_true")

    tech_parser = subparsers.add_parser("technical-audit", help="Run technical SEO audit.")
    tech_parser.add_argument("--site", default="")
    tech_parser.add_argument("--base-url", default="")
    tech_parser.add_argument("--fetch-remote", action="store_true")
    tech_parser.add_argument("--timeout", type=int, default=8)
    tech_parser.add_argument("--no-add-remote-sitemap-urls", action="store_true")

    technical_findings_parser = subparsers.add_parser("technical-findings", help="Generate structured findings from url-inventory.csv.")
    technical_findings_parser.add_argument("--inventory-path", default="")

    ai_crawler_parser = subparsers.add_parser("ai-crawler-policy", help="Audit robots.txt, llms.txt, and AI crawler access policy.")
    ai_crawler_parser.add_argument("--site", default="")
    ai_crawler_parser.add_argument("--base-url", default="")
    ai_crawler_parser.add_argument("--fetch-remote", action="store_true")
    ai_crawler_parser.add_argument("--timeout", type=int, default=8)
    ai_crawler_parser.add_argument("--path", action="append", default=[])
    ai_crawler_draft_parser = subparsers.add_parser("ai-crawler-draft", help="Create owner-review robots.txt and llms.txt drafts; does not publish.")
    ai_crawler_draft_parser.add_argument("--site", default="")
    ai_crawler_draft_parser.add_argument("--base-url", default="")

    gsc_parser = subparsers.add_parser("gsc-sync", help="Run GSC report/sync when credentials are configured.")
    gsc_parser.add_argument("--site-url", default="")
    gsc_parser.add_argument("--use-api", action="store_true")
    gsc_parser.add_argument("--start-date", default="")
    gsc_parser.add_argument("--end-date", default="")
    gsc_parser.add_argument("--inspection-limit", type=int, default=50)

    google_index_parser = subparsers.add_parser("google-index-status", help="Generate Google index status report.")
    google_index_parser.add_argument("--urls", default="inventory", choices=["inventory", "changed"])
    google_index_parser.add_argument("--site-url", default="")
    google_index_parser.add_argument("--use-api", action="store_true")
    google_index_parser.add_argument("--inspection-limit", type=int, default=50)

    sitemap_parser = subparsers.add_parser("google-submit-sitemap", help="Submit sitemap through GSC when configured.")
    sitemap_parser.add_argument("--site-url", default="")
    sitemap_parser.add_argument("--sitemap-url", default="")
    sitemap_parser.add_argument("--use-api", action="store_true")

    baidu_parser = subparsers.add_parser("baidu-submit", help="Run Baidu submit preflight/report.")
    baidu_parser.add_argument("--urls", default="inventory", choices=["inventory", "changed"])
    baidu_parser.add_argument("--config", default="")
    baidu_parser.add_argument("--use-api", action="store_true")
    baidu_parser.add_argument("--submit-limit", type=int, default=50)

    indexnow_parser = subparsers.add_parser("indexnow-submit", help="Run IndexNow submit preflight/report.")
    indexnow_parser.add_argument("--urls", default="inventory", choices=["inventory", "changed"])
    indexnow_parser.add_argument("--use-api", action="store_true")
    indexnow_parser.add_argument("--submit-limit", type=int, default=50)
    indexnow_parser.add_argument("--action-type", default="updated", choices=["added", "updated", "deleted"])
    indexnow_parser.add_argument("--verify-key", action="store_true")

    subparsers.add_parser("opportunities", help="Score SEO/GEO opportunities.")
    quality_parser = subparsers.add_parser("content-quality-review", help="Review draft content quality, claim safety, and GEO readiness.")
    quality_parser.add_argument("--draft-path", default="")
    quality_parser.add_argument("--target-url", default="")
    feedback_parser = subparsers.add_parser("post-publish-feedback", help="Create a 7/30-day post-publish feedback watchlist.")
    feedback_parser.add_argument("--target-url", default="")
    subparsers.add_parser("daily-performance-digest", help="Create a local daily SEO performance digest; does not fetch or publish.")
    subparsers.add_parser("growth-data-health", help="Check whether GSC/Ads/lead/local data can drive decisions; does not fetch or modify platforms.")
    subparsers.add_parser("lead-quality-tracker", help="Create or summarize the owner-filled lead quality log for ROI decisions.")
    subparsers.add_parser("lead-quality-editor", help="Create a local HTML editor for lead quality CSV entry.")
    subparsers.add_parser("ads-decision-review", help="Create guarded Google Ads keep/tighten/pause recommendations from local exports.")
    subparsers.add_parser("growth-learning-memory", help="Build a local learning memory from Ads decisions, lead quality, and post-publish feedback.")
    subparsers.add_parser("ads-asset-status-tracker", help="Track Google Ads asset approval/serving status from local observations.")
    subparsers.add_parser("growth-action-queue", help="Build a unified safe growth action queue from data gaps, memories, and asset status.")
    subparsers.add_parser("ai-search-monitor", help="Create a manual AI search/GEO monitoring queue; does not query AI platforms.")
    competitor_parser = subparsers.add_parser("competitor-gap-audit", help="Create a manual competitor gap audit checklist; does not fetch competitors.")
    competitor_parser.add_argument("--competitors-config", default="")
    competitor_weekly_parser = subparsers.add_parser("competitor-weekly-monitor", help="Create a fixed competitor weekly monitoring checklist; does not fetch competitors.")
    competitor_weekly_parser.add_argument("--competitors-config", default="")
    subparsers.add_parser("local-citation-tracker", help="Create a local citation/NAP tracker; does not submit directories.")
    subparsers.add_parser("local-seo-verification", help="Create a local SEO truth-verification table for GBP/Bing/NAP/photos/reviews.")
    subparsers.add_parser("real-proof-asset-request", help="Create a real proof asset request list for owner review.")
    subparsers.add_parser("weekly-growth-control", help="Run the local weekly SEO/GEO/PPC growth control report.")
    subparsers.add_parser("growth-ops-audit", help="Run all safe professional SEO/GEO growth ops reports.")
    calendar_parser = subparsers.add_parser("content-calendar", help="Generate a rotating daily SEO/GEO content calendar.")
    calendar_parser.add_argument("--days", type=int, default=14)
    calendar_parser.add_argument("--start-date", default="")
    calendar_parser.add_argument("--history-path", default="")
    calendar_parser.add_argument("--lookback", type=int, default=10)
    subparsers.add_parser("daily", help="Run draft-only daily SEO/GEO workflow.")
    daily_automation_parser = subparsers.add_parser("daily-automation", help="Run one safe daily SEO/GEO automation task.")
    daily_automation_parser.add_argument("--pipeline", default="brief", choices=["brief", "rich-content", "publish-prep"])
    daily_automation_parser.add_argument("--target-url", default="")
    daily_automation_parser.add_argument("--topic", default="")
    daily_automation_parser.add_argument("--website-root", default="")
    daily_automation_parser.add_argument("--skip-research-discovery", action="store_true")
    daily_automation_parser.add_argument("--research-config-path", default="")
    daily_automation_parser.add_argument("--no-fetch-research-remote", action="store_true")
    daily_automation_parser.add_argument("--research-search-provider", default="hybrid-rss")
    daily_automation_parser.add_argument("--research-search-feeds-config", default="seo-workspace/config/research-search-feeds.example.yml")
    daily_automation_parser.add_argument("--research-timeout", type=int, default=10)
    daily_automation_parser.add_argument("--research-per-seed-limit", type=int, default=5)
    daily_automation_parser.add_argument("--research-limit", type=int, default=20)
    daily_automation_parser.add_argument("--no-write-research-example", action="store_true")
    daily_automation_parser.add_argument("--no-auto-accept-research-sources", action="store_true")
    daily_automation_parser.add_argument("--research-intake-min-score", type=int, default=60)
    daily_automation_parser.add_argument("--research-intake-limit", type=int, default=2)
    daily_automation_parser.add_argument("--authorization-profile-path", default="")
    schedule_parser = subparsers.add_parser("automation-schedule", help="Generate/validate safe daily automation schedule plan.")
    schedule_parser.add_argument("--config-path", default="")
    schedule_parser.add_argument("--authorization-profile-path", default="")
    schedule_parser.add_argument("--no-write-example", action="store_true")
    install_plan_parser = subparsers.add_parser("automation-install-plan", help="Create no-install launchd/cron handoff files for fixed-time automation.")
    install_plan_parser.add_argument("--schedule-plan-path", default="")
    install_plan_parser.add_argument("--install-kind", default="launchd", choices=["launchd", "cron", "both"])
    subparsers.add_parser("automation-completion-audit", help="Audit whether all major SEO/GEO automation capabilities are present.")
    authorization_parser = subparsers.add_parser("scheduled-publish-authorization", help="Validate scheduled publish authorization profile; does not publish.")
    authorization_parser.add_argument("--profile-path", default="")
    authorization_parser.add_argument("--no-write-example", action="store_true")
    runner_parser = subparsers.add_parser("scheduled-publish-runner", help="Create a scheduled publish run request; does not execute.")
    runner_parser.add_argument("--profile-path", default="")
    runner_parser.add_argument("--target-url", default="")
    runner_parser.add_argument("--now", default="")
    runner_parser.add_argument("--window-minutes", type=int, default=20)
    runner_parser.add_argument("--ignore-schedule-window", action="store_true")
    runner_parser.add_argument("--allow-duplicate-run", action="store_true")
    runner_parser.add_argument("--no-write-example", action="store_true")
    orchestrator_parser = subparsers.add_parser("scheduled-publish-orchestrator", help="Run safe scheduled publish-prep orchestration; does not live publish.")
    orchestrator_parser.add_argument("--profile-path", default="")
    orchestrator_parser.add_argument("--target-url", default="")
    orchestrator_parser.add_argument("--now", default="")
    orchestrator_parser.add_argument("--window-minutes", type=int, default=20)
    orchestrator_parser.add_argument("--ignore-schedule-window", action="store_true")
    orchestrator_parser.add_argument("--allow-duplicate-run", action="store_true")
    orchestrator_parser.add_argument("--skip-research-discovery", action="store_true")
    orchestrator_parser.add_argument("--no-fetch-research-remote", action="store_true")
    orchestrator_parser.add_argument("--research-search-provider", default="hybrid-rss")
    orchestrator_parser.add_argument("--research-search-feeds-config", default="seo-workspace/config/research-search-feeds.example.yml")
    orchestrator_parser.add_argument("--research-timeout", type=int, default=10)
    orchestrator_parser.add_argument("--research-per-seed-limit", type=int, default=5)
    orchestrator_parser.add_argument("--research-limit", type=int, default=20)
    orchestrator_parser.add_argument("--no-write-research-example", action="store_true")
    orchestrator_parser.add_argument("--no-auto-accept-research-sources", action="store_true")
    orchestrator_parser.add_argument("--research-intake-min-score", type=int, default=60)
    orchestrator_parser.add_argument("--research-intake-limit", type=int, default=2)
    orchestrator_parser.add_argument("--no-write-example", action="store_true")
    postrun_parser = subparsers.add_parser("scheduled-publish-postrun", help="Summarize scheduled publish automation artifacts; does not execute.")
    postrun_parser.add_argument("--orchestration-path", default="")
    postrun_parser.add_argument("--run-request-path", default="")
    postrun_parser.add_argument("--daily-run-path", default="")
    postrun_parser.add_argument("--readiness-path", default="")
    postrun_parser.add_argument("--implementation-path", default="")
    postrun_parser.add_argument("--operator-path", default="")
    postrun_parser.add_argument("--receipt-path", default="")

    service_brief_parser = subparsers.add_parser("service-pattern-brief", help="Generate a draft-only service-pattern brief.")
    service_brief_parser.add_argument("--target-url", required=True)
    service_brief_parser.add_argument("--date", default="")
    service_editor_parser = subparsers.add_parser("service-pattern-editor", help="Create a draft-only service-pattern rich editor.")
    service_editor_parser.add_argument("--target-url", required=True)
    service_editor_parser.add_argument("--date", default="")
    service_payload_parser = subparsers.add_parser("service-pattern-publish-payload", help="Convert service-pattern editor payload/export into CMS payload draft.")
    service_payload_parser.add_argument("--editor-payload-path", required=True)
    service_payload_parser.add_argument("--output-name", default="")
    service_media_parser = subparsers.add_parser("service-pattern-media-assets", help="Prepare draft-only service-pattern concept media assets.")
    service_media_parser.add_argument("--cms-payload-path", required=True)
    service_media_parser.add_argument("--public-base-url", default="")
    service_media_parser.add_argument("--output-prefix", default="")
    service_pattern_parser = subparsers.add_parser("service-pattern-package", help="Build a full draft-only service-pattern content package.")
    service_pattern_parser.add_argument("--target-url", default="")
    service_pattern_parser.add_argument("--service-slug", default="")
    service_pattern_parser.add_argument("--all", action="store_true")
    service_pattern_parser.add_argument("--date", default="")
    service_pattern_parser.add_argument("--public-base-url", default="")
    subparsers.add_parser("content-system", help="Generate content production and publishing automation map.")
    studio_parser = subparsers.add_parser("content-studio", help="Run a draft-only target-page content studio package.")
    studio_parser.add_argument("--target-url", default="")
    studio_parser.add_argument("--pipeline", default="rich-content", choices=["brief", "rich-content", "publish-prep"])
    studio_parser.add_argument("--topic", default="")
    studio_parser.add_argument("--website-root", default="")
    studio_parser.add_argument("--skip-research-discovery", action="store_true")
    studio_parser.add_argument("--research-config-path", default="")
    studio_parser.add_argument("--no-fetch-research-remote", action="store_true")
    studio_parser.add_argument("--research-search-provider", default="hybrid-rss")
    studio_parser.add_argument("--research-search-feeds-config", default="seo-workspace/config/research-search-feeds.example.yml")
    studio_parser.add_argument("--research-timeout", type=int, default=10)
    studio_parser.add_argument("--research-per-seed-limit", type=int, default=5)
    studio_parser.add_argument("--research-limit", type=int, default=20)
    studio_parser.add_argument("--no-write-research-example", action="store_true")
    studio_parser.add_argument("--no-auto-accept-research-sources", action="store_true")
    studio_parser.add_argument("--research-intake-min-score", type=int, default=60)
    studio_parser.add_argument("--research-intake-limit", type=int, default=2)
    studio_parser.add_argument("--authorization-profile-path", default="")
    studio_queue_parser = subparsers.add_parser("content-studio-queue", help="Build a draft-only content studio production queue for site URLs.")
    studio_queue_parser.add_argument("--limit", type=int, default=0)
    studio_next_parser = subparsers.add_parser("content-studio-next", help="Run the next draft-only content studio queue item.")
    studio_next_parser.add_argument("--target-url", default="")
    studio_next_parser.add_argument("--pipeline", default="", choices=["", "brief", "rich-content", "publish-prep"])
    studio_next_parser.add_argument("--website-root", default="")
    studio_next_parser.add_argument("--history-path", default="")
    studio_next_parser.add_argument("--rebuild-queue", action="store_true")
    studio_next_parser.add_argument("--no-fetch-research-remote", action="store_true")
    studio_next_parser.add_argument("--research-search-provider", default="hybrid-rss")
    studio_next_parser.add_argument("--research-search-feeds-config", default="seo-workspace/config/research-search-feeds.example.yml")
    studio_next_parser.add_argument("--owner-review-package", action="store_true")
    studio_orchestrator_parser = subparsers.add_parser("content-studio-orchestrator", help="Run safe fixed-time content-studio queue orchestration.")
    studio_orchestrator_parser.add_argument("--config-path", default="")
    studio_orchestrator_parser.add_argument("--now", default="")
    studio_orchestrator_parser.add_argument("--window-minutes", type=int, default=20)
    studio_orchestrator_parser.add_argument("--ignore-schedule-window", action="store_true")
    studio_orchestrator_parser.add_argument("--allow-duplicate-run", action="store_true")
    studio_postrun_parser = subparsers.add_parser("content-studio-postrun", help="Summarize content-studio orchestration outputs without executing.")
    studio_postrun_parser.add_argument("--orchestration-path", default="")
    studio_postrun_parser.add_argument("--next-run-path", default="")
    studio_postrun_parser.add_argument("--queue-path", default="")
    studio_postrun_parser.add_argument("--history-path", default="")
    studio_publish_candidate_parser = subparsers.add_parser("content-studio-publish-candidate", help="Create a safe owner-review publish candidate from Content Studio output.")
    studio_publish_candidate_parser.add_argument("--postrun-path", default="")
    studio_publish_candidate_parser.add_argument("--content-studio-run-path", default="")
    studio_publish_candidate_parser.add_argument("--website-root", default="")
    studio_publish_candidate_parser.add_argument("--target-url", default="")
    studio_publish_prep_parser = subparsers.add_parser("content-studio-publish-prep", help="Run safe local publish-prep handoff steps for a Content Studio candidate.")
    studio_publish_prep_parser.add_argument("--candidate-path", default="")
    studio_publish_prep_parser.add_argument("--website-root", default="")
    studio_publish_prep_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    studio_publish_prep_parser.add_argument("--owner-approved", action="store_true")
    studio_publish_prep_parser.add_argument("--explicit-execution", action="store_true")
    studio_publish_prep_parser.add_argument("--qa-passed", action="store_true")
    studio_publish_prep_parser.add_argument("--media-ready", action="store_true")
    studio_publish_prep_parser.add_argument("--latest-research-verified", action="store_true")
    studio_publish_prep_parser.add_argument("--allow-blocked-plan", action="store_true")
    studio_approval_packet_parser = subparsers.add_parser("content-studio-approval-packet", help="Create an owner approval packet from Content Studio publish-prep evidence.")
    studio_approval_packet_parser.add_argument("--prep-path", default="")
    studio_approval_packet_parser.add_argument("--candidate-path", default="")
    studio_approval_packet_parser.add_argument("--media-plan-path", default="")
    studio_media_url_template_parser = subparsers.add_parser("content-studio-media-url-template", help="Create an uploaded URL map template for Content Studio concept media.")
    studio_media_url_template_parser.add_argument("--media-plan-path", default="")
    studio_media_url_template_parser.add_argument("--output-path", default="")
    studio_media_url_template_parser.add_argument("--public-base-url", default="")
    studio_media_ready_parser = subparsers.add_parser("content-studio-media-ready-handoff", help="Build a media-ready Content Studio handoff from confirmed uploaded URLs without uploading or publishing.")
    studio_media_ready_parser.add_argument("--upload-plan-path", default="")
    studio_media_ready_parser.add_argument("--uploaded-url-map-path", default="")
    studio_media_ready_parser.add_argument("--cms-payload-path", default="")
    studio_media_ready_parser.add_argument("--candidate-path", default="")
    studio_media_ready_parser.add_argument("--website-root", default="")
    studio_media_ready_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    studio_media_ready_parser.add_argument("--owner-approved", action="store_true")
    studio_media_ready_parser.add_argument("--explicit-execution", action="store_true")
    studio_media_ready_parser.add_argument("--qa-passed", action="store_true")
    studio_media_ready_parser.add_argument("--storage-ready", action="store_true")
    studio_media_ready_parser.add_argument("--uploaded-confirmed", action="store_true")
    studio_media_ready_parser.add_argument("--latest-research-verified", action="store_true")
    studio_media_ready_parser.add_argument("--allow-blocked-plan", action="store_true")
    studio_uploaded_url_draft_parser = subparsers.add_parser("content-studio-uploaded-url-map-draft", help="Create or validate an owner-fillable uploaded URL map draft.")
    studio_uploaded_url_draft_parser.add_argument("--template-path", default="")
    studio_uploaded_url_draft_parser.add_argument("--output-path", default="")
    studio_uploaded_url_draft_parser.add_argument("--validate-only", action="store_true")
    studio_uploaded_url_editor_parser = subparsers.add_parser("content-studio-uploaded-url-map-editor", help="Create a local HTML editor for owner-filled uploaded image URLs.")
    studio_uploaded_url_editor_parser.add_argument("--source-path", default="")
    studio_uploaded_url_import_parser = subparsers.add_parser("content-studio-uploaded-url-map-import", help="Import and validate an owner-filled uploaded URL map JSON.")
    studio_uploaded_url_import_parser.add_argument("--filled-map-path", default="")
    studio_uploaded_url_import_parser.add_argument("--template-path", default="")
    studio_uploaded_url_import_parser.add_argument("--output-path", default="")
    studio_media_status_parser = subparsers.add_parser("content-studio-media-status", help="Summarize Content Studio media URL readiness without uploading or publishing.")
    studio_media_status_parser.add_argument("--uploaded-url-map-path", default="")
    studio_media_status_parser.add_argument("--template-path", default="")
    studio_media_status_parser.add_argument("--media-url-map-path", default="")
    studio_media_status_parser.add_argument("--media-ready-payload-path", default="")
    studio_media_status_parser.add_argument("--publish-readiness-path", default="")
    studio_operator_ready_parser = subparsers.add_parser("content-studio-operator-ready-handoff", help="Refresh Content Studio media-ready through operator-ready handoff without live execution.")
    studio_operator_ready_parser.add_argument("--uploaded-url-map-path", default="")
    studio_operator_ready_parser.add_argument("--cms-payload-path", default="")
    studio_operator_ready_parser.add_argument("--website-root", default="")
    studio_operator_ready_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    studio_operator_ready_parser.add_argument("--owner-approved", action="store_true")
    studio_operator_ready_parser.add_argument("--explicit-execution", action="store_true")
    studio_operator_ready_parser.add_argument("--qa-passed", action="store_true")
    studio_operator_ready_parser.add_argument("--storage-ready", action="store_true")
    studio_operator_ready_parser.add_argument("--uploaded-confirmed", action="store_true")
    studio_operator_ready_parser.add_argument("--latest-research-verified", action="store_true")
    studio_operator_ready_parser.add_argument("--allow-blocked-plan", action="store_true")
    studio_operator_ready_parser.add_argument("--allow-blocked-operator", action="store_true")
    studio_media_review_parser = subparsers.add_parser("content-studio-media-review-package", help="Build a local owner-review gallery for generated Content Studio media.")
    studio_media_review_parser.add_argument("--media-upload-plan-path", default="")
    studio_media_review_parser.add_argument("--concept-manifest-path", default="")
    studio_owner_decision_editor_parser = subparsers.add_parser("content-studio-owner-decision-editor", help="Create a local HTML owner decision form; does not execute.")
    studio_owner_decision_editor_parser.add_argument("--decision-path", default="")
    studio_owner_decision_import_parser = subparsers.add_parser("content-studio-owner-decision-import", help="Import an owner-filled decision JSON; does not execute.")
    studio_owner_decision_import_parser.add_argument("--filled-decision-path", required=True)
    studio_owner_decision_import_parser.add_argument("--template-path", default="")
    studio_owner_decision_import_parser.add_argument("--output-path", default="")
    studio_owner_decision_parser = subparsers.add_parser("content-studio-owner-decision-status", help="Validate an owner-filled Content Studio decision template without executing.")
    studio_owner_decision_parser.add_argument("--decision-path", default="")
    studio_owner_decision_parser.add_argument("--media-status-path", default="")
    studio_owner_decision_parser.add_argument("--approval-packet-path", default="")
    studio_owner_decision_parser.add_argument("--website-root", default="")
    studio_decision_orchestrator_parser = subparsers.add_parser("content-studio-decision-orchestrator", help="Run the next safe no-write step from an owner decision.")
    studio_decision_orchestrator_parser.add_argument("--decision-path", default="")
    studio_decision_orchestrator_parser.add_argument("--media-status-path", default="")
    studio_decision_orchestrator_parser.add_argument("--approval-packet-path", default="")
    studio_decision_orchestrator_parser.add_argument("--uploaded-url-map-path", default="")
    studio_decision_orchestrator_parser.add_argument("--candidate-path", default="")
    studio_decision_orchestrator_parser.add_argument("--website-root", default="")
    studio_decision_orchestrator_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    studio_owner_review_parser = subparsers.add_parser("content-studio-owner-review-package", help="Build a complete no-write owner review package for latest Content Studio output.")
    studio_owner_review_parser.add_argument("--website-root", default="")
    studio_owner_review_parser.add_argument("--target-url", default="")
    studio_owner_review_parser.add_argument("--postrun-path", default="")
    studio_owner_review_parser.add_argument("--content-studio-run-path", default="")
    studio_owner_review_parser.add_argument("--public-base-url", default="")

    research_parser = subparsers.add_parser("latest-research", help="Fetch/log latest source research for content packages.")
    research_parser.add_argument("--target-url", default="")
    research_parser.add_argument("--query", action="append", default=[])
    research_parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source as type|url|usage note|claim boundary|query. Repeatable.",
    )
    research_parser.add_argument("--timeout", type=int, default=10)

    discovery_parser = subparsers.add_parser("research-discovery", help="Discover candidate latest-research sources; does not write source log.")
    discovery_parser.add_argument("--target-url", default="")
    discovery_parser.add_argument("--config-path", default="")
    discovery_parser.add_argument("--no-fetch-remote", action="store_true")
    discovery_parser.add_argument("--timeout", type=int, default=10)
    discovery_parser.add_argument("--per-seed-limit", type=int, default=5)
    discovery_parser.add_argument("--limit", type=int, default=20)
    discovery_parser.add_argument("--no-write-example", action="store_true")

    search_parser = subparsers.add_parser("research-search", help="Generate/fetch current internet search candidates; does not write source log.")
    search_parser.add_argument("--target-url", default="")
    search_parser.add_argument("--provider", default="google-news-rss")
    search_parser.add_argument("--no-fetch-remote", action="store_true")
    search_parser.add_argument("--timeout", type=int, default=10)
    search_parser.add_argument("--limit", type=int, default=20)
    search_parser.add_argument("--market", default="MY")
    search_parser.add_argument("--language", default="en")
    search_parser.add_argument("--feeds-config", default="")
    search_parser.add_argument("--no-write-feeds-example", action="store_true")

    intake_parser = subparsers.add_parser("research-intake", help="Auto-record trusted discovery candidates into source log; does not publish.")
    intake_parser.add_argument("--candidates-path", default="")
    intake_parser.add_argument("--target-url", default="")
    intake_parser.add_argument("--limit", type=int, default=2)
    intake_parser.add_argument("--min-score", type=int, default=60)
    intake_parser.add_argument("--allowed-source-type", action="append", default=[])
    intake_parser.add_argument("--timeout", type=int, default=10)

    rich_parser = subparsers.add_parser("rich-content", help="Generate image-rich content package with source log.")
    rich_parser.add_argument("--target-url", default="", help="Target URL or path. Defaults to top opportunity.")
    rich_parser.add_argument("--topic", default="", help="Optional content topic override.")
    rich_parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Source row as type|title|url|publisher|date|usage note. Repeatable.",
    )
    rich_parser.add_argument("--no-use-research-log", action="store_true", help="Do not auto-attach existing research-source-log rows for the target page.")

    blocks_parser = subparsers.add_parser("rich-blocks", help="Convert rich-content package into structured blocks, HTML, and CMS payload drafts.")
    blocks_parser.add_argument("--target-url", default="", help="Target or paired URL from a rich-content package.")
    blocks_parser.add_argument("--draft-path", default="", help="Specific rich-content Markdown package.")

    editor_parser = subparsers.add_parser("rich-editor", help="Create a draft-only draggable rich text/image editor package.")
    editor_parser.add_argument("--blocks-path", default="")
    editor_parser.add_argument("--media-plan-path", default="")
    editor_parser.add_argument("--concept-manifest-path", default="")

    editor_apply_parser = subparsers.add_parser("rich-editor-apply", help="Apply rich-editor JSON export to a CMS payload draft; does not publish.")
    editor_apply_parser.add_argument("--editor-export-path", default="")
    editor_apply_parser.add_argument("--cms-payload-path", default="")

    media_parser = subparsers.add_parser("media-assets", help="Prepare generated-design media assets and optional media-ready CMS payload.")
    media_parser.add_argument("--blocks-path", default="")
    media_parser.add_argument("--cms-payload-path", default="")
    media_parser.add_argument("--url-map-path", default="")

    concept_assets_parser = subparsers.add_parser("concept-assets", help="Generate local SVG design/rendering concept assets from media-asset-plan.json.")
    concept_assets_parser.add_argument("--media-plan-path", default="")
    concept_assets_parser.add_argument("--asset-dir", default="")

    media_upload_parser = subparsers.add_parser("media-upload-plan", help="Create a draft-only media upload queue; does not upload.")
    media_upload_parser.add_argument("--media-plan-path", default="")
    media_upload_parser.add_argument("--concept-manifest-path", default="")
    media_upload_parser.add_argument("--media-file-manifest-path", default="")
    media_upload_parser.add_argument("--bucket", default="site-images")
    media_upload_parser.add_argument("--storage-prefix", default="media/seo-generated")
    media_upload_parser.add_argument("--public-base-url", default="")

    media_upload_executor_parser = subparsers.add_parser("media-upload-executor", help="Create a gated media upload execution request; does not upload.")
    media_upload_executor_parser.add_argument("--upload-plan-path", default="")
    media_upload_executor_parser.add_argument("--uploaded-url-map-path", default="")
    media_upload_executor_parser.add_argument("--cms-payload-path", default="")
    media_upload_executor_parser.add_argument("--owner-approved", action="store_true")
    media_upload_executor_parser.add_argument("--explicit-execution", action="store_true")
    media_upload_executor_parser.add_argument("--qa-passed", action="store_true")
    media_upload_executor_parser.add_argument("--storage-ready", action="store_true")
    media_upload_executor_parser.add_argument("--uploaded-confirmed", action="store_true")

    media_map_parser = subparsers.add_parser("media-url-map", help="Build media URL map from local generated/selected files; does not upload.")
    media_map_parser.add_argument("--asset-dir", default="")
    media_map_parser.add_argument("--public-base-url", default="")
    media_map_parser.add_argument("--media-plan-path", default="")

    queue_parser = subparsers.add_parser("publish-queue", help="Generate owner-review publishing queue and CMS field map.")
    queue_parser.add_argument("--website-root", default="", help="Optional website source root for evidence checks.")

    adapter_parser = subparsers.add_parser("website-publish-adapter", help="Discover read-only website publishing adapter evidence.")
    adapter_parser.add_argument("--website-root", default="", help="Website source root to scan read-only.")

    plan_parser = subparsers.add_parser("publish-plan", help="Create a gated execution plan from approved-publish-queue.csv; does not publish.")
    plan_parser.add_argument("--target-url", default="", help="Target or paired URL from the queue.")
    plan_parser.add_argument("--draft-path", default="", help="Exact draft_path value from approved-publish-queue.csv.")
    plan_parser.add_argument("--mode", default="pr", choices=["draft", "pr", "staging", "live"])
    plan_parser.add_argument("--owner-approved", action="store_true")
    plan_parser.add_argument("--explicit-execution", action="store_true")
    plan_parser.add_argument("--qa-passed", action="store_true")
    plan_parser.add_argument("--owner-input-resolved", action="store_true")
    plan_parser.add_argument("--latest-research-verified", action="store_true")
    plan_parser.add_argument("--single-language-approved", action="store_true")
    plan_parser.add_argument("--confirm-live", action="store_true")
    plan_parser.add_argument("--backup-path", default="")
    plan_parser.add_argument("--changelog-path", default="")
    plan_parser.add_argument("--rollback-plan-path", default="")

    executor_parser = subparsers.add_parser("publish-executor", help="Build a gated CMS/source write request dry-run; does not publish.")
    executor_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    executor_parser.add_argument("--plan-path", default="")
    executor_parser.add_argument("--cms-payload-path", default="")
    executor_parser.add_argument("--next-status", default="draft", choices=["draft", "published"])
    executor_parser.add_argument("--owner-approved", action="store_true")
    executor_parser.add_argument("--explicit-execution", action="store_true")
    executor_parser.add_argument("--qa-passed", action="store_true")
    executor_parser.add_argument("--media-ready", action="store_true")
    executor_parser.add_argument("--allow-blocked-plan", action="store_true")

    readiness_parser = subparsers.add_parser("publish-readiness", help="Summarize publish handoff readiness; does not publish.")
    readiness_parser.add_argument("--publish-plan-path", default="")
    readiness_parser.add_argument("--cms-request-path", default="")
    readiness_parser.add_argument("--media-request-path", default="")
    readiness_parser.add_argument("--media-url-map-path", default="")
    readiness_parser.add_argument("--media-ready-payload-path", default="")
    readiness_parser.add_argument("--research-log-path", default="")
    readiness_parser.add_argument("--queue-path", default="")

    bundle_parser = subparsers.add_parser("publish-bundle", help="Create a sealed publish execution bundle; does not execute.")
    bundle_parser.add_argument("--readiness-path", default="")
    bundle_parser.add_argument("--cms-request-path", default="")

    approved_executor_parser = subparsers.add_parser("publish-approved-executor", help="Simulate a gated owner-approved executor; does not execute writes.")
    approved_executor_parser.add_argument("--bundle-path", default="")
    approved_executor_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    approved_executor_parser.add_argument("--owner-approved", action="store_true")
    approved_executor_parser.add_argument("--explicit-execution", action="store_true")
    approved_executor_parser.add_argument("--qa-passed", action="store_true")
    approved_executor_parser.add_argument("--backup-path", default="")
    approved_executor_parser.add_argument("--changelog-path", default="")
    approved_executor_parser.add_argument("--rollback-plan-path", default="")
    approved_executor_parser.add_argument("--confirm-live", action="store_true")
    approved_executor_parser.add_argument("--allowed-target-url", action="append", default=[])

    execution_input_parser = subparsers.add_parser("publish-approved-execution-input", help="Create guarded future execution input templates; does not execute writes.")
    execution_input_parser.add_argument("--operator-path", default="")
    execution_input_parser.add_argument("--helper-call-path", default="")
    execution_input_parser.add_argument("--adapter-path", default="")
    execution_input_parser.add_argument("--allow-blocked-operator", action="store_true")

    cms_write_parser = subparsers.add_parser("publish-cms-write-executor", help="Guarded CMS write executor; defaults to dry-run.")
    cms_write_parser.add_argument("--execution-input-path", default="")
    cms_write_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "staging", "live"])
    cms_write_parser.add_argument("--confirm-write", action="store_true")
    cms_write_parser.add_argument("--allowed-target-url", action="append", default=[])
    cms_write_parser.add_argument("--require-env", action="store_true")

    media_write_parser = subparsers.add_parser("publish-media-upload-executor", help="Guarded media upload executor; defaults to dry-run.")
    media_write_parser.add_argument("--upload-plan-path", default="")
    media_write_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "staging", "live"])
    media_write_parser.add_argument("--confirm-upload", action="store_true")
    media_write_parser.add_argument("--allowed-bucket", default="site-images")
    media_write_parser.add_argument("--require-env", action="store_true")
    media_write_parser.add_argument("--no-create-media-records", action="store_true")

    post_media_parser = subparsers.add_parser("publish-post-media-handoff", help="Chain uploaded media URLs into operator-ready and CMS dry-run handoff.")
    post_media_parser.add_argument("--uploaded-url-map-path", default="")
    post_media_parser.add_argument("--website-root", default="")
    post_media_parser.add_argument("--allowed-target-url", action="append", default=[])
    post_media_parser.add_argument("--strict-operator", action="store_true")

    implementation_parser = subparsers.add_parser("publish-implementation-package", help="Create a no-write publish implementation package.")
    implementation_parser.add_argument("--execution-record-path", default="")
    implementation_parser.add_argument("--website-root", default="")
    implementation_parser.add_argument("--adapter-path", default="")

    operator_parser = subparsers.add_parser("publish-operator-package", help="Create a no-write publish operator command package.")
    operator_parser.add_argument("--implementation-path", default="")
    operator_parser.add_argument("--helper-call-path", default="")

    operator_ready_parser = subparsers.add_parser("publish-operator-ready-handoff", help="Refresh the no-write operator-ready publish handoff chain.")
    operator_ready_parser.add_argument("--website-root", default="")
    operator_ready_parser.add_argument("--mode", default="dry-run", choices=["dry-run", "pr", "staging", "live"])
    operator_ready_parser.add_argument("--owner-approved", action="store_true")
    operator_ready_parser.add_argument("--explicit-execution", action="store_true")
    operator_ready_parser.add_argument("--qa-passed", action="store_true")
    operator_ready_parser.add_argument("--media-ready", action="store_true")
    operator_ready_parser.add_argument("--latest-research-verified", action="store_true")
    operator_ready_parser.add_argument("--allow-blocked-plan", action="store_true")
    operator_ready_parser.add_argument("--allow-blocked-operator", action="store_true")
    operator_ready_parser.add_argument("--backup-path", default="")
    operator_ready_parser.add_argument("--changelog-path", default="")
    operator_ready_parser.add_argument("--rollback-plan-path", default="")
    operator_ready_parser.add_argument("--confirm-live", action="store_true")
    operator_ready_parser.add_argument("--allowed-target-url", action="append", default=[])

    receipt_parser = subparsers.add_parser("publish-execution-receipt", help="Verify a publish execution result receipt; does not execute writes.")
    receipt_parser.add_argument("--operator-path", default="")
    receipt_parser.add_argument("--execution-result-path", default="")
    receipt_parser.add_argument("--no-write-example", action="store_true")

    subparsers.add_parser("entity", help="Generate entity profile.")
    subparsers.add_parser("geo-ai", help="Generate GEO/AI readiness report.")
    subparsers.add_parser("local-seo", help="Generate local SEO report.")
    subparsers.add_parser("schema", help="Generate schema recommendations and validation report.")
    subparsers.add_parser("multilingual", help="Generate language pairs and multilingual report.")
    subparsers.add_parser("image-seo", help="Generate image SEO report.")

    qa_parser = subparsers.add_parser("qa", help="Run pre-publish QA.")
    qa_parser.add_argument("--file", default="", help="Reserved for future explicit draft selection.")
    qa_parser.add_argument("--target-url", default="")
    qa_parser.add_argument("--mode", default="draft", choices=["draft", "live"])
    qa_parser.add_argument("--backup-path", default="")
    qa_parser.add_argument("--rollback-plan-path", default="")
    qa_parser.add_argument("--content-path", default="")

    apply_parser = subparsers.add_parser("apply", help="Apply preflight only; does not publish.")
    apply_parser.add_argument("--plan", required=True)
    apply_parser.add_argument("--mode", required=True, choices=["pr", "staging", "live"])
    apply_parser.add_argument("--confirm-live", action="store_true")
    apply_parser.add_argument("--qa-passed", action="store_true")
    apply_parser.add_argument("--backup-path", default="")
    apply_parser.add_argument("--rollback-plan-path", default="")
    apply_parser.add_argument("--changelog-path", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    command = args.command

    if command == "validate":
        return run_validate(root)
    if command == "config":
        result = validate_config(root, config_path=args.config)
        print("PASS" if result.ok else "FAIL")
        for warning in result.warnings:
            print(f"warning: {warning}")
        for error in result.errors:
            print(f"error: {error}")
        return 0 if result.ok else 1
    if command == "crawl":
        return run_technical_audit(root, args, include_findings=False)
    if command == "technical-audit":
        return run_technical_audit(root, args, include_findings=True)
    if command == "technical-findings":
        summary, artifacts = run_technical_findings_report(root, inventory_path=args.inventory_path)
        print(f"Generated technical findings: {summary['finding_count']} blockers={summary['publish_blocker_count']}")
        for output in artifacts:
            print(output)
        return 0
    if command == "ai-crawler-policy":
        summary, artifacts = run_ai_crawler_policy_report(
            root,
            base_url=args.site or args.base_url,
            fetch_remote=args.fetch_remote,
            timeout=args.timeout,
            paths=args.path or None,
        )
        print(
            "Generated AI crawler policy rows: "
            f"{summary['policy_row_count']} findings={summary['finding_count']} blocked_visibility={summary['blocked_visibility_count']}"
        )
        for output in artifacts:
            print(output)
        return 0
    if command == "ai-crawler-draft":
        summary, artifacts = run_ai_crawler_owner_review_draft(root, base_url=args.site or args.base_url)
        print(f"Generated AI crawler owner-review drafts: {summary['status']}")
        for output in artifacts:
            print(output)
        return 0
    if command in {"gsc-sync", "google-index-status"}:
        rows = run_google_indexation_report(
            root=root,
            site_url=args.site_url,
            use_api=args.use_api,
            inspection_limit=args.inspection_limit,
            start_date=getattr(args, "start_date", ""),
            end_date=getattr(args, "end_date", ""),
        )
        print(f"Generated Google index status rows: {len(rows)}")
        return 0
    if command == "google-submit-sitemap":
        rows = run_google_indexation_report(
            root=root,
            site_url=args.site_url,
            use_api=args.use_api,
            submit_sitemap_url=args.sitemap_url,
        )
        print(f"Generated Google index status rows: {len(rows)}")
        return 0
    if command == "baidu-submit":
        rows = run_baidu_indexation_report(root=root, config_path=args.config, use_api=args.use_api, submit_limit=args.submit_limit)
        print(f"Generated Baidu index status rows: {len(rows)}")
        return 0
    if command == "indexnow-submit":
        rows = run_indexnow_report(root=root, use_api=args.use_api, submit_limit=args.submit_limit, action_type=args.action_type, verify_key=args.verify_key)
        print(f"Generated IndexNow status rows: {len(rows)}")
        return 0
    if command == "opportunities":
        scores = run_opportunity_finder(root)
        print(f"Generated opportunity scores: {len(scores)}")
        return 0
    if command == "content-quality-review":
        summary, artifacts = run_content_quality_review(root, draft_path=args.draft_path, target_url=args.target_url)
        print(f"Generated content quality review: {summary['status']} score={summary['total_score']}/{summary['max_score']}")
        for output in artifacts:
            print(output)
        return 0 if summary["status"] != "blocked_before_owner_review" else 1
    if command == "post-publish-feedback":
        summary, artifacts = run_post_publish_feedback(root, target_url=args.target_url)
        print(f"Generated post-publish feedback watchlist: {summary['status']} items={summary['watchlist_count']}")
        for output in artifacts:
            print(output)
        return 0 if summary["status"] != "blocked_missing_target_url" else 1
    if command == "daily-performance-digest":
        _summary, artifacts = run_daily_performance_digest(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "growth-data-health":
        _summary, artifacts = run_data_health_center(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "lead-quality-tracker":
        _summary, artifacts = run_lead_quality_tracker(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "lead-quality-editor":
        _summary, artifacts = run_lead_quality_editor(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "ads-decision-review":
        _summary, artifacts = run_ads_decision_review(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "growth-learning-memory":
        _summary, artifacts = run_growth_learning_memory(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "ads-asset-status-tracker":
        _summary, artifacts = run_ads_asset_status_tracker(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "growth-action-queue":
        _summary, artifacts = run_growth_action_queue(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "ai-search-monitor":
        _summary, artifacts = run_ai_search_monitor(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "competitor-gap-audit":
        _summary, artifacts = run_competitor_gap_audit(root, competitors_config=args.competitors_config)
        for output in artifacts:
            print(output)
        return 0
    if command == "competitor-weekly-monitor":
        _summary, artifacts = run_competitor_weekly_monitor(root, competitors_config=args.competitors_config)
        for output in artifacts:
            print(output)
        return 0
    if command == "local-citation-tracker":
        _summary, artifacts = run_local_citation_tracker(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "local-seo-verification":
        _summary, artifacts = run_local_seo_verification(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "real-proof-asset-request":
        _summary, artifacts = run_real_proof_asset_request(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "weekly-growth-control":
        _summary, artifacts = run_weekly_growth_control(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "growth-ops-audit":
        _summary, artifacts = run_growth_ops_audit(root)
        for output in artifacts:
            print(output)
        return 0
    if command == "content-calendar":
        result, artifacts = run_content_calendar(
            root,
            days=args.days,
            start_date=args.start_date,
            history_path=args.history_path,
            lookback=args.lookback,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "daily":
        outputs = run_daily(root)
        for output in outputs:
            print(output)
        return 0
    if command == "daily-automation":
        result, artifacts = run_daily_automation(
            root,
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
    if command == "automation-schedule":
        result, artifacts = run_automation_schedule(
            root,
            config_path=args.config_path,
            authorization_profile_path=args.authorization_profile_path,
            write_example=not args.no_write_example,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "automation-install-plan":
        summary, artifacts = run_automation_install_plan(
            root,
            schedule_plan_path=args.schedule_plan_path,
            install_kind=args.install_kind,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "automation_install_plan_ready_for_owner_review" else 1
    if command == "automation-completion-audit":
        summary, artifacts = run_automation_completion_audit(root)
        for output in artifacts:
            print(output)
        return 0 if summary["capability_ready"] else 1
    if command == "scheduled-publish-authorization":
        result, artifacts = run_scheduled_publish_authorization(root, profile_path=args.profile_path, write_example=not args.no_write_example)
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "scheduled-publish-runner":
        result, artifacts = run_scheduled_publish_runner(
            root,
            profile_path=args.profile_path,
            target_url=args.target_url,
            now=args.now,
            window_minutes=args.window_minutes,
            ignore_schedule_window=args.ignore_schedule_window,
            allow_duplicate_run=args.allow_duplicate_run,
            write_example=not args.no_write_example,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "scheduled-publish-orchestrator":
        result, artifacts = run_scheduled_publish_orchestrator(
            root,
            profile_path=args.profile_path,
            target_url=args.target_url,
            now=args.now,
            window_minutes=args.window_minutes,
            ignore_schedule_window=args.ignore_schedule_window,
            allow_duplicate_run=args.allow_duplicate_run,
            discover_research_sources=not args.skip_research_discovery,
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
            write_example=not args.no_write_example,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "scheduled-publish-postrun":
        result, artifacts = run_scheduled_publish_postrun(
            root,
            orchestration_path=args.orchestration_path,
            run_request_path=args.run_request_path,
            daily_run_path=args.daily_run_path,
            readiness_path=args.readiness_path,
            implementation_path=args.implementation_path,
            operator_path=args.operator_path,
            receipt_path=args.receipt_path,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "content-system":
        for output in run_content_system(root):
            print(output)
        return 0
    if command == "content-studio":
        summary, artifacts = run_content_studio(
            root,
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
        for output in artifacts:
            print(output)
        return 0 if not summary.get("automation_blockers") else 1
    if command == "content-studio-queue":
        _, artifacts = run_content_studio_queue(root, limit=args.limit)
        for output in artifacts:
            print(output)
        return 0
    if command == "content-studio-next":
        _, artifacts = run_content_studio_next(
            root,
            target_url=args.target_url,
            pipeline=args.pipeline,
            website_root=args.website_root,
            history_path=args.history_path,
            rebuild_queue=args.rebuild_queue,
            research_fetch_remote=not args.no_fetch_research_remote,
            research_search_provider=args.research_search_provider,
            research_search_feeds_config=args.research_search_feeds_config,
            owner_review_package=args.owner_review_package,
        )
        for output in artifacts:
            print(output)
        return 0
    if command == "content-studio-orchestrator":
        summary, artifacts = run_content_studio_orchestrator(
            root,
            config_path=args.config_path,
            now=args.now,
            window_minutes=args.window_minutes,
            ignore_schedule_window=args.ignore_schedule_window,
            allow_duplicate_run=args.allow_duplicate_run,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "content_studio_orchestration_completed" else 1
    if command == "content-studio-postrun":
        summary, artifacts = run_content_studio_postrun(
            root,
            orchestration_path=args.orchestration_path,
            next_run_path=args.next_run_path,
            queue_path=args.queue_path,
            history_path=args.history_path,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "content_studio_postrun_ready_for_owner_review" else 1
    if command == "content-studio-publish-candidate":
        summary, artifacts = run_content_studio_publish_candidate(
            root,
            postrun_path=args.postrun_path,
            content_studio_run_path=args.content_studio_run_path,
            website_root=args.website_root,
            target_url=args.target_url,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "content_studio_publish_candidate_waiting_owner_review" else 1
    if command == "content-studio-publish-prep":
        summary, artifacts = run_content_studio_publish_prep(
            root,
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
    if command == "content-studio-approval-packet":
        packet, artifacts = run_content_studio_approval_packet(
            root,
            prep_path=args.prep_path,
            candidate_path=args.candidate_path,
            media_plan_path=args.media_plan_path,
        )
        for output in artifacts:
            print(output)
        return 0 if packet["status"] == "approval_packet_waiting_owner_review" else 1
    if command == "content-studio-media-url-template":
        template, artifacts = run_content_studio_media_url_template(
            root,
            media_plan_path=args.media_plan_path,
            output_path=args.output_path,
            public_base_url=args.public_base_url,
        )
        for output in artifacts:
            print(output)
        return 0 if template["status"] == "uploaded_url_map_template_ready" else 1
    if command == "content-studio-media-ready-handoff":
        summary, artifacts = run_content_studio_media_ready_handoff(
            root,
            upload_plan_path=args.upload_plan_path,
            uploaded_url_map_path=args.uploaded_url_map_path,
            cms_payload_path=args.cms_payload_path,
            candidate_path=args.candidate_path,
            website_root=args.website_root,
            mode=args.mode,
            owner_approved=args.owner_approved,
            explicit_execution=args.explicit_execution,
            qa_passed=args.qa_passed,
            storage_ready=args.storage_ready,
            uploaded_confirmed=args.uploaded_confirmed,
            latest_research_verified=args.latest_research_verified,
            allow_blocked_plan=args.allow_blocked_plan,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "media_ready_handoff_waiting_owner_review" else 1
    if command == "content-studio-uploaded-url-map-draft":
        draft, artifacts = run_content_studio_uploaded_url_map_draft(
            root,
            template_path=args.template_path,
            output_path=args.output_path,
            validate_only=args.validate_only,
        )
        for output in artifacts:
            print(output)
        return 0 if draft["status"] == "uploaded_url_map_ready_for_confirmation" else 1
    if command == "content-studio-uploaded-url-map-editor":
        summary, artifacts = run_content_studio_uploaded_url_map_editor(root, source_path=args.source_path)
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "uploaded_url_map_editor_ready" else 1
    if command == "content-studio-uploaded-url-map-import":
        summary, artifacts = run_content_studio_uploaded_url_map_import(
            root,
            filled_map_path=args.filled_map_path,
            template_path=args.template_path,
            output_path=args.output_path,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "uploaded_url_map_imported_waiting_media_status" else 1
    if command == "content-studio-media-status":
        summary, artifacts = run_content_studio_media_status(
            root,
            uploaded_url_map_path=args.uploaded_url_map_path,
            template_path=args.template_path,
            media_url_map_path=args.media_url_map_path,
            media_ready_payload_path=args.media_ready_payload_path,
            publish_readiness_path=args.publish_readiness_path,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] in {"media_urls_ready_for_handoff", "media_ready_payload_present"} else 1
    if command == "content-studio-operator-ready-handoff":
        summary, artifacts = run_content_studio_operator_ready_handoff(
            root,
            uploaded_url_map_path=args.uploaded_url_map_path,
            cms_payload_path=args.cms_payload_path,
            website_root=args.website_root,
            mode=args.mode,
            owner_approved=args.owner_approved,
            explicit_execution=args.explicit_execution,
            qa_passed=args.qa_passed,
            storage_ready=args.storage_ready,
            uploaded_confirmed=args.uploaded_confirmed,
            latest_research_verified=args.latest_research_verified,
            allow_blocked_plan=args.allow_blocked_plan,
            allow_blocked_operator=args.allow_blocked_operator,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "content_studio_operator_ready_handoff_waiting_owner_review" else 1
    if command == "content-studio-media-review-package":
        summary, artifacts = run_content_studio_media_review_package(
            root,
            media_upload_plan_path=args.media_upload_plan_path,
            concept_manifest_path=args.concept_manifest_path,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "media_review_package_ready" else 1
    if command == "content-studio-owner-decision-editor":
        summary, artifacts = run_content_studio_owner_decision_editor(root, decision_path=args.decision_path)
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "owner_decision_editor_ready" else 1
    if command == "content-studio-owner-decision-import":
        summary, artifacts = run_content_studio_owner_decision_import(
            root,
            filled_decision_path=args.filled_decision_path,
            template_path=args.template_path,
            output_path=args.output_path,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "owner_decision_imported_waiting_status_check" else 1
    if command == "content-studio-owner-decision-status":
        summary, artifacts = run_content_studio_owner_decision_status(
            root,
            decision_path=args.decision_path,
            media_status_path=args.media_status_path,
            approval_packet_path=args.approval_packet_path,
            website_root=args.website_root,
        )
        for output in artifacts:
            print(output)
        return 0 if not summary.get("blockers") else 1
    if command == "content-studio-decision-orchestrator":
        summary, artifacts = run_content_studio_decision_orchestrator(
            root,
            decision_path=args.decision_path,
            media_status_path=args.media_status_path,
            approval_packet_path=args.approval_packet_path,
            uploaded_url_map_path=args.uploaded_url_map_path,
            candidate_path=args.candidate_path,
            website_root=args.website_root,
            mode=args.mode,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] != "decision_orchestration_blocked" else 1
    if command == "content-studio-owner-review-package":
        summary, artifacts = run_content_studio_owner_review_package(
            root,
            website_root=args.website_root,
            target_url=args.target_url,
            postrun_path=args.postrun_path,
            content_studio_run_path=args.content_studio_run_path,
            public_base_url=args.public_base_url,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "owner_review_package_ready" else 1
    if command == "service-pattern-brief":
        print(run_service_pattern_brief(root, target_url=args.target_url, today=args.date))
        return 0
    if command == "service-pattern-editor":
        for output in run_service_pattern_rich_editor(root, target_url=args.target_url, today=args.date).values():
            print(output)
        return 0
    if command == "service-pattern-publish-payload":
        for output in run_service_pattern_publish_payload(
            root,
            editor_payload_path=args.editor_payload_path,
            output_name=args.output_name,
        ).values():
            print(output)
        return 0
    if command == "service-pattern-media-assets":
        for output in run_service_pattern_media_assets(
            root,
            cms_payload_path=args.cms_payload_path,
            public_base_url=args.public_base_url,
            output_prefix=args.output_prefix,
        ).values():
            print(output)
        return 0
    if command == "service-pattern-package":
        _, artifacts = run_service_pattern_content_package(
            root,
            target_url=args.target_url,
            service_slug=args.service_slug,
            all_services=args.all,
            today=args.date,
            public_base_url=args.public_base_url,
        )
        for output in artifacts:
            print(output)
        return 0
    if command == "latest-research":
        result, artifacts = run_latest_research(root, target_url=args.target_url, queries=args.query, sources=args.source, timeout=args.timeout)
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "research-discovery":
        result, artifacts = run_research_discovery(
            root,
            target_url=args.target_url,
            config_path=args.config_path,
            fetch_remote=not args.no_fetch_remote,
            timeout=args.timeout,
            per_seed_limit=args.per_seed_limit,
            limit=args.limit,
            write_example=not args.no_write_example,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "research-search":
        result, artifacts = run_research_search(
            root,
            target_url=args.target_url,
            provider=args.provider,
            fetch_remote=not args.no_fetch_remote,
            timeout=args.timeout,
            limit=args.limit,
            market=args.market,
            language=args.language,
            feeds_config=args.feeds_config,
            write_feeds_example=not args.no_write_feeds_example,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "research-intake":
        result, artifacts = run_research_intake(
            root,
            candidates_path=args.candidates_path,
            target_url=args.target_url,
            limit=args.limit,
            min_score=args.min_score,
            allowed_source_types=args.allowed_source_type or None,
            timeout=args.timeout,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "rich-content":
        sources = [ResearchSource.from_cli(value) for value in args.source]
        print(write_rich_content_package(root, target_url=args.target_url, topic=args.topic, sources=sources, use_research_log=not args.no_use_research_log))
        return 0
    if command == "rich-blocks":
        for output in run_rich_blocks(root, target_url=args.target_url, draft_path=args.draft_path):
            print(output)
        return 0
    if command == "rich-editor":
        result, _ = run_rich_editor(
            root,
            blocks_path=args.blocks_path,
            media_plan_path=args.media_plan_path,
            concept_manifest_path=args.concept_manifest_path,
        )
        for output in result.artifacts.values():
            print(output)
        return 0 if result.ok else 1
    if command == "rich-editor-apply":
        result, _ = run_rich_editor_apply(root, editor_export_path=args.editor_export_path, cms_payload_path=args.cms_payload_path)
        for output in result.artifacts.values():
            print(output)
        return 0 if result.ok else 1
    if command == "media-assets":
        result, artifacts = run_media_assets(root, blocks_path=args.blocks_path, cms_payload_path=args.cms_payload_path, url_map_path=args.url_map_path)
        for output in result.artifacts.values():
            print(output)
        return 0 if result.ok else 1
    if command == "concept-assets":
        result, _ = run_concept_assets(root, media_plan_path=args.media_plan_path, asset_dir=args.asset_dir)
        for output in result.artifacts.values():
            print(output)
        return 0 if result.ok else 1
    if command == "media-upload-plan":
        result, _ = run_media_upload_plan(
            root,
            media_plan_path=args.media_plan_path,
            concept_manifest_path=args.concept_manifest_path,
            media_file_manifest_path=args.media_file_manifest_path,
            bucket=args.bucket,
            storage_prefix=args.storage_prefix,
            public_base_url=args.public_base_url,
        )
        for output in result.artifacts.values():
            print(output)
        return 0 if result.ok else 1
    if command == "media-upload-executor":
        result, _ = run_media_upload_executor(
            root,
            upload_plan_path=args.upload_plan_path,
            uploaded_url_map_path=args.uploaded_url_map_path,
            cms_payload_path=args.cms_payload_path,
            owner_approved=args.owner_approved,
            explicit_execution=args.explicit_execution,
            qa_passed=args.qa_passed,
            storage_ready=args.storage_ready,
            uploaded_confirmed=args.uploaded_confirmed,
        )
        for output in result.artifacts.values():
            print(output)
        return 0 if result.ok else 1
    if command == "media-url-map":
        result, _ = run_media_url_map(root, asset_dir=args.asset_dir, public_base_url=args.public_base_url, media_plan_path=args.media_plan_path)
        for output in result.artifacts.values():
            print(output)
        return 0 if result.ok else 1
    if command == "publish-queue":
        for output in run_publish_queue(root, website_root=args.website_root):
            print(output)
        return 0
    if command == "website-publish-adapter":
        result, artifacts = run_website_publish_adapter(root, website_root=args.website_root)
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-plan":
        result, artifacts = run_publish_plan(
            root,
            target_url=args.target_url,
            draft_path=args.draft_path,
            mode=args.mode,
            owner_approved=args.owner_approved,
            explicit_execution=args.explicit_execution,
            qa_passed=args.qa_passed,
            owner_input_resolved=args.owner_input_resolved,
            latest_research_verified=args.latest_research_verified,
            single_language_approved=args.single_language_approved,
            confirm_live=args.confirm_live,
            backup_path=args.backup_path,
            changelog_path=args.changelog_path,
            rollback_plan_path=args.rollback_plan_path,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-executor":
        result, artifacts = run_publish_executor(
            root,
            mode=args.mode,
            plan_path=args.plan_path,
            cms_payload_path=args.cms_payload_path,
            next_status=args.next_status,
            owner_approved=args.owner_approved,
            explicit_execution=args.explicit_execution,
            qa_passed=args.qa_passed,
            media_ready=args.media_ready,
            allow_blocked_plan=args.allow_blocked_plan,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-readiness":
        result, artifacts = run_publish_readiness(
            root,
            publish_plan_path=args.publish_plan_path,
            cms_request_path=args.cms_request_path,
            media_request_path=args.media_request_path,
            media_url_map_path=args.media_url_map_path,
            media_ready_payload_path=args.media_ready_payload_path,
            research_log_path=args.research_log_path,
            queue_path=args.queue_path,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-bundle":
        result, artifacts = run_publish_bundle(root, readiness_path=args.readiness_path, cms_request_path=args.cms_request_path)
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-approved-executor":
        result, artifacts = run_publish_approved_executor(
            root,
            bundle_path=args.bundle_path,
            mode=args.mode,
            owner_approved=args.owner_approved,
            explicit_execution=args.explicit_execution,
            qa_passed=args.qa_passed,
            backup_path=args.backup_path,
            changelog_path=args.changelog_path,
            rollback_plan_path=args.rollback_plan_path,
            confirm_live=args.confirm_live,
            allowed_target_urls=args.allowed_target_url,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-approved-execution-input":
        result, artifacts = run_publish_approved_execution_input(
            root,
            operator_path=args.operator_path,
            helper_call_path=args.helper_call_path,
            adapter_path=args.adapter_path,
            allow_blocked_operator=args.allow_blocked_operator,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-cms-write-executor":
        summary, artifacts = run_publish_cms_write_executor(
            root,
            execution_input_path=args.execution_input_path,
            mode=args.mode,
            confirm_write=args.confirm_write,
            allowed_target_urls=args.allowed_target_url,
            require_env=args.require_env,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] in {"cms_write_executor_ready_dry_run", "cms_write_executed_waiting_post_write_qa"} else 1
    if command == "publish-media-upload-executor":
        summary, artifacts = run_publish_media_upload_executor(
            root,
            upload_plan_path=args.upload_plan_path,
            mode=args.mode,
            confirm_upload=args.confirm_upload,
            allowed_bucket=args.allowed_bucket,
            require_env=args.require_env,
            create_media_records=not args.no_create_media_records,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] in {"media_upload_executor_ready_dry_run", "media_uploaded_waiting_media_ready_handoff"} else 1
    if command == "publish-post-media-handoff":
        summary, artifacts = run_publish_post_media_handoff(
            root,
            uploaded_url_map_path=args.uploaded_url_map_path,
            website_root=args.website_root,
            allowed_target_urls=args.allowed_target_url,
            allow_blocked_operator=not args.strict_operator,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "post_media_handoff_ready_for_owner_review" else 1
    if command == "publish-implementation-package":
        result, artifacts = run_publish_implementation_package(
            root,
            execution_record_path=args.execution_record_path,
            website_root=args.website_root,
            adapter_path=args.adapter_path,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-operator-package":
        result, artifacts = run_publish_operator_package(
            root,
            implementation_path=args.implementation_path,
            helper_call_path=args.helper_call_path,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "publish-operator-ready-handoff":
        summary, artifacts = run_publish_operator_ready_handoff(
            root,
            website_root=args.website_root,
            mode=args.mode,
            owner_approved=args.owner_approved,
            explicit_execution=args.explicit_execution,
            qa_passed=args.qa_passed,
            media_ready=args.media_ready,
            latest_research_verified=args.latest_research_verified,
            allow_blocked_plan=args.allow_blocked_plan,
            allow_blocked_operator=args.allow_blocked_operator,
            backup_path=args.backup_path,
            changelog_path=args.changelog_path,
            rollback_plan_path=args.rollback_plan_path,
            confirm_live=args.confirm_live,
            allowed_target_urls=args.allowed_target_url,
        )
        for output in artifacts:
            print(output)
        return 0 if summary["status"] == "operator_ready_handoff_waiting_owner_review" else 1
    if command == "publish-execution-receipt":
        result, artifacts = run_publish_execution_receipt(
            root,
            operator_path=args.operator_path,
            execution_result_path=args.execution_result_path,
            write_example=not args.no_write_example,
        )
        for output in artifacts:
            print(output)
        return 0 if result.ok else 1
    if command == "entity":
        print(run_entity_profile(root))
        return 0
    if command == "geo-ai":
        print(run_geo_ai_report(root))
        return 0
    if command == "local-seo":
        print(run_local_seo_report(root))
        return 0
    if command == "schema":
        print(write_schema_recommendations(root))
        print(run_schema_validation_report(root))
        return 0
    if command == "multilingual":
        print(write_language_pairs(root))
        print(run_multilingual_report(root))
        return 0
    if command == "image-seo":
        print(write_visual_briefs(root))
        print(run_image_seo_report(root))
        return 0
    if command == "qa":
        result = run_qa(
            root,
            target_url=args.target_url,
            mode=args.mode,
            backup_path=args.backup_path,
            rollback_plan_path=args.rollback_plan_path,
            content_path=args.content_path,
        )
        print(write_qa_report(root, result))
        return 0 if result.ok else 1
    if command == "apply":
        return run_apply(root, args)
    parser.error(f"Unhandled command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
