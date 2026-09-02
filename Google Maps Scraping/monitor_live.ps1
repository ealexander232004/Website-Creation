# Live 10-second updating snapshot for Google Maps enrichment runs.
# Run from PowerShell: .\monitor_live.ps1
# Press Ctrl+C to exit.

$query = @"
with latest_run as (
    select run_id, started_at, enqueued_count
    from warehouse.google_maps_enrichment_runs
    order by started_at desc
    limit 1
),
stats as (
    select
        count(*) filter (where status in ('matched', 'not_found', 'failed')) as done,
        count(*) filter (where status = 'matched') as matched,
        count(*) filter (where website_status = 'not_listed_on_google') as true_no_website,
        count(*) filter (where website_status = 'live') as live_website,
        count(*) filter (where website_status = 'timeout') as timeouts,
        count(*) filter (where status = 'failed') as failed,
        count(*) filter (where status = 'in_progress') as in_flight,
        count(*) filter (where status = 'queued') as queue_remaining
    from warehouse.google_maps_enrichment
    where run_id = (select run_id from latest_run)
)
select
    r.run_id,
    to_char(now() - r.started_at, 'HH24:MI:SS') as elapsed,
    r.enqueued_count as total_enqueued,
    s.done,
    round(100.0 * s.done / nullif(r.enqueued_count, 0), 2) as pct_complete,
    round(s.done / greatest(extract(epoch from (now() - r.started_at)), 1.0), 1) as leads_per_sec,
    case
        when s.done > 0 then
            to_char(
                ((r.enqueued_count - s.done) / (s.done / greatest(extract(epoch from (now() - r.started_at)), 1.0))) * interval '1 second',
                'HH24:MI:SS'
            )
        else 'Calculating...'
    end as eta_remaining,
    s.matched,
    s.true_no_website,
    s.live_website,
    s.timeouts,
    s.failed,
    s.in_flight,
    s.queue_remaining
from latest_run r, stats s;
"@

Write-Host "Starting live 10-second monitoring loop. Press Ctrl+C to exit." -ForegroundColor Cyan

while ($true) {
    Clear-Host
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "       GOOGLE MAPS WAREHOUSE ENRICHMENT: 1.38M FMCSA CARRIER RUN SNAPSHOT       " -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | Stop Trigger: Create file 'STOP'" -ForegroundColor DarkGray
    Write-Host ""
    
    docker exec googlemapsscraping-postgres-1 psql -U gmaps_scraper -d lead_warehouse -c "\x" -c "$query"
    
    Start-Sleep -Seconds 10
}
