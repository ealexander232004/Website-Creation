"""Probe current proxied Bing responses without persisting lead or email data."""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from pathlib import Path

import psycopg
from bs4 import BeautifulSoup
from curl_cffi import requests
from psycopg.rows import dict_row


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = Path(__file__).resolve().parent / "bing_probe_snapshot.json"
sys.path.insert(0, str(PROJECT_DIR))

from config import DEFAULT_CONFIG
from email_extractor import (
    EMAIL_REGEX,
    clean_extracted_email,
    email_matches_business,
    is_search_result_relevant,
)
from proxy_manager import ProxyManager


HEADERS = {
    "User-Agent": DEFAULT_CONFIG.user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def build_phone_query(row: dict[str, object]) -> str:
    phone = str(row.get("phone") or "")
    digits = re.sub(r"[^\d]", "", phone)
    formatted = (
        f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        if len(digits) == 10
        else phone
    )
    return f'"{row["name"]}" "{formatted}" OR "{digits}"'


def build_name_city_query(row: dict[str, object]) -> str:
    return f'"{row["name"]}" "{row.get("city") or ""}" email OR contact'


def main() -> None:
    with psycopg.connect(DEFAULT_CONFIG.database_url, row_factory=dict_row) as connection:
        leads = connection.execute(
            """
            WITH first_queue AS (
                SELECT DISTINCT ON (place_id) place_id, campaign_id
                FROM email_queue
                ORDER BY place_id, created_at, id
            )
            SELECT lead.place_id, lead.name, lead.category, lead.phone, lead.city
            FROM first_queue
            JOIN leads AS lead USING (place_id)
            JOIN email_extraction_status AS status USING (place_id)
            WHERE first_queue.campaign_id = (SELECT max(id) FROM campaigns)
              AND status.status = 'no_email'
              AND lead.phone IS NOT NULL
              AND btrim(lead.phone) <> ''
            ORDER BY md5(lead.place_id)
            LIMIT 10
            """
        ).fetchall()

    proxy_manager = ProxyManager(proxy_urls_file=DEFAULT_CONFIG.proxy_urls_file)
    results: list[dict[str, object]] = []
    for probe_number, lead in enumerate(leads, start=1):
        for query_variant, query in (
            ("current_phone_first", build_phone_query(lead)),
            ("omitted_name_city", build_name_city_query(lead)),
        ):
            route = proxy_manager.get_next_proxy()
            if route is None or not route.raw_url:
                raise RuntimeError("No proxy route available; probe will not use a direct connection")
            response = requests.get(
                f"https://www.bing.com/search?q={urllib.parse.quote(query)}",
                headers=HEADERS,
                proxies={"http": route.raw_url, "https": route.raw_url},
                timeout=12,
                impersonate="chrome120",
            )
            soup = BeautifulSoup(response.text, "html.parser")
            lower_body = response.text.lower()
            relevant_cards = 0
            raw_emails_on_relevant_cards = 0
            cleaned_emails_on_relevant_cards = 0
            accepted_emails_on_relevant_cards = 0
            for item in soup.select("li.b_algo"):
                item_text = item.get_text(" ", strip=True)
                if not is_search_result_relevant(
                    item_text,
                    business_name=str(lead["name"]),
                    phone=str(lead.get("phone") or ""),
                    city=str(lead.get("city") or ""),
                    category=str(lead.get("category") or ""),
                ):
                    continue
                relevant_cards += 1
                for raw_email in EMAIL_REGEX.findall(item_text):
                    raw_emails_on_relevant_cards += 1
                    cleaned = clean_extracted_email(raw_email)
                    if not cleaned:
                        continue
                    cleaned_emails_on_relevant_cards += 1
                    if email_matches_business(
                        cleaned,
                        str(lead["name"]),
                        category=str(lead.get("category") or ""),
                        phone=str(lead.get("phone") or ""),
                        local_context=item_text,
                        result_context=item_text,
                    ):
                        accepted_emails_on_relevant_cards += 1
            results.append(
                {
                    "probe": probe_number,
                    "query_variant": query_variant,
                    "status_code": response.status_code,
                    "body_bytes": len(response.content),
                    "looks_like_search_page": bool(soup.title and soup.title.get_text(" ", strip=True).endswith(" - Search")),
                    "result_cards": len(soup.select("li.b_algo")),
                    "result_headings": len(soup.select("li.b_algo h2 a")),
                    "relevant_result_cards": relevant_cards,
                    "raw_emails_on_relevant_cards": raw_emails_on_relevant_cards,
                    "cleaned_emails_on_relevant_cards": cleaned_emails_on_relevant_cards,
                    "accepted_emails_on_relevant_cards": accepted_emails_on_relevant_cards,
                    "has_bing_captcha_marker": "captcha" in lower_body,
                    "has_unusual_traffic_marker": "unusual traffic" in lower_body,
                    "has_verify_marker": "verify you are human" in lower_body,
                }
            )

    OUTPUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
