from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "seo-workspace" / "tools" / "service_pattern_media_assets.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("service_pattern_media_assets", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_cms_payload(tmp_path: Path) -> Path:
    payload = {
        "target_kind": "service",
        "table": "services",
        "admin_helper": "saveAdminService",
        "payload": {
            "slug": "approval",
            "status": "draft",
            "title_zh": "装修许可申请规划",
            "title_en": "Renovation Permit Application Planning",
            "content_zh": (
                '<section><figure class="seo-rich-editor-media">'
                '<img src="NEEDS_MEDIA_UPLOAD:flash-cast-approval-zh-concept-1.webp" alt="装修许可申请动线概念图" loading="lazy" />'
                "<figcaption>审批文件整理概念图。 <strong>概念设计 / 效果图方案</strong></figcaption>"
                '<p class="seo-rich-claim-boundary">概念图，不是真实完工案例。</p>'
                "</figure></section>"
            ),
            "content_en": (
                '<section><figure class="seo-rich-editor-media">'
                '<img src="NEEDS_MEDIA_UPLOAD:flash-cast-approval-en-concept-1.webp" alt="renovation permit planning rendering concept" loading="lazy" />'
                "<figcaption>Document planning rendering concept. <strong>design concept / rendering concept</strong></figcaption>"
                '<p class="seo-rich-claim-boundary">Concept only; not completed project proof.</p>'
                "</figure></section>"
            ),
            "image_url": "NEEDS_MEDIA_UPLOAD:flash-cast-approval-en-concept-1.webp",
            "alt_zh": "装修许可申请动线概念图",
            "alt_en": "renovation permit planning rendering concept",
        },
        "editor_applied": {
            "target_url": "https://flashcast.com.my/en/services/approval",
            "paired_url": "https://flashcast.com.my/zh/services/approval",
            "no_media_upload_executed": True,
            "no_live_actions_executed": True,
        },
    }
    path = tmp_path / "seo-workspace" / "data" / "approval-service-pattern-cms-payload.editor-applied.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_service_pattern_media_assets_generates_plan_svg_and_url_map(tmp_path: Path):
    tool = load_tool()
    cms_payload_path = write_cms_payload(tmp_path)

    artifacts = tool.run(
        tmp_path,
        str(cms_payload_path),
        public_base_url="https://cdn.example.com/flash-cast/service-pattern/approval",
    )
    media_plan = json.loads(artifacts["media_plan"].read_text(encoding="utf-8"))
    manifest = json.loads(artifacts["concept_manifest"].read_text(encoding="utf-8"))
    url_map = json.loads(artifacts["media_url_map"].read_text(encoding="utf-8"))
    ready_payload = json.loads(artifacts["media_ready_cms_payload"].read_text(encoding="utf-8"))

    assert media_plan["status"] == "media_ready_payload_draft_generated"
    assert media_plan["no_media_upload_executed"] is True
    assert media_plan["media_count"] == 2
    assert media_plan["media_assets"][0]["asset_kind"] == "generated_design_rendering_concept"
    assert "NEEDS_MEDIA_UPLOAD:" not in json.dumps(ready_payload, ensure_ascii=False)
    assert url_map["flash-cast-approval-en-concept-1.webp"].endswith("flash-cast-approval-en-concept-1.svg")

    generated_paths = [Path(item["local_path"]) for item in manifest["assets"]]
    assert all(path.is_file() for path in generated_paths)
    assert "Generated visual for design planning only" in generated_paths[0].read_text(encoding="utf-8")
    assert artifacts["report"].read_text(encoding="utf-8").count("未上传媒体") >= 1


def test_service_pattern_media_assets_without_public_url_stays_draft_only(tmp_path: Path):
    tool = load_tool()
    cms_payload_path = write_cms_payload(tmp_path)

    artifacts = tool.run(tmp_path, str(cms_payload_path))
    summary = json.loads(artifacts["summary"].read_text(encoding="utf-8"))
    media_plan = json.loads(artifacts["media_plan"].read_text(encoding="utf-8"))

    assert summary["status"] == "needs_media_generation_or_upload"
    assert summary["no_image_api_called"] is True
    assert "media_ready_cms_payload" not in artifacts
    assert all(not item["public_file_url"] for item in media_plan["media_assets"])
