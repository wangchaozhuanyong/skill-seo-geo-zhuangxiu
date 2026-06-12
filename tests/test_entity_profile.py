from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_entity_profile


entity_profile = load_entity_profile()


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
- Main service area: Kuala Lumpur, Selangor, and Klang Valley
- Phone: +601128853888
- Email: flashcast001@gmail.com
- Address if public: 94, Jalan Mega Mendung,Taman United, 58200 Kuala Lumpur
- Google Business Profile: NEEDS OWNER INPUT
- Licenses/certifications: Public site states SSM registered company; SSM number and other certifications need owner confirmation.
- Insurance/warranty: Public site states workmanship warranty and after-sales support; exact warranty scope and duration need owner confirmation.

## Positioning

- Main value proposition: Design-and-build renovation support.

## Proof

- Real case studies from public site:
  - Mont Kiara Luxury Condo Renovation
- Awards: NEEDS OWNER INPUT
- Media mentions: NEEDS OWNER INPUT
""",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "services.md",
        """# Services

### Residential Renovation

- Existing URL: https://flashcast.com.my/en/services/renovation
- Chinese URL: https://flashcast.com.my/zh/services/renovation
- Description: Home renovation in KL and Selangor.
- Customer type: Homeowners.
- Problems solved: Old finishes and poor storage.
- Best CTA: Request a renovation quotation.
- Real case study references: Mont Kiara Luxury Condo Renovation.
""",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Residential renovation,/en/locations/kuala-lumpur,Mont Kiara Luxury Condo Renovation,,yes\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "case-studies.csv",
        "project_name,location,property_type,size,budget_range,timeline,service,year,client_goal,main_problem,scope,materials,challenge,solution,result,photos_available,testimonial,related_url,notes\n"
        "Mont Kiara Luxury Condo Renovation,\"Mont Kiara, Kuala Lumpur\",Condo,1250 sq ft,NEEDS OWNER INPUT,8 weeks,Residential renovation,,,,,,,,yes,,/en/projects/mont-kiara-luxury-condo-renovation,\n",
    )


def test_entity_profile_contains_entity_nap_services_and_guardrails(tmp_path):
    seed_workspace(tmp_path)

    output = entity_profile.run_entity_profile(tmp_path)
    text = output.read_text(encoding="utf-8")

    assert output.name == "entity-profile.md"
    assert "FLASH CAST SDN. BHD." in text
    assert "+601128853888" in text
    assert "flashcast001@gmail.com" in text
    assert "Residential Renovation" in text
    assert "Verified area count: 1" in text
    assert "中文直接答案" in text
    assert "English Direct Answer" in text
    assert "NEEDS OWNER INPUT" in text
    assert "不创建 AI bait spam pages" in text
    assert "rendering concept" in text
