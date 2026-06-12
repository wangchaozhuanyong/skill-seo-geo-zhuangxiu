from tests.agents.skills.renovation_seo_geo_import import load_citations


citations = load_citations()


def test_citation_opportunities_are_review_queue_only(tmp_path):
    output = citations.write_citation_opportunities(tmp_path)
    rows = citations.read_csv_rows(output)

    assert output.name == "citation-opportunities.csv"
    assert len(rows) >= 5
    assert rows[0]["platform"] == "Google Business Profile"
    assert rows[0]["status"] == "needs_owner_input"
    assert "Do not claim ratings" in rows[0]["notes"]
    assert citations.priority_counts(rows)["high"] >= 1
