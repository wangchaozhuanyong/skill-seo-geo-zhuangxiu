from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_automation_completion_audit


completion_audit = load_automation_completion_audit()


def test_completion_audit_reports_capability_ready_in_repo():
    root = Path(__file__).resolve().parents[1]

    summary, artifacts = completion_audit.run_automation_completion_audit(root)

    assert summary["capability_ready"] is True
    assert summary["status"] in {
        "automation_capability_complete_waiting_owner_runtime_inputs",
        "automation_fully_execution_ready",
    }
    assert any("真实媒体 URL" in item for item in summary["remaining_owner_inputs"]) or summary["execution_ready_now"] is True
    assert all(path.exists() for path in artifacts)
