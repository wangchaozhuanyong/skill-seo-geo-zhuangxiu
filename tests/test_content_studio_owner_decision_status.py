import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_owner_decision_status


owner_decision_status = load_content_studio_owner_decision_status()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_decision_workspace(tmp_path: Path, *, scope: str = "owner_review_only", approved: bool = False) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json",
        {
            "status": "owner_decision_template_waiting_owner_input",
            "target_url": "https://flashcast.com.my/en/services/kitchen",
            "paired_url": "https://flashcast.com.my/zh/services/kitchen",
            "approval_is_not_execution": True,
            "decision": {
                "content_approved": approved,
                "media_urls_confirmed": approved,
                "qa_approved": approved,
                "latest_research_verified": approved,
                "explicit_execution_requested": approved,
                "allowed_execution_scope": scope,
                "owner_notes": "",
            },
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-media-status.json",
        {
            "status": "media_urls_need_owner_input",
            "counts": {"total": 1, "ready": 0, "missing_public_url": 1, "needs_owner_confirmation": 1},
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-approval-packet.json",
        {
            "status": "approval_packet_waiting_owner_review",
            "target_url": "https://flashcast.com.my/en/services/kitchen",
            "paired_url": "https://flashcast.com.my/zh/services/kitchen",
        },
    )


def test_owner_decision_status_defaults_to_review_only_without_execution(tmp_path: Path):
    seed_decision_workspace(tmp_path)

    summary, artifacts = owner_decision_status.run_content_studio_owner_decision_status(tmp_path)

    assert summary["status"] == "owner_decision_review_only"
    assert summary["approval_is_not_execution"] is True
    assert summary["no_publish_executed"] is True
    assert summary["allowed_execution_scope"] == "owner_review_only"
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision-status.json").exists()
    report = tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-owner-decision-status.md"
    assert report.exists()
    assert "approval / decision 仍不等于 execution" in report.read_text(encoding="utf-8")
    assert artifacts


def test_owner_decision_status_detects_ready_for_media_handoff(tmp_path: Path):
    seed_decision_workspace(tmp_path, scope="media_ready_handoff_only", approved=True)

    summary, _ = owner_decision_status.run_content_studio_owner_decision_status(tmp_path)

    assert summary["status"] == "owner_decision_ready_for_media_handoff"
    assert summary["media_required"] is True
    assert summary["missing_decisions"] == []
    assert any("content-studio-media-ready-handoff" in item["command"] for item in summary["recommended_commands"])


def test_owner_decision_status_detects_ready_for_operator_handoff(tmp_path: Path):
    seed_decision_workspace(tmp_path, scope="operator_ready_handoff_only", approved=True)
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-media-status.json",
        {
            "status": "media_ready_payload_present",
            "counts": {"total": 1, "ready": 1, "missing_public_url": 0, "needs_owner_confirmation": 0},
        },
    )

    summary, _ = owner_decision_status.run_content_studio_owner_decision_status(tmp_path)

    assert summary["status"] == "owner_decision_ready_for_operator_handoff"
    assert summary["media_required"] is False
    assert summary["missing_decisions"] == []
    assert any("content-studio-operator-ready-handoff" in item["command"] for item in summary["recommended_commands"])


def test_owner_decision_status_blocks_unsupported_scope(tmp_path: Path):
    seed_decision_workspace(tmp_path, scope="publish_now", approved=True)

    summary, _ = owner_decision_status.run_content_studio_owner_decision_status(tmp_path)

    assert summary["status"] == "owner_decision_status_blocked_missing_inputs"
    assert any("Unsupported allowed_execution_scope" in blocker for blocker in summary["blockers"])
