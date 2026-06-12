from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_next, load_content_studio_queue
from tests.test_daily_automation import seed_workspace


content_studio_next = load_content_studio_next()
content_studio_queue = load_content_studio_queue()


def test_content_studio_next_runs_first_queue_item_and_records_history(tmp_path: Path):
    seed_workspace(tmp_path)
    content_studio_queue.run_content_studio_queue(tmp_path, limit=2)

    summary, artifacts = content_studio_next.run_content_studio_next(tmp_path, research_fetch_remote=False)
    next_json, history_csv, report_path = artifacts
    payload = json.loads(next_json.read_text(encoding="utf-8"))

    assert summary["status"] == "content_studio_next_waiting_owner_review"
    assert payload["no_live_actions_executed"] is True
    assert payload["research_search_provider"] == "hybrid-rss"
    assert payload["research_search_feeds_config"] == "seo-workspace/config/research-search-feeds.example.yml"
    assert payload["research_fetch_remote"] is False
    assert payload["research_artifacts"]
    assert payload["selected_queue_item"]["target_url"]
    assert history_csv.is_file()
    assert "target_url" in history_csv.read_text(encoding="utf-8")
    report = report_path.read_text(encoding="utf-8")
    assert "Content Studio Next Run" in report
    assert "Research search provider: `hybrid-rss`" in report


def test_content_studio_next_skips_history_item(tmp_path: Path):
    seed_workspace(tmp_path)
    queue_summary, _ = content_studio_queue.run_content_studio_queue(tmp_path, limit=2)
    first = queue_summary["queue"][0]["target_url"]

    history = tmp_path / "seo-workspace" / "data" / "content-studio-history.csv"
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text(
        "run_at,target_url,paired_url,pipeline,status,queue_slot,content_studio_json,content_studio_report\n"
        f"2026-06-11T00:00:00Z,{first},,rich-content,done,1,,\n",
        encoding="utf-8",
    )

    summary, _ = content_studio_next.run_content_studio_next(tmp_path, research_fetch_remote=False)

    assert summary["selected_queue_item"]["target_url"] != first


def test_content_studio_next_can_build_owner_review_package(tmp_path: Path):
    seed_workspace(tmp_path)
    content_studio_queue.run_content_studio_queue(tmp_path, limit=1)

    summary, artifacts = content_studio_next.run_content_studio_next(
        tmp_path,
        research_fetch_remote=False,
        owner_review_package=True,
    )

    assert summary["owner_review_package_status"] == "owner_review_package_ready"
    assert summary["artifacts"]["owner_review_package_report"].endswith("content-studio-owner-review-package.md")
    assert (tmp_path / "seo-workspace" / "data" / "content-studio-owner-review-package.json").exists()
    assert len(artifacts) > 3
