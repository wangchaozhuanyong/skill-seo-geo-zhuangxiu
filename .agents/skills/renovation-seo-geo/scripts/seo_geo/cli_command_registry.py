"""Command metadata for the unified SEO/GEO CLI.

The parser still lives in ``seo_geo_cli.py`` for compatibility. This registry is
the first guardrail for splitting parser construction into smaller modules:
every public command must have an owner, write behavior, and mode boundary.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable


SEO_SKILL = "renovation-seo-geo"
PPC_SKILL = "google-ads-renovation-ppc"


@dataclass(frozen=True)
class CliCommandMetadata:
    name: str
    group: str
    owner_skill: str
    writes_files: bool
    default_mode: str
    output_paths: tuple[str, ...]
    publish_gate: bool = False


def _records(
    names: Iterable[str],
    *,
    group: str,
    owner_skill: str = SEO_SKILL,
    writes_files: bool = True,
    default_mode: str = "draft",
    output_paths: tuple[str, ...] = ("seo-workspace/reports/", "seo-workspace/data/"),
    publish_gate: bool = False,
) -> tuple[CliCommandMetadata, ...]:
    return tuple(
        CliCommandMetadata(
            name=name,
            group=group,
            owner_skill=owner_skill,
            writes_files=writes_files,
            default_mode=default_mode,
            output_paths=output_paths,
            publish_gate=publish_gate,
        )
        for name in names
    )


_COMMANDS = (
    *_records(
        ["validate"],
        group="core",
        writes_files=True,
        default_mode="audit",
        output_paths=("seo-workspace/reports/",),
    ),
    *_records(
        ["config"],
        group="core",
        writes_files=False,
        default_mode="audit",
        output_paths=(),
    ),
    *_records(
        [
            "crawl",
            "technical-audit",
            "technical-findings",
            "ai-crawler-policy",
            "ai-crawler-draft",
            "entity",
            "geo-ai",
            "local-seo",
            "schema",
            "multilingual",
            "image-seo",
            "opportunities",
            "content-quality-review",
            "post-publish-feedback",
            "qa",
        ],
        group="seo_audit",
        default_mode="audit",
    ),
    *_records(
        [
            "gsc-sync",
            "google-index-status",
            "google-submit-sitemap",
            "baidu-submit",
            "indexnow-submit",
        ],
        group="indexation",
        default_mode="audit",
    ),
    *_records(
        [
            "daily-performance-digest",
            "growth-data-health",
            "growth-learning-memory",
            "growth-action-queue",
            "ai-search-monitor",
            "competitor-gap-audit",
            "competitor-weekly-monitor",
            "local-citation-tracker",
            "local-seo-verification",
            "real-proof-asset-request",
            "weekly-growth-control",
            "growth-ops-audit",
        ],
        group="growth",
        default_mode="audit",
    ),
    *_records(
        [
            "lead-quality-tracker",
            "lead-quality-editor",
            "ads-decision-review",
            "ads-asset-status-tracker",
        ],
        group="paid_growth",
        owner_skill=PPC_SKILL,
        default_mode="paid-ads-audit",
    ),
    *_records(
        [
            "content-calendar",
            "daily",
            "daily-automation",
            "content-system",
            "service-pattern-brief",
            "service-pattern-editor",
            "service-pattern-publish-payload",
            "service-pattern-media-assets",
            "service-pattern-package",
        ],
        group="content",
        default_mode="draft",
        output_paths=("seo-workspace/drafts/", "seo-workspace/reports/", "seo-workspace/data/"),
    ),
    *_records(
        [
            "automation-schedule",
            "automation-install-plan",
            "automation-completion-audit",
            "scheduled-publish-authorization",
            "scheduled-publish-runner",
            "scheduled-publish-orchestrator",
            "scheduled-publish-postrun",
        ],
        group="automation",
        default_mode="draft",
        publish_gate=True,
    ),
    *_records(
        [
            "content-studio",
            "content-studio-queue",
            "content-studio-next",
            "content-studio-orchestrator",
            "content-studio-postrun",
            "content-studio-publish-candidate",
            "content-studio-publish-prep",
            "content-studio-approval-packet",
            "content-studio-media-url-template",
            "content-studio-media-ready-handoff",
            "content-studio-uploaded-url-map-draft",
            "content-studio-uploaded-url-map-editor",
            "content-studio-uploaded-url-map-import",
            "content-studio-media-status",
            "content-studio-operator-ready-handoff",
            "content-studio-media-review-package",
            "content-studio-owner-decision-editor",
            "content-studio-owner-decision-import",
            "content-studio-owner-decision-status",
            "content-studio-decision-orchestrator",
            "content-studio-owner-review-package",
        ],
        group="content_studio",
        default_mode="draft",
        output_paths=("seo-workspace/drafts/", "seo-workspace/reports/", "seo-workspace/data/"),
        publish_gate=True,
    ),
    *_records(
        [
            "latest-research",
            "research-discovery",
            "research-search",
            "research-intake",
            "rich-content",
            "rich-blocks",
            "rich-editor",
            "rich-editor-apply",
            "media-assets",
            "concept-assets",
            "media-upload-plan",
            "media-upload-executor",
            "media-url-map",
        ],
        group="rich_content_media",
        default_mode="draft",
        output_paths=("seo-workspace/drafts/", "seo-workspace/reports/", "seo-workspace/data/", "seo-workspace/media/"),
    ),
    *_records(
        [
            "publish-queue",
            "website-publish-adapter",
            "publish-plan",
            "publish-executor",
            "publish-readiness",
            "publish-bundle",
            "publish-approved-executor",
            "publish-approved-execution-input",
            "publish-cms-write-executor",
            "publish-media-upload-executor",
            "publish-post-media-handoff",
            "publish-implementation-package",
            "publish-operator-package",
            "publish-operator-ready-handoff",
            "publish-execution-receipt",
            "apply",
        ],
        group="publishing",
        default_mode="dry-run",
        publish_gate=True,
    ),
)

COMMAND_REGISTRY: dict[str, CliCommandMetadata] = {item.name: item for item in _COMMANDS}


def parser_command_names(parser: argparse.ArgumentParser) -> set[str]:
    for action in parser._actions:
        if getattr(action, "dest", None) == "command" and hasattr(action, "choices"):
            return set(action.choices)
    return set()


def validate_parser_registry(parser: argparse.ArgumentParser) -> None:
    parser_names = parser_command_names(parser)
    registry_names = set(COMMAND_REGISTRY)
    missing = sorted(parser_names - registry_names)
    stale = sorted(registry_names - parser_names)
    if missing or stale:
        details = []
        if missing:
            details.append(f"missing registry metadata: {', '.join(missing)}")
        if stale:
            details.append(f"stale registry metadata: {', '.join(stale)}")
        raise RuntimeError("; ".join(details))
