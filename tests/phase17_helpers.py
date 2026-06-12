from pathlib import Path
from typing import Optional
from datetime import date


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_qa_workspace(
    tmp_path: Path,
    *,
    target_overrides: Optional[dict[str, str]] = None,
    keyword_location: str = "Kuala Lumpur",
    draft_extra: str = "",
    draft_body: Optional[str] = None,
) -> None:
    target = {
        "indexable": "yes",
        "robots_allowed": "yes",
        "meta_robots": "",
        "canonical_self": "yes",
        "sitemap_included": "yes",
        "word_count": "300",
        "internal_outlinks_count": "2",
    }
    if target_overrides:
        target.update(target_overrides)
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        f"https://flashcast.com.my/zh/services/renovation,zh,service,200,{target['indexable']},{target['robots_allowed']},{target['meta_robots']},https://flashcast.com.my/zh/services/renovation,{target['canonical_self']},yes,住宅装修,住宅装修,住宅装修,{target['word_count']},2,{target['internal_outlinks_count']},WebPage,0,0,,{target['sitemap_included']},\n"
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
        f"住宅装修 吉隆坡,commercial,ready,/zh/services/renovation,/zh/services/renovation,service,high,住宅装修,{keyword_location},\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Residential renovation,/en/locations/kuala-lumpur,,,yes\n",
    )
    body = draft_body or (
        "中文页面建议文案\n概念设计\n英文页面建议文案\nrendering concept\n"
        "CTA: 获取免费报价\nInternal links: `/zh/quote` and `/en/quote`.\n"
    )
    today = date.today().isoformat()
    write(tmp_path / "seo-workspace" / "drafts" / f"{today}-test-content-brief.md", body + draft_extra)
    write(tmp_path / "seo-workspace" / "reports" / f"{today}-schema-report.md", "Errors: 0\nStatus: PASS\n")
