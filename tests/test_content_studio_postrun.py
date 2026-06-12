from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_orchestrator, load_content_studio_postrun
from tests.test_content_studio_orchestrator import write_schedule
from tests.test_daily_automation import seed_workspace


content_studio_orchestrator = load_content_studio_orchestrator()
content_studio_postrun = load_content_studio_postrun()


def test_content_studio_postrun_summarizes_completed_orchestration(tmp_path: Path):
    seed_workspace(tmp_path)
    config_path = write_schedule(tmp_path)
    content_studio_orchestrator.run_content_studio_orchestrator(
        tmp_path,
        config_path=str(config_path),
        now="2026-06-11T09:00:00+08:00",
    )

    summary, artifacts = content_studio_postrun.run_content_studio_postrun(tmp_path)
    json_path, report_path = artifacts
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert summary["status"] == "content_studio_postrun_ready_for_owner_review"
    assert payload["latest_run"]["target_url"]
    assert payload["next_queue_item"]["target_url"]
    assert payload["no_live_actions_executed"] is True
    assert "Content Studio Postrun Report" in report_path.read_text(encoding="utf-8")


def test_content_studio_postrun_blocks_missing_artifacts(tmp_path: Path):
    summary, artifacts = content_studio_postrun.run_content_studio_postrun(tmp_path)
    json_path, _ = artifacts
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert summary["status"] == "content_studio_postrun_blocked"
    assert any("Missing content-studio-orchestration.json" in blocker for blocker in payload["blockers"])
