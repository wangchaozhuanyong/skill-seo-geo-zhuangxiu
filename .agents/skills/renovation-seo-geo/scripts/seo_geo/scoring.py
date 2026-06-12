"""SEO opportunity scoring rules for daily task prioritization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

try:
    from .hreflang import expected_pair_url
except ImportError:  # pragma: no cover
    from hreflang import expected_pair_url


HIGH_IMPRESSIONS_THRESHOLD = 100
LOW_CTR_THRESHOLD = 0.02


@dataclass
class ScoreEvent:
    label: str
    points: int
    note: str = ""


@dataclass
class OpportunityScore:
    url: str
    keyword: str = ""
    language: str = ""
    page_type: str = ""
    service: str = ""
    location: str = ""
    total_score: int = 0
    task_type: str = ""
    events: list[ScoreEvent] = field(default_factory=list)

    @property
    def positive_events(self) -> list[ScoreEvent]:
        return [event for event in self.events if event.points > 0]

    @property
    def penalty_events(self) -> list[ScoreEvent]:
        return [event for event in self.events if event.points < 0]

    def add(self, label: str, points: int, note: str = "") -> None:
        self.events.append(ScoreEvent(label=label, points=points, note=note))
        self.total_score += points


def normalize_url(value: str, base_url: str = "") -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return strip_url_fragment(value)
    if value.startswith("/") and base_url:
        return strip_url_fragment(urljoin(base_url.rstrip("/") + "/", value.lstrip("/")))
    return strip_url_fragment(value)


def strip_url_fragment(value: str) -> str:
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/") if parts.path != "/" else parts.path, parts.query, ""))


def parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def is_commercial_intent(search_intent: str) -> bool:
    return (search_intent or "").strip().lower() in {"commercial", "transactional"}


def is_local_commercial(keyword_row: dict[str, str], page_type: str) -> bool:
    if not is_commercial_intent(keyword_row.get("search_intent", "")):
        return False
    location = keyword_row.get("location", "").strip()
    keyword = keyword_row.get("keyword", "").lower()
    return bool(location) or page_type == "local" or any(term in keyword for term in ("kuala lumpur", "selangor", "吉隆坡", "雪兰莪"))


def is_service_page(page_type: str, url: str) -> bool:
    path = urlsplit(url).path
    return page_type == "service" or "/services/" in path


def is_location_page(page_type: str, url: str) -> bool:
    path = urlsplit(url).path
    return page_type == "local" or "/locations/" in path


def is_noindex(meta_robots: str) -> bool:
    return "noindex" in (meta_robots or "").lower()


def is_wrong_canonical(inventory_row: dict[str, str]) -> bool:
    value = inventory_row.get("canonical_self", "")
    return value == "no"


def has_faq_schema(schema_types: str) -> bool:
    return "FAQPage" in {item.strip() for item in (schema_types or "").split(";")}


def has_any_schema(schema_types: str) -> bool:
    return bool((schema_types or "").strip())


def weak_cta(inventory_row: dict[str, str]) -> bool:
    page_type = inventory_row.get("page_type", "")
    if page_type == "conversion":
        return False
    return parse_int(inventory_row.get("internal_outlinks_count", "")) < 2


def weak_internal_links(inventory_row: dict[str, str]) -> bool:
    inlinks = parse_int(inventory_row.get("internal_inlinks_count", ""))
    outlinks = parse_int(inventory_row.get("internal_outlinks_count", ""))
    return inlinks < 2 or outlinks < 2


def has_language_pair(url: str, inventory_urls: set[str]) -> bool:
    pair = expected_pair_url(url)
    return not pair or pair in inventory_urls


def indexed_by_google(index_row: dict[str, str]) -> bool:
    verdict = index_row.get("verdict", "").upper()
    coverage = index_row.get("coverage_state", "").lower()
    if verdict == "PASS":
        return True
    return "indexed" in coverage and "not indexed" not in coverage


def not_indexed_by_google(index_row: dict[str, str]) -> bool:
    if not index_row or index_row.get("inspection_state") != "checked":
        return False
    return not indexed_by_google(index_row)


def has_case_proof(url: str, internal_links: list[dict[str, str]], case_rows: list[dict[str, str]], service: str) -> bool:
    for row in internal_links:
        if normalize_url(row.get("source_url", ""), base_url="https://flashcast.com.my") == url and "/projects/" in row.get("target_url", ""):
            return True
    service_lower = (service or "").lower()
    if not service_lower:
        return False
    for row in case_rows:
        case_service = row.get("service", "").lower()
        if service_lower in case_service or case_service in service_lower:
            return True
    return False


def verified_location(location: str, service_areas: list[dict[str, str]]) -> bool:
    if not location:
        return True
    parts = [part.strip().lower() for part in location.replace(",", ";").split(";") if part.strip()]
    if not parts:
        return True
    verified_names = set()
    verified_countries = set()
    for row in service_areas:
        if row.get("verified", "").lower() == "yes":
            for field in ("area", "city", "state_or_region"):
                if row.get(field):
                    verified_names.add(row[field].lower())
            if row.get("country"):
                verified_countries.add(row["country"].lower())
    return all(part in verified_names or part in verified_countries for part in parts)


def duplicate_city_swap_risk(inventory_row: dict[str, str]) -> bool:
    if inventory_row.get("page_type") != "local":
        return False
    return parse_int(inventory_row.get("word_count", "")) < 80


def ranking_event(score: OpportunityScore, position: float) -> None:
    if 2 <= position <= 3:
        score.add("existing ranking position 2-3", 6, "Close-to-top keyword/page opportunity.")
    elif 4 <= position <= 10:
        score.add("existing ranking position 4-10", 5, "First-page improvement opportunity.")
    elif 11 <= position <= 20:
        score.add("existing ranking position 11-20", 4, "Second-page opportunity.")


def performance_events(score: OpportunityScore, performance_row: dict[str, str], index_row: dict[str, str]) -> None:
    impressions = parse_int(performance_row.get("impressions", ""))
    ctr = parse_float(performance_row.get("ctr", ""))
    position = parse_float(performance_row.get("position", ""))
    ranking_event(score, position)
    if impressions >= HIGH_IMPRESSIONS_THRESHOLD and ctr < LOW_CTR_THRESHOLD:
        score.add("high impressions low CTR", 4, "Rewrite title/meta and improve SERP intent match.")
    if indexed_by_google(index_row) and impressions > 0 and ctr < LOW_CTR_THRESHOLD:
        score.add("indexed but low CTR", 3, "Indexed page has low CTR.")


def infer_task_type(score: OpportunityScore) -> str:
    labels = {event.label for event in score.events}
    if labels & {"not indexable", "blocked by robots", "noindex", "canonical to wrong URL"}:
        return "technical SEO fix"
    if labels & {"existing ranking position 2-3", "existing ranking position 4-10", "existing ranking position 11-20", "high impressions low CTR", "indexed but low CTR"}:
        return "GSC CTR/ranking optimization"
    if is_service_page(score.page_type, score.url) or is_location_page(score.page_type, score.url):
        return "high-commercial-intent page optimization"
    if "missing FAQ" in labels or "missing schema" in labels:
        return "FAQ/schema/content enhancement"
    if "weak internal links" in labels:
        return "internal linking optimization"
    return "content refresh or page audit"


def score_candidate(
    *,
    url: str,
    keyword_row: Optional[dict[str, str]] = None,
    inventory_row: Optional[dict[str, str]] = None,
    performance_row: Optional[dict[str, str]] = None,
    google_index_row: Optional[dict[str, str]] = None,
    inventory_urls: Optional[set[str]] = None,
    internal_links: Optional[list[dict[str, str]]] = None,
    case_rows: Optional[list[dict[str, str]]] = None,
    service_areas: Optional[list[dict[str, str]]] = None,
) -> OpportunityScore:
    keyword_row = keyword_row or {}
    inventory_row = inventory_row or {}
    performance_row = performance_row or {}
    google_index_row = google_index_row or {}
    inventory_urls = inventory_urls or set()
    internal_links = internal_links or []
    case_rows = case_rows or []
    service_areas = service_areas or []

    page_type = inventory_row.get("page_type") or keyword_row.get("page_type", "")
    score = OpportunityScore(
        url=url,
        keyword=keyword_row.get("keyword", ""),
        language=inventory_row.get("language", ""),
        page_type=page_type,
        service=keyword_row.get("service", ""),
        location=keyword_row.get("location", ""),
    )

    if is_commercial_intent(keyword_row.get("search_intent", "")):
        score.add("commercial intent", 5, "Commercial/transactional query.")
    if is_local_commercial(keyword_row, page_type):
        score.add("local commercial intent", 5, "Commercial query with local intent.")
    if is_service_page(page_type, url):
        score.add("service page", 5, "Service page usually has high lead value.")
    if is_location_page(page_type, url):
        score.add("location page", 4, "Local page can capture area-specific demand.")

    performance_events(score, performance_row, google_index_row)

    if not_indexed_by_google(google_index_row) and score.total_score >= 8:
        score.add("not indexed but high business value", 3, "High-value URL appears not indexed in Google inspection.")
    if not has_faq_schema(inventory_row.get("schema_types", "")):
        score.add("missing FAQ", 1, "Add helpful FAQ and FAQPage schema if appropriate.")
    if not has_any_schema(inventory_row.get("schema_types", "")):
        score.add("missing schema", 1, "Add relevant structured data.")
    if weak_cta(inventory_row):
        score.add("weak CTA", 2, "Improve quote/contact path from the page.")
    if weak_internal_links(inventory_row):
        score.add("weak internal links", 2, "Add useful inbound/outbound internal links.")
    if is_service_page(page_type, url) and not has_case_proof(url, internal_links, case_rows, score.service):
        score.add("no case proof", -1, "Use real case link or clearly labeled design concept proof.")
    if not verified_location(score.location, service_areas):
        score.add("unsupported location", -10, "Location is not verified in service-areas.csv.")
    if duplicate_city_swap_risk(inventory_row):
        score.add("duplicate city-swap risk", -8, "Local page appears too thin; avoid doorway-page pattern.")
    if not has_language_pair(url, inventory_urls):
        score.add("missing /zh or /en pair", -3, "Bilingual pair is missing from URL inventory.")
    if inventory_row.get("indexable") == "no":
        score.add("not indexable", -10, "Page cannot be indexed until fixed.")
    if inventory_row.get("robots_allowed") == "no":
        score.add("blocked by robots", -10, "Robots.txt blocks crawling.")
    if is_noindex(inventory_row.get("meta_robots", "")):
        score.add("noindex", -10, "Meta robots noindex blocks indexing.")
    if is_wrong_canonical(inventory_row):
        score.add("canonical to wrong URL", -8, "Canonical does not point to itself.")

    score.task_type = infer_task_type(score)
    return score


def score_sort_key(score: OpportunityScore) -> tuple[int, int, int, str]:
    page_type_priority = {
        "service": 5,
        "local": 4,
        "service-hub": 3,
        "home": 2,
        "article": 1,
    }.get(score.page_type, 0)
    commercial_signal = int(any(event.label == "commercial intent" for event in score.events))
    return (score.total_score, page_type_priority, commercial_signal, score.url)
