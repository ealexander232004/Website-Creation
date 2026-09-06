"""Regression tests for the browserless Google Maps payload client."""

from __future__ import annotations

import unittest
import urllib.parse

from rpc_client import GoogleMapsRpcClient


def sample_place_array() -> list[object]:
    place: list[object] = [None] * 260
    place[2] = ["3450 Sacramento St #204", "San Francisco, CA 94118"]
    place[4] = [None, None, None, None, None, None, None, 4.9]
    place[7] = ["https://example.com/", "example.com"]
    place[9] = [None, None, 37.7880523, -122.4495079]
    place[10] = "0x808f7fcbb5995f53:0xbc9c9e013fd095b"
    place[11] = "Example Plumbing"
    place[13] = ["Plumber", "Drainage service"]
    place[37] = [None, 243]
    place[39] = "3450 Sacramento St #204, San Francisco, CA 94118"
    place[78] = "ChIJU1-Ztct_j4ARWwn9E-DJyQs"
    place[178] = [["(415) 917-1088"]]
    return place


class DirectMapsClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = GoogleMapsRpcClient("http://proxy.invalid:8001")
        self.addCleanup(self.client.close)

    def test_proxy_is_mandatory(self) -> None:
        with self.assertRaisesRegex(ValueError, "require"):
            GoogleMapsRpcClient(None)

    def test_live_payload_shape_is_parsed(self) -> None:
        root: list[object] = [None] * 72
        root[64] = [[None, sample_place_array()]]
        leads = self.client._extract_leads_from_rpc_data(root, "plumber", 37.7749, -122.4194)

        self.assertEqual(len(leads), 1)
        lead = leads[0]
        self.assertEqual(lead.name, "Example Plumbing")
        self.assertEqual(lead.category, "Plumber")
        self.assertEqual(lead.all_categories, ["Plumber", "Drainage service"])
        self.assertEqual(lead.phone, "(415) 917-1088")
        self.assertEqual(lead.reviews_count, 243)
        self.assertEqual(lead.rating, 4.9)
        self.assertEqual(lead.place_id, "ChIJU1-Ztct_j4ARWwn9E-DJyQs")
        self.assertEqual(lead.cid, str(int("bc9c9e013fd095b", 16)))
        self.assertEqual(lead.website_raw, "https://example.com/")
        self.assertIn("query=Example+Plumbing", lead.maps_url)

    def test_pagination_offset_is_inserted_and_replaced(self) -> None:
        base = "https://www.google.com/search?tbm=map&q=plumber&pb=!1splumber!7i20!10b1"
        page_two = self.client._payload_url_with_offset(base, 20)
        page_three = self.client._payload_url_with_offset(page_two, 40)

        page_two_pb = urllib.parse.parse_qs(urllib.parse.urlsplit(page_two).query)["pb"][0]
        page_three_pb = urllib.parse.parse_qs(urllib.parse.urlsplit(page_three).query)["pb"][0]
        self.assertIn("!7i20!8i20!10b1", page_two_pb)
        self.assertIn("!7i20!8i40!10b1", page_three_pb)
        self.assertEqual(page_three_pb.count("!8i"), 1)


if __name__ == "__main__":
    unittest.main()
