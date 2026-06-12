import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_owner_review_package


owner_review_package = load_content_studio_owner_review_package()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def seed_workspace(tmp_path: Path) -> None:
    target_url = "https://flashcast.com.my/en/services/kitchen"
    paired_url = "https://flashcast.com.my/zh/services/kitchen"
    draft = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    media_file = tmp_path / "seo-workspace" / "media" / "generated" / "hero.svg"
    write(media_file, "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'><rect width='10' height='10'/></svg>\n")
    write(
        draft,
        "\n".join(
            [
                "# Rich Content Package",
                "",
                f"- 目标页面: `{target_url}`",
                f"- 配对页面: `{paired_url}`",
                "- 页面类型: service",
                "",
                "## Publishing Field Map",
                "",
                "- content_en: Kitchen renovation design concept",
                "- content_zh: 厨房装修设计方案",
                "- design concept / rendering concept",
            ]
        )
        + "\n",
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-postrun-summary.json",
        {"latest_run": {"target_url": target_url, "paired_url": paired_url}},
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-run.json",
        {"requested_target_url": target_url, "content_outputs": [str(draft)]},
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json",
        {"payload": {"content_zh": "x", "content_en": "x", "image_url": "NEEDS_MEDIA_UPLOAD:hero.webp"}},
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-upload-plan.json",
        {
            "status": "owner_review_required",
            "queue": [
                {
                    "queue_id": "media-upload-001",
                    "placeholder_filename": "hero.webp",
                    "public_filename": "hero.svg",
                    "local_path": str(media_file),
                    "object_path": "media/seo-generated/hero.svg",
                    "alt_zh": "厨房效果图方案",
                    "alt_en": "kitchen rendering concept",
                    "claim_boundary": "Generated visual for concept only.",
                }
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "concept-asset-manifest.json",
        {
            "status": "concept_assets_generated",
            "assets": [
                {
                    "placeholder_filename": "hero.webp",
                    "generated_filename": "hero.svg",
                    "local_path": str(media_file),
                    "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
                    "claim_boundary": "Generated visual for concept only.",
                }
            ],
        },
    )


def test_owner_review_package_runs_all_local_handoff_steps(tmp_path):
    seed_workspace(tmp_path)

    summary, artifacts = owner_review_package.run_content_studio_owner_review_package(tmp_path)

    assert summary["status"] == "owner_review_package_ready"
    assert summary["target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert [step["step"] for step in summary["steps"]] == [
        "content_studio_publish_candidate",
        "content_studio_publish_prep",
        "content_studio_approval_packet",
        "content_studio_owner_decision_editor",
        "content_studio_media_review_package",
        "content_studio_media_url_template",
        "content_studio_uploaded_url_map_draft",
        "content_studio_uploaded_url_map_editor",
        "content_studio_media_status",
        "content_studio_owner_decision_status",
    ]
    assert summary["no_publish_executed"] is True
    assert summary["media_status_summary"]["status"] == "media_urls_need_owner_input"
    assert summary["media_status_summary"]["counts"]["missing_public_url"] == 1
    commands = [item["command"] for item in summary["recommended_commands"]]
    assert any("rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json" in command for command in commands)
    assert any("media-assets" in command for command in commands)
    assert any("content-studio-owner-decision-import" in command for command in commands)
    assert any("content-studio-owner-decision-status" in command for command in commands)
    assert any("content-studio-decision-orchestrator" in command for command in commands)
    assert any("content-studio-uploaded-url-map-editor" in command for command in commands)
    assert any("content-studio-uploaded-url-map-import" in command for command in commands)
    assert any("content-studio-media-ready-handoff" in command for command in commands)
    assert any("content-studio-operator-ready-handoff" in command for command in commands)
    assert any("publish-readiness" in command for command in commands)
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-review-package.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision-editor.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision-status.json").exists()
    dashboard = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-content-studio-owner-review-dashboard.html"
    assert dashboard.exists()
    dashboard_html = dashboard.read_text(encoding="utf-8")
    assert "Content Studio Owner Review Dashboard" in dashboard_html
    assert "富文本图文编辑器" in dashboard_html
    assert "rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json" in dashboard_html
    assert "media-assets" in dashboard_html
    assert "业主决定表单" in dashboard_html
    assert "业主决定模板" in dashboard_html
    assert "业主决定状态" in dashboard_html
    assert "效果图审核 Gallery" in dashboard_html
    assert "图片 URL 填写表单" in dashboard_html
    assert "uploaded-url-map.filled.json" in dashboard_html
    assert "content-studio-uploaded-url-map-editor" in dashboard_html
    assert "content-studio-uploaded-url-map-import" in dashboard_html
    assert "No upload" in dashboard_html
    assert "0/1" in dashboard_html
    assert "Missing URLs" in dashboard_html
    assert "content-studio-media-ready-handoff" in dashboard_html
    assert "content-studio-operator-ready-handoff" in dashboard_html
    assert "content-studio-owner-decision-import" in dashboard_html
    assert "content-studio-decision-orchestrator" in dashboard_html
    assert "publish-readiness" in dashboard_html
    assert (tmp_path / "seo-workspace" / "data" / "uploaded-url-map.template.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-media-status.md").exists()
    assert (tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-content-studio-owner-decision-editor.html").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-owner-decision-status.md").exists()
    assert (tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-content-studio-media-review-gallery.html").exists()
    assert (tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-content-studio-uploaded-url-map-editor.html").exists()
    assert artifacts
