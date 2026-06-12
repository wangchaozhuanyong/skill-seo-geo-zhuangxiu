# Google Search Console Policy

Owner-facing reports must stay in Simplified Chinese. Do not store Google credentials, OAuth tokens, service-account JSON, or API secrets in the repository.

Use Google Search Console for:

- Search Analytics exports by query, page, country, device, and date.
- URL Inspection API checks for Google index status, Google-selected canonical, user canonical, crawl/indexing state, and coverage issues.
- Search Console Sitemaps API submission when explicitly requested and credentials are configured.

Do not use Google Indexing API for ordinary renovation service pages, blog posts, case studies, city pages, homepage, or conversion pages. The Indexing API is allowed only for pages with `JobPosting` structured data or `BroadcastEvent` embedded in `VideoObject` structured data.

Index and sitemap reporting language must avoid guarantees. Use wording such as "submitted", "checked", "ready for inspection", "not checked", or "needs credentials"; never write "guaranteed indexed", "guaranteed ranking", or "guaranteed first page".
