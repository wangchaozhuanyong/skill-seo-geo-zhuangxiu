from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_local_seo


local_seo = load_local_seo()


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

## Proof

- Real testimonials: No published testimonials found in public homepage data.
""",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "entity-profile.md",
        "FLASH CAST SDN. BHD.\n+601128853888\n概念设计\nrendering concept\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Residential renovation,/en/locations/kuala-lumpur,,,yes\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,hreflang_pair,schema_types,internal_inlinks_count,internal_outlinks_count,word_count\n"
        "https://flashcast.com.my/en/locations/kuala-lumpur,en,local,200,yes,yes,yes,yes,LocalBusiness;Service,2,2,300\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "renovation kuala lumpur,commercial,ready,/en/locations/kuala-lumpur,/en/locations/kuala-lumpur,local,high,Residential renovation,Kuala Lumpur,\n",
    )


def test_local_seo_report_includes_required_checks_and_guardrails(tmp_path):
    seed_workspace(tmp_path)

    output = local_seo.run_local_seo_report(tmp_path)
    text = output.read_text(encoding="utf-8")

    assert output.name == f"{date.today().isoformat()}-local-seo-report.md"
    assert (tmp_path / "seo-workspace" / "data" / "citation-opportunities.csv").exists()
    required = [
        "Google Business Profile data import",
        "Baidu local/map data import if provided",
        "NAP consistency",
        "service areas",
        "city pages",
        "local schema",
        "local CTA",
        "reviews only if real",
        "local photos only if real",
        "concept images must be labeled",
        "citation opportunities",
        "unsupported locations",
        "不使用虚假评价",
        "不创建 city-swap doorway pages",
    ]
    for item in required:
        assert item in text
