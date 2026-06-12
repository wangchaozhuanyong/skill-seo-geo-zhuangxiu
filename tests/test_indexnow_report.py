from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_indexnow


indexnow = load_indexnow()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ready_row(**overrides):
    row = {
        "url": "https://example.com/en/services/kitchen",
        "language": "en",
        "page_type": "service",
        "status_code": "200",
        "indexable": "yes",
        "robots_allowed": "yes",
        "canonical_self": "yes",
        "sitemap_included": "yes",
    }
    row.update(overrides)
    return row


def test_indexnow_preflight_ready_requires_all_technical_checks():
    assert indexnow.is_preflight_ready(ready_row())
    assert not indexnow.is_preflight_ready(ready_row(status_code="404"))
    assert not indexnow.is_preflight_ready(ready_row(indexable="no"))
    assert not indexnow.is_preflight_ready(ready_row(robots_allowed="no"))
    assert not indexnow.is_preflight_ready(ready_row(canonical_self="no"))
    assert not indexnow.is_preflight_ready(ready_row(sitemap_included="no"))


def test_indexnow_status_needs_key_when_ready():
    rows = indexnow.build_indexnow_status_rows(
        [ready_row()],
        config=indexnow.IndexNowConfig(),
        submit_log_rows=[],
    )

    assert rows[0]["indexnow_ready"] == "yes"
    assert rows[0]["indexnow_status"] == "needs-owner-input"
    assert rows[0]["action"] == "needs_indexnow_key"


def test_indexnow_status_blocks_repeated_received_url():
    rows = indexnow.build_indexnow_status_rows(
        [ready_row()],
        config=indexnow.IndexNowConfig(key="abcDEF123456", host="example.com"),
        submit_log_rows=[{"url": "https://example.com/en/services/kitchen", "status": "received"}],
    )

    assert rows[0]["indexnow_status"] == "already_received"
    assert rows[0]["action"] == "do_not_resubmit_without_change"


def test_indexnow_report_without_key_writes_outputs(tmp_path, monkeypatch):
    monkeypatch.delenv("INDEXNOW_KEY", raising=False)
    monkeypatch.delenv("INDEXNOW_HOST", raising=False)
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,sitemap_included\n"
        "https://example.com/en/services/kitchen,en,service,200,yes,yes,yes,yes\n",
    )

    rows = indexnow.run_indexnow_report(root=tmp_path, use_api=False)

    assert rows[0]["action"] == "needs_indexnow_key"
    assert (tmp_path / "seo-workspace" / "data" / "indexnow-submit-log.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "indexnow-status.csv").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-indexnow-report.md").exists()
