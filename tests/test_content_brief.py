from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_content_brief


content_brief = load_content_brief()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(tmp_path / "seo-workspace" / "data" / "brand-profile.md", "- Company name: FLASH CAST SDN. BHD.\n- Website: https://example.com/\n")
    write(
        tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv",
        "url,keyword,language,page_type,service,location,total_score,task_type,positive_events,penalty_events\n"
        "https://example.com/zh/services/renovation,住宅装修 吉隆坡,zh,service,住宅装修,Kuala Lumpur,20,high-commercial-intent page optimization,,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,hreflang_pair,schema_types,internal_inlinks_count,internal_outlinks_count,word_count\n"
        "https://example.com/zh/services/renovation,zh,service,200,yes,yes,yes,yes,WebPage,1,1,20\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "住宅装修 吉隆坡,commercial,ready,/zh/services/renovation,/zh/services/renovation,service,high,住宅装修,Kuala Lumpur,\n",
    )


def test_content_brief_contains_required_bilingual_sections(tmp_path):
    seed_workspace(tmp_path)

    output = content_brief.run_content_brief(tmp_path)
    text = output.read_text(encoding="utf-8")

    required = [
        "中文页面建议文案",
        "英文页面建议文案",
        "Bilingual SEO Title",
        "Bilingual Meta Description",
        "Bilingual Slug",
        "Bilingual H1/H2/H3",
        "Bilingual FAQ",
        "Bilingual Internal Links",
        "Bilingual Image Brief",
        "Bilingual Alt Text",
        "CTA",
        "Schema 建议",
        "Owner Approval Notes",
        "QA Checklist",
        "等待业主审核和明确执行指令",
    ]
    for item in required:
        assert item in text

    assert output.name == f"{date.today().isoformat()}-residential-renovation-content-brief.md"
