from pathlib import Path

import pytest

from tests.agents.skills.renovation_seo_geo_import import load_permissions


permissions = load_permissions()


def context(mode, tmp_path, **kwargs):
    return permissions.PermissionContext(
        mode=permissions.parse_mode(mode),
        root=tmp_path,
        **kwargs,
    )


def test_audit_mode_blocks_writes(tmp_path):
    with pytest.raises(permissions.SeoGeoPermissionError):
        permissions.validate_write_path("seo-workspace/reports/a.md", context("audit", tmp_path))


def test_draft_mode_allows_only_drafts_and_reports(tmp_path):
    permissions.validate_write_path("seo-workspace/drafts/a.md", context("draft", tmp_path))
    permissions.validate_write_path("seo-workspace/reports/a.md", context("draft", tmp_path))
    with pytest.raises(permissions.SeoGeoPermissionError):
        permissions.validate_write_path("src/page.tsx", context("draft", tmp_path))


def test_pr_mode_allows_repo_file_writes(tmp_path):
    permissions.validate_write_path("src/page.tsx", context("pr", tmp_path))


def test_paths_outside_root_are_blocked(tmp_path):
    outside = Path("/tmp/outside-seo-geo-test.txt")
    with pytest.raises(permissions.SeoGeoPermissionError):
        permissions.validate_write_path(outside, context("pr", tmp_path))
