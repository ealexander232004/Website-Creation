# Unified Overture + Foursquare + FMCSA lead warehouse

PostgreSQL database: `lead_warehouse`

The warehouse preserves all locally available source data and adds a canonical
entity layer. It does not overwrite or modify the existing Google Maps scraper
database.

## Data model

- `raw_overture.*`: lossless Overture candidates and email evidence
- `raw_foursquare.*`: lossless Foursquare candidates, email evidence, taxonomy,
  and cross-source match evidence
- `raw_fmcsa.*`: typed FMCSA motor-carrier records, normalized email evidence,
  and import audit runs
- `warehouse.entities`: canonical business/place entities
- `warehouse.source_places`: source membership and match provenance
- `warehouse.entity_emails`: normalized email addresses with source agreement
- `warehouse.entity_phones`: normalized phones with all raw representations
- `warehouse.entity_socials`: platform-specific social profiles
- `warehouse.entity_categories`: source-native categories and hierarchies
- `warehouse.qualified_no_website_email_leads`: deduplicated lead view
- `warehouse.fmcsa_small_business_email_leads`: current filtered FMCSA carriers
  with email-quality fields
- `warehouse.lead_summary`: headline counts

Every Overture candidate seeds an entity. A Foursquare candidate attaches to an
Overture entity only when the existing high-confidence matcher agrees on phone,
name plus postcode, or email plus name. Otherwise it receives its own entity.

FMCSA carriers attach only when an existing entity is corroborated by email plus
phone, email plus exact normalized name, or phone plus exact normalized name and
postcode. Ambiguous records receive their own FMCSA entity. FMCSA records do not
set `is_qualified_no_website_email_lead`, because this source has no website
presence field.

## Build

Docker Desktop and the existing scraper Postgres service must be running:

```powershell
cd "C:\Users\ezraa\Documents\Local Documents\Website Creation\Google Maps Scraping"
docker compose up -d postgres

cd "C:\Users\ezraa\Documents\Local Documents\Website Creation\Lead Warehouse"
python .\build_warehouse.py
```

Import the filtered FMCSA snapshot after the base warehouse build:

```powershell
cd "C:\Users\ezraa\Documents\Local Documents\Website Creation\Lead Warehouse"
python .\import_fmcsa.py
```

Run or re-run the cross-source canonical deduplication to a fixed point:

```powershell
python .\deduplicate_warehouse.py
```

Raw source rows are never deleted by deduplication. Only canonical entities are
merged, and every merge is recorded in `warehouse.entity_merge_log`.

The build uses the existing local Postgres username/password but creates the
separate `lead_warehouse` database. Credentials remain in the scraper `.env`.

## Status and count

```powershell
python .\build_warehouse.py --status
```

```powershell
python .\import_fmcsa.py --status
```

```powershell
docker exec googlemapsscraping-postgres-1 psql -U gmaps_scraper -d lead_warehouse -c "select * from warehouse.lead_summary;"
```
