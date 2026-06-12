import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_media_ready_handoff,
    load_content_studio_owner_review_package,
)
from tests.test_content_studio_owner_review_package import seed_workspace


media_ready_handoff = load_content_studio_media_ready_handoff()
owner_review_package = load_content_studio_owner_review_package()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_media_ready_handoff_generates_payload_from_confirmed_urls(tmp_path: Path):
    seed_workspace(tmp_path)
    owner_review_package.run_content_studio_owner_review_package(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json",
        {
            "files": [
                {
                    "placeholder_filename": "hero.webp",
                    "public_filename": "hero.svg",
                    "object_path": "media/seo-generated/hero.svg",
                    "file_url": "https://cdn.example.com/media/seo-generated/hero.svg",
                }
            ]
        },
    )

    summary, artifacts = media_ready_handoff.run_content_studio_media_ready_handoff(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        storage_ready=True,
        uploaded_confirmed=True,
        latest_research_verified=True,
        allow_blocked_plan=True,
    )
    payload_path = tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))

    assert summary["status"] == "media_ready_handoff_waiting_owner_review"
    assert summary["media_ready"] is True
    assert summary["no_media_upload_executed"] is True
    assert payload["payload"]["image_url"] == "https://cdn.example.com/media/seo-generated/hero.svg"
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-media-ready-handoff.json").exists()
    assert (tmp_path / "seo-workspace" / "reports").joinpath(f"{date.today().isoformat()}-content-studio-media-ready-handoff.md").exists()
    assert artifacts


def test_media_ready_handoff_blocks_without_confirmed_uploaded_urls(tmp_path: Path):
    seed_workspace(tmp_path)
    owner_review_package.run_content_studio_owner_review_package(tmp_path)

    summary, _ = media_ready_handoff.run_content_studio_media_ready_handoff(
        tmp_path,
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        storage_ready=True,
    )

    assert summary["status"] == "media_ready_handoff_blocked"
    assert summary["media_ready"] is False
    assert any("Uploaded URL map" in blocker or "missing URLs" in blocker for blocker in summary["blockers"])
