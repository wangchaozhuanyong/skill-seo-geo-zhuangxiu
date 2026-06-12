from tests.agents.skills.renovation_seo_geo_import import load_content_refresh, load_page_audit


page_audit = load_page_audit()
content_refresh = load_content_refresh()


def test_page_audit_detects_content_gaps():
    audit = page_audit.audit_page(
        url="https://example.com/zh/services/renovation",
        inventory_row={
            "page_type": "service",
            "language": "zh",
            "status_code": "200",
            "indexable": "yes",
            "robots_allowed": "yes",
            "canonical_self": "yes",
            "hreflang_pair": "yes",
            "schema_types": "WebPage",
            "internal_inlinks_count": "1",
            "internal_outlinks_count": "1",
            "word_count": "20",
        },
        keyword_row={"keyword": "住宅装修 吉隆坡", "page_type": "service"},
        score_row={"total_score": "20"},
    )

    fields = {finding.field for finding in audit.findings}
    assert "FAQ" in fields
    assert "CTA/internal links" in fields
    assert "internal inlinks" in fields
    assert "content depth" in fields


def test_content_refresh_actions_follow_audit_findings():
    audit = page_audit.audit_page(
        url="https://example.com/zh/services/renovation",
        inventory_row={
            "page_type": "service",
            "schema_types": "WebPage",
            "internal_inlinks_count": "1",
            "internal_outlinks_count": "1",
            "word_count": "20",
        },
        keyword_row={},
        score_row={},
    )

    actions = content_refresh.refresh_actions_for_audit(audit)
    sections = {action.section for action in actions}

    assert "FAQ" in sections
    assert "CTA" in sections
    assert "Internal links" in sections
