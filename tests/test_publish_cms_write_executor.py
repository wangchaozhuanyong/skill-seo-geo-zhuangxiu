import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_cms_write_executor


cms_write_executor = load_publish_cms_write_executor()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ready_execution_input() -> dict:
    return {
        "status": "execution_input_template_ready_for_approved_executor",
        "action": "publish_approved_execution_input_template_only_no_execute",
        "target_url": "https://flashcast.com.my/en/services/kitchen",
        "paired_url": "https://flashcast.com.my/zh/services/kitchen",
        "admin_helper": "saveAdminService",
        "admin_helper_call": {
            "function": "saveAdminService",
            "input": {
                "record": {
                    "slug": "kitchen",
                    "title_zh": "厨房装修图文方案",
                    "title_en": "Kitchen Renovation Image-Rich Plan",
                    "content_zh": "<p>设计方案</p>",
                    "content_en": "<p>Design concept</p>",
                    "status": "draft",
                },
                "nextStatus": "draft",
            },
        },
        "blockers": [],
        "warnings": [],
    }


def test_publish_cms_write_executor_ready_dry_run_without_writing(tmp_path: Path):
    input_path = tmp_path / "seo-workspace" / "data" / "publish-approved-execution-input.json"
    write_json(input_path, ready_execution_input())

    summary, artifacts = cms_write_executor.run_publish_cms_write_executor(
        tmp_path,
        allowed_target_urls=[
            "https://flashcast.com.my/en/services/kitchen",
            "https://flashcast.com.my/zh/services/kitchen",
        ],
    )

    assert summary["status"] == "cms_write_executor_ready_dry_run"
    assert summary["cms_write_executed"] is False
    assert summary["no_cms_write_executed"] is True
    assert summary["blockers"] == []
    assert summary["content_publish_api_request"]["contentType"] == "service"
    assert summary["content_publish_api_request"]["mode"] == "dry-run"
    assert summary["content_publish_api_request"]["record"]["slug"] == "kitchen"
    report = tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-publish-cms-write-executor.md"
    report_text = report.read_text(encoding="utf-8")
    assert "永远不直接写 Supabase/数据库表" in report_text
    assert "content-publish" in report_text
    assert all(path.exists() for path in artifacts)


def test_publish_cms_write_executor_blocks_live_without_confirm_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("FLASHCAST_APPROVED_PUBLISH_RUN", raising=False)
    input_path = tmp_path / "seo-workspace" / "data" / "publish-approved-execution-input.json"
    write_json(input_path, ready_execution_input())

    summary, _ = cms_write_executor.run_publish_cms_write_executor(
        tmp_path,
        mode="live",
        confirm_write=True,
        allowed_target_urls=[
            "https://flashcast.com.my/en/services/kitchen",
            "https://flashcast.com.my/zh/services/kitchen",
        ],
    )

    assert summary["status"] == "blocked_before_cms_write_execution"
    assert summary["cms_write_executed"] is False
    assert any("FLASHCAST_APPROVED_PUBLISH_RUN" in blocker for blocker in summary["blockers"])
    assert any("FLASHCAST_CONTENT_PUBLISH_URL" in blocker for blocker in summary["blockers"])
    assert any("FLASHCAST_ADMIN_ACCESS_TOKEN" in blocker and "FLASHCAST_CONTENT_PUBLISH_SECRET" in blocker for blocker in summary["blockers"])


def test_publish_cms_write_executor_blocks_staging_without_admin_api_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FLASHCAST_APPROVED_PUBLISH_RUN", "I_UNDERSTAND_THIS_WRITES_CMS")
    monkeypatch.delenv("FLASHCAST_CONTENT_PUBLISH_URL", raising=False)
    monkeypatch.delenv("FLASHCAST_ADMIN_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("FLASHCAST_CONTENT_PUBLISH_SECRET", raising=False)
    input_path = tmp_path / "seo-workspace" / "data" / "publish-approved-execution-input.json"
    write_json(input_path, ready_execution_input())

    summary, _ = cms_write_executor.run_publish_cms_write_executor(
        tmp_path,
        mode="staging",
        confirm_write=True,
        allowed_target_urls=[
            "https://flashcast.com.my/en/services/kitchen",
            "https://flashcast.com.my/zh/services/kitchen",
        ],
    )

    assert summary["status"] == "blocked_before_cms_write_execution"
    assert summary["direct_database_write_disabled"] is True
    assert summary["required_publish_path"] == "website_admin_backend"
    assert any("FLASHCAST_CONTENT_PUBLISH_URL" in blocker for blocker in summary["blockers"])
    assert any("FLASHCAST_ADMIN_ACCESS_TOKEN" in blocker and "FLASHCAST_CONTENT_PUBLISH_SECRET" in blocker for blocker in summary["blockers"])


def test_publish_cms_write_executor_blocks_media_placeholders(tmp_path: Path):
    payload = ready_execution_input()
    payload["admin_helper_call"]["input"]["record"]["content_en"] = "NEEDS_MEDIA_UPLOAD:hero.webp"
    write_json(tmp_path / "seo-workspace" / "data" / "publish-approved-execution-input.json", payload)

    summary, _ = cms_write_executor.run_publish_cms_write_executor(
        tmp_path,
        allowed_target_urls=[
            "https://flashcast.com.my/en/services/kitchen",
            "https://flashcast.com.my/zh/services/kitchen",
        ],
    )

    assert summary["status"] == "blocked_before_cms_write_execution"
    assert any("Media placeholders remain" in blocker for blocker in summary["blockers"])
