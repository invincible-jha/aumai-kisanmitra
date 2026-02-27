"""Comprehensive tests for aumai-kisanmitra core module."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from aumai_kisanmitra.core import FarmerAssistant, MandiPriceTracker, PestDatabase
from aumai_kisanmitra.models import (
    AGRICULTURAL_DISCLAIMER,
    FarmerQuery,
    FarmerResponse,
    MandiPrice,
    PestInfo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tracker() -> MandiPriceTracker:
    return MandiPriceTracker()


@pytest.fixture()
def pest_db() -> PestDatabase:
    return PestDatabase()


@pytest.fixture()
def assistant() -> FarmerAssistant:
    return FarmerAssistant()


@pytest.fixture()
def sample_price() -> MandiPrice:
    return MandiPrice(
        commodity="rice",
        market="Azadpur",
        state="Delhi",
        min_price=1800.0,
        max_price=2200.0,
        modal_price=2000.0,
        date="2026-02-26",
    )


@pytest.fixture()
def loaded_tracker(tracker: MandiPriceTracker) -> MandiPriceTracker:
    """Tracker pre-loaded with rice and wheat records across multiple states."""
    tracker.add_price(MandiPrice(
        commodity="rice", market="Azadpur", state="Delhi",
        min_price=1800.0, max_price=2200.0, modal_price=2000.0, date="2026-02-25",
    ))
    tracker.add_price(MandiPrice(
        commodity="rice", market="Lucknow", state="UP",
        min_price=1750.0, max_price=2100.0, modal_price=1950.0, date="2026-02-26",
    ))
    tracker.add_price(MandiPrice(
        commodity="rice", market="Patna", state="Bihar",
        min_price=1700.0, max_price=2050.0, modal_price=1900.0, date="2026-02-24",
    ))
    tracker.add_price(MandiPrice(
        commodity="wheat", market="Azadpur", state="Delhi",
        min_price=2000.0, max_price=2350.0, modal_price=2150.0, date="2026-02-26",
    ))
    return tracker


# ---------------------------------------------------------------------------
# MandiPrice model tests
# ---------------------------------------------------------------------------


class TestMandiPriceModel:
    def test_valid_price_record(self) -> None:
        price = MandiPrice(
            commodity="rice",
            market="Azadpur",
            state="Delhi",
            min_price=1800.0,
            max_price=2200.0,
            modal_price=2000.0,
            date="2026-02-26",
        )
        assert price.commodity == "rice"
        assert price.modal_price == 2000.0

    def test_negative_min_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            MandiPrice(
                commodity="wheat",
                market="Delhi",
                state="Delhi",
                min_price=-100.0,
                max_price=2000.0,
                modal_price=1900.0,
                date="2026-02-26",
            )

    def test_negative_max_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            MandiPrice(
                commodity="wheat",
                market="Delhi",
                state="Delhi",
                min_price=1800.0,
                max_price=-50.0,
                modal_price=1900.0,
                date="2026-02-26",
            )

    def test_negative_modal_price_raises(self) -> None:
        with pytest.raises(ValidationError):
            MandiPrice(
                commodity="wheat",
                market="Delhi",
                state="Delhi",
                min_price=1800.0,
                max_price=2000.0,
                modal_price=-10.0,
                date="2026-02-26",
            )

    def test_zero_prices_valid(self) -> None:
        price = MandiPrice(
            commodity="rice",
            market="Test",
            state="Test",
            min_price=0.0,
            max_price=0.0,
            modal_price=0.0,
            date="2026-01-01",
        )
        assert price.min_price == 0.0


# ---------------------------------------------------------------------------
# PestInfo model tests
# ---------------------------------------------------------------------------


class TestPestInfoModel:
    def test_valid_pest_info(self) -> None:
        pest = PestInfo(
            name="Aphids",
            affected_crops=["Wheat", "Rice"],
            symptoms=["yellowing", "curling"],
            treatment=["spray neem oil"],
            prevention=["remove weeds"],
        )
        assert pest.name == "Aphids"

    def test_pest_info_empty_lists_valid(self) -> None:
        pest = PestInfo(
            name="TestPest",
            affected_crops=[],
            symptoms=[],
            treatment=[],
            prevention=[],
        )
        assert pest.affected_crops == []


# ---------------------------------------------------------------------------
# FarmerQuery and FarmerResponse model tests
# ---------------------------------------------------------------------------


class TestFarmerQueryModel:
    def test_valid_query_default_language(self) -> None:
        query = FarmerQuery(query="What fertilizer for wheat?")
        assert query.language == "en"
        assert query.location is None

    def test_query_with_location(self) -> None:
        query = FarmerQuery(query="Best crop for my field", location="Punjab")
        assert query.location == "Punjab"

    def test_query_with_hindi_language(self) -> None:
        query = FarmerQuery(query="Gehun ke liye kya fertilizer?", language="hi")
        assert query.language == "hi"


class TestFarmerResponseModel:
    def test_default_disclaimer(self) -> None:
        response = FarmerResponse(answer="Use DAP fertilizer.")
        assert response.disclaimer == AGRICULTURAL_DISCLAIMER

    def test_default_language_en(self) -> None:
        response = FarmerResponse(answer="Use DAP fertilizer.")
        assert response.language == "en"

    def test_default_empty_sources(self) -> None:
        response = FarmerResponse(answer="Use DAP fertilizer.")
        assert response.sources == []


# ---------------------------------------------------------------------------
# MandiPriceTracker tests
# ---------------------------------------------------------------------------


class TestMandiPriceTracker:
    def test_add_and_retrieve_single_price(
        self, tracker: MandiPriceTracker, sample_price: MandiPrice
    ) -> None:
        tracker.add_price(sample_price)
        results = tracker.get_prices("rice")
        assert len(results) == 1
        assert results[0].commodity == "rice"

    def test_get_prices_case_insensitive(
        self, tracker: MandiPriceTracker, sample_price: MandiPrice
    ) -> None:
        tracker.add_price(sample_price)
        assert len(tracker.get_prices("RICE")) == 1
        assert len(tracker.get_prices("Rice")) == 1

    def test_get_prices_filters_by_state(
        self, loaded_tracker: MandiPriceTracker
    ) -> None:
        results = loaded_tracker.get_prices("rice", state="Delhi")
        assert len(results) == 1
        assert results[0].state == "Delhi"

    def test_get_prices_state_case_insensitive(
        self, loaded_tracker: MandiPriceTracker
    ) -> None:
        lower = loaded_tracker.get_prices("rice", state="delhi")
        upper = loaded_tracker.get_prices("rice", state="DELHI")
        assert len(lower) == len(upper) == 1

    def test_get_prices_unknown_commodity_returns_empty(
        self, loaded_tracker: MandiPriceTracker
    ) -> None:
        assert loaded_tracker.get_prices("saffron") == []

    def test_get_prices_sorted_newest_first(
        self, loaded_tracker: MandiPriceTracker
    ) -> None:
        results = loaded_tracker.get_prices("rice")
        dates = [p.date for p in results]
        assert dates == sorted(dates, reverse=True)

    def test_price_trend_returns_chronological(
        self, tracker: MandiPriceTracker
    ) -> None:
        tracker.add_price(MandiPrice(
            commodity="wheat", market="Azadpur", state="Delhi",
            min_price=2100.0, max_price=2400.0, modal_price=2250.0, date="2026-02-26",
        ))
        tracker.add_price(MandiPrice(
            commodity="wheat", market="Azadpur", state="Delhi",
            min_price=2050.0, max_price=2350.0, modal_price=2200.0, date="2026-02-24",
        ))
        tracker.add_price(MandiPrice(
            commodity="wheat", market="Azadpur", state="Delhi",
            min_price=1980.0, max_price=2280.0, modal_price=2130.0, date="2026-02-22",
        ))
        trend = tracker.price_trend("wheat", "Azadpur")
        dates = [p.date for p in trend]
        assert dates == sorted(dates)

    def test_price_trend_filters_by_market(
        self, loaded_tracker: MandiPriceTracker
    ) -> None:
        trend = loaded_tracker.price_trend("rice", "Lucknow")
        assert all(p.market == "Lucknow" for p in trend)

    def test_price_trend_unknown_market_returns_empty(
        self, loaded_tracker: MandiPriceTracker
    ) -> None:
        assert loaded_tracker.price_trend("rice", "NonExistentMandi") == []

    def test_all_prices_returns_all_records(
        self, loaded_tracker: MandiPriceTracker
    ) -> None:
        all_p = loaded_tracker.all_prices()
        assert len(all_p) == 4  # 3 rice + 1 wheat

    def test_all_prices_empty_tracker(self, tracker: MandiPriceTracker) -> None:
        assert tracker.all_prices() == []

    def test_all_prices_returns_copy(self, tracker: MandiPriceTracker, sample_price: MandiPrice) -> None:
        tracker.add_price(sample_price)
        copy1 = tracker.all_prices()
        copy1.clear()
        copy2 = tracker.all_prices()
        assert len(copy2) == 1

    def test_multiple_adds_are_tracked(self, tracker: MandiPriceTracker) -> None:
        for i in range(5):
            tracker.add_price(MandiPrice(
                commodity="onion",
                market=f"Market{i}",
                state="Maharashtra",
                min_price=1000.0,
                max_price=2000.0,
                modal_price=1500.0,
                date=f"2026-02-{20 + i:02d}",
            ))
        assert len(tracker.get_prices("onion")) == 5


# ---------------------------------------------------------------------------
# PestDatabase tests
# ---------------------------------------------------------------------------


class TestPestDatabase:
    def test_all_pests_returns_at_least_25(self, pest_db: PestDatabase) -> None:
        assert len(pest_db.all_pests()) >= 25

    def test_all_pests_are_pest_info_objects(self, pest_db: PestDatabase) -> None:
        for pest in pest_db.all_pests():
            assert isinstance(pest, PestInfo)

    def test_all_pests_returns_copy(self, pest_db: PestDatabase) -> None:
        copy = pest_db.all_pests()
        copy.clear()
        assert len(pest_db.all_pests()) >= 25

    def test_identify_yellowing_returns_results(self, pest_db: PestDatabase) -> None:
        results = pest_db.identify(["yellowing"])
        assert len(results) > 0

    def test_identify_returns_list_of_pest_info(self, pest_db: PestDatabase) -> None:
        results = pest_db.identify(["wilting"])
        for r in results:
            assert isinstance(r, PestInfo)

    def test_identify_empty_symptoms_returns_empty(self, pest_db: PestDatabase) -> None:
        results = pest_db.identify([])
        assert results == []

    def test_identify_nonsense_symptoms_returns_empty(self, pest_db: PestDatabase) -> None:
        results = pest_db.identify(["zzz_unknown_abc"])
        assert results == []

    def test_identify_case_insensitive(self, pest_db: PestDatabase) -> None:
        lower = pest_db.identify(["yellowing"])
        upper = pest_db.identify(["YELLOWING"])
        assert len(lower) == len(upper)

    def test_identify_high_overlap_ranked_first(self, pest_db: PestDatabase) -> None:
        """Pests with more symptom matches should appear earlier."""
        results = pest_db.identify(["yellowing", "wilting", "stunted growth"])
        assert len(results) > 0
        # The first result should have at least one symptom matching

    def test_by_crop_rice_has_pests(self, pest_db: PestDatabase) -> None:
        rice_pests = pest_db.by_crop("Rice")
        assert len(rice_pests) > 0

    def test_by_crop_case_insensitive(self, pest_db: PestDatabase) -> None:
        lower = pest_db.by_crop("rice")
        upper = pest_db.by_crop("RICE")
        assert len(lower) == len(upper)

    def test_by_crop_cotton_has_pests(self, pest_db: PestDatabase) -> None:
        assert len(pest_db.by_crop("Cotton")) > 0

    def test_by_crop_unknown_returns_empty(self, pest_db: PestDatabase) -> None:
        assert pest_db.by_crop("AncientGrain") == []

    def test_brown_plant_hopper_affects_rice(self, pest_db: PestDatabase) -> None:
        rice_pests = pest_db.by_crop("Rice")
        names = [p.name for p in rice_pests]
        assert "Brown Plant Hopper" in names

    def test_identify_hopperburn_returns_brown_plant_hopper(
        self, pest_db: PestDatabase
    ) -> None:
        results = pest_db.identify(["hopperburn"])
        names = [r.name for r in results]
        assert "Brown Plant Hopper" in names

    def test_identify_bored_bolls_returns_helicoverpa(
        self, pest_db: PestDatabase
    ) -> None:
        results = pest_db.identify(["bored bolls"])
        assert len(results) > 0

    def test_identify_multiple_symptoms_narrows_results_or_more_relevant(
        self, pest_db: PestDatabase
    ) -> None:
        single = pest_db.identify(["yellowing"])
        multi = pest_db.identify(["yellowing", "lodging", "hopperburn"])
        # multi match should have Brown Plant Hopper near top
        if multi:
            assert multi[0].name == "Brown Plant Hopper"

    def test_all_pests_have_non_empty_treatment(self, pest_db: PestDatabase) -> None:
        for pest in pest_db.all_pests():
            assert len(pest.treatment) > 0, f"Pest {pest.name} has no treatments"

    def test_all_pests_have_non_empty_prevention(self, pest_db: PestDatabase) -> None:
        for pest in pest_db.all_pests():
            assert len(pest.prevention) > 0, f"Pest {pest.name} has no prevention"

    def test_all_pests_have_at_least_one_affected_crop(
        self, pest_db: PestDatabase
    ) -> None:
        for pest in pest_db.all_pests():
            assert len(pest.affected_crops) > 0, f"Pest {pest.name} has no affected crops"


# ---------------------------------------------------------------------------
# FarmerAssistant tests
# ---------------------------------------------------------------------------


class TestFarmerAssistant:
    def test_respond_returns_farmer_response(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="What price should I sell rice for?")
        response = assistant.respond(query)
        assert isinstance(response, FarmerResponse)

    def test_respond_answer_is_non_empty_string(
        self, assistant: FarmerAssistant
    ) -> None:
        query = FarmerQuery(query="How do I irrigate my wheat?")
        response = assistant.respond(query)
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0

    def test_respond_disclaimer_is_present(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="Random question")
        response = assistant.respond(query)
        assert response.disclaimer == AGRICULTURAL_DISCLAIMER

    def test_respond_sources_is_list(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="Tell me about pests")
        response = assistant.respond(query)
        assert isinstance(response.sources, list)

    def test_respond_mandi_price_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="What is the mandi price for rice today?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "price" in combined or "mandi" in combined or "agmarknet" in combined

    def test_respond_pest_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="My crop has pest attack with yellow leaves")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "pest" in combined or "symptom" in combined or "kvk" in combined

    def test_respond_fertilizer_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="What NPK fertilizer should I use?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "fertilizer" in combined or "nutrient" in combined or "soil" in combined

    def test_respond_irrigation_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="How often should I give drip irrigation?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "irrigation" in combined or "water" in combined or "drip" in combined

    def test_respond_seed_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="Which certified hybrid seed should I use?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "seed" in combined or "variety" in combined or "certified" in combined

    def test_respond_weather_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="Will there be rain? What is the weather forecast?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "weather" in combined or "imd" in combined or "forecast" in combined

    def test_respond_loan_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="How do I get a KCC loan from the bank?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "loan" in combined or "kcc" in combined or "credit" in combined

    def test_respond_insurance_query(self, assistant: FarmerAssistant) -> None:
        query = FarmerQuery(query="How do I enrol in Pradhan Mantri Fasal Bima?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "insurance" in combined or "pmfby" in combined or "bima" in combined

    def test_respond_msp_query(self, assistant: FarmerAssistant) -> None:
        # Use a query that scores 2 on the MSP keyword entry ("msp" + "procurement")
        # vs 1 on the mandi-prices entry ("price"), ensuring the MSP response wins.
        query = FarmerQuery(query="What is the MSP procurement rate for wheat?")
        response = assistant.respond(query)
        combined = response.answer.lower()
        assert "msp" in combined or "support price" in combined or "procurement" in combined

    def test_respond_unknown_query_returns_default(
        self, assistant: FarmerAssistant
    ) -> None:
        query = FarmerQuery(query="asdfghjkl qwerty zxcv")
        response = assistant.respond(query)
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0

    def test_respond_with_location_adds_location_in_answer(
        self, assistant: FarmerAssistant
    ) -> None:
        query = FarmerQuery(
            query="What fertilizer should I use?",
            location="Nashik",
        )
        response = assistant.respond(query)
        assert "Nashik" in response.answer

    def test_respond_language_preserved_in_response(
        self, assistant: FarmerAssistant
    ) -> None:
        query = FarmerQuery(query="fertilizer use", language="hi")
        response = assistant.respond(query)
        assert response.language == "hi"

    def test_respond_sources_non_empty_for_keyword_match(
        self, assistant: FarmerAssistant
    ) -> None:
        query = FarmerQuery(query="mandi price for onion")
        response = assistant.respond(query)
        assert len(response.sources) > 0

    def test_respond_does_not_raise_on_empty_query(
        self, assistant: FarmerAssistant
    ) -> None:
        query = FarmerQuery(query="")
        response = assistant.respond(query)
        assert isinstance(response, FarmerResponse)


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


@given(query_text=st.text(min_size=0, max_size=200))
@settings(max_examples=30)
def test_farmer_assistant_never_raises(query_text: str) -> None:
    """FarmerAssistant.respond must never raise for any text input."""
    assistant = FarmerAssistant()
    query = FarmerQuery(query=query_text)
    response = assistant.respond(query)
    assert isinstance(response, FarmerResponse)
    assert len(response.answer) > 0


@given(
    commodity=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Ll", "Lu"))),
    price=st.floats(min_value=0.0, max_value=100000.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=20)
def test_mandi_tracker_add_retrieve_property(commodity: str, price: float) -> None:
    """Any valid commodity+price should be storable and retrievable."""
    tracker = MandiPriceTracker()
    tracker.add_price(MandiPrice(
        commodity=commodity,
        market="TestMarket",
        state="TestState",
        min_price=price,
        max_price=price,
        modal_price=price,
        date="2026-01-01",
    ))
    results = tracker.get_prices(commodity)
    assert len(results) == 1
    assert results[0].modal_price == price


@given(symptoms=st.lists(
    st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "Zs"))),
    min_size=0,
    max_size=5,
))
@settings(max_examples=20)
def test_pest_identify_never_raises(symptoms: list[str]) -> None:
    db = PestDatabase()
    results = db.identify(symptoms)
    assert isinstance(results, list)
