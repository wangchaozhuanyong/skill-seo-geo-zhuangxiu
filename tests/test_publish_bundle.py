import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_bundle


publish_bundle = load_publish_bundle()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_ready_bundle_workspace(tmp_path: Path) -> None:
    data_dir = tmp_path / "seo-workspace" / "data"
    write_json(
        data_dir / "publish-readiness.json",
        {
            "status": "ready_for_owner_approved_publish_handoff",
            "blockers": [],
            "warnings": [],
            "evidence": {
                "target_urls": [TARGET_URL, PAIRED_URL],
                "valid_latest_research_source_count": 1,
                "latest_research_sources": [
                    {
                        "target_url": TARGET_URL,
                        "source_title": "Search Central structured data guidance",
                        "source_url": "https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data",
                        "publisher": "Google Search Central",
                        "claim_boundary": "general guidance only; not a FLASH CAST business claim",
                    }
                ],
                "media_url_map_present": True,
                "media_ready_payload_present": True,
                "editor_applied_payload_present": True,
                "editor_applied_used_edited_blocks": True,
            },
        },
    )
    write_json(
        data_dir / "cms-write-request.json",
        {
            "status": "dry_run_write_request_ready",
            "blockers": [],
            "warnings": [],
            "write_request": {
                "action": "dry_run_only_no_cms_write",
                "no_cms_write_executed": True,
                "target_url": TARGET_URL,
                "paired_url": PAIRED_URL,
                "table": "services",
                "admin_helper": "saveAdminService",
                "cms_payload_path": str(data_dir / "rich-content-cms-payload.media-ready.json"),
                "cms_payload_selection": "auto_media_ready",
                "planned_helper_call": {
                    "function": "saveAdminService",
                    "input": {
                        "record": {
                            "slug": "kitchen",
                            "title_en": "Kitchen Image-Rich Renovation Plan",
                            "image_url": "https://cdn.example.com/hero.webp",
                            "status": "draft",
                        },
                        "nextStatus": "draft",
                    },
                },
                "payload_keys": ["slug", "title_en", "image_url", "status"],
                "media_placeholders": [],
                "seo_assets_after_write": ["regenerate seo-manifest", "regenerate sitemap.xml"],
            },
        },
    )


def test_publish_bundle_blocks_without_readiness_or_write_request(tmp_path):
    result, artifacts = publish_bundle.run_publish_bundle(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_execution_bundle"
    assert any("publish-readiness.json" in blocker for blocker in result.blockers)
    assert any("cms-write-request.json" in blocker for blocker in result.blockers)
    bundle_path, report_path = artifacts
    assert bundle_path.exists()
    assert report_path.exists()


def test_publish_bundle_blocks_when_readiness_or_cms_request_not_ready(tmp_path):
    data_dir = tmp_path / "seo-workspace" / "data"
    write_json(data_dir / "publish-readiness.json", {"status": "blocked_before_publish_handoff", "blockers": ["Missing media-ready payload."]})
    write_json(
        data_dir / "cms-write-request.json",
        {
            "status": "blocked_before_cms_write",
            "blockers": ["Media placeholders remain."],
            "write_request": {
                "no_cms_write_executed": True,
                "planned_helper_call": {"function": "saveAdminService", "input": {}},
                "media_placeholders": ["payload.image_url=NEEDS_MEDIA_UPLOAD:hero.webp"],
            },
        },
    )

    result, _ = publish_bundle.run_publish_bundle(tmp_path)

    assert not result.ok
    assert any("Publish readiness is not ready" in blocker for blocker in result.blockers)
    assert any("CMS write request is not dry_run_write_request_ready" in blocker for blocker in result.blockers)
    assert any("media placeholders" in blocker.lower() for blocker in result.blockers)


def test_publish_bundle_creates_ready_execution_bundle_without_writing_live(tmp_path):
    seed_ready_bundle_workspace(tmp_path)

    result, artifacts = publish_bundle.run_publish_bundle(tmp_path)

    assert result.ok
    assert result.status == "execution_bundle_ready_for_approved_executor"
    assert result.bundle["admin_helper"] == "saveAdminService"
    assert result.bundle["planned_helper_call"]["function"] == "saveAdminService"
    assert result.bundle["media_ready_payload_present"] is True
    assert result.bundle["editor_applied_used_edited_blocks"] is True
    assert result.bundle["no_cms_write_executed"] is True
    assert result.bundle["no_live_actions_executed"] is True
    bundle_path, report_path = artifacts
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert payload["bundle"]["action"] == "sealed_execution_bundle_only_no_cms_write"
    assert "sealed bundle only" in report_path.read_text(encoding="utf-8")
