"""Regression tests for fail-closed email-enrichment networking."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from email_extractor import (
    EmailFootprintExtractor,
    clean_extracted_email,
    email_matches_business,
    is_search_result_relevant,
)
from proxy_manager import ProxyRoute


class FakeDatabase:
    def ping(self) -> None:
        return None


class EmptyProxyManager:
    total_proxies = 0

    def get_next_proxy(self):
        return None


class OneProxyManager:
    total_proxies = 1

    def __init__(self) -> None:
        self.route = ProxyRoute.from_url("http://proxy-user:proxy-pass@proxy.invalid:8001")

    def get_next_proxy(self) -> ProxyRoute:
        return self.route


class FakeResponse:
    status_code = 200
    text = "<html><body>No address published.</body></html>"


class EmailProxyEnforcementTests(unittest.TestCase):
    def test_constructor_rejects_empty_proxy_pool(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "direct-network fallback is disabled"):
            EmailFootprintExtractor(FakeDatabase(), proxy_manager=EmptyProxyManager())

    def test_every_email_request_receives_required_proxy_mapping(self) -> None:
        manager = OneProxyManager()
        extractor = EmailFootprintExtractor(FakeDatabase(), proxy_manager=manager)
        calls = []

        def fake_get(url, **kwargs):
            calls.append((url, kwargs))
            return FakeResponse()

        lead = {
            "name": "Example Plumbing",
            "phone": "",
            "city": "Austin",
            "place_id": "test-place-id",
        }
        with patch("email_extractor.requests.get", side_effect=fake_get):
            self.assertEqual(extractor.search_lead_footprint(lead), [])

        self.assertGreaterEqual(len(calls), 1)
        for _, kwargs in calls:
            self.assertEqual(
                kwargs["proxies"],
                {"http": manager.route.raw_url, "https": manager.route.raw_url},
            )

    def test_proxy_failure_is_not_mislabeled_as_no_email(self) -> None:
        extractor = EmailFootprintExtractor(FakeDatabase(), proxy_manager=OneProxyManager())
        lead = {
            "name": "Example Electric",
            "phone": "",
            "city": "Denver",
            "place_id": "test-place-id",
        }
        with patch("email_extractor.requests.get", side_effect=RuntimeError("proxy unavailable")):
            with self.assertRaisesRegex(RuntimeError, "All proxied email search requests failed"):
                extractor.search_lead_footprint(lead)

    def test_unrelated_directory_email_dump_is_filtered_and_bounded(self) -> None:
        extractor = EmailFootprintExtractor(FakeDatabase(), proxy_manager=OneProxyManager())
        search_html = (
            '<li class="b_algo"><h2><a href="https://directory.invalid/example-plumbing">'
            "Example Plumbing</a></h2></li>"
        )
        unrelated = " ".join(
            f"person{index:02d}@unrelated.org" for index in range(30)
        )
        landing_html = f"{unrelated} contact@exampleplumbing.com"
        responses = [
            type("SearchResponse", (), {"status_code": 200, "text": search_html})(),
            type("LandingResponse", (), {"status_code": 200, "text": landing_html})(),
        ]
        lead = {
            "name": "Example Plumbing",
            "phone": "",
            "city": "Austin",
            "place_id": "test-place-id",
        }

        with patch("email_extractor.requests.get", side_effect=responses):
            emails = extractor.search_lead_footprint(lead)

        self.assertEqual([email.email for email in emails], ["contact@exampleplumbing.com"])

    def test_unrelated_search_result_email_and_link_are_ignored(self) -> None:
        extractor = EmailFootprintExtractor(FakeDatabase(), proxy_manager=OneProxyManager())
        search_html = (
            '<li class="b_algo"><h2><a href="https://directory.invalid/other-company">'
            "Unrelated Company</a></h2><p>sales@unrelated.org</p></li>"
        )
        lead = {
            "name": "Example Plumbing",
            "category": "Plumber",
            "phone": "(512) 555-0100",
            "city": "Austin",
            "place_id": "test-place-id",
        }
        fake_response = type(
            "SearchResponse", (), {"status_code": 200, "text": search_html}
        )()

        with patch("email_extractor.requests.get", return_value=fake_response) as get:
            self.assertEqual(extractor.search_lead_footprint(lead), [])

        self.assertEqual(get.call_count, 2)

    def test_short_single_token_business_collision_is_ignored(self) -> None:
        extractor = EmailFootprintExtractor(FakeDatabase(), proxy_manager=OneProxyManager())
        search_html = (
            '<li class="b_algo"><h2><a href="https://allstar-electric.invalid/">'
            "All Star Electric</a></h2><p>info@allstar-electric.com</p></li>"
        )
        lead = {
            "name": "A M Star Electric",
            "category": "Electrician",
            "phone": "",
            "city": "",
            "place_id": "test-place-id",
        }
        fake_response = type(
            "SearchResponse", (), {"status_code": 200, "text": search_html}
        )()

        with patch("email_extractor.requests.get", return_value=fake_response) as get:
            self.assertEqual(extractor.search_lead_footprint(lead), [])

        self.assertEqual(get.call_count, 1)

    def test_directory_page_requires_address_level_business_context(self) -> None:
        extractor = EmailFootprintExtractor(FakeDatabase(), proxy_manager=OneProxyManager())
        search_html = (
            '<li class="b_algo"><h2><a href="https://directory.invalid/plumbers">'
            "Big Dog Plumbing</a></h2></li>"
        )
        landing_html = " ".join(
            [
                "Big Dog Plumbing",
                "cjs.plumbing@verizon.net",
                "fleetplumbing@cox.net",
                "giornoplumbing@gmail.com",
            ]
        )

        def fake_get(url, **kwargs):
            if "bing.com" in url:
                return type("SearchResponse", (), {"status_code": 200, "text": search_html})()
            return type("LandingResponse", (), {"status_code": 200, "text": landing_html})()

        lead = {
            "name": "Big Dog Plumbing",
            "category": "Plumber",
            "phone": "",
            "city": "",
            "place_id": "test-place-id",
        }
        with patch("email_extractor.requests.get", side_effect=fake_get):
            self.assertEqual(extractor.search_lead_footprint(lead), [])

    def test_matching_listing_context_alone_does_not_authorize_platform_email(self) -> None:
        context = "M J Mechanical Plumbing Heating & A (507) 627-8723"

        self.assertFalse(
            email_matches_business(
                "help@nears.me",
                "M J Mechanical Plumbing Heating & A",
                category="Mechanical contractor",
                phone="(507) 627-8723",
                local_context=context,
                result_context=context,
                source_url="https://hvac-usa.nears.me/example",
            )
        )

    def test_brand_identity_accepts_owner_and_acronym_addresses(self) -> None:
        self.assertTrue(
            email_matches_business(
                "bschroering@psci.net",
                "Schroering Plumbing Heating & A/C",
                category="Plumber",
            )
        )
        self.assertTrue(
            email_matches_business(
                "kathy@sosplumbing.net",
                "SOS Plumbing and Drain Service Medford Oregon",
                category="Plumber",
            )
        )
        self.assertFalse(
            email_matches_business(
                "service@messmermechanical.com",
                "Schroering Plumbing Heating & A/C",
                category="Plumber",
            )
        )

    def test_uppercase_surname_is_not_treated_as_an_acronym(self) -> None:
        self.assertFalse(
            email_matches_business(
                "info@oneillwetsuits.com",
                "O'NEILL PLUMBING",
                category="No reviews",
            )
        )

    def test_initial_only_name_requires_phone_corroboration(self) -> None:
        wrong_context = "B & S Electric (813) 555-0199"
        right_context = "B & S Electric (513) 805-3612"
        kwargs = {
            "business_name": "B & S Electric",
            "category": "Electrician",
            "phone": "(513) 805-3612",
        }

        self.assertFalse(
            is_search_result_relevant(
                wrong_context,
                business_name=kwargs["business_name"],
                category=kwargs["category"],
                phone=kwargs["phone"],
            )
        )
        self.assertFalse(
            email_matches_business(
                "services@bselectricfl.com",
                local_context=wrong_context,
                **kwargs,
            )
        )
        self.assertTrue(
            email_matches_business(
                "services@bselectricfl.com",
                local_context=right_context,
                **kwargs,
            )
        )

    def test_blacklist_applies_to_subdomains(self) -> None:
        self.assertIsNone(clean_extracted_email("events@collector.sentry.io"))


if __name__ == "__main__":
    unittest.main()
