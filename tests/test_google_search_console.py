from tests.agents.skills.renovation_seo_geo_import import load_google_search_console


gsc = load_google_search_console()


def test_config_reports_missing_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GSC_OAUTH_CLIENT_CONFIG", raising=False)
    monkeypatch.delenv("GSC_OAUTH_TOKEN_JSON", raising=False)
    monkeypatch.delenv("GSC_SITE_URL", raising=False)

    config = gsc.GoogleSearchConsoleConfig.from_env()

    assert "GSC_SITE_URL" in config.missing_configuration()
    assert "GOOGLE_APPLICATION_CREDENTIALS or OAuth config" in config.missing_configuration()
    assert not config.can_use_api()


def test_normalize_search_analytics_response():
    rows = gsc.normalize_search_analytics_response(
        {
            "rows": [
                {
                    "keys": ["kitchen renovation", "https://example.com/en/services/kitchen", "mys", "DESKTOP", "2026-06-01"],
                    "clicks": 3,
                    "impressions": 100,
                    "ctr": 0.03,
                    "position": 4.2,
                }
            ]
        },
        ["query", "page", "country", "device", "date"],
    )

    assert rows == [
        {
            "query": "kitchen renovation",
            "page": "https://example.com/en/services/kitchen",
            "country": "mys",
            "device": "DESKTOP",
            "date": "2026-06-01",
            "clicks": "3",
            "impressions": "100",
            "ctr": "0.03",
            "position": "4.2",
        }
    ]


def test_write_search_analytics_outputs(tmp_path):
    rows = [
        {
            "query": "kitchen renovation",
            "page": "https://example.com/en/services/kitchen",
            "clicks": "2",
            "impressions": "100",
            "ctr": "0.02",
            "position": "5",
        },
        {
            "query": "kitchen renovation",
            "page": "https://example.com/en/services/kitchen",
            "clicks": "1",
            "impressions": "50",
            "ctr": "0.02",
            "position": "3",
        },
    ]

    queries_path, pages_path = gsc.write_search_analytics_outputs(tmp_path, rows)

    assert queries_path.exists()
    assert pages_path.exists()
    assert "kitchen renovation,3,150,0.020000,4.33" in queries_path.read_text(encoding="utf-8")
