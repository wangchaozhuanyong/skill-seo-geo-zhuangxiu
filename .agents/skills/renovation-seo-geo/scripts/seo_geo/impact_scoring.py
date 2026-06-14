"""Impact and effort scoring for SEO/GEO opportunity rows."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from .scoring import OpportunityScore
except ImportError:  # pragma: no cover
    from scoring import OpportunityScore


TECHNICAL_BLOCKER_LABELS = {
    "not indexable",
    "blocked by robots",
    "noindex",
    "canonical to wrong URL",
}
GSC_LABELS = {
    "existing ranking position 2-3",
    "existing ranking position 4-10",
    "existing ranking position 11-20",
    "high impressions low CTR",
    "indexed but low CTR",
    "not indexed but high business value",
}
LOW_EFFORT_LABELS = {
    "missing FAQ",
    "missing schema",
    "weak CTA",
    "weak internal links",
    "high impressions low CTR",
    "indexed but low CTR",
}
HIGH_EFFORT_LABELS = {
    "not indexable",
    "blocked by robots",
    "canonical to wrong URL",
    "missing /zh or /en pair",
    "duplicate city-swap risk",
}


@dataclass(frozen=True)
class ImpactScore:
    seo_impact: int
    business_impact: int
    fix_effort: int
    impact_priority_score: float
    impact_priority_band: str
    quick_win: bool


def _event_labels(score: OpportunityScore) -> set[str]:
    return {event.label for event in score.events}


def _clamp(value: int, minimum: int = 1, maximum: int = 10) -> int:
    return max(minimum, min(maximum, value))


def calculate_impact_score(score: OpportunityScore) -> ImpactScore:
    labels = _event_labels(score)

    seo_impact = 3
    if labels & TECHNICAL_BLOCKER_LABELS:
        seo_impact += 4
    if labels & GSC_LABELS:
        seo_impact += 3
    if "missing schema" in labels or "missing FAQ" in labels:
        seo_impact += 1
    if "weak internal links" in labels:
        seo_impact += 1
    if "missing /zh or /en pair" in labels:
        seo_impact += 2

    business_impact = 2
    if "commercial intent" in labels:
        business_impact += 2
    if "local commercial intent" in labels:
        business_impact += 2
    if "service page" in labels:
        business_impact += 2
    if "location page" in labels:
        business_impact += 2
    if labels & GSC_LABELS:
        business_impact += 1
    if "unsupported location" in labels:
        business_impact -= 3

    fix_effort = 3
    if labels & LOW_EFFORT_LABELS:
        fix_effort -= 1
    if labels & HIGH_EFFORT_LABELS:
        fix_effort += 3
    if "no case proof" in labels:
        fix_effort += 1
    if "unsupported location" in labels:
        fix_effort += 3

    seo_impact = _clamp(seo_impact)
    business_impact = _clamp(business_impact)
    fix_effort = _clamp(fix_effort)
    weighted = round((seo_impact * 0.4) + (business_impact * 0.4) + ((10 - fix_effort) * 0.2), 1)
    if weighted >= 7.5:
        band = "high"
    elif weighted >= 5.5:
        band = "medium"
    else:
        band = "low"
    quick_win = weighted >= 6.5 and fix_effort <= 4 and not labels & TECHNICAL_BLOCKER_LABELS
    return ImpactScore(
        seo_impact=seo_impact,
        business_impact=business_impact,
        fix_effort=fix_effort,
        impact_priority_score=weighted,
        impact_priority_band=band,
        quick_win=quick_win,
    )


def impact_to_row(score: OpportunityScore) -> dict[str, str]:
    impact = calculate_impact_score(score)
    return {
        "seo_impact": str(impact.seo_impact),
        "business_impact": str(impact.business_impact),
        "fix_effort": str(impact.fix_effort),
        "impact_priority_score": f"{impact.impact_priority_score:.1f}",
        "impact_priority_band": impact.impact_priority_band,
        "quick_win": "yes" if impact.quick_win else "no",
    }
