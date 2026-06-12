"""Configuration loading and validation for SEO/GEO tooling."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_MAIN_KEYS = [
    "site_url",
    "production_url",
    "staging_url",
    "zh_prefix",
    "en_prefix",
    "sitemap_url",
    "robots_url",
    "target_markets",
    "target_languages",
    "primary_services",
    "priority_service_areas",
    "competitors",
    "approval_mode",
]

REQUIRED_SEARCH_KEYS = [
    "gsc_site_url",
    "baidu_site",
    "indexnow_endpoint",
]

REQUIRED_CMS_KEYS = [
    "cms_mode",
    "admin_service_path",
    "allowed_live_paths",
    "disallowed_live_paths",
]


@dataclass
class ConfigValidation:
    values: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith(("\"", "'")) and value.endswith(("\"", "'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small YAML subset used by repo config examples."""
    if not path.exists():
        return {}
    raw_lines = [
        line for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    for index, raw_line in enumerate(raw_lines):
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            if isinstance(parent, list):
                parent.append(parse_scalar(line[2:]))
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value:
            if isinstance(parent, dict):
                parent[key] = parse_scalar(value)
            continue
        next_container: Any = []
        for future in raw_lines[index + 1:]:
            if not future.strip():
                continue
            future_indent = len(future) - len(future.lstrip(" "))
            if future_indent <= indent:
                break
            next_container = [] if future.strip().startswith("- ") else {}
            break
        if isinstance(parent, dict):
            parent[key] = next_container
        stack.append((indent, next_container))
    return root


def parse_env_example(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def flatten_search_config(search_config: dict[str, Any]) -> dict[str, Any]:
    google = search_config.get("google", {}) if isinstance(search_config.get("google"), dict) else {}
    baidu = search_config.get("baidu", {}) if isinstance(search_config.get("baidu"), dict) else {}
    indexnow = search_config.get("indexnow", {}) if isinstance(search_config.get("indexnow"), dict) else {}
    return {
        "gsc_site_url": google.get("gsc_site_url", ""),
        "baidu_site": baidu.get("baidu_site", ""),
        "indexnow_endpoint": indexnow.get("indexnow_endpoint", ""),
    }


def flatten_cms_config(main_config: dict[str, Any], cms_config: dict[str, Any]) -> dict[str, Any]:
    publishing = main_config.get("publishing", {}) if isinstance(main_config.get("publishing"), dict) else {}
    return {
        "cms_mode": cms_config.get("cms_mode", ""),
        "admin_service_path": cms_config.get("admin_service_path", ""),
        "allowed_live_paths": publishing.get("allowed_live_paths", []),
        "disallowed_live_paths": publishing.get("disallowed_live_paths", []),
    }


def contains_secret(value: Any) -> bool:
    if isinstance(value, dict):
        return any(contains_secret(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_secret(item) for item in value)
    text = str(value)
    if "NEEDS_OWNER_INPUT" in text:
        return False
    secret_patterns = [
        r"ya29\.",
        r"AIza[0-9A-Za-z_-]{20,}",
        r"[A-Za-z0-9_-]{32,}",
        r"-----BEGIN PRIVATE KEY-----",
    ]
    return any(re.search(pattern, text) for pattern in secret_patterns)


def is_missing_value(value: Any) -> bool:
    return value is None or value == "" or value == []


def validate_config(root: Path, config_path: str = "") -> ConfigValidation:
    root = root.resolve()
    main_path = Path(config_path) if config_path else root / "seo-workspace" / "config" / "seo-geo-config.example.yml"
    if not main_path.is_absolute():
        main_path = root / main_path
    search_path = root / "seo-workspace" / "config" / "search-engines.example.yml"
    cms_path = root / "seo-workspace" / "config" / "cms.example.yml"
    env_path = root / ".env.example"

    main_config = parse_simple_yaml(main_path)
    search_config = parse_simple_yaml(search_path)
    cms_config = parse_simple_yaml(cms_path)
    env_values = parse_env_example(env_path)
    values: dict[str, Any] = {}
    values.update(main_config)
    values.update(flatten_search_config(search_config))
    values.update(flatten_cms_config(main_config, cms_config))
    result = ConfigValidation(values=values)

    for key in REQUIRED_MAIN_KEYS + REQUIRED_SEARCH_KEYS + REQUIRED_CMS_KEYS:
        if key not in values or is_missing_value(values[key]):
            result.errors.append(f"Missing required config key: {key}")
    if values.get("zh_prefix") != "/zh":
        result.errors.append("zh_prefix must be /zh")
    if values.get("en_prefix") != "/en":
        result.errors.append("en_prefix must be /en")
    if values.get("approval_mode") not in {"draft_only", "owner_approval_required"}:
        result.warnings.append("approval_mode should normally be draft_only or owner_approval_required")
    for key, value in values.items():
        if contains_secret(value):
            result.errors.append(f"Potential real secret detected in config key: {key}")
    for key, value in env_values.items():
        if contains_secret(value):
            result.errors.append(f"Potential real secret detected in .env.example key: {key}")
    for env_key in ("GSC_SITE_URL", "BAIDU_SITE", "INDEXNOW_ENDPOINT", "INDEXNOW_HOST"):
        if env_key not in env_values:
            result.errors.append(f"Missing .env.example key: {env_key}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SEO/GEO configuration examples.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--config", default="", help="Optional main config path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_config(Path(args.root), config_path=args.config)
    print("PASS" if result.ok else "FAIL")
    for warning in result.warnings:
        print(f"warning: {warning}")
    for error in result.errors:
        print(f"error: {error}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
