import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_publish_prep


content_studio_publish_prep = load_content_studio_publish_prep()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def seed_candidate_workspace(tmp_path: Path) -> None:
    target_url = "https://flashcast.com.my/en/services/kitchen"
    paired_url = "https://flashcast.com.my/zh/services/kitchen"
    draft_path = "seo-workspace/drafts/2026-06-11-en-services-kitchen-rich-content-package.md"
    write(
        tmp_path / draft_path,
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
            ]
        )
        + "\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "approved-publish-queue.csv",
        "draft_path,target_url,paired_url,page_type,target_kind,table,admin_helper,status,language_scope,rich_text_ready,image_strategy,required_gate,notes\n"
        f"{draft_path},{target_url},{paired_url},service,service,services,saveAdminService,owner_review_required,bilingual_pair_required,yes: package contains Publishing Field Map,concept images required,owner approval + explicit execution,Use saveAdminService\n",
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "publishing-field-map.json",
        {
            "field_map": {
                "service": {
                    "table": "services",
                    "admin_helper": "saveAdminService",
                    "content_fields": ["content_zh", "content_en"],
                    "image_fields": ["image_url", "alt_zh", "alt_en"],
                    "source_files": [],
                }
            },
            "website_evidence": {"status": "not_checked"},
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-publish-candidate.json",
        {
            "status": "content_studio_publish_candidate_waiting_owner_review",
            "target_url": target_url,
            "paired_url": paired_url,
            "matched_draft_path": draft_path,
            "candidate_row": {
                "draft_path": draft_path,
                "target_url": target_url,
                "paired_url": paired_url,
                "target_kind": "service",
                "table": "services",
                "admin_helper": "saveAdminService",
                "status": "owner_review_required",
            },
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json",
        {
            "target_kind": "service",
            "table": "services",
            "admin_helper": "saveAdminService",
            "payload": {"slug": "kitchen", "content_zh": "厨房装修设计方案", "content_en": "Kitchen renovation design concept"},
            "editor_applied": True,
        },
    )


def test_content_studio_publish_prep_generates_local_handoff(tmp_path):
    seed_candidate_workspace(tmp_path)

    summary, artifacts = content_studio_publish_prep.run_content_studio_publish_prep(tmp_path, allow_blocked_plan=True)

    assert summary["status"] == "publish_prep_ready_for_owner_review"
    assert summary["target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert summary["no_cms_write_executed"] is True
    assert summary["no_publish_executed"] is True
    assert summary["owner_review_required"] is True
    assert any(step["step"] == "publish_plan" for step in summary["steps"])
    assert any(step["step"] == "publish_execution_receipt" for step in summary["steps"])
    assert artifacts
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-publish-prep.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-execution-plan.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-execution-receipt.json").exists()


def test_content_studio_publish_prep_reports_missing_candidate(tmp_path):
    summary, _ = content_studio_publish_prep.run_content_studio_publish_prep(tmp_path)

    assert summary["status"] == "publish_prep_blocked_missing_candidate"
    assert any("Missing content-studio-publish-candidate.json" in blocker for blocker in summary["blockers"])
