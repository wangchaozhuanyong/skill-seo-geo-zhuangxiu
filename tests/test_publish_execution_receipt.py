from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_execution_receipt


publish_execution_receipt = load_publish_execution_receipt()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ready_operator_payload() -> dict:
    return {
        "status": "operator_command_ready_for_future_execution",
        "blockers": [],
        "warnings": [],
        "operator_package": {
            "action": "publish_operator_command_package_only_no_write",
            "status": "operator_command_ready_for_future_execution",
            "operator_allowed_for_future_executor": True,
            "target_url": TARGET_URL,
            "paired_url": PAIRED_URL,
            "table": "services",
            "admin_helper": "saveAdminService",
            "cms_payload_path": "seo-workspace/data/rich-content-cms-payload.media-ready.json",
            "cms_payload_selection": "auto_media_ready",
            "admin_helper_call": {
                "function": "saveAdminService",
                "input": {"record": {"slug": "kitchen", "status": "draft"}, "nextStatus": "draft"},
            },
            "command_groups": {
                "pre_execution": ["npm run backup:supabase"],
                "post_write_seo": ["npm run generate:sitemap"],
                "qa": ["npm run verify:seo-html"],
                "build": ["npm run build"],
                "rollback": ["restore backed-up CMS/source record"],
            },
            "blockers": [],
            "warnings": [],
        },
    }


def ready_execution_result() -> dict:
    return {
        "generated_at": "2026-06-11T00:00:00+00:00",
        "action": "publish_execution_result_record",
        "status": "publish_execution_completed",
        "target_url": TARGET_URL,
        "paired_url": PAIRED_URL,
        "admin_helper": "saveAdminService",
        "publish_status": "draft",
        "cms_record_id": "service-kitchen",
        "executed_operator_package_path": "seo-workspace/data/publish-operator-command.json",
        "executed_helper_call_path": "seo-workspace/data/publish-admin-helper-call.json",
        "backup_completed_before_write": True,
        "cms_write_completed": True,
        "cms_write_result_recorded": True,
        "seo_assets_regenerated_after_write": True,
        "qa_passed_after_write": True,
        "rollback_evidence_retained": True,
        "explicit_publish_status_approval": False,
        "live_url_verified": False,
        "command_results": [
            {"command": "npm run backup:supabase", "exit_code": 0, "completed": True},
            {"command": "admin helper call", "exit_code": 0, "completed": True},
            {"command": "npm run generate:sitemap", "exit_code": 0, "completed": True},
        ],
    }


def seed_operator(tmp_path: Path, payload: dict | None = None) -> None:
    write_json(tmp_path / "seo-workspace" / "data" / "publish-operator-command.json", payload or ready_operator_payload())


def seed_result(tmp_path: Path, payload: dict | None = None) -> None:
    write_json(tmp_path / "seo-workspace" / "data" / "publish-execution-result.json", payload or ready_execution_result())


def test_publish_execution_receipt_blocks_without_result_and_writes_example(tmp_path):
    seed_operator(tmp_path)

    result, artifacts = publish_execution_receipt.run_publish_execution_receipt(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_publish_execution_receipt"
    assert any("publish-execution-result.json" in blocker for blocker in result.blockers)
    receipt_path, report_path = artifacts
    assert receipt_path.exists()
    assert report_path.exists()
    assert (tmp_path / "seo-workspace" / "config" / "publish-execution-result.example.json").exists()


def test_publish_execution_receipt_verifies_ready_result_without_writes(tmp_path):
    seed_operator(tmp_path)
    seed_result(tmp_path)

    result, artifacts = publish_execution_receipt.run_publish_execution_receipt(tmp_path)

    assert result.ok
    assert result.status == "publish_execution_receipt_verified"
    assert result.receipt["receipt_verified_for_post_publish_qa"] is True
    assert result.receipt["admin_helper"] == "saveAdminService"
    assert result.receipt["result_flags"]["cms_write_completed"] is True
    assert result.receipt["no_commands_executed_by_receipt_verifier"] is True
    receipt_path, report_path = artifacts
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["receipt"]["action"] == "publish_execution_receipt_verification_only_no_execute"
    assert "receipt verification only" in report_path.read_text(encoding="utf-8")


def test_publish_execution_receipt_blocks_published_result_without_live_verification(tmp_path):
    seed_operator(tmp_path)
    payload = ready_execution_result()
    payload["publish_status"] = "published"
    payload["explicit_publish_status_approval"] = True
    payload["live_url_verified"] = False
    seed_result(tmp_path, payload)

    result, _ = publish_execution_receipt.run_publish_execution_receipt(tmp_path)

    assert not result.ok
    assert any("live_url_verified" in blocker for blocker in result.blockers)


def test_publish_execution_receipt_blocks_target_mismatch(tmp_path):
    seed_operator(tmp_path)
    payload = ready_execution_result()
    payload["target_url"] = "https://flashcast.com.my/en/services/bathroom"
    seed_result(tmp_path, payload)

    result, _ = publish_execution_receipt.run_publish_execution_receipt(tmp_path)

    assert not result.ok
    assert any("target_url does not match" in blocker for blocker in result.blockers)


def test_publish_execution_receipt_blocks_incomplete_command(tmp_path):
    seed_operator(tmp_path)
    payload = ready_execution_result()
    payload["command_results"][0]["completed"] = False
    seed_result(tmp_path, payload)

    result, _ = publish_execution_receipt.run_publish_execution_receipt(tmp_path)

    assert not result.ok
    assert any("command not completed" in blocker for blocker in result.blockers)
