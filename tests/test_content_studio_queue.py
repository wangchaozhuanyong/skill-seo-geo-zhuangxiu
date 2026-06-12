from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_queue


content_studio_queue = load_content_studio_queue()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        "https://flashcast.com.my/en/services/kitchen,en,service,200,yes,yes,,https://flashcast.com.my/en/services/kitchen,yes,yes,Kitchen,Kitchen,Kitchen,500,1,1,WebPage,1,0,,yes,\n"
        "https://flashcast.com.my/zh/services/kitchen,zh,service,200,yes,yes,,https://flashcast.com.my/zh/services/kitchen,yes,yes,厨房,厨房,厨房,500,1,1,WebPage,1,0,,yes,\n"
        "https://flashcast.com.my/en/blog/kitchen-cabinet-price-malaysia,en,article,200,yes,yes,,https://flashcast.com.my/en/blog/kitchen-cabinet-price-malaysia,yes,yes,Kitchen Cabinet,Kitchen Cabinet,Kitchen Cabinet,700,1,1,Article,1,0,,yes,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen renovation malaysia,commercial,ready,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen renovation,Kuala Lumpur,\n"
        "kitchen cabinet price malaysia,informational,research,/en/blog/kitchen-cabinet-price-malaysia,/en/blog/kitchen-cabinet-price-malaysia,article,medium,Kitchen cabinet,Malaysia,\n",
    )
    write(tmp_path / "seo-workspace" / "data" / "internal-links.csv", "source_url,target_url,anchor_text,context,priority\n")
    write(tmp_path / "seo-workspace" / "data" / "case-studies.csv", "project_name,service,related_url,location,scope,result\n")
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Kitchen renovation,/en/locations/kuala-lumpur,,,yes\n",
    )


def test_content_studio_queue_builds_bilingual_production_queue(tmp_path: Path):
    seed_workspace(tmp_path)

    summary, artifacts = content_studio_queue.run_content_studio_queue(tmp_path)
    json_path, csv_path, report_path = artifacts
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    rows = payload["queue"]
    kitchen = next(row for row in rows if row["target_url"] == "https://flashcast.com.my/en/services/kitchen")

    assert summary["status"] == "content_studio_queue_ready_for_owner_review"
    assert summary["no_live_actions_executed"] is True
    assert summary["no_cms_write_executed"] is True
    assert len(rows) == 2
    assert kitchen["paired_url"] == "https://flashcast.com.my/zh/services/kitchen"
    assert kitchen["recommended_pipeline"] == "rich-content"
    assert "content-studio --target-url https://flashcast.com.my/en/services/kitchen" in kitchen["content_studio_command"]
    assert "service-pattern-package --service-slug kitchen" in kitchen["service_pattern_command"]
    assert csv_path.is_file()
    assert "Content Studio Queue" in report_path.read_text(encoding="utf-8")


def test_content_studio_queue_limit(tmp_path: Path):
    seed_workspace(tmp_path)

    summary, _ = content_studio_queue.run_content_studio_queue(tmp_path, limit=1)

    assert summary["queue_count"] == 1
