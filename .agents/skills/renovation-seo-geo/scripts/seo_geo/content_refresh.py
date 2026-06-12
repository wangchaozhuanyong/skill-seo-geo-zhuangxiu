"""Content refresh planning helpers."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from .page_audit import PageAudit
except ImportError:  # pragma: no cover
    from page_audit import PageAudit


@dataclass
class RefreshAction:
    section: str
    action: str
    reason: str


def refresh_actions_for_audit(audit: PageAudit) -> list[RefreshAction]:
    actions: list[RefreshAction] = []
    fields = {finding.field for finding in audit.findings}
    if "FAQ" in fields:
        actions.append(RefreshAction("FAQ", "Add bilingual FAQ and FAQPage schema.", "FAQ gap was detected."))
    if "CTA/internal links" in fields:
        actions.append(RefreshAction("CTA", "Strengthen quote/contact CTA and related service links.", "CTA path is weak."))
    if "internal inlinks" in fields:
        actions.append(RefreshAction("Internal links", "Add inbound links from service hub, homepage, articles, and project pages.", "Page needs stronger internal authority."))
    if "content depth" in fields:
        actions.append(RefreshAction("Body copy", "Add process, budget factors, material choices, and design-planning examples.", "Page depth is thin."))
    if not actions:
        actions.append(RefreshAction("Review", "Run manual content QA before publishing.", "No major content gap detected."))
    return actions


def refresh_actions_markdown(actions: list[RefreshAction]) -> str:
    lines = []
    for action in actions:
        lines.append(f"- {action.section}: {action.action} 原因: {action.reason}")
    return "\n".join(lines)
