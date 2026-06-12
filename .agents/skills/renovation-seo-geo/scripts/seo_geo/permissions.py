"""Execution-mode guardrails for SEO/GEO automation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union


class SeoGeoMode(str, Enum):
    AUDIT = "audit"
    DRAFT = "draft"
    PR = "pr"
    STAGING = "staging"
    LIVE = "live"


class SeoGeoPermissionError(RuntimeError):
    """Raised when a requested SEO/GEO action is not allowed in the mode."""


@dataclass
class PermissionContext:
    mode: SeoGeoMode
    root: Path = field(default_factory=Path.cwd)
    confirm_live: bool = False
    allow_live_env: bool = False
    qa_passed: bool = False
    backup_path: Optional[Path] = None
    changelog_path: Optional[Path] = None
    rollback_plan_path: Optional[Path] = None
    allowed_live_paths: tuple[str, ...] = ()
    disallowed_live_paths: tuple[str, ...] = (".env", ".env.local", ".env.production")

    @classmethod
    def from_env(
        cls,
        mode: Union[str, SeoGeoMode],
        *,
        confirm_live: bool = False,
        root: Optional[Path] = None,
        qa_passed: bool = False,
        backup_path: Optional[Union[str, Path]] = None,
        changelog_path: Optional[Union[str, Path]] = None,
        rollback_plan_path: Optional[Union[str, Path]] = None,
    ) -> "PermissionContext":
        return cls(
            mode=parse_mode(mode),
            root=(root or Path.cwd()).resolve(),
            confirm_live=confirm_live,
            allow_live_env=os.environ.get("SEO_GEO_ALLOW_LIVE") == "1",
            qa_passed=qa_passed,
            backup_path=Path(backup_path) if backup_path else None,
            changelog_path=Path(changelog_path) if changelog_path else None,
            rollback_plan_path=Path(rollback_plan_path) if rollback_plan_path else None,
        )


def parse_mode(value: Union[str, SeoGeoMode]) -> SeoGeoMode:
    if isinstance(value, SeoGeoMode):
        return value
    try:
        return SeoGeoMode(value)
    except ValueError as exc:
        valid = ", ".join(item.value for item in SeoGeoMode)
        raise SeoGeoPermissionError(f"Unknown SEO/GEO mode '{value}'. Expected one of: {valid}") from exc


def relative_to_root(path: Union[str, Path], root: Path) -> str:
    resolved = (root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise SeoGeoPermissionError(f"Path is outside repository root: {path}") from exc


def _matches_prefix(relative_path: str, prefixes: tuple[str, ...]) -> bool:
    return any(relative_path == prefix or relative_path.startswith(f"{prefix}/") for prefix in prefixes)


def is_draft_workspace_path(relative_path: str) -> bool:
    return _matches_prefix(relative_path, ("seo-workspace/drafts", "seo-workspace/reports"))


def validate_write_path(path: Union[str, Path], context: PermissionContext) -> None:
    relative_path = relative_to_root(path, context.root)

    if context.mode == SeoGeoMode.AUDIT:
        raise SeoGeoPermissionError("audit mode is read-only and cannot write files")

    if context.mode == SeoGeoMode.DRAFT and not is_draft_workspace_path(relative_path):
        raise SeoGeoPermissionError(
            "draft mode can only write under seo-workspace/drafts or seo-workspace/reports"
        )

    if context.mode == SeoGeoMode.LIVE:
        validate_live_preconditions(context)
        if _matches_prefix(relative_path, context.disallowed_live_paths):
            raise SeoGeoPermissionError(f"live mode cannot write disallowed path: {relative_path}")
        if context.allowed_live_paths and not _matches_prefix(relative_path, context.allowed_live_paths):
            raise SeoGeoPermissionError(f"live mode path is not in allowed_live_paths: {relative_path}")


def validate_live_preconditions(context: PermissionContext) -> None:
    if context.mode != SeoGeoMode.LIVE:
        return

    missing: list[str] = []
    if not context.allow_live_env:
        missing.append("SEO_GEO_ALLOW_LIVE=1")
    if not context.confirm_live:
        missing.append("--confirm-live")
    if not context.qa_passed:
        missing.append("qa passed")
    for label, path in (
        ("backup created", context.backup_path),
        ("changelog created", context.changelog_path),
        ("rollback plan created", context.rollback_plan_path),
    ):
        if not path or not path.exists():
            missing.append(label)

    if missing:
        raise SeoGeoPermissionError("live mode blocked; missing: " + ", ".join(missing))


def assert_can_write(path: Union[str, Path], context: PermissionContext) -> Path:
    validate_write_path(path, context)
    return (context.root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
