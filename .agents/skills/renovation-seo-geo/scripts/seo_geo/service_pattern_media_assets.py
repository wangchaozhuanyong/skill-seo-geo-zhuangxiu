"""Formal CLI wrapper for draft-only service-pattern media assets."""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - package import path differs between CLI and tests
    from .service_pattern_workspace_tools import load_service_pattern_tool
except ImportError:  # pragma: no cover
    from service_pattern_workspace_tools import load_service_pattern_tool


def run_service_pattern_media_assets(
    root: Path,
    *,
    cms_payload_path: str,
    public_base_url: str = "",
    output_prefix: str = "",
) -> dict[str, Path]:
    tool = load_service_pattern_tool(root.resolve(), "service_pattern_media_assets")
    return tool.run(root.resolve(), cms_payload_path, public_base_url, output_prefix)
