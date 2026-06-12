from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_scheduled_publish_orchestrator


scheduled_publish_orchestrator = load_scheduled_publish_orchestrator()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"
SCHEDULED_NOW = "2026-06-15T01:00:00+00:00"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def future_date() -> str:
    return (dt.date.today() + dt.timedelta(days=30)).isoformat()


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "brand-profile.md",
        "- Brand name: FLASH CAST\n- Company name: FLASH CAST SDN. BHD.\n- Website: https://flashcast.com.my/\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen renovation malaysia,commercial,ready,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen renovation,Kuala Lumpur,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        f"{TARGET_URL},en,service,200,yes,yes,,{TARGET_URL},yes,yes,Kitchen Renovation,Kitchen renovation,Kitchen Renovation,500,1,1,WebPage,1,0,,yes,\n"
        f"{PAIRED_URL},zh,service,200,yes,yes,,{PAIRED_URL},yes,yes,厨房装修,厨房装修,厨房装修,500,1,1,WebPage,1,0,,yes,\n",
    )
    write(tmp_path / "seo-workspace" / "data" / "internal-links.csv", "source_url,target_url,anchor_text,context,priority\n")
    write(tmp_path / "seo-workspace" / "data" / "case-studies.csv", "project_name,service,related_url,location,scope,result\n")
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Kitchen renovation,/en/locations/kuala-lumpur,,,yes\n",
    )


def ready_profile(tmp_path: Path) -> Path:
    website_root = tmp_path / "website"
    website_root.mkdir(parents=True, exist_ok=True)
    profile_path = tmp_path / "seo-workspace" / "config" / "scheduled-publish-authorization.yml"
    write(
        profile_path,
        f"""automation_id: "flash-cast-daily-seo-geo"
enabled: true
authorization_profile_id: "SCHEDULED-PUBLISH-PROFILE-TEST"
owner_authorization_id: "OWNER-APPROVED-SCHEDULED-PUBLISH-TEST"
authorized_pipeline: "publish-prep"
mode: "dry-run"
timezone: "Asia/Kuala_Lumpur"
local_time: "09:00"
allowed_weekdays:
  - "Mon"
allowed_target_urls:
  - "{TARGET_URL}"
  - "{PAIRED_URL}"
website_root: "{website_root}"
max_pages_per_run: 1
language_scope: "bilingual_pair_required"
expires_at: "{future_date()}"
require_owner_approved: true
require_explicit_execution: true
require_qa_passed: true
require_media_ready: true
require_storage_ready: true
require_backup: true
require_changelog: true
require_rollback: true
require_confirm_live: false
safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
""",
    )
    return profile_path


def test_scheduled_publish_orchestrator_blocks_when_runner_not_ready(tmp_path):
    seed_workspace(tmp_path)

    result, artifacts = scheduled_publish_orchestrator.run_scheduled_publish_orchestrator(
        tmp_path,
        now=SCHEDULED_NOW,
        research_fetch_remote=False,
    )

    assert not result.ok
    assert result.status == "blocked_before_scheduled_publish_orchestration"
    assert any("profile missing" in blocker for blocker in result.blockers)
    orchestration_path, report_path = artifacts
    assert orchestration_path.exists()
    assert report_path.exists()
    payload = json.loads(orchestration_path.read_text(encoding="utf-8"))
    assert payload["orchestration"]["daily_automation_summary"]["status"] == "not_executed"
    assert payload["no_live_actions_executed"] is True


def test_scheduled_publish_orchestrator_runs_safe_publish_prep_when_runner_ready(tmp_path):
    seed_workspace(tmp_path)
    profile_path = ready_profile(tmp_path)

    result, artifacts = scheduled_publish_orchestrator.run_scheduled_publish_orchestrator(
        tmp_path,
        profile_path=str(profile_path),
        now=SCHEDULED_NOW,
        research_fetch_remote=False,
        research_write_example=False,
        write_example=False,
    )

    assert result.ok
    assert result.status == "scheduled_publish_safe_prep_completed"
    orchestration = result.orchestration
    assert orchestration["daily_automation_executed"] is True
    assert orchestration["research_search_provider"] == "hybrid-rss"
    assert orchestration["research_search_feeds_config"] == "seo-workspace/config/research-search-feeds.example.yml"
    assert orchestration["daily_automation_summary"]["pipeline"] == "publish-prep"
    assert orchestration["daily_automation_summary"]["status"] == "publish_prep_blocked_before_owner_authorization"
    assert orchestration["no_publish_executed"] is True
    assert orchestration["no_live_actions_executed"] is True
    orchestration_path, report_path = artifacts
    payload = json.loads(orchestration_path.read_text(encoding="utf-8"))
    assert payload["orchestration"]["action"] == "scheduled_publish_orchestration_safe_prep_only"
    assert (tmp_path / "seo-workspace" / "data" / "daily-automation-run.json").exists()
    report = report_path.read_text(encoding="utf-8")
    assert "safe orchestration only" in report
    assert "Research search provider: `hybrid-rss`" in report
