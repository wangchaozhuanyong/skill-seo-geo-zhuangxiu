import csv
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_latest_research


latest_research = load_latest_research()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_latest_research_fetches_file_source_and_writes_logs(tmp_path):
    source = tmp_path / "source.html"
    write(
        source,
        """<!doctype html>
<html>
<head>
  <title>Kitchen Planning Source</title>
  <meta name="description" content="Kitchen planning guidance.">
  <meta property="og:site_name" content="Example Publisher">
  <meta property="article:published_time" content="2026-06-01T09:00:00Z">
</head>
<body>Kitchen planning content.</body>
</html>
""",
    )

    result, artifacts = latest_research.run_latest_research(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        queries=["kitchen renovation malaysia planning"],
        sources=[f"official|{source.as_uri()}|Use for general kitchen planning guidance|not a FLASH CAST claim|kitchen renovation malaysia planning"],
    )

    assert result.ok
    assert result.sources[0].source_title == "Kitchen Planning Source"
    assert result.sources[0].publisher == "Example Publisher"
    assert result.sources[0].published_or_accessed_date == "2026-06-01"
    latest_path, report_path, brief_path = artifacts
    latest_rows = read_csv(latest_path)
    source_rows = read_csv(tmp_path / "seo-workspace" / "data" / "research-source-log.csv")
    assert latest_rows[0]["fetch_status"] == "fetched"
    assert latest_rows[0]["meta_description"] == "Kitchen planning guidance."
    assert source_rows[0]["claim_boundary"] == "not a FLASH CAST claim"
    assert "Kitchen Planning Source" in report_path.read_text(encoding="utf-8")
    assert brief_path.exists()


def test_latest_research_blocks_query_without_sources(tmp_path):
    result, artifacts = latest_research.run_latest_research(
        tmp_path,
        target_url="https://flashcast.com.my/en/blog/kitchen-planning",
        queries=["latest kitchen design trends malaysia"],
    )

    assert not result.ok
    assert any("no source URLs" in blocker for blocker in result.blockers)
    latest_path, report_path, _ = artifacts
    assert latest_path.exists()
    assert "Use Codex/web search" in report_path.read_text(encoding="utf-8")


def test_latest_research_blocks_empty_source_url(tmp_path):
    result, artifacts = latest_research.run_latest_research(
        tmp_path,
        target_url="https://flashcast.com.my/en/blog/kitchen-planning",
        queries=["latest kitchen design trends malaysia"],
        sources=["official||Use note|Boundary|query text"],
    )

    assert not result.ok
    assert any("valid URL" in blocker for blocker in result.blockers)
    latest_path, report_path, _ = artifacts
    assert latest_path.exists()
    assert "valid URL" in report_path.read_text(encoding="utf-8")
