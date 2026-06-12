import csv
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_crawl, load_url_inventory


crawl = load_crawl()
url_inventory = load_url_inventory()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_run_inventory_audit_from_local_sitemap_and_html(tmp_path):
    page_url = "https://example.com/en/services/kitchen"
    pair_url = "https://example.com/zh/services/kitchen"
    write(
        tmp_path / "public" / "sitemap.xml",
        f"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>{page_url}</loc><lastmod>2026-06-07</lastmod></url>
        </urlset>
        """,
    )
    write(
        tmp_path / "en" / "services" / "kitchen" / "index.html",
        f"""
        <html>
          <head>
            <title>Kitchen Renovation Malaysia</title>
            <meta name="description" content="Kitchen renovation planning and cabinet design.">
            <link rel="canonical" href="{page_url}">
            <link rel="alternate" hreflang="zh" href="{pair_url}">
            <script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage"}}</script>
          </head>
          <body>
            <h1>Kitchen Renovation Malaysia</h1>
            <p>This page explains kitchen renovation planning, storage, materials, lighting, workflow, and quotation preparation for homeowners.</p>
            <a href="{pair_url}">Chinese kitchen page</a>
            <img src="/kitchen.jpg">
          </body>
        </html>
        """,
    )

    inventory_path = tmp_path / "seo-workspace" / "data" / "url-inventory.csv"
    report_path = tmp_path / "seo-workspace" / "reports" / "audit.md"
    rows = crawl.run_inventory_audit(
        root=tmp_path,
        base_url="https://example.com",
        output_inventory=inventory_path,
        output_report=report_path,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["url"] == page_url
    assert row["language"] == "en"
    assert row["page_type"] == "service"
    assert row["status_code"] == "200"
    assert row["indexable"] == "yes"
    assert row["canonical_self"] == "yes"
    assert row["hreflang_pair"] == "yes"
    assert row["schema_types"] == "FAQPage"
    assert row["missing_alt_count"] == "1"
    assert inventory_path.exists()
    assert "Technical SEO/GEO Audit" in report_path.read_text(encoding="utf-8")

    with inventory_path.open(newline="", encoding="utf-8") as handle:
        saved = list(csv.DictReader(handle))
    assert saved[0]["url"] == page_url


def test_url_inventory_collects_keyword_and_internal_link_urls(tmp_path):
    data_dir = tmp_path / "seo-workspace" / "data"
    write(
        data_dir / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen,commercial,ready,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen,Kuala Lumpur,\n",
    )
    write(
        data_dir / "internal-links.csv",
        "source_url,target_url,anchor_text,context,priority\n"
        "/en,/en/services/kitchen,kitchen renovation,Homepage,high\n",
    )

    candidates = []
    candidates.extend(url_inventory.collect_from_keyword_map(data_dir / "keyword-map.csv", "https://example.com"))
    candidates.extend(url_inventory.collect_from_internal_links(data_dir / "internal-links.csv", "https://example.com"))
    deduped = url_inventory.dedupe_candidates(candidates)

    assert [candidate.url for candidate in deduped] == [
        "https://example.com/en",
        "https://example.com/en/services/kitchen",
    ]
