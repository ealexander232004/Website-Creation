# Foursquare email/no-website lead database

This project builds a resumable local DuckDB from the current Foursquare Open
Source Places release. It scans every Places file in the selected release and
keeps US rows with a populated `email` and a null or blank `website`.

There is deliberately **no `date_refreshed` cutoff**. All source refresh dates
are retained.

## Qualification rules

`contact_places` contains every US email/no-website candidate for auditing.
`qualified_leads` applies the business and email-quality rules:

- `date_closed IS NULL`
- none of Foursquare's official noncommercial category IDs
- none of: `closed`, `duplicate`, `delete`, `doesnt_exist`, `privatevenue`
- syntax-valid, non-placeholder email

Social profiles do not count as websites. Role accounts such as `info@` and
`sales@` remain eligible. SMTP verification is not performed.

Foursquare does not publish an employee-count, revenue, independent-business,
or small-business flag. `qualified_leads` is therefore a probable commercial
business set, not a guaranteed SMB set.

## One-time access setup

1. Log in at <https://huggingface.co/datasets/foursquare/fsq-os-places>.
2. Accept the dataset conditions.
3. Create a read token at <https://huggingface.co/settings/tokens>.
4. In PowerShell, set it for the current terminal without placing it in shell
   history:

```powershell
$env:HF_TOKEN = Read-Host "Hugging Face read token" -MaskInput
```

The pipeline never writes the token into the database, progress file, or source
tree.

## Run or resume

```powershell
cd "C:\Users\ezraa\Documents\Local Documents\Website Creation\Foursquare"
python .\download_leads.py
```

The latest release is discovered automatically. Each batch commits separately,
and rerunning skips completed source files.

## Monitor without opening the active database

```powershell
python .\download_leads.py --status
```

For continuous monitoring:

```powershell
while ($true) { Clear-Host; python .\download_leads.py --status; Start-Sleep 15 }
```

## Outputs

- `foursquare_email_no_website.duckdb`
- `exports/qualified_leads.parquet`
- `exports/foursquare_unique_vs_overture.parquet`
- `foursquare_email_no_website.progress.json`

The DuckDB includes:

- `contact_places`: all raw email/no-website candidates in scope
- `lead_emails`: normalized email checks
- `fsq_categories`: Foursquare's category taxonomy for the release
- `qualified_leads`: probable commercial, open, usable-email leads
- `overture_matches`: auditable cross-source match evidence
- `best_overture_match`: best Overture candidate for each Foursquare lead
- `foursquare_unique_vs_overture`: qualified leads without a high-confidence
  Overture duplicate
- `database_summary`: build and quality counts

High-confidence Overture duplicates require an exact normalized phone, an exact
normalized name plus postal code, or an exact email plus normalized name.
Email-only matches are deliberately not treated as duplicates because chains
may reuse corporate addresses across locations.
