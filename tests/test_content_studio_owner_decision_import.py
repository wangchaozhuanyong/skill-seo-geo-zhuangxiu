import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_owner_decision_import,
    load_content_studio_owner_decision_status,
)
from tests.test_content_studio_owner_decision_status import seed_decision_workspace


owner_decision_import = load_content_studio_owner_decision_import()
owner_decision_status = load_content_studio_owner_decision_status()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def filled_decision_payload(scope: str = "media_ready_handoff_only") -> dict:
    return {
        "status": "owner_decision_filled_waiting_codex_review",
        "target_url": "https://flashcast.com.my/en/services/kitchen",
        "paired_url": "https://flashcast.com.my/zh/services/kitchen",
        "exported_from_owner_decision_editor": True,
        "approval_is_not_execution": True,
        "decision": {
            "content_approved": True,
            "media_urls_confirmed": True,
            "qa_approved": True,
            "latest_research_verified": True,
            "explicit_execution_requested": True,
            "allowed_execution_scope": scope,
            "owner_notes": "Approved from local HTML form.",
        },
    }


def test_owner_decision_import_updates_template_and_status(tmp_path: Path):
    seed_decision_workspace(tmp_path)
    filled_path = tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.filled.json"
    write_json(filled_path, filled_decision_payload())

    summary, artifacts = owner_decision_import.run_content_studio_owner_decision_import(
        tmp_path,
        filled_decision_path=str(filled_path),
    )
    template = json.loads((tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json").read_text(encoding="utf-8"))
    status, _ = owner_decision_status.run_content_studio_owner_decision_status(tmp_path)

    assert summary["status"] == "owner_decision_imported_waiting_status_check"
    assert summary["no_publish_executed"] is True
    assert template["status"] == "owner_decision_imported_waiting_status_check"
    assert template["imported_from_owner_decision_editor"] is True
    assert template["decision"]["content_approved"] is True
    assert template["decision"]["allowed_execution_scope"] == "media_ready_handoff_only"
    assert status["status"] == "owner_decision_ready_for_media_handoff"
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision-import.json").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-owner-decision-import.md").exists()
    assert artifacts


def test_owner_decision_import_accepts_operator_ready_scope(tmp_path: Path):
    seed_decision_workspace(tmp_path)
    filled_path = tmp_path / "seo-workspace" / "data" / "operator-scope.json"
    write_json(filled_path, filled_decision_payload(scope="operator_ready_handoff_only"))

    summary, _ = owner_decision_import.run_content_studio_owner_decision_import(
        tmp_path,
        filled_decision_path=str(filled_path),
    )
    template = json.loads((tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json").read_text(encoding="utf-8"))

    assert summary["status"] == "owner_decision_imported_waiting_status_check"
    assert template["decision"]["allowed_execution_scope"] == "operator_ready_handoff_only"
    assert "operator_ready_handoff_only" in template["decision"]["allowed_execution_scope_options"]


def test_owner_decision_import_blocks_wrong_target(tmp_path: Path):
    seed_decision_workspace(tmp_path)
    filled = filled_decision_payload()
    filled["target_url"] = "https://flashcast.com.my/en/services/bathroom"
    filled_path = tmp_path / "seo-workspace" / "data" / "wrong-target.json"
    write_json(filled_path, filled)

    summary, _ = owner_decision_import.run_content_studio_owner_decision_import(
        tmp_path,
        filled_decision_path=str(filled_path),
    )

    assert summary["status"] == "owner_decision_import_blocked"
    assert any("target_url does not match" in blocker for blocker in summary["blockers"])


def test_owner_decision_import_blocks_unsupported_scope(tmp_path: Path):
    seed_decision_workspace(tmp_path)
    filled_path = tmp_path / "seo-workspace" / "data" / "bad-scope.json"
    write_json(filled_path, filled_decision_payload(scope="publish_now"))

    summary, _ = owner_decision_import.run_content_studio_owner_decision_import(
        tmp_path,
        filled_decision_path=str(filled_path),
    )

    assert summary["status"] == "owner_decision_import_blocked"
    assert any("Unsupported allowed_execution_scope" in blocker for blocker in summary["blockers"])
