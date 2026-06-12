import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_media_review_package


media_review_package = load_content_studio_media_review_package()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_review_inputs(tmp_path: Path, *, local_file_exists: bool = True) -> Path:
    media_path = tmp_path / "seo-workspace" / "media" / "generated" / "hero.svg"
    if local_file_exists:
        media_path.parent.mkdir(parents=True, exist_ok=True)
        media_path.write_text("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'><rect width='10' height='10'/></svg>\n", encoding="utf-8")
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-upload-plan.json",
        {
            "status": "owner_review_required",
            "queue": [
                {
                    "queue_id": "media-upload-001",
                    "placeholder_filename": "hero.webp",
                    "public_filename": "hero.svg",
                    "local_path": str(media_path),
                    "object_path": "media/seo-generated/2026-06-11/hero.svg",
                    "bucket": "site-images",
                    "usage_type": "hero",
                    "alt_zh": "厨房效果图方案",
                    "alt_en": "kitchen rendering concept",
                    "claim_boundary": "Generated rendering concept only.",
                    "public_url": "NEEDS_PUBLIC_URL:site-images/media/seo-generated/2026-06-11/hero.svg",
                }
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "concept-asset-manifest.json",
        {
            "status": "concept_assets_generated",
            "assets": [
                {
                    "placeholder_filename": "hero.webp",
                    "generated_filename": "hero.svg",
                    "local_path": str(media_path),
                    "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    "claim_boundary": "Generated rendering concept only.",
                }
            ],
        },
    )
    return media_path


def test_media_review_package_generates_gallery_for_existing_assets(tmp_path: Path):
    seed_review_inputs(tmp_path)

    summary, artifacts = media_review_package.run_content_studio_media_review_package(tmp_path)

    assert summary["status"] == "media_review_package_ready"
    assert summary["item_count"] == 1
    assert summary["items"][0]["local_file_exists"] is True
    assert summary["no_media_upload_executed"] is True
    assert all(path.exists() for path in artifacts)
    gallery = artifacts[1].read_text(encoding="utf-8")
    assert "kitchen rendering concept" in gallery
    assert "不得作为真实完工案例" in gallery


def test_media_review_package_blocks_missing_local_assets(tmp_path: Path):
    seed_review_inputs(tmp_path, local_file_exists=False)

    summary, _ = media_review_package.run_content_studio_media_review_package(tmp_path)

    assert summary["status"] == "blocked_missing_media_review_inputs"
    assert any("Local media file missing" in blocker for blocker in summary["blockers"])
