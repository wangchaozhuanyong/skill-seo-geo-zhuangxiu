import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_media_upload_plan


media_upload_plan = load_media_upload_plan()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_upload_plan_workspace(tmp_path: Path) -> None:
    asset_dir = tmp_path / "seo-workspace" / "media" / "generated"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "flash-cast-hero-rendering-concept.svg").write_text("<svg></svg>", encoding="utf-8")
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-asset-plan.json",
        {
            "status": "needs_media_generation_or_upload",
            "no_media_upload_executed": True,
            "media_assets": [
                {
                    "filename": "flash-cast-hero-rendering-concept.webp",
                    "target_url": "https://flashcast.com.my/en/services/kitchen",
                    "paired_url": "https://flashcast.com.my/zh/services/kitchen",
                    "folder": "media",
                    "usage_type": "hero",
                    "mime_type": "image/webp",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "claim_boundary": "Generated visual for design/rendering concept only; not a real project photo.",
                }
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "concept-asset-manifest.json",
        {
            "status": "concept_assets_generated",
            "no_media_upload_executed": True,
            "assets": [
                {
                    "placeholder_filename": "flash-cast-hero-rendering-concept.webp",
                    "generated_filename": "flash-cast-hero-rendering-concept.svg",
                    "local_path": str(asset_dir / "flash-cast-hero-rendering-concept.svg"),
                    "mime_type": "image/svg+xml",
                    "claim_boundary": "Generated SVG design/rendering concept only; not a real project photo.",
                }
            ],
        },
    )
    write_csv(
        tmp_path / "seo-workspace" / "data" / "media-file-manifest.csv",
        "\n".join(
            [
                "filename,public_filename,local_path,exists,file_url,usage_type,mime_type,placeholder_mime_type,alt_zh,alt_en,claim_boundary",
                f"flash-cast-hero-rendering-concept.webp,flash-cast-hero-rendering-concept.svg,{asset_dir / 'flash-cast-hero-rendering-concept.svg'},yes,,hero,image/svg+xml,image/webp,FLASH CAST 服务页效果图方案主图,FLASH CAST service page rendering concept,Generated SVG design/rendering concept only; not a real project photo.",
            ]
        )
        + "\n",
    )


def test_media_upload_plan_generates_queue_and_record_drafts(tmp_path):
    seed_upload_plan_workspace(tmp_path)

    result, artifacts = media_upload_plan.run_media_upload_plan(tmp_path)

    assert result.ok
    assert result.status == "owner_review_required"
    assert result.queue_count == 1
    queue_path, plan_path, report_path = artifacts
    queue = queue_path.read_text(encoding="utf-8")
    assert "uploadAdminMediaObject" in queue
    assert "createAdminMediaAsset" in queue
    assert "NEEDS_PUBLIC_URL:site-images/media/seo-generated" in queue
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["no_media_upload_executed"] is True
    assert plan["media_assets_record_drafts"][0]["mime_type"] == "image/svg+xml"
    assert plan["media_assets_record_drafts"][0]["alt_en"] == "FLASH CAST service page rendering concept"
    assert "未上传媒体" in report_path.read_text(encoding="utf-8")


def test_media_upload_plan_blocks_without_concept_manifest(tmp_path):
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-asset-plan.json",
        {"media_assets": [{"filename": "missing.webp"}]},
    )

    result, artifacts = media_upload_plan.run_media_upload_plan(tmp_path)

    assert not result.ok
    assert result.status == "blocked_missing_media_upload_inputs"
    assert any("Run concept-assets first" in blocker for blocker in result.blockers)
    assert artifacts[0].exists()
