"""Small Business Category Taxonomy Presets for Google Maps Lead Generation."""

from __future__ import annotations

from typing import Dict, List

# Core 50 high-probability independent small business niches without websites
ALL_SMALL_BUSINESS = [
    # Home Services & Trades (20)
    "plumber",
    "electrician",
    "roofing contractor",
    "hvac contractor",
    "landscaping service",
    "handyman",
    "painter",
    "drywall contractor",
    "pest control service",
    "tree service",
    "flooring contractor",
    "carpenter",
    "masonry contractor",
    "fence contractor",
    "deck builder",
    "pressure washing service",
    "house cleaning service",
    "junk removal",
    "locksmith",
    "garage door supplier",
    # Automotive (10)
    "auto repair shop",
    "mobile mechanic",
    "auto body shop",
    "car detailing service",
    "towing service",
    "tire shop",
    "oil change service",
    "auto window tinting service",
    "transmission shop",
    "boat repair shop",
    # Personal Care, Wellness & Grooming (10)
    "barber shop",
    "hair salon",
    "nail salon",
    "massage therapist",
    "tattoo shop",
    "pet groomer",
    "dog trainer",
    "personal trainer",
    "beauty salon",
    "tanning salon",
    # Local & Professional Services (10)
    "notary public",
    "tax consultant",
    "appliance repair service",
    "tailor",
    "dry cleaner",
    "welder",
    "food truck",
    "catering food and drink supplier",
    "florist",
    "moving company",
]

# Vertical Specific Subsets
HOME_SERVICES_PRESET = [
    "plumber",
    "electrician",
    "roofing contractor",
    "hvac contractor",
    "landscaping service",
    "handyman",
    "painter",
    "drywall contractor",
    "pest control service",
    "tree service",
    "flooring contractor",
    "carpenter",
    "masonry contractor",
    "fence contractor",
    "deck builder",
    "pressure washing service",
    "house cleaning service",
    "junk removal",
    "pool cleaning service",
    "locksmith",
    "garage door supplier",
    "insulation contractor",
    "concrete contractor",
    "water damage restoration service",
    "gutter cleaning service",
]

AUTOMOTIVE_PRESET = [
    "auto repair shop",
    "mobile mechanic",
    "auto body shop",
    "car detailing service",
    "towing service",
    "tire shop",
    "oil change service",
    "auto window tinting service",
    "transmission shop",
    "used car dealer",
    "boat repair shop",
    "motorcycle repair shop",
    "auto glass shop",
    "muffler shop",
    "brake shop",
]

PERSONAL_CARE_PRESET = [
    "barber shop",
    "hair salon",
    "nail salon",
    "massage therapist",
    "tattoo shop",
    "pet groomer",
    "dog trainer",
    "personal trainer",
    "beauty salon",
    "tanning salon",
    "eyebrow bar",
    "skincare clinic",
]

LOCAL_SERVICES_PRESET = [
    "notary public",
    "bookkeeper",
    "tax consultant",
    "appliance repair service",
    "tailor",
    "dry cleaner",
    "welder",
    "food truck",
    "catering food and drink supplier",
    "florist",
    "moving company",
    "shoe repair shop",
    "upholstery shop",
    "screen repair service",
    "sharpening service",
]

# 10 Broad Anchor Terms for Fast High-Volume Sweeps
BROAD_ANCHORS_PRESET = [
    "contractor",
    "repair service",
    "cleaning service",
    "maintenance service",
    "salon",
    "shop",
    "service",
    "installer",
    "catering",
    "towing",
]

CATEGORY_PRESETS: Dict[str, List[str]] = {
    "all_small_business": ALL_SMALL_BUSINESS,
    "home_services": HOME_SERVICES_PRESET,
    "auto": AUTOMOTIVE_PRESET,
    "personal_care": PERSONAL_CARE_PRESET,
    "local_services": LOCAL_SERVICES_PRESET,
    "broad_anchors": BROAD_ANCHORS_PRESET,
}


def resolve_keywords(
    keyword_input: str | None = None,
    preset: str | None = "all_small_business",
) -> List[str]:
    """Resolves CLI input or preset name into a clean list of keyword search strings."""
    if keyword_input:
        # Check if comma-separated list
        if "," in keyword_input:
            return [k.strip() for k in keyword_input.split(",") if k.strip()]
        return [keyword_input.strip()]

    if preset and preset.lower() in CATEGORY_PRESETS:
        return CATEGORY_PRESETS[preset.lower()]

    return ALL_SMALL_BUSINESS
