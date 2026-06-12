from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_system


content_system = load_content_system()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,sitemap_included\n"
        "https://flashcast.com.my/zh/services/renovation,zh,service,200,yes,yes,yes,yes,住宅装修,住宅装修,住宅装修,300,2,2,WebPage,0,0,yes\n"
        "https://flashcast.com.my/en/blog/kitchen-cabinet-price-malaysia,en,article,200,yes,yes,yes,yes,Kitchen Cabinet,Kitchen Cabinet,Kitchen Cabinet,600,2,2,Article,1,0,yes\n"
        "https://flashcast.com.my/en/projects/sample,en,case-study,200,yes,yes,yes,yes,Sample,Sample,Sample,400,2,2,WebPage,2,0,yes\n",
    )


def test_content_system_generates_map_and_report(tmp_path):
    seed_workspace(tmp_path)

    data_path, report_path = content_system.run_content_system(tmp_path)
    rows = content_system.read_csv_rows(data_path)
    report = report_path.read_text(encoding="utf-8")

    assert data_path.name == "content-publishing-system-map.csv"
    assert report_path.name == f"{date.today().isoformat()}-content-publishing-system-report.md"
    assert len(rows) == 3
    assert rows[0]["paired_url"] == "https://flashcast.com.my/en/services/renovation"
    assert rows[0]["content_priority"] == "high"
    assert "Service schema" in rows[0]["content_package"]
    assert "required before drafting" in rows[1]["latest_research_policy"]
    assert "not a substitute for project proof" in rows[2]["latest_research_policy"]
    assert "daily draft generation" in rows[0]["automation_cadence"]
    assert "publish-execution-receipt" in rows[0]["live_publish_gate"]
    assert "固定时间 publish-prep 只允许在精确授权 profile 存在、校验通过、本次 run request ready、safe orchestrator 放行且 postrun 复盘完成时执行下一步" in report
    assert "等待业主审核和明确执行指令" in report
