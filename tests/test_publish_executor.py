import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_executor


publish_executor = load_publish_executor()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_executor_workspace(tmp_path: Path, *, plan_status: str = "ready_for_approved_execution_plan", image_url: str = "/uploads/kitchen.webp") -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "publish-execution-plan.json",
        {
            "status": plan_status,
            "queue_item": {
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "paired_url": "https://flashcast.com.my/zh/services/kitchen",
                "table": "services",
                "admin_helper": "saveAdminService",
            },
            "no_publish_executed": True,
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {
                "slug": "kitchen",
                "title_zh": "厨房装修图文方案",
                "title_en": "Kitchen Image-Rich Renovation Plan",
                "content_zh": "<section><h1>厨房装修图文方案</h1></section>",
                "content_en": "<section><h1>Kitchen Image-Rich Renovation Plan</h1></section>",
                "image_url": image_url,
                "alt_zh": "FLASH CAST 厨房效果图方案",
                "alt_en": "FLASH CAST kitchen rendering concept",
                "status": "draft",
            },
        },
    )


def test_publish_executor_blocks_without_ready_plan_flags_and_media(tmp_path):
    seed_executor_workspace(
        tmp_path,
        plan_status="blocked_before_publish",
        image_url="NEEDS_MEDIA_UPLOAD:flash-cast-kitchen.webp",
    )

    result, artifacts = publish_executor.run_publish_executor(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_cms_write"
    assert any("not ready_for_approved_execution_plan" in blocker for blocker in result.blockers)
    assert any("--owner-approved" in blocker for blocker in result.blockers)
    assert any("--explicit-execution" in blocker for blocker in result.blockers)
    assert any("--qa-passed" in blocker for blocker in result.blockers)
    assert any("Media placeholders remain" in blocker for blocker in result.blockers)
    request_path, report_path = artifacts
    payload = json.loads(request_path.read_text(encoding="utf-8"))
    assert payload["write_request"]["no_cms_write_executed"] is True
    assert "dry-run only" in report_path.read_text(encoding="utf-8")


def test_publish_executor_builds_save_admin_service_write_request(tmp_path):
    seed_executor_workspace(tmp_path)

    result, artifacts = publish_executor.run_publish_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        media_ready=True,
        next_status="draft",
    )

    assert result.ok
    assert result.status == "dry_run_write_request_ready"
    request = result.write_request
    assert request["admin_helper"] == "saveAdminService"
    assert request["planned_helper_call"]["function"] == "saveAdminService"
    assert request["planned_helper_call"]["input"]["record"]["slug"] == "kitchen"
    assert request["planned_helper_call"]["input"]["nextStatus"] == "draft"
    assert request["media_placeholders"] == []
    assert all(path.exists() for path in artifacts)


def test_publish_executor_prefers_editor_applied_payload_by_default(tmp_path):
    seed_executor_workspace(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {
                "slug": "kitchen",
                "title_zh": "编辑后的厨房图文方案",
                "title_en": "Edited Kitchen Image-Rich Plan",
                "content_zh": "<section><h1>编辑后的厨房图文方案</h1></section>",
                "content_en": "<section><h1>Edited Kitchen Image-Rich Plan</h1></section>",
                "image_url": "/uploads/edited.webp",
                "status": "draft",
            },
            "editor_applied": {"no_cms_write_executed": True, "no_live_actions_executed": True},
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-editor-apply-summary.json",
        {"status": "editor_applied_payload_ready_for_owner_review", "blockers": []},
    )

    result, _ = publish_executor.run_publish_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert result.ok
    request = result.write_request
    assert request["cms_payload_selection"] == "auto_editor_applied"
    assert request["planned_helper_call"]["input"]["record"]["title_en"] == "Edited Kitchen Image-Rich Plan"


def test_publish_executor_blocks_editor_applied_payload_when_editor_apply_qa_blocked(tmp_path):
    seed_executor_workspace(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {"slug": "kitchen", "title_en": "Edited Draft", "image_url": "/uploads/edited.webp", "status": "draft"},
            "editor_applied": {"no_cms_write_executed": True, "no_live_actions_executed": True},
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-editor-apply-summary.json",
        {"status": "rich_editor_apply_blocked", "blockers": ["image is missing media.claim_boundary"]},
    )

    result, _ = publish_executor.run_publish_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert not result.ok
    assert any("Editor-applied payload QA is not ready" in blocker for blocker in result.blockers)


def test_publish_executor_prefers_media_ready_payload_over_editor_applied(tmp_path):
    seed_executor_workspace(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {"slug": "kitchen", "title_en": "Edited Draft", "image_url": "NEEDS_MEDIA_UPLOAD:hero.webp", "status": "draft"},
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {"slug": "kitchen", "title_en": "Edited Media Ready", "image_url": "https://cdn.example.com/hero.webp", "status": "draft"},
            "editor_applied": {"no_cms_write_executed": True},
        },
    )

    result, _ = publish_executor.run_publish_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        media_ready=True,
    )

    assert result.ok
    assert result.write_request["cms_payload_selection"] == "auto_media_ready"
    assert result.write_request["planned_helper_call"]["input"]["record"]["title_en"] == "Edited Media Ready"


def test_publish_executor_blocks_even_with_media_ready_flag_when_selected_payload_has_placeholders(tmp_path):
    seed_executor_workspace(tmp_path, image_url="NEEDS_MEDIA_UPLOAD:hero.webp")

    result, _ = publish_executor.run_publish_executor(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        media_ready=True,
    )

    assert not result.ok
    assert any("Media placeholders remain in selected CMS payload" in blocker for blocker in result.blockers)
