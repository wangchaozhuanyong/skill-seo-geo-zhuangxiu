import csv
import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_readiness


publish_readiness = load_publish_readiness()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def seed_queue_and_research(tmp_path: Path) -> None:
    write_csv(
        tmp_path / "seo-workspace" / "data" / "approved-publish-queue.csv",
        [
            {
                "draft_path": "seo-workspace/drafts/kitchen.md",
                "target_url": TARGET_URL,
                "paired_url": PAIRED_URL,
                "target_kind": "service",
                "table": "services",
                "admin_helper": "saveAdminService",
                "status": "owner_review_required",
            }
        ],
    )
    write_csv(
        tmp_path / "seo-workspace" / "data" / "research-source-log.csv",
        [
            {
                "date_added": "2026-06-10",
                "target_url": TARGET_URL,
                "source_type": "official",
                "source_title": "Search Central structured data guidance",
                "source_url": "https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data",
                "publisher": "Google Search Central",
                "published_or_accessed_date": "2026-06-10",
                "usage_note": "Use only for schema visibility guidance",
                "claim_boundary": "general guidance only; not a FLASH CAST business claim",
            }
        ],
    )


def seed_blocked_workspace(tmp_path: Path) -> None:
    seed_queue_and_research(tmp_path)
    data_dir = tmp_path / "seo-workspace" / "data"
    write_json(
        data_dir / "publish-execution-plan.json",
        {
            "status": "blocked_before_publish",
            "no_publish_executed": True,
            "queue_item": {"target_url": TARGET_URL, "paired_url": PAIRED_URL},
            "blockers": ["Owner has not approved this exact queued package (--owner-approved missing)."],
            "warnings": [],
        },
    )
    write_json(
        data_dir / "cms-write-request.json",
        {
            "status": "blocked_before_cms_write",
            "blockers": ["Publish plan is not ready_for_approved_execution_plan: blocked_before_publish."],
            "warnings": [],
            "write_request": {"no_cms_write_executed": True},
        },
    )
    write_json(
        data_dir / "media-upload-plan.json",
        {
            "status": "owner_review_required",
            "queue": [{"queue_id": "media-upload-001"}],
            "no_media_upload_executed": True,
        },
    )
    write_json(
        data_dir / "media-upload-execution-request.json",
        {
            "status": "blocked_before_media_upload",
            "no_media_upload_executed": True,
            "blockers": ["Storage readiness is not confirmed (--storage-ready missing)."],
            "warnings": ["No uploaded URL map supplied; media-ready CMS payload was not generated."],
            "operations": [{"queue_id": "media-upload-001"}],
        },
    )


def seed_ready_workspace(tmp_path: Path) -> None:
    seed_queue_and_research(tmp_path)
    data_dir = tmp_path / "seo-workspace" / "data"
    write_json(
        data_dir / "publish-execution-plan.json",
        {
            "status": "ready_for_approved_execution_plan",
            "no_publish_executed": True,
            "queue_item": {"target_url": TARGET_URL, "paired_url": PAIRED_URL},
            "blockers": [],
            "warnings": [],
        },
    )
    write_json(
        data_dir / "cms-write-request.json",
        {
            "status": "dry_run_write_request_ready",
            "blockers": [],
            "warnings": [],
            "write_request": {"no_cms_write_executed": True},
        },
    )
    write_json(
        data_dir / "media-upload-plan.json",
        {
            "status": "ready_for_media_upload_execution",
            "queue": [{"queue_id": "media-upload-001"}],
            "no_media_upload_executed": True,
        },
    )
    write_json(
        data_dir / "media-upload-execution-request.json",
        {
            "status": "media_ready_payload_generated_from_uploaded_urls",
            "no_media_upload_executed": True,
            "blockers": [],
            "warnings": [],
            "operations": [{"queue_id": "media-upload-001", "status": "uploaded_url_supplied"}],
        },
    )
    write_json(data_dir / "media-url-map.json", {"hero.webp": "https://cdn.example.com/hero.svg"})
    write_json(data_dir / "rich-content-cms-payload.media-ready.json", {"payload": {"image_url": "https://cdn.example.com/hero.svg"}})


def test_publish_readiness_blocks_when_artifacts_are_missing(tmp_path):
    result, artifacts = publish_readiness.run_publish_readiness(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_publish_handoff"
    assert any("publish-execution-plan.json" in blocker for blocker in result.blockers)
    assert any("cms-write-request.json" in blocker for blocker in result.blockers)
    assert any("media-upload-execution-request.json" in blocker for blocker in result.blockers)
    assert all(path.exists() for path in artifacts)


def test_publish_readiness_reports_current_blocked_chain(tmp_path):
    seed_blocked_workspace(tmp_path)

    result, _ = publish_readiness.run_publish_readiness(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_publish_handoff"
    assert result.evidence["valid_latest_research_source_count"] == 1
    assert result.evidence["planned_media_operation_count"] == 1
    assert any("Publish plan is not ready_for_approved_execution_plan" in blocker for blocker in result.blockers)
    assert any("Missing media-url-map.json" in blocker for blocker in result.blockers)
    assert any("Publish plan blocker" in blocker for blocker in result.blockers)


def test_publish_readiness_passes_when_full_handoff_artifacts_are_ready(tmp_path):
    seed_ready_workspace(tmp_path)

    result, artifacts = publish_readiness.run_publish_readiness(tmp_path)

    assert result.ok
    assert result.status == "ready_for_owner_approved_publish_handoff"
    assert result.evidence["valid_latest_research_source_count"] == 1
    assert result.evidence["media_url_map_present"] is True
    assert result.evidence["media_ready_payload_present"] is True
    readiness_json, report_path = artifacts
    payload = json.loads(readiness_json.read_text(encoding="utf-8"))
    assert payload["status"] == "ready_for_owner_approved_publish_handoff"
    assert "readiness-only" in report_path.read_text(encoding="utf-8")


def test_publish_readiness_reports_editor_applied_payload_evidence(tmp_path):
    seed_ready_workspace(tmp_path)
    data_dir = tmp_path / "seo-workspace" / "data"
    editor_payload_path = data_dir / "rich-content-cms-payload.editor-applied.json"
    media_ready_path = data_dir / "rich-content-cms-payload.media-ready.json"
    write_json(
        editor_payload_path,
        {
            "payload": {"title_en": "Edited Kitchen Plan", "image_url": "NEEDS_MEDIA_UPLOAD:hero.webp"},
            "editor_applied": {"no_cms_write_executed": True, "no_live_actions_executed": True},
        },
    )
    write_json(
        data_dir / "rich-content-editor-apply-summary.json",
        {
            "status": "editor_applied_payload_ready_for_owner_review",
            "used_edited_blocks": True,
            "zh_block_count": 2,
            "en_block_count": 2,
        },
    )
    write_json(
        media_ready_path,
        {
            "payload": {"title_en": "Edited Kitchen Plan", "image_url": "https://cdn.example.com/hero.svg"},
            "editor_applied": {"no_cms_write_executed": True, "no_live_actions_executed": True},
        },
    )
    write_json(
        data_dir / "cms-write-request.json",
        {
            "status": "dry_run_write_request_ready",
            "blockers": [],
            "warnings": [],
            "write_request": {
                "no_cms_write_executed": True,
                "cms_payload_path": str(media_ready_path),
                "cms_payload_selection": "auto_media_ready",
            },
        },
    )

    result, _ = publish_readiness.run_publish_readiness(tmp_path)

    assert result.ok
    assert result.evidence["editor_applied_payload_present"] is True
    assert result.evidence["editor_applied_used_edited_blocks"] is True
    assert result.evidence["media_ready_uses_editor_applied_payload"] is True
    assert result.evidence["cms_payload_selection"] == "auto_media_ready"


def test_publish_readiness_blocks_when_editor_applied_qa_blocked(tmp_path):
    seed_ready_workspace(tmp_path)
    data_dir = tmp_path / "seo-workspace" / "data"
    editor_payload_path = data_dir / "rich-content-cms-payload.editor-applied.json"
    media_ready_path = data_dir / "rich-content-cms-payload.media-ready.json"
    write_json(
        editor_payload_path,
        {
            "payload": {"title_en": "Edited Kitchen Plan", "image_url": "NEEDS_MEDIA_UPLOAD:hero.webp"},
            "editor_applied": {"no_cms_write_executed": True, "no_live_actions_executed": True},
        },
    )
    write_json(
        data_dir / "rich-content-editor-apply-summary.json",
        {"status": "rich_editor_apply_blocked", "blockers": ["image is missing media.claim_boundary"]},
    )
    write_json(
        media_ready_path,
        {
            "payload": {"title_en": "Edited Kitchen Plan", "image_url": "https://cdn.example.com/hero.svg"},
            "editor_applied": {"no_cms_write_executed": True, "no_live_actions_executed": True},
        },
    )
    write_json(
        data_dir / "cms-write-request.json",
        {
            "status": "dry_run_write_request_ready",
            "blockers": [],
            "warnings": [],
            "write_request": {
                "no_cms_write_executed": True,
                "cms_payload_path": str(media_ready_path),
                "cms_payload_selection": "auto_media_ready",
            },
        },
    )

    result, _ = publish_readiness.run_publish_readiness(tmp_path)

    assert not result.ok
    assert any("Editor-applied payload QA is not ready" in blocker for blocker in result.blockers)
    assert result.evidence["editor_applied_status"] == "rich_editor_apply_blocked"
