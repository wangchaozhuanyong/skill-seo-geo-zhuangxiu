import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_media_upload_executor


media_upload_executor = load_media_upload_executor()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_executor_workspace(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-upload-plan.json",
        {
            "status": "owner_review_required",
            "no_media_upload_executed": True,
            "queue": [
                {
                    "queue_id": "media-upload-001",
                    "placeholder_filename": "flash-cast-hero-rendering-concept.webp",
                    "public_filename": "flash-cast-hero-rendering-concept.svg",
                    "local_path": str(tmp_path / "seo-workspace" / "media" / "generated" / "flash-cast-hero-rendering-concept.svg"),
                    "exists": "yes",
                    "bucket": "site-images",
                    "object_path": "media/seo-generated/2026-06-10/flash-cast-hero-rendering-concept.svg",
                    "public_url": "NEEDS_PUBLIC_URL:site-images/media/seo-generated/2026-06-10/flash-cast-hero-rendering-concept.svg",
                    "mime_type": "image/svg+xml",
                    "folder": "media",
                    "usage_type": "hero",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "claim_boundary": "Generated SVG design/rendering concept only; not a real project photo.",
                    "upload_helper": "uploadAdminMediaObject",
                    "record_helper": "createAdminMediaAsset",
                }
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-asset-plan.json",
        {
            "status": "needs_media_generation_or_upload",
            "no_media_upload_executed": True,
            "media_assets": [
                {
                    "filename": "flash-cast-hero-rendering-concept.webp",
                    "usage_type": "hero",
                    "mime_type": "image/webp",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "claim_boundary": "Generated visual for design/rendering concept only.",
                }
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.json",
        {
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {
                "slug": "kitchen",
                "content_en": '<img src="flash-cast-hero-rendering-concept.webp" alt="hero">',
                "image_url": "NEEDS_MEDIA_UPLOAD:flash-cast-hero-rendering-concept.webp",
                "status": "draft",
            },
        },
    )


def test_media_upload_executor_blocks_without_required_gates(tmp_path):
    seed_executor_workspace(tmp_path)

    result, artifacts = media_upload_executor.run_media_upload_executor(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_media_upload"
    assert any("--owner-approved" in blocker for blocker in result.blockers)
    request_path, report_path, map_path, ready_path = artifacts
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["no_media_upload_executed"] is True
    assert request["operations"][0]["upload_helper"] == "uploadAdminMediaObject"
    assert "未上传媒体" in report_path.read_text(encoding="utf-8")
    assert map_path is None
    assert ready_path is None


def test_media_upload_executor_generates_media_ready_payload_from_confirmed_urls(tmp_path):
    seed_executor_workspace(tmp_path)
    uploaded_map = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json"
    write_json(uploaded_map, {"flash-cast-hero-rendering-concept.webp": "https://cdn.example.com/media/hero.svg"})

    result, artifacts = media_upload_executor.run_media_upload_executor(
        tmp_path,
        uploaded_url_map_path=str(uploaded_map),
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        storage_ready=True,
        uploaded_confirmed=True,
    )

    assert result.ok
    assert result.status == "media_ready_payload_generated_from_uploaded_urls"
    _, _, map_path, ready_path = artifacts
    assert map_path is not None
    assert ready_path is not None
    url_map = json.loads(map_path.read_text(encoding="utf-8"))
    assert url_map["flash-cast-hero-rendering-concept.webp"] == "https://cdn.example.com/media/hero.svg"
    ready = json.loads(ready_path.read_text(encoding="utf-8"))
    assert ready["payload"]["image_url"] == "https://cdn.example.com/media/hero.svg"
    assert 'src="https://cdn.example.com/media/hero.svg"' in ready["payload"]["content_en"]


def test_media_upload_executor_uses_editor_applied_payload_when_present(tmp_path):
    seed_executor_workspace(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {
                "slug": "kitchen",
                "title_en": "Edited Upload Payload",
                "content_en": '<section><img src="flash-cast-hero-rendering-concept.webp" alt="hero"></section>',
                "image_url": "NEEDS_MEDIA_UPLOAD:flash-cast-hero-rendering-concept.webp",
                "status": "draft",
            },
            "editor_applied": {"no_cms_write_executed": True},
        },
    )
    uploaded_map = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json"
    write_json(uploaded_map, {"flash-cast-hero-rendering-concept.webp": "https://cdn.example.com/media/hero.svg"})

    result, artifacts = media_upload_executor.run_media_upload_executor(
        tmp_path,
        uploaded_url_map_path=str(uploaded_map),
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        storage_ready=True,
        uploaded_confirmed=True,
    )

    assert result.ok
    request = json.loads(artifacts[0].read_text(encoding="utf-8"))
    ready_path = artifacts[3]
    assert ready_path is not None
    ready = json.loads(ready_path.read_text(encoding="utf-8"))
    assert request["cms_payload_selection"] == "auto_editor_applied"
    assert ready["payload"]["title_en"] == "Edited Upload Payload"
    assert ready["editor_applied"]["no_cms_write_executed"] is True


def test_media_upload_executor_rejects_unconfirmed_uploaded_urls(tmp_path):
    seed_executor_workspace(tmp_path)
    uploaded_map = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json"
    write_json(uploaded_map, {"flash-cast-hero-rendering-concept.webp": "https://cdn.example.com/media/hero.svg"})

    result, _ = media_upload_executor.run_media_upload_executor(
        tmp_path,
        uploaded_url_map_path=str(uploaded_map),
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        storage_ready=True,
    )

    assert not result.ok
    assert any("--uploaded-confirmed" in blocker for blocker in result.blockers)
