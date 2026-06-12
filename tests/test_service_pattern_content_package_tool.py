from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_service_pattern_content_package


service_pattern_content_package = load_service_pattern_content_package()


def write_patterns(tmp_path: Path) -> None:
    payload = {
        "version": "test",
        "status": "owner_review_required",
        "services": {
            "builtin": {
                "urls": {
                    "en": "https://flashcast.com.my/en/services/builtin",
                    "zh": "https://flashcast.com.my/zh/services/builtin",
                },
                "keywords": {"en": "custom built in furniture malaysia", "zh": "定制家具 吉隆坡"},
                "service_name": {"en": "Custom Built-In Furniture", "zh": "定制家具"},
                "h1": {"en": "Custom Built-In Furniture Planning", "zh": "定制家具与收纳规划"},
                "positioning": {"en": "Plan cabinet details.", "zh": "规划柜体细节。"},
                "needs": {"en": ["wardrobe", "TV cabinet"], "zh": ["衣柜", "电视柜"]},
                "sections": {"en": ["Material direction"], "zh": ["材料方向"]},
                "faq": {
                    "en": ["Can renderings be used?|Yes, as concepts."],
                    "zh": ["可以用效果图吗？|可以，必须标注为概念设计。"],
                },
                "image_concepts": {
                    "en": ["wardrobe rendering concept", "TV cabinet material board"],
                    "zh": ["衣柜效果图方案", "电视柜材料 mood board"],
                },
                "cta": {"en": "Share dimensions.", "zh": "提交尺寸。"},
                "schema": ["Service", "FAQPage", "ImageObject"],
                "owner_input_required": ["final CTA/contact display"],
            },
            "approval": {
                "urls": {
                    "en": "https://flashcast.com.my/en/services/approval",
                    "zh": "https://flashcast.com.my/zh/services/approval",
                },
                "keywords": {"en": "renovation permit application malaysia", "zh": "装修许可申请"},
                "service_name": {"en": "Renovation Permit Application", "zh": "装修许可申请"},
                "h1": {"en": "Renovation Permit Application Planning", "zh": "装修许可申请规划"},
                "positioning": {"en": "Plan permit documents.", "zh": "规划审批资料。"},
                "needs": {"en": ["document checklist"], "zh": ["资料清单"]},
                "sections": {"en": ["Document planning"], "zh": ["资料规划"]},
                "faq": {"en": ["Is this legal advice?|No."], "zh": ["这是法律意见吗？|不是。"]},
                "image_concepts": {"en": ["permit document planning concept"], "zh": ["审批资料规划概念图"]},
                "cta": {"en": "Ask for document guidance.", "zh": "咨询资料准备建议。"},
                "schema": ["Service", "FAQPage", "ImageObject"],
                "owner_input_required": ["final CTA/contact display"],
            },
        },
    }
    data_dir = tmp_path / "seo-workspace" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "service-content-patterns.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_service_pattern_content_package_builds_single_full_package(tmp_path: Path):
    write_patterns(tmp_path)

    summary, artifacts = service_pattern_content_package.run_service_pattern_content_package(tmp_path, service_slug="builtin", today="2026-06-11")
    summary_path, _, report_path = artifacts
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    package = summary["packages"][0]
    package_artifacts = package["artifacts"]

    assert summary["status"] == "owner_review_package_ready"
    assert summary["no_live_actions_executed"] is True
    assert package["service_slug"] == "builtin"
    assert package["media_count"] == 4
    assert package["media_status"] == "needs_media_generation_or_upload"
    assert Path(package_artifacts["brief"]).is_file()
    assert Path(package_artifacts["rich_editor_html"]).is_file()
    assert Path(package_artifacts["cms_payload"]).is_file()
    assert Path(package_artifacts["media_media_plan"]).is_file()
    assert "NEEDS_MEDIA_UPLOAD:" in Path(package_artifacts["cms_payload"]).read_text(encoding="utf-8")
    assert "概念设计" in report_path.read_text(encoding="utf-8")


def test_service_pattern_content_package_builds_all_services(tmp_path: Path):
    write_patterns(tmp_path)

    summary, artifacts = service_pattern_content_package.run_service_pattern_content_package(
        tmp_path,
        all_services=True,
        today="2026-06-11",
        public_base_url="https://cdn.example.com/flash-cast/service-pattern",
    )
    summary_path, _, _ = artifacts
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["scope"] == "all-services"
    assert summary["package_count"] == 2
    assert summary["no_media_upload_executed"] is True
    assert {item["service_slug"] for item in summary["packages"]} == {"approval", "builtin"}
    assert all(item["media_status"] == "media_ready_payload_draft_generated" for item in summary["packages"])
    for item in summary["packages"]:
        ready_path = Path(item["artifacts"]["media_media_ready_cms_payload"])
        assert ready_path.is_file()
        assert "NEEDS_MEDIA_UPLOAD:" not in ready_path.read_text(encoding="utf-8")
