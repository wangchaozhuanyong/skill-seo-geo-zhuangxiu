from tests.agents.skills.renovation_seo_geo_import import load_canonical, load_hreflang


canonical = load_canonical()
hreflang = load_hreflang()


def test_extract_canonical_and_compare_self():
    html = '<html><head><link rel="canonical" href="/en/services/kitchen"></head></html>'
    page_url = "https://example.com/en/services/kitchen/"
    canonical_url = canonical.extract_canonical_url(html, page_url)
    assert canonical_url == "https://example.com/en/services/kitchen"
    assert canonical.is_self_canonical(page_url, canonical_url)


def test_hreflang_pair_detection_for_language_pair():
    html = """
    <link rel="alternate" hreflang="en" href="https://example.com/en/services/kitchen">
    <link rel="alternate" hreflang="zh" href="https://example.com/zh/services/kitchen">
    """
    page_url = "https://example.com/en/services/kitchen"
    links = hreflang.extract_hreflang_links(html, page_url)
    assert hreflang.detect_language_from_url(page_url) == "en"
    assert hreflang.expected_pair_url(page_url) == "https://example.com/zh/services/kitchen"
    assert hreflang.has_hreflang_pair(page_url, links)
