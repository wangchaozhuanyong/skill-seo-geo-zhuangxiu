"""Load draft-only service-pattern workspace tools for formal CLI wrappers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_service_pattern_tool(root: Path, module_name: str) -> ModuleType:
    """Load a service-pattern helper from the workspace tools directory."""
    path = root / "seo-workspace" / "tools" / f"{module_name}.py"
    if not path.exists():
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "seo-workspace" / "tools" / f"{module_name}.py"
            if candidate.exists():
                path = candidate
                break
    if not path.exists():
        raise RuntimeError(f"Missing service-pattern workspace tool: {module_name}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load service-pattern workspace tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
