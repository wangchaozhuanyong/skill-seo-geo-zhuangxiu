"""Import helpers for skill scripts stored outside a Python package path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[3]
SEO_GEO_DIR = ROOT / ".agents" / "skills" / "renovation-seo-geo" / "scripts" / "seo_geo"


def load_module(name: str) -> ModuleType:
    path = SEO_GEO_DIR / f"{name}.py"
    if str(SEO_GEO_DIR) not in sys.path:
        sys.path.insert(0, str(SEO_GEO_DIR))
    spec = importlib.util.spec_from_file_location(f"seo_geo_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_nested_module(relative_path: str, module_name: str) -> ModuleType:
    path = SEO_GEO_DIR / relative_path
    if str(SEO_GEO_DIR) not in sys.path:
        sys.path.insert(0, str(SEO_GEO_DIR))
    spec = importlib.util.spec_from_file_location(f"seo_geo_{module_name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_permissions() -> ModuleType:
    return load_module("permissions")


def load_backups() -> ModuleType:
    return load_module("backups")


def load_automation_schedule() -> ModuleType:
    return load_module("automation_schedule")


def load_automation_install_plan() -> ModuleType:
    return load_module("automation_install_plan")


def load_automation_completion_audit() -> ModuleType:
    return load_module("automation_completion_audit")


def load_scheduled_publish_authorization() -> ModuleType:
    return load_module("scheduled_publish_authorization")


def load_scheduled_publish_runner() -> ModuleType:
    return load_module("scheduled_publish_runner")


def load_scheduled_publish_orchestrator() -> ModuleType:
    return load_module("scheduled_publish_orchestrator")


def load_scheduled_publish_postrun() -> ModuleType:
    return load_module("scheduled_publish_postrun")


def load_change_log() -> ModuleType:
    return load_module("change_log")


def load_crawl() -> ModuleType:
    return load_module("crawl")


def load_url_inventory() -> ModuleType:
    return load_module("url_inventory")


def load_robots_sitemap() -> ModuleType:
    return load_module("robots_sitemap")


def load_canonical() -> ModuleType:
    return load_module("canonical")


def load_hreflang() -> ModuleType:
    return load_module("hreflang")


def load_google_search_console() -> ModuleType:
    return load_nested_module("integrations/google_search_console.py", "google_search_console")


def load_google_indexation() -> ModuleType:
    return load_nested_module("indexation/google.py", "google_indexation")


def load_baidu_integration() -> ModuleType:
    return load_nested_module("integrations/baidu.py", "baidu_integration")


def load_baidu_indexation() -> ModuleType:
    return load_nested_module("indexation/baidu.py", "baidu_indexation")


def load_indexnow() -> ModuleType:
    return load_nested_module("indexation/indexnow.py", "indexnow")


def load_scoring() -> ModuleType:
    return load_module("scoring")


def load_opportunity_finder() -> ModuleType:
    return load_module("opportunity_finder")


def load_page_audit() -> ModuleType:
    return load_module("page_audit")


def load_content_brief() -> ModuleType:
    return load_module("content_brief")


def load_content_calendar() -> ModuleType:
    return load_module("content_calendar")


def load_content_studio() -> ModuleType:
    return load_module("content_studio")


def load_content_studio_decision_orchestrator() -> ModuleType:
    return load_module("content_studio_decision_orchestrator")


def load_content_studio_queue() -> ModuleType:
    return load_module("content_studio_queue")


def load_content_studio_next() -> ModuleType:
    return load_module("content_studio_next")


def load_content_studio_operator_ready_handoff() -> ModuleType:
    return load_module("content_studio_operator_ready_handoff")


def load_content_studio_orchestrator() -> ModuleType:
    return load_module("content_studio_orchestrator")


def load_content_studio_postrun() -> ModuleType:
    return load_module("content_studio_postrun")


def load_content_studio_publish_candidate() -> ModuleType:
    return load_module("content_studio_publish_candidate")


def load_content_studio_publish_prep() -> ModuleType:
    return load_module("content_studio_publish_prep")


def load_content_studio_approval_packet() -> ModuleType:
    return load_module("content_studio_approval_packet")


def load_content_studio_media_url_template() -> ModuleType:
    return load_module("content_studio_media_url_template")


def load_content_studio_media_ready_handoff() -> ModuleType:
    return load_module("content_studio_media_ready_handoff")


def load_content_studio_media_review_package() -> ModuleType:
    return load_module("content_studio_media_review_package")


def load_content_studio_media_status() -> ModuleType:
    return load_module("content_studio_media_status")


def load_content_studio_uploaded_url_map_draft() -> ModuleType:
    return load_module("content_studio_uploaded_url_map_draft")


def load_content_studio_owner_review_package() -> ModuleType:
    return load_module("content_studio_owner_review_package")


def load_content_studio_owner_decision_status() -> ModuleType:
    return load_module("content_studio_owner_decision_status")


def load_content_studio_owner_decision_editor() -> ModuleType:
    return load_module("content_studio_owner_decision_editor")


def load_content_studio_owner_decision_import() -> ModuleType:
    return load_module("content_studio_owner_decision_import")


def load_publish_approved_execution_input() -> ModuleType:
    return load_module("publish_approved_execution_input")


def load_publish_cms_write_executor() -> ModuleType:
    return load_module("publish_cms_write_executor")


def load_publish_media_upload_executor() -> ModuleType:
    return load_module("publish_media_upload_executor")


def load_publish_post_media_handoff() -> ModuleType:
    return load_module("publish_post_media_handoff")


def load_publish_operator_ready_handoff() -> ModuleType:
    return load_module("publish_operator_ready_handoff")


def load_content_refresh() -> ModuleType:
    return load_module("content_refresh")


def load_content_system() -> ModuleType:
    return load_module("content_system")


def load_daily_automation() -> ModuleType:
    return load_module("daily_automation")


def load_concept_assets() -> ModuleType:
    return load_module("concept_assets")


def load_entity_profile() -> ModuleType:
    return load_module("entity_profile")


def load_geo_ai() -> ModuleType:
    return load_module("geo_ai")


def load_growth_ops() -> ModuleType:
    return load_module("growth_ops")


def load_citations() -> ModuleType:
    return load_module("citations")


def load_local_seo() -> ModuleType:
    return load_module("local_seo")


def load_latest_research() -> ModuleType:
    return load_module("latest_research")


def load_schema_generator() -> ModuleType:
    return load_module("schema_generator")


def load_schema_validator() -> ModuleType:
    return load_module("schema_validator")


def load_language_pairs() -> ModuleType:
    return load_module("language_pairs")


def load_hreflang_validator() -> ModuleType:
    return load_module("hreflang_validator")


def load_visual_brief() -> ModuleType:
    return load_module("visual_brief")


def load_image_seo() -> ModuleType:
    return load_module("image_seo")


def load_qa() -> ModuleType:
    return load_module("qa")


def load_research_discovery() -> ModuleType:
    return load_module("research_discovery")


def load_research_search() -> ModuleType:
    return load_module("research_search")


def load_research_intake() -> ModuleType:
    return load_module("research_intake")


def load_rich_content() -> ModuleType:
    return load_module("rich_content")


def load_rich_blocks() -> ModuleType:
    return load_module("rich_blocks")


def load_rich_editor() -> ModuleType:
    return load_module("rich_editor")


def load_rich_editor_apply() -> ModuleType:
    return load_module("rich_editor_apply")


def load_media_assets() -> ModuleType:
    return load_module("media_assets")


def load_media_upload_plan() -> ModuleType:
    return load_module("media_upload_plan")


def load_media_upload_executor() -> ModuleType:
    return load_module("media_upload_executor")


def load_media_url_map() -> ModuleType:
    return load_module("media_url_map")


def load_content_studio_uploaded_url_map_editor() -> ModuleType:
    return load_module("content_studio_uploaded_url_map_editor")


def load_content_studio_uploaded_url_map_import() -> ModuleType:
    return load_module("content_studio_uploaded_url_map_import")


def load_publish_bundle() -> ModuleType:
    return load_module("publish_bundle")


def load_publish_approved_executor() -> ModuleType:
    return load_module("publish_approved_executor")


def load_publish_implementation_package() -> ModuleType:
    return load_module("publish_implementation_package")


def load_publish_operator_package() -> ModuleType:
    return load_module("publish_operator_package")


def load_publish_execution_receipt() -> ModuleType:
    return load_module("publish_execution_receipt")


def load_service_pattern_content_package() -> ModuleType:
    return load_module("service_pattern_content_package")


def load_service_pattern_brief() -> ModuleType:
    return load_module("service_pattern_brief")


def load_service_pattern_rich_editor() -> ModuleType:
    return load_module("service_pattern_rich_editor")


def load_service_pattern_publish_payload() -> ModuleType:
    return load_module("service_pattern_publish_payload")


def load_service_pattern_media_assets() -> ModuleType:
    return load_module("service_pattern_media_assets")


def load_website_publish_adapter() -> ModuleType:
    return load_module("website_publish_adapter")


def load_publish_queue() -> ModuleType:
    return load_module("publish_queue")


def load_publish_plan() -> ModuleType:
    return load_module("publish_plan")


def load_publish_executor() -> ModuleType:
    return load_module("publish_executor")


def load_publish_readiness() -> ModuleType:
    return load_module("publish_readiness")


def load_config() -> ModuleType:
    return load_module("config")


def load_cli() -> ModuleType:
    path = ROOT / ".agents" / "skills" / "renovation-seo-geo" / "scripts" / "seo_geo_cli.py"
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("seo_geo_cli", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
