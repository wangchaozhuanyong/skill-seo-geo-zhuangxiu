# IndexNow Policy

Owner-facing reports must stay in Simplified Chinese. Do not treat IndexNow as a guaranteed indexing or ranking tool.

Use IndexNow for:

- Notifying participating search engines when URLs are added, updated, or deleted.
- Verifying that the IndexNow key file is publicly accessible.
- Recording `received`, `accepted`, `failed`, or `needs-owner-input` submission states.

Do not write `indexed` based only on an IndexNow HTTP response. A 200 response only means the endpoint received the URL or URL set. A 202 response means accepted and key validation may still be pending.

Before any IndexNow API submit, each URL must be HTTP 200, indexable, robots allowed, self-canonical, included in sitemap, and materially added/updated/deleted. Do not repeatedly submit unchanged URLs.
