import csv
from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_google_indexation


google = load_google_indexation()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_google_indexation_report_without_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GSC_OAUTH_CLIENT_CONFIG", raising=False)
    monkeypatch.delenv("GSC_OAUTH_TOKEN_JSON", raising=False)
    monkeypatch.delenv("GSC_SITE_URL", raising=False)
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,sitemap_included,schema_types\n"
        "https://example.com/en/services/kitchen,en,service,200,yes,yes,yes,yes,WebPage\n",
    )

    rows = google.run_google_indexation_report(root=tmp_path, site_url="https://example.com/", use_api=False)

    assert len(rows) == 1
    assert rows[0]["action"] == "needs_gsc_credentials"
    assert (tmp_path / "seo-workspace" / "data" / "gsc-queries.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "gsc-pages.csv").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-google-indexation-report.md").exists()

    with (tmp_path / "seo-workspace" / "data" / "google-index-status.csv").open(newline="", encoding="utf-8") as handle:
        saved = list(csv.DictReader(handle))
    assert saved[0]["inspection_state"] == "not_checked"


def test_preflight_failure_blocks_gsc_inspection(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,sitemap_included,schema_types\n"
        "https://example.com/en/services/kitchen,en,service,404,no,yes,no,no,WebPage\n",
    )

    rows = google.run_google_indexation_report(root=tmp_path, site_url="https://example.com/", use_api=False)

    assert rows[0]["action"] == "fix_preflight_before_gsc_inspection"
