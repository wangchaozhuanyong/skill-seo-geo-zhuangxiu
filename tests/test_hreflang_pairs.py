from tests.agents.skills.renovation_seo_geo_import import load_hreflang


hreflang = load_hreflang()


def test_hreflang_pairs_require_reciprocal_language_path():
    en_url = "https://flashcast.com.my/en/services/renovation"
    zh_url = "https://flashcast.com.my/zh/services/renovation"

    assert hreflang.expected_pair_url(en_url) == zh_url
    assert hreflang.expected_pair_url(zh_url) == en_url
    assert hreflang.has_hreflang_pair(en_url, {"zh": zh_url, "en": en_url})
