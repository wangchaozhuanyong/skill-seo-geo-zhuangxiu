import csv
import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_research_discovery


research_discovery = load_research_discovery()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "brand-profile.md",
        "- Website: https://flashcast.com.my/\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv",
        "url,keyword,language,page_type,service,location,total_score,task_type,positive_events,penalty_events\n"
        "https://flashcast.com.my/en/services/kitchen,kitchen renovation malaysia,en,service,Kitchen renovation,Kuala Lumpur,25,high-commercial-intent page optimization,,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen renovation malaysia,commercial,ready,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen renovation,Kuala Lumpur,\n",
    )


def test_research_discovery_generates_offline_candidates_from_default_seeds(tmp_path):
    seed_workspace(tmp_path)

    result, artifacts = research_discovery.run_research_discovery(tmp_path, fetch_remote=False)

    assert result.ok
    assert result.status == "research_candidates_ready_for_selection"
    assert result.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert result.candidates
    csv_path, json_path, report_path, handoff_path = artifacts
    assert csv_path.exists()
    assert json_path.exists()
    assert report_path.exists()
    assert handoff_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["no_source_log_write"] is True
    assert payload["no_live_actions_executed"] is True
    assert "latest-research" in report_path.read_text(encoding="utf-8")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["latest_research_source_arg"]


def test_research_discovery_blocks_without_target_or_seeds(tmp_path):
    config_path = tmp_path / "seo-workspace" / "config" / "research-sources.yml"
    write(config_path, "sources:\n")

    result, _ = research_discovery.run_research_discovery(
        tmp_path,
        config_path=str(config_path),
        fetch_remote=False,
        write_example=False,
    )

    assert not result.ok
    assert result.status == "research_discovery_blocked"
    assert any("No target URL selected" in blocker for blocker in result.blockers)
    assert any("No trusted research seeds" in blocker for blocker in result.blockers)


def test_research_discovery_custom_seed_is_scored(tmp_path):
    seed_workspace(tmp_path)
    config_path = tmp_path / "seo-workspace" / "config" / "research-sources.yml"
    write(
        config_path,
        """sources:
  official_test:
    source_type: "official"
    publisher: "Official Test Source"
    seed_url: "https://example.com/kitchen-renovation-guidance"
    discovery_mode: "page"
    authority_score: 50
    usage_note: "Use only for test guidance."
    claim_boundary: "Test guidance only; not a FLASH CAST claim."
""",
    )

    result, _ = research_discovery.run_research_discovery(
        tmp_path,
        config_path=str(config_path),
        fetch_remote=False,
        write_example=False,
    )

    assert result.ok
    assert result.candidates[0].publisher == "Official Test Source"
    assert result.candidates[0].source_type == "official"
    assert "https://example.com/kitchen-renovation-guidance" in result.candidates[0].latest_research_arg()
