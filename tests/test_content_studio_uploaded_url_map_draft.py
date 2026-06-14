import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_media_url_template,
    load_content_studio_uploaded_url_map_draft,
)
from tests.test_content_studio_media_url_template import seed_media_plan


uploaded_url_map_draft = load_content_studio_uploaded_url_map_draft()
media_url_template = load_content_studio_media_url_template()


def test_uploaded_url_map_draft_writes_owner_fillable_json(tmp_path: Path):
    seed_media_plan(tmp_path)
    media_url_template.run_content_studio_media_url_template(tmp_path)

    draft, artifacts = uploaded_url_map_draft.run_content_studio_uploaded_url_map_draft(tmp_path)

    assert draft["status"] == "uploaded_url_map_needs_owner_urls"
    assert draft["files"][0]["owner_url_confirmed"] is False
    assert draft["validation"]["blockers"][0].startswith("Missing file_url")
    assert (tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json").exists()
    assert all(path.exists() for path in artifacts)


def test_uploaded_url_map_draft_validate_only_accepts_confirmed_https_urls(tmp_path: Path):
    data_path = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "placeholder_filename": "hero.webp",
                        "file_url": "https://cdn.example.com/hero.webp",
                        "owner_url_confirmed": True,
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    draft, _ = uploaded_url_map_draft.run_content_studio_uploaded_url_map_draft(tmp_path, validate_only=True)

    assert draft["status"] == "uploaded_url_map_ready_for_confirmation"
    assert draft["validation"]["ready_file_count"] == 1
    assert draft["validation"]["blockers"] == []


def test_uploaded_url_map_draft_blocks_non_https_urls(tmp_path: Path):
    data_path = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps({"files": [{"placeholder_filename": "hero.webp", "file_url": "http://example.com/hero.webp"}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    draft, _ = uploaded_url_map_draft.run_content_studio_uploaded_url_map_draft(tmp_path, validate_only=True)

    assert draft["status"] == "uploaded_url_map_needs_owner_urls"
    assert any("public HTTPS" in blocker for blocker in draft["validation"]["blockers"])


def test_uploaded_url_map_draft_preserves_existing_confirmed_public_urls(tmp_path: Path):
    seed_media_plan(tmp_path)
    media_url_template.run_content_studio_media_url_template(tmp_path)
    data_path = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json"
    data_path.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "placeholder_filename": "flash-cast-hero-rendering-concept.webp",
                        "file_url": "https://cdn.example.com/flash-cast-hero-rendering-concept.webp",
                        "owner_url_confirmed": True,
                        "upload_status": "uploaded",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    draft, _ = uploaded_url_map_draft.run_content_studio_uploaded_url_map_draft(tmp_path)

    assert draft["files"][0]["file_url"] == "https://cdn.example.com/flash-cast-hero-rendering-concept.webp"
    assert draft["files"][0]["owner_url_confirmed"] is True
    assert draft["files"][0]["upload_status"] == "uploaded"
