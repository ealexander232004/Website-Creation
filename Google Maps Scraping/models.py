"""Pydantic data models for the Google Maps Lead Extraction system."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class WebsiteType(str, Enum):
    """Classification of a business's web presence."""
    NO_WEBSITE = "none"                       # No website link provided
    SOCIAL_MEDIA = "social_media"             # Facebook, Instagram, Yelp, etc.
    DEPRECATED_GOOGLE_SITE = "google_site"    # *.business.site (defunct since March 2024)
    FREE_BUILDER = "free_builder"             # linktr.ee, carrd, wixsite, wordpress.com
    CUSTOM_DOMAIN = "custom_domain"           # Dedicated business website (e.g. joesplumbing.com)
    CORPORATE_CHAIN = "corporate_chain"       # National chain / franchise (e.g. Walmart, McDonald's)


class ClaimedStatus(str, Enum):
    """Google Business Profile verification status."""
    CLAIMED = "claimed"
    UNCLAIMED = "unclaimed"  # "Claim this business" link is present
    UNKNOWN = "unknown"


class SearchJobStatus(str, Enum):
    """Lifecycle status of a partitioned search job."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Lead(BaseModel):
    """Structured entity representing a scraped business lead."""

    place_id: Optional[str] = Field(None, description="Google Maps Place ID or unique feature identifier")
    cid: Optional[str] = Field(None, description="Google Customer Identification number")
    name: str = Field(..., description="Business name")
    category: Optional[str] = Field(None, description="Primary business category (e.g. Roofing contractor)")
    all_categories: List[str] = Field(default_factory=list, description="Additional secondary categories")
    
    # Contact & Location
    phone: Optional[str] = Field(None, description="Cleaned phone number")
    full_address: Optional[str] = Field(None, description="Full formatted address")
    street: Optional[str] = Field(None, description="Street address line")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State code or full name")
    zip_code: Optional[str] = Field(None, description="5-digit or extended ZIP code")
    country: str = Field("United States", description="Country name")
    latitude: Optional[float] = Field(None, description="Geographic latitude")
    longitude: Optional[float] = Field(None, description="Geographic longitude")
    plus_code: Optional[str] = Field(None, description="Google Plus Code")

    # Web Presence & Assessment
    website_raw: Optional[str] = Field(None, description="Raw website URL from Google Maps profile")
    website_type: WebsiteType = Field(WebsiteType.NO_WEBSITE, description="Categorized website status")
    website_explanation: Optional[str] = Field(None, description="Explanation for classification")
    has_website: bool = Field(False, description="True if the listed URL counts as a website for targeting")

    # Reputation & Profile Metadata
    rating: Optional[float] = Field(None, description="Average review rating (0.0 - 5.0)")
    reviews_count: int = Field(0, description="Total number of Google reviews")
    is_claimed: ClaimedStatus = Field(ClaimedStatus.UNKNOWN, description="GBP claimed status")
    price_level: Optional[str] = Field(None, description="Price tier indicator (e.g. $, $$, $$$)")
    business_status: Optional[str] = Field(None, description="Operational status (e.g. OPERATIONAL, CLOSED)")
    
    # Metadata & Tracking
    maps_url: Optional[str] = Field(None, description="Direct URL to Google Maps place listing")
    search_keyword: Optional[str] = Field(None, description="Keyword query that discovered this lead")
    search_location: Optional[str] = Field(None, description="Geographic location query")
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of scrape")

    def to_flat_dict(self) -> Dict[str, Any]:
        """Flattens the lead model for tabular CSV/Excel export."""
        return {
            "name": self.name,
            "category": self.category,
            "phone": self.phone,
            "website_raw": self.website_raw,
            "website_type": self.website_type.value,
            "has_website": self.has_website,
            "website_explanation": self.website_explanation,
            "is_claimed": self.is_claimed.value,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "full_address": self.full_address,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "place_id": self.place_id,
            "cid": self.cid,
            "maps_url": self.maps_url,
            "search_keyword": self.search_keyword,
            "search_location": self.search_location,
            "scraped_at": self.scraped_at.isoformat(),
        }


class SearchJob(BaseModel):
    """A single geographic search task in the execution queue."""

    id: Optional[int] = None
    campaign_id: Optional[int] = None
    keyword: str
    location_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zoom_level: int = 14
    bounding_box: Optional[str] = None
    status: SearchJobStatus = SearchJobStatus.PENDING
    results_found: int = 0
    leads_saved: int = 0
    error_message: Optional[str] = None
    attempts: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
