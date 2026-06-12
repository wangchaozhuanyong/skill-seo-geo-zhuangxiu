from __future__ import annotations

import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_service_pattern_brief,
    load_service_pattern_media_assets,
    load_service_pattern_publish_payload,
    load_service_pattern_rich_editor,
)
from tests.test_service_pattern_content_package_tool import write_patterns


service_pattern_brief = load_service_pattern_brief()
service_pattern_rich_editor = load_service_pattern_rich_editor()
service_pattern_publish_payload = load_service_pattern_publish_payload()
service_pattern_media_assets = load_service_pattern_media_assets()


TARGET_URL = "https://flashcast.com.my/en/services/builtin"


def test_service_pattern_formal_wrappers_build_review_chain(tmp_path: Path):
    write_patterns(tmp_path)

    brief_path = service_pattern_brief.run_service_pattern_brief(tmp_path, target_url=TARGET_URL, today="2026-06-11")
    editor_artifacts = service_pattern_rich_editor.run_service_pattern_rich_editor(tmp_path, target_url=TARGET_URL, today="2026-06-11")
    payload_artifacts = service_pattern_publish_payload.run_service_pattern_publish_payload(
        tmp_path,
        editor_payload_path=str(editor_artifacts["payload"]),
    )
    media_artifacts = service_pattern_media_assets.run_service_pattern_media_assets(
        tmp_path,
        cms_payload_path=str(payload_artifacts["cms_payload"]),
    )

    media_summary = json.loads(media_artifacts["summary"].read_text(encoding="utf-8"))

    assert brief_path.is_file()
    assert editor_artifacts["editor_html"].is_file()
    assert payload_artifacts["cms_payload"].is_file()
    assert media_artifacts["media_plan"].is_file()
    assert media_summary["status"] == "needs_media_generation_or_upload"
    assert media_summary["no_live_actions_executed"] is True
