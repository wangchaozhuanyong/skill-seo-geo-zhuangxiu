# Schema Policy

Supported schema recommendations:

- Organization
- LocalBusiness
- HomeAndConstructionBusiness
- Service
- Article
- FAQPage
- BreadcrumbList
- ImageObject
- VideoObject only when real visible video data exists
- Review only when real review data exists and is visible
- AggregateRating only when real aggregate rating exists and is visible

Hard rules:

- schema content must appear in visible page content
- no fake rating
- no fake review
- no fake price
- no fake opening hours
- no fake service area
- no Review schema without real review data
- no AggregateRating without real aggregate data
- no ImageObject claiming real project proof for concept images

