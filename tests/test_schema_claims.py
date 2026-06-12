from tests.agents.skills.renovation_seo_geo_import import load_schema_validator


schema_validator = load_schema_validator()


def test_schema_claims_block_fake_price_hours_and_service_area(tmp_path):
    fake_schema = [{
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "FLASH CAST SDN. BHD.",
        "priceRange": "$$",
        "openingHours": "Mo-Fr 09:00-18:00",
        "areaServed": [{"@type": "Place", "name": "Unverified City"}],
    }]

    result = schema_validator.validate_schemas(tmp_path, fake_schema)

    messages = "\n".join(issue.message for issue in result.issues)
    assert not result.ok
    assert "priceRange" in messages
    assert "openingHours" in messages
    assert "Unsupported service area" in messages
