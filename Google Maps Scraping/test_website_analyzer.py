"""Regression tests for no-website targeting policy."""

from __future__ import annotations

import unittest

from models import WebsiteType
from website_analyzer import classify_website, is_target_lead


class WebsiteAnalyzerTests(unittest.TestCase):
    def test_social_profile_counts_as_no_website(self) -> None:
        website_type, has_website, _ = classify_website("https://facebook.com/example")

        self.assertEqual(website_type, WebsiteType.SOCIAL_MEDIA)
        self.assertFalse(has_website)
        self.assertTrue(is_target_lead(website_type))

    def test_free_hosted_site_counts_as_a_website(self) -> None:
        website_type, has_website, _ = classify_website("https://example.wixsite.com/home")

        self.assertEqual(website_type, WebsiteType.FREE_BUILDER)
        self.assertTrue(has_website)
        self.assertFalse(is_target_lead(website_type))

    def test_dead_google_business_site_still_counts_as_no_website(self) -> None:
        website_type, has_website, _ = classify_website("https://example.business.site")

        self.assertEqual(website_type, WebsiteType.DEPRECATED_GOOGLE_SITE)
        self.assertFalse(has_website)
        self.assertTrue(is_target_lead(website_type))


if __name__ == "__main__":
    unittest.main()
