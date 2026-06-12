from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_scheduled_publish_authorization


scheduled_publish_authorization = load_scheduled_publish_authorization()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def future_date() -> str:
    return (dt.date.today() + dt.timedelta(days=30)).isoformat()


def ready_profile(tmp_path: Path, *, mode: str = "dry-run", max_pages: int = 1, live_confirm: bool = False) -> str:
    website_root = tmp_path / "website"
    website_root.mkdir(parents=True, exist_ok=True)
    confirm_phrase = "CONFIRM LIVE SCHEDULED PUBLISH" if live_confirm else ""
    require_confirm_live = "true" if live_confirm else "false"
    return f"""automation_id: "flash-cast-daily-seo-geo"
enabled: true
authorization_profile_id: "SCHEDULED-PUBLISH-PROFILE-TEST"
owner_authorization_id: "OWNER-APPROVED-SCHEDULED-PUBLISH-TEST"
authorized_pipeline: "publish-prep"
mode: "{mode}"
timezone: "Asia/Kuala_Lumpur"
local_time: "09:00"
allowed_weekdays:
  - "Mon"
  - "Tue"
allowed_target_urls:
  - "{TARGET_URL}"
  - "{PAIRED_URL}"
website_root: "{website_root}"
max_pages_per_run: {max_pages}
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
require_confirm_live: {require_confirm_live}
confirm_live_phrase: "{confirm_phrase}"
safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
"""


def test_scheduled_publish_authorization_blocks_missing_profile_and_writes_example(tmp_path):
    result, artifacts = scheduled_publish_authorization.run_scheduled_publish_authorization(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_scheduled_publish_authorization"
    assert any("profile missing" in blocker for blocker in result.blockers)
    example_path, json_path, report_path = artifacts
    assert example_path.exists()
    assert json_path.exists()
    assert report_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["no_live_actions_executed"] is True
    assert payload["authorization"]["no_daily_automation_executed"] is True
    assert "authorization-check-only" in report_path.read_text(encoding="utf-8")


def test_scheduled_publish_authorization_accepts_ready_dry_run_profile(tmp_path):
    profile_path = tmp_path / "seo-workspace" / "config" / "scheduled-publish-authorization.yml"
    write(profile_path, ready_profile(tmp_path))

    result, artifacts = scheduled_publish_authorization.run_scheduled_publish_authorization(
        tmp_path,
        profile_path=str(profile_path),
        write_example=False,
    )

    assert result.ok
    assert result.status == "scheduled_publish_authorization_ready"
    assert result.authorization["authorization_ready_for_scheduled_publish"] is True
    assert result.authorization["profile"]["max_pages_per_run"] == 1
    assert result.authorization["no_publish_executed"] is True
    assert any("daily-automation" in command for command in result.authorization["allowed_daily_automation_commands"])
    _, json_path, _ = artifacts
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["authorization"]["required_runtime_flags"]


def test_scheduled_publish_authorization_live_mode_requires_confirmation_phrase(tmp_path):
    profile_path = tmp_path / "seo-workspace" / "config" / "scheduled-publish-authorization.yml"
    write(profile_path, ready_profile(tmp_path, mode="live", live_confirm=False))

    blocked, _ = scheduled_publish_authorization.run_scheduled_publish_authorization(
        tmp_path,
        profile_path=str(profile_path),
        write_example=False,
    )

    assert not blocked.ok
    assert any("require_confirm_live=true" in blocker for blocker in blocked.blockers)
    assert any("confirm_live_phrase" in blocker for blocker in blocked.blockers)

    write(profile_path, ready_profile(tmp_path, mode="live", live_confirm=True))

    ready, _ = scheduled_publish_authorization.run_scheduled_publish_authorization(
        tmp_path,
        profile_path=str(profile_path),
        write_example=False,
    )

    assert ready.ok
    assert "--confirm-live" in ready.authorization["required_runtime_flags"]


def test_scheduled_publish_authorization_blocks_bulk_pages(tmp_path):
    profile_path = tmp_path / "seo-workspace" / "config" / "scheduled-publish-authorization.yml"
    write(profile_path, ready_profile(tmp_path, max_pages=2))

    result, _ = scheduled_publish_authorization.run_scheduled_publish_authorization(
        tmp_path,
        profile_path=str(profile_path),
        write_example=False,
    )

    assert not result.ok
    assert any("max_pages_per_run" in blocker for blocker in result.blockers)
