import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_media_url_template


media_url_template = load_content_studio_media_url_template()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_media_plan(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-upload-plan.json",
        {
            "status": "owner_review_required",
            "queue": [
                {
                    "queue_id": "media-upload-001",
                    "placeholder_filename": "flash-cast-hero-rendering-concept.webp",
                    "public_filename": "flash-cast-hero-rendering-concept.svg",
                    "object_path": "media/seo-generated/2026-06-11/flash-cast-hero-rendering-concept.svg",
                    "local_path": "/tmp/flash-cast-hero-rendering-concept.svg",
                    "bucket": "site-images",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "claim_boundary": "Generated SVG design/rendering concept only.",
                }
            ],
        },
    )


def test_media_url_template_writes_files_list_for_executor(tmp_path):
    seed_media_plan(tmp_path)

    template, artifacts = media_url_template.run_content_studio_media_url_template(tmp_path)

    assert template["status"] == "uploaded_url_map_template_ready"
    assert template["no_media_upload_executed"] is True
    assert template["files"][0]["placeholder_filename"] == "flash-cast-hero-rendering-concept.webp"
    assert template["files"][0]["file_url"] == ""
    assert template["files"][0]["claim_boundary"] == "Generated SVG design/rendering concept only."
    assert all(path.exists() for path in artifacts)


def test_media_url_template_can_prefill_public_base_url(tmp_path):
    seed_media_plan(tmp_path)

    template, _ = media_url_template.run_content_studio_media_url_template(tmp_path, public_base_url="https://cdn.example.com/uploads")

    assert template["files"][0]["file_url"] == "https://cdn.example.com/uploads/media/seo-generated/2026-06-11/flash-cast-hero-rendering-concept.svg"
    assert template["public_base_url_prefilled"] is True


def test_media_url_template_blocks_without_media_plan(tmp_path):
    template, _ = media_url_template.run_content_studio_media_url_template(tmp_path)

    assert template["status"] == "blocked_missing_media_upload_plan"
    assert template["files"] == []
