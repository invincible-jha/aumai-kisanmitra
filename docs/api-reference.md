# API Reference — aumai-kisanmitra

Complete reference for all public classes, functions, and Pydantic models in the
`aumai_kisanmitra` package. All classes and functions are typed; the package requires
Python 3.11+ and uses strict mypy mode.

---

## Module: `aumai_kisanmitra.models`

Pydantic v2 models used as input and output at all API boundaries.

---

### `AGRICULTURAL_DISCLAIMER`

```python
AGRICULTURAL_DISCLAIMER: str
```

Mandatory disclaimer string included in all `FarmerResponse` outputs and CLI output:

> *"This tool does not replace professional agronomic advice. Verify mandi prices with
> official AGMARKNET sources. Pest identification results must be confirmed by local
> agricultural extension officers."*

---

### `MandiPrice`

```python
class MandiPrice(BaseModel):
    commodity: str
    market: str
    state: str
    min_price: float
    max_price: float
    modal_price: float
    date: str
```

A mandi (agricultural market) price record for a commodity on a specific date.

**Fields:**

| Field         | Type    | Constraints | Description |
|---------------|---------|-------------|-------------|
| `commodity`   | `str`   | required    | Name of the agricultural commodity (e.g., `"rice"`, `"wheat"`) |
| `market`      | `str`   | required    | Name of the mandi/market (e.g., `"Azadpur"`, `"Nashik"`) |
| `state`       | `str`   | required    | State where the mandi is located (e.g., `"Delhi"`, `"Maharashtra"`) |
| `min_price`   | `float` | `>= 0.0`    | Minimum price in INR per quintal |
| `max_price`   | `float` | `>= 0.0`    | Maximum price in INR per quintal |
| `modal_price` | `float` | `>= 0.0`    | Modal (most common/frequent) price in INR per quintal |
| `date`        | `str`   | required    | Date of price record in `YYYY-MM-DD` format |

**Example:**

```python
from aumai_kisanmitra.models import MandiPrice

price = MandiPrice(
    commodity="wheat",
    market="Karnal",
    state="Haryana",
    min_price=2000.0,
    max_price=2380.0,
    modal_price=2180.0,
    date="2026-02-27",
)
```

---

### `PestInfo`

```python
class PestInfo(BaseModel):
    name: str
    affected_crops: list[str]
    symptoms: list[str]
    treatment: list[str]
    prevention: list[str]
```

Information about an agricultural pest or disease in India's farming context.

**Fields:**

| Field            | Type        | Description |
|------------------|-------------|-------------|
| `name`           | `str`       | Common name of the pest or disease |
| `affected_crops` | `list[str]` | Crops affected by this pest |
| `symptoms`       | `list[str]` | Observable symptoms of infestation |
| `treatment`      | `list[str]` | Recommended chemical or biological treatment measures |
| `prevention`     | `list[str]` | Preventive measures to avoid infestation |

**Example:**

```python
from aumai_kisanmitra.models import PestInfo

pest = PestInfo(
    name="Aphids",
    affected_crops=["Wheat", "Cotton", "Mustard"],
    symptoms=["curling leaves", "yellowing", "sticky honeydew"],
    treatment=["Spray dimethoate 30 EC @ 500 ml/ha", "Neem oil spray 5%"],
    prevention=["Encourage natural predators", "Remove weeds"],
)
```

---

### `FarmerQuery`

```python
class FarmerQuery(BaseModel):
    query: str
    language: str = "en"
    location: str | None = None
```

A query submitted by a farmer, optionally with location context and language code.

**Fields:**

| Field      | Type           | Default  | Description |
|------------|----------------|----------|-------------|
| `query`    | `str`          | required | The farmer's question or concern |
| `language` | `str`          | `"en"`   | BCP-47 language code for the query (e.g., `"en"`, `"hi"`, `"mr"`) |
| `location` | `str` or `None`| `None`   | Farmer's location for context (e.g., `"Nagpur, Maharashtra"`) |

**Example:**

```python
from aumai_kisanmitra.models import FarmerQuery

query = FarmerQuery(
    query="How to apply for Kisan Credit Card?",
    language="en",
    location="Amravati, Maharashtra",
)
```

---

### `FarmerResponse`

```python
class FarmerResponse(BaseModel):
    answer: str
    sources: list[str] = []
    language: str = "en"
    disclaimer: str = AGRICULTURAL_DISCLAIMER
```

Response to a farmer query with advisory text, source references, and a disclaimer.

**Fields:**

| Field        | Type        | Default                 | Description |
|--------------|-------------|-------------------------|-------------|
| `answer`     | `str`       | required                | The advisory response text |
| `sources`    | `list[str]` | `[]`                    | Sources or references supporting the answer |
| `language`   | `str`       | `"en"`                  | Language code carried through from the query |
| `disclaimer` | `str`       | `AGRICULTURAL_DISCLAIMER` | Mandatory agricultural disclaimer |

**Example:**

```python
print(response.answer)
for source in response.sources:
    print(f"  Source: {source}")
print(response.disclaimer)
```

---

## Module: `aumai_kisanmitra.core`

The core engine. Contains three classes: `MandiPriceTracker`, `PestDatabase`, and
`FarmerAssistant`.

---

### `MandiPriceTracker`

```python
class MandiPriceTracker:
    def __init__(self) -> None: ...
    def add_price(self, price: MandiPrice) -> None: ...
    def get_prices(self, commodity: str, state: str | None = None) -> list[MandiPrice]: ...
    def price_trend(self, commodity: str, market: str) -> list[MandiPrice]: ...
    def all_prices(self) -> list[MandiPrice]: ...
```

In-memory store for mandi commodity prices with query and trend analysis utilities. Designed
to be populated from an Agmarknet or eNAM API feed and then queried by commodity and state.

---

#### `MandiPriceTracker.__init__`

```python
def __init__(self) -> None
```

Initialises an empty price store. No pre-loaded data.

---

#### `MandiPriceTracker.add_price`

```python
def add_price(self, price: MandiPrice) -> None
```

Add a mandi price record to the tracker.

**Parameters:**

| Parameter | Type         | Description |
|-----------|--------------|-------------|
| `price`   | `MandiPrice` | A validated price record to add |

**Example:**

```python
from aumai_kisanmitra.models import MandiPrice

tracker.add_price(MandiPrice(
    commodity="onion", market="Nashik", state="Maharashtra",
    min_price=1200.0, max_price=2000.0, modal_price=1600.0, date="2026-02-27"
))
```

---

#### `MandiPriceTracker.get_prices`

```python
def get_prices(self, commodity: str, state: str | None = None) -> list[MandiPrice]
```

Return all price records for a commodity, optionally filtered by state. Results are sorted by
date descending (most recent first).

**Parameters:**

| Parameter   | Type           | Description |
|-------------|----------------|-------------|
| `commodity` | `str`          | Commodity name; case-insensitive |
| `state`     | `str` or `None`| Optional state filter; case-insensitive |

**Returns:** `list[MandiPrice]` — matching records sorted newest first; empty if none found.

**Example:**

```python
all_rice = tracker.get_prices("rice")
up_rice = tracker.get_prices("rice", state="UP")
```

---

#### `MandiPriceTracker.price_trend`

```python
def price_trend(self, commodity: str, market: str) -> list[MandiPrice]
```

Return chronological price records for a commodity at a specific market. Results are sorted by
date ascending for trend analysis.

**Parameters:**

| Parameter   | Type  | Description |
|-------------|-------|-------------|
| `commodity` | `str` | Commodity name; case-insensitive |
| `market`    | `str` | Market/mandi name; case-insensitive |

**Returns:** `list[MandiPrice]` — records for this commodity and market, oldest first.

**Example:**

```python
trend = tracker.price_trend("wheat", "Azadpur")
for record in trend:
    print(f"{record.date}: {record.modal_price} INR/quintal")
```

---

#### `MandiPriceTracker.all_prices`

```python
def all_prices(self) -> list[MandiPrice]
```

Return all stored price records in insertion order.

**Returns:** `list[MandiPrice]`

---

### `PestDatabase`

```python
class PestDatabase:
    def __init__(self) -> None: ...
    def all_pests(self) -> list[PestInfo]: ...
    def identify(self, symptoms: list[str]) -> list[PestInfo]: ...
    def by_crop(self, crop_name: str) -> list[PestInfo]: ...
```

Repository of Indian agricultural pests and diseases with symptom-based identification.

The built-in database contains 30+ entries covering:
- **Insects:** Brown Plant Hopper, Aphids, Stem Borer, Whitefly, Thrips, Red Spider Mite,
  Mealy Bug, Helicoverpa (Bollworm), Cutworm, Leaf Folder, Jassid, Caterpillar (Army Worm),
  Fall Armyworm, Diamond Back Moth, Pod Borer, White Grub, Mango Hopper, Coconut Mite.
- **Fungi/Diseases:** Powdery Mildew, Rice Blast, Late Blight, Yellow Rust, Leaf Blight,
  Downy Mildew, Rust (Groundnut), Collar Rot.
- **Bacteria:** Bacterial Wilt.
- **Nematodes:** Root Knot Nematodes.
- **Scales and mites:** Scales (fruit crops).

---

#### `PestDatabase.__init__`

```python
def __init__(self) -> None
```

Initialises the pest database from the static built-in catalogue.

---

#### `PestDatabase.all_pests`

```python
def all_pests(self) -> list[PestInfo]
```

Return all pests in the database.

**Returns:** `list[PestInfo]` — all 30+ pests in insertion order.

---

#### `PestDatabase.identify`

```python
def identify(self, symptoms: list[str]) -> list[PestInfo]
```

Return pests whose recorded symptom set overlaps with the provided symptom keywords. Results
are ranked by overlap score (highest first). A score of zero means no overlap.

**Algorithm:** For each pest, the method counts how many of the provided symptoms appear as
substrings in any of the pest's recorded symptoms (case-insensitive). Pests with zero overlap
are excluded.

**Parameters:**

| Parameter  | Type        | Description |
|------------|-------------|-------------|
| `symptoms` | `list[str]` | List of observed symptom keywords or phrases |

**Returns:** `list[PestInfo]` — matching pests sorted by descending overlap score.

**Example:**

```python
results = db.identify(["yellowing", "hopperburn", "wilting"])
if results:
    print(f"Most likely pest: {results[0].name}")
    print(f"Treatment: {results[0].treatment[0]}")
```

---

#### `PestDatabase.by_crop`

```python
def by_crop(self, crop_name: str) -> list[PestInfo]
```

Return all pests affecting a specific crop. Case-insensitive exact match on
`PestInfo.affected_crops`.

**Parameters:**

| Parameter   | Type  | Description |
|-------------|-------|-------------|
| `crop_name` | `str` | Crop name, e.g., `"Rice"`, `"Cotton"` |

**Returns:** `list[PestInfo]` — pests known to affect this crop.

**Example:**

```python
rice_pests = db.by_crop("rice")
cotton_pests = db.by_crop("Cotton")  # case-insensitive
```

---

### `FarmerAssistant`

```python
class FarmerAssistant:
    def respond(self, query: FarmerQuery) -> FarmerResponse: ...
```

Rule-based assistant that maps farmer queries to curated advisory responses using keyword
matching. No network calls or LLM inference — works offline within SMS gateway latency.

**Advisory categories and trigger keywords:**

| Category   | Keywords |
|------------|----------|
| Price/mandi | `price`, `mandi`, `rate`, `sell`, `market` |
| Pest/disease | `pest`, `insect`, `bug`, `disease`, `fungus`, `infection` |
| Fertilizer | `fertilizer`, `urea`, `dap`, `npk`, `manure`, `compost` |
| Irrigation | `irrigation`, `water`, `drip`, `sprinkler`, `rain` |
| Seed | `seed`, `variety`, `sow`, `hybrid`, `certified` |
| Weather | `weather`, `rain`, `flood`, `drought`, `forecast` |
| Loan/credit | `loan`, `credit`, `kcc`, `finance`, `money` |
| Insurance | `insurance`, `fasal bima`, `pradhan mantri` |
| MSP | `msp`, `minimum support price`, `procurement` |

---

#### `FarmerAssistant.respond`

```python
def respond(self, query: FarmerQuery) -> FarmerResponse
```

Return an advisory response to the farmer's query by scoring keyword matches against all
categories and selecting the highest-scoring category's pre-written answer.

If the query scores zero on all categories, a generic fallback response is returned directing
the farmer to call the Kisan Call Centre (1800-180-1551) or use the Kisan Suvidha App.

If `query.location` is set, the answer is extended with advice to contact the local Block
Agriculture Officer or KVK.

**Parameters:**

| Parameter | Type          | Description |
|-----------|---------------|-------------|
| `query`   | `FarmerQuery` | The farmer's query with optional location and language |

**Returns:** `FarmerResponse` — answer text, sources list, language, and disclaimer.

**Example:**

```python
from aumai_kisanmitra.core import FarmerAssistant
from aumai_kisanmitra.models import FarmerQuery

assistant = FarmerAssistant()
response = assistant.respond(FarmerQuery(
    query="What is the MSP for wheat this year?",
    location="Karnal, Haryana",
))
print(response.answer)
```

---

## Module: `aumai_kisanmitra.cli`

CLI entry point registered as the `kisanmitra` console script.

### `main`

The Click group. Invoke with `kisanmitra --help`.

### `prices(commodity, state)`

Click command. Loads a built-in sample dataset, calls `MandiPriceTracker.get_prices()`,
and prints a tabular result to stdout.

### `pest(symptoms, crop)`

Click command. Parses comma-separated symptoms, calls `PestDatabase.identify()`, optionally
filters results by `PestDatabase.by_crop()`, and prints the top 5 matches.

### `ask(query, location, language)`

Click command. Constructs a `FarmerQuery` and calls `FarmerAssistant.respond()`.

### `serve(port, host)`

Click command. Not implemented in v0.1.0. Exits with error.

---

## Module: `aumai_kisanmitra`

### `__version__`

```python
__version__: str  # "0.1.0"
```

Package version string. Access via `aumai_kisanmitra.__version__` or `kisanmitra --version`.
