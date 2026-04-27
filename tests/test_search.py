import tempfile
import unittest
from pathlib import Path

from src.pipeline.search import load_records, search_records


class SearchTests(unittest.TestCase):
    def test_load_records_and_search(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "legislation.jsonl"
            path.write_text(
                "\n".join(
                    [
                        '{"short_title":"Privacy Act 1988","jurisdiction":"Cth","status":"operative","source_id":"pa1988",'
                        '"text":"Division 1 Preliminary\\nSection 5 Definitions\\nThis Act protects privacy."}',
                        '{"short_title":"Privacy Act 1988","jurisdiction":"Cth","status":"operative","source_id":"pa1988",'
                        '"text":"duplicate"}',
                        '{"short_title":"Evidence Act 1995","jurisdiction":"Cth","status":"operative","source_id":"ea1995",'
                        '"text":"Clause 1 Name of Act"}',
                    ]
                ),
                encoding="utf-8",
            )
            rows = load_records(path)
            self.assertEqual(len(rows), 3)

            results = search_records("section 5", rows)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["source_id"], "pa1988")
            self.assertTrue(results[0]["snippets"])
            self.assertTrue(any("Section 5" in s for s in results[0]["snippets"]))

            filtered = search_records("clause 1", rows, jurisdiction="cth", status="operative", limit=1)
            self.assertEqual(len(filtered), 1)


if __name__ == "__main__":
    unittest.main()
