from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "output_contract_validator", ROOT / "scripts" / "validate_output_contract.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SCHEMA = json.loads((ROOT / "schemas" / "output-contract.schema.json").read_text(encoding="utf-8"))
PLATFORMS = json.loads((ROOT / "config" / "platforms.json").read_text(encoding="utf-8"))["platforms"]
FIXTURES = ROOT / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class OutputContractValidatorTests(unittest.TestCase):
    def validate(self, record: dict) -> list[str]:
        return VALIDATOR.validate_record(record, SCHEMA, PLATFORMS)

    def test_bundled_example_passes(self) -> None:
        record = json.loads(
            (ROOT / "examples" / "output-contract.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], self.validate(record))

    def test_valid_fixture_passes(self) -> None:
        self.assertEqual([], self.validate(load_fixture("output-contract.valid.json")))

    def test_unknown_platform_fails(self) -> None:
        errors = self.validate(load_fixture("output-contract.unknown-platform.json"))
        self.assertTrue(any("unknown platform_id" in error for error in errors), errors)

    def test_unknown_key_fails(self) -> None:
        errors = self.validate(load_fixture("output-contract.unknown-key.json"))
        self.assertTrue(any("additional property" in error for error in errors), errors)

    def test_missing_required_field_fails(self) -> None:
        record = load_fixture("output-contract.valid.json")
        del record["decision"]
        errors = self.validate(record)
        self.assertTrue(any("decision" in error for error in errors), errors)

    def test_invalid_decision_fails(self) -> None:
        record = load_fixture("output-contract.valid.json")
        record["decision"] = "SHIP_IT"
        errors = self.validate(record)
        self.assertTrue(any("SHIP_IT" in error for error in errors), errors)

    def test_published_true_fails(self) -> None:
        record = load_fixture("output-contract.valid.json")
        record["published"] = True
        errors = self.validate(record)
        self.assertTrue(any("published" in error for error in errors), errors)

    def test_skill_mismatch_fails(self) -> None:
        record = load_fixture("output-contract.valid.json")
        record["skill_name"] = "platform-write-zhihu"
        errors = self.validate(record)
        self.assertTrue(any("not the skill registered" in error for error in errors), errors)

    def test_duplicate_fact_id_used_fails(self) -> None:
        record = load_fixture("output-contract.valid.json")
        record["fact_ids_used"] = ["FACT-FIXTURE-001", "FACT-FIXTURE-001"]
        errors = self.validate(record)
        self.assertTrue(any("duplicate fact_id" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
