import unittest

from src.ingest.austlii.client import AustliiClient


class ClientTests(unittest.TestCase):
    def test_candidate_urls_includes_variants(self):
        url = "https://www.austlii.edu.au/au/legis/cth/consol_act/"
        candidates = AustliiClient._candidate_urls(url)
        self.assertIn(url, candidates)
        self.assertIn("https://www8.austlii.edu.au/au/legis/cth/consol_act/", candidates)
        self.assertIn("http://www.austlii.edu.au/au/legis/cth/consol_act/", candidates)

    def test_default_headers_match_required_austlii_profile(self):
        client = AustliiClient()
        self.assertIn("Chrome/122.0.0.0", client.user_agent)
        self.assertEqual(client.extra_headers.get("Referer"), "https://www.austlii.edu.au/forms/search1.html")
        self.assertEqual(
            client.extra_headers.get("Accept"),
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )
        self.assertEqual(client.extra_headers.get("Accept-Language"), "en-AU,en;q=0.9")


if __name__ == "__main__":
    unittest.main()
