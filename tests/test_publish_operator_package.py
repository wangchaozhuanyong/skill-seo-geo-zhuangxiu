from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_operator_package


publish_operator_package = load_publish_operator_package()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ready_implementation_payload() -> dict:
    helper_call = {
        "function": "saveAdminService",
        "input": {
            "record": {
                "slug": "kitchen",
                "title_en": "Kitchen Image-Rich Renovation Plan",
                "image_url": "https://cdn.example.com/kitchen.webp",
                "status": "draft",
            },
            "nextStatus": "draft",
        },
    }
    return {
        "status": "implementation_package_ready_for_future_executor",
        "blockers": [],
        "warnings": [],
        "package": {
            "generated_at": "2026-06-11T00:00:00+00:00",
            "action": "implementation_package_only_no_write",
            "status": "implementation_package_ready_for_future_executor",
            "implementation_allowed_for_future_executor": True,
            "target_url": TARGET_URL,
            "paired_url": PAIRED_URL,
            "table": "services",
            "admin_helper": "saveAdminService",
            "cms_payload_path": "seo-workspace/data/rich-content-cms-payload.media-ready.json",
            "cms_payload_selection": "auto_media_ready",
            "admin_helper_call": helper_call,
            "payload_keys": ["slug", "title_en", "image_url", "status"],
            "latest_research_sources": [{"source_title": "Schema.org Service"}],
            "website_evidence": {
                "website_root": "/tmp/site",
                "package_manager": "npm",
                "node_engine": ">=20 <23",
                "helper_summary": {"saveAdminService": 1},
            },
            "website_adapter_status": "website_publish_adapter_ready",
            "website_adapter_contract": {"service_pages": "prefer saveAdminService"},
            "backup_commands": ["npm run backup:supabase"],
            "seo_generation_commands": ["npm run generate:sitemap", "node scripts/generate-seo-manifest.mjs"],
            "website_qa_commands": ["npm run verify:seo-html"],
            "build_commands": ["npm run build"],
            "qa_commands": [
                f"python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url {TARGET_URL}",
                f"python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url {PAIRED_URL}",
                "npm run verify:seo-html",
            ],
            "rollback_plan": ["restore backed-up CMS/source record for both language versions"],
            "blockers": [],
            "warnings": [],
            "no_cms_write_executed": True,
            "no_source_page_write_executed": True,
            "no_media_upload_executed": True,
            "no_publish_executed": True,
            "no_deploy_executed": True,
            "no_live_actions_executed": True,
        },
    }


def seed_ready_files(tmp_path: Path, payload: dict | None = None) -> None:
    implementation = payload or ready_implementation_payload()
    write_json(tmp_path / "seo-workspace" / "data" / "publish-implementation-package.json", implementation)
    helper_call = implementation["package"]["admin_helper_call"]
    write_json(tmp_path / "seo-workspace" / "data" / "publish-admin-helper-call.json", helper_call)


def test_publish_operator_package_blocks_without_implementation(tmp_path):
    result, artifacts = publish_operator_package.run_publish_operator_package(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_operator_command"
    assert any("publish-implementation-package.json" in blocker for blocker in result.blockers)
    package_path, report_path = artifacts
    assert package_path.exists()
    assert report_path.exists()


def test_publish_operator_package_blocks_when_implementation_not_ready(tmp_path):
    payload = ready_implementation_payload()
    payload["status"] = "blocked_before_implementation_package"
    payload["blockers"] = ["Approved execution blocker: Owner approval flag missing."]
    payload["package"]["status"] = "blocked_before_implementation_package"
    payload["package"]["implementation_allowed_for_future_executor"] = False
    seed_ready_files(tmp_path, payload)

    result, _ = publish_operator_package.run_publish_operator_package(tmp_path)

    assert not result.ok
    assert any("top-level status" in blocker for blocker in result.blockers)
    assert any("does not allow future executor" in blocker for blocker in result.blockers)


def test_publish_operator_package_creates_command_manifest_without_writes(tmp_path):
    seed_ready_files(tmp_path)

    result, artifacts = publish_operator_package.run_publish_operator_package(tmp_path)

    assert result.ok
    assert result.status == "operator_command_ready_for_future_execution"
    assert result.operator_package["operator_allowed_for_future_executor"] is True
    assert result.operator_package["admin_helper_call"]["function"] == "saveAdminService"
    assert result.operator_package["command_groups"]["pre_execution"] == ["npm run backup:supabase"]
    assert "node scripts/generate-seo-manifest.mjs" in result.operator_package["command_groups"]["post_write_seo"]
    assert "npm run verify:seo-html" in result.operator_package["command_groups"]["qa"]
    assert "npm run build" in result.operator_package["command_groups"]["build"]
    assert "cd /tmp/site && npm run backup:supabase" in result.operator_package["dry_run_command_preview"]
    assert result.operator_package["required_operator_confirmations"]["owner_approved_specific_implementation_package"] is False
    assert result.operator_package["no_commands_executed"] is True
    assert result.operator_package["no_live_actions_executed"] is True
    package_path, report_path = artifacts
    payload = json.loads(package_path.read_text(encoding="utf-8"))
    assert payload["operator_package"]["action"] == "publish_operator_command_package_only_no_write"
    assert "operator command package only" in report_path.read_text(encoding="utf-8")


def test_publish_operator_package_requires_ready_website_adapter(tmp_path):
    payload = ready_implementation_payload()
    payload["package"]["website_adapter_status"] = "missing"
    seed_ready_files(tmp_path, payload)

    result, _ = publish_operator_package.run_publish_operator_package(tmp_path)

    assert not result.ok
    assert any("Website publish adapter is required" in blocker for blocker in result.blockers)


def test_publish_operator_package_blocks_helper_mismatch(tmp_path):
    seed_ready_files(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "publish-admin-helper-call.json",
        {"function": "saveAdminBlogPost", "input": {}},
    )

    result, _ = publish_operator_package.run_publish_operator_package(tmp_path)

    assert not result.ok
    assert any("does not match" in blocker for blocker in result.blockers)
