# Google Maps warehouse enrichment

This worker enriches only rows from
`warehouse.qualified_no_website_email_leads`. That view requires the warehouse
entity to be a no-website lead and to have at least one usable email.

## Run it

From `Google Maps Scraping`:

```powershell
python .\enrich_google_maps.py --limit 500 --workers 10
```

Each worker is assigned one configured proxy route. The command refuses to run
with fewer than two workers, with no proxy routes, or with more workers than
proxy routes. `GoogleMapsRpcClient` also refuses requests without a proxy, so
there is no direct-network fallback.

For a larger rollout, repeat the command with the desired batch size. New runs
skip every entity already present in `warehouse.google_maps_enrichment`:

```powershell
python .\enrich_google_maps.py --limit 50000 --workers 10
```

If a process is interrupted, resume its existing queue. Add `--retry-failed` to
also retry rows that exhausted their per-request attempts:

```powershell
python .\enrich_google_maps.py --resume-run <run-uuid> --workers 10 --retry-failed
```

## Search and matching

The query is exactly `{Business name} {Location}`. Location is normally city,
region, and postcode, with street/country used only when locality is absent.

Candidate identity is not based on exact names alone. The matcher combines:

- normalized and fuzzy business-name similarity, including legal suffixes and
  longer Maps display names;
- postcode, city, region, street number, and street-token agreement;
- distance from the warehouse coordinates;
- separation from the second-best confident candidate.

Results are `matched`, `ambiguous`, `not_found`, or `failed`. Only `matched`
rows receive a top-level Google Place ID, Maps URL, or website. Ambiguous and
rejected candidates remain in `candidate_snapshot` for auditing, preventing a
nearby false match from becoming an entity association.

## Review metadata

The anonymous Maps search payload reliably supplies discovery and profile
identity fields, but it does not reliably expose the true review count or newest
review. Anonymous place pages can also return Google's limited view. A nearby
counter in the existing generic parser is the photo count, so this worker never
uses it as a review count.

For verified review count and newest review date, configure a Google Maps
Platform key with the legacy Place Details service enabled:

```powershell
$env:GOOGLE_MAPS_API_KEY = '<key>'
python .\enrich_google_maps.py --limit 500 --workers 10
```

To backfill a completed run that was initially searched without a key:

```powershell
python .\enrich_google_maps.py --resume-run <run-uuid> --workers 10 --backfill-reviews
```

The Place Details request is sent through the same assigned proxy and asks for
`reviews_sort=newest`. Without a key, `review_count` and `latest_review_at` stay
NULL and `review_metadata_source` is `unavailable_no_api_key`; no estimate is
stored.

Review content and Places data have Google attribution, display, and storage
rules. Confirm the intended use against current Google Maps Platform terms
before enabling the official provider for a production-scale persistent store.

## Tables

- `warehouse.google_maps_enrichment_runs` stores run configuration and summary.
- `warehouse.google_maps_enrichment` is the resumable per-entity queue and
  latest enrichment result.

Schema setup is idempotent and lives in
`Lead Warehouse/postgres/003_google_maps_enrichment.sql`.
