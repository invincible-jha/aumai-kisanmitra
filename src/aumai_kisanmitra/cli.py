"""CLI entry point for aumai-kisanmitra."""

from __future__ import annotations

import sys
from datetime import date

import click

from .core import FarmerAssistant, MandiPriceTracker, PestDatabase
from .models import AGRICULTURAL_DISCLAIMER, FarmerQuery, MandiPrice


@click.group()
@click.version_option()
def main() -> None:
    """AumAI KisanMitra — Farmer assistant with mandi prices and pest identification."""


@main.command("prices")
@click.option("--commodity", required=True, help="Commodity name (e.g. rice, wheat)")
@click.option("--state", default=None, help="Filter by state name (e.g. UP, Maharashtra)")
def prices(commodity: str, state: str | None) -> None:
    """Show mandi prices for a commodity. Loads sample data for demonstration."""
    tracker = MandiPriceTracker()

    # Load sample data for demonstration
    today = date.today().isoformat()
    sample_prices = [
        MandiPrice(commodity="rice", market="Azadpur", state="Delhi", min_price=1800.0, max_price=2200.0, modal_price=2000.0, date=today),
        MandiPrice(commodity="rice", market="Lucknow", state="UP", min_price=1750.0, max_price=2100.0, modal_price=1950.0, date=today),
        MandiPrice(commodity="rice", market="Patna", state="Bihar", min_price=1700.0, max_price=2050.0, modal_price=1900.0, date=today),
        MandiPrice(commodity="wheat", market="Azadpur", state="Delhi", min_price=2000.0, max_price=2350.0, modal_price=2150.0, date=today),
        MandiPrice(commodity="wheat", market="Lucknow", state="UP", min_price=1950.0, max_price=2300.0, modal_price=2100.0, date=today),
        MandiPrice(commodity="cotton", market="Akola", state="Maharashtra", min_price=6000.0, max_price=6800.0, modal_price=6400.0, date=today),
        MandiPrice(commodity="cotton", market="Warangal", state="Telangana", min_price=5900.0, max_price=6700.0, modal_price=6300.0, date=today),
        MandiPrice(commodity="onion", market="Nashik", state="Maharashtra", min_price=1200.0, max_price=2000.0, modal_price=1600.0, date=today),
        MandiPrice(commodity="potato", market="Agra", state="UP", min_price=800.0, max_price=1200.0, modal_price=1000.0, date=today),
    ]
    for price in sample_prices:
        tracker.add_price(price)

    results = tracker.get_prices(commodity, state)
    if not results:
        click.echo(f"No price data found for commodity '{commodity}'" + (f" in state '{state}'" if state else "") + ".")
        click.echo("\nNote: Connect to Agmarknet API for live prices.")
        return

    click.echo(f"\nMANDI PRICES: {commodity.upper()}" + (f" | State: {state}" if state else ""))
    click.echo(f"{'Market':<20} {'State':<15} {'Min':>8} {'Max':>8} {'Modal':>8} {'Date':<12}")
    click.echo("-" * 75)
    for p in results:
        click.echo(f"{p.market:<20} {p.state:<15} {p.min_price:>8.0f} {p.max_price:>8.0f} {p.modal_price:>8.0f} {p.date:<12}")
    click.echo("\n(Prices in INR per quintal)")
    click.echo(f"\n{AGRICULTURAL_DISCLAIMER}\n")


@main.command("pest")
@click.option("--symptoms", required=True, help="Comma-separated symptoms (e.g. 'yellow leaves,spots')")
@click.option("--crop", default=None, help="Crop name to filter results")
def pest(symptoms: str, crop: str | None) -> None:
    """Identify pests based on observed symptoms."""
    db = PestDatabase()
    symptom_list = [s.strip() for s in symptoms.split(",") if s.strip()]

    if crop:
        candidates = db.by_crop(crop)
        candidate_names = {p.name for p in candidates}
        results = [p for p in db.identify(symptom_list) if p.name in candidate_names]
        if not results:
            results = candidates
    else:
        results = db.identify(symptom_list)

    if not results:
        click.echo("No matching pests found. Try different symptom keywords.")
        click.echo("Common symptoms: yellowing, wilting, spots, holes, rotting, stunted growth")
        return

    click.echo(f"\nPEST IDENTIFICATION RESULTS ({len(results)} match(es)):")
    for i, pest_info in enumerate(results[:5], 1):
        click.echo(f"\n{'='*50}")
        click.echo(f"{i}. {pest_info.name}")
        click.echo(f"   Affected Crops: {', '.join(pest_info.affected_crops)}")
        click.echo(f"   Symptoms: {'; '.join(pest_info.symptoms)}")
        click.echo("   Treatment:")
        for t in pest_info.treatment:
            click.echo(f"     - {t}")
        click.echo("   Prevention:")
        for p_item in pest_info.prevention:
            click.echo(f"     - {p_item}")

    click.echo(f"\n{AGRICULTURAL_DISCLAIMER}\n")


@main.command("ask")
@click.option("--query", required=True, help="Your farming question")
@click.option("--location", default=None, help="Your location for context")
@click.option("--language", default="en", help="Language code")
def ask(query: str, location: str | None, language: str) -> None:
    """Ask a farming question and get an advisory response."""
    assistant = FarmerAssistant()
    farmer_query = FarmerQuery(query=query, language=language, location=location)
    response = assistant.respond(farmer_query)

    click.echo(f"\nADVISORY RESPONSE:")
    click.echo(f"{response.answer}")
    if response.sources:
        click.echo("\nSources:")
        for source in response.sources:
            click.echo(f"  - {source}")
    click.echo(f"\n{AGRICULTURAL_DISCLAIMER}\n")


@main.command("serve")
@click.option("--port", default=8000, help="Port to serve on")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
def serve(port: int, host: str) -> None:
    """Start the KisanMitra API server (not yet implemented)."""
    click.echo("Error: The KisanMitra API server is not yet available. The api module has not been implemented.", err=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
