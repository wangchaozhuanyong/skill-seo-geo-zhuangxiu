from tests.agents.skills.renovation_seo_geo_import import load_url_inventory


url_inventory = load_url_inventory()


def test_url_inventory_infers_language_page_type_and_sitemap_defaults():
    row = url_inventory.blank_inventory_row("https://flashcast.com.my/zh/services/kitchen")

    assert row["language"] == "zh"
    assert row["page_type"] == "service"
    assert row["sitemap_included"] == "no"
    assert row["canonical_self"] == "unknown"
