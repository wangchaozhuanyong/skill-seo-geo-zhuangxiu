import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_owner_decision_editor


owner_decision_editor = load_content_studio_owner_decision_editor()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_decision_template(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json",
        {
            "status": "owner_decision_template_waiting_owner_input",
            "target_url": "https://flashcast.com.my/en/services/kitchen",
            "paired_url": "https://flashcast.com.my/zh/services/kitchen",
            "decision": {
                "content_approved": False,
                "media_urls_confirmed": False,
                "qa_approved": False,
                "latest_research_verified": False,
                "explicit_execution_requested": False,
                "allowed_execution_scope": "owner_review_only",
                "allowed_execution_scope_options": [
                    "owner_review_only",
                    "media_ready_handoff_only",
                    "approved_dry_run_only",
                    "operator_ready_handoff_only",
                    "live_publish_requires_separate_confirmation",
                ],
                "owner_notes": "",
            },
            "action_items_snapshot": [
                {"title_zh": "批准这个具体页面候选", "details_zh": "批准不等于真实发布。"}
            ],
            "approval_is_not_execution": True,
        },
    )


def test_owner_decision_editor_generates_local_html_form(tmp_path: Path):
    seed_decision_template(tmp_path)

    summary, artifacts = owner_decision_editor.run_content_studio_owner_decision_editor(tmp_path)

    assert summary["status"] == "owner_decision_editor_ready"
    assert summary["target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert summary["no_publish_executed"] is True
    html_path = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-content-studio-owner-decision-editor.html"
    html = html_path.read_text(encoding="utf-8")
    assert "业主决定表单" in html
    assert "content_approved" in html
    assert "content-studio-owner-decision.filled.json" in html
    assert "operator_ready_handoff_only" in html
    assert "approval_is_not_execution" in html
    assert "不会上传图片、不会写 CMS、不会发布、不会部署" in html
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision-editor.json").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-owner-decision-editor.md").exists()
    assert artifacts


def test_owner_decision_editor_blocks_without_template(tmp_path: Path):
    summary, _ = owner_decision_editor.run_content_studio_owner_decision_editor(tmp_path)

    assert summary["status"] == "owner_decision_editor_blocked"
    assert any("Missing owner decision template" in blocker for blocker in summary["blockers"])
