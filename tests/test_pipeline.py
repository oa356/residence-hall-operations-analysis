import json
import unittest
from pathlib import Path

import pandas as pd

from src.analyze import PROCESSED_PATH, RAW_PATH, clean_data, summarize


ROOT = Path(__file__).resolve().parents[1]


class MaintenancePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(RAW_PATH)
        cls.cleaned = clean_data(cls.raw)
        cls.metrics, cls.tables = summarize(cls.cleaned)

    def test_raw_dataset_has_expected_quality_issue(self):
        self.assertEqual(len(self.raw), 3200)
        self.assertEqual(self.raw["request_id"].nunique(), 3199)

    def test_cleaning_removes_duplicate_request_id(self):
        self.assertEqual(len(self.cleaned), 3199)
        self.assertEqual(self.cleaned["request_id"].nunique(), len(self.cleaned))

    def test_derived_metrics_are_present_and_valid(self):
        required = {"assignment_hours", "resolution_hours", "sla_target_hours", "within_assignment_sla"}
        self.assertTrue(required.issubset(self.cleaned.columns))
        self.assertTrue((self.cleaned["assignment_hours"] >= 0).all())
        self.assertGreater(self.metrics["assignment_sla_rate"], 0)
        self.assertLessEqual(self.metrics["assignment_sla_rate"], 100)

    def test_summary_tables_cover_all_categories(self):
        self.assertEqual(self.tables["category_summary"]["requests"].sum(), 3199)
        self.assertGreaterEqual(len(self.tables["hall_summary"]), 6)
        self.assertGreaterEqual(len(self.tables["issue_summary"]), 10)

    def test_generated_metrics_file_matches_clean_dataset_when_present(self):
        metrics_path = ROOT / "reports" / "metrics.json"
        if metrics_path.exists():
            saved = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["clean_records"], len(self.cleaned))
            self.assertEqual(saved["raw_records"], len(self.raw))


if __name__ == "__main__":
    unittest.main()
