from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_approved_executor


publish_approved_executor = load_publish_approved_executor()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ready_bundle_payload() -> dict:
    return {
        "status": "execution_bundle_ready_for_approved_executor",
        "blockers": [],
        "warnings": [],
        "bundle": {
            "generated_at": "2026-06-11T00:00:00+00:00",
            "action": "sealed_execution_bundle_only_no_cms_write",
            "status": "execution_bundle_ready_for_approved_executor",
            "target_url": TARGET_URL,
            "paired_url": PAIRED_URL,
            "table": "services",
            "admin_helper": "saveAdminService",
            "cms_payload_path": "seo-workspace/data/rich-content-cms-payload.media-ready.json",
            "cms_payload_selection": "auto_media_ready",
            "planned_helper_call": {
                "function": "saveAdminService",
                "input": {
                    "record": {
                        "slug": "kitchen",
                        "title_en": "Kitchen Image-Rich Renovation Plan",
                        "image_url": "https://cdn.example.com/kitchen.webp",
                        "status": "draft",
                    },
                    "nextStatus": "draft",
                },
            },
            "payload_keys": ["slug", "title_en", "image_url", "status"],
            "latest_research_sources": [{"source_title": "Schema.org Service"}],
            "media_url_map_present": True,
            "media_ready_payload_present": True,
            "editor_applied_payload_present": True,
            "editor_applied_used_edited_blocks": True,
            "post_write_tasks": ["regenerate seo-manifest", "regenerate sitemap.xml"],
            "required_pre_execution_checks": ["owner approval is recorded for this exact bundle"],
            "no_cms_write_executed": True,
            "no_source_page_write_executed": True,
            "no_media_upload_executed": True,
            "no_publish_executed": True,
            "no_deploy_executed": True,
            "no_live_actions_executed": True,
        },
    }


def seed_ready_bundle(tmp_path: Path, payload: dict | None = None) -> Path:
    bundle_path = tmp_path / "seo-workspace" / "data" / "publish-execution-bundle.json"
    write_json(bundle_path, payload or ready_bundle_payload())
    return bundle_path


def test_publish_approved_executor_blocks_without_bundle(tmp_path):
    result, artifacts = publish_approved_executor.run_publish_approved_executor(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_approved_execution"
    assert any("publish-execution-bundle.json" in blocker for blocker in result.blockers)
    record_path, report_path = artifacts
    assert record_path.exists()
    assert report_path.exists()


def test_publish_approved_executor_blocks_when_bundle_is_not_ready(tmp_path):
    payload = ready_bundle_payload()
    payload["status"] = "blocked_before_execution_bundle"
    payload["blockers"] = ["Publish readiness blocker: Missing media-ready payload."]
    payload["bundle"]["status"] = "blocked_before_execution_bundle"
    seed_ready_bundle(tmp_path, payload)

    result, _ = publish_approved_executor.run_publish_approved_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert not result.ok
    assert any("top-level status" in blocker for blocker in result.blockers)
    assert any("Publish bundle blocker" in blocker for blocker in result.blockers)


def test_publish_approved_executor_blocks_without_owner_execution_and_qa_flags(tmp_path):
    seed_ready_bundle(tmp_path)

    result, _ = publish_approved_executor.run_publish_approved_executor(tmp_path)

    assert not result.ok
    assert any("--owner-approved" in blocker for blocker in result.blockers)
    assert any("--explicit-execution" in blocker for blocker in result.blockers)
    assert any("--qa-passed" in blocker for blocker in result.blockers)


def test_publish_approved_executor_creates_simulation_record_without_writes(tmp_path):
    seed_ready_bundle(tmp_path)

    result, artifacts = publish_approved_executor.run_publish_approved_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        allowed_target_urls=[TARGET_URL, PAIRED_URL],
    )

    assert result.ok
    assert result.status == "approved_execution_simulation_ready"
    assert result.execution_record["execution_allowed_for_future_executor"] is True
    assert result.execution_record["simulated_helper_call"]["function"] == "saveAdminService"
    assert result.execution_record["no_cms_write_executed"] is True
    assert result.execution_record["no_live_actions_executed"] is True
    record_path, report_path = artifacts
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    assert payload["execution_record"]["action"] == "approved_execution_simulation_only_no_write"
    assert "approved-executor simulation only" in report_path.read_text(encoding="utf-8")


def test_publish_approved_executor_live_mode_requires_evidence_and_confirm(tmp_path):
    seed_ready_bundle(tmp_path)

    blocked, _ = publish_approved_executor.run_publish_approved_executor(
        tmp_path,
        mode="live",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert not blocked.ok
    assert any("Backup" in blocker for blocker in blocked.blockers)
    assert any("--confirm-live" in blocker for blocker in blocked.blockers)

    backup = tmp_path / "seo-workspace" / "backups" / "backup.json"
    changelog = tmp_path / "seo-workspace" / "reports" / "changelog.md"
    rollback = tmp_path / "seo-workspace" / "reports" / "rollback.md"
    backup.parent.mkdir(parents=True, exist_ok=True)
    changelog.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text("{}", encoding="utf-8")
    changelog.write_text("changes", encoding="utf-8")
    rollback.write_text("rollback", encoding="utf-8")

    ready, _ = publish_approved_executor.run_publish_approved_executor(
        tmp_path,
        mode="live",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        backup_path=str(backup),
        changelog_path=str(changelog),
        rollback_plan_path=str(rollback),
        confirm_live=True,
    )

    assert ready.ok
    assert ready.execution_record["mode"] == "live"
    assert ready.execution_record["no_publish_executed"] is True


def test_publish_approved_executor_blocks_media_placeholders_in_bundle(tmp_path):
    payload = ready_bundle_payload()
    payload["bundle"]["planned_helper_call"]["input"]["record"]["image_url"] = "NEEDS_MEDIA_UPLOAD:kitchen-hero.webp"
    seed_ready_bundle(tmp_path, payload)

    result, _ = publish_approved_executor.run_publish_approved_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert not result.ok
    assert any("Media placeholders remain" in blocker for blocker in result.blockers)
