import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_media_url_template,
    load_content_studio_uploaded_url_map_draft,
    load_content_studio_uploaded_url_map_import,
)
from tests.test_content_studio_media_url_template import seed_media_plan


media_url_template = load_content_studio_media_url_template()
uploaded_url_map_draft = load_content_studio_uploaded_url_map_draft()
uploaded_url_map_import = load_content_studio_uploaded_url_map_import()
PLACEHOLDER = "flash-cast-hero-rendering-concept.webp"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_uploaded_url_map_import_writes_validated_workspace_map(tmp_path: Path):
    seed_media_plan(tmp_path)
    media_url_template.run_content_studio_media_url_template(tmp_path)
    uploaded_url_map_draft.run_content_studio_uploaded_url_map_draft(tmp_path)
    filled = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.filled.json"
    write_json(
        filled,
        {
            "files": [
                {
                    "placeholder_filename": PLACEHOLDER,
                    "file_url": "https://cdn.example.com/flash-cast-hero-rendering-concept.webp",
                    "owner_url_confirmed": True,
                }
            ]
        },
    )

    summary, artifacts = uploaded_url_map_import.run_content_studio_uploaded_url_map_import(tmp_path)
    data_path, output_path, report_path = artifacts
    output = json.loads(output_path.read_text(encoding="utf-8"))

    assert summary["status"] == "uploaded_url_map_imported_waiting_media_status"
    assert summary["ready_file_count"] == 1
    assert summary["validation"]["blockers"] == []
    assert output["status"] == "uploaded_url_map_imported_from_owner_editor"
    assert output["files"][0]["file_url"] == "https://cdn.example.com/flash-cast-hero-rendering-concept.webp"
    assert output["no_publish_executed"] is True
    assert data_path.exists()
    assert report_path.exists()


def test_uploaded_url_map_import_blocks_mismatched_placeholders(tmp_path: Path):
    seed_media_plan(tmp_path)
    media_url_template.run_content_studio_media_url_template(tmp_path)
    filled = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.filled.json"
    write_json(
        filled,
        {
            "files": [
                {
                    "placeholder_filename": "wrong-page.webp",
                    "file_url": "https://cdn.example.com/wrong.webp",
                    "owner_url_confirmed": True,
                }
            ]
        },
    )

    summary, _ = uploaded_url_map_import.run_content_studio_uploaded_url_map_import(tmp_path)

    assert summary["status"] == "uploaded_url_map_import_blocked"
    assert any("missing current placeholders" in blocker for blocker in summary["validation"]["blockers"])
    assert any("not in the current template" in blocker for blocker in summary["validation"]["blockers"])


def test_uploaded_url_map_import_blocks_non_https(tmp_path: Path):
    seed_media_plan(tmp_path)
    media_url_template.run_content_studio_media_url_template(tmp_path)
    filled = tmp_path / "seo-workspace" / "data" / "uploaded-url-map.filled.json"
    write_json(filled, {"files": [{"placeholder_filename": PLACEHOLDER, "file_url": "http://cdn.example.com/hero.webp"}]})

    summary, _ = uploaded_url_map_import.run_content_studio_uploaded_url_map_import(tmp_path)

    assert summary["status"] == "uploaded_url_map_import_blocked"
    assert any("public HTTPS" in blocker for blocker in summary["validation"]["blockers"])
