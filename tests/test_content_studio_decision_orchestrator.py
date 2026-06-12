import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_content_studio_decision_orchestrator,
    load_content_studio_owner_review_package,
)
from tests.test_content_studio_owner_review_package import seed_workspace


decision_orchestrator = load_content_studio_decision_orchestrator()
owner_review_package = load_content_studio_owner_review_package()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def approve_decision(tmp_path: Path, scope: str) -> None:
    path = tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["decision"].update(
        {
            "content_approved": True,
            "media_urls_confirmed": True,
            "qa_approved": True,
            "latest_research_verified": True,
            "explicit_execution_requested": True,
            "allowed_execution_scope": scope,
        }
    )
    write_json(path, payload)


def write_confirmed_uploaded_url_map(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "uploaded-url-map.json",
        {
            "files": [
                {
                    "placeholder_filename": "hero.webp",
                    "public_filename": "hero.svg",
                    "object_path": "media/seo-generated/hero.svg",
                    "file_url": "https://cdn.example.com/media/seo-generated/hero.svg",
                    "owner_url_confirmed": True,
                }
            ]
        },
    )


def test_decision_orchestrator_stops_when_owner_review_only(tmp_path: Path):
    seed_workspace(tmp_path)
    owner_review_package.run_content_studio_owner_review_package(tmp_path)

    summary, artifacts = decision_orchestrator.run_content_studio_decision_orchestrator(tmp_path)

    assert summary["status"] == "decision_orchestration_waiting_owner_input"
    assert summary["orchestrated_action"] == "no_action_waiting_owner_input"
    assert summary["no_publish_executed"] is True
    assert any("content_approved=true" in blocker for blocker in summary["blockers"])
    assert len(summary["steps"]) == 1
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-decision-orchestration.json").exists()
    report = tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-decision-orchestration.md"
    assert report.exists()
    assert "未上传媒体、未写 CMS、未改源码、未发布、未部署" in report.read_text(encoding="utf-8")
    assert artifacts


def test_decision_orchestrator_runs_media_handoff_when_scope_allows(tmp_path: Path):
    seed_workspace(tmp_path)
    owner_review_package.run_content_studio_owner_review_package(tmp_path)
    approve_decision(tmp_path, "media_ready_handoff_only")
    write_confirmed_uploaded_url_map(tmp_path)

    summary, _ = decision_orchestrator.run_content_studio_decision_orchestrator(tmp_path)

    assert summary["status"] == "decision_orchestration_waiting_owner_review"
    assert summary["orchestrated_action"] == "run_media_ready_handoff_no_write"
    assert any(step["step"] == "content_studio_media_ready_handoff" for step in summary["steps"])
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-media-ready-handoff.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.media-ready.json").exists()
    assert summary["no_media_upload_executed"] is True
    assert summary["no_cms_write_executed"] is True


def test_decision_orchestrator_runs_operator_handoff_when_scope_allows(tmp_path: Path):
    seed_workspace(tmp_path)
    owner_review_package.run_content_studio_owner_review_package(tmp_path)
    approve_decision(tmp_path, "operator_ready_handoff_only")
    write_confirmed_uploaded_url_map(tmp_path)
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-media-status.json",
        {
            "status": "media_ready_payload_present",
            "counts": {"total": 1, "ready": 1, "missing_public_url": 0, "needs_owner_confirmation": 0},
        },
    )

    summary, _ = decision_orchestrator.run_content_studio_decision_orchestrator(tmp_path)

    assert summary["status"] == "decision_orchestration_waiting_owner_review"
    assert summary["orchestrated_action"] == "run_operator_ready_handoff_no_write"
    assert any(step["step"] == "content_studio_operator_ready_handoff" for step in summary["steps"])
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-operator-ready-handoff.json").exists()
    assert summary["no_media_upload_executed"] is True
    assert summary["no_cms_write_executed"] is True
    assert summary["no_publish_executed"] is True
