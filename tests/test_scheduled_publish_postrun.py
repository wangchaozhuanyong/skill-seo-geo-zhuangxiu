from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_scheduled_publish_postrun


scheduled_publish_postrun = load_scheduled_publish_postrun()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scheduled_publish_postrun_blocks_without_orchestration(tmp_path):
    result, artifacts = scheduled_publish_postrun.run_scheduled_publish_postrun(tmp_path)

    assert not result.ok
    assert result.status == "scheduled_publish_postrun_blocked"
    assert any("scheduled-publish-orchestration.json" in blocker for blocker in result.blockers)
    json_path, report_path = artifacts
    assert json_path.exists()
    assert report_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["no_live_actions_executed"] is True


def test_scheduled_publish_postrun_categorizes_blockers_and_next_actions(tmp_path):
    orchestration_path = tmp_path / "seo-workspace" / "data" / "scheduled-publish-orchestration.json"
    run_request_path = tmp_path / "seo-workspace" / "data" / "scheduled-publish-run-request.json"
    daily_path = tmp_path / "seo-workspace" / "data" / "daily-automation-run.json"
    readiness_path = tmp_path / "seo-workspace" / "data" / "publish-readiness.json"
    implementation_path = tmp_path / "seo-workspace" / "data" / "publish-implementation-package.json"
    operator_path = tmp_path / "seo-workspace" / "data" / "publish-operator-command.json"
    receipt_path = tmp_path / "seo-workspace" / "data" / "publish-execution-receipt.json"
    write_json(
        orchestration_path,
        {
            "status": "blocked_before_scheduled_publish_orchestration",
            "blockers": [
                "Scheduled publish authorization profile missing.",
                "Current local time 16:51 is outside the authorized 20-minute window around 09:00.",
            ],
            "orchestration": {
                "status": "blocked_before_scheduled_publish_orchestration",
                "runner_status": "blocked_before_scheduled_publish_run",
                "target_url": TARGET_URL,
                "paired_url": PAIRED_URL,
                "daily_automation_summary": {"status": "not_executed", "steps": [], "handoff_blockers": []},
            },
        },
    )
    write_json(
        run_request_path,
        {
            "status": "blocked_before_scheduled_publish_run",
            "blockers": ["allowed_target_urls must not be empty."],
            "run_request": {"status": "blocked_before_scheduled_publish_run", "target_url": TARGET_URL, "paired_url": PAIRED_URL},
        },
    )
    write_json(
        daily_path,
        {
            "status": "publish_prep_blocked_before_owner_authorization",
            "handoff_blockers": [
                "Publish plan blocker: Owner has not approved this exact queued package (--owner-approved missing).",
                "CMS write request blocker: Media placeholders remain in selected CMS payload.",
            ],
            "steps": [{"name": "publish_readiness", "status": "blocked_before_publish_handoff"}],
        },
    )
    write_json(readiness_path, {"status": "blocked_before_publish_handoff", "blockers": ["Missing media-url-map.json."]})
    write_json(implementation_path, {"status": "blocked_before_implementation_package", "blockers": ["Implementation package is not ready."]})
    write_json(operator_path, {"status": "blocked_before_operator_command", "blockers": ["Operator command package is not ready."]})
    write_json(receipt_path, {"status": "blocked_before_publish_execution_receipt", "blockers": ["Publish execution receipt is not ready."]})

    result, artifacts = scheduled_publish_postrun.run_scheduled_publish_postrun(tmp_path)

    assert not result.ok
    categories = result.summary["blocker_categories"]
    assert "authorization" in categories
    assert "schedule_window" in categories
    assert "owner_approval" in categories
    assert "media" in categories
    assert "implementation" in categories
    assert "operator" in categories
    assert "receipt" in categories
    assert any("授权" in action or "authorization" in action for action in result.summary["next_actions"])
    assert any("operator-command" in action for action in result.summary["next_actions"])
    json_path, report_path = artifacts
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["summary"]["target_url"] == TARGET_URL
    assert payload["summary"]["operator_status"] == "blocked_before_operator_command"
    assert payload["summary"]["receipt_status"] == "blocked_before_publish_execution_receipt"
    assert "Recommended Next Actions" in report_path.read_text(encoding="utf-8")
