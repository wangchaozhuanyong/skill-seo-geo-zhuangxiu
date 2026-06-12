import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_website_publish_adapter


website_publish_adapter = load_website_publish_adapter()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_website(root: Path) -> None:
    write(
        root / "package.json",
        json.dumps(
            {
                "name": "flashcast-website",
                "engines": {"node": ">=20 <23"},
                "scripts": {
                    "build": "vite build",
                    "typecheck": "tsc --noEmit",
                    "lint": "eslint .",
                    "test": "vitest run",
                    "verify:seo-html": "node scripts/verify-seo-html.mjs",
                    "verify:preview": "node scripts/verify-preview.mjs",
                    "backup:supabase": "node scripts/backup-supabase.mjs",
                    "generate:sitemap": "node scripts/generate-sitemap.mjs",
                    "generate:llms": "node scripts/generate-llms.mjs",
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
    )
    write(root / "package-lock.json", "{}\n")
    write(root / ".env.example", "VITE_SUPABASE_URL=\nVITE_SUPABASE_ANON_KEY=\n")
    write(
        root / "src" / "backend" / "modules" / "services" / "service" / "serviceService.ts",
        "export async function saveAdminService(input: SaveAdminServiceInput) { return input }\n",
    )
    write(
        root / "src" / "backend" / "modules" / "media" / "service" / "mediaService.ts",
        "export function uploadAdminMediaObject(bucket: string) { return bucket }\n"
        "export function createAdminMediaAsset(input: unknown) { return input }\n",
    )
    for script in ("generate-sitemap.mjs", "generate-seo-manifest.mjs", "generate-llms.mjs", "verify-seo-html.mjs"):
        write(root / "scripts" / script, "console.log('ok')\n")
    write(root / "public" / "sitemap.xml", "<urlset />\n")
    write(root / "docs" / "rules" / "seo-cms-publishing.md", "# Rules\n")


def test_website_publish_adapter_blocks_without_website_root(tmp_path):
    result, artifacts = website_publish_adapter.run_website_publish_adapter(tmp_path)

    assert not result.ok
    assert result.status == "blocked_before_website_publish_adapter"
    assert any("--website-root" in blocker for blocker in result.blockers)
    adapter_path, report_path = artifacts
    assert adapter_path.exists()
    assert report_path.exists()


def test_website_publish_adapter_discovers_commands_helpers_and_assets(tmp_path):
    website_root = tmp_path / "site"
    seed_website(website_root)

    result, artifacts = website_publish_adapter.run_website_publish_adapter(tmp_path, website_root=str(website_root))

    assert result.ok
    assert result.status == "website_publish_adapter_ready"
    assert result.adapter["package_manager"] == "npm"
    assert result.adapter["node_engine"] == ">=20 <23"
    assert result.adapter["scanned_file_count"] >= 2
    assert result.adapter["helper_summary"]["saveAdminService"] == 1
    assert result.adapter["helper_summary"]["uploadAdminMediaObject"] == 1
    assert "npm run verify:seo-html" in result.adapter["commands"]["qa_commands"]
    assert "node scripts/generate-seo-manifest.mjs" in result.adapter["commands"]["seo_generation_commands"]
    assert "VITE_SUPABASE_URL" in result.adapter["env_keys_from_example"]
    assert result.adapter["no_live_actions_executed"] is True
    adapter_path, report_path = artifacts
    payload = json.loads(adapter_path.read_text(encoding="utf-8"))
    assert payload["adapter"]["future_executor_contract"]["service_pages"] == "prefer saveAdminService for services table records"
    assert "read-only discovery" in report_path.read_text(encoding="utf-8")
