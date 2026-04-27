import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.ingest.austlii import store
from src.models.legislation import InstrumentType, Jurisdiction, LegislationRecord


class StoreTests(unittest.TestCase):
    def test_upsert_replaces_by_source_id(self):
        with tempfile.TemporaryDirectory() as td:
            processed = Path(td) / "legislation.jsonl"

            with patch.object(store, "PROCESSED_PATH", processed):
                first = LegislationRecord(
                    source_url="https://example.test/one",
                    source_id="id-1",
                    short_title="Privacy Act 1988",
                    full_title="Privacy Act 1988",
                    jurisdiction=Jurisdiction.CTH,
                    instrument_type=InstrumentType.ACT,
                    status="unknown",
                    text="unknown",
                )
                second = LegislationRecord(
                    source_url="https://example.test/one",
                    source_id="id-1",
                    short_title="Privacy Act 1988",
                    full_title="Privacy Act 1988",
                    jurisdiction=Jurisdiction.CTH,
                    instrument_type=InstrumentType.ACT,
                    status="operative",
                    text="in force",
                )

                store.upsert_record(first)
                store.upsert_record(second)

            lines = [line for line in processed.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(lines), 1)
            self.assertIn('"operative"', lines[0])


if __name__ == "__main__":
    unittest.main()
