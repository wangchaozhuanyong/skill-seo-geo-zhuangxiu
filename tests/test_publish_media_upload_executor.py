import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_media_upload_executor


media_upload_executor = load_publish_media_upload_executor()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_upload_plan(tmp_path: Path, *, bucket: str = "site-images") -> None:
    asset = tmp_path / "seo-workspace" / "media" / "generated" / "hero.svg"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>\n", encoding="utf-8")
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-upload-plan.json",
        {
            "status": "owner_review_required",
            "queue": [
                {
                    "queue_id": "media-upload-001",
                    "placeholder_filename": "hero.webp",
                    "public_filename": "hero.svg",
                    "local_path": str(asset),
                    "bucket": bucket,
                    "object_path": "media/seo-generated/2026-06-11/hero.svg",
                    "mime_type": "image/svg+xml",
                    "folder": "media",
                    "usage_type": "hero",
                    "alt_zh": "效果图方案",
                    "alt_en": "Rendering concept",
                    "claim_boundary": "Generated SVG design/rendering concept only; not a real project photo.",
                }
            ],
        },
    )


def test_publish_media_upload_executor_ready_dry_run_without_upload(tmp_path: Path):
    seed_upload_plan(tmp_path)

    summary, artifacts = media_upload_executor.run_publish_media_upload_executor(tmp_path)

    assert summary["status"] == "media_upload_executor_ready_dry_run"
    assert summary["media_upload_executed"] is False
    assert summary["no_media_upload_executed"] is True
    assert summary["blockers"] == []
    report = tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-publish-media-upload-executor.md"
    report_text = report.read_text(encoding="utf-8")
    assert "永远不直接上传媒体或写 media_assets 表" in report_text
    assert "网站管理后台媒体库" in report_text
    assert artifacts[0].exists()
    assert not artifacts[1].exists()
    assert artifacts[2].exists()


def test_publish_media_upload_executor_blocks_live_without_confirm_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("FLASHCAST_APPROVED_MEDIA_UPLOAD_RUN", raising=False)
    seed_upload_plan(tmp_path)

    summary, _ = media_upload_executor.run_publish_media_upload_executor(
        tmp_path,
        mode="live",
        confirm_upload=True,
    )

    assert summary["status"] == "blocked_before_media_upload_execution"
    assert summary["media_upload_executed"] is False
    assert any("FLASHCAST_APPROVED_MEDIA_UPLOAD_RUN" in blocker for blocker in summary["blockers"])
    assert any("Direct Supabase storage/media_assets writes are disabled" in blocker for blocker in summary["blockers"])


def test_publish_media_upload_executor_blocks_staging_direct_storage_write(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FLASHCAST_APPROVED_MEDIA_UPLOAD_RUN", "I_UNDERSTAND_THIS_UPLOADS_MEDIA")
    seed_upload_plan(tmp_path)

    summary, _ = media_upload_executor.run_publish_media_upload_executor(
        tmp_path,
        mode="staging",
        confirm_upload=True,
    )

    assert summary["status"] == "blocked_before_media_upload_execution"
    assert summary["direct_storage_write_disabled"] is True
    assert summary["required_upload_path"] == "website_admin_media_library"
    assert any("Direct Supabase storage/media_assets writes are disabled" in blocker for blocker in summary["blockers"])


def test_publish_media_upload_executor_blocks_wrong_bucket(tmp_path: Path):
    seed_upload_plan(tmp_path, bucket="private")

    summary, _ = media_upload_executor.run_publish_media_upload_executor(tmp_path, allowed_bucket="site-images")

    assert summary["status"] == "blocked_before_media_upload_execution"
    assert any("bucket is not allowed" in blocker for blocker in summary["blockers"])
