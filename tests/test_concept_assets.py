import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_concept_assets


concept_assets = load_concept_assets()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_concept_asset_workspace(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-asset-plan.json",
        {
            "status": "needs_media_generation_or_upload",
            "no_media_upload_executed": True,
            "media_assets": [
                {
                    "filename": "flash-cast-hero-rendering-concept.webp",
                    "usage_type": "hero",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    "prompt": "Create a premium kitchen renovation rendering concept with warm wood cabinets.",
                },
                {
                    "filename": "flash-cast-material-mood-board.webp",
                    "usage_type": "material",
                    "alt_zh": "FLASH CAST 材料 mood board",
                    "alt_en": "FLASH CAST material mood board",
                    "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    "prompt": "Create a material palette for kitchen cabinet, backsplash, countertop, and lighting.",
                },
            ],
        },
    )


def test_concept_assets_generates_svg_files_and_manifest(tmp_path):
    seed_concept_asset_workspace(tmp_path)

    result, artifacts = concept_assets.run_concept_assets(tmp_path)

    assert result.ok
    assert result.status == "concept_assets_generated"
    assert result.generated_count == 2
    manifest_path, report_path = artifacts
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["no_media_upload_executed"] is True
    assert manifest["assets"][0]["placeholder_filename"] == "flash-cast-hero-rendering-concept.webp"
    assert manifest["assets"][0]["generated_filename"] == "flash-cast-hero-rendering-concept.svg"
    svg_path = tmp_path / "seo-workspace" / "media" / "generated" / "flash-cast-hero-rendering-concept.svg"
    svg_text = svg_path.read_text(encoding="utf-8")
    assert "<svg" in svg_text
    assert "Generated visual for design planning only" in svg_text
    assert "Not a real project photo" in svg_text
    assert "flash-cast-hero-rendering-concept.webp" in report_path.read_text(encoding="utf-8")


def test_concept_assets_blocks_without_media_plan(tmp_path):
    result, artifacts = concept_assets.run_concept_assets(tmp_path)

    assert not result.ok
    assert result.status == "blocked_missing_media_plan"
    assert any("Run media-assets first" in blocker for blocker in result.blockers)
    assert artifacts[0].exists()
