import json
from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_schema_generator, load_schema_validator


schema_generator = load_schema_generator()
schema_validator = load_schema_validator()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "brand-profile.md",
        """# Brand Profile

## Company

- Company name: FLASH CAST SDN. BHD.
- Brand name: FLASH CAST
- Website: https://flashcast.com.my/
- Phone: +601128853888
- Email: flashcast001@gmail.com
- Address if public: 94, Jalan Mega Mendung,Taman United, 58200 Kuala Lumpur

## Proof

- Real testimonials: No published testimonials found in public homepage data.
""",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "services.md",
        """# Services

### Residential Renovation

- Existing URL: https://flashcast.com.my/en/services/renovation
- Description: Home renovation in KL and Selangor.
""",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Residential renovation,/en/locations/kuala-lumpur,,,yes\n"
        "Selangor,Malaysia,Selangor,Selangor,,Residential renovation,/en/locations/selangor,,,yes\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "case-studies.csv",
        "project_name,location,property_type,size,budget_range,timeline,service,year,client_goal,main_problem,scope,materials,challenge,solution,result,photos_available,testimonial,related_url,notes\n",
    )
    write(
        tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-residential-renovation-content-brief.md",
        "# Brief\n\nBilingual FAQ\n",
    )


def test_schema_generator_outputs_supported_schema_without_fake_rating(tmp_path):
    seed_workspace(tmp_path)

    output = schema_generator.write_schema_recommendations(tmp_path)
    schemas = json.loads(output.read_text(encoding="utf-8"))
    types = {item if isinstance(item, str) else tuple(item) for schema in schemas for item in ([schema["@type"]] if isinstance(schema["@type"], str) else schema["@type"])}
    text = output.read_text(encoding="utf-8")

    assert output.name == "schema-recommendations.json"
    assert "Organization" in types
    assert "LocalBusiness" in types
    assert "HomeAndConstructionBusiness" in types
    assert "Service" in types
    assert "FAQPage" in types
    assert "ImageObject" in types
    assert "VideoObject" in types
    assert "AggregateRating" not in text
    assert '"review"' not in text
    assert "priceRange" not in text
    assert "openingHours" not in text


def test_schema_validator_blocks_fake_review_rating_price_hours_and_area(tmp_path):
    seed_workspace(tmp_path)
    fake_schemas = [
        {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "FLASH CAST SDN. BHD.",
            "aggregateRating": {"@type": "AggregateRating", "ratingValue": "5"},
            "priceRange": "$$",
            "openingHours": "Mo-Fr 09:00-18:00",
            "areaServed": [{"@type": "Place", "name": "Unsupported City"}],
        },
        {
            "@context": "https://schema.org",
            "@type": "Review",
            "reviewBody": "Fake review",
        },
    ]

    validation = schema_validator.validate_schemas(tmp_path, fake_schemas)

    assert not validation.ok
    messages = "\n".join(issue.message for issue in validation.issues)
    assert "Forbidden or owner-input field present: aggregateRating" in messages
    assert "Forbidden or owner-input field present: priceRange" in messages
    assert "Forbidden or owner-input field present: openingHours" in messages
    assert "Unsupported service area" in messages
    assert "requires real owner-provided data" in messages


def test_schema_report_contains_rules_and_waiting_status(tmp_path):
    seed_workspace(tmp_path)
    schema_generator.write_schema_recommendations(tmp_path)

    output = schema_validator.run_schema_validation_report(tmp_path)
    text = output.read_text(encoding="utf-8")

    assert output.name == f"{date.today().isoformat()}-schema-report.md"
    assert "Organization" in text
    assert "LocalBusiness" in text
    assert "HomeAndConstructionBusiness" in text
    assert "Service" in text
    assert "FAQPage" in text
    assert "BreadcrumbList" in text
    assert "ImageObject" in text
    assert "VideoObject" in text
    assert "不允许 fake rating" in text
    assert "不允许 fake review" in text
    assert "不允许 fake price" in text
    assert "不允许 fake opening hours" in text
    assert "不允许 fake service area" in text
    assert "等待业主审核和明确执行指令" in text
