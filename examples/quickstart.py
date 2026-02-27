"""aumai-kisanmitra quickstart — farmer mobile assistant demonstrations.

DISCLAIMER: Verify all recommendations with local agricultural experts.
This tool does not replace professional agronomic advice. Mandi prices
must be verified with official AGMARKNET sources. Pest identification
results must be confirmed by local agricultural extension officers.

This file demonstrates:
  1. Adding and querying mandi commodity prices via MandiPriceTracker.
  2. Retrieving a price trend at a specific mandi over time.
  3. Identifying pests from observed field symptoms via PestDatabase.
  4. Querying all pests affecting a specific crop.
  5. Submitting farmer queries to FarmerAssistant for advisory responses.

Run directly:
    python examples/quickstart.py

Install first:
    pip install aumai-kisanmitra
"""

from __future__ import annotations

from aumai_kisanmitra.core import FarmerAssistant, MandiPriceTracker, PestDatabase
from aumai_kisanmitra.models import (
    AGRICULTURAL_DISCLAIMER,
    FarmerQuery,
    MandiPrice,
)


# ---------------------------------------------------------------------------
# Demo 1: Loading mandi prices and filtering by commodity + state
# ---------------------------------------------------------------------------

def demo_mandi_price_query() -> None:
    """Populate MandiPriceTracker with sample records and query by commodity.

    MandiPrice records use INR per quintal (100 kg).  min_price, max_price,
    and modal_price mirror the three-price format published by AGMARKNET.
    """
    print("\n--- Demo 1: Mandi Price Query ---")

    tracker = MandiPriceTracker()

    records = [
        MandiPrice(
            commodity="Wheat",
            market="Azadpur",
            state="Delhi",
            min_price=2050.0,
            max_price=2200.0,
            modal_price=2120.0,
            date="2026-02-20",
        ),
        MandiPrice(
            commodity="Wheat",
            market="Khanna",
            state="Punjab",
            min_price=2100.0,
            max_price=2250.0,
            modal_price=2180.0,
            date="2026-02-21",
        ),
        MandiPrice(
            commodity="Wheat",
            market="Indore",
            state="Madhya Pradesh",
            min_price=1980.0,
            max_price=2100.0,
            modal_price=2040.0,
            date="2026-02-21",
        ),
        MandiPrice(
            commodity="Rice",
            market="Karnal",
            state="Haryana",
            min_price=1800.0,
            max_price=1950.0,
            modal_price=1880.0,
            date="2026-02-21",
        ),
    ]

    for record in records:
        tracker.add_price(record)

    # Query wheat prices across all states (returned newest-first).
    all_wheat = tracker.get_prices("Wheat")
    print(f"  Wheat records (all states): {len(all_wheat)}")
    for price in all_wheat:
        print(
            f"    {price.market}, {price.state}: "
            f"modal=Rs {price.modal_price}/quintal  ({price.date})"
        )

    # Narrow to Punjab only.
    punjab_wheat = tracker.get_prices("Wheat", state="Punjab")
    print(f"\n  Wheat in Punjab: {len(punjab_wheat)} record(s)")
    if punjab_wheat:
        best = punjab_wheat[0]
        print(f"    Latest: {best.market} — Rs {best.modal_price}/quintal")


# ---------------------------------------------------------------------------
# Demo 2: Price trend at a specific mandi
# ---------------------------------------------------------------------------

def demo_price_trend() -> None:
    """Show price movement at a single mandi across multiple dates.

    price_trend() returns records in chronological order (oldest first),
    making it straightforward to compute day-over-day changes or plot a
    time series for a decision-support dashboard.
    """
    print("\n--- Demo 2: Price Trend at Khanna Mandi ---")

    tracker = MandiPriceTracker()

    daily_data = [
        ("2026-02-17", 2080.0, 2150.0, 2110.0),
        ("2026-02-18", 2090.0, 2160.0, 2125.0),
        ("2026-02-19", 2075.0, 2140.0, 2100.0),
        ("2026-02-20", 2100.0, 2200.0, 2155.0),
        ("2026-02-21", 2100.0, 2250.0, 2180.0),
    ]

    for date, min_price, max_price, modal_price in daily_data:
        tracker.add_price(MandiPrice(
            commodity="Wheat",
            market="Khanna",
            state="Punjab",
            min_price=min_price,
            max_price=max_price,
            modal_price=modal_price,
            date=date,
        ))

    trend = tracker.price_trend("Wheat", "Khanna")
    print(f"  {'Date':<12} {'Min':>8} {'Modal':>8} {'Max':>8}  (INR/quintal)")
    print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8}")
    for price in trend:
        print(
            f"  {price.date:<12} "
            f"{price.min_price:>8.0f} "
            f"{price.modal_price:>8.0f} "
            f"{price.max_price:>8.0f}"
        )


# ---------------------------------------------------------------------------
# Demo 3: Pest identification from field symptoms
# ---------------------------------------------------------------------------

def demo_pest_identification() -> None:
    """Identify likely pests from symptoms observed in the field.

    PestDatabase.identify() scores each pest by the number of symptom
    keywords that overlap with the observed set, then returns results ranked
    by score.  Verify top matches with your local KVK or agriculture officer.
    """
    print("\n--- Demo 3: Pest Identification by Symptom ---")

    db = PestDatabase()

    # Symptoms reported by a rice farmer.
    observed_symptoms = ["yellowing", "wilting", "hopperburn"]
    matches = db.identify(observed_symptoms)

    print(f"  Observed symptoms: {observed_symptoms}")
    print(f"  Top {min(3, len(matches))} matching pests:")
    for pest in matches[:3]:
        print(f"\n    Pest     : {pest.name}")
        print(f"    Crops    : {', '.join(pest.affected_crops)}")
        print(f"    Treatment: {pest.treatment[0]}")
        print(f"    Prevention: {pest.prevention[0]}")

    print(f"\n  {AGRICULTURAL_DISCLAIMER}")


# ---------------------------------------------------------------------------
# Demo 4: All pests for a given crop
# ---------------------------------------------------------------------------

def demo_pests_by_crop() -> None:
    """List every pest in the database that affects a given crop.

    Use this to generate crop-specific pest management schedules or to
    populate training data for a crop-advisory chatbot.
    """
    print("\n--- Demo 4: Pests Affecting Cotton ---")

    db = PestDatabase()
    cotton_pests = db.by_crop("Cotton")

    print(f"  {len(cotton_pests)} pests found for Cotton:")
    for pest in cotton_pests:
        symptom_count = f"({len(pest.symptoms)} symptoms known)"
        print(f"    - {pest.name} {symptom_count}")


# ---------------------------------------------------------------------------
# Demo 5: Farmer advisory assistant
# ---------------------------------------------------------------------------

def demo_farmer_assistant() -> None:
    """Submit natural-language queries to FarmerAssistant and display responses.

    FarmerAssistant uses keyword matching to route queries to curated
    advisory responses with source references.  An optional location field
    appends a localised follow-up suggestion pointing to the nearest KVK.
    """
    print("\n--- Demo 5: Farmer Advisory Assistant ---")

    assistant = FarmerAssistant()

    queries = [
        FarmerQuery(
            query="What is the current mandi rate for wheat?",
            language="en",
            location="Punjab",
        ),
        FarmerQuery(
            query="My cotton crop has white cottony masses and yellowing leaves.",
            language="en",
            location="Vidarbha, Maharashtra",
        ),
        FarmerQuery(
            query="How can I apply for a Kisan Credit Card?",
            language="en",
        ),
    ]

    for farmer_query in queries:
        response = assistant.respond(farmer_query)
        print(f"\n  Query   : {farmer_query.query}")
        print(f"  Answer  : {response.answer[:160]}...")
        print(f"  Sources : {', '.join(response.sources)}")

    print(f"\n  Disclaimer: {AGRICULTURAL_DISCLAIMER}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all five kisanmitra quickstart demonstrations."""
    print("=" * 60)
    print("aumai-kisanmitra quickstart")
    print("Farmer mobile assistant — mandi prices, pest ID, advisory")
    print("=" * 60)

    demo_mandi_price_query()
    demo_price_trend()
    demo_pest_identification()
    demo_pests_by_crop()
    demo_farmer_assistant()

    print("\nDone.")


if __name__ == "__main__":
    main()
