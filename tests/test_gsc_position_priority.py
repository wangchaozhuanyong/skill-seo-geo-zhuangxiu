from tests.agents.skills.renovation_seo_geo_import import load_scoring


scoring = load_scoring()


def inventory():
    return {
        "page_type": "service",
        "indexable": "yes",
        "robots_allowed": "yes",
        "canonical_self": "yes",
        "schema_types": "WebPage",
        "internal_inlinks_count": "2",
        "internal_outlinks_count": "2",
    }


def labels_for_position(position):
    score = scoring.score_candidate(
        url="https://example.com/en/services/kitchen",
        keyword_row={"search_intent": "commercial", "page_type": "service"},
        inventory_row=inventory(),
        performance_row={"position": str(position), "impressions": "50", "ctr": "0.1"},
        inventory_urls={"https://example.com/en/services/kitchen", "https://example.com/zh/services/kitchen"},
    )
    return {event.label for event in score.events}


def test_gsc_position_2_3_priority():
    assert "existing ranking position 2-3" in labels_for_position(2.5)


def test_gsc_position_4_10_priority():
    assert "existing ranking position 4-10" in labels_for_position(7)


def test_gsc_position_11_20_priority():
    assert "existing ranking position 11-20" in labels_for_position(15)


def test_high_impression_low_ctr_priority():
    score = scoring.score_candidate(
        url="https://example.com/en/services/kitchen",
        keyword_row={"search_intent": "commercial", "page_type": "service"},
        inventory_row=inventory(),
        performance_row={"position": "6", "impressions": "500", "ctr": "0.005"},
        google_index_row={"inspection_state": "checked", "verdict": "PASS"},
        inventory_urls={"https://example.com/en/services/kitchen", "https://example.com/zh/services/kitchen"},
    )

    labels = {event.label for event in score.events}
    assert "high impressions low CTR" in labels
    assert "indexed but low CTR" in labels
