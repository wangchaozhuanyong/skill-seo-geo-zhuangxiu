"""Formal CLI wrapper for draft-only service-pattern rich editors."""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - package import path differs between CLI and tests
    from .service_pattern_workspace_tools import load_service_pattern_tool
except ImportError:  # pragma: no cover
    from service_pattern_workspace_tools import load_service_pattern_tool


def run_service_pattern_rich_editor(root: Path, *, target_url: str, today: str = "") -> dict[str, Path]:
    tool = load_service_pattern_tool(root.resolve(), "service_pattern_rich_editor")
    return tool.run(root.resolve(), target_url, today)
