from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_baidu_indexation, load_baidu_integration


baidu_indexation = load_baidu_indexation()
baidu = load_baidu_integration()


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


def test_baidu_preflight_ready_requires_all_technical_checks():
    assert baidu_indexation.is_preflight_ready(ready_row())
    assert not baidu_indexation.is_preflight_ready(ready_row(status_code="301"))
    assert not baidu_indexation.is_preflight_ready(ready_row(indexable="no"))
    assert not baidu_indexation.is_preflight_ready(ready_row(robots_allowed="no"))
    assert not baidu_indexation.is_preflight_ready(ready_row(canonical_self="no"))
    assert not baidu_indexation.is_preflight_ready(ready_row(sitemap_included="no"))


def test_baidu_index_status_needs_credentials_when_ready():
    rows = baidu_indexation.build_baidu_index_status_rows(
        [ready_row()],
        config=baidu.BaiduConfig(),
        submit_log_rows=[],
    )

    assert rows[0]["baidu_submit_ready"] == "yes"
    assert rows[0]["baidu_submit_status"] == "needs-owner-input"
    assert rows[0]["action"] == "needs_baidu_credentials"


def test_baidu_index_status_blocks_repeated_submission():
    rows = baidu_indexation.build_baidu_index_status_rows(
        [ready_row()],
        config=baidu.BaiduConfig(site="https://example.com", push_token="token"),
        submit_log_rows=[{"url": "https://example.com/en/services/kitchen", "status": "accepted"}],
    )

    assert rows[0]["baidu_submit_status"] == "already_submitted"
    assert rows[0]["action"] == "do_not_resubmit_without_change"


def test_baidu_report_without_credentials_writes_outputs(tmp_path, monkeypatch):
    monkeypatch.delenv("BAIDU_SITE", raising=False)
    monkeypatch.delenv("BAIDU_PUSH_TOKEN", raising=False)
    monkeypatch.delenv("BAIDU_SUBMIT_ENDPOINT", raising=False)
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,sitemap_included\n"
        "https://example.com/en/services/kitchen,en,service,200,yes,yes,yes,yes\n",
    )

    rows = baidu_indexation.run_baidu_indexation_report(root=tmp_path, use_api=False)

    assert rows[0]["action"] == "needs_baidu_credentials"
    assert (tmp_path / "seo-workspace" / "data" / "baidu-submit-log.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "baidu-index-status.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "baidu-deadlinks.txt").exists()
    assert (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-baidu-indexation-report.md").exists()
