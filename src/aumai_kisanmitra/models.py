"""Pydantic v2 models for aumai-kisanmitra farmer assistant."""

from __future__ import annotations

from pydantic import BaseModel, Field

AGRICULTURAL_DISCLAIMER = (
    "Verify recommendations with local agricultural experts before application."
)

__all__ = [
    "MandiPrice",
    "PestInfo",
    "FarmerQuery",
    "FarmerResponse",
    "AGRICULTURAL_DISCLAIMER",
]


class MandiPrice(BaseModel):
    """Mandi (agricultural market) price record for a commodity."""

    commodity: str = Field(..., description="Name of the agricultural commodity")
    market: str = Field(..., description="Name of the mandi/market")
    state: str = Field(..., description="State where the mandi is located")
    min_price: float = Field(..., ge=0.0, description="Minimum price in INR per quintal")
    max_price: float = Field(..., ge=0.0, description="Maximum price in INR per quintal")
    modal_price: float = Field(..., ge=0.0, description="Modal (most common) price in INR per quintal")
    date: str = Field(..., description="Date of price record in YYYY-MM-DD format")


class PestInfo(BaseModel):
    """Information about an agricultural pest or disease."""

    name: str = Field(..., description="Common name of the pest or disease")
    affected_crops: list[str] = Field(..., description="Crops affected by this pest")
    symptoms: list[str] = Field(..., description="Observable symptoms of infestation")
    treatment: list[str] = Field(..., description="Recommended treatment measures")
    prevention: list[str] = Field(..., description="Preventive measures to avoid infestation")


class FarmerQuery(BaseModel):
    """A query submitted by a farmer."""

    query: str = Field(..., description="The farmer's question or concern")
    language: str = Field(default="en", description="Language code for the query")
    location: str | None = Field(default=None, description="Farmer's location for context")


class FarmerResponse(BaseModel):
    """Response to a farmer query with sources and disclaimer."""

    answer: str = Field(..., description="The advisory response")
    sources: list[str] = Field(default_factory=list, description="Sources or references")
    language: str = Field(default="en", description="Language of the response")
    disclaimer: str = Field(
        default=AGRICULTURAL_DISCLAIMER,
        description="Mandatory agricultural disclaimer",
    )
