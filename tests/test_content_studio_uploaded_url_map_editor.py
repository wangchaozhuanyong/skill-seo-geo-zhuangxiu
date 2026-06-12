import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_media_url_template,
    load_content_studio_uploaded_url_map_draft,
    load_content_studio_uploaded_url_map_editor,
)
from tests.test_content_studio_media_url_template import seed_media_plan


media_url_template = load_content_studio_media_url_template()
uploaded_url_map_draft = load_content_studio_uploaded_url_map_draft()
uploaded_url_map_editor = load_content_studio_uploaded_url_map_editor()


def test_uploaded_url_map_editor_writes_local_html_form(tmp_path: Path):
    seed_media_plan(tmp_path)
    media_url_template.run_content_studio_media_url_template(tmp_path)
    uploaded_url_map_draft.run_content_studio_uploaded_url_map_draft(tmp_path)

    summary, artifacts = uploaded_url_map_editor.run_content_studio_uploaded_url_map_editor(tmp_path)
    data_path, html_path, report_path = artifacts
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")

    assert summary["status"] == "uploaded_url_map_editor_ready"
    assert payload["file_count"] == 1
    assert payload["no_publish_executed"] is True
    assert payload["download_filename"] == "uploaded-url-map.filled.json"
    assert "Download uploaded-url-map.filled.json" in html
    assert "owner_url_confirmed" in html
    assert "https://cdn.example.com/path/image.webp" in html
    assert "设计方案 / 效果图方案 / rendering concept" in html
    assert "link.download = 'uploaded-url-map.filled.json'" in html
    assert '<script type="application/json" id="initialPayload">{"files":' in html
    assert report_path == tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-uploaded-url-map-editor.md"
    assert all(path.exists() for path in artifacts)


def test_uploaded_url_map_editor_blocks_without_files(tmp_path: Path):
    summary, artifacts = uploaded_url_map_editor.run_content_studio_uploaded_url_map_editor(tmp_path)

    assert summary["status"] == "uploaded_url_map_editor_blocked"
    assert summary["file_count"] == 0
    assert all(path.exists() for path in artifacts)
