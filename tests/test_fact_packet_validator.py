from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fact_packet_validator", ROOT / "scripts" / "validate_fact_packet.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SCHEMA = json.loads((ROOT / "schemas" / "fact-packet.schema.json").read_text(encoding="utf-8"))
FIXTURES = ROOT / "tests" / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FactPacketValidatorTests(unittest.TestCase):
    def test_bundled_example_passes(self) -> None:
        packet = json.loads(
            (ROOT / "examples" / "fact-packet.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], VALIDATOR.validate_packet(packet, SCHEMA))

    def test_valid_fixture_passes(self) -> None:
        packet = load_fixture("fact-packet.valid.json")
        self.assertEqual([], VALIDATOR.validate_packet(packet, SCHEMA))

    def test_invalid_evidence_status_fails(self) -> None:
        packet = load_fixture("fact-packet.invalid-enum.json")
        errors = VALIDATOR.validate_packet(packet, SCHEMA)
        self.assertTrue(any("PROBABLY_TRUE" in error for error in errors), errors)

    def test_duplicate_fact_id_fails(self) -> None:
        packet = load_fixture("fact-packet.duplicate-fact-id.json")
        errors = VALIDATOR.validate_packet(packet, SCHEMA)
        self.assertTrue(any("duplicate fact_id" in error for error in errors), errors)

    def test_missing_required_field_fails(self) -> None:
        packet = load_fixture("fact-packet.valid.json")
        del packet["facts"][0]["claim"]
        errors = VALIDATOR.validate_packet(packet, SCHEMA)
        self.assertTrue(any("claim" in error for error in errors), errors)

    def test_additional_property_fails(self) -> None:
        packet = load_fixture("fact-packet.valid.json")
        packet["facts"][0]["surprise"] = "not in the schema"
        errors = VALIDATOR.validate_packet(packet, SCHEMA)
        self.assertTrue(any("additional property" in error for error in errors), errors)

    def test_invalid_date_fails(self) -> None:
        packet = load_fixture("fact-packet.valid.json")
        packet["facts"][0]["as_of"] = "2026-13-40"
        errors = VALIDATOR.validate_packet(packet, SCHEMA)
        self.assertTrue(any("YYYY-MM-DD" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
