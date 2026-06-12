import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_rich_editor


rich_editor = load_rich_editor()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_editor_workspace(tmp_path: Path) -> None:
    generated_dir = tmp_path / "seo-workspace" / "media" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    (generated_dir / "flash-cast-hero-rendering-concept.svg").write_text("<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>", encoding="utf-8")
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-blocks.json",
        {
            "metadata": {
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "paired_url": "https://flashcast.com.my/zh/services/kitchen",
                "keyword": "kitchen renovation malaysia",
            },
            "blocks_zh": [
                {
                    "id": "hero",
                    "type": "hero",
                    "heading": "厨房装修图文方案",
                    "body": "这是一份用于业主审核的厨房装修图文结构。",
                    "image": {
                        "filename": "flash-cast-hero-rendering-concept.webp",
                        "slot": "服务页效果图方案主图",
                        "alt": "FLASH CAST 厨房装修效果图方案",
                        "caption": "此图为规划/效果图方案，不作为真实完工案例或客户照片。",
                        "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    },
                },
                {"id": "cta", "type": "cta", "heading": "获取装修建议", "body": "发送空间需求。", "href": "/zh/quote", "label": "获取报价"},
            ],
            "blocks_en": [
                {
                    "id": "hero",
                    "type": "hero",
                    "heading": "Kitchen Renovation Image Plan",
                    "body": "An image-rich structure for owner review.",
                    "image": {
                        "filename": "flash-cast-hero-rendering-concept.webp",
                        "slot": "service page rendering concept",
                        "alt": "FLASH CAST kitchen renovation rendering concept",
                        "caption": "This image is a planning/rendering concept, not a completed real project or customer photo.",
                        "concept_label": "design concept / rendering concept",
                    },
                }
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-asset-plan.json",
        {
            "media_assets": [
                {
                    "filename": "flash-cast-hero-rendering-concept.webp",
                    "usage_type": "hero",
                    "file_url": "NEEDS_MEDIA_UPLOAD:flash-cast-hero-rendering-concept.webp",
                    "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    "claim_boundary": "Generated visual for design/rendering concept only; not a real project photo or customer case proof.",
                }
            ]
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "concept-asset-manifest.json",
        {
            "assets": [
                {
                    "placeholder_filename": "flash-cast-hero-rendering-concept.webp",
                    "generated_filename": "flash-cast-hero-rendering-concept.svg",
                    "local_path": str(generated_dir / "flash-cast-hero-rendering-concept.svg"),
                    "claim_boundary": "Generated SVG design/rendering concept only; not a real project photo or customer case proof.",
                }
            ]
        },
    )


def test_rich_editor_writes_editable_manifest_html_and_report(tmp_path):
    seed_editor_workspace(tmp_path)

    result, artifacts = rich_editor.run_rich_editor(tmp_path)

    assert result.ok
    assert result.status == "editable_rich_content_ready_for_owner_review"
    manifest_path, html_path, report_path = artifacts
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    editor_html = html_path.read_text(encoding="utf-8")
    report = report_path.read_text(encoding="utf-8")

    assert manifest["no_live_actions_executed"] is True
    assert manifest["no_cms_write_executed"] is True
    assert manifest["no_media_upload_executed"] is True
    assert "insert_new_heading_text_image_cta_blocks" in manifest["editor_capabilities"]
    assert "insert_multiple_inline_concept_images" in manifest["editor_capabilities"]
    assert manifest["languages"]["zh"]["blocks"][0]["can_drag"] is True
    assert manifest["languages"]["zh"]["blocks"][0]["editable_fields"]["heading"] == "厨房装修图文方案"
    assert "Generated visual for design/rendering concept only" in manifest["languages"]["en"]["blocks"][0]["media"]["claim_boundary"]
    assert manifest["media_library_handoff"][0]["generated_local_path"].endswith(".svg")
    assert "contenteditable=\"true\"" in editor_html
    assert "draggable=\"true\"" in editor_html
    assert "Add Text Block" in editor_html
    assert "Add Image Block" in editor_html
    assert "Add CTA Block" in editor_html
    assert "dataset.newBlock" in editor_html
    assert "Export Edited JSON" in editor_html
    assert "Download edited-export.json" in editor_html
    assert "rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json" in editor_html
    assert "link.download = 'edited-export.json'" in editor_html
    assert "未登录 CMS、未上传媒体、未写数据库、未发布、未部署" in report


def test_rich_editor_blocks_without_rich_blocks_payload(tmp_path):
    result, artifacts = rich_editor.run_rich_editor(tmp_path)

    assert not result.ok
    assert result.status == "rich_editor_blocked"
    assert any("Run rich-blocks first" in blocker for blocker in result.blockers)
    assert artifacts[0].exists()
