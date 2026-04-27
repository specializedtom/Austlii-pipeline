import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.models.legislation import Jurisdiction
from src.pipeline import workflow


class WorkflowTests(unittest.TestCase):
    def test_ingest_continues_on_failure(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)

            class FailingClient:
                def fetch(self, _url):
                    raise RuntimeError("blocked")

            with patch.object(workflow, "STATE_FILE", base / "state.json"), patch.object(
                workflow, "FAILED_FILE", base / "failed.jsonl"
            ), patch.object(workflow, "discover_seed_urls", lambda _j: ["https://example.invalid/test"]), patch.object(
                workflow, "AustliiClient", FailingClient
            ):
                result = workflow.ingest(Jurisdiction.CTH)

            self.assertEqual(result["records_ingested"], 0)
            self.assertEqual(result["records_failed"], 1)
            self.assertTrue((base / "failed.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
