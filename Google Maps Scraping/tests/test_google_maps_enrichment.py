from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import datetime, timezone

from google_maps_enrichment import (
    EnrichmentRepository,
    EnrichmentJob,
    MATCH_POLICY_VERSION,
    MATCH_THRESHOLD,
    ReviewMetadata,
    ThrottleController,
    WebsiteVerification,
    assess_candidate,
    build_search_query,
    choose_match,
    fetch_internal_review_metadata,
    fetch_official_review_metadata,
    name_similarity,
    verify_website,
)
from models import Lead
from proxy_manager import ProxyRoute
from rpc_client import (
    GoogleMapsPayloadDiscoveryError,
    GoogleMapsReviewPage,
    GoogleMapsRpcClient,
    GoogleMapsThrottleError,
)


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
        "review_count_available": True,
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

    def test_exact_generic_name_far_away_matches_under_recall_bias(self) -> None:
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
        self.assertEqual(choose_match(source, [candidate]).status, "matched")

    def test_nearby_different_business_is_not_a_match(self) -> None:
        candidate = lead(name="Coastal Veterinary Hospital")
        self.assertEqual(choose_match(job(), [candidate]).status, "not_found")

    def test_two_close_candidates_choose_the_highest_score(self) -> None:
        candidates = [
            lead(name="Robason Farm Pet Salon", place_id="ChIJ-one"),
            lead(
                name="Robason Farms Pets Salon",
                place_id="ChIJ-two",
                latitude=28.00195,
                longitude=-97.08308,
            ),
        ]
        decision = choose_match(job(), candidates)
        self.assertEqual(decision.status, "matched")
        self.assertEqual(decision.best, decision.candidates[0])

    def test_same_address_and_similar_name_crosses_binary_line(self) -> None:
        source = job(canonical_name="Port A Food Hut")
        candidate = lead(name="Port A Beer Hut")
        self.assertEqual(choose_match(source, [candidate]).status, "matched")

    def test_expanded_name_and_rough_location_cross_binary_line(self) -> None:
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
        self.assertEqual(choose_match(source, [candidate]).status, "matched")

    def test_possible_nearby_branch_with_rough_location_is_matched(self) -> None:
        candidate = lead(
            name="Robason Farms Pet Salon II",
            full_address="3140 Another Ave, Rockport, TX 70000",
            street="3140 Another Ave",
            zip_code="70000",
            latitude=28.008,
            longitude=-97.083,
        )
        self.assertEqual(choose_match(job(), [candidate]).status, "matched")

    def test_high_name_similarity_tolerates_rough_location_only(self) -> None:
        candidate = lead(
            name="Robason Farm Pet Salon",
            full_address="900 Harbor Rd, Aransas Pass, TX 78336",
            street="900 Harbor Rd",
            city="Aransas Pass",
            state="TX",
            zip_code="78336",
            latitude=27.91,
            longitude=-97.15,
        )
        self.assertEqual(choose_match(job(), [candidate]).status, "matched")

    def test_rough_location_cannot_override_a_different_name(self) -> None:
        candidate = lead(
            name="Coastal Veterinary Hospital",
            full_address="1935 Monkey Rd, Rockport, TX 78382",
        )
        self.assertEqual(choose_match(job(), [candidate]).status, "not_found")

    def test_no_candidates_is_a_binary_not_found(self) -> None:
        decision = choose_match(job(), [])
        self.assertEqual(decision.status, "not_found")
        self.assertIsNone(decision.best)

    def test_decision_uses_the_documented_hard_threshold(self) -> None:
        assessment = assess_candidate(job(), lead())
        decision = choose_match(job(), [lead()])
        self.assertGreaterEqual(assessment.composite_score, MATCH_THRESHOLD)
        self.assertEqual(decision.reason, "binary_score_at_or_above_threshold")


class FakeDatabaseConnection:
    def __init__(self) -> None:
        self.query = None
        self.params = None
        self.queries = []
        self.param_list = []
        self.committed = False

    def execute(self, query, params):
        self.query = query
        self.params = params
        self.queries.append(query)
        self.param_list.append(params)

    def commit(self) -> None:
        self.committed = True

class PersistenceTests(unittest.TestCase):
    def test_binary_confidence_and_policy_are_written(self) -> None:
        source = job()
        decision = choose_match(source, [lead(website_raw="https://example.com/")])
        connection = FakeDatabaseConnection()
        EnrichmentRepository.finish(
            connection,
            source,
            build_search_query(source),
            decision,
            ReviewMetadata(None, None, None, "unavailable_no_api_key"),
        )
        self.assertIn("match_policy_version = %s", connection.query)
        self.assertEqual(connection.query.count("%s"), len(connection.params))
        self.assertIn(decision.best.composite_score, connection.params)
        self.assertIn(MATCH_POLICY_VERSION, connection.params)
        self.assertIn(MATCH_THRESHOLD, connection.params)
        self.assertIn("queued", connection.params)
        self.assertTrue(connection.committed)

    def test_finish_batch_writes_all_items(self) -> None:
        source1 = job(entity_id=101)
        source2 = job(entity_id=102)
        decision1 = choose_match(source1, [lead(website_raw="https://example.com/")])
        decision2 = choose_match(source2, [])
        connection = FakeDatabaseConnection()
        items = [
            (
                source1,
                build_search_query(source1),
                decision1,
                ReviewMetadata(5, None, None, "test"),
            ),
            (
                source2,
                build_search_query(source2),
                decision2,
                ReviewMetadata(None, None, None, "test"),
            ),
        ]
        EnrichmentRepository.finish_batch(connection, items)
        self.assertEqual(len(connection.queries), 2)
        self.assertEqual(connection.param_list[0][-1], 101)
        self.assertEqual(connection.param_list[1][-1], 102)
        self.assertTrue(connection.committed)

    def test_finish_website_batch_writes_all_items(self) -> None:
        from google_maps_enrichment import WebsiteJob, WebsiteVerification
        job1 = WebsiteJob(entity_id=201, website_url="https://live.com")
        job2 = WebsiteJob(entity_id=202, website_url="https://dead.com")
        v1 = WebsiteVerification(True, "live", datetime.now(timezone.utc))
        v2 = WebsiteVerification(False, "http_404", datetime.now(timezone.utc))
        connection = FakeDatabaseConnection()
        EnrichmentRepository.finish_website_batch(connection, [(job1, v1), (job2, v2)])
        self.assertEqual(len(connection.queries), 2)
        self.assertIn("website_check_state = 'completed'", connection.queries[0])
        self.assertEqual(connection.param_list[0][-1], 201)
        self.assertEqual(connection.param_list[1][-1], 202)
        self.assertTrue(connection.committed)


class ReviewMetadataTests(unittest.TestCase):
    def test_no_api_key_never_substitutes_unverified_count(self) -> None:
        metadata = fetch_official_review_metadata(object(), "ChIJ-test", None)
        self.assertIsNone(metadata.review_count)
        self.assertIsNone(metadata.latest_review_at)
        self.assertEqual(metadata.source, "unavailable_no_api_key")

    def test_internal_metadata_extracts_structured_count_and_hours(self) -> None:
        sample_lead = lead(
            cid="12345",
            reviews_count=47,
            operating_hours={"Monday": "9 AM–5 PM"},
            has_operating_hours=True,
            is_claimed_owner=True,
            is_permanently_closed=False,
            is_temporarily_closed=False,
        )
        metadata = fetch_internal_review_metadata(object(), sample_lead)
        self.assertEqual(metadata.review_count, 47)
        self.assertIsNone(metadata.latest_review_at)
        self.assertEqual(metadata.source, "maps_search_structured")
        self.assertTrue(metadata.has_operating_hours)
        self.assertFalse(metadata.is_permanently_closed)
        self.assertFalse(metadata.is_temporarily_closed)
        self.assertEqual(metadata.regular_hours, {"Monday": "9 AM–5 PM"})
        self.assertTrue(metadata.is_claimed_owner)
    def test_internal_unlisted_count_reports_unlisted(self) -> None:
        sample_lead = lead(reviews_count=0, review_count_available=False)
        metadata = fetch_internal_review_metadata(object(), sample_lead)
        self.assertIsNone(metadata.review_count)
        self.assertEqual(metadata.source, "maps_search_unlisted_or_zero")

class ReviewRpcTests(unittest.TestCase):
    def test_search_parser_uses_review_count_not_photo_count(self) -> None:
        place = [None] * 179
        place[4] = [None] * 9
        place[4][7] = 4.8
        place[4][8] = 103
        place[9] = [None, None, 28.0019, -97.083]
        place[10] = "0x0:0x7b"
        place[11] = "Robason Farms Pet Salon"
        place[37] = [None, 25]
        place[39] = "1935 Monkey Rd, Rockport, TX 78382"
        place[78] = "ChIJ-test"

        client = object.__new__(GoogleMapsRpcClient)
        parsed = client._parse_place_array(place, "test", 28.0, -97.0)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.reviews_count, 103)
        self.assertTrue(parsed.review_count_available)
        self.assertEqual(parsed.cid, "123")

    def test_search_parser_extracts_operating_hours(self) -> None:
        place = [None] * 210
        place[4] = [None] * 9
        place[4][7] = 4.6
        place[4][8] = 533
        place[9] = [None, None, 33.4078, -111.9540]
        place[10] = "0x0:0x7b"
        place[11] = "The Gaming Zone"
        place[57] = [None, "The Gaming Zone (Owner)"]
        place[78] = "ChIJ-test"
        place[203] = [
            [
                ["Wednesday", 3, [2026, 9, 2], [["11 AM–7 PM", [[11], [19]]]]],
                ["Thursday", 4, [2026, 9, 3], [["11 AM–10 PM", [[11], [22]]]]],
            ],
            [["Wednesday", 3, [2026, 9, 2], [["11 AM–7 PM", [[11], [19]]]]], 0, 4, None, ["Opens soon · 11 AM"]]
        ]

        client = object.__new__(GoogleMapsRpcClient)
        parsed = client._parse_place_array(place, "test", 33.4, -111.9)
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed.has_operating_hours)
        self.assertTrue(parsed.is_claimed_owner)
        self.assertEqual(parsed.operating_hours["Wednesday"], "11 AM–7 PM")
        self.assertEqual(parsed.operating_hours["Thursday"], "11 AM–10 PM")

    def test_search_parser_rescues_review_count_from_p4_sub3(self) -> None:
        place = [None] * 180
        place[4] = [None, None, None, ["https://maps...", "27 reviews"], None, None, None, 3.7]
        place[9] = [None, None, 34.0, -84.0]
        place[10] = "0x0:0x7b"
        place[11] = "Rio Bravo Auto Sales"
        place[78] = "ChIJ-test"

        client = object.__new__(GoogleMapsRpcClient)
        parsed = client._parse_place_array(place, "test", 34.0, -84.0)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.reviews_count, 27)
        self.assertTrue(parsed.review_count_available)
        self.assertTrue(parsed.review_count_available)
        self.assertEqual(parsed.rating, 3.7)

    def test_search_parser_detects_permanent_closure(self) -> None:
        place = [None] * 100
        place[10] = "0x0:0x7b"
        place[11] = "Closed Restaurant"
        place[78] = "ChIJ-test"
        place[88] = ["CLOSED", "SearchResult.TYPE_RESTAURANT"]

        client = object.__new__(GoogleMapsRpcClient)
        parsed = client._parse_place_array(place, "test", 33.4, -111.9)
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed.is_permanently_closed)
        self.assertFalse(parsed.is_temporarily_closed)
        self.assertFalse(parsed.has_operating_hours)
        self.assertEqual(parsed.business_status, "CLOSED_PERMANENTLY")
    def test_qv9_payload_extracts_microsecond_timestamp(self) -> None:
        micros = 1_752_227_400_000_000
        metadata = [None, None, None, micros, None, None, "2 months ago"]
        payload = [None, None, [[[None, metadata]]], None, None, True]
        page = GoogleMapsRpcClient._parse_review_rpc_payload(payload)
        self.assertTrue(page.has_reviews)
        self.assertEqual(
            page.latest_review_at,
            datetime.fromtimestamp(micros / 1_000_000, tz=timezone.utc),
        )
        self.assertEqual(page.relative_date, "2 months ago")

    def test_qv9_request_uses_cid_and_newest_sort(self) -> None:
        client = object.__new__(GoogleMapsRpcClient)
        inner = client._review_rpc_inner("123", "session-id", 81)
        self.assertEqual(inner[0][0][0], "0x0:0x7b")
        self.assertEqual(inner[0][5], [None, None, None, [[1]]])
        self.assertEqual(inner[4][0], "session-id")
        self.assertEqual(inner[4][6], 81)
        self.assertEqual(inner[12], [2])


@dataclass
class FakeResponse:
    status_code: int
    url: str = "https://example.com/"
    text: str = "ok"


class FakeWebsiteClient:
    def __init__(self, result) -> None:
        self.result = result
        self.calls = 0

    def _get(self, _url, headers):
        del headers
        self.calls += 1
        result = self.result.pop(0) if isinstance(self.result, list) else self.result
        if isinstance(result, Exception):
            raise result
        return result


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
        client = FakeWebsiteClient(TimeoutError("timed out"))
        verification = verify_website(
            client,
            "https://example.com/",
        )
        self.assertFalse(verification.verified)
        self.assertEqual(verification.status, "timeout")
        self.assertEqual(client.calls, 1)

    def test_deterministic_network_error_is_not_retried(self) -> None:
        client = FakeWebsiteClient(OSError("connection refused"))
        verification = verify_website(client, "https://example.com/")
        self.assertFalse(verification.verified)
        self.assertEqual(verification.status, "network_error")
        self.assertEqual(client.calls, 1)

    def test_http_503_error_is_not_retried(self) -> None:
        client = FakeWebsiteClient([FakeResponse(503)])
        verification = verify_website(client, "https://example.com/")
        self.assertFalse(verification.verified)
        self.assertEqual(verification.status, "http_503")
        self.assertEqual(client.calls, 1)

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

    def test_payload_discovery_miss_resets_session_without_proxy_cooldown(self) -> None:
        controller = ThrottleController()
        route = ProxyRoute.from_url("http://proxy.example:8080")
        throttled = controller.record_failure(
            route,
            GoogleMapsPayloadDiscoveryError("missing payload URL"),
        )
        self.assertFalse(throttled)
        self.assertEqual(route.failure_count, 0)
        self.assertEqual(route.cooldown_until, 0.0)
        self.assertFalse(controller.stop_requested)


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


class MultiProcessArgTests(unittest.TestCase):
    def test_processes_arg_defaults_to_one(self) -> None:
        from enrich_google_maps import parse_args
        import sys
        orig_argv = sys.argv
        try:
            sys.argv = ["enrich_google_maps.py", "--limit", "100", "--workers", "10"]
            args = parse_args()
            self.assertEqual(args.processes, 1)
            self.assertIsNone(args.child_run)
            self.assertEqual(args.worker_offset, 0)
        finally:
            sys.argv = orig_argv

    def test_processes_arg_parses_custom_value(self) -> None:
        from enrich_google_maps import parse_args
        import sys
        orig_argv = sys.argv
        try:
            sys.argv = ["enrich_google_maps.py", "--limit", "100", "--workers", "10", "--processes", "4"]
            args = parse_args()
            self.assertEqual(args.processes, 4)
        finally:
            sys.argv = orig_argv

if __name__ == "__main__":
    unittest.main()
