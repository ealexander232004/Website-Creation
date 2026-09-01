# Facebook last-post enrichment

This project enriches the existing PostgreSQL lead warehouse with the latest
post timestamp visible in an anonymous Facebook business-page document.

It is deliberately scoped to public account pages. It does **not** log in,
replay undocumented GraphQL requests, solve CAPTCHAs, spoof browser
fingerprints, or switch proxy routes after Facebook presents an access wall.

## How it works

1. Keyset-pages through `warehouse.entity_socials` and normalizes the Facebook
   IDs/URLs without loading the 800k+ source rows into memory.
2. Claims durable jobs with `FOR UPDATE SKIP LOCKED` and short transactions.
3. Launches Chromium with one explicit proxy route. Direct-network fallback is
   disabled.
4. Downloads only the top-level public document. Scripts, images, video,
   stylesheets, fonts, and other subresources are blocked.
5. Reads structured `creation_time`/`publish_time` values embedded in the
   document and persists the newest plausible timestamp as `timestamptz`.
6. Halts the run on login redirects, challenges, access denials, or rate limits
   rather than trying to bypass them.

Network failures and oversized/unparseable documents also halt the run after
persisting a bounded retry. Twenty consecutive `no_data` results trigger a
parser-drift circuit breaker by default (`--max-consecutive-no-data`).

This keeps parsing less brittle than visual DOM selectors while staying on the
public document surface. The document itself can still be large; test bandwidth
and route behavior before queueing a large campaign.

## Install

```powershell
cd "C:\Users\ezraa\Documents\Local Documents\Website Creation-facebook-last-post\Facebook Last Post"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

The existing workspace Python environment already contains the runtime
dependencies, so an editable install is enough for local testing.

## Database setup

Credentials can be loaded from the existing private scraper dotenv file. The
database defaults to `lead_warehouse`, even if that file's `POSTGRES_DB` points
at the older Google Maps database.

```powershell
facebook-last-post `
  --env-file "C:\Users\ezraa\Documents\Local Documents\Website Creation\Google Maps Scraping\.env" `
  migrate
```

The migration creates:

- `facebook_enrichment.profile_activity`: durable queue plus latest result per
  source Facebook account
- `facebook_enrichment.entity_last_post`: entity-level rollup across duplicate
  account references

Enqueue all source profiles:

```powershell
facebook-last-post `
  --env-file "C:\Users\ezraa\Documents\Local Documents\Website Creation\Google Maps Scraping\.env" `
  enqueue --batch-size 2000
```

For a bounded integration test, add `--limit 10`.

## Proxy verification and public-page probe

First verify all proxy routes against the provider's IP echo endpoint. This
prints route labels and public IPs, never credentials:

```powershell
& "C:\Users\ezraa\Documents\Local Documents\Website Creation\Proxies\verify-proxies.ps1"
```

Then test exactly one route against one public Facebook page:

```powershell
facebook-last-post probe `
  --proxy-file "C:\Users\ezraa\Documents\Local Documents\Website Creation\Proxies\proxy-urls.txt" `
  --proxy-index 1 `
  --url "https://www.facebook.com/Meta/"
```

The command never tries another route automatically. A `login_required`,
`challenge`, `access_denied`, or `rate_limited` result exits nonzero and contains
no scraped page body.

## Run queued jobs

Start with one bounded job and one worker:

```powershell
facebook-last-post `
  --env-file "C:\Users\ezraa\Documents\Local Documents\Website Creation\Google Maps Scraping\.env" `
  run `
  --proxy-file "C:\Users\ezraa\Documents\Local Documents\Website Creation\Proxies\proxy-urls.txt" `
  --proxy-index 1 `
  --workers 1 `
  --max-jobs 1 `
  --delay-seconds 5
```

`--workers` is capped at four. Every worker in one run uses the same selected
route; the runner never rotates on failure. Each worker holds one persistent
database connection, so `DATABASE_URL`/`FACEBOOK_DATABASE_URL` may point to a
transaction pooler for a remote deployment.

Inspect progress:

```powershell
facebook-last-post `
  --env-file "C:\Users\ezraa\Documents\Local Documents\Website Creation\Google Maps Scraping\.env" `
  stats
```

## Result states

| State | Meaning |
|---|---|
| `succeeded` | A supported public post timestamp was found |
| `no_data` | The public document loaded but had no supported timestamp |
| `unavailable` | Facebook reported the account/content unavailable |
| `blocked` | Login wall, challenge, access denial, or rate limit; run halted |
| `retry` | Transient network/parser failure with bounded backoff |
| `failed` | Transient failure exhausted `--max-attempts` |

Login walls are never recorded as `no_data`.

## Query the enrichment

```sql
select
    entity.entity_id,
    entity.canonical_name,
    activity.last_facebook_post_at,
    activity.last_facebook_checked_at
from warehouse.entities as entity
left join facebook_enrichment.entity_last_post as activity using (entity_id)
where entity.is_qualified_no_website_email_lead;
```

Keep database and proxy credentials out of source control, logs, screenshots,
and command history. Confirm that your collection and use of public page data is
authorized and consistent with applicable terms and law before a large run.
