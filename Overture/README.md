# Overture email/no-website lead database

This project builds a resumable local DuckDB from the Overture Maps Places
release. The source filter is exact:

- at least one value in `emails`
- no values in `websites`
- social-profile URLs remain eligible because Overture stores them separately in
  `socials`
- default geography: any address with `country = 'US'`

Overture does not expose a native `small_business` flag. The database therefore
keeps every contact-matching place in `contact_places` and exposes the
`small_business_leads` view using a transparent proxy: no known Overture brand,
a commercial taxonomy group, not permanently closed, and at least one
syntactically valid email.

## Run or resume

```powershell
cd "C:\Users\ezraa\Documents\Local Documents\Website Creation\Overture"
python .\download_leads.py
```

The process commits each of the 16 source partitions separately. Running the
same command again skips completed partitions.

## Progress without touching the locked database

```powershell
python .\download_leads.py --status
```

## Query after the writer exits

```powershell
python -c "import duckdb; c=duckdb.connect('overture_smb_leads.duckdb', read_only=True); print(c.sql('SELECT * FROM database_summary').df().to_string(index=False))"
```

Useful objects:

- `contact_places`: all places matching email present + website absent
- `lead_emails`: normalized, one email per row with syntax and role-account flags
- `usable_emails`: syntax-valid email rows plus reuse counts
- `small_business_leads`: probable small-business places ready for analysis
- `database_summary`: compact build and row counts
- `processed_partitions`: resumability and per-partition timing/errors

Use `--country ALL` with a different `--database` path for a global build. A
database cannot be silently mixed across releases or country scopes.
