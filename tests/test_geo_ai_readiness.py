from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_geo_ai


geo_ai = load_geo_ai()


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

### Kitchen Renovation

- Existing URL: https://flashcast.com.my/en/services/kitchen
- Chinese URL: https://flashcast.com.my/zh/services/kitchen
- Description: Kitchen renovation.

### Bathroom Renovation

- Existing URL: https://flashcast.com.my/en/services/bathroom
- Chinese URL: https://flashcast.com.my/zh/services/bathroom
- Description: Bathroom renovation.

### Office Renovation

- Existing URL: https://flashcast.com.my/en/services/office-renovation
- Chinese URL: https://flashcast.com.my/zh/services/office-renovation
- Description: Office renovation.

### Shop Renovation

- Existing URL: https://flashcast.com.my/en/services/shop-renovation
- Chinese URL: https://flashcast.com.my/zh/services/shop-renovation
- Description: Shop renovation.
""",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Residential renovation,/en/locations/kuala-lumpur,Mont Kiara Luxury Condo Renovation,,yes\n"
        "Selangor,Malaysia,Selangor,Selangor,,Residential renovation,/en/locations/selangor,,,yes\n"
        "Klang Valley,Malaysia,Kuala Lumpur and Selangor,Klang Valley,,Residential renovation,,,,yes\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "case-studies.csv",
        "project_name,location,property_type,size,budget_range,timeline,service,year,client_goal,main_problem,scope,materials,challenge,solution,result,photos_available,testimonial,related_url,notes\n"
        "Mont Kiara Luxury Condo Renovation,\"Mont Kiara, Kuala Lumpur\",Condo,1250 sq ft,NEEDS OWNER INPUT,8 weeks,Residential renovation,,,,,,,,yes,,/en/projects/mont-kiara-luxury-condo-renovation,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,hreflang_pair,schema_types,internal_inlinks_count,internal_outlinks_count,word_count\n"
        "https://flashcast.com.my/zh/services/renovation,zh,service,200,yes,yes,yes,yes,WebPage;Service,2,2,320\n",
    )
    write(
        tmp_path / "seo-workspace" / "drafts" / "2026-06-07-residential-renovation-content-brief.md",
        "# Brief\n\n中文页面建议文案\n\n英文页面建议文案\n\nBilingual FAQ\n\nQA Checklist\n\n概念设计\n\nrendering concept\n",
    )


def test_geo_ai_report_contains_required_checks_and_guardrails(tmp_path):
    seed_workspace(tmp_path)

    output = geo_ai.run_geo_ai_report(tmp_path)
    text = output.read_text(encoding="utf-8")

    assert output.name == f"{date.today().isoformat()}-geo-ai-readiness-report.md"
    assert (tmp_path / "seo-workspace" / "data" / "entity-profile.md").exists()
    required = [
        "brand/entity consistency",
        "company name consistency",
        "NAP consistency",
        "service taxonomy",
        "area coverage",
        "direct answer blocks",
        "concise summary blocks",
        "evidence blocks",
        "FAQ",
        "comparison tables only when useful",
        "schema",
        "crawlability",
        "indexability",
        "page clarity",
        "unique non-commodity content",
        "concept/rendering label",
        "不创建 AI bait spam pages",
        "不创建 mass query-variation pages",
        "不伪造 citations",
    ]
    for item in required:
        assert item in text
