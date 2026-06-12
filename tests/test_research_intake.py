import csv
import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_research_intake


research_intake = load_research_intake()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_candidate_payload(tmp_path: Path, *, source_url: str, score: int = 90, source_type: str = "official") -> None:
    payload = {
        "status": "research_candidates_ready_for_selection",
        "target_url": "https://flashcast.com.my/en/services/kitchen",
        "queries": ["kitchen renovation malaysia"],
        "candidates": [
            {
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "query": "kitchen renovation malaysia",
                "candidate_url": source_url,
                "source_type": source_type,
                "publisher": "Trusted Test Source",
                "source_title": "Trusted Kitchen Planning",
                "published_or_accessed_date": "2026-06-11",
                "score": str(score),
                "discovery_status": "fetched:200",
                "usage_note": "Use only for general kitchen planning guidance.",
                "claim_boundary": "General guidance only; not a FLASH CAST claim.",
                "latest_research_source_arg": f"{source_type}|{source_url}|Use only for general kitchen planning guidance.|General guidance only; not a FLASH CAST claim.|kitchen renovation malaysia",
            }
        ],
        "no_source_log_write": True,
        "no_live_actions_executed": True,
    }
    write(tmp_path / "seo-workspace" / "data" / "research-discovery-candidates.json", json.dumps(payload, ensure_ascii=False) + "\n")


def test_research_intake_records_trusted_candidate_into_source_log(tmp_path):
    source = tmp_path / "trusted-source.html"
    write(
        source,
        """<!doctype html>
<html>
<head>
  <title>Trusted Kitchen Planning</title>
  <meta name="description" content="Kitchen planning guidance.">
  <meta property="og:site_name" content="Trusted Test Source">
  <meta property="article:published_time" content="2026-06-01T09:00:00Z">
</head>
<body>Kitchen planning content.</body>
</html>
""",
    )
    write_candidate_payload(tmp_path, source_url=source.as_uri())

    result, artifacts = research_intake.run_research_intake(tmp_path, min_score=60)

    assert result.ok
    assert result.status == "research_sources_recorded_for_content"
    assert result.selected_source_count == 1
    assert result.fetched_source_count == 1
    rows = read_csv(tmp_path / "seo-workspace" / "data" / "research-source-log.csv")
    assert rows[0]["source_title"] == "Trusted Kitchen Planning"
    assert rows[0]["claim_boundary"] == "General guidance only; not a FLASH CAST claim."
    intake_json, report_path = artifacts
    payload = json.loads(intake_json.read_text(encoding="utf-8"))
    assert payload["source_log_write_executed"] is True
    assert payload["no_live_actions_executed"] is True
    assert "可信 research-discovery" in report_path.read_text(encoding="utf-8")


def test_research_intake_skips_low_score_candidate(tmp_path):
    source = tmp_path / "trusted-source.html"
    write(source, "<html><head><title>Low Score</title></head><body></body></html>\n")
    write_candidate_payload(tmp_path, source_url=source.as_uri(), score=20)

    result, artifacts = research_intake.run_research_intake(tmp_path, min_score=60)

    assert result.ok
    assert result.status == "research_intake_no_sources_recorded"
    assert result.selected_source_count == 0
    assert not (tmp_path / "seo-workspace" / "data" / "research-source-log.csv").exists()
    payload = json.loads(artifacts[0].read_text(encoding="utf-8"))
    assert payload["source_log_write_executed"] is False
    assert any("below min_score" in warning for warning in result.warnings)


def test_research_intake_blocks_without_discovery_payload(tmp_path):
    result, artifacts = research_intake.run_research_intake(tmp_path)

    assert not result.ok
    assert result.status == "research_intake_blocked"
    assert any("Run research-discovery first" in blocker for blocker in result.blockers)
    assert artifacts[0].exists()
