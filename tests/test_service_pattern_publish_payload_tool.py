from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "seo-workspace" / "tools" / "service_pattern_publish_payload.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("service_pattern_publish_payload", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_editor_payload(tmp_path: Path) -> Path:
    payload = {
        "status": "service_pattern_rich_editor_ready_for_owner_review",
        "target_url": "https://flashcast.com.my/en/services/builtin",
        "paired_url": "https://flashcast.com.my/zh/services/builtin",
        "service_slug": "builtin",
        "service_name": {"zh": "定制家具", "en": "Custom Built-In Furniture"},
        "languages": {
            "zh": {
                "blocks": [
                    {"id": "zh-hero", "type": "hero", "heading": "定制家具与收纳规划", "body": "规划柜体。"},
                    {
                        "id": "zh-image-1",
                        "type": "image",
                        "heading": "衣柜效果图方案",
                        "body": "概念图。",
                        "media": {
                            "filename": "flash-cast-builtin-zh-concept-1.webp",
                            "file_url": "NEEDS_MEDIA_UPLOAD:flash-cast-builtin-zh-concept-1.webp",
                            "alt": "定制家具效果图方案",
                            "caption": "概念设计，非真实案例。",
                            "concept_label": "概念设计 / 效果图方案",
                            "claim_boundary": "Concept only.",
                        },
                    },
                    {"id": "zh-cta", "type": "cta", "heading": "获取建议", "body": "提交尺寸。", "href": "/zh/quote", "label": "获取报价"},
                ]
            },
            "en": {
                "blocks": [
                    {"id": "en-hero", "type": "hero", "heading": "Custom Built-In Furniture Planning", "body": "Plan cabinets."},
                    {
                        "id": "en-image-1",
                        "type": "image",
                        "heading": "Wardrobe rendering concept",
                        "body": "Concept image.",
                        "media": {
                            "filename": "flash-cast-builtin-en-concept-1.webp",
                            "file_url": "NEEDS_MEDIA_UPLOAD:flash-cast-builtin-en-concept-1.webp",
                            "alt": "custom built-in furniture rendering concept",
                            "caption": "Design concept, not a real project.",
                            "concept_label": "design concept / rendering concept",
                            "claim_boundary": "Concept only.",
                        },
                    },
                    {"id": "en-cta", "type": "cta", "heading": "Request Advice", "body": "Share dimensions.", "href": "/en/quote", "label": "Request a Quote"},
                ],
                "edited_blocks": [
                    {"editor_id": "en-hero", "type": "hero", "sort_order": 1, "edited_fields": {"heading": "Edited Built-In Furniture Planning"}},
                    {"editor_id": "en-image-1", "type": "image", "sort_order": 2, "edited_fields": {"media.caption": "Edited rendering concept caption."}},
                    {"editor_id": "en-cta", "type": "cta", "sort_order": 3, "edited_fields": {"label": "Book Measurement"}},
                ],
            },
        },
    }
    path = tmp_path / "seo-workspace" / "data" / "builtin-service-pattern-rich-editor-payload.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_service_pattern_publish_payload_builds_cms_payload(tmp_path: Path):
    tool = load_tool()
    editor_payload_path = write_editor_payload(tmp_path)

    artifacts = tool.run(tmp_path, str(editor_payload_path))
    cms_payload = json.loads(artifacts["cms_payload"].read_text(encoding="utf-8"))
    summary = json.loads(artifacts["summary"].read_text(encoding="utf-8"))

    assert cms_payload["target_kind"] == "service"
    assert cms_payload["table"] == "services"
    assert cms_payload["admin_helper"] == "saveAdminService"
    assert cms_payload["payload"]["slug"] == "builtin"
    assert cms_payload["payload"]["status"] == "draft"
    assert cms_payload["payload"]["title_zh"] == "定制家具与收纳规划"
    assert cms_payload["payload"]["title_en"] == "Edited Built-In Furniture Planning"
    assert "seo-rich-editor-media" in cms_payload["payload"]["content_en"]
    assert "Edited rendering concept caption." in cms_payload["payload"]["content_en"]
    assert "Book Measurement" in cms_payload["payload"]["content_en"]
    assert cms_payload["editor_applied"]["no_live_actions_executed"] is True
    assert summary["used_edited_blocks"] is True
    assert summary["media_placeholders"] == [
        "flash-cast-builtin-en-concept-1.webp",
        "flash-cast-builtin-zh-concept-1.webp",
    ]
