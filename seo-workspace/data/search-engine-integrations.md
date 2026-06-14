# Search Engine And Analytics Integration Status

Updated: 2026-06-14

## Google Search Console

- Property observed: `sc-domain:flashcast.com.my`
- Access status: owner Chrome session can view the property.
- Sitemap status: `https://flashcast.com.my/sitemap.xml` was successfully submitted in Google Search Console on 2026-06-12.
- Latest visible sitemap row after submission:
  - Submitted: 2026-06-12
  - Last read: 2026-06-11
  - Status: success
  - Discovered pages: 372
  - Discovered videos: 0
- Local sitemap/indexation prep status: production sitemap returns HTTP 200 and local Google index-status generation covered 458 changed/sitemap URLs on 2026-06-12.
- 2026-06-14 local API status: no reusable GSC API credentials are configured in this repository or current shell, so local URL Inspection / sitemap API calls remain `needs_gsc_credentials`.
- 2026-06-14 local preflight refresh: 458 sitemap URLs are HTTP 200, indexable, robots allowed, canonical self, and sitemap included; technical preflight blockers are 0.
- Latest visible snapshot captured locally:
  - `seo-workspace/data/gsc-pages.csv`
  - `seo-workspace/data/gsc-queries.csv`
- Notes: GSC discovered URL counts update asynchronously after Google reprocesses the sitemap. OAuth/API sync is still not configured in this repository. Do not store credentials in the repo.

## Google Analytics 4

- Measurement ID: `G-K71PQ0MSV2`
- Website status: installed in production HTML on `https://flashcast.com.my/` on 2026-06-12.
- Source implementation: website repo defaults GA4 tracking to this public measurement ID unless overridden by `VITE_GA_MEASUREMENT_ID`.
- Data status: GA Realtime showed 1 active user from Malaysia after production verification on 2026-06-12.
- Notes: First regular reports may still take time to populate after initial realtime collection.

## Bing Webmaster Tools

- Site: `https://flashcast.com.my/`
- Verification method: HTML meta tag.
- Verification status: successful in owner Chrome session on 2026-06-12.
- Website status: Bing verification meta is present in production HTML.

## Local Profiles

- Google Business Profile: verified in owner Chrome session on 2026-06-12.
- Bing Places: imported from Google Business Profile and verified in owner Chrome session on 2026-06-12. Sync completed successfully. Current status is pending publication, with Bing UI showing an estimated 7-12 days before publication.
- Apple Business Connect / Apple Maps: out of scope by owner decision on 2026-06-12. No profile was claimed or modified; do not continue unless the owner explicitly reopens it.

## IndexNow

- Key file status: public IndexNow key file is hosted on `https://flashcast.com.my/`.
- Submit status: 30 core homepage, service, and location URLs were submitted on 2026-06-12.
- Endpoint result: `202 accepted`; this is not an indexing guarantee.
- 2026-06-14 key file recheck: existing public key file returned HTTP 200 and matched the local file.
- 2026-06-14 post-publish update notification: `/en/services/shop-renovation` and `/zh/services/shop-renovation` were submitted as updated URLs; endpoint returned `200 received`. This is not an indexing guarantee.
- Evidence:
  - `seo-workspace/data/indexnow-submit-log.csv`
  - `seo-workspace/reports/2026-06-12-indexnow-live-submit.md`
  - `seo-workspace/reports/2026-06-14-search-engine-credential-execution.md`

## Baidu

- Site: `https://flashcast.com.my/` is present in Baidu Search Resource Platform under the owner account.
- API submit status: 10 URLs accepted by Baidu normal inclusion API on 2026-06-12; daily remaining quota returned by Baidu was `0`.
- API parameter note: Baidu accepted `site=flashcast.com.my`; protocol-prefixed variants returned `site init fail`.
- Remaining ready URLs: 442 are technically ready but not submitted because the visible daily API quota was exhausted.
- 2026-06-14 local API status: no reusable Baidu API token is configured in this repository or current shell, so local API submission remains `needs_baidu_credentials`.
- 2026-06-14 blocked URL recheck: the 6 old HTTP `000` preflight blockers were rechecked and are no longer blockers; current technical preflight blockers are 0.
- Evidence:
  - `seo-workspace/data/baidu-index-status.csv`
  - `seo-workspace/data/baidu-submit-log.csv`
  - `seo-workspace/reports/2026-06-14-indexation-blocked-url-recheck.md`
  - `seo-workspace/reports/2026-06-14-search-engine-credential-execution.md`
