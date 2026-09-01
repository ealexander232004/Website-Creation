from __future__ import annotations

import unittest
from dataclasses import dataclass

from google_maps_enrichment import (
    EnrichmentJob,
    ThrottleController,
    build_search_query,
    choose_match,
    fetch_official_review_metadata,
    name_similarity,
    verify_website,
)
from models import Lead
from proxy_manager import ProxyRoute
from rpc_client import GoogleMapsRpcClient, GoogleMapsThrottleError


def job(**overrides) -> EnrichmentJob:
    values = {
        "entity_id": 1,
        "canonical_name": "Robason Farms Pet Salon LLC",
        "street_address": "1935 Monkey Road",
        "city": "Rockport",
        "region": "TX",
        "postcode": "78382-1000",
        "country": "US",
        "latitude": 28.001886,
        "longitude": -97.083062,
    }
    values.update(overrides)
    return EnrichmentJob(**values)


def lead(**overrides) -> Lead:
    values = {
        "place_id": "ChIJ-test",
        "cid": "123",
        "name": "Robason Farms Pet Salon",
        "full_address": "1935 Monkey Rd, Rockport, TX 78382",
        "street": "1935 Monkey Rd",
        "city": "Rockport",
        "state": "TX",
        "zip_code": "78382",
        "latitude": 28.00190,
        "longitude": -97.08305,
        "website_raw": None,
    }
    values.update(overrides)
    return Lead(**values)


class MatchingTests(unittest.TestCase):
    def test_query_is_business_name_plus_location(self) -> None:
        self.assertEqual(
            build_search_query(job()),
            "Robason Farms Pet Salon LLC Rockport TX 78382-1000",
        )

    def test_legal_suffix_does_not_create_false_negative(self) -> None:
        self.assertEqual(name_similarity("Acme Plumbing LLC", "Acme Plumbing"), 1.0)

    def test_added_person_or_location_descriptor_does_not_create_false_negative(self) -> None:
        self.assertGreaterEqual(
            name_similarity("Modern Maryland Realty", "Shane Anderson, Modern Maryland Realty"),
            0.95,
        )

    def test_typo_with_strong_location_is_matched(self) -> None:
        decision = choose_match(job(), [lead(name="Robason Farm Pet Salonn")])
        self.assertEqual(decision.status, "matched")
        self.assertGreater(decision.best.name_score, 0.78)

    def test_exact_generic_name_far_away_is_ambiguous(self) -> None:
        source = job(
            canonical_name="Main Street Auto",
            city="Rockport",
            region="TX",
            postcode="78382",
        )
        candidate = lead(
            name="Main Street Auto",
            full_address="12 Main St, Dallas, TX 75201",
            street="12 Main St",
            city="Dallas",
            state="TX",
            zip_code="75201",
            latitude=32.7767,
            longitude=-96.7970,
        )
        self.assertEqual(choose_match(source, [candidate]).status, "ambiguous")

    def test_nearby_different_business_is_not_a_match(self) -> None:
        candidate = lead(name="Coastal Veterinary Hospital")
        self.assertEqual(choose_match(job(), [candidate]).status, "not_found")

    def test_two_close_candidates_are_ambiguous(self) -> None:
        candidates = [
            lead(name="Robason Farm Pet Salon", place_id="ChIJ-one"),
            lead(
                name="Robason Farms Pets Salon",
                place_id="ChIJ-two",
                latitude=28.00195,
                longitude=-97.08308,
            ),
        ]
        self.assertEqual(choose_match(job(), candidates).status, "ambiguous")

    def test_same_address_but_materially_different_name_is_ambiguous(self) -> None:
        source = job(canonical_name="Port A Food Hut")
        candidate = lead(name="Port A Beer Hut")
        self.assertEqual(choose_match(source, [candidate]).status, "ambiguous")

    def test_expanded_generic_name_with_bad_coordinate_is_ambiguous(self) -> None:
        source = job(
            canonical_name="Owl's Nest",
            street_address=None,
            city="Bedford",
            region="TX",
            postcode=None,
        )
        candidate = lead(
            name="The Owl's Nest Daycare & Preschool, Bedford",
            full_address="100 Main St, Bedford, TX",
            street="100 Main St",
            city="Bedford",
            state="TX",
            zip_code=None,
            latitude=34.0,
            longitude=-97.0,
        )
        self.assertEqual(choose_match(source, [candidate]).status, "ambiguous")

    def test_possible_nearby_branch_with_weak_address_is_ambiguous(self) -> None:
        candidate = lead(
            name="Robason Farms Pet Salon II",
            full_address="3140 Another Ave, Rockport, TX 70000",
            street="3140 Another Ave",
            zip_code="70000",
            latitude=28.008,
            longitude=-97.083,
        )
        self.assertEqual(choose_match(job(), [candidate]).status, "ambiguous")


class ReviewMetadataTests(unittest.TestCase):
    def test_no_api_key_never_substitutes_unverified_count(self) -> None:
        metadata = fetch_official_review_metadata(object(), "ChIJ-test", None)
        self.assertIsNone(metadata.review_count)
        self.assertIsNone(metadata.latest_review_at)
        self.assertEqual(metadata.source, "unavailable_no_api_key")


@dataclass
class FakeResponse:
    status_code: int
    url: str = "https://example.com/"
    text: str = "ok"


class FakeWebsiteClient:
    def __init__(self, result) -> None:
        self.result = result

    def _get(self, _url, headers):
        del headers
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class WebsiteVerificationTests(unittest.TestCase):
    def test_missing_google_website_is_left_for_explicit_negative_status(self) -> None:
        verification = verify_website(FakeWebsiteClient(FakeResponse(200)), None)
        self.assertIsNone(verification.verified)
        self.assertIsNone(verification.status)

    def test_successful_get_is_live(self) -> None:
        verification = verify_website(
            FakeWebsiteClient(FakeResponse(200)),
            "https://example.com/",
            max_attempts=1,
        )
        self.assertTrue(verification.verified)
        self.assertEqual(verification.status, "live")

    def test_http_error_keeps_exact_status(self) -> None:
        verification = verify_website(
            FakeWebsiteClient(FakeResponse(404)),
            "https://example.com/missing",
            max_attempts=1,
        )
        self.assertFalse(verification.verified)
        self.assertEqual(verification.status, "http_404")

    def test_timeout_is_not_reported_as_live(self) -> None:
        verification = verify_website(
            FakeWebsiteClient(TimeoutError("timed out")),
            "https://example.com/",
            max_attempts=1,
        )
        self.assertFalse(verification.verified)
        self.assertEqual(verification.status, "timeout")


class ThrottleControllerTests(unittest.TestCase):
    def test_hard_throttle_rate_aborts_run(self) -> None:
        controller = ThrottleController(
            window_size=3,
            minimum_events=3,
            rate_threshold=0.66,
            consecutive_limit=10,
        )
        route = ProxyRoute.from_url("http://proxy.example:8080")
        controller.record_failure(route, GoogleMapsThrottleError("HTTP 429"))
        controller.record_success(route)
        controller.record_failure(route, GoogleMapsThrottleError("HTTP 429"))
        self.assertTrue(controller.stop_requested)
        self.assertIn("hard throttle", controller.abort_reason)


class FakeCaptchaHandler:
    enabled = True

    def is_challenge_page(self, _url, _title, content) -> bool:
        return "challenge" in content

    def extract_sitekey(self, _content, _url) -> str:
        return "site-key"

    def solve_recaptcha(self, _url, _site_key, proxy_url=None) -> str:
        self.proxy_url = proxy_url
        return "solution-token"


class RpcCaptchaTests(unittest.TestCase):
    def test_challenge_is_solved_with_same_proxy_route(self) -> None:
        handler = FakeCaptchaHandler()
        client = GoogleMapsRpcClient(
            proxy_url="http://proxy.example:8080",
            captcha_handler=handler,
        )
        client._submit_google_challenge = lambda _response, _token: FakeResponse(
            200,
            "https://www.google.com/maps",
            "resolved",
        )
        try:
            response = client._guard_google_response(
                FakeResponse(200, "https://www.google.com/sorry/index", "challenge")
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(client.captcha_detected, 1)
            self.assertEqual(client.captcha_solved, 1)
            self.assertEqual(handler.proxy_url, "http://proxy.example:8080")
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
