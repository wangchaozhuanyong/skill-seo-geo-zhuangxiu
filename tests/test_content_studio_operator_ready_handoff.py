from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_operator_ready_handoff,
    load_content_studio_owner_review_package,
)
from tests.test_content_studio_owner_review_package import seed_workspace


operator_ready_handoff = load_content_studio_operator_ready_handoff()
owner_review_package = load_content_studio_owner_review_package()


def test_content_studio_operator_ready_handoff_writes_no_write_summary_when_blocked(tmp_path: Path):
    seed_workspace(tmp_path)
    owner_review_package.run_content_studio_owner_review_package(tmp_path)
    website_root = tmp_path / "website"
    website_root.mkdir(parents=True, exist_ok=True)

    summary, artifacts = operator_ready_handoff.run_content_studio_operator_ready_handoff(
        tmp_path,
        website_root=str(website_root),
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
        storage_ready=True,
        allow_blocked_plan=True,
        allow_blocked_operator=True,
    )

    assert summary["status"] == "content_studio_operator_ready_handoff_blocked"
    assert summary["media_ready"] is False
    assert summary["operator_ready"] is False
    assert summary["no_publish_executed"] is True
    assert any(step["step"] == "content_studio_media_status" for step in summary["steps"])
    assert any(step["step"] == "content_studio_media_ready_handoff" for step in summary["steps"])
    assert any(step["step"] == "publish_operator_ready_handoff" for step in summary["steps"])
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-operator-ready-handoff.json").exists()
    assert list((tmp_path / "seo-workspace" / "reports").glob("*-content-studio-operator-ready-handoff.md"))
    assert artifacts
