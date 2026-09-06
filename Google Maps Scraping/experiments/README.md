# Direct Google Maps Payload Investigation

Captured and validated on 2026-08-31. These scripts are investigation harnesses;
the production implementation is in `rpc_client.py` and `scraper.py`.

## Finding

The current Google Maps HTML bootstrap publishes a same-origin link shaped like
`/search?tbm=map&...&pb=...`. Fetching that link in the same proxied HTTP session
returns a JSON payload containing the place records, so Chromium and its map,
image, font, telemetry, and vector-tile traffic are not required.

The former `/maps/rpc/search` request and hand-built `pb` template are stale: the
former returned HTTP 404, while the latter returned a small response with no place
records. Production code therefore discovers Google's current payload URL from
the bootstrap instead of trying to synthesize it.

## Proxy invariant

Every experimental and production Maps request requires a configured proxy.
`GoogleMapsRpcClient` raises before creating a request when no proxy URL is
provided, and it passes the proxy on every request. Browser and HTTP egress were
also checked from inside their respective sessions using an IP echo service.

## Results

- Ten concurrent queries on proxy ports 8001-8010: 10/10 succeeded, 200/200
  listings parsed, 2.07 seconds wall time in the latest burst.
- One San Francisco plumber viewport: direct returned 20 listings in 1.75 seconds;
  the asset-blocked browser returned 12 in 3.36 seconds. All 12 browser results
  were present in the direct response.
- Captured completed response bodies: about 0.38 MB for bootstrap plus direct
  payload versus 6.44 MB for the relevant browser traffic, roughly 16.9x less.
- Pagination was validated by modifying the live payload's offset: two pages
  produced 40 unique listings with only two listings overlapping between pages.

Latest compact evidence is saved in `direct_benchmark.json` and
`browser_direct_comparison.json`. Large raw captures are intentionally ignored by
Git under `experiments/artifacts/`.

A production observation of campaign #2 completed 296 Maps jobs and 629 email
jobs after restart, at roughly 130 and 275 jobs/min respectively. Six transient
bootstrap misses were automatically reclaimed and completed by the durable queue;
there were zero terminal job failures, HTTP 403/429 responses, or circuit-breaker
events during the observation window.

Email enrichment was already HTTP-only, so there were no browser assets to remove.
It now fails closed when no proxy route is available, treats total proxy failure as
a retryable error instead of `no_email`, and retains at most five relevance-ranked
addresses per lead to prevent broad directory pages from importing staff lists.

## Reproduce

From the project directory:

```powershell
python experiments\benchmark_direct_client.py
python experiments\compare_browser_direct.py
python -m unittest -v test_rpc_direct.py
```

The capture and payload probes accept `--help` for query, coordinate, zoom, and
proxy-route options:

```powershell
python experiments\capture_maps_network.py --help
python experiments\direct_payload_probe.py --help
```

## Operational caveat

`tbm=map` is an undocumented Google web implementation detail. It can change
without notice, so `--mode browser` remains available as a fallback. Google's
documented alternative is Places API Text Search (New), which requires an API
key, billing, and an explicit response field mask. No Maps Platform API key was
available in this environment, so that route was researched but not exercised.
