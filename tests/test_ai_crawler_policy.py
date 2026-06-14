import csv
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_ai_crawler_policy


ai_crawler_policy = load_ai_crawler_policy()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ai_crawler_policy_detects_blocked_visibility_agent_and_missing_llms(tmp_path):
    write(tmp_path / "seo-workspace" / "data" / "brand-profile.md", "- Website: https://example.com/\n")
    write(
        tmp_path / "public" / "robots.txt",
        "User-agent: OAI-SearchBot\n"
        "Disallow: /\n"
        "\n"
        "User-agent: GPTBot\n"
        "Disallow: /\n"
        "\n"
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://example.com/sitemap.xml\n",
    )

    summary, artifacts = ai_crawler_policy.run_ai_crawler_policy_report(tmp_path, paths=["/"])

    assert summary["policy_row_count"] == len(ai_crawler_policy.BOT_PROFILES)
    assert summary["blocked_visibility_count"] == 1
    assert (tmp_path / "seo-workspace" / "data" / "ai-crawler-policy.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "ai-crawler-policy-findings.csv").exists()
    assert len(artifacts) == 5
    with (tmp_path / "seo-workspace" / "data" / "ai-crawler-policy-findings.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    categories = {row["category"] for row in rows}
    assert "ai_search_access" in categories
    assert "llms_txt" in categories
    assert "training_opt_out" in categories


def test_ai_crawler_policy_accepts_local_llms_and_default_allow_without_robots(tmp_path):
    write(tmp_path / "seo-workspace" / "data" / "brand-profile.md", "- Website: https://example.com/\n")
    write(tmp_path / "public" / "llms.txt", "# Example\n\n- https://example.com/en/services/kitchen\n")

    summary, _artifacts = ai_crawler_policy.run_ai_crawler_policy_report(tmp_path, paths=["/en/"])

    assert summary["blocked_visibility_count"] == 0
    assert summary["finding_count"] == 1


def test_ai_crawler_owner_review_draft_writes_robots_and_llms_without_publishing(tmp_path):
    write(tmp_path / "seo-workspace" / "data" / "brand-profile.md", "- Company name: Example Sdn Bhd\n- Website: https://example.com/\n")
    write(
        tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv",
        "url,keyword,language,page_type,service,location,total_score,task_type,positive_events,penalty_events\n"
        "https://example.com/en/services/kitchen,kitchen renovation,en,service,kitchen,Kuala Lumpur,30,service,,\n",
    )

    summary, artifacts = ai_crawler_policy.run_ai_crawler_owner_review_draft(tmp_path)

    assert summary["status"] == "ai_crawler_owner_review_draft_ready"
    assert summary["owner_approval_required_before_publish"] is True
    assert len(artifacts) == 4
    robots_text = artifacts[0].read_text(encoding="utf-8")
    llms_text = artifacts[1].read_text(encoding="utf-8")
    assert "OAI-SearchBot" in robots_text
    assert "# User-agent: GPTBot" in robots_text
    assert "https://example.com/en/services/kitchen" in llms_text
    assert "Do not publish without owner approval" in llms_text
