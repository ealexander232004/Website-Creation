"""Automated Performance Optimizer & Grid Search for Google Maps Enrichment.

Runs 20+ systematic 10k configurations across processes, worker counts, and ratios
to find the absolute fastest, most stable setup.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psycopg

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "gmaps_scraper",
    "password": "7sK9mQ4vN2xR8pL6cT5wH3jF",
    "dbname": "lead_warehouse",
}

# 24 Diverse Configurations to sweep the parameter space
EXPERIMENTS: list[dict[str, Any]] = [
    # Baseline sweeps around 770-1100 total workers (5 processes)
    {"procs": 5, "maps": 220, "maps_per_ip": 4, "web": 550, "web_per_ip": 10, "rps": 20.0, "pool": 200},
    {"procs": 5, "maps": 220, "maps_per_ip": 4, "web": 660, "web_per_ip": 12, "rps": 20.0, "pool": 200},
    {"procs": 5, "maps": 220, "maps_per_ip": 4, "web": 770, "web_per_ip": 14, "rps": 20.0, "pool": 200},
    {"procs": 5, "maps": 220, "maps_per_ip": 4, "web": 880, "web_per_ip": 16, "rps": 20.0, "pool": 200},
    
    # 275 Maps workers (5 per IP)
    {"procs": 5, "maps": 275, "maps_per_ip": 5, "web": 550, "web_per_ip": 10, "rps": 20.0, "pool": 200},
    {"procs": 5, "maps": 275, "maps_per_ip": 5, "web": 660, "web_per_ip": 12, "rps": 20.0, "pool": 200},
    {"procs": 5, "maps": 275, "maps_per_ip": 5, "web": 770, "web_per_ip": 14, "rps": 20.0, "pool": 200},
    {"procs": 5, "maps": 275, "maps_per_ip": 5, "web": 880, "web_per_ip": 16, "rps": 20.0, "pool": 200},
    
    # 330 Maps workers (6 per IP)
    {"procs": 5, "maps": 330, "maps_per_ip": 6, "web": 660, "web_per_ip": 12, "rps": 20.0, "pool": 250},
    {"procs": 5, "maps": 330, "maps_per_ip": 6, "web": 825, "web_per_ip": 15, "rps": 20.0, "pool": 250},
    {"procs": 5, "maps": 330, "maps_per_ip": 6, "web": 990, "web_per_ip": 18, "rps": 20.0, "pool": 250},
    
    # RPS = 25.0 sweeps
    {"procs": 5, "maps": 275, "maps_per_ip": 5, "web": 660, "web_per_ip": 12, "rps": 25.0, "pool": 200},
    {"procs": 5, "maps": 275, "maps_per_ip": 5, "web": 770, "web_per_ip": 14, "rps": 25.0, "pool": 200},
    {"procs": 5, "maps": 330, "maps_per_ip": 6, "web": 660, "web_per_ip": 12, "rps": 25.0, "pool": 250},
    {"procs": 5, "maps": 330, "maps_per_ip": 6, "web": 825, "web_per_ip": 15, "rps": 25.0, "pool": 250},
    
    # 6 processes (aligns with 6 physical Performance cores)
    {"procs": 6, "maps": 264, "maps_per_ip": 5, "web": 660, "web_per_ip": 12, "rps": 20.0, "pool": 200},
    {"procs": 6, "maps": 330, "maps_per_ip": 6, "web": 792, "web_per_ip": 15, "rps": 20.0, "pool": 250},
    {"procs": 6, "maps": 330, "maps_per_ip": 6, "web": 924, "web_per_ip": 17, "rps": 25.0, "pool": 250},
    
    # 8 processes (broad multi-core distribution)
    {"procs": 8, "maps": 280, "maps_per_ip": 6, "web": 680, "web_per_ip": 13, "rps": 20.0, "pool": 250},
    {"procs": 8, "maps": 320, "maps_per_ip": 6, "web": 800, "web_per_ip": 15, "rps": 20.0, "pool": 250},
    {"procs": 8, "maps": 360, "maps_per_ip": 7, "web": 920, "web_per_ip": 17, "rps": 25.0, "pool": 250},
    
    # 4 processes comparison
    {"procs": 4, "maps": 220, "maps_per_ip": 4, "web": 660, "web_per_ip": 12, "rps": 20.0, "pool": 200},
    
    # Higher throughput sweet-spot sweeps
    {"procs": 5, "maps": 385, "maps_per_ip": 7, "web": 770, "web_per_ip": 14, "rps": 25.0, "pool": 250},
    {"procs": 5, "maps": 385, "maps_per_ip": 7, "web": 935, "web_per_ip": 17, "rps": 25.0, "pool": 250},
]


def clean_db(run_id: str | None = None) -> None:
    """Deletes test run data so all runs execute against the exact same 10,000 leads."""
    with psycopg.connect(**DB_CONFIG) as conn:
        if run_id:
            conn.execute("delete from warehouse.google_maps_enrichment where run_id = %s", (run_id,))
            conn.execute("delete from warehouse.google_maps_enrichment_runs where run_id = %s", (run_id,))
        else:
            conn.execute("""
                delete from warehouse.google_maps_enrichment
                where run_id in (select run_id from warehouse.google_maps_enrichment_runs order by started_at desc limit 1);
                delete from warehouse.google_maps_enrichment_runs
                where run_id in (select run_id from warehouse.google_maps_enrichment_runs order by started_at desc limit 1);
            """)


def get_run_details(run_id: str) -> dict[str, Any]:
    with psycopg.connect(**DB_CONFIG) as conn:
        row = conn.execute("""
            select completed_at - started_at as duration,
                   summary->'runtime'->'proxy_bandwidth' as bandwidth,
                   summary->'runtime'->'postgres_pool_stats' as pool_stats,
                   summary->'statuses' as statuses,
                   summary->'website_statuses' as website_statuses
            from warehouse.google_maps_enrichment_runs
            where run_id = %s
        """, (run_id,)).fetchone()
        if not row:
            return {}
        duration, bandwidth, pool_stats, statuses, web_statuses = row
        return {
            "db_duration_sec": duration.total_seconds() if duration else 0.0,
            "bandwidth_mb": (bandwidth or {}).get("total_mb", 0.0),
            "pool_waiting": (pool_stats or {}).get("requests_waiting", 0),
            "matched": (statuses or {}).get("matched", 0),
            "not_found": (statuses or {}).get("not_found", 0),
            "failed": (statuses or {}).get("failed", 0),
            "live": (web_statuses or {}).get("live", 0),
            "timeout": (web_statuses or {}).get("timeout", 0),
            "http_429": (web_statuses or {}).get("http_429", 0),
        }


def run_experiment(exp: dict[str, Any], exp_idx: int, total_exps: int) -> dict[str, Any]:
    procs = exp["procs"]
    maps = exp["maps"]
    maps_per_ip = exp["maps_per_ip"]
    web = exp["web"]
    web_per_ip = exp["web_per_ip"]
    rps = exp["rps"]
    pool = exp["pool"]
    total_workers = maps + web

    header = (
        f"\n[{exp_idx}/{total_exps}] RUNNING: procs={procs} | maps={maps} ({maps_per_ip}/IP) | "
        f"web={web} ({web_per_ip}/IP) | total={total_workers} | rps={rps} | pool={pool}"
    )
    print(header, flush=True)

    cmd = [
        sys.executable,
        "enrich_google_maps.py",
        "--limit", "10000",
        "--workers", str(maps),
        "--workers-per-proxy", str(maps_per_ip),
        "--website-workers", str(web),
        "--website-workers-per-proxy", str(web_per_ip),
        "--postgres-pool-size", str(pool),
        "--maps-rps-per-proxy", str(rps),
        "--website-timeout", "4.0",
        "--timeout", "10.0",
        "--processes", str(procs),
        "--monitor-interval", "2.0",
    ]

    t0 = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent),
    )
    wall_time = time.time() - t0

    stdout = result.stdout
    run_id = None
    for line in stdout.splitlines():
        if line.startswith("run_id="):
            run_id = line.split()[0].split("=")[1]
            break

    db_details = get_run_details(run_id) if run_id else {}
    if run_id:
        clean_db(run_id)

    res = {
        "exp_idx": exp_idx,
        "config": exp,
        "wall_time_sec": round(wall_time, 2),
        "db_time_sec": round(db_details.get("db_duration_sec", wall_time), 2),
        "throughput": round(10000.0 / wall_time, 1) if wall_time > 0 else 0.0,
        "matched": db_details.get("matched", 0),
        "not_found": db_details.get("not_found", 0),
        "failed": db_details.get("failed", 0),
        "live": db_details.get("live", 0),
        "timeout": db_details.get("timeout", 0),
        "bandwidth_mb": db_details.get("bandwidth_mb", 0.0),
        "returncode": result.returncode,
    }

    summary_line = (
        f"-> Finished in {res['wall_time_sec']}s ({res['db_time_sec']}s DB) | "
        f"Rate: {res['throughput']} leads/s | Live: {res['live']} | "
        f"Timeouts: {res['timeout']} | Failed: {res['failed']} | Code: {res['returncode']}"
    )
    print(summary_line, flush=True)
    return res


def main() -> int:
    results: list[dict[str, Any]] = []
    total = len(EXPERIMENTS)

    print(f"Starting 10k Optimization Sweep: {total} experiments scheduled.")
    print("All runs test 10k leads across 55 US proxies with --website-timeout 4.0.")

    try:
        for idx, exp in enumerate(EXPERIMENTS, 1):
            res = run_experiment(exp, idx, total)
            results.append(res)
            # Save intermediate results
            Path("benchmark_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    except KeyboardInterrupt:
        print("\nOptimization sweep interrupted by user! Summarizing completed runs...", flush=True)

    if not results:
        print("No experiments completed.")
        return 1

    # Sort leaderboard by wall time ascending (fastest first)
    sorted_results = sorted(results, key=lambda r: r["wall_time_sec"])
    best = sorted_results[0]

    print("\n" + "="*80)
    print("OPTIMIZATION SWEEP COMPLETE — TOP 5 FASTEST CONFIGURATIONS")
    print("="*80)
    print(f"{'Rank':<5} {'Wall Time':<11} {'Rate':<14} {'Procs':<6} {'Maps':<7} {'Web':<7} {'Total':<7} {'RPS/IP':<8} {'Live':<6}")
    print("-" * 80)
    for rank, r in enumerate(sorted_results[:5], 1):
        c = r["config"]
        tot = c["maps"] + c["web"]
        print(
            f"#{rank:<4} {r['wall_time_sec']:>6.2f}s     "
            f"{r['throughput']:>6.1f} leads/s  "
            f"{c['procs']:<6} {c['maps']:<7} {c['web']:<7} {tot:<7} "
            f"{c['rps']:<8} {r['live']:<6}"
        )

    print("\n" + "="*80)
    c_best = best["config"]
    print(f"OVERALL WINNER: Rank #1 in {best['wall_time_sec']}s ({best['throughput']} leads/s)")
    print(f"Optimal Command:")
    print(
        f"python enrich_google_maps.py --limit 10000 --processes {c_best['procs']} "
        f"--workers {c_best['maps']} --workers-per-proxy {c_best['maps_per_ip']} "
        f"--website-workers {c_best['web']} --website-workers-per-proxy {c_best['web_per_ip']} "
        f"--maps-rps-per-proxy {c_best['rps']} --postgres-pool-size {c_best['pool']} "
        f"--website-timeout 4.0 --timeout 10.0"
    )
    print("="*80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
