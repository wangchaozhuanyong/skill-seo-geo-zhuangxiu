from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "seo-workspace" / "tools" / "service_pattern_rich_editor.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("service_pattern_rich_editor", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_patterns(tmp_path: Path) -> None:
    payload = {
        "services": {
            "builtin": {
                "urls": {
                    "en": "https://flashcast.com.my/en/services/builtin",
                    "zh": "https://flashcast.com.my/zh/services/builtin",
                },
                "keywords": {"en": "custom built in furniture malaysia", "zh": "定制家具 吉隆坡"},
                "service_name": {"en": "Custom Built-In Furniture", "zh": "定制家具"},
                "h1": {"en": "Custom Built-In Furniture Planning", "zh": "定制家具与收纳规划"},
                "positioning": {"en": "Plan storage and cabinet details.", "zh": "规划收纳与柜体细节。"},
                "needs": {"en": ["wardrobe", "TV cabinet"], "zh": ["衣柜", "电视柜"]},
                "sections": {"en": ["Material direction", "Hardware planning"], "zh": ["材料方向", "五金规划"]},
                "faq": {
                    "en": ["Can renderings be used? | Yes, as concepts."],
                    "zh": ["可以用效果图吗？|可以，必须标注为概念设计。"],
                },
                "image_concepts": {
                    "en": ["wardrobe rendering concept", "TV cabinet material board"],
                    "zh": ["衣柜效果图方案", "电视柜材料 mood board"],
                },
                "cta": {"en": "Share dimensions.", "zh": "提交尺寸。"},
                "schema": ["Service", "FAQPage", "ImageObject"],
                "owner_input_required": ["final CTA/contact display"],
            }
        }
    }
    data_dir = tmp_path / "seo-workspace" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "service-content-patterns.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_service_pattern_rich_editor_outputs_multi_image_editor(tmp_path: Path):
    tool = load_tool()
    write_patterns(tmp_path)

    artifacts = tool.run(tmp_path, "https://flashcast.com.my/zh/services/builtin", "2026-06-11")
    payload = json.loads(artifacts["payload"].read_text(encoding="utf-8"))
    html_text = artifacts["editor_html"].read_text(encoding="utf-8")

    assert payload["status"] == "service_pattern_rich_editor_ready_for_owner_review"
    assert payload["safety"]["no_live_actions_executed"] is True
    assert "multiple_inline_concept_images" in payload["editor_capabilities"]
    assert sum(1 for item in payload["languages"]["zh"]["blocks"] if item["type"] == "image") == 2
    assert sum(1 for item in payload["languages"]["en"]["blocks"] if item["type"] == "image") == 2
    assert "Add Image" in html_text
    assert "Export Edited JSON" in html_text
    assert "NEEDS_MEDIA_UPLOAD:flash-cast-builtin-zh-concept-1.webp" in html_text
    assert "owner_edited_export_pending_execution_approval" in html_text

    match = re.search(r'<script id="source" type="application/json">(.*?)</script>', html_text, flags=re.S)
    assert match
    script_payload = json.loads(match.group(1))
    assert script_payload["service_slug"] == "builtin"
