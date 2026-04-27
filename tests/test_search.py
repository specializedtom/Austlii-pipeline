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
                        '{"short_title":"Privacy Act 1988","jurisdiction":"Cth","status":"operative","source_id":"pa1988"}',
                        '{"short_title":"Evidence Act 1995","jurisdiction":"Cth","status":"operative","source_id":"ea1995"}',
                    ]
                ),
                encoding="utf-8",
            )
            rows = load_records(path)
            self.assertEqual(len(rows), 2)

            results = search_records("privacy", rows)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["source_id"], "pa1988")

            filtered = search_records("act", rows, jurisdiction="cth", status="operative", limit=1)
            self.assertEqual(len(filtered), 1)


if __name__ == "__main__":
    unittest.main()
