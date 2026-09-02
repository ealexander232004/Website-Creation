# Live 10-second updating snapshot for Google Maps enrichment runs.
# Run from PowerShell: .\monitor_live.ps1
# Press Ctrl+C to exit.

$query = @"
select
    r.run_id,
    to_char(now() - r.started_at, 'HH24:MI:SS') as elapsed,
    r.enqueued_count as total_enqueued,
    count(e.entity_id) filter (where e.status in ('matched', 'not_found', 'failed')) as done,
    round(100.0 * count(e.entity_id) filter (where e.status in ('matched', 'not_found', 'failed')) / nullif(r.enqueued_count, 0), 2) as pct_complete,
    round(count(e.entity_id) filter (where e.status in ('matched', 'not_found', 'failed')) / greatest(extract(epoch from (now() - r.started_at)), 1.0), 1) as leads_per_sec,
    case
        when count(e.entity_id) filter (where e.status in ('matched', 'not_found', 'failed')) > 0 then
            to_char(
                (
                    (r.enqueued_count - count(e.entity_id) filter (where e.status in ('matched', 'not_found', 'failed')))
                    / (count(e.entity_id) filter (where e.status in ('matched', 'not_found', 'failed')) / greatest(extract(epoch from (now() - r.started_at)), 1.0))
                ) * interval '1 second',
                'HH24:MI:SS'
            )
        else 'Calculating...'
    end as estimated_time_remaining,
    count(e.entity_id) filter (where e.status = 'matched') as matched,
    count(e.entity_id) filter (where e.website_status = 'not_listed_on_google') as true_no_website,
    count(e.entity_id) filter (where e.website_status = 'live') as live_website,
    count(e.entity_id) filter (where e.website_status = 'timeout') as timeouts,
    count(e.entity_id) filter (where e.status = 'failed') as failed,
    count(e.entity_id) filter (where e.status = 'in_progress') as in_flight,
    count(e.entity_id) filter (where e.status = 'queued') as queue_remaining
from warehouse.google_maps_enrichment_runs r
left join warehouse.google_maps_enrichment e on e.run_id = r.run_id
where r.run_id = (select run_id from warehouse.google_maps_enrichment_runs order by started_at desc limit 1)
group by r.run_id, r.started_at, r.enqueued_count;
"@

Write-Host "Starting live 10-second monitoring loop. Press Ctrl+C to exit." -ForegroundColor Cyan

while ($true) {
    Clear-Host
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "        GOOGLE MAPS WAREHOUSE ENRICHMENT: LIVE RUN SNAPSHOT (10s Refresh)        " -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | Stop Trigger: Create file 'STOP'" -ForegroundColor DarkGray
    Write-Host ""
    
    docker exec googlemapsscraping-postgres-1 psql -U gmaps_scraper -d lead_warehouse -c "\x" -c "$query"
    
    Start-Sleep -Seconds 10
}
