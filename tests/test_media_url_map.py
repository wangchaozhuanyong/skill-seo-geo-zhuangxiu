import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_media_url_map


media_url_map = load_media_url_map()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_url_map_workspace(tmp_path: Path) -> Path:
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-asset-plan.json",
        {
            "status": "needs_media_generation_or_upload",
            "no_media_upload_executed": True,
            "media_assets": [
                {
                    "filename": "flash-cast-hero-rendering-concept.webp",
                    "usage_type": "hero",
                    "mime_type": "image/webp",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "claim_boundary": "Generated visual for design/rendering concept only; not a real project photo or customer case proof.",
                },
                {
                    "filename": "flash-cast-material-mood-board.webp",
                    "usage_type": "material",
                    "mime_type": "image/webp",
                    "alt_zh": "FLASH CAST 材料 mood board",
                    "alt_en": "FLASH CAST material mood board",
                    "claim_boundary": "Generated visual for design/rendering concept only; not a real project photo or customer case proof.",
                },
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-blocks.json",
        {
            "metadata": {"target_url": "https://flashcast.com.my/en/services/kitchen"},
            "media_placeholders": [
                {
                    "filename": "flash-cast-hero-rendering-concept.webp",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "concept_label": "concept",
                },
                {
                    "filename": "flash-cast-material-mood-board.webp",
                    "alt_zh": "FLASH CAST 材料 mood board",
                    "alt_en": "FLASH CAST material mood board",
                    "concept_label": "concept",
                },
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.json",
        {
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {
                "slug": "kitchen",
                "content_en": '<img src="flash-cast-hero-rendering-concept.webp" alt="hero">',
                "content_zh": '<img src="flash-cast-material-mood-board.webp" alt="材料">',
                "image_url": "NEEDS_MEDIA_UPLOAD:flash-cast-hero-rendering-concept.webp",
                "status": "draft",
            },
        },
    )
    asset_dir = tmp_path / "seo-workspace" / "media" / "generated"
    asset_dir.mkdir(parents=True, exist_ok=True)
    return asset_dir


def test_media_url_map_blocks_when_files_or_public_url_missing(tmp_path):
    asset_dir = seed_url_map_workspace(tmp_path)
    (asset_dir / "flash-cast-hero-rendering-concept.webp").write_bytes(b"fake webp")

    result, artifacts = media_url_map.run_media_url_map(tmp_path, asset_dir=str(asset_dir))

    assert not result.ok
    assert result.status == "blocked_missing_media_files_or_url"
    assert any("Public base URL missing" in blocker for blocker in result.blockers)
    assert any("flash-cast-material-mood-board.webp" in blocker for blocker in result.blockers)
    manifest_path, map_path, report_path = artifacts
    assert manifest_path.exists()
    assert map_path is None
    assert "exists: `no`" in report_path.read_text(encoding="utf-8")


def test_media_url_map_generates_map_and_media_ready_payload(tmp_path):
    asset_dir = seed_url_map_workspace(tmp_path)
    (asset_dir / "flash-cast-hero-rendering-concept.webp").write_bytes(b"fake webp")
    (asset_dir / "flash-cast-material-mood-board.webp").write_bytes(b"fake webp")

    result, artifacts = media_url_map.run_media_url_map(
        tmp_path,
        asset_dir=str(asset_dir),
        public_base_url="https://cdn.example.com/media",
    )

    assert result.ok
    assert result.status == "media_url_map_ready"
    manifest_path, map_path, report_path = artifacts
    assert manifest_path.exists()
    assert map_path is not None
    url_map = json.loads(map_path.read_text(encoding="utf-8"))
    assert url_map["flash-cast-hero-rendering-concept.webp"] == "https://cdn.example.com/media/flash-cast-hero-rendering-concept.webp"
    ready_payload = json.loads((tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json").read_text(encoding="utf-8"))
    serialized = json.dumps(ready_payload, ensure_ascii=False)
    assert "NEEDS_MEDIA_UPLOAD" not in serialized
    assert 'src="https://cdn.example.com/media/flash-cast-hero-rendering-concept.webp"' in ready_payload["payload"]["content_en"]
    assert "media_url_map" in report_path.read_text(encoding="utf-8")


def test_media_url_map_accepts_svg_concept_assets_for_webp_placeholders(tmp_path):
    asset_dir = seed_url_map_workspace(tmp_path)
    (asset_dir / "flash-cast-hero-rendering-concept.svg").write_text("<svg></svg>", encoding="utf-8")
    (asset_dir / "flash-cast-material-mood-board.svg").write_text("<svg></svg>", encoding="utf-8")

    result, artifacts = media_url_map.run_media_url_map(
        tmp_path,
        asset_dir=str(asset_dir),
        public_base_url="https://cdn.example.com/media",
    )

    assert result.ok
    manifest_path, map_path, _ = artifacts
    assert map_path is not None
    manifest = manifest_path.read_text(encoding="utf-8")
    assert "flash-cast-hero-rendering-concept.svg" in manifest
    assert "image/svg+xml" in manifest
    url_map = json.loads(map_path.read_text(encoding="utf-8"))
    assert url_map["flash-cast-hero-rendering-concept.webp"] == "https://cdn.example.com/media/flash-cast-hero-rendering-concept.svg"
    ready_payload = json.loads((tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json").read_text(encoding="utf-8"))
    assert 'src="https://cdn.example.com/media/flash-cast-hero-rendering-concept.svg"' in ready_payload["payload"]["content_en"]
