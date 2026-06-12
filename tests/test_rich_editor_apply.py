import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_rich_editor_apply


rich_editor_apply = load_rich_editor_apply()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_apply_workspace(tmp_path: Path) -> Path:
    editor_export = tmp_path / "seo-workspace" / "data" / "edited-export.json"
    write_json(
        editor_export,
        {
            "status": "owner_edited_export_pending_execution_approval",
            "target_url": "https://flashcast.com.my/en/services/kitchen",
            "paired_url": "https://flashcast.com.my/zh/services/kitchen",
            "languages": {
                "zh": {
                    "blocks": [
                        {
                            "editor_id": "zh-hero",
                            "type": "hero",
                            "sort_order": 1,
                            "editable_fields": {"heading": "原始中文标题", "body": "原始中文正文"},
                            "media": {
                                "filename": "hero.webp",
                                "alt": "原始 alt",
                                "caption": "原始图注",
                                "concept_label": "概念设计 / 效果图方案",
                                "claim_boundary": "Generated visual for design/rendering concept only; not a real project photo.",
                                "file_url": "NEEDS_MEDIA_UPLOAD:hero.webp",
                            },
                        },
                        {
                            "editor_id": "zh-cta",
                            "type": "cta",
                            "sort_order": 2,
                            "editable_fields": {"heading": "原始 CTA", "body": "原始 CTA 正文", "href": "/zh/quote", "label": "获取报价"},
                            "media": {},
                        },
                    ],
                    "edited_blocks": [
                        {
                            "editor_id": "zh-cta",
                            "type": "cta",
                            "sort_order": 1,
                            "edited_fields": {"heading": "先咨询厨房动线", "body": "把厨房照片和需求发给我们。", "href": "/zh/quote", "label": "预约厨房规划"},
                        },
                        {
                            "editor_id": "zh-hero",
                            "type": "hero",
                            "sort_order": 2,
                            "edited_fields": {
                                "heading": "厨房装修图文方案",
                                "body": "编辑后的中文正文。",
                                "media.alt": "编辑后的厨房效果图 alt",
                                "media.caption": "编辑后的图注，仍是效果图方案。",
                            },
                        },
                        {
                            "editor_id": "zh-new-image-1",
                            "type": "image",
                            "sort_order": 3,
                            "is_new": True,
                            "edited_fields": {
                                "heading": "新增收纳效果图方案",
                                "body": "新增的图文混排图片说明。",
                                "media.filename": "new-storage-rendering.webp",
                                "media.file_url": "NEEDS_MEDIA_UPLOAD:new-storage-rendering.webp",
                                "media.alt": "新增收纳效果图 alt",
                                "media.caption": "新增图注，标注为效果图方案。",
                                "media.concept_label": "概念设计 / 效果图方案",
                                "media.claim_boundary": "Concept/rendering asset only; not real project proof.",
                            },
                        },
                    ],
                },
                "en": {
                    "blocks": [
                        {
                            "editor_id": "en-hero",
                            "type": "hero",
                            "sort_order": 1,
                            "editable_fields": {"heading": "Original English Heading", "body": "Original English body."},
                            "media": {
                                "filename": "hero.webp",
                                "alt": "Original alt",
                                "caption": "Original caption",
                                "concept_label": "design concept / rendering concept",
                                "claim_boundary": "Generated visual for design/rendering concept only; not a real project photo.",
                                "file_url": "NEEDS_MEDIA_UPLOAD:hero.webp",
                            },
                        }
                    ],
                    "edited_blocks": [
                        {
                            "editor_id": "en-hero",
                            "type": "hero",
                            "sort_order": 1,
                            "edited_fields": {
                                "heading": "Kitchen Renovation Visual Plan",
                                "body": "Edited English body.",
                                "media.alt": "Edited kitchen rendering alt",
                                "media.caption": "Edited caption, still a rendering concept.",
                            },
                        }
                    ],
                },
            },
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
                "title_zh": "旧中文标题",
                "title_en": "Old English Title",
                "content_zh": "<p>old zh</p>",
                "content_en": "<p>old en</p>",
                "image_url": "old.webp",
                "status": "draft",
            },
        },
    )
    return editor_export


def test_rich_editor_apply_writes_editor_applied_payload(tmp_path):
    editor_export = seed_apply_workspace(tmp_path)

    result, artifacts = rich_editor_apply.run_rich_editor_apply(tmp_path, editor_export_path=str(editor_export))

    assert result.ok
    assert result.status == "editor_applied_payload_ready_for_owner_review"
    payload_path, summary_path, report_path = artifacts
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")

    assert payload["payload"]["title_zh"] == "厨房装修图文方案"
    assert payload["payload"]["title_en"] == "Kitchen Renovation Visual Plan"
    assert "编辑后的厨房效果图 alt" in payload["payload"]["content_zh"]
    assert "新增收纳效果图方案" in payload["payload"]["content_zh"]
    assert "新增收纳效果图 alt" in payload["payload"]["content_zh"]
    assert "Edited kitchen rendering alt" in payload["payload"]["content_en"]
    assert payload["payload"]["content_zh"].find("先咨询厨房动线") < payload["payload"]["content_zh"].find("厨房装修图文方案")
    assert payload["payload"]["image_url"] == "NEEDS_MEDIA_UPLOAD:hero.webp"
    assert payload["editor_applied"]["no_cms_write_executed"] is True
    assert payload["editor_applied"]["no_live_actions_executed"] is True
    assert summary["used_edited_blocks"] is True
    assert summary["qa_checked"] is True
    assert summary["qa_media_block_count"] == 3
    assert "NEEDS_MEDIA_UPLOAD:hero.webp" in report
    assert "NEEDS_MEDIA_UPLOAD:new-storage-rendering.webp" in report
    assert "未登录 CMS、未上传媒体、未写数据库、未发布、未部署" in report


def test_rich_editor_apply_blocks_without_editor_export(tmp_path):
    result, artifacts = rich_editor_apply.run_rich_editor_apply(tmp_path)

    assert not result.ok
    assert result.status == "rich_editor_apply_blocked"
    assert any("Run rich-editor first" in blocker for blocker in result.blockers)
    assert artifacts[0].exists()


def test_rich_editor_apply_blocks_image_without_claim_boundary(tmp_path):
    editor_export = seed_apply_workspace(tmp_path)
    payload = json.loads(editor_export.read_text(encoding="utf-8"))
    new_image = payload["languages"]["zh"]["edited_blocks"][2]
    del new_image["edited_fields"]["media.claim_boundary"]
    editor_export.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result, artifacts = rich_editor_apply.run_rich_editor_apply(tmp_path, editor_export_path=str(editor_export))

    assert not result.ok
    assert result.status == "rich_editor_apply_blocked"
    assert any("missing media.claim_boundary" in blocker for blocker in result.blockers)
    output = json.loads(artifacts[0].read_text(encoding="utf-8"))
    summary = json.loads(artifacts[1].read_text(encoding="utf-8"))
    assert output == {}
    assert summary["qa_checked"] is True


def test_rich_editor_apply_blocks_unsupported_claim_text(tmp_path):
    editor_export = seed_apply_workspace(tmp_path)
    payload = json.loads(editor_export.read_text(encoding="utf-8"))
    payload["languages"]["en"]["edited_blocks"][0]["edited_fields"]["body"] = "Customer review: fixed price and warranty included."
    editor_export.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result, artifacts = rich_editor_apply.run_rich_editor_apply(tmp_path, editor_export_path=str(editor_export))

    assert not result.ok
    assert result.status == "rich_editor_apply_blocked"
    assert any("unsupported factual claim" in blocker for blocker in result.blockers)
    report = artifacts[2].read_text(encoding="utf-8")
    assert "Customer review" in report


def test_rich_editor_apply_allows_safety_instruction_with_claim_words(tmp_path):
    editor_export = seed_apply_workspace(tmp_path)
    payload = json.loads(editor_export.read_text(encoding="utf-8"))
    payload["languages"]["zh"]["edited_blocks"][0]["edited_fields"]["body"] = "不要写固定价格、固定工期或保修承诺。"
    editor_export.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result, _ = rich_editor_apply.run_rich_editor_apply(tmp_path, editor_export_path=str(editor_export))

    assert result.ok
    assert result.status == "editor_applied_payload_ready_for_owner_review"
