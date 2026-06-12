from tests.agents.skills.renovation_seo_geo_import import load_scoring


scoring = load_scoring()


def base_inventory(**overrides):
    row = {
        "url": "https://example.com/en/services/kitchen",
        "language": "en",
        "page_type": "service",
        "status_code": "200",
        "indexable": "yes",
        "robots_allowed": "yes",
        "meta_robots": "",
        "canonical_self": "yes",
        "hreflang_pair": "yes",
        "schema_types": "WebPage",
        "internal_inlinks_count": "1",
        "internal_outlinks_count": "1",
        "word_count": "500",
        "sitemap_included": "yes",
    }
    row.update(overrides)
    return row


def keyword(**overrides):
    row = {
        "keyword": "kitchen renovation kuala lumpur",
        "search_intent": "commercial",
        "page_type": "service",
        "service": "Kitchen renovation",
        "location": "Kuala Lumpur",
    }
    row.update(overrides)
    return row


def test_commercial_service_page_scores_high_value_signals():
    score = scoring.score_candidate(
        url="https://example.com/en/services/kitchen",
        keyword_row=keyword(),
        inventory_row=base_inventory(),
        inventory_urls={
            "https://example.com/en/services/kitchen",
            "https://example.com/zh/services/kitchen",
        },
        service_areas=[{"area": "Kuala Lumpur", "city": "Kuala Lumpur", "country": "Malaysia", "verified": "yes"}],
    )

    labels = {event.label for event in score.events}
    assert "commercial intent" in labels
    assert "local commercial intent" in labels
    assert "service page" in labels
    assert "missing FAQ" in labels
    assert score.total_score >= 15


def test_technical_blockers_apply_negative_scores():
    score = scoring.score_candidate(
        url="https://example.com/en/services/kitchen",
        keyword_row=keyword(),
        inventory_row=base_inventory(indexable="no", robots_allowed="no", canonical_self="no"),
        inventory_urls={"https://example.com/en/services/kitchen"},
    )

    labels = {event.label for event in score.events}
    assert "not indexable" in labels
    assert "blocked by robots" in labels
    assert "canonical to wrong URL" in labels
    assert score.task_type == "technical SEO fix"


def test_missing_language_pair_penalizes_bilingual_gap():
    score = scoring.score_candidate(
        url="https://example.com/en/services/kitchen",
        keyword_row=keyword(),
        inventory_row=base_inventory(),
        inventory_urls={"https://example.com/en/services/kitchen"},
    )

    assert "missing /zh or /en pair" in {event.label for event in score.events}
