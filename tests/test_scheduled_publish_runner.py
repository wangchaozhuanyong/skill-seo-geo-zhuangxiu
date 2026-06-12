from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_scheduled_publish_runner


scheduled_publish_runner = load_scheduled_publish_runner()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"
SCHEDULED_NOW = "2026-06-15T01:00:00+00:00"
OUTSIDE_WINDOW_NOW = "2026-06-15T04:00:00+00:00"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def future_date() -> str:
    return (dt.date.today() + dt.timedelta(days=30)).isoformat()


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


def test_scheduled_publish_runner_blocks_missing_authorization_profile(tmp_path):
    result, artifacts = scheduled_publish_runner.run_scheduled_publish_runner(tmp_path, now=SCHEDULED_NOW)

    assert not result.ok
    assert result.status == "blocked_before_scheduled_publish_run"
    assert any("profile missing" in blocker for blocker in result.blockers)
    request_path, log_path, report_path = artifacts
    assert request_path.exists()
    assert log_path.exists()
    assert report_path.exists()
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert payload["no_live_actions_executed"] is True
    assert payload["run_request"]["no_daily_automation_executed"] is True


def test_scheduled_publish_runner_creates_ready_request_without_execution(tmp_path):
    profile_path = ready_profile(tmp_path)

    result, artifacts = scheduled_publish_runner.run_scheduled_publish_runner(
        tmp_path,
        profile_path=str(profile_path),
        now=SCHEDULED_NOW,
        write_example=False,
    )

    assert result.ok
    assert result.status == "scheduled_publish_run_request_ready"
    request = result.run_request
    assert request["run_allowed_for_scheduler"] is True
    assert request["target_url"] == TARGET_URL
    assert request["paired_url"] == PAIRED_URL
    assert request["schedule_window"]["inside_window"] is True
    assert request["no_publish_executed"] is True
    assert "daily-automation" in request["daily_automation_command"]
    assert any("publish-operator-package" in command for command in request["required_followup_commands"])
    assert any("publish-execution-receipt" in command for command in request["required_followup_commands"])
    request_path, log_path, report_path = artifacts
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert payload["run_request"]["action"] == "scheduled_publish_run_request_only_no_execute"
    assert TARGET_URL in log_path.read_text(encoding="utf-8")
    assert "run-request-only" in report_path.read_text(encoding="utf-8")


def test_scheduled_publish_runner_blocks_duplicate_ready_request(tmp_path):
    profile_path = ready_profile(tmp_path)

    first, _ = scheduled_publish_runner.run_scheduled_publish_runner(
        tmp_path,
        profile_path=str(profile_path),
        now=SCHEDULED_NOW,
        write_example=False,
    )
    second, _ = scheduled_publish_runner.run_scheduled_publish_runner(
        tmp_path,
        profile_path=str(profile_path),
        now=SCHEDULED_NOW,
        write_example=False,
    )

    assert first.ok
    assert not second.ok
    assert any("already exists" in blocker for blocker in second.blockers)


def test_scheduled_publish_runner_blocks_outside_schedule_window(tmp_path):
    profile_path = ready_profile(tmp_path)

    blocked, _ = scheduled_publish_runner.run_scheduled_publish_runner(
        tmp_path,
        profile_path=str(profile_path),
        now=OUTSIDE_WINDOW_NOW,
        write_example=False,
    )

    assert not blocked.ok
    assert any("outside the authorized" in blocker for blocker in blocked.blockers)


def test_scheduled_publish_runner_blocks_target_outside_authorized_scope(tmp_path):
    profile_path = ready_profile(tmp_path)

    result, _ = scheduled_publish_runner.run_scheduled_publish_runner(
        tmp_path,
        profile_path=str(profile_path),
        target_url="https://flashcast.com.my/en/services/bathroom",
        now=SCHEDULED_NOW,
        write_example=False,
    )

    assert not result.ok
    assert any("not included in allowed_target_urls" in blocker for blocker in result.blockers)
