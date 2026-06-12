from pathlib import Path
from datetime import date

from tests.agents.skills.renovation_seo_geo_import import load_hreflang_validator, load_language_pairs


language_pairs = load_language_pairs()
hreflang_validator = load_hreflang_validator()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,canonical_self,hreflang_pair,in_sitemap,schema_types,internal_inlinks_count,internal_outlinks_count,word_count\n"
        "https://flashcast.com.my/zh/services/renovation,zh,service,200,yes,yes,yes,yes,yes,WebPage,2,2,300\n"
        "https://flashcast.com.my/en/services/renovation,en,service,200,yes,yes,yes,yes,yes,WebPage,2,2,300\n"
        "https://flashcast.com.my/zh/services/kitchen,zh,service,200,yes,yes,no,no,no,WebPage,1,1,120\n",
    )
    write(
        tmp_path / "seo-workspace" / "drafts" / "2026-06-07-residential-renovation-content-brief.md",
        "# Brief\n\n中文页面建议文案\n住宅装修\n\n英文页面建议文案\nResidential renovation service planning.\n\nBilingual SEO Title\n\nBilingual Meta Description\n",
    )


def test_language_pairs_builds_pair_inventory(tmp_path):
    seed_workspace(tmp_path)

    output = language_pairs.write_language_pairs(tmp_path)
    rows = language_pairs.read_csv_rows(output)

    assert output.name == "language-pairs.csv"
    renovation = [row for row in rows if row["source_url"].endswith("/zh/services/renovation")][0]
    kitchen = [row for row in rows if row["source_url"].endswith("/zh/services/kitchen")][0]
    assert renovation["pair_exists"] == "yes"
    assert renovation["service_slug_pair_consistent"] == "yes"
    assert kitchen["pair_exists"] == "no"
    assert kitchen["source_canonical_self"] == "no"


def test_hreflang_validator_reports_required_multilingual_checks(tmp_path):
    seed_workspace(tmp_path)

    output = hreflang_validator.run_multilingual_report(tmp_path)
    text = output.read_text(encoding="utf-8")

    assert output.name == f"{date.today().isoformat()}-multilingual-seo-report.md"
    assert (tmp_path / "seo-workspace" / "data" / "language-pairs.csv").exists()
    required = [
        "/zh 和 /en URL pair",
        "hreflang self reference",
        "hreflang alternate reference",
        "canonical 不跨语言错误",
        "sitemap 是否包含双语 URL",
        "中文页面是否中文",
        "英文页面是否英文",
        "meta 是否双语匹配",
        "service slug pair 是否一致",
        "Missing paired language URL",
        "Source canonical is not self-referencing",
        "等待业主审核和明确执行指令",
    ]
    for item in required:
        assert item in text
