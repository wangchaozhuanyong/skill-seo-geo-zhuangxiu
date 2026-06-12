import csv
from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_opportunity_finder


finder = load_opportunity_finder()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_opportunity_finder_generates_sorted_report(tmp_path):
    write(tmp_path / "seo-workspace" / "data" / "brand-profile.md", "- Website: https://example.com/\n")
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen renovation,commercial,ready,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen renovation,Kuala Lumpur,\n"
        "paint ideas,informational,learn,/en/blog/paint,/en/blog/paint,article,low,Paint,,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_self,hreflang_pair,schema_types,internal_inlinks_count,internal_outlinks_count,word_count,sitemap_included\n"
        "https://example.com/en/services/kitchen,en,service,200,yes,yes,,yes,yes,WebPage,1,1,500,yes\n"
        "https://example.com/zh/services/kitchen,zh,service,200,yes,yes,,yes,yes,WebPage,1,1,500,yes\n"
        "https://example.com/en/blog/paint,en,article,200,yes,yes,,yes,yes,WebPage,1,1,500,yes\n",
    )
    write(tmp_path / "seo-workspace" / "data" / "internal-links.csv", "source_url,target_url,anchor_text,context,priority\n")
    write(tmp_path / "seo-workspace" / "data" / "case-studies.csv", "project_name,service,related_url\n")
    write(tmp_path / "seo-workspace" / "data" / "service-areas.csv", "area,country,state_or_region,city,verified\nKuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,yes\n")
    write(tmp_path / "seo-workspace" / "data" / "gsc-pages.csv", "page,clicks,impressions,ctr,position\n")
    write(tmp_path / "seo-workspace" / "data" / "gsc-queries.csv", "query,clicks,impressions,ctr,position\n")
    write(tmp_path / "seo-workspace" / "data" / "google-index-status.csv", "url,inspection_state,verdict,coverage_state\n")

    scores = finder.run_opportunity_finder(tmp_path)

    assert scores[0].url == "https://example.com/en/services/kitchen"
    assert (tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-seo-opportunity-score.md").exists()
    with (tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["url"] == "https://example.com/en/services/kitchen"
