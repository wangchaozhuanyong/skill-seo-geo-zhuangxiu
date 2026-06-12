import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_media_status,
    load_content_studio_media_url_template,
)
from tests.test_content_studio_media_url_template import seed_media_plan


media_status = load_content_studio_media_status()
media_url_template = load_content_studio_media_url_template()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_media_status_reports_missing_owner_urls_from_template(tmp_path: Path):
    seed_media_plan(tmp_path)
    media_url_template.run_content_studio_media_url_template(tmp_path)

    summary, artifacts = media_status.run_content_studio_media_status(tmp_path)

    assert summary["status"] == "media_urls_need_owner_input"
    assert summary["source"] == "template"
    assert summary["counts"]["missing_public_url"] == 1
    assert any("Missing file_url" in blocker for blocker in summary["blockers"])
    assert "先上传或选择效果图" in summary["next_actions"][0]
    assert all(path.exists() for path in artifacts)


def test_media_status_reports_urls_ready_for_handoff(tmp_path: Path):
    write_json(
        tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json",
        {
            "files": [
                {
                    "placeholder_filename": "hero.webp",
                    "file_url": "https://cdn.example.com/hero.webp",
                    "owner_url_confirmed": True,
                    "claim_boundary": "Generated rendering concept only.",
                }
            ]
        },
    )

    summary, _ = media_status.run_content_studio_media_status(tmp_path)

    assert summary["status"] == "media_urls_ready_for_handoff"
    assert summary["source"] == "uploaded_url_map"
    assert summary["counts"]["ready"] == 1
    assert summary["blockers"] == []
    assert "content-studio-media-ready-handoff" in summary["next_actions"][0]


def test_media_status_reports_media_ready_payload_present(tmp_path: Path):
    write_json(
        tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json",
        {
            "files": [
                {
                    "placeholder_filename": "hero.webp",
                    "file_url": "https://cdn.example.com/hero.webp",
                    "owner_url_confirmed": True,
                }
            ]
        },
    )
    write_json(tmp_path / "seo-workspace" / "data" / "media-url-map.json", {"hero.webp": "https://cdn.example.com/hero.webp"})
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json",
        {"payload": {"image_url": "https://cdn.example.com/hero.webp"}},
    )

    summary, _ = media_status.run_content_studio_media_status(tmp_path)

    assert summary["status"] == "media_ready_payload_present"
    assert summary["media_url_map_present"] is True
    assert summary["media_ready_payload_present"] is True
    assert "media-ready CMS payload 已存在" in summary["next_actions"][0]
