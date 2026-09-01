"""Regression tests for email discovery precision and coverage."""

from __future__ import annotations

import unittest

from email_extractor import (
    build_search_queries,
    clean_extracted_email,
    email_matches_business,
)


class EmailSyntaxTests(unittest.TestCase):
    def test_accepts_plus_address_and_modern_tld(self) -> None:
        self.assertEqual(
            clean_extracted_email("Sales+West@Example.Photography"),
            "sales+west@example.photography",
        )

    def test_accepts_one_character_local_part(self) -> None:
        self.assertEqual(clean_extracted_email("a@acme.co"), "a@acme.co")

    def test_rejects_placeholder_and_asset_domains(self) -> None:
        self.assertIsNone(clean_extracted_email("sales@example.com"))
        self.assertIsNone(clean_extracted_email("sales@logo.png"))

    def test_system_prefix_only_rejects_actual_role_mailboxes(self) -> None:
        self.assertIsNone(clean_extracted_email("no-reply@acme.co"))
        self.assertEqual(
            clean_extracted_email("testimonials@acme.co"),
            "testimonials@acme.co",
        )


class SearchQueryTests(unittest.TestCase):
    def test_phone_leads_keep_name_city_fallback(self) -> None:
        queries = build_search_queries(
            "Acme Plumbing",
            phone="(512) 555-0199",
            city="Austin",
        )
        self.assertEqual(len(queries), 3)
        self.assertIn('"Acme Plumbing" "Austin"', queries[1])
        self.assertIn("5125550199", queries[0])


class BusinessOwnershipTests(unittest.TestCase):
    def test_nearby_phone_confirms_free_provider_mailbox(self) -> None:
        self.assertTrue(
            email_matches_business(
                "owner.name@gmail.com",
                "Acme Plumbing",
                category="Plumber",
                phone="512-555-0199",
                local_context="Call 512-555-0199 or owner.name@gmail.com",
                result_context="Acme Plumbing in Austin - contact information",
                source_url="https://local-listings.test/acme",
            )
        )

    def test_phone_without_result_name_does_not_transfer_ownership(self) -> None:
        self.assertFalse(
            email_matches_business(
                "wintermountainbtd@gmail.com",
                "Freedom Home Services LLC",
                category="House cleaning service",
                phone="423-621-1908",
                local_context="Call 423-621-1908 or wintermountainbtd@gmail.com",
                result_context="Winter Mountain Timber Dogs available puppies",
                source_url="https://wintermountaintimberdogs.com/available-puppies/",
            )
        )

    def test_directory_mailbox_is_rejected_even_near_business_phone(self) -> None:
        self.assertFalse(
            email_matches_business(
                "support@local-listings.test",
                "Acme Plumbing",
                category="Plumber",
                phone="512-555-0199",
                local_context="Acme Plumbing 512-555-0199 support@local-listings.test",
                source_url="https://local-listings.test/acme",
            )
        )

    def test_generic_industry_terms_do_not_establish_ownership(self) -> None:
        self.assertFalse(
            email_matches_business(
                "contact@foodtruckvibes.com",
                "Bob's Food Truck",
                category="Food truck",
                result_context="Bob's Food Truck in Austin",
                source_url="https://foodtruckvibes.com/bobs-food-truck",
            )
        )

    def test_distinctive_branded_domain_is_accepted(self) -> None:
        self.assertTrue(
            email_matches_business(
                "hello@centralvalleyroofing.com",
                "Central Valley Roofing",
                category="Roofing contractor",
                result_context="Central Valley Roofing contact details",
                source_url="https://centralvalleyroofing.com/contact",
            )
        )

    def test_four_character_brand_is_not_overfiltered(self) -> None:
        self.assertTrue(
            email_matches_business(
                "hello@acmeplumbing.com",
                "Acme Plumbing",
                category="Plumber",
                result_context="Acme Plumbing contact details",
                source_url="https://acmeplumbing.com/contact",
            )
        )

    def test_one_shared_word_does_not_match_unrelated_domain(self) -> None:
        self.assertFalse(
            email_matches_business(
                "insurance@growtherapy.com",
                "Grow Your Roots Carpentry, LLC",
                category="Carpenter",
                phone="458-205-4237",
                local_context="insurance@growtherapy.com",
                result_context="Grow Therapy insurance information",
                source_url="https://growtherapy.com/",
            )
        )

    def test_ambiguous_single_word_brand_is_not_enough(self) -> None:
        self.assertFalse(
            email_matches_business(
                "info@californiavaletparking.com",
                "Valet",
                category="Dry cleaner",
                result_context="California Valet Parking",
                source_url="https://californiavaletparking.com/",
            )
        )

    def test_partial_global_name_is_not_enough(self) -> None:
        self.assertFalse(
            email_matches_business(
                "admin@theglobalangle.com",
                "WARS Global",
                category="Contractor",
                result_context="Countries currently at war - The Global Angle",
                source_url="https://theglobalangle.com/countries-currently-at-war/",
            )
        )

    def test_single_word_name_requires_location_or_category_corroboration(self) -> None:
        self.assertFalse(
            email_matches_business(
                "hello@caffeluxxe.com",
                "Luxxe",
                category="Cleaners",
                city="Show Low",
                result_context="Caffe Luxxe specialty coffee roasters",
                source_url="https://caffeluxxe.com/",
            )
        )

    def test_directory_landing_page_cannot_use_phone_alone(self) -> None:
        common = {
            "business_name": "Boats R Us",
            "category": "Boat repair shop",
            "phone": "815-744-2628",
            "city": "Shorewood",
            "local_context": "Boats R Us 815-744-2628 contact details",
            "result_context": "Boats R Us boat repair in Shorewood",
            "source_url": "https://local.us-info.com/boats-r-us.html",
            "allow_phone_confirmation": False,
            "require_local_corroboration": True,
        }
        self.assertFalse(
            email_matches_business(
                "audrey@arcticthermalsolutions.com",
                **common,
            )
        )
        self.assertTrue(
            email_matches_business(
                "boatsrus@sbcglobal.net",
                **common,
            )
        )

    def test_digit_brand_survives_directory_precision_rule(self) -> None:
        self.assertTrue(
            email_matches_business(
                "book.transporta2b@gmail.com",
                "A2B Transport and Towing",
                category="Towing service",
                phone="704-555-0199",
                city="Salisbury",
                local_context="book.transporta2b@gmail.com",
                result_context="A2B Transport and Towing in Salisbury",
                source_url="https://dot.report/usdot/4208367",
                allow_phone_confirmation=False,
                require_local_corroboration=True,
            )
        )

    def test_same_name_directory_listing_in_another_state_is_rejected(self) -> None:
        self.assertFalse(
            email_matches_business(
                "carolinatowingandroadside@gmail.com",
                "Carolina Towing",
                category="Towing service",
                phone="706-832-3505",
                city="North Augusta",
                local_context="Carolina Towing & Roadside Assistance, Trinity NC",
                result_context="Carolina Towing & Roadside Assistance LLC - Trinity, North Carolina",
                source_url="https://bubba.ai/trucking-companies/north-carolina/trinity/carolina-towing-roadside-assistance-llc",
                allow_phone_confirmation=False,
                require_local_corroboration=True,
            )
        )

    def test_two_word_prefix_does_not_confirm_three_word_business(self) -> None:
        self.assertFalse(
            email_matches_business(
                "hello@redoakrealty.com",
                "RED OAK TRADING",
                category="Auto repair shop",
                city="Moody",
                result_context="Red Oak Realty homes and agents",
                source_url="https://redoakrealty.com/",
            )
        )

    def test_full_multiword_name_still_confirms_branded_free_mailbox(self) -> None:
        self.assertTrue(
            email_matches_business(
                "faizaanwarsewing@gmail.com",
                "Faiza Anwar Sewing & Alteration",
                category="Sewing shop",
                city="Everett",
                result_context="Faiza Anwar Sewing & Alteration in Everett",
                source_url="https://faizaanwarsewing.com/",
            )
        )

    def test_person_name_at_unrelated_custom_domain_is_rejected(self) -> None:
        self.assertFalse(
            email_matches_business(
                "raycook@allstate.com",
                "Ray Cook CPA",
                category="Accountant",
                phone="207-377-8749",
                city="Winthrop",
                local_context="Ray Cook CPA 207-377-8749 raycook@allstate.com",
                result_context="Ray Cook CPA in Winthrop",
                source_url="https://www.allbiz.com/business/ray-cook-cpa",
                allow_phone_confirmation=False,
                require_local_corroboration=True,
            )
        )

    def test_modern_free_provider_still_uses_branded_local_part(self) -> None:
        self.assertTrue(
            email_matches_business(
                "acmeplumbing@proton.me",
                "Acme Plumbing",
                category="Plumber",
                city="Austin",
                result_context="Acme Plumbing in Austin",
                source_url="https://local-listings.test/acme",
            )
        )


if __name__ == "__main__":
    unittest.main()
