import csv
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_technical_findings


technical_findings = load_technical_findings()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_technical_findings_flags_publish_blockers_and_warnings(tmp_path):
    inventory_path = tmp_path / "seo-workspace" / "data" / "url-inventory.csv"
    write(
        inventory_path,
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        "https://example.com/en/services/kitchen,en,service,200,no,no,noindex,https://example.com/en/services/other,no,no,,Kitchen meta,,120,0,1,,2,1,,no,\n",
    )

    summary, artifacts = technical_findings.run_technical_findings_report(tmp_path)

    assert summary["publish_blocker_count"] >= 4
    assert (tmp_path / "seo-workspace" / "data" / "technical-audit-findings.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "technical-audit-findings.json").exists()
    assert len(artifacts) == 3
    with (tmp_path / "seo-workspace" / "data" / "technical-audit-findings.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    categories = {row["category"] for row in rows}
    assert {"crawlability", "indexability", "canonical", "on_page", "image_seo"} <= categories


def test_technical_findings_handles_missing_inventory(tmp_path):
    summary, _artifacts = technical_findings.run_technical_findings_report(tmp_path)

    assert summary["finding_count"] == 1
    assert summary["publish_blocker_count"] == 0
