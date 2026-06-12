from tests.agents.skills.renovation_seo_geo_import import load_scoring
from tests.test_gsc_position_priority import inventory


scoring = load_scoring()


def test_high_impression_low_ctr_priority_file():
    score = scoring.score_candidate(
        url="https://example.com/en/services/kitchen",
        keyword_row={"search_intent": "commercial", "page_type": "service"},
        inventory_row=inventory(),
        performance_row={"position": "8", "impressions": "1000", "ctr": "0.001"},
        google_index_row={"inspection_state": "checked", "verdict": "PASS"},
        inventory_urls={"https://example.com/en/services/kitchen", "https://example.com/zh/services/kitchen"},
    )

    assert "high impressions low CTR" in {event.label for event in score.events}
