from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "seo-workspace" / "tools" / "service_pattern_brief_preview.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("service_pattern_brief_preview", TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_service_pattern_preview_generates_target_specific_brief(tmp_path: Path):
    tool = load_tool()
    data_dir = tmp_path / "seo-workspace" / "data"
    data_dir.mkdir(parents=True)
    payload = {
        "services": {
            "approval": {
                "urls": {
                    "en": "https://flashcast.com.my/en/services/approval",
                    "zh": "https://flashcast.com.my/zh/services/approval",
                },
                "keywords": {"en": "renovation permit dbkl", "zh": "公寓装修申请 吉隆坡"},
                "service_name": {"en": "Permit and Drawing Support", "zh": "准证图纸支持"},
                "h1": {"en": "Renovation Approval Support", "zh": "装修申请与图纸支持"},
                "positioning": {"en": "Prepare approval notes safely.", "zh": "安全整理申请资料。"},
                "needs": {"en": ["management approval"], "zh": ["管理处申请"]},
                "sections": {"en": ["Document checklist"], "zh": ["文件清单"]},
                "faq": {
                    "en": ["What should I prepare? | Site photos and scope."],
                    "zh": ["需要准备什么？|现场照片和范围。"],
                },
                "image_concepts": {
                    "en": ["approval document rendering concept"],
                    "zh": ["申请资料效果图方案"],
                },
                "cta": {"en": "Share approval details.", "zh": "提交申请资料。"},
                "schema": ["Service", "FAQPage"],
                "owner_input_required": ["final CTA/contact display"],
            }
        }
    }
    (data_dir / "service-content-patterns.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    output = tool.run(tmp_path, "https://flashcast.com.my/en/services/approval", "2026-06-11")
    text = output.read_text(encoding="utf-8")

    assert output.name == "2026-06-11-approval-service-pattern-brief.md"
    assert "装修申请与图纸支持" in text
    assert "Renovation Approval Support" in text
    assert "公寓装修申请 吉隆坡" in text
    assert "renovation permit dbkl" in text
    assert "Residential Renovation" not in text
    assert "未登录 CMS、未上传媒体、未写源码页面、未发布、未部署" in text
