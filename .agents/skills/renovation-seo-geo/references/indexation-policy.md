# Indexation Policy

Indexation work helps search engines discover and evaluate crawlable URLs. It is not a ranking or indexing guarantee.

Use indexation workflows for:

- sitemap and robots checks
- canonical and hreflang consistency
- Google Search Console URL Inspection and sitemap submission when credentials are configured
- Baidu normal inclusion API preflight and submission when owner-approved credentials are configured
- IndexNow added/updated/deleted URL notifications when key ownership is configured

Before any submit, URL-level preflight must pass:

- HTTP 200
- indexable
- robots allowed
- self-canonical
- sitemap included
- materially new, updated, or deleted as appropriate

Do not repeatedly submit unchanged URLs. Do not call Google Indexing API for ordinary renovation pages.

Reports must use accurate states such as `ready`, `checked`, `submitted`, `received`, `accepted`, `failed`, `not_checked`, or `needs_owner_input`. Never use `guaranteed indexed`, `guaranteed ranking`, or `guaranteed first page`.

