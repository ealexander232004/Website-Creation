"""Website presence classification engine for Google Maps lead generation.

Analyzes raw URLs from Google Maps profiles to distinguish between:
1. Real custom business websites (e.g. joesroofingaustin.com)
2. Missing websites (True No-Website)
3. Social media / directory profiles masquerading as websites (Facebook, Yelp, etc.)
4. Deprecated Google Business Site domains (*.business.site shut down by Google in 2024)
5. Free generic link trees / subdomains (linktr.ee, carrd.co, wixsite.com)
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

from models import WebsiteType


# Social media and business directory domains commonly inserted as substitute websites
SOCIAL_AND_DIRECTORY_DOMAINS = {
    # Major Social Networks
    "facebook.com",
    "m.facebook.com",
    "fb.com",
    "fb.me",
    "instagram.com",
    "instagr.am",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "pinterest.com",
    "youtube.com",
    "youtu.be",
    # Directories & Lead Generation Platforms
    "yelp.com",
    "m.yelp.com",
    "yellowpages.com",
    "superpages.com",
    "dexknows.com",
    "angi.com",
    "angieslist.com",
    "homeadvisor.com",
    "thumbtack.com",
    "houzz.com",
    "bark.com",
    "nextdoor.com",
    "bbb.org",
    "chamberofcommerce.com",
    "merchantcircle.com",
    "manta.com",
    "mapquest.com",
    "tripadvisor.com",
}

# Free link aggregator / generic builder domains
FREE_BUILDER_DOMAINS = {
    "linktr.ee",
    "carrd.co",
    "bio.link",
    "beacons.ai",
    "taplink.cc",
    "stan.store",
    "wixsite.com",
    "wordpress.com",
    "weebly.com",
    "square.site",
    "myshopify.com",
    "blogspot.com",
    "sites.google.com",
}

# Major national chains and franchises that should be excluded from independent small business leads
NATIONAL_CHAINS_EXCLUSIONS = {
    "walmart.com", "target.com", "homedepot.com", "lowes.com", "mcdonalds.com",
    "starbucks.com", "subway.com", "tacobell.com", "wendys.com", "cvs.com", "walgreens.com",
    "burgerking.com", "dominos.com", "pizzahut.com", "7-eleven.com", "circlek.com",
    "dollargeneral.com", "familydollar.com", "autozone.com", "oreillyauto.com",
    "advanceautoparts.com", "jiffylube.com", "midas.com", "firestonecompleteautocare.com",
    "pepboys.com", "valvoline.com", "mrrooter.com", "roto-rooter.com", "servpro.com",
    "stanleysteemer.com", "terminix.com", "orkin.com", "safelite.com", "maaco.com",
    "aamco.com", "ups.com", "fedex.com", "usps.com", "bankofamerica.com", "chase.com",
    "wellsfargo.com", "hrblock.com", "jacksonhewitt.com", "greatclips.com", "supercuts.com"
}


def clean_url(url: Optional[str]) -> Optional[str]:
    """Cleans and standardizes raw URL strings extracted from Google Maps."""
    if not url:
        return None
    
    url = url.strip()
    if not url or url.lower() in {"null", "none", "n/a", "undefined"}:
        return None

    # Handle Google redirect links: https://www.google.com/url?q=https://target.com...
    if "google.com/url?" in url:
        match = re.search(r"[?&]q=([^&]+)", url)
        if match:
            url = match.group(1)

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    return url


def extract_root_domain(url: str) -> str:
    """Extracts the registered root domain or hostname."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def classify_website(raw_url: Optional[str]) -> Tuple[WebsiteType, bool, str]:
    """Analyzes a URL and classifies its web presence.

    Returns:
        Tuple of (WebsiteType, has_real_website_boolean, explanatory_reason)
    """
    url = clean_url(raw_url)

    # 1. True No-Website
    if not url:
        return (
            WebsiteType.NO_WEBSITE,
            False,
            "No website URL listed in Google Business Profile",
        )

    domain = extract_root_domain(url)
    if not domain:
        return (
            WebsiteType.NO_WEBSITE,
            False,
            "Invalid or unparseable URL provided",
        )

    # 2. Deprecated Google Business Site (Shut down March 2024)
    # Examples: joesplumbing.business.site, xyz.negocio.site
    if domain.endswith(".business.site") or domain.endswith(".negocio.site"):
        return (
            WebsiteType.DEPRECATED_GOOGLE_SITE,
            False,
            "Dead Google Business Site (.business.site was deprecated by Google in 2024)",
        )

    # 3. National Corporate Franchise / Chain
    for chain in NATIONAL_CHAINS_EXCLUSIONS:
        if domain == chain or domain.endswith("." + chain):
            return (
                WebsiteType.CORPORATE_CHAIN,
                True,
                f"National corporate franchise / chain ({chain})",
            )

    # 3. Social Media & Directory Profiles
    for social_domain in SOCIAL_AND_DIRECTORY_DOMAINS:
        if domain == social_domain or domain.endswith("." + social_domain):
            return (
                WebsiteType.SOCIAL_MEDIA,
                False,
                f"Using social/directory platform profile ({social_domain}) instead of dedicated website",
            )

    # 4. Free Builder / Link Aggregator Subdomain
    for builder in FREE_BUILDER_DOMAINS:
        if domain == builder or domain.endswith("." + builder):
            return (
                WebsiteType.FREE_BUILDER,
                False,
                f"Hosted on free builder/link-tree subdomain ({builder})",
            )

    # 5. Dedicated Custom Domain Website
    return (
        WebsiteType.CUSTOM_DOMAIN,
        True,
        f"Custom dedicated domain ({domain})",
    )


def is_target_lead(
    website_type: WebsiteType,
    no_website_only: bool = True,
    include_social: bool = True,
    include_deprecated_google: bool = True,
    include_free_builders: bool = True,
) -> bool:
    """Evaluates whether a lead meets the user's 'no website' filter criteria."""
    if not no_website_only:
        return True

    if website_type == WebsiteType.NO_WEBSITE:
        return True
    if include_social and website_type == WebsiteType.SOCIAL_MEDIA:
        return True
    if include_deprecated_google and website_type == WebsiteType.DEPRECATED_GOOGLE_SITE:
        return True
    if include_free_builders and website_type == WebsiteType.FREE_BUILDER:
        return True

    return False
