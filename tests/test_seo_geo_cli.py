from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_cli


cli = load_cli()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_minimal_workspace(tmp_path: Path) -> None:
    write(tmp_path / "seo-workspace" / "data" / "brand-profile.md", "- Company name: FLASH CAST SDN. BHD.\n- Website: https://flashcast.com.my/\n")
    write(tmp_path / "seo-workspace" / "data" / "services.md", "# Services\n\n### Residential Renovation\n\n- Existing URL: https://flashcast.com.my/en/services/renovation\n- Description: Home renovation.\n")
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        "https://flashcast.com.my/zh/services/renovation,zh,service,200,yes,yes,,https://flashcast.com.my/zh/services/renovation,yes,yes,住宅装修,住宅装修,住宅装修,300,2,2,WebPage,0,0,,yes,\n"
        "https://flashcast.com.my/en/services/renovation,en,service,200,yes,yes,,https://flashcast.com.my/en/services/renovation,yes,yes,Residential Renovation,Residential Renovation,Residential Renovation,300,2,2,WebPage,0,0,,yes,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv",
        "url,keyword,language,page_type,service,location,total_score,task_type,positive_events,penalty_events\n"
        "https://flashcast.com.my/zh/services/renovation,住宅装修 吉隆坡,zh,service,住宅装修,Kuala Lumpur,20,high-commercial-intent page optimization,,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "住宅装修 吉隆坡,commercial,ready,/zh/services/renovation,/zh/services/renovation,service,high,住宅装修,Kuala Lumpur,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Residential renovation,/en/locations/kuala-lumpur,,,yes\n",
    )
    write(
        tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-test-content-brief.md",
        "中文页面建议文案\n概念设计\n英文页面建议文案\nrendering concept\nCTA: 获取免费报价\n`/zh/quote` `/en/quote`\n",
    )
    write(tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-schema-report.md", "Errors: 0\nStatus: PASS\n")


def test_cli_parser_includes_required_commands():
    parser = cli.build_parser()

    args = parser.parse_args(["validate"])
    assert args.command == "validate"
    args = parser.parse_args(["crawl", "--site", "https://example.com"])
    assert args.command == "crawl"
    assert args.site == "https://example.com"
    args = parser.parse_args(["technical-findings", "--inventory-path", "seo-workspace/data/url-inventory.csv"])
    assert args.command == "technical-findings"
    assert args.inventory_path == "seo-workspace/data/url-inventory.csv"
    args = parser.parse_args(["ai-crawler-policy", "--site", "https://example.com", "--path", "/", "--path", "/en/"])
    assert args.command == "ai-crawler-policy"
    assert args.site == "https://example.com"
    assert args.path == ["/", "/en/"]
    args = parser.parse_args(["ai-crawler-draft", "--site", "https://example.com"])
    assert args.command == "ai-crawler-draft"
    assert args.site == "https://example.com"
    args = parser.parse_args(["content-quality-review", "--draft-path", "seo-workspace/drafts/example.md"])
    assert args.command == "content-quality-review"
    assert args.draft_path == "seo-workspace/drafts/example.md"
    args = parser.parse_args(["post-publish-feedback", "--target-url", "https://example.com/en/services/kitchen"])
    assert args.command == "post-publish-feedback"
    assert args.target_url == "https://example.com/en/services/kitchen"
    args = parser.parse_args(["apply", "--plan", "plan.md", "--mode", "pr"])
    assert args.command == "apply"
    assert args.mode == "pr"
    args = parser.parse_args(["content-system"])
    assert args.command == "content-system"
    args = parser.parse_args(["daily-performance-digest"])
    assert args.command == "daily-performance-digest"
    args = parser.parse_args(["ai-search-monitor"])
    assert args.command == "ai-search-monitor"
    args = parser.parse_args(["competitor-gap-audit", "--competitors-config", "seo-workspace/config/competitors.example.yml"])
    assert args.command == "competitor-gap-audit"
    assert args.competitors_config == "seo-workspace/config/competitors.example.yml"
    args = parser.parse_args(["local-citation-tracker"])
    assert args.command == "local-citation-tracker"
    args = parser.parse_args(["real-proof-asset-request"])
    assert args.command == "real-proof-asset-request"
    args = parser.parse_args(["growth-ops-audit"])
    assert args.command == "growth-ops-audit"
    args = parser.parse_args(
        [
            "content-studio",
            "--target-url",
            "https://flashcast.com.my/en/services/kitchen",
            "--pipeline",
            "publish-prep",
            "--no-fetch-research-remote",
        ]
    )
    assert args.command == "content-studio"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.pipeline == "publish-prep"
    assert args.no_fetch_research_remote is True
    assert args.research_search_provider == "hybrid-rss"
    assert args.research_search_feeds_config == "seo-workspace/config/research-search-feeds.example.yml"
    args = parser.parse_args(["content-studio-queue", "--limit", "10"])
    assert args.command == "content-studio-queue"
    assert args.limit == 10
    args = parser.parse_args(["content-studio-next", "--rebuild-queue", "--no-fetch-research-remote", "--owner-review-package"])
    assert args.command == "content-studio-next"
    assert args.rebuild_queue is True
    assert args.no_fetch_research_remote is True
    assert args.research_search_provider == "hybrid-rss"
    assert args.research_search_feeds_config == "seo-workspace/config/research-search-feeds.example.yml"
    assert args.owner_review_package is True
    args = parser.parse_args(["content-studio-orchestrator", "--ignore-schedule-window", "--allow-duplicate-run"])
    assert args.command == "content-studio-orchestrator"
    assert args.ignore_schedule_window is True
    assert args.allow_duplicate_run is True
    args = parser.parse_args(["content-studio-postrun", "--orchestration-path", "seo-workspace/data/content-studio-orchestration.json"])
    assert args.command == "content-studio-postrun"
    assert args.orchestration_path == "seo-workspace/data/content-studio-orchestration.json"
    args = parser.parse_args(["content-studio-publish-candidate", "--website-root", "/tmp/site"])
    assert args.command == "content-studio-publish-candidate"
    assert args.website_root == "/tmp/site"
    args = parser.parse_args(["content-studio-publish-prep", "--website-root", "/tmp/site", "--allow-blocked-plan"])
    assert args.command == "content-studio-publish-prep"
    assert args.website_root == "/tmp/site"
    assert args.allow_blocked_plan is True
    args = parser.parse_args(["content-studio-approval-packet", "--prep-path", "seo-workspace/data/content-studio-publish-prep.json"])
    assert args.command == "content-studio-approval-packet"
    assert args.prep_path == "seo-workspace/data/content-studio-publish-prep.json"
    args = parser.parse_args(["content-studio-media-url-template", "--public-base-url", "https://cdn.example.com"])
    assert args.command == "content-studio-media-url-template"
    assert args.public_base_url == "https://cdn.example.com"
    args = parser.parse_args(
        [
            "content-studio-media-ready-handoff",
            "--uploaded-url-map-path",
            "seo-workspace/data/uploaded-url-map.json",
            "--owner-approved",
            "--explicit-execution",
            "--qa-passed",
            "--storage-ready",
            "--uploaded-confirmed",
        ]
    )
    assert args.command == "content-studio-media-ready-handoff"
    assert args.uploaded_url_map_path == "seo-workspace/data/uploaded-url-map.json"
    assert args.owner_approved is True
    assert args.uploaded_confirmed is True
    args = parser.parse_args(["content-studio-uploaded-url-map-draft", "--validate-only"])
    assert args.command == "content-studio-uploaded-url-map-draft"
    assert args.validate_only is True
    args = parser.parse_args(["content-studio-uploaded-url-map-editor", "--source-path", "seo-workspace/data/uploaded-url-map.json"])
    assert args.command == "content-studio-uploaded-url-map-editor"
    assert args.source_path == "seo-workspace/data/uploaded-url-map.json"
    args = parser.parse_args(["content-studio-uploaded-url-map-import", "--filled-map-path", "seo-workspace/data/uploaded-url-map.filled.json"])
    assert args.command == "content-studio-uploaded-url-map-import"
    assert args.filled_map_path == "seo-workspace/data/uploaded-url-map.filled.json"
    args = parser.parse_args(["content-studio-media-status", "--uploaded-url-map-path", "seo-workspace/data/uploaded-url-map.json"])
    assert args.command == "content-studio-media-status"
    assert args.uploaded_url_map_path == "seo-workspace/data/uploaded-url-map.json"
    args = parser.parse_args(
        [
            "content-studio-operator-ready-handoff",
            "--uploaded-url-map-path",
            "seo-workspace/data/uploaded-url-map.json",
            "--website-root",
            "/tmp/site",
            "--allow-blocked-operator",
        ]
    )
    assert args.command == "content-studio-operator-ready-handoff"
    assert args.uploaded_url_map_path == "seo-workspace/data/uploaded-url-map.json"
    assert args.website_root == "/tmp/site"
    assert args.allow_blocked_operator is True
    args = parser.parse_args(["content-studio-media-review-package", "--media-upload-plan-path", "seo-workspace/data/media-upload-plan.json"])
    assert args.command == "content-studio-media-review-package"
    assert args.media_upload_plan_path == "seo-workspace/data/media-upload-plan.json"
    args = parser.parse_args(["content-studio-owner-review-package", "--website-root", "/tmp/site"])
    assert args.command == "content-studio-owner-review-package"
    assert args.website_root == "/tmp/site"
    args = parser.parse_args(["publish-approved-execution-input", "--allow-blocked-operator"])
    assert args.command == "publish-approved-execution-input"
    assert args.allow_blocked_operator is True
    args = parser.parse_args(
        [
            "publish-cms-write-executor",
            "--mode",
            "live",
            "--confirm-write",
            "--allowed-target-url",
            "https://flashcast.com.my/en/services/kitchen",
        ]
    )
    assert args.command == "publish-cms-write-executor"
    assert args.mode == "live"
    assert args.confirm_write is True
    assert args.allowed_target_url == ["https://flashcast.com.my/en/services/kitchen"]
    args = parser.parse_args(
        [
            "publish-media-upload-executor",
            "--mode",
            "live",
            "--confirm-upload",
            "--allowed-bucket",
            "site-images",
            "--no-create-media-records",
        ]
    )
    assert args.command == "publish-media-upload-executor"
    assert args.mode == "live"
    assert args.confirm_upload is True
    assert args.allowed_bucket == "site-images"
    assert args.no_create_media_records is True
    args = parser.parse_args(
        [
            "publish-post-media-handoff",
            "--uploaded-url-map-path",
            "seo-workspace/data/uploaded-url-map.json",
            "--allowed-target-url",
            "https://flashcast.com.my/en/services/kitchen",
        ]
    )
    assert args.command == "publish-post-media-handoff"
    assert args.uploaded_url_map_path == "seo-workspace/data/uploaded-url-map.json"
    assert args.allowed_target_url == ["https://flashcast.com.my/en/services/kitchen"]
    args = parser.parse_args(["publish-operator-ready-handoff", "--website-root", "/tmp/site", "--allow-blocked-operator"])
    assert args.command == "publish-operator-ready-handoff"
    assert args.website_root == "/tmp/site"
    assert args.allow_blocked_operator is True
    args = parser.parse_args(["service-pattern-brief", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--date", "2026-06-11"])
    assert args.command == "service-pattern-brief"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.date == "2026-06-11"
    args = parser.parse_args(["service-pattern-editor", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--date", "2026-06-11"])
    assert args.command == "service-pattern-editor"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    args = parser.parse_args(["service-pattern-publish-payload", "--editor-payload-path", "seo-workspace/data/kitchen-service-pattern-rich-editor-payload.json"])
    assert args.command == "service-pattern-publish-payload"
    assert args.editor_payload_path == "seo-workspace/data/kitchen-service-pattern-rich-editor-payload.json"
    args = parser.parse_args(["service-pattern-media-assets", "--cms-payload-path", "seo-workspace/data/kitchen-service-pattern-cms-payload.editor-applied.json"])
    assert args.command == "service-pattern-media-assets"
    assert args.cms_payload_path == "seo-workspace/data/kitchen-service-pattern-cms-payload.editor-applied.json"
    args = parser.parse_args(["service-pattern-package", "--service-slug", "kitchen", "--date", "2026-06-11"])
    assert args.command == "service-pattern-package"
    assert args.service_slug == "kitchen"
    assert args.date == "2026-06-11"
    args = parser.parse_args(["content-calendar", "--days", "7", "--start-date", "2026-06-15", "--history-path", "seo-workspace/data/history.csv", "--lookback", "5"])
    assert args.command == "content-calendar"
    assert args.days == 7
    assert args.start_date == "2026-06-15"
    assert args.history_path == "seo-workspace/data/history.csv"
    assert args.lookback == 5
    args = parser.parse_args(["automation-install-plan", "--install-kind", "both", "--schedule-plan-path", "seo-workspace/data/daily-automation-schedule-plan.json"])
    assert args.command == "automation-install-plan"
    assert args.install_kind == "both"
    assert args.schedule_plan_path == "seo-workspace/data/daily-automation-schedule-plan.json"
    args = parser.parse_args(["automation-completion-audit"])
    assert args.command == "automation-completion-audit"
    args = parser.parse_args(["latest-research", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--query", "kitchen renovation malaysia", "--source", "official|https://example.com|Use note|Boundary|query text"])
    assert args.command == "latest-research"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.query == ["kitchen renovation malaysia"]
    assert args.source
    args = parser.parse_args(["research-discovery", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--no-fetch-remote"])
    assert args.command == "research-discovery"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.no_fetch_remote is True
    args = parser.parse_args(["research-search", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--no-fetch-remote", "--market", "MY", "--language", "en", "--provider", "trusted-rss", "--feeds-config", "seo-workspace/config/research-search-feeds.yml"])
    assert args.command == "research-search"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.no_fetch_remote is True
    assert args.market == "MY"
    assert args.language == "en"
    assert args.provider == "trusted-rss"
    assert args.feeds_config == "seo-workspace/config/research-search-feeds.yml"
    args = parser.parse_args(["research-intake", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--min-score", "70", "--allowed-source-type", "official"])
    assert args.command == "research-intake"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.min_score == 70
    assert args.allowed_source_type == ["official"]
    args = parser.parse_args(["rich-content", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--source", "official|Title|https://example.com|Publisher|2026-06-10|Use note"])
    assert args.command == "rich-content"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.source
    args = parser.parse_args(["rich-content", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--no-use-research-log"])
    assert args.no_use_research_log is True
    args = parser.parse_args(["rich-blocks", "--target-url", "https://flashcast.com.my/en/services/kitchen"])
    assert args.command == "rich-blocks"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    args = parser.parse_args(["rich-editor", "--blocks-path", "seo-workspace/data/rich-content-blocks.json"])
    assert args.command == "rich-editor"
    assert args.blocks_path == "seo-workspace/data/rich-content-blocks.json"
    args = parser.parse_args(["rich-editor-apply", "--editor-export-path", "seo-workspace/data/edited-export.json"])
    assert args.command == "rich-editor-apply"
    assert args.editor_export_path == "seo-workspace/data/edited-export.json"
    args = parser.parse_args(["media-assets", "--url-map-path", "seo-workspace/data/media-url-map.json"])
    assert args.command == "media-assets"
    assert args.url_map_path == "seo-workspace/data/media-url-map.json"
    args = parser.parse_args(["concept-assets", "--asset-dir", "seo-workspace/media/generated"])
    assert args.command == "concept-assets"
    assert args.asset_dir == "seo-workspace/media/generated"
    args = parser.parse_args(["media-upload-plan", "--bucket", "site-images", "--storage-prefix", "media/seo-generated"])
    assert args.command == "media-upload-plan"
    assert args.bucket == "site-images"
    assert args.storage_prefix == "media/seo-generated"
    args = parser.parse_args(["media-upload-executor", "--owner-approved", "--explicit-execution", "--qa-passed", "--storage-ready"])
    assert args.command == "media-upload-executor"
    assert args.owner_approved is True
    assert args.storage_ready is True
    args = parser.parse_args(["media-url-map", "--asset-dir", "seo-workspace/media/generated", "--public-base-url", "https://cdn.example.com/media"])
    assert args.command == "media-url-map"
    assert args.asset_dir == "seo-workspace/media/generated"
    assert args.public_base_url == "https://cdn.example.com/media"
    args = parser.parse_args(["publish-queue", "--website-root", "/tmp/site"])
    assert args.command == "publish-queue"
    assert args.website_root == "/tmp/site"
    args = parser.parse_args(["website-publish-adapter", "--website-root", "/tmp/site"])
    assert args.command == "website-publish-adapter"
    assert args.website_root == "/tmp/site"
    args = parser.parse_args(["publish-plan", "--target-url", "https://flashcast.com.my/en/services/kitchen", "--owner-approved", "--explicit-execution", "--qa-passed"])
    assert args.command == "publish-plan"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.owner_approved
    assert args.explicit_execution
    assert args.qa_passed
    args = parser.parse_args(["publish-executor", "--owner-approved", "--explicit-execution", "--qa-passed", "--media-ready"])
    assert args.command == "publish-executor"
    assert args.media_ready
    args = parser.parse_args(["publish-readiness", "--media-url-map-path", "seo-workspace/data/media-url-map.json"])
    assert args.command == "publish-readiness"
    assert args.media_url_map_path == "seo-workspace/data/media-url-map.json"
    args = parser.parse_args(["publish-bundle", "--readiness-path", "seo-workspace/data/publish-readiness.json"])
    assert args.command == "publish-bundle"
    assert args.readiness_path == "seo-workspace/data/publish-readiness.json"
    args = parser.parse_args(
        [
            "publish-approved-executor",
            "--bundle-path",
            "seo-workspace/data/publish-execution-bundle.json",
            "--owner-approved",
            "--explicit-execution",
            "--qa-passed",
            "--allowed-target-url",
            "https://flashcast.com.my/en/services/kitchen",
        ]
    )
    assert args.command == "publish-approved-executor"
    assert args.bundle_path == "seo-workspace/data/publish-execution-bundle.json"
    assert args.owner_approved
    assert args.allowed_target_url == ["https://flashcast.com.my/en/services/kitchen"]
    args = parser.parse_args(
        [
            "publish-implementation-package",
            "--execution-record-path",
            "seo-workspace/data/publish-approved-execution-record.json",
            "--website-root",
            "/tmp/site",
            "--adapter-path",
            "seo-workspace/data/website-publish-adapter.json",
        ]
    )
    assert args.command == "publish-implementation-package"
    assert args.execution_record_path == "seo-workspace/data/publish-approved-execution-record.json"
    assert args.website_root == "/tmp/site"
    assert args.adapter_path == "seo-workspace/data/website-publish-adapter.json"
    args = parser.parse_args(
        [
            "publish-operator-package",
            "--implementation-path",
            "seo-workspace/data/publish-implementation-package.json",
            "--helper-call-path",
            "seo-workspace/data/publish-admin-helper-call.json",
        ]
    )
    assert args.command == "publish-operator-package"
    assert args.implementation_path == "seo-workspace/data/publish-implementation-package.json"
    assert args.helper_call_path == "seo-workspace/data/publish-admin-helper-call.json"
    args = parser.parse_args(
        [
            "publish-execution-receipt",
            "--operator-path",
            "seo-workspace/data/publish-operator-command.json",
            "--execution-result-path",
            "seo-workspace/data/publish-execution-result.json",
            "--no-write-example",
        ]
    )
    assert args.command == "publish-execution-receipt"
    assert args.operator_path == "seo-workspace/data/publish-operator-command.json"
    assert args.execution_result_path == "seo-workspace/data/publish-execution-result.json"
    assert args.no_write_example is True
    args = parser.parse_args(["--config", "seo-workspace/config/seo-geo-config.example.yml", "config"])
    assert args.command == "config"
    assert args.config == "seo-workspace/config/seo-geo-config.example.yml"
    args = parser.parse_args(
        [
            "daily-automation",
            "--pipeline",
            "publish-prep",
            "--website-root",
            "/tmp/site",
            "--no-fetch-research-remote",
            "--research-search-provider",
            "hybrid-rss",
            "--research-search-feeds-config",
            "seo-workspace/config/research-search-feeds.example.yml",
            "--research-timeout",
            "3",
            "--research-limit",
            "7",
            "--no-auto-accept-research-sources",
            "--research-intake-min-score",
            "75",
            "--research-intake-limit",
            "1",
            "--authorization-profile-path",
            "seo-workspace/config/scheduled-publish-authorization.yml",
        ]
    )
    assert args.command == "daily-automation"
    assert args.pipeline == "publish-prep"
    assert args.website_root == "/tmp/site"
    assert args.no_fetch_research_remote is True
    assert args.research_search_provider == "hybrid-rss"
    assert args.research_search_feeds_config == "seo-workspace/config/research-search-feeds.example.yml"
    assert args.research_timeout == 3
    assert args.research_limit == 7
    assert args.no_auto_accept_research_sources is True
    assert args.research_intake_min_score == 75
    assert args.research_intake_limit == 1
    assert args.authorization_profile_path == "seo-workspace/config/scheduled-publish-authorization.yml"
    args = parser.parse_args(
        [
            "automation-schedule",
            "--config-path",
            "seo-workspace/config/daily-automation.yml",
            "--authorization-profile-path",
            "seo-workspace/config/scheduled-publish-authorization.yml",
        ]
    )
    assert args.command == "automation-schedule"
    assert args.config_path == "seo-workspace/config/daily-automation.yml"
    assert args.authorization_profile_path == "seo-workspace/config/scheduled-publish-authorization.yml"
    args = parser.parse_args(["scheduled-publish-authorization", "--profile-path", "seo-workspace/config/scheduled-publish-authorization.yml"])
    assert args.command == "scheduled-publish-authorization"
    assert args.profile_path == "seo-workspace/config/scheduled-publish-authorization.yml"
    args = parser.parse_args(
        [
            "scheduled-publish-runner",
            "--profile-path",
            "seo-workspace/config/scheduled-publish-authorization.yml",
            "--target-url",
            "https://flashcast.com.my/en/services/kitchen",
            "--now",
            "2026-06-15T01:00:00+00:00",
            "--window-minutes",
            "30",
            "--ignore-schedule-window",
            "--allow-duplicate-run",
        ]
    )
    assert args.command == "scheduled-publish-runner"
    assert args.profile_path == "seo-workspace/config/scheduled-publish-authorization.yml"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.now == "2026-06-15T01:00:00+00:00"
    assert args.window_minutes == 30
    assert args.ignore_schedule_window is True
    assert args.allow_duplicate_run is True
    args = parser.parse_args(
        [
            "scheduled-publish-orchestrator",
            "--profile-path",
            "seo-workspace/config/scheduled-publish-authorization.yml",
            "--target-url",
            "https://flashcast.com.my/en/services/kitchen",
            "--now",
            "2026-06-15T01:00:00+00:00",
            "--no-fetch-research-remote",
            "--research-search-provider",
            "trusted-rss",
            "--research-timeout",
            "4",
            "--research-limit",
            "6",
        ]
    )
    assert args.command == "scheduled-publish-orchestrator"
    assert args.profile_path == "seo-workspace/config/scheduled-publish-authorization.yml"
    assert args.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert args.no_fetch_research_remote is True
    assert args.research_search_provider == "trusted-rss"
    assert args.research_timeout == 4
    assert args.research_limit == 6
    args = parser.parse_args(
        [
            "scheduled-publish-postrun",
            "--orchestration-path",
            "seo-workspace/data/scheduled-publish-orchestration.json",
            "--daily-run-path",
            "seo-workspace/data/daily-automation-run.json",
            "--operator-path",
            "seo-workspace/data/publish-operator-command.json",
            "--receipt-path",
            "seo-workspace/data/publish-execution-receipt.json",
        ]
    )
    assert args.command == "scheduled-publish-postrun"
    assert args.orchestration_path == "seo-workspace/data/scheduled-publish-orchestration.json"
    assert args.daily_run_path == "seo-workspace/data/daily-automation-run.json"
    assert args.operator_path == "seo-workspace/data/publish-operator-command.json"
    assert args.receipt_path == "seo-workspace/data/publish-execution-receipt.json"


def test_cli_qa_runs_and_writes_report(tmp_path):
    seed_minimal_workspace(tmp_path)

    exit_code = cli.main(["--root", str(tmp_path), "qa"])

    assert exit_code == 0
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-prepublish-qa-report.md").exists()


def test_cli_apply_live_blocks_without_preconditions(tmp_path):
    seed_minimal_workspace(tmp_path)
    plan = tmp_path / "seo-workspace" / "drafts" / "plan.md"
    plan.write_text("plan", encoding="utf-8")

    exit_code = cli.main(["--root", str(tmp_path), "apply", "--plan", str(plan), "--mode", "live", "--confirm-live"])

    report = tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-apply-preflight-report.md"
    assert exit_code == 1
    assert report.exists()
    assert "Live mode blocked" in report.read_text(encoding="utf-8")
