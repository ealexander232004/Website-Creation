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

Maps discovery and website reachability use separate queues. Maps workers write
the binary match and enqueue any listed website immediately; website workers
claim those rows with `FOR UPDATE SKIP LOCKED` and verify them concurrently.
Logical Maps searches are paced by one shared limiter per proxy instead of a
fixed delay in every worker. Example optimized configuration:

```powershell
python .\enrich_google_maps.py --limit 5000 --workers 75 --workers-per-proxy 8 `
  --website-workers 25 --website-workers-per-proxy 3 `
  --postgres-pool-size 25 --maps-rps-per-proxy 5
```

All network workers share the bounded Postgres pool. Connections are borrowed
only for queue claims and result updates, then returned before any HTTP call, so
100 network workers use no more than 25 database connections.

Website checks default to a 6-second timeout and two attempts. Only timeouts,
HTTP 429, and 5xx responses are retried; deterministic TLS, network, URL,
redirect, and ordinary 4xx failures are recorded immediately.

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

Candidate identity uses a high-recall, name-dominant policy:

- normalized and fuzzy business-name similarity contributes 85% of ranking;
- coarse postcode, city, region, and distance agreement contributes 15%;
- street-level, phone, email-domain, website, and semantic evidence are not
  match deciders;
- the highest-scoring candidate is `matched` at a composite score of 0.65 or
  higher and is otherwise `not_found`.

This is a deliberately recall-favoring binary policy. Near-exact names tolerate
broad location disagreement, coarse locality can rescue a somewhat changed
name, and a close second candidate does not create an ambiguous result.

Completed searches are `matched` or `not_found`; request failures are `failed`.
Only `matched` rows receive a top-level Google Place ID, Maps URL, or website.
Rejected candidates remain in `candidate_snapshot` for auditing. Every new
decision stores `match_score`, `match_policy_version`, and `match_threshold` so
the hard-line decision is reproducible. Historic rows may retain the retired
`ambiguous` status and are labeled `legacy_multiclass_v1`.

## Review metadata

When published, the structured Maps search entity supplies the review count at
`p[4][8]`. Google can omit that field in anonymous/limited sessions; the worker
stores NULL in that case rather than zero. `p[37][1]` is the photo count and is
deliberately ignored. For businesses with reviews, the worker calls Maps'
internal `qv9Egd` structured RPC and takes the timestamp from the first review
returned by the newest-first request. It reuses the search session and assigned
proxy; it does not parse a business page or its DOM. Anonymous sessions can also
return a valid but limited/empty qv9 response, which is recorded distinctly and
does not imply that the business has no reviews.

`review_metadata_source` distinguishes a confirmed zero count, a newest review,
a limited/empty RPC response, a missing timestamp/CID, and request errors. This
means an unavailable detail response never gets mistaken for a zero-review
business. A configured `GOOGLE_MAPS_API_KEY` is optional and is used only as a
legacy Place Details fallback when qv9 does not produce a newest-review date.

To backfill a completed run that is missing review metadata:

```powershell
python .\enrich_google_maps.py --resume-run <run-uuid> --workers 10 --backfill-reviews
```

Review content and Places data have Google attribution, display, and storage
rules. Confirm the intended use against current Google Maps Platform terms
before using the enrichment at production scale.

## Tables

- `warehouse.google_maps_enrichment_runs` stores run configuration and summary.
- `warehouse.google_maps_enrichment` is the resumable per-entity queue and
  latest enrichment result.

Schema setup is idempotent and lives in
`Lead Warehouse/postgres/003_google_maps_enrichment.sql`.
