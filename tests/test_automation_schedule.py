import json
from datetime import date, timedelta
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_automation_schedule


automation_schedule = load_automation_schedule()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_authorization_profile(tmp_path: Path) -> Path:
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
  - "https://flashcast.com.my/en/services/kitchen"
  - "https://flashcast.com.my/zh/services/kitchen"
website_root: "{website_root}"
max_pages_per_run: 1
language_scope: "bilingual_pair_required"
expires_at: "{(date.today() + timedelta(days=30)).isoformat()}"
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


def test_automation_schedule_writes_safe_default_examples(tmp_path):
    result, artifacts = automation_schedule.run_automation_schedule(tmp_path)

    assert result.ok
    assert result.status == "schedule_plan_ready_for_owner_review"
    example_path, plan_path, cron_path, launchd_path, report_path = artifacts
    assert example_path.exists()
    assert plan_path.exists()
    assert cron_path.exists()
    assert launchd_path.exists()
    assert report_path.exists()
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    assert payload["no_schedule_installed"] is True
    assert payload["no_live_actions_executed"] is True
    assert payload["schedule"]["publish_enabled"] is False
    assert payload["schedule"]["executor"] == "daily-automation"
    cron = cron_path.read_text(encoding="utf-8")
    assert "daily-automation" in cron
    assert "--research-search-provider" in cron
    assert "hybrid-rss" in cron
    assert "--research-search-feeds-config" in cron
    assert "schedule-plan-only" in report_path.read_text(encoding="utf-8")


def test_automation_schedule_supports_content_studio_next_executor(tmp_path):
    config_path = tmp_path / "seo-workspace" / "config" / "daily-automation.yml"
    write(
        config_path,
        """automation_id: "flash-cast-daily-seo-geo"
enabled: true
timezone: "Asia/Kuala_Lumpur"
time_local: "09:00"
executor: "content-studio-next"
pipeline: "rich-content"
owner_review_package: true
fetch_research_remote: false
publish_enabled: false
max_tasks_per_run: 1
language_scope: "bilingual_pair_required"
safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
""",
    )

    result, artifacts = automation_schedule.run_automation_schedule(tmp_path, config_path=str(config_path), write_example=False)
    _, plan_path, cron_path, _, report_path = artifacts
    payload = json.loads(plan_path.read_text(encoding="utf-8"))
    cron = cron_path.read_text(encoding="utf-8")
    report = report_path.read_text(encoding="utf-8")

    assert result.ok
    assert payload["schedule"]["executor"] == "content-studio-next"
    assert payload["schedule"]["owner_review_package"] is True
    assert "content-studio-orchestrator" in cron
    assert "content-studio-next" not in cron
    assert "--config-path" in cron
    assert "daily-automation --pipeline" not in cron
    assert "content-studio-next" in report
    assert '"owner_review_package": true' in plan_path.read_text(encoding="utf-8")


def test_automation_schedule_blocks_publish_without_exact_authorization(tmp_path):
    config_path = tmp_path / "seo-workspace" / "config" / "daily-automation.yml"
    write(
        config_path,
        """automation_id: "flash-cast-daily-seo-geo"
enabled: true
timezone: "Asia/Kuala_Lumpur"
time_local: "09:00"
pipeline: "publish-prep"
publish_enabled: true
max_tasks_per_run: 1
language_scope: "bilingual_pair_required"
owner_authorization:
  exact_authorization_id: "NEEDS_OWNER_INPUT"
  owner_approved: false
  explicit_execution: false
  allowed_pipeline: "publish-prep"
  allowed_target_paths:
safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
""",
    )

    result, artifacts = automation_schedule.run_automation_schedule(tmp_path, config_path=str(config_path), write_example=False)

    assert not result.ok
    assert result.status == "schedule_plan_blocked"
    assert any("exact_authorization_id" in blocker for blocker in result.blockers)
    assert any("owner_approved" in blocker for blocker in result.blockers)
    assert artifacts[1].exists()


def test_automation_schedule_accepts_authorized_publish_prep_handoff(tmp_path):
    config_path = tmp_path / "seo-workspace" / "config" / "daily-automation.yml"
    authorization_profile_path = write_authorization_profile(tmp_path)
    write(
        config_path,
        """automation_id: "flash-cast-daily-seo-geo"
enabled: true
timezone: "Asia/Kuala_Lumpur"
time_local: "09:00"
pipeline: "publish-prep"
publish_enabled: true
max_tasks_per_run: 1
language_scope: "bilingual_pair_required"
owner_authorization:
  exact_authorization_id: "OWNER-APPROVED-2026-06-11-KITCHEN"
  owner_approved: true
  explicit_execution: true
  allowed_pipeline: "publish-prep"
  allowed_target_paths:
    - "/en/services/kitchen"
    - "/zh/services/kitchen"
  qa_required: true
  backup_required: true
  rollback_required: true
  media_url_confirmation_required: true
  live_confirmation_required: true
safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
""",
    )

    result, _ = automation_schedule.run_automation_schedule(
        tmp_path,
        config_path=str(config_path),
        authorization_profile_path=str(authorization_profile_path),
        write_example=False,
    )

    assert result.ok
    assert result.status == "schedule_plan_ready_for_owner_review"
    assert result.schedule["publish_enabled"] is True
