from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_calendar


content_calendar = load_content_calendar()


KITCHEN_EN = "https://flashcast.com.my/en/services/kitchen"
KITCHEN_ZH = "https://flashcast.com.my/zh/services/kitchen"
BATHROOM_EN = "https://flashcast.com.my/en/services/bathroom"
BATHROOM_ZH = "https://flashcast.com.my/zh/services/bathroom"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path, *, recent_kitchen: bool = False) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "brand-profile.md",
        "- Brand name: FLASH CAST\n- Company name: FLASH CAST SDN. BHD.\n- Website: https://flashcast.com.my/\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen renovation malaysia,commercial,ready,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen renovation,Kuala Lumpur,\n"
        "bathroom renovation malaysia,commercial,ready,/en/services/bathroom,/en/services/bathroom,service,high,Bathroom renovation,Kuala Lumpur,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        f"{KITCHEN_EN},en,service,200,yes,yes,,{KITCHEN_EN},yes,yes,Kitchen Renovation,Kitchen renovation,Kitchen Renovation,500,1,1,WebPage,1,0,,yes,\n"
        f"{KITCHEN_ZH},zh,service,200,yes,yes,,{KITCHEN_ZH},yes,yes,厨房装修,厨房装修,厨房装修,500,1,1,WebPage,1,0,,yes,\n"
        f"{BATHROOM_EN},en,service,200,yes,yes,,{BATHROOM_EN},yes,yes,Bathroom Renovation,Bathroom renovation,Bathroom Renovation,500,1,1,WebPage,1,0,,yes,\n"
        f"{BATHROOM_ZH},zh,service,200,yes,yes,,{BATHROOM_ZH},yes,yes,浴室装修,浴室装修,浴室装修,500,1,1,WebPage,1,0,,yes,\n",
    )
    write(tmp_path / "seo-workspace" / "data" / "internal-links.csv", "source_url,target_url,anchor_text,context,priority\n")
    write(tmp_path / "seo-workspace" / "data" / "case-studies.csv", "project_name,service,related_url,location,scope,result\n")
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Kitchen renovation; Bathroom renovation,/en/locations/kuala-lumpur,,,yes\n",
    )
    if recent_kitchen:
        write(
            tmp_path / "seo-workspace" / "data" / "daily-automation-run.json",
            json.dumps({"selected_task": {"target_url": KITCHEN_EN}}, ensure_ascii=False, indent=2) + "\n",
        )


def test_content_calendar_generates_bilingual_rotating_plan(tmp_path):
    seed_workspace(tmp_path)

    result, artifacts = content_calendar.run_content_calendar(tmp_path, days=2, start_date="2026-06-15")

    assert result.ok
    assert result.status == "content_calendar_ready_for_owner_review"
    assert len(result.calendar) == 2
    assert all(row["paired_url"] for row in result.calendar)
    assert all(row["owner_review_required"] == "yes" for row in result.calendar)
    json_path, csv_path, report_path = artifacts
    assert json_path.exists()
    assert csv_path.exists()
    assert report_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["no_live_actions_executed"] is True
    assert "calendar-only" in report_path.read_text(encoding="utf-8")


def test_content_calendar_penalizes_recent_repeat_url(tmp_path):
    seed_workspace(tmp_path, recent_kitchen=True)

    result, _ = content_calendar.run_content_calendar(tmp_path, days=2, start_date="2026-06-15")

    assert result.ok
    assert result.calendar[0]["target_url"] == BATHROOM_EN
    kitchen_row = next(row for row in result.calendar if row["target_url"] == KITCHEN_EN)
    assert "recent_repeat_penalty" in kitchen_row["rotation_notes"]
