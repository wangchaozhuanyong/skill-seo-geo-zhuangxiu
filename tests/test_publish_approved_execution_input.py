import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_approved_execution_input


approved_execution_input = load_publish_approved_execution_input()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_ready_inputs(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "publish-operator-command.json",
        {
            "status": "operator_command_ready_for_future_execution",
            "blockers": [],
            "warnings": [],
            "operator_package": {
                "action": "publish_operator_command_package_only_no_write",
                "status": "operator_command_ready_for_future_execution",
                "operator_allowed_for_future_executor": True,
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "paired_url": "https://flashcast.com.my/zh/services/kitchen",
                "admin_helper": "saveAdminService",
                "website_root": str(tmp_path / "website"),
                "admin_helper_call": {
                    "function": "saveAdminService",
                    "input": {"slug": "kitchen", "payload": {"title": "Kitchen"}},
                },
                "command_groups": {
                    "pre_execution": ["npm run backup:supabase"],
                    "post_write_seo": ["npm run generate:sitemap"],
                    "qa": ["npm run verify:seo-html"],
                    "build": ["npm run build"],
                },
                "no_commands_executed": True,
                "no_cms_write_executed": True,
                "no_source_page_write_executed": True,
                "no_media_upload_executed": True,
                "no_publish_executed": True,
                "no_deploy_executed": True,
                "no_live_actions_executed": True,
            },
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "publish-admin-helper-call.json",
        {"function": "saveAdminService", "input": {"slug": "kitchen", "payload": {"title": "Kitchen"}}},
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "website-publish-adapter.json",
        {
            "status": "website_publish_adapter_ready",
            "adapter": {
                "website_root": str(tmp_path / "website"),
                "helpers": [
                    {
                        "helper": "saveAdminService",
                        "kind": "export",
                        "path": "src/backend/modules/services/service/serviceService.ts",
                        "line": 98,
                    }
                ],
            },
        },
    )


def test_publish_approved_execution_input_writes_guarded_templates(tmp_path: Path):
    seed_ready_inputs(tmp_path)

    result, artifacts = approved_execution_input.run_publish_approved_execution_input(tmp_path)
    payload = json.loads((tmp_path / "seo-workspace" / "data" / "publish-approved-execution-input.json").read_text(encoding="utf-8"))
    runner = (tmp_path / "seo-workspace" / "tools" / "publish-approved-execution-runner.mjs").read_text(encoding="utf-8")

    assert result.status == "execution_input_template_ready_for_approved_executor"
    assert payload["admin_helper"] == "saveAdminService"
    assert payload["no_cms_write_executed"] is True
    assert "FLASHCAST_APPROVED_PUBLISH_RUN" in runner
    assert (tmp_path / "seo-workspace" / "data" / "publish-execution-result.template.json").exists()
    assert artifacts


def test_publish_approved_execution_input_blocks_unready_operator_by_default(tmp_path: Path):
    seed_ready_inputs(tmp_path)
    data_path = tmp_path / "seo-workspace" / "data" / "publish-operator-command.json"
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    payload["status"] = "blocked_before_operator_command"
    payload["operator_package"]["operator_allowed_for_future_executor"] = False
    write_json(data_path, payload)

    result, _ = approved_execution_input.run_publish_approved_execution_input(tmp_path)

    assert result.status == "blocked_before_execution_input_template"
    assert any("Operator package" in blocker for blocker in result.blockers)
