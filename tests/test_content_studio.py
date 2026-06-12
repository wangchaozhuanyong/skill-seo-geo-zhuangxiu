from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio
from tests.test_daily_automation import seed_workspace


content_studio = load_content_studio()


def test_content_studio_runs_target_page_rich_package(tmp_path: Path):
    seed_workspace(tmp_path)

    summary, artifacts = content_studio.run_content_studio(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        pipeline="rich-content",
        research_fetch_remote=False,
    )
    data_path, report_path = artifacts
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    step_names = {step["name"] for step in payload["steps"]}

    assert summary["status"] == "rich_content_package_waiting_owner_review"
    assert payload["requested_target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert payload["research_search_provider"] == "hybrid-rss"
    assert payload["research_search_feeds_config"] == "seo-workspace/config/research-search-feeds.example.yml"
    assert payload["research_fetch_remote"] is False
    assert payload["research_artifacts"]
    assert payload["no_live_actions_executed"] is True
    assert payload["owner_review_required"] is True
    assert "research_search" in step_names
    assert "rich_content" in step_names
    assert "rich_editor" in step_names
    assert "rich_editor_apply" in step_names
    assert "service_pattern_package" in step_names
    assert report_path.is_file()
    report = report_path.read_text(encoding="utf-8")
    assert "Content Studio" in report
    assert "Research search provider: `hybrid-rss`" in report


def test_content_studio_publish_prep_stops_at_handoff_gates(tmp_path: Path):
    seed_workspace(tmp_path)

    summary, artifacts = content_studio.run_content_studio(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        pipeline="publish-prep",
        research_fetch_remote=False,
    )
    data_path, _ = artifacts
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    step_names = {step["name"] for step in payload["steps"]}

    assert summary["status"] == "publish_prep_blocked_before_owner_authorization"
    assert payload["no_cms_write_executed"] is True
    assert payload["no_media_upload_executed"] is True
    assert payload["no_source_write_executed"] is True
    assert "publish_readiness" in step_names
    assert "publish_operator_package" in step_names
    assert payload["handoff_blockers"]
