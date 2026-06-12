import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_post_media_handoff
from tests.test_content_studio_owner_review_package import seed_workspace


post_media_handoff = load_publish_post_media_handoff()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_uploaded_url_map(tmp_path: Path, *, ready: bool) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json",
        {
            "files": [
                {
                    "placeholder_filename": "hero.webp",
                    "public_filename": "hero.svg",
                    "object_path": "media/seo-generated/hero.svg",
                    "file_url": "https://cdn.example.com/hero.svg" if ready else "",
                    "owner_url_confirmed": ready,
                }
            ]
        },
    )


def test_post_media_handoff_blocks_when_media_urls_missing(tmp_path: Path):
    seed_workspace(tmp_path)
    write_uploaded_url_map(tmp_path, ready=False)

    summary, artifacts = post_media_handoff.run_publish_post_media_handoff(tmp_path)

    assert summary["status"] == "post_media_handoff_blocked"
    assert summary["media_status"] == "media_urls_need_owner_input"
    assert any("Media URLs are not ready" in blocker for blocker in summary["blockers"])
    assert summary["no_cms_write_executed"] is True
    assert artifacts


def test_post_media_handoff_runs_downstream_steps_when_media_urls_ready(tmp_path: Path):
    seed_workspace(tmp_path)
    write_uploaded_url_map(tmp_path, ready=True)

    summary, _ = post_media_handoff.run_publish_post_media_handoff(
        tmp_path,
        allowed_target_urls=[
            "https://flashcast.com.my/en/services/kitchen",
            "https://flashcast.com.my/zh/services/kitchen",
        ],
    )

    assert any(step["step"] == "content_studio_media_status" for step in summary["steps"])
    assert any(step["step"] == "content_studio_operator_ready_handoff" for step in summary["steps"])
    assert any(step["step"] == "publish_cms_write_executor_dry_run" for step in summary["steps"])
    assert (tmp_path / "seo-workspace" / "data" / "publish-post-media-handoff.json").exists()
    assert summary["no_media_upload_executed"] is True
    assert summary["no_cms_write_executed"] is True
