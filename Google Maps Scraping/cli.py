"""Rich Command Line Interface for Google Maps Small Business Scraper."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from categories import CATEGORY_PRESETS, resolve_keywords
from config import DEFAULT_CONFIG, ScraperConfig
from database import Database
from export import LeadExporter
from scraper import ScraperOrchestrator

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


@click.group()
def cli() -> None:
    """Google Maps Small Business Lead Scraper for Businesses Without Websites."""
    pass


@cli.command()
@click.option("--keyword", "-k", help="Business niche or comma-separated list (e.g. 'plumber, roofing')")
@click.option("--preset", "-p", type=click.Choice(list(CATEGORY_PRESETS.keys())), default="all_small_business", help="Category taxonomy preset")
@click.option("--city", "-c", help="Target city name (e.g. 'Austin, TX', 'Miami, FL')")
@click.option("--state", "-s", help="2-letter US State abbreviation (e.g. 'TX', 'CA', 'FL')")
@click.option("--limit", "-l", type=int, default=None, help="Maximum number of search jobs to execute")
@click.option("--workers", "-w", default=5, help="Number of concurrent workers")
@click.option("--headless/--headed", default=True, help="Run browser headlessly or with visible UI")
@click.option("--no-website-only/--all-leads", default=True, help="Filter only businesses without custom websites")
def scrape(
    keyword: Optional[str],
    preset: str,
    city: Optional[str],
    state: Optional[str],
    limit: Optional[int],
    workers: int,
    headless: bool,
    no_website_only: bool,
) -> None:
    """Directly scrape a city, state, or nationwide multi-category target."""
    keywords = resolve_keywords(keyword_input=keyword, preset=preset)
    config = ScraperConfig(
        workers=workers,
        headless=headless,
        no_website_only=no_website_only,
    )
    orchestrator = ScraperOrchestrator(config)

    console.print(
        Panel.fit(
            f"[bold green]Starting Google Maps Multi-Category Scraper[/bold green]\n"
            f"[cyan]Categories ({len(keywords)}):[/cyan] {', '.join(keywords[:4])}...\n"
            f"[cyan]Target:[/cyan] {city or (f'State {state}' if state else 'Top US Cities')}\n"
            f"[cyan]Workers:[/cyan] {workers}\n"
            f"[cyan]Limit Jobs:[/cyan] {limit or 'Unlimited'}\n"
            f"[cyan]No-Website Filter:[/cyan] {no_website_only}",
            title="Campaign Configuration",
            border_style="green",
        )
    )

    count = orchestrator.enqueue_taxonomy_campaign(
        keywords=keywords,
        state_code=state,
        custom_cities=[city] if city else None,
        limit=limit,
    )
    console.print(f"[yellow]Enqueued {count} search jobs in queue.[/yellow]")

    # Run the orchestrator
    asyncio.run(orchestrator.run())
    console.print("[bold green]Scraping completed successfully![/bold green]")


@cli.command()
@click.option("--keyword", "-k", help="Business niche or comma-separated list")
@click.option("--preset", "-p", type=click.Choice(list(CATEGORY_PRESETS.keys())), default="all_small_business", help="Category taxonomy preset")
@click.option("--state", "-s", help="2-letter US State abbreviation (e.g. 'TX', 'NY')")
@click.option("--city", "-c", help="Specific city name")
@click.option("--limit", "-l", type=int, default=5000, help="Maximum number of search jobs to enqueue")
def queue(
    keyword: Optional[str],
    preset: str,
    state: Optional[str],
    city: Optional[str],
    limit: int,
) -> None:
    """Enqueues multi-category geographic search tasks into the database queue."""
    keywords = resolve_keywords(keyword_input=keyword, preset=preset)
    config = DEFAULT_CONFIG
    orchestrator = ScraperOrchestrator(config)

    added = orchestrator.enqueue_taxonomy_campaign(
        keywords=keywords,
        state_code=state,
        custom_cities=[city] if city else None,
        limit=limit,
    )
    console.print(f"[bold green]Successfully enqueued {added} search tasks into database queue![/bold green]")


@cli.command()
@click.option("--workers", "-w", default=5, help="Number of concurrent workers")
@click.option("--headless/--headed", default=True, help="Run browser headlessly or with visible UI")
def resume(workers: int, headless: bool) -> None:
    """Resumes processing pending jobs from the database queue."""
    config = ScraperConfig(workers=workers, headless=headless)
    orchestrator = ScraperOrchestrator(config)

    stats = orchestrator.db.get_stats()
    console.print(f"[cyan]Resuming search queue ({stats['queue_pending']} pending tasks remaining with {workers} workers)...[/cyan]")
    asyncio.run(orchestrator.run())


@cli.command()
@click.option("--format", "-f", type=click.Choice(["csv", "excel", "jsonl"]), default="csv")
@click.option("--output", "-o", help="Output file path (defaults to exports/leads_<timestamp>)")
@click.option("--no-website-only/--all-leads", default=True, help="Export only businesses without websites")
@click.option("--state", "-s", help="Filter by state code (e.g. TX)")
@click.option("--category", "-c", help="Filter by category substring (e.g. Plumber)")
@click.option("--min-reviews", default=0, help="Minimum Google reviews count")
@click.option("--unclaimed-only", is_flag=True, help="Export only unclaimed Google Business Profiles")
def export(
    format: str,
    output: Optional[str],
    no_website_only: bool,
    state: Optional[str],
    category: Optional[str],
    min_reviews: int,
    unclaimed_only: bool,
) -> None:
    """Exports collected leads to CSV, Excel, or JSONL with advanced filtering."""
    db = Database(DEFAULT_CONFIG.database_path)
    exporter = LeadExporter(db)

    ext = "xlsx" if format == "excel" else format
    output_path = Path(output) if output else DEFAULT_CONFIG.export_dir / f"leads_no_website.{ext}"

    if format == "csv":
        count = exporter.export_to_csv(
            output_path=output_path,
            no_website_only=no_website_only,
            state=state,
            category=category,
            min_reviews=min_reviews,
            unclaimed_only=unclaimed_only,
        )
    elif format == "excel":
        count = exporter.export_to_excel(
            output_path=output_path,
            state=state,
            category=category,
        )
    else:
        count = exporter.export_to_jsonl(
            output_path=output_path,
            no_website_only=no_website_only,
        )

    console.print(f"[bold green]Successfully exported {count} leads to: {output_path}[/bold green]")


@cli.command()
def stats() -> None:
    """Displays summary statistics of scraped leads and campaign progress."""
    db = Database(DEFAULT_CONFIG.database_path)
    s = db.get_stats()

    table = Table(title="Google Maps Leads Database Overview", border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Total Leads Scraped", f"{s['total_leads']:,}")
    table.add_row("Leads Without Real Website", f"{s['no_website_leads']:,} ({s['percentage_no_website']}%)")
    table.add_row("Using Social Media Only", f"{s['social_only_leads']:,}")
    table.add_row("Unclaimed Business Profiles", f"{s['unclaimed_leads']:,}")
    table.add_row("---", "---")
    table.add_row("Queue Total Tasks", f"{s['queue_total']:,}")
    table.add_row("Queue Pending Tasks", f"{s['queue_pending']:,}")
    table.add_row("Queue Completed Tasks", f"{s['queue_completed']:,}")
    table.add_row("Queue Failed Tasks", f"{s['queue_failed']:,}")

    console.print(table)


@cli.command()
def check() -> None:
    """Checks Proxy Pool and CapSolver integration credentials."""
    config = DEFAULT_CONFIG
    orchestrator = ScraperOrchestrator(config)

    table = Table(title="System Environment Diagnostic", border_style="blue")
    table.add_column("Component", style="bold")
    table.add_column("Status", style="yellow")
    table.add_column("Details")

    # Proxy check
    proxies_count = orchestrator.proxy_manager.total_proxies
    table.add_row(
        "Proxies",
        "[green]Ready[/green]" if proxies_count > 0 else "[red]Missing[/red]",
        f"{proxies_count} proxy routes loaded from bundle",
    )

    # CapSolver check
    captcha = orchestrator.captcha_handler
    if captcha.enabled:
        balance = captcha.check_balance()
        table.add_row(
            "CapSolver",
            "[green]Connected[/green]",
            f"Account Balance: ${balance:.3f} USD",
        )
    else:
        table.add_row(
            "CapSolver",
            "[yellow]Disabled[/yellow]",
            "No API key configured",
        )

    # Database
    db_exists = config.database_path.is_file()
    table.add_row(
        "SQLite Database",
        "[green]Active[/green]" if db_exists else "[cyan]Ready to create[/cyan]",
        str(config.database_path),
    )

    console.print(table)


if __name__ == "__main__":
    cli()
