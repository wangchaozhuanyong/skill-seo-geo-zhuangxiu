from tests.agents.skills.renovation_seo_geo_import import load_robots_sitemap


robots_sitemap = load_robots_sitemap()


def test_parse_sitemap_xml_with_lastmod():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://example.com/en/services/kitchen</loc>
        <lastmod>2026-06-07</lastmod>
      </url>
    </urlset>
    """
    entries = robots_sitemap.parse_sitemap_xml(xml)
    assert len(entries) == 1
    assert entries[0].loc == "https://example.com/en/services/kitchen"
    assert entries[0].lastmod == "2026-06-07"


def test_robots_allowed_respects_disallow():
    robots = "User-agent: *\nDisallow: /admin\nSitemap: https://example.com/sitemap.xml\n"
    info = robots_sitemap.parse_robots_txt(robots)
    assert info.sitemaps == ["https://example.com/sitemap.xml"]
    assert robots_sitemap.robots_allowed("https://example.com/en/services", robots)
    assert not robots_sitemap.robots_allowed("https://example.com/admin", robots)
