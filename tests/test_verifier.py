import unittest
from unittest.mock import patch

from src.pipeline import verifier


class VerifierTests(unittest.TestCase):
    def test_extract_legislation_citations(self):
        text = "Under the Privacy Act 1988 (Cth), the Copyright Act, and Evidence Act 1995 (Cth), obligations apply."
        hits = verifier.extract_legislation_citations(text, limit=5)
        self.assertEqual(len(hits), 3)
        self.assertEqual(hits[0]["title"], "Privacy Act")
        self.assertFalse(hits[0]["citation"].lower().startswith("the "))
        self.assertEqual(hits[1]["title"], "Copyright Act")
        self.assertIsNone(hits[1]["year"])

    def test_verify_text_citations(self):
        with patch.object(verifier, "austlii_legislation_search") as mock_search:
            mock_search.side_effect = [
                {"found": True, "title": "Privacy Act 1988", "url": "https://www.austlii.edu.au/x"},
                {"found": False, "error": "not found"},
            ]
            out = verifier.verify_text_citations(
                "Privacy Act 1988 and Madeup Act 1999",
                limit=5,
                default_jurisdiction="Cth",
            )
            self.assertEqual(out["citations_found"], 2)
            self.assertEqual(len(out["verified"]), 1)
            self.assertEqual(len(out["unverified"]), 1)


if __name__ == "__main__":
    unittest.main()
