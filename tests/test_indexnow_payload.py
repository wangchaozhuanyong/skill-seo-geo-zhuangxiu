from tests.agents.skills.renovation_seo_geo_import import load_indexnow


indexnow = load_indexnow()


def test_indexnow_key_validation():
    assert indexnow.is_valid_key("abcDEF123-456")
    assert not indexnow.is_valid_key("short")
    assert not indexnow.is_valid_key("contains_space bad")


def test_indexnow_payload_includes_key_location():
    config = indexnow.IndexNowConfig(
        key="abcDEF123456",
        key_location="https://example.com/key.txt",
        host="example.com",
    )

    payload = indexnow.build_payload(["https://example.com/en"], config)

    assert payload == {
        "host": "example.com",
        "key": "abcDEF123456",
        "keyLocation": "https://example.com/key.txt",
        "urlList": ["https://example.com/en"],
    }


def test_indexnow_response_200_is_received_not_indexed():
    response = indexnow.classify_response(200)

    assert response["status"] == "received"
    assert "indexing guarantee" in response["message"]


def test_indexnow_host_ownership_filters_other_hosts():
    config = indexnow.IndexNowConfig(host="example.com")
    urls = [
        "https://example.com/en",
        "https://other.com/en",
    ]

    assert indexnow.validate_host_ownership(urls, config) == ["https://example.com/en"]
