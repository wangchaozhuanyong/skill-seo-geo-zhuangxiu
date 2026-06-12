from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_implementation_package


publish_implementation_package = load_publish_implementation_package()


TARGET_URL = "https://flashcast.com.my/en/services/kitchen"
PAIRED_URL = "https://flashcast.com.my/zh/services/kitchen"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ready_execution_record() -> dict:
    return {
        "status": "approved_execution_simulation_ready",
        "blockers": [],
        "warnings": [],
        "execution_record": {
            "generated_at": "2026-06-11T00:00:00+00:00",
            "mode": "dry-run",
            "action": "approved_execution_simulation_only_no_write",
            "status": "approved_execution_simulation_ready",
            "execution_allowed_for_future_executor": True,
            "target_url": TARGET_URL,
            "paired_url": PAIRED_URL,
            "table": "services",
            "admin_helper": "saveAdminService",
            "cms_payload_path": "seo-workspace/data/rich-content-cms-payload.media-ready.json",
            "cms_payload_selection": "auto_media_ready",
            "simulated_helper_call": {
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
            },
            "payload_keys": ["slug", "title_en", "image_url", "status"],
            "latest_research_sources": [{"source_title": "Schema.org Service"}],
            "post_write_tasks": ["regenerate seo-manifest", "regenerate sitemap.xml"],
            "no_cms_write_executed": True,
            "no_source_page_write_executed": True,
            "no_media_upload_executed": True,
            "no_publish_executed": True,
            "no_deploy_executed": True,
            "no_live_actions_executed": True,
        },
    }


def seed_record(tmp_path: Path, payload: dict | None = None) -> Path:
    record_path = tmp_path / "seo-workspace" / "data" / "publish-approved-execution-record.json"
    write_json(record_path, payload or ready_execution_record())
    return record_path


def seed_adapter(tmp_path: Path) -> Path:
    adapter_path = tmp_path / "seo-workspace" / "data" / "website-publish-adapter.json"
    write_json(
        adapter_path,
        {
            "status": "website_publish_adapter_ready",
            "blockers": [],
            "warnings": [],
            "adapter": {
                "website_root": "/tmp/site",
                "package_manager": "npm",
                "node_engine": ">=20 <23",
                "commands": {
                    "backup_commands": ["npm run backup:supabase"],
                    "seo_generation_commands": ["npm run generate:sitemap", "node scripts/generate-seo-manifest.mjs", "npm run generate:llms"],
                    "qa_commands": ["npm run typecheck", "npm run verify:seo-html"],
                    "build_commands": ["npm run build"],
                },
                "helpers": [
                    {"helper": "saveAdminService", "path": "src/backend/modules/services/service/serviceService.ts", "line": 98, "kind": "export"},
                    {"helper": "uploadAdminMediaObject", "path": "src/backend/modules/media/service/mediaService.ts", "line": 34, "kind": "export"},
                ],
                "helper_summary": {"saveAdminService": 1, "uploadAdminMediaObject": 1},
                "seo_assets": [{"path": "public/sitemap.xml", "exists": True}],
                "docs": [{"path": "docs/rules/seo-cms-publishing.md", "exists": True}],
                "env_keys_from_example": ["VITE_SUPABASE_URL"],
                "future_executor_contract": {"service_pages": "prefer saveAdminService for services table records"},
            },
        },
    )
    return adapter_path


def test_publish_implementation_package_blocks_without_record(tmp_path):
    result, artifacts = publish_implementation_package.run_publish_implementation_package(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_implementation_package"
    assert any("publish-approved-execution-record.json" in blocker for blocker in result.blockers)
    package_path, helper_path, report_path = artifacts
    assert package_path.exists()
    assert helper_path.exists()
    assert report_path.exists()


def test_publish_implementation_package_blocks_when_record_not_ready(tmp_path):
    payload = ready_execution_record()
    payload["status"] = "blocked_before_approved_execution"
    payload["blockers"] = ["Owner approval flag missing (--owner-approved)."]
    payload["execution_record"]["status"] = "blocked_before_approved_execution"
    payload["execution_record"]["execution_allowed_for_future_executor"] = False
    seed_record(tmp_path, payload)

    result, _ = publish_implementation_package.run_publish_implementation_package(tmp_path)

    assert not result.ok
    assert any("top-level status" in blocker for blocker in result.blockers)
    assert any("does not allow future executor" in blocker for blocker in result.blockers)


def test_publish_implementation_package_creates_helper_call_without_writes(tmp_path):
    seed_record(tmp_path)

    result, artifacts = publish_implementation_package.run_publish_implementation_package(tmp_path)

    assert result.ok
    assert result.status == "implementation_package_ready_for_future_executor"
    assert result.package["implementation_allowed_for_future_executor"] is True
    assert result.package["admin_helper_call"]["function"] == "saveAdminService"
    assert result.package["no_cms_write_executed"] is True
    assert result.package["no_live_actions_executed"] is True
    assert result.package["website_evidence"]["provided"] is False
    assert any("Missing website-publish-adapter.json" in warning for warning in result.warnings)
    package_path, helper_path, report_path = artifacts
    payload = json.loads(package_path.read_text(encoding="utf-8"))
    helper_payload = json.loads(helper_path.read_text(encoding="utf-8"))
    assert payload["package"]["action"] == "implementation_package_only_no_write"
    assert helper_payload["function"] == "saveAdminService"
    assert "implementation package only" in report_path.read_text(encoding="utf-8")


def test_publish_implementation_package_uses_adapter_commands(tmp_path):
    seed_record(tmp_path)
    seed_adapter(tmp_path)

    result, _ = publish_implementation_package.run_publish_implementation_package(tmp_path)

    assert result.ok
    assert result.package["website_adapter_status"] == "website_publish_adapter_ready"
    assert result.package["backup_commands"] == ["npm run backup:supabase"]
    assert "node scripts/generate-seo-manifest.mjs" in result.package["seo_generation_commands"]
    assert "npm run verify:seo-html" in result.package["website_qa_commands"]
    assert "npm run build" in result.package["build_commands"]
    assert "npm run verify:seo-html" in result.package["qa_commands"]
    assert result.package["website_evidence"]["package_manager"] == "npm"
    assert result.package["website_evidence"]["helper_summary"]["saveAdminService"] == 1


def test_publish_implementation_package_records_website_helper_evidence(tmp_path):
    seed_record(tmp_path)
    website_root = tmp_path / "site"
    source_path = website_root / "src" / "admin" / "services.ts"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("export async function saveAdminService() { return null }\n", encoding="utf-8")

    result, _ = publish_implementation_package.run_publish_implementation_package(
        tmp_path,
        website_root=str(website_root),
    )

    assert result.ok
    evidence = result.package["website_evidence"]
    assert evidence["exists"] is True
    assert evidence["helper_matches"]
    assert evidence["helper_matches"][0]["helper"] == "saveAdminService"


def test_publish_implementation_package_blocks_media_placeholders(tmp_path):
    payload = ready_execution_record()
    payload["execution_record"]["simulated_helper_call"]["input"]["record"]["image_url"] = "NEEDS_MEDIA_UPLOAD:kitchen.webp"
    seed_record(tmp_path, payload)

    result, _ = publish_implementation_package.run_publish_implementation_package(tmp_path)

    assert not result.ok
    assert any("Media placeholders remain" in blocker for blocker in result.blockers)
