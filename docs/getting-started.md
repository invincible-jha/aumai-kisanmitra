# Getting Started with aumai-kisanmitra

This guide walks you from installation to working with mandi prices, pest identification, and
farmer advisory responses in under ten minutes.

---

## Prerequisites

- **Python 3.11 or newer.** Check your version with `python --version`.
- **pip** or **uv** package manager.

No API keys, no database setup, no external services required. KisanMitra runs entirely
in-process. Live mandi prices from Agmarknet require an optional API integration
(not included in this package).

---

## Installation

### With pip

```bash
pip install aumai-kisanmitra
```

### With uv (recommended)

```bash
uv add aumai-kisanmitra
```

### For development (editable install from source)

```bash
git clone https://github.com/aumai/aumai-kisanmitra.git
cd aumai-kisanmitra
pip install -e ".[dev]"
```

### Verify the installation

```bash
kisanmitra --version
kisanmitra --help
```

You should see the version number and subcommands: `prices`, `pest`, `ask`, `serve`.

---

## Step-by-Step Tutorial

### Step 1 — Check mandi prices

The CLI ships with a sample dataset for demonstration. In production, replace the sample
data with a feed from Agmarknet (agmarknet.gov.in) or eNAM (enam.gov.in).

```bash
# All rice prices in the sample dataset
kisanmitra prices --commodity rice

# Rice prices filtered to Uttar Pradesh
kisanmitra prices --commodity rice --state UP

# Cotton prices in Maharashtra
kisanmitra prices --commodity cotton --state Maharashtra
```

The sample dataset includes: `rice`, `wheat`, `cotton`, `onion`, `potato`.

### Step 2 — Add and query prices from Python

```python
from aumai_kisanmitra.core import MandiPriceTracker
from aumai_kisanmitra.models import MandiPrice

tracker = MandiPriceTracker()

# Load price records (in production, fetch from Agmarknet API)
tracker.add_price(MandiPrice(
    commodity="wheat",
    market="Lucknow",
    state="UP",
    min_price=1950.0,
    max_price=2300.0,
    modal_price=2100.0,
    date="2026-02-27",
))
tracker.add_price(MandiPrice(
    commodity="wheat",
    market="Karnal",
    state="Haryana",
    min_price=2000.0,
    max_price=2380.0,
    modal_price=2180.0,
    date="2026-02-27",
))

# Latest prices for wheat across all states
all_wheat = tracker.get_prices("wheat")
for record in all_wheat:
    spread = record.max_price - record.min_price
    print(f"{record.market}, {record.state}: modal={record.modal_price:.0f} "
          f"(spread: {spread:.0f}) INR/quintal")

# Price trend for a single market (chronological)
trend = tracker.price_trend("wheat", "Lucknow")
for record in trend:
    print(f"{record.date}: {record.modal_price} INR/quintal")
```

### Step 3 — Identify pests from symptoms

```bash
# Broad symptom search
kisanmitra pest --symptoms "yellowing,wilting"

# With a crop filter to narrow results
kisanmitra pest --symptoms "bored bolls,circular holes,frass" --crop cotton

# Fungal disease search
kisanmitra pest --symptoms "powdery white patches,leaf drop"
```

From Python:

```python
from aumai_kisanmitra.core import PestDatabase

db = PestDatabase()

# Symptom-based identification
results = db.identify(["yellowing", "hopperburn", "wilting"])
print(f"Top match: {results[0].name}")
print(f"Treatment: {results[0].treatment[0]}")

# All pests affecting rice
rice_pests = db.by_crop("rice")
print(f"\nRice pests ({len(rice_pests)}):")
for pest in rice_pests:
    print(f"  {pest.name}")
```

### Step 4 — Ask a farming question

The `FarmerAssistant` handles natural-language queries using keyword matching across nine
advisory domains: mandi prices, pests/diseases, fertilizer, irrigation, seeds, weather,
credit, insurance, and MSP.

```bash
# Crop insurance query
kisanmitra ask --query "How do I apply for crop insurance?"

# MSP query with location context
kisanmitra ask --query "Where can I sell wheat at MSP?" --location "Karnal, Haryana"

# Weather advisory query
kisanmitra ask --query "How should I prepare my fields for monsoon flooding?"

# Seed query
kisanmitra ask --query "Where do I buy certified wheat seed?"
```

From Python:

```python
from aumai_kisanmitra.core import FarmerAssistant
from aumai_kisanmitra.models import FarmerQuery

assistant = FarmerAssistant()

query = FarmerQuery(
    query="What is the interest rate on Kisan Credit Card?",
    language="en",
    location="Pune, Maharashtra",
)

response = assistant.respond(query)
print(f"Answer: {response.answer}\n")
print("Sources:")
for source in response.sources:
    print(f"  - {source}")
print(f"\nDisclaimer: {response.disclaimer}")
```

### Step 5 — Exploring all pests in the database

```python
from aumai_kisanmitra.core import PestDatabase

db = PestDatabase()
all_pests = db.all_pests()

print(f"Total pests: {len(all_pests)}")

# Summarise by type (insects vs. fungi vs. bacteria)
for pest in all_pests:
    crops_str = ", ".join(pest.affected_crops[:3])
    if len(pest.affected_crops) > 3:
        crops_str += f" +{len(pest.affected_crops) - 3} more"
    print(f"  {pest.name:<30} Crops: {crops_str}")
```

---

## Common Patterns and Recipes

### Recipe 1 — Compare prices across multiple mandis for the same commodity

```python
from aumai_kisanmitra.core import MandiPriceTracker
from aumai_kisanmitra.models import MandiPrice

tracker = MandiPriceTracker()
today = "2026-02-27"

# Add prices from multiple markets
market_data = [
    ("rice", "Azadpur", "Delhi", 1800, 2200, 2000),
    ("rice", "Lucknow", "UP", 1750, 2100, 1950),
    ("rice", "Patna", "Bihar", 1700, 2050, 1900),
    ("rice", "Kolkata", "West Bengal", 1820, 2150, 1980),
]
for commodity, market, state, mn, mx, modal in market_data:
    tracker.add_price(MandiPrice(
        commodity=commodity, market=market, state=state,
        min_price=mn, max_price=mx, modal_price=modal, date=today
    ))

# Find the best modal price
all_rice = tracker.get_prices("rice")
best = max(all_rice, key=lambda p: p.modal_price)
worst = min(all_rice, key=lambda p: p.modal_price)

print(f"Best price: {best.market} ({best.state}) — {best.modal_price} INR/quintal")
print(f"Worst price: {worst.market} ({worst.state}) — {worst.modal_price} INR/quintal")
print(f"Price gap: {best.modal_price - worst.modal_price:.0f} INR/quintal")
```

### Recipe 2 — Build a pest alert for a specific crop and symptom set

```python
from aumai_kisanmitra.core import PestDatabase

db = PestDatabase()

# Simulate what a farmer reports via SMS
sms_text = "cotton yellow leaves sticky"
symptoms = sms_text.split()

# Get pests, then filter to cotton
all_matches = db.identify(symptoms)
cotton_pests = {p.name for p in db.by_crop("cotton")}
cotton_matches = [p for p in all_matches if p.name in cotton_pests]

if cotton_matches:
    top = cotton_matches[0]
    print(f"Most likely: {top.name}")
    print(f"First treatment step: {top.treatment[0]}")
    print(f"Preventive measure: {top.prevention[0]}")
```

### Recipe 3 — Format a response for WhatsApp delivery

```python
from aumai_kisanmitra.core import FarmerAssistant
from aumai_kisanmitra.models import FarmerQuery

assistant = FarmerAssistant()

def format_whatsapp_reply(query_text: str, location: str | None = None) -> str:
    """Format a farmer response for WhatsApp character limits."""
    query = FarmerQuery(query=query_text, location=location)
    response = assistant.respond(query)

    # WhatsApp message: answer + sources in compact form
    sources_text = "\n".join(f"• {s}" for s in response.sources)
    return f"{response.answer}\n\n*Sources:*\n{sources_text}"

msg = format_whatsapp_reply(
    "How do I enrol for PMFBY insurance?",
    location="Nagpur, Maharashtra",
)
print(msg)
```

### Recipe 4 — Run a batch of farmer queries and summarise topic coverage

```python
from aumai_kisanmitra.core import FarmerAssistant
from aumai_kisanmitra.models import FarmerQuery

assistant = FarmerAssistant()

sample_queries = [
    "What is the onion price in Nashik today?",
    "My sugarcane has white cottony masses on the stems",
    "How to apply for KCC loan?",
    "Will it rain this week in Bihar?",
    "Where to get certified paddy seed?",
    "What is the MSP for soybean?",
    "How to reduce irrigation costs with drip system?",
]

for query_text in sample_queries:
    response = assistant.respond(FarmerQuery(query=query_text))
    first_sentence = response.answer.split(".")[0] + "."
    print(f"Q: {query_text[:50]}")
    print(f"A: {first_sentence}")
    print()
```

### Recipe 5 — Integrate with aumai-climatewatch for weather queries

```python
from aumai_kisanmitra.core import FarmerAssistant
from aumai_kisanmitra.models import FarmerQuery, FarmerResponse

# Requires: pip install aumai-climatewatch
from aumai_climatewatch.core import ClimateZoneRegistry, AlertGenerator

registry = ClimateZoneRegistry()
generator = AlertGenerator()
assistant = FarmerAssistant()

def enhanced_respond(query_text: str, state: str | None = None) -> FarmerResponse:
    """Enhance weather queries with actual ClimateWatch alerts."""
    query = FarmerQuery(query=query_text, location=state)
    response = assistant.respond(query)

    # If this is a weather query and we have a state, inject real alerts
    weather_keywords = ["weather", "rain", "flood", "drought", "heat"]
    is_weather = any(kw in query_text.lower() for kw in weather_keywords)

    if is_weather and state:
        zones = registry.zones_for_state(state)
        if zones:
            zone = zones[0]
            # Use zone normal conditions as a proxy observation
            obs = {"temperature_c": zone.avg_temp_c + 3, "rainfall_mm": 5.0,
                   "humidity_pct": 60.0, "wind_kmh": 15.0, "rainfall_deficit_pct": 0.0}
            alerts = generator.evaluate_conditions(zone, obs)
            if alerts:
                alert_text = " | ".join(a.message[:80] for a in alerts)
                response.answer += f"\n\nCurrent alerts: {alert_text}"

    return response

result = enhanced_respond("Will there be floods this week?", state="Bihar")
print(result.answer)
```

---

## Troubleshooting FAQ

**Q: `kisanmitra prices` shows "No price data found for commodity X".**

The built-in sample dataset only contains: `rice`, `wheat`, `cotton`, `onion`, `potato`.
For other commodities, add records manually via `MandiPriceTracker.add_price()` or integrate
with the Agmarknet API.

---

**Q: `kisanmitra pest` shows no results for my symptoms.**

Try more generic symptom keywords. The matcher looks for substring overlaps, so `"yellow"`
matches `"yellowing"` and `"yellow leaves"`. If still no result, use `--symptoms "yellowing"` as
a broad starting point and filter with `--crop` to narrow results.

---

**Q: The `FarmerAssistant` always returns the generic fallback response.**

The assistant uses keyword matching. Ensure your query contains at least one keyword from a
supported category. For example, queries about pesticides will not match — use `"pest"`,
`"insect"`, `"disease"`, or `"fungus"` instead.

Supported keyword categories and example triggers:

| Category   | Example keywords            |
|------------|-----------------------------|
| Price      | price, mandi, rate, sell    |
| Pest       | pest, insect, disease, bug  |
| Fertilizer | fertilizer, urea, dap, npk  |
| Irrigation | irrigation, water, drip     |
| Seed       | seed, variety, hybrid       |
| Weather    | weather, rain, flood        |
| Loan       | loan, credit, kcc, finance  |
| Insurance  | insurance, fasal bima, pmfby|
| MSP        | msp, minimum support price  |

---

**Q: `MandiPrice` raises a `ValidationError` on min_price or max_price.**

Both `min_price` and `max_price` must be `>= 0.0`. Ensure prices are in INR per quintal as
non-negative floats.

---

**Q: How do I handle queries in Hindi?**

Pass `language="hi"` in `FarmerQuery`. The `language` field is stored and returned in
`FarmerResponse` for your application to use for translation, but KisanMitra's built-in
responses are in English. Wrap the response text in a translation service (e.g., Google
Translate API) for regional language delivery.

---

**Q: Can I add my own advisory topics to `FarmerAssistant`?**

Yes. Subclass `FarmerAssistant` and override `respond()`, or modify the `_KEYWORD_RESPONSES`
list in `core.py` before instantiation. Each entry in `_KEYWORD_RESPONSES` is a tuple of
`(keywords: list[str], answer: str, sources: list[str])`.

---

**Q: `kisanmitra serve` exits immediately with an error.**

The API server module is not implemented in v0.1.0. This subcommand will be implemented in a
future release. Use the Python API or CLI directly in the meantime.

---

## Next Steps

- Read the [API Reference](api-reference.md) for complete class and method signatures.
- Explore the [examples/quickstart.py](../examples/quickstart.py) for runnable demo code.
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to add pests, government schemes, or language support.
- For crop-specific soil and fertilizer guidance, install [aumai-farmbrain](https://github.com/aumai/aumai-farmbrain).
- For climate and flood/drought alerts, install [aumai-climatewatch](https://github.com/aumai/aumai-climatewatch).
