# Google Maps Small Business Scraper (No-Website Lead Engine)

A high-performance, modular Google Maps scraper designed to extract small business leads across the United States that **do not have a website** or rely solely on social media / deprecated Google business pages.

---

## Key Capabilities

1. **Precision Web Presence Classification**:
   - **True No-Website**: Identifies listings with zero website link in their Google profile.
   - **Social-Media-Only Substitutes**: Automatically identifies when a business owner linked a Facebook page, Instagram profile, Yelp listing, or directory page instead of a real website.
   - **Dead Google Sites**: Detects defunct `*.business.site` domains (which Google officially deprecated in March 2024, leaving those businesses with non-functional pages).
   - **Free Site Builders**: Flags listings using `linktr.ee`, `carrd.co`, `wixsite.com`, `wordpress.com`, etc.

2. **Unclaimed Google Business Profile Detection**:
   - Identifies businesses showing the "Claim this business" badge—a key signal for high-converting outreach.

3. **U.S.-Wide Scaling via Spatial Partitioning**:
   - Google Maps strictly limits single queries to **120 results maximum**.
   - Solved via **Spatial Bounding Box Matrices** & **Adaptive Coordinate Grids** across all 50 U.S. states and top metropolitan cities.

4. **Headless Execution & Anti-Detection**:
   - Default **headless** browser execution powered by Playwright with stealth scripts overriding `navigator.webdriver`, plugins, locales, and viewport fingerprints.
   - Human-like scrolling physics with micro-delays and jitter.

5. **Integrated Proxy & CapSolver Support**:
   - Automatically detects and routes requests through the user's static ISP proxies (`Proxies/proxy-urls.txt`).
   - Integrated with CapSolver (`Captcha Solver/capsolver_client.py`) for automated reCAPTCHA v2 challenge resolution.

6. **WAL-Mode SQLite Persistence & Resumable Queue**:
   - Concurrent-safe local database (`gmaps_leads.db`) with deduplication on `place_id`, `cid`, and compound address keys.
   - Persistent queue enables pause, resume, and recovery across long scraping sessions.

7. **Multi-Format Lead Export**:
   - Exports directly to CSV, multi-tab Excel (`.xlsx`), or JSONL with filtering by state, review count, category, and website type.

---

## Directory Layout

```
Google Maps Scraping/
├── config.py                 # Configuration settings, env loading, defaults
├── models.py                 # Pydantic data models (Lead, SearchJob, WebsiteType)
├── website_analyzer.py       # URL classification engine (No website vs Social vs Custom)
├── geo_grid.py               # US Geographic database (50 States, Bounding Boxes, Cities)
├── proxy_manager.py          # Proxy pool manager with health checks and rotation
├── captcha_handler.py        # CapSolver bridge for Google bot challenge handling
├── parser.py                 # HTML & detail sidebar data extraction
├── browser_engine.py         # Headless Playwright engine with stealth scripts
├── database.py               # SQLite WAL-mode storage & task queue
├── export.py                 # Export engine (CSV, Multi-tab Excel, JSONL)
├── scraper.py                # Multi-worker async orchestrator
├── cli.py                    # Rich CLI interface
├── run.py                    # Entry point executable
├── requirements.txt          # Package dependencies
└── README.md                 # System documentation
```

---

## Quick Start & Usage

### 1. Diagnostic Check
Verify your proxy bundle and CapSolver balance:
```powershell
python run.py check
```

### 2. Direct Scrape (City / State / Nationwide)
Scrape a specific city headlessly with 3 workers:
```powershell
python run.py scrape --keyword "plumber" --city "Austin, TX" --headless
```

Scrape an entire state using a coordinate grid:
```powershell
python run.py scrape --keyword "roofing contractor" --state TX --step 0.08 --workers 4
```

### 3. Enqueue Nationwide Campaigns (Resumable)
Add all 50 states to the database queue:
```powershell
python run.py queue --keyword "auto repair" --all-states --step 0.10
```

Resume processing pending queue jobs at any time:
```powershell
python run.py resume --workers 5 --headless
```

### 4. Inspect Database Statistics
```powershell
python run.py stats
```

### 5. Export Leads
Export only businesses without websites to a clean CSV:
```powershell
python run.py export --format csv --no-website-only --output exports/leads_no_website.csv
```

Export to a multi-tab Excel spreadsheet organized by category:
```powershell
python run.py export --format excel --output exports/leads_master.xlsx
```

---

## System Capabilities vs Limitations

### What it is Able to Do:
- **Zero-Website Discovery**: Isolates small businesses lacking dedicated domains.
- **Enriched Profile Data**: Extracts business name, primary and secondary categories, direct phone number, full street address, city, state, zip code, rating, review count, price tier, and maps URL.
- **Unclaimed Profile Identification**: Flags businesses eligible for Google Business Profile claim outreach.
- **Nationwide Coverage**: Penetrates beyond the 120-result Google Maps cap via spatial subdivision.
- **Fault-Tolerant Resumption**: Interrupted jobs retain progress in SQLite; only uncompleted grid cells run on restart.
- **Headless Background Execution**: Low CPU and RAM consumption with zero GUI windows needed.

### Limitations & Considerations:
1. **Google Maps 120-Result Ceiling Per Cell**:
   - Even with zoom 14-16z, hyper-dense metropolitan centers (e.g. Midtown Manhattan, NY) may have >120 listings of a generic niche (e.g. "restaurant") in a single block. A smaller `--step` (e.g. 0.03 deg) or sub-niche keywords are recommended for dense downtown cores.
2. **Owner Email Addresses**:
   - Google Maps profiles list phone numbers and physical addresses, but **never display direct email addresses**. Direct email enrichment requires secondary scraping of linked social pages or WHOIS records.
3. **Service-Area Businesses (SABs)**:
   - Businesses that operate without a public storefront (e.g. mobile locksmiths) hide their street address on Maps, showing only the service city/county.
4. **Proxy Pool Size vs Concurrency**:
   - When running nationwide with high worker counts (10+), rotating across at least 10–25 residential or dedicated ISP proxies prevents Google from triggering rate-limit cooldowns.
