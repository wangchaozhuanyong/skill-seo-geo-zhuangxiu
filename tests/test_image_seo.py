from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_image_seo, load_visual_brief


visual_brief = load_visual_brief()
image_seo = load_image_seo()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,sitemap_included\n"
        "https://flashcast.com.my/zh/services/renovation,zh,service,200,yes,yes,yes,yes,住宅装修,住宅装修,住宅装修,300,2,2,WebPage;ImageObject,0,0,yes\n"
        "https://flashcast.com.my/en/projects/sample,en,case-study,200,yes,yes,yes,yes,Sample,Sample,Sample,300,2,2,WebPage,2,1,yes\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "entity-profile.md",
        "概念设计\nrendering concept\n",
    )


def test_visual_brief_creates_labeled_concept_assets(tmp_path):
    seed_workspace(tmp_path)

    output = visual_brief.write_visual_briefs(tmp_path)
    rows = visual_brief.read_csv_rows(output)

    assert output.name == "visual-asset-briefs.csv"
    assert rows
    assert "概念设计" in rows[0]["concept_label_zh"]
    assert "rendering concept" in rows[0]["concept_label_en"]
    assert rows[0]["file_name_suggestion"].endswith(".webp")
    assert "Real project photo proof" in rows[0]["owner_input_required"]


def test_image_seo_report_includes_required_checks_and_boundaries(tmp_path):
    seed_workspace(tmp_path)

    output = image_seo.run_image_seo_report(tmp_path)
    text = output.read_text(encoding="utf-8")

    assert output.name == f"{date.today().isoformat()}-image-seo-report.md"
    assert (tmp_path / "seo-workspace" / "data" / "visual-asset-briefs.csv").exists()
    required = [
        "missing alt",
        "generic alt",
        "image size",
        "width/height",
        "lazy loading",
        "hero image",
        "service image",
        "case image",
        "concept/rendering label",
        "file names",
        "image sitemap readiness",
        "Missing alt count: 1",
        "概念设计",
        "rendering concept",
        "等待业主审核和明确执行指令",
    ]
    for item in required:
        assert item in text
