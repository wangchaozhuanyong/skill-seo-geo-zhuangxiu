import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_media_assets


media_assets = load_media_assets()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_media_workspace(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-blocks.json",
        {
            "metadata": {
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "paired_url": "https://flashcast.com.my/zh/services/kitchen",
            },
            "media_placeholders": [
                {
                    "filename": "flash-cast-hero-rendering-concept.webp",
                    "slot": "service page rendering concept",
                    "alt_zh": "FLASH CAST 服务页效果图方案主图",
                    "alt_en": "FLASH CAST service page rendering concept",
                    "caption_zh": "此图为规划/效果图方案，不作为真实完工案例或客户照片。",
                    "caption_en": "This image is a planning/rendering concept, not a completed real project or customer photo.",
                    "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    "prompt": "Create a kitchen rendering concept.",
                },
                {
                    "filename": "flash-cast-material-mood-board.webp",
                    "slot": "material mood board",
                    "alt_zh": "FLASH CAST 材料 mood board",
                    "alt_en": "FLASH CAST material mood board",
                    "caption_zh": "此图为规划/效果图方案，不作为真实完工案例或客户照片。",
                    "caption_en": "This image is a planning/rendering concept, not a completed real project or customer photo.",
                    "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    "prompt": "Create a material mood board.",
                },
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {
                "slug": "kitchen",
                "content_en": '<section><img src="flash-cast-hero-rendering-concept.webp" alt="hero"></section>',
                "content_zh": '<section><img src="flash-cast-material-mood-board.webp" alt="材料"></section>',
                "image_url": "NEEDS_MEDIA_UPLOAD:flash-cast-hero-rendering-concept.webp",
                "status": "draft",
            },
        },
    )


def test_media_assets_generates_plan_prompts_and_url_map_example(tmp_path):
    seed_media_workspace(tmp_path)

    result, artifacts = media_assets.run_media_assets(tmp_path)

    assert result.ok
    assert result.status == "needs_media_generation_or_upload"
    plan_path, map_path, prompts_path, ready_path = artifacts
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert ready_path is None
    assert plan["no_media_upload_executed"] is True
    assert len(plan["media_assets"]) == 2
    assert plan["media_assets"][0]["usage_type"] == "hero"
    assert plan["media_assets"][1]["usage_type"] == "material"
    assert "real project photo" in plan["media_assets"][0]["claim_boundary"]
    assert "flash-cast-hero-rendering-concept.webp" in map_path.read_text(encoding="utf-8")
    assert "Negative Prompt" in prompts_path.read_text(encoding="utf-8")


def test_media_assets_generates_media_ready_payload_when_url_map_complete(tmp_path):
    seed_media_workspace(tmp_path)
    url_map = tmp_path / "seo-workspace" / "data" / "media-url-map.json"
    write_json(
        url_map,
        {
            "flash-cast-hero-rendering-concept.webp": "https://cdn.example.com/hero.webp",
            "flash-cast-material-mood-board.webp": "https://cdn.example.com/material.webp",
        },
    )

    result, artifacts = media_assets.run_media_assets(tmp_path, url_map_path=str(url_map))

    assert result.ok
    assert result.status == "media_ready_payload_generated"
    ready_path = artifacts[3]
    assert ready_path is not None
    ready = json.loads(ready_path.read_text(encoding="utf-8"))
    serialized = json.dumps(ready, ensure_ascii=False)
    assert "NEEDS_MEDIA_UPLOAD" not in serialized
    assert 'src="https://cdn.example.com/hero.webp"' in ready["payload"]["content_en"]
    assert 'src="https://cdn.example.com/material.webp"' in ready["payload"]["content_zh"]
    assert ready["payload"]["image_url"] == "https://cdn.example.com/hero.webp"


def test_media_assets_uses_editor_applied_payload_when_present(tmp_path):
    seed_media_workspace(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {
                "slug": "kitchen",
                "title_en": "Edited Kitchen Plan",
                "content_en": '<section><img src="flash-cast-hero-rendering-concept.webp" alt="hero"></section>',
                "content_zh": (
                    '<section><img src="flash-cast-material-mood-board.webp" alt="材料"></section>'
                    '<figure class="seo-rich-editor-media">'
                    '<img src="NEEDS_MEDIA_UPLOAD:new-storage-rendering.webp" alt="新增收纳效果图 alt" loading="lazy" />'
                    '<figcaption>新增图注，标注为效果图方案。 <strong>概念设计 / 效果图方案</strong></figcaption>'
                    '<p class="seo-rich-claim-boundary">Concept/rendering asset only; not real project proof.</p>'
                    '</figure>'
                ),
                "image_url": "NEEDS_MEDIA_UPLOAD:flash-cast-hero-rendering-concept.webp",
                "status": "draft",
            },
            "editor_applied": {
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "paired_url": "https://flashcast.com.my/zh/services/kitchen",
                "no_cms_write_executed": True,
            },
        },
    )
    url_map = tmp_path / "seo-workspace" / "data" / "media-url-map.json"
    write_json(
        url_map,
        {
            "flash-cast-hero-rendering-concept.webp": "https://cdn.example.com/hero.webp",
            "flash-cast-material-mood-board.webp": "https://cdn.example.com/material.webp",
            "new-storage-rendering.webp": "https://cdn.example.com/new-storage.webp",
        },
    )

    result, artifacts = media_assets.run_media_assets(tmp_path, url_map_path=str(url_map))

    assert result.ok
    ready_path = artifacts[3]
    assert ready_path is not None
    plan = json.loads(artifacts[0].read_text(encoding="utf-8"))
    ready = json.loads(ready_path.read_text(encoding="utf-8"))
    assert plan["cms_payload_selection"] == "auto_editor_applied"
    assert len(plan["media_assets"]) == 3
    new_asset = next(item for item in plan["media_assets"] if item["filename"] == "new-storage-rendering.webp")
    assert new_asset["alt_zh"] == "新增收纳效果图 alt"
    assert new_asset["caption_zh"].startswith("新增图注")
    assert new_asset["claim_boundary"] == "Concept/rendering asset only; not real project proof."
    assert ready["payload"]["title_en"] == "Edited Kitchen Plan"
    assert "https://cdn.example.com/new-storage.webp" in ready["payload"]["content_zh"]
    assert ready["editor_applied"]["no_cms_write_executed"] is True


def test_media_assets_blocks_when_url_map_incomplete(tmp_path):
    seed_media_workspace(tmp_path)
    url_map = tmp_path / "seo-workspace" / "data" / "media-url-map.json"
    write_json(url_map, {"flash-cast-hero-rendering-concept.webp": "https://cdn.example.com/hero.webp"})

    result, artifacts = media_assets.run_media_assets(tmp_path, url_map_path=str(url_map))

    assert not result.ok
    assert any("flash-cast-material-mood-board.webp" in blocker for blocker in result.blockers)
    assert artifacts[3] is None
