"""Backup helpers for approved SEO/GEO write operations."""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path
from typing import List, Optional, Union


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_file_backup(
    paths: List[Union[str, Path]],
    *,
    root: Optional[Path] = None,
    backup_root: Optional[Path] = None,
) -> Path:
    """Copy files into a timestamped backup directory and write a manifest."""
    repo_root = (root or Path.cwd()).resolve()
    target_root = backup_root or repo_root / "seo-workspace" / "backups"
    backup_dir = target_root / timestamp()
    backup_dir.mkdir(parents=True, exist_ok=True)

    manifest: List[dict[str, Union[str, bool]]] = []
    for item in paths:
        source = (repo_root / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
        try:
            relative = source.relative_to(repo_root)
        except ValueError:
            relative = Path(source.name)
        record: dict[str, Union[str, bool]] = {
            "source": str(source),
            "relative_path": relative.as_posix(),
            "existed": source.exists(),
        }
        if source.is_file():
            destination = backup_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            record["backup_path"] = str(destination)
        manifest.append(record)

    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return backup_dir


def create_text_backup(
    name: str,
    content: str,
    *,
    root: Optional[Path] = None,
    backup_root: Optional[Path] = None,
) -> Path:
    repo_root = (root or Path.cwd()).resolve()
    target_root = backup_root or repo_root / "seo-workspace" / "backups"
    backup_dir = target_root / timestamp()
    backup_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(char if char.isalnum() or char in "._-" else "-" for char in name)
    output_path = backup_dir / safe_name
    output_path.write_text(content, encoding="utf-8")
    return output_path
