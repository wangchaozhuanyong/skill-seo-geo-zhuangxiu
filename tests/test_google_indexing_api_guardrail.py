import pytest

from tests.agents.skills.renovation_seo_geo_import import load_google_indexation


google = load_google_indexation()


def test_google_indexing_api_blocks_ordinary_renovation_page():
    row = {
        "url": "https://example.com/en/services/kitchen",
        "page_type": "service",
        "schema_types": "WebPage;HomeAndConstructionBusiness",
    }

    with pytest.raises(google.GoogleIndexingApiBlocked):
        google.assert_google_indexing_api_allowed(row)


def test_google_indexing_api_allows_jobposting_schema():
    row = {"page_type": "job", "schema_types": "WebPage;JobPosting"}

    google.assert_google_indexing_api_allowed(row)


def test_google_indexing_api_allows_broadcast_event_inside_videoobject():
    row = {"page_type": "video", "schema_types": "WebPage;VideoObject;BroadcastEvent"}

    google.assert_google_indexing_api_allowed(row)
