from pathlib import Path


def test_generated_artifact_ignore_policy_covers_runtime_outputs():
    text = Path(".gitignore").read_text(encoding="utf-8")

    required_patterns = {
        "seo-workspace/data/*.mjs",
        "seo-workspace/data/import-templates/",
        "seo-workspace/drafts/*.csv",
        "seo-workspace/reports/*.csv",
        "seo-workspace/reports/*.html",
        "seo-workspace/reports/*.json",
        "seo-workspace/reports/*.png",
        "seo-workspace/reports/browser-evidence/",
    }

    for pattern in sorted(required_patterns):
        assert pattern in text
