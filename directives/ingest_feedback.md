# Directive: Ingest Social Feedback (Real World)

## Goal
Process incoming social media mentions from Apify Scrapers to identify feature requests or bug reports.

## Search Queries
The agent should periodically run `ingest_social.py` with the following queries:
- `"@MyBrand feature"`
- `"@MyBrand bug"`
- `"@MyBrand broken"`
- `"@MyBrand help"`

## Inputs
- **Social Content**: JSON dataset from Apify.
- **User Handle**: `@screen_name` from Apify.
- **Platform**: `twitter` or `facebook`.

## Steps

1.  **Run Ingestion**
    - `python3 execution/ingest_social.py --query "@MyBrand feature"`
    - **Output**: List of JSON objects.

2.  **Process Each Item**
    - For each item in output:
        - Check for Existing Tickets (`ticket_manager.py find_similar_ticket`).
        - Link or Create (`ticket_manager.py create_ticket`).

## Success Criteria
- Real tweets are captured and turned into tickets.
- Rate limits are respected (Scrapers usually handle this, but we poll every 1 hour).
