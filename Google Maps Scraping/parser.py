"""Data extraction engine for Google Maps listing cards and detail views.

Supports hybrid extraction:
1. Fast Protobuf/JSON deserialization from window.APP_INITIALIZATION_STATE
2. Robust DOM tree parsing for feed cards and detail panels
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from models import ClaimedStatus, Lead, WebsiteType
from website_analyzer import classify_website

logger = logging.getLogger("gmaps_scraper.parser")

# Regex patterns for U.S. addresses and phone numbers
US_PHONE_REGEX = re.compile(r"(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})")
US_ZIP_REGEX = re.compile(r"\b([0-9]{5})(?:-[0-9]{4})?\b")
US_STATE_REGEX = re.compile(
    r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b",
    re.IGNORECASE,
)
RATING_REVIEWS_REGEX = re.compile(r"([0-9]\.[0-9])\s*(?:stars?|\*|\()?\s*\(?([0-9,]+)\)?")


def parse_us_address(full_address: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Decomposes a raw US address into (street, city, state, zip_code)."""
    if not full_address:
        return None, None, None, None

    address = full_address.strip()
    # Remove trailing country if present
    address = re.sub(r",?\s*(?:United States|USA|US)$", "", address, flags=re.IGNORECASE).strip()

    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Extract ZIP code
    zip_match = US_ZIP_REGEX.search(address)
    if zip_match:
        zip_code = zip_match.group(1)

    # Extract State
    state_match = US_STATE_REGEX.search(address)
    if state_match:
        state = state_match.group(1).upper()

    # Split by comma segments
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) >= 3:
        street = parts[0]
        city = parts[1]
    elif len(parts) == 2:
        street = parts[0]
        city = parts[1]
    elif len(parts) == 1:
        street = parts[0]

    return street, city, state, zip_code


def parse_phone(raw_phone: Optional[str]) -> Optional[str]:
    """Cleans and standardizes raw phone strings into (XXX) XXX-XXXX format."""
    if not raw_phone:
        return None
    match = US_PHONE_REGEX.search(raw_phone)
    if match:
        return f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
    return raw_phone.strip()


class GoogleMapsParser:
    """Parses Google Maps HTML, feed cards, and detail sidebars."""

    @staticmethod
    def parse_card_element_html(
        card_html: str,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Optional[Lead]:
        """Extracts structured lead data from an individual search feed card HTML."""
        soup = BeautifulSoup(card_html, "html.parser")

        # 1. Business Name
        name_tag = (
            soup.select_one("div.fontHeadlineSmall")
            or soup.select_one(".qBF1Pd")
            or soup.select_one("a.hfpxzc")
        )
        if not name_tag:
            return None
        name = name_tag.get_text(strip=True)
        if not name:
            return None

        # 2. Maps Place URL and Place ID
        link_tag = soup.select_one("a.hfpxzc") or soup.select_one("a[href*='/maps/place/']")
        maps_url = link_tag.get("href") if link_tag else None
        
        place_id = None
        latitude = None
        longitude = None

        if maps_url:
            # Extract coordinates from URL: /@34.0522,-118.2437,14z/
            coord_match = re.search(r"@([0-9.-]+),([0-9.-]+)", maps_url)
            if coord_match:
                try:
                    latitude = float(coord_match.group(1))
                    longitude = float(coord_match.group(2))
                except ValueError:
                    pass

            # Extract Hex CID or place ID
            cid_match = re.search(r"0x[0-9a-fA-F]+:0x([0-9a-fA-F]+)", maps_url)
            if cid_match:
                place_id = cid_match.group(1)

        # 3. Rating & Reviews Count
        rating = None
        reviews_count = 0
        rating_tag = soup.select_one("span.MW4etd") or soup.select_one("span[role='img']")
        if rating_tag:
            try:
                rating = float(rating_tag.get_text(strip=True))
            except ValueError:
                pass

        reviews_tag = soup.select_one("span.UY7F9")
        if reviews_tag:
            rev_text = reviews_tag.get_text(strip=True).replace("(", "").replace(")", "").replace(",", "")
            try:
                reviews_count = int(rev_text)
            except ValueError:
                pass

        # 4. Category & Address snippet
        category = None
        full_address = None
        phone = None

        info_divs = soup.select("div.W4Efsd")
        for div in info_divs:
            text = div.get_text(" | ", strip=True)
            # Check for phone number
            if not phone:
                phone_match = US_PHONE_REGEX.search(text)
                if phone_match:
                    phone = parse_phone(phone_match.group(0))

            # Split segments
            segments = [s.strip() for s in text.split("·") if s.strip()]
            for seg in segments:
                if not category and not any(char.isdigit() for char in seg) and len(seg) < 40:
                    category = seg
                elif not full_address and any(char.isdigit() for char in seg):
                    full_address = seg

        # 5. Website presence check
        # Google Maps renders an anchor with aria-label="Website" or data-value="Website" on the feed card
        website_tag = soup.select_one("a[data-value='Website']") or soup.select_one("a[aria-label*='website' i]")
        raw_website = website_tag.get("href") if website_tag else None

        # Classify website
        web_type, has_real_web, explanation = classify_website(raw_website)
        street, city, state, zip_code = parse_us_address(full_address)

        return Lead(
            place_id=place_id,
            name=name,
            category=category,
            phone=phone,
            full_address=full_address,
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            latitude=latitude,
            longitude=longitude,
            website_raw=raw_website,
            website_type=web_type,
            website_explanation=explanation,
            has_website=has_real_web,
            rating=rating,
            reviews_count=reviews_count,
            is_claimed=ClaimedStatus.UNKNOWN,
            maps_url=maps_url,
            search_keyword=keyword,
            search_location=location,
        )

    @staticmethod
    def parse_detail_page_html(
        detail_html: str,
        current_url: Optional[str] = None,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Optional[Lead]:
        """Extracts complete metadata from the opened Google Maps Place detail sidebar."""
        soup = BeautifulSoup(detail_html, "html.parser")

        # 1. Business Title
        title_tag = soup.select_one("h1.DUwDvf") or soup.select_one("h1")
        if not title_tag:
            return None
        name = title_tag.get_text(strip=True)
        if not name:
            return None

        # 2. Category
        category = None
        cat_btn = soup.select_one("button[jsaction*='category']") or soup.select_one("button.DkEaL")
        if cat_btn:
            category = cat_btn.get_text(strip=True)

        # 3. Rating & Total Reviews
        rating = None
        reviews_count = 0
        rating_div = soup.select_one("div.F7nice")
        if rating_div:
            score_span = rating_div.select_one("span[aria-hidden='true']")
            if score_span:
                try:
                    rating = float(score_span.get_text(strip=True))
                except ValueError:
                    pass

            count_span = rating_div.select_one("span[aria-label*='reviews']")
            if count_span:
                rev_text = re.sub(r"[^\d]", "", count_span.get_text(strip=True))
                if rev_text:
                    reviews_count = int(rev_text)

        # 4. Contact Details: Address, Phone, Website, Claimed Status
        full_address = None
        phone = None
        website_raw = None
        is_claimed = ClaimedStatus.CLAIMED
        plus_code = None

        # Address button
        addr_btn = (
            soup.select_one("button[data-item-id='address']")
            or soup.select_one("button[aria-label^='Address:']")
        )
        if addr_btn:
            full_address = addr_btn.get_text(strip=True).replace("Address: ", "")

        # Phone button
        phone_btn = (
            soup.select_one("button[data-item-id^='phone:']")
            or soup.select_one("button[aria-label^='Phone:']")
        )
        if phone_btn:
            phone = parse_phone(phone_btn.get_text(strip=True).replace("Phone: ", ""))

        # Website button
        web_link = (
            soup.select_one("a[data-item-id='authority']")
            or soup.select_one("a[aria-label^='Website:']")
        )
        if web_link:
            website_raw = web_link.get("href")

        # Plus code
        code_btn = soup.select_one("button[data-item-id='oloc']")
        if code_btn:
            plus_code = code_btn.get_text(strip=True)

        # Claimed Status ("Claim this business" present = UNCLAIMED)
        claim_btn = (
            soup.select_one("button[data-item-id='merchant']")
            or soup.select_one("a[aria-label*='Claim this business' i]")
            or soup.select_one("button[aria-label*='Claim this business' i]")
        )
        if claim_btn:
            is_claimed = ClaimedStatus.UNCLAIMED

        # Price Level
        price_level = None
        price_tag = soup.select_one("span[aria-label*='Price:']")
        if price_tag:
            price_level = price_tag.get_text(strip=True)

        # Coordinates & Place ID from URL
        latitude = None
        longitude = None
        place_id = None

        if current_url:
            coord_match = re.search(r"@([0-9.-]+),([0-9.-]+)", current_url)
            if coord_match:
                try:
                    latitude = float(coord_match.group(1))
                    longitude = float(coord_match.group(2))
                except ValueError:
                    pass

            cid_match = re.search(r"0x[0-9a-fA-F]+:0x([0-9a-fA-F]+)", current_url)
            if cid_match:
                place_id = cid_match.group(1)

        web_type, has_real_web, explanation = classify_website(website_raw)
        street, city, state, zip_code = parse_us_address(full_address)

        return Lead(
            place_id=place_id,
            name=name,
            category=category,
            phone=phone,
            full_address=full_address,
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            latitude=latitude,
            longitude=longitude,
            plus_code=plus_code,
            website_raw=website_raw,
            website_type=web_type,
            website_explanation=explanation,
            has_website=has_real_web,
            rating=rating,
            reviews_count=reviews_count,
            is_claimed=is_claimed,
            price_level=price_level,
            maps_url=current_url,
            search_keyword=keyword,
            search_location=location,
        )
