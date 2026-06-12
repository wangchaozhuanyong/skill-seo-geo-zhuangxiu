#!/usr/bin/env python3
"""Discover a read-only website publishing adapter contract."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


ADAPTER_JSON_NAME = "website-publish-adapter.json"
SCAN_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
HELPER_NAMES = [
    "saveAdminService",
    "saveAdminBlogPost",
    "saveAdminRecord",
    "uploadAdminMediaObject",
    "createAdminMediaAsset",
]
SEO_SCRIPT_FILES = [
    "scripts/generate-sitemap.mjs",
    "scripts/generate-seo-manifest.mjs",
    "scripts/generate-llms.mjs",
    "scripts/verify-seo-html.mjs",
    "scripts/release-check.mjs",
]


@dataclass
class WebsitePublishAdapterResult:
    status: str
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    adapter: dict[str, object] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def safe_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def iter_source_files(root: Path, *, limit: int = 1600) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    files: list[Path] = []
    ignored_dirs = {"node_modules", ".git", "dist", "build", ".next", "coverage", ".turbo"}
    for current_raw, dirs, names in os.walk(root):
        current = Path(current_raw)
        dirs[:] = [item for item in dirs if item not in ignored_dirs and not item.startswith(".cache")]
        for name in names:
            path = current / name
            if path.suffix in SCAN_EXTENSIONS:
                files.append(path)
                if len(files) >= limit:
                    return files
    return files


def line_number_for(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "package-lock.json").exists():
        return "npm"
    return "unknown"


def command_for(manager: str, script_name: str) -> str:
    if manager == "pnpm":
        return f"pnpm run {script_name}"
    if manager == "yarn":
        return f"yarn {script_name}"
    return f"npm run {script_name}"


def detect_scripts(package_json: dict[str, object], root: Path, manager: str) -> dict[str, object]:
    scripts = safe_dict(package_json.get("scripts"))
    commands: dict[str, object] = {
        "package_manager": manager,
        "available_scripts": sorted(scripts.keys()),
        "content_write_commands": [],
        "seo_generation_commands": [],
        "qa_commands": [],
        "backup_commands": [],
        "build_commands": [],
    }

    if "backup:supabase" in scripts:
        commands["backup_commands"].append(command_for(manager, "backup:supabase"))
    for name in ("typecheck", "lint", "test", "verify:seo-html", "verify:preview", "verify:deploy-cache", "release:check"):
        if name in scripts:
            commands["qa_commands"].append(command_for(manager, name))
    for name in ("generate:sitemap", "generate:llms"):
        if name in scripts:
            commands["seo_generation_commands"].append(command_for(manager, name))
    if (root / "scripts" / "generate-seo-manifest.mjs").exists():
        commands["seo_generation_commands"].append("node scripts/generate-seo-manifest.mjs")
    if "build" in scripts:
        commands["build_commands"].append(command_for(manager, "build"))
    for name in ("seed:second-stage", "seed:long-tail", "content:humanize-blog:write"):
        if name in scripts:
            commands["content_write_commands"].append(command_for(manager, name))
    return commands


def detect_env_keys(root: Path) -> list[str]:
    env_example = root / ".env.example"
    if not env_example.exists():
        return []
    keys: list[str] = []
    for line in env_example.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key and not key.startswith("#"):
            keys.append(key)
    return sorted(set(keys))


def discover_helpers(root: Path, files: list[Path] | None = None) -> list[dict[str, object]]:
    files = files if files is not None else iter_source_files(root)
    matches: list[dict[str, object]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        relative = path.relative_to(root).as_posix()
        for helper in HELPER_NAMES:
            for match in re.finditer(rf"\b{re.escape(helper)}\b", text):
                line = line_number_for(text, match.start())
                line_text = text.splitlines()[line - 1].strip()[:220]
                kind = "export" if re.search(rf"export\s+(async\s+)?function\s+{re.escape(helper)}\b", line_text) else "reference"
                matches.append(
                    {
                        "helper": helper,
                        "path": relative,
                        "line": line,
                        "kind": kind,
                        "snippet": line_text,
                    }
                )
    return matches[:120]


def discover_seo_assets(root: Path) -> list[dict[str, object]]:
    assets: list[dict[str, object]] = []
    for relative in SEO_SCRIPT_FILES:
        path = root / relative
        assets.append({"path": relative, "exists": path.exists(), "type": "script"})
    for relative in ("public/sitemap.xml", "public/llms.txt", "public/seo-manifest.json", "functions/seo-manifest.json"):
        path = root / relative
        assets.append({"path": relative, "exists": path.exists(), "type": "generated_asset"})
    return assets


def discover_docs(root: Path) -> list[dict[str, object]]:
    candidates = [
        "AGENTS.md",
        "docs/rules/seo-cms-publishing.md",
        "docs/DEVELOPMENT_RULES.md",
        "docs/supabase-deployment.md",
        "docs/launch-checklist.md",
    ]
    return [{"path": item, "exists": (root / item).exists()} for item in candidates]


def evaluate_adapter(root: Path, adapter: dict[str, object]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    if not root.exists() or not root.is_dir():
        blockers.append(f"Website root does not exist or is not a directory: {root}")
        return blockers, warnings
    if not (root / "package.json").exists():
        blockers.append("Website package.json is missing; cannot infer publish commands.")
    helpers = adapter.get("helpers", [])
    helper_names = {str(item.get("helper", "")) for item in helpers if isinstance(item, dict)}
    if "saveAdminService" not in helper_names and "saveAdminRecord" not in helper_names:
        blockers.append("No service/admin save helper was found in website source.")
    if "uploadAdminMediaObject" not in helper_names:
        warnings.append("No uploadAdminMediaObject reference found; media publishing adapter may be incomplete.")
    commands = safe_dict(adapter.get("commands"))
    if not commands.get("seo_generation_commands"):
        warnings.append("No SEO generation command was detected.")
    if not commands.get("qa_commands"):
        warnings.append("No QA command was detected.")
    if not commands.get("backup_commands"):
        warnings.append("No backup command was detected.")
    return blockers, warnings


def build_adapter(root: Path) -> dict[str, object]:
    package_json = read_json(root / "package.json")
    manager = package_manager(root)
    source_files = iter_source_files(root) if root.exists() else []
    helpers = discover_helpers(root, source_files) if root.exists() else []
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": "read_only_publish_adapter_discovery",
        "website_root": str(root),
        "package_manager": manager,
        "node_engine": safe_dict(package_json.get("engines")).get("node", ""),
        "scanned_file_count": len(source_files),
        "commands": detect_scripts(package_json, root, manager),
        "helpers": helpers,
        "helper_summary": {
            name: len([item for item in helpers if item.get("helper") == name])
            for name in HELPER_NAMES
        },
        "seo_assets": discover_seo_assets(root),
        "docs": discover_docs(root),
        "env_keys_from_example": detect_env_keys(root),
        "future_executor_contract": {
            "service_pages": "prefer saveAdminService for services table records",
            "generic_records": "use saveAdminRecord only when page type has no specialized helper",
            "media": "use uploadAdminMediaObject then createAdminMediaAsset after owner-approved upload execution",
            "seo_after_write": ["generate:sitemap", "node scripts/generate-seo-manifest.mjs", "generate:llms", "verify:seo-html"],
            "safety": "adapter discovery is read-only and must not execute npm, CMS, Supabase, uploads, publish, or deploy",
        },
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
    }


def render_report(result: WebsitePublishAdapterResult) -> str:
    adapter = result.adapter
    commands = safe_dict(adapter.get("commands"))
    helper_summary = safe_dict(adapter.get("helper_summary"))
    lines = [
        "# Website Publish Adapter Discovery",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Website root: `{adapter.get('website_root', '')}`",
        f"- Package manager: `{adapter.get('package_manager', 'unknown')}`",
        f"- Node engine: `{adapter.get('node_engine', '')}`",
        "- 执行状态: read-only discovery；未运行 npm、未调用 CMS、未改源码、未上传媒体、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天为未来真实发布执行器补齐网站适配层：只读识别当前网站的 admin helper、媒体 helper、SEO 生成脚本、QA 命令、备份命令和发布规则文档。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(["", "## Helper Summary", ""])
    lines.extend(f"- {name}: `{count}`" for name, count in helper_summary.items())
    lines.extend(["", "## Commands", ""])
    for label in ("backup_commands", "seo_generation_commands", "qa_commands", "build_commands", "content_write_commands"):
        values = commands.get(label, [])
        lines.append(f"- {label}: `{', '.join(values) if values else 'None'}`")
    lines.extend(["", "## SEO Assets", ""])
    for asset in adapter.get("seo_assets", []):
        if isinstance(asset, dict):
            lines.append(f"- `{asset.get('path')}`: `{asset.get('exists')}`")
    lines.extend(["", "## Safety Notes", ""])
    lines.extend(
        [
            "- 该 adapter 只是只读发现，不会执行任何网站命令。",
            "- 后续真实 executor 必须继续通过 owner approval、QA、backup、rollback 和 live confirmation 门禁。",
            "- 图文/效果图素材仍必须保持 design/rendering concept 标注，不得伪装成真实项目证明。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, result: WebsitePublishAdapterResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    adapter_path = data_dir / ADAPTER_JSON_NAME
    report_path = reports_dir / f"{today}-website-publish-adapter.md"
    result.artifacts.update({"adapter": str(adapter_path), "report": str(report_path)})
    write_text(
        adapter_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "adapter": result.adapter,
                "artifacts": result.artifacts,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return adapter_path, report_path


def run_website_publish_adapter(
    root: Path,
    *,
    website_root: str = "",
) -> tuple[WebsitePublishAdapterResult, tuple[Path, Path]]:
    root = root.resolve()
    website_path = resolve_path(root, website_root) if website_root else Path()
    adapter = build_adapter(website_path) if website_root else {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "action": "read_only_publish_adapter_discovery",
        "website_root": "",
        "package_manager": "unknown",
        "commands": {},
        "helpers": [],
        "helper_summary": {},
        "seo_assets": [],
        "docs": [],
        "env_keys_from_example": [],
        "future_executor_contract": {},
        "no_cms_write_executed": True,
        "no_source_page_write_executed": True,
        "no_media_upload_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "no_live_actions_executed": True,
    }
    blockers, warnings = evaluate_adapter(website_path, adapter) if website_root else (
        ["Website root is required for publish adapter discovery (--website-root)."],
        [],
    )
    status = "website_publish_adapter_ready" if not blockers else "blocked_before_website_publish_adapter"
    result = WebsitePublishAdapterResult(status=status, blockers=blockers, warnings=warnings, adapter=adapter)
    artifacts = write_outputs(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover a read-only website publishing adapter contract.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--website-root", default="", help="Website source root to scan read-only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_website_publish_adapter(Path(args.root), website_root=args.website_root)
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
