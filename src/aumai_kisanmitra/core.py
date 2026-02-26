"""Core logic for aumai-kisanmitra: mandi prices, pest database, farmer assistant."""

from __future__ import annotations

from collections import defaultdict

from .models import (
    AGRICULTURAL_DISCLAIMER,
    FarmerQuery,
    FarmerResponse,
    MandiPrice,
    PestInfo,
)

__all__ = ["MandiPriceTracker", "PestDatabase", "FarmerAssistant"]

# ---------------------------------------------------------------------------
# Static pest catalogue — 30+ common Indian agricultural pests
# ---------------------------------------------------------------------------

_RAW_PESTS: list[dict[str, object]] = [
    {
        "name": "Brown Plant Hopper",
        "affected_crops": ["Rice"],
        "symptoms": ["yellowing", "wilting", "hopperburn", "lodging"],
        "treatment": ["Apply imidacloprid 17.8 SL @ 125 ml/ha", "Drain field for 3-4 days", "Apply BPMC 50 EC"],
        "prevention": ["Use resistant varieties", "Avoid excessive nitrogen", "Maintain field drainage"],
    },
    {
        "name": "Aphids",
        "affected_crops": ["Wheat", "Mustard", "Cotton", "Okra", "Groundnut"],
        "symptoms": ["curling leaves", "yellowing", "sticky honeydew", "stunted growth", "sooty mould"],
        "treatment": ["Spray dimethoate 30 EC @ 500 ml/ha", "Apply imidacloprid 17.8 SL @ 75 ml/ha", "Neem oil spray 5%"],
        "prevention": ["Encourage natural predators (ladybird beetles)", "Avoid dense planting", "Remove weeds"],
    },
    {
        "name": "Stem Borer",
        "affected_crops": ["Rice", "Maize", "Sugarcane", "Sorghum"],
        "symptoms": ["dead heart", "white ear", "borer entry holes", "frass", "stem tunnelling"],
        "treatment": ["Apply carbofuran 3G @ 20 kg/ha", "Release Trichogramma parasitoids", "Chlorpyrifos 20 EC"],
        "prevention": ["Use light traps", "Destroy stubbles after harvest", "Balanced nitrogen application"],
    },
    {
        "name": "Whitefly",
        "affected_crops": ["Cotton", "Tomato", "Brinjal", "Chilli", "Cucurbits"],
        "symptoms": ["yellowing", "silver streaks", "sticky leaves", "sooty mould", "virus transmission"],
        "treatment": ["Thiamethoxam 25 WG @ 100 g/ha", "Yellow sticky traps", "Neem seed kernel extract 5%"],
        "prevention": ["Intercropping with marigold", "Remove infected plants", "Avoid over-irrigation"],
    },
    {
        "name": "Thrips",
        "affected_crops": ["Chilli", "Cotton", "Onion", "Groundnut"],
        "symptoms": ["silver streaks on leaves", "upward curling", "scarring", "bronzing"],
        "treatment": ["Spinosad 45 SC @ 100 ml/ha", "Fipronil 5 SC @ 600 ml/ha"],
        "prevention": ["Blue sticky traps", "Avoid planting near maize", "Reflective mulch"],
    },
    {
        "name": "Red Spider Mite",
        "affected_crops": ["Cotton", "Brinjal", "Okra", "Beans", "Maize"],
        "symptoms": ["bronze speckling", "webbing", "leaf drop", "yellowing"],
        "treatment": ["Dicofol 18.5 EC @ 1.5 l/ha", "Sulphur 80 WP @ 2.5 kg/ha", "Abamectin 1.8 EC"],
        "prevention": ["Overhead irrigation reduces mites", "Avoid dusty conditions", "Predatory mites"],
    },
    {
        "name": "Mealy Bug",
        "affected_crops": ["Cotton", "Grapes", "Pomegranate", "Papaya"],
        "symptoms": ["white cottony masses", "yellowing", "stunted growth", "sooty mould"],
        "treatment": ["Profenofos 50 EC @ 1 l/ha", "Spray ethion 50 EC", "Release Cryptolaemus predators"],
        "prevention": ["Destroy crop debris", "Ant management", "Avoid excess nitrogen"],
    },
    {
        "name": "Helicoverpa (Bollworm)",
        "affected_crops": ["Cotton", "Tomato", "Chickpea", "Pigeonpea", "Maize"],
        "symptoms": ["bored bolls/pods/fruit", "circular entry holes", "larval frass", "premature boll/pod drop"],
        "treatment": ["Spinosad 45 SC @ 150 ml/ha", "Bt spray 750 g/ha", "Emamectin benzoate 5 SG"],
        "prevention": ["Pheromone traps (5/ha)", "Use Bt cotton varieties", "Intercrop with sorghum"],
    },
    {
        "name": "Cutworm",
        "affected_crops": ["Wheat", "Maize", "Vegetables", "Cotton"],
        "symptoms": ["cut seedlings at ground level", "wilting", "night feeding"],
        "treatment": ["Chlorpyrifos 20 EC @ 2.5 l/ha soil drench", "Poison bait (bran + chlorpyrifos)"],
        "prevention": ["Deep ploughing in summer", "Remove weeds", "Flood irrigation before planting"],
    },
    {
        "name": "Leaf Folder",
        "affected_crops": ["Rice"],
        "symptoms": ["longitudinal folded leaves", "white leaf streaks", "feeding damage"],
        "treatment": ["Chlorpyrifos 20 EC @ 1.5 l/ha", "Monocrotophos 36 WSC @ 750 ml/ha"],
        "prevention": ["Balanced fertilisation", "Avoid dense planting", "Light traps"],
    },
    {
        "name": "Jassid (Leafhopper)",
        "affected_crops": ["Cotton", "Groundnut", "Okra", "Brinjal"],
        "symptoms": ["yellowing from leaf margins", "leaf curl downward", "burning appearance"],
        "treatment": ["Imidacloprid 70 WG @ 35 g/ha", "Thiamethoxam 25 WG @ 80 g/ha"],
        "prevention": ["Hairy-leaved varieties", "Avoid close planting", "Yellow sticky traps"],
    },
    {
        "name": "Powdery Mildew",
        "affected_crops": ["Wheat", "Grapes", "Cucurbits", "Pea", "Mustard"],
        "symptoms": ["white powdery patches", "yellowing below", "premature leaf drop", "stunted growth"],
        "treatment": ["Sulphur 80 WP @ 2.5 kg/ha", "Propiconazole 25 EC @ 500 ml/ha", "Hexaconazole 5 EC"],
        "prevention": ["Resistant varieties", "Avoid overhead irrigation", "Proper plant spacing"],
    },
    {
        "name": "Blast (Rice Blast)",
        "affected_crops": ["Rice"],
        "symptoms": ["diamond-shaped lesions", "eye-shaped spots", "neck rot", "panicle blast"],
        "treatment": ["Tricyclazole 75 WP @ 300 g/ha", "Isoprothiolane 40 EC @ 750 ml/ha"],
        "prevention": ["Balanced nitrogen", "Resistant varieties", "Silicon application"],
    },
    {
        "name": "Late Blight",
        "affected_crops": ["Potato", "Tomato"],
        "symptoms": ["water-soaked lesions", "white mouldy growth", "rapid wilting", "brown rotting tubers"],
        "treatment": ["Metalaxyl + Mancozeb 72 WP @ 2 kg/ha", "Cymoxanil + Mancozeb"],
        "prevention": ["Certified disease-free seed", "Avoid over-irrigation", "Copper fungicides preventively"],
    },
    {
        "name": "Yellow Rust",
        "affected_crops": ["Wheat", "Barley"],
        "symptoms": ["yellow stripe pustules", "yellow powder on leaves", "stunted growth"],
        "treatment": ["Propiconazole 25 EC @ 500 ml/ha", "Tebuconazole 250 EW @ 750 ml/ha"],
        "prevention": ["Resistant varieties", "Early sowing", "Balanced nutrition"],
    },
    {
        "name": "Leaf Blight",
        "affected_crops": ["Rice", "Maize", "Wheat"],
        "symptoms": ["water-soaked lesions turning brown", "leaf blighting", "straw-coloured patches"],
        "treatment": ["Validamycin 3 L @ 2 l/ha", "Copper oxychloride 50 WP @ 3 kg/ha"],
        "prevention": ["Balanced NPK", "Proper drainage", "Resistant varieties"],
    },
    {
        "name": "Fruit Borer",
        "affected_crops": ["Brinjal", "Tomato", "Chilli"],
        "symptoms": ["bored fruits", "dropping fruits", "larval frass at entry"],
        "treatment": ["Emamectin benzoate 5 SG @ 220 g/ha", "Spinosad 45 SC @ 100 ml/ha"],
        "prevention": ["Pheromone traps", "Remove damaged fruits", "Inter-cropping"],
    },
    {
        "name": "Nematodes (Root Knot)",
        "affected_crops": ["Tomato", "Brinjal", "Groundnut", "Banana", "Cucurbits"],
        "symptoms": ["root galls/knots", "stunting", "yellowing", "poor yield", "wilting"],
        "treatment": ["Carbofuran 3G @ 1 kg ai/ha", "Phorate 10G @ 1 kg ai/ha", "Biocontrol with Paecilomyces"],
        "prevention": ["Crop rotation with cereals", "Marigold inter-cropping", "Soil solarisation"],
    },
    {
        "name": "Downy Mildew",
        "affected_crops": ["Maize", "Pearl Millet", "Grapes", "Cucurbits"],
        "symptoms": ["downy white growth on underside", "chlorotic patches", "downcurled leaves"],
        "treatment": ["Metalaxyl 8% + Mancozeb 64% WP @ 2.5 kg/ha", "Fosetyl-Al 80 WP"],
        "prevention": ["Seed treatment with metalaxyl", "Avoid overhead irrigation", "Resistant varieties"],
    },
    {
        "name": "Bacterial Wilt",
        "affected_crops": ["Tomato", "Brinjal", "Pepper", "Potato"],
        "symptoms": ["sudden wilting", "vascular browning", "bacterial ooze in water test"],
        "treatment": ["No effective chemical cure; remove and destroy infected plants", "Streptomycin sulphate as preventive"],
        "prevention": ["Resistant varieties", "Soil sterilisation", "Crop rotation", "Avoid wounding roots"],
    },
    {
        "name": "Caterpillar (Army Worm)",
        "affected_crops": ["Maize", "Sorghum", "Rice", "Wheat"],
        "symptoms": ["ragged leaf feeding", "defoliation", "windowpane feeding", "frass"],
        "treatment": ["Chlorpyrifos 20 EC @ 2.5 l/ha", "Emamectin benzoate 5 SG", "Spinetoram 11.7 SC"],
        "prevention": ["Light traps", "Birds on field", "Early planting"],
    },
    {
        "name": "Fall Armyworm",
        "affected_crops": ["Maize", "Sorghum", "Cotton", "Rice"],
        "symptoms": ["ragged feeding in whorl", "frass like sawdust", "irregular holes in leaves"],
        "treatment": ["Emamectin benzoate 5 SG @ 220 g/ha", "Spinetoram 11.7 SC @ 375 ml/ha", "Bt spray"],
        "prevention": ["Intercrop with Napier grass", "Pheromone traps", "Avoid late planting"],
    },
    {
        "name": "Diamond Back Moth",
        "affected_crops": ["Cabbage", "Cauliflower", "Mustard", "Radish"],
        "symptoms": ["window pane feeding", "shot holes", "skeletonised leaves", "greenish larvae on underside"],
        "treatment": ["Spinosad 45 SC @ 150 ml/ha", "Emamectin benzoate 5 SG @ 200 g/ha", "Chlorfenapyr 10 SC"],
        "prevention": ["Bt crops", "Pheromone traps", "Natural predators"],
    },
    {
        "name": "Pod Borer (Gram)",
        "affected_crops": ["Chickpea", "Pigeonpea", "Cowpea"],
        "symptoms": ["bored pods", "excreta near entry holes", "damaged seeds"],
        "treatment": ["Endosulfan 35 EC @ 1.5 l/ha", "Profenofos 50 EC @ 1 l/ha"],
        "prevention": ["Intercrop chickpea with coriander", "Pheromone traps", "Early sowing"],
    },
    {
        "name": "Rust (Groundnut)",
        "affected_crops": ["Groundnut"],
        "symptoms": ["small orange-brown pustules", "yellowing", "defoliation"],
        "treatment": ["Mancozeb 75 WP @ 2.5 kg/ha", "Chlorothalonil 75 WP @ 1.5 kg/ha"],
        "prevention": ["Resistant varieties", "Seed treatment with thiram", "Early sowing"],
    },
    {
        "name": "Collar Rot",
        "affected_crops": ["Groundnut", "Chickpea", "Sunflower"],
        "symptoms": ["rotting at collar region", "dark brown lesion", "plant collapse"],
        "treatment": ["Soil drench with carbendazim 0.1%", "Thiram seed treatment"],
        "prevention": ["Seed treatment", "Avoid water-logged conditions", "Crop rotation"],
    },
    {
        "name": "White Grub",
        "affected_crops": ["Sugarcane", "Groundnut", "Maize", "Potato"],
        "symptoms": ["plants pulled out easily", "severed roots", "yellowing", "wilting"],
        "treatment": ["Chlorpyrifos 20 EC soil incorporation", "Imidacloprid 70 WS seed treatment"],
        "prevention": ["Summer ploughing to expose grubs", "Light traps for adults", "Neem cake application"],
    },
    {
        "name": "Scales",
        "affected_crops": ["Mango", "Citrus", "Coconut", "Grapes"],
        "symptoms": ["encrusted bark/leaves", "yellowing", "sooty mould", "branch die-back"],
        "treatment": ["DNOC 40 EC @ 1.5 l/ha in water", "Machine oil emulsion spray", "Dimethoate 30 EC"],
        "prevention": ["Prune infested branches", "Encourage natural predators", "Ant management"],
    },
    {
        "name": "Mango Hopper",
        "affected_crops": ["Mango"],
        "symptoms": ["yellowing and drying of inflorescences", "honeydew secretion", "sooty mould"],
        "treatment": ["Imidacloprid 17.8 SL @ 0.5 ml/l water", "Carbaryl 50 WP @ 2 g/l water"],
        "prevention": ["Prune dense canopy", "Remove weeds", "Spray at panicle emergence"],
    },
    {
        "name": "Coconut Mite (Eriophyid)",
        "affected_crops": ["Coconut"],
        "symptoms": ["triangular brown patches on husk", "scarring", "stunted nut"],
        "treatment": ["Wettable sulphur 80 WP @ 2 g/l water", "Dicofol 18.5 EC"],
        "prevention": ["Avoid water stress", "Remove dried leaves", "Summer spraying"],
    },
]


class MandiPriceTracker:
    """In-memory store for mandi commodity prices with query and trend utilities."""

    def __init__(self) -> None:
        # Map: (commodity_lower, state_lower, market_lower) -> list of prices
        self._store: list[MandiPrice] = []

    def add_price(self, price: MandiPrice) -> None:
        """Add a mandi price record to the tracker."""
        self._store.append(price)

    def get_prices(
        self, commodity: str, state: str | None = None
    ) -> list[MandiPrice]:
        """Return all price records for a commodity, optionally filtered by state."""
        comm_lower = commodity.lower()
        results = [p for p in self._store if p.commodity.lower() == comm_lower]
        if state:
            state_lower = state.lower()
            results = [p for p in results if p.state.lower() == state_lower]
        return sorted(results, key=lambda p: p.date, reverse=True)

    def price_trend(self, commodity: str, market: str) -> list[MandiPrice]:
        """Return chronological price records for a commodity at a specific market."""
        comm_lower = commodity.lower()
        mkt_lower = market.lower()
        results = [
            p for p in self._store
            if p.commodity.lower() == comm_lower and p.market.lower() == mkt_lower
        ]
        return sorted(results, key=lambda p: p.date)

    def all_prices(self) -> list[MandiPrice]:
        """Return all stored price records."""
        return list(self._store)


class PestDatabase:
    """Repository of Indian agricultural pests with symptom-based identification."""

    def __init__(self) -> None:
        self._pests: list[PestInfo] = [PestInfo(**entry) for entry in _RAW_PESTS]  # type: ignore[arg-type]

    def all_pests(self) -> list[PestInfo]:
        """Return all pests in the database."""
        return list(self._pests)

    def identify(self, symptoms: list[str]) -> list[PestInfo]:
        """Return pests whose symptom set overlaps with the provided symptoms."""
        symptoms_lower = {s.lower() for s in symptoms}
        scored: list[tuple[int, PestInfo]] = []
        for pest in self._pests:
            pest_symptoms_lower = {s.lower() for s in pest.symptoms}
            overlap = sum(
                1 for s in symptoms_lower
                if any(s in ps for ps in pest_symptoms_lower)
            )
            if overlap > 0:
                scored.append((overlap, pest))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [pest for _, pest in scored]

    def by_crop(self, crop_name: str) -> list[PestInfo]:
        """Return pests affecting a specific crop."""
        crop_lower = crop_name.lower()
        return [
            p for p in self._pests
            if any(c.lower() == crop_lower for c in p.affected_crops)
        ]


# ---------------------------------------------------------------------------
# Farmer assistant
# ---------------------------------------------------------------------------

_KEYWORD_RESPONSES: list[tuple[list[str], str, list[str]]] = [
    (
        ["price", "mandi", "rate", "sell", "market"],
        "Mandi prices vary by location and date. Use the 'prices' command or API to fetch current prices for your commodity and state. Agmarknet (agmarknet.gov.in) publishes daily mandi arrivals and prices across India.",
        ["Agmarknet (agmarknet.gov.in)", "eNAM (enam.gov.in)"],
    ),
    (
        ["pest", "insect", "bug", "disease", "fungus", "infection"],
        "Identify the pest or disease by its visible symptoms. Use the 'pest' command with symptom keywords to get matching pests and treatments. Always consult your local Krishi Vigyan Kendra (KVK) for confirmation.",
        ["ICAR Pest Management", "Krishi Vigyan Kendra network"],
    ),
    (
        ["fertilizer", "urea", "dap", "npk", "manure", "compost"],
        "Fertilizer requirements depend on soil test results. Get a soil health card from your state agriculture department. Base fertilizer application on NPK soil test recommendations. ICAR recommends integrated nutrient management combining inorganic and organic sources.",
        ["Soil Health Card scheme (soilhealth.dac.gov.in)", "ICAR nutrient management guidelines"],
    ),
    (
        ["irrigation", "water", "drip", "sprinkler", "rain"],
        "Irrigation scheduling should be based on crop stage and soil moisture. Drip irrigation can save 40-50% water compared to flood irrigation. PM Krishi Sinchayee Yojana provides subsidies for micro-irrigation systems.",
        ["PM Krishi Sinchayee Yojana", "ICAR crop water requirement data"],
    ),
    (
        ["seed", "variety", "sow", "hybrid", "certified"],
        "Use certified seeds from authorised dealers to ensure germination rates and disease resistance. State seed corporations and ICAR release improved varieties. Consult your block agriculture officer for variety recommendations suited to your region.",
        ["National Seeds Corporation (seedsindia.gov.in)", "ICAR variety releases"],
    ),
    (
        ["weather", "rain", "flood", "drought", "forecast"],
        "Monitor IMD weather forecasts at mausam.imd.gov.in. Agromet advisories are issued every Tuesday and Friday for all districts. Subscribe to SMS alerts from your state agriculture department.",
        ["IMD Agromet Advisory (agromet.imd.gov.in)", "Kisan Suvidha app"],
    ),
    (
        ["loan", "credit", "kcc", "finance", "money"],
        "Kisan Credit Card (KCC) provides short-term credit at 7% interest (4% with prompt repayment). Apply through your nearest bank or primary agriculture credit society. PM Kisan scheme provides Rs 6000 per year in three instalments.",
        ["Kisan Credit Card (RBI guidelines)", "PM-KISAN (pmkisan.gov.in)"],
    ),
    (
        ["insurance", "fasal bima", "pradhan mantri"],
        "Pradhan Mantri Fasal Bima Yojana (PMFBY) covers crop loss due to natural calamities at very low premium rates (2% for kharif, 1.5% for rabi). Enrol through banks or Common Service Centres before the cutoff date.",
        ["PMFBY (pmfby.gov.in)", "Krishi Rakshak portal"],
    ),
    (
        ["msp", "minimum support price", "procurement"],
        "The government announces MSP for 23 kharif and rabi crops. Procurement happens through FCI, NAFED, and state agencies. Register on eMitra or msprice portals for selling at MSP centres. Check latest MSP at agricoop.gov.in.",
        ["Commission for Agricultural Costs & Prices (cacp.gov.in)", "FCI (fci.gov.in)"],
    ),
]


class FarmerAssistant:
    """Rule-based assistant that answers farmer queries with keyword matching."""

    def respond(self, query: FarmerQuery) -> FarmerResponse:
        """Return an advisory response to the farmer's query."""
        query_lower = query.query.lower()
        best_answer = (
            "I can help with crop prices, pest identification, fertilizers, irrigation,"
            " seeds, weather, loans, insurance, and MSP. Please describe your query in more"
            " detail or use specific commands for prices and pest identification."
        )
        best_sources: list[str] = ["Kisan Call Centre (1800-180-1551)", "Kisan Suvidha App"]

        best_score = 0
        for keywords, answer, sources in _KEYWORD_RESPONSES:
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > best_score:
                best_score = score
                best_answer = answer
                best_sources = sources

        if query.location:
            best_answer += (
                f" For location-specific advice in {query.location}, contact your"
                " local Block Agriculture Officer or Krishi Vigyan Kendra."
            )

        return FarmerResponse(
            answer=best_answer,
            sources=best_sources,
            language=query.language,
            disclaimer=AGRICULTURAL_DISCLAIMER,
        )
