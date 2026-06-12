from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_config


config = load_config()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_config(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "config" / "seo-geo-config.example.yml",
        """site_url: "https://flashcast.com.my"
production_url: "https://flashcast.com.my"
staging_url: "NEEDS_OWNER_INPUT"
zh_prefix: "/zh"
en_prefix: "/en"
sitemap_url: "https://flashcast.com.my/sitemap.xml"
robots_url: "https://flashcast.com.my/robots.txt"
target_markets:
  - Malaysia
target_languages:
  - zh
  - en
primary_services:
  - Residential renovation
priority_service_areas:
  - Kuala Lumpur
competitors:
  - NEEDS_OWNER_INPUT
approval_mode: draft_only
publishing:
  allowed_live_paths:
    - seo-workspace/drafts
  disallowed_live_paths:
    - .env
""",
    )
    write(
        tmp_path / "seo-workspace" / "config" / "search-engines.example.yml",
        """google:
  gsc_site_url: "https://flashcast.com.my/"
baidu:
  baidu_site: "https://flashcast.com.my"
indexnow:
  indexnow_endpoint: "https://api.indexnow.org/indexnow"
""",
    )
    write(
        tmp_path / "seo-workspace" / "config" / "cms.example.yml",
        """cms_mode: admin_service
admin_service_path: "NEEDS_OWNER_INPUT"
""",
    )
    write(
        tmp_path / ".env.example",
        """GSC_SITE_URL=https://flashcast.com.my/
BAIDU_SITE=https://flashcast.com.my
INDEXNOW_ENDPOINT=https://api.indexnow.org/indexnow
INDEXNOW_HOST=flashcast.com.my
""",
    )


def test_config_validation_accepts_required_example_keys(tmp_path):
    seed_config(tmp_path)

    result = config.validate_config(tmp_path)

    assert result.ok
    assert result.values["site_url"] == "https://flashcast.com.my"
    assert result.values["gsc_site_url"] == "https://flashcast.com.my/"
    assert result.values["cms_mode"] == "admin_service"
    assert result.values["allowed_live_paths"] == ["seo-workspace/drafts"]


def test_config_validation_blocks_secret_like_values(tmp_path):
    seed_config(tmp_path)
    write(
        tmp_path / ".env.example",
        "GSC_SITE_URL=https://flashcast.com.my/\nBAIDU_SITE=https://flashcast.com.my\nINDEXNOW_ENDPOINT=https://api.indexnow.org/indexnow\nINDEXNOW_HOST=flashcast.com.my\nINDEXNOW_KEY=abcdefghijklmnopqrstuvwxyz1234567890SECRET\n",
    )

    result = config.validate_config(tmp_path)

    assert not result.ok
    assert any("Potential real secret" in error for error in result.errors)


def test_config_validation_does_not_treat_long_nested_policy_keys_as_secrets(tmp_path):
    seed_config(tmp_path)
    write(
        tmp_path / "seo-workspace" / "config" / "seo-geo-config.example.yml",
        """site_url: "https://flashcast.com.my"
production_url: "https://flashcast.com.my"
staging_url: "NEEDS_OWNER_INPUT"
zh_prefix: "/zh"
en_prefix: "/en"
sitemap_url: "https://flashcast.com.my/sitemap.xml"
robots_url: "https://flashcast.com.my/robots.txt"
target_markets:
  - Malaysia
target_languages:
  - zh
  - en
primary_services:
  - Residential renovation
priority_service_areas:
  - Kuala Lumpur
competitors:
  - NEEDS_OWNER_INPUT
approval_mode: draft_only
publishing:
  require_exact_authorization_profile: true
  require_concept_labels_for_generated_images: true
  require_source_log_for_latest_research: true
  allowed_live_paths:
    - seo-workspace/drafts
  disallowed_live_paths:
    - .env
""",
    )

    result = config.validate_config(tmp_path)

    assert result.ok
