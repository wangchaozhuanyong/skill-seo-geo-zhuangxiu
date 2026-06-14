from tests.agents.skills.renovation_seo_geo_import import load_impact_scoring, load_scoring


impact_scoring = load_impact_scoring()
scoring = load_scoring()


def test_impact_scoring_marks_commercial_metadata_work_as_quick_win():
    score = scoring.OpportunityScore(
        url="https://example.com/en/services/kitchen",
        keyword="kitchen renovation kuala lumpur",
        language="en",
        page_type="service",
        service="Kitchen",
        location="Kuala Lumpur",
    )
    score.add("commercial intent", 5)
    score.add("local commercial intent", 5)
    score.add("service page", 5)
    score.add("missing FAQ", 1)
    score.add("weak internal links", 2)

    impact = impact_scoring.calculate_impact_score(score)

    assert impact.business_impact >= 8
    assert impact.fix_effort <= 4
    assert impact.quick_win is True


def test_impact_scoring_raises_effort_for_technical_blockers():
    score = scoring.OpportunityScore(url="https://example.com/en/services/kitchen", page_type="service")
    score.add("service page", 5)
    score.add("blocked by robots", -10)
    score.add("canonical to wrong URL", -8)

    impact = impact_scoring.calculate_impact_score(score)

    assert impact.seo_impact >= 7
    assert impact.fix_effort >= 6
    assert impact.quick_win is False
