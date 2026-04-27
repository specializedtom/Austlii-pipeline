import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.pipeline import workflow


class ClassifyTests(unittest.TestCase):
    def test_classify_updates_status_in_processed_file(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            processed = base / "legislation.jsonl"
            state = base / "state.json"
            failed = base / "failed.jsonl"

            processed.write_text(
                '{"source_url":"https://example.test/a","source_id":"a1","short_title":"Privacy Act 1988",'
                '"full_title":"Privacy Act 1988","jurisdiction":"Cth","instrument_type":"Act",'
                '"status":"unknown","text":"This Act is currently in force."}\n',
                encoding="utf-8",
            )

            with patch.object(workflow, "PROCESSED_FILE", processed), patch.object(workflow, "STATE_FILE", state), patch.object(
                workflow, "FAILED_FILE", failed
            ):
                result = workflow.classify()

            self.assertEqual(result["records_classified"], 1)
            self.assertEqual(result["operative_records"], 1)
            self.assertIn('"status": "operative"', processed.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
