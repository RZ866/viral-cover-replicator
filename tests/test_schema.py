from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from create_example import build
from validate_report import validate_instance, validate_semantics


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "schemas" / "shooting-report.schema.json").read_text(encoding="utf-8"))

    def errors(self, data):
        return validate_instance(data, self.schema, self.schema) + validate_semantics(data)

    def test_valid_example_passes(self):
        self.assertEqual([], self.errors(build()))

    def test_missing_required_field_is_rejected(self):
        data = build(); del data["lighting"]
        self.assertTrue(any("lighting" in item for item in self.errors(data)))

    def test_wrong_type_and_unknown_field_are_rejected(self):
        data = build(); data["project_info"]["mode"] = 7; data["secret"] = "x"
        errors = self.errors(data)
        self.assertTrue(any("mode" in item for item in errors))
        self.assertTrue(any("secret" in item for item in errors))

    def test_null_stages_are_allowed(self):
        data = build(); data["comparison_results"] = None; data["originality_review"] = None
        self.assertEqual([], self.errors(data))

    def test_three_plans_must_be_distinct(self):
        data = build(); data["original_shooting_plans"][1]["theme"] = data["original_shooting_plans"][0]["theme"]
        self.assertTrue(any("theme" in item for item in self.errors(data)))

    def test_unknown_claim_must_not_fake_confidence(self):
        data = build(); data["image_observations"].append({"type":"UNKNOWN","statement":"无法判断","evidence":None,"confidence":.8})
        self.assertTrue(any("UNKNOWN" in item for item in self.errors(data)))


if __name__ == "__main__":
    unittest.main()
