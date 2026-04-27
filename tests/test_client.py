import unittest

from src.ingest.austlii.client import AustliiClient


class ClientTests(unittest.TestCase):
    def test_candidate_urls_includes_variants(self):
        url = "https://www.austlii.edu.au/au/legis/cth/consol_act/"
        candidates = AustliiClient._candidate_urls(url)
        self.assertIn(url, candidates)
        self.assertIn("https://www8.austlii.edu.au/au/legis/cth/consol_act/", candidates)
        self.assertIn("http://www.austlii.edu.au/au/legis/cth/consol_act/", candidates)


if __name__ == "__main__":
    unittest.main()
