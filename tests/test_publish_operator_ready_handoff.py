from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_operator_ready_handoff
from tests.test_content_studio_owner_review_package import seed_workspace


operator_ready_handoff = load_publish_operator_ready_handoff()


def test_operator_ready_handoff_writes_no_write_summary_when_blocked(tmp_path: Path):
    seed_workspace(tmp_path)
    website_root = tmp_path / "website"
    website_root.mkdir(parents=True, exist_ok=True)

    summary, artifacts = operator_ready_handoff.run_publish_operator_ready_handoff(
        tmp_path,
        website_root=str(website_root),
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        media_ready=False,
        allow_blocked_plan=True,
        allow_blocked_operator=True,
    )

    assert summary["status"] == "operator_ready_handoff_blocked"
    assert summary["operator_ready"] is False
    assert summary["execution_input_ready"] is False
    assert summary["no_cms_write_executed"] is True
    assert "warning_summary" in summary
    assert (tmp_path / "seo-workspace" / "data" / "publish-operator-ready-handoff.json").exists()
    report = next((tmp_path / "seo-workspace" / "reports").glob("*-publish-operator-ready-handoff.md")).read_text(encoding="utf-8")
    assert "完整 warning 证据数量" in report
    assert any(step["step"] == "publish_approved_execution_input" for step in summary["steps"])
    assert artifacts
