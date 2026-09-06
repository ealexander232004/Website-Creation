# Continue Website Creation on Linux

This repository is the Keeplyn website business plus its lead acquisition and
qualification tooling. Use **GitHub main plus the entire private LocalSend
folder**. The private folder is named `Website-Creation-LocalSend-2026-09-06`.
It belongs outside the checkout and contains live credentials and business data.

## What the project does

| Area | Purpose and durable state |
| --- | --- |
| `Keeplyn.com` | Next.js 16 / React 19 marketing site, concept demos, customer request/upload flow, customer portal, admin review and revisions, domain selection, approved-demo checkout, hosting and lifecycle notifications. Supabase owns hosted Auth, Storage and database state; Stripe owns payments/subscriptions; Resend sends transactional email; Vercel serves the site. |
| `Overture` | Resumable Overture Places scan for US businesses with email but no website. Raw candidates, email evidence, qualification views and processed partitions live in DuckDB. |
| `Foursquare` | Resumable Foursquare Places scan, taxonomy and email quality, plus conservative matches against Overture. Requires the existing Hugging Face account/token for gated source access. DuckDB and Parquet exports are private. |
| `FMCSA` | Original filtered September 1 motor-carrier census CSV. This source has no website-presence field, so its carriers are not automatically treated as no-website leads. |
| `Lead Warehouse` | Separate `lead_warehouse` PostgreSQL database. Preserves raw Overture/Foursquare/FMCSA records and builds canonical entities, source memberships, normalized contact evidence, conservative matching and auditable deduplication. |
| `Google Maps Scraping` | Original scraper and its `gmaps_scraper` PostgreSQL database; also warehouse enrichment that checks business matches, actual website availability and review metadata. Durable run IDs and queues support continuation. RPC and browser paths, email extraction, benchmarks and diagnostics remain available. |
| `Facebook Last Post` | Warehouse Facebook profile queue/results and entity rollups. Includes the latest uncommitted mobile/desktop triage work, metadata fields and `restricted` state. Its older README describes the original browser worker; `run_1k_triage.py` is a separate experimental runner and **does not enforce a 1,000-job limit**. |
| `Proxies`, `Captcha Solver` | Reusable clients and helper scripts in Git; authenticated routes, generated provider configs and CapSolver keys in the private transfer. |
| `scripts` | PostgreSQL backup/restore helpers, Linux dependencies and transfer verification. Existing PowerShell backups use the `gdrive:PostgresBackups` rclone remote. |

As of the transfer, the live warehouse has 2,616,345 canonical entities. Database
snapshots, schema dumps, exact counts and validation results belong to the private
package; those are the authoritative transfer state. Restoring the dumps is the
continuation path. Do not rebuild or re-import the warehouse merely to migrate PCs.

## 1. Clone and verify the private transfer

Install Git, Python 3.12 with venv support, Node.js 22 or newer, Docker Engine and
the Compose plugin using your Linux distribution's supported installation method.
Optional tools: rclone, PowerShell (`pwsh`) for the existing `.ps1` helpers, and
Google Chrome for the manual proxy browser. Budget at least 40 GB free disk for
the repository, transfer, installed dependencies and restored database indexes.

```bash
git clone https://github.com/ealexander232004/Website-Creation.git
cd Website-Creation
export HANDOFF="$HOME/Transfers/Website-Creation-LocalSend-2026-09-06"
# Change HANDOFF to the directory received through LocalSend.
python3 scripts/verify-handoff.py "$HANDOFF"
cp -a "$HANDOFF/workspace-private/." .
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements-linux.txt
python -m pip install -e './Facebook Last Post[dev]'
python -m playwright install --with-deps chromium
```

The overlay includes dotfiles. Check `git status --short --ignored` afterward:
credentials, databases and generated data should be ignored. Do not copy the
whole handoff folder into Git or run `git add -f` on private files. Windows
`node_modules`, Python environments, browser binaries, caches and Docker virtual
disks are deliberately excluded; reinstall them on Linux.

## 2. Restore local PostgreSQL

The existing compose service uses PostgreSQL 17, a named volume and port 5432.
Credentials come from `Google Maps Scraping/.env`. No data is stored in the image.
The transfer contains logical dumps, so Docker Desktop/WSL are not needed on Linux.

```bash
docker compose -p googlemapsscraping -f 'Google Maps Scraping/compose.yaml' \
  --env-file 'Google Maps Scraping/.env' up -d postgres
docker compose -p googlemapsscraping -f 'Google Maps Scraping/compose.yaml' \
  --env-file 'Google Maps Scraping/.env' ps
# Wait for postgres to become healthy, then:
python scripts/restore-linux.py "$HANDOFF"
python 'Lead Warehouse/build_warehouse.py' --status
python 'Lead Warehouse/import_fmcsa.py' --status
facebook-last-post --env-file 'Google Maps Scraping/.env' stats
(cd 'Google Maps Scraping' && python run.py stats)
```

The restore helper refuses databases with existing user rows and fails on the
first PostgreSQL restore error. It restores `lead_warehouse` and `gmaps_scraper`
into the local container; keep scrapers stopped during restore. The private
`postgres/roles.sql` and `postgres/postgres.dump` are supplementary recovery
artifacts. The compose-created `gmaps_scraper` role suffices for this project;
do not blindly replay role creation over an initialized server.

The restored archive already includes Facebook metadata columns. For a fresh
schema setup or future code deployment, `facebook-last-post ... migrate` now
applies both numbered SQL files, including the previously missing metadata and
state update. Queue leases retain timestamps; allow old leases to expire before
resuming workers. Avoid running the ThinkPad and Linux copies as separate writers
after choosing the Linux snapshot as your continuation point.

## 3. Start Keeplyn and reconnect hosted services

```bash
cd Keeplyn.com
npm ci
npm run dev
# In a second terminal, with the same directory:
npm run typecheck
npm run lint
npm run build
```

The transferred `.env.local` contains the existing service keys and price IDs.
Inspect `NEXT_PUBLIC_SITE_URL` locally; use `http://localhost:3000` for local
development when exercising links that should return to this PC. The hosted
Supabase project, its customers/uploads, Stripe objects, Resend domain and Vercel
deployment remain in their existing accounts; they are not machine-local data
and should not be recreated. Existing migrations are in `Keeplyn.com/supabase`.
Use the same accounts and reauthenticate the Vercel/Supabase/Stripe/GitHub CLIs or
connectors you need. Copied Vercel OIDC tokens are temporary and are not a durable
login. Browser sessions, OS keychains and Codex authentication are not portable.
The private root `.env` includes the locally saved account recovery codes.

Production webhooks still point at production. Local webhook testing requires
its own forwarding setup and matching signing secret. Local development currently
uses real hosted service credentials; actions in the portal can affect those
services. No production deployment or external customer action was needed for
this machine transfer.

## 4. Continue data work

From the checkout root with `.venv` active:

```bash
python Overture/download_leads.py --status
python Foursquare/download_leads.py --status
python -m pytest 'Facebook Last Post/tests' -q
(cd 'Google Maps Scraping' && python -m pytest tests test_email_extractor_quality.py -q)
```

For Maps work, read `Google Maps Scraping/GOOGLE_MAPS_ENRICHMENT.md`, inspect
restored run IDs, and use `--resume-run <run-uuid>` when continuing an existing
run. The older scraper README still describes SQLite; current primary storage
is PostgreSQL. Historical SQLite files from the extra worktree are preserved
privately as consistent SQLite backups.

Run the experimental Facebook triage script from the checkout root because it
resolves `.env` and proxy files relative to the working directory. Its filename
is not a budget control. Preserve its current state for development before
starting a large job; the original browser runner and triage runner have
different access-wall and retry behavior.

Copy the private account config files only if needed:

```bash
mkdir -p "$HOME/.config/rclone" "$HOME/.cache/huggingface"
cp "$HANDOFF/home/.config/rclone/rclone.conf" "$HOME/.config/rclone/"
cp "$HANDOFF/home/.cache/huggingface/"* "$HOME/.cache/huggingface/"
chmod 600 "$HOME/.config/rclone/rclone.conf" "$HOME/.cache/huggingface/"*
```

The rclone configuration preserves access to older Google Drive backups.
The original PowerShell backup script performs retention pruning; read its
parameters before running it. `CHROME_PATH=/usr/bin/chromium` can select Chromium
for `Proxies/launch-hardened-incognito-proxy.mjs`; Linux defaults to `google-chrome`.
Use `pwsh` for other `.ps1` helpers, translating Windows paths in their examples.
Snapshot JSON/logs contain historical Windows paths and are audit records.

## Unfinished historical work

Two additional GitHub branches preserve source that was outside current main:

- `codex/archive-worktree-f739`: older unfinished scraper/database changes and
  a different Stripe checkout/webhook implementation.
- `codex/archive-stash-hosting`: the saved “WIP before hosting updates fix” stash,
  including source files that differ from the surviving worktree.

These are archival source snapshots, not merged features. Compare and cherry-pick
deliberately; replacing main with either would regress the newer website and
warehouse. The private package also has the full `worktree-f739` file snapshot,
two stash tar archives and `all-local-refs.bundle` for exact Git recovery. The
bundle includes historical private data and stays off GitHub. New Codex tasks
can read this document to recover project context; desktop task history itself
is not part of the application repository.
