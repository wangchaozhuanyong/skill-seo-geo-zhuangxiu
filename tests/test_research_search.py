import csv
import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_research_search


research_search = load_research_search()


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_research_search_no_fetch_generates_query_plan(tmp_path):
    seed_workspace(tmp_path)

    result, artifacts = research_search.run_research_search(tmp_path, fetch_remote=False)

    assert result.ok
    assert result.status == "research_search_queries_ready"
    assert result.target_url == "https://flashcast.com.my/en/services/kitchen"
    assert any("kitchen renovation malaysia" in query for query in result.queries)
    csv_path, json_path, report_path, handoff_path = artifacts
    assert csv_path.exists()
    assert json_path.exists()
    assert report_path.exists()
    assert handoff_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["no_source_log_write"] is True
    assert payload["no_live_actions_executed"] is True
    assert payload["candidates"] == []
    assert "Remote search fetching disabled" in report_path.read_text(encoding="utf-8")


def test_research_search_google_news_rss_candidates(monkeypatch, tmp_path):
    seed_workspace(tmp_path)

    def fake_fetch(query: str, *, timeout: int, market: str = "MY", language: str = "en"):
        return [
            research_search.SearchResult(
                query=query,
                url=f"https://example.com/{query.replace(' ', '-')}",
                title=f"{query} planning update",
                publisher="Example Industry Source",
                published_date="2026-06-10",
                snippet="Kitchen renovation planning guidance for Malaysia.",
                provider="google-news-rss",
            )
        ]

    monkeypatch.setattr(research_search, "fetch_google_news_rss", fake_fetch)

    result, artifacts = research_search.run_research_search(tmp_path, fetch_remote=True, limit=3)

    assert result.ok
    assert result.status == "research_search_candidates_ready_for_intake"
    assert result.candidates
    assert result.candidates[0].source_type == "industry"
    assert result.candidates[0].discovery_status == "search_result:google-news-rss"
    assert "not a FLASH CAST business claim" in result.candidates[0].latest_research_arg()
    rows = read_csv(artifacts[0])
    assert rows[0]["latest_research_source_arg"]
    payload = json.loads(artifacts[1].read_text(encoding="utf-8"))
    assert payload["candidates"][0]["candidate_url"].startswith("https://example.com/")
    assert "research-intake" in artifacts[2].read_text(encoding="utf-8")


def test_research_search_trusted_rss_candidates(monkeypatch, tmp_path):
    seed_workspace(tmp_path)
    feeds_config = tmp_path / "seo-workspace" / "config" / "research-search-feeds.test.yml"
    write(
        feeds_config,
        """feeds:
  search_blog:
    source_type: "search_engine"
    publisher: "Search Blog"
    feed_url: "https://search.example.com/feed.xml"
    authority_score: 45
    usage_note: "Use only for search guidance."
    claim_boundary: "Search guidance only; not a FLASH CAST claim."
""",
    )

    def fake_fetch(feed, *, timeout: int, queries: list[str]):
        return [
            research_search.SearchResult(
                query=queries[0],
                url="https://search.example.com/kitchen-renovation-structured-data",
                title="Kitchen renovation structured data guidance",
                publisher=feed.publisher,
                published_date="2026-06-11",
                snippet="Structured data guidance for service content.",
                provider="trusted-rss",
                source_type=feed.source_type,
                usage_note=feed.usage_note,
                claim_boundary=feed.claim_boundary,
            )
        ]

    monkeypatch.setattr(research_search, "fetch_trusted_feed", fake_fetch)

    result, artifacts = research_search.run_research_search(
        tmp_path,
        provider="trusted-rss",
        fetch_remote=True,
        feeds_config=str(feeds_config),
        limit=5,
    )

    assert result.ok
    assert result.status == "research_search_candidates_ready_for_intake"
    assert result.provider == "trusted-rss"
    assert result.candidates[0].source_type == "search_engine"
    assert result.candidates[0].discovery_status == "search_result:trusted-rss"
    assert "not a FLASH CAST claim" in result.candidates[0].latest_research_arg()
    payload = json.loads(artifacts[1].read_text(encoding="utf-8"))
    assert payload["candidates"][0]["publisher"] == "Search Blog"
    assert any("Trusted RSS config example" in warning for warning in payload["warnings"])
