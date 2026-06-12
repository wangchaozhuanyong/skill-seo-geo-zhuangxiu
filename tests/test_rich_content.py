from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_rich_content


rich_content = load_rich_content()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "brand-profile.md",
        "- Company name: FLASH CAST SDN. BHD.\n- Brand name: FLASH CAST\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,sitemap_included\n"
        "https://flashcast.com.my/en/blog/kitchen-cabinet-price-malaysia,en,article,200,yes,yes,yes,yes,Kitchen Cabinet,Kitchen Cabinet,Kitchen Cabinet,600,2,2,Article,1,0,yes\n"
        "https://flashcast.com.my/en/services/kitchen,en,service,200,yes,yes,yes,yes,Kitchen,Kitchen,Kitchen,400,2,2,Service,0,0,yes\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen cabinet price malaysia,informational,consideration,/en/blog/kitchen-cabinet-price-malaysia,/en/blog/kitchen-cabinet-price-malaysia,article,medium,Kitchen cabinet,Malaysia,\n"
        "kitchen renovation malaysia,commercial,ready-to-contact,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen renovation,Kuala Lumpur; Selangor,\n",
    )


def test_rich_content_marks_article_without_sources_as_needing_live_search(tmp_path):
    seed_workspace(tmp_path)

    output = rich_content.write_rich_content_package(
        tmp_path,
        target_url="https://flashcast.com.my/en/blog/kitchen-cabinet-price-malaysia",
        topic="Kitchen Cabinet Price Malaysia",
    )
    text = output.read_text(encoding="utf-8")
    source_log = tmp_path / "seo-workspace" / "data" / "research-source-log.csv"

    assert output.name == f"{date.today().isoformat()}-en-blog-kitchen-cabinet-price-malaysia-rich-content-package.md"
    assert "NEEDS LIVE SEARCH" in text
    assert "图文内容块 / Image-Rich Blocks" in text
    assert "Publishing Field Map" in text
    assert "research-source-log.csv" in text
    assert source_log.exists()
    assert source_log.read_text(encoding="utf-8").startswith("date_added,target_url,source_type")


def test_rich_content_writes_sources_and_concept_labels(tmp_path):
    seed_workspace(tmp_path)
    source = rich_content.ResearchSource.from_cli(
        "manufacturer|Cabinet hardware guide|https://example.com/hardware|Example Publisher|2026-06-10|Use for material guidance only"
    )

    output = rich_content.write_rich_content_package(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        topic="Kitchen Renovation Malaysia",
        sources=[source],
    )
    text = output.read_text(encoding="utf-8")
    source_log = (tmp_path / "seo-workspace" / "data" / "research-source-log.csv").read_text(encoding="utf-8")

    assert "source_log_attached (1 source rows)" in text
    assert "Cabinet hardware guide" in text
    assert "概念设计 / 效果图方案 / 规划示例" in text
    assert "generated images must include concept/rendering labels" in text
    assert "Cabinet hardware guide" in source_log


def test_rich_content_auto_attaches_existing_research_log(tmp_path):
    seed_workspace(tmp_path)
    source_log_path = tmp_path / "seo-workspace" / "data" / "research-source-log.csv"
    write(
        source_log_path,
        "\n".join(
            [
                "date_added,target_url,source_type,source_title,source_url,publisher,published_or_accessed_date,usage_note,claim_boundary",
                "2026-06-10,https://flashcast.com.my/en/services/kitchen,official,Google structured data,https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data,Google Search Central,2026-06-10,Use only for schema guidance,general guidance only; not a FLASH CAST business claim",
            ]
        )
        + "\n",
    )

    output = rich_content.write_rich_content_package(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        topic="Kitchen Renovation Malaysia",
    )
    text = output.read_text(encoding="utf-8")
    source_log = source_log_path.read_text(encoding="utf-8")

    assert "source_log_attached (1 source rows)" in text
    assert "Google structured data" in text
    assert source_log.count("https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data") == 1
