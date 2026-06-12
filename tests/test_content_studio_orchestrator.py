from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_orchestrator
from tests.test_daily_automation import seed_workspace


content_studio_orchestrator = load_content_studio_orchestrator()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_schedule(tmp_path: Path, *, executor: str = "content-studio-next", owner_review_package: bool = False) -> Path:
    config_path = tmp_path / "seo-workspace" / "config" / "daily-automation.yml"
    write(
        config_path,
        f"""automation_id: "flash-cast-daily-seo-geo"
enabled: true
timezone: "Asia/Kuala_Lumpur"
time_local: "09:00"
executor: "{executor}"
pipeline: "rich-content"
owner_review_package: {str(owner_review_package).lower()}
fetch_research_remote: false
publish_enabled: false
max_tasks_per_run: 1
language_scope: "bilingual_pair_required"
safety_gates:
  no_cms_login_without_execution: true
  no_media_upload_without_execution: true
  no_source_write_without_execution: true
  no_publish_without_execution: true
  no_deploy_without_execution: true
  concept_labels_required: true
""",
    )
    return config_path


def test_content_studio_orchestrator_runs_inside_schedule_window(tmp_path: Path):
    seed_workspace(tmp_path)
    config_path = write_schedule(tmp_path)

    summary, artifacts = content_studio_orchestrator.run_content_studio_orchestrator(
        tmp_path,
        config_path=str(config_path),
        now="2026-06-11T09:05:00+08:00",
    )
    data_path, log_path, report_path = artifacts
    payload = json.loads(data_path.read_text(encoding="utf-8"))

    assert summary["status"] == "content_studio_orchestration_completed"
    assert payload["no_live_actions_executed"] is True
    assert payload["next_summary"]["selected_queue_item"]["target_url"]
    assert payload["next_summary"]["research_search_provider"] == "hybrid-rss"
    assert payload["next_summary"]["research_search_feeds_config"] == "seo-workspace/config/research-search-feeds.example.yml"
    assert log_path.is_file()
    assert "content_studio_orchestration_completed" in log_path.read_text(encoding="utf-8")
    assert "Content Studio Orchestration" in report_path.read_text(encoding="utf-8")


def test_content_studio_orchestrator_can_build_owner_review_package(tmp_path: Path):
    seed_workspace(tmp_path)
    config_path = write_schedule(tmp_path, owner_review_package=True)

    summary, artifacts = content_studio_orchestrator.run_content_studio_orchestrator(
        tmp_path,
        config_path=str(config_path),
        now="2026-06-11T09:05:00+08:00",
    )
    data_path, _, report_path = artifacts
    payload = json.loads(data_path.read_text(encoding="utf-8"))

    assert summary["status"] == "content_studio_orchestration_completed"
    assert payload["owner_review_package_enabled"] is True
    assert payload["next_summary"]["owner_review_package_status"] == "owner_review_package_ready"
    assert payload["artifacts"]["owner_review_package_report"].endswith("content-studio-owner-review-package.md")
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-review-package.json").exists()
    assert "Owner review package: `True`" in report_path.read_text(encoding="utf-8")


def test_content_studio_orchestrator_blocks_wrong_executor(tmp_path: Path):
    seed_workspace(tmp_path)
    config_path = write_schedule(tmp_path, executor="daily-automation")

    summary, _ = content_studio_orchestrator.run_content_studio_orchestrator(
        tmp_path,
        config_path=str(config_path),
        now="2026-06-11T09:00:00+08:00",
    )

    assert summary["status"] == "content_studio_orchestration_blocked"
    assert any("executor: content-studio-next" in blocker for blocker in summary["blockers"])


def test_content_studio_orchestrator_blocks_duplicate_same_day(tmp_path: Path):
    seed_workspace(tmp_path)
    config_path = write_schedule(tmp_path)

    content_studio_orchestrator.run_content_studio_orchestrator(
        tmp_path,
        config_path=str(config_path),
        now="2026-06-11T09:00:00+08:00",
    )
    summary, _ = content_studio_orchestrator.run_content_studio_orchestrator(
        tmp_path,
        config_path=str(config_path),
        now="2026-06-11T09:10:00+08:00",
    )

    assert summary["status"] == "content_studio_orchestration_blocked"
    assert any("already completed" in blocker for blocker in summary["blockers"])
