"""HTTP checks for SEO/GEO crawl and indexability audits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; SEO-GEO-Audit/1.0; +https://example.com/seo-geo)"
)


@dataclass
class HttpCheckResult:
    url: str
    status_code: Optional[int] = None
    final_url: str = ""
    content_type: str = ""
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status_code is not None and 200 <= self.status_code < 400


def decode_body(raw: bytes, content_type: str) -> str:
    charset = "utf-8"
    marker = "charset="
    lower = content_type.lower()
    if marker in lower:
        charset = lower.split(marker, 1)[1].split(";", 1)[0].strip() or charset
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def fetch_url(
    url: str,
    *,
    timeout: int = 15,
    user_agent: str = DEFAULT_USER_AGENT,
    read_body: bool = True,
    max_bytes: int = 2_000_000,
) -> HttpCheckResult:
    request = Request(url, headers={"User-Agent": user_agent})
    try:
        with urlopen(request, timeout=timeout) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            content_type = headers.get("content-type", "")
            raw = response.read(max_bytes) if read_body else b""
            return HttpCheckResult(
                url=url,
                status_code=response.getcode(),
                final_url=response.geturl(),
                content_type=content_type,
                body=decode_body(raw, content_type) if raw else "",
                headers=headers,
            )
    except HTTPError as exc:
        headers = {key.lower(): value for key, value in exc.headers.items()}
        content_type = headers.get("content-type", "")
        raw = exc.read(max_bytes) if read_body else b""
        return HttpCheckResult(
            url=url,
            status_code=exc.code,
            final_url=exc.geturl(),
            content_type=content_type,
            body=decode_body(raw, content_type) if raw else "",
            headers=headers,
            error=str(exc),
        )
    except (URLError, OSError, TimeoutError) as exc:
        return HttpCheckResult(url=url, final_url=url, error=str(exc))


def check_urls(urls: list[str], *, timeout: int = 15) -> list[HttpCheckResult]:
    return [fetch_url(url, timeout=timeout) for url in urls]


def status_issue(status_code: Optional[int]) -> str:
    if status_code is None:
        return "http_unchecked"
    if 200 <= status_code < 300:
        return ""
    if 300 <= status_code < 400:
        return "redirect"
    if status_code == 404:
        return "not_found"
    if status_code >= 500:
        return "server_error"
    return f"http_{status_code}"
