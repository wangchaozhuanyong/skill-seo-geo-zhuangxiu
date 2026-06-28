from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_qa


qa = load_qa()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path, *, fake_claim: bool = False) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        "https://flashcast.com.my/zh/services/renovation,zh,service,200,yes,yes,,https://flashcast.com.my/zh/services/renovation,yes,yes,住宅装修,住宅装修,住宅装修,300,2,2,WebPage,0,0,,yes,\n"
        "https://flashcast.com.my/en/services/renovation,en,service,200,yes,yes,,https://flashcast.com.my/en/services/renovation,yes,yes,Residential Renovation,Residential Renovation,Residential Renovation,300,2,2,WebPage,0,0,,yes,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv",
        "url,keyword,language,page_type,service,location,total_score,task_type,positive_events,penalty_events\n"
        "https://flashcast.com.my/zh/services/renovation,住宅装修 吉隆坡,zh,service,住宅装修,Kuala Lumpur,20,high-commercial-intent page optimization,,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "住宅装修 吉隆坡,commercial,ready,/zh/services/renovation,/zh/services/renovation,service,high,住宅装修,Kuala Lumpur,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Residential renovation,/en/locations/kuala-lumpur,,,yes\n",
    )
    extra = "\nGuaranteed first page ranking." if fake_claim else ""
    write(
        tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-test-content-brief.md",
        "中文页面建议文案\n概念设计\n英文页面建议文案\nrendering concept\nCTA: 获取免费报价\n/internal link `/zh/quote` and `/en/quote`.\nNEEDS OWNER INPUT: confirm WhatsApp.\n"
        + extra,
    )
    write(
        tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-schema-report.md",
        "Errors: 0\nStatus: PASS\n",
    )


def test_qa_owner_input_only_does_not_fail(tmp_path):
    seed_workspace(tmp_path)

    result = qa.run_qa(tmp_path)
    report = qa.write_qa_report(tmp_path, result)
    text = report.read_text(encoding="utf-8")

    assert result.ok
    assert result.error_count == 0
    assert result.owner_input_count >= 1
    assert "严重问题 exit code = 1" in text
    assert "只有 owner input 缺失" in text
    assert "backup exists before live" in text
    assert "rollback plan exists before live" in text


def test_qa_fake_ranking_promise_fails(tmp_path):
    seed_workspace(tmp_path, fake_claim=True)

    result = qa.run_qa(tmp_path)

    assert not result.ok
    assert result.error_count >= 1
    assert any(issue.check == "no fake ranking promise" for issue in result.issues)


def test_qa_matches_absolute_target_url_to_relative_inventory_path(tmp_path):
    seed_workspace(tmp_path)
    inventory_path = tmp_path / "seo-workspace" / "data" / "url-inventory.csv"
    text = inventory_path.read_text(encoding="utf-8")
    text = text.replace("https://flashcast.com.my/zh/services/renovation", "/zh/services/renovation")
    text = text.replace("https://flashcast.com.my/en/services/renovation", "/en/services/renovation")
    inventory_path.write_text(text, encoding="utf-8")

    result = qa.run_qa(tmp_path, target_url="https://flashcast.com.my/en/services/renovation")

    assert result.ok
    assert not any(issue.check == "target page exists" for issue in result.issues)
    assert not any(issue.check == "/zh and /en pair considered" for issue in result.issues)


def test_qa_live_requires_backup_and_rollback(tmp_path):
    seed_workspace(tmp_path)

    result = qa.run_qa(tmp_path, mode="live")

    assert not result.ok
    assert any(issue.check == "backup exists before live" for issue in result.issues)
    assert any(issue.check == "rollback plan exists before live" for issue in result.issues)
