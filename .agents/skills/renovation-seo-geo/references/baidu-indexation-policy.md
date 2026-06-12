# Baidu Indexation Policy

Owner-facing reports must stay in Simplified Chinese. Do not store Baidu tokens in the repository.

Use Baidu Search Resource Platform for:

- 普通收录 API 推送 after URL-level technical preflight.
- Sitemap URL recording and owner-side submission planning.
- Deadlink file generation for real 404/410 URLs.
- Owner-provided exports for 索引量, 流量与关键词, 抓取异常.

Baidu submission is discovery/indexation assistance, not a ranking or indexing guarantee. Reports must use `submitted`, `accepted`, `failed`, or `needs-owner-input`; never write `guaranteed indexed` or `guaranteed ranking`.

Before any Baidu API submit, each URL must be HTTP 200, indexable, robots allowed, self-canonical, included in sitemap, and not already submitted unless the page has materially changed.
