from tests.agents.skills.renovation_seo_geo_import import load_baidu_integration


baidu = load_baidu_integration()


def test_baidu_config_reports_missing_values(monkeypatch):
    monkeypatch.delenv("BAIDU_SITE", raising=False)
    monkeypatch.delenv("BAIDU_PUSH_TOKEN", raising=False)
    monkeypatch.delenv("BAIDU_SUBMIT_ENDPOINT", raising=False)

    config = baidu.BaiduConfig.from_env()

    assert "BAIDU_SITE" in config.missing_configuration()
    assert "BAIDU_PUSH_TOKEN or BAIDU_SUBMIT_ENDPOINT" in config.missing_configuration()
    assert not config.can_submit()


def test_build_submit_endpoint_uses_site_and_token():
    config = baidu.BaiduConfig(site="https://example.com", push_token="token123")

    endpoint = baidu.build_submit_endpoint(config)

    assert endpoint.startswith("http://data.zz.baidu.com/urls?")
    assert "site=https%3A%2F%2Fexample.com" in endpoint
    assert "token=token123" in endpoint


def test_classify_submitted_urls_handles_baidu_error_lists():
    urls = [
        "https://example.com/a",
        "https://example.com/b",
        "https://other.com/c",
    ]
    response = {
        "status": "accepted",
        "success": 1,
        "not_valid": ["https://example.com/b"],
        "not_same_site": ["https://other.com/c"],
    }

    statuses = baidu.classify_submitted_urls(urls, response)

    assert statuses["https://example.com/a"] == "accepted"
    assert statuses["https://example.com/b"] == "failed:not_valid"
    assert statuses["https://other.com/c"] == "failed:not_same_site"


def test_submit_urls_without_config_needs_owner_input():
    response = baidu.submit_urls(["https://example.com/a"], baidu.BaiduConfig())

    assert response["status"] == "needs-owner-input"
